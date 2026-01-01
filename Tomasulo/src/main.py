import os
import sys

# Enable running as a script (e.g. `python Tomasulo/src/main.py`) by fixing the
# module search path for relative imports.
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    __package__ = "Tomasulo.src"

from assassyn.frontend import *
from assassyn.backend import *
from assassyn import utils, backend
from assassyn.utils import run_simulator, run_verilator
from .decoder import decoder_logic
from .ROB import *
from .RS import *
from .LSQ import *
from .commit import *
from .arbitrator import *
from .multiplier import MultiplierRegs, MultiplierState, MUL_RSEntry, MUL_RS_downstream, MUL_signal, MUL_LATENCY, MUL_RS_NUM

ROB_MASK = (1 << ROB_IDX_WIDTH) - 1

# Issue 阶段产生的预测控制信号
IssueControl_signal = Record(
    predict_valid = Bits(1),     # B/JAL 预测跳转有效
    predict_target_pc = UInt(32), # 预测的目标 PC
    jalr_stall = Bits(1),        # JALR 需要 stall
    stall = Bits(1),             # 资源冲突导致的 stall
    stall_pc = UInt(32),         # stall 时的 PC
)

class MemeoryAccess(Downstream):
    def __init__(self):
        super().__init__()
    @downstream.combinational
    def build(self,
              dcache: SRAM,
              data: Value,
              mem_read: Value,
              mem_write: Value,
              read_addr: Value,
              write_addr: Value,
              data_base: Value,
              ):
        # Upstream modules may not have produced values in the first few cycles,
        # so guard inputs with sensible defaults to avoid invalid reads.
        read_addr = read_addr.optional(default=UInt(32)(0))
        write_addr = write_addr.optional(default=UInt(32)(0))
        data = data.optional(default=UInt(32)(0))
        mem_write = mem_write.optional(default=Bits(1)(0))
        # data_base 是常量输入，不需要 optional 包装
        addr = mem_read.select(read_addr, write_addr)
        # 将地址转为数据段内偏移（默认 data_base=0x2000），再对齐到字地址
        word_addr = ((addr - data_base) >> UInt(32)(2)).bitcast(UInt(32))
        conflict = mem_read & mem_write
        with Condition(conflict):
            log("MEM conflict: mem_read & mem_write both asserted, read_addr=0x{:08x} write_addr=0x{:08x}", read_addr, write_addr)
            finish()
        dcache.build(
            we = mem_write,
            re = mem_read,
            addr = word_addr.bitcast(Bits(dcache.addr_width)),
            wdata = data.bitcast(Bits(32))
        )

class Issuer(Module):
    def __init__(self):
        super().__init__(
            ports={
                "pc_addr": Port(UInt(32))
            }
        )
    @module.combinational
    def build(self,
              icache: SRAM,
              ):
        pc_addr = self.pop_all_ports(True)
        instr = icache.dout[0]
        re = (pc_addr != UInt(32)(0)).select(Bits(1)(1), Bits(1)(1))
        return pc_addr, instr, re
class IsserImpl(Downstream):
    def __init__(self):
        super().__init__()
    @downstream.combinational
    def build(self,
              pc_addr: Value,
              instr: Value,
              re: Value,
              rob: ROB,
              rs: list[RSEntry],
              mul_rs: list[MUL_RSEntry],  # 乘法保留站（2个）
              lsq: LSQEntry,
              rat: RAT,  # 改用新的 RAT 类
              regs: RegArray,
              bht: BHT,  # 添加 BHT 参数
              cbd_signal):  # RecordValue
        re = re.optional(default=Bits(1)(0))
        pc_addr = pc_addr.optional(default=UInt(32)(0))
        instr = instr.optional(default=Bits(32)(0))
        
        # 默认输出值
        stall = Bits(1)(0)
        stall_pc = UInt(32)(0)
        predict_valid = Bits(1)(0)
        predict_target_pc = UInt(32)(0)
        jalr_stall = Bits(1)(0)
        
        cbd_payload = cbd_signal.value().optional(default=CBD_signal.bundle(
            ROB_idx=UInt(ROB_IDX_WIDTH)(0),
            rd_data=UInt(32)(0),
            valid=Bits(1)(0),
        ).value())
        cbd = CBD_signal.view(cbd_payload)
        
        decoder_result = decoder_logic(
            instr,
            reg_pending = rat,  # RAT 支持 [] 索引
            regs=regs,
            rob = rob,
            cbd = cbd,
        )
        is_mem = decoder_result.mem_read | decoder_result.mem_write
        is_mul = decoder_result.is_mul  # 乘法指令
        rs_busy = rs[0].busy[0]
        for i in range(1, RS_ENTRY_NUM):
            rs_busy = rs_busy & rs[i].busy[0]
        # 乘法 RS 全部繁忙才 stall
        mul_rs_busy = mul_rs[0].busy[0]
        for i in range(1, MUL_RS_NUM):
            mul_rs_busy = mul_rs_busy & mul_rs[i].busy[0]
        
        # 资源冲突 stall：根据指令类型检查对应的资源
        # 乘法指令 -> 检查 mul_rs
        # 内存指令 -> 检查 lsq
        # 其他 -> 检查 rs
        target_busy = is_mul.select(mul_rs_busy, is_mem.select(lsq.busy[0], rs_busy))
        resource_stall = (rob.is_full() | target_busy) & re
        stall = resource_stall
        
        # 分支预测信号：B/JAL 可以预测跳转，JALR 需要 stall
        # predict_target_pc = PC + imm (对于 B 和 JAL)
        branch_target = pc_addr + decoder_result.imm.bitcast(UInt(32))
        
        # 使用 BHT 预测条件分支
        # JAL 总是跳转，B类型使用 BHT 预测
        bht_prediction = bht.predict(pc_addr)  # BHT 预测结果
        is_B_branch = decoder_result.is_B & re & (~resource_stall)
        is_jal_branch = decoder_result.is_jal & re & (~resource_stall)
        
        # 只有在没有资源 stall 且是 predictable branch 时才预测
        # B 类型：BHT 预测跳转时才预测 taken
        # JAL：总是预测跳转
        predict_taken = is_jal_branch | (is_B_branch & bht_prediction)
        predict_valid = predict_taken
        predict_target_pc = branch_target
        
        # JALR 需要 stall（不预测）
        is_jalr_issue = decoder_result.is_jalr & re & (~resource_stall)
        jalr_stall = is_jalr_issue
        
        with Condition(re == Bits(1)(1)):
            log("issuer: pc=0x{:08x} instr=0x{:08x} is_mem={} stall={} predict_valid={} jalr_stall={} bht_pred={}", 
                pc_addr, instr, is_mem, stall, predict_valid, jalr_stall, bht_prediction)

            with Condition(~stall):
                rob_idx = rob.tail[0]
                next_tail = ((rob.tail[0] + UInt(ROB_IDX_WIDTH)(1)) & UInt(ROB_IDX_WIDTH)(ROB_MASK)).bitcast(UInt(ROB_IDX_WIDTH))
                rob.tail[0] <= next_tail
                rob._write_busy(rob_idx, Bits(1)(1))
                rob._write_ready(rob_idx, Bits(1)(0))
                rob.pc[rob_idx] <= pc_addr
                rob.dest[rob_idx] <= decoder_result.rd
                rob.value[rob_idx] <= UInt(32)(0)
                rob._write_is_branch(rob_idx, decoder_result.is_branch)
                rob._write_is_syscall(rob_idx, decoder_result.is_ecall | decoder_result.is_ebreak)
                rob._write_is_store(rob_idx, decoder_result.mem_write)
                rob._write_is_jalr(rob_idx, decoder_result.is_jalr)
                
                # 记录分支预测信息（使用 BHT 预测结果）
                # JAL：总是预测跳转
                # B 类型：使用 BHT 预测
                # JALR：不预测（predicted_taken = 0）
                rob._write_predicted_taken(rob_idx, predict_taken)
                rob.predicted_pc[rob_idx] <= branch_target

                # 生成源操作数的依赖信息，rat 用 0 表示无依赖，其余存 rob_idx+1
                # RAT 返回 Bits 类型，需要转换为 UInt 进行算术运算
                qj_raw = decoder_result.rs1_used.select(rat[decoder_result.rs1], Bits(REG_PENDING_WIDTH)(0)).bitcast(UInt(REG_PENDING_WIDTH))
                qk_raw = decoder_result.rs2_used.select(rat[decoder_result.rs2], Bits(REG_PENDING_WIDTH)(0)).bitcast(UInt(REG_PENDING_WIDTH))
                qj = (qj_raw != UInt(REG_PENDING_WIDTH)(0)).select(
                    (qj_raw - UInt(REG_PENDING_WIDTH)(1)).bitcast(Bits(REG_PENDING_WIDTH)),
                    Bits(REG_PENDING_WIDTH)(0)
                )
                qk = (qk_raw != UInt(REG_PENDING_WIDTH)(0)).select(
                    (qk_raw - UInt(REG_PENDING_WIDTH)(1)).bitcast(Bits(REG_PENDING_WIDTH)),
                    Bits(REG_PENDING_WIDTH)(0)
                )
                rs1_val = decoder_result.rs1_value
                rs2_val = decoder_result.rs2_value
                qj_valid = decoder_result.rs1_valid
                qk_valid = decoder_result.rs2_valid

                # 重命名表写入 rd（存 rob_idx+1，0 作为 sentinel）
                rat.write_if(
                    decoder_result.rd_used & (decoder_result.rd != Bits(5)(0)),
                    decoder_result.rd,
                    (rob_idx + UInt(ROB_IDX_WIDTH)(1)).bitcast(Bits(REG_PENDING_WIDTH))
                )

                with Condition(is_mem):
                    log("issuer -> LSQ: rob_idx={} rd={} rs1_dep={} rs2_dep={}", rob_idx, decoder_result.rd, qj, qk)
                    lsq.busy[0] <= Bits(1)(1)
                    lsq.is_load[0] <= decoder_result.mem_read
                    lsq.is_store[0] <= decoder_result.mem_write
                    lsq.rob_idx[0] <= rob_idx.zext(Bits(ROB_IDX_WIDTH))
                    lsq.rd[0] <= decoder_result.rd
                    lsq.qj[0] <= qj
                    lsq.qk[0] <= qk
                    lsq.qj_valid[0] <= qj_valid
                    lsq.qk_valid[0] <= qk_valid
                    lsq.vj[0] <= rs1_val
                    lsq.vk[0] <= rs2_val
                    lsq.rs2_id[0] <= decoder_result.rs2
                    lsq.imm[0] <= decoder_result.imm.bitcast(UInt(32))
                with Condition(~is_mem & ~is_mul):
                    # 非内存、非乘法指令 -> 发送到 ALU RS
                    RS_select = Bits(RS_NUM_WIDTH)(RS_MAX)
                    for i in range(RS_ENTRY_NUM):
                        RS_select = (rs[i].busy[0]).select(RS_select, Bits(RS_NUM_WIDTH)(i))
                    with Condition(RS_select == Bits(RS_NUM_WIDTH)(RS_MAX)):
                        log("issuer error: no free RS found")
                        finish()
                    log("select RS idx = {}", RS_select)
                    log("issuer -> RS: rob_idx={} rd={} rs1_dep={} rs2_dep={}", rob_idx, decoder_result.rd, qj, qk)
                    for i in range(RS_ENTRY_NUM):
                        with Condition(RS_select == Bits(RS_NUM_WIDTH)(i)):
                            rs[i].busy[0] <= Bits(1)(1)
                            rs[i].op[0] <= decoder_result.alu_type
                            op1_val = rs1_val
                            op2_val = decoder_result.rs2_used.select(
                                rs2_val,
                                decoder_result.imm.bitcast(UInt(32))
                            )
                            op1_val = decoder_result.is_lui.select(UInt(32)(0),
                                        decoder_result.is_auipc.select(pc_addr, op1_val))
                            rs[i].vj[0] <= op1_val
                            op2_val = decoder_result.rs2_used.select(
                                rs2_val,
                                decoder_result.imm.bitcast(UInt(32))
                            )
                            rs[i].vk[0] <= op2_val
                            rs[i].qj[0] <= qj
                            rs[i].qk[0] <= qk
                            rs[i].qj_valid[0] <= qj_valid
                            rs[i].qk_valid[0] <= qk_valid
                            rs[i].rd[0] <= decoder_result.rd
                            rs[i].rob_idx[0] <= rob_idx.zext(Bits(ROB_IDX_WIDTH))
                            rs[i].imm[0] <= decoder_result.imm.bitcast(UInt(32))
                            rs[i].is_branch[0] <= decoder_result.is_branch
                            rs[i].is_B[0] <= decoder_result.is_B  # 条件分支 B 类型
                            rs[i].is_jal[0] <= decoder_result.is_jal
                            rs[i].is_jalr[0] <= decoder_result.is_jalr
                            rs[i].is_lui[0] <= decoder_result.is_lui
                            rs[i].is_auipc[0] <= decoder_result.is_auipc
                            rs[i].pc_addr[0] <= pc_addr
                            rs[i].is_syscall[0] <= decoder_result.is_ecall | decoder_result.is_ebreak

                with Condition(is_mul):
                    # 乘法指令 -> 发送到 MUL_RS（选择空闲的 RS entry）
                    MUL_RS_select = Bits(2)(MUL_RS_NUM)  # 默认无效值
                    for i in range(MUL_RS_NUM):
                        MUL_RS_select = (mul_rs[i].busy[0]).select(MUL_RS_select, Bits(2)(i))
                    log("issuer -> MUL_RS[{}]: rob_idx={} rd={} rs1_dep={} rs2_dep={}", 
                        MUL_RS_select, rob_idx, decoder_result.rd, qj, qk)
                    for i in range(MUL_RS_NUM):
                        with Condition(MUL_RS_select == Bits(2)(i)):
                            mul_rs[i].busy[0] <= Bits(1)(1)
                            mul_rs[i].op[0] <= decoder_result.alu_type
                            mul_rs[i].vj[0] <= rs1_val
                            mul_rs[i].vk[0] <= rs2_val
                            mul_rs[i].qj[0] <= qj
                            mul_rs[i].qk[0] <= qk
                            mul_rs[i].qj_valid[0] <= qj_valid
                            mul_rs[i].qk_valid[0] <= qk_valid
                            mul_rs[i].rd[0] <= decoder_result.rd
                            mul_rs[i].rob_idx[0] <= rob_idx.zext(Bits(ROB_IDX_WIDTH))

            stall_pc = pc_addr
        
        return IssueControl_signal.bundle(
            predict_valid = predict_valid,
            predict_target_pc = predict_target_pc,
            jalr_stall = jalr_stall,
            stall = stall,
            stall_pc = stall_pc,
        )

class Fetcher(Module):
    def __init__(self):
        super().__init__(
            ports={}
        )
    @module.combinational
    def build(self):
        pc_reg = RegArray(UInt(32), 1, initializer=[0])
        pc_addr = pc_reg[0]
        return pc_reg, pc_addr


class FetchControl(Downstream):
    """
    统一的取指控制 Downstream
    整合来自 Issue 和 CDB 的所有控制信号，同周期传递给 Fetcher
    
    优先级（从高到低）：
    1. flush (mispredicted): 预测错误，跳转到 correct_pc
    2. jalr_resolved: JALR 执行完成，跳转到计算出的地址
    3. jalr_stall: 遇到 JALR，暂停取指
    4. predict_valid: B/JAL 预测跳转
    5. stall: 资源冲突 stall
    6. normal: PC + 4
    """
    def __init__(self):
        super().__init__()
    
    @downstream.combinational
    def build(self,
              issue_ctrl,      # IssueControl_signal RecordValue
              branch_ctrl,     # BranchControl_signal RecordValue
              ):
        # Issue 控制信号 - 使用 .value().optional() 模式
        issue_payload = issue_ctrl.value().optional(default=IssueControl_signal.bundle(
            predict_valid = Bits(1)(0),
            predict_target_pc = UInt(32)(0),
            jalr_stall = Bits(1)(0),
            stall = Bits(1)(0),
            stall_pc = UInt(32)(0),
        ).value())
        issue = IssueControl_signal.view(issue_payload)
        
        # Branch 控制信号
        branch_payload = branch_ctrl.value().optional(default=BranchControl_signal.bundle(
            jalr_resolved = Bits(1)(0),
            jalr_target_pc = UInt(32)(0),
            mispredicted = Bits(1)(0),
            correct_pc = UInt(32)(0),
        ).value())
        branch = BranchControl_signal.view(branch_payload)
        
        # 计算最终的控制信号
        # 优先级：flush > jalr_resolved > jalr_stall > predict > stall > normal
        
        # 最终输出
        do_flush = branch.mispredicted
        do_jalr_resume = branch.jalr_resolved & (~do_flush)
        do_jalr_stall = issue.jalr_stall & (~do_flush) & (~do_jalr_resume)
        do_predict = issue.predict_valid & (~do_flush) & (~do_jalr_resume) & (~do_jalr_stall)
        do_stall = issue.stall & (~do_flush) & (~do_jalr_resume) & (~do_jalr_stall) & (~do_predict)
        
        # 目标 PC
        target_pc = do_flush.select(branch.correct_pc,
                    do_jalr_resume.select(branch.jalr_target_pc,
                    do_predict.select(issue.predict_target_pc,
                    issue.stall_pc)))  # stall 时保持当前 PC
        
        # 是否停止取指
        stop_fetch = do_jalr_stall
        
        # 是否重新启动取指（从停止状态恢复）
        restart_fetch = do_flush | do_jalr_resume
        
        # 是否跳转（不是 PC+4）
        do_jump = do_flush | do_jalr_resume | do_predict
        
        log("FetchCtrl: flush={} jalr_resume={} jalr_stall={} predict={} stall={} target=0x{:08x}",
            do_flush, do_jalr_resume, do_jalr_stall, do_predict, do_stall, target_pc)
        
        return do_flush, do_stall, do_jalr_stall, do_predict, do_jump, restart_fetch, target_pc, issue.stall_pc


class FetcherImpl(Downstream):
    def __init__(self):
        super().__init__()
    @downstream.combinational
    def build(self,
            icache: SRAM,
            pc_reg: RegArray,
            pc_addr: Value,
            # FetchControl 的输出
            do_flush: Value,
            do_stall: Value,
            do_jalr_stall: Value,
            do_predict: Value,
            do_jump: Value,
            restart_fetch: Value,
            target_pc: Value,
            stall_pc: Value,
            issuer: Issuer):
        
        # 设置默认值
        do_flush = do_flush.optional(default=Bits(1)(0))
        do_stall = do_stall.optional(default=Bits(1)(0))
        do_jalr_stall = do_jalr_stall.optional(default=Bits(1)(0))
        do_predict = do_predict.optional(default=Bits(1)(0))
        do_jump = do_jump.optional(default=Bits(1)(0))
        restart_fetch = restart_fetch.optional(default=Bits(1)(0))
        target_pc = target_pc.optional(default=UInt(32)(0))
        stall_pc = stall_pc.optional(default=UInt(32)(0))
        pc_addr = pc_addr.optional(default=UInt(32)(0))
        
        # 取指使能寄存器：跟踪是否处于停止状态
        re_reg = RegArray(Bits(1), 1, initializer=[1])
        
        # 判断是否从停止状态恢复
        was_stopped = ~re_reg[0]
        resume_from_stop = was_stopped & restart_fetch
        
        # 计算最终的取指 PC
        # 1. flush/jalr_resume: 跳转到 target_pc
        # 2. predict: 跳转到预测目标
        # 3. stall: 保持 stall_pc
        # 4. normal: 使用当前 pc_addr
        fetch_pc = do_stall.select(stall_pc,
                   do_jump.select(target_pc,
                   resume_from_stop.select(target_pc, pc_addr)))
        
        # 计算取指使能
        # 停止条件：jalr_stall（且不是在恢复）
        # 恢复条件：restart_fetch
        re = do_stall.select(Bits(1)(1),  # stall 时继续取同一条
             restart_fetch.select(Bits(1)(1),  # 恢复时开始取指
             do_jalr_stall.select(Bits(1)(0),  # jalr_stall 时停止
             re_reg[0])))  # 否则保持之前状态
        
        re_reg[0] <= re
        
        # 构建 icache 访问
        word_addr = (fetch_pc >> UInt(32)(2)).bitcast(UInt(32))
        icache.build(we = Bits(1)(0),
                     re = re,
                     addr = word_addr.bitcast(Bits(icache.addr_width)),
                     wdata = Bits(32)(0))
        
        log("fetcherimpl: fetch_pc=0x{:08x} do_stall={} do_jump={} restart={} re={}", 
            fetch_pc, do_stall, do_jump, restart_fetch, re)
        
        with Condition(re == Bits(1)(1)):
            # 更新 PC 寄存器
            next_pc = do_jump.select(target_pc + UInt(32)(4), fetch_pc + UInt(32)(4))
            pc_reg[0] <= next_pc
            # 将当前 PC 传递给 issuer
            issuer.async_called(pc_addr=fetch_pc)


class Driver(Module):
    def __init__(self):
        super().__init__(
            ports={}
        )
    @module.combinational
    def build(self, fetcher : Fetcher, committer : Commiter):
        is_init = RegArray(UInt(1), 1, initializer=[1])
        tick_reg = RegArray(UInt(8), 1, initializer=[0])
        with Condition(is_init[0] == UInt(1)(1)):
            is_init[0] <= UInt(1)(0)
            fetcher.async_called()
            committer.async_called()
            log("CPU Simulation Started")
        with Condition(is_init[0] == UInt(1)(0)):
            fetcher.async_called()
        committer.async_called()
        # heartbeat 翻转，驱动 CDB 下游每周期触发
        tick_reg[0] <= tick_reg[0] + UInt(8)(1)
        return tick_reg[0]


class FlushControl(Downstream):
    """
    Flush 控制 Downstream
    当检测到预测错误时，清理流水线状态
    """
    def __init__(self):
        super().__init__()
    
    @downstream.combinational
    def build(self,
              do_flush: Value,
              rat: RAT,
              rob: ROB,
              rs: list[RSEntry],
              mul_rs: list[MUL_RSEntry],  # 乘法保留站（2个）
              lsq: LSQEntry,
              metadata: Value):
        do_flush = do_flush.optional(default=Bits(1)(0))
        metadata = metadata.optional(default=UInt(8)(0))
        _ = metadata == metadata  # 确保每周期触发
        
        with Condition(do_flush):
            log("FLUSH: Misprediction detected! Clearing pipeline...")
            # 1. 清空 RAT
            rat.flush_all()
            
            # 2. 清空 ROB（重置指针，清空状态）
            rob.flush()
            
            # 3. 清空所有 RS
            for i in range(RS_ENTRY_NUM):
                rs[i].busy[0] <= Bits(1)(0)
                rs[i].fired[0] <= Bits(1)(0)
                rs[i].qj_valid[0] <= Bits(1)(0)
                rs[i].qk_valid[0] <= Bits(1)(0)
            
            # 4. 清空所有 MUL_RS
            for i in range(MUL_RS_NUM):
                mul_rs[i].busy[0] <= Bits(1)(0)
                mul_rs[i].fired[0] <= Bits(1)(0)
                mul_rs[i].qj_valid[0] <= Bits(1)(0)
                mul_rs[i].qk_valid[0] <= Bits(1)(0)
            
            # 5. 清空 LSQ
            lsq.busy[0] <= Bits(1)(0)
            lsq.fired[0] <= Bits(1)(0)
            lsq.qj_valid[0] <= Bits(1)(0)
            lsq.qk_valid[0] <= Bits(1)(0)


current_path = os.path.dirname(os.path.abspath(__file__))
workspace = f'{current_path}/workspace/'

def build_CPU(depth_log=18, data_base=0x2000):
    sys = SysBuilder("CPU")
    with sys:
        icache = SRAM(width= 32,
                      depth= 1 << depth_log,
                      init_file= f"{workspace}/workload.exe")
        icache.name = "icache"
        dcache = SRAM(width= 32,
                      depth= 1 << depth_log,
                      init_file= f"{workspace}/data.mem")
        dcache.name = "dcache"
        
        regs = RegArray(UInt(32), 32, initializer=[0]*32)
        # 使用新的 RAT 类（32个独立RegArray）
        rat = RAT()
        # 使用 BHT 进行分支预测（64条目，2-bit饱和计数器）
        bht = BHT()

        fetcher = Fetcher()
        issuer = Issuer()
        issueimpl = IsserImpl()
        driver = Driver()
        rs = [RSEntry() for _ in range(RS_ENTRY_NUM)]
        rs_downstream = [RS_downstream() for _ in range(RS_ENTRY_NUM)]
        alu = [ALU() for _ in range(RS_ENTRY_NUM)]
        
        # 乘法器及其保留站（2个 RS entry）
        mul_rs = [MUL_RSEntry() for _ in range(MUL_RS_NUM)]
        mul_rs_downstream = [MUL_RS_downstream(rs_idx=i) for i in range(MUL_RS_NUM)]
        mul_regs = MultiplierRegs()  # 共享寄存器
        multiplier_state = MultiplierState()
        
        rob = ROB()
        lsq = LSQEntry()
        lsq_downstream = LSQ_downstream()
        lsu = LSU()
        mem_access = MemeoryAccess()
        cdb_arbitrator = CDB_Arbitrator()
        committer = Commiter()
        fetcherimpl = FetcherImpl()
        fetch_control = FetchControl()
        flush_control = FlushControl()

        # 构建各模块
        pc_reg, pc_addr = fetcher.build()
        mem_we, mem_addr, mem_data = committer.build(
            rob = rob,
            regs = regs,
            rat = rat,  # 传入 RAT 对象
        )

        lsu_cbd_signal = lsu.build(dcache=dcache)
        alu_cbd_signal_list = []
        for i in range(RS_ENTRY_NUM):
            alu_cbd_signal_list.append(alu[i].build())
        
        metadata = driver.build(
            fetcher=fetcher,
            committer=committer,
        )
        
        # 乘法器状态机（每周期执行，处理倒计时和 ROB 写入）
        mul_rob_idx, mul_rd_data, mul_is_done = multiplier_state.build(
            mul_regs=mul_regs,
            rob=rob,
            metadata=metadata,
        )
        
        # CDB Arbitrator 现在返回 CBD_signal 和 BranchControl_signal
        # 同时负责更新 BHT（乘法器不经过 CDB，在单独的 downstream 处理）
        cbd_signal, branch_ctrl = cdb_arbitrator.build(
            LSU_CBD_req=lsu_cbd_signal,
            ALU_CBD_req=alu_cbd_signal_list,
            rob=rob,
            bht=bht,  # 传入 BHT 用于更新
            metadata=metadata,
        )
        
        issue_pc_addr, instr, re = issuer.build(icache=icache)
        
        # Issue 产生预测控制信号（使用 BHT 预测）
        issue_ctrl = issueimpl.build(
            pc_addr=issue_pc_addr,
            instr=instr,
            re=re,
            rob=rob,
            rs=rs,
            mul_rs=mul_rs,  # 添加乘法保留站
            lsq=lsq,
            rat=rat,
            regs=regs,
            bht=bht,  # 传入 BHT 用于预测
            cbd_signal=cbd_signal,
        )
        
        # FetchControl 整合所有控制信号
        do_flush, do_stall, do_jalr_stall, do_predict, do_jump, restart_fetch, target_pc, stall_pc = fetch_control.build(
            issue_ctrl=issue_ctrl,
            branch_ctrl=branch_ctrl,
        )
        
        # FlushControl 处理 flush 时的清理
        flush_control.build(
            do_flush=do_flush,
            rat=rat,
            rob=rob,
            rs=rs,
            mul_rs=mul_rs,  # 添加乘法保留站
            lsq=lsq,
            metadata=metadata,
        )
        
        # LSQ downstream
        lsq_re, read_addr = lsq_downstream.build(
            lsq=lsq,
            cbd_signal=cbd_signal,
            lsu=lsu,
            rob=rob,
            regs=regs,
            issue_stall=do_stall,
            metadata=metadata,
        )
        
        # RS downstreams
        for i in range(RS_ENTRY_NUM):
            rs_downstream[i].build(
                rs=rs[i],
                alu=alu[i],
                cbd_signal=cbd_signal,
                mul_broadcast=(mul_rob_idx, mul_rd_data, mul_is_done),
                issue_stall=do_stall,
                metadata=metadata,
            )
        
        # MUL_RS downstream - 监听 CDB 更新操作数
        # 传递 mul 信号用于 RS 更新（当乘法完成时，其他等待该结果的 RS 需要更新）
        for i in range(MUL_RS_NUM):
            mul_rs_downstream[i].build(
                rs=mul_rs[i],
                mul_regs=mul_regs,  # 乘法器共享寄存器
                cbd_signal=cbd_signal,
                mul_broadcast=(mul_rob_idx, mul_rd_data, mul_is_done),
                metadata=metadata,
            )

        # Memory access
        mem_access.build(
            dcache=dcache,
            data=mem_data,
            mem_read=lsq_re,
            mem_write=mem_we,
            read_addr=read_addr,
            write_addr=mem_addr,
            data_base=UInt(32)(data_base),
        )
        
        # FetcherImpl 使用新的控制信号
        fetcherimpl.build(
            icache=icache,
            pc_reg=pc_reg,
            pc_addr=pc_addr,
            do_flush=do_flush,
            do_stall=do_stall,
            do_jalr_stall=do_jalr_stall,
            do_predict=do_predict,
            do_jump=do_jump,
            restart_fetch=restart_fetch,
            target_pc=target_pc,
            stall_pc=stall_pc,
            issuer=issuer,
        )
    return sys

def main():
    import argparse

    # --sim-threshold 100 --idle-threshold 100 设置模拟器参数
    parser = argparse.ArgumentParser(description="Run CPU simulator")
    parser.add_argument("--sim-threshold", type=int, default=100, help="max simulation steps")
    parser.add_argument("--idle-threshold", type=int, default=100, help="idle cycles before stop")
    parser.add_argument("--data-base", type=lambda x: int(x, 0), default=0x2000, 
                        help="data segment base address (default: 0x2000)")
    parser.add_argument("--no-verilator", action="store_true", help="skip running verilator")
    args = parser.parse_args()

    print(f"Config: data_base=0x{args.data_base:x}, sim_threshold={args.sim_threshold}, idle_threshold={args.idle_threshold}")

    sys = build_CPU(depth_log = 18, data_base=args.data_base)
    cfg = backend.config(
        resource_base='.',
        verilog=True,
        verbose=True,
        sim_threshold=args.sim_threshold,
        idle_threshold=args.idle_threshold,
    )
    sim,vcd = elaborate(sys=sys, **cfg)
    output = run_simulator(sim)
    print("simulate output is written in /workspace/log")
    with open(f"{workspace}/log", "w") as f:
        print(output, file = f)
    if not args.no_verilator:
        try:
            ver_output = run_verilator(vcd)
            print("verilator output is written in /workspace/verilator_log")
            with open(f"{workspace}/verilator_log", "w") as f:
                print(ver_output, file = f)
        except Exception as e:
            print("warning: running verilator failed:", e)

if __name__ == "__main__":
    main()

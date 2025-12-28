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

ROB_MASK = (1 << ROB_IDX_WIDTH) - 1

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
              lsq: LSQEntry,
              reg_pending: RegArray,
              regs: RegArray,
              cbd_signal: Value):
        re = re.optional(default=Bits(1)(0))
        pc_addr = pc_addr.optional(default=UInt(32)(0))
        instr = instr.optional(default=Bits(32)(0))
        # 默认保持不阻塞，只有在 re 有效且分析出冲突时才更新
        stall = Bits(1)(0)
        stall_pc = UInt(32)(0)
        stop_signal = Bits(1)(0)
        cbd_payload = cbd_signal.value().optional(default=CBD_signal.bundle(
            ROB_idx=UInt(4)(0),
            rd_data=UInt(32)(0),
            valid=Bits(1)(0),
        ).value())
        cbd = CBD_signal.view(cbd_payload)
        
        decoder_result = decoder_logic(
            instr,
            reg_pending = reg_pending,
            regs=regs,
            rob = rob,
            cbd = cbd,
        )
        is_mem = decoder_result.mem_read | decoder_result.mem_write
        rs_busy = rs[0].busy[0]
        for i in range(1, RS_ENTRY_NUM):
            rs_busy = rs_busy & rs[i].busy[0]
        stall = (rob.is_full() | is_mem.select(lsq.busy[0], rs_busy)) & re
        stop_signal = (~stall & decoder_result.is_branch) & re
        with Condition(re == Bits(1)(1)):
            log("issuer: pc=0x{:08x} instr=0x{:08x} is_mem={} stall={}", pc_addr, instr, is_mem, stall)

            with Condition(~stall):
                rob_idx = rob.tail[0]
                next_tail = ((rob.tail[0] + UInt(ROB_IDX_WIDTH)(1)) & UInt(ROB_IDX_WIDTH)(ROB_MASK)).bitcast(UInt(ROB_IDX_WIDTH))
                rob.tail[0] <= next_tail
                rob.busy[rob_idx] <= Bits(1)(1)
                rob.ready[rob_idx] <= Bits(1)(0)
                rob.pc[rob_idx] <= pc_addr
                rob.dest[rob_idx] <= decoder_result.rd
                rob.value[rob_idx] <= UInt(32)(0)
                rob.is_branch[rob_idx] <= decoder_result.is_branch
                rob.is_syscall[rob_idx] <= decoder_result.is_ecall | decoder_result.is_ebreak
                rob.is_store[rob_idx] <= decoder_result.mem_write

                # 生成源操作数的依赖信息，reg_pending 用 0 表示无依赖，其余存 rob_idx+1
                # decoder 已经旁路 CDB/ROB/寄存器，这里只做 tag/valid 封装
                qj_raw = decoder_result.rs1_used.select(reg_pending[decoder_result.rs1], Bits(REG_PENDING_WIDTH)(0))
                qk_raw = decoder_result.rs2_used.select(reg_pending[decoder_result.rs2], Bits(REG_PENDING_WIDTH)(0))
                # 只有 reg_pending 非 0 时才减 1，避免 0-1 下溢变成 0xff 传给 LSQ/RS
                qj = (qj_raw != Bits(REG_PENDING_WIDTH)(0)).select(
                    (qj_raw - Bits(REG_PENDING_WIDTH)(1)).bitcast(Bits(REG_PENDING_WIDTH)),
                    Bits(REG_PENDING_WIDTH)(0)
                )
                qk = (qk_raw != Bits(REG_PENDING_WIDTH)(0)).select(
                    (qk_raw - Bits(REG_PENDING_WIDTH)(1)).bitcast(Bits(REG_PENDING_WIDTH)),
                    Bits(REG_PENDING_WIDTH)(0)
                )
                rs1_val = decoder_result.rs1_value
                rs2_val = decoder_result.rs2_value
                qj_valid = decoder_result.rs1_valid
                qk_valid = decoder_result.rs2_valid

                # 重命名表写入 rd（存 rob_idx+1，0 作为 sentinel）
                with Condition(decoder_result.rd_used & (decoder_result.rd != Bits(5)(0))):
                    reg_pending[decoder_result.rd] <= (rob_idx + UInt(ROB_IDX_WIDTH)(1)).bitcast(Bits(REG_PENDING_WIDTH))

                with Condition(is_mem):
                    # LSQ 入口
                    log("issuer -> LSQ: rob_idx={} rd={} rs1_dep={} rs2_dep={}", rob_idx, decoder_result.rd, qj, qk)
                    lsq.busy[0] <= Bits(1)(1)
                    lsq.is_load[0] <= decoder_result.mem_read
                    lsq.is_store[0] <= decoder_result.mem_write
                    lsq.rob_idx[0] <= rob_idx.zext(Bits(4))
                    lsq.rd[0] <= decoder_result.rd
                    lsq.qj[0] <= qj
                    lsq.qk[0] <= qk
                    lsq.qj_valid[0] <= qj_valid
                    lsq.qk_valid[0] <= qk_valid
                    lsq.vj[0] <= rs1_val
                    lsq.vk[0] <= rs2_val
                    lsq.rs2_id[0] <= decoder_result.rs2
                    lsq.imm[0] <= decoder_result.imm.bitcast(UInt(32))
                with Condition(~is_mem):
                    RS_select = Bits(RS_NUM_WIDTH)(RS_MAX) # 不存在的初始值
                    for i in range(RS_ENTRY_NUM):
                        RS_select = (rs[i].busy[0]).select(RS_select, Bits(RS_NUM_WIDTH)(i))
                    with Condition(RS_select == Bits(RS_NUM_WIDTH)(RS_MAX)):
                        log("issuer error: no free RS found")
                        finish()
                    # RS 入口
                    log("select RS idx = {}", RS_select)
                    log("issuer -> RS: rob_idx={} rd={} rs1_dep={} rs2_dep={}", rob_idx, decoder_result.rd, qj, qk)
                    for i in range(RS_ENTRY_NUM):
                        with Condition(RS_select == Bits(RS_NUM_WIDTH)(i)):
                            rs[i].busy[0] <= Bits(1)(1)
                            rs[i].op[0] <= decoder_result.alu_type
                            # op1/op2 特殊处理：LUI 用 0+imm，AUIPC 用 pc+imm，其余保持 rs1/rs2 或 imm
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
                            rs[i].rob_idx[0] <= rob_idx.zext(Bits(4))
                            rs[i].imm[0] <= decoder_result.imm.bitcast(UInt(32))
                            rs[i].is_branch[0] <= decoder_result.is_branch
                            rs[i].is_jal[0] <= decoder_result.is_jal
                            rs[i].is_jalr[0] <= decoder_result.is_jalr
                            rs[i].is_lui[0] <= decoder_result.is_lui
                            rs[i].is_auipc[0] <= decoder_result.is_auipc
                            rs[i].pc_addr[0] <= pc_addr
                            rs[i].is_syscall[0] <= decoder_result.is_ecall | decoder_result.is_ebreak

            # 输出给 fetcherimpl 的握手/停顿信号
            stall_pc = pc_addr
            # 分支指令发射后暂停取指，等待 ALU 计算出跳转目标再由 start_signal 重新启动
        # re 为 0 时直接保持默认值 0；只有 re 为 1 时上面的 Condition 会覆盖
        return stall, stall_pc, stop_signal

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

class FetcherImpl(Downstream):
    def __init__(self):
        super().__init__()
    @downstream.combinational
    def build(self,
            icache: SRAM,
            pc_reg: RegArray,
            pc_addr: Value,
            stall: Value,
            stall_pc: Value,
            stop_signal: Value,
            start_signal: Value,
            target_pc: Value,
            issuer: Issuer):
        stall = stall.optional(default=Bits(1)(0))
        stall_pc = stall_pc.optional(default=UInt(32)(0))
        stop_signal = stop_signal.optional(default=Bits(1)(0))
        pc_addr = pc_addr.optional(default=UInt(32)(0))
        start_signal = start_signal.optional(default=Bits(1)(0))
        target_pc = target_pc.optional(default=UInt(32)(0))
        re_reg = RegArray(Bits(1), 1, initializer=[1])
        start_effective = start_signal & (~re_reg[0])  # 只在 re_reg 处于停住状态时响应 start
        fetch_pc = stall.select(stall_pc,
                                   start_effective.select(target_pc, pc_addr))
        re = stall.select(
            Bits(1)(1),
            start_effective.select(Bits(1)(1),
            stop_signal.select(
                Bits(1)(0), re_reg[0]
            )
        ))
        re_reg[0] <= re
        word_addr = (fetch_pc >> UInt(32)(2)).bitcast(UInt(32))
        icache.build(we = Bits(1)(0),
                     re = re,
                     addr = word_addr.bitcast(Bits(icache.addr_width)),
                     wdata = Bits(32)(0))
        log("fetcherimpl: fetch_pc=0x{:08x} stall={} start={} target=0x{:08x} re={}", fetch_pc, stall, start_signal, target_pc, re)
        with Condition(re == Bits(1)(1)):
            pc_reg[0] <= fetch_pc + UInt(32)(4)
            # 将当前 PC 传递给 issuer
            issuer.async_called(pc_addr=fetch_pc)


class Driver(Module):
    def __init__(self):
        super().__init__(
            ports={}
        )
    @module.combinational
    def build(self, fecher : Fetcher, committer : Commiter):
        is_init = RegArray(UInt(1), 1, initializer=[1])
        tick_reg = RegArray(Bits(8), 1, initializer=[0])
        with Condition(is_init[0] == UInt(1)(1)):
            is_init[0] <= UInt(1)(0)
            fecher.async_called()
            committer.async_called()
            log("CPU Simulation Started")
        with Condition(is_init[0] == UInt(1)(0)):
            fecher.async_called()
        committer.async_called()
        # heartbeat 翻转，驱动 CDB 下游每周期触发
        tick_reg[0] <= tick_reg[0] + Bits(8)(1)
        return tick_reg[0]


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
        reg_pending = RegArray(Bits(REG_PENDING_WIDTH), 32, initializer=[0]*32)

        
        fetcher = Fetcher()
        issuer = Issuer()
        issueimpl = IsserImpl()
        driver = Driver()
        rs = [RSEntry() for _ in range(RS_ENTRY_NUM)]
        rs_downstream = [RS_downstream() for _ in range(RS_ENTRY_NUM)]
        alu = [ALU() for _ in range(RS_ENTRY_NUM)]
        rob = ROB()
        lsq = LSQEntry()
        lsq_downstream = LSQ_downstream()
        lsu = LSU()
        mem_access = MemeoryAccess()
        cdb_arbitrator = CDB_Arbitrator()
        committer = Commiter()

        fetcherimpl = FetcherImpl()


        pc_reg, pc_addr = fetcher.build()
        mem_we, mem_addr, mem_data = committer.build(
            rob = rob,
            regs = regs,
            reg_pending = reg_pending,
        )

        lsu_cbd_signal = lsu.build(dcache=dcache)
        alu_cbd_signal_list = []
        for i in range(RS_ENTRY_NUM):
            alu_cbd_signal_list.append(alu[i].build())
        
        metadata = driver.build(
            fecher=fetcher,
            committer=committer,
        )
        
        cbd_signal, start_signal, target_pc = cdb_arbitrator.build(
            LSU_CBD_req=lsu_cbd_signal,
            ALU_CBD_req=alu_cbd_signal_list,
            rob=rob,
            metadata=metadata,
        )
        issue_pc_addr, instr, re = issuer.build(icache=icache)
        stall, stall_pc, stop_signal = issueimpl.build(
            pc_addr=issue_pc_addr,
            instr=instr,
            re=re,
            rob=rob,
            rs=rs,
            lsq=lsq,
            reg_pending=reg_pending,
            regs=regs,
            cbd_signal=cbd_signal,
        )
        re, read_addr = lsq_downstream.build(
            lsq=lsq,
            cbd_signal=cbd_signal,
            lsu=lsu,
            rob=rob,
            regs=regs,
            issue_stall=stall,
            metadata=metadata,
        )
        for i in range(RS_ENTRY_NUM):
            rs_downstream[i].build(
                rs=rs[i],
                alu=alu[i],
                cbd_signal=cbd_signal,
                issue_stall=stall,
                metadata=metadata,
            )
        mem_access.build(
            dcache=dcache,
            data=mem_data,
            mem_read=re,
            mem_write=mem_we,
            read_addr=read_addr,
            write_addr=mem_addr,
            data_base=UInt(32)(data_base),
        )
        
        fetcherimpl.build(
            icache=icache,
            pc_reg=pc_reg,
            pc_addr=pc_addr,
            stall=stall,
            stall_pc=stall_pc,
            stop_signal=stop_signal,
            start_signal=start_signal,
            target_pc=target_pc,
            issuer=issuer
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
    # ver_output = run_verilator(vcd)
    # print("verilator output is written in /workspace/verilator_log")
    # with open(f"{workspace}/verilator_log", "w") as f:
    #     print(ver_output, file = f)

if __name__ == "__main__":
    main()

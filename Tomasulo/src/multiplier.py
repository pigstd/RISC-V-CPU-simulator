"""
乘法器模块 - Tomasulo CPU 的 M 扩展实现

非流水线版本：乘法器 busy 期间不接受新请求，需要 4 个周期完成一次乘法
"""
from assassyn.frontend import *
try:
    from .instruction import RV32I_ALU
    from .signals import MUL_CBD_signal
    from .ROB import ROB_IDX_WIDTH, REG_PENDING_WIDTH
except ImportError:
    from Tomasulo.src.instruction import RV32I_ALU
    from Tomasulo.src.signals import MUL_CBD_signal
    from Tomasulo.src.ROB import ROB_IDX_WIDTH, REG_PENDING_WIDTH

# 乘法器周期数
MUL_LATENCY = 4

# 乘法保留站数量
MUL_RS_NUM = 2

# 乘法器输入信号
MUL_signal = Record(
    op1_val = UInt(32),    # 操作数 1
    op2_val = UInt(32),    # 操作数 2
    alu_type = Bits(RV32I_ALU.CNT),  # 乘法类型 (MUL/MULH/MULHSU/MULHU)
    ROB_idx = UInt(ROB_IDX_WIDTH),     # ROB 索引
)


class MultiplierRegs:
    """乘法器的共享状态寄存器"""
    def __init__(self):
        self.cycle_cnt = RegArray(UInt(4), 1, initializer=[0])  # 倒计时器
        self.op1 = RegArray(UInt(32), 1, initializer=[0])   # 操作数 1
        self.op2 = RegArray(UInt(32), 1, initializer=[0])   # 操作数 2
        self.alu_type = RegArray(Bits(RV32I_ALU.CNT), 1, initializer=[0])  # 乘法类型
        self.rob_idx = RegArray(UInt(ROB_IDX_WIDTH), 1, initializer=[0])  # ROB 索引
        self.pending = RegArray(Bits(1), 1, initializer=[0])  # 是否有待处理的请求


class MultiplierState(Downstream):
    """
    乘法器状态机（Downstream - 每周期执行）
    
    状态机：
    - cycle_cnt = 0: IDLE，可以接受新请求
    - cycle_cnt > 0: BUSY，正在计算，不接受新请求
    
    当 cycle_cnt 从 MUL_LATENCY 减到 1 时，输出结果并直接写入 ROB
    """
    
    def __init__(self):
        super().__init__()
    
    @downstream.combinational
    def build(self, mul_regs: MultiplierRegs, rob, metadata):
        """
        mul_regs: 乘法器的共享寄存器
        rob: ROB 实例
        metadata: Driver 的 tick
        """
        metadata = metadata.optional(default=UInt(8)(0))
        _ = metadata == metadata  # 确保每周期触发
        
        # 读取状态
        cycle_cnt = mul_regs.cycle_cnt[0]
        op1 = mul_regs.op1[0]
        op2 = mul_regs.op2[0]
        rob_idx = mul_regs.rob_idx[0]
        pending = mul_regs.pending[0]
        
        # 当前状态
        is_idle = (cycle_cnt == UInt(4)(0))
        is_done = (cycle_cnt == UInt(4)(1))
        is_busy = ~is_idle & ~is_done
        
        # 计算乘法结果
        mul_result = (op1 * op2).bitcast(UInt(32))
        
        log("MulState: idle={} done={} busy={} cnt={} pending={} op1=0x{:08x} op2=0x{:08x} result=0x{:08x} rob_idx={}",
            is_idle, is_done, is_busy, cycle_cnt, pending, op1, op2, mul_result, rob_idx)
        
        # 状态转移
        # IDLE 且有待处理请求时，开始计数
        with Condition(is_idle & pending):
            mul_regs.cycle_cnt[0] <= UInt(4)(MUL_LATENCY)
            mul_regs.pending[0] <= Bits(1)(0)  # 清除 pending
            log("MulState: start computing, op1=0x{:08x} op2=0x{:08x} rob_idx={}",
                op1, op2, rob_idx)
        
        with Condition(is_busy):
            # BUSY 状态：计算中，倒计时
            new_cnt = cycle_cnt - UInt(4)(1)
            mul_regs.cycle_cnt[0] <= new_cnt
            log("MulState: computing, cnt={} -> {}", cycle_cnt, new_cnt)
        
        with Condition(is_done):
            # DONE 状态：输出结果，回到 IDLE
            mul_regs.cycle_cnt[0] <= UInt(4)(0)
            # 直接写入 ROB
            rob._write_ready(rob_idx, Bits(1)(1))
            rob.value[rob_idx] <= mul_result
            log("MulState: done, result=0x{:08x} rob_idx={}, wrote to ROB", mul_result, rob_idx)
        
        # 返回完成信号（用于广播给 RS 更新操作数）
        return rob_idx, mul_result, is_done
        
        # 使用的操作数（计算中使用寄存器值，完成时输出）
        op1 = op1_reg[0]
        op2 = op2_reg[0]
        alu_type = alu_type_reg[0]
        
        # 计算乘法结果
        mul_result_u32 = (op1 * op2).bitcast(UInt(32))
        mul_result = mul_result_u32
        
        log("MulState: idle={} done={} cnt={} has_req={} op1=0x{:08x} op2=0x{:08x} result=0x{:08x} rob_idx={}",
            is_idle, is_done, cycle_cnt[0], has_request, op1, op2, mul_result, rob_idx_reg[0])
        
        # 状态转移
        # IDLE 且有新请求时，开始计数
        with Condition(is_idle & has_request):
            op1_reg[0] <= req_op1
            op2_reg[0] <= req_op2
            alu_type_reg[0] <= req_alu_type
            rob_idx_reg[0] <= req_rob_idx
            cycle_cnt[0] <= UInt(4)(MUL_LATENCY)
            log("MulState: accept request, op1=0x{:08x} op2=0x{:08x} rob_idx={}",
                req_op1, req_op2, req_rob_idx)
        
        is_busy = ~is_idle & ~is_done
        with Condition(is_busy):
            # BUSY 状态：计算中，倒计时
            new_cnt = cycle_cnt[0] - UInt(4)(1)
            cycle_cnt[0] <= new_cnt
            log("MulState: computing, cnt={} -> {}", cycle_cnt[0], new_cnt)
        
        with Condition(is_done):
            # DONE 状态：输出结果，回到 IDLE
            cycle_cnt[0] <= UInt(4)(0)
            # 直接写入 ROB
            rob._write_ready(rob_idx_reg[0], Bits(1)(1))
            rob.value[rob_idx_reg[0]] <= mul_result
            log("MulState: done, result=0x{:08x} rob_idx={}, wrote to ROB", mul_result, rob_idx_reg[0])
        
        # 返回完成信号（用于广播给 RS 更新操作数）
        return rob_idx_reg[0], mul_result, is_done


# 乘法保留站条目
class MUL_RSEntry:
    """乘法保留站条目"""
    def __init__(self):
        self.busy = RegArray(Bits(1), 1, initializer=[0])
        self.op = RegArray(Bits(RV32I_ALU.CNT), 1, initializer=[0])  # 乘法类型
        self.vj = RegArray(UInt(32), 1, initializer=[0])  # 操作数 1
        self.vk = RegArray(UInt(32), 1, initializer=[0])  # 操作数 2
        self.qj = RegArray(Bits(REG_PENDING_WIDTH), 1, initializer=[0])   # 源 1 ROB 标签
        self.qk = RegArray(Bits(REG_PENDING_WIDTH), 1, initializer=[0])   # 源 2 ROB 标签
        self.qj_valid = RegArray(Bits(1), 1, initializer=[0])  # 源 1 就绪
        self.qk_valid = RegArray(Bits(1), 1, initializer=[0])  # 源 2 就绪
        self.rd = RegArray(Bits(5), 1, initializer=[0])
        self.rob_idx = RegArray(Bits(ROB_IDX_WIDTH), 1, initializer=[0])
        self.fired = RegArray(Bits(1), 1, initializer=[0])  # 是否已发射


class MUL_RS_downstream(Downstream):
    """乘法保留站的 downstream 逻辑"""
    
    def __init__(self, rs_idx=0):
        super().__init__()
        self.rs_idx = rs_idx  # 标识处理的 RS entry 索引
    
    @downstream.combinational
    def build(self,
              rs: MUL_RSEntry,
              mul_regs: MultiplierRegs,  # 乘法器的共享寄存器
              cbd_signal,  # CDB 广播信号
              mul_broadcast,  # 乘法器完成广播 (rob_idx, rd_data, is_done)
              metadata):  # 用于驱动 downstream 的元数据
        """
        监听 CDB 更新操作数，就绪时将请求写入乘法器寄存器
        """
        from .arbitrator import CBD_signal
        
        metadata = metadata.optional(default=UInt(8)(0))
        _ = metadata == metadata  # 确保每周期触发
        
        # 解包乘法器广播信号，使用 optional 防止无效值
        mul_rob_idx, mul_rd_data, mul_is_done = mul_broadcast
        mul_rob_idx = mul_rob_idx.optional(default=UInt(ROB_IDX_WIDTH)(0))
        mul_rd_data = mul_rd_data.optional(default=UInt(32)(0))
        mul_is_done = mul_is_done.optional(default=Bits(1)(0))
        
        # 获取 CDB 信号
        cbd_payload = cbd_signal.value()
        cbd = CBD_signal.view(cbd_payload)
        cbd_valid = cbd.valid
        cbd_rob_idx = cbd.ROB_idx
        cbd_rd_data = cbd.rd_data
        
        # 检查乘法器是否空闲
        mul_idle = (mul_regs.cycle_cnt[0] == UInt(4)(0)) & (~mul_regs.pending[0])
        
        log("MUL_RS downstream: busy={} qj_v={} qk_v={} rob_idx={} fired={} cbd_valid={} cbd_rob={} mul_done={} mul_idle={}",
            rs.busy[0], rs.qj_valid[0], rs.qk_valid[0], rs.rob_idx[0], rs.fired[0], cbd_valid, cbd_rob_idx, mul_is_done, mul_idle)
        
        # 监听 CDB 广播，更新操作数
        busy_flag = rs.busy[0]
        with Condition(busy_flag & cbd_valid):
            # 检查 qj 是否在等待这个 ROB 条目
            qj_match = (~rs.qj_valid[0]) & (rs.qj[0] == cbd_rob_idx)
            with Condition(qj_match):
                rs.qj_valid[0] <= Bits(1)(1)
                rs.vj[0] <= cbd_rd_data
                log("MUL_RS: update qj from CDB, rob={} data=0x{:08x}", cbd_rob_idx, cbd_rd_data)
            
            # 检查 qk 是否在等待这个 ROB 条目
            qk_match = (~rs.qk_valid[0]) & (rs.qk[0] == cbd_rob_idx)
            with Condition(qk_match):
                rs.qk_valid[0] <= Bits(1)(1)
                rs.vk[0] <= cbd_rd_data
                log("MUL_RS: update qk from CDB, rob={} data=0x{:08x}", cbd_rob_idx, cbd_rd_data)
        
        # 监听乘法器完成广播，更新操作数（类似 CDB 广播）
        with Condition(busy_flag & mul_is_done):
            # 检查 qj 是否在等待乘法器的结果
            mul_qj_match = (~rs.qj_valid[0]) & (rs.qj[0] == mul_rob_idx)
            with Condition(mul_qj_match):
                rs.qj_valid[0] <= Bits(1)(1)
                rs.vj[0] <= mul_rd_data
                log("MUL_RS: update qj from MUL, rob={} data=0x{:08x}", mul_rob_idx, mul_rd_data)
            
            # 检查 qk 是否在等待乘法器的结果
            mul_qk_match = (~rs.qk_valid[0]) & (rs.qk[0] == mul_rob_idx)
            with Condition(mul_qk_match):
                rs.qk_valid[0] <= Bits(1)(1)
                rs.vk[0] <= mul_rd_data
                log("MUL_RS: update qk from MUL, rob={} data=0x{:08x}", mul_rob_idx, mul_rd_data)
        
        # 就绪时发射（通过设置乘法器寄存器的 pending 标志）
        ready = (busy_flag == Bits(1)(1)) & rs.qj_valid[0] & rs.qk_valid[0] & ~rs.fired[0] & mul_idle
        with Condition(ready):
            log("MUL_RS: fire to multiplier, op1=0x{:08x} op2=0x{:08x} rob_idx={}",
                rs.vj[0], rs.vk[0], rs.rob_idx[0])
            # 写入乘法器寄存器
            mul_regs.op1[0] <= rs.vj[0]
            mul_regs.op2[0] <= rs.vk[0]
            mul_regs.alu_type[0] <= rs.op[0]
            mul_regs.rob_idx[0] <= rs.rob_idx[0].bitcast(UInt(ROB_IDX_WIDTH))  # 转换类型
            mul_regs.pending[0] <= Bits(1)(1)  # 标记有待处理的请求
            rs.fired[0] <= Bits(1)(1)
        
        # 乘法完成时清除 MUL_RS（如果当前 RS 的 ROB idx 匹配）
        rs_matches_done = busy_flag & mul_is_done & (rs.rob_idx[0] == mul_rob_idx)
        with Condition(rs_matches_done):
            rs.busy[0] <= Bits(1)(0)
            rs.fired[0] <= Bits(1)(0)
            rs.qj_valid[0] <= Bits(1)(0)
            rs.qk_valid[0] <= Bits(1)(0)
            log("MUL_RS: cleared after mul done, rob_idx={}", mul_rob_idx)
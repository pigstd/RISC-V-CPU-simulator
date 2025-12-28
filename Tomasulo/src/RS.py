from assassyn.frontend import *
# 直接复用 ALU 模块里定义的 ALU_signal 记录类型
from .alu import ALU, ALU_signal
from .arbitrator import CBD_signal as CDBSignal
try:
    from .instruction import RV32I_ALU
except ImportError:
    from Tomasulo.src.instruction import RV32I_ALU

# Tomasulo Reservation Station (简化版) 的基础数据结构
# 每个 RS entry 持有操作数就绪标志、操作数值或标签、目标 rd、ROB 索引等。

RS_SIZE = 2
RS_IDX_WIDTH = (RS_SIZE - 1).bit_length()

class RSEntry:
    def __init__(self):
        # busy/ready 标志
        self.busy = RegArray(Bits(1), 1, initializer=[0])
        self.op = RegArray(Bits(RV32I_ALU.CNT), 1, initializer=[0])  # ALU one-hot 类型
        # 操作数值与来源
        self.vj = RegArray(UInt(32), 1, initializer=[0])
        self.vk = RegArray(UInt(32), 1, initializer=[0])
        self.qj = RegArray(Bits(4), 1, initializer=[0])           # 源操作数的标签（ROB idx），0 表示就绪
        self.qk = RegArray(Bits(4), 1, initializer=[0])
        self.qj_valid = RegArray(Bits(1), 1, initializer=[0])     # 标记 vj/vk 是否有效
        self.qk_valid = RegArray(Bits(1), 1, initializer=[0])
        # 目标寄存器 / ROB
        self.rd = RegArray(Bits(5), 1, initializer=[0])
        self.rob_idx = RegArray(Bits(4), 1, initializer=[0])
        # 立即数等额外字段
        self.imm = RegArray(UInt(32), 1, initializer=[0])
        # 分支/JAL/JALR 控制
        self.is_branch = RegArray(Bits(1), 1, initializer=[0])
        self.is_jal = RegArray(Bits(1), 1, initializer=[0])
        self.is_jalr = RegArray(Bits(1), 1, initializer=[0])
        self.is_lui = RegArray(Bits(1), 1, initializer=[0])
        self.is_auipc = RegArray(Bits(1), 1, initializer=[0])
        self.pc_addr = RegArray(UInt(32), 1, initializer=[0])
        self.is_syscall = RegArray(Bits(1), 1, initializer=[0])
        # 是否发射给 ALU
        self.fired = RegArray(Bits(1), 1, initializer=[0])


class RS_downstream(Downstream):
    def __init__(self):
        super().__init__()

    @downstream.combinational
    def build(self,
              rs: RSEntry,
              alu : ALU,
              cbd_signal: Value,
              issue_stall: Value,
              metadata: Value):
        # 依赖 Issuer 的输出，保证在有发射动作时也会调度 RS_downstream
        issue_stall = issue_stall.optional(default=Bits(1)(0))
        metadata = metadata.optional(default=Bits(8)(0))
        # 人为依赖 metadata，确保每周期都触发一次（即使上游无事件）
        _ = metadata == metadata
        log("RS downstream metadata={} busy={} qj_v={} qk_v={} rob_idx={} op={:014b}", metadata, rs.busy[0], rs.qj_valid[0], rs.qk_valid[0], rs.rob_idx[0], rs.op[0])
        log("cbd_signal valid={} ROB_idx={} rd_data=0x{:08x}", cbd_signal.valid, cbd_signal.ROB_idx, cbd_signal.rd_data)
        with Condition(cbd_signal.valid & (rs.busy[0] == Bits(1)(1))):
            # 如果有新的广播信号，更新 RS 中等待的操作数
            with Condition((rs.qj[0] == cbd_signal.ROB_idx) & ~rs.qj_valid[0]):
                rs.vj[0] <= cbd_signal.rd_data
                rs.qj_valid[0] <= Bits(1)(1)  # 标记为就绪
            with Condition((rs.qk[0] == cbd_signal.ROB_idx) & ~rs.qk_valid[0]):
                rs.vk[0] <= cbd_signal.rd_data
                rs.qk_valid[0] <= Bits(1)(1)  # 标记为就绪
        busy_flag = rs.busy[0]  # 直接用 busy 位，避免被不必要的比较折叠成常量
        # 需要显式括号，否则 Python 运算符优先级会把 & 和 == 搅在一起
        with Condition(cbd_signal.valid & (busy_flag == Bits(1)(1)) &
                       (cbd_signal.ROB_idx == rs.rob_idx[0])):
            # 如果 ROB 提交了该指令，清空 RS entry
            rs.busy[0] <= Bits(1)(0)
            rs.qj_valid[0] <= Bits(1)(0)
            rs.qk_valid[0] <= Bits(1)(0)
            rs.fired[0] <= Bits(1)(0)
        with Condition((busy_flag == Bits(1)(1)) & ~(rs.qj_valid[0] & rs.qk_valid[0])):
            log("RS waiting rob_idx={} qj_valid={} qk_valid={} qj={} qk={}", rs.rob_idx[0], rs.qj_valid[0], rs.qk_valid[0], rs.qj[0], rs.qk[0])
        with Condition((busy_flag == Bits(1)(1)) & (rs.qj_valid[0] & rs.qk_valid[0]) & (rs.fired[0] == Bits(1)(0))):
            log("RS fire ALU: rob_idx={} op1=0x{:08x} op2=0x{:08x} op={:014b}", rs.rob_idx[0], rs.vj[0], rs.vk[0], rs.op[0])
            alu.async_called(
                alu_signals=ALU_signal.bundle(
                    op1_val = rs.vj[0],
                    op2_val = rs.vk[0],
                    alu_type = rs.op[0],
                    is_B = rs.is_branch[0],
                    is_jal = rs.is_jal[0],
                    is_jalr = rs.is_jalr[0],
                    pc_addr = rs.pc_addr[0],
                    imm_val = rs.imm[0],
                    ROB_idx = rs.rob_idx[0],
                )
            )
            rs.fired[0] <= Bits(1)(1)

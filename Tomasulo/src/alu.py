from assassyn.frontend import *
try:
    from .instruction import *
except ImportError:
    from Tomasulo.src.instruction import *

# 全局配置 - 数据段基地址（默认 0x2000）
# 可通过 executor.DATA_BASE_OFFSET = xxx 在外部设置
DATA_BASE_OFFSET = 0x2000

ALU_signal = Record(
    op1_val = UInt(32),    # op1
    op2_val = UInt(32),    # op2
    alu_type = Bits(RV32I_ALU.CNT),  # ALU 操
    is_B = Bits(1),   # 是否 B 指令
    is_jal = Bits(1), # 是否 JAL 指令
    is_jalr = Bits(1),# 是否 JALR 指令
    pc_addr = UInt(32),   # 当前指令 PC 地址
    imm_val = UInt(32),   # 立即数
    ROB_idx = UInt(4),    # 指令在 ROB 中的索引
)

ALU_CBD_signal = Record(
    ROB_idx = UInt(4),    # 指令在 ROB 中的索引
    rd_data = UInt(32),   # 写回数据
    valid = Bits(1),     # 数据有效标志
    is_branch = Bits(1),  # 是否分支指令
    next_pc = UInt(32),   # 分支指令的下一个 PC（如果不是分支指令则无效）
)

# jal ：op1 = pc, op2 = imm
# jalr：op1 = rs1, op2 = imm
# 这两个的 rd 的结果都要写成 pc + 4

class ALU(Module):
    def __init__(self):
        super().__init__(ports = {
            "alu_signals": Port(ALU_signal),
        })
    
    @module.combinational
    def build(self):
        signal = self.pop_all_ports(True)
        op1 = signal.op1_val
        op2 = signal.op2_val
        alu_type = signal.alu_type
        # 为每个 ALU opcode 准备候选结果（统一为 u32）
        alu_candidates = [UInt(32)(0) for _ in range(RV32I_ALU.CNT)]
        shamt = op2[0:4]
        op1_s = op1.bitcast(Int(32))
        op2_s = op2.bitcast(Int(32))
        alu_candidates[RV32I_ALU.ALU_ADD]     = (op1 + op2).bitcast(UInt(32))
        alu_candidates[RV32I_ALU.ALU_SUB]     = (op1 - op2).bitcast(UInt(32))
        alu_candidates[RV32I_ALU.ALU_AND]     = (op1 & op2).bitcast(UInt(32))
        alu_candidates[RV32I_ALU.ALU_OR]      = (op1 | op2).bitcast(UInt(32))
        alu_candidates[RV32I_ALU.ALU_XOR]     = (op1 ^ op2).bitcast(UInt(32))
        alu_candidates[RV32I_ALU.ALU_SLL]     = (op1 << shamt).bitcast(UInt(32))
        alu_candidates[RV32I_ALU.ALU_SRL]     = (op1 >> shamt).bitcast(UInt(32))
        alu_candidates[RV32I_ALU.ALU_SRA]     = (op1_s >> shamt).bitcast(UInt(32))
        alu_candidates[RV32I_ALU.ALU_CMP_EQ]  = (op1 == op2).zext(UInt(32))
        alu_candidates[RV32I_ALU.ALU_CMP_LT]  = (op1_s < op2_s).zext(UInt(32))
        alu_candidates[RV32I_ALU.ALU_CMP_LTU] = (op1 < op2).zext(UInt(32))
        alu_candidates[RV32I_ALU.ALU_CMP_GE]  = (op1_s >= op2_s).zext(UInt(32))
        alu_candidates[RV32I_ALU.ALU_CMP_GEU] = (op1 >= op2).zext(UInt(32))
        alu_candidates[RV32I_ALU.ALU_CMP_NE]  = (op1 != op2).zext(UInt(32))
        # 选择最终结果
        # 其余保持 0（ALU_NONE 等）
        alu_res_basic = UInt(32)(0)
        for i in range(RV32I_ALU.CNT):
            alu_res_basic = (alu_type == Bits(RV32I_ALU.CNT)(1 << i)).select(alu_candidates[i], alu_res_basic)
        
        # 处理 jal / jalr 指令
        alu_res = (signal.is_jal | signal.is_jalr).select(
            signal.pc_addr + UInt(32)(4),
            alu_res_basic
        )
        is_branch = signal.is_B | signal.is_jal | signal.is_jalr
        branch_taken = (alu_res_basic != UInt(32)(0))
        branch_pc = branch_taken.select(signal.pc_addr + signal.imm_val, signal.pc_addr + UInt(32)(4))

        # jal: next_pc = pc + imm
        # jalr: next_pc = rs1 + imm (已在 alu_res_basic 中计算)
        next_pc = signal.is_jal.select(
            signal.pc_addr + signal.imm_val,
            signal.is_jalr.select(
                alu_res_basic,
                signal.is_B.select(branch_pc, alu_res_basic)
            )
        )

        log("alu_res_basic = {:08x}, alu_res = {:08x}, next_pc = {:08x}, is_branch = {}", alu_res_basic, alu_res, next_pc, is_branch)

        cbd_signal = ALU_CBD_signal.bundle(
            ROB_idx = signal.ROB_idx,
            rd_data = alu_res,
            valid = Bits(1)(1),
            is_branch = is_branch,
            next_pc = next_pc,
        )

        return cbd_signal

        

from assassyn.frontend import *

@rewrite_assign
def decoder_R_type(inst, is_eq):
    opcode = inst[0:6]
    funct3 = inst[12:14]
    funct7 = inst[25:31]
    # log("Decoding R-type instruction")
    # log("Opcode: {}, funct3: {}, funct7: {}", opcode, funct3, funct7)
    rd = inst[7:11]
    rs1 = inst[15:19]
    rs2 = inst[20:24]
    # log("rs1: {}, rs2: {}, rd: {}", rs1, rs2, rd)
    R_type_op = [
        # name opcode funct3 funct7 ALU
        ["add",  0b0110011, 0b000, 0b0000000, RV32I_ALU.ALU_ADD],
        ["sub",  0b0110011, 0b000, 0b0100000, RV32I_ALU.ALU_SUB],
        ["and",  0b0110011, 0b111, 0b0000000, RV32I_ALU.ALU_AND],
        ["or",   0b0110011, 0b110, 0b0000000, RV32I_ALU.ALU_OR],
        ["xor",  0b0110011, 0b100, 0b0000000, RV32I_ALU.ALU_XOR],
        ["sll",  0b0110011, 0b001, 0b0000000, RV32I_ALU.ALU_SLL],
        ["srl",  0b0110011, 0b101, 0b0000000, RV32I_ALU.ALU_SRL],
        ["sra",  0b0110011, 0b101, 0b0100000, RV32I_ALU.ALU_SRA],
        ["slt",  0b0110011, 0b010, 0b0000000, RV32I_ALU.ALU_CMP_LT],
        ["sltu", 0b0110011, 0b011, 0b0000000, RV32I_ALU.ALU_CMP_LTU],
    ]
    is_R = Bits(1)(0)
    alu_type = Bits(RV32I_ALU.CNT)(1 << RV32I_ALU.ALU_NONE)
    for [name, op, f3, f7, alu] in R_type_op:
        eq = (opcode == Bits(7)(op)) & (funct3 == Bits(3)(f3)) & (funct7 == Bits(7)(f7))
        is_eq[name] = eq
        is_R = is_R | eq
        alu_onehot = Bits(RV32I_ALU.CNT)(1 << alu)
        alu_type = eq.select(alu_onehot, alu_type)
        with Condition(eq):
            log(f"Decoded R-type instruction: {name}")
    return is_R, rs1, rs2, rd, alu_type

@rewrite_assign
def decoder_I_type(inst, is_eq):
    imm = inst[20:31]
    rs1 = inst[15:19]
    rd = inst[7:11]
    opcode = inst[0:6]
    funct3 = inst[12:14]
    # log("Decoding I-type instruction")
    # log("Opcode: {}, funct3: {}", opcode, funct3)
    I_type_op = [
        # name   opcode     funct3   alu
        ["jalr",  0b1100111, 0b000, RV32I_ALU.ALU_ADD],
        ["lb",    0b0000011, 0b000, RV32I_ALU.ALU_ADD],
        ["lh",    0b0000011, 0b001, RV32I_ALU.ALU_ADD],
        ["lw",    0b0000011, 0b010, RV32I_ALU.ALU_ADD],
        ["lbu",   0b0000011, 0b100, RV32I_ALU.ALU_ADD],
        ["lhu",   0b0000011, 0b101, RV32I_ALU.ALU_ADD],
        ["addi",  0b0010011, 0b000, RV32I_ALU.ALU_ADD],
        ["slti",  0b0010011, 0b010, RV32I_ALU.ALU_CMP_LT],
        ["sltiu", 0b0010011, 0b011, RV32I_ALU.ALU_CMP_LTU],
        ["xori",  0b0010011, 0b100, RV32I_ALU.ALU_XOR],
        ["ori",   0b0010011, 0b110, RV32I_ALU.ALU_OR],
        ["andi",  0b0010011, 0b111, RV32I_ALU.ALU_AND],
        ["ecall", 0b1110011, 0b000, RV32I_ALU.ALU_NONE],
        ["ebreak",0b1110011, 0b000, RV32I_ALU.ALU_NONE],
    ]
    is_I = Bits(1)(0)
    alu_type = Bits(RV32I_ALU.CNT)(1 << RV32I_ALU.ALU_NONE)
    for [name, op, f3, alu] in I_type_op:
        extra = Bits(1)(1)
        if name == "ecall":
            extra = imm == Bits(12)(0)
        if name == "ebreak":
            extra = imm == Bits(12)(1)
        eq = (opcode == Bits(7)(op)) & (funct3 == Bits(3)(f3)) & extra
        is_eq[name] = eq
        is_I = is_I | eq
        alu_onehot = Bits(RV32I_ALU.CNT)(1 << alu)
        alu_type = eq.select(alu_onehot, alu_type)
        with Condition(eq):
            log(f"Decoded I-type instruction: {name}")
    return is_I, rs1, imm, rd, alu_type

@rewrite_assign
def decoder_I_star(inst, is_eq):
    imm = inst[20:31]
    imm11_5 = inst[25:31]
    rs1 = inst[15:19]
    rd = inst[7:11]
    opcode = inst[0:6]
    funct3 = inst[12:14]

    # 需要额外检查 imm[11:5] 或 imm 全匹配的 I 型
    special_op = [
        # name  opcode     funct3   imm_check        alu
        ["slli",  0b0010011, 0b001, Bits(7)(0b0000000), RV32I_ALU.ALU_SLL],
        ["srli",  0b0010011, 0b101, Bits(7)(0b0000000), RV32I_ALU.ALU_SRL],
        ["srai",  0b0010011, 0b101, Bits(7)(0b0100000), RV32I_ALU.ALU_SRA],
    ]

    is_I_star = Bits(1)(0)
    alu_type = Bits(RV32I_ALU.CNT)(1 << RV32I_ALU.ALU_NONE)
    for [name, op, f3, imm_chk, alu] in special_op:
        extra = imm11_5 == imm_chk

        eq = (opcode == Bits(7)(op)) & (funct3 == Bits(3)(f3)) & extra
        is_eq[name] = eq
        is_I_star = is_I_star | eq
        alu_onehot = Bits(RV32I_ALU.CNT)(1 << alu)
        alu_type = eq.select(alu_onehot, alu_type)
        with Condition(eq):
            log(f"Decoded I*-type instruction: {name}")

    return is_I_star, rs1, imm, rd, alu_type

@rewrite_assign
def decoder_S_type(inst, is_eq):
    imm11_5 = inst[25:31]
    imm4_0 = inst[7:11]
    imm = concat(imm11_5, imm4_0)
    rs1 = inst[15:19]
    rs2 = inst[20:24]
    opcode = inst[0:6]
    funct3 = inst[12:14]
    S_type_op = [
        # name opcode funct3
        ["sb", 0b0100011, 0b000],
        ["sh", 0b0100011, 0b001],
        ["sw", 0b0100011, 0b010],
    ]
    is_S = Bits(1)(0)
    for [name, op, f3] in S_type_op:
        eq = (opcode == Bits(7)(op)) & (funct3 == Bits(3)(f3))
        is_eq[name] = eq
        is_S = is_S | eq
        with Condition(eq):
            log(f"Decoded S-type instruction: {name}")
    return is_S, rs1, rs2, imm

@rewrite_assign
def decoder_B_type(inst, is_eq):
    imm12 = inst[31:31]
    imm11 = inst[7:7]
    imm10_5 = inst[25:30]
    imm4_1 = inst[8:11]
    imm = concat(imm12, imm11, imm10_5, imm4_1, Bits(1)(0))
    rs1 = inst[15:19]
    rs2 = inst[20:24]
    opcode = inst[0:6]
    funct3 = inst[12:14]
    B_type_op = [
        # name opcode   funct3    alu
        ["beq",  0b1100011, 0b000, RV32I_ALU.ALU_CMP_EQ],
        ["bne",  0b1100011, 0b001, RV32I_ALU.ALU_CMP_NE],
        ["blt",  0b1100011, 0b100, RV32I_ALU.ALU_CMP_LT],
        ["bge",  0b1100011, 0b101, RV32I_ALU.ALU_CMP_GE],
        ["bltu", 0b1100011, 0b110, RV32I_ALU.ALU_CMP_LTU],
        ["bgeu", 0b1100011, 0b111, RV32I_ALU.ALU_CMP_GEU],
    ]
    is_B = Bits(1)(0)
    alu_type = Bits(RV32I_ALU.CNT)(1 << RV32I_ALU.ALU_NONE)
    for [name, op, f3, alu] in B_type_op:
        eq = (opcode == Bits(7)(op)) & (funct3 == Bits(3)(f3))
        is_eq[name] = eq
        is_B = is_B | eq
        alu_onehot = Bits(RV32I_ALU.CNT)(1 << alu)
        alu_type = eq.select(alu_onehot, alu_type)
        with Condition(eq):
            log(f"Decoded B-type instruction: {name}")
    return is_B, rs1, rs2, imm, alu_type

@rewrite_assign
def decoder_U_type(inst, is_eq):
    imm = inst[12:31]
    rd = inst[7:11]
    opcode = inst[0:6]
    U_type_op = [
        # name opcode
        ["lui",   0b0110111],
        ["auipc", 0b0010111],
    ]
    is_U = Bits(1)(0)
    for [name, op] in U_type_op:
        eq = opcode == Bits(7)(op)
        is_eq[name] = eq
        is_U = is_U | eq
        with Condition(eq):
            log(f"Decoded U-type instruction: {name}")
    return is_U, imm, rd

@rewrite_assign
def decoder_J_type(inst, is_eq):
    rd = inst[7:11]
    opcode = inst[0:6]
    imm20 = inst[31:31]
    imm10_1 = inst[21:30]
    imm11 = inst[20:20]
    imm19_12 = inst[12:19]
    imm = concat(imm20, imm19_12, imm11, imm10_1, Bits(1)(0))
    J_type_op = [
        # name opcode
        ["jal", 0b1101111],
    ]
    is_J = Bits(1)(0)
    for [name, op] in J_type_op:
        eq = opcode == Bits(7)(op)
        is_eq[name] = eq
        is_J = is_J | eq
        with Condition(eq):
            log(f"Decoded J-type instruction: {name}")
    return is_J, imm, rd

class RV32I_ALU:
    CNT = 15
    ALU_ADD = 0
    ALU_SUB = 1
    ALU_XOR = 2
    ALU_OR = 3
    ALU_AND = 4
    ALU_SLL = 5
    ALU_SRL = 6
    ALU_SRA = 7
    ALU_CMP_EQ = 8
    ALU_CMP_LT = 9
    ALU_CMP_LTU = 10
    ALU_CMP_GE = 11
    ALU_CMP_GEU = 12
    ALU_CMP_NE = 13
    ALU_NONE = 14

deocder_signals = Record(
    rs1 = Bits(5),
    rs1_used = Bits(1),
    rs1_value = UInt(32),
    rs1_valid = Bits(1),
    rs2 = Bits(5),
    rs2_used = Bits(1),
    rs2_value = UInt(32),
    rs2_valid = Bits(1),
    rd = Bits(5),
    rd_used = Bits(1),
    imm = Bits(32),
    imm_used = Bits(1),
    alu_type = Bits(RV32I_ALU.CNT),
    mem_read = Bits(1),
    mem_write = Bits(1),
    is_branch = Bits(1),
    branch_type = Bits(3),
    is_B = Bits(1),  # 条件分支 B 类型指令
    is_jal = Bits(1),
    is_jalr = Bits(1),
    is_ecall = Bits(1),
    is_ebreak = Bits(1),
    is_lui = Bits(1),
    is_auipc = Bits(1),
    is_valid = Bits(1),
    # 分支预测相关：B/JAL可预测跳转，JALR需要stall
    is_predictable_branch = Bits(1),  # B 或 JAL，可以预测
)

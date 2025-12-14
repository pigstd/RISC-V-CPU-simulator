from assassyn.frontend import *
from instruction import *


@rewrite_assign
def decoder_logic(inst):
    is_eq = {}
    [is_R, R_rs1, R_rs2, R_rd, R_alu] = decoder_R_type(inst=inst, is_eq=is_eq)
    [is_I, I_rs1, I_imm, I_rd, I_alu] = decoder_I_type(inst=inst, is_eq=is_eq)
    [is_I_star, I_star_rs1, I_star_imm, I_star_rd, I_star_alu] = decoder_I_star(inst=inst, is_eq=is_eq)
    [is_S, S_rs1, S_rs2, S_imm] = decoder_S_type(inst=inst, is_eq=is_eq)
    [is_B, B_rs1, B_rs2, B_imm] = decoder_B_type(inst=inst, is_eq=is_eq)
    [is_U, U_imm, U_rd] = decoder_U_type(inst=inst, is_eq=is_eq)
    [is_J, J_imm, J_rd] = decoder_J_type(inst=inst, is_eq=is_eq)

    # 接下来信息整合
    ecall = is_eq.get("ecall", Bits(1)(0))
    ebreak = is_eq.get("ebreak", Bits(1)(0))

    rs1_used = is_R | is_I | is_I_star | is_S | is_B
    rs1 = is_R.select(R_rs1,
            is_I.select(I_rs1,
            is_I_star.select(I_star_rs1,
            is_S.select(S_rs1,
            is_B.select(B_rs1, Bits(5)(0))))))

    rs2_used = is_R | is_S | is_B
    rs2 = is_R.select(R_rs2,
            is_S.select(S_rs2,
            is_B.select(B_rs2, Bits(5)(0))))

    is_I_writes = is_I & ~(ecall | ebreak)
    rd_used = is_R | is_I_writes | is_I_star | is_U | is_J
    rd = is_R.select(R_rd,
         is_I_writes.select(I_rd,
         is_I_star.select(I_star_rd,
         is_U.select(U_rd,
         is_J.select(J_rd, Bits(5)(0))))))

    imm_used = is_I | is_I_star | is_S | is_B | is_U | is_J
    imm_zero = Bits(32)(0)
    imm_I_sext = I_imm.sext(Int(32)).bitcast(Bits(32))
    imm_S_sext = S_imm.sext(Int(32)).bitcast(Bits(32))
    imm_B_sext = B_imm.sext(Int(32)).bitcast(Bits(32))
    imm_J_sext = J_imm.sext(Int(32)).bitcast(Bits(32))
    imm_U_shifted = concat(U_imm, Bits(12)(0))
    imm_Istar_zext = I_star_imm.zext(Bits(32))
    imm = is_I.select(imm_I_sext,
          is_I_star.select(imm_Istar_zext,
          is_S.select(imm_S_sext,
          is_B.select(imm_B_sext,
          is_U.select(imm_U_shifted,
          is_J.select(imm_J_sext, imm_zero))))))

    mem_read = (is_eq.get("lb", Bits(1)(0)) |
                is_eq.get("lh", Bits(1)(0)) |
                is_eq.get("lw", Bits(1)(0)) |
                is_eq.get("lbu", Bits(1)(0)) |
                is_eq.get("lhu", Bits(1)(0)))
    mem_write = (is_eq.get("sb", Bits(1)(0)) |
                 is_eq.get("sh", Bits(1)(0)) |
                 is_eq.get("sw", Bits(1)(0)))
    is_branch = is_B | is_J | is_eq.get("jalr", Bits(1)(0))
    branch_type = is_B.select(inst[12:14], Bits(3)(0))
    is_jal = is_J
    is_jalr = is_eq.get("jalr", Bits(1)(0))
    is_ecall = ecall
    is_ebreak = ebreak

    # ALU 类型：优先 R > I > I*
    alu_type = is_R.select(R_alu,
               is_I.select(I_alu,
               is_I_star.select(I_star_alu, Bits(RV32I_ALU.CNT)(1 << RV32I_ALU.ALU_NONE))))

    log("decoder type flags: R={} I={} I*={} S={} B={} U={} J={} ecall={} ebreak={}",
        is_R, is_I, is_I_star, is_S, is_B, is_U, is_J, ecall, ebreak)
    log("decoder: imm(raw)={} imm(signed)={}", imm, imm.bitcast(Int(32)))
    log("decoder: rs1_used = {} , rs1 = {}", rs1_used, rs1)
    log("decoder: rs2_used = {} , rs2 = {}", rs2_used, rs2)
    log("decoder: rd_used = {} , rd = {}", rd_used, rd)
    log("decoder: imm_used = {} , imm = {}", imm_used, imm)
    log("decoder: mem_read = {} , mem_write = {} , is_branch = {} , branch_type = {}", mem_read, mem_write, is_branch, branch_type)
    log("decoder: alu_type(onehot)={:014b}", alu_type)

    return deocder_signals.bundle(
        rs1=rs1,
        rs1_used=rs1_used,
        rs2=rs2,
        rs2_used=rs2_used,
        rd=rd,
        rd_used=rd_used,
        imm=imm,
        imm_used=imm_used,
        alu_type=alu_type,
        mem_read=mem_read,
        mem_write=mem_write,
        is_branch=is_branch,
        branch_type=branch_type,
        is_jal=is_jal,
        is_jalr=is_jalr,
        is_ecall=is_ecall,
        is_ebreak=is_ebreak,
    )

from assassyn.frontend import *
from instruction import *

# 全局配置 - 数据段基地址（默认 0x2000）
# 可通过 executor.DATA_BASE_OFFSET = xxx 在外部设置
DATA_BASE_OFFSET = 0x2000


@rewrite_assign
def executor_logic(signals, pc_addr: Value, dcache: SRAM,
                   EX_rd : Value,
                   EX_result : Value,
                   MEM_rd : Value,
                   MEM_result : Value,):

    log("bypass: EX_rd={} EX_result={} MEM_rd={} MEM_result={}", EX_rd, EX_result, MEM_rd, MEM_result)

    log("rs1: {}, rs2: {}", signals.rs1, signals.rs2)

    rs1_val = (signals.rs1 == EX_rd).select(EX_result,
               (signals.rs1 == MEM_rd).select(MEM_result,
               signals.rs1_value))
    rs2_val = (signals.rs2 == EX_rd).select(EX_result,
               (signals.rs2 == MEM_rd).select(MEM_result,
               signals.rs2_value))

    imm_val = signals.imm.bitcast(UInt(32))

    log("executor input: pc={} rs1_used={} rs2_used={} rd_used={} alu_type={:014b} imm={} branch_type={} jal={} jalr={} ecall={} ebreak={}",
        pc_addr, signals.rs1_used, signals.rs2_used, signals.rd_used, signals.alu_type, imm_val,
        signals.branch_type, signals.is_jal, signals.is_jalr, signals.is_ecall, signals.is_ebreak)

    # 根据 rs2_used 选择第二操作数（R 指令用 rs2，I/I* 用 imm）
    op2 = signals.rs2_used.select(rs2_val, imm_val)

    # 为每个 ALU opcode 准备候选结果（统一为 u32）
    alu_candidates = [UInt(32)(0) for _ in range(RV32I_ALU.CNT)]
    shamt = op2[0:4]
    rs1_s = rs1_val.bitcast(Int(32))
    op2_s = op2.bitcast(Int(32))
    alu_candidates[RV32I_ALU.ALU_ADD]     = (rs1_val + op2).bitcast(UInt(32))
    alu_candidates[RV32I_ALU.ALU_SUB]     = (rs1_val - op2).bitcast(UInt(32))
    alu_candidates[RV32I_ALU.ALU_AND]     = (rs1_val & op2).bitcast(UInt(32))
    alu_candidates[RV32I_ALU.ALU_OR]      = (rs1_val | op2).bitcast(UInt(32))
    alu_candidates[RV32I_ALU.ALU_XOR]     = (rs1_val ^ op2).bitcast(UInt(32))
    alu_candidates[RV32I_ALU.ALU_SLL]     = (rs1_val << shamt).bitcast(UInt(32))
    alu_candidates[RV32I_ALU.ALU_SRL]     = (rs1_val >> shamt).bitcast(UInt(32))
    alu_candidates[RV32I_ALU.ALU_SRA]     = (rs1_s >> shamt).bitcast(UInt(32))
    alu_candidates[RV32I_ALU.ALU_CMP_EQ]  = (rs1_val == op2).zext(UInt(32))
    alu_candidates[RV32I_ALU.ALU_CMP_LT]  = (rs1_s < op2_s).zext(UInt(32))
    alu_candidates[RV32I_ALU.ALU_CMP_LTU] = (rs1_val < op2).zext(UInt(32))
    alu_candidates[RV32I_ALU.ALU_CMP_GE]  = (rs1_s >= op2_s).zext(UInt(32))
    alu_candidates[RV32I_ALU.ALU_CMP_GEU] = (rs1_val >= op2).zext(UInt(32))
    # 其余保持 0（ALU_NONE 等）

    log("executor operands: rs1_val={} rs2_val={} op2={} shamt={}", rs1_val, rs2_val, op2, shamt)

    # one-hot 选择 ALU 结果
    # alu_res_basic = signals.alu_type.select1hot(*alu_candidates)
    alu_res_basic = UInt(32)(0)
    for i in range(RV32I_ALU.CNT):
        alu_res_basic = (signals.alu_type == Bits(RV32I_ALU.CNT)(1 << i)).select(alu_candidates[i], alu_res_basic)
    
    # LUI: rd = imm (imm 已经是左移12位后的值)
    # AUIPC: rd = PC + imm
    lui_res = imm_val
    auipc_res = (pc_addr + imm_val).bitcast(UInt(32))
    alu_res = signals.is_lui.select(lui_res,
              signals.is_auipc.select(auipc_res, alu_res_basic))

    log("executor mem flags: mem_read={}, mem_write={}, branch={}", signals.mem_read, signals.mem_write, signals.is_branch)

    # ecall/ebreak：直接结束仿真
    sys_trap = signals.is_ecall | signals.is_ebreak
    with Condition(sys_trap):
        log("executor: system trap ecall={} ebreak={} at pc={}", signals.is_ecall, signals.is_ebreak, pc_addr)
        finish()

    # 访存地址与对齐
    eff_addr = (rs1_val + imm_val).bitcast(UInt(32))
    misaligned = (eff_addr & UInt(32)(0b11)) != UInt(32)(0)
    mem_re = signals.mem_read & ~misaligned
    mem_we = signals.mem_write & ~misaligned
    # 数据段基地址偏移：使用全局配置 DATA_BASE_OFFSET
    # 需要将访问地址减去基地址，得到 dcache 中的实际索引
    dcache_addr = eff_addr - UInt(32)(DATA_BASE_OFFSET)
    # 字节地址转字地址（右移2位）
    word_addr = (dcache_addr  >> UInt(32)(2)).bitcast(UInt(32))
    addr_oob = (word_addr >= UInt(32)(dcache.depth)) & ( mem_re | mem_we )
    with Condition(addr_oob):
        log("dcache addr out of range: eff_addr={} word_addr={} depth={}", eff_addr, word_addr, UInt(32)(dcache.depth))
        finish()
    # 触发 dcache 访问（异步 dout）
    dcache.build(
        we=mem_we.bitcast(Bits(1)),
        re=mem_re.bitcast(Bits(1)),
        addr=word_addr.bitcast(Bits(dcache.addr_width)),
        wdata=rs2_val.bitcast(Bits(32)),
    )
    with Condition(signals.mem_read | signals.mem_write):
        log("executor mem access: addr={} re={} we={} misaligned={}", eff_addr, mem_re, mem_we, misaligned)

    # 分支/跳转逻辑
    link_addr = pc_addr + UInt(32)(4)
    is_jal_like = signals.is_jal | signals.is_jalr

    # 计算分支条件
    rs1_s = rs1_val.bitcast(Int(32))
    rs2_s = rs2_val.bitcast(Int(32))
    cond_eq = rs1_val == rs2_val
    cond_lt = rs1_s < rs2_s
    cond_ltu = rs1_val < rs2_val
    cond_ne = cond_eq == Bits(1)(0)
    cond_ge = cond_lt == Bits(1)(0)
    cond_geu = cond_ltu == Bits(1)(0)

    funct3 = signals.branch_type
    beq = funct3 == Bits(3)(0b000)
    bne = funct3 == Bits(3)(0b001)
    blt = funct3 == Bits(3)(0b100)
    bge = funct3 == Bits(3)(0b101)
    bltu = funct3 == Bits(3)(0b110)
    bgeu = funct3 == Bits(3)(0b111)
    branch_cond = (beq & cond_eq) | (bne & cond_ne) | (blt & cond_lt) | (bge & cond_ge) | (bltu & cond_ltu) | (bgeu & cond_geu)

    branch_taken = is_jal_like | ((signals.is_branch & ~is_jal_like) & branch_cond)

    # 计算目标地址
    jalr_target_bits = (rs1_val + imm_val) & UInt(32)(0xFFFFFFFE)
    jalr_target = jalr_target_bits.bitcast(UInt(32))
    pc_target_raw = signals.is_jalr.select(jalr_target, pc_addr + imm_val)
    pc_target_masked = (pc_target_raw & UInt(32)(0xFFFFFFFC)).bitcast(UInt(32))
    pc_misaligned = ((pc_target_raw & UInt(32)(0b11)).bitcast(UInt(32))) != UInt(32)(0)
    pc_target_aligned = signals.is_jalr.select(jalr_target, pc_target_masked)
    with Condition(signals.is_branch & branch_taken & pc_misaligned):
        log("branch target misaligned: target={}", pc_target_raw)

    pc_default = link_addr  # 默认下一条
    pc_next = branch_taken.select(pc_target_aligned, pc_default)
    log("executor pc flow: default_next={} target={} taken={} jal_like={}", pc_default, pc_target_aligned, branch_taken, is_jal_like)
    # 现在不在 ex 阶段更新 pc_reg，会把这个 pc_next 传给 Fetchimpl 直接让他去 fetch 这个
    # pc_reg[0] <= pc_next

    # EX 仅产生写回数据意图，实际写回在 MA/WB
    rd_data = is_jal_like.select(link_addr, alu_res)
    # 若系统调用，忽略写回内容
    rd_data = sys_trap.select(UInt(32)(0), rd_data)

    log("executor: rs1={} rs2={} op2={} alu_res={} pc_next={}", rs1_val, rs2_val, op2, alu_res, pc_next)
    return rd_data.bitcast(Bits(32)), signals.is_branch, pc_next, mem_re, mem_we

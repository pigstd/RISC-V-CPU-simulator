# unit_tests/test_cases.py
from asm_utils import ASM

def case_hazard_war():
    """Write-After-Read Hazard"""
    instrs = [
        ASM.addi(1, 0, 10),  # x1 = 10
        ASM.addi(3, 0, 20),  # x3 = 20
        ASM.add(2, 1, 3),    # x2 = x1 + x3 = 30 (Read x1)
        ASM.addi(1, 0, 5),   # x1 = 5 (Write x1)
        ASM.nop()
    ]
    # 预期: x1=5, x2=30, x3=20
    expected = {1: 5, 2: 30, 3: 20}
    return instrs, expected

def case_loop_sum():
    """Sum 1 to 5 (1+2+3+4+5 = 15)"""
    instrs = [
        ASM.addi(1, 0, 0),   # sum = 0
        ASM.addi(2, 0, 5),   # count = 5
        # Loop: (offset -8)
        ASM.add(1, 1, 2),    # sum += count
        ASM.addi(2, 2, -1),  # count--
        ASM.bne(2, 0, -8),   # if count != 0 goto Loop
        ASM.nop()
    ]
    # 预期: x1 (sum) = 15, x2 (count) = 0
    expected = {1: 15, 2: 0}
    return instrs, expected


def case_alu_ops():
    """ALU operations coverage: add/sub/shift/logic/compare"""
    instrs = [
        ASM.addi(1, 0, 5),    # x1 = 5
        ASM.addi(2, 0, 2),    # x2 = 2
        ASM.add(3, 1, 2),     # x3 = 7
        ASM.sub(4, 1, 2),     # x4 = 3
        ASM.sll(5, 1, 2),     # x5 = 5 << 2 = 20
        ASM.srl(6, 1, 2),     # x6 = 5 >> 2 = 1
        ASM.sra(7, 1, 2),     # x7 = 5 >> 2 (arith) = 1
        ASM.and_(8, 1, 2),    # x8 = 5 & 2 = 0
        ASM.or_(9, 1, 2),     # x9 = 5 | 2 = 7
        ASM.xor(10, 1, 2),    # x10 = 5 ^ 2 = 7
        ASM.slt(11, 2, 1),    # x11 = (2 < 5) = 1
        ASM.sltu(12, 2, 1),   # x12 = (2 < 5) unsigned = 1
        ASM.nop()
    ]
    expected = {3:7, 4:3, 5:20, 6:1, 7:1, 8:0, 9:7, 10:7, 11:1, 12:1}
    return instrs, expected


def case_mem_rw():
    """Memory write then read back via lw/sw"""
    instrs = [
        ASM.lui(1, 0x2000),   # x1 = DATA_BASE_OFFSET (0x2000)
        ASM.addi(2, 0, 123),   # x2 = 123
        ASM.sw(1, 2, 0),       # store x2 -> [x1 + 0]
        ASM.lw(3, 1, 0),       # load into x3
        ASM.nop()
    ]
    expected = {3:123}
    return instrs, expected


def case_branches_and_jumps():
    """Coverage: beq, bne, blt, bge, jal, jalr"""
    instrs = [
        # beq: if equal skip next instruction
        ASM.addi(1, 0, 5),    # x1 = 5
        ASM.addi(2, 0, 5),    # x2 = 5
        ASM.beq(1, 2, 8),     # equal -> skip next addi
        ASM.addi(3, 0, 1),    # skipped
        ASM.addi(3, 0, 2),    # executed -> x3 = 2

        # bne: if not equal skip next
        ASM.addi(4, 0, 1),    # x4 = 1
        ASM.addi(5, 0, 2),    # x5 = 2
        ASM.bne(4, 5, 8),     # not equal -> skip next
        ASM.addi(6, 0, 1),    # skipped
        ASM.addi(6, 0, 3),    # executed -> x6 = 3

        # blt / bge: signed compare
        ASM.addi(7, 0, -1),   # x7 = -1
        ASM.addi(8, 0, 1),    # x8 = 1
        ASM.blt(7, 8, 8),     # -1 < 1 -> skip next
        ASM.addi(9, 0, 4),    # skipped
        ASM.addi(9, 0, 5),    # executed -> x9 = 5

        # jal: jump over next instruction
        ASM.jal(10, 8),       # rd=x10(link), jump forward 8 bytes
        ASM.addi(11, 0, 1),   # skipped
        ASM.addi(11, 0, 7),   # executed -> x11 = 7

        # jalr: jump to address in register
        ASM.addi(12, 0, 84),   # x12 = 84 (target address -> points to addi x14=9)
        ASM.jalr(13, 12, 0),  # jump to x12, rd=x13
        ASM.addi(14, 0, 1),   # skipped
        ASM.addi(14, 0, 9),   # executed -> x14 = 9

        ASM.nop()
    ]

    expected = {
        3: 2,
        6: 3,
        9: 5,
        11: 7,
        14: 9
    }
    return instrs, expected
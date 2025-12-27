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
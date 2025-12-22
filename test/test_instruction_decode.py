import os
import sys
import unittest
from contextlib import contextmanager

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
sys.path.append(ROOT_DIR)

from assassyn.frontend import Bits, Module, SysBuilder  # noqa: E402
from assassyn.ir.array import Slice  # noqa: E402
from assassyn.ir.const import Const  # noqa: E402
from assassyn.ir.dtype import RecordValue  # noqa: E402
from assassyn.ir.expr.arith import BinaryOp, UnaryOp  # noqa: E402
from assassyn.ir.expr.expr import Cast, Concat, Operand, Select, Select1Hot  # noqa: E402
sys.path.append(os.path.join(ROOT_DIR, "src"))
from decoder import decoder_logic  # noqa: E402,E402
from instruction import RV32I_ALU  # noqa: E402,E402


def mask_bits(value: int, bits: int) -> int:
    mask = (1 << bits) - 1
    return value & mask


def sext(value: int, bits: int) -> int:
    mask = (1 << bits) - 1
    value &= mask
    sign_bit = 1 << (bits - 1)
    if value & sign_bit:
        value -= (1 << bits)
    return value


def alu_onehot(idx: int) -> Bits:
    return Bits(RV32I_ALU.CNT)(1 << idx)


def encode_r(funct7: int, rs2: int, rs1: int, funct3: int, rd: int, opcode: int = 0b0110011) -> int:
    return ((mask_bits(funct7, 7) << 25) |
            (mask_bits(rs2, 5) << 20) |
            (mask_bits(rs1, 5) << 15) |
            (mask_bits(funct3, 3) << 12) |
            (mask_bits(rd, 5) << 7) |
            mask_bits(opcode, 7))


def encode_i(imm: int, rs1: int, funct3: int, rd: int, opcode: int) -> int:
    imm12 = mask_bits(imm, 12)
    return ((imm12 << 20) |
            (mask_bits(rs1, 5) << 15) |
            (mask_bits(funct3, 3) << 12) |
            (mask_bits(rd, 5) << 7) |
            mask_bits(opcode, 7))


def encode_s(imm: int, rs1: int, rs2: int, funct3: int, opcode: int = 0b0100011) -> int:
    imm12 = mask_bits(imm, 12)
    imm11_5 = (imm12 >> 5) & 0x7F
    imm4_0 = imm12 & 0x1F
    return ((imm11_5 << 25) |
            (mask_bits(rs2, 5) << 20) |
            (mask_bits(rs1, 5) << 15) |
            (mask_bits(funct3, 3) << 12) |
            (imm4_0 << 7) |
            mask_bits(opcode, 7))


def encode_b(imm: int, rs1: int, rs2: int, funct3: int, opcode: int = 0b1100011) -> int:
    if imm % 2 != 0:
        raise ValueError("branch immediate must be 2-byte aligned")
    imm13 = mask_bits(imm, 13)
    imm12 = (imm13 >> 12) & 0x1
    imm11 = (imm13 >> 11) & 0x1
    imm10_5 = (imm13 >> 5) & 0x3F
    imm4_1 = (imm13 >> 1) & 0xF
    return ((imm12 << 31) |
            (imm10_5 << 25) |
            (mask_bits(rs2, 5) << 20) |
            (mask_bits(rs1, 5) << 15) |
            (mask_bits(funct3, 3) << 12) |
            (imm4_1 << 8) |
            (imm11 << 7) |
            mask_bits(opcode, 7))


def encode_u(imm20: int, rd: int, opcode: int) -> int:
    return ((mask_bits(imm20, 20) << 12) |
            (mask_bits(rd, 5) << 7) |
            mask_bits(opcode, 7))


def encode_j(imm: int, rd: int, opcode: int = 0b1101111) -> int:
    if imm % 2 != 0:
        raise ValueError("jump immediate must be 2-byte aligned")
    imm21 = mask_bits(imm, 21)
    imm20 = (imm21 >> 20) & 0x1
    imm10_1 = (imm21 >> 1) & 0x3FF
    imm11 = (imm21 >> 11) & 0x1
    imm19_12 = (imm21 >> 12) & 0xFF
    return ((imm20 << 31) |
            (imm10_1 << 21) |
            (imm11 << 20) |
            (imm19_12 << 12) |
            (mask_bits(rd, 5) << 7) |
            mask_bits(opcode, 7))


def bits32(value: int) -> Bits:
    return Bits(32)(value & 0xFFFFFFFF)


def eval_value(node):
    if isinstance(node, Operand):
        return eval_value(node.value)
    if isinstance(node, RecordValue):
        return eval_value(node.value())
    if isinstance(node, Const):
        return node.value
    if isinstance(node, Slice):
        base = eval_value(node.x)
        l = eval_value(node.l)
        r = eval_value(node.r)
        mask = (1 << (r - l + 1)) - 1
        return (base >> l) & mask
    if isinstance(node, Concat):
        lsb = eval_value(node.lsb)
        msb = eval_value(node.msb)
        return (msb << node.lsb.dtype.bits) | lsb
    if isinstance(node, Cast):
        val = eval_value(node.x)
        src_bits = node.x.dtype.bits
        tgt_bits = node.dtype.bits
        mask = (1 << tgt_bits) - 1
        if node.opcode == Cast.SEXT:
            sign_bit = 1 << (src_bits - 1)
            if val & sign_bit:
                val = (val | (~((1 << src_bits) - 1))) & ((1 << max(src_bits, tgt_bits)) - 1)
        return val & mask
    if isinstance(node, BinaryOp):
        lhs = eval_value(node.lhs)
        rhs = eval_value(node.rhs)
        if node.opcode == BinaryOp.ADD:
            return lhs + rhs
        if node.opcode == BinaryOp.SUB:
            return lhs - rhs
        if node.opcode == BinaryOp.BITWISE_AND:
            return lhs & rhs
        if node.opcode == BinaryOp.BITWISE_OR:
            return lhs | rhs
        if node.opcode == BinaryOp.BITWISE_XOR:
            return lhs ^ rhs
        if node.opcode == BinaryOp.SHL:
            return lhs << rhs
        if node.opcode == BinaryOp.SHR:
            return lhs >> rhs
        if node.opcode == BinaryOp.EQ:
            return int(lhs == rhs)
        if node.opcode == BinaryOp.NEQ:
            return int(lhs != rhs)
        if node.opcode == BinaryOp.ILT:
            return int(lhs < rhs)
        if node.opcode == BinaryOp.IGT:
            return int(lhs > rhs)
        if node.opcode == BinaryOp.ILE:
            return int(lhs <= rhs)
        if node.opcode == BinaryOp.IGE:
            return int(lhs >= rhs)
    if isinstance(node, UnaryOp):
        val = eval_value(node.x)
        if node.opcode == UnaryOp.NEG:
            return -val
        if node.opcode == UnaryOp.FLIP:
            return ~val
    if isinstance(node, Select):
        cond = eval_value(node.cond)
        return eval_value(node.true_value if cond else node.false_value)
    if isinstance(node, Select1Hot):
        cond = eval_value(node.cond)
        for idx, val in enumerate(node.values):
            if cond & (1 << idx):
                return eval_value(val)
        return 0
    raise TypeError(f"Cannot eval node of type {type(node)}: {node}")


@contextmanager
def decoder_env():
    with SysBuilder("decoder_unit") as builder:
        dummy = Module(ports={})
        dummy.body = []
        builder.enter_context_of(dummy)
        try:
            yield
        finally:
            builder.exit_context_of()


@contextmanager
def decoded(inst: int):
    with decoder_env():
        yield decoder_logic(Bits(32)(inst))


class DecoderCoverageTest(unittest.TestCase):
    def resolve(self, value):
        try:
            return eval_value(value)
        except TypeError:
            return repr(value)

    def check_fields(self, sigs, expected):
        for key, value in expected.items():
            actual = getattr(sigs, key)
            actual_resolved = self.resolve(actual)
            expected_resolved = self.resolve(value)
            self.assertEqual(actual_resolved, expected_resolved,
                             msg=f"{key} mismatch (actual={actual_resolved}, expected={expected_resolved})")

    def test_r_type_decoding(self):
        add_inst = encode_r(0b0000000, 7, 6, 0b000, 5)
        with decoded(add_inst) as sigs:
            self.check_fields(sigs, {
                "rs1": Bits(5)(6),
                "rs2": Bits(5)(7),
                "rd": Bits(5)(5),
                "rs1_used": Bits(1)(1),
                "rs2_used": Bits(1)(1),
                "rd_used": Bits(1)(1),
                "alu_type": alu_onehot(RV32I_ALU.ALU_ADD),
            })

        sub_inst = encode_r(0b0100000, 3, 2, 0b000, 1)
        with decoded(sub_inst) as sigs:
            self.check_fields(sigs, {
                "rs1": Bits(5)(2),
                "rs2": Bits(5)(3),
                "rd": Bits(5)(1),
                "alu_type": alu_onehot(RV32I_ALU.ALU_SUB),
            })

    def test_i_type_arith_and_load_and_jalr(self):
        addi_inst = encode_i(sext(-4, 12), 2, 0b000, 1, 0b0010011)
        with decoded(addi_inst) as sigs:
            self.check_fields(sigs, {
                "rs1": Bits(5)(2),
                "rd": Bits(5)(1),
                "imm": bits32(sext(-4, 12)),
                "rs1_used": Bits(1)(1),
                "rs2_used": Bits(1)(0),
                "rd_used": Bits(1)(1),
                "mem_read": Bits(1)(0),
                "mem_write": Bits(1)(0),
                "is_branch": Bits(1)(0),
                "is_jal": Bits(1)(0),
                "is_jalr": Bits(1)(0),
                "alu_type": alu_onehot(RV32I_ALU.ALU_ADD),
            })

        jalr_inst = encode_i(8, 4, 0b000, 5, 0b1100111)
        with decoded(jalr_inst) as sigs:
            self.check_fields(sigs, {
                "rs1": Bits(5)(4),
                "rd": Bits(5)(5),
                "imm": bits32(8),
                "is_branch": Bits(1)(1),
                "is_jal": Bits(1)(0),
                "is_jalr": Bits(1)(1),
            })

        lw_inst = encode_i(12, 3, 0b010, 8, 0b0000011)
        with decoded(lw_inst) as sigs:
            self.check_fields(sigs, {
                "rs1": Bits(5)(3),
                "rd": Bits(5)(8),
                "imm": bits32(12),
                "mem_read": Bits(1)(1),
                "mem_write": Bits(1)(0),
                "is_branch": Bits(1)(0),
            })

    def test_shift_immediates(self):
        slli_inst = encode_i(1, 1, 0b001, 2, 0b0010011)
        with decoded(slli_inst) as sigs:
            self.check_fields(sigs, {
                "rs1": Bits(5)(1),
                "rd": Bits(5)(2),
                "alu_type": alu_onehot(RV32I_ALU.ALU_SLL),
            })

        srai_inst = encode_i((0b0100000 << 5) | 7, 10, 0b101, 9, 0b0010011)
        with decoded(srai_inst) as sigs:
            self.check_fields(sigs, {
                "rs1": Bits(5)(10),
                "rd": Bits(5)(9),
                "imm": bits32((0b0100000 << 5) | 7),
                "alu_type": alu_onehot(RV32I_ALU.ALU_SRA),
            })

    def test_store_and_branch(self):
        sw_inst = encode_s(16, 9, 8, 0b010)
        with decoded(sw_inst) as sigs:
            self.check_fields(sigs, {
                "rs1": Bits(5)(9),
                "rs2": Bits(5)(8),
                "imm": bits32(16),
                "mem_read": Bits(1)(0),
                "mem_write": Bits(1)(1),
                "is_branch": Bits(1)(0),
            })

        beq_inst = encode_b(sext(-4, 13), 1, 2, 0b000)
        with decoded(beq_inst) as sigs:
            self.check_fields(sigs, {
                "rs1": Bits(5)(1),
                "rs2": Bits(5)(2),
                "imm": bits32(sext(-4, 13)),
                "is_branch": Bits(1)(1),
                "branch_type": Bits(3)(0b000),
            })

    def test_u_and_j_types(self):
        lui_inst = encode_u(0x12345, 3, 0b0110111)
        with decoded(lui_inst) as sigs:
            self.check_fields(sigs, {
                "rd": Bits(5)(3),
                "imm": bits32(0x12345000),
                "rd_used": Bits(1)(1),
            })

        auipc_inst = encode_u(0x1, 6, 0b0010111)
        with decoded(auipc_inst) as sigs:
            self.check_fields(sigs, {
                "rd": Bits(5)(6),
                "imm": bits32(0x1000),
                "rd_used": Bits(1)(1),
            })

        jal_inst = encode_j(0x10, 1)
        with decoded(jal_inst) as sigs:
            self.check_fields(sigs, {
                "rd": Bits(5)(1),
                "imm": bits32(0x10),
                "is_branch": Bits(1)(1),
                "is_jal": Bits(1)(1),
                "is_jalr": Bits(1)(0),
            })

    def test_system_instructions(self):
        ecall_inst = 0x00000073
        with decoded(ecall_inst) as sigs:
            self.check_fields(sigs, {
                "rd_used": Bits(1)(0),
                "rs1_used": Bits(1)(1),
                "rs1": Bits(5)(0),
            })

        ebreak_inst = 0x00100073
        with decoded(ebreak_inst) as sigs:
            self.check_fields(sigs, {
                "rd_used": Bits(1)(0),
                "rs1_used": Bits(1)(1),
                "rs1": Bits(5)(0),
            })


if __name__ == "__main__":
    unittest.main()

# unittests/asm_utils.py

class ASM:
    """
    一个简单的 RISC-V 指令编码器工具类。
    用于在测试中生成机器码。
    """
    @staticmethod
    def _encode_r(opcode, funct3, funct7, rd, rs1, rs2):
        return (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode

    @staticmethod
    def _encode_i(opcode, funct3, rd, rs1, imm):
        imm = int(imm) & 0xFFF # 强转 int 防止传入 string
        return (imm << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode

    @staticmethod
    def _encode_s(opcode, funct3, rs1, rs2, imm):
        imm = int(imm) & 0xFFF
        imm11_5 = (imm >> 5) & 0x7F
        imm4_0 = imm & 0x1F
        return (imm11_5 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (imm4_0 << 7) | opcode

    @staticmethod
    def _encode_b(opcode, funct3, rs1, rs2, imm):
        imm = int(imm) & 0x1FFF
        imm12 = (imm >> 12) & 0x1
        imm10_5 = (imm >> 5) & 0x3F
        imm4_1 = (imm >> 1) & 0xF
        imm11 = (imm >> 11) & 0x1
        return (imm12 << 31) | (imm10_5 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (imm4_1 << 8) | (imm11 << 7) | opcode

    @staticmethod
    def _encode_u(opcode, rd, imm):
        imm = int(imm) & 0xFFFFF000
        return (imm) | (rd << 7) | opcode

    @staticmethod
    def _encode_j(opcode, rd, imm):
        imm = int(imm) & 0x1FFFFF
        # imm[20|10:1|11|19:12]
        imm20 = (imm >> 20) & 0x1
        imm10_1 = (imm >> 1) & 0x3FF
        imm11 = (imm >> 11) & 0x1
        imm19_12 = (imm >> 12) & 0xFF
        return (imm20 << 31) | (imm19_12 << 12) | (imm11 << 20) | (imm10_1 << 21) | (rd << 7) | opcode

    # --- 公开的指令接口 ---
    
    @classmethod
    def addi(cls, rd, rs1, imm):
        return cls._encode_i(0b0010011, 0b000, rd, rs1, imm)

    @classmethod
    def add(cls, rd, rs1, rs2):
        return cls._encode_r(0b0110011, 0b000, 0b0000000, rd, rs1, rs2)
    @classmethod
    def sub(cls, rd, rs1, rs2):
        return cls._encode_r(0b0110011, 0b000, 0b0100000, rd, rs1, rs2)

    @classmethod
    def and_(cls, rd, rs1, rs2):
        return cls._encode_r(0b0110011, 0b111, 0b0000000, rd, rs1, rs2)

    @classmethod
    def or_(cls, rd, rs1, rs2):
        return cls._encode_r(0b0110011, 0b110, 0b0000000, rd, rs1, rs2)

    @classmethod
    def xor(cls, rd, rs1, rs2):
        return cls._encode_r(0b0110011, 0b100, 0b0000000, rd, rs1, rs2)

    @classmethod
    def sll(cls, rd, rs1, rs2):
        return cls._encode_r(0b0110011, 0b001, 0b0000000, rd, rs1, rs2)

    @classmethod
    def srl(cls, rd, rs1, rs2):
        return cls._encode_r(0b0110011, 0b101, 0b0000000, rd, rs1, rs2)

    @classmethod
    def sra(cls, rd, rs1, rs2):
        return cls._encode_r(0b0110011, 0b101, 0b0100000, rd, rs1, rs2)

    @classmethod
    def slt(cls, rd, rs1, rs2):
        return cls._encode_r(0b0110011, 0b010, 0b0000000, rd, rs1, rs2)

    @classmethod
    def sltu(cls, rd, rs1, rs2):
        return cls._encode_r(0b0110011, 0b011, 0b0000000, rd, rs1, rs2)
        
    @classmethod
    def sw(cls, rs1, rs2, imm):
        return cls._encode_s(0b0100011, 0b010, rs1, rs2, imm)

    @classmethod
    def lw(cls, rd, rs1, imm):
        return cls._encode_i(0b0000011, 0b010, rd, rs1, imm)
    
    @classmethod
    def beq(cls, rs1, rs2, imm):
        return cls._encode_b(0b1100011, 0b000, rs1, rs2, imm)
    
    @classmethod
    def bne(cls, rs1, rs2, imm):
        return cls._encode_b(0b1100011, 0b001, rs1, rs2, imm)

    @classmethod
    def blt(cls, rs1, rs2, imm):
        return cls._encode_b(0b1100011, 0b100, rs1, rs2, imm)

    @classmethod
    def bge(cls, rs1, rs2, imm):
        return cls._encode_b(0b1100011, 0b101, rs1, rs2, imm)

    @classmethod
    def bltu(cls, rs1, rs2, imm):
        return cls._encode_b(0b1100011, 0b110, rs1, rs2, imm)

    @classmethod
    def bgeu(cls, rs1, rs2, imm):
        return cls._encode_b(0b1100011, 0b111, rs1, rs2, imm)

    @classmethod
    def andi(cls, rd, rs1, imm):
        return cls._encode_i(0b0010011, 0b111, rd, rs1, imm)

    @classmethod
    def ori(cls, rd, rs1, imm):
        return cls._encode_i(0b0010011, 0b110, rd, rs1, imm)

    @classmethod
    def xori(cls, rd, rs1, imm):
        return cls._encode_i(0b0010011, 0b100, rd, rs1, imm)

    @classmethod
    def slli(cls, rd, rs1, shamt):
        return cls._encode_i(0b0010011, 0b001, rd, rs1, shamt)

    @classmethod
    def srli(cls, rd, rs1, shamt):
        # srli uses funct7=0000000 encoded in imm[11:0]
        return cls._encode_i(0b0010011, 0b101, rd, rs1, shamt)

    @classmethod
    def srai(cls, rd, rs1, shamt):
        # srai uses funct7=0100000 placed in imm[11:0]
        imm = (0b0100000 << 5) | (int(shamt) & 0x1F)
        return cls._encode_i(0b0010011, 0b101, rd, rs1, imm)

    @classmethod
    def slti(cls, rd, rs1, imm):
        return cls._encode_i(0b0010011, 0b010, rd, rs1, imm)

    @classmethod
    def sltiu(cls, rd, rs1, imm):
        return cls._encode_i(0b0010011, 0b011, rd, rs1, imm)

    @classmethod
    def jal(cls, rd, imm):
        return cls._encode_j(0b1101111, rd, imm)

    @classmethod
    def jalr(cls, rd, rs1, imm):
        return cls._encode_i(0b1100111, 0b000, rd, rs1, imm)

    @classmethod
    def lui(cls, rd, imm):
        return cls._encode_u(0b0110111, rd, imm)

    @classmethod
    def auipc(cls, rd, imm):
        return cls._encode_u(0b0010111, rd, imm)

    @classmethod
    def nop(cls):
        return cls.addi(0, 0, 0)

    @classmethod
    def ebreak(cls):
        # I-type, opcode=1110011, funct3=000, imm=1, rs1=0, rd=0
        return cls._encode_i(0b1110011, 0b000, 0, 0, 1)

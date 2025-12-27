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
        imm = int(imm)
        imm11_5 = (imm >> 5) & 0x7F
        imm4_0 = imm & 0x1F
        return (imm11_5 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (imm4_0 << 7) | opcode

    @staticmethod
    def _encode_b(opcode, funct3, rs1, rs2, imm):
        imm = int(imm)
        imm12 = (imm >> 12) & 0x1
        imm10_5 = (imm >> 5) & 0x3F
        imm4_1 = (imm >> 1) & 0xF
        imm11 = (imm >> 11) & 0x1
        return (imm12 << 31) | (imm10_5 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (imm4_1 << 8) | (imm11 << 7) | opcode

    # --- 公开的指令接口 ---
    
    @classmethod
    def addi(cls, rd, rs1, imm):
        return cls._encode_i(0b0010011, 0b000, rd, rs1, imm)

    @classmethod
    def add(cls, rd, rs1, rs2):
        return cls._encode_r(0b0110011, 0b000, 0b0000000, rd, rs1, rs2)
        
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
    def nop(cls):
        return cls.addi(0, 0, 0)
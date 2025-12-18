// 测试逻辑运算 AND, OR, XOR
// (0xF0 & 0x0F) | 0x33 ^ 0x11 = 0 | 0x33 ^ 0x11 = 0x22 = 34
void _start() __attribute__((naked));

void _start() {
    asm volatile (
        "li t0, 0xF0\n"
        "li t1, 0x0F\n"
        "and t2, t0, t1\n"    // t2 = 0xF0 & 0x0F = 0
        "li t3, 0x33\n"
        "or t2, t2, t3\n"     // t2 = 0 | 0x33 = 0x33
        "li t4, 0x11\n"
        "xor a0, t2, t4\n"    // a0 = 0x33 ^ 0x11 = 0x22 = 34
        "nop\n"
        "nop\n"
        "nop\n"
        "ebreak\n"
    );
}

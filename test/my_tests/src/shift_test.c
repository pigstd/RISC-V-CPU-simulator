// 测试移位操作
// 1 << 4 = 16, 16 >> 2 = 4
void _start() __attribute__((naked));

void _start() {
    asm volatile (
        "li t0, 1\n"
        "slli t0, t0, 4\n"    // t0 = 1 << 4 = 16
        "srli a0, t0, 2\n"    // a0 = 16 >> 2 = 4
        "nop\n"
        "nop\n"
        "nop\n"
        "ebreak\n"
    );
}

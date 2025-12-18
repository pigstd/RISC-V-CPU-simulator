// 非常简单的测试 - 不使用栈和内存
// 只使用寄存器来计算 1+2+3+4+5 = 15

void _start() __attribute__((naked));

void _start() {
    asm volatile (
        // 计算 1+2+3+4+5
        "li a0, 1\n"
        "addi a0, a0, 2\n"    // a0 = 3
        "addi a0, a0, 3\n"    // a0 = 6
        "addi a0, a0, 4\n"    // a0 = 10
        "addi a0, a0, 5\n"    // a0 = 15
        "nop\n"
        "nop\n"
        "nop\n"
        "ebreak\n"
    );
}

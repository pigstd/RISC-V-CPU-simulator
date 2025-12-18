// 测试比较指令 SLT/SLTU
// 结果: (5 < 10) + (10 < 5) + (-1 <u 1) = 1 + 0 + 0 = 1
void _start() __attribute__((naked));

void _start() {
    asm volatile (
        "li t0, 5\n"
        "li t1, 10\n"
        "slt t2, t0, t1\n"    // t2 = (5 < 10) = 1
        "slt t3, t1, t0\n"    // t3 = (10 < 5) = 0
        "li t4, -1\n"
        "li t5, 1\n"
        "sltu t6, t4, t5\n"   // t6 = (-1 as unsigned) < 1 = 0 (0xFFFFFFFF > 1)
        "add a0, t2, t3\n"    // a0 = 1 + 0 = 1
        "add a0, a0, t6\n"    // a0 = 1 + 0 = 1
        "nop\n"
        "nop\n"
        "nop\n"
        "ebreak\n"
    );
}

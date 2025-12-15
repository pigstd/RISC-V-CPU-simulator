// 简单循环测试 - 只用寄存器
// 计算 sum(1..10) = 55

void _start() __attribute__((naked));

void _start() {
    asm volatile (
        // t0 = counter, t1 = limit, a0 = sum
        "li t0, 1\n"          // i = 1
        "li t1, 11\n"         // limit = 11
        "li a0, 0\n"          // sum = 0
        
        "loop:\n"
        "add a0, a0, t0\n"    // sum += i
        "addi t0, t0, 1\n"    // i++
        "blt t0, t1, loop\n"  // if i < 11, goto loop
        
        "nop\n"
        "nop\n"
        "nop\n"
        "ebreak\n"
    );
}

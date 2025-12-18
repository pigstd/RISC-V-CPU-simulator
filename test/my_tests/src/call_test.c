// 测试 JAL/JALR 函数调用
// 调用一个简单函数计算 a0 + 10，传入 a0=5，期望返回 15
void _start() __attribute__((naked));

void _start() {
    asm volatile (
        "li a0, 5\n"          // 参数 = 5
        "jal ra, add_ten\n"   // 调用函数
        "nop\n"
        "nop\n"
        "nop\n"
        "ebreak\n"
        
        "add_ten:\n"
        "addi a0, a0, 10\n"   // a0 = a0 + 10
        "jalr zero, ra, 0\n"  // 返回 (ret)
    );
}

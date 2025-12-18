// 计算最大公约数 GCD(48, 18) = 6
int main() {
    int a = 48;
    int b = 18;
    int temp;
    
    // 欧几里得算法
    while (b != 0) {
        temp = b;
        b = a % b;  // 注意: 需要硬件支持 REM 指令，或者用软件实现
        a = temp;
    }
    
    // GCD(48, 18) = 6
    asm volatile (
        "mv a0, %0\n"
        "nop\n"
        "nop\n"
        "nop\n"
        "ebreak"
        :
        : "r" (a)
        : "a0"
    );
    return 0;
}

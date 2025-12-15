// 统计整数中 1 的个数 (popcount)
// 0b10110101 = 181, 有 5 个 1
int main() {
    int n = 181;  // 0b10110101
    int count = 0;
    
    while (n != 0) {
        count = count + (n & 1);
        n = n >> 1;
    }
    
    // 181 has 5 ones
    asm volatile (
        "mv a0, %0\n"
        "nop\n"
        "nop\n"
        "nop\n"
        "ebreak"
        :
        : "r" (count)
        : "a0"
    );
    return 0;
}

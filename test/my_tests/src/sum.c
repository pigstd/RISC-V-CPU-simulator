// 计算 1+2+3+...+10 = 55
int main() {
    int n = 10;
    int sum = 0;
    int i;
    
    for (i = 1; i <= n; i++) {
        sum = sum + i;
    }
    
    // Sum(1..10) = 55
    asm volatile (
        "mv a0, %0\n"
        "nop\n"
        "nop\n"
        "nop\n"
        "ebreak"
        :
        : "r" (sum)
        : "a0"
    );
    return 0;
}

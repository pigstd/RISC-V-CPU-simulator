// 判断 17 是否为素数 (1=是, 0=否)
int main() {
    int n = 17;
    int is_prime = 1;
    int i;
    
    if (n <= 1) {
        is_prime = 0;
    } else {
        for (i = 2; i * i <= n; i++) {
            if (n % i == 0) {
                is_prime = 0;
                break;
            }
        }
    }
    
    // 17 is prime, result = 1
    asm volatile (
        "mv a0, %0\n"
        "nop\n"
        "nop\n"
        "nop\n"
        "ebreak"
        :
        : "r" (is_prime)
        : "a0"
    );
    return 0;
}

int main() {
    int n = 10;
    int a = 0, b = 1, c, i;
    if (n == 0) c = a;
    else {
        for (i = 2; i <= n; i++) {
            c = a + b;
            a = b;
            b = c;
        }
    }
    // Fib(10) = 55
    asm volatile (
        "mv a0, %0\n"
        "nop\n"
        "nop\n"
        "nop\n"
        "ebreak"
        :
        : "r" (c)
        : "a0"
    );
    return 0;
}

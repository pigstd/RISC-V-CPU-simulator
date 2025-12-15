// Fibonacci(10) = 55 - 只用寄存器实现
void _start() __attribute__((naked));

void _start() {
    asm volatile (
        // t0 = fib(n-2), t1 = fib(n-1), t2 = temp
        // t3 = counter, t4 = n
        "li t0, 0\n"          // fib(0) = 0
        "li t1, 1\n"          // fib(1) = 1
        "li t3, 2\n"          // counter = 2
        "li t4, 10\n"         // n = 10
        
        "fib_loop:\n"
        "add t2, t0, t1\n"    // t2 = fib(n-2) + fib(n-1)
        "mv t0, t1\n"         // fib(n-2) = fib(n-1)
        "mv t1, t2\n"         // fib(n-1) = new fib
        "addi t3, t3, 1\n"    // counter++
        "ble t3, t4, fib_loop\n" // if counter <= n, continue
        
        "mv a0, t1\n"         // result = fib(n)
        "nop\n"
        "nop\n"
        "nop\n"
        "ebreak\n"
    );
}

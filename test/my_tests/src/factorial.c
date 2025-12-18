// 计算阶乘 5! = 120
// 使用循环加法代替乘法 (RV32I 没有 MUL 指令)

// 用加法实现乘法
int multiply(int a, int b) {
    int result = 0;
    int negative = 0;
    
    // 处理负数
    if (a < 0) {
        a = -a;
        negative = !negative;
    }
    if (b < 0) {
        b = -b;
        negative = !negative;
    }
    
    // 循环加法
    while (b > 0) {
        result = result + a;
        b = b - 1;
    }
    
    return negative ? -result : result;
}

int main() {
    int n = 5;
    int result = 1;
    int i;
    
    for (i = 1; i <= n; i++) {
        result = multiply(result, i);
    }
    
    // 5! = 120
    asm volatile (
        "mv a0, %0\n"
        "nop\n"
        "nop\n"
        "nop\n"
        "ebreak"
        :
        : "r" (result)
        : "a0"
    );
    return 0;
}

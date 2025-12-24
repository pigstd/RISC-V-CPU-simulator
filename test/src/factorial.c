// 阶乘 5! = 120
// 使用快速乘（RV32I 无 MUL 指令）

int multiply(int a, int b) {
    int result = 0;
    int neg = 0;
    
    if (a < 0) { a = -a; neg = !neg; }
    if (b < 0) { b = -b; neg = !neg; }
    
    // 快速乘: O(log b)
    while (b) {
        if (b & 1) result += a;
        a <<= 1;
        b >>= 1;
    }
    
    return neg ? -result : result;
}

int main() {
    int n = 5;
    int result = 1;
    
    for (int i = 1; i <= n; i++) {
        result = multiply(result, i);
    }
    
    return result;  // 预期: 120
}

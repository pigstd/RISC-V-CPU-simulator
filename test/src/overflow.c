// 整数溢出测试
// 测试 32 位有符号整数加法和乘法溢出行为

// 快速乘: O(log b)
int multiply(int a, int b) {
    int result = 0;
    int neg = 0;
    
    if (a < 0) { a = -a; neg = !neg; }
    if (b < 0) { b = -b; neg = !neg; }
    
    while (b) {
        if (b & 1) result += a;
        a <<= 1;
        b >>= 1;
    }
    
    return neg ? -result : result;
}

int main() {
    int correct = 0;
    
    // 测试 1: 大数加法溢出
    // 2147483647 + 1 = -2147483648 (溢出)
    int max_int = 2147483647;  // 0x7FFFFFFF
    int overflow_add = max_int + 1;
    if (overflow_add == -2147483648) correct++;  // -2147483648 = 0x80000000
    
    // 测试 2: 大数加法溢出
    // 2000000000 + 2000000000 = -294967296 (溢出)
    int a = 2000000000;
    int b = 2000000000;
    int sum = a + b;  // 4000000000 溢出为 -294967296
    if (sum == -294967296) correct++;
    
    // 测试 3: 负数溢出
    // -2147483648 - 1 = 2147483647 (溢出)
    int min_int = -2147483648;  // 0x80000000
    int overflow_sub = min_int - 1;
    if (overflow_sub == 2147483647) correct++;
    
    // 测试 4: 乘法溢出
    // 100000 * 100000 = 10000000000 溢出为 1410065408
    int x = 100000;
    int y = 100000;
    int product = multiply(x, y);
    // 10000000000 mod 2^32 = 1410065408 (0x540BE400)
    if (product == 1410065408) correct++;
    
    // 测试 5: 更大的乘法溢出
    // 50000 * 50000 = 2500000000 溢出为 -1794967296
    int p = 50000;
    int q = 50000;
    int prod2 = multiply(p, q);
    // 2500000000 作为有符号 32 位 = -1794967296
    if (prod2 == -1794967296) correct++;
    
    // 测试 6: 连续溢出
    int val = 1073741824;  // 2^30
    val = val + val;       // 2^31 = -2147483648 (溢出)
    val = val + val;       // -2^32 mod 2^32 = 0
    if (val == 0) correct++;
    
    // 测试 7: 左移溢出
    int shift_val = 1;
    for (int i = 0; i < 31; i++) {
        shift_val = shift_val << 1;
    }
    // 1 << 31 = -2147483648 (0x80000000)
    if (shift_val == -2147483648) correct++;
    
    // 测试 8: 乘以 -1 溢出
    // -2147483648 * -1 仍然是 -2147483648 (溢出)
    int neg_min = -2147483648;
    int neg_one = -1;
    int overflow_mul = multiply(neg_min, neg_one);
    if (overflow_mul == -2147483648) correct++;
    
    return correct;  // 预期: 8 (全部正确)
}

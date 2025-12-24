// 2x2 矩阵乘法
// 使用快速乘（RV32I 无 MUL 指令）

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
    // A = | 1  2 |    B = | 5  6 |
    //     | 3  4 |        | 7  8 |
    // C = | 19  22 |
    //     | 43  50 |
    
    int A[2][2] = {{1, 2}, {3, 4}};
    int B[2][2] = {{5, 6}, {7, 8}};
    int C[2][2];
    
    // 矩阵乘法
    for (int i = 0; i < 2; i++) {
        for (int j = 0; j < 2; j++) {
            C[i][j] = 0;
            for (int k = 0; k < 2; k++) {
                C[i][j] += multiply(A[i][k], B[k][j]);
            }
        }
    }
    
    // 验证
    int expected[2][2] = {{19, 22}, {43, 50}};
    int correct = 0;
    for (int i = 0; i < 2; i++) {
        for (int j = 0; j < 2; j++) {
            if (C[i][j] == expected[i][j]) correct++;
        }
    }
    
    return correct;  // 预期: 4 (全部正确)
}

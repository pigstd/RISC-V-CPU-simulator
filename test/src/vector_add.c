// 向量加法: C = A + B
int main() {
    int n = 10;
    int a[10] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    int b[10] = {11, 12, 13, 14, 15, 16, 17, 18, 19, 20};
    int c[10];
    
    // 向量加法
    for (int i = 0; i < n; i++) {
        c[i] = a[i] + b[i];
    }
    
    // 预期: c = {12, 14, 16, 18, 20, 22, 24, 26, 28, 30}
    int expected[10] = {12, 14, 16, 18, 20, 22, 24, 26, 28, 30};
    
    // 验证每个元素
    int correct = 0;
    for (int i = 0; i < n; i++) {
        if (c[i] == expected[i]) correct++;
    }
    
    return correct;  // 预期: 10 (全部正确)
}

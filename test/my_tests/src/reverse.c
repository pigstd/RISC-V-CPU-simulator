// 翻转数组
int main() {
    int arr[5] = {1, 2, 3, 4, 5};
    int n = 5;
    int i, temp;
    
    // 翻转数组
    for (i = 0; i < n / 2; i++) {
        temp = arr[i];
        arr[i] = arr[n - 1 - i];
        arr[n - 1 - i] = temp;
    }
    
    // 翻转后: {5, 4, 3, 2, 1}
    // 返回第一个元素验证
    int result = arr[0];  // 应该是 5
    
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

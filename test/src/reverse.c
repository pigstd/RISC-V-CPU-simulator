// 翻转数组
int main() {
    int arr[5] = {1, 2, 3, 4, 5};
    int n = 5;
    int temp;
    
    // 翻转数组
    for (int i = 0; i < n / 2; i++) {
        temp = arr[i];
        arr[i] = arr[n - 1 - i];
        arr[n - 1 - i] = temp;
    }
    
    // 翻转后: {5, 4, 3, 2, 1}
    // 验证：返回第一个元素
    return arr[0];  // 预期: 5
}

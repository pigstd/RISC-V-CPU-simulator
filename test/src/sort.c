// 冒泡排序
int main() {
    int arr[5] = {5, 2, 4, 1, 3};
    int n = 5;
    int temp;
    
    // 冒泡排序
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
    
    // 验证: 排序后 {1,2,3,4,5}, 返回总和 15
    int sum = 0;
    for (int i = 0; i < n; i++) {
        sum += arr[i];
    }
    
    // 额外验证首尾元素
    if (arr[0] != 1 || arr[4] != 5) {
        sum = 0;
    }
    
    return sum;  // 预期: 15
}

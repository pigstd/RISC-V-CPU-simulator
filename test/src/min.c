// 求数组最小值
int main() {
    int arr[8] = {7, 3, 9, 1, 5, 8, 2, 6};
    int n = 8;
    int min_val = arr[0];
    
    for (int i = 1; i < n; i++) {
        if (arr[i] < min_val) {
            min_val = arr[i];
        }
    }
    
    return min_val;  // 预期: 1
}

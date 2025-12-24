// 统计数组中偶数个数
int main() {
    int arr[10] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    int n = 10;
    int count = 0;
    
    for (int i = 0; i < n; i++) {
        if ((arr[i] & 1) == 0) {
            count++;
        }
    }
    
    return count;  // 预期: 5 (2,4,6,8,10)
}

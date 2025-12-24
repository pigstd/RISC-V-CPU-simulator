// 数组求和
int main() {
    int arr[6] = {10, 20, 30, 40, 50, 60};
    int n = 6;
    int sum = 0;
    
    for (int i = 0; i < n; i++) {
        sum += arr[i];
    }
    
    return sum;  // 预期: 210
}

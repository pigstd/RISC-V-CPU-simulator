// 找数组中的最大值
int main() {
    int arr[6] = {3, 7, 2, 9, 4, 1};
    int n = 6;
    int max_val = arr[0];
    int i;
    
    for (i = 1; i < n; i++) {
        if (arr[i] > max_val) {
            max_val = arr[i];
        }
    }
    
    return max_val;
}

// 二分查找
int main() {
    int arr[10] = {1, 3, 5, 7, 9, 11, 13, 15, 17, 19};
    int target = 13;
    int n = 10;
    
    int left = 0;
    int right = n - 1;
    int result = -1;
    
    while (left <= right) {
        int mid = left + ((right - left) >> 1);
        if (arr[mid] == target) {
            result = mid;
            break;
        } else if (arr[mid] < target) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    
    return result;  // 预期: 6 (arr[6] = 13)
}

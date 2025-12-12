int main() {
    int arr[5] = {5, 2, 4, 1, 3};
    int n = 5;
    int i, j, temp;
    for (i = 0; i < n-1; i++) {
        for (j = 0; j < n-i-1; j++) {
            if (arr[j] > arr[j+1]) {
                temp = arr[j];
                arr[j] = arr[j+1];
                arr[j+1] = temp;
            }
        }
    }
    // Check if sorted: 1, 2, 3, 4, 5. Sum = 15.
    int sum = 0;
    for(i=0; i<n; ++i) sum += arr[i];
    
    // Verify first and last element specifically to be sure
    if (arr[0] != 1 || arr[4] != 5) sum = 0;

    asm volatile (
        "mv a0, %0\n"
        "nop\n"
        "nop\n"
        "nop\n"
        "ebreak"
        :
        : "r" (sum)
        : "a0"
    );
    return 0;
}

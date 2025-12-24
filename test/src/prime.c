// 判断素数
// 检查 17 是否为素数 (是)

int main() {
    int n = 17;
    int is_prime = 1;
    
    if (n <= 1) {
        is_prime = 0;
    } else {
        for (int i = 2; i < n; i++) {
            // 检查 n % i == 0 (用减法模拟)
            int temp = n;
            while (temp >= i) {
                temp -= i;
            }
            if (temp == 0) {
                is_prime = 0;
                break;
            }
        }
    }
    
    return is_prime;  // 预期: 1 (17是素数)
}

// 统计二进制中 1 的个数 (popcount)
// 181 = 0b10110101, 有 5 个 1
int main() {
    int n = 181;
    int count = 0;
    
    while (n != 0) {
        count += (n & 1);
        n >>= 1;
    }
    
    return count;  // 预期: 5
}

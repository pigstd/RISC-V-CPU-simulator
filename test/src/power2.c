// 递推求 2^8 = 256，然后验证结果
int main() {
    int base = 2;
    int exp = 8;
    int result = 1;
    
    for (int i = 0; i < exp; i++) {
        result = result + result;  // result *= 2
    }
    
    // 2^8 = 256, 验证后返回 8
    return (result == 256) ? 8 : 0;  // 预期: 8
}

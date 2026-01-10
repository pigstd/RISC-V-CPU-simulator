// 测试负数的 Load Word 指令
// 注意：当前 CPU 只支持 LW (字加载)

int main() {
    volatile int data[4];
    data[0] = 1000;
    data[1] = -500;     // 负数
    data[2] = 2000;
    data[3] = -200;     // 负数
    
    int sum = 0;
    sum += data[0];     // +1000
    sum += data[1];     // -500
    sum += data[2];     // +2000
    sum += data[3];     // -200
    
    // 1000 + (-500) + 2000 + (-200) = 2300
    return sum % 256;   // 预期: 252
}

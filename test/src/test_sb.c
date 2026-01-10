// 测试基本的 Store Word 指令
// 注意：当前 CPU 只支持 SW (字存储)

int main() {
    volatile int buf[5];
    
    // SW 存储完整的 32 位
    buf[0] = 10;
    buf[1] = 20;
    buf[2] = 30;
    buf[3] = 40;
    buf[4] = 50;
    
    // 验证存储和加载都正确
    int sum = 0;
    sum += buf[0];
    sum += buf[1];
    sum += buf[2];
    sum += buf[3];
    sum += buf[4];
    
    // 10 + 20 + 30 + 40 + 50 = 150
    return sum;   // 预期: 150
}

// 测试基本的 Load 指令功能
// 注意：当前 CPU 只支持 LW (字加载)，不支持 LB/LBU
// 这个测试验证数组读取（生成 LW 指令）

int main() {
    // 测试数组加载
    volatile int data[4];
    data[0] = 10;
    data[1] = 20;
    data[2] = 30;
    data[3] = 40;
    
    int sum = 0;
    sum += data[0];    // LW
    sum += data[1];    // LW
    sum += data[2];    // LW
    sum += data[3];    // LW
    
    // 10 + 20 + 30 + 40 = 100
    return sum;  // 预期: 100
}

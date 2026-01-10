// 测试数组 Store/Load Word 指令
// 注意：当前 CPU 只支持 SW/LW

int main() {
    volatile int buf[4];
    
    // SW 存储 32 位
    buf[0] = 100;
    buf[1] = 200;
    buf[2] = 300;
    buf[3] = 400;
    
    // 验证存储正确
    int sum = 0;
    sum += buf[0];
    sum += buf[1];
    sum += buf[2];
    sum += buf[3];
    
    // 100 + 200 + 300 + 400 = 1000
    if(sum==1000)return 1;
    else  return 0;
}

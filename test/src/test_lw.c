// 测试 LW (Load Word) 指令：加载字（4字节）
// LW rd, offset(rs1): 从内存 [rs1+offset] 加载 4 字节

int main() {
    // 测试数据：各种整数值
    int data[5];
    data[0] = 100;
    data[1] = 200;
    data[2] = 300;
    data[3] = -50;      // 负数
    data[4] = 12345;
    
    // LW 加载完整的 32 位字
    int sum = 0;
    sum += data[0];     // +100
    sum += data[1];     // +200
    sum += data[2];     // +300
    sum += data[3];     // -50
    sum += data[4];     // +12345
    
    // 100 + 200 + 300 + (-50) + 12345 = 12895
    // 返回值取模避免溢出
    if(sum==12895)return 1;
    else  return 0;
}

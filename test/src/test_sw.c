// 测试 SW (Store Word) 指令：存储字（4字节）
// SW rs2, offset(rs1): 将 rs2 的全部 32 位存入内存 [rs1+offset]

int main() {
    int buf[4];
    
    // SW 存储完整的 32 位
    buf[0] = 100000;
    buf[1] = 200000;
    buf[2] = -50000;
    buf[3] = 12345;
    
    // 验证存储正确
    int sum = 0;
    sum += buf[0];      // 100000
    sum += buf[1];      // 200000
    sum += buf[2];      // -50000
    sum += buf[3];      // 12345
    
    // 100000 + 200000 + (-50000) + 12345 = 262345
    // 取模到合理范围
    if(sum==262345)return 1;
    else  return 0;   // 预期: 262345 % 256 = 73
}

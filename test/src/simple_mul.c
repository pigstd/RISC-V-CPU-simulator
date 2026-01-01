// 简单乘法测试: 7 * 8 = 56
// 使用 RISC-V M 扩展的 MUL 指令

int main() {
    int a = 7;
    int b = 8;
    int result = a * b;  // 编译为 MUL 指令
    return result;  // 预期: 56
}

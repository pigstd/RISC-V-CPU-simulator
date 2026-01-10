// 简单乘法测试: 7 * 8 + 9 = 65
// 使用 RISC-V M 扩展的 MUL 指令

int main() {
    int a = 7;
    int b = 8;
    int c = 9;
    int result = a * b + c;  // 编译为 MUL 指令
    return result;  // 预期: 65
}

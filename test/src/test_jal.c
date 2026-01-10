// 测试 JAL 指令：函数调用
// JAL rd, offset: 跳转到 PC+offset，将返回地址 PC+4 存入 rd
int add(int a, int b) {
    return a + b;
}

int sub(int a, int b) {
    return a - b;
}

int main() {
    int x = add(10, 5);   // JAL 调用 add，期望 15
    int y = sub(x, 3);    // JAL 调用 sub，期望 12
    int z = add(y, y);    // JAL 调用 add，期望 24
    return z;  // 预期: 24
}

// 测试 JALR 指令：通过函数指针间接调用
// JALR rd, rs1, offset: 跳转到 (rs1+offset) & ~1，将 PC+4 存入 rd
// 函数指针调用会生成 JALR 指令

int double_val(int x) {
    return x + x;
}

int triple_val(int x) {
    return x + x + x;
}

int main() {
    // 函数指针调用会生成 JALR
    int (*func_ptr)(int);
    
    func_ptr = double_val;
    int a = func_ptr(5);   // JALR 调用，期望 10
    
    func_ptr = triple_val;
    int b = func_ptr(4);   // JALR 调用，期望 12
    
    return a + b;  // 预期: 22
}

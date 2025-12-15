// 测试移位操作：1 << 4 = 16, 16 >> 2 = 4
int main() {
    int t0 = 1;
    t0 = t0 << 4;     // 16
    t0 = (unsigned)t0 >> 2; // 4

    asm volatile (
        "mv a0, %0\n"
        "nop\n"
        "nop\n"
        "nop\n"
        "ebreak"
        :
        : "r"(t0)
        : "a0"
    );
    return 0;
}

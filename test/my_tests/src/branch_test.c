// 测试所有分支指令
// 每条分支如果正确跳过则加1，总计6个分支 = 6
void _start() __attribute__((naked));

void _start() {
    asm volatile (
        "li a0, 0\n"          // result counter
        "li t0, 5\n"
        "li t1, 10\n"
        "li t2, 5\n"
        
        // BEQ: t0 == t2 (5 == 5) should branch
        "beq t0, t2, beq_ok\n"
        "j fail\n"
        "beq_ok:\n"
        "addi a0, a0, 1\n"
        
        // BNE: t0 != t1 (5 != 10) should branch
        "bne t0, t1, bne_ok\n"
        "j fail\n"
        "bne_ok:\n"
        "addi a0, a0, 1\n"
        
        // BLT: t0 < t1 (5 < 10) should branch
        "blt t0, t1, blt_ok\n"
        "j fail\n"
        "blt_ok:\n"
        "addi a0, a0, 1\n"
        
        // BGE: t1 >= t0 (10 >= 5) should branch
        "bge t1, t0, bge_ok\n"
        "j fail\n"
        "bge_ok:\n"
        "addi a0, a0, 1\n"
        
        // BLTU: t0 <u t1 (5 < 10 unsigned) should branch
        "bltu t0, t1, bltu_ok\n"
        "j fail\n"
        "bltu_ok:\n"
        "addi a0, a0, 1\n"
        
        // BGEU: t1 >=u t0 (10 >= 5 unsigned) should branch  
        "bgeu t1, t0, bgeu_ok\n"
        "j fail\n"
        "bgeu_ok:\n"
        "addi a0, a0, 1\n"
        
        // Success: a0 = 6
        "j done\n"
        
        "fail:\n"
        "li a0, 0\n"
        
        "done:\n"
        "nop\n"
        "nop\n"
        "nop\n"
        "ebreak\n"
    );
}

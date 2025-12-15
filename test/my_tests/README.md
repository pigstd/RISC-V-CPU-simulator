# 测试程序说明

本目录包含用于验证 RISC-V CPU 模拟器的测试程序集。

## 测试程序列表

### 纯寄存器测试 (推荐 - 不需要 dcache)

| 测试名称 | 预期结果 (a0) | 描述 | 状态 |
|---------|---------------|------|------|
| **simple_add** | 15 | 简单加法 1+2+3+4+5 | ✅ 验证通过 |
| **loop_sum** | 55 | 循环计算 1+2+...+10 | ✅ 验证通过 |
| **fib_reg** | 55 | Fibonacci(10) 纯寄存器版 | 待测试 |

### 带内存访问测试 (需要 dcache 配置正确)

| 测试名称 | 预期结果 (a0) | 描述 |
|---------|---------------|------|
| **fib** | 55 | Fibonacci(10) 使用栈 |
| **sort** | 15 | 冒泡排序，返回排序后数组元素之和 |
| **factorial** | 120 | 计算 5! (循环加法实现乘法) |
| **sum** | 55 | 计算 1+2+...+10 使用栈 |
| **bitcount** | 5 | 统计 181 (0b10110101) 中 1 的个数 |
| **max** | 9 | 从数组 {3,7,2,9,4,1} 中找最大值 |
| **reverse** | 5 | 翻转数组 {1,2,3,4,5}，返回第一个元素 |

## 编译方法

```bash
# 编译所有测试
./compile_all.sh

# 编译纯寄存器测试
riscv64-unknown-elf-gcc -march=rv32i -mabi=ilp32 -O0 -nostdlib -static \
  -Wl,--no-relax -Tlink.ld src/simple_add.c -o workloads/simple_add.riscv
riscv64-unknown-elf-objdump -d workloads/simple_add.riscv > workloads/simple_add.riscv.dump
python3 ../utils/loader.py --fname workloads/simple_add.riscv.dump --odir workloads
```

## 生成的文件

每个测试程序会生成以下文件：

- `*.riscv` - ELF 可执行文件
- `*.riscv.dump` - 反汇编输出
- `*.exe` - 指令内存 hex 文件 (用于 icache)
- `*.data` - 数据内存 hex 文件 (用于 dcache)
- `*.config` - 测试配置文件

## 使用测试

将生成的 `.exe` 文件复制到模拟器的 workspace 目录：

```bash
# 例如，测试 fib
cp workloads/fib.exe /path/to/naive-cpu/src/workspace/workload.exe
cp workloads/fib.data /path/to/naive-cpu/src/workspace/data.mem
```

然后运行模拟器并验证最终 a0 (x10) 寄存器的值。

## 架构要求

所有测试程序仅使用 **RV32I** 基本指令集：

- 整数算术: ADD, ADDI, SUB
- 逻辑运算: AND, ANDI, OR, ORI, XOR, XORI
- 移位: SLL, SLLI, SRL, SRLI, SRA, SRAI
- 比较: SLT, SLTI, SLTU, SLTIU
- 分支: BEQ, BNE, BLT, BGE, BLTU, BGEU
- 跳转: JAL, JALR
- 加载: LW, LH, LHU, LB, LBU
- 存储: SW, SH, SB
- 立即数: LUI, AUIPC
- 系统: EBREAK

**注意**: 不支持 RV32M (乘法/除法) 扩展。factorial 测试使用循环加法模拟乘法。

## 源代码结构

```
src/
├── start.S     # 启动代码 (设置栈指针, 调用 main, ebreak)
├── fib.c       # Fibonacci 计算
├── sort.c      # 冒泡排序
├── factorial.c # 阶乘计算 (循环加法)
├── sum.c       # 求和
├── bitcount.c  # 位计数
├── max.c       # 数组最大值
└── reverse.c   # 数组翻转
```

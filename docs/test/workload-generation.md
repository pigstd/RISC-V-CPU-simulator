# Minor-CPU 测试程序生成指南

本文档详细介绍如何将C/C++程序转换为可以在minor-cpu上测试的程序文件格式。

## 概述

将C/C++程序转换为minor-cpu可测试程序需要生成三类文件：

| 文件类型 | 扩展名 | 说明 |
|---------|--------|------|
| 指令文件 | `.exe` | 包含程序的机器指令（.text段） |
| 数据文件 | `.data` | 包含程序的初始化数据（.data段） |
| 配置文件 | `.config` | 包含内存偏移配置信息 |

## 完整工作流程

### 步骤1：编写C/C++源代码

编写符合RV32I指令集的C程序。以下是一个简单示例 `acc.c`：

```c
//  riscv64-unknown-elf-gcc -O3 file.c -march=rv32i -mabi=ilp32 -nostdlib

int a[100];
int b[100];

int main() {
  int sum = 0;
  for (int i = 0; i < 100; ++i) {
    a[i] = i;
  }
  for (int i = 0; i < 100; ++i) {
    b[a[i]]++;
    sum = sum + b[a[i]];
  }
  return sum;
}
```

**注意事项：**
- 使用 `-nostdlib` 避免依赖标准库
- 目标架构为 RV32I（`-march=rv32i -mabi=ilp32`）

### 步骤2：编译C/C++程序为RISC-V ELF文件

使用RISC-V工具链编译程序：

```bash
riscv64-unknown-elf-gcc -O3 your_program.c \
    -march=rv32i \
    -mabi=ilp32 \
    -nostdlib \
    -o your_program.riscv
```

**编译选项说明：**
- `-O3`：最高优化等级
- `-march=rv32i`：目标RV32I指令集
- `-mabi=ilp32`：32位整数ABI
- `-nostdlib`：不链接标准库

### 步骤3：生成objdump反汇编文件

```bash
riscv64-unknown-elf-objdump -D your_program.riscv > your_program.riscv.dump
```

### 步骤4：使用loader.py转换为CPU测试文件

运行位于 `utils/loader.py` 的转换工具：

```bash
python utils/loader.py \
    --fname your_program.riscv.dump \
    --odir workloads
```

**参数说明：**
- `--fname`：objdump输出文件路径
- `--odir`：输出目录（默认为当前目录）
- `--exit-tohost`：（可选）使用tohost方式退出

执行后会生成三个文件：
- `workloads/your_program.exe`
- `workloads/your_program.data`（如果有.data段）
- `workloads/your_program.config`

## 生成文件格式详解

### 1. `.exe` 文件（指令文件）

每行包含一个32位指令的十六进制表示，地址从0开始递增。

**格式示例：**
```
000007b7 //  0: lui a5, 0x00
0b878793 //  4: addi a5, a5, 184
19078693 //  8: addi a3, a5, 400
00000513 // 12: li a0, 0
0007a703 // 16: lw a4, 0(a5)
00478793 // 20: addi a5, a5, 4
00e50533 // 24: add a0, a0, a4
fed79ae3 // 28: bne a5, a3, -12
00100073 // 32: ebreak
00000033 // 36: add x0, x0, x0, pad the ebreak with noops
```

**格式规范：**
- 每行格式：`XXXXXXXX // 注释`
- `XXXXXXXX`：8位十六进制指令码
- `//` 后为注释（地址和汇编指令）
- 空行用 `0 // padding` 填充

### 2. `.data` 文件（数据文件）

包含程序的初始化数据段内容。

**格式示例：**
```
255c
41b
2107
2380
c1c
1440
```

**格式规范：**
- 每行一个32位数据值的十六进制表示
- 地址从 `data_offset` 开始递增
- 可包含注释

### 3. `.config` 文件（配置文件）

JSON格式的配置信息。

**格式示例：**
```json
{ "offset": 0x80000000, "data_offset": 0xb8 }
```

或：
```json
{ "offset": 0x10094, "data_offset": -0x10094 }
```

**字段说明：**
- `offset`：程序的起始地址（通常是ELF文件中.text段的起始地址）
- `data_offset`：数据段相对于指令段的偏移量

## 运行测试

### 方法1：直接指定测试用例

将生成的文件放入 `workloads/` 目录后，运行CPU仿真：

```bash
cd examples/minor-cpu/src
python main.py --case your_program
```

### 方法2：使用workspace

文件会被自动复制到 `workspace/` 目录：
- `your_program.exe` → `workspace/workload.exe`
- `your_program.data` → `workspace/workload.data`
- `your_program.config` → `workspace/workload.config`

## 已有的Benchmark程序

`workloads/` 目录下已包含多个可用的benchmark：

| 程序名 | 说明 |
|-------|------|
| `0to100` | 累加0到100 |
| `acc` | 数组累加 |
| `median` | 中位数计算 |
| `multiply` | 乘法测试 |
| `qsort` | 快速排序 |
| `rsort` | 基数排序 |
| `towers` | 汉诺塔 |
| `vvadd` | 向量加法 |
| `dhrystone` | Dhrystone基准测试 |

## 单元测试（rv32ui-p-*）

`unit-tests/` 目录包含RISC-V指令集的单元测试：

```
rv32ui-p-add     # ADD指令测试
rv32ui-p-addi    # ADDI指令测试
rv32ui-p-and     # AND指令测试
rv32ui-p-beq     # BEQ分支测试
rv32ui-p-jal     # JAL跳转测试
rv32ui-p-lw      # LW加载测试
rv32ui-p-sw      # SW存储测试
...
```

## 完整示例：从C到测试

```bash
# 1. 编写源代码
cat > mytest.c << 'EOF'
int main() {
    int sum = 0;
    for (int i = 1; i <= 10; i++) {
        sum += i;
    }
    return sum;
}
EOF

# 2. 编译
riscv64-unknown-elf-gcc -O3 mytest.c \
    -march=rv32i -mabi=ilp32 -nostdlib \
    -o mytest.riscv

# 3. 生成objdump
riscv64-unknown-elf-objdump -D mytest.riscv > mytest.riscv.dump

# 4. 转换为CPU测试文件
python utils/loader.py --fname mytest.riscv.dump --odir workloads

# 5. 运行测试
cd src
python main.py --case mytest
```

## 高级用法

### 使用gold文件验证

可以创建 `.riscv.gold` 文件用于结果验证：
- 文件名格式：`your_program.riscv.gold`
- 包含期望的执行trace

### 自定义验证脚本

可以创建 `.sh` 脚本进行自定义验证：
- 文件名格式：`your_program.sh`
- 脚本接收日志文件和数据文件作为参数

示例 (`0to100.sh`)：
```bash
#!/bin/bash
sum=$(cat $1 | grep "writeback.*x14" | awk "{ sum += \$NF } END { print sum }")
ref=$(cat $2 | awk '{ print "0x"$1 }' | awk "{ sum += \$1 } END { print sum }")
if [ $sum -ne $ref ]; then
    echo "Error! $sum != $ref"
    exit 1
fi
```

## 常见问题

### Q1: 找不到riscv64-unknown-elf-gcc？
安装RISC-V工具链：
```bash
# Ubuntu/Debian
sudo apt install gcc-riscv64-unknown-elf

# 或从源码编译
git clone https://github.com/riscv/riscv-gnu-toolchain
cd riscv-gnu-toolchain
./configure --prefix=/opt/riscv --with-arch=rv32i --with-abi=ilp32
make
```

### Q2: 程序太大？
loader.py对程序大小有限制：
- 指令段：最多16000个32位指令
- 数据段：最多160000个32位数据

### Q3: 数据段地址不对齐？
loader.py会自动处理2字节到4字节的合并，但源程序应尽量使用4字节对齐的数据。

## 相关文件

- 转换工具：`utils/loader.py`
- Benchmark程序：`workloads/`
- 单元测试：`unit-tests/`
- CPU主程序：`src/main.py`

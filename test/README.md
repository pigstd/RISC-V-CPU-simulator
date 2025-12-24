# RISC-V CPU 模拟器测试套件

本目录包含 RISC-V CPU 模拟器的测试用例和构建工具。

## 目录结构

```
test/
├── src/              # C 源代码测试文件
├── test_suite/       # 编译后的测试用例（可直接运行）
├── common/           # 公共头文件和库
├── workspace/        # 编译临时目录
└── batch_build.py    # 批量编译脚本
```

## 快速开始

### 运行测试

从项目根目录运行：

```bash
# 运行所有测试
python scripts/run_tests.py

# 运行指定测试
python scripts/run_tests.py simple_add fib max

# 列出所有可用测试
python scripts/run_tests.py --list

# 详细输出（失败时显示更多信息）
python scripts/run_tests.py -v
```

### 编译测试用例

```bash
cd test
python batch_build.py
```

这会将 `src/` 下的所有 `.c` 文件编译到 `test_suite/` 目录。

## 测试格式

每个测试用例包含以下文件：

| 文件            | 说明                         |
| --------------- | ---------------------------- |
| `*.exe`         | 指令内存（十六进制）         |
| `*.data`        | 数据内存（十六进制，可为空） |
| `*.ans`         | 期望的 a0 寄存器值（十进制） |
| `*.asm`         | 反汇编代码（调试用）         |
| `*.config.json` | 配置文件（可选）             |

## 配置文件

每个测试可以有独立的配置文件 `<name>.config.json`：

```json
{
  "name": "test_name",
  "memory": {
    "text_base": 0,
    "data_base": 8192
  },
  "simulator": {
    "sim_threshold": 100000,
    "idle_threshold": 50000
  }
}
```

- `data_base`: 数据段基地址（默认 0x2000 = 8192）
- `sim_threshold`: 最大模拟周期数
- `idle_threshold`: 空闲周期阈值

## 编写新测试

1. 在 `src/` 下创建 C 源文件：

```c
// test/src/my_test.c
int main() {
    int result = 0;
    // ... 你的测试代码 ...
    return result;  // 返回值会写入 a0 寄存器
}
```

2. 运行编译脚本：

```bash
python batch_build.py
```

3. 运行测试：

```bash
python ../scripts/run_tests.py my_test
```

## 测试输出说明

运行测试时会显示以下统计信息：

| 列名   | 说明                 |
| ------ | -------------------- |
| Cycles | 模拟器运行的总周期数 |
| Instr  | 解码阶段处理的指令数 |
| Fetch  | 取指阶段获取的指令数 |

示例输出：

```
Test Name                 Status       Cycles      Instr      Fetch Message
------------------------------------------------------------------------------------------
simple_add                PASS             28         23         24 a0=15 (correct)
fib                       PASS            386        368        369 a0=55 (correct)
vector_mul_100            PASS          43090      40977      40978 a0=100 (correct)
```

## 当前测试列表

| 测试名         | 说明                         |
| -------------- | ---------------------------- |
| simple_add     | 简单加法                     |
| loop_sum       | 循环求和 1+2+...+10          |
| fib            | 斐波那契数列                 |
| factorial      | 阶乘计算                     |
| max/min        | 数组最大/最小值              |
| array_sum      | 数组求和                     |
| vector_add     | 向量加法（10 元素）          |
| vector_add_100 | 向量加法（100 元素）         |
| vector_mul_100 | 向量乘法（100 元素，快速乘） |
| matrix_mul     | 矩阵乘法                     |
| binary_search  | 二分查找                     |
| sort           | 冒泡排序                     |
| prime          | 素数判断                     |
| overflow       | 整数溢出测试                 |
| ...            | ...                          |

## 注意事项

- 本模拟器仅支持 RV32I 指令集，**不支持 MUL 指令**
- 乘法需要使用快速乘算法（二进制分解）实现
- 数据段默认从 0x2000 开始，可通过配置文件修改

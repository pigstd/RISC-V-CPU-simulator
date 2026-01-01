# 分支预测实现文档

## 1. 概述

本 Tomasulo 乱序处理器实现了基于 **2-bit 饱和计数器** 的动态分支预测机制。该机制通过 **Branch History Table (BHT)** 记录分支历史，在 Issue 阶段进行预测，在 Execute 阶段验证预测结果，预测错误时触发流水线 Flush。

## 2. 预测算法

### 2.1 2-bit 饱和计数器

每个 BHT 条目使用 2-bit 饱和计数器，有 4 种状态：

```
状态值  名称                预测结果
──────────────────────────────────────
  00   强不跳转 (SNT)       不跳转
  01   弱不跳转 (WNT)       不跳转
  10   弱跳转   (WT)        跳转
  11   强跳转   (ST)        跳转
```

**状态转换图：**

```
                 实际不跳转
              ←─────────────→
         ┌────┐           ┌────┐
    ┌───►│ 00 │←──────────│ 01 │◄───┐
    │    │SNT │           │WNT │    │
    │    └────┘           └────┘    │
    │      │                │       │
实际 │      │ 实际跳转    实际 │       │ 实际
不跳 │      ▼              跳转│       │ 不跳
    │    ┌────┐           ┌────┐    │
    └────│ 10 │──────────►│ 11 │────┘
         │WT  │           │ ST │
         └────┘           └────┘
              ←─────────────→
                 实际跳转
```

**更新规则：**
- 实际跳转：计数器 +1（饱和到 3）
- 实际不跳转：计数器 -1（饱和到 0）

**预测规则：**
- 计数器 ≥ 2：预测跳转 (Taken)
- 计数器 < 2：预测不跳转 (Not Taken)

### 2.2 BHT 索引计算

```
BHT 配置：
- 条目数量：64 (2^6)
- 索引位宽：6 bits
- 索引计算：PC[7:2]（字地址）& 0x3F

地址映射示例：
PC = 0x1000_0100 → 字地址 = 0x0040 → 索引 = 0x00 (0)
PC = 0x1000_0104 → 字地址 = 0x0041 → 索引 = 0x01 (1)
PC = 0x1000_0200 → 字地址 = 0x0080 → 索引 = 0x00 (0，冲突）
```

### 2.3 预测逻辑

```python
def predict(pc):
    idx = (pc >> 2) & 0x3F  # 字地址取低 6 位
    counter = BHT[idx]
    return counter >= 2  # True = 预测跳转
```

## 3. 分支类型处理

| 指令类型 | 处理方式 | 预测目标 PC |
|---------|---------|------------|
| **B 类型** (beq, bne, blt, bge, bltu, bgeu) | 使用 BHT 预测 | PC + imm |
| **JAL** | 总是预测跳转 | PC + imm |
| **JALR** | 不预测，Stall 等待 | 需要等待 rs1 可用 |

## 4. 流水线集成

### 4.1 Issue 阶段（预测）

```
1. 解码指令，识别分支类型
2. 若为 B 类型：
   - 查询 BHT 获取预测结果
   - 预测跳转 → predict_valid=1, predict_target_pc=PC+imm
   - 预测不跳 → predict_valid=0, 顺序执行
3. 若为 JAL：
   - predict_valid=1, predict_target_pc=PC+imm
4. 若为 JALR：
   - jalr_stall=1, 等待目标地址计算
5. 将预测信息写入 ROB：
   - predicted_taken：预测是否跳转
   - predicted_pc：预测的目标 PC
```

### 4.2 Execute 阶段（验证）

```
1. ALU 计算实际分支结果：
   - branch_taken：实际是否跳转
   - next_pc：实际下一条 PC
2. 从 ROB 读取预测信息
3. 比较预测与实际：
   - B 类型：predicted_taken ≠ branch_taken → mispredicted
4. 更新 BHT（仅 B 类型）：
   - bht.update_if(is_B, branch_pc, branch_taken)
```

### 4.3 Misprediction 处理

```
当 mispredicted = 1 时：
1. 产生 Flush 信号
2. 清空 RAT（重命名表）
3. 清空 ROB（重排序缓冲）
4. 清空所有 RS（保留站）
5. 清空 MUL_RS（乘法保留站）
6. 清空 LSQ（Load/Store 队列）
7. 使用 correct_pc 重新取指
```

## 5. 关键数据结构

### 5.1 BHT 类

```python
class BHT:
    counters = RegArray(Bits(2), 64)  # 64 个 2-bit 计数器
    
    def predict(pc) → Bits(1)         # 预测是否跳转
    def update_if(cond, pc, taken)    # 条件更新计数器
```

### 5.2 BHT 代码详解

#### 5.2.1 数据结构

```python
class BHT:
    def __init__(self):
        # 单个 RegArray 存储所有 64 个 2-bit 计数器
        # 初始化为 2（弱跳转 Weakly Taken）
        # 选择 2 作为初始值是因为：
        #   - 大多数循环第一次进入时会跳转
        #   - 从"弱跳转"开始可以更快收敛
        self.counters = RegArray(Bits(2), BHT_SIZE, initializer=[2] * BHT_SIZE)
```

#### 5.2.2 索引计算

```python
def get_index(self, pc: Value) -> Value:
    """
    从 PC 计算 BHT 索引
    
    设计思路：
    1. PC 低 2 位总是 00（RISC-V 指令 4 字节对齐）
    2. 使用 PC[7:2] 作为索引，即字地址的低 6 位
    3. 这样相邻 64 条指令映射到不同 BHT 条目
    
    计算过程：
    PC = 0x1000_0104
        ↓ 右移 2 位（除以 4）
    字地址 = 0x0040_0041
        ↓ AND 0x3F（取低 6 位）
    索引 = 0x01 = 1
    """
    word_addr = (pc >> UInt(32)(2)).bitcast(UInt(32))
    return (word_addr & UInt(32)(BHT_SIZE - 1)).bitcast(Bits(BHT_IDX_WIDTH))
```

#### 5.2.3 预测逻辑

```python
def predict(self, pc: Value) -> Value:
    """
    根据 PC 预测是否跳转
    
    预测规则：
    - counter >= 2 (弱跳转/强跳转) → 预测跳转
    - counter <  2 (弱不跳/强不跳) → 预测不跳
    
    返回值：Bits(1)，1=跳转，0=不跳
    """
    idx = self.get_index(pc)
    counter = self.counters[idx]  # 读取对应计数器
    
    # 比较并选择返回值
    # select(a, b) 等价于：条件为真返回 a，否则返回 b
    return (counter >= Bits(2)(2)).select(Bits(1)(1), Bits(1)(0))
```

#### 5.2.4 更新逻辑

```python
def update_if(self, cond: Value, pc: Value, taken: Value):
    """
    条件更新计数器
    
    参数：
    - cond: 更新条件（只有 B 类型分支才更新）
    - pc: 分支指令的 PC
    - taken: 实际是否跳转（1=跳转，0=不跳）
    
    更新规则（饱和计数器）：
    - taken=1: counter = min(counter + 1, 3)
    - taken=0: counter = max(counter - 1, 0)
    """
    idx = self.get_index(pc)
    old_val = self.counters[idx]
    
    # 饱和加减运算
    new_val = taken.select(
        # taken=1: 加 1，但饱和到 3
        (old_val == Bits(2)(3)).select(
            Bits(2)(3),                    # 已经是 3，保持不变
            old_val + Bits(2)(1)           # 否则 +1
        ),
        # taken=0: 减 1，但饱和到 0
        (old_val == Bits(2)(0)).select(
            Bits(2)(0),                    # 已经是 0，保持不变
            old_val - Bits(2)(1)           # 否则 -1
        )
    )
    
    # 只在 cond=1 时执行写入
    with Condition(cond):
        self.counters[idx] <= new_val
```

#### 5.2.5 BHT 操作示例

```
示例：循环分支预测过程

假设循环分支 PC = 0x1000_0100，执行 5 次后退出

索引计算：0x1000_0100 >> 2 = 0x0040_0040，& 0x3F = 0x00
         该分支映射到 BHT[0]

初始状态：BHT[0] = 2 (弱跳转)

迭代 1: 预测=跳转(2>=2), 实际=跳转 ✓, 更新: 2→3
迭代 2: 预测=跳转(3>=2), 实际=跳转 ✓, 更新: 3→3 (饱和)
迭代 3: 预测=跳转(3>=2), 实际=跳转 ✓, 更新: 3→3
迭代 4: 预测=跳转(3>=2), 实际=跳转 ✓, 更新: 3→3
迭代 5: 预测=跳转(3>=2), 实际=不跳 ✗, 更新: 3→2

循环结束后 BHT[0] = 2 (弱跳转)

下次进入同一循环：
  第 1 次: 预测=跳转(2>=2), 实际=跳转 ✓
  无需重新"预热"，因为计数器还在 2
```

### 5.3 ROB 分支字段

```python
rob.is_branch[idx]        # 是否为分支指令
rob.predicted_taken[idx]  # 预测是否跳转
rob.predicted_pc[idx]     # 预测的目标 PC
rob.pc[idx]               # 分支指令 PC（用于更新 BHT）
```

### 5.4 分支控制信号

```python
BranchControl_signal = Record(
    jalr_resolved = Bits(1),   # JALR 完成
    jalr_target_pc = UInt(32), # JALR 目标地址
    mispredicted = Bits(1),    # 预测错误
    correct_pc = UInt(32),     # 正确的 PC
)
```

## 6. 准确率分析

### 6.1 测试结果

| 测试程序 | 总分支数 | 预测错误 | 准确率 |
|---------|---------|---------|-------|
| fib | 12 | 1 | 91.7% |
| factorial | 48 | 13 | 72.9% |
| binary_search | 11 | 4 | 63.6% |
| vector_mul_real | 11 | 1 | 90.9% |

### 6.2 准确率影响因素

**高准确率场景（>90%）：**
- 循环分支：循环体执行多次后计数器稳定在强跳转状态
- 规律性分支：分支行为一致，计数器能快速收敛

**低准确率场景（<80%）：**
- 数据依赖分支：分支结果依赖输入数据，行为不规律
- 短循环：循环次数少，计数器未能收敛就结束
- BHT 别名冲突：不同分支映射到相同 BHT 条目，相互干扰

### 6.3 2-bit vs 1-bit 饱和计数器对比

```
示例：循环执行 10 次后退出

1-bit 计数器：
  第 1-9 次：预测跳转 ✓ (9 次正确)
  第 10 次：预测跳转 ✗ (1 次错误)
  第 11 次（循环外）：预测不跳 ✓
  准确率：10/11 = 90.9%，每次循环结束都会错 1 次

2-bit 计数器：
  第 1-9 次：预测跳转 ✓ (9 次正确)
  第 10 次：预测跳转 ✗ (1 次错误)
  第 11 次（循环外）：预测跳转 ✗ (仍为弱跳转)
  但下次进入循环时：
  - 1-bit 需要 1 次预热
  - 2-bit 可能直接命中（如果计数器还在 2/3）
```

**2-bit 优势：** 对于嵌套循环、函数多次调用等场景，2-bit 计数器能更好地保持历史信息，减少重复预热开销。

### 6.4 理论准确率上界

对于 64 条目 BHT，假设分支均匀分布：

$$
\text{别名冲突概率} = 1 - \left(1 - \frac{1}{64}\right)^{n-1}
$$

其中 $n$ 是程序中的分支数量。当程序有 100 个分支时，约 78% 的概率存在至少一次别名冲突。

## 7. 可能的优化方向

1. **增加 BHT 条目数**：从 64 扩展到 256/1024，减少别名冲突
2. **使用全局历史**：GShare 预测器，PC XOR 全局分支历史
3. **两级预测**：局部历史 + 全局历史的混合预测器
4. **BTB (Branch Target Buffer)**：缓存分支目标地址，加速 JAL/JALR
5. **循环预测器**：专门针对循环分支的预测优化

## 8. 文件位置

| 组件 | 文件 | 行号 |
|-----|-----|-----|
| BHT 类定义 | `src/ROB.py` | 14-66 |
| Issue 阶段预测 | `src/main.py` | 145-160 |
| Execute 阶段验证 | `src/arbitrator.py` | 193-227 |
| Flush 逻辑 | `src/main.py` | 488-525 |

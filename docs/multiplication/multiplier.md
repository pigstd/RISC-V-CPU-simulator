# 乘法器实现文档（RISC-V M 扩展）

## 1. 概述

本 Tomasulo 乱序处理器实现了 RISC-V M 扩展的乘法指令子集。采用 **非流水线设计**，乘法器 busy 期间不接受新请求，每次乘法需要 **4 个时钟周期** 完成。

### 1.1 支持的指令

| 指令     | 功能             | 操作数                        | 结果                    |
| -------- | ---------------- | ----------------------------- | ----------------------- |
| `MUL`    | 乘法（低 32 位） | rs1 × rs2                     | rd = (rs1 × rs2)[31:0]  |
| `MULH`   | 高位有符号乘法   | signed(rs1) × signed(rs2)     | rd = (rs1 × rs2)[63:32] |
| `MULHSU` | 高位混合符号乘法 | signed(rs1) × unsigned(rs2)   | rd = (rs1 × rs2)[63:32] |
| `MULHU`  | 高位无符号乘法   | unsigned(rs1) × unsigned(rs2) | rd = (rs1 × rs2)[63:32] |

### 1.2 指令编码

```
31      25  24   20  19   15  14  12  11    7  6     0
┌─────────┬────────┬────────┬──────┬────────┬────────┐
│ 0000001 │   rs2  │   rs1  │funct3│   rd   │0110011 │
└─────────┴────────┴────────┴──────┴────────┴────────┘
  funct7                             R-type opcode

funct3 编码：
  000 = MUL
  001 = MULH
  010 = MULHSU
  011 = MULHU
```

## 2. 硬件架构

### 2.1 模块组成

```
                    ┌─────────────────────────────────────────┐
                    │              CDB 广播总线               │
                    └───────────────────┬─────────────────────┘
                                        │
    ┌───────────────────────────────────┼───────────────────────────────────┐
    │                                   │                                   │
    ▼                                   ▼                                   │
┌─────────┐                       ┌─────────┐                               │
│MUL_RS[0]│                       │MUL_RS[1]│     乘法保留站                │
│ Entry 0 │                       │ Entry 1 │     (2 个条目)                │
└────┬────┘                       └────┬────┘                               │
     │                                 │                                    │
     │  qj_valid & qk_valid & ~fired & mul_idle                            │
     │                                 │                                    │
     └────────────┬────────────────────┘                                    │
                  │ 选择就绪的 RS                                           │
                  ▼                                                         │
         ┌────────────────┐                                                 │
         │ MultiplierRegs │  共享寄存器（pending, op1, op2, rob_idx）       │
         └───────┬────────┘                                                 │
                 │ pending = 1 时启动                                       │
                 ▼                                                          │
         ┌────────────────┐                                                 │
         │MultiplierState │  状态机 Downstream（每周期执行）                │
         │  4 周期延迟    │                                                 │
         └───────┬────────┘                                                 │
                 │ cycle_cnt = 1 时完成                                     │
                 ▼                                                          │
         ┌────────────────┐                                                 │
         │      ROB       │  直接写入结果                                   │
         └───────┬────────┘                                                 │
                 │                                                          │
                 └──────────────────────────────────────────────────────────┘
                           乘法完成广播（清除对应 RS）
```

### 2.2 关键组件

| 组件       | 类名                | 数量 | 功能                         |
| ---------- | ------------------- | ---- | ---------------------------- |
| 乘法保留站 | `MUL_RSEntry`       | 2    | 缓存乘法指令，等待操作数就绪 |
| 保留站逻辑 | `MUL_RS_downstream` | 2    | 监听 CDB，发射就绪指令       |
| 共享寄存器 | `MultiplierRegs`    | 1    | 乘法器输入/状态寄存器        |
| 乘法状态机 | `MultiplierState`   | 1    | 4 周期计算状态机             |

## 3. 数据结构

### 3.1 MUL_RSEntry（乘法保留站条目）

```python
class MUL_RSEntry:
    busy      = RegArray(Bits(1), 1)   # 条目是否被占用
    op        = RegArray(Bits(19), 1)  # 乘法类型 (ALU_MUL/MULH/MULHSU/MULHU)
    vj        = RegArray(UInt(32), 1)  # 操作数 1 的值
    vk        = RegArray(UInt(32), 1)  # 操作数 2 的值
    qj        = RegArray(Bits(4), 1)   # 操作数 1 的 ROB 标签
    qk        = RegArray(Bits(4), 1)   # 操作数 2 的 ROB 标签
    qj_valid  = RegArray(Bits(1), 1)   # 操作数 1 是否就绪
    qk_valid  = RegArray(Bits(1), 1)   # 操作数 2 是否就绪
    rd        = RegArray(Bits(5), 1)   # 目标寄存器
    rob_idx   = RegArray(Bits(4), 1)   # ROB 索引
    fired     = RegArray(Bits(1), 1)   # 是否已发射到乘法器
```

### 3.2 MultiplierRegs（乘法器共享寄存器）

```python
class MultiplierRegs:
    cycle_cnt = RegArray(UInt(4), 1)   # 倒计时计数器
    op1       = RegArray(UInt(32), 1)  # 操作数 1
    op2       = RegArray(UInt(32), 1)  # 操作数 2
    alu_type  = RegArray(Bits(19), 1)  # 乘法类型
    rob_idx   = RegArray(UInt(4), 1)   # ROB 索引
    pending   = RegArray(Bits(1), 1)   # 待处理请求标志
```

### 3.3 ALU 类型编码

```python
class RV32I_ALU:
    ALU_MUL    = 15  # 低 32 位乘法
    ALU_MULH   = 16  # 高 32 位有符号×有符号
    ALU_MULHSU = 17  # 高 32 位有符号×无符号
    ALU_MULHU  = 18  # 高 32 位无符号×无符号
```

## 4. 执行流程

### 4.1 Issue 阶段

```
1. 解码器识别乘法指令（is_mul = 1）
2. 检查 MUL_RS 是否有空闲条目：
   - mul_rs_busy = mul_rs[0].busy & mul_rs[1].busy
   - 如果全满则 stall
3. 选择空闲的 RS 条目（优先选择索引小的）
4. 写入 RS 条目：
   - busy = 1
   - op = decoder_result.alu_type
   - vj/vk = 操作数值（如果就绪）
   - qj/qk = ROB 标签（如果未就绪）
   - qj_valid/qk_valid = 操作数就绪标志
   - rob_idx = 分配的 ROB 索引
```

### 4.2 RS Downstream（每周期执行）

```
对于每个 MUL_RS entry：
1. 监听 CDB 广播：
   - 如果 qj 等待的 ROB 完成 → 更新 vj, qj_valid=1
   - 如果 qk 等待的 ROB 完成 → 更新 vk, qk_valid=1

2. 监听乘法器完成广播：
   - 其他 MUL_RS 可能等待乘法结果
   - 更新方式同 CDB

3. 就绪检测：
   ready = busy & qj_valid & qk_valid & ~fired & mul_idle

4. 发射（当 ready=1）：
   - 写入 MultiplierRegs (op1, op2, alu_type, rob_idx)
   - 设置 pending = 1
   - 设置 fired = 1

5. 完成清除（当乘法完成且 ROB 匹配）：
   - busy = 0, fired = 0
   - 清除 qj_valid, qk_valid
```

### 4.3 乘法器状态机

```
状态转换图：

    ┌─────────────────────────────────────────────────┐
    │                                                 │
    ▼                                                 │
┌────────┐  pending=1   ┌────────┐   cnt--   ┌──────────┐
│  IDLE  │ ───────────► │  BUSY  │ ────────► │ COUNTING │
│ cnt=0  │              │ cnt=4  │           │ cnt=3→2  │
└────────┘              └────────┘           └────┬─────┘
    ▲                                             │
    │                                             │ cnt=1
    │         ┌────────┐                          ▼
    └─────────│  DONE  │◄─────────────────────────┘
   cnt=0→0    │ cnt=1  │
   写入 ROB   └────────┘

状态说明：
- IDLE (cnt=0, pending=0): 空闲，可接受新请求
- BUSY (cnt=4→2): 计算中，倒计时
- DONE (cnt=1): 输出结果，写入 ROB
```

### 4.4 四周期详细时序

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         乘法器四周期详细执行过程                              │
└─────────────────────────────────────────────────────────────────────────────┘

周期 N（RS 发射）:
┌─────────────────────────────────────────────────────────────────────────────┐
│  MUL_RS_downstream 检测到就绪条件：                                         │
│    ready = busy & qj_valid & qk_valid & ~fired & mul_idle                  │
│                                                                             │
│  动作：                                                                     │
│    mul_regs.op1 ← rs.vj[0]           // 写入操作数 1                       │
│    mul_regs.op2 ← rs.vk[0]           // 写入操作数 2                       │
│    mul_regs.alu_type ← rs.op[0]      // 写入乘法类型                       │
│    mul_regs.rob_idx ← rs.rob_idx[0]  // 写入 ROB 索引                      │
│    mul_regs.pending ← 1              // 标记有待处理请求                    │
│    rs.fired ← 1                      // 标记 RS 已发射                      │
│                                                                             │
│  状态：cycle_cnt = 0, pending = 1                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
周期 N+1（开始计算）:
┌─────────────────────────────────────────────────────────────────────────────┐
│  MultiplierState.build() 检测到：is_idle & pending                         │
│                                                                             │
│  动作：                                                                     │
│    mul_regs.cycle_cnt ← 4           // 设置倒计时 = MUL_LATENCY            │
│    mul_regs.pending ← 0             // 清除 pending 标志                   │
│                                                                             │
│  状态：cycle_cnt = 4, pending = 0                                          │
│  注意：此时 op1, op2, rob_idx 已经锁存在寄存器中                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
周期 N+2（计算中 - 第 1 周期）:
┌─────────────────────────────────────────────────────────────────────────────┐
│  MultiplierState.build() 检测到：is_busy (cycle_cnt > 1)                   │
│                                                                             │
│  动作：                                                                     │
│    mul_regs.cycle_cnt ← cycle_cnt - 1  // 倒计时：4 → 3                    │
│                                                                             │
│  状态：cycle_cnt = 3                                                       │
│  硬件活动：乘法器内部计算（组合逻辑 mul_result = op1 * op2 始终有效）       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
周期 N+3（计算中 - 第 2 周期）:
┌─────────────────────────────────────────────────────────────────────────────┐
│  MultiplierState.build() 检测到：is_busy (cycle_cnt > 1)                   │
│                                                                             │
│  动作：                                                                     │
│    mul_regs.cycle_cnt ← cycle_cnt - 1  // 倒计时：3 → 2                    │
│                                                                             │
│  状态：cycle_cnt = 2                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
周期 N+4（计算中 - 第 3 周期）:
┌─────────────────────────────────────────────────────────────────────────────┐
│  MultiplierState.build() 检测到：is_busy (cycle_cnt > 1)                   │
│                                                                             │
│  动作：                                                                     │
│    mul_regs.cycle_cnt ← cycle_cnt - 1  // 倒计时：2 → 1                    │
│                                                                             │
│  状态：cycle_cnt = 1（下一周期进入 DONE）                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
周期 N+5（完成 - DONE）:
┌─────────────────────────────────────────────────────────────────────────────┐
│  MultiplierState.build() 检测到：is_done (cycle_cnt == 1)                  │
│                                                                             │
│  动作：                                                                     │
│    mul_regs.cycle_cnt ← 0              // 回到 IDLE                        │
│    rob.ready[rob_idx] ← 1              // 标记 ROB 结果就绪                 │
│    rob.value[rob_idx] ← mul_result     // 写入乘法结果                     │
│                                                                             │
│  返回值（广播给其他 RS）：                                                  │
│    return (rob_idx, mul_result, is_done=1)                                 │
│                                                                             │
│  状态：cycle_cnt = 0（回到 IDLE，可接受新请求）                             │
│                                                                             │
│  同周期 MUL_RS_downstream 动作：                                           │
│    检测到 mul_is_done & (rs.rob_idx == mul_rob_idx)                        │
│    rs.busy ← 0, rs.fired ← 0   // 清除该 RS 条目                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.5 状态机核心代码

```python
@downstream.combinational
def build(self, mul_regs: MultiplierRegs, rob, metadata):
    # 读取当前状态
    cycle_cnt = mul_regs.cycle_cnt[0]
    op1 = mul_regs.op1[0]
    op2 = mul_regs.op2[0]
    rob_idx = mul_regs.rob_idx[0]
    pending = mul_regs.pending[0]

    # 状态判断
    is_idle = (cycle_cnt == UInt(4)(0))
    is_done = (cycle_cnt == UInt(4)(1))
    is_busy = ~is_idle & ~is_done

    # 乘法结果（组合逻辑，始终计算）
    mul_result = (op1 * op2).bitcast(UInt(32))

    # 状态转移 1：IDLE + pending → 开始计算
    with Condition(is_idle & pending):
        mul_regs.cycle_cnt[0] <= UInt(4)(MUL_LATENCY)  # = 4
        mul_regs.pending[0] <= Bits(1)(0)

    # 状态转移 2：BUSY → 继续倒计时
    with Condition(is_busy):
        mul_regs.cycle_cnt[0] <= cycle_cnt - UInt(4)(1)

    # 状态转移 3：DONE → 输出结果，回到 IDLE
    with Condition(is_done):
        mul_regs.cycle_cnt[0] <= UInt(4)(0)
        rob.ready[rob_idx] <= Bits(1)(1)
        rob.value[rob_idx] <= mul_result

    return rob_idx, mul_result, is_done
```

### 4.6 为什么是 4 周期？

```
设计考量：
1. 真实硬件乘法器延迟：32×32 位乘法在 ASIC/FPGA 上通常需要多周期
2. 模拟流水线冲突：非流水线设计强制后续乘法等待
3. 可配置性：MUL_LATENCY 常量可调整

实际计算周期分解：
  周期 1 (cnt=4→3): 可视为乘法器 Stage 1（部分积生成）
  周期 2 (cnt=3→2): 可视为乘法器 Stage 2（部分积累加）
  周期 3 (cnt=2→1): 可视为乘法器 Stage 3（进位传播）
  周期 4 (cnt=1→0): 结果输出 + 写回 ROB

注：当前实现使用组合逻辑 (op1 * op2)，4 周期仅为模拟延迟
    真实 RTL 实现可替换为 Booth 编码乘法器等
```

## 5. 时序分析

### 5.1 单条乘法指令延迟

```
Cycle 0: Issue - 写入 MUL_RS
Cycle 1: RS Downstream - 发射到乘法器 (pending=1, cycle_cnt=4)
Cycle 2: Multiplier - 计算中 (cycle_cnt=3)
Cycle 3: Multiplier - 计算中 (cycle_cnt=2)
Cycle 4: Multiplier - 计算中 (cycle_cnt=1, DONE)
Cycle 5: 结果可用于后续指令

总延迟：4 周期（从发射到结果可用）
```

### 5.2 背靠背乘法吞吐

```
由于非流水线设计，连续乘法需要等待：

Cycle:  0   1   2   3   4   5   6   7   8   9
MUL 1: [Is][Fi][C3][C2][C1][--][--][--][--][--]
MUL 2: [Is][RS][RS][RS][RS][Fi][C3][C2][C1][--]

说明：
- [Is] = Issue 到 RS
- [Fi] = 发射到乘法器
- [C#] = 乘法器计算中
- [RS] = 在 RS 中等待

吞吐量：每 5 周期 1 条乘法（如果有数据依赖则更慢）
```

### 5.3 两个 RS 的并行优势

```
有 2 个 RS 可以缓存指令，减少 Issue stall：

无依赖的两条乘法：
Cycle:  0   1   2   3   4   5   6   7   8   9
MUL 1: [Is][Fi][C3][C2][C1][--][--][--][--][--]
MUL 2: [Is][RS][RS][RS][RS][Fi][C3][C2][C1][--]
      │    └── 第 2 条可以立即 Issue，不用 stall
      └─────── 两条在同一周期 Issue

如果只有 1 个 RS：
Cycle:  0   1   2   3   4   5   6   7   8   9
MUL 1: [Is][Fi][C3][C2][C1][--][--][--][--][--]
MUL 2: [ST][ST][ST][ST][ST][Is][Fi][C3][C2][C1]
       └── Issue 阶段 stall 5 个周期
```

## 6. 多广播总线架构

### 6.1 为什么采用独立广播

本实现采用 **多条广播总线** 设计，乘法器结果通过独立的 `mul_broadcast` 广播，而非走 CDB 仲裁：

```
                    执行单元完成
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌─────────┐     ┌─────────┐     ┌─────────┐
    │CDB (ALU)│     │CDB (LSU)│     │MUL_BCAST│
    │ 4个ALU  │     │ 1个LSU  │     │  乘法器 │
    │ 仲裁选1 │     │  独占   │     │  独占   │
    └────┬────┘     └────┬────┘     └────┬────┘
         │               │               │
         └───────────────┴───────────────┘
                         │
                         ▼
              所有 RS 同时监听 3 条总线
```

**设计优势：**

- **无仲裁延迟**：乘法完成后立即广播，不需要等待 CDB 空闲
- **更高吞吐**：ALU 和乘法器可以同周期各广播一个结果
- **实现简单**：避免修改复杂的 CDB 仲裁逻辑

### 6.2 结果传播路径

```
┌─────────────────┐
│ MultiplierState │
└────────┬────────┘
         │ is_done = 1
         │
         ├──────────────────────► ROB.ready[rob_idx] = 1
         │                        ROB.value[rob_idx] = result
         │
         └──────────────────────► mul_broadcast 信号
                                  │
                 ┌────────────────┼────────────────┐
                 ▼                ▼                ▼
         ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
         │ RS ×4       │  │ MUL_RS ×2   │  │    LSQ      │
         │(普通保留站) │  │(乘法保留站) │  │ (访存队列)  │
         └─────────────┘  └─────────────┘  └─────────────┘
```

### 6.3 RS 监听两个广播源

**关键：所有 RS 必须同时监听 CDB 和乘法器广播！**

```python
# RS_downstream.build() 中的监听逻辑

# 1. 监听 CDB 广播（ALU/LSU 结果）
with Condition(cbd_signal.valid & busy):
    with Condition((qj == cbd_signal.ROB_idx) & ~qj_valid):
        vj <= cbd_signal.rd_data
        qj_valid <= 1
    with Condition((qk == cbd_signal.ROB_idx) & ~qk_valid):
        vk <= cbd_signal.rd_data
        qk_valid <= 1

# 2. 监听乘法器广播（乘法结果）
with Condition(mul_is_done & busy):
    with Condition((qj == mul_rob_idx) & ~qj_valid):
        vj <= mul_rd_data
        qj_valid <= 1
    with Condition((qk == mul_rob_idx) & ~qk_valid):
        vk <= mul_rd_data
        qk_valid <= 1
```

### 6.4 常见 Bug：普通 RS 未监听乘法广播

如果 `RS_downstream` 只监听 `cbd_signal` 而不监听 `mul_broadcast`，会导致：

```
程序：
  MUL x1, x2, x3    ; 乘法，结果写 x1
  ADD x4, x1, x5    ; 加法，依赖 x1

执行过程：
  周期 N:   MUL 发射到乘法器
  周期 N+1: ADD 发射到 RS，qj 等待 MUL 的 ROB 索引
  周期 N+4: MUL 完成，广播 mul_broadcast

  BUG: RS 没有监听 mul_broadcast → ADD 永远等待 → 死锁！
```

**修复**：确保 `RS_downstream.build()` 接收并处理 `mul_broadcast` 参数。

## 7. Flush 处理

当分支预测错误触发 Flush 时：

```python
for i in range(MUL_RS_NUM):  # 清空所有 MUL_RS
    mul_rs[i].busy[0] = 0
    mul_rs[i].fired[0] = 0
    mul_rs[i].qj_valid[0] = 0
    mul_rs[i].qk_valid[0] = 0
```

**注意**：正在乘法器中执行的指令不会被取消，因为：

1. 乘法器没有实现中断机制
2. 但其结果写入的 ROB entry 已被 Flush，commit 时会被忽略

## 8. 测试验证

### 8.1 测试用例

**simple_mul.c:**

```c
int main() {
    int a = 7;
    int b = 8;
    return a * b;  // 预期: 56 (0x38)
}
```

**vector_mul_real.c:**

```c
int A[10] = {1,2,3,4,5,6,7,8,9,10};
int B[10] = {10,9,8,7,6,5,4,3,2,1};
int C[10];

int main() {
    for (int i = 0; i < 10; i++)
        C[i] = A[i] * B[i];  // 使用 MUL 指令
    return 10;
}
```

### 8.2 测试结果

| 测试            | 状态    | 周期数 | 指令数 |
| --------------- | ------- | ------ | ------ |
| simple_mul      | ✅ PASS | 43     | 19     |
| vector_mul_real | ✅ PASS | 486    | 268    |

## 9. 文件位置

| 组件              | 文件                 | 行号    |
| ----------------- | -------------------- | ------- |
| 乘法指令解码      | `src/instruction.py` | 220-240 |
| ALU 类型定义      | `src/instruction.py` | 261-264 |
| MultiplierRegs    | `src/multiplier.py`  | 30-40   |
| MultiplierState   | `src/multiplier.py`  | 43-106  |
| MUL_RSEntry       | `src/multiplier.py`  | 149-161 |
| MUL_RS_downstream | `src/multiplier.py`  | 164-260 |
| Issue 逻辑        | `src/main.py`        | 268-291 |
| Flush 逻辑        | `src/main.py`        | 515-520 |

## 10. 未来优化方向

1. **流水线乘法器**：每周期可发射新乘法，吞吐量提升到 1
2. **增加 RS 数量**：缓存更多乘法指令
3. **支持除法指令**：DIV/DIVU/REM/REMU（M 扩展完整实现）
4. **CDB 广播**：修复框架 bug 后，通过 CDB 广播结果
5. **早期 Bypass**：在 DONE 状态前一周期就开始传递结果

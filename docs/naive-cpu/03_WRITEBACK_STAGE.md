# 写回阶段 (Writeback Stage) 详细文档

## 📌 概述

写回阶段（Writeback Stage，简称 W 阶段）是 Minor-CPU 流水线的最后一个阶段。它的职责相对简单但至关重要：

1. **写入寄存器堆** - 将计算结果或内存数据写入目标寄存器
2. **释放寄存器占用** - 更新 `reg_onwrite` 位图，标记寄存器可用
3. **完成指令提交** - 标志一条指令的完全执行结束

---

## 📂 源文件位置

写回阶段的代码位于 `writeback.py` 文件中，代码非常简洁。

---

## 🏗️ 模块定义

```python
from assassyn.frontend import *
from opcodes import *

class WriteBack(Module):

    def __init__(self):
        super().__init__(
            ports={
                'rd': Port(Bits(5)),      # 目标寄存器编号
                'mdata': Port(Bits(32)),  # 要写入的数据
            },
            no_arbiter=True)  # 不使用仲裁器

        self.name = 'W'
```

### 输入端口详解

| 端口名  | 位宽    | 来源     | 说明                                   |
| ------- | ------- | -------- | -------------------------------------- |
| `rd`    | 5 bits  | 访存阶段 | 目标寄存器编号，范围 0-31，对应 x0-x31 |
| `mdata` | 32 bits | 访存阶段 | 要写入寄存器的 32 位数据               |

### `no_arbiter=True` 的含义

在 Assassyn 框架中，模块默认带有仲裁器来处理来自多个源的请求。设置 `no_arbiter=True` 意味着：

1. 该模块只接受单一来源的调用（来自访存阶段）
2. 简化硬件设计，减少面积和延迟
3. 流水线中的写回阶段本来就是顺序执行的，不需要仲裁

---

## 🔄 执行流程详解

### 完整代码

```python
@module.combinational
def build(self, reg_file: Array):
    """
    写回阶段的组合逻辑

    参数:
        reg_file: 32 个 32 位通用寄存器组成的数组

    返回:
        rd: 目标寄存器编号，用于更新 reg_onwrite
    """

    # 从端口弹出数据
    rd, mdata = self.pop_all_ports(False)

    # 只有当 rd 不是 x0 时才写入
    with Condition((rd != Bits(5)(0))):
        log("writeback        | x{:02}          | 0x{:08x}", rd, mdata)
        reg_file[rd] = mdata

    return rd
```

### 第一步：获取输入数据

```python
rd, mdata = self.pop_all_ports(False)
```

**`pop_all_ports(False)` 说明**：

- `pop_all_ports()` 一次性从所有端口弹出数据
- 参数 `False` 表示按照端口定义的顺序返回（非命名方式）
- 返回值顺序与 `__init__` 中 `ports` 字典的定义顺序一致

**数据来源追溯**：

```
┌─────────────┐    bind()     ┌─────────────┐    async_called()    ┌─────────────┐
│ MemAccess   │──────────────▶│   FIFO      │─────────────────────▶│  WriteBack  │
│  rd, arg    │               │  缓冲队列    │                      │  rd, mdata  │
└─────────────┘               └─────────────┘                      └─────────────┘
```

---

### 第二步：条件写入寄存器

```python
with Condition((rd != Bits(5)(0))):
    log("writeback        | x{:02}          | 0x{:08x}", rd, mdata)
    reg_file[rd] = mdata
```

**为什么要检查 `rd != 0`？**

RISC-V 架构中，x0 寄存器（也称为 `zero` 寄存器）有特殊规定：

1. **读取 x0 始终返回 0** - 无论写入什么值
2. **写入 x0 无效** - 任何写入操作都被忽略
3. **硬件实现可以优化** - 不需要为 x0 分配实际存储

因此，我们在软件/硬件层面都跳过对 x0 的写入操作。

**使用 x0 的场景**：

```asm
# x0 作为丢弃目标
jal x0, label      # 跳转但不保存返回地址（不是函数调用）

# x0 作为零源
add x1, x2, x0     # x1 = x2 + 0，即 mov x1, x2
beq x0, x0, label  # 无条件跳转（总是相等）

# 某些指令的默认行为
sw x1, 0(x2)       # store 指令没有 rd，rd 字段为 0
```

---

### 第三步：返回目标寄存器编号

```python
return rd
```

**返回值的用途**：

返回的 `rd` 用于更新 `reg_onwrite` 位图，标记该寄存器不再被占用。这是通过 `Onwrite` 下游模块实现的：

```python
class Onwrite(Downstream):
    def build(self, reg_onwrite, exec_rd, writeback_rd):
        # ...
        wb_bit = (wb_rd != Bits(5)(0)).select(Bits(32)(1) << wb_rd, Bits(32)(0))
        reg_onwrite[0] = reg_onwrite[0] ^ ex_bit ^ wb_bit
        # ...
```

---

## 📊 寄存器堆结构

### 定义

```python
# 在 main.py 的 build_cpu() 中
reg_file = RegArray(bits32, 32)  # 32 个 32 位寄存器
```

### 访问模式

| 操作 | 阶段     | 端口       | 说明            |
| ---- | -------- | ---------- | --------------- |
| 读取 | 执行 (E) | 2 个读端口 | 读取 rs1 和 rs2 |
| 写入 | 写回 (W) | 1 个写端口 | 写入 rd         |

### 读写冲突处理

当同一周期内读写同一寄存器时（例如 `add x1, x1, x2`）：

```
周期 N:
  - 执行阶段读取 x1（旧值）
  - 写回阶段写入 x1（新值）

结果: 读取获得旧值，这是正确的行为
      （因为当前执行的指令依赖的是之前指令的结果）
```

---

## 🔗 与旁路网络的关系

### 旁路时序

```
写回阶段设置 wb_bypass:
  ↓
  访存阶段已经设置了 wb_bypass
  写回阶段不需要额外设置

但是 Onwrite 会更新 reg_onwrite:
  ↓
  下一周期执行阶段可以知道寄存器已释放
```

### 完整的数据前递链

```
时间轴: ─────────────────────────────────────────────────────▶

指令 A (add x1, x2, x3):
    │ E  │ M  │ W  │
         │    │    │
         │    │    └── 周期 3: 写入 reg_file[1]
         │    │        更新 reg_onwrite
         │    │
         │    └─────── 周期 2: 设置 wb_bypass
         │
         └──────────── 周期 1: 设置 exec_bypass, mem_bypass
                       result 可用

指令 B (sub x4, x1, x5):
              │ E  │
              │    │
              └────└── 如果在周期 1-2: 从旁路获取 x1
                       如果在周期 3+: 从 reg_file 获取 x1
```

---

## 📈 性能特性

### 单周期完成

写回阶段是纯组合逻辑，在单个时钟周期内完成：

```
时钟上升沿
    │
    ├── 读取 FIFO 中的 rd 和 mdata
    │
    ├── 检查 rd != 0
    │
    ├── 写入 reg_file[rd] = mdata
    │
    └── 输出 rd 给 Onwrite

时钟下降沿
    │
    └── 数据稳定，准备下一周期
```

### 吞吐量

- **理想情况**: 1 条指令/周期
- **实际情况**: 取决于前级流水线的暂停情况

---

## 🔍 日志输出分析

```python
log("writeback        | x{:02}          | 0x{:08x}", rd, mdata)
```

**示例输出**：

```
@line:21    Cycle @10.00: [W]    writeback        | x01          | 0x00000064
@line:21    Cycle @11.00: [W]    writeback        | x02          | 0x00000001
@line:21    Cycle @12.00: [W]    writeback        | x01          | 0x00000065
```

**字段解释**：

| 字段           | 含义                  |
| -------------- | --------------------- |
| `@line:21`     | 源代码行号            |
| `Cycle @10.00` | 当前仿真周期          |
| `[W]`          | 模块名称（WriteBack） |
| `x01`          | 目标寄存器            |
| `0x00000064`   | 写入的值（十六进制）  |

---

## ⚠️ 注意事项

### 1. 指令提交点

写回阶段是指令的**提交点（Commit Point）**。一旦写回完成：

- 指令的所有副作用都已生效
- 异常处理可以基于此状态进行恢复
- 性能计数器可以增加已完成指令数

### 2. 写回顺序

Minor-CPU 是顺序执行处理器，写回顺序与程序顺序一致。这保证了：

- 精确异常处理
- 简化的寄存器一致性模型
- 无需复杂的重排序缓冲区

### 3. 异常情况

当前实现不包含异常处理。如果需要支持异常：

```python
# 假设的异常处理代码
with Condition(has_exception):
    # 不写入寄存器
    # 跳转到异常处理程序
    pass
with Condition(~has_exception):
    with Condition(rd != Bits(5)(0)):
        reg_file[rd] = mdata
```

---

## 🔗 与其他模块的接口

### 从访存阶段接收数据

```python
# 在 memory_access.py 中
wb_bound = writeback.bind(mdata=arg, rd=rd)
wb_bound.async_called()
```

### 向 Onwrite 提供数据

```python
# 在 main.py 中
onwrite_downstream.build(
    reg_onwrite=reg_onwrite,
    exec_rd=exec_rd,
    writeback_rd=wb_rd,  # 来自 writeback.build() 的返回值
)
```

---

## 📊 完整流水线中的位置

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ Fetch   │──▶│ Decode  │──▶│ Execute │──▶│MemAccess│──▶│WriteBack│
│   (F)   │   │   (D)   │   │   (E)   │   │   (M)   │   │   (W)   │
└─────────┘   └─────────┘   └─────────┘   └─────────┘   └────┬────┘
                                                              │
                                                              ▼
                                                        ┌───────────┐
                                                        │ reg_file  │
                                                        │  x0-x31   │
                                                        └───────────┘
```

---

## 📝 代码完整性验证

### 正确性条件

1. **所有指令最终都经过写回阶段**

   - 即使是 `store` 或 `branch` 指令也会经过
   - 这些指令的 `rd=0`，不会实际写入

2. **写入值的正确性**

   - `mdata` 来自访存阶段的正确选择
   - Load: D-Cache 数据
   - ALU: 计算结果
   - JAL/JALR: PC+4

3. **时序正确性**
   - 写回发生在执行和访存之后
   - `reg_onwrite` 在写回后更新

### 测试用例

```asm
# 基本写回测试
addi x1, x0, 100    # x1 = 100
addi x2, x0, 200    # x2 = 200
add  x3, x1, x2     # x3 = 300

# 验证: 周期 N 执行 add, 周期 N+2 写回
#       此时 x3 应该等于 300
```

---

## 🎯 总结

写回阶段虽然代码简洁，但它是整个流水线的"终点站"，确保：

1. ✅ 计算结果正确写入寄存器
2. ✅ 寄存器占用状态正确更新
3. ✅ 指令执行流程完整闭环
4. ✅ 与旁路网络正确配合

它的简洁性恰恰体现了良好的流水线设计：复杂的工作在前级完成，写回只负责最终的"落笔"。

# Minor-CPU 完整代码分析报告

## 📌 宏观架构概述

Minor-CPU 是一个使用 Assassyn 框架实现的 **单发射（Single-Issue）顺序执行 RISC-V 处理器**。它实现了 RV32I 基础指令集的大部分指令。

### 整体流水线结构

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌──────────┐
│ Fetcher │───▶│ Decoder │───▶│Execution│───▶│ Memory  │───▶│Writeback │
│   (F)   │    │   (D)   │    │   (E)   │    │ Access  │    │   (W)    │
└─────────┘    └─────────┘    └─────────┘    │   (M)   │    └──────────┘
                                            └─────────┘
```

### 关键数据通路

1. **取指 (Fetch)**: 从 I-Cache 读取指令
2. **译码 (Decode)**: 解析指令类型、操作数、控制信号
3. **执行 (Execute)**: ALU 运算、分支判断
4. **访存 (Memory)**: 读/写 D-Cache
5. **写回 (Writeback)**: 写入寄存器堆

---

## 📂 文件结构说明

| 文件 | 作用 |
|------|------|
| `main.py` | 主程序，定义所有模块并连接流水线 |
| `instructions.py` | 指令类型定义和解码逻辑 |
| `decoder.py` | 译码器主逻辑 |
| `opcodes.py` | Opcode 常量定义 |
| `writeback.py` | 写回阶段 |
| `memory_access.py` | 访存阶段 |
| `nocsr.py` | 无 CSR 支持的简化版本 |
| `br_pre_main.py` | 带分支预测的版本 |

---

# 📖 各文件详细分析

---

## 1. `instructions.py` - 指令类型与解码

### 1.1 核心概念

这个文件定义了 RISC-V 的 6 种指令格式，并提供指令解码功能。

### 1.2 `InstType` 基类

```python
class InstType:
    FIELDS = [
        ((0, 6), 'opcode', Bits),   # 位 0-6: 操作码
        ((7, 11), 'rd', Bits),       # 位 7-11: 目标寄存器
        ((15, 19), 'rs1', Bits),     # 位 15-19: 源寄存器1
        ((20, 24), 'rs2', Bits),     # 位 20-24: 源寄存器2
        ((12, 14), 'funct3', Bits),  # 位 12-14: 功能码3
        ((25, 31), 'funct7', Bits),  # 位 25-31: 功能码7
    ]
```

**作用**：定义 RISC-V 指令的标准字段位置。

**`__init__` 方法**：
- 根据指令类型决定哪些字段是有效的（`rd`, `rs1`, `rs2`, `funct3`, `funct7`）
- 创建 `Record` 类型来表示指令结构
- 存储原始指令值 `self.value`

**`view()` 方法**：
```python
def view(self):
    return self.dtype.view(self.value)
```
**作用**：把 32 位原始指令转换为带命名字段的视图，这样就可以用 `view.opcode`、`view.rd` 等方式访问指令字段。

### 1.3 六种指令类型

#### R-Type (寄存器型)
```python
class RInst(InstType):
    # 字段: opcode, rd, rs1, rs2, funct3, funct7
    # 用途: add, sub, and, or, xor, sll, srl 等
```
**特点**：所有字段都存在，没有立即数。

#### I-Type (立即数型)
```python
class IInst(InstType):
    # 字段: opcode, rd, rs1, funct3, imm[11:0]
    # 用途: addi, lw, jalr 等
```
**特点**：12 位立即数，需要符号扩展。

#### S-Type (存储型)
```python
class SInst(InstType):
    # 字段: opcode, rs1, rs2, funct3, imm[11:5], imm[4:0]
    # 用途: sw, sb 等
```
**特点**：立即数分散在两个位置。

#### U-Type (高位立即数型)
```python
class UInst(InstType):
    # 字段: opcode, rd, imm[31:12]
    # 用途: lui, auipc
```
**特点**：20 位高位立即数。

#### J-Type (跳转型)
```python
class JInst(InstType):
    # 字段: opcode, rd, imm[20], imm[10:1], imm[11], imm[19:12]
    # 用途: jal
```
**特点**：立即数位置打乱，需要重新组装。

#### B-Type (分支型)
```python
class BInst(InstType):
    # 字段: opcode, rs1, rs2, funct3, imm[12], imm[10:5], imm[4:1], imm[11]
    # 用途: beq, bne, blt, bge 等
```
**特点**：用于条件分支，立即数位置分散。

### 1.4 `InstSignal` - 解码结果封装

```python
class InstSignal:
    def __init__(self, eq, alu, cond=None):
        self.eq = eq      # 1-bit: 指令是否匹配
        self.alu = ...    # 16-bit 独热码: 选择哪个 ALU 操作
        self.cond = ...   # 16-bit 独热码: 分支条件
        self.flip = ...   # 1-bit: 是否翻转条件
```

**工作原理**：
- `eq` 是硬件比较结果，表示当前指令是否匹配某个特定指令
- `alu` 使用独热编码（one-hot），例如 `1 << ALU_ADD` 表示加法
- 后续用 `select1hot` 根据 `alu` 选择对应的计算结果

### 1.5 `decode()` 方法解析

以 R-Type 为例：
```python
@rewrite_assign
def decode(self, opcode, funct3, funct7, alu, ex_code=None):
    view = self.view()                              # 获取字段视图
    opcode = view.opcode == Bits(7)(opcode)         # 比较 opcode
    funct3 = view.funct3 == Bits(3)(funct3)         # 比较 funct3
    funct7 = view.funct7 == Bits(7)(funct7)         # 比较 funct7
    eq = opcode & funct3 & funct7 & ex              # 全部匹配才为真
    return InstSignal(eq, alu)
```

**关键点**：
- 这些比较生成的是**硬件比较电路**，不是 Python 运行时比较
- `eq` 是一个 1-bit 硬件信号
- 所有支持的指令并行解码，最后用 `select1hot` 选出匹配的那个

### 1.6 `supported_opcodes` - 指令定义表

```python
supported_opcodes = [
  # (助记符, (解码参数...), 指令类型)
  ('add', (0b0110011, 0b000, 0b0000000, RV32I_ALU.ALU_ADD), RInst),
  ('beq', (0b1100011, 0b000, RV32I_ALU.ALU_CMP_EQ, False), BInst),
  ...
]
```

**作用**：定义所有支持的指令及其编码参数。

### 1.7 `deocder_signals` - 解码输出信号结构

```python
deocder_signals = Record(
  rs1=Bits(5),         # 源寄存器1
  rs1_valid=Bits(1),   # rs1 是否有效
  rs2=Bits(5),         # 源寄存器2
  rs2_valid=Bits(1),   # rs2 是否有效
  rd=Bits(5),          # 目标寄存器
  rd_valid=Bits(1),    # rd 是否有效
  imm=Bits(32),        # 立即数（扩展后）
  imm_valid=Bits(1),   # 立即数是否有效
  memory=Bits(2),      # [0]=读, [1]=写
  alu=Bits(16),        # ALU 操作独热码
  cond=Bits(16),       # 条件独热码
  flip=Bits(1),        # 条件翻转
  is_branch=Bits(1),   # 是否分支指令
  is_offset_br=Bits(1),# 是否 PC 相对跳转
  link_pc=Bits(1),     # 是否链接 PC (jal/jalr)
  ...
)
```

---

## 2. `decoder.py` - 译码器逻辑

### 2.1 `decode_logic()` 函数

这是译码器的核心函数，实现了完整的指令解码流程。

```python
@rewrite_assign
def decode_logic(inst):
    # 1. 为每种指令类型创建视图
    views = {i: i(inst) for i in supported_types}
    
    # 2. 遍历所有支持的指令进行匹配
    for mn, args, cur_type in supported_opcodes:
        ri = views[cur_type]
        signal = ri.decode(*args)  # 调用对应类型的 decode
        eq = signal.eq
        
        # 收集匹配信号
        alu = alu | eq.select(signal.alu, Bits(0))
        ...
    
    # 3. 提取操作数
    rd = rd_valid.select(views[RInst].view().rd, Bits(5)(0))
    rs1 = rs1_valid.select(views[RInst].view().rs1, Bits(5)(0))
    
    # 4. 处理立即数
    for i in supported_types:
        new_imm = views[i].imm(True)
        if new_imm is not None:
            imm = is_type[i].select(new_imm, imm)
    
    # 5. 返回打包的解码信号
    return deocder_signals.bundle(
        memory=memory,
        alu=alu,
        ...
    )
```

**核心思路**：
1. 所有指令类型**并行解码**
2. 每条指令产生一个 `eq` 信号表示是否匹配
3. 用 `select` 多路选择器根据匹配结果选出正确的控制信号
4. 打包成 `Record` 传递给执行阶段

---

## 3. `main.py` - 主程序与流水线

### 3.1 `Execution` - 执行阶段

```python
class Execution(Module):
    def __init__(self):
        super().__init__(
            ports={
                'signals': Port(deocder_signals),  # 解码信号
                'fetch_addr': Port(Bits(32)),      # 指令地址
            })
```

**核心功能**：

#### 3.1.1 数据冒险检测
```python
# 检查 rs1 是否可用（旁路 or 无冲突）
a_valid = (exec_bypass_reg[0] == rs1) |    # 执行阶段旁路
          (mem_bypass_reg[0] == rs1) |     # 访存阶段旁路
          ~signals.rs1_valid |              # 不需要 rs1
          (~(on_write >> rs1))[0:0]         # 寄存器未被占用

valid = a_valid & b_valid & rd_valid
wait_until(valid)  # 阻塞直到数据可用
```

**原理**：
- `reg_onwrite` 记录哪些寄存器正在被写入
- 旁路（bypass）机制允许直接获取前序阶段的结果
- `wait_until` 在硬件层面实现流水线暂停

#### 3.1.2 操作数获取（带旁路）
```python
def bypass(bypass_reg, bypass_data, idx, value):
    return (bypass_reg[0] == idx).select(bypass_data[0], value)

a = bypass(mem_bypass_reg, mem_bypass_data, rs1, rf[rs1])
a = bypass(exec_bypass_reg, exec_bypass_data, rs1, a)
a = (rs1 == Bits(5)(0)).select(Bits(32)(0), a)  # x0 恒为 0
```

**旁路优先级**：
1. 先检查访存阶段旁路
2. 再检查执行阶段旁路
3. 最后从寄存器堆读取

#### 3.1.3 ALU 运算
```python
results = [Bits(32)(0)] * RV32I_ALU.CNT

results[RV32I_ALU.ALU_ADD] = (alu_a + alu_b)
results[RV32I_ALU.ALU_SUB] = (a - b)
results[RV32I_ALU.ALU_CMP_LT] = (a < b).select(Bits(32)(1), Bits(32)(0))
...

result = alu.select1hot(*results)  # 根据 alu 独热码选择结果
```

**设计思路**：
- 并行计算所有可能的结果
- 用 `select1hot` 根据指令类型选择正确的结果
- 这在硬件上实现为大型多路选择器

#### 3.1.4 分支处理
```python
condition = signals.cond.select1hot(*results)
condition = signals.flip.select(~condition, condition)

with Condition(signals.is_branch):
    exec_br_dest[0] = condition[0:0].select(result, pc0)
```

**分支判断**：
- 用 ALU 计算比较结果（相等、小于等）
- `flip` 用于实现 `bne`（不等）、`bge`（大于等于）等
- 分支目标地址写入 `exec_br_dest` 供取指阶段使用

### 3.2 `Decoder` - 译码阶段模块

```python
class Decoder(Module):
    @module.combinational
    def build(self, executor: Module, rdata: RegArray):
        fetch_addr = self.pop_all_ports(False)
        inst = rdata[0].bitcast(Bits(32))
        
        signals = decode_logic(inst)
        
        e_call = executor.async_called(signals=signals, fetch_addr=fetch_addr)
        e_call.bind.set_fifo_depth(signals=2, fetch_addr=2)
```

**作用**：
- 从 I-Cache 读取指令 (`rdata`)
- 调用 `decode_logic` 解码
- 异步调用执行模块

### 3.3 `Fetcher` 与 `FetcherImpl` - 取指阶段

```python
class Fetcher(Module):
    def build(self):
        pc_reg = RegArray(Bits(32), 1)
        addr = pc_reg[0]
        return pc_reg, addr
```

**基础取指**：维护 PC 寄存器。

```python
class FetcherImpl(Downstream):
    def build(self, on_branch, ex_bypass, ...):
        # 分支预测/恢复逻辑
        should_fetch = (~on_branch) & (~br_sm[0]) & fetch_valid[0]
        
        # 确定取指地址
        to_fetch = (jump_flag).select(ex_bypass[0], pc_addr)
        
        # 限制流水线深度
        real_fetch = should_fetch & (new_cnt < Int(8)(3))
        
        icache.build(Bits(1)(0), real_fetch, to_fetch[...], Bits(32)(0))
```

**复杂取指**：
- 处理分支预测失败的恢复
- 限制在途指令数量（`ongoing < 3`）
- 控制 I-Cache 访问

### 3.4 `Onwrite` - 寄存器占用追踪

```python
class Onwrite(Downstream):
    def build(self, reg_onwrite, exec_rd, writeback_rd):
        ex_bit = (ex_rd != 0).select(Bits(32)(1) << ex_rd, Bits(32)(0))
        wb_bit = (wb_rd != 0).select(Bits(32)(1) << wb_rd, Bits(32)(0))
        
        reg_onwrite[0] = reg_onwrite[0] ^ ex_bit ^ wb_bit
```

**作用**：
- 用位图追踪哪些寄存器正在被写入
- 执行阶段设置位，写回阶段清除位
- 用于数据冒险检测

### 3.5 `build_cpu()` - CPU 构建函数

```python
def build_cpu(depth_log):
    sys = SysBuilder('minor_cpu')
    
    with sys:
        # 1. 定义数据结构
        reg_file = RegArray(bits32, 32)          # 32 个通用寄存器
        exec_bypass_reg = RegArray(bits5, 1)     # 旁路寄存器号
        exec_bypass_data = RegArray(bits32, 1)   # 旁路数据
        
        # 2. 创建 Cache
        icache = SRAM(width=32, depth=1<<depth_log, ...)
        dcache = SRAM(width=32, depth=1<<depth_log, ...)
        
        # 3. 实例化各阶段模块
        fetcher = Fetcher()
        decoder = Decoder()
        executor = Execution()
        memory_access = MemoryAccess()
        writeback = WriteBack()
        
        # 4. 连接模块
        executor.build(
            exec_bypass_reg=exec_bypass_reg,
            mem_bypass_reg=mem_bypass_reg,
            rf=reg_file,
            memory=memory_access,
            ...
        )
```

---

## 4. `memory_access.py` - 访存阶段

```python
class MemoryAccess(Module):
    def __init__(self):
        super().__init__(
            ports={
                'rd': Port(Bits(5)),
                'mem_ext': Port(Bits(2)),
                'result': Port(Bits(32)),
                'is_mem_read': Port(Bits(1))
            },
            no_arbiter=True)
```

### 4.1 `build()` 方法

```python
def build(self, writeback, mem_bypass_reg, mem_bypass_data, ...):
    # 弹出端口数据
    mem_ext = self.mem_ext.pop()
    result = self.result.pop()
    rd = self.rd.pop()
    is_mem_read = self.is_mem_read.pop()
    
    # 读取 D-Cache 数据
    data = rdata[0].bitcast(Bits(32))
    
    # 设置旁路
    with Condition(is_mem_read):
        mem_bypass_reg[0] = rd
        mem_bypass_data[0] = data
    
    # 处理符号/零扩展
    ext = sign.select(Bits(24)(0xffffff), Bits(24)(0))
    data_cut = mem_ext[1:1].select(Bits(24)(0).concat(arg[0:7]), ext.concat(arg[0:7]))
    
    # 调用写回阶段
    wb_bound = writeback.bind(mdata=arg, rd=rd)
    wb_bound.async_called()
```

**功能**：
1. 处理 load 指令的数据读取
2. 实现符号扩展（`lw`）和零扩展（`lbu`）
3. 设置访存阶段旁路
4. 调用写回阶段

---

## 5. `writeback.py` - 写回阶段

```python
class WriteBack(Module):
    def __init__(self):
        super().__init__(
            ports={
                'rd': Port(Bits(5)),
                'mdata': Port(Bits(32)),
            }, no_arbiter=True)

    @module.combinational
    def build(self, reg_file: Array):
        rd, mdata = self.pop_all_ports(False)
        with Condition((rd != Bits(5)(0))):
            reg_file[rd] = mdata
        return rd
```

**功能**：
- 将结果写入寄存器堆
- 跳过 x0（恒为 0）
- 返回 `rd` 用于更新 `reg_onwrite`

---

## 6. `opcodes.py` - 操作码定义

```python
class Opcode:
    LUI     = Bits(7)(0b0110111)
    ADDI    = Bits(7)(0b0010011)
    ADD     = Bits(7)(0b0110011)
    LW      = Bits(7)(0b0000011)
    BNE     = Bits(7)(0b1100011)
    ...

class OpcodeChecker:
    def check(self, *types):
        # 检查 opcode 是否匹配指定类型
        ...
```

**作用**：提供 opcode 常量和检查工具。

---

## 7. `RV32I_ALU` - ALU 操作定义

```python
class RV32I_ALU:
    CNT = 16          # 总共 16 种操作

    ALU_ADD = 0       # 加法
    ALU_SUB = 1       # 减法
    ALU_XOR = 2       # 异或
    ALU_OR = 3        # 或
    ALU_AND = 4       # 与
    ALU_SLL = 5       # 逻辑左移
    ALU_SRL = 6       # 逻辑右移
    ALU_SRA = 7       # 算术右移
    ALU_CMP_EQ = 8    # 相等比较
    ALU_CMP_LT = 9    # 有符号小于
    ALU_CMP_LTU = 10  # 无符号小于
    ALU_TRUE = 11     # 恒真（用于 jal）
    ALU_NONE = 15     # 无操作
```

---

## 🔄 数据流总结

```
                    ┌──────────────────────────────────────────┐
                    │              旁路网络                     │
                    │  ┌─────────┐ ┌─────────┐ ┌─────────┐    │
                    │  │exec_bypass│ │mem_bypass│ │wb_bypass│    │
                    │  └────┬────┘ └────┬────┘ └────┬────┘    │
                    └───────┼──────────┼──────────┼───────────┘
                            │          │          │
┌────────┐   inst   ┌───────▼──┐  signals ┌──────▼──┐  result  ┌───────▼──┐  mdata  ┌──────────┐
│I-Cache │─────────▶│ Decoder  │─────────▶│Execution│─────────▶│MemAccess │────────▶│Writeback │
└────────┘          └──────────┘          └────┬────┘          └────┬─────┘         └────┬─────┘
                                               │                    │                    │
                                               │                    │                    │
                                               ▼                    ▼                    ▼
                                         ┌─────────┐          ┌─────────┐          ┌─────────┐
                                         │ reg_onwrite (占用追踪)                             │
                                         └────────────────────────────────────────────────────┘
```

---

## 📊 性能特性

| 特性 | 实现方式 |
|------|---------|
| 流水线深度 | 5 级 (F/D/E/M/W) |
| 数据冒险 | 旁路 + 暂停 |
| 控制冒险 | 分支预测 (br_pre_main.py) |
| 分支延迟 | ~2 周期 |
| 内存模型 | 分离 I/D Cache |

---

## 🛠️ 运行方式

```bash
cd examples/minor-cpu/src
source ../../../setup.sh
python main.py
```

测试用例在 `unit-tests/` 和 `workloads/` 目录下。

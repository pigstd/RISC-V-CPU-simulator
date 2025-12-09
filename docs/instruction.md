# RV32I 指令参考（模拟器实现版）

由 ChatGPT 生成。

> 适用场景：单核、顺序执行、仅用户态/裸机（无 OS/调试器），仅 **RV32I**（不含压缩与其他扩展）。  
> 目标：给出**需要的指令**、**结构（编码/字段）**与**功能/语义**，作为你写解释器/模拟器的实现依据。

---

## 0) 范围与基本约定

- **架构**：RV32I，`XLEN=32`；寄存器 `x0` **硬连为 0**（对 `x0` 的写回应被丢弃）。
- **取指对齐**：基础 ISA `IALIGN=32` → 指令必须 **4 字节对齐**。跳转/被采纳分支若把 `pc` 引到非 4B 对齐地址，**在该跳转/分支指令处**报告 *instruction‑address‑misaligned*。
- **整数算术**：不产生算术异常（溢出忽略，结果按 32 位截断）。
- **移位**：  
  - 立即数移位（`SLLI/SRLI/SRAI`）仅使用 `shamt` **低 5 位**；`SRAI` 与 `SRLI` 由立即数高位位段区分。  
  - 寄存器移位（`SLL/SRL/SRA`）仅使用 `rs2` **低 5 位**。
- **访存**：`addr = x[rs] + sext(imm12)`；是否支持**非对齐**由 EEI（执行环境接口）决定：实现可选择**支持**或在不对齐时抛 *misaligned/access fault*。  
  **注意**：即使 `rd = x0`，**Load 的异常与任何副作用也必须发生**（只是丢弃结果）。
- **不在本文件内**：`FENCE.I`（属于 **Zifencei** 扩展），CSR 指令等。

---

## 1) 指令格式与立即数拼接（R/I/S/B/U/J）

- **R**：`funct7 | rs2 | rs1 | funct3 | rd | opcode`  
- **I**：`imm[11:0] | rs1 | funct3 | rd | opcode`（`sext(imm)`）  
- **S**：`imm[11:5] | rs2 | rs1 | funct3 | imm[4:0] | opcode`（组合后 `sext`）  
- **B**：`imm[12|10:5] | rs2 | rs1 | funct3 | imm[4:1|11] | opcode` → 组合后 **再左移 1**；`sext`  
- **U**：`imm[31:12] | rd | opcode` → 使用时 **左移 12**  
- **J**：`imm[20|10:1|11|19:12] | rd | opcode` → 组合后 **再左移 1**；`sext`

---

## 2) 常量/地址生成（U/J/I）

### LUI — *U 型*（`opcode = 0110111`）
- **语义**：`x[rd] = (imm20 << 12)`  
- **用途**：装高 20 位，配合 `ADDI`/`ORRI` 等构造常量。

### AUIPC — *U 型*（`opcode = 0010111`）
- **语义**：`x[rd] = pc + (imm20 << 12)`  
- **用途**：构造 PC 相对地址/常量池基址。

### JAL — *J 型*（`opcode = 1101111`）
- **语义**：`x[rd] = pc + 4`；`pc = pc + sext(J_imm) << 1`（范围 ±1 MiB）。  
- **异常**：若目标非 4B 对齐 → 在 `JAL` 本条报告 *instruction‑address‑misaligned*。

### JALR — *I 型*（`opcode = 1100111`, `funct3 = 000`）
- **语义**：`t = x[rs1] + sext(imm12)`；`pc = (t & ~1)`（**目标最低位强制清零**）；`x[rd] = pc_old + 4`。  
- **异常**：若目标非 4B 对齐 → 在 `JALR` 本条报告 *instruction‑address‑misaligned*。

### 条件分支 — *B 型*（`opcode = 1100011`）
- **指令**：`BEQ/BNE/BLT/BGE/BLTU/BGEU` 对应 `funct3=000/001/100/101/110/111`。  
- **语义**：`target = pc + sext(B_imm) << 1`；`take = (==, !=, <, >=)`（有/无符号取决于指令）。  
  仅当 **采取分支** 且目标非 4B 对齐时报告 *instruction‑address‑misaligned*。

---

## 3) 访存（Load/Store）

> 主 opcode：`LOAD = 0000011`，`STORE = 0100011`。有效地址：`x[rs1] + sext(imm12)`。

### 加载（I 型，`funct3` 指示宽度/符号）
- `LB`（`000`）：读 **1B**，**符号扩展**到 32 位写 `x[rd]`  
- `LBU`（`100`）：读 **1B**，**零扩展**到 32 位  
- `LH`（`001`）：读 **2B**，**符号扩展**到 32 位  
- `LHU`（`101`）：读 **2B**，**零扩展**到 32 位  
- `LW`（`010`）：读 **4B**，原样写 `x[rd]`

> 注：目前为了实现 benchmark，只需要管 LW 指令，其他的可以先不实现。

**异常/对齐**：非对齐行为由 EEI 决定（可支持或抛 *misaligned*/ *access fault*）。即使 `rd=x0`，也必须触发相应异常/副作用（只是不写回结果）。

### 存储（S 型，`funct3` 指示宽度）
- `SB`（`000`）/ `SH`（`001`）/ `SW`（`010`）：把 `x[rs2]` 的低 8/16/32 位写入内存  
**异常/对齐**：同上。

---

## 4) 立即数算术/逻辑（OP‑IMM，`opcode = 0010011`）

- `ADDI`（`funct3=000`）：`x[rd] = x[rs1] + sext(imm12)`（整数运算**不产生溢出异常**）  
- `SLTI`/`SLTIU`（`010/011`）：按 **有符号/无符号** `<` 置 `x[rd]` 为 1/0（立即数仍按 `sext` 解释）  
- `XORI`/`ORI`/`ANDI`（`100/110/111`）：位运算  
- `SLLI`（`001`）：`x[rd] = x[rs1] << shamt[4:0]`  
- `SRLI`/`SRAI`（`101`）：逻辑/算术右移；移位数取 `shamt[4:0]`；`SRAI` 由高位位段区分（见下节编码速查）

---

## 5) 寄存器算术/逻辑（OP，`opcode = 0110011`）

- `ADD/SUB`：`funct3=000`，`funct7=0000000/0100000`  
- `SLL/SLT/SLTU/XOR/SRL/SRA/OR/AND`：  
  - `funct3 = 001/010/011/100/101/101/110/111`  
  - `SRA` 用 `funct7 = 0100000`，其余 `funct7 = 0000000`  
- 右移类型：`SRL` 逻辑、`SRA` 算术；寄存器移位只看 `rs2 & 0x1F`

---

## 6) 内存顺序（FENCE）

- **FENCE pred, succ** — *MISC‑MEM*（`opcode = 0001111`, `funct3 = 000`）  
  建立对同一 hart 的 **R/W/I/O** 访问的先后可见性；简单模拟器（单核、无并发 I/O）可视作**无可见效果**。  
  一些编码（如 `pred=0` 且 `fm=0`）为 **HINT**（可忽略）。

> 注：**`FENCE.I` 不属于 RV32I**，位于 **Zifencei** 扩展。

> 注：目前应该是不需要考虑这个操作的，如果遇到了，可以直接当作 NOP 处理或者报错。

---

## 7) 系统类（SYSTEM, `opcode = 1110011`）

- **ECALL**（`funct3=000`, `imm12=0`）：环境调用 → **精确陷入**到 EEI  
- **EBREAK**（`funct3=000`, `imm12=1`）：断点 → **精确陷入**到调试/EEI  
- **实现建议（你的场景）**：解码并抛出可诊断的 Trap（例如设置 cause=Environment call / Breakpoint）。  
  在极简实现里，**ECALL/EBREAK 可用一个统一的 SYSTEM‑Trap 处理**；`FENCE` 可按 **NOP** 处理。

---

## 8) 编码速查（主 opcode 与 `funct3/funct7`）

- **U**：`LUI(0110111)`，`AUIPC(0010111)`  
- **J/I**：`JAL(1101111)`；`JALR(1100111, funct3=000)`  
- **B**：`BRANCH(1100011)` → `BEQ/BNE/BLT/BGE/BLTU/BGEU = 000/001/100/101/110/111`  
- **LOAD**：`0000011` → `LB/LH/LW/LBU/LHU = 000/001/010/100/101`  
- **STORE**：`0100011` → `SB/SH/SW = 000/001/010`  
- **OP‑IMM**：`0010011` →  
  - `ADDI/SLTI/SLTIU/XORI/ORI/ANDI = 000/010/011/100/110/111`  
  - `SLLI/SRLI/SRAI = 001/101`（`SRAI` 由 `imm[11:5]=0100000` 区分；`SRLI` 为 `0000000`）  
- **OP**：`0110011` → 见第 5 节（`SRA` 用 `funct7=0100000`，其余 `0000000`）  
- **MISC‑MEM**：`0001111` → `FENCE (funct3=000)`  
- **SYSTEM**：`1110011` → `ECALL(imm12=0) / EBREAK(imm12=1)`（`funct3=000`）

---

## 9) 伪指令与提示（HINT）

- 规范化 **NOP**：`ADDI x0, x0, 0`。  
- 若将来加入并发/缓存/设备，再根据 `pred/succ/fm` 实现真实的内存顺序语义。

---

## 10) 实现要点（建议）

- **非法指令路径**：未实现的编码抛 *illegal instruction*，便于定位。  
- **不对齐策略**：初期可实现“强制对齐+抛异常”；后期需要时再做“非对齐拼接读写”。  
- **最小可用集**：若仅跑用户态裸机 C/测试：本文件第 2–5 节的全部 +（`FENCE` 视作 NOP；`ECALL/EBREAK` 视作 Trap）。  

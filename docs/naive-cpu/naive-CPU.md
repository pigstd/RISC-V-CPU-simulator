# Naive CPU 设计说明

本文描述了第一个“naive”版本 RISC-V 解释器 CPU 的结构与约束，为之后在 assassyn 框架中实现提供 blueprint。核心目标：一次只执行一条 RV32I 指令、无流水线/乱序，且可以只实现跑基准所需的精简指令子集，逐步迭代。

## 1. 设计目标与假设

- **架构范围**：RV32I，`XLEN=32`，统一小端。`x0` 始终为 0，写入被丢弃，浮点/CSR 不实现。
- **执行模型**：单核、完全顺序（fetch → decode → execute → writeback → pc+=4/跳转）。任何指令的耗时都可视作 1 个仿真“节拍”。
- **取指与地址**：指令固定 4 字节对齐，数据访存在 4 字节对齐策略即可；遇到未对齐/未实现编码直接抛异常（便于调试）。
- **目标场景**：能够在 assassyn 中执行 benchmark 循环与简单算术，优先满足 README 中列出的 3 个程序。
- **可观测接口**：CPU 通过 assassyn 的 `Memory` 对象访问统一地址空间，由宿主提供初始内存与 I/O。暂不实现中断。

## 2. 架构态（Architectural State）

| 组件 | 描述 |
| --- | --- |
| `pc` | 32 位程序计数器，指向当前指令。 |
| `regs[32]` | 通用寄存器堆，`regs[0]` 恒 0，写前可额外 mask。 |
| `memory` | 通过 assassyn 的 `MainMemoryInterface` 读写字节；对齐策略：只接受 4B 对齐 LW/SW。 |
| `csr/trap state` | 简化为 `Exception` 结构（类型、`badaddr`、`pc`），遇到非法指令或越界时抛到上层。 |
| `halt` flag | 用于 `ECALL`/`EBREAK`，让宿主捕捉并结束/切换。 |

> 备注：naive 阶段不必实现 CSR file，只需记录 trap 元信息方便日志。

## 3. 指令支持策略

参考 `docs/instruction.md` 给出的 RV32I 全量定义，naive CPU 分阶段实现：

### Stage 0 — 够跑简单循环

- `LUI/AUIPC`：构造常量、PC 相对地址。
- `JAL/JALR/BEQ/BNE`：最基本跳转/分支。
- `ADDI/ADD/SUB`：整数算术；`ADD/SUB` 由 opcode `0110011`，`funct7` 区分。
- `LW/SW`：只支持 4B load/store，遇到 `funct3!=010` 直接抛非法指令。
- `ECALL/EBREAK`：统一视作 “host trap”，携带当前 `pc` 与 `a0`（方便模拟 syscalls）。

Stage 0 已能覆盖“从 0 加到 100”的循环。

### Stage 1 — 覆盖向量加/乘 benchmark

- 逻辑/比较：`SLT/SLTU/SLTI/SLTIU`、`AND/OR/XOR` 及对应立即数形态。
- 乘法可由软件循环实现，若 benchmark 依赖 RV32M，可在此阶段用软件库替代；若需要硬件乘法，可新增 `mul_step()` 辅助（但仍保持单指令执行完毕）。
- `BLT/BGE/BLTU/BGEU`：带符号/无符号比较分支。
- 加载/存储扩展至 `LH/LHU/LB/LBU/SB/SH`，可选择“只允许对齐”，不对齐抛 trap。
- `FENCE` 视作 NOP，便于与汇编兼容。

### Stage 2 — 完整 RV32I

实现 `docs/instruction.md` 中剩余指令，保留顺序执行模型，为后续流水线版本打基础。

## 4. 执行循环

核心循环抽象为五级流水（IF/ID/EX/MEM/WB）的逐阶段状态机——虽然 naive 版本不并行执行多条指令，但仍按照流水顺序依次完成每级动作：

| 阶段 | 所有指令共性 | 算术/逻辑 | 访存 | 分支/跳转 | SYSTEM |
| --- | --- | --- | --- | --- | --- |
| IF（取指） | `pc` → memory 取 32b 指令，异常则记录 `AccessFault` | 同共性 | 同共性 | 同共性 | 同共性 |
| ID（译码） | 拆 opcode、funct、`rs1/rs2/rd`，查 handler；读取 `regs[rs*]` | 直接将 `rs` 值送往 EX | 生成基址与偏移 | 解析立即数/比较类型 | 识别 ECALL/EBREAK |
| EX（执行） | 组合控制信号，预先计算 `pc+4` | 做加减/逻辑/比较、生成 `rd_val` | 计算 `addr = rs1 + imm` | 计算分支条件与 `target` | 生成 trap 信息 |
| MEM（访存） | 默认无动作 | N/A | 根据 `addr` 在 memory 读写；完成 sign-extend | 若需要读取跳转表，可在此阶段访问 | 可选：与宿主交互 |
| WB（回写） | 若无异常，将结果写 `rd`，再更新 `pc` | `rd_val` 写寄存器，`pc = pc+4` | Load：mem 数据写回；Store：不写寄存器 | 若分支/跳转成立，`pc=target` 否则 `pc+4` | 设置 `halt` 并把 trap 暴露给宿主 |

实现要点：

1. **解码**：使用表驱动（opcode → handler），未命中时抛 “illegal instruction”。
2. **写回顺序**：先计算结果，再一次性写 `rd`，避免读写冲突。写 `x0` 时直接丢弃。
3. **分支跳转**：统一函数 `branch_target(pc, imm, align=4)`，负责对齐检查。
4. **访存**：封装 `load(size, addr)` / `store(size, addr, value)`；由该层进行对齐与 sign-extend。

## 5. 内存模型与异常

1. **读写规则**  
   - 只允许 4 字节对齐的 `LW/SW`，后续再放开其他宽度。  
   - 未对齐就直接抛 `MisalignedAccess{addr,size}`，方便定位。
2. **非法指令**  
   - 解码表里没有的 opcode/funct 直接抛 `IllegalInstruction{instr, pc}`。  
   - 这样可以在日志中准确看到是哪条指令没实现。
3. **越界访问**  
   - assassyn 的 `Memory` 若检测到访问越界，会给出错误；CPU 捕捉后转成 `AccessFault{addr}`。
4. **Trap/异常上报**  
   - 一旦发生上述任意错误，记录到 `cpu.trap_state`（类型、`badaddr`、`pc`）。  
   - 同时把 `halt=True`，让上层驱动（或测试）停机并读取 trap 信息。

## 6. 与 assassyn 的集成

1. **接口形式**：实现一个 `NaiveCpu` 类，按照 assassyn 习惯提供 `step()`（执行 1 条指令）与 `run(max_steps)`（循环调用 `step`，直到 `halt` 或次数耗尽）。
2. **内存/总线**：依赖 assassyn 自带的 `Memory`/`BusDevice`。CPU 只和统一的内存端口交互，其余设备（ROM、SRAM、外设）都通过总线注册。
3. **程序装载**：提供辅助方法 `load_program(binary, base_addr)`，把裸 bin/ELF 片段写入内存，并把 `pc` 初始化到入口地址。
4. **调试能力**：在 `step()` 内部支持可选 `trace` 标志，打印 `pc`、原始指令、关键寄存器，方便调试和单步验证。

## 7. 验证路径

整体测试框架沿用 Minor CPU 的系统流程：一次构建多次运行 → 为每个 case 准备统一的 InitFile → 运行软仿真（可选再跑 Verilog） → 用脚本检查 `raw.log` 判定 PASS/FAIL。所有层级的测试都复用这套流程，只是 workload 的内容不同。

1. **单元/微型测试**  
   - Workload 只包含极小的 hand-written 程序（几条指令），针对单条 Stage 0 指令验证读写、分支和异常。  
   - 依旧通过 InitFile 把程序写入 SRAM，运行仿真器并用检查脚本比对寄存器或内存输出。
2. **集成测试**  
   - Workload 换成覆盖取指/跳转/访存交互的 ELF 或指令流，确保 CPU、内存、总线以及 Driver 的整体连接正确。  
   - 依赖同样的 init/运行/检查步骤，只是检查脚本会验证更长的 trace 或关键寄存器。
3. **基准程序**  
   - 使用 README 列出的 benchmark 作为 workload，把编译产物写入 InitFile 后跑完整程序。  
   - 检查脚本负责解析 `raw.log` 或内存输出，确认 benchmark 结果正确。

系统流程细节（所有层级共用）：

1. **一次构建，多次运行**：调用类似 `build_cpu()` 的流程用 assassyn 实例化 CPU/总线/内存（可选导出 Verilog），所有 workload 共用这一套仿真器产物。  
2. **准备 InitFile**：对每个 case 把编译好的 ELF/数据复制到 `.workspace/`（或自定义目录），生成 `workload.init/.text/.data` 以及 `workload.config`，供 Driver 初始化内存与寄存器。  
3. **运行与校验**：运行软件仿真器（可选再跑 Verilog），输出写到 `raw.log`，随后执行 workload 附带脚本（`workload.sh` 或 `find_pass.sh`）解析日志并返回 PASS/FAIL。  
4. **调试模式**：若需要定位问题，就把两次仿真日志分别保存为 `<case>.log` 与 `<case>.verilog.log`。

## 8. 后续演进

- 在 naive CPU 验证通过后，再扩展至 5 级流水。

该文档将作为 naive CPU 实现与审核的依据，实际代码中应保持与此一致，并在实现完成后更新此文件记录差异。

RISC-V (RV32I) 乱序执行处理器设计文档

# 1. 架构概览 (Architecture Overview)

指令集架构 (ISA): RV32I (Base Integer Instruction Set)

微架构核心: 托马斯洛算法 (Tomasulo's Algorithm) + 重排序缓冲区 (ROB)

流水线深度: 逻辑上分为 5 个大阶段 (Fetch -> Decode/Queue -> Issue -> Execute -> Commit)

乱序策略: 执行乱序 (Out-of-Order Execution)，提交顺序 (In-Order Commit)

分支策略: 无预测 (No Prediction) / 遇分支即阻塞 (Stall-and-Wait)

访存策略: 强保序 (Strong Ordering) —— Load 必须等待所有未提交 Store 完成

写回总线: 单条 CDB (Single Common Data Bus) + 仲裁器 (Arbiter)

# 2. 流水线阶段详细设计 (Pipeline Stages)

### Stage 1: 取指 (Fetch)

功能: 从指令内存 (I-Mem) 读取指令。

作为 Downstream，每次需要接受从 Issue 阶段传来的 stall_fetch 信号，停止信号，以及 alu 发来的分支跳转信号。

逻辑：存在一个 we_reg 寄存器，表示是否读，每个周期如果接收到停止，那么就设置为 0，如果接收到跳转，那么就设置为 1，否则保持不变。

优先级：stall 优先，因为如果是 stall，那么这个指令并没有真正被执行，那么 pc 还是应该更新。

取的地址：如果接收到 stall 信号，那么就取 issue 传入的 pc 值，如果接收到跳转信号，那么就取 alu 传入的 target_pc，否则取 pc_reg。

更新 pc：如果 we_reg 为 1，则 pc_reg 更新为下一个地址 (pc_reg + 4)，否则保持不变。


### Stage 2: 译码与发射 (Issue)

功能: 组合逻辑译码，并在同周期写入指令队列。

逻辑:

如果是分支，那么要给下游传递 停止信号，停止取指。

如果是访存指令，那么进入 LSQ，否则进入 RS。

首先要从 ROB 取信号，如果 ROB 满了，那么需要传递 stall。如果 LSQ 或者 RS 满了，那么也需要传递 stall。

否则的话，读取 RAT，进行重命名。

核心逻辑：

RAT 查表 (Renaming):

读取源操作数 rs1, rs2。

如果 RAT 中对应条目指向 ROB 且 Ready=0，则获取 ROB ID 作为 Tag。

如果 RAT 指向 ARF 或 Ready=1，则直接获取 Value。

分配 (Allocate):

分配一个 ROB 条目 (Tail)。

分配一个 RS 槽位 (Busy=0) 或 LSQ 槽位。

更新 RAT: 将目标寄存器 rd 映射到当前的 ROB Tail ID。

### Stage 3: 执行 (Execute)

组件:

RS (Reservation Stations): 用于 ALU 指令。

LSQ (Load/Store Queue): 用于 Memory 指令。

Arbiter (仲裁器): 管理单 CDB 冲突。

逻辑:

RS/LSQ 需要一个 downstream，每个 RS/LSQ 从 CDB 中接受广播的数据，更新自己的操作数状态。

如果 valid，发送给对应的 ALU/LSU 执行单元。

执行单元执行完之后，需要把数据发给 Arbiter，接下来 Arbiter 发送 CBD 的信号，并且将数据给 ROB。

LSU 的细节：如果是 Store，计算地址之后直接可以发 CBD，更新入 ROB，如果是 Load，必须要等待所有未提交 Store 完成之后，才能发 CBD，否则保持 Busy 状态。

这些 ALU/LSU 是 Module，每次 RS/LSQ，如果数据合法，就会发给对应的 Module 执行。

### Stage 4: 提交 (Commit)

功能: 更新架构状态，处理 Store 写内存。

逻辑:

检查 ROB Head。

如果 Ready == 1:

Reg Write: 将 Value 写入物理寄存器堆 (ARF)。

Store Commit: 如果是 Store 指令，向 Data Memory 发起写操作。

Retire: Head <= Head + 1，释放 ROB 条目。

Store Counter Update: 如果是 Store，全局 Store 计数器 -1。

3. 关键模块与数据结构

3.1. 统一 Tag 定义

Tag: 使用 ROB ID (例如 4 bits，支持 16 条指令在飞)。

全系统统一：RAT 指向 ROB ID，RS 等待 ROB ID，CDB 广播 ROB ID。

3.2. 寄存器状态表 (RAT)

深度: 32 (对应 x0-x31)。

内容: { Valid, ROB_ID }。

注意: x0 永远硬连线为 0，不分配 ROB。

3.3. 保留站 (RS) - 针对 ALU

结构: 数组 (Station Pool)，例如 4-8 个槽位。

字段:

Busy: 1 bit

Op: ALU 操作码

Vj, Vk: 32 bits (操作数值)

Qj, Qk: Tag (ROB ID)

Qj_valid, Qk_valid: 1 bit (数据是否有效)

Dest_Tag: Tag (本指令的 ROB ID)

3.4. 访存队列 (LSQ) - 针对 Load/Store

结构: 数组 (Station Pool)，不做 FIFO，纯乱序池。

字段: 类似 RS，但增加 Addr (地址), Store_Data (存入的数据)。

Store 处理:

Issue 进 LSQ -> 算地址 -> 写 ROB -> LSQ 释放。

不写内存，不广播 CDB。

Load 处理 (保守策略):

全局计数器 inflight_store_count。

唤醒条件: (Operands_Ready) && (inflight_store_count == 0)。

执行 -> 申请 CDB -> 广播 -> 释放。

3.5. 仲裁器 (Arbiter)

输入: alu1_req, alu2_req, lsu_req。

输出: alu1_grant, alu2_grant, lsu_grant, mux_sel。

优先级: LSU > ALU1 > ALU2 (Load 优先，防止阻塞后级依赖)。

3.6. 重排序缓冲区 (ROB)

结构: 循环队列 (Circular Buffer)，深度 e.g. 16。

字段:

Dest_Reg: 5 bits (写回目标寄存器)

Value: 32 bits (计算结果，来自 CDB)

Ready: 1 bit (是否完成)

Is_Store: 1 bit (类型标记)

Store_Addr: 32 bits (Store 专用)

写端口:

Port 1 (Issue): 写入元数据 (Dest_Reg, Type...)。

Port 2 (CDB): 写入结果 (Value, Ready=1)。

4. 关键控制流与防冲突设计

4.1. 分支控制 (Stall-and-Wait)

Issue 阶段: 译码发现是 Branch/JAL/JALR。

动作:

拉高 frontend_stall 信号，冻结 PC 和 Fetch。

# 5. 设计改进点（发射一次的握手）

- RS / LSQ 发射到 ALU/LSU 需要“一次性”握手：给每个 entry 增加“已发射”标志，发射过一次后不再重复 `async_called`，等待 CDB/LSU 返回或 busy 清空。否则组合逻辑每周期都会 fire 同一条指令。
- CDB 单通道：ALU/LSU 输出若竞争 CDB，需要在本地寄存/队列里缓冲未授予的结果，避免依赖“重复 fire”抢占仲裁。
- 分支重定向：`start_signal/target_pc` 需要打拍或用 pending 寄存器，确保是单周期脉冲，避免组合电平导致重复重定向。

# 6. assassyn 使用时的坑点（组合 != 一次性）

- `with Condition(...)` 只是组合多路选择，不会“执行一次”。需要单次行为时必须用 Reg/Wire 打拍或 pending 标志。
- 对非 Option 调用 `.optional()` / `.valid()` 会把信号当常量折叠，容易导致输入被硬编码。只在 Option 类型上用这些方法。
- 多个 `with Condition` 对同一信号赋值会生成组合 mux，若期望时序行为要用寄存器明确时序更新。

该分支指令正常发射进 RS。

ALU 执行: 算出 Taken 和 Target Addr。

恢复:

ALU 直接发信号修改 PC。

Issue 撤销 frontend_stall。

流水线恢复取指。

4.2. 访存防冲突 (Global Store Counter)

计数器: reg [4:0] stores_in_flight。

增加: Issue 发射一条 Store 指令时 +1。

减少: ROB 提交 (Commit) 一条 Store 指令时 -1。

Load 阻塞: LSQ 中的 Load 指令只有在 stores_in_flight == 0 时才允许请求执行。

4.3. CDB 冲突处理

请求: ALU/LSU 算完后，拉高 req，且保持 Busy=1。

等待: 如果 Grant=0，保持输出数据不变，保持 req=1，等待下一拍。

释放: 只有当 req=1 且 Grant=1 的上升沿，才将 Busy 置 0。

5. 开发步骤建议 (Implementation Roadmap)

基础定义: 定义 cdb_packet_t，rob_id_t 等接口。

Mock 环境: 写一个简单的单周期 RAM 模拟内存。

阶段一 (前端): 实现 Fetch -> Queue -> Decode -> Issue 的空逻辑（只做计数，不发 RS）。
验证分支 Stall 逻辑。

阶段二 (ALU通路): 实现 RS, Arbiter, CDB, ALU。验证 ADD, SUB 指令的乱序发射、执行、CDB 广播。

阶段三 (ROB与提交): 加入 ROB 和 RAT。验证指令能正确 Commit 到模拟的 Register File。

阶段四 (访存): 加入 LSQ 和 Store 计数器。验证 SW 随后 LW 的阻塞逻辑。

集成测试: 运行简单的汇编程序（如斐波那契数列计算）。

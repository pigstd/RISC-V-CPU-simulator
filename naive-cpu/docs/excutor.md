先去通读 main.py / instruction.py / decoder.py，executor 的基本设计如下：

- 输入：decoder_logic 打包出的 `deocder_signals`（rs1/rs2/rd/imm/alu_type/mem_read/mem_write/is_branch 等），以及 PC 寄存器、通用寄存器堆（RegArray[32]，x0 固定为 0），**dcache**。
- 操作数获取：`rs1_used/rs2_used` 决定是否从寄存器堆取值，否则用 0。后续可以补充 jalr 等用 rs1 做基址的特殊分支。
- ALU：`alu_type` 是 one-hot (1<<ALU_* )；针对 ADD/SUB/AND/OR/XOR/SLL/SRL/SRA/SLT/SLTU/比较等，用 select/mux 生成 `alu_res`。I/R 指令共用。
- 写回意图：EX 只生成 “写回意图” 而不直接改寄存器；`rd_used` 为真且 rd!=0 时输出 `rd` 和 `rd_data_ex`（jal/jalr 用 link，其他用 `alu_res`）。
- PC 更新：默认 `pc_next = pc_addr + 4`；分支/跳转依据条件或 jal/jalr 目标更新，并做对齐检查。
- **存储器集成**：将 `dcache` 传入 Executor，在 EX 阶段根据 `mem_read/mem_write` 直接对 `dcache.build` 进行访问（dout 异步），这样在下一拍 MemoryAccess 阶段可以拿到 `dcache.dout[0]` 作为 load 数据；未对齐或非法访存可在此记录/抛异常。
- **WB 模块**：新增单独 WB 阶段，由 MA 汇总写回信息：若 `mem_read` 为真则使用 `dcache.dout`，否则用 EX 提供的 `rd_data_ex`。WB 统一执行 `regs[rd] <= wb_data`（rd!=0/rd_en gating），避免 EX/MA 各自写回造成混乱，方便后续处理异常/冒险。

连接关系：main 侧把 `dcache` 也传给 executor，executor 完成访存触发和写回意图输出；MemoryAccess 在下一拍消费 `dcache.dout` 及 EX 结果，最终交给 WB 模块统一写寄存器。

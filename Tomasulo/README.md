# Tomasulo CPU Simulator Notes

工程基于 assassyn 语言实现 Tomasulo 风格的简易 CPU 模拟器。以下是近期调试中需要牢记的要点，方便后续维护和排错。

## 关键约定
- **数据内存基址**：LSU/dcache 访问必须用 `addr - data_base` 再按字寻址；`build_CPU` 支持 CLI `--data-base` 透传。
- **重命名表位宽**：`reg_pending` 存 `rob_idx + 1`（0 表示无依赖），位宽需为 `ROB_IDX_WIDTH + 1`，否则尾部索引会溢出为 0 导致依赖丢失。
- **U-type 处理**：decoder 为 LUI/AUIPC 输出 ALU_ADD；Issuer 设置 `op1=0`(LUI)/`op1=pc`(AUIPC)，`op2=imm`，RS 保存 `is_lui/is_auipc` 以便 ALU。
- **Record 与 RegArray**：寄存器数组只能存 Bits，读出时用 `Record.view(...)` 还原，`select` 组合逻辑要加括号避免优先级陷阱。
- **分支/JAL/JALR 控制**：ALU 的分支结果通过 CDB `start_signal/target_pc` 驱动取指停/启；FetcherImpl 仅在 start 时跳转。
- **Store 提交流程**：ROB 持有 `store_addr/store_data`，commit 负责驱动外部存储；LSQ load 需等 qj/qk 就绪且 ROB 无未提交 store 才能发射。

## 测试提示
- Tomasulo 专用回归脚本：`python Tomasulo/run_tests.py [--list | <cases>]`（只跑 Python 模拟器）。
- 单元测试覆盖：分支/jal/jalr、U-type、hazard、存储等，可用 `pytest unit_tests -k <pattern>` 快速定位问题。

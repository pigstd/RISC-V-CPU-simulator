from assassyn.frontend import *
from .lsu import *
from .alu import *
from .ROB import *
from .RS import RS_ENTRY_NUM, RS_NUM_WIDTH, RS_MAX

# 统一的广播信号格式（用于所有执行单元）
CBD_signal = Record(
    ROB_idx = UInt(ROB_IDX_WIDTH),    # 指令在 ROB 中的索引
    rd_data = UInt(32),   # 写回数据
    valid = Bits(1),     # 数据有效标志
)

# 分支控制信号，用于传递给 FetchControl
BranchControl_signal = Record(
    # JALR 相关
    jalr_resolved = Bits(1),   # JALR 执行完成，可以恢复取指
    jalr_target_pc = UInt(32), # JALR 计算出的目标地址
    # 预测验证相关
    mispredicted = Bits(1),    # 预测错误，需要 flush
    correct_pc = UInt(32),     # 正确的 PC（用于 flush 后恢复）
)


class CDB_Arbitrator(Downstream):
    """
    无仲裁 CDB - 每个执行单元直接写 ROB
    
    优化后的架构：
    - 4 个 ALU 各自独立广播
    - 1 个 LSU 独立广播
    - 2 个乘法器独立广播（在 main.py 中处理）
    
    每个执行单元完成时直接写入 ROB 对应条目，无需仲裁。
    因为每条指令有唯一的 ROB 索引，同周期写不同索引不冲突。
    """
    def __init__(self):
        super().__init__()
        
    @downstream.combinational
    def build(self, LSU_CBD_req: Value, ALU_CBD_req: list[Value], rob: ROB, bht: BHT, metadata: Value):
        """
        返回:
        - cbd_signal: 兼容的广播信号（仅用于 Issue 阶段的旁路）
        - branch_ctrl: 分支控制信号
        - alu_broadcasts: 4 个 ALU 的广播信号 [(rob_idx, rd_data, valid), ...]
        - lsu_broadcast: LSU 的广播信号 (rob_idx, rd_data, valid)
        """
        metadata = metadata.optional(default=UInt(8)(0))
        log("NoArb CDB metadata={}", metadata)
        
        # ========== 处理 LSU 请求 ==========
        lsu_payload = LSU_CBD_req.value().optional(default=LSU_CBD_signal.bundle(
            ROB_idx = UInt(ROB_IDX_WIDTH)(0),
            rd_data = UInt(32)(0),
            valid = Bits(1)(0),
            is_load = Bits(1)(0),
            is_store = Bits(1)(0),
            store_addr = UInt(32)(0),
            store_data = UInt(32)(0),
        ).value())
        lsu_req = LSU_CBD_signal.view(lsu_payload)
        
        lsu_valid = lsu_req.valid
        lsu_rob_idx = lsu_req.ROB_idx
        lsu_rd_data = lsu_req.rd_data
        lsu_is_store = lsu_req.is_store
        lsu_store_addr = lsu_req.store_addr
        lsu_store_data = lsu_req.store_data
        
        # LSU 直接写 ROB
        with Condition(lsu_valid):
            rob._write_ready(lsu_rob_idx, Bits(1)(1))
            rob._write_value(lsu_rob_idx, lsu_rd_data)
            log("NoArb: LSU done, rob_idx={} rd_data=0x{:08x}", lsu_rob_idx, lsu_rd_data)
            # Store 记录地址和数据
            with Condition(lsu_is_store):
                rob.store_addr[lsu_rob_idx] <= lsu_store_addr
                rob.store_data[lsu_rob_idx] <= lsu_store_data
        
        # ========== 处理 ALU 请求 ==========
        alu_broadcasts = []
        
        # 用于分支处理的变量 - 使用 Assassyn 类型
        any_branch = Bits(1)(0)
        branch_is_jalr = Bits(1)(0)
        branch_is_B = Bits(1)(0)
        branch_taken = Bits(1)(0)
        branch_next_pc = UInt(32)(0)
        branch_rob_idx = UInt(ROB_IDX_WIDTH)(0)
        
        for i in range(RS_ENTRY_NUM):
            alu_payload = ALU_CBD_req[i].value().optional(default=ALU_CBD_signal.bundle(
                ROB_idx = UInt(ROB_IDX_WIDTH)(0),
                rd_data = UInt(32)(0),
                valid = Bits(1)(0),
                is_branch = Bits(1)(0),
                next_pc = UInt(32)(0),
                is_jalr = Bits(1)(0),
                is_jal = Bits(1)(0),
                is_B = Bits(1)(0),
                branch_taken = Bits(1)(0),
            ).value())
            alu_req = ALU_CBD_signal.view(alu_payload)
            
            alu_valid = alu_req.valid
            alu_rob_idx = alu_req.ROB_idx
            alu_rd_data = alu_req.rd_data
            
            # ALU 直接写 ROB
            with Condition(alu_valid):
                rob._write_ready(alu_rob_idx, Bits(1)(1))
                rob._write_value(alu_rob_idx, alu_rd_data)
                log("NoArb: ALU done, rob_idx={} rd_data=0x{:08x}", alu_rob_idx, alu_rd_data)
                # 分支指令：把执行结果写入 ROB，commit 时再判断 mispredicted
                with Condition(alu_req.is_branch):
                    rob._write_actual_taken(alu_rob_idx, alu_req.branch_taken)
                    rob._write_actual_next_pc(alu_rob_idx, alu_req.next_pc)
                    log("NoArb: Branch exec rob_idx={} actual_taken={} actual_next_pc=0x{:08x}",
                        alu_rob_idx, alu_req.branch_taken, alu_req.next_pc)
            
            # 收集广播信号
            alu_broadcasts.append((alu_rob_idx, alu_rd_data, alu_valid))
            
            # 收集分支信息（任意一个 ALU 可能产生分支）
            # 使用条件选择累积分支信息，而不是 with Condition 赋值
            is_this_branch = alu_valid & alu_req.is_branch
            any_branch = any_branch | is_this_branch
            branch_is_jalr = is_this_branch.select(alu_req.is_jalr, branch_is_jalr)
            branch_is_B = is_this_branch.select(alu_req.is_B, branch_is_B)
            branch_taken = is_this_branch.select(alu_req.branch_taken, branch_taken)
            branch_next_pc = is_this_branch.select(alu_req.next_pc, branch_next_pc)
            branch_rob_idx = is_this_branch.select(alu_rob_idx, branch_rob_idx)
        
        # LSU 广播信号
        lsu_broadcast = (lsu_rob_idx, lsu_rd_data, lsu_valid)
        
        # ========== 分支控制信号生成 ==========
        # 注意：mispredicted 的检测移到 commit 阶段，这里只处理 JALR 立即恢复取指
        branch_pc = rob.pc[branch_rob_idx]
        
        # JALR 完成信号（JALR 需要立即恢复取指，因为之前 stall 了）
        jalr_resolved = any_branch & branch_is_jalr
        jalr_target_pc = branch_next_pc
        
        # 更新 BHT（只有 B 类型条件分支执行完就更新）
        bht.update_if(branch_is_B & any_branch, branch_pc, branch_taken)
        
        log("CDB branch: any={} is_B={} is_jalr={} taken={} next_pc=0x{:08x}", 
            any_branch, branch_is_B, branch_is_jalr, branch_taken, branch_next_pc)
        
        # mispredicted 和 correct_pc 不再在这里生成，设为 0
        # commit 阶段会生成真正的 mispredicted 信号
        branch_ctrl = BranchControl_signal.bundle(
            jalr_resolved = jalr_resolved,
            jalr_target_pc = jalr_target_pc,
            mispredicted = Bits(1)(0),  # 移到 commit 阶段检测
            correct_pc = UInt(32)(0),   # 移到 commit 阶段提供
        )
        
        # 为了兼容性，构建一个合并的 CBD_signal（用于 Issue 旁路）
        any_valid = lsu_valid
        sel_rob_idx = lsu_rob_idx
        sel_rd_data = lsu_rd_data
        
        for (rob_idx, rd_data, valid) in alu_broadcasts:
            any_valid = any_valid | valid
            sel_rob_idx = valid.select(rob_idx, sel_rob_idx)
            sel_rd_data = valid.select(rd_data, sel_rd_data)
        
        cbd_signal = CBD_signal.bundle(
            ROB_idx = sel_rob_idx,
            rd_data = sel_rd_data,
            valid = any_valid,
        )
        
        return cbd_signal, branch_ctrl, alu_broadcasts, lsu_broadcast

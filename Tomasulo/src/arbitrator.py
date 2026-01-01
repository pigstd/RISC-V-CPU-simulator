from assassyn.frontend import *
from .lsu import *
from .alu import *
from .ROB import *
from .RS import RS_ENTRY_NUM, RS_NUM_WIDTH, RS_MAX

CBD_signal = Record(
    ROB_idx = UInt(4),    # 指令在 ROB 中的索引
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
    def __init__(self):
        super().__init__()
    @downstream.combinational
    def build(self, LSU_CBD_req: Value, ALU_CBD_req: list[Value], rob : ROB, bht: BHT, metadata : Value):
        lsu_cbd_reg = RegArray(Bits(LSU_CBD_signal.bits), 1, initializer=[0])
        alu_cbd_reg = [RegArray(Bits(ALU_CBD_signal.bits), 1, initializer=[0]) for _ in range(RS_ENTRY_NUM)]
        # metadata 仅用于驱动 downstream，每周期都会访问一次
        metadata = metadata.optional(default=Bits(8)(0))
        log("CDB arb metadata={}", metadata)
        # 为输入 request 增加默认值，避免第一次未产生请求时访问无效字段
        # 给上下游提供安全的默认值（当 LSU/ALU 尚未产生输出时不会访问无效 Option）
        lsu_payload = LSU_CBD_req.value().optional(default=LSU_CBD_signal.bundle(
            ROB_idx = UInt(4)(0),
            rd_data = UInt(32)(0),
            valid = Bits(1)(0),
            is_load = Bits(1)(0),
            is_store = Bits(1)(0),
            store_addr = UInt(32)(0),
            store_data = UInt(32)(0),
        ).value())
        lsu_req = LSU_CBD_signal.view(lsu_payload)

        alu_req = []
        for i in range(RS_ENTRY_NUM):
            alu_payload = ALU_CBD_req[i].value().optional(default=ALU_CBD_signal.bundle(
                ROB_idx = UInt(4)(0),
                rd_data = UInt(32)(0),
                valid = Bits(1)(0),
                is_branch = Bits(1)(0),
                next_pc = UInt(32)(0),
                is_jalr = Bits(1)(0),
                is_jal = Bits(1)(0),
                is_B = Bits(1)(0),
                branch_taken = Bits(1)(0),
            ).value())
            alu_req.append(ALU_CBD_signal.view(alu_payload))
        # alu_payload = ALU_CBD_req.value().optional(default=ALU_CBD_signal.bundle(
        #     ROB_idx = UInt(4)(0),
        #     rd_data = UInt(32)(0),
        #     valid = Bits(1)(0),
        #     is_branch = Bits(1)(0),
        #     next_pc = UInt(32)(0),
        # ).value())
        # alu_req = ALU_CBD_signal.view(alu_payload)
        # 如果 lsu_req 这个周期没有，寄存器里面可能有
        # Record 不能 select，手动 bundle 然后每个元素都 select
        # lsu_cbd = lsu_req.valid.select(lsu_req, lsu_cbd_reg[0])
        lsu_cbd_reg_view = LSU_CBD_signal.view(lsu_cbd_reg[0])
        alu_cbd_reg_view = [ALU_CBD_signal.view(reg[0]) for reg in alu_cbd_reg]
        lsu_cbd = LSU_CBD_signal.bundle(
            ROB_idx = lsu_req.valid.select(lsu_req.ROB_idx, lsu_cbd_reg_view.ROB_idx),
            rd_data = lsu_req.valid.select(lsu_req.rd_data, lsu_cbd_reg_view.rd_data),
            valid = lsu_req.valid.select(lsu_req.valid, lsu_cbd_reg_view.valid),
            is_load = lsu_req.valid.select(lsu_req.is_load, lsu_cbd_reg_view.is_load),
            is_store = lsu_req.valid.select(lsu_req.is_store, lsu_cbd_reg_view.is_store),
            store_addr = lsu_req.valid.select(lsu_req.store_addr, lsu_cbd_reg_view.store_addr),
            store_data = lsu_req.valid.select(lsu_req.store_data, lsu_cbd_reg_view.store_data),
        )
        # alu_cbd = alu_req.valid.select(alu_req, alu_cbd_reg[0])
        alu_cbd = [ALU_CBD_signal.bundle(
            ROB_idx = alu_req[i].valid.select(alu_req[i].ROB_idx, alu_cbd_reg_view[i].ROB_idx),
            rd_data = alu_req[i].valid.select(alu_req[i].rd_data, alu_cbd_reg_view[i].rd_data),
            valid = alu_req[i].valid.select(alu_req[i].valid, alu_cbd_reg_view[i].valid),
            is_branch = alu_req[i].valid.select(alu_req[i].is_branch, alu_cbd_reg_view[i].is_branch),
            next_pc = alu_req[i].valid.select(alu_req[i].next_pc, alu_cbd_reg_view[i].next_pc),
            is_jalr = alu_req[i].valid.select(alu_req[i].is_jalr, alu_cbd_reg_view[i].is_jalr),
            is_jal = alu_req[i].valid.select(alu_req[i].is_jal, alu_cbd_reg_view[i].is_jal),
            is_B = alu_req[i].valid.select(alu_req[i].is_B, alu_cbd_reg_view[i].is_B),
            branch_taken = alu_req[i].valid.select(alu_req[i].branch_taken, alu_cbd_reg_view[i].branch_taken),
        ) for i in range(RS_ENTRY_NUM)]
        # 直接使用包好的默认值，不再逐字段 optional
        lsu_valid = lsu_cbd.valid
        lsu_rob_idx = lsu_cbd.ROB_idx
        lsu_rd_data = lsu_cbd.rd_data
        lsu_is_store = lsu_cbd.is_store
        lsu_store_addr = lsu_cbd.store_addr
        lsu_store_data = lsu_cbd.store_data

        alu_valid = [alu_cbd[i].valid for i in range(RS_ENTRY_NUM)]
        alu_rob_idx = [alu_cbd[i].ROB_idx for i in range(RS_ENTRY_NUM)]
        alu_rd_data = [alu_cbd[i].rd_data for i in range(RS_ENTRY_NUM)]
        alu_is_branch = [alu_cbd[i].is_branch for i in range(RS_ENTRY_NUM)]
        alu_next_pc = [alu_cbd[i].next_pc for i in range(RS_ENTRY_NUM)]
        alu_is_jalr = [alu_cbd[i].is_jalr for i in range(RS_ENTRY_NUM)]
        alu_is_jal = [alu_cbd[i].is_jal for i in range(RS_ENTRY_NUM)]
        alu_is_B = [alu_cbd[i].is_B for i in range(RS_ENTRY_NUM)]
        alu_branch_taken = [alu_cbd[i].branch_taken for i in range(RS_ENTRY_NUM)]

        valid = lsu_valid
        for i in range(RS_ENTRY_NUM):
            valid = valid | alu_valid[i]
        # 优先级：LSU > ALU0 > ALU1 > ...
        select_CDB = Bits(RS_NUM_WIDTH)(RS_MAX) # 无效值
        select_CDB = lsu_valid.select(Bits(RS_NUM_WIDTH)(0), select_CDB)
        for i in range(RS_ENTRY_NUM):
            # 如果还没有被选择，则选择当前的 ALU
            select_CDB = (alu_valid[i] & (select_CDB == Bits(RS_NUM_WIDTH)(RS_MAX))).select(Bits(RS_NUM_WIDTH)(i+1), select_CDB)

        ROB_idx = lsu_valid.select(lsu_rob_idx, UInt(4)(0))
        for i in range(RS_ENTRY_NUM):
            ROB_idx = (alu_valid[i] & (select_CDB == Bits(RS_NUM_WIDTH)(i+1))).select(alu_rob_idx[i], ROB_idx)
        rd_data = lsu_valid.select(lsu_rd_data, UInt(32)(0))
        for i in range(RS_ENTRY_NUM):
            rd_data = (alu_valid[i] & (select_CDB == Bits(RS_NUM_WIDTH)(i+1))).select(alu_rd_data[i], rd_data)
        log("CDB arb: LSU_valid={} select_CDB={} sel_rob_idx={} rd_data=0x{:08x}", lsu_valid, select_CDB, ROB_idx, rd_data)
        # 将选择的结果修改进 ROB
        with Condition(valid):
            rob.ready[ROB_idx] <= Bits(1)(1)
            rob.value[ROB_idx] <= rd_data
            # 若为 store，记录地址与数据（is_store 在 issue 时写入）
            with Condition(lsu_valid & lsu_is_store):
                rob.store_addr[ROB_idx] <= lsu_store_addr
                rob.store_data[ROB_idx] <= lsu_store_data
        
        # 如果这个周期有 req 但是没有被广播出去，则存入寄存器，等待下周期广播
        with Condition(lsu_req.valid & (select_CDB != Bits(RS_NUM_WIDTH)(0))):
            lsu_cbd_reg[0] <= lsu_req.value()
        for i in range(RS_ENTRY_NUM):
            with Condition(alu_req[i].valid & (select_CDB != Bits(RS_NUM_WIDTH)(i + 1))):
                alu_cbd_reg[i][0] <= alu_req[i].value()
        # 如果这个周期是广播的寄存器的 cbd，那么清空寄存器
        with Condition(lsu_valid & (~lsu_req.valid) & (select_CDB == Bits(RS_NUM_WIDTH)(0))):
            lsu_cbd_reg[0] <= LSU_CBD_signal.bundle(
                ROB_idx = UInt(4)(0),
                rd_data = UInt(32)(0),
                valid = Bits(1)(0),
                is_load = Bits(1)(0),
                is_store = Bits(1)(0),
                store_addr = UInt(32)(0),
                store_data = UInt(32)(0),
            ).value()
        for i in range(RS_ENTRY_NUM):
            with Condition(alu_valid[i] & (~alu_req[i].valid) & (select_CDB == Bits(RS_NUM_WIDTH)(i + 1))):
                alu_cbd_reg[i][0] <= ALU_CBD_signal.bundle(
                    ROB_idx = UInt(4)(0),
                    rd_data = UInt(32)(0),
                    valid = Bits(1)(0),
                    is_branch = Bits(1)(0),
                    next_pc = UInt(32)(0),
                    is_jalr = Bits(1)(0),
                    is_jal = Bits(1)(0),
                    is_B = Bits(1)(0),
                    branch_taken = Bits(1)(0),
                ).value()
        
        # ========== 分支控制信号生成 ==========
        # 提取被选中的分支信息
        sel_is_branch = Bits(1)(0)
        sel_is_jalr = Bits(1)(0)
        sel_is_jal = Bits(1)(0)
        sel_is_B = Bits(1)(0)
        sel_branch_taken = Bits(1)(0)
        sel_next_pc = UInt(32)(0)
        sel_rob_idx_for_branch = UInt(4)(0)
        
        for i in range(RS_ENTRY_NUM):
            is_selected = alu_valid[i] & (select_CDB == Bits(RS_NUM_WIDTH)(i+1))
            sel_is_branch = is_selected.select(alu_is_branch[i], sel_is_branch)
            sel_is_jalr = is_selected.select(alu_is_jalr[i], sel_is_jalr)
            sel_is_jal = is_selected.select(alu_is_jal[i], sel_is_jal)
            sel_is_B = is_selected.select(alu_is_B[i], sel_is_B)
            sel_branch_taken = is_selected.select(alu_branch_taken[i], sel_branch_taken)
            sel_next_pc = is_selected.select(alu_next_pc[i], sel_next_pc)
            sel_rob_idx_for_branch = is_selected.select(alu_rob_idx[i], sel_rob_idx_for_branch)
        
        # 分支验证：检查 ROB 中记录的预测是否正确
        # 预测信息存储在 ROB 中：predicted_taken, predicted_pc
        predicted_taken = rob.predicted_taken[sel_rob_idx_for_branch]
        predicted_pc = rob.predicted_pc[sel_rob_idx_for_branch]
        branch_pc = rob.pc[sel_rob_idx_for_branch]  # 分支指令的 PC，用于更新 BHT
        
        # 对于 B 指令：
        #   - 预测 taken 但实际 not taken → 预测错误
        #   - 预测 not taken 但实际 taken → 预测错误（新增！）
        # 对于 JAL：
        #   - 总是预测跳转，不会出错
        # 对于 JALR：
        #   - 不预测，没有 misprediction，只需要传递 jalr_resolved
        
        # B 指令预测错误：预测与实际不一致
        b_mispredicted_taken = sel_is_B & predicted_taken & (~sel_branch_taken)  # 预测跳转但没跳
        b_mispredicted_not_taken = sel_is_B & (~predicted_taken) & sel_branch_taken  # 预测不跳转但跳了
        b_mispredicted = b_mispredicted_taken | b_mispredicted_not_taken
        
        # JALR 完成信号
        jalr_resolved = sel_is_branch & sel_is_jalr
        jalr_target_pc = sel_next_pc
        
        # 预测错误信号
        mispredicted = sel_is_branch & b_mispredicted
        # 正确的 PC：ALU 计算的 next_pc
        correct_pc = sel_next_pc
        
        # ========== 更新 BHT ==========
        # 只有 B 类型条件分支需要更新 BHT
        bht.update_if(sel_is_B, branch_pc, sel_branch_taken)
        
        log("CDB branch: is_branch={} is_B={} branch_taken={} predicted={} mispred={} pc=0x{:08x}", 
            sel_is_branch, sel_is_B, sel_branch_taken, predicted_taken, mispredicted, branch_pc)
        
        # 返回：CBD_signal 和 分支控制信号
        return CBD_signal.bundle(
            ROB_idx = ROB_idx,
            rd_data = rd_data,
            valid = valid,
        ), BranchControl_signal.bundle(
            jalr_resolved = jalr_resolved,
            jalr_target_pc = jalr_target_pc,
            mispredicted = mispredicted,
            correct_pc = correct_pc,
        )

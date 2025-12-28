from assassyn.frontend import *
from .lsu import *
from .alu import *
from .ROB import *

CBD_signal = Record(
    ROB_idx = UInt(4),    # 指令在 ROB 中的索引
    rd_data = UInt(32),   # 写回数据
    valid = Bits(1),     # 数据有效标志
)

class CDB_Arbitrator(Downstream):
    def __init__(self):
        super().__init__()
    @downstream.combinational
    def build(self, LSU_CBD_req: Value, ALU_CBD_req: Value, rob : ROB, metadata : Value):
        lsu_cbd_reg = RegArray(Bits(LSU_CBD_signal.bits), 1, initializer=[0])
        alu_cbd_reg = RegArray(Bits(ALU_CBD_signal.bits), 1, initializer=[0])
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

        alu_payload = ALU_CBD_req.value().optional(default=ALU_CBD_signal.bundle(
            ROB_idx = UInt(4)(0),
            rd_data = UInt(32)(0),
            valid = Bits(1)(0),
            is_branch = Bits(1)(0),
            next_pc = UInt(32)(0),
        ).value())
        alu_req = ALU_CBD_signal.view(alu_payload)
        # 如果 lsu_req 这个周期没有，寄存器里面可能有
        # Record 不能 select，手动 bundle 然后每个元素都 select
        # lsu_cbd = lsu_req.valid.select(lsu_req, lsu_cbd_reg[0])
        lsu_cbd_reg_view = LSU_CBD_signal.view(lsu_cbd_reg[0])
        alu_cbd_reg_view = ALU_CBD_signal.view(alu_cbd_reg[0])
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
        alu_cbd = ALU_CBD_signal.bundle(
            ROB_idx = alu_req.valid.select(alu_req.ROB_idx, alu_cbd_reg_view.ROB_idx),
            rd_data = alu_req.valid.select(alu_req.rd_data, alu_cbd_reg_view.rd_data),
            valid = alu_req.valid.select(alu_req.valid, alu_cbd_reg_view.valid),
            is_branch = alu_req.valid.select(alu_req.is_branch, alu_cbd_reg_view.is_branch),
            next_pc = alu_req.valid.select(alu_req.next_pc, alu_cbd_reg_view.next_pc),
        )
        # 直接使用包好的默认值，不再逐字段 optional
        lsu_valid = lsu_cbd.valid
        lsu_rob_idx = lsu_cbd.ROB_idx
        lsu_rd_data = lsu_cbd.rd_data
        lsu_is_store = lsu_cbd.is_store
        lsu_store_addr = lsu_cbd.store_addr
        lsu_store_data = lsu_cbd.store_data

        alu_valid = alu_cbd.valid
        alu_rob_idx = alu_cbd.ROB_idx
        alu_rd_data = alu_cbd.rd_data
        alu_is_branch = alu_cbd.is_branch
        alu_next_pc = alu_cbd.next_pc

        valid = lsu_valid | alu_valid
        select_CDB = lsu_valid.select(Bits(2)(0),
                    alu_valid.select(Bits(2)(1), Bits(2)(2)))
        ROB_idx = lsu_valid.select(lsu_rob_idx, alu_rob_idx)
        rd_data = lsu_valid.select(lsu_rd_data, alu_rd_data)
        log("CDB arb: LSU_valid={} ALU_valid={} sel_rob_idx={} rd_data=0x{:08x}", lsu_valid, alu_valid, ROB_idx, rd_data)
        # 将选择的结果修改进 ROB
        with Condition(valid):
            rob.ready[ROB_idx] <= Bits(1)(1)
            rob.value[ROB_idx] <= rd_data
            # 若为 store，记录地址与数据（is_store 在 issue 时写入）
            with Condition(lsu_valid & lsu_is_store):
                rob.store_addr[ROB_idx] <= lsu_store_addr
                rob.store_data[ROB_idx] <= lsu_store_data
        
        # 如果这个周期有 req 但是没有被广播出去，则存入寄存器，等待下周期广播
        with Condition(lsu_req.valid & (select_CDB != Bits(2)(0))):
            lsu_cbd_reg[0] <= lsu_req.value()
        with Condition(alu_req.valid & (select_CDB != Bits(2)(1))):
            alu_cbd_reg[0] <= alu_req.value()
        # 如果这个周期是广播的寄存器的 cbd，那么清空寄存器
        with Condition(lsu_valid & (~lsu_req.valid) & (select_CDB == Bits(2)(0))):
            lsu_cbd_reg[0] <= LSU_CBD_signal.bundle(
                ROB_idx = UInt(4)(0),
                rd_data = UInt(32)(0),
                valid = Bits(1)(0),
                is_load = Bits(1)(0),
                is_store = Bits(1)(0),
                store_addr = UInt(32)(0),
                store_data = UInt(32)(0),
            ).value()
        with Condition(alu_valid & (~alu_req.valid) & (select_CDB == Bits(2)(1))):
            alu_cbd_reg[0] <= ALU_CBD_signal.bundle(
                ROB_idx = UInt(4)(0),
                rd_data = UInt(32)(0),
                valid = Bits(1)(0),
                is_branch = Bits(1)(0),
                next_pc = UInt(32)(0),
            ).value()
        
        # 返回：CBD_signal, is_branch, next_PC
        start_signal = lsu_valid.select(Bits(1)(0), alu_valid & alu_is_branch)
        target_pc = alu_valid.select(alu_next_pc, UInt(32)(0))
        return CBD_signal.bundle(
            ROB_idx = ROB_idx,
            rd_data = rd_data,
            valid = valid,
        ), start_signal, target_pc

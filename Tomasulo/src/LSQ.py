from assassyn.frontend import *
from .alu import ALU_CBD_signal
from .lsu import *
from .ROB import *
from .arbitrator import CBD_signal as CDBSignal

# 简化版 LSQ：单槽，依赖 CDB 信号来填充地址/数据


class LSQEntry:
    def __init__(self):
        self.busy = RegArray(Bits(1), 1, initializer=[0])
        self.is_load = RegArray(Bits(1), 1, initializer=[0])
        self.is_store = RegArray(Bits(1), 1, initializer=[0])
        self.rob_idx = RegArray(Bits(ROB_IDX_WIDTH), 1, initializer=[0])
        self.rd = RegArray(Bits(5), 1, initializer=[0])          # load 写回目标
        self.data = RegArray(UInt(32), 1, initializer=[0])       # store 数据
        # 依赖/就绪标志
        self.rd = RegArray(Bits(5), 1, initializer=[0])          # load 写回目标
        self.qj_valid = RegArray(Bits(1), 1, initializer=[0])
        self.qk_valid = RegArray(Bits(1), 1, initializer=[0])    # rs2 就绪标志
        self.qj = RegArray(Bits(REG_PENDING_WIDTH), 1, initializer=[0])          # rs1 对应的 ROB 条目
        self.qk = RegArray(Bits(REG_PENDING_WIDTH), 1, initializer=[0])          # rs2 对应的 ROB
        # 源值与立即数
        self.vj = RegArray(UInt(32), 1, initializer=[0])
        self.vk = RegArray(UInt(32), 1, initializer=[0])
        self.rs2_id = RegArray(Bits(5), 1, initializer=[0])      # rs2 编号，用于回退从寄存器读
        self.imm = RegArray(UInt(32), 1, initializer=[0])
        # 是否发射给 LSU
        self.fired = RegArray(Bits(1), 1, initializer=[0])


class LSQ_downstream(Downstream):
    """
    接收所有广播信号更新 LSQ entry，并在 commit/flush 后清空。
    """
    def __init__(self):
        super().__init__()

    @downstream.combinational
    def build(self,
              lsq: LSQEntry,
              all_broadcasts: list,  # 所有广播信号 [(rob_idx, rd_data, valid), ...]
              lsu : LSU,
              rob : ROB,
              regs: RegArray,
              issue_stall: Value,
              metadata: Value):
        issue_stall = issue_stall.optional(default=Bits(1)(0))
        metadata = metadata.optional(default=UInt(8)(0))
        _ = metadata == metadata
        log("LSQ downstream metadata={} busy={} qj_v={} qk_v={} rob_idx={}", metadata, lsq.busy[0], lsq.qj_valid[0], lsq.qk_valid[0], lsq.rob_idx[0])
        
        busy_flag = lsq.busy[0]
        
        # 监听所有广播信号，更新操作数
        for bcast_idx, (bcast_rob_idx, bcast_rd_data, bcast_valid) in enumerate(all_broadcasts):
            bcast_rob_idx = bcast_rob_idx.optional(default=UInt(ROB_IDX_WIDTH)(0))
            bcast_rd_data = bcast_rd_data.optional(default=UInt(32)(0))
            bcast_valid = bcast_valid.optional(default=Bits(1)(0))
            
            with Condition(bcast_valid & (busy_flag == Bits(1)(1))):
                # 如果有新的广播信号，更新 lsq 中等待的操作数
                with Condition((lsq.qj[0] == bcast_rob_idx) & ~lsq.qj_valid[0]):
                    lsq.vj[0] <= bcast_rd_data
                    lsq.qj_valid[0] <= Bits(1)(1)  # 标记为就绪
                    log("LSQ: update qj from bcast, rob={} data=0x{:08x}", bcast_rob_idx, bcast_rd_data)
                with Condition((lsq.qk[0] == bcast_rob_idx) & ~lsq.qk_valid[0]):
                    lsq.vk[0] <= bcast_rd_data
                    lsq.qk_valid[0] <= Bits(1)(1)  # 标记为就绪
                    log("LSQ: update qk from bcast, rob={} data=0x{:08x}", bcast_rob_idx, bcast_rd_data)
                    
                # 如果广播的 ROB 索引匹配当前 LSQ 的目标，清空 LSQ
                with Condition(bcast_rob_idx == lsq.rob_idx[0]):
                    lsq.busy[0] <= Bits(1)(0)
                    lsq.qj_valid[0] <= Bits(1)(0)
                    lsq.qk_valid[0] <= Bits(1)(0)
                    lsq.fired[0] <= Bits(1)(0)
        
        log("LSQ debug: busy={} is_load={} is_store={} qj_v={} qk_v={} has_no_store={}", lsq.busy[0], lsq.is_load[0], lsq.is_store[0], lsq.qj_valid[0], lsq.qk_valid[0], rob.has_no_store())
        with Condition(lsq.busy[0] & ~(lsq.qj_valid[0] & lsq.qk_valid[0])):
            log("LSQ waiting rob_idx={} qj_valid={} qk_valid={} qj={} qk={}", lsq.rob_idx[0], lsq.qj_valid[0], lsq.qk_valid[0], lsq.qj[0], lsq.qk[0])
            # 如果依赖的生产者已提交（rob.busy=0），直接从寄存器补全
            with Condition(~lsq.qk_valid[0] & (rob._read_busy(lsq.qk[0]) == Bits(1)(0))):
                lsq.vk[0] <= regs[lsq.rs2_id[0]]
                lsq.qk_valid[0] <= Bits(1)(1)
        re = (lsq.busy[0] & (lsq.qj_valid[0] & lsq.qk_valid[0]) & (~lsq.fired[0]) & lsq.is_load[0] & rob.has_no_store())
        with Condition(lsq.busy[0] & (lsq.qj_valid[0] & lsq.qk_valid[0]) & (~lsq.fired[0])):
            with Condition(lsq.is_store[0]):
                log("LSQ fire store: rob_idx={} addr=0x{:08x} data=0x{:08x}", lsq.rob_idx[0], lsq.vj[0] + lsq.imm[0], lsq.vk[0])
                lsu.async_called(
                    lsu_signal=LSU_signal.bundle(
                        is_load=Bits(1)(0),
                        is_store=Bits(1)(1),
                        ROB_idx=lsq.rob_idx[0],
                        address=lsq.vj[0] + lsq.imm[0],
                        rs2_value=lsq.vk[0],
                    )
                )
                lsq.fired[0] <= Bits(1)(1)
            with Condition(lsq.is_load[0] & rob.has_no_store()):
                log("LSQ fire load: rob_idx={} addr=0x{:08x}", lsq.rob_idx[0], lsq.vj[0] + lsq.imm[0])
                lsu.async_called(
                    lsu_signal=LSU_signal.bundle(
                        is_load=Bits(1)(1),
                        is_store=Bits(1)(0),
                        ROB_idx=lsq.rob_idx[0],
                        address=lsq.vj[0] + lsq.imm[0],
                        rs2_value=Bits(32)(0),
                    )
                )
                lsq.fired[0] <= Bits(1)(1)
        # re address
        return re, lsq.vj[0] + lsq.imm[0]

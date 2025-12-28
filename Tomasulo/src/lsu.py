from assassyn.frontend import *
try:
    from .instruction import *
except ImportError:
    from Tomasulo.src.instruction import *

LSU_signal = Record(
    is_load = Bits(1),
    is_store = Bits(1),
    ROB_idx = UInt(4),    # 指令在 ROB 中的索引
    address = UInt(32),   # 计算得到的内存地址
    rs2_value = UInt(32), # 源操作数 2 的值（仅用于存储指令）
    
)

LSU_CBD_signal = Record(
    ROB_idx = UInt(4),    # 指令在 ROB 中的索引
    rd_data = UInt(32),   # 写回数据 (仅用于 load 指令)
    valid = Bits(1),     # 数据有效标志
    is_load = Bits(1),  # 是否为 load 指令
    is_store = Bits(1), # 是否为 store 指令
    store_addr = UInt(32), # store 地址
    store_data = UInt(32), # store 数据
)

# 在 async_call 这个 LSU 前就应该 build 好 dcache，这样直接拿数据即可
class LSU(Module):
    def __init__(self):
        super().__init__(ports = {
            "lsu_signal" : Port(LSU_signal),
        })
    @module.combinational
    def build(self, dcache : SRAM):
        LSU_signal = self.pop_all_ports(True)
        log("LSU: req is_load={} is_store={} addr=0x{:08x} rs2=0x{:08x} rob_idx={}", LSU_signal.is_load, LSU_signal.is_store, LSU_signal.address, LSU_signal.rs2_value, LSU_signal.ROB_idx)
        return LSU_CBD_signal.bundle(
            ROB_idx = LSU_signal.ROB_idx,
            rd_data = LSU_signal.is_load.select(
                dcache.dout[0].bitcast(UInt(32)),
                UInt(32)(0),
            ),
            valid = Bits(1)(1),
            is_load = LSU_signal.is_load,
            is_store = LSU_signal.is_store,
            store_addr = LSU_signal.address,
            store_data = LSU_signal.rs2_value,
        )

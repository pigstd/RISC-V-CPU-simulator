from assassyn.frontend import *

# 环形 ROB 队列深度
FIFO_SIZE = 8
ROB_IDX_WIDTH = (FIFO_SIZE - 1).bit_length()
# reg_pending 需要一个额外的 sentinel，因此使用更宽的位宽
REG_PENDING_WIDTH = ROB_IDX_WIDTH + 1


# ROB: 按字段分布式存储为寄存器队列，同时维护头尾指针
class ROB:
    def __init__(self):
        # 环形队列指针
        self.head = RegArray(UInt(ROB_IDX_WIDTH), 1, initializer=[0])
        self.tail = RegArray(UInt(ROB_IDX_WIDTH), 1, initializer=[0])

        # 各字段的寄存器队列
        self.busy = RegArray(Bits(1), FIFO_SIZE, initializer=[0] * FIFO_SIZE)
        self.ready = RegArray(Bits(1), FIFO_SIZE, initializer=[0] * FIFO_SIZE)
        self.dest = RegArray(Bits(5), FIFO_SIZE, initializer=[0] * FIFO_SIZE)
        self.value = RegArray(UInt(32), FIFO_SIZE, initializer=[0] * FIFO_SIZE)
        self.is_branch = RegArray(Bits(1), FIFO_SIZE, initializer=[0] * FIFO_SIZE)
        self.pc = RegArray(UInt(32), FIFO_SIZE, initializer=[0] * FIFO_SIZE)
        self.is_syscall = RegArray(Bits(1), FIFO_SIZE, initializer=[0] * FIFO_SIZE)
        self.is_store = RegArray(Bits(1), FIFO_SIZE, initializer=[0] * FIFO_SIZE)
        # store 专用字段：地址与数据
        self.store_addr = RegArray(UInt(32), FIFO_SIZE, initializer=[0] * FIFO_SIZE)
        self.store_data = RegArray(UInt(32), FIFO_SIZE, initializer=[0] * FIFO_SIZE)
    def is_full(self) -> Bits:
        """
        判断 ROB 是否已满：next_tail 与 head 重合且 head 位置忙。
        """
        next_tail = (self.tail[0] + UInt(ROB_IDX_WIDTH)(1)).bitcast(UInt(ROB_IDX_WIDTH))
        return (next_tail == self.head[0]) & self.busy[self.head[0]]
    def has_no_store(self) -> Bits:
        """
        ROB 内没有待提交的 store：枚举所有 entry 的 is_store 取反求与。
        """
        no_store = Bits(1)(1)
        for i in range(FIFO_SIZE):
            no_store = no_store & ~self.is_store[i]
        return no_store

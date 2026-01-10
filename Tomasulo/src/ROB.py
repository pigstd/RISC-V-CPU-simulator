from assassyn.frontend import *

# 环形 ROB 队列深度
FIFO_SIZE = 8
ROB_IDX_WIDTH = (FIFO_SIZE - 1).bit_length()
# reg_pending 需要一个额外的 sentinel，因此使用更宽的位宽
REG_PENDING_WIDTH = ROB_IDX_WIDTH + 1

# BHT 配置
BHT_SIZE = 64  # BHT 条目数量（2^6 = 64）
BHT_IDX_WIDTH = 6  # 用 PC[7:2] 作为索引（跳过低2位对齐）


class BHT:
    """
    Branch History Table - 分支历史表
    使用 2-bit 饱和计数器进行分支预测
    
    计数器状态：
    - 00 (0): 强不跳转 (Strongly Not Taken)
    - 01 (1): 弱不跳转 (Weakly Not Taken)
    - 10 (2): 弱跳转   (Weakly Taken)
    - 11 (3): 强跳转   (Strongly Taken)
    
    预测：计数器 >= 2 时预测跳转
    更新：taken +1（饱和到3），not taken -1（饱和到0）
    """
    def __init__(self):
        # 单个 RegArray 存储所有 64 个 2-bit 计数器
        # 初始化为 2（弱跳转）
        self.counters = RegArray(Bits(2), BHT_SIZE, initializer=[2] * BHT_SIZE)
    
    def get_index(self, pc: Value) -> Value:
        """
        从 PC 计算 BHT 索引
        使用 PC[7:2]（跳过低2位字节对齐），然后取模确保在范围内
        """
        # PC >> 2 得到字地址，然后 & (BHT_SIZE-1) 取模
        word_addr = (pc >> UInt(32)(2)).bitcast(UInt(32))
        return (word_addr & UInt(32)(BHT_SIZE - 1)).bitcast(Bits(BHT_IDX_WIDTH))
    
    def predict(self, pc: Value) -> Value:
        """
        根据 PC 预测是否跳转
        返回 Bits(1): 1=预测跳转, 0=预测不跳转
        """
        idx = self.get_index(pc)
        counter = self.counters[idx]  # 直接索引读取
        # 计数器 >= 2 时预测跳转
        return (counter >= Bits(2)(2)).select(Bits(1)(1), Bits(1)(0))
    
    def update_if(self, cond: Value, pc: Value, taken: Value):
        """
        条件更新：仅当 cond=1 时更新
        taken=1: 计数器+1（饱和到3）
        taken=0: 计数器-1（饱和到0）
        """
        idx = self.get_index(pc)
        old_val = self.counters[idx].bitcast(UInt(2))
        # 饱和加减 - 使用 UInt 进行算术运算
        new_val = taken.select(
            # taken: +1, 饱和到 3
            (old_val == UInt(2)(3)).select(UInt(2)(3), old_val + UInt(2)(1)),
            # not taken: -1, 饱和到 0
            (old_val == UInt(2)(0)).select(UInt(2)(0), old_val - UInt(2)(1))
        )
        with Condition(cond):
            self.counters[idx] <= new_val.bitcast(Bits(2))


# RAT: 32个独立的RegArray，支持同周期flush
class RAT:
    """
    Register Alias Table - 重命名表
    使用32个独立的RegArray实现，以便支持同周期全部flush
    每个entry存储 rob_idx + 1，0表示无依赖
    """
    def __init__(self):
        # 32个独立的RegArray，每个存储一个寄存器的pending信息
        self.pending = [RegArray(Bits(REG_PENDING_WIDTH), 1, initializer=[0]) 
                       for _ in range(32)]
    
    def read(self, reg_idx: Value) -> Value:
        """
        组合逻辑读取指定寄存器的pending信息
        返回 rob_idx + 1，0表示无依赖
        """
        result = Bits(REG_PENDING_WIDTH)(0)
        for i in range(32):
            result = (reg_idx == Bits(5)(i)).select(self.pending[i][0], result)
        return result
    
    def __getitem__(self, reg_idx: Value) -> Value:
        """支持 rat[reg_idx] 语法的读取"""
        return self.read(reg_idx)
    
    def write_if(self, cond: Value, reg_idx: Value, value: Value):
        """
        带条件的写入，用于处理 rd != 0 等情况
        """
        for i in range(32):
            with Condition(cond & (reg_idx == Bits(5)(i))):
                log("RAT.write_if: rd={} val={}", reg_idx, value)
                self.pending[i][0] <= value
    
    def clear_if(self, reg_idx: Value, expected_value: Value):
        """
        条件清零，仅当当前值等于expected_value时才清零
        用于commit时清理：只有RAT仍指向当前ROB entry时才清零
        """
        for i in range(32):
            cond = (reg_idx == Bits(5)(i)) & (self.pending[i][0] == expected_value)
            with Condition(cond):
                log("RAT.clear_if: rd={} pending={} -> 0", reg_idx, expected_value)
                self.pending[i][0] <= Bits(REG_PENDING_WIDTH)(0)
    
    def flush_all(self):
        """
        Flush时调用，同周期清空所有32个entry
        """
        for i in range(32):
            self.pending[i][0] <= Bits(REG_PENDING_WIDTH)(0)

# 避免 clear_if 和 write_if 冲突，如果同时操作同一个寄存器，那么 write_if 优先级更高
class RAT_downstream(Downstream):
    def __init__(self):
        super().__init__()
    @downstream.combinational
    def build(self,
              rat: RAT,
              write_if_cond: Value,
              write_if_reg_idx: Value,
              write_if_value: Value,
              clear_if_cond : Value,
              clear_if_reg_idx: Value,
              clear_if_expected_value: Value):
        write_if_cond = write_if_cond.optional(default=Bits(1)(0))
        write_if_reg_idx = write_if_reg_idx.optional(default=Bits(5)(0))
        write_if_value = write_if_value.optional(default=Bits(REG_PENDING_WIDTH)(0))
        clear_if_cond = clear_if_cond.optional(default=Bits(1)(0))
        clear_if_reg_idx = clear_if_reg_idx.optional(default=Bits(5)(0))
        clear_if_expected_value = clear_if_expected_value.optional(default=Bits(REG_PENDING_WIDTH)(0))
        rat.write_if(write_if_cond, write_if_reg_idx, write_if_value)
        with Condition(((~write_if_cond) | (write_if_reg_idx != clear_if_reg_idx)) & clear_if_cond):
            rat.clear_if(clear_if_reg_idx, clear_if_expected_value)

# ROB: 按字段分布式存储为寄存器队列，同时维护头尾指针
# 需要在 flush 时清空的字段使用独立 RegArray 列表，避免动态/静态索引冲突
class ROB:
    def __init__(self):
        # 环形队列指针
        self.head = RegArray(UInt(ROB_IDX_WIDTH), 1, initializer=[0])
        self.tail = RegArray(UInt(ROB_IDX_WIDTH), 1, initializer=[0])

        # ========== 需要在 flush 时清空的字段：使用独立 RegArray 列表 ==========
        # 这样可以在 flush 时用静态索引写入，在其他时候用动态索引写入，互不冲突
        self.busy = [RegArray(Bits(1), 1, initializer=[0]) for _ in range(FIFO_SIZE)]
        self.ready = [RegArray(Bits(1), 1, initializer=[0]) for _ in range(FIFO_SIZE)]
        self.is_branch = [RegArray(Bits(1), 1, initializer=[0]) for _ in range(FIFO_SIZE)]
        self.is_syscall = [RegArray(Bits(1), 1, initializer=[0]) for _ in range(FIFO_SIZE)]
        self.is_store = [RegArray(Bits(1), 1, initializer=[0]) for _ in range(FIFO_SIZE)]
        self.is_jalr = [RegArray(Bits(1), 1, initializer=[0]) for _ in range(FIFO_SIZE)]
        self.predicted_taken = [RegArray(Bits(1), 1, initializer=[0]) for _ in range(FIFO_SIZE)]
        
        # ========== 不需要在 flush 时清空的字段：保持单个 RegArray ==========
        # 这些字段只在分配或更新时用动态索引写入，不会冲突
        self.dest = RegArray(Bits(5), FIFO_SIZE, initializer=[0] * FIFO_SIZE)
        # value 可能在同一周期被多个执行单元写入，拆成 per-entry RegArray 以避免同一端口被重复使用
        self.value = [RegArray(UInt(32), 1, initializer=[0]) for _ in range(FIFO_SIZE)]
        self.pc = RegArray(UInt(32), FIFO_SIZE, initializer=[0] * FIFO_SIZE)
        # store 专用字段：地址与数据
        self.store_addr = RegArray(UInt(32), FIFO_SIZE, initializer=[0] * FIFO_SIZE)
        self.store_data = RegArray(UInt(32), FIFO_SIZE, initializer=[0] * FIFO_SIZE)
        # 分支预测相关字段
        self.predicted_pc = RegArray(UInt(32), FIFO_SIZE, initializer=[0] * FIFO_SIZE)
    def _read_busy(self, idx: Value) -> Value:
        """辅助方法：通过动态索引读取 busy"""
        result = Bits(1)(0)
        for i in range(FIFO_SIZE):
            result = (idx == UInt(ROB_IDX_WIDTH)(i)).select(self.busy[i][0], result)
        return result
    
    def _read_ready(self, idx: Value) -> Value:
        """辅助方法：通过动态索引读取 ready"""
        result = Bits(1)(0)
        for i in range(FIFO_SIZE):
            result = (idx == UInt(ROB_IDX_WIDTH)(i)).select(self.ready[i][0], result)
        return result
    
    def _read_is_branch(self, idx: Value) -> Value:
        """辅助方法：通过动态索引读取 is_branch"""
        result = Bits(1)(0)
        for i in range(FIFO_SIZE):
            result = (idx == UInt(ROB_IDX_WIDTH)(i)).select(self.is_branch[i][0], result)
        return result
    
    def _read_is_syscall(self, idx: Value) -> Value:
        """辅助方法：通过动态索引读取 is_syscall"""
        result = Bits(1)(0)
        for i in range(FIFO_SIZE):
            result = (idx == UInt(ROB_IDX_WIDTH)(i)).select(self.is_syscall[i][0], result)
        return result
    
    def _read_is_store(self, idx: Value) -> Value:
        """辅助方法：通过动态索引读取 is_store"""
        result = Bits(1)(0)
        for i in range(FIFO_SIZE):
            result = (idx == UInt(ROB_IDX_WIDTH)(i)).select(self.is_store[i][0], result)
        return result
    
    def _read_is_jalr(self, idx: Value) -> Value:
        """辅助方法：通过动态索引读取 is_jalr"""
        result = Bits(1)(0)
        for i in range(FIFO_SIZE):
            result = (idx == UInt(ROB_IDX_WIDTH)(i)).select(self.is_jalr[i][0], result)
        return result
    
    def _read_predicted_taken(self, idx: Value) -> Value:
        """辅助方法：通过动态索引读取 predicted_taken"""
        result = Bits(1)(0)
        for i in range(FIFO_SIZE):
            result = (idx == UInt(ROB_IDX_WIDTH)(i)).select(self.predicted_taken[i][0], result)
        return result
    
    def _write_busy(self, idx: Value, val: Value):
        """辅助方法：通过动态索引写入 busy"""
        for i in range(FIFO_SIZE):
            with Condition(idx == UInt(ROB_IDX_WIDTH)(i)):
                self.busy[i][0] <= val
    
    def _write_ready(self, idx: Value, val: Value):
        """辅助方法：通过动态索引写入 ready"""
        for i in range(FIFO_SIZE):
            with Condition(idx == UInt(ROB_IDX_WIDTH)(i)):
                self.ready[i][0] <= val
    
    def _write_is_branch(self, idx: Value, val: Value):
        """辅助方法：通过动态索引写入 is_branch"""
        for i in range(FIFO_SIZE):
            with Condition(idx == UInt(ROB_IDX_WIDTH)(i)):
                self.is_branch[i][0] <= val
    
    def _write_is_syscall(self, idx: Value, val: Value):
        """辅助方法：通过动态索引写入 is_syscall"""
        for i in range(FIFO_SIZE):
            with Condition(idx == UInt(ROB_IDX_WIDTH)(i)):
                self.is_syscall[i][0] <= val
    
    def _write_is_store(self, idx: Value, val: Value):
        """辅助方法：通过动态索引写入 is_store"""
        for i in range(FIFO_SIZE):
            with Condition(idx == UInt(ROB_IDX_WIDTH)(i)):
                self.is_store[i][0] <= val
    
    def _write_is_jalr(self, idx: Value, val: Value):
        """辅助方法：通过动态索引写入 is_jalr"""
        for i in range(FIFO_SIZE):
            with Condition(idx == UInt(ROB_IDX_WIDTH)(i)):
                self.is_jalr[i][0] <= val
    
    def _write_predicted_taken(self, idx: Value, val: Value):
        """辅助方法：通过动态索引写入 predicted_taken"""
        for i in range(FIFO_SIZE):
            with Condition(idx == UInt(ROB_IDX_WIDTH)(i)):
                self.predicted_taken[i][0] <= val

    def _read_value(self, idx: Value) -> Value:
        """通过动态索引读取 value（拆分为 per-entry RegArray 后的包装）"""
        result = UInt(32)(0)
        for i in range(FIFO_SIZE):
            result = (idx == UInt(ROB_IDX_WIDTH)(i)).select(self.value[i][0], result)
        return result

    def _write_value(self, idx: Value, val: Value):
        """通过动态索引写入 value（每个 entry 独立的 RegArray）"""
        for i in range(FIFO_SIZE):
            with Condition(idx == UInt(ROB_IDX_WIDTH)(i)):
                self.value[i][0] <= val

    def is_full(self) -> Bits:
        """
        判断 ROB 是否已满：next_tail 与 head 重合且 head 位置忙。
        """
        next_tail = (self.tail[0] + UInt(ROB_IDX_WIDTH)(1)).bitcast(UInt(ROB_IDX_WIDTH))
        return (next_tail == self.head[0]) & self._read_busy(self.head[0])
    def has_no_store(self) -> Bits:
        """
        ROB 内没有待提交的 store：枚举所有 entry 的 is_store 取反求与。
        """
        no_store = Bits(1)(1)
        for i in range(FIFO_SIZE):
            no_store = no_store & ~self.is_store[i][0]
        return no_store
    
    def flush(self):
        """
        Flush ROB：重置tail到head，清空所有busy位
        用于分支预测失败时的恢复
        使用独立 RegArray 列表，每个寄存器只写一次，符合 Assassyn 设计理念
        """
        # 重置tail指针到head
        log("ROB.flush: tail {} -> head {}", self.tail[0], self.head[0])
        self.tail[0] <= self.head[0]
        # 清空所有entry的相关位（每个独立 RegArray 只写一次）
        for i in range(FIFO_SIZE):
            self.busy[i][0] <= Bits(1)(0)
            self.ready[i][0] <= Bits(1)(0)
            self.is_branch[i][0] <= Bits(1)(0)
            self.is_syscall[i][0] <= Bits(1)(0)
            self.is_store[i][0] <= Bits(1)(0)
            self.is_jalr[i][0] <= Bits(1)(0)
            self.predicted_taken[i][0] <= Bits(1)(0)

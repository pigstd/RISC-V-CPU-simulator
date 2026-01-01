from assassyn.frontend import *
from .ROB import *

# 简单的提交器：每个周期尝试提交 head 处的一条指令


class Commiter(Module):
    def __init__(self):
        super().__init__(ports={})

    @module.combinational
    def build(self, rob: ROB, regs: RegArray, rat: RAT):
        head = rob.head[0]
        can_commit = rob.busy[head] & rob.ready[head]

        mem_we = can_commit & rob.is_store[head]
        mem_addr = mem_we.select(rob.store_addr[head], UInt(32)(0))
        mem_data = mem_we.select(rob.store_data[head], UInt(32)(0))
        log("commit: can_commit={} head={} is_store={} rd={} value={}", can_commit, head, rob.is_store[head], rob.dest[head], rob.value[head])

        # 仅当 RAT 仍指向 head 时清零映射
        head_tag = (head + UInt(ROB_IDX_WIDTH)(1)).bitcast(Bits(REG_PENDING_WIDTH))
        dest = rob.dest[head]

        with Condition(can_commit):
            # 统一的提交日志，便于统计提交数量（含 store 和 syscall）
            log("commit: retire rob={} pc=0x{:08x} rd={} is_store={} value=0x{:08x}", head, rob.pc[head], rob.dest[head], rob.is_store[head], rob.value[head])
            with Condition(rob.is_syscall[head]):
                log("commit: hit syscall/ebreak at pc=0x{:08x}", rob.pc[head])
                finish()
            # 普通写回（非 store），rd != 0
            with Condition(~rob.is_store[head] & (dest != Bits(5)(0))):
                regs[dest] <= rob.value[head]
                # 使用 RAT 的 clear_if 方法，仅当当前映射仍指向此 ROB entry 时清零
                rat.clear_if(dest, head_tag)
                log("commit: writeback rd={} value={}", dest, rob.value[head])
            # 清空 entry 状态
            rob.busy[head] <= Bits(1)(0)
            rob.ready[head] <= Bits(1)(0)
            rob.is_branch[head] <= Bits(1)(0)
            rob.is_syscall[head] <= Bits(1)(0)
            rob.is_store[head] <= Bits(1)(0)
            rob.dest[head] <= Bits(5)(0)
            rob.value[head] <= UInt(32)(0)
            rob.pc[head] <= UInt(32)(0)
            rob.store_addr[head] <= UInt(32)(0)
            rob.store_data[head] <= UInt(32)(0)
            # 清空分支预测相关字段
            rob.predicted_taken[head] <= Bits(1)(0)
            rob.predicted_pc[head] <= UInt(32)(0)
            rob.is_jalr[head] <= Bits(1)(0)

            # head++（环形）
            next_head = ((head + UInt(ROB_IDX_WIDTH)(1)) & UInt(ROB_IDX_WIDTH)((1 << ROB_IDX_WIDTH) - 1)).bitcast(UInt(ROB_IDX_WIDTH))
            rob.head[0] <= next_head
        return mem_we, mem_addr, mem_data
        

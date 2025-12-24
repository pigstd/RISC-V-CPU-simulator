from assassyn.frontend import *
from assassyn.backend import *
from assassyn import utils, backend
from assassyn.utils import run_simulator, run_verilator
from decoder import *
from executor import executor_logic

class WriteBack(Module):
    def __init__(self):
        super().__init__(
            ports={
                    "rd": Port(Bits(5)),
                    "data": Port(Bits(32))
                }
        )
    @module.combinational
    def build(self, regs: RegArray, fetcher, reg_to_write: RegArray):
        rd, data = self.pop_all_ports(True)
        with Condition(rd != Bits(5)(0)):
            regs[rd] <= data.bitcast(UInt(32))
            log("writeback stage: rd = {} data = {}", rd, data)
            # 写回后，目标寄存器待写入数减一
            reg_to_write[rd] <= reg_to_write[rd] - UInt(32)(1)
        fetcher.async_called()

class MemoryAccess(Module):
    def __init__(self):
        super().__init__(
            ports={
                    "decoder_result": Port(deocder_signals),
                    "wdata": Port(Bits(32))
                }
        )

    @module.combinational
    def build(self,
              dcache: SRAM,
              writeback: WriteBack,
              regs: RegArray):
        signals, wdata = self.pop_all_ports(True)
        rs1_val = signals.rs1_used.select(regs[signals.rs1], UInt(32)(0))
        rs2_val = signals.rs2_used.select(regs[signals.rs2], UInt(32)(0))
        eff_addr = (rs1_val + signals.imm.bitcast(UInt(32))).bitcast(UInt(32))
        misaligned = (eff_addr & UInt(32)(0b11)) != UInt(32)(0)
        mem_re = signals.mem_read & ~misaligned
        mem_we = signals.mem_write & ~misaligned

        # 读取 dcache dout（executor 在前一拍已触发）
        mem_rdata = dcache.dout[0]

        with Condition(signals.mem_read | signals.mem_write):
            log("memory stage: read={} write={} addr={} rs1_val={} imm={} rs2_val={} misaligned={}",
                mem_re, mem_we, eff_addr, rs1_val, signals.imm, rs2_val, misaligned)

        # store 访存已在 EX 阶段触发，这里仅记录
        with Condition(mem_we):
            log("memory store: addr={} data={}", eff_addr, rs2_val)

        # load写回
        with Condition(mem_re & signals.rd_used & (signals.rd != Bits(5)(0))):
            log("memory load writeback: rd={} data={}", signals.rd, mem_rdata)
        
        wb_data = mem_re.select(
            mem_rdata,
            wdata
        )
        rd_for_wb = signals.rd_used.select(signals.rd, Bits(5)(0))
        writeback.async_called(rd=rd_for_wb, data=wb_data)

class Executor(Module):
    def __init__(self):
        super().__init__(
            ports={"decoder_result": Port(deocder_signals),
                   "pc_addr": Port(UInt(32))}
        )

    @module.combinational
    def build(self, regs: RegArray, pc_reg: RegArray, memoryaccess: MemoryAccess, dcache: SRAM):
        decoder_result, pc_addr = self.pop_all_ports(True)
        rd_data, ex_branch_taken, ex_pc_next = executor_logic(
            signals = decoder_result,
            regs = regs,
            pc_addr= pc_addr,
            dcache = dcache)
        memoryaccess.async_called(decoder_result=decoder_result, wdata=rd_data)
        return ex_branch_taken, ex_pc_next


class Decoder(Module):
    def __init__(self):
        super().__init__(
            ports={"pc_addr": Port(UInt(32))}
        )
    @module.combinational
    def build(self,
              icache: SRAM,
              executor: Executor,
              reg_to_write: RegArray):
        pc_addr = self.pop_all_ports(True)
        instr = icache.dout[0]
        opcode = instr[0:6]
        funct3 = instr[12:14]
        funct7 = instr[25:31]
        log("decoder fetch pc={} instr=0x{:08x} opcode={:07b} funct3={:03b} funct7={:07b}",
            pc_addr, instr, opcode, funct3, funct7)

        decoder_result = decoder_logic(inst=instr, reg_to_write=reg_to_write)
        with Condition(decoder_result.is_valid):
            executor.async_called(decoder_result=decoder_result, pc_addr=pc_addr)
        with Condition(~decoder_result.is_valid):
            log("decoder invalid instruction at pc={}: instr=0x{:08x}", pc_addr, instr)
        # is_branch, pc_addr, is_valid
        # is_valid 应该在 decoder 的时候放进去，但是现在还没有写
        return decoder_result.is_branch, pc_addr, decoder_result.is_valid

class Fetcher(Module):
    def __init__(self):
        super().__init__(
            ports={}
        )
    @module.combinational
    def build(self,
              icache: SRAM,
              decoder: Decoder,
              pc_reg: RegArray):
        pc_addr = pc_reg[0]

        # log("fetch stage pc addr: {}", pc_addr)

        # 由于是 naive CPU，所以要取的肯定就是 pc_addr 对应的指令
        # PC 是字节地址，SRAM 按字（word）索引，需要右移2位
        # word_addr = (pc_addr >> UInt(32)(2)).bitcast(UInt(32))
        # icache.build(we=Bits(1)(0),
        #              re=Bits(1)(1),
        #              addr=word_addr,
        #              wdata=Bits(32)(0))
        # decoder.async_called(pc_addr=pc_addr)

        return pc_reg, pc_addr

class FetcherImpl(Downstream):
    def __init__(self):
        super().__init__()
    # FetcherImpl 完成了 Fetcher 的下游接口
    # 需要 Decoder 的时候知道上一条是不是 分支指令
    # 如果是，那么就要停，
    # 下个cycle 应该 ex_is_brach 满足，并且直接从 ex_pc_bypass 取地址
    # 如果数据 invalid，这个时候应该重新 fetch 同一条指令（decoder 用过的的指令）
    # invalid 的优先级高，也就是说，如果 invalid，那么一定是要取 decoder_pc_addr 的地址
    # 否则就继续取指
    @downstream.combinational
    def build(self,
              is_branch : Value,
              is_valid : Value,
              pc_reg : RegArray,
              pc_addr : Value,
              decoder_pc_addr : Value,
              ex_is_branch : Value,
              ex_pc_bypass : Value,
              icache : SRAM,
              decoder : Decoder):
        is_branch = is_branch.optional(Bits(1)(0))
        is_valid = is_valid.optional(Bits(1)(1))
        ex_is_branch = ex_is_branch.optional(Bits(1)(0))
        ex_pc_bypass = ex_pc_bypass.optional(UInt(32)(0))
        decoder_pc_addr = decoder_pc_addr.optional(UInt(32)(0))

        # 如果 上一条不是分支，或者数据 invalid，那么都需要 fetch
        need_fetch = (~is_branch) | (~is_valid) 

        log("fetcher: is_branch={} is_valid={} ex_is_branch={} pc_addr={} decoder_pc_addr={}",
            is_branch, is_valid, ex_is_branch, pc_addr, decoder_pc_addr)

        fetch_pc_addr = is_valid.select(
            ex_is_branch.select(ex_pc_bypass, pc_addr),
            decoder_pc_addr)

        word_addr = (fetch_pc_addr >> UInt(32)(2)).bitcast(UInt(32))
        icache.build(we=Bits(1)(0),
                     re=need_fetch,
                     addr=word_addr,
                     wdata=Bits(32)(0))
        
        with Condition(need_fetch):
            pc_reg[0] <= fetch_pc_addr + UInt(32)(4)
            decoder.async_called(pc_addr=fetch_pc_addr)
            log("fetch stage pc addr: {}", fetch_pc_addr)
        with Condition(~need_fetch):
            # 保持为这个 decoder 出来的地址，这样之后修改就不会错
            pc_reg[0] <= decoder_pc_addr  
            log("fetch stage hold pc addr: {}", decoder_pc_addr)

class Driver(Module):
    def __init__(self):
        super().__init__(
            ports={}
        )
    @module.combinational
    def build(self, fecher : Fetcher):
        is_init = RegArray(UInt(1), 1, initializer=[1])

        with Condition(is_init[0] == UInt(1)(1)):
            is_init[0] <= UInt(1)(0)
            fecher.async_called()
            log("CPU Simulation Started")
        with Condition(is_init[0] == UInt(1)(0)):
            fecher.async_called()


current_path = os.path.dirname(os.path.abspath(__file__))
workspace = f'{current_path}/workspace/'

def build_CPU(depth_log=18):
    sys = SysBuilder("CPU")
    with sys:
        icache = SRAM(width= 32,
                      depth= 1 << depth_log,
                      init_file= f"{workspace}/workload.exe")
        icache.name = "icache"
        dcache = SRAM(width= 32,
                      depth= 1 << depth_log,
                      init_file= f"{workspace}/data.mem")
        dcache.name = "dcache"
        regs = RegArray(UInt(32), 32, initializer=[0]*32)
        pc_reg = RegArray(UInt(32), 1, initializer=[0])
        # 每个寄存器有多少个指令要写入但是还没有写入
        reg_to_write = RegArray(UInt(32), 32, initializer=[0]*32)

        writeback = WriteBack()
        memoryaccess = MemoryAccess()
        executor = Executor()
        decoder = Decoder()
        fetcher = Fetcher()
        driver = Driver()
        fetcherimpl = FetcherImpl()
        writeback.build(regs=regs, fetcher=fetcher, reg_to_write=reg_to_write)
        memoryaccess.build(dcache=dcache, regs=regs, writeback=writeback)
        is_branch, decoder_pc_reg, is_valid = decoder.build(icache=icache, executor=executor, reg_to_write=reg_to_write)
        pc_reg, pc_addr = fetcher.build(icache=icache, decoder=decoder, pc_reg=pc_reg)
        driver.build(fecher=fetcher)
        ex_branch_taken, ex_pc_next = executor.build(regs=regs, pc_reg=pc_reg, memoryaccess=memoryaccess, dcache=dcache)
        fetcherimpl.build(is_branch=is_branch,
                          is_valid=is_valid,
                          pc_reg=pc_reg,
                          pc_addr=pc_addr,
                          decoder_pc_addr=decoder_pc_reg,
                          ex_is_branch=ex_branch_taken,
                          ex_pc_bypass=ex_pc_next,
                          icache=icache,
                          decoder=decoder)
    return sys

def main():
    import argparse
    import executor

    # --sim-threshold 100 --idle-threshold 100 设置模拟器参数
    parser = argparse.ArgumentParser(description="Run CPU simulator")
    parser.add_argument("--sim-threshold", type=int, default=100, help="max simulation steps")
    parser.add_argument("--idle-threshold", type=int, default=100, help="idle cycles before stop")
    parser.add_argument("--data-base", type=lambda x: int(x, 0), default=0x2000, 
                        help="data segment base address (default: 0x2000)")
    args = parser.parse_args()

    # 设置数据段基地址
    executor.DATA_BASE_OFFSET = args.data_base
    print(f"Config: data_base=0x{args.data_base:x}, sim_threshold={args.sim_threshold}, idle_threshold={args.idle_threshold}")

    sys = build_CPU(depth_log = 18)
    cfg = backend.config(
        resource_base='.',
        verilog=True,
        verbose=True,
        sim_threshold=args.sim_threshold,
        idle_threshold=args.idle_threshold,
    )
    sim,vcd = elaborate(sys=sys, **cfg)
    output = run_simulator(sim)
    print("simulate output is written in /workspace/log")
    with open(f"{workspace}/log", "w") as f:
        print(output, file = f)

if __name__ == "__main__":
    main()

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
        return rd_for_wb, wb_data

class Mem_downstream(Downstream):
    def __init__(self):
        super().__init__()
    @downstream.combinational
    def build(self,
              MEM_rd : RegArray,
              MEM_result : RegArray,
              MEM_rd_in : Value,
              MEM_result_in : Value):
        MEM_rd_in = MEM_rd_in.optional(Bits(5)(0))
        MEM_result_in = MEM_result_in.optional(Bits(32)(0))
        MEM_rd[0] <= MEM_rd_in
        MEM_result[0] <= MEM_result_in.bitcast(UInt(32))

class Executor(Module):
    def __init__(self):
        super().__init__(
            ports={"decoder_result": Port(deocder_signals),
                   "pc_addr": Port(UInt(32))}
        )

    @module.combinational
    def build(self, memoryaccess: MemoryAccess, dcache: SRAM,
              EX_rd : RegArray,
              EX_result : RegArray,
              MEM_rd : RegArray,
              MEM_result : RegArray):
        decoder_result, pc_addr = self.pop_all_ports(True)
        rd_data, ex_branch_taken, ex_pc_next, mem_re, mem_we = executor_logic(
            signals = decoder_result,
            pc_addr= pc_addr,
            dcache = dcache,
            EX_rd = EX_rd[0],
            EX_result = EX_result[0],
            MEM_rd = MEM_rd[0],
            MEM_result = MEM_result[0]
        )
        memoryaccess.async_called(decoder_result=decoder_result, wdata=rd_data)
        return ex_branch_taken, ex_pc_next, decoder_result.rd, rd_data, mem_re, mem_we

# 把 ex 的结果传进寄存器，如果没有调用 EX 那就是 rd = 0
class EX_downstream(Downstream):
    def __init__(self):
        super().__init__()
    @downstream.combinational
    def build(self,
              EX_rd : RegArray,
              EX_result : RegArray,
              EX_rd_in : Value,
              EX_result_in : Value,
              mem_re : Value,
              mem_we : Value):
        EX_rd_in = EX_rd_in.optional(Bits(5)(0))
        EX_result_in = EX_result_in.optional(Bits(32)(0))
        EX_rd[0] <= (mem_we | mem_re).select(Bits(5)(0), EX_rd_in)
        EX_result[0] <= (mem_we | mem_re).select(UInt(32)(0), EX_result_in.bitcast(UInt(32)))


class Decoder(Module):
    def __init__(self):
        super().__init__(
            ports={"pc_addr": Port(UInt(32))}
        )
    @module.combinational
    def build(self,
              icache: SRAM,
              executor: Executor,
              reg_to_write: RegArray,
              regs: RegArray,
              ID_rd : RegArray,
              ID_is_load : RegArray,
              MEM_rd : RegArray,
              MEM_result : RegArray):
        pc_addr = self.pop_all_ports(True)
        instr = icache.dout[0]
        opcode = instr[0:6]
        funct3 = instr[12:14]
        funct7 = instr[25:31]
        log("decoder fetch pc={} instr=0x{:08x} opcode={:07b} funct3={:03b} funct7={:07b}",
            pc_addr, instr, opcode, funct3, funct7)

        decoder_result = decoder_logic(
            inst=instr, reg_to_write=reg_to_write, regs=regs,
            ID_rd=ID_rd[0], ID_is_load=ID_is_load[0],
            MEM_rd=MEM_rd[0], MEM_result=MEM_result[0]
        )
        with Condition(decoder_result.is_valid):
            executor.async_called(decoder_result=decoder_result, pc_addr=pc_addr)
        with Condition(~decoder_result.is_valid):
            log("decoder invalid instruction at pc={}: instr=0x{:08x}", pc_addr, instr)
        ID_rd_in = decoder_result.is_valid.select(
            decoder_result.rd,
            Bits(5)(0)
        )
        ID_is_load_in = decoder_result.is_valid.select(
            decoder_result.mem_read,
            Bits(1)(0)
        )
        # is_branch, pc_addr, is_valid
        return decoder_result.is_branch, pc_addr, decoder_result.is_valid, ID_rd_in, ID_is_load_in

class ID_downstream(Downstream):
    def __init__(self):
        super().__init__()
    @downstream.combinational
    def build(self,
              ID_rd : RegArray,
              ID_is_load : RegArray,
              ID_rd_in : Value,
              ID_is_load_in : Value):
        ID_rd_in = ID_rd_in.optional(Bits(5)(0))
        ID_is_load_in = ID_is_load_in.optional(Bits(1)(0))
        ID_rd[0] <= ID_rd_in
        ID_is_load[0] <= ID_is_load_in

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
        ex_downstream = EX_downstream()
        mem_downstream = Mem_downstream()
        id_downstream = ID_downstream()

        # ID 阶段得到的 rd，以及是否是 load 指令
        ID_rd = RegArray(Bits(5), 1, initializer=[0])
        ID_is_load = RegArray(Bits(1), 1, initializer=[0])

        # EX 算出来的 rd 和 result 的寄存器
        EX_rd = RegArray(Bits(5), 1, initializer=[0])
        EX_result = RegArray(UInt(32), 1, initializer=[0])

        # MEM 阶段的 rd 和 result 的寄存器
        MEM_rd = RegArray(Bits(5), 1, initializer=[0])
        MEM_result = RegArray(UInt(32), 1, initializer=[0])

        writeback.build(regs=regs, fetcher=fetcher, reg_to_write=reg_to_write)

        MEM_rd_in, MEM_result_in = memoryaccess.build(dcache=dcache, regs=regs, writeback=writeback)
        mem_downstream.build(MEM_rd=MEM_rd, MEM_result=MEM_result, MEM_rd_in=MEM_rd_in, MEM_result_in=MEM_result_in)

        is_branch, decoder_pc_reg, is_valid, ID_rd_in, ID_is_load_in = decoder.build(
            icache=icache, executor=executor, reg_to_write=reg_to_write, regs = regs,
            ID_rd=ID_rd, ID_is_load=ID_is_load,
            MEM_rd=MEM_rd, MEM_result=MEM_result
        )
        id_downstream.build(ID_rd=ID_rd, ID_is_load=ID_is_load, ID_rd_in=ID_rd_in, ID_is_load_in=ID_is_load_in)

        pc_reg, pc_addr = fetcher.build(icache=icache, decoder=decoder, pc_reg=pc_reg)

        driver.build(fecher=fetcher)

        ex_branch_taken, ex_pc_next, EX_rd_in, EX_result_in, mem_re, mem_we = executor.build(
            memoryaccess=memoryaccess, dcache=dcache,
            EX_rd=EX_rd, EX_result=EX_result,
            MEM_rd=MEM_rd, MEM_result=MEM_result
        )
        ex_downstream.build(
            EX_rd=EX_rd, EX_result=EX_result, EX_rd_in=EX_rd_in, EX_result_in=EX_result_in,
            mem_re=mem_re, mem_we=mem_we)

        fetcherimpl.build(is_branch=is_branch,
                          is_valid=is_valid,
                          pc_reg=pc_reg,
                          pc_addr=pc_addr,
                          decoder_pc_addr=decoder_pc_reg,
                          ex_is_branch=ex_branch_taken,
                          ex_pc_bypass=ex_pc_next,
                          icache=icache,
                          decoder=decoder
        )
    return sys

def main():
    import argparse

    # --sim-threshold 100 --idle-threshold 100 设置模拟器参数
    parser = argparse.ArgumentParser(description="Run CPU simulator")
    parser.add_argument("--sim-threshold", type=int, default=100, help="max simulation steps")
    parser.add_argument("--idle-threshold", type=int, default=100, help="idle cycles before stop")
    args = parser.parse_args()

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

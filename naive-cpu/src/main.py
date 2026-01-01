import os
from assassyn.frontend import *
from assassyn.backend import *
from assassyn import utils, backend
from assassyn.utils import run_simulator, run_verilator
from decoder import *
from excutor import executor_logic

class WriteBack(Module):
    def __init__(self):
        super().__init__(
            ports={
                    "rd": Port(Bits(5)),
                    "data": Port(Bits(32))
                }
        )
    @module.combinational
    def build(self, regs: RegArray, fetcher):
        rd, data = self.pop_all_ports(True)
        with Condition(rd != Bits(5)(0)):
            regs[rd] <= data.bitcast(UInt(32))
            log("writeback stage: rd = {} data = {}", rd, data)
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
            ports={"decoder_result": Port(deocder_signals)}
        )

    @module.combinational
    def build(self, regs: RegArray, pc_reg: RegArray, memoryaccess: MemoryAccess, dcache: SRAM):
        signals = self.pop_all_ports(True)
        rd_data = executor_logic(signals, regs, pc_reg, dcache)
        memoryaccess.async_called(decoder_result=signals, wdata=rd_data)


class Decoder(Module):
    def __init__(self):
        super().__init__(
            ports={"pc_addr": Port(UInt(32))}
        )
    @module.combinational
    def build(self,
              icache: SRAM,
              executor: Executor):
        pc_addr = self.pop_all_ports(True)
        instr = icache.dout[0]
        opcode = instr[0:6]
        funct3 = instr[12:14]
        funct7 = instr[25:31]
        log("decoder fetch pc={} instr=0x{:08x} opcode={:07b} funct3={:03b} funct7={:07b}",
            pc_addr, instr, opcode, funct3, funct7)

        decoder_result = decoder_logic(inst=instr)
        executor.async_called(decoder_result=decoder_result)

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

        log("fetch stage pc addr: {}", pc_addr)

        # 由于是 naive CPU，所以要取的肯定就是 pc_addr 对应的指令
        # PC 是字节地址，SRAM 按字（word）索引，需要右移2位
        word_addr = (pc_addr >> UInt(32)(2)).bitcast(UInt(32))
        icache.build(we=Bits(1)(0),
                     re=Bits(1)(1),
                     addr=word_addr,
                     wdata=Bits(32)(0))
        decoder.async_called(pc_addr=pc_addr)

        return pc_reg, pc_addr

class Driver(Module):
    def __init__(self):
        super().__init__(
            ports={}
        )
    @module.combinational
    def build(self, fetcher : Fetcher):
        is_init = RegArray(UInt(1), 1, initializer=[1])

        with Condition(is_init[0] == UInt(1)(1)):
            is_init[0] <= UInt(1)(0)
            fetcher.async_called()
            log("Naive CPU Simulation Started")
        # with Condition(is_init[0] == UInt(1)(0)):
            # log("Naive CPU Simulation Running")


current_path = os.path.dirname(os.path.abspath(__file__))
workspace = f'{current_path}/workspace/'

def build_naive_CPU(depth_log=18):
    sys = SysBuilder("Naive-CPU")
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

        writeback = WriteBack()
        memoryaccess = MemoryAccess()
        executor = Executor()
        decoder = Decoder()
        fetcher = Fetcher()
        driver = Driver()
        writeback.build(regs=regs, fetcher=fetcher)
        memoryaccess.build(dcache=dcache, regs=regs, writeback=writeback)
        decoder.build(icache=icache, executor=executor)
        pc_reg, pc_addr = fetcher.build(icache=icache, decoder=decoder, pc_reg=pc_reg)
        driver.build(fetcher=fetcher)
        executor.build(regs=regs, pc_reg=pc_reg, memoryaccess=memoryaccess, dcache=dcache)
    return sys

def main():
    import argparse

    # --sim-threshold 100 --idle-threshold 100 设置模拟器参数
    parser = argparse.ArgumentParser(description="Run Naive CPU simulator")
    parser.add_argument("--sim-threshold", type=int, default=100, help="max simulation steps")
    parser.add_argument("--idle-threshold", type=int, default=100, help="idle cycles before stop")
    args = parser.parse_args()

    sys = build_naive_CPU(depth_log = 18)
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

from assassyn.frontend import *
from assassyn.backend import *
from assassyn import utils
from assassyn.utils import run_simulator, run_verilator

class Fetcher(Module):
    def __init__(self):
        super().__init__(
            ports={}
        )
    @module.combinational
    def build(self,
              icache: SRAM):
        pc_reg = RegArray(UInt(32), 1)
        pc_addr = pc_reg[0]

        log("fecher pc addr: {}", pc_addr)

        # 由于是 naive CPU，所以要取的肯定就是 pc_addr 对应的指令
        icache.build(we=Bits(1)(0),
                     re=Bits(1)(1),
                     addr=pc_addr,
                     wdata=Bits(32)(0))
        # Fetch 阶段完成后，pc + 4，如果是跳转指令的话，在后续阶段会修改 pc_reg 的值
        pc_reg[0] <= pc_addr + UInt(32)(4)

        # 如果有 Decoder，这个时候就 async_called Decoder

        return pc_reg, pc_addr

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
            log("Naive CPU Simulation Started")
        with Condition(is_init[0] == UInt(1)(0)):
            log("Naive CPU Simulation Running")


current_path = os.path.dirname(os.path.abspath(__file__))
workspace = f'{current_path}/workspace/'

def build_naive_CPU(depth_log):
    sys = SysBuilder("Naive-CPU")
    with sys:
        icache = SRAM(width= 32,
                      depth= 1 << depth_log,
                      init_file= f"{workspace}/workload.exe")
        icache.name = "icache"
        fetcher = Fetcher()
        pc_reg, pc_addr = fetcher.build(icache=icache)
        driver = Driver()
        driver.build(fecher=fetcher)
    return sys

def main():
    sys = build_naive_CPU(depth_log = 16)
    sim,vcd = elaborate(sys=sys,
                        verbose=True,
                        verilog=True,
                        resource_base='.')
    output = run_simulator(sim)
    print("simulate output:")
    print(output)

if __name__ == "__main__":
    main()

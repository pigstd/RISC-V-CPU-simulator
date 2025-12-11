from assassyn.frontend import *
from assassyn.backend import *
from assassyn import utils
from assassyn.utils import run_simulator, run_verilator

class Driver(Module):
    def __init__(self):
        super().__init__(
            ports={}
        )
    @module.combinational
    def build(self):
        is_init = RegArray(UInt(1), 1, initializer=[1])

        with Condition(is_init[0] == UInt(1)(1)):
            is_init[0] <= UInt(1)(0)
            log("Naive CPU Simulation Started")
        with Condition(is_init[0] == UInt(1)(0)):
            log("Naive CPU Simulation Running")

def top():
    sys = SysBuilder("Naive-CPU")
    with sys:
        driver = Driver()
        driver.build()
    return sys

def main():
    sys = top()
    sim,vcd = elaborate(sys=sys, verbose=True, verilog=True)
    output = run_simulator(sim)
    print("simulate output:")
    print(output)

if __name__ == "__main__":
    main()

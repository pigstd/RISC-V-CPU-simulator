import os
import subprocess
import shutil
import sys
import json

# ================= 配置区域 =================
# 获取脚本所在目录，确保路径正确
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(SCRIPT_DIR, "src")          # 存放 C 代码的文件夹
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "test_suite")   # 输出结果的文件夹

# RISC-V 工具链前缀
RV_PREFIX = "riscv64-unknown-elf-"
# 你的电脑自带的 GCC (用于生成标准答案)
HOST_GCC  = "gcc"

# 内存布局 (根据你的 CPU 设计调整)
TEXT_ADDR = "0x00000000"
DATA_ADDR = "0x00002000"

# 模拟器默认参数
DEFAULT_SIM_THRESHOLD = 100000
DEFAULT_IDLE_THRESHOLD = 50000

# 需要 M 扩展（乘法指令）的测试用例
# 这些测试会使用 -march=rv32im 编译
M_EXTENSION_TESTS = [
    "simple_mul",
    "vector_mul_real",
    "simple_div",
    "simple_rem",
    "div_exact",
    "div_unsigned",
    "multiple",
    "div_rem_combo",
]
# ===========================================

def run_cmd(cmd, cwd=None):
    """执行命令，静默模式，出错则抛出异常"""
    try:
        subprocess.check_output(cmd, shell=True, cwd=cwd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(f"Error executing: {cmd}")
        print(e.output.decode())
        raise

def create_common_files():
    """生成通用的 start.s 和 linker.ld"""
    common_dir = os.path.join(SCRIPT_DIR, "common")
    if not os.path.exists(common_dir):
        os.makedirs(common_dir)
        
    # start.s
    with open(os.path.join(common_dir, "start.s"), "w") as f:
        f.write(f"""
.section .text
.globl _start
_start:
    lui sp, 0x20
    jal main
    ebreak
.section .text
.globl __main_loop
__main_loop:
    j __main_loop
""")

    # linker.ld
    with open(os.path.join(common_dir, "linker.ld"), "w") as f:
        f.write(f"""
OUTPUT_ARCH( "riscv" )
ENTRY( _start )
SECTIONS
{{
  . = {TEXT_ADDR};
  .text : {{ *(.text.init) *(.text) }}
  . = {DATA_ADDR};
  .data : {{ *(.data) *(.rodata*) *(.sdata) }}
  .bss : {{ *(.bss) *(.sbss) }}
}}
""")

def generate_ans(c_path, case_dir, case_name):
    """【关键】用本机 GCC 运行代码，生成标准答案 .ans"""
    host_exe = os.path.join(case_dir, "host_runner")
    
    # 1. 编译 (x86/host)
    run_cmd(f"{HOST_GCC} {c_path} -o {host_exe} -O0")
    
    # 2. 运行并获取 exit code
    try:
        # 运行编译出的程序
        ret_code = subprocess.call(host_exe)
        # 注意：Linux/Unix 的 exit code 通常是 8-bit (0-255)。
        # 如果你的测试结果超过 255，这种方法需要修改（改用打印到 stdout）。
        
        ans_file = os.path.join(case_dir, f"{case_name}.ans")
        with open(ans_file, "w") as f:
            # 将结果写入 .ans 文件，比如 "5050"
            f.write(str(ret_code))
            
    finally:
        if os.path.exists(host_exe):
            os.remove(host_exe)

def generate_riscv_files(c_path, case_dir, case_name):
    """生成 RISC-V 的 .exe (指令) 和 .data (数据)"""
    elf_file = os.path.join(case_dir, f"{case_name}.elf")
    linker = os.path.join(SCRIPT_DIR, "common", "linker.ld")
    start_s = os.path.join(SCRIPT_DIR, "common", "start.s")
    
    # 根据测试用例选择架构：M 扩展测试使用 rv32im，其他使用 rv32i
    if case_name in M_EXTENSION_TESTS:
        march = "rv32im"
    else:
        march = "rv32i"
    
    # 1. 编译 RISC-V ELF
    run_cmd(f"{RV_PREFIX}gcc -march={march} -mabi=ilp32 -O0 -nostdlib -T {linker} {start_s} {c_path} -o {elf_file}")
    
    # 2. 反汇编 (可选，用于调试)
    run_cmd(f"{RV_PREFIX}objdump -d {elf_file} > {os.path.join(case_dir, case_name + '.asm')}")
    
    # 3. 提取指令 (.exe)
    bin_inst = os.path.join(case_dir, "temp_inst.bin")
    run_cmd(f"{RV_PREFIX}objcopy -O binary --only-section=.text {elf_file} {bin_inst}")
    run_cmd(f"hexdump -v -e '1/4 \"%08x\" \"\\n\"' {bin_inst} > {os.path.join(case_dir, case_name + '.exe')}")
    
    # 4. 提取数据 (.data)
    bin_data = os.path.join(case_dir, "temp_data.bin")
    run_cmd(f"{RV_PREFIX}objcopy -O binary --only-section=.data {elf_file} {bin_data}")
    
    data_file = os.path.join(case_dir, case_name + '.data')
    if os.path.exists(bin_data) and os.path.getsize(bin_data) > 0:
        run_cmd(f"hexdump -v -e '1/4 \"%08x\" \"\\n\"' {bin_data} > {data_file}")
    else:
        # 空数据
        open(data_file, 'w').close()

    # 清理中间文件
    for f in [elf_file, bin_inst, bin_data]:
        if os.path.exists(f): os.remove(f)

def generate_config(case_dir, case_name):
    """生成测试配置文件 .config.json"""
    config = {
        "name": case_name,
        "memory": {
            "text_base": int(TEXT_ADDR, 16),
            "data_base": int(DATA_ADDR, 16),
        },
        "simulator": {
            "sim_threshold": DEFAULT_SIM_THRESHOLD,
            "idle_threshold": DEFAULT_IDLE_THRESHOLD,
        }
    }
    config_file = os.path.join(case_dir, f"{case_name}.config.json")
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

def main():
    if not os.path.exists(SOURCE_DIR):
        print(f"Error: Source directory '{SOURCE_DIR}' not found.")
        return

    # 清理并重建输出目录
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)
    
    create_common_files()
    
    # 扫描所有 .c 文件
    files = [f for f in os.listdir(SOURCE_DIR) if f.endswith(".c")]
    print(f"Found {len(files)} test cases in '{SOURCE_DIR}'...")
    
    for f in files:
        case_name = os.path.splitext(f)[0]
        c_path = os.path.abspath(os.path.join(SOURCE_DIR, f))
        case_dir = os.path.join(OUTPUT_DIR, case_name)
        
        os.makedirs(case_dir)
        
        print(f"Processing: {case_name} ...", end="", flush=True)
        try:
            # 1. 生成 .ans (运行在本机)
            generate_ans(c_path, case_dir, case_name)
            # 2. 生成 .exe/.data (交叉编译)
            generate_riscv_files(c_path, case_dir, case_name)
            # 3. 生成 .config.json (模拟器配置)
            generate_config(case_dir, case_name)
            print(" Done.")
        except Exception as e:
            print(f" Failed! {e}")

    print("\nBatch build complete!")

if __name__ == "__main__":
    main()
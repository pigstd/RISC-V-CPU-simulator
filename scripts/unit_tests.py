import sys
import os
import re
import importlib
import io
import contextlib
import functools

# ================= 路径配置 =================
# 脚本位于 scripts/，我们需要向上找到根目录，再找到 src 和 unit_tests
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
TEST_DIR = os.path.join(PROJECT_ROOT, 'unit_tests')

# 将 src 和 unit_tests 加入 python 路径，以便 import
sys.path.insert(0, SRC_DIR)
sys.path.insert(0, TEST_DIR)

# ================= 导入模块 =================
# 将 unit_tests 目录加入路径并导入测试用例与仿真工具
try:
    sys.path.insert(0, TEST_DIR)
    import test_cases
    from main import build_CPU, workspace as WORKSPACE_PATH
    from assassyn import backend
    from assassyn.utils import run_simulator
except ImportError as e:
    print(f"❌ 环境配置错误: {e}")
    print(f"请确保 assassyn 框架已安装，且 {SRC_DIR} 下有 main.py")
    sys.exit(1)

# ================= 工具函数 =================

def write_workload(instructions):
    """
    将指令列表写入 src/workspace/workload.exe
    格式：每行一个 8 字符宽的 16 进制字符串
    """
    # 确保目录存在
    os.makedirs(WORKSPACE_PATH, exist_ok=True)
    file_path = os.path.join(WORKSPACE_PATH, "workload.exe")
    
    with open(file_path, "w") as f:
        for instr in instructions:
            # 这里的 instr 是 int，转成 00000013 这种格式
            f.write(f"{instr:08x}\n")
    return file_path

def parse_log_and_get_regs(log_output):
    """
    解析仿真日志，模拟寄存器的最终状态。
    关注日志行： 'writeback stage: rd = 1 data = 5'
    """
    # 模拟一个寄存器堆
    regs = {i: 0 for i in range(32)}
    
    # 正则表达式匹配日志
    # 假设日志格式为: writeback stage: rd = 1 data = 5
    # 如果 assassyn 输出的是 Bit(5)(1) 这种格式，需要调整正则
    wb_pattern = re.compile(r"writeback stage: rd = (\d+) data = (\d+)")
    
    for line in log_output.splitlines():
        # 去除颜色代码（如果有）和空白
        clean_line = line.strip()
        
        match = wb_pattern.search(clean_line)
        if match:
            rd = int(match.group(1))
            data = int(match.group(2))
            
            # x0 永远是 0，不写入
            if rd != 0:
                regs[rd] = data
                
    return regs

def run_single_test(case_name, case_func):
    print(f"Testing [{case_name}]...", end=" ", flush=True)
    
    # 1. 准备数据
    instrs, expected_regs = case_func()
    
    # 2. 写入 workload.exe
    write_workload(instrs)
    
    # 3. 构建并运行仿真
    # 注意：这里我们调用 build_CPU 重新构建系统以加载新的 workload
    try:
        # 使用 stdout=False 防止仿真日志直接打印到终端干扰测试结果
        # 需要确保你的 run_simulator 支持捕获输出返回
        sys_design = build_CPU(depth_log=18)
        
        # 配置仿真参数 (步数可以给大一点，防止复杂程序跑不完)
        cfg = backend.config(
            resource_base=SRC_DIR, # 资源根目录设为 src
            verilog=False,         # 单元测试不需要生成 Verilog，跑仿真即可
            verbose=True,          # 必须开启 verbose 才能看到 log
            sim_threshold=1000,    # 最大步数
            idle_threshold=20      # 空闲停止
        )
        
        # 你的 main.py 里 run_simulator 返回了 output 字符串
        # elaborate 过程中会产生大量编译/构建输出，很多是由子进程直接写到 fd，
        # 所以需要重定向底层文件描述符以彻底屏蔽
        @contextlib.contextmanager
        def _suppress_subprocess_output():
            devnull_fd = os.open(os.devnull, os.O_RDWR)
            try:
                saved_stdout = os.dup(1)
                saved_stderr = os.dup(2)
                os.dup2(devnull_fd, 1)
                os.dup2(devnull_fd, 2)
                yield
            finally:
                os.dup2(saved_stdout, 1)
                os.dup2(saved_stderr, 2)
                os.close(saved_stdout)
                os.close(saved_stderr)
                os.close(devnull_fd)

        # 临时静默 Rust 编译器的警告信息
        old_rustflags = os.environ.get('RUSTFLAGS')
        os.environ['RUSTFLAGS'] = (old_rustflags + ' -Awarnings') if old_rustflags else '-Awarnings'
        try:
            with _suppress_subprocess_output():
                sim, _ = backend.elaborate(sys=sys_design, **cfg)
                log_output = run_simulator(sim)
        finally:
            if old_rustflags is None:
                os.environ.pop('RUSTFLAGS', None)
            else:
                os.environ['RUSTFLAGS'] = old_rustflags
        
    except Exception as e:
        print(f"\n❌ Simulation Crash: {e}")
        return False

    # 4. 验证结果
    final_regs = parse_log_and_get_regs(log_output)
    
    all_passed = True
    error_msgs = []
    
    for reg_idx, expected_val in expected_regs.items():
        actual_val = final_regs.get(reg_idx, 0)
        # 将无符号整数处理一下，防止负数补码差异 (假设是32位无符号对比)
        if actual_val != expected_val:
            all_passed = False
            error_msgs.append(f"x{reg_idx}: expected {expected_val}, got {actual_val}")

    if all_passed:
        print("✅ PASS")
        return True
    else:
        print("❌ FAIL")
        for msg in error_msgs:
            print(f"   -> {msg}")
        # 如果失败，把关键的 writeback 日志打出来方便调试
        print("   -> Recent Writebacks:")
        wb_lines = [l for l in log_output.splitlines() if "writeback" in l][-5:]
        for l in wb_lines:
            print(f"      {l}")
        return False

# ================= 主程序 =================

if __name__ == "__main__":
    print("================ RISC-V CPU Simulation Tests ================")
    
    tests = [
        (name, func) 
        for name, func in vars(test_cases).items() 
        if name.startswith('case_') and callable(func)
    ]
    
    passed = 0
    for name, func in tests:
        if run_single_test(name, func):
            passed += 1
            
    print("=============================================================")
    print(f"Summary: {passed}/{len(tests)} passed.")
    
    if passed != len(tests):
        sys.exit(1)
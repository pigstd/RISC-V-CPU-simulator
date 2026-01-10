import pathlib
import subprocess

from asm_utils import ASM


def write_workload(instrs, workload_path):
    lines = [f"{word & 0xFFFFFFFF:08x}" for word in instrs]
    workload_path.write_text("\n".join(lines) + "\n")


def run_sim_and_collect_log(instrs, sim_threshold=50, idle_threshold=20, data_words=None):
    repo = pathlib.Path(__file__).resolve().parents[1]
    workload = repo / "Tomasulo" / "src" / "workspace" / "workload.exe"
    data_mem = repo / "Tomasulo" / "src" / "workspace" / "data.mem"
    log_path = repo / "Tomasulo" / "src" / "workspace" / "log"

    write_workload(instrs, workload)
    if data_words is None:
        data_mem.write_text("")  # 清空数据区
    else:
        lines = [f"{w & 0xFFFFFFFF:08x}" for w in data_words]
        data_mem.write_text("\n".join(lines) + "\n")
    if log_path.exists():
        log_path.unlink()

    cmd = [
        "python",
        "Tomasulo/src/main.py",
        "--sim-threshold",
        str(sim_threshold),
        "--idle-threshold",
        str(idle_threshold),
    ]
    result = subprocess.run(cmd, cwd=repo, capture_output=True, text=True)
    assert result.returncode == 0, f"sim exit={result.returncode}, stdout={result.stdout}, stderr={result.stderr}"
    assert log_path.exists(), "仿真未生成日志"
    return log_path.read_text()


def test_simple_add_then_ebreak():
    """
    构造一段最小程序：
      addi x1, x0, 5
      add  x2, x1, x1
      ebreak
      nop
    把机器码写入 Tomasulo/src/workspace/workload.exe，运行主程序，期望正常退出。
    """
    instrs = [
        ASM.addi(1, 0, 5),
        ASM.add(2, 1, 1),
        ASM.ebreak(),
        ASM.nop(),
    ]
    log_text = run_sim_and_collect_log(instrs, sim_threshold=20, idle_threshold=10)
    # 需要看到 ebreak 译码 + ALU 开火 + 提交到 syscall 才算通过
    assert "Decoded I-type instruction: ebreak" in log_text, "log 未看到 ebreak 译码"
    assert "RS fire ALU" in log_text, "RS 从未向 ALU 发送指令，流水线未前进"
    assert "commit: hit syscall/ebreak" in log_text, "未看到提交阶段处理 ebreak，可能卡住未提交"

    # 校验 x2 = x1 + x1 = 10
    assert "commit: can_commit=1 head=0 is_store=0 rd=1 value=5" in log_text, "x1 写回结果异常"
    assert "commit: can_commit=1 head=1 is_store=0 rd=2 value=10" in log_text, "x2 写回结果不是 10"


def test_long_add_sub_chain():
    """
    更长的加/减数据相关链路，验证多个写回以及 ebreak 触发。
    目标寄存器结果：
      x1=3, x2=7, x3=10, x4=13, x5=6, x6=16
    """
    instrs = [
        ASM.addi(1, 0, 3),
        ASM.addi(2, 0, 7),
        ASM.add(3, 1, 2),   # 10
        ASM.add(4, 3, 1),   # 13
        ASM.sub(5, 4, 2),   # 6
        ASM.add(6, 5, 3),   # 16
        ASM.ebreak(),
    ]

    log_text = run_sim_and_collect_log(instrs, sim_threshold=200, idle_threshold=100)

    assert "Decoded I-type instruction: ebreak" in log_text, "log 未看到 ebreak 译码"
    assert "commit: hit syscall/ebreak" in log_text, "commit 阶段未处理 ebreak"
    for rd, val in {1: 3, 2: 7, 3: 10, 4: 13, 5: 6, 6: 16}.items():
        assert f"commit: writeback rd={rd} value={val}" in log_text, f"rd={rd} 写回值错误"


def test_branch_stop_and_redirect():
    """
    分支发射后应 stop 取指，ALU 计算出 next_pc 后由 start_signal 重启。
    beq 预期跳过 addi x3,0,111，直接执行后面的 addi x3,0,222。
    """
    instrs = [
        ASM.addi(1, 0, 1),      # x1 = 1
        ASM.addi(2, 0, 2),      # x2 = 2
        ASM.beq(1, 1, 8),       # 跳过下一条
        ASM.addi(3, 0, 111),    # 被跳过
        ASM.addi(3, 0, 222),    # 命中
        ASM.ebreak(),
    ]
    log_text = run_sim_and_collect_log(instrs, sim_threshold=200, idle_threshold=100)

    assert "Decoded B-type instruction: beq" in log_text, "log 未看到 beq 译码"
    assert "commit: hit syscall/ebreak" in log_text, "未看到 ebreak 提交"
    assert "commit: writeback rd=3 value=222" in log_text, "跳转后 x3 写回不是 222"
    assert "commit: writeback rd=3 value=111" not in log_text, "分支未正确跳过 x3=111 的写回"

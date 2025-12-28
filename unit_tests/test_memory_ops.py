from asm_utils import ASM
from test_simple_ebreak import run_sim_and_collect_log
import pytest


def test_sw_then_lw_roundtrip():
    """
    基础加载：直接从 data.mem 预置值读取。
    通过日志检查 lw 译码、ebreak 提交，以及 x3 写回正确值。
    """
    instrs = [
        ASM.lui(1, 0x2000),   # x1 = data_base
        ASM.lw(3, 1, 0),      # x3 = [x1+0]
        ASM.ebreak(),
    ]
    log_text = run_sim_and_collect_log(instrs, sim_threshold=120, idle_threshold=80, data_words=[123])

    assert "Decoded I-type instruction: lw" in log_text, "log 未看到 lw 译码"
    assert "commit: hit syscall/ebreak" in log_text, "未看到 ebreak 提交"
    assert "commit: writeback rd=3 value=123" in log_text, "lw 回读结果不是 123"


def test_store_load_two_offsets():
    """
    连续两个地址回读，验证两次 lw 取数正确。
    """
    instrs = [
        ASM.lui(1, 0x2000),    # base
        ASM.lw(4, 1, 0),       # x4 = [base+0]
        ASM.lw(5, 1, 4),       # x5 = [base+4]
        ASM.ebreak(),
    ]
    log_text = run_sim_and_collect_log(instrs, sim_threshold=120, idle_threshold=80, data_words=[0x111, 0x222])

    assert "Decoded I-type instruction: lw" in log_text, "log 未看到 lw 译码"
    assert "commit: hit syscall/ebreak" in log_text, "未看到 ebreak 提交"
    assert "commit: writeback rd=4 value=273" in log_text, "x4 回读值不是 0x111"
    assert "commit: writeback rd=5 value=546" in log_text, "x5 回读值不是 0x222"


def test_sw_then_lw_same_cycle_dependency():
    """
    构造 sw 后紧跟 lw 读取同一地址，验证数据回写/取数路径。
    期望：store 将 addi 结果写入 [base]，紧随的 lw 读回同一值到 x3。
    """
    instrs = [
        ASM.lui(1, 0x2000),           # base = data_base
        ASM.lui(2, 0xdeadb000),       # x2 = 0xdeadb000
        ASM.addi(2, 2, 0x0eef),       # x2 = 0xdeadaeef (addi 12-bit 立即数符号扩展)
        ASM.sw(1, 2, 0),              # store x2 -> [base]
        ASM.lw(3, 1, 0),              # load back to x3
        ASM.ebreak(),
    ]
    log_text = run_sim_and_collect_log(instrs, sim_threshold=400, idle_threshold=200)

    assert "commit: hit syscall/ebreak" in log_text, "未看到 ebreak 提交"
    assert "commit: writeback rd=3 value=3735924463" in log_text, "lw 未读回 addi 的结果 0xdeadaeef"

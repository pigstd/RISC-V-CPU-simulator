from asm_utils import ASM
from test_simple_ebreak import run_sim_and_collect_log


def test_lui_and_auipc_basic():
    """
    验证 U-type 指令写回：
      - LUI: rd = imm << 12
      - AUIPC: rd = pc + (imm << 12)
    """
    instrs = [
        ASM.lui(1, 0x10000),     # x1 = 0x0001_0000
        ASM.auipc(2, 0x20000),   # pc=0x4 -> x2 = 0x4 + 0x0002_0000 = 0x20004
        ASM.ebreak(),
    ]
    log_text = run_sim_and_collect_log(instrs, sim_threshold=100, idle_threshold=50)

    assert "commit: hit syscall/ebreak" in log_text, "未看到 ebreak 提交"
    expect = {1: 0x00010000, 2: 0x00020004}
    for rd, val in expect.items():
        assert f"commit: writeback rd={rd} value={val}" in log_text, f"rd={rd} 写回非 {val:#x}"

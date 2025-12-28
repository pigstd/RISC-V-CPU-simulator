from asm_utils import ASM
from test_simple_ebreak import run_sim_and_collect_log


def test_jal_and_jalr_jump_and_link():
    """
    覆盖 jal + jalr：
      - jal 跳过一条指令，rd 写回 link(pc+4)
      - jalr 跳到寄存器 + imm 的目标，rd 写回 link(pc+4)
    预期：
      x2=222（跳过 x2=111），x4=333（跳过 x4=111），x5=8（jal link），x6=20（jalr link）
    """
    instrs = [
        ASM.addi(1, 0, 24),    # x1 = 24 (jalr 基址)
        ASM.jal(5, 8),         # 跳过下一条，rd=x5=pc+4=8
        ASM.addi(2, 0, 111),   # 应跳过
        ASM.addi(2, 0, 222),   # 命中
        ASM.jalr(6, 1, 4),     # 目标 = 24+4=28，rd=x6=pc+4=20
        ASM.addi(4, 0, 111),   # 应跳过
        ASM.addi(3, 0, 0),     # 填充
        ASM.addi(4, 0, 333),   # 命中
        ASM.ebreak(),
    ]

    log_text = run_sim_and_collect_log(instrs, sim_threshold=300, idle_threshold=150)

    assert "Decoded J-type instruction: jal" in log_text, "log 未看到 jal 译码"
    assert "Decoded I-type instruction: jalr" in log_text, "log 未看到 jalr 译码"
    assert "commit: hit syscall/ebreak" in log_text, "未看到 ebreak 提交"

    expect = {
        2: 222,
        4: 333,
        5: 8,
        6: 20,
    }
    for rd, val in expect.items():
        assert f"commit: writeback rd={rd} value={val}" in log_text, f"rd={rd} 写回不为 {val}"

    # 确保被跳过的指令未写回
    assert "commit: writeback rd=2 value=111" not in log_text, "jal 未跳过 x2=111"
    assert "commit: writeback rd=4 value=111" not in log_text, "jalr 未跳过 x4=111"

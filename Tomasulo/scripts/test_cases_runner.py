import sys
import pathlib

import pytest

# 确保能复用根目录下已有的测试工具与指令编码器
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
UNIT_TEST_DIR = REPO_ROOT / "unit_tests"
if str(UNIT_TEST_DIR) not in sys.path:
    sys.path.insert(0, str(UNIT_TEST_DIR))

from unit_tests.test_simple_ebreak import run_sim_and_collect_log
from unit_tests.test_cases import (
    case_hazard_war,
    case_loop_sum,
    case_alu_ops,
    case_mem_rw,
    case_branches_and_jumps,
)
from unit_tests.asm_utils import ASM


def _run_case(case_fn, name: str, sim_threshold: int = 300, idle_threshold: int = 150):
    instrs, expected = case_fn()
    # 为每个用例追加 ebreak 收尾
    instrs = list(instrs) + [ASM.ebreak()]
    log_text = run_sim_and_collect_log(instrs, sim_threshold=sim_threshold, idle_threshold=idle_threshold)
    assert "commit: hit syscall/ebreak" in log_text, f"{name}: 未看到 ebreak 提交"
    for rd, val in expected.items():
        assert f"commit: writeback rd={rd} value={val}" in log_text, f"{name}: rd={rd} 写回非 {val}"
    return log_text


@pytest.mark.parametrize(
    "case_fn,name,sim,idle",
    [
        (case_hazard_war, "hazard_war", 200, 120),
        (case_loop_sum, "loop_sum", 400, 200),
        (case_alu_ops, "alu_ops", 250, 150),
        (case_mem_rw, "mem_rw", 250, 150),
        (case_branches_and_jumps, "branches_and_jumps", 400, 200),
    ],
)
def test_cases_suite(case_fn, name, sim, idle):
    _run_case(case_fn, name, sim_threshold=sim, idle_threshold=idle)

#!/usr/bin/env python3
"""
Tomasulo 専用测试脚本：复制测试用例到 Tomasulo/src/workspace/ 后运行仿真，
便于查看 workspace/log 调试。默认不跑 verilator。
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
TEST_SUITE_DIR = REPO_ROOT / "test" / "test_suite"
WORKSPACE_DIR = SCRIPT_DIR / "src" / "workspace"
SIM_MODULE = "Tomasulo.src.main"

# 匹配 writeback a0 的日志
LOG_PATTERN = re.compile(r"writeback stage: rd = ([0-9a-fA-Fx]+) data = ([0-9a-fA-Fx]+)")


def discover_tests():
    tests = []
    if TEST_SUITE_DIR.exists():
        for td in sorted(TEST_SUITE_DIR.iterdir()):
            if td.is_dir():
                exe = td / f"{td.name}.exe"
                ans = td / f"{td.name}.ans"
                if exe.exists() and ans.exists():
                    tests.append(td.name)
    return tests


def read_config(config_file: Path):
    default = {
        "memory": {"text_base": 0x0, "data_base": 0x2000},
        "simulator": {"sim_threshold": 10000, "idle_threshold": 5000},
    }
    if config_file.exists():
        try:
            return json.loads(config_file.read_text())
        except json.JSONDecodeError:
            return default
    return default


def read_expected(ans_file: Path):
    if ans_file.exists():
        content = ans_file.read_text().strip()
        if content:
            return int(content)
    return None


def extract_a0(log_text: str):
    vals = []
    for rd_str, data_str in LOG_PATTERN.findall(log_text):
        try:
            rd = int(rd_str, 0)
            if rd == 10:
                vals.append(int(data_str, 0))
        except ValueError:
            continue
    return vals[-1] if vals else None


def run_one(name: str, sim_threshold=None, idle_threshold=None, verbose=False):
    td = TEST_SUITE_DIR / name
    files = {
        "exe": td / f"{name}.exe",
        "data": td / f"{name}.data",
        "ans": td / f"{name}.ans",
        "config": td / f"{name}.config.json",
    }
    if not files["exe"].exists() or not files["ans"].exists():
        return False, f"missing exe/ans for {name}"

    config = read_config(files["config"])
    if sim_threshold is None:
        sim_threshold = config.get("simulator", {}).get("sim_threshold", 10000)
    if idle_threshold is None:
        idle_threshold = config.get("simulator", {}).get("idle_threshold", 5000)
    data_base = config.get("memory", {}).get("data_base", 0x2000)
    expected = read_expected(files["ans"])
    if expected is None:
        return False, f"cannot read expected for {name}"

    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(files["exe"], WORKSPACE_DIR / "workload.exe")
    if files["data"].exists() and files["data"].stat().st_size > 0:
        shutil.copyfile(files["data"], WORKSPACE_DIR / "data.mem")
    else:
        (WORKSPACE_DIR / "data.mem").write_text("")
    (WORKSPACE_DIR / "expected").write_text(str(expected))

    cmd = [
        sys.executable,
        "-m",
        SIM_MODULE,
        "--sim-threshold",
        str(sim_threshold),
        "--idle-threshold",
        str(idle_threshold),
        "--data-base",
        hex(data_base),
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return False, "timeout"

    log_text = proc.stdout
    (WORKSPACE_DIR / "log").write_text(log_text)
    if verbose and proc.stderr:
        (WORKSPACE_DIR / "stderr").write_text(proc.stderr)

    if proc.returncode != 0:
        return False, f"sim exit {proc.returncode}"

    sim_a0 = extract_a0(log_text)
    if sim_a0 is None:
        return False, "no a0 writeback found"
    if sim_a0 != expected:
        return False, f"a0 mismatch: got {sim_a0}, expected {expected}"
    return True, f"a0={sim_a0} (expected {expected})"


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run Tomasulo tests (no verilator)")
    parser.add_argument("tests", nargs="*", help="tests to run, default all")
    parser.add_argument("-v", "--verbose", action="store_true", help="dump stderr to workspace")
    parser.add_argument("--sim-threshold", type=int, default=None)
    parser.add_argument("--idle-threshold", type=int, default=None)
    args = parser.parse_args()

    all_tests = discover_tests()
    targets = args.tests or all_tests
    if not targets:
        print("No tests found in test/test_suite")
        return

    print(f"Running {len(targets)} test(s)...\n")
    passed = 0
    for t in targets:
        if t not in all_tests:
            print(f"[SKIP] {t} (not found)")
            continue
        ok, msg = run_one(
            t,
            sim_threshold=args.sim_threshold,
            idle_threshold=args.idle_threshold,
            verbose=args.verbose,
        )
        status = "PASS" if ok else "FAIL"
        print(f"{t:<20} {status} {msg}")
        if ok:
            passed += 1
    print(f"\nSummary: {passed}/{len(targets)} passed")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Batch-run prebuilt workloads against the naive CPU simulator and check a0.

Usage:
    python naive-cpu/test/run_workloads.py            # run all known cases
    python naive-cpu/test/run_workloads.py fib sum    # run selected cases
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
# Prefer per-repo workloads, fall back to test suites and naive-cpu workspace
WORKLOAD_DIR = REPO_ROOT / "test" / "my_tests" / "workloads"
if not WORKLOAD_DIR.exists():
    WORKLOAD_DIR = REPO_ROOT / "test" / "test_suite"
if not WORKLOAD_DIR.exists():
    WORKLOAD_DIR = REPO_ROOT / "naive-cpu" / "src" / "workspace"
WORKSPACE_DIR = REPO_ROOT / "naive-cpu" / "src" / "workspace"
SIM_ENTRY = REPO_ROOT / "naive-cpu" / "src" / "main.py"

# Expected a0 values for each workload
EXPECTED = {
    "simple_add": 15,
    "loop_sum": 55,
    "fib_reg": 55,
    "fib": 55,
    "sort": 15,
    "factorial": 120,
    "sum": 55,
    "bitcount": 5,
    "max": 9,
    "reverse": 5,
    "shift_test": 4,
}

LOG_PATTERN = re.compile(r"writeback stage: rd = ([0-9a-fA-Fx]+) data = ([0-9a-fA-Fx]+)")


def locate_workload(name: str):
    # Prefer per-test subfolder, fallback to flat layout for compatibility
    candidates = []
    # test/<name>/<name>.exe + .data
    candidates.append((WORKLOAD_DIR / name / f"{name}.exe", WORKLOAD_DIR / name / f"{name}.data"))
    # flat: <name>.exe + <name>.data
    candidates.append((WORKLOAD_DIR / f"{name}.exe", WORKLOAD_DIR / f"{name}.data"))
    # common naming: workload.exe + data.mem inside naive workspace
    candidates.append((WORKLOAD_DIR / f"{name}.exe", WORKLOAD_DIR / "data.mem"))
    candidates.append((WORKLOAD_DIR / f"{name}.exe", WORKLOAD_DIR / f"{name}.mem"))
    # fallback: generic workload.exe + data.mem in workspace dir
    candidates.append((WORKLOAD_DIR / "workload.exe", WORKLOAD_DIR / "data.mem"))

    for exe, data in candidates:
        if exe.exists() and data.exists():
            return exe, data

    # As a last resort, search recursively for matching exe and data files
    exe_paths = list(WORKLOAD_DIR.rglob(f"{name}.exe")) if WORKLOAD_DIR.exists() else []
    for exe in exe_paths:
        data_candidates = [exe.with_suffix('.data'), exe.with_suffix('.mem'), exe.parent / 'data.mem']
        for d in data_candidates:
            if d.exists():
                return exe, d

    return None, None


def run_one(name: str, sim_threshold: int = 500000, idle_threshold: int = 500000):
    exe, data = locate_workload(name)
    if exe is None or data is None:
        return False, f"missing workload files for {name}"

    shutil.copyfile(exe, WORKSPACE_DIR / "workload.exe")
    shutil.copyfile(data, WORKSPACE_DIR / "data.mem")

    proc = subprocess.run(
        [
            sys.executable,
            str(SIM_ENTRY),
            "--sim-threshold",
            str(sim_threshold),
            "--idle-threshold",
            str(idle_threshold),
        ],
        capture_output=True,
        text=True,
    )

    if proc.returncode != 0:
        return False, f"simulator exited with {proc.returncode}\n{proc.stderr}"

    log_file = WORKSPACE_DIR / "log"
    if log_file.exists():
        log_text = log_file.read_text()
    else:
        log_text = proc.stdout

    matches = []
    for rd_str, data_str in LOG_PATTERN.findall(log_text):
        try:
            rd_val = int(rd_str, 0)
        except ValueError:
            continue
        if rd_val == 10:
            matches.append(int(data_str, 0))

    if not matches:
        return False, "no a0 writeback found in log"

    last_val = matches[-1]
    expected = EXPECTED.get(name)
    if expected is None:
        return False, f"no expected value set for {name}"

    if last_val != expected:
        return False, f"a0 mismatch: got {last_val}, expected {expected}"

    return True, f"a0={last_val}"


def main():
    targets = sys.argv[1:] or sorted(EXPECTED.keys())
    passed = 0
    for name in targets:
        ok, msg = run_one(name)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}: {msg}")
        passed += int(ok)

    print(f"\nSummary: {passed}/{len(targets)} passed")
    if passed != len(targets):
        sys.exit(1)


if __name__ == "__main__":
    main()

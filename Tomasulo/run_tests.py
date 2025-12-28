#!/usr/bin/env python3
"""
Run test cases in test/test_suite against the Tomasulo simulator (Python simulator only).

Test layout (same as scripts/run_tests.py for the 5-stage CPU):
- <name>.exe   : instruction memory hex file
- <name>.data  : data memory hex file (may be empty or missing)
- <name>.ans   : expected a0 value (decimal)
- <name>.asm   : disassembly for reference
- <name>.config.json : optional config with data_base / sim thresholds

Usage:
    python Tomasulo/run_tests.py               # run all tests
    python Tomasulo/run_tests.py loop_sum max  # run selected tests
    python Tomasulo/run_tests.py --list        # list available tests
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
TEST_SUITE_DIR = REPO_ROOT / "test" / "test_suite"
WORKSPACE_DIR = SCRIPT_DIR / "src" / "workspace"
SIM_ENTRY = SCRIPT_DIR / "src" / "main.py"

WORKLOAD_FILE = WORKSPACE_DIR / "workload.exe"
DATA_FILE = WORKSPACE_DIR / "data.mem"
LOG_FILE = WORKSPACE_DIR / "log"

# Patterns for extracting basic stats from simulator log
CYCLE_PATTERN = re.compile(r"Cycle @(\d+(?:\.\d+)?)")
FETCH_PATTERN = re.compile(r"fetcherimpl: fetch_pc=", re.IGNORECASE)
# 统一统计提交：匹配 commit: retire rob=... rd=... is_store=... value=...
COMMIT_PATTERN = re.compile(
    r"commit: retire rob=\d+\s+pc=0x[0-9a-fA-F]+\s+rd=(\d+)\s+is_store=\d+\s+value=0x([0-9a-fA-F]+)",
    re.IGNORECASE,
)


def discover_tests():
    """Return a sorted list of available test names."""
    tests = []
    if TEST_SUITE_DIR.exists():
        for entry in sorted(TEST_SUITE_DIR.iterdir()):
            if entry.is_dir():
                name = entry.name
                exe_file = entry / f"{name}.exe"
                ans_file = entry / f"{name}.ans"
                if exe_file.exists() and ans_file.exists():
                    tests.append(name)
    return tests


def get_test_files(name: str) -> dict:
    """Return paths to the files for a given test name."""
    base = TEST_SUITE_DIR / name
    return {
        "exe": base / f"{name}.exe",
        "data": base / f"{name}.data",
        "ans": base / f"{name}.ans",
        "asm": base / f"{name}.asm",
        "config": base / f"{name}.config.json",
    }


def read_config(config_file: Path) -> dict:
    """Load optional config file; fall back to defaults."""
    default = {
        "memory": {"data_base": 0x2000},
        "simulator": {"sim_threshold": 10000, "idle_threshold": 5000},
    }
    if config_file.exists():
        try:
            with config_file.open() as f:
                loaded = json.load(f)
            # Shallow-merge with defaults
            for section, values in default.items():
                if section in loaded and isinstance(loaded[section], dict):
                    merged = values.copy()
                    merged.update(loaded[section])
                    loaded[section] = merged
                else:
                    loaded[section] = values
            return loaded
        except json.JSONDecodeError:
            pass
    return default


def read_expected(ans_file: Path):
    """Read expected a0 value (int) from .ans file."""
    if ans_file.exists():
        content = ans_file.read_text().strip()
        if content:
            try:
                return int(content)
            except ValueError:
                return None
    return None


def extract_stats(log_text: str) -> dict:
    """Extract simple stats from simulator log."""
    cycles = [float(c) for c in CYCLE_PATTERN.findall(log_text)]
    commits = COMMIT_PATTERN.findall(log_text)
    fetches = FETCH_PATTERN.findall(log_text)
    stats = {
        "cycles": int(cycles[-1]) if cycles else 0,
        "commits": len(commits),
        "fetches": len(fetches),
    }
    return stats


def extract_a0(log_text: str):
    """Extract the last committed a0 (x10) value from log."""
    a0_vals = []
    for rd_str, val_str in COMMIT_PATTERN.findall(log_text):
        try:
            rd = int(rd_str, 0)
            if rd == 10:
                a0_vals.append(int(val_str, 16))
        except ValueError:
            continue
    return a0_vals[-1] if a0_vals else None


def run_test(name: str, sim_threshold: int = None, idle_threshold: int = None, verbose: bool = False):
    """Run one test; returns (ok, message, stats)."""
    files = get_test_files(name)
    stats = {"cycles": 0, "commits": 0, "fetches": 0}

    if not files["exe"].exists():
        return False, f"missing {name}.exe", stats
    if not files["ans"].exists():
        return False, f"missing {name}.ans", stats

    config = read_config(files["config"])
    if sim_threshold is None:
        sim_threshold = config.get("simulator", {}).get("sim_threshold", 10000)
    if idle_threshold is None:
        idle_threshold = config.get("simulator", {}).get("idle_threshold", 5000)
    data_base = config.get("memory", {}).get("data_base", 0x2000)

    expected = read_expected(files["ans"])
    if expected is None:
        return False, f"cannot parse expected value from {name}.ans", stats

    # Stage memory files into Tomasulo workspace
    shutil.copyfile(files["exe"], WORKLOAD_FILE)
    if files["data"].exists() and files["data"].stat().st_size > 0:
        shutil.copyfile(files["data"], DATA_FILE)
    else:
        DATA_FILE.write_text("")
    if LOG_FILE.exists():
        LOG_FILE.unlink()

    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(SIM_ENTRY),
                "--sim-threshold",
                str(sim_threshold),
                "--idle-threshold",
                str(idle_threshold),
                "--data-base",
                hex(data_base),
            ],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(REPO_ROOT),
        )
    except subprocess.TimeoutExpired:
        return False, "timeout (120s)", stats

    if proc.returncode != 0:
        if verbose:
            print(f"[{name}] simulator stderr (truncated):\n{proc.stderr[-800:]}")
        return False, f"simulator error (exit {proc.returncode})", stats

    log_text = LOG_FILE.read_text() if LOG_FILE.exists() else proc.stdout
    stats = extract_stats(log_text)
    a0_val = extract_a0(log_text)
    if a0_val is None:
        if verbose:
            print(f"[{name}] log tail:\n{log_text[-800:]}")
        return False, "no a0 writeback found", stats

    if a0_val != expected:
        return False, f"a0 mismatch: got {a0_val}, expected {expected}", stats

    msg = f"a0={a0_val} (expected {expected})"
    return True, msg, stats


def main():
    parser = argparse.ArgumentParser(description="Run Tomasulo simulator tests (simulator only)")
    parser.add_argument("tests", nargs="*", help="tests to run (default: all)")
    parser.add_argument("--list", action="store_true", help="list available tests")
    parser.add_argument("--sim-threshold", type=int, default=None, help="override sim threshold")
    parser.add_argument("--idle-threshold", type=int, default=None, help="override idle threshold")
    parser.add_argument("-v", "--verbose", action="store_true", help="show log tail on failure")
    parser.add_argument("--no-report", action="store_true", help="skip writing report file")
    args = parser.parse_args()

    available = discover_tests()
    if args.list:
        print("Available tests:")
        for t in available:
            print(f"  {t}")
        return

    targets = args.tests or available
    if not targets:
        print("No tests found under test/test_suite")
        return

    print(f"Running {len(targets)} test(s) with Tomasulo simulator...\n")
    header = f"{'Test Name':<20} {'Status':<6} {'Cycles':>8} {'Commits':>8} {'Fetches':>8} Message"
    separator = "-" * len(header)
    print(header)
    print(separator)

    report_lines = [header, separator]
    passed = 0
    for name in targets:
        ok, msg, stats = run_test(
            name,
            sim_threshold=args.sim_threshold,
            idle_threshold=args.idle_threshold,
            verbose=args.verbose,
        )
        status = "PASS" if ok else "FAIL"
        line = f"{name:<20} {status:<6} {stats['cycles']:>8} {stats['commits']:>8} {stats['fetches']:>8} {msg}"
        print(line)
        report_lines.append(line)
        passed += int(ok)

    summary = f"Summary: {passed}/{len(targets)} passed, {len(targets) - passed} failed"
    print("\n" + summary)
    report_lines.append(summary)

    if not args.no_report:
        report_file = REPO_ROOT / "test" / "test_report_tomasulo"
        report_file.write_text("\n".join(report_lines) + "\n")
        print(f"Report saved to: {report_file}")

    if passed != len(targets):
        sys.exit(1)


if __name__ == "__main__":
    main()

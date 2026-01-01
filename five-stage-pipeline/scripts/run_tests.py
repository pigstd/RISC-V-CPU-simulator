#!/usr/bin/env python3
"""
Run test cases from test/test_suite against the CPU simulator.

Test format:
- *.exe: instruction memory (hex)
- *.data: data memory (hex, may be empty)
- *.ans: expected a0 value (decimal)
- *.asm: disassembly (for debugging)

Usage:
    python scripts/run_tests.py                  # run all tests
    python scripts/run_tests.py 1to100 max       # run selected tests
    python scripts/run_tests.py --list           # list available tests
"""

import os
import re
import shutil
import subprocess
import sys
import json
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
# Repository root is two levels up from this scripts directory
REPO_ROOT = SCRIPT_DIR.parent.parent
# Project root (five-stage-pipeline) is the parent of this scripts dir
PROJ_ROOT = SCRIPT_DIR.parent
TEST_DIR = REPO_ROOT / "test"
TEST_SUITE_DIR = TEST_DIR / "test_suite"
# Use project-local src/workspace/main.py
SRC_DIR = PROJ_ROOT / "src"
WORKSPACE_DIR = SRC_DIR / "workspace"
SIM_ENTRY = SRC_DIR / "main.py"

# Pattern to extract a0 writeback from log
LOG_PATTERN = re.compile(r"writeback stage: rd = ([0-9a-fA-Fx]+) data = ([0-9a-fA-Fx]+)")
# Pattern to extract cycle number
CYCLE_PATTERN = re.compile(r"Cycle @(\d+(?:\.\d+)?)")
# Pattern to count executed instructions (executor stage)
EXEC_PATTERN = re.compile(r"executor input: pc=")
# Pattern to extract verilator timing summary
VERILATOR_TIMING_PATTERN = re.compile(
    r"\*\*\s+tb\.test_tb\s+PASS\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)"
)


def extract_stats(log_text: str) -> dict:
    """Extract statistics from simulation log."""
    stats = {
        "cycles": 0,
        "instructions": 0,
        "fetches": 0,
    }
    
    # Find max cycle
    cycles = CYCLE_PATTERN.findall(log_text)
    if cycles:
        stats["cycles"] = int(float(cycles[-1]))
    
    # Count executed instructions (executor stage, no duplicates due to stalls)
    stats["instructions"] = len(EXEC_PATTERN.findall(log_text))
    
    # Count fetches
    stats["fetches"] = log_text.count("fetch stage pc addr:")
    
    return stats


def extract_a0(log_text: str):
    """Return last a0 writeback value from log (int) or None."""
    a0_values = []
    for rd_str, data_str in LOG_PATTERN.findall(log_text):
        try:
            rd_val = int(rd_str, 0)
            if rd_val == 10:  # a0 = x10
                a0_values.append(int(data_str, 0))
        except ValueError:
            continue
    return a0_values[-1] if a0_values else None


def parse_verilator_timing(log_text: str) -> dict:
    """Parse SIM TIME/REAL TIME/RATIO from verilator log (ns/s)."""
    res = {"sim_time_ns": None, "real_time_s": None, "ratio": None}
    m = VERILATOR_TIMING_PATTERN.search(log_text)
    if m:
        res["sim_time_ns"] = float(m.group(1))
        res["real_time_s"] = float(m.group(2))
        res["ratio"] = float(m.group(3))
    return res


def discover_tests():
    """Discover all available test cases."""
    tests = []
    if TEST_SUITE_DIR.exists():
        for test_dir in sorted(TEST_SUITE_DIR.iterdir()):
            if test_dir.is_dir():
                name = test_dir.name
                exe_file = test_dir / f"{name}.exe"
                ans_file = test_dir / f"{name}.ans"
                if exe_file.exists() and ans_file.exists():
                    tests.append(name)
    # Also accept flat layout: test/<name>.exe + test/<name>.ans
    if TEST_DIR.exists():
        for exe in sorted(TEST_DIR.glob("*.exe")):
            name = exe.stem
            ans = TEST_DIR / f"{name}.ans"
            if ans.exists() and name not in tests:
                tests.append(name)
    return tests


def get_test_files(name: str):
    """Get paths to test files."""
    test_dir = TEST_SUITE_DIR / name
    return {
        "exe": test_dir / f"{name}.exe",
        "data": test_dir / f"{name}.data",
        "ans": test_dir / f"{name}.ans",
        "asm": test_dir / f"{name}.asm",
        "config": test_dir / f"{name}.config.json",
    }


def read_config(config_file: Path) -> dict:
    """Read config from .config.json file."""
    default_config = {
        "memory": {
            "text_base": 0x0,
            "data_base": 0x2000,
        },
        "simulator": {
            "sim_threshold": 10000,
            "idle_threshold": 5000,
        }
    }
    if config_file.exists():
        try:
            with open(config_file) as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return default_config


def read_expected(ans_file: Path) -> int:
    """Read expected a0 value from .ans file."""
    if ans_file.exists():
        content = ans_file.read_text().strip()
        if content:
            return int(content)
    return None


def run_test(name: str, sim_threshold: int = None, idle_threshold: int = None, verbose: bool = False, use_verilator: bool = False):
    """Run a single test case. Returns (success, message, stats)."""
    files = get_test_files(name)
    stats = {
        "cycles": 0,
        "instructions": 0,
        "fetches": 0,
        "verilator_sim_time_ns": None,
        "verilator_real_time_s": None,
        "verilator_ratio": None,
    }
    veri_stats = {"cycles": 0, "instructions": 0, "fetches": 0}
    
    # Check required files
    if not files["exe"].exists():
        return False, f"missing {name}.exe", stats
    if not files["ans"].exists():
        return False, f"missing {name}.ans", stats
    
    # Read config
    config = read_config(files["config"])
    
    # Use config values if not overridden by command line
    if sim_threshold is None:
        sim_threshold = config.get("simulator", {}).get("sim_threshold", 10000)
    if idle_threshold is None:
        idle_threshold = config.get("simulator", {}).get("idle_threshold", 5000)
    
    # Get memory layout from config
    data_base = config.get("memory", {}).get("data_base", 0x2000)
    
    # Read expected value
    expected = read_expected(files["ans"])
    if expected is None:
        return False, f"cannot read expected value from {name}.ans", stats
    
    # Copy files to workspace
    shutil.copyfile(files["exe"], WORKSPACE_DIR / "workload.exe")
    
    # Handle data file (may be empty or missing)
    if files["data"].exists() and files["data"].stat().st_size > 0:
        shutil.copyfile(files["data"], WORKSPACE_DIR / "data.mem")
    else:
        # Create empty data.mem if needed
        (WORKSPACE_DIR / "data.mem").write_text("")
    
    # Run simulator
    cmd = [
        sys.executable,
        str(SIM_ENTRY),
        "--sim-threshold", str(sim_threshold),
        "--idle-threshold", str(idle_threshold),
        "--data-base", hex(data_base),
    ]
    if not use_verilator:
        cmd.append("--no-verilator")
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout
        )
    except subprocess.TimeoutExpired:
        return False, "timeout (60s)", stats
    
    if proc.returncode != 0:
        if verbose:
            print(f"  stderr: {proc.stderr[:500]}")
        return False, f"simulator error (exit code {proc.returncode})", stats
    
    # Read log
    log_file = WORKSPACE_DIR / "log"
    if log_file.exists():
        log_text = log_file.read_text()
    else:
        log_text = proc.stdout
    
    # Extract statistics from log
    stats = extract_stats(log_text)
    
    sim_a0 = extract_a0(log_text)
    if sim_a0 is None:
        if verbose:
            print(f"  log tail:\n{log_text[-1000:]}")
        return False, "no a0 writeback found", stats
    
    if use_verilator:
        veri_log_file = WORKSPACE_DIR / "verilator_log"
        if veri_log_file.exists():
            veri_log_text = veri_log_file.read_text()
            veri_stats = extract_stats(veri_log_text)
            veri_a0 = extract_a0(veri_log_text)
            timing = parse_verilator_timing(veri_log_text)
            stats["verilator_sim_time_ns"] = timing["sim_time_ns"]
            stats["verilator_real_time_s"] = timing["real_time_s"]
            stats["verilator_ratio"] = timing["ratio"]
        else:
            veri_log_text = ""
            veri_a0 = None

        if veri_a0 is None:
            if verbose and veri_log_text:
                print(f"  verilator log tail:\n{veri_log_text[-1000:]}")
            return False, "verilator: no a0 writeback found", stats

        # Check results against expected
        if sim_a0 != expected:
            return False, f"sim a0 mismatch: got {sim_a0}, expected {expected}", stats
        if veri_a0 != expected:
            return False, f"verilator a0 mismatch: got {veri_a0}, expected {expected}", stats

        msg = f"sim a0={sim_a0}, verilator a0={veri_a0} (expected {expected})"
        if veri_stats.get("cycles", 0):
            msg += f" | veri cycles={veri_stats['cycles']}"
        return True, msg, stats
    else:
        # Only validate simulator (SIM) output a0; skip Verilator checks
        if sim_a0 != expected:
            return False, f"sim a0 mismatch: got {sim_a0}, expected {expected}", stats
        msg = f"sim a0={sim_a0} (expected {expected})"
        return True, msg, stats


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run test1 test suite")
    parser.add_argument("tests", nargs="*", help="specific tests to run")
    parser.add_argument("--list", action="store_true", help="list available tests")
    parser.add_argument("--sim-threshold", type=int, default=None, help="max simulation steps (overrides config)")
    parser.add_argument("--idle-threshold", type=int, default=None, help="idle cycles before stop (overrides config)")
    parser.add_argument("-v", "--verilator", action="store_true", help="enable Verilator run (default: only run Python sim)")
    parser.add_argument("--verbose", action="store_true", help="verbose output on failure")
    parser.add_argument("--no-report", action="store_true", help="do not generate test report")
    args = parser.parse_args()
    
    available_tests = discover_tests()
    
    if args.list:
        print("Available tests:")
        for t in available_tests:
            print(f"  {t}")
        return
    
    # Determine which tests to run
    if args.tests:
        targets = args.tests
        # Validate
        for t in targets:
            if t not in available_tests:
                print(f"Warning: test '{t}' not found in test_suite")
    else:
        targets = available_tests
    
    if not targets:
        print("No tests found in test_suite/")
        return
    
    # Prepare report output
    report_lines = []
    from datetime import datetime
    report_lines.append(f"RISC-V CPU Simulator Test Report")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"")
    
    # Run tests
    print(f"Running {len(targets)} test(s)...\n")
    header = f"{'Test Name':<25} {'Status':<8} {'Cycles':>10} {'Instr':>10} {'Fetch':>10} {'V-Sim(ns)':>12} {'V-Real(s)':>12} {'V-Ratio':>10} Message"
    separator = "-" * 130
    print(header)
    print(separator)
    report_lines.append(header)
    report_lines.append(separator)
    
    passed = 0
    failed = 0
    
    for name in targets:
        ok, msg, stats = run_test(
            name,
            sim_threshold=args.sim_threshold,
            idle_threshold=args.idle_threshold,
            verbose=args.verbose,
            use_verilator=args.verilator,
        )
        status = "PASS" if ok else "FAIL"
        cycles = stats.get("cycles", 0)
        instrs = stats.get("instructions", 0)
        fetches = stats.get("fetches", 0)
        v_sim = stats.get("verilator_sim_time_ns") or 0
        v_real = stats.get("verilator_real_time_s") or 0
        v_ratio = stats.get("verilator_ratio") or 0
        line = f"{name:<25} {status:<8} {cycles:>10} {instrs:>10} {fetches:>10} {v_sim:>12.2f} {v_real:>12.2f} {v_ratio:>10.2f} {msg}"
        print(line)
        report_lines.append(line)
        if ok:
            passed += 1
        else:
            failed += 1
    
    # Summary
    summary_sep = f"\n{'='*40}"
    summary_line = f"Summary: {passed}/{len(targets)} passed, {failed} failed"
    print(summary_sep)
    print(summary_line)
    report_lines.append(summary_sep)
    report_lines.append(summary_line)
    
    # Write report to file
    if not args.no_report:
        report_file = TEST_DIR / "test_report"
        report_file.write_text("\n".join(report_lines) + "\n")
        print(f"\nReport saved to: {report_file}")
    
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

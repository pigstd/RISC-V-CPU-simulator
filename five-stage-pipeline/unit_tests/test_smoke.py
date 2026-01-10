import pathlib
import subprocess


def test_tomasulo_smoke_run():
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    cmd = ["python", "Tomasulo/src/main.py", "--sim-threshold", "5", "--idle-threshold", "5"]
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    assert result.returncode == 0, f"Simulator run failed: {result.stderr or result.stdout}"

    log_path = repo_root / "Tomasulo" / "src" / "workspace" / "log"
    assert log_path.exists(), "Simulation log not found"
    log_text = log_path.read_text()
    assert "CPU Simulation Started" in log_text, "Simulator log missing startup marker"

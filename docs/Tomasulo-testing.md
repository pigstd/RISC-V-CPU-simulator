测试指南
========

概览
----
- 两类测试：
  - `unit_tests/`：pytest 单测，直接运行模拟器并检查日志。
  - `Tomasulo/run_tomasulo_tests.py`：跑 `test/test_suite` 里的功能用例。

pytest 单测
-----------
- 全部单测：`python -m pytest unit_tests`
- 某个文件：`python -m pytest unit_tests/test_simple_ebreak.py`
- 某个用例：`python -m pytest unit_tests/test_simple_ebreak.py::test_simple_add_then_ebreak`
- 关键词过滤：`python -m pytest unit_tests -k ebreak`
- 查看打印：加 `-s`，如 `python -m pytest -s unit_tests/test_memory_ops.py::test_sw_then_lw_roundtrip`
- 日志位置：每次运行后查看 `Tomasulo/src/workspace/log`（stderr 如有也在同目录）。

功能用例（`test/test_suite`）
----------------------------
- 脚本：`python Tomasulo/run_tomasulo_tests.py`
- 跑全部：`python Tomasulo/run_tomasulo_tests.py`
- 跑指定用例（目录名即用例名，如 `simple_add`, `array_sum`）：`python Tomasulo/run_tomasulo_tests.py simple_add array_sum`
- 可选参数：
  - `--sim-threshold N` / `--idle-threshold N` 调整步数
  - `-v` 把 stderr 写到 `Tomasulo/src/workspace/stderr`
- 生成文件：会将用例拷到 `Tomasulo/src/workspace/`（`workload.exe`, `data.mem`），期望值写 `expected`，日志写 `log`。

提示
----
- 默认假设命令在仓库根目录执行。
- 失败时优先看 `Tomasulo/src/workspace/log` 里的流水线事件与调试输出。

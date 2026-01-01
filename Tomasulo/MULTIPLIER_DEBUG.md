# 乘法器调试与实现进度

## 已完成
1. ✅ 创建测试用例 (simple_mul, vector_mul_real)
2. ✅ 扩展指令解码器支持 M 扩展 (MUL/MULH/MULHSU/MULHU)
3. ✅ 实现 multiplier.py：
   - Multiplier 类（非流水线，4周期乘法）
   - MUL_RSEntry（乘法保留站条目）
   - MUL_RS_downstream（乘法保留站下游逻辑）
4. ✅ 集成到 main.py（issue、flush 逻辑）
5. ✅ 创建 signals.py 避免循环导入

## 遇到的问题

### 问题 1: Assassyn `.valid` intrinsic 错误
**症状**: 编译时 AssertionError in `_codegen_value_valid`  
**根本原因**: 在 arbitrator.py 中访问 `mul_req.valid` 时出现

```python
AssertionError: assert isinstance(node.get_operand(0).value, Expr)
```

**解决**: 简化 MUL_RS_downstream，移除 `mul_busy.optional(default=Bits(1)(0))` 这样的常量参数

### 问题 2: multiplier 输出无法被读取
**症状**: simple_mul 运行 10000 周期，11 条指令执行，但无结果输出  
**根本原因**: arbitrator 中乘法器 CDB 处理被禁用（为避免编译错误）

## 当前状态
- simple_mul 能编译运行但无结果（乘法器被孤立）
- 需要恢复 arbitrator 中乘法器的 CDB 集成

## 下一步计划

### 方案 A: 修复 arbitrator 中的 `.valid` 使用
需要找到避免 `.valid` intrinsic 的方式，或理解为什么 MUL_CBD_signal 与 LSU/ALU_CBD_signal 不兼容

```python
# 当前有问题的模式（LSU/ALU 用这个却能工作）
mul_req.valid.select(mul_req.ROB_idx, mul_cbd_reg_view.ROB_idx)

# 可能的替代方案
# 1. 提取到中间变量
# 2. 改变 Record 定义方式
# 3. 使用不同的选择机制
```

### 方案 B: Workaround - multiplier 直接写 ROB
1. Multiplier.build() 增加 ROB 参数
2. 当 mul_result.valid 时，直接写入 ROB
3. 跳过 CDB arbitrator

### 调试建议
1. 对比 LSU_CBD_signal 和 MUL_CBD_signal 的 IR 生成
2. 测试其他简单的 Record 操作
3. 查看 Assassyn 框架对 Record view 的处理

## 文件位置
- 测试用例: `test/src/simple_mul.c`, `test/src/vector_mul_real.c`
- 模块: `Tomasulo/src/multiplier.py`
- 信号定义: `Tomasulo/src/signals.py`
- 集成: `Tomasulo/src/main.py`
- CDB: `Tomasulo/src/arbitrator.py`

## 构建命令
```bash
cd Tomasulo
python script/run_tests.py simple_mul
python script/run_tests.py fib  # 测试基础功能
```

"""
公共信号定义 - 避免循环导入问题
"""
from assassyn.frontend import *
from .ROB import ROB_IDX_WIDTH

# 乘法器 CDB 信号
MUL_CBD_signal = Record(
    ROB_idx = UInt(ROB_IDX_WIDTH),     # ROB 索引
    rd_data = UInt(32),    # 结果
    valid = Bits(1),       # 结果有效
)

#!/bin/bash

# 批量编译所有测试程序

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
SRC_DIR="$SCRIPT_DIR/src"
WORKLOAD_DIR="$SCRIPT_DIR/workloads"
UTILS_DIR="$SCRIPT_DIR/../utils"

CROSS_COMPILE=riscv64-unknown-elf-
CC="${CROSS_COMPILE}gcc"
OBJDUMP="${CROSS_COMPILE}objdump"
OBJCOPY="${CROSS_COMPILE}objcopy"

CFLAGS="-march=rv32i -mabi=ilp32 -O0 -nostdlib -static -Wl,--no-relax"

# 创建输出目录
mkdir -p "$WORKLOAD_DIR"

# 所有测试程序列表 (仅使用 RV32I 指令)
TESTS=("fib" "sort" "factorial" "sum" "bitcount" "max" "reverse")

# 跳过需要乘法/除法的测试 (RV32I 不支持)
SKIP_TESTS=("gcd" "prime")

for TEST in "${TESTS[@]}"; do
    SRC_FILE="$SRC_DIR/$TEST.c"
    
    if [ ! -f "$SRC_FILE" ]; then
        echo "[SKIP] $TEST: Source file not found"
        continue
    fi
    
    echo "[BUILD] Compiling $TEST..."
    
    # 编译
    $CC $CFLAGS \
        -T"$SCRIPT_DIR/link.ld" \
        "$SRC_DIR/start.S" \
        "$SRC_FILE" \
        -o "$WORKLOAD_DIR/$TEST.riscv" 2>&1
    
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to compile $TEST"
        continue
    fi
    
    # 生成反汇编
    $OBJDUMP -d "$WORKLOAD_DIR/$TEST.riscv" > "$WORKLOAD_DIR/$TEST.riscv.dump"
    
    # 使用 loader.py 生成 hex 文件
    python3 "$UTILS_DIR/loader.py" --fname "$WORKLOAD_DIR/$TEST.riscv.dump" --odir "$WORKLOAD_DIR"
    
    echo "[OK] $TEST compiled successfully"
    echo "     ELF: $WORKLOAD_DIR/$TEST.riscv"
    echo "     Dump: $WORKLOAD_DIR/$TEST.riscv.dump"
    echo "     Hex: $WORKLOAD_DIR/$TEST.exe"
done

echo ""
echo "=== Compilation Summary ==="
echo "Tests compiled: ${TESTS[*]}"
echo "Tests skipped (needs M extension): ${SKIP_TESTS[*]}"
echo ""
echo "Note: gcd.c and prime.c use modulo (%) operation which requires"
echo "      RV32M extension. To compile them, use -march=rv32im"

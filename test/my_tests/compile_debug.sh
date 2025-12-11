#!/bin/bash
set -e

# RISC-V Toolchain
RISCV_PREFIX="${RISCV_PREFIX:-riscv64-unknown-elf-}"
RISCV_GCC="${RISCV_PREFIX}gcc"
RISCV_OBJDUMP="${RISCV_PREFIX}objdump"

SOURCE_FILE="$1"
OUTPUT_DIR="${2:-$(dirname "$0")/../workloads}"
BASENAME=$(basename "$SOURCE_FILE" .c)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOADER_SCRIPT="$(dirname "$0")/../utils/loader.py"

mkdir -p "$OUTPUT_DIR"

RISCV_ELF="$OUTPUT_DIR/${BASENAME}.riscv"
DUMP_FILE="$OUTPUT_DIR/${BASENAME}.riscv.dump"
EXE_FILE="$OUTPUT_DIR/${BASENAME}.exe"
DATA_FILE="$OUTPUT_DIR/${BASENAME}.data"
CONFIG_FILE="$OUTPUT_DIR/${BASENAME}.config"

START_FILE="$(dirname "$SOURCE_FILE")/start.S"
FILES_TO_COMPILE="$SOURCE_FILE"
if [ -f "$START_FILE" ]; then
    FILES_TO_COMPILE="$START_FILE $SOURCE_FILE"
    echo "Found start.S, including it."
fi

echo "Compiling $SOURCE_FILE with -O0..."

# Compile with -O0 to prevent optimization
$RISCV_GCC -O0 $FILES_TO_COMPILE \
    -march=rv32i \
    -mabi=ilp32 \
    -nostdlib \
    -Wl,--no-relax \
    -o "$RISCV_ELF"

# Disassemble
$RISCV_OBJDUMP -d "$RISCV_ELF" > "$DUMP_FILE"

# Generate simulation files
python3 "$LOADER_SCRIPT" --fname "$DUMP_FILE" --odir "$OUTPUT_DIR"

echo "Done: $EXE_FILE"

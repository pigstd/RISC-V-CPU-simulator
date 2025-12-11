#!/bin/bash
LOG_FILE=$1
echo "Checking log file: $LOG_FILE"
if ! grep -q "ebreak" "$LOG_FILE"; then
    echo "FAIL: Simulation did not hit ebreak"
    exit 1
fi
LAST_LINE=$(grep "writeback.*|.*x10.*|.*0x" "$LOG_FILE" | tail -n 1)
if [ -z "$LAST_LINE" ]; then
    echo "FAIL: No writeback to x10 found"
    exit 1
fi
VAL_HEX=$(echo "$LAST_LINE" | awk '{print $NF}')
VAL_DEC=$(printf "%d" "$VAL_HEX")
echo "Last write to x10: $VAL_HEX ($VAL_DEC)"
if [ "$VAL_DEC" -eq 55 ]; then
    echo "PASS: x10 = 55"
    exit 0
else
    echo "FAIL: Expected x10=55, got $VAL_DEC"
    exit 1
fi

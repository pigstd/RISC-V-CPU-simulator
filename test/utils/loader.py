#!/usr/bin/env python3
"""
RISC-V ELF Dump to HEX Loader

This script parses RISC-V objdump output and generates hex files
suitable for loading into SRAM-based instruction/data memories.

Usage:
    python loader.py --fname <dump_file> --odir <output_dir>
"""

import argparse
import os
import re
from pathlib import Path


def parse_dump_file(dump_path: str):
    """
    Parse RISC-V objdump output and extract instructions.
    
    Returns:
        list of (address, instruction_hex) tuples
    """
    instructions = []
    
    with open(dump_path, 'r') as f:
        lines = f.readlines()
    
    # Pattern for instruction lines:
    # "   10074:	00500093          	addi	ra,zero,5"
    # "    addr:  hex_code           asm"
    pattern = re.compile(r'^\s*([0-9a-fA-F]+):\s+([0-9a-fA-F]+)\s+')
    
    for line in lines:
        match = pattern.match(line)
        if match:
            addr_str = match.group(1)
            instr_str = match.group(2)
            
            addr = int(addr_str, 16)
            
            # Handle 2-byte (compressed) or 4-byte instructions
            if len(instr_str) == 4:
                # 2-byte compressed instruction
                instr = int(instr_str, 16)
                instructions.append((addr, instr, 2))
            elif len(instr_str) == 8:
                # 4-byte standard instruction
                instr = int(instr_str, 16)
                instructions.append((addr, instr, 4))
    
    return instructions


def generate_hex_file(instructions, output_path: str, base_addr: int = 0x10000, mem_depth: int = 65536):
    """
    Generate a hex file from instructions.
    
    Each line contains a 32-bit word in hexadecimal format (no prefix).
    The hex file starts from address 0 (word 0) in the SRAM.
    Instructions are placed relative to their position from base_addr.
    """
    if not instructions:
        print("Warning: No instructions found!")
        return
    
    # Create a memory image (indexed by relative word address from base)
    memory = {}
    base_word_addr = base_addr // 4
    
    for addr, instr, size in instructions:
        # Convert to word-aligned address relative to base
        word_addr = addr // 4
        relative_word_addr = word_addr - base_word_addr
        byte_offset = addr % 4
        
        if relative_word_addr < 0:
            print(f"Warning: Address 0x{addr:08X} is before base address 0x{base_addr:08X}")
            continue
        
        if size == 4:
            # 4-byte instruction, must be word-aligned
            memory[relative_word_addr] = instr
        elif size == 2:
            # 2-byte compressed instruction
            if relative_word_addr not in memory:
                memory[relative_word_addr] = 0
            if byte_offset == 0:
                memory[relative_word_addr] = (memory[relative_word_addr] & 0xFFFF0000) | instr
            else:
                memory[relative_word_addr] = (memory[relative_word_addr] & 0x0000FFFF) | (instr << 16)
    
    # Find the range of addresses used
    if memory:
        min_rel_addr = min(memory.keys())
        max_rel_addr = max(memory.keys())
        
        print(f"Code range: 0x{(min_rel_addr + base_word_addr)*4:08X} - 0x{(max_rel_addr + base_word_addr)*4:08X}")
        print(f"Base address: 0x{base_addr:08X}")
        print(f"Relative word range: {min_rel_addr} - {max_rel_addr}")
        print(f"Number of instructions: {len(memory)}")
    
    # Write hex file - starting from word address 0
    with open(output_path, 'w') as f:
        for i in range(mem_depth):
            if i in memory:
                f.write(f"{memory[i]:08X}\n")
            else:
                f.write("00000000\n")
    
    print(f"Generated hex file: {output_path}")


def generate_config_file(instructions, output_path: str, basename: str):
    """
    Generate a config file with test metadata.
    """
    if not instructions:
        return
    
    # Calculate some basic statistics
    addrs = [addr for addr, _, _ in instructions]
    min_addr = min(addrs)
    max_addr = max(addrs)
    num_instructions = len(instructions)
    
    with open(output_path, 'w') as f:
        f.write(f"# Test configuration for {basename}\n")
        f.write(f"name={basename}\n")
        f.write(f"start_addr=0x{min_addr:08X}\n")
        f.write(f"end_addr=0x{max_addr:08X}\n")
        f.write(f"num_instructions={num_instructions}\n")
        f.write(f"exe_file={basename}.exe\n")
        f.write(f"data_file={basename}.data\n")
    
    print(f"Generated config file: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Convert RISC-V objdump output to hex files for simulation'
    )
    parser.add_argument('--fname', required=True, help='Input dump file path')
    parser.add_argument('--odir', required=True, help='Output directory')
    parser.add_argument('--base', default='0x10000', help='Base address (default: 0x10000)')
    parser.add_argument('--depth', type=int, default=65536, help='Memory depth (default: 65536)')
    
    args = parser.parse_args()
    
    # Parse base address
    base_addr = int(args.base, 0)
    
    # Get basename
    fname = Path(args.fname)
    basename = fname.stem
    if basename.endswith('.riscv'):
        basename = basename[:-6]
    
    # Create output directory
    os.makedirs(args.odir, exist_ok=True)
    
    # Parse dump file
    print(f"Parsing dump file: {args.fname}")
    instructions = parse_dump_file(args.fname)
    print(f"Found {len(instructions)} instructions")
    
    # Generate output files
    exe_path = os.path.join(args.odir, f"{basename}.exe")
    data_path = os.path.join(args.odir, f"{basename}.data")
    config_path = os.path.join(args.odir, f"{basename}.config")
    
    # Generate instruction memory hex file
    generate_hex_file(instructions, exe_path, base_addr, args.depth)
    
    # Generate empty data memory file
    with open(data_path, 'w') as f:
        for _ in range(1024):  # Default data memory size
            f.write("00000000\n")
    print(f"Generated data file: {data_path}")
    
    # Generate config file
    generate_config_file(instructions, config_path, basename)
    
    print("\nDone!")


if __name__ == '__main__':
    main()

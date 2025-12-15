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
import subprocess
import sys
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


def parse_elf_sections(elf_path: Path, names):
    """
    Parse section headers from ELF using readelf -S.
    Returns list of tuples (name, addr, offset, size, type).
    """
    try:
        out = subprocess.check_output(
            ["riscv64-unknown-elf-readelf", "-S", str(elf_path)],
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Warning: failed to run readelf on {elf_path}: {e}")
        return []

    sec_re = re.compile(
        r"\s*\[\s*\d+\]\s+(\S+)\s+(\S+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)"
    )
    sections = []
    for line in out.splitlines():
        m = sec_re.match(line)
        if not m:
            continue
        name, stype, addr_hex, off_hex, size_hex = m.groups()
        if name not in names:
            continue
        addr = int(addr_hex, 16)
        off = int(off_hex, 16)
        size = int(size_hex, 16)
        sections.append((name, stype, addr, off, size))
    return sections


def generate_data_file(elf_path: Path, output_path: str, base_addr: int = 0x0, mem_depth: int = 262144):
    """
    Generate data memory image (.data file) from ELF's data/rodata/sdata/bss.
    """
    if not elf_path.exists():
        print(f"Warning: ELF file {elf_path} not found, generating zeroed data file.")
        with open(output_path, 'w') as f:
            for _ in range(mem_depth):
                f.write("00000000\n")
        return

    sections = parse_elf_sections(elf_path, {".data", ".sdata", ".rodata", ".sbss", ".bss"})
    mem_bytes = bytearray(mem_depth * 4)

    # Load file once for copying section contents
    try:
        elf_bytes = elf_path.read_bytes()
    except OSError as e:
        print(f"Warning: failed to read ELF {elf_path}: {e}")
        elf_bytes = b""

    for name, stype, addr, off, size in sections:
        if size == 0:
            continue
        rel = addr - base_addr
        if rel < 0:
            print(f"Warning: section {name} at 0x{addr:08X} before base 0x{base_addr:08X}, skipped.")
            continue
        end = rel + size
        if end > len(mem_bytes):
            # Extend to fit the section
            mem_bytes.extend(b"\x00" * (end - len(mem_bytes)))
        if size == 0:
            continue

        if stype == "NOBITS":
            chunk = b"\x00" * size  # bss/sbss
        else:
            chunk = elf_bytes[off:off + size] if off + size <= len(elf_bytes) else b""
            if len(chunk) < size:
                chunk = chunk.ljust(size, b"\x00")
        mem_bytes[rel:end] = chunk
        print(f"Placed section {name} size {size} at offset 0x{rel:x}")

    with open(output_path, 'w') as f:
        for i in range(0, len(mem_bytes), 4):
            word = int.from_bytes(mem_bytes[i:i + 4], 'little')
            f.write(f"{word:08X}\n")
    print(f"Generated data file: {output_path}")


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
    parser.add_argument('--base', default='0x10000', help='Instruction base address (default: 0x10000)')
    parser.add_argument('--data-base', default='0x0', help='Data base address (default: 0x0)')
    parser.add_argument('--depth', type=int, default=65536, help='Instruction memory depth (words, default: 65536)')
    parser.add_argument('--data-depth', type=int, default=262144, help='Data memory depth (words, default: 262144)')
    
    args = parser.parse_args()
    
    # Parse base addresses
    base_addr = int(args.base, 0)
    data_base_addr = int(args.data_base, 0)
    
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

    # Generate data memory file from ELF (if available)
    elf_path = fname.with_suffix("") if fname.suffix == ".dump" else fname
    if elf_path.suffix != ".riscv" and (fname.suffix == ".riscv" or fname.suffixes[-2:] == [".riscv", ".dump"]):
        elf_path = fname.with_suffix("")  # handle *.riscv.dump
    generate_data_file(elf_path, data_path, data_base_addr, args.data_depth)
    
    # Generate config file
    generate_config_file(instructions, config_path, basename)
    
    print("\nDone!")


if __name__ == '__main__':
    main()

/* Simple linker script for RISC-V tests */

OUTPUT_ARCH(riscv)
ENTRY(_start)

MEMORY
{
    /* Code starts at 0x10000 */
    TEXT   (rx)  : ORIGIN = 0x10000, LENGTH = 64K
    /* Data at 0x80000 */
    DATA   (rw)  : ORIGIN = 0x80000, LENGTH = 64K
    /* Stack at 0x10000 (grows down) */
}

SECTIONS
{
    . = 0x10000;
    
    .text : {
        *(.text.init)
        *(.text)
        *(.text.*)
    } > TEXT
    
    .rodata : {
        *(.rodata)
        *(.rodata.*)
    } > TEXT
    
    . = 0x80000;
    
    .data : {
        *(.data)
        *(.data.*)
        *(.sdata)
        *(.sdata.*)
    } > DATA
    
    .bss : {
        *(.bss)
        *(.bss.*)
        *(.sbss)
        *(.sbss.*)
    } > DATA
    
    /DISCARD/ : {
        *(.comment)
        *(.note.*)
        *(.riscv.attributes)
    }
}

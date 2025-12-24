
OUTPUT_ARCH( "riscv" )
ENTRY( _start )
SECTIONS
{
  . = 0x00000000;
  .text : { *(.text.init) *(.text) }
  . = 0x00002000;
  .data : { *(.data) *(.rodata*) *(.sdata) }
  .bss : { *(.bss) *(.sbss) }
}

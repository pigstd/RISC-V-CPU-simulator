
.section .text
.globl _start
_start:
    lui sp, 0x20
    jal main
    ebreak
.section .text
.globl __main_loop
__main_loop:
    j __main_loop

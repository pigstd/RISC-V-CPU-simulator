
/home/louhao/System-2025/RISC-V-CPU-simulator/test/test_suite/simple_add/simple_add.elf:     file format elf32-littleriscv


Disassembly of section .text:

00000000 <_start>:
   0:	00020137          	lui	sp,0x20
   4:	00c000ef          	jal	ra,10 <main>
   8:	00100073          	ebreak

0000000c <__main_loop>:
   c:	0000006f          	j	c <__main_loop>

00000010 <main>:
  10:	fe010113          	addi	sp,sp,-32 # 1ffe0 <main+0x1ffd0>
  14:	00812e23          	sw	s0,28(sp)
  18:	02010413          	addi	s0,sp,32
  1c:	00f00793          	li	a5,15
  20:	fef42623          	sw	a5,-20(s0)
  24:	fec42783          	lw	a5,-20(s0)
  28:	00078513          	mv	a0,a5
  2c:	01c12403          	lw	s0,28(sp)
  30:	02010113          	addi	sp,sp,32
  34:	00008067          	ret

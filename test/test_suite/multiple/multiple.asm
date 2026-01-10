
/home/louhao/System-2025/RISC-V-CPU-simulator/test/test_suite/multiple/multiple.elf:     file format elf32-littleriscv


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
  1c:	00700793          	li	a5,7
  20:	fef42623          	sw	a5,-20(s0)
  24:	00800793          	li	a5,8
  28:	fef42423          	sw	a5,-24(s0)
  2c:	00900793          	li	a5,9
  30:	fef42223          	sw	a5,-28(s0)
  34:	fec42703          	lw	a4,-20(s0)
  38:	fe842783          	lw	a5,-24(s0)
  3c:	02f707b3          	mul	a5,a4,a5
  40:	fe442703          	lw	a4,-28(s0)
  44:	00f707b3          	add	a5,a4,a5
  48:	fef42023          	sw	a5,-32(s0)
  4c:	fe042783          	lw	a5,-32(s0)
  50:	00078513          	mv	a0,a5
  54:	01c12403          	lw	s0,28(sp)
  58:	02010113          	addi	sp,sp,32
  5c:	00008067          	ret

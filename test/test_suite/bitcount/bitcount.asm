
test_suite/bitcount/bitcount.elf:     file format elf32-littleriscv


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
  1c:	0b500793          	li	a5,181
  20:	fef42623          	sw	a5,-20(s0)
  24:	fe042423          	sw	zero,-24(s0)
  28:	0240006f          	j	4c <main+0x3c>
  2c:	fec42783          	lw	a5,-20(s0)
  30:	0017f793          	andi	a5,a5,1
  34:	fe842703          	lw	a4,-24(s0)
  38:	00f707b3          	add	a5,a4,a5
  3c:	fef42423          	sw	a5,-24(s0)
  40:	fec42783          	lw	a5,-20(s0)
  44:	4017d793          	srai	a5,a5,0x1
  48:	fef42623          	sw	a5,-20(s0)
  4c:	fec42783          	lw	a5,-20(s0)
  50:	fc079ee3          	bnez	a5,2c <main+0x1c>
  54:	fe842783          	lw	a5,-24(s0)
  58:	00078513          	mv	a0,a5
  5c:	01c12403          	lw	s0,28(sp)
  60:	02010113          	addi	sp,sp,32
  64:	00008067          	ret

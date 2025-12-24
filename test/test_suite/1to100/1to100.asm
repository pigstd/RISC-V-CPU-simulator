
test_suite/1to100/1to100.elf:     file format elf32-littleriscv


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
  1c:	fe042623          	sw	zero,-20(s0)
  20:	fe042423          	sw	zero,-24(s0)
  24:	0200006f          	j	44 <main+0x34>
  28:	fec42703          	lw	a4,-20(s0)
  2c:	fe842783          	lw	a5,-24(s0)
  30:	00f707b3          	add	a5,a4,a5
  34:	fef42623          	sw	a5,-20(s0)
  38:	fe842783          	lw	a5,-24(s0)
  3c:	00178793          	addi	a5,a5,1
  40:	fef42423          	sw	a5,-24(s0)
  44:	fe842703          	lw	a4,-24(s0)
  48:	06400793          	li	a5,100
  4c:	fce7dee3          	bge	a5,a4,28 <main+0x18>
  50:	fec42703          	lw	a4,-20(s0)
  54:	fffff7b7          	lui	a5,0xfffff
  58:	c4678793          	addi	a5,a5,-954 # ffffec46 <main+0xffffec36>
  5c:	00f707b3          	add	a5,a4,a5
  60:	0017b793          	seqz	a5,a5
  64:	0ff7f793          	andi	a5,a5,255
  68:	fef42223          	sw	a5,-28(s0)
  6c:	fe442783          	lw	a5,-28(s0)
  70:	00078513          	mv	a0,a5
  74:	01c12403          	lw	s0,28(sp)
  78:	02010113          	addi	sp,sp,32
  7c:	00008067          	ret

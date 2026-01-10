
/home/louhao/System-2025/RISC-V-CPU-simulator/test/test_suite/prime/prime.elf:     file format elf32-littleriscv


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
  1c:	01100793          	li	a5,17
  20:	fef42023          	sw	a5,-32(s0)
  24:	00100793          	li	a5,1
  28:	fef42623          	sw	a5,-20(s0)
  2c:	fe042703          	lw	a4,-32(s0)
  30:	00100793          	li	a5,1
  34:	00e7c663          	blt	a5,a4,40 <main+0x30>
  38:	fe042623          	sw	zero,-20(s0)
  3c:	0600006f          	j	9c <main+0x8c>
  40:	00200793          	li	a5,2
  44:	fef42423          	sw	a5,-24(s0)
  48:	0480006f          	j	90 <main+0x80>
  4c:	fe042783          	lw	a5,-32(s0)
  50:	fef42223          	sw	a5,-28(s0)
  54:	0140006f          	j	68 <main+0x58>
  58:	fe442703          	lw	a4,-28(s0)
  5c:	fe842783          	lw	a5,-24(s0)
  60:	40f707b3          	sub	a5,a4,a5
  64:	fef42223          	sw	a5,-28(s0)
  68:	fe442703          	lw	a4,-28(s0)
  6c:	fe842783          	lw	a5,-24(s0)
  70:	fef754e3          	bge	a4,a5,58 <main+0x48>
  74:	fe442783          	lw	a5,-28(s0)
  78:	00079663          	bnez	a5,84 <main+0x74>
  7c:	fe042623          	sw	zero,-20(s0)
  80:	01c0006f          	j	9c <main+0x8c>
  84:	fe842783          	lw	a5,-24(s0)
  88:	00178793          	addi	a5,a5,1
  8c:	fef42423          	sw	a5,-24(s0)
  90:	fe842703          	lw	a4,-24(s0)
  94:	fe042783          	lw	a5,-32(s0)
  98:	faf74ae3          	blt	a4,a5,4c <main+0x3c>
  9c:	fec42783          	lw	a5,-20(s0)
  a0:	00078513          	mv	a0,a5
  a4:	01c12403          	lw	s0,28(sp)
  a8:	02010113          	addi	sp,sp,32
  ac:	00008067          	ret

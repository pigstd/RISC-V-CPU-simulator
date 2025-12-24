
test_suite/power2/power2.elf:     file format elf32-littleriscv


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
  1c:	00200793          	li	a5,2
  20:	fef42223          	sw	a5,-28(s0)
  24:	00800793          	li	a5,8
  28:	fef42023          	sw	a5,-32(s0)
  2c:	00100793          	li	a5,1
  30:	fef42623          	sw	a5,-20(s0)
  34:	fe042423          	sw	zero,-24(s0)
  38:	01c0006f          	j	54 <main+0x44>
  3c:	fec42783          	lw	a5,-20(s0)
  40:	00179793          	slli	a5,a5,0x1
  44:	fef42623          	sw	a5,-20(s0)
  48:	fe842783          	lw	a5,-24(s0)
  4c:	00178793          	addi	a5,a5,1
  50:	fef42423          	sw	a5,-24(s0)
  54:	fe842703          	lw	a4,-24(s0)
  58:	fe042783          	lw	a5,-32(s0)
  5c:	fef740e3          	blt	a4,a5,3c <main+0x2c>
  60:	fec42703          	lw	a4,-20(s0)
  64:	10000793          	li	a5,256
  68:	00f71663          	bne	a4,a5,74 <main+0x64>
  6c:	00800793          	li	a5,8
  70:	0080006f          	j	78 <main+0x68>
  74:	00000793          	li	a5,0
  78:	00078513          	mv	a0,a5
  7c:	01c12403          	lw	s0,28(sp)
  80:	02010113          	addi	sp,sp,32
  84:	00008067          	ret

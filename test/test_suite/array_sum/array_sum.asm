
test_suite/array_sum/array_sum.elf:     file format elf32-littleriscv


Disassembly of section .text:

00000000 <_start>:
   0:	00020137          	lui	sp,0x20
   4:	00c000ef          	jal	ra,10 <main>
   8:	00100073          	ebreak

0000000c <__main_loop>:
   c:	0000006f          	j	c <__main_loop>

00000010 <main>:
  10:	fc010113          	addi	sp,sp,-64 # 1ffc0 <main+0x1ffb0>
  14:	02812e23          	sw	s0,60(sp)
  18:	04010413          	addi	s0,sp,64
  1c:	000027b7          	lui	a5,0x2
  20:	00078793          	mv	a5,a5
  24:	0007a503          	lw	a0,0(a5) # 2000 <main+0x1ff0>
  28:	0047a583          	lw	a1,4(a5)
  2c:	0087a603          	lw	a2,8(a5)
  30:	00c7a683          	lw	a3,12(a5)
  34:	0107a703          	lw	a4,16(a5)
  38:	0147a783          	lw	a5,20(a5)
  3c:	fca42623          	sw	a0,-52(s0)
  40:	fcb42823          	sw	a1,-48(s0)
  44:	fcc42a23          	sw	a2,-44(s0)
  48:	fcd42c23          	sw	a3,-40(s0)
  4c:	fce42e23          	sw	a4,-36(s0)
  50:	fef42023          	sw	a5,-32(s0)
  54:	00600793          	li	a5,6
  58:	fef42223          	sw	a5,-28(s0)
  5c:	fe042623          	sw	zero,-20(s0)
  60:	fe042423          	sw	zero,-24(s0)
  64:	0300006f          	j	94 <main+0x84>
  68:	fe842783          	lw	a5,-24(s0)
  6c:	00279793          	slli	a5,a5,0x2
  70:	ff040713          	addi	a4,s0,-16
  74:	00f707b3          	add	a5,a4,a5
  78:	fdc7a783          	lw	a5,-36(a5)
  7c:	fec42703          	lw	a4,-20(s0)
  80:	00f707b3          	add	a5,a4,a5
  84:	fef42623          	sw	a5,-20(s0)
  88:	fe842783          	lw	a5,-24(s0)
  8c:	00178793          	addi	a5,a5,1
  90:	fef42423          	sw	a5,-24(s0)
  94:	fe842703          	lw	a4,-24(s0)
  98:	fe442783          	lw	a5,-28(s0)
  9c:	fcf746e3          	blt	a4,a5,68 <main+0x58>
  a0:	fec42783          	lw	a5,-20(s0)
  a4:	00078513          	mv	a0,a5
  a8:	03c12403          	lw	s0,60(sp)
  ac:	04010113          	addi	sp,sp,64
  b0:	00008067          	ret

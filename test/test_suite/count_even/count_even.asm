
test_suite/count_even/count_even.elf:     file format elf32-littleriscv


Disassembly of section .text:

00000000 <_start>:
   0:	00020137          	lui	sp,0x20
   4:	00c000ef          	jal	ra,10 <main>
   8:	00100073          	ebreak

0000000c <__main_loop>:
   c:	0000006f          	j	c <__main_loop>

00000010 <main>:
  10:	fb010113          	addi	sp,sp,-80 # 1ffb0 <main+0x1ffa0>
  14:	04812623          	sw	s0,76(sp)
  18:	05010413          	addi	s0,sp,80
  1c:	000027b7          	lui	a5,0x2
  20:	00078793          	mv	a5,a5
  24:	0007ae03          	lw	t3,0(a5) # 2000 <main+0x1ff0>
  28:	0047a303          	lw	t1,4(a5)
  2c:	0087a883          	lw	a7,8(a5)
  30:	00c7a803          	lw	a6,12(a5)
  34:	0107a503          	lw	a0,16(a5)
  38:	0147a583          	lw	a1,20(a5)
  3c:	0187a603          	lw	a2,24(a5)
  40:	01c7a683          	lw	a3,28(a5)
  44:	0207a703          	lw	a4,32(a5)
  48:	0247a783          	lw	a5,36(a5)
  4c:	fbc42e23          	sw	t3,-68(s0)
  50:	fc642023          	sw	t1,-64(s0)
  54:	fd142223          	sw	a7,-60(s0)
  58:	fd042423          	sw	a6,-56(s0)
  5c:	fca42623          	sw	a0,-52(s0)
  60:	fcb42823          	sw	a1,-48(s0)
  64:	fcc42a23          	sw	a2,-44(s0)
  68:	fcd42c23          	sw	a3,-40(s0)
  6c:	fce42e23          	sw	a4,-36(s0)
  70:	fef42023          	sw	a5,-32(s0)
  74:	00a00793          	li	a5,10
  78:	fef42223          	sw	a5,-28(s0)
  7c:	fe042623          	sw	zero,-20(s0)
  80:	fe042423          	sw	zero,-24(s0)
  84:	0380006f          	j	bc <main+0xac>
  88:	fe842783          	lw	a5,-24(s0)
  8c:	00279793          	slli	a5,a5,0x2
  90:	ff040713          	addi	a4,s0,-16
  94:	00f707b3          	add	a5,a4,a5
  98:	fcc7a783          	lw	a5,-52(a5)
  9c:	0017f793          	andi	a5,a5,1
  a0:	00079863          	bnez	a5,b0 <main+0xa0>
  a4:	fec42783          	lw	a5,-20(s0)
  a8:	00178793          	addi	a5,a5,1
  ac:	fef42623          	sw	a5,-20(s0)
  b0:	fe842783          	lw	a5,-24(s0)
  b4:	00178793          	addi	a5,a5,1
  b8:	fef42423          	sw	a5,-24(s0)
  bc:	fe842703          	lw	a4,-24(s0)
  c0:	fe442783          	lw	a5,-28(s0)
  c4:	fcf742e3          	blt	a4,a5,88 <main+0x78>
  c8:	fec42783          	lw	a5,-20(s0)
  cc:	00078513          	mv	a0,a5
  d0:	04c12403          	lw	s0,76(sp)
  d4:	05010113          	addi	sp,sp,80
  d8:	00008067          	ret

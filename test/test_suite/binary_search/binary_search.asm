
/home/louhao/System-2025/RISC-V-CPU-simulator/test/test_suite/binary_search/binary_search.elf:     file format elf32-littleriscv


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
  4c:	fbc42823          	sw	t3,-80(s0)
  50:	fa642a23          	sw	t1,-76(s0)
  54:	fb142c23          	sw	a7,-72(s0)
  58:	fb042e23          	sw	a6,-68(s0)
  5c:	fca42023          	sw	a0,-64(s0)
  60:	fcb42223          	sw	a1,-60(s0)
  64:	fcc42423          	sw	a2,-56(s0)
  68:	fcd42623          	sw	a3,-52(s0)
  6c:	fce42823          	sw	a4,-48(s0)
  70:	fcf42a23          	sw	a5,-44(s0)
  74:	00d00793          	li	a5,13
  78:	fef42023          	sw	a5,-32(s0)
  7c:	00a00793          	li	a5,10
  80:	fcf42e23          	sw	a5,-36(s0)
  84:	fe042623          	sw	zero,-20(s0)
  88:	fdc42783          	lw	a5,-36(s0)
  8c:	fff78793          	addi	a5,a5,-1
  90:	fef42423          	sw	a5,-24(s0)
  94:	fff00793          	li	a5,-1
  98:	fef42223          	sw	a5,-28(s0)
  9c:	0800006f          	j	11c <main+0x10c>
  a0:	fe842703          	lw	a4,-24(s0)
  a4:	fec42783          	lw	a5,-20(s0)
  a8:	40f707b3          	sub	a5,a4,a5
  ac:	4017d793          	srai	a5,a5,0x1
  b0:	fec42703          	lw	a4,-20(s0)
  b4:	00f707b3          	add	a5,a4,a5
  b8:	fcf42c23          	sw	a5,-40(s0)
  bc:	fd842783          	lw	a5,-40(s0)
  c0:	00279793          	slli	a5,a5,0x2
  c4:	ff040713          	addi	a4,s0,-16
  c8:	00f707b3          	add	a5,a4,a5
  cc:	fc07a783          	lw	a5,-64(a5)
  d0:	fe042703          	lw	a4,-32(s0)
  d4:	00f71863          	bne	a4,a5,e4 <main+0xd4>
  d8:	fd842783          	lw	a5,-40(s0)
  dc:	fef42223          	sw	a5,-28(s0)
  e0:	0480006f          	j	128 <main+0x118>
  e4:	fd842783          	lw	a5,-40(s0)
  e8:	00279793          	slli	a5,a5,0x2
  ec:	ff040713          	addi	a4,s0,-16
  f0:	00f707b3          	add	a5,a4,a5
  f4:	fc07a783          	lw	a5,-64(a5)
  f8:	fe042703          	lw	a4,-32(s0)
  fc:	00e7da63          	bge	a5,a4,110 <main+0x100>
 100:	fd842783          	lw	a5,-40(s0)
 104:	00178793          	addi	a5,a5,1
 108:	fef42623          	sw	a5,-20(s0)
 10c:	0100006f          	j	11c <main+0x10c>
 110:	fd842783          	lw	a5,-40(s0)
 114:	fff78793          	addi	a5,a5,-1
 118:	fef42423          	sw	a5,-24(s0)
 11c:	fec42703          	lw	a4,-20(s0)
 120:	fe842783          	lw	a5,-24(s0)
 124:	f6e7dee3          	bge	a5,a4,a0 <main+0x90>
 128:	fe442783          	lw	a5,-28(s0)
 12c:	00078513          	mv	a0,a5
 130:	04c12403          	lw	s0,76(sp)
 134:	05010113          	addi	sp,sp,80
 138:	00008067          	ret

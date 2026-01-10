
/home/louhao/System-2025/RISC-V-CPU-simulator/test/test_suite/reverse/reverse.elf:     file format elf32-littleriscv


Disassembly of section .text:

00000000 <_start>:
   0:	00020137          	lui	sp,0x20
   4:	00c000ef          	jal	ra,10 <main>
   8:	00100073          	ebreak

0000000c <__main_loop>:
   c:	0000006f          	j	c <__main_loop>

00000010 <main>:
  10:	fd010113          	addi	sp,sp,-48 # 1ffd0 <main+0x1ffc0>
  14:	02812623          	sw	s0,44(sp)
  18:	03010413          	addi	s0,sp,48
  1c:	000027b7          	lui	a5,0x2
  20:	00078793          	mv	a5,a5
  24:	0007a583          	lw	a1,0(a5) # 2000 <main+0x1ff0>
  28:	0047a603          	lw	a2,4(a5)
  2c:	0087a683          	lw	a3,8(a5)
  30:	00c7a703          	lw	a4,12(a5)
  34:	0107a783          	lw	a5,16(a5)
  38:	fcb42823          	sw	a1,-48(s0)
  3c:	fcc42a23          	sw	a2,-44(s0)
  40:	fcd42c23          	sw	a3,-40(s0)
  44:	fce42e23          	sw	a4,-36(s0)
  48:	fef42023          	sw	a5,-32(s0)
  4c:	00500793          	li	a5,5
  50:	fef42423          	sw	a5,-24(s0)
  54:	fe042623          	sw	zero,-20(s0)
  58:	0800006f          	j	d8 <main+0xc8>
  5c:	fec42783          	lw	a5,-20(s0)
  60:	00279793          	slli	a5,a5,0x2
  64:	ff040713          	addi	a4,s0,-16
  68:	00f707b3          	add	a5,a4,a5
  6c:	fe07a783          	lw	a5,-32(a5)
  70:	fef42223          	sw	a5,-28(s0)
  74:	fe842783          	lw	a5,-24(s0)
  78:	fff78713          	addi	a4,a5,-1
  7c:	fec42783          	lw	a5,-20(s0)
  80:	40f707b3          	sub	a5,a4,a5
  84:	00279793          	slli	a5,a5,0x2
  88:	ff040713          	addi	a4,s0,-16
  8c:	00f707b3          	add	a5,a4,a5
  90:	fe07a703          	lw	a4,-32(a5)
  94:	fec42783          	lw	a5,-20(s0)
  98:	00279793          	slli	a5,a5,0x2
  9c:	ff040693          	addi	a3,s0,-16
  a0:	00f687b3          	add	a5,a3,a5
  a4:	fee7a023          	sw	a4,-32(a5)
  a8:	fe842783          	lw	a5,-24(s0)
  ac:	fff78713          	addi	a4,a5,-1
  b0:	fec42783          	lw	a5,-20(s0)
  b4:	40f707b3          	sub	a5,a4,a5
  b8:	00279793          	slli	a5,a5,0x2
  bc:	ff040713          	addi	a4,s0,-16
  c0:	00f707b3          	add	a5,a4,a5
  c4:	fe442703          	lw	a4,-28(s0)
  c8:	fee7a023          	sw	a4,-32(a5)
  cc:	fec42783          	lw	a5,-20(s0)
  d0:	00178793          	addi	a5,a5,1
  d4:	fef42623          	sw	a5,-20(s0)
  d8:	fe842783          	lw	a5,-24(s0)
  dc:	01f7d713          	srli	a4,a5,0x1f
  e0:	00f707b3          	add	a5,a4,a5
  e4:	4017d793          	srai	a5,a5,0x1
  e8:	00078713          	mv	a4,a5
  ec:	fec42783          	lw	a5,-20(s0)
  f0:	f6e7c6e3          	blt	a5,a4,5c <main+0x4c>
  f4:	fd042783          	lw	a5,-48(s0)
  f8:	00078513          	mv	a0,a5
  fc:	02c12403          	lw	s0,44(sp)
 100:	03010113          	addi	sp,sp,48
 104:	00008067          	ret

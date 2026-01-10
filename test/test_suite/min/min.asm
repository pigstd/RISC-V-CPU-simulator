
/home/louhao/System-2025/RISC-V-CPU-simulator/test/test_suite/min/min.elf:     file format elf32-littleriscv


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
  24:	0007a883          	lw	a7,0(a5) # 2000 <main+0x1ff0>
  28:	0047a803          	lw	a6,4(a5)
  2c:	0087a503          	lw	a0,8(a5)
  30:	00c7a583          	lw	a1,12(a5)
  34:	0107a603          	lw	a2,16(a5)
  38:	0147a683          	lw	a3,20(a5)
  3c:	0187a703          	lw	a4,24(a5)
  40:	01c7a783          	lw	a5,28(a5)
  44:	fd142223          	sw	a7,-60(s0)
  48:	fd042423          	sw	a6,-56(s0)
  4c:	fca42623          	sw	a0,-52(s0)
  50:	fcb42823          	sw	a1,-48(s0)
  54:	fcc42a23          	sw	a2,-44(s0)
  58:	fcd42c23          	sw	a3,-40(s0)
  5c:	fce42e23          	sw	a4,-36(s0)
  60:	fef42023          	sw	a5,-32(s0)
  64:	00800793          	li	a5,8
  68:	fef42223          	sw	a5,-28(s0)
  6c:	fc442783          	lw	a5,-60(s0)
  70:	fef42623          	sw	a5,-20(s0)
  74:	00100793          	li	a5,1
  78:	fef42423          	sw	a5,-24(s0)
  7c:	0440006f          	j	c0 <main+0xb0>
  80:	fe842783          	lw	a5,-24(s0)
  84:	00279793          	slli	a5,a5,0x2
  88:	ff040713          	addi	a4,s0,-16
  8c:	00f707b3          	add	a5,a4,a5
  90:	fd47a783          	lw	a5,-44(a5)
  94:	fec42703          	lw	a4,-20(s0)
  98:	00e7de63          	bge	a5,a4,b4 <main+0xa4>
  9c:	fe842783          	lw	a5,-24(s0)
  a0:	00279793          	slli	a5,a5,0x2
  a4:	ff040713          	addi	a4,s0,-16
  a8:	00f707b3          	add	a5,a4,a5
  ac:	fd47a783          	lw	a5,-44(a5)
  b0:	fef42623          	sw	a5,-20(s0)
  b4:	fe842783          	lw	a5,-24(s0)
  b8:	00178793          	addi	a5,a5,1
  bc:	fef42423          	sw	a5,-24(s0)
  c0:	fe842703          	lw	a4,-24(s0)
  c4:	fe442783          	lw	a5,-28(s0)
  c8:	faf74ce3          	blt	a4,a5,80 <main+0x70>
  cc:	fec42783          	lw	a5,-20(s0)
  d0:	00078513          	mv	a0,a5
  d4:	03c12403          	lw	s0,60(sp)
  d8:	04010113          	addi	sp,sp,64
  dc:	00008067          	ret

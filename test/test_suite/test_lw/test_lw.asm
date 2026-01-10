
/home/louhao/System-2025/RISC-V-CPU-simulator/test/test_suite/test_lw/test_lw.elf:     file format elf32-littleriscv


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
  1c:	06400793          	li	a5,100
  20:	fcf42c23          	sw	a5,-40(s0)
  24:	0c800793          	li	a5,200
  28:	fcf42e23          	sw	a5,-36(s0)
  2c:	12c00793          	li	a5,300
  30:	fef42023          	sw	a5,-32(s0)
  34:	fce00793          	li	a5,-50
  38:	fef42223          	sw	a5,-28(s0)
  3c:	000037b7          	lui	a5,0x3
  40:	03978793          	addi	a5,a5,57 # 3039 <main+0x3029>
  44:	fef42423          	sw	a5,-24(s0)
  48:	fe042623          	sw	zero,-20(s0)
  4c:	fd842783          	lw	a5,-40(s0)
  50:	fec42703          	lw	a4,-20(s0)
  54:	00f707b3          	add	a5,a4,a5
  58:	fef42623          	sw	a5,-20(s0)
  5c:	fdc42783          	lw	a5,-36(s0)
  60:	fec42703          	lw	a4,-20(s0)
  64:	00f707b3          	add	a5,a4,a5
  68:	fef42623          	sw	a5,-20(s0)
  6c:	fe042783          	lw	a5,-32(s0)
  70:	fec42703          	lw	a4,-20(s0)
  74:	00f707b3          	add	a5,a4,a5
  78:	fef42623          	sw	a5,-20(s0)
  7c:	fe442783          	lw	a5,-28(s0)
  80:	fec42703          	lw	a4,-20(s0)
  84:	00f707b3          	add	a5,a4,a5
  88:	fef42623          	sw	a5,-20(s0)
  8c:	fe842783          	lw	a5,-24(s0)
  90:	fec42703          	lw	a4,-20(s0)
  94:	00f707b3          	add	a5,a4,a5
  98:	fef42623          	sw	a5,-20(s0)
  9c:	fec42703          	lw	a4,-20(s0)
  a0:	000037b7          	lui	a5,0x3
  a4:	25f78793          	addi	a5,a5,607 # 325f <main+0x324f>
  a8:	00f71663          	bne	a4,a5,b4 <main+0xa4>
  ac:	00100793          	li	a5,1
  b0:	0080006f          	j	b8 <main+0xa8>
  b4:	00000793          	li	a5,0
  b8:	00078513          	mv	a0,a5
  bc:	02c12403          	lw	s0,44(sp)
  c0:	03010113          	addi	sp,sp,48
  c4:	00008067          	ret


/home/louhao/System-2025/RISC-V-CPU-simulator/test/test_suite/test_lb/test_lb.elf:     file format elf32-littleriscv


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
  1c:	00a00793          	li	a5,10
  20:	fcf42e23          	sw	a5,-36(s0)
  24:	01400793          	li	a5,20
  28:	fef42023          	sw	a5,-32(s0)
  2c:	01e00793          	li	a5,30
  30:	fef42223          	sw	a5,-28(s0)
  34:	02800793          	li	a5,40
  38:	fef42423          	sw	a5,-24(s0)
  3c:	fe042623          	sw	zero,-20(s0)
  40:	fdc42783          	lw	a5,-36(s0)
  44:	fec42703          	lw	a4,-20(s0)
  48:	00f707b3          	add	a5,a4,a5
  4c:	fef42623          	sw	a5,-20(s0)
  50:	fe042783          	lw	a5,-32(s0)
  54:	fec42703          	lw	a4,-20(s0)
  58:	00f707b3          	add	a5,a4,a5
  5c:	fef42623          	sw	a5,-20(s0)
  60:	fe442783          	lw	a5,-28(s0)
  64:	fec42703          	lw	a4,-20(s0)
  68:	00f707b3          	add	a5,a4,a5
  6c:	fef42623          	sw	a5,-20(s0)
  70:	fe842783          	lw	a5,-24(s0)
  74:	fec42703          	lw	a4,-20(s0)
  78:	00f707b3          	add	a5,a4,a5
  7c:	fef42623          	sw	a5,-20(s0)
  80:	fec42783          	lw	a5,-20(s0)
  84:	00078513          	mv	a0,a5
  88:	02c12403          	lw	s0,44(sp)
  8c:	03010113          	addi	sp,sp,48
  90:	00008067          	ret

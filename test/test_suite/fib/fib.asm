
/home/louhao/System-2025/RISC-V-CPU-simulator/test/test_suite/fib/fib.elf:     file format elf32-littleriscv


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
  24:	fe042623          	sw	zero,-20(s0)
  28:	00100793          	li	a5,1
  2c:	fef42423          	sw	a5,-24(s0)
  30:	fe042223          	sw	zero,-28(s0)
  34:	fdc42783          	lw	a5,-36(s0)
  38:	00079863          	bnez	a5,48 <main+0x38>
  3c:	fec42783          	lw	a5,-20(s0)
  40:	fef42223          	sw	a5,-28(s0)
  44:	0600006f          	j	a4 <main+0x94>
  48:	fdc42703          	lw	a4,-36(s0)
  4c:	00100793          	li	a5,1
  50:	00f71863          	bne	a4,a5,60 <main+0x50>
  54:	fe842783          	lw	a5,-24(s0)
  58:	fef42223          	sw	a5,-28(s0)
  5c:	0480006f          	j	a4 <main+0x94>
  60:	00200793          	li	a5,2
  64:	fef42023          	sw	a5,-32(s0)
  68:	0300006f          	j	98 <main+0x88>
  6c:	fec42703          	lw	a4,-20(s0)
  70:	fe842783          	lw	a5,-24(s0)
  74:	00f707b3          	add	a5,a4,a5
  78:	fef42223          	sw	a5,-28(s0)
  7c:	fe842783          	lw	a5,-24(s0)
  80:	fef42623          	sw	a5,-20(s0)
  84:	fe442783          	lw	a5,-28(s0)
  88:	fef42423          	sw	a5,-24(s0)
  8c:	fe042783          	lw	a5,-32(s0)
  90:	00178793          	addi	a5,a5,1
  94:	fef42023          	sw	a5,-32(s0)
  98:	fe042703          	lw	a4,-32(s0)
  9c:	fdc42783          	lw	a5,-36(s0)
  a0:	fce7d6e3          	bge	a5,a4,6c <main+0x5c>
  a4:	fe442783          	lw	a5,-28(s0)
  a8:	00078513          	mv	a0,a5
  ac:	02c12403          	lw	s0,44(sp)
  b0:	03010113          	addi	sp,sp,48
  b4:	00008067          	ret


/home/louhao/System-2025/RISC-V-CPU-simulator/test/test_suite/test_sw/test_sw.elf:     file format elf32-littleriscv


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
  1c:	000187b7          	lui	a5,0x18
  20:	6a078793          	addi	a5,a5,1696 # 186a0 <main+0x18690>
  24:	fcf42e23          	sw	a5,-36(s0)
  28:	000317b7          	lui	a5,0x31
  2c:	d4078793          	addi	a5,a5,-704 # 30d40 <main+0x30d30>
  30:	fef42023          	sw	a5,-32(s0)
  34:	ffff47b7          	lui	a5,0xffff4
  38:	cb078793          	addi	a5,a5,-848 # ffff3cb0 <main+0xffff3ca0>
  3c:	fef42223          	sw	a5,-28(s0)
  40:	000037b7          	lui	a5,0x3
  44:	03978793          	addi	a5,a5,57 # 3039 <main+0x3029>
  48:	fef42423          	sw	a5,-24(s0)
  4c:	fe042623          	sw	zero,-20(s0)
  50:	fdc42783          	lw	a5,-36(s0)
  54:	fec42703          	lw	a4,-20(s0)
  58:	00f707b3          	add	a5,a4,a5
  5c:	fef42623          	sw	a5,-20(s0)
  60:	fe042783          	lw	a5,-32(s0)
  64:	fec42703          	lw	a4,-20(s0)
  68:	00f707b3          	add	a5,a4,a5
  6c:	fef42623          	sw	a5,-20(s0)
  70:	fe442783          	lw	a5,-28(s0)
  74:	fec42703          	lw	a4,-20(s0)
  78:	00f707b3          	add	a5,a4,a5
  7c:	fef42623          	sw	a5,-20(s0)
  80:	fe842783          	lw	a5,-24(s0)
  84:	fec42703          	lw	a4,-20(s0)
  88:	00f707b3          	add	a5,a4,a5
  8c:	fef42623          	sw	a5,-20(s0)
  90:	fec42703          	lw	a4,-20(s0)
  94:	000407b7          	lui	a5,0x40
  98:	0c978793          	addi	a5,a5,201 # 400c9 <main+0x400b9>
  9c:	00f71663          	bne	a4,a5,a8 <main+0x98>
  a0:	00100793          	li	a5,1
  a4:	0080006f          	j	ac <main+0x9c>
  a8:	00000793          	li	a5,0
  ac:	00078513          	mv	a0,a5
  b0:	02c12403          	lw	s0,44(sp)
  b4:	03010113          	addi	sp,sp,48
  b8:	00008067          	ret

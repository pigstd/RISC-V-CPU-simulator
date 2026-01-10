
/home/louhao/System-2025/RISC-V-CPU-simulator/test/test_suite/factorial/factorial.elf:     file format elf32-littleriscv


Disassembly of section .text:

00000000 <_start>:
   0:	00020137          	lui	sp,0x20
   4:	0d8000ef          	jal	ra,dc <main>
   8:	00100073          	ebreak

0000000c <__main_loop>:
   c:	0000006f          	j	c <__main_loop>

00000010 <multiply>:
  10:	fd010113          	addi	sp,sp,-48 # 1ffd0 <main+0x1fef4>
  14:	02812623          	sw	s0,44(sp)
  18:	03010413          	addi	s0,sp,48
  1c:	fca42e23          	sw	a0,-36(s0)
  20:	fcb42c23          	sw	a1,-40(s0)
  24:	fe042623          	sw	zero,-20(s0)
  28:	fe042423          	sw	zero,-24(s0)
  2c:	fdc42783          	lw	a5,-36(s0)
  30:	0207d063          	bgez	a5,50 <multiply+0x40>
  34:	fdc42783          	lw	a5,-36(s0)
  38:	40f007b3          	neg	a5,a5
  3c:	fcf42e23          	sw	a5,-36(s0)
  40:	fe842783          	lw	a5,-24(s0)
  44:	0017b793          	seqz	a5,a5
  48:	0ff7f793          	andi	a5,a5,255
  4c:	fef42423          	sw	a5,-24(s0)
  50:	fd842783          	lw	a5,-40(s0)
  54:	0407dc63          	bgez	a5,ac <multiply+0x9c>
  58:	fd842783          	lw	a5,-40(s0)
  5c:	40f007b3          	neg	a5,a5
  60:	fcf42c23          	sw	a5,-40(s0)
  64:	fe842783          	lw	a5,-24(s0)
  68:	0017b793          	seqz	a5,a5
  6c:	0ff7f793          	andi	a5,a5,255
  70:	fef42423          	sw	a5,-24(s0)
  74:	0380006f          	j	ac <multiply+0x9c>
  78:	fd842783          	lw	a5,-40(s0)
  7c:	0017f793          	andi	a5,a5,1
  80:	00078a63          	beqz	a5,94 <multiply+0x84>
  84:	fec42703          	lw	a4,-20(s0)
  88:	fdc42783          	lw	a5,-36(s0)
  8c:	00f707b3          	add	a5,a4,a5
  90:	fef42623          	sw	a5,-20(s0)
  94:	fdc42783          	lw	a5,-36(s0)
  98:	00179793          	slli	a5,a5,0x1
  9c:	fcf42e23          	sw	a5,-36(s0)
  a0:	fd842783          	lw	a5,-40(s0)
  a4:	4017d793          	srai	a5,a5,0x1
  a8:	fcf42c23          	sw	a5,-40(s0)
  ac:	fd842783          	lw	a5,-40(s0)
  b0:	fc0794e3          	bnez	a5,78 <multiply+0x68>
  b4:	fe842783          	lw	a5,-24(s0)
  b8:	00078863          	beqz	a5,c8 <multiply+0xb8>
  bc:	fec42783          	lw	a5,-20(s0)
  c0:	40f007b3          	neg	a5,a5
  c4:	0080006f          	j	cc <multiply+0xbc>
  c8:	fec42783          	lw	a5,-20(s0)
  cc:	00078513          	mv	a0,a5
  d0:	02c12403          	lw	s0,44(sp)
  d4:	03010113          	addi	sp,sp,48
  d8:	00008067          	ret

000000dc <main>:
  dc:	fe010113          	addi	sp,sp,-32
  e0:	00112e23          	sw	ra,28(sp)
  e4:	00812c23          	sw	s0,24(sp)
  e8:	02010413          	addi	s0,sp,32
  ec:	00500793          	li	a5,5
  f0:	fef42223          	sw	a5,-28(s0)
  f4:	00100793          	li	a5,1
  f8:	fef42623          	sw	a5,-20(s0)
  fc:	00100793          	li	a5,1
 100:	fef42423          	sw	a5,-24(s0)
 104:	0200006f          	j	124 <main+0x48>
 108:	fe842583          	lw	a1,-24(s0)
 10c:	fec42503          	lw	a0,-20(s0)
 110:	f01ff0ef          	jal	ra,10 <multiply>
 114:	fea42623          	sw	a0,-20(s0)
 118:	fe842783          	lw	a5,-24(s0)
 11c:	00178793          	addi	a5,a5,1
 120:	fef42423          	sw	a5,-24(s0)
 124:	fe842703          	lw	a4,-24(s0)
 128:	fe442783          	lw	a5,-28(s0)
 12c:	fce7dee3          	bge	a5,a4,108 <main+0x2c>
 130:	fec42783          	lw	a5,-20(s0)
 134:	00078513          	mv	a0,a5
 138:	01c12083          	lw	ra,28(sp)
 13c:	01812403          	lw	s0,24(sp)
 140:	02010113          	addi	sp,sp,32
 144:	00008067          	ret

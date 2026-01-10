
/home/louhao/System-2025/RISC-V-CPU-simulator/test/test_suite/vector_mul_100/vector_mul_100.elf:     file format elf32-littleriscv


Disassembly of section .text:

00000000 <_start>:
   0:	00020137          	lui	sp,0x20
   4:	0d8000ef          	jal	ra,dc <main>
   8:	00100073          	ebreak

0000000c <__main_loop>:
   c:	0000006f          	j	c <__main_loop>

00000010 <multiply>:
  10:	fd010113          	addi	sp,sp,-48 # 1ffd0 <C+0x1db20>
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
  ec:	06400793          	li	a5,100
  f0:	fef42023          	sw	a5,-32(s0)
  f4:	fe042623          	sw	zero,-20(s0)
  f8:	0680006f          	j	160 <main+0x84>
  fc:	000027b7          	lui	a5,0x2
 100:	00078713          	mv	a4,a5
 104:	fec42783          	lw	a5,-20(s0)
 108:	00279793          	slli	a5,a5,0x2
 10c:	00f707b3          	add	a5,a4,a5
 110:	0007a683          	lw	a3,0(a5) # 2000 <A>
 114:	000027b7          	lui	a5,0x2
 118:	19078713          	addi	a4,a5,400 # 2190 <B>
 11c:	fec42783          	lw	a5,-20(s0)
 120:	00279793          	slli	a5,a5,0x2
 124:	00f707b3          	add	a5,a4,a5
 128:	0007a783          	lw	a5,0(a5)
 12c:	00078593          	mv	a1,a5
 130:	00068513          	mv	a0,a3
 134:	eddff0ef          	jal	ra,10 <multiply>
 138:	00050693          	mv	a3,a0
 13c:	000027b7          	lui	a5,0x2
 140:	4b078713          	addi	a4,a5,1200 # 24b0 <C>
 144:	fec42783          	lw	a5,-20(s0)
 148:	00279793          	slli	a5,a5,0x2
 14c:	00f707b3          	add	a5,a4,a5
 150:	00d7a023          	sw	a3,0(a5)
 154:	fec42783          	lw	a5,-20(s0)
 158:	00178793          	addi	a5,a5,1
 15c:	fef42623          	sw	a5,-20(s0)
 160:	fec42703          	lw	a4,-20(s0)
 164:	fe042783          	lw	a5,-32(s0)
 168:	f8f74ae3          	blt	a4,a5,fc <main+0x20>
 16c:	fe042423          	sw	zero,-24(s0)
 170:	fe042223          	sw	zero,-28(s0)
 174:	0500006f          	j	1c4 <main+0xe8>
 178:	000027b7          	lui	a5,0x2
 17c:	4b078713          	addi	a4,a5,1200 # 24b0 <C>
 180:	fe442783          	lw	a5,-28(s0)
 184:	00279793          	slli	a5,a5,0x2
 188:	00f707b3          	add	a5,a4,a5
 18c:	0007a703          	lw	a4,0(a5)
 190:	000027b7          	lui	a5,0x2
 194:	32078693          	addi	a3,a5,800 # 2320 <expected>
 198:	fe442783          	lw	a5,-28(s0)
 19c:	00279793          	slli	a5,a5,0x2
 1a0:	00f687b3          	add	a5,a3,a5
 1a4:	0007a783          	lw	a5,0(a5)
 1a8:	00f71863          	bne	a4,a5,1b8 <main+0xdc>
 1ac:	fe842783          	lw	a5,-24(s0)
 1b0:	00178793          	addi	a5,a5,1
 1b4:	fef42423          	sw	a5,-24(s0)
 1b8:	fe442783          	lw	a5,-28(s0)
 1bc:	00178793          	addi	a5,a5,1
 1c0:	fef42223          	sw	a5,-28(s0)
 1c4:	fe442703          	lw	a4,-28(s0)
 1c8:	fe042783          	lw	a5,-32(s0)
 1cc:	faf746e3          	blt	a4,a5,178 <main+0x9c>
 1d0:	fe842783          	lw	a5,-24(s0)
 1d4:	00078513          	mv	a0,a5
 1d8:	01c12083          	lw	ra,28(sp)
 1dc:	01812403          	lw	s0,24(sp)
 1e0:	02010113          	addi	sp,sp,32
 1e4:	00008067          	ret

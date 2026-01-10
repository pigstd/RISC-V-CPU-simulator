
/home/louhao/System-2025/RISC-V-CPU-simulator/test/test_suite/overflow/overflow.elf:     file format elf32-littleriscv


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
  dc:	fa010113          	addi	sp,sp,-96
  e0:	04112e23          	sw	ra,92(sp)
  e4:	04812c23          	sw	s0,88(sp)
  e8:	06010413          	addi	s0,sp,96
  ec:	fe042623          	sw	zero,-20(s0)
  f0:	800007b7          	lui	a5,0x80000
  f4:	fff7c793          	not	a5,a5
  f8:	fef42023          	sw	a5,-32(s0)
  fc:	fe042783          	lw	a5,-32(s0)
 100:	00178793          	addi	a5,a5,1 # 80000001 <main+0x7fffff25>
 104:	fcf42e23          	sw	a5,-36(s0)
 108:	fdc42703          	lw	a4,-36(s0)
 10c:	800007b7          	lui	a5,0x80000
 110:	00f71863          	bne	a4,a5,120 <main+0x44>
 114:	fec42783          	lw	a5,-20(s0)
 118:	00178793          	addi	a5,a5,1 # 80000001 <main+0x7fffff25>
 11c:	fef42623          	sw	a5,-20(s0)
 120:	773597b7          	lui	a5,0x77359
 124:	40078793          	addi	a5,a5,1024 # 77359400 <main+0x77359324>
 128:	fcf42c23          	sw	a5,-40(s0)
 12c:	773597b7          	lui	a5,0x77359
 130:	40078793          	addi	a5,a5,1024 # 77359400 <main+0x77359324>
 134:	fcf42a23          	sw	a5,-44(s0)
 138:	fd842703          	lw	a4,-40(s0)
 13c:	fd442783          	lw	a5,-44(s0)
 140:	00f707b3          	add	a5,a4,a5
 144:	fcf42823          	sw	a5,-48(s0)
 148:	fd042703          	lw	a4,-48(s0)
 14c:	ee6b37b7          	lui	a5,0xee6b3
 150:	80078793          	addi	a5,a5,-2048 # ee6b2800 <main+0xee6b2724>
 154:	00f71863          	bne	a4,a5,164 <main+0x88>
 158:	fec42783          	lw	a5,-20(s0)
 15c:	00178793          	addi	a5,a5,1
 160:	fef42623          	sw	a5,-20(s0)
 164:	800007b7          	lui	a5,0x80000
 168:	fcf42623          	sw	a5,-52(s0)
 16c:	fcc42783          	lw	a5,-52(s0)
 170:	fff78793          	addi	a5,a5,-1 # 7fffffff <main+0x7fffff23>
 174:	fcf42423          	sw	a5,-56(s0)
 178:	fc842703          	lw	a4,-56(s0)
 17c:	800007b7          	lui	a5,0x80000
 180:	fff7c793          	not	a5,a5
 184:	00f71863          	bne	a4,a5,194 <main+0xb8>
 188:	fec42783          	lw	a5,-20(s0)
 18c:	00178793          	addi	a5,a5,1 # 80000001 <main+0x7fffff25>
 190:	fef42623          	sw	a5,-20(s0)
 194:	000187b7          	lui	a5,0x18
 198:	6a078793          	addi	a5,a5,1696 # 186a0 <main+0x185c4>
 19c:	fcf42223          	sw	a5,-60(s0)
 1a0:	000187b7          	lui	a5,0x18
 1a4:	6a078793          	addi	a5,a5,1696 # 186a0 <main+0x185c4>
 1a8:	fcf42023          	sw	a5,-64(s0)
 1ac:	fc042583          	lw	a1,-64(s0)
 1b0:	fc442503          	lw	a0,-60(s0)
 1b4:	e5dff0ef          	jal	ra,10 <multiply>
 1b8:	faa42e23          	sw	a0,-68(s0)
 1bc:	fbc42703          	lw	a4,-68(s0)
 1c0:	540be7b7          	lui	a5,0x540be
 1c4:	40078793          	addi	a5,a5,1024 # 540be400 <main+0x540be324>
 1c8:	00f71863          	bne	a4,a5,1d8 <main+0xfc>
 1cc:	fec42783          	lw	a5,-20(s0)
 1d0:	00178793          	addi	a5,a5,1
 1d4:	fef42623          	sw	a5,-20(s0)
 1d8:	0000c7b7          	lui	a5,0xc
 1dc:	35078793          	addi	a5,a5,848 # c350 <main+0xc274>
 1e0:	faf42c23          	sw	a5,-72(s0)
 1e4:	0000c7b7          	lui	a5,0xc
 1e8:	35078793          	addi	a5,a5,848 # c350 <main+0xc274>
 1ec:	faf42a23          	sw	a5,-76(s0)
 1f0:	fb442583          	lw	a1,-76(s0)
 1f4:	fb842503          	lw	a0,-72(s0)
 1f8:	e19ff0ef          	jal	ra,10 <multiply>
 1fc:	faa42823          	sw	a0,-80(s0)
 200:	fb042703          	lw	a4,-80(s0)
 204:	950307b7          	lui	a5,0x95030
 208:	90078793          	addi	a5,a5,-1792 # 9502f900 <main+0x9502f824>
 20c:	00f71863          	bne	a4,a5,21c <main+0x140>
 210:	fec42783          	lw	a5,-20(s0)
 214:	00178793          	addi	a5,a5,1
 218:	fef42623          	sw	a5,-20(s0)
 21c:	400007b7          	lui	a5,0x40000
 220:	faf42623          	sw	a5,-84(s0)
 224:	fac42783          	lw	a5,-84(s0)
 228:	00179793          	slli	a5,a5,0x1
 22c:	faf42623          	sw	a5,-84(s0)
 230:	fac42783          	lw	a5,-84(s0)
 234:	00179793          	slli	a5,a5,0x1
 238:	faf42623          	sw	a5,-84(s0)
 23c:	fac42783          	lw	a5,-84(s0)
 240:	00079863          	bnez	a5,250 <main+0x174>
 244:	fec42783          	lw	a5,-20(s0)
 248:	00178793          	addi	a5,a5,1 # 40000001 <main+0x3fffff25>
 24c:	fef42623          	sw	a5,-20(s0)
 250:	00100793          	li	a5,1
 254:	fef42423          	sw	a5,-24(s0)
 258:	fe042223          	sw	zero,-28(s0)
 25c:	01c0006f          	j	278 <main+0x19c>
 260:	fe842783          	lw	a5,-24(s0)
 264:	00179793          	slli	a5,a5,0x1
 268:	fef42423          	sw	a5,-24(s0)
 26c:	fe442783          	lw	a5,-28(s0)
 270:	00178793          	addi	a5,a5,1
 274:	fef42223          	sw	a5,-28(s0)
 278:	fe442703          	lw	a4,-28(s0)
 27c:	01e00793          	li	a5,30
 280:	fee7d0e3          	bge	a5,a4,260 <main+0x184>
 284:	fe842703          	lw	a4,-24(s0)
 288:	800007b7          	lui	a5,0x80000
 28c:	00f71863          	bne	a4,a5,29c <main+0x1c0>
 290:	fec42783          	lw	a5,-20(s0)
 294:	00178793          	addi	a5,a5,1 # 80000001 <main+0x7fffff25>
 298:	fef42623          	sw	a5,-20(s0)
 29c:	800007b7          	lui	a5,0x80000
 2a0:	faf42423          	sw	a5,-88(s0)
 2a4:	fff00793          	li	a5,-1
 2a8:	faf42223          	sw	a5,-92(s0)
 2ac:	fa442583          	lw	a1,-92(s0)
 2b0:	fa842503          	lw	a0,-88(s0)
 2b4:	d5dff0ef          	jal	ra,10 <multiply>
 2b8:	faa42023          	sw	a0,-96(s0)
 2bc:	fa042703          	lw	a4,-96(s0)
 2c0:	800007b7          	lui	a5,0x80000
 2c4:	00f71863          	bne	a4,a5,2d4 <main+0x1f8>
 2c8:	fec42783          	lw	a5,-20(s0)
 2cc:	00178793          	addi	a5,a5,1 # 80000001 <main+0x7fffff25>
 2d0:	fef42623          	sw	a5,-20(s0)
 2d4:	fec42783          	lw	a5,-20(s0)
 2d8:	00078513          	mv	a0,a5
 2dc:	05c12083          	lw	ra,92(sp)
 2e0:	05812403          	lw	s0,88(sp)
 2e4:	06010113          	addi	sp,sp,96
 2e8:	00008067          	ret

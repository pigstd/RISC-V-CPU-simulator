
/home/louhao/System-2025/RISC-V-CPU-simulator/test/test_suite/matrix_mul/matrix_mul.elf:     file format elf32-littleriscv


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
  dc:	f9010113          	addi	sp,sp,-112
  e0:	06112623          	sw	ra,108(sp)
  e4:	06812423          	sw	s0,104(sp)
  e8:	07010413          	addi	s0,sp,112
  ec:	000027b7          	lui	a5,0x2
  f0:	00078793          	mv	a5,a5
  f4:	0007a603          	lw	a2,0(a5) # 2000 <main+0x1f24>
  f8:	0047a683          	lw	a3,4(a5)
  fc:	0087a703          	lw	a4,8(a5)
 100:	00c7a783          	lw	a5,12(a5)
 104:	fcc42423          	sw	a2,-56(s0)
 108:	fcd42623          	sw	a3,-52(s0)
 10c:	fce42823          	sw	a4,-48(s0)
 110:	fcf42a23          	sw	a5,-44(s0)
 114:	000027b7          	lui	a5,0x2
 118:	01078793          	addi	a5,a5,16 # 2010 <main+0x1f34>
 11c:	0007a603          	lw	a2,0(a5)
 120:	0047a683          	lw	a3,4(a5)
 124:	0087a703          	lw	a4,8(a5)
 128:	00c7a783          	lw	a5,12(a5)
 12c:	fac42c23          	sw	a2,-72(s0)
 130:	fad42e23          	sw	a3,-68(s0)
 134:	fce42023          	sw	a4,-64(s0)
 138:	fcf42223          	sw	a5,-60(s0)
 13c:	fe042623          	sw	zero,-20(s0)
 140:	1040006f          	j	244 <main+0x168>
 144:	fe042423          	sw	zero,-24(s0)
 148:	0e40006f          	j	22c <main+0x150>
 14c:	fec42783          	lw	a5,-20(s0)
 150:	00179713          	slli	a4,a5,0x1
 154:	fe842783          	lw	a5,-24(s0)
 158:	00f707b3          	add	a5,a4,a5
 15c:	00279793          	slli	a5,a5,0x2
 160:	ff040713          	addi	a4,s0,-16
 164:	00f707b3          	add	a5,a4,a5
 168:	fa07ac23          	sw	zero,-72(a5)
 16c:	fe042223          	sw	zero,-28(s0)
 170:	0a40006f          	j	214 <main+0x138>
 174:	fec42783          	lw	a5,-20(s0)
 178:	00179713          	slli	a4,a5,0x1
 17c:	fe442783          	lw	a5,-28(s0)
 180:	00f707b3          	add	a5,a4,a5
 184:	00279793          	slli	a5,a5,0x2
 188:	ff040713          	addi	a4,s0,-16
 18c:	00f707b3          	add	a5,a4,a5
 190:	fd87a683          	lw	a3,-40(a5)
 194:	fe442783          	lw	a5,-28(s0)
 198:	00179713          	slli	a4,a5,0x1
 19c:	fe842783          	lw	a5,-24(s0)
 1a0:	00f707b3          	add	a5,a4,a5
 1a4:	00279793          	slli	a5,a5,0x2
 1a8:	ff040713          	addi	a4,s0,-16
 1ac:	00f707b3          	add	a5,a4,a5
 1b0:	fc87a783          	lw	a5,-56(a5)
 1b4:	00078593          	mv	a1,a5
 1b8:	00068513          	mv	a0,a3
 1bc:	e55ff0ef          	jal	ra,10 <multiply>
 1c0:	00050693          	mv	a3,a0
 1c4:	fec42783          	lw	a5,-20(s0)
 1c8:	00179713          	slli	a4,a5,0x1
 1cc:	fe842783          	lw	a5,-24(s0)
 1d0:	00f707b3          	add	a5,a4,a5
 1d4:	00279793          	slli	a5,a5,0x2
 1d8:	ff040713          	addi	a4,s0,-16
 1dc:	00f707b3          	add	a5,a4,a5
 1e0:	fb87a783          	lw	a5,-72(a5)
 1e4:	00f68733          	add	a4,a3,a5
 1e8:	fec42783          	lw	a5,-20(s0)
 1ec:	00179693          	slli	a3,a5,0x1
 1f0:	fe842783          	lw	a5,-24(s0)
 1f4:	00f687b3          	add	a5,a3,a5
 1f8:	00279793          	slli	a5,a5,0x2
 1fc:	ff040693          	addi	a3,s0,-16
 200:	00f687b3          	add	a5,a3,a5
 204:	fae7ac23          	sw	a4,-72(a5)
 208:	fe442783          	lw	a5,-28(s0)
 20c:	00178793          	addi	a5,a5,1
 210:	fef42223          	sw	a5,-28(s0)
 214:	fe442703          	lw	a4,-28(s0)
 218:	00100793          	li	a5,1
 21c:	f4e7dce3          	bge	a5,a4,174 <main+0x98>
 220:	fe842783          	lw	a5,-24(s0)
 224:	00178793          	addi	a5,a5,1
 228:	fef42423          	sw	a5,-24(s0)
 22c:	fe842703          	lw	a4,-24(s0)
 230:	00100793          	li	a5,1
 234:	f0e7dce3          	bge	a5,a4,14c <main+0x70>
 238:	fec42783          	lw	a5,-20(s0)
 23c:	00178793          	addi	a5,a5,1
 240:	fef42623          	sw	a5,-20(s0)
 244:	fec42703          	lw	a4,-20(s0)
 248:	00100793          	li	a5,1
 24c:	eee7dce3          	bge	a5,a4,144 <main+0x68>
 250:	000027b7          	lui	a5,0x2
 254:	02078793          	addi	a5,a5,32 # 2020 <main+0x1f44>
 258:	0007a603          	lw	a2,0(a5)
 25c:	0047a683          	lw	a3,4(a5)
 260:	0087a703          	lw	a4,8(a5)
 264:	00c7a783          	lw	a5,12(a5)
 268:	f8c42c23          	sw	a2,-104(s0)
 26c:	f8d42e23          	sw	a3,-100(s0)
 270:	fae42023          	sw	a4,-96(s0)
 274:	faf42223          	sw	a5,-92(s0)
 278:	fe042023          	sw	zero,-32(s0)
 27c:	fc042e23          	sw	zero,-36(s0)
 280:	0800006f          	j	300 <main+0x224>
 284:	fc042c23          	sw	zero,-40(s0)
 288:	0600006f          	j	2e8 <main+0x20c>
 28c:	fdc42783          	lw	a5,-36(s0)
 290:	00179713          	slli	a4,a5,0x1
 294:	fd842783          	lw	a5,-40(s0)
 298:	00f707b3          	add	a5,a4,a5
 29c:	00279793          	slli	a5,a5,0x2
 2a0:	ff040713          	addi	a4,s0,-16
 2a4:	00f707b3          	add	a5,a4,a5
 2a8:	fb87a703          	lw	a4,-72(a5)
 2ac:	fdc42783          	lw	a5,-36(s0)
 2b0:	00179693          	slli	a3,a5,0x1
 2b4:	fd842783          	lw	a5,-40(s0)
 2b8:	00f687b3          	add	a5,a3,a5
 2bc:	00279793          	slli	a5,a5,0x2
 2c0:	ff040693          	addi	a3,s0,-16
 2c4:	00f687b3          	add	a5,a3,a5
 2c8:	fa87a783          	lw	a5,-88(a5)
 2cc:	00f71863          	bne	a4,a5,2dc <main+0x200>
 2d0:	fe042783          	lw	a5,-32(s0)
 2d4:	00178793          	addi	a5,a5,1
 2d8:	fef42023          	sw	a5,-32(s0)
 2dc:	fd842783          	lw	a5,-40(s0)
 2e0:	00178793          	addi	a5,a5,1
 2e4:	fcf42c23          	sw	a5,-40(s0)
 2e8:	fd842703          	lw	a4,-40(s0)
 2ec:	00100793          	li	a5,1
 2f0:	f8e7dee3          	bge	a5,a4,28c <main+0x1b0>
 2f4:	fdc42783          	lw	a5,-36(s0)
 2f8:	00178793          	addi	a5,a5,1
 2fc:	fcf42e23          	sw	a5,-36(s0)
 300:	fdc42703          	lw	a4,-36(s0)
 304:	00100793          	li	a5,1
 308:	f6e7dee3          	bge	a5,a4,284 <main+0x1a8>
 30c:	fe042783          	lw	a5,-32(s0)
 310:	00078513          	mv	a0,a5
 314:	06c12083          	lw	ra,108(sp)
 318:	06812403          	lw	s0,104(sp)
 31c:	07010113          	addi	sp,sp,112
 320:	00008067          	ret

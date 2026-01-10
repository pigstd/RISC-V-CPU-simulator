
/home/louhao/System-2025/RISC-V-CPU-simulator/test/test_suite/vector_add/vector_add.elf:     file format elf32-littleriscv


Disassembly of section .text:

00000000 <_start>:
   0:	00020137          	lui	sp,0x20
   4:	00c000ef          	jal	ra,10 <main>
   8:	00100073          	ebreak

0000000c <__main_loop>:
   c:	0000006f          	j	c <__main_loop>

00000010 <main>:
  10:	f4010113          	addi	sp,sp,-192 # 1ff40 <main+0x1ff30>
  14:	0a812e23          	sw	s0,188(sp)
  18:	0c010413          	addi	s0,sp,192
  1c:	00a00793          	li	a5,10
  20:	fef42023          	sw	a5,-32(s0)
  24:	000027b7          	lui	a5,0x2
  28:	00078793          	mv	a5,a5
  2c:	0007ae03          	lw	t3,0(a5) # 2000 <main+0x1ff0>
  30:	0047a303          	lw	t1,4(a5)
  34:	0087a883          	lw	a7,8(a5)
  38:	00c7a803          	lw	a6,12(a5)
  3c:	0107a503          	lw	a0,16(a5)
  40:	0147a583          	lw	a1,20(a5)
  44:	0187a603          	lw	a2,24(a5)
  48:	01c7a683          	lw	a3,28(a5)
  4c:	0207a703          	lw	a4,32(a5)
  50:	0247a783          	lw	a5,36(a5)
  54:	fbc42c23          	sw	t3,-72(s0)
  58:	fa642e23          	sw	t1,-68(s0)
  5c:	fd142023          	sw	a7,-64(s0)
  60:	fd042223          	sw	a6,-60(s0)
  64:	fca42423          	sw	a0,-56(s0)
  68:	fcb42623          	sw	a1,-52(s0)
  6c:	fcc42823          	sw	a2,-48(s0)
  70:	fcd42a23          	sw	a3,-44(s0)
  74:	fce42c23          	sw	a4,-40(s0)
  78:	fcf42e23          	sw	a5,-36(s0)
  7c:	000027b7          	lui	a5,0x2
  80:	02878793          	addi	a5,a5,40 # 2028 <main+0x2018>
  84:	0007ae03          	lw	t3,0(a5)
  88:	0047a303          	lw	t1,4(a5)
  8c:	0087a883          	lw	a7,8(a5)
  90:	00c7a803          	lw	a6,12(a5)
  94:	0107a503          	lw	a0,16(a5)
  98:	0147a583          	lw	a1,20(a5)
  9c:	0187a603          	lw	a2,24(a5)
  a0:	01c7a683          	lw	a3,28(a5)
  a4:	0207a703          	lw	a4,32(a5)
  a8:	0247a783          	lw	a5,36(a5)
  ac:	f9c42823          	sw	t3,-112(s0)
  b0:	f8642a23          	sw	t1,-108(s0)
  b4:	f9142c23          	sw	a7,-104(s0)
  b8:	f9042e23          	sw	a6,-100(s0)
  bc:	faa42023          	sw	a0,-96(s0)
  c0:	fab42223          	sw	a1,-92(s0)
  c4:	fac42423          	sw	a2,-88(s0)
  c8:	fad42623          	sw	a3,-84(s0)
  cc:	fae42823          	sw	a4,-80(s0)
  d0:	faf42a23          	sw	a5,-76(s0)
  d4:	fe042623          	sw	zero,-20(s0)
  d8:	0500006f          	j	128 <main+0x118>
  dc:	fec42783          	lw	a5,-20(s0)
  e0:	00279793          	slli	a5,a5,0x2
  e4:	ff040713          	addi	a4,s0,-16
  e8:	00f707b3          	add	a5,a4,a5
  ec:	fc87a703          	lw	a4,-56(a5)
  f0:	fec42783          	lw	a5,-20(s0)
  f4:	00279793          	slli	a5,a5,0x2
  f8:	ff040693          	addi	a3,s0,-16
  fc:	00f687b3          	add	a5,a3,a5
 100:	fa07a783          	lw	a5,-96(a5)
 104:	00f70733          	add	a4,a4,a5
 108:	fec42783          	lw	a5,-20(s0)
 10c:	00279793          	slli	a5,a5,0x2
 110:	ff040693          	addi	a3,s0,-16
 114:	00f687b3          	add	a5,a3,a5
 118:	f6e7ac23          	sw	a4,-136(a5)
 11c:	fec42783          	lw	a5,-20(s0)
 120:	00178793          	addi	a5,a5,1
 124:	fef42623          	sw	a5,-20(s0)
 128:	fec42703          	lw	a4,-20(s0)
 12c:	fe042783          	lw	a5,-32(s0)
 130:	faf746e3          	blt	a4,a5,dc <main+0xcc>
 134:	000027b7          	lui	a5,0x2
 138:	05078793          	addi	a5,a5,80 # 2050 <main+0x2040>
 13c:	0007ae03          	lw	t3,0(a5)
 140:	0047a303          	lw	t1,4(a5)
 144:	0087a883          	lw	a7,8(a5)
 148:	00c7a803          	lw	a6,12(a5)
 14c:	0107a503          	lw	a0,16(a5)
 150:	0147a583          	lw	a1,20(a5)
 154:	0187a603          	lw	a2,24(a5)
 158:	01c7a683          	lw	a3,28(a5)
 15c:	0207a703          	lw	a4,32(a5)
 160:	0247a783          	lw	a5,36(a5)
 164:	f5c42023          	sw	t3,-192(s0)
 168:	f4642223          	sw	t1,-188(s0)
 16c:	f5142423          	sw	a7,-184(s0)
 170:	f5042623          	sw	a6,-180(s0)
 174:	f4a42823          	sw	a0,-176(s0)
 178:	f4b42a23          	sw	a1,-172(s0)
 17c:	f4c42c23          	sw	a2,-168(s0)
 180:	f4d42e23          	sw	a3,-164(s0)
 184:	f6e42023          	sw	a4,-160(s0)
 188:	f6f42223          	sw	a5,-156(s0)
 18c:	fe042423          	sw	zero,-24(s0)
 190:	fe042223          	sw	zero,-28(s0)
 194:	0480006f          	j	1dc <main+0x1cc>
 198:	fe442783          	lw	a5,-28(s0)
 19c:	00279793          	slli	a5,a5,0x2
 1a0:	ff040713          	addi	a4,s0,-16
 1a4:	00f707b3          	add	a5,a4,a5
 1a8:	f787a703          	lw	a4,-136(a5)
 1ac:	fe442783          	lw	a5,-28(s0)
 1b0:	00279793          	slli	a5,a5,0x2
 1b4:	ff040693          	addi	a3,s0,-16
 1b8:	00f687b3          	add	a5,a3,a5
 1bc:	f507a783          	lw	a5,-176(a5)
 1c0:	00f71863          	bne	a4,a5,1d0 <main+0x1c0>
 1c4:	fe842783          	lw	a5,-24(s0)
 1c8:	00178793          	addi	a5,a5,1
 1cc:	fef42423          	sw	a5,-24(s0)
 1d0:	fe442783          	lw	a5,-28(s0)
 1d4:	00178793          	addi	a5,a5,1
 1d8:	fef42223          	sw	a5,-28(s0)
 1dc:	fe442703          	lw	a4,-28(s0)
 1e0:	fe042783          	lw	a5,-32(s0)
 1e4:	faf74ae3          	blt	a4,a5,198 <main+0x188>
 1e8:	fe842783          	lw	a5,-24(s0)
 1ec:	00078513          	mv	a0,a5
 1f0:	0bc12403          	lw	s0,188(sp)
 1f4:	0c010113          	addi	sp,sp,192
 1f8:	00008067          	ret

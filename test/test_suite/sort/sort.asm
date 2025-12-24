
test_suite/sort/sort.elf:     file format elf32-littleriscv


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
  24:	0007a583          	lw	a1,0(a5) # 2000 <main+0x1ff0>
  28:	0047a603          	lw	a2,4(a5)
  2c:	0087a683          	lw	a3,8(a5)
  30:	00c7a703          	lw	a4,12(a5)
  34:	0107a783          	lw	a5,16(a5)
  38:	fcb42223          	sw	a1,-60(s0)
  3c:	fcc42423          	sw	a2,-56(s0)
  40:	fcd42623          	sw	a3,-52(s0)
  44:	fce42823          	sw	a4,-48(s0)
  48:	fcf42a23          	sw	a5,-44(s0)
  4c:	00500793          	li	a5,5
  50:	fcf42e23          	sw	a5,-36(s0)
  54:	fe042623          	sw	zero,-20(s0)
  58:	0cc0006f          	j	124 <main+0x114>
  5c:	fe042423          	sw	zero,-24(s0)
  60:	0a00006f          	j	100 <main+0xf0>
  64:	fe842783          	lw	a5,-24(s0)
  68:	00279793          	slli	a5,a5,0x2
  6c:	ff040713          	addi	a4,s0,-16
  70:	00f707b3          	add	a5,a4,a5
  74:	fd47a703          	lw	a4,-44(a5)
  78:	fe842783          	lw	a5,-24(s0)
  7c:	00178793          	addi	a5,a5,1
  80:	00279793          	slli	a5,a5,0x2
  84:	ff040693          	addi	a3,s0,-16
  88:	00f687b3          	add	a5,a3,a5
  8c:	fd47a783          	lw	a5,-44(a5)
  90:	06e7d263          	bge	a5,a4,f4 <main+0xe4>
  94:	fe842783          	lw	a5,-24(s0)
  98:	00279793          	slli	a5,a5,0x2
  9c:	ff040713          	addi	a4,s0,-16
  a0:	00f707b3          	add	a5,a4,a5
  a4:	fd47a783          	lw	a5,-44(a5)
  a8:	fcf42c23          	sw	a5,-40(s0)
  ac:	fe842783          	lw	a5,-24(s0)
  b0:	00178793          	addi	a5,a5,1
  b4:	00279793          	slli	a5,a5,0x2
  b8:	ff040713          	addi	a4,s0,-16
  bc:	00f707b3          	add	a5,a4,a5
  c0:	fd47a703          	lw	a4,-44(a5)
  c4:	fe842783          	lw	a5,-24(s0)
  c8:	00279793          	slli	a5,a5,0x2
  cc:	ff040693          	addi	a3,s0,-16
  d0:	00f687b3          	add	a5,a3,a5
  d4:	fce7aa23          	sw	a4,-44(a5)
  d8:	fe842783          	lw	a5,-24(s0)
  dc:	00178793          	addi	a5,a5,1
  e0:	00279793          	slli	a5,a5,0x2
  e4:	ff040713          	addi	a4,s0,-16
  e8:	00f707b3          	add	a5,a4,a5
  ec:	fd842703          	lw	a4,-40(s0)
  f0:	fce7aa23          	sw	a4,-44(a5)
  f4:	fe842783          	lw	a5,-24(s0)
  f8:	00178793          	addi	a5,a5,1
  fc:	fef42423          	sw	a5,-24(s0)
 100:	fdc42703          	lw	a4,-36(s0)
 104:	fec42783          	lw	a5,-20(s0)
 108:	40f707b3          	sub	a5,a4,a5
 10c:	fff78793          	addi	a5,a5,-1
 110:	fe842703          	lw	a4,-24(s0)
 114:	f4f748e3          	blt	a4,a5,64 <main+0x54>
 118:	fec42783          	lw	a5,-20(s0)
 11c:	00178793          	addi	a5,a5,1
 120:	fef42623          	sw	a5,-20(s0)
 124:	fdc42783          	lw	a5,-36(s0)
 128:	fff78793          	addi	a5,a5,-1
 12c:	fec42703          	lw	a4,-20(s0)
 130:	f2f746e3          	blt	a4,a5,5c <main+0x4c>
 134:	fe042223          	sw	zero,-28(s0)
 138:	fe042023          	sw	zero,-32(s0)
 13c:	0300006f          	j	16c <main+0x15c>
 140:	fe042783          	lw	a5,-32(s0)
 144:	00279793          	slli	a5,a5,0x2
 148:	ff040713          	addi	a4,s0,-16
 14c:	00f707b3          	add	a5,a4,a5
 150:	fd47a783          	lw	a5,-44(a5)
 154:	fe442703          	lw	a4,-28(s0)
 158:	00f707b3          	add	a5,a4,a5
 15c:	fef42223          	sw	a5,-28(s0)
 160:	fe042783          	lw	a5,-32(s0)
 164:	00178793          	addi	a5,a5,1
 168:	fef42023          	sw	a5,-32(s0)
 16c:	fe042703          	lw	a4,-32(s0)
 170:	fdc42783          	lw	a5,-36(s0)
 174:	fcf746e3          	blt	a4,a5,140 <main+0x130>
 178:	fc442703          	lw	a4,-60(s0)
 17c:	00100793          	li	a5,1
 180:	00f71863          	bne	a4,a5,190 <main+0x180>
 184:	fd442703          	lw	a4,-44(s0)
 188:	00500793          	li	a5,5
 18c:	00f70463          	beq	a4,a5,194 <main+0x184>
 190:	fe042223          	sw	zero,-28(s0)
 194:	fe442783          	lw	a5,-28(s0)
 198:	00078513          	mv	a0,a5
 19c:	03c12403          	lw	s0,60(sp)
 1a0:	04010113          	addi	sp,sp,64
 1a4:	00008067          	ret

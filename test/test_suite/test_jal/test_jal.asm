
/home/louhao/System-2025/RISC-V-CPU-simulator/test/test_suite/test_jal/test_jal.elf:     file format elf32-littleriscv


Disassembly of section .text:

00000000 <_start>:
   0:	00020137          	lui	sp,0x20
   4:	06c000ef          	jal	ra,70 <main>
   8:	00100073          	ebreak

0000000c <__main_loop>:
   c:	0000006f          	j	c <__main_loop>

00000010 <add>:
  10:	fe010113          	addi	sp,sp,-32 # 1ffe0 <main+0x1ff70>
  14:	00812e23          	sw	s0,28(sp)
  18:	02010413          	addi	s0,sp,32
  1c:	fea42623          	sw	a0,-20(s0)
  20:	feb42423          	sw	a1,-24(s0)
  24:	fec42703          	lw	a4,-20(s0)
  28:	fe842783          	lw	a5,-24(s0)
  2c:	00f707b3          	add	a5,a4,a5
  30:	00078513          	mv	a0,a5
  34:	01c12403          	lw	s0,28(sp)
  38:	02010113          	addi	sp,sp,32
  3c:	00008067          	ret

00000040 <sub>:
  40:	fe010113          	addi	sp,sp,-32
  44:	00812e23          	sw	s0,28(sp)
  48:	02010413          	addi	s0,sp,32
  4c:	fea42623          	sw	a0,-20(s0)
  50:	feb42423          	sw	a1,-24(s0)
  54:	fec42703          	lw	a4,-20(s0)
  58:	fe842783          	lw	a5,-24(s0)
  5c:	40f707b3          	sub	a5,a4,a5
  60:	00078513          	mv	a0,a5
  64:	01c12403          	lw	s0,28(sp)
  68:	02010113          	addi	sp,sp,32
  6c:	00008067          	ret

00000070 <main>:
  70:	fe010113          	addi	sp,sp,-32
  74:	00112e23          	sw	ra,28(sp)
  78:	00812c23          	sw	s0,24(sp)
  7c:	02010413          	addi	s0,sp,32
  80:	00500593          	li	a1,5
  84:	00a00513          	li	a0,10
  88:	f89ff0ef          	jal	ra,10 <add>
  8c:	fea42623          	sw	a0,-20(s0)
  90:	00300593          	li	a1,3
  94:	fec42503          	lw	a0,-20(s0)
  98:	fa9ff0ef          	jal	ra,40 <sub>
  9c:	fea42423          	sw	a0,-24(s0)
  a0:	fe842583          	lw	a1,-24(s0)
  a4:	fe842503          	lw	a0,-24(s0)
  a8:	f69ff0ef          	jal	ra,10 <add>
  ac:	fea42223          	sw	a0,-28(s0)
  b0:	fe442783          	lw	a5,-28(s0)
  b4:	00078513          	mv	a0,a5
  b8:	01c12083          	lw	ra,28(sp)
  bc:	01812403          	lw	s0,24(sp)
  c0:	02010113          	addi	sp,sp,32
  c4:	00008067          	ret

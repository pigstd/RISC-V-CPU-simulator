
/home/louhao/System-2025/RISC-V-CPU-simulator/test/test_suite/test_jalr/test_jalr.elf:     file format elf32-littleriscv


Disassembly of section .text:

00000000 <_start>:
   0:	00020137          	lui	sp,0x20
   4:	064000ef          	jal	ra,68 <main>
   8:	00100073          	ebreak

0000000c <__main_loop>:
   c:	0000006f          	j	c <__main_loop>

00000010 <double_val>:
  10:	fe010113          	addi	sp,sp,-32 # 1ffe0 <main+0x1ff78>
  14:	00812e23          	sw	s0,28(sp)
  18:	02010413          	addi	s0,sp,32
  1c:	fea42623          	sw	a0,-20(s0)
  20:	fec42783          	lw	a5,-20(s0)
  24:	00179793          	slli	a5,a5,0x1
  28:	00078513          	mv	a0,a5
  2c:	01c12403          	lw	s0,28(sp)
  30:	02010113          	addi	sp,sp,32
  34:	00008067          	ret

00000038 <triple_val>:
  38:	fe010113          	addi	sp,sp,-32
  3c:	00812e23          	sw	s0,28(sp)
  40:	02010413          	addi	s0,sp,32
  44:	fea42623          	sw	a0,-20(s0)
  48:	fec42703          	lw	a4,-20(s0)
  4c:	00070793          	mv	a5,a4
  50:	00179793          	slli	a5,a5,0x1
  54:	00e787b3          	add	a5,a5,a4
  58:	00078513          	mv	a0,a5
  5c:	01c12403          	lw	s0,28(sp)
  60:	02010113          	addi	sp,sp,32
  64:	00008067          	ret

00000068 <main>:
  68:	fe010113          	addi	sp,sp,-32
  6c:	00112e23          	sw	ra,28(sp)
  70:	00812c23          	sw	s0,24(sp)
  74:	02010413          	addi	s0,sp,32
  78:	01000793          	li	a5,16
  7c:	fef42623          	sw	a5,-20(s0)
  80:	fec42783          	lw	a5,-20(s0)
  84:	00500513          	li	a0,5
  88:	000780e7          	jalr	a5
  8c:	fea42423          	sw	a0,-24(s0)
  90:	03800793          	li	a5,56
  94:	fef42623          	sw	a5,-20(s0)
  98:	fec42783          	lw	a5,-20(s0)
  9c:	00400513          	li	a0,4
  a0:	000780e7          	jalr	a5
  a4:	fea42223          	sw	a0,-28(s0)
  a8:	fe842703          	lw	a4,-24(s0)
  ac:	fe442783          	lw	a5,-28(s0)
  b0:	00f707b3          	add	a5,a4,a5
  b4:	00078513          	mv	a0,a5
  b8:	01c12083          	lw	ra,28(sp)
  bc:	01812403          	lw	s0,24(sp)
  c0:	02010113          	addi	sp,sp,32
  c4:	00008067          	ret

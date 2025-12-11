# RISC-V-CPU-simulator

A simple RISC-V CPU simulator implemented in Python using [assassyn](https://github.com/Synthesys-Lab/assassyn).

# Benchmarks

最终这个 CPU 需要完成以下 benchmark：

- [] 一个[向量乘法](https://github.com/ucb-bar/riscv-benchmarks/blob/4d46f673ae42a321e35f5b40b2f5c8f498bc1d9d/multiply/multiply_main.c#L35-L40)
- [] 一个[向量加法](https://github.com/ucb-bar/riscv-benchmarks/blob/master/vvadd/vvadd_main.c#L26-L31)
- [] 一个从 0 加到 100 的循环

以上代码都需要：

写出 .c 代码，用 [riscv-gnu-toolchain-gcc](https://github.com/riscv-collab/riscv-gnu-toolchain) 编译出来 .o，把对应函数的 binary 抽出来给 CPU 跑。

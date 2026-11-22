# 裸机 C 工程

这个目录是一个完整的 RV32I 裸机程序，外设地址沿用第 12 章：LED `0xffff0010`、UART 数据 `0xffff0030`、UART 状态 `0xffff0034`。程序先算 1 到 10 的和（结果 55），把低 8 位写到 LED，再从串口输出两个字符 `Hi`，最后原地停机。

## 需要什么工具

编译本目录需要 RISC-V 交叉编译工具链，运行需要 QEMU 或本书自己的硬件仿真。本书写作时使用的机器上没有安装这些工具，因此下面命令给出的是标准用法，需要在装好工具的机器上执行。

- 交叉编译器：`riscv32-unknown-elf-gcc`（也可把目录 Makefile 里的 `CROSS` 改成机器上实际的前缀，如 `riscv64-unknown-elf-`）
- 工具：`riscv32-unknown-elf-objdump`、`riscv32-unknown-elf-objcopy`
- 运行：第 12 章的 Verilog 仿真，或 `code/qemu/hello/` 下的 QEMU 示例

工具链下载地址见课件"如何选择RISC-V交叉编译器"一页，Windows 用户可用 xPack GNU RISC-V 工具链，解压后把 `bin` 加进 PATH。

## 编译

在本目录执行：

```
make
```

会生成三个文件：

- `main.elf`：带符号和段信息的 ELF 文件，交给 `objdump` 看反汇编。
- `main.bin`：从 ELF 抽出的纯二进制镜像，烧进 Flash 或装进模拟器。
- `main.dis`：反汇编与源码混排的文本，用来核对编译器到底生成了什么。

清掉产物用 `make clean`。

## 看反汇编

```
make main.dis
type main.dis
```

打开 `main.dis`，找 `sum_to`，你会看到编译器把一个 `for` 循环变成了 `addi`、`bge`、`add` 和跳转。再找 `main`，`LED = s` 变成一条 `sw`，而 `uart_putc` 里的 `while` 变成 `lui` 加 `lw` 加 `bge`。这正是第 13 章要你看的东西：C 的每一行都对应到具体的指令。

## 预期结果

在本书的 Verilog 仿真里跑 `main.bin`，应当看到：

- LED 寄存器低 8 位为 `0x37`（十进制 55）
- 串口依次收到 `H`、`i`

在没有本书外设的通用 QEMU 机器上，这些地址没有接设备，所以本目录的 ELF 不适合直接给 QEMU 跑。`code/qemu/hello/` 提供了一个把字符写到 QEMU 串口的独立小例子，工具链流程完全相同，只有外设地址不同。

## 本机就能跑的对照实验

不想装工具链也能走通同一条概念链。`code/python/13_toolchain/` 下有一个 Python 演示：

```
python build_image.py
python test_toolchain.py
```

它复用第 7 章的模拟器，把"编译器输出"的汇编序列汇编成镜像，报告段布局，把镜像装进内存运行，并检查 LED 值与串口输出。真机上由 GCC 完成的每一步，这里都用看得见的 Python 演一遍。

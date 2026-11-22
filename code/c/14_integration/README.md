# 综合实验：从 C 程序到处理器

这一组文件把全书的主线走了一遍：一段 C 程序，经过交叉编译、反汇编、制作镜像，最后交给第 8 章的单周期核执行。它回答一个问题——前面十几章搭的每一样东西，在真实的工具链里是怎样接起来的。

## 工具链

- RISC-V 交叉编译器 `riscv64-unknown-elf-gcc`
- 二进制工具 `objcopy`、`objdump`
- 本机 Python（跑 `tools/bin_to_hex.py`）
- Icarus Verilog（跑单周期核）

本机没有安装交叉编译器，因此 `make` 这一步**需要在装好 RISC-V GCC 的机器上执行**。工具链的完整安装步骤见教材附录 C。不过链路上从"汇编到镜像再到运行"的部分，已经在第 13 章用 Python 工具链逐条验证过（`code/python/13_toolchain/`），可以先在那里看到每一步的产物。

## 从 C 到波形

```sh
make            # 依次产出 program.elf、program.dump、code.hex
make disasm     # 单独看反汇编（已含在 all 里）
make sim        # 把 code.hex 装进第 8 章的单周期核仿真
```

各步骤的产物：

1. `program.elf`：链接后的可执行程序，入口在 `_start`，代码从 `0x00400000` 开始。
2. `program.dump`：反汇编，对照正文看编译器把 `sum_to()` 展开了成哪些指令。
3. `code.hex`：从 `.text` 抽出来的二进制，每 4 字节一个 32 位字，供 `$readmemh` 读取。
4. 仿真：LED 写出 55（0x37），串口输出 `sum=55`。

## 地址布局

| 内容 | 地址 |
| --- | --- |
| 指令内存 | `0x00400000` 起 |
| 数据内存 | `0x10000000` 起 |
| LED | `0xffff0010` |
| UART 数据 | `0xffff0030` |

这份布局与第 12 章的外设、第 8 章的单周期核完全一致，所以 `code.hex` 可以直接被 `imem.v` 读取。

## 一处要注意的地方

反汇编里会看到 `sum_to()` 的循环被编译成 `addi`、`bltu` 之类的指令，字符串常量被放进了 `.text` 段末尾。链接脚本 `program.ld` 特意把 `.rodata` 并进 `.text`，否则 `objcopy -j .text` 会漏掉那些字符，串口就打不出 `sum=55`。这与 QEMU 多任务工程里把代码和数据分开放的做法不同——因为那一版由 OpenSBI/QEMU 负责加载 ELF，不需要自己做镜像。

# QEMU virt 上的最小裸机程序

这个例子只做一件事：通过 QEMU virt 机器的串口打印一行 `Hello from RISC-V`。它和 `code/c/13_baremetal/` 的 C 程序用的是同一套工具链和同样的链接思路，唯一的区别是外设地址——QEMU 的串口在 `0x10000000`，本书自己搭的外设在 `0xffff0000`。

## 编译并运行

在装有 RISC-V 工具链和 QEMU 的机器上：

```
make
make run
```

终端应当打印：

```
Hello from RISC-V
```

程序最后进入 `for(;;)` 死循环，QEMU 不会自己退出。按 `Ctrl+A` 再按 `X` 可以退出 QEMU。

## 常见麻烦

- 提示找不到 `riscv64-unknown-elf-gcc`：改 Makefile 第一行的 `CROSS`，让它匹配机器上实际的编译器前缀。
- 提示找不到 `qemu-system-riscv32`：装 QEMU，或把 QEMU 的可执行目录加进 PATH。
- 屏幕没有输出：确认命令里有 `-serial stdio` 和 `-nographic`；少了这两个选项，串口输出不会出现在当前终端。

本机没有装 QEMU 和交叉编译器，这组脚本没有在本机实跑，属于"照着做就能复现"的对照实验。核心实验用 `code/python/13_toolchain/` 或第 12 章的 Verilog 仿真即可在本机完成。

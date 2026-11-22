# 附录 C　工具链与环境搭建

全书只用四组软件：RARS、Digital 与 Icarus Verilog、RISC-V GCC 交叉编译工具链、QEMU。这一章讲它们怎么装、怎么跑，以及出了问题先看哪里。

先说明一件事：本书的核心实验不依赖全部工具。RARS 用于第 3 章，Digital 与 Icarus Verilog 从第 4 章起贯穿硬件部分，这两组免费、体积不大，装好就能走完从指令到五级流水线的主要路线。RISC-V GCC 和 QEMU 主要用于第 11、13、14 章的软件对照实验，这组脚本在编写本书的机器上没有实跑，因为那台机器没有安装它们；文中给出的是标准命令和预期现象，在装好工具的机器上应当能复现。

## C.1 RARS 的安装与汇编程序调试

### RARS 是什么

RARS 是 RISC-V Assembler and Runtime Simulator 的缩写，一个用 Java 写的 RISC-V 汇编器和模拟器。它能把汇编翻译成机器码，也能单步执行、查看寄存器和内存。第 3 章写汇编程序时一直用它。

它能看到的是指令集这一层，看不到时钟和电路。这正是它的用处：先把程序在指令集层调试对，再去硬件里跑，出问题就知道是程序错了还是电路错了。

### 安装

RARS 是一个独立的 jar 文件，从它的官方发布页下载 `rars.jar`，放到任意目录即可。运行需要 Java 运行环境，Java 8 或更新版本都行：

```bash
java -jar rars.jar
```

如果双击 jar 文件打不开，多半是系统没有关联 Java，用上面这条命令最稳妥。启动时可能出现一个设置窗口，问是否开启伪指令、是否允许自修改代码，保持默认即可。

### 跑一个程序

以第 3 章的最小程序为例。在 RARS 里新建文件，输入：

```asm
.text
.globl main
main:
    li   a7, 10          # 服务号 10：退出程序
    ecall
```

按汇编按钮（或 F3），再按运行按钮（或 F5）。程序会立刻结束，因为服务号 10 就是让 RARS 退出。想看执行过程，改用单步按钮（F7 或 F8），每按一次执行一条指令。

调试时最有用的是三个窗口：

- **Registers** 显示 32 个通用寄存器和 `pc` 的当前值，变化的值会高亮；
- **Memory** 显示数据内存，可以按字节、半字、字查看；
- **Execute** 是主界面，能看到源码、机器码和当前执行位置。

用 `li a0, 42` 加 `ecall`（服务号 1）打印整数，单步走到 `ecall` 时，先在 Registers 窗口确认 `a0` 确实是 42，再执行，就能把"数据准备"和"服务调用"两件事分开看。

### 常见问题

**汇编报错 `Illegal operand`。** 先检查是不是把 RARS 不认识的写法当成真指令了。`li`、`la`、`mv`、`ret` 都是伪指令，RARS 默认开启伪指令支持；如果关掉了，就会报这类错。

**中文注释变成乱码。** 把源文件存成 UTF-8，RARS 的编辑器对中文注释支持不稳定，必要时可以把注释写成英文，或者只在正文里对照阅读。

**`ecall` 没有输出。** 检查 `a7` 里的服务号对不对。服务号放错寄存器是最常见的失误，RARS 只认 `a7`。

## C.2 Digital 与 Icarus Verilog 的配合使用

### 两者分工

Digital 是图形化的数字电路仿真器，用鼠标连线搭门电路，能单步看信号沿导线传播。Icarus Verilog 是命令行仿真器，跑 Verilog 测试台，适合验证复杂模块并自动检查几十项断言。

本书让两者做同一件事。第 4 章先用 Digital 搭一个带使能的 D 触发器，看清时钟沿和数据锁存的关系，再用 Verilog 描述同一个触发器，用测试台检查 7 项行为。图形给直觉，代码给效率，谁也替代不了谁。

### 安装

Digital 从它的官方发布页下载，解压后运行 `Digital.jar` 即可，同样需要 Java。也可以直接双击发行包里的启动脚本。

Icarus Verilog 在 Windows、Linux、macOS 上都有安装包。Windows 下从官方发布页下载安装程序，安装时勾上把可执行文件加入 PATH 的选项。装完后打开终端验证：

```bash
iverilog -v
```

能打印版本信息就说明装好了。本书的代码用 `-g2012` 选项编译，对应 Verilog-2012 语法。

### 跑一个测试台

到第 4 章的代码目录，编译并运行：

```bash
cd code/verilog/04_digital
iverilog -g2012 -o sim.out dff_en.v tb_dff_en.v
vvp sim.out
```

输出应当是一串 `PASS` 和最后的 `ALL TESTS PASSED`。`iverilog` 负责编译，生成 `sim.out`；`vvp` 负责运行这个编译产物。两条命令分开写，方便在改了代码之后只重跑第二步——当然第一步也得重编译才生效。

附录 B 的三个测试台命令在第 B.6 节列出，可以直接拿去验证环境。

### Digital 电路的用法

`code/digital/` 下是 `.dig` 文件，本质上是 XML，用文本编辑器也能打开，但通常用 Digital 打开。打开后按单步按钮，电路里的每个门都会显示当前输入和输出值。

本书的电路从简单到复杂：第 4 章是与门和带使能的触发器，第 5 章是半加器和一位 ALU，第 8 章是分支相等判据，第 10 章是转发二选一，第 12 章是地址译码器，第 14 章是定时器中断判据。多数电路带真值表，可以用 Digital 的测试功能逐行验证。

### 常见问题

**`iverilog` 不认识 `$clog2`。** 老版本不支持这个系统函数，升级到 10 版以上即可。本书写作时用的是 12.0 版。

**数组上界报错。** Icarus Verilog 不接受在数组声明的方括号里直接写参数表达式。先转成 `localparam`，例如 `localparam DEPTH_M1 = DEPTH - 1;`，再用 `mem [0:DEPTH_M1]`。

**编译报 `Unknown module type`。** 某个子模块没有列进编译命令。检查是不是漏了文件，附录 B 的 ALU 测试台就需要同时编译 `alu.v`、`adder_32.v`、`full_adder.v` 和 `half_adder.v`。

## C.3 RISC-V GCC 交叉编译、ELF、链接脚本与 Makefile

### 什么是交叉编译

在一台 x86 电脑上编译出能在 RISC-V 处理器上运行的程序，叫交叉编译。完成这件事的工具链叫 RISC-V GCC，里面包含编译器 `gcc`、汇编器 `as`、链接器 `ld`、反汇编工具 `objdump` 和格式转换工具 `objcopy`。

工具链的名字里常带前缀，比如 `riscv64-unknown-elf-` 或 `riscv32-unknown-elf-`。这两个都能编译 32 位 RV32I 程序，用 `-march=rv32i -mabi=ilp32` 指定目标和 ABI 即可。本书两个前缀都用过，以实际安装为准；Makefile 第一行是 `CROSS =`，改这一处就能切换。

### 安装

不同的系统安装方式不一样：

- **Windows**：可以安装 Windows 版 RISC-V GCC 工具链，下载后解压，把 `bin` 目录加入 PATH。也可以用 WSL 装 Linux 版。
- **Ubuntu 或 Debian**：`sudo apt install gcc-riscv64-unknown-elf binutils-riscv64-unknown-elf`
- **macOS**：用 Homebrew 安装 `riscv-gnu-toolchain` 相关的配方，或从源码构建。

装完后验证：

```bash
riscv64-unknown-elf-gcc --version
```

能打印版本就行。GDB 调试还需要 `riscv64-unknown-elf-gdb`，它通常不在基础包里，要单独装。

### 编译参数的意思

以 `code/c/13_baremetal/Makefile` 为例：

```makefile
CROSS   = riscv32-unknown-elf-
CC      = $(CROSS)gcc
OBJDUMP = $(CROSS)objdump
OBJCOPY = $(CROSS)objcopy

CFLAGS = -march=rv32i -mabi=ilp32 -nostdlib -O1 -g -Wall -T link.ld
```

逐个看这些参数。`-march=rv32i` 指定只生成基本整数指令，不用乘法和压缩指令，正好和本书的硬件一致；`-mabi=ilp32` 指定整数和指针都是 32 位；`-nostdlib` 告诉编译器不要链接标准库，因为裸机程序没有操作系统，也没有 C 运行时的启动代码；`-O1` 是轻度优化，保留了一些可读性，反汇编时容易和源码对上；`-g` 加入调试信息；`-Wall` 打开常见警告；`-T link.ld` 指定链接脚本。

`make` 之后会生成三个文件：`main.elf` 是带符号和段信息的可执行文件，`main.bin` 是要装进内存的纯二进制镜像，`main.dis` 是反汇编，用来对照 C 源码和机器码。

### 链接脚本做什么

链接脚本决定程序各段放在哪个地址。第 13 章的 `link.ld` 把代码放在 Flash 区 `0x00400000`，把数据放在内存区 `0x10000000`，并定义了 `sp` 的初值和 bss 段的起止符号，启动代码靠它们设栈和清零 bss。

这里最容易出的错是只读数据被丢掉。`objcopy -j .text` 只提取 `.text` 段，如果字符串常量单独落在 `.rodata` 段，镜像里就没有它们，程序跑起来会打印乱码。第 14 章的链接脚本因此把 `.rodata` 并进了 `.text`：

```
    .text : {
        *(.text.start)
        *(.text*)
        *(.rodata*)
    }
```

链接脚本的语法细节可以查 GNU ld 手册，本书只用到了 `SECTIONS`、段匹配和几个符号定义，够用即可。

### 从 ELF 到硬件镜像

第 14 章的综合实验把整条链串了起来：

```makefile
program.elf: start.S program.c program.ld
	$(CC) $(CFLAGS) -o $@ start.S program.c

program.dump: program.elf
	$(OBJDUMP) -d -s program.elf > $@

program.bin: program.elf
	$(OBJCOPY) -O binary -j .text program.elf $@

# 把二进制镜像转成 Icarus Verilog 能读的 code.hex（每行一个 32 位字）
code.hex: program.bin
	$(PYTHON) ../../../tools/bin_to_hex.py program.bin code.hex
```

`objdump` 出来的 `.dump` 给人看，`objcopy` 出来的 `.bin` 给机器用，`bin_to_hex.py` 再把它转成 Icarus Verilog 能读的 `code.hex`，每行一个 32 位字。转换脚本按小端序读四个字节合成一个字，这和 RV32I 的内存序一致。

在 `code/c/14_integration/` 下执行 `make`，会一次生成 elf、dump、bin 和 hex；执行 `make sim`，会把 hex 拷给第 8 章的单周期核并跑仿真。

### Makefile 常见问题

**提示 `CROSS` 找不到。** 本机装的工具链前缀和 Makefile 第一行不一致，改 `CROSS` 的值。

**`make` 不重新生成。** 目标文件的时间戳比依赖文件新时 make 会跳过。改了链接脚本却没重新链接，删掉 elf 再来一次，或者用 `make -B` 强制重建。

**反汇编里看不到 C 源码。** 编译时没加 `-g`，或者用了 `-O2` 以上的优化导致代码被重排。用 `-O1 -g` 最容易对照。

## C.4 QEMU 与 OpenSBI 运行裸机程序，GDB 调试

### QEMU 在这本书里的角色

QEMU 是一个完整的机器模拟器。本书用它演示异常、中断和多任务在真实软件环境里是什么样，不拿它替代自己搭的处理器。两条线是并行的：Verilog 那边看信号怎么走，QEMU 这边看程序在完整系统里怎么跑。

本书的 QEMU 实验都跑在 `virt` 机器上，这是一个通用的 RISC-V 虚拟平台，带串口、CLINT 定时器等外设。外设地址和本书自己搭的核不同：QEMU 的串口在 `0x10000000`，CLINT 在 `0x02000000`；本书的第 12 章用的是 `0xffff0000` 区。读代码时要先确认在哪一边。

### 安装

Ubuntu 或 Debian 下：

```bash
sudo apt install qemu-system-misc
```

macOS 用 Homebrew 安装 `qemu`，Windows 可以从 QEMU 官网下载安装包。装完后验证：

```bash
qemu-system-riscv32 --version
```

OpenSBI 是 RISC-V 的固件，为上层软件提供引导和机器模式服务。本书的裸机例子直接从 `-kernel` 加载 ELF，用 `-bios none` 跳过固件，所以不装 OpenSBI 也能跑最小示例。想观察 S 模式程序通过 OpenSBI 进入 M 模式，需要另外准备固件，那已经超出本书主线。

### 跑最小示例

`code/qemu/hello/` 是最小例子，一个 C 程序通过串口打印一行字。在装有工具的机器上：

```bash
cd code/qemu/hello
make
make run
```

`make run` 执行的命令是：

```bash
qemu-system-riscv32 -machine virt -nographic -monitor none -serial stdio -bios none -kernel hello.elf
```

逐项看这几个参数。`-machine virt` 选虚拟平台；`-nographic` 不开图形窗口；`-serial stdio` 把串口接到当前终端，没有它就看不打印内容；`-monitor none` 关掉 QEMU 自己的监控台；`-bios none` 不加载固件；`-kernel hello.elf` 指定要运行的程序。

预期输出是一行：

```
Hello from RISC-V
```

程序最后进入死循环，QEMU 不会自己退出。按 `Ctrl+A` 再按 `X` 退出。

### 跑多任务示例

`code/qemu/multitask/` 是第 14 章的多任务工程，包含 PCB、上下文切换、CLINT 定时器中断和轮转调度：

```bash
cd code/qemu/multitask
make
make run
```

预期串口交替输出 A 和 B，表明两个任务在定时器中断下轮流运行。这和 `code/python/14_multitask/run.py` 在本机跑出的 ABAB 是同一件事，只是一个在完整模拟器里，一个在本书自己写的教学模拟器里。

### GDB 调试

GDB 能在 QEMU 里单步执行、设断点、看寄存器。需要两个终端。

第一个终端启动 QEMU 并等 GDB 连接：

```bash
qemu-system-riscv32 -machine virt -nographic -serial stdio -bios none \
    -kernel hello.elf -S -gdb tcp::1234
```

`-S` 让 CPU 在启动时暂停，`-gdb tcp::1234` 打开调试端口。

第二个终端启动交叉调试器：

```bash
riscv64-unknown-elf-gdb hello.elf
(gdb) target remote :1234
(gdb) break main
(gdb) continue
(gdb) info registers
(gdb) step
```

连上之后，用法和本地调试一样。`break` 设断点，`continue` 跑到断点，`step` 单步进入，`info registers` 看寄存器。编译时要加 `-g`，否则 GDB 找不到源码行号。

调试裸机程序有个特别有用的技巧：在陷阱处理程序入口设断点，每次异常或中断进来都会停住，可以直接看 `mcause`、`mepc` 和 `mstatus` 的值。第 11 章讲的现场保存，用这个办法能看得很清楚。

### 常见问题

**屏幕没有任何输出。** 先确认命令里有 `-serial stdio` 和 `-nographic`。再检查程序的串口地址和 `virt` 平台一致不一致，本书第 12 章的 `0xffff0030` 在 QEMU 里不是串口。

**提示找不到 `qemu-system-riscv32`。** 有些发行版只提供 `qemu-system-riscv64`，它也能跑 32 位客户机，把命令换过去即可。

**`make` 报找不到编译器。** 改 Makefile 第一行的 `CROSS`，让它匹配机器上实际的前缀。用 `which riscv64-unknown-elf-gcc` 查一下就知道了。

**GDB 连不上。** 确认 QEMU 启动时带了 `-gdb tcp::1234`，且没有被防火墙拦住。端口号可以改，两端一致就行。

### 本机验证状况再说明一次

编写本书的机器上没有安装 RISC-V GCC 和 QEMU，所以 `code/qemu/` 与 `code/c/` 下的这两组工程没有在本机实跑。文中的命令来自项目 README，预期现象来自程序语义。如果按上面的步骤做遇到与预期不符的情况，先核对工具链前缀、外设地址和 QEMU 参数这三样，多数问题都出在这里。

本书的核心实验不依赖它们：第 6、7 章的 Python 模拟器，第 8 至 12 章的 Verilog 仿真，都能用 Python 和 Icarus Verilog 在本机完成，第 14 章的多任务切换也有一个本机能跑的 Python 版本。工具凑不齐的时候，先用这些把原理走通，再找机会补上 QEMU 的对照实验。

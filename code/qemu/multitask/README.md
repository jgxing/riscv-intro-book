# QEMU 多任务示例

这是一个运行在 QEMU `virt` 机器上的最小抢占式多任务程序。两个任务轮流往串口写字符，定时器中断负责抢占，切换由完整的现场保存与恢复完成。它把第 11 章的陷阱机制、第 12 章的定时器外设、第 13 章的裸机 C 工程串在了一起。

## 需要的工具

- RISC-V 交叉编译器 `riscv64-unknown-elf-gcc`
- QEMU 模拟器 `qemu-system-riscv32`

推荐用官方 GNU 工具链的预编译版本，环境的安装步骤见教材附录 C。本机没有安装这两样工具，因此下面这组命令**需要在装好工具的机器上运行**。同样的机制已经在本章的 Python 模拟器里逐拍验证过（`code/python/14_multitask/`），可以先用它建立直觉。

## 运行

```sh
make            # 编译出 multitask.elf
make disasm     # 生成反汇编，看看陷阱向量和现场保存代码
make run        # 在 QEMU 里运行
```

预期在串口上看到 A 和 B 交替出现，每个字符之间隔一段延时：

```
multitask start
timer on
ABABABABABAB...
```

## 关键文件

- `start.S`：陷阱向量、完整的现场保存与恢复、`switch_context`、首次启动任务的 `start_task`。
- `main.c`：PCB 结构、轮转调度、定时器中断处理、两个任务。
- `platform.h`：UART 与 CLINT 的寄存器地址，CSR 读写的内联汇编封装。
- `multitask.ld`：链接脚本，代码放在 `0x80000000`，栈顶放在 RAM 末端。

## 和 Python 版的对应关系

| 概念 | Python 版 | QEMU 版 |
| --- | --- | --- |
| 陷阱进入 | `CPU.trap()` | `trap_handler` 的压栈段 |
| 现场保存 | `PCB.save()` | `start.S` 里 31 条 `sw` |
| 调度 | `Machine.schedule_next()` | `handle_trap()` 里轮转 current |
| 现场恢复 | `PCB.restore()` | `start.S` 里 31 条 `lw` |
| 陷阱返回 | `CPU.mret()` | `mret` 指令 |
| 定时器 | `TimerBus.tick()` | CLINT 的 mtime / mtimecmp |

特别留意一处：进入陷阱时硬件会清掉 `mstatus.MIE`，所以 `start.S` 在返回前必须用 `mret` 恢复它。如果只改 PC 而不执行 `mret`，中断就再也进不来了。Python 版演示过这个坑：初版忘了在切换后恢复中断使能，陷阱只发生了一次。

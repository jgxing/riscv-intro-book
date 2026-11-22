# RISC-V 处理器设计入门：从指令集到五级流水线

一本面向数字逻辑与程序设计基础读者的 RISC-V 入门教材。从 RV32I 指令集和汇编讲起，经过门电路、Python 模拟器与单周期处理器，最终落到带转发、停顿和冲刷的五级流水线，并延伸到异常中断、外设与基于 C 的裸机编程。

全书坚持一条主线：每条指令从取指到写回走过哪些站点，硬件为什么要这样设计。四组工具贯穿始终：RARS 看指令执行，Digital 与 Icarus Verilog 看电路与时序，Python 模拟器看指令语义，RISC-V GCC 与 QEMU 看真实软件如何落到硬件上。

## 目录结构

```
.
├── 前言.md                     写作动机、目标读者与章节安排
├── 教材大纲.md                 编写定位与详细大纲
├── 参考文献与延伸阅读.md        教材、规范、开源项目与在线资源
├── 附录A_RV32I指令与CSR速查.md
├── 附录B_Verilog模块与测试台模板.md
├── 附录C_工具链与环境搭建.md
├── chapters/                   第 1 至 14 章正文（Markdown）
├── figures/                    66 张可编辑 SVG 插图
├── cover/                      封面（SVG 源文件与 PNG 预览）
├── code/
│   ├── digital/                10 个 Digital 电路（.dig，XML 格式）
│   ├── python/
│   │   ├── 06_simulator/       取指与译码、指令语义模拟器
│   │   ├── 07_simulator/       执行、访存与完整 Python 模拟器
│   │   ├── 12_peripheral/      GPIO、UART、定时器的 Python 模型
│   │   ├── 13_toolchain/       汇编器、镜像生成与 ELF 对照
│   │   └── 14_multitask/       多任务 CPU、CLINT 与轮转调度
│   ├── verilog/
│   │   ├── 04_digital/         带使能的 D 触发器
│   │   ├── 05_arith/           ALU 与寄存器堆
│   │   ├── 08_single_cycle/    单周期处理器
│   │   ├── 09_pipeline/        五级流水线（用 NOP 规避冒险）
│   │   ├── 10_hazard/          转发、load-use 停顿与分支冲刷
│   │   ├── 11_trap/            CSR、异常、中断与 mret
│   │   ├── 12_peripheral/      GPIO、UART、定时器与总线
│   │   └── appendix_b/         通用模块与测试台模板
│   ├── c/
│   │   ├── 13_baremetal/       裸机 C 程序、启动代码与链接脚本
│   │   └── 14_integration/     综合实验：从 ELF 到仿真 Hex
│   └── qemu/
│       ├── hello/              QEMU 下的最小裸机程序
│       └── multitask/          QEMU 下的 M 模式轮转调度
└── tools/                      课件索引、Hex 生成与发布脚本
```

## 测试状态

发布前已在本机重新跑过所有不依赖 GCC/QEMU 的测试，结果如下。

| 目录 | 内容 | 结果 |
|---|---|---|
| `python/06_simulator` | 译码器测试 | 65 项通过 |
| `python/07_simulator` | 执行与访存测试 | 58 项通过 |
| `python/12_peripheral` | 外设模型测试 | 全部通过 |
| `python/13_toolchain` | 汇编与镜像生成测试 | 全部通过 |
| `python/14_multitask` | 多任务调度测试 | 27 项通过 |
| `verilog/04_digital` | D 触发器测试台 | 全部通过 |
| `verilog/05_arith` | ALU、寄存器堆测试台 | 全部通过 |
| `verilog/08_single_cycle` | 单周期核测试台 | 全部通过 |
| `verilog/09_pipeline` | 五级流水线测试台 | 全部通过 |
| `verilog/10_hazard` | 冒险处理测试台 | 全部通过 |
| `verilog/11_trap` | 异常中断测试台 | 全部通过 |
| `verilog/12_peripheral` | 外设总线测试台 | 全部通过 |
| `verilog/appendix_b` | 三个通用模板测试台 | 全部通过 |

`code/c/` 与 `code/qemu/` 里的工程需要 RISC-V GCC、QEMU 和 OpenSBI 才能运行，本机未安装这些工具，因此没有在本机实测；各目录 README 写明了构建命令与预期输出。

## 运行测试

Python 测试需要在各自目录下运行，因为程序会读取同目录的汇编源文件：

```bash
cd code/python/14_multitask
python test_multitask.py
```

Verilog 测试同样要在各自目录下编译，测试台用相对路径读取 `code.hex`：

```bash
cd code/verilog/10_hazard
iverilog -g2012 -o sim.vvp *.v
vvp sim.vvp
```

## 配套工具

- [RARS](https://github.com/TheThirdOne/rars)：图形化 RISC-V 汇编器与模拟器
- [Digital](https://github.com/hneemann/Digital)：数字电路仿真软件，用于打开 `.dig` 文件
- [Icarus Verilog](http://iverilog.icarus.edu/)：Verilog 仿真器，用于运行测试台
- [RISC-V GNU Toolchain](https://github.com/riscv-collab/riscv-gnu-toolchain)：编译 C 裸机程序
- [QEMU](https://www.qemu.org/) 与 [OpenSBI](https://github.com/riscv-software-src/opensbi)：运行真实裸机镜像

工具安装与环境变量配置见 `附录C_工具链与环境搭建.md`。

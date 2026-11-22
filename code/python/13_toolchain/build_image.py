"""从汇编生成镜像，报告段布局，装进模拟器运行，检查外设输出。"""

import os

from assemble import assemble
from cpu import CPU
from decode import decode, disasm
from demo_bus import DemoBus
from execute import execute
from memory import BASE

HERE = os.path.dirname(os.path.abspath(__file__))

# 与 link.ld 对应的逻辑地址；模拟器的物理基址是 BASE
FLASH_ORIGIN = 0x00400000
RAM_ORIGIN = 0x10000000
STACK_TOP = RAM_ORIGIN + 64 * 1024


def build():
    with open(os.path.join(HERE, "program.s"), encoding="utf-8") as f:
        words, labels = assemble(f.read())
    return words, labels


def report_sections(words, labels):
    text_size = 4 * len(words)
    print("ELF 段布局（逻辑地址，来自 link.ld）")
    print("  段        起始地址      大小     属性")
    print("  .text     0x%08x  %5d B   rx" % (FLASH_ORIGIN, text_size))
    print("  .rodata   0x%08x  %5d B   r" % (FLASH_ORIGIN + text_size, 0))
    print("  .data     0x%08x  %5d B   rwx" % (RAM_ORIGIN, 0))
    print("  .bss      0x%08x  %5d B   rwx" % (RAM_ORIGIN, 0))
    print("  栈底      0x%08x" % STACK_TOP)
    print("入口 _start（本演示的 main）: 0x%08x" % FLASH_ORIGIN)
    print("符号表: " + ", ".join("%s=0x%x" % (k, v)
                              for k, v in sorted(labels.items())))
    print()


def load_image(bus, words):
    """把逻辑地址 0x00400000 的镜像搬到模拟器基址 BASE。"""
    for i, word in enumerate(words):
        bus.store32(BASE + 4 * i, word)


def run_image(words, trace=True, max_steps=500):
    bus = DemoBus()
    load_image(bus, words)
    cpu = CPU(bus, entry=BASE)
    steps = 0
    while steps < max_steps:
        pc = cpu.get_pc()
        word = cpu.fetch()
        before = list(cpu.regs)
        running = execute(cpu, decode(word), bus)
        steps += 1
        if trace:
            changed = ["x%d=0x%08x" % (i, cpu.regs[i])
                       for i in range(1, 32) if before[i] != cpu.regs[i]]
            print("pc=0x%08x  %-22s %s"
                  % (pc, disasm(word), " ".join(changed)))
        if not running:
            break
    return cpu, bus, steps


def main():
    words, labels = build()
    print("汇编得到 %d 条指令，共 %d 字节\n" % (len(words), 4 * len(words)))
    report_sections(words, labels)
    print("反汇编（重定位到模拟器基址 0x%08x）" % BASE)
    cpu, bus, steps = run_image(words, trace=True)
    print("\n执行 %d 步后:" % steps)
    print("  sum_to(10) -> x10(a0) = %d" % cpu.get_reg(10))
    print("  LED        = 0x%02x" % bus.led)
    print("  UART 输出  = %r" % "".join(bus.uart_tx))
    ok = (cpu.get_reg(10) == 55 and bus.led == 0x37
          and "".join(bus.uart_tx) == "Hi")
    print("结果:", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    if not main():
        raise SystemExit(1)

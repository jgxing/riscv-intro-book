"""运行器：装载程序，逐条执行，打印发生变化的寄存器。"""

from bus import Bus
from cpu import CPU
from decode import decode, disasm
from execute import execute
from memory import BASE


def load_program(bus, words, data_chunks=()):
    for i, word in enumerate(words):
        bus.store32(BASE + 4 * i, word)
    for addr, blob in data_chunks:
        if isinstance(blob, int):
            bus.store32(addr, blob)
        elif isinstance(blob, (list, tuple)):
            for j, word in enumerate(blob):
                bus.store32(addr + 4 * j, word)
        else:
            for j, byte in enumerate(blob):
                bus.store8(addr + j, byte)


def run(words, data_chunks=(), max_steps=1000, trace=True):
    bus = Bus()
    load_program(bus, words, data_chunks)
    cpu = CPU(bus)
    steps = 0
    running = True
    while running and steps < max_steps:
        pc = cpu.get_pc()
        word = cpu.fetch()
        d = decode(word)
        before = list(cpu.regs)
        running = execute(cpu, d, bus)
        after = list(cpu.regs)
        steps += 1
        if trace:
            changed = ["x%d=0x%08x" % (i, after[i])
                       for i in range(1, 32) if before[i] != after[i]]
            print("pc=0x%08x  %-24s  %s"
                  % (pc, disasm(word), "  ".join(changed)))
    if steps >= max_steps:
        raise RuntimeError("step limit reached")
    return cpu, bus, steps

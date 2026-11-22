"""走通例子：把几条指令放进内存，逐条取指、译码、打印。"""

from cpu import CPU
from decode import decode, disasm
from memory import BASE, Memory

PROGRAM = [
    0x00500093,  # addi  x1, x0, 5
    0x00308133,  # add   x2, x1, x3
    0x0080A203,  # lw    x4, 8(x1)
    0x0050A023,  # sw    x5, 0(x1)
    0xFE028EE3,  # beq   x5, x0, -4
    0x00000073,  # ecall
]

mem = Memory()
for i, word in enumerate(PROGRAM):
    mem.store32(BASE + 4 * i, word)

cpu = CPU(mem)
for _ in range(len(PROGRAM)):
    pc = cpu.get_pc()
    word = cpu.fetch()
    d = decode(word)
    print("pc=0x%08x  word=0x%08x  kind=%-8s  %s"
          % (pc, word, d.kind, disasm(word)))
    cpu.pc_inc4()

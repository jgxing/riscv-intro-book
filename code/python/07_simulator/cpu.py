"""CPU 状态：程序计数器、32 个整数寄存器，以及取指操作。"""

from memory import BASE


class CPU:
    def __init__(self, mem, entry=BASE):
        self.mem = mem
        self.pc = entry
        self.regs = [0] * 32

    def get_pc(self):
        return self.pc

    def set_pc(self, addr):
        self.pc = addr & 0xFFFFFFFF

    def pc_inc4(self):
        self.set_pc(self.pc + 4)

    def get_reg(self, n):
        if n == 0:
            return 0
        return self.regs[n]

    def set_reg(self, n, value):
        if n != 0:
            self.regs[n] = value & 0xFFFFFFFF

    def fetch(self):
        return self.mem.load32(self.pc)

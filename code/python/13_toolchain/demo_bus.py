"""演示用总线：把本书第 12 章的外设地址接进第 7 章的模拟器。"""

from memory import Memory

LED_ADDR = 0xFFFF0010
UART_DATA = 0xFFFF0030
UART_STAT = 0xFFFF0034

UART_DR = 0x01
UART_THRE = 0x20


class DemoBus:
    """两块地址空间：主存在 0x80000000，外设在 0xffff0000。"""

    def __init__(self):
        self.mem = Memory()
        self.io = Memory(base=0xFFFF0000, size=0x100)
        self.uart_tx = []
        self.led = 0

    def load8(self, addr):
        if 0xFFFF0000 <= addr < 0xFFFF0100:
            if addr == UART_STAT:
                return UART_DR | UART_THRE
            return self.io.load8(addr)
        return self.mem.load8(addr)

    def store8(self, addr, value):
        if addr == LED_ADDR:
            self.led = value & 0xFF
        if addr == UART_DATA:
            self.uart_tx.append(chr(value & 0xFF))
        if 0xFFFF0000 <= addr < 0xFFFF0100:
            self.io.store8(addr, value)
        else:
            self.mem.store8(addr, value)

    def load16(self, addr):
        return self.load8(addr) | (self.load8(addr + 1) << 8)

    def store16(self, addr, value):
        self.store8(addr, value)
        self.store8(addr + 1, value >> 8)

    def load32(self, addr):
        return (self.load8(addr)
                | (self.load8(addr + 1) << 8)
                | (self.load8(addr + 2) << 16)
                | (self.load8(addr + 3) << 24))

    def store32(self, addr, value):
        self.store8(addr, value)
        self.store8(addr + 1, value >> 8)
        self.store8(addr + 2, value >> 16)
        self.store8(addr + 3, value >> 24)

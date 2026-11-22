"""带机器定时器的总线：定时器到点时把 mip 的 MTIE 位置起来。

地址沿用第 12 章：主存在 0x80000000，外设在 0xffff0000。
mtime 与 mtimecmp 是 64 位寄存器，这里只实现低 32 位，够教学演示用。
"""

from memory import Memory

MTIME = 0xFFFF0000
MTIMECMP = 0xFFFF0008
LED_ADDR = 0xFFFF0010
UART_DATA = 0xFFFF0030
UART_STAT = 0xFFFF0034

UART_DR = 0x01
UART_THRE = 0x20

MTIE = 1 << 7   # mip / mie 里的机器定时器位


class TimerBus:
    def __init__(self):
        self.mem = Memory()
        self.io = Memory(base=0xFFFF0000, size=0x100)
        self.uart_tx = []
        self.led = 0
        self.mtime = 0
        self.mtimecmp = 0xFFFFFFFF

    def tick(self):
        """每执行一条指令前进一个周期，返回是否产生了新的定时器中断。"""
        self.mtime = (self.mtime + 1) & 0xFFFFFFFF
        return self.mtime == self.mtimecmp

    def timer_pending(self):
        return self.mtime >= self.mtimecmp

    def clear_timer(self):
        """把比较值推到未来，相当于清除本次中断。"""
        self.mtimecmp = (self.mtime + 0x10000000) & 0xFFFFFFFF

    # ---- 按字节的地址译码 ----
    def load8(self, addr):
        if addr == UART_STAT:
            return UART_DR | UART_THRE
        if MTIME <= addr < MTIME + 8:
            return (self.mtime >> (8 * (addr - MTIME))) & 0xFF
        if MTIMECMP <= addr < MTIMECMP + 8:
            return (self.mtimecmp >> (8 * (addr - MTIMECMP))) & 0xFF
        if 0xFFFF0000 <= addr < 0xFFFF0100:
            return self.io.load8(addr)
        return self.mem.load8(addr)

    def store8(self, addr, value):
        if addr == LED_ADDR:
            self.led = value & 0xFF
        if addr == UART_DATA:
            self.uart_tx.append(chr(value & 0xFF))
        if MTIME <= addr < MTIME + 8:
            shift = 8 * (addr - MTIME)
            self.mtime = (self.mtime & ~(0xFF << shift)) | ((value & 0xFF) << shift)
        elif MTIMECMP <= addr < MTIMECMP + 8:
            shift = 8 * (addr - MTIMECMP)
            self.mtimecmp = (self.mtimecmp & ~(0xFF << shift)) | ((value & 0xFF) << shift)
        elif 0xFFFF0000 <= addr < 0xFFFF0100:
            self.io.store8(addr, value)
        else:
            self.mem.store8(addr, value)

    def load16(self, addr):
        return self.load8(addr) | (self.load8(addr + 1) << 8)

    def store16(self, addr, value):
        self.store8(addr, value)
        self.store8(addr + 1, value >> 8)

    def load32(self, addr):
        return (self.load8(addr) | (self.load8(addr + 1) << 8)
                | (self.load8(addr + 2) << 16) | (self.load8(addr + 3) << 24))

    def store32(self, addr, value):
        self.store8(addr, value)
        self.store8(addr + 1, value >> 8)
        self.store8(addr + 2, value >> 16)
        self.store8(addr + 3, value >> 24)

"""总线：按地址把访问分发给内存或 UART。"""

from memory import Memory
from uart import UART_BASE, UART_SIZE, UART


class Bus:
    def __init__(self, mem=None, uart=None):
        self.mem = mem if mem is not None else Memory()
        self.uart = uart if uart is not None else UART()

    def _is_uart(self, addr):
        return UART_BASE <= addr < UART_BASE + UART_SIZE

    def load8(self, addr):
        if self._is_uart(addr):
            return self.uart.read(addr - UART_BASE)
        return self.mem.load8(addr)

    def store8(self, addr, value):
        if self._is_uart(addr):
            self.uart.write(addr - UART_BASE, value)
            return
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

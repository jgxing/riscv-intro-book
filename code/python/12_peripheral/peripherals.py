"""第 12 章外设的 Python 模型：GPIO、UART、定时器与总线译码。

地址布局与 Verilog 版本一致：
  内存       0x10000000 起
  定时器低   0xffff0000，定时器高 0xffff0004
  LED        0xffff0010（写）
  开关       0xffff0020（读）
  UART 数据  0xffff0030，UART 状态 0xffff0034
"""


def u32(x):
    return x & 0xFFFFFFFF


# ---- 地址常量 ----
MEM_BASE = 0x10000000
MEM_SIZE = 0x1000

MTIME_LO = 0xFFFF0000
MTIME_HI = 0xFFFF0004
LED_ADDR = 0xFFFF0010
SW_ADDR = 0xFFFF0020
UART_DATA = 0xFFFF0030
UART_STAT = 0xFFFF0034

LSR_DR = 0x01    # 接收数据就绪
LSR_THRE = 0x20  # 发送保持寄存器空


class GPIO:
    """两个寄存器：写 LED，读开关。"""

    def __init__(self):
        self.led = 0

    def matches(self, addr):
        return addr in (LED_ADDR, SW_ADDR)

    def read(self, addr, switches):
        if addr == SW_ADDR:
            return switches & 0xFF
        return 0

    def write(self, addr, value):
        if addr == LED_ADDR:
            self.led = value & 0xFF


class UART:
    """一个数据寄存器，一个状态寄存器，行为对齐 Verilog 版。"""

    def __init__(self):
        self.rx_queue = []
        self.tx_log = []

    def matches(self, addr):
        return addr in (UART_DATA, UART_STAT)

    def feed(self, data):
        if isinstance(data, str):
            data = data.encode("ascii")
        self.rx_queue.extend(data)

    def read(self, addr):
        if addr == UART_DATA:
            return self.rx_queue.pop(0) if self.rx_queue else 0
        if addr == UART_STAT:
            status = LSR_THRE
            if self.rx_queue:
                status |= LSR_DR
            return status
        return 0

    def write(self, addr, value):
        if addr == UART_DATA:
            self.tx_log.append(value & 0xFF)

    def output(self):
        return bytes(self.tx_log).decode("ascii", errors="replace")


class Timer:
    """64 位自由运行计数器，读低 32 位或高 32 位。"""

    def __init__(self):
        self.count = 0

    def matches(self, addr):
        return (MTIME_LO <= addr < MTIME_LO + 4) or \
               (MTIME_HI <= addr < MTIME_HI + 4)

    def tick(self):
        self.count = (self.count + 1) & 0xFFFFFFFFFFFFFFFF

    def read(self, addr):
        if MTIME_LO <= addr < MTIME_LO + 4:
            return (self.count >> (8 * (addr - MTIME_LO))) & 0xFF
        if MTIME_HI <= addr < MTIME_HI + 4:
            return (self.count >> (32 + 8 * (addr - MTIME_HI))) & 0xFF
        return 0


class Bus:
    """按地址把字节访问分发给内存或外设。"""

    def __init__(self, switches=0):
        self.mem = bytearray(MEM_SIZE)
        self.switches = switches & 0xFF
        self.gpio = GPIO()
        self.uart = UART()
        self.timer = Timer()

    @staticmethod
    def _in_mem(addr):
        return MEM_BASE <= addr < MEM_BASE + MEM_SIZE

    def load8(self, addr):
        addr = u32(addr)
        if self._in_mem(addr):
            return self.mem[addr - MEM_BASE]
        if self.gpio.matches(addr):
            return self.gpio.read(addr, self.switches) & 0xFF
        if self.uart.matches(addr):
            return self.uart.read(addr) & 0xFF
        if self.timer.matches(addr):
            return self.timer.read(addr) & 0xFF
        return 0

    def store8(self, addr, value):
        addr = u32(addr)
        value &= 0xFF
        if self._in_mem(addr):
            self.mem[addr - MEM_BASE] = value
        elif addr == LED_ADDR:
            self.gpio.write(addr, value)
        elif addr == UART_DATA:
            self.uart.write(addr, value)

    def load32(self, addr):
        return (self.load8(addr)
                | (self.load8(addr + 1) << 8)
                | (self.load8(addr + 2) << 16)
                | (self.load8(addr + 3) << 24))

    def store32(self, addr, value):
        for i in range(4):
            self.store8(addr + i, (value >> (8 * i)) & 0xFF)

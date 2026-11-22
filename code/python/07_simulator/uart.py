"""简化的 16550 UART：一个数据寄存器，一个线路状态寄存器。"""

UART_BASE = 0x10000000
UART_SIZE = 8

RBR = 0x00  # 接收缓冲寄存器，读
THR = 0x00  # 发送保持寄存器，写
LSR = 0x05  # 线路状态寄存器，读

LSR_DR = 0x01   # 接收数据就绪
LSR_THRE = 0x20  # 发送保持寄存器空


class UART:
    def __init__(self):
        self.rx_fifo = []
        self.tx_log = []

    def feed(self, data):
        if isinstance(data, str):
            data = data.encode("ascii")
        self.rx_fifo.extend(data)

    def read(self, offset):
        if offset == RBR:
            return self.rx_fifo.pop(0) if self.rx_fifo else 0
        if offset == LSR:
            status = LSR_THRE
            if self.rx_fifo:
                status |= LSR_DR
            return status
        return 0

    def write(self, offset, value):
        if offset == THR:
            self.tx_log.append(value & 0xFF)

    def output(self):
        return bytes(self.tx_log).decode("ascii", errors="replace")

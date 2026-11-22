"""第 12 章外设对照演示：用 Python 复现硬件里那一套地址访问。"""

from peripherals import Bus, LED_ADDR, SW_ADDR, UART_DATA, UART_STAT, \
    MTIME_LO, MEM_BASE


def main():
    bus = Bus(switches=0x5a)

    # 点亮 LED：写一个字节到 0xffff0010
    bus.store8(LED_ADDR, 0xa5)
    print("LED = 0x%02x" % bus.gpio.led)

    # 读开关：从 0xffff0020 读回 0x5a
    sw = bus.load8(SW_ADDR)
    print("switch = 0x%02x" % sw)

    # 串口输出 Hi：逐字节写到 0xffff0030
    for ch in b"Hi":
        bus.store8(UART_DATA, ch)
    print("UART output =", bus.uart.output())

    # 从串口读一个字符，再看状态寄存器
    bus.uart.feed("Z")
    print("UART status with data = 0x%02x" % bus.load8(UART_STAT))
    print("UART read = %r" % chr(bus.load8(UART_DATA)))
    print("UART status after read = 0x%02x" % bus.load8(UART_STAT))

    # 定时器：走几拍，读低 32 位
    for _ in range(5):
        bus.timer.tick()
    print("timer low = %d" % bus.load32(MTIME_LO))

    # 普通内存读写仍然走同一套 load/store
    bus.store32(MEM_BASE, 0x12345678)
    print("mem[0] = 0x%08x" % bus.load32(MEM_BASE))


if __name__ == "__main__":
    main()

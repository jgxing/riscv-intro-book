"""第 12 章外设模型自检：逐项核对 GPIO、UART、定时器与总线译码。"""

from peripherals import Bus, LED_ADDR, SW_ADDR, UART_DATA, UART_STAT, \
    MTIME_LO, MTIME_HI, MEM_BASE, LSR_DR, LSR_THRE

errors = 0


def chk(got, want, label):
    global errors
    if got != want:
        print("FAIL %-32s got=%r want=%r" % (label, got, want))
        errors += 1
    else:
        print("PASS %-32s = %r" % (label, got))


bus = Bus(switches=0x5a)

# GPIO
bus.store8(LED_ADDR, 0xa5)
chk(bus.gpio.led, 0xa5, "LED write")
chk(bus.load8(SW_ADDR), 0x5a, "switch read")

# UART 发送
for ch in b"Hi":
    bus.store8(UART_DATA, ch)
chk(bus.uart.output(), "Hi", "UART tx string")

# UART 接收与状态
chk(bus.load8(UART_STAT), LSR_THRE, "status empty")
bus.uart.feed("Z")
chk(bus.load8(UART_STAT), LSR_THRE | LSR_DR, "status has data")
chk(bus.load8(UART_DATA), ord("Z"), "UART rx byte")
chk(bus.load8(UART_STAT), LSR_THRE, "status empty again")

# 定时器
for _ in range(300):
    bus.timer.tick()
chk(bus.load32(MTIME_LO), 300, "timer low 32 bits")
chk(bus.load32(MTIME_HI), 0, "timer high 32 bits")

# 定时器跨 32 位边界
bus.timer.count = (1 << 32) + 7
chk(bus.load32(MTIME_LO), 7, "timer low after wrap")
chk(bus.load32(MTIME_HI), 1, "timer high after wrap")

# 普通内存
bus.store32(MEM_BASE + 4, 0xdeadbeef)
chk(bus.load32(MEM_BASE + 4), 0xdeadbeef, "memory word roundtrip")

# 未映射地址读回 0
chk(bus.load8(0x00000000), 0, "unmapped read zero")

if errors == 0:
    print("ALL TESTS PASSED")
else:
    print("%d TESTS FAILED" % errors)

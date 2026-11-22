"""两个能在本模拟器上跑的小程序，机器码由 encode.py 生成。"""

from encode import enc_b, enc_i, enc_j, enc_r, enc_s, enc_u
from memory import BASE

# 数组求和：x1 指向数组，x2 是剩余个数，x3 累加，结果写到 UART 数据寄存器
SUM_PROGRAM = [
    enc_u(0x80000000, 1, 0x37),       # 0  lui   x1, 0x80000
    enc_i(0x100, 1, 0, 1, 0x13),      # 1  addi  x1, x1, 256
    enc_i(5, 0, 0, 2, 0x13),          # 2  addi  x2, x0, 5
    enc_i(0, 0, 0, 3, 0x13),          # 3  addi  x3, x0, 0
    enc_i(0, 1, 2, 4, 0x03),          # 4  lw    x4, 0(x1)      <- loop
    enc_r(0, 4, 3, 0, 3, 0x33),       # 5  add   x3, x3, x4
    enc_i(4, 1, 0, 1, 0x13),          # 6  addi  x1, x1, 4
    enc_i(-1, 2, 0, 2, 0x13),         # 7  addi  x2, x2, -1
    enc_b(-16, 0, 2, 1, 0x63),        # 8  bne   x2, x0, -16
    enc_u(0x10000000, 5, 0x37),       # 9  lui   x5, 0x10000
    enc_s(0, 3, 5, 2, 0x23),          # 10 sw    x3, 0(x5)
    enc_i(0, 0, 0, 0, 0x73),          # 11 ecall
]

# 串口打印：逐字节读字符串，遇到结尾 0 停止
PRINT_PROGRAM = [
    enc_u(0x80000000, 1, 0x37),       # 0  lui   x1, 0x80000
    enc_i(0x200, 1, 0, 1, 0x13),      # 1  addi  x1, x1, 512
    enc_u(0x10000000, 5, 0x37),       # 2  lui   x5, 0x10000
    enc_i(0, 0, 0, 2, 0x13),          # 3  addi  x2, x0, 0
    enc_r(0, 2, 1, 0, 3, 0x33),       # 4  add   x3, x1, x2     <- loop
    enc_i(0, 3, 4, 4, 0x03),          # 5  lbu   x4, 0(x3)
    enc_b(16, 0, 4, 0, 0x63),         # 6  beq   x4, x0, 16     -> done
    enc_s(0, 4, 5, 2, 0x23),          # 7  sw    x4, 0(x5)
    enc_i(1, 2, 0, 2, 0x13),          # 8  addi  x2, x2, 1
    enc_j(-20, 0, 0x6F),              # 9  jal   x0, -20        -> loop
    enc_i(0, 0, 0, 0, 0x73),          # 10 ecall                <- done
]

SUM_DATA_ADDR = BASE + 0x100
SUM_DATA = [10, 20, 30, 40, 50]

PRINT_DATA_ADDR = BASE + 0x200
PRINT_DATA = b"Hi, RV32I!\n"

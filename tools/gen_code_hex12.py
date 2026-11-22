# 生成第 12 章外设实验的指令存储器镜像
# 基地址 0x00400000，外设区从 0xffff0000 开始

BASE = 0x00400000
DEPTH = 1024


def r_type(funct7, rs2, rs1, funct3, rd, opcode):
    return ((funct7 & 0x7f) << 25) | ((rs2 & 0x1f) << 20) | \
           ((rs1 & 0x1f) << 15) | ((funct3 & 7) << 12) | \
           ((rd & 0x1f) << 7) | opcode


def u_type(imm20, rd, opcode):
    return ((imm20 & 0xfffff) << 12) | ((rd & 0x1f) << 7) | opcode


def i_type(imm, rs1, funct3, rd, opcode):
    return ((imm & 0xfff) << 20) | ((rs1 & 0x1f) << 15) | \
           ((funct3 & 7) << 12) | ((rd & 0x1f) << 7) | opcode


def s_type(imm, rs2, rs1, funct3, opcode):
    imm &= 0xfff
    return ((imm >> 5) << 25) | ((rs2 & 0x1f) << 20) | \
           ((rs1 & 0x1f) << 15) | ((funct3 & 7) << 12) | \
           ((imm & 0x1f) << 7) | opcode


def j_type(imm, rd, opcode):
    imm &= 0x1fffff
    b20 = (imm >> 20) & 1
    b19_12 = (imm >> 12) & 0xff
    b11 = (imm >> 11) & 1
    b10_1 = (imm >> 1) & 0x3ff
    return (b20 << 31) | (b10_1 << 21) | (b11 << 20) | \
           (b19_12 << 12) | ((rd & 0x1f) << 7) | opcode


NOP = 0x00000013
prog = {}

# x1 = 0xffff0000，所有外设地址都以它为基址
prog[0x00] = u_type(0xffff0, 1, 0x37)          # lui  x1, 0xffff0      -> 0xffff0000
prog[0x04] = i_type(0xa5, 0, 0, 2, 0x13)       # addi x2, x0, 0xa5     -> 0xa5 点灯图案
prog[0x08] = i_type(0x10, 1, 0, 3, 0x13)       # addi x3, x1, 0x10     -> LED 地址
prog[0x0c] = s_type(0, 2, 3, 0b010, 0x23)      # sw   x2, 0(x3)        写 LED
prog[0x10] = i_type(0x20, 1, 0, 4, 0x13)       # addi x4, x1, 0x20     -> 开关地址
prog[0x14] = i_type(0, 4, 0b010, 5, 0x03)      # lw   x5, 0(x4)        读开关 -> x5
prog[0x18] = i_type(0x48, 0, 0, 6, 0x13)       # addi x6, x0, 0x48     -> 'H'
prog[0x1c] = i_type(0x30, 1, 0, 7, 0x13)       # addi x7, x1, 0x30     -> UART 数据地址
prog[0x20] = s_type(0, 6, 7, 0b010, 0x23)      # sw   x6, 0(x7)        发送 'H'
prog[0x24] = i_type(0x69, 0, 0, 8, 0x13)       # addi x8, x0, 0x69     -> 'i'
prog[0x28] = s_type(0, 8, 7, 0b010, 0x23)      # sw   x8, 0(x7)        发送 'i'
prog[0x2c] = i_type(0x34, 1, 0, 9, 0x13)       # addi x9, x1, 0x34     -> UART 状态地址
prog[0x30] = i_type(0, 9, 0b010, 10, 0x03)     # lw   x10, 0(x9)       读 UART 状态 -> x10
prog[0x34] = i_type(0, 1, 0b010, 11, 0x03)     # lw   x11, 0(x1)        读定时器低 32 位 -> x11
prog[0x38] = i_type(0, 7, 0b010, 12, 0x03)     # lw   x12, 0(x7)        读 UART 接收数据 -> x12
prog[0x3c] = j_type(0, 0, 0x6f)                # j    0x3c             停机自环

words = [prog.get(i * 4, NOP) for i in range(DEPTH)]
out = "D:/aiprojects/workbuddy/riscv入门教程/code/verilog/12_peripheral/code.hex"
with open(out, "w", encoding="utf-8") as f:
    for w in words:
        f.write("%08x\n" % w)

for off in sorted(prog):
    print("0x%02x: %08x" % (off, prog[off]))
print("wrote", out, len(words), "words")

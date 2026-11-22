"""生成第 10 章冒险处理测试用的 code.hex。

程序不插 NOP，覆盖四类情况：
  1. EX/MEM 与 MEM/WB 两条转发路径
  2. 同一寄存器连续写时的优先级
  3. store 数据转发、load-use 停顿
  4. 分支 taken/not taken、jal、jalr 的冲刷与链接地址转发
"""
from pathlib import Path

MASK32 = 0xFFFFFFFF
NOP = 0x00000013


def enc_r(f7, rs2, rs1, f3, rd, op):
    return ((f7 << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | op) & MASK32


def enc_i(imm, rs1, f3, rd, op):
    return ((imm << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | op) & MASK32


def enc_s(imm, rs2, rs1, f3, rd, op):
    return (((imm >> 5) << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | ((imm & 0x1F) << 7) | op) & MASK32


def enc_u(imm, rd, op):
    return (((imm & 0xFFFFF) << 12) | (rd << 7) | op) & MASK32


def enc_b(imm, rs2, rs1, f3, rd, op):
    imm &= 0x1FFF
    return (((imm >> 12) << 31) | (((imm >> 5) & 0x3F) << 25) | (rs2 << 20) | (rs1 << 15)
            | (f3 << 12) | (((imm >> 1) & 0xF) << 8) | (((imm >> 11) & 1) << 7) | op) & MASK32


def enc_j(imm, rd, op):
    imm &= 0x1FFFFF
    return (((imm >> 20) << 31) | (((imm >> 1) & 0x3FF) << 21) | (((imm >> 11) & 1) << 20)
            | (((imm >> 12) & 0xFF) << 12) | (rd << 7) | op) & MASK32


prog = [
    (enc_i(5, 0, 0, 1, 0x13),  "addi  x1, x0, 5"),
    (enc_i(3, 1, 0, 2, 0x13),  "addi  x2, x1, 3       # EX/MEM 转发"),
    (enc_i(7, 0, 0, 1, 0x13),  "addi  x1, x0, 7"),
    (enc_r(0, 2, 1, 0, 3, 0x33), "add   x3, x1, x2     # 两个源都转发"),
    (enc_u(0x10000, 10, 0x37), "lui   x10, 0x10000"),
    (enc_i(9, 0, 0, 4, 0x13),  "addi  x4, x0, 9"),
    (enc_s(0, 4, 10, 2, 0, 0x23), "sw    x4, 0(x10)     # store 数据转发"),
    (enc_i(0, 10, 2, 5, 0x03), "lw    x5, 0(x10)"),
    (enc_i(1, 5, 0, 6, 0x13),  "addi  x6, x5, 1       # load-use 停顿"),
    (enc_i(4, 0, 0, 7, 0x13),  "addi  x7, x0, 4"),
    (enc_b(12, 7, 7, 0, 0, 0x63), "beq   x7, x7, 12    # taken, 冲刷两条"),
    (enc_i(111, 0, 0, 8, 0x13), "addi  x8, x0, 111    # 被冲刷"),
    (enc_i(222, 0, 0, 9, 0x13), "addi  x9, x0, 222    # 被冲刷"),
    (enc_i(42, 0, 0, 8, 0x13), "addi  x8, x0, 42"),
    (enc_b(8, 0, 7, 0, 0, 0x63), "beq   x7, x0, 8      # not taken"),
    (enc_i(55, 0, 0, 9, 0x13), "addi  x9, x0, 55"),
    (enc_j(16, 11, 0x6F),     "jal   x11, 16        # x11=0x44, 跳 0x50"),
    (enc_i(666, 0, 0, 12, 0x13), "addi x12, x0, 666   # 被冲刷"),
    (enc_i(777, 0, 0, 13, 0x13), "addi x13, x0, 777   # 被冲刷"),
    (NOP,                     "nop                  # 被跳过"),
    (enc_j(4, 11, 0x6F),      "jal   x11, 4         # x11=0x54"),
    (enc_i(0, 11, 0, 14, 0x67), "jalr  x14, x11, 0   # 目标 0x54, 自环"),
    (enc_i(0, 0, 0, 0, 0x13), "nop                  # 不会执行"),
]

words = [w for w, _ in prog]
DEPTH = 1024
full = words + [0] * (DEPTH - len(words))

out = Path("D:/aiprojects/workbuddy/riscv入门教程/code/verilog/10_hazard/code.hex")
out.write_text("\n".join("%08x" % w for w in full) + "\n", encoding="utf-8")
print("wrote", out, len(full), "words (", len(words), "real instructions )")
for i, (w, asm) in enumerate(prog):
    print("0x%08x  0x%08x  %s" % (0x00400000 + i * 4, w, asm))

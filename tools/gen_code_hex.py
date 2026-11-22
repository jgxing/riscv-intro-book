"""生成第 8 章单周期处理器测试用的 code.hex。"""
from pathlib import Path

MASK32 = 0xFFFFFFFF


def enc_r(f7, rs2, rs1, f3, rd, op):
    return ((f7 << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | op) & MASK32


def enc_i(imm, rs1, f3, rd, op):
    return ((imm << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | op) & MASK32


def enc_s(imm, rs2, rs1, f3, rd, op):
    return (((imm >> 5) << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | ((imm & 0x1F) << 7) | op) & MASK32


def enc_b(imm, rs2, rs1, f3, rd, op):
    imm &= 0x1FFF
    return (((imm >> 12) << 31) | (((imm >> 5) & 0x3F) << 25) | (rs2 << 20) | (rs1 << 15)
            | (f3 << 12) | (((imm >> 1) & 0xF) << 8) | (((imm >> 11) & 1) << 7) | op) & MASK32


def enc_u(imm, rd, op):
    return (((imm & 0xFFFFF) << 12) | (rd << 7) | op) & MASK32


def enc_j(imm, rd, op):
    imm &= 0x1FFFFF
    return (((imm >> 20) << 31) | (((imm >> 1) & 0x3FF) << 21) | (((imm >> 11) & 1) << 20)
            | (((imm >> 12) & 0xFF) << 12) | (rd << 7) | op) & MASK32


# 测试程序
prog = [
    enc_i(5, 0, 0, 1, 0x13),        # 0x00  addi x1, x0, 5
    enc_i(3, 0, 0, 2, 0x13),        # 0x04  addi x2, x0, 3
    enc_r(0, 2, 1, 0, 3, 0x33),     # 0x08  add  x3, x1, x2
    enc_u(0x10000, 4, 0x37),        # 0x0C  lui  x4, 0x10000  -> x4=0x10000000
    enc_s(0, 3, 4, 2, 0, 0x23),     # 0x10  sw   x3, 0(x4)
    enc_i(0, 4, 2, 5, 0x03),        # 0x14  lw   x5, 0(x4)
    enc_b(8, 3, 5, 0, 0, 0x63),     # 0x18  beq  x5, x3, +8
    enc_i(99, 0, 0, 6, 0x13),       # 0x1C  addi x6, x0, 99  (should be skipped)
    enc_i(42, 0, 0, 7, 0x13),       # 0x20  addi x7, x0, 42
    enc_j(0, 0, 0x6F),              # 0x24  jal  x0, 0  (self loop)
]

DEPTH = 1024
words = prog + [0] * (DEPTH - len(prog))

out = Path("D:/aiprojects/workbuddy/riscv入门教程/code/verilog/08_single_cycle/code.hex")
out.write_text("\n".join("%08x" % w for w in words) + "\n", encoding="utf-8")
print("wrote", out, len(words), "words (", len(prog), "real instructions )")
for i, w in enumerate(prog):
    print("0x%08x  0x%08x" % (0x00400000 + i * 4, w))

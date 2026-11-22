"""生成第 9 章五级流水线测试用的 code.hex。

与第 8 章程序语义相同，但在有数据相关的指令之间插入 NOP，
让消费者在第 4 拍之后才读寄存器。第 10 章会用转发把这些 NOP 去掉。
"""
from pathlib import Path

MASK32 = 0xFFFFFFFF
NOP = 0x00000013  # addi x0, x0, 0


def enc_r(f7, rs2, rs1, f3, rd, op):
    return ((f7 << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | op) & MASK32


def enc_i(imm, rs1, f3, rd, op):
    return ((imm << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | op) & MASK32


def enc_s(imm, rs2, rs1, f3, rd, op):
    return (((imm >> 5) << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | ((imm & 0x1F) << 7) | op) & MASK32


def enc_u(imm, rd, op):
    return (((imm & 0xFFFFF) << 12) | (rd << 7) | op) & MASK32


def enc_j(imm, rd, op):
    imm &= 0x1FFFFF
    return (((imm >> 20) << 31) | (((imm >> 1) & 0x3FF) << 21) | (((imm >> 11) & 1) << 20)
            | (((imm >> 12) & 0xFF) << 12) | (rd << 7) | op) & MASK32


prog = [
    (enc_i(5, 0, 0, 1, 0x13), "addi x1, x0, 5"),
    (enc_i(3, 0, 0, 2, 0x13), "addi x2, x0, 3"),
    (NOP, "nop"),
    (NOP, "nop"),
    (NOP, "nop"),
    (enc_r(0, 2, 1, 0, 3, 0x33), "add  x3, x1, x2"),
    (enc_u(0x10000, 4, 0x37), "lui  x4, 0x10000"),
    (NOP, "nop"),
    (NOP, "nop"),
    (NOP, "nop"),
    (enc_s(0, 3, 4, 2, 0, 0x23), "sw   x3, 0(x4)"),
    (enc_i(0, 4, 2, 5, 0x03), "lw   x5, 0(x4)"),
    (NOP, "nop"),
    (NOP, "nop"),
    (NOP, "nop"),
    (enc_i(1, 5, 0, 6, 0x13), "addi x6, x5, 1"),
    (enc_j(0, 0, 0x6F), "jal  x0, 0"),
]
words = [w for w, _ in prog]

DEPTH = 1024
full = words + [0] * (DEPTH - len(words))

out = Path("D:/aiprojects/workbuddy/riscv入门教程/code/verilog/09_pipeline/code.hex")
out.write_text("\n".join("%08x" % w for w in full) + "\n", encoding="utf-8")
print("wrote", out, len(full), "words (", len(words), "real instructions )")
for i, (w, asm) in enumerate(prog):
    print("0x%08x  0x%08x  %s" % (0x00400000 + i * 4, w, asm))

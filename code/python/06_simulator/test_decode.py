"""第 6 章自测：内存读写、字段提取、立即数与译码。"""

import tempfile
from pathlib import Path

from cpu import CPU
from decode import (decode, disasm, get_funct3, get_funct7, get_opcode, get_rd,
                    get_rs1, get_rs2, imm_b, imm_i, imm_j, imm_s, imm_u)
from memory import BASE, Memory

passed = 0
failed = 0


def check(got, want, msg):
    global passed, failed
    if got == want:
        passed += 1
    else:
        failed += 1
        print("FAIL %-40s got %r want %r" % (msg, got, want))


def enc_r(f7, rs2, rs1, f3, rd, op):
    return ((f7 << 25) | (rs2 << 20) | (rs1 << 15)
            | (f3 << 12) | (rd << 7) | op)


def enc_i(imm, rs1, f3, rd, op):
    return (((imm & 0xFFF) << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | op)


def enc_s(imm, rs2, rs1, f3, op):
    im = imm & 0xFFF
    return ((((im >> 5) & 0x7F) << 25) | (rs2 << 20) | (rs1 << 15)
            | (f3 << 12) | ((im & 0x1F) << 7) | op)


def enc_b(imm, rs2, rs1, f3, op):
    im = imm & 0x1FFF
    return ((((im >> 12) & 1) << 31) | (((im >> 5) & 0x3F) << 25)
            | (rs2 << 20) | (rs1 << 15) | (f3 << 12)
            | (((im >> 1) & 0xF) << 8) | (((im >> 11) & 1) << 7) | op)


def enc_u(imm, rd, op):
    return ((imm & 0xFFFFF000) | (rd << 7) | op)


def enc_j(imm, rd, op):
    im = imm & 0x1FFFFF
    return ((((im >> 20) & 1) << 31) | (((im >> 1) & 0x3FF) << 21)
            | (((im >> 11) & 1) << 20) | (((im >> 12) & 0xFF) << 12)
            | (rd << 7) | op)


# 内存：小端与地址检查
mem = Memory()
mem.store32(BASE, 0x12345678)
check(mem.load8(BASE), 0x78, "little endian byte 0")
check(mem.load8(BASE + 1), 0x56, "little endian byte 1")
check(mem.load8(BASE + 2), 0x34, "little endian byte 2")
check(mem.load8(BASE + 3), 0x12, "little endian byte 3")
check(mem.load32(BASE), 0x12345678, "store32 then load32")
try:
    mem.load32(BASE + Memory().mem.__len__() - 2)
    check(False, True, "out of range must raise")
except ValueError:
    check(True, True, "out of range raises ValueError")

with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "image.bin"
    p.write_bytes(bytes([0x93, 0x00, 0x05, 0x00]))
    check(mem.load_image(str(p), BASE + 0x100), 4, "load_image returns byte count")
    check(mem.load32(BASE + 0x100), 0x00050093, "load_image loads little endian")

# 字段提取：addi x1, x0, 5
w = 0x00500093
check(get_opcode(w), 0x13, "opcode of addi")
check(get_rd(w), 1, "rd of addi")
check(get_funct3(w), 0, "funct3 of addi")
check(get_rs1(w), 0, "rs1 of addi")
check(get_rs2(w), 5, "I-type bits 25:31 hold imm[11:5], not rs2")

# 立即数：正负、拼接
check(imm_i(enc_i(-1, 0, 0, 1, 0x13)), -1, "imm_i sign extend")
check(imm_i(enc_i(2047, 0, 0, 1, 0x13)), 2047, "imm_i positive max")
check(imm_s(enc_s(-8, 2, 1, 2, 0x23)), -8, "imm_s sign extend")
check(imm_b(enc_b(-6, 2, 1, 0, 0x63)), -6, "imm_b sign extend")
check(imm_b(enc_b(4094, 2, 1, 0, 0x63)), 4094, "imm_b positive max")
check(imm_u(enc_u(0x12345000, 3, 0x37)), 0x12345000, "imm_u keeps high 20 bits")
check(imm_j(enc_j(-1024, 1, 0x6F)), -1024, "imm_j sign extend")

# 译码与反汇编
cases = [
    (enc_r(0x00, 3, 1, 0, 2, 0x33), "add", "add x2, x1, x3", 0),
    (enc_r(0x20, 3, 1, 0, 2, 0x33), "sub", "sub x2, x1, x3", 0),
    (enc_i(5, 0, 0, 1, 0x13), "addi", "addi x1, x0, 5", 5),
    (enc_i(-1, 1, 0, 2, 0x13), "addi", "addi x2, x1, -1", -1),
    (enc_i(0x400, 1, 5, 2, 0x13), "srai", "srai x2, x1, 0", 0x400),
    (enc_i(8, 1, 2, 4, 0x03), "lw", "lw x4, 8(x1)", 8),
    (enc_s(4, 5, 1, 2, 0x23), "sw", "sw x5, 4(x1)", 4),
    (enc_b(-8, 2, 1, 0, 0x63), "beq", "beq x1, x2, -8", -8),
    (enc_u(0x10000000, 1, 0x37), "lui", "lui x1, 0x10000", 0x10000000),
    (enc_u(0x80000000, 1, 0x17), "auipc", "auipc x1, 0x80000", 0x80000000),
    (enc_j(4, 1, 0x6F), "jal", "jal x1, +4", 4),
    (enc_i(0, 2, 0, 1, 0x67), "jalr", "jalr x1, 0(x2)", 0),
    (enc_i(0, 0, 0, 0, 0x73), "ecall", "ecall", 0),
]
for w, name, text, imm in cases:
    d = decode(w)
    check(d.name, name, "decode name " + name)
    check(d.imm, imm, "decode imm " + name)
    check(disasm(w), text, "disasm " + text)

check(decode(0x00000000).name, "illegal", "zero word is illegal")

# CPU：取指与 PC
mem2 = Memory()
for i, w in enumerate([0x00500093, 0x003100B3, 0x00000013]):
    mem2.store32(BASE + 4 * i, w)
cpu = CPU(mem2)
check(cpu.get_pc(), BASE, "initial pc")
check(cpu.fetch(), 0x00500093, "fetch first word")
cpu.pc_inc4()
check(cpu.get_pc(), BASE + 4, "pc_inc4")
cpu.set_reg(5, 0x12345678)
check(cpu.get_reg(5), 0x12345678, "set/get reg")
cpu.set_reg(0, 999)
check(cpu.get_reg(0), 0, "x0 stays zero")

print("passed %d, failed %d" % (passed, failed))
if failed:
    raise SystemExit(1)
print("ALL TESTS PASSED")

"""测试与示例程序用的编码辅助：按字段把 RV32I 指令拼成 32 位机器码。"""


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

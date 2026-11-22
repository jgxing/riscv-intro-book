"""指令字段提取与译码：把 32 位指令字拆成操作码、寄存器号和立即数。"""

from collections import namedtuple

Inst = namedtuple("Inst", "opcode rd funct3 rs1 rs2 funct7 imm kind name")

OPCODE_KIND = {
    0x37: "lui", 0x17: "auipc", 0x6F: "jal", 0x67: "jalr",
    0x63: "branch", 0x03: "load", 0x23: "store",
    0x13: "op-imm", 0x33: "op", 0x0F: "fence", 0x73: "system",
}

KIND_FORM = {
    "lui": "U", "auipc": "U", "jal": "J", "branch": "B", "store": "S",
    "jalr": "I", "load": "I", "op-imm": "I", "fence": "I", "system": "I",
    "op": "R",
}

R_NAME = {
    (0x00, 0): "add", (0x20, 0): "sub",
    (0x00, 1): "sll", (0x00, 2): "slt", (0x00, 3): "sltu",
    (0x00, 4): "xor", (0x00, 5): "srl", (0x20, 5): "sra",
    (0x00, 6): "or", (0x00, 7): "and",
}
OP_IMM_NAME = {0: "addi", 1: "slli", 2: "slti", 3: "sltiu", 4: "xori", 6: "ori", 7: "andi"}
LOAD_NAME = {0: "lb", 1: "lh", 2: "lw", 4: "lbu", 5: "lhu"}
STORE_NAME = {0: "sb", 1: "sh", 2: "sw"}
BRANCH_NAME = {0: "beq", 1: "bne", 4: "blt", 5: "bge", 6: "bltu", 7: "bgeu"}


def get_opcode(inst):
    return inst & 0x7F


def get_rd(inst):
    return (inst >> 7) & 0x1F


def get_funct3(inst):
    return (inst >> 12) & 0x7


def get_rs1(inst):
    return (inst >> 15) & 0x1F


def get_rs2(inst):
    return (inst >> 20) & 0x1F


def get_funct7(inst):
    return (inst >> 25) & 0x7F


def sext(value, bits):
    sign = 1 << (bits - 1)
    return value - (1 << bits) if value & sign else value


def imm_i(inst):
    return sext((inst >> 20) & 0xFFF, 12)


def imm_s(inst):
    imm = (((inst >> 25) & 0x7F) << 5) | ((inst >> 7) & 0x1F)
    return sext(imm, 12)


def imm_b(inst):
    imm = (((inst >> 31) & 1) << 12
           | ((inst >> 7) & 1) << 11
           | ((inst >> 25) & 0x3F) << 5
           | ((inst >> 8) & 0xF) << 1)
    return sext(imm, 13)


def imm_u(inst):
    return inst & 0xFFFFF000


def imm_j(inst):
    imm = (((inst >> 31) & 1) << 20
           | ((inst >> 12) & 0xFF) << 12
           | ((inst >> 20) & 1) << 11
           | ((inst >> 21) & 0x3FF) << 1)
    return sext(imm, 21)


IMM_FUNCS = {"I": imm_i, "S": imm_s, "B": imm_b, "U": imm_u, "J": imm_j, "R": None}


def inst_name(kind, f3, f7, imm):
    if kind == "op":
        return R_NAME.get((f7, f3), "op?")
    if kind == "op-imm":
        if f3 == 5:
            return "srai" if f7 == 0x20 else "srli"
        return OP_IMM_NAME.get(f3, "op-imm?")
    if kind == "load":
        return LOAD_NAME.get(f3, "load?")
    if kind == "store":
        return STORE_NAME.get(f3, "store?")
    if kind == "branch":
        return BRANCH_NAME.get(f3, "branch?")
    if kind == "system":
        if imm == 0:
            return "ecall"
        if imm == 1:
            return "ebreak"
        return "csr"
    if kind == "illegal":
        return "illegal"
    return kind


def decode(inst):
    opcode = get_opcode(inst)
    kind = OPCODE_KIND.get(opcode, "illegal")
    rd = get_rd(inst)
    f3 = get_funct3(inst)
    rs1 = get_rs1(inst)
    rs2 = get_rs2(inst)
    f7 = get_funct7(inst)
    imm = 0
    if kind != "illegal":
        func = IMM_FUNCS[KIND_FORM[kind]]
        if func is not None:
            imm = func(inst)
    return Inst(opcode, rd, f3, rs1, rs2, f7, imm, kind,
                inst_name(kind, f3, f7, imm))


def disasm(inst):
    d = decode(inst)
    n = d.name
    if n in R_NAME.values():
        return "%s x%d, x%d, x%d" % (n, d.rd, d.rs1, d.rs2)
    if n in ("addi", "slti", "sltiu", "xori", "ori", "andi", "slli"):
        return "%s x%d, x%d, %d" % (n, d.rd, d.rs1, d.imm)
    if n in ("srli", "srai"):
        return "%s x%d, x%d, %d" % (n, d.rd, d.rs1, d.imm & 0x1F)
    if n in LOAD_NAME.values():
        return "%s x%d, %d(x%d)" % (n, d.rd, d.imm, d.rs1)
    if n in STORE_NAME.values():
        return "%s x%d, %d(x%d)" % (n, d.rs2, d.imm, d.rs1)
    if n in BRANCH_NAME.values():
        return "%s x%d, x%d, %+d" % (n, d.rs1, d.rs2, d.imm)
    if n == "lui":
        return "lui x%d, 0x%05x" % (d.rd, (d.imm >> 12) & 0xFFFFF)
    if n == "auipc":
        return "auipc x%d, 0x%05x" % (d.rd, (d.imm >> 12) & 0xFFFFF)
    if n == "jal":
        return "jal x%d, %+d" % (d.rd, d.imm)
    if n == "jalr":
        return "jalr x%d, %d(x%d)" % (d.rd, d.imm, d.rs1)
    return n

"""精简 RV32I 汇编器：把本项目用到的指令子集汇编成 32 位机器码。

支持标签、十六进制/十进制立即数、注释，以及 li/mv/nop/j/call/ret 等伪指令。
它不追求通用，只求把"编译器输出的汇编"变成能装进第 7 章模拟器的镜像。
"""

import re

from encode import enc_r, enc_i, enc_s, enc_b, enc_u, enc_j

REG = {name: num for num, name in enumerate(
    ["zero", "ra", "sp", "gp", "tp", "t0", "t1", "t2", "s0", "s1",
     "a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7",
     "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9",
     "t3", "t4", "t5", "t6"])}
REG.update({"x%d" % i: i for i in range(32)})

R_FUNCT = {"add": (0x00, 0x0), "sub": (0x20, 0x0),
           "sll": (0x00, 0x1), "slt": (0x00, 0x2), "sltu": (0x00, 0x3),
           "xor": (0x00, 0x4), "srl": (0x00, 0x5), "sra": (0x20, 0x5),
           "or": (0x00, 0x6), "and": (0x00, 0x7)}
I_FUNCT = {"addi": 0x0, "slti": 0x2, "sltiu": 0x3,
           "xori": 0x4, "ori": 0x6, "andi": 0x7}
SHIFT_FUNCT = {"slli": (0x00, 0x1), "srli": (0x00, 0x5), "srai": (0x20, 0x5)}
LOAD_FUNCT = {"lb": 0x0, "lh": 0x1, "lw": 0x2, "lbu": 0x4, "lhu": 0x5}
STORE_FUNCT = {"sb": 0x0, "sh": 0x1, "sw": 0x2}
BRANCH_FUNCT = {"beq": 0x0, "bne": 0x1, "blt": 0x4,
                "bge": 0x5, "bltu": 0x6, "bgeu": 0x7}

MEM_RE = re.compile(r"^(-?(?:0x[0-9a-fA-F]+|\d+))?\((\w+)\)$")


def number(text):
    """把 0x10、-4、42 这样的文本变成整数。"""
    text = text.strip()
    neg = text.startswith("-")
    if neg:
        text = text[1:]
    value = int(text, 16) if text.lower().startswith("0x") else int(text, 10)
    return -value if neg else value


def reg(text):
    name = text.strip().lower()
    if name not in REG:
        raise ValueError("unknown register: %s" % text)
    return REG[name]


def clean(source):
    """去掉注释和空行，保留 (行号, 语句)。"""
    out = []
    for lineno, raw in enumerate(source.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if line:
            out.append((lineno, line))
    return out


def expand(line):
    """把伪指令展开成一条或两条真实指令，返回助记符列表。"""
    parts = line.replace(",", " ").split()
    op = parts[0].lower()
    args = parts[1:]

    if op == "nop":
        return [("addi", ["zero", "zero", "0"])]
    if op == "mv":
        return [("addi", [args[0], args[1], "0"])]
    if op == "li":
        imm = number(args[1])
        if -2048 <= imm <= 2047:
            return [("addi", [args[0], "zero", str(imm)])]
        return [("lui", [args[0], str((imm + 0x800) >> 12)]),
                ("addi", [args[0], args[0], str(imm & 0xFFF)])]
    if op == "j":
        return [("jal", ["zero", args[0]])]
    if op == "call":
        return [("jal", ["ra", args[0]])]
    if op == "ret":
        return [("jalr", ["zero", "ra", "0"])]
    if op == "ble":
        return [("bge", [args[1], args[0], args[2]])]
    if op == "bgt":
        return [("blt", [args[1], args[0], args[2]])]
    return [(op, args)]


def operand_value(text, labels, constants, pc):
    """解析立即数：可能是数字、常量名，或相对 pc 的标签。"""
    text = text.strip()
    try:
        return number(text)
    except ValueError:
        pass
    if text in constants:
        return constants[text]
    if text in labels:
        return labels[text] - pc
    raise ValueError("unknown immediate: %s" % text)


def encode_one(op, args, pc, labels, constants):
    """把一条真实指令编成一个 32 位字。"""
    if op in ("ecall", "ebreak", "mret"):
        return {"ecall": 0x00000073, "ebreak": 0x00100073,
                "mret": 0x30200073}[op]
    if op in R_FUNCT:
        f7, f3 = R_FUNCT[op]
        return enc_r(f7, reg(args[2]), reg(args[1]), f3, reg(args[0]), 0x33)
    if op in I_FUNCT:
        return enc_i(operand_value(args[2], labels, constants, pc),
                     reg(args[1]), I_FUNCT[op], reg(args[0]), 0x13)
    if op in SHIFT_FUNCT:
        f7, f3 = SHIFT_FUNCT[op]
        imm = (f7 << 5) | number(args[2])
        return enc_i(imm, reg(args[1]), f3, reg(args[0]), 0x13)
    if op in LOAD_FUNCT:
        m = MEM_RE.match(args[1])
        if not m:
            raise ValueError("bad load operand: %s" % args[1])
        imm = number(m.group(1)) if m.group(1) else 0
        return enc_i(imm, reg(m.group(2)), LOAD_FUNCT[op],
                     reg(args[0]), 0x03)
    if op in STORE_FUNCT:
        m = MEM_RE.match(args[1])
        if not m:
            raise ValueError("bad store operand: %s" % args[1])
        imm = number(m.group(1)) if m.group(1) else 0
        return enc_s(imm, reg(args[0]), reg(m.group(2)),
                     STORE_FUNCT[op], 0x23)
    if op in BRANCH_FUNCT:
        off = operand_value(args[2], labels, constants, pc)
        return enc_b(off, reg(args[1]), reg(args[0]),
                     BRANCH_FUNCT[op], 0x63)
    if op == "jal":
        off = operand_value(args[1], labels, constants, pc)
        return enc_j(off, reg(args[0]), 0x6F)
    if op == "jalr":
        if len(args) == 2:
            return enc_i(0, reg(args[0]), 0, reg(args[1]), 0x67)
        off = operand_value(args[2], labels, constants, pc)
        return enc_i(off, reg(args[1]), 0, reg(args[0]), 0x67)
    if op == "lui":
        return enc_u(number(args[1]) << 12, reg(args[0]), 0x37)
    if op == "auipc":
        return enc_u(number(args[1]) << 12, reg(args[0]), 0x17)
    if op == "fence":
        return 0x0FF0000F
    raise ValueError("unsupported instruction: %s" % op)


def assemble(source):
    """两遍汇编，返回 (words, labels)。labels 的值是相对偏移（字节）。"""
    lines = clean(source)
    labels, constants = {}, {}
    pc = 0

    # 第一遍：收集标签与常量，算出每条指令的地址
    for _, line in lines:
        while ":" in line:
            name, line = line.split(":", 1)
            labels[name.strip()] = pc
            line = line.strip()
            if not line:
                break
        if not line:
            continue
        op = line.split()[0].lower()
        if op == ".equ":
            parts = line.replace(",", " ").split()
            constants[parts[1]] = number(parts[2])
            continue
        if op == ".word":
            pc += 4
            continue
        pc += 4 * len(expand(line))

    # 第二遍：生成机器码
    words = []
    pc = 0
    for lineno, line in lines:
        while ":" in line:
            _, line = line.split(":", 1)
            line = line.strip()
            if not line:
                break
        if not line:
            continue
        op = line.split()[0].lower()
        if op == ".equ":
            continue
        if op == ".word":
            words.append(number(line.split()[1]) & 0xFFFFFFFF)
            pc += 4
            continue
        for real_op, args in expand(line):
            words.append(encode_one(real_op, args, pc, labels, constants)
                         & 0xFFFFFFFF)
            pc += 4
    return words, labels

"""指令执行：按译码结果改变 CPU 状态，必要时通过总线访问内存或外设。"""

from decode import sext

MASK = 0xFFFFFFFF


def u32(value):
    return value & MASK


def s32(value):
    return sext(value, 32)


def ex_lui(cpu, d, bus, pc):
    cpu.set_reg(d.rd, d.imm)
    return u32(pc + 4), True


def ex_auipc(cpu, d, bus, pc):
    cpu.set_reg(d.rd, u32(pc + d.imm))
    return u32(pc + 4), True


R_OPS = {
    "add": lambda a, b: u32(a + b),
    "sub": lambda a, b: u32(a - b),
    "sll": lambda a, b: u32(a << (b & 0x1F)),
    "slt": lambda a, b: 1 if s32(a) < s32(b) else 0,
    "sltu": lambda a, b: 1 if u32(a) < u32(b) else 0,
    "xor": lambda a, b: a ^ b,
    "srl": lambda a, b: u32(a) >> (b & 0x1F),
    "sra": lambda a, b: u32(s32(a) >> (b & 0x1F)),
    "or": lambda a, b: a | b,
    "and": lambda a, b: a & b,
}

I_OPS = {
    "addi": lambda a, imm: u32(a + imm),
    "slti": lambda a, imm: 1 if s32(a) < imm else 0,
    "sltiu": lambda a, imm: 1 if u32(a) < u32(imm) else 0,
    "xori": lambda a, imm: a ^ u32(imm),
    "ori": lambda a, imm: a | u32(imm),
    "andi": lambda a, imm: a & u32(imm),
    "srli": lambda a, imm: u32(a) >> (imm & 0x1F),
    "srai": lambda a, imm: u32(s32(a) >> (imm & 0x1F)),
}


def ex_op(cpu, d, bus, pc):
    a = cpu.get_reg(d.rs1)
    b = cpu.get_reg(d.rs2)
    cpu.set_reg(d.rd, R_OPS[d.name](a, b))
    return u32(pc + 4), True


def ex_op_imm(cpu, d, bus, pc):
    a = cpu.get_reg(d.rs1)
    if d.name in ("slli", "srli", "srai"):
        shamt = d.imm & 0x1F
        if d.name == "slli":
            result = u32(a << shamt)
        elif d.name == "srli":
            result = u32(a) >> shamt
        else:
            result = u32(s32(a) >> shamt)
    else:
        result = I_OPS[d.name](a, d.imm)
    cpu.set_reg(d.rd, result)
    return u32(pc + 4), True


def ex_load(cpu, d, bus, pc):
    addr = u32(cpu.get_reg(d.rs1) + d.imm)
    if d.name == "lb":
        value = sext(bus.load8(addr), 8)
    elif d.name == "lbu":
        value = bus.load8(addr)
    elif d.name == "lh":
        value = sext(bus.load16(addr), 16)
    elif d.name == "lhu":
        value = bus.load16(addr)
    else:
        value = bus.load32(addr)
    cpu.set_reg(d.rd, value)
    return u32(pc + 4), True


def ex_store(cpu, d, bus, pc):
    addr = u32(cpu.get_reg(d.rs1) + d.imm)
    value = cpu.get_reg(d.rs2)
    if d.name == "sb":
        bus.store8(addr, value)
    elif d.name == "sh":
        bus.store16(addr, value)
    else:
        bus.store32(addr, value)
    return u32(pc + 4), True


def ex_branch(cpu, d, bus, pc):
    a = cpu.get_reg(d.rs1)
    b = cpu.get_reg(d.rs2)
    name = d.name
    if name == "beq":
        taken = a == b
    elif name == "bne":
        taken = a != b
    elif name == "blt":
        taken = s32(a) < s32(b)
    elif name == "bge":
        taken = s32(a) >= s32(b)
    elif name == "bltu":
        taken = u32(a) < u32(b)
    else:
        taken = u32(a) >= u32(b)
    return (u32(pc + d.imm) if taken else u32(pc + 4)), True


def ex_jal(cpu, d, bus, pc):
    cpu.set_reg(d.rd, u32(pc + 4))
    return u32(pc + d.imm), True


def ex_jalr(cpu, d, bus, pc):
    target = u32((cpu.get_reg(d.rs1) + d.imm) & ~1)
    cpu.set_reg(d.rd, u32(pc + 4))
    return target, True


def ex_fence(cpu, d, bus, pc):
    return u32(pc + 4), True


def ex_system(cpu, d, bus, pc):
    return u32(pc + 4), False


def ex_illegal(cpu, d, bus, pc):
    raise ValueError("illegal instruction at pc=0x%08x" % pc)


EXEC = {
    "lui": ex_lui, "auipc": ex_auipc,
    "op": ex_op, "op-imm": ex_op_imm,
    "load": ex_load, "store": ex_store,
    "branch": ex_branch, "jal": ex_jal, "jalr": ex_jalr,
    "fence": ex_fence, "system": ex_system, "illegal": ex_illegal,
}


def execute(cpu, d, bus):
    """执行一条已译码指令，返回 running；pc 的推进集中在这里。"""
    pc = cpu.get_pc()
    next_pc, running = EXEC[d.kind](cpu, d, bus, pc)
    cpu.set_pc(next_pc)
    return running

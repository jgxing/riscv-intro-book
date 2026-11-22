"""第 7 章自测：执行、访存、分支跳转、总线与 UART。"""

import tempfile
from pathlib import Path

from bus import Bus
from cpu import CPU
from decode import decode
from encode import enc_b, enc_i, enc_j, enc_r, enc_s, enc_u
from execute import execute, s32, u32
from memory import BASE, Memory
from programs import (PRINT_DATA, PRINT_DATA_ADDR, PRINT_PROGRAM,
                      SUM_DATA, SUM_DATA_ADDR, SUM_PROGRAM)
from run import run
from uart import UART_BASE, LSR_DR, LSR_THRE, UART

passed = 0
failed = 0


def check(got, want, msg):
    global passed, failed
    if got == want:
        passed += 1
    else:
        failed += 1
        print("FAIL %-42s got %r want %r" % (msg, got, want))


def step(word, bus=None, pc=BASE):
    bus = bus if bus is not None else Bus()
    cpu = CPU(bus, entry=pc)
    running = execute(cpu, decode(word), bus)
    return cpu, bus, running


# 32 位回绕与有符号转换
check(u32(0x100000000), 0, "u32 wraps to 32 bits")
check(u32(-1), 0xFFFFFFFF, "u32 of negative")
check(s32(0xFFFFFFFF), -1, "s32 of 0xFFFFFFFF")
check(s32(0x7FFFFFFF), 0x7FFFFFFF, "s32 of positive max")

# R 型运算
# 元组顺序：f7, rs2, rs1, f3, rd, opcode, rs1 的值, rs2 的值, 期望结果, 名称
r_cases = [
    (0x00, 2, 1, 0, 3, 0x33, 0x0000000F, 0x00000005, 0x00000014, "add"),
    (0x20, 2, 1, 0, 3, 0x33, 0x0000000F, 0x00000005, 0x0000000A, "sub"),
    (0x00, 2, 1, 1, 3, 0x33, 0x00000001, 0x00000004, 0x00000010, "sll"),
    (0x00, 2, 1, 2, 3, 0x33, 0xFFFFFFFF, 0x00000001, 1, "slt signed"),
    (0x00, 2, 1, 3, 3, 0x33, 0xFFFFFFFF, 0x00000001, 0, "sltu unsigned"),
    (0x00, 2, 1, 4, 3, 0x33, 0xF0F0F0F0, 0x0F0F0F0F, 0xFFFFFFFF, "xor"),
    (0x00, 2, 1, 5, 3, 0x33, 0x80000000, 0x00000004, 0x08000000, "srl"),
    (0x20, 2, 1, 5, 3, 0x33, 0x80000000, 0x00000004, 0xF8000000, "sra"),
    (0x00, 2, 1, 6, 3, 0x33, 0xF0F0F0F0, 0x0F0F0F0F, 0xFFFFFFFF, "or"),
    (0x00, 2, 1, 7, 3, 0x33, 0xF0F0F0F0, 0x0F0F0F0F, 0, "and"),
]
for f7, rs2, rs1, f3, rd, op, a, b, want, name in r_cases:
    bus = Bus()
    cpu = CPU(bus)
    cpu.set_reg(rs1, a)
    cpu.set_reg(rs2, b)
    execute(cpu, decode(enc_r(f7, rs2, rs1, f3, rd, op)), bus)
    check(cpu.get_reg(rd), want, "R " + name)

# I 型运算
# 元组顺序：imm, rs1, f3, opcode, rd, rs1 的值, 期望结果, 名称
i_cases = [
    (5, 1, 0, 0x13, 2, 0x0000000A, 0x0000000F, "addi"),
    (-1, 1, 0, 0x13, 2, 5, 4, "addi negative imm"),
    (1, 1, 2, 0x13, 2, 0xFFFFFFFF, 1, "slti"),
    (1, 1, 3, 0x13, 2, 0xFFFFFFFF, 0, "sltiu"),
    (0x0FF, 1, 4, 0x13, 2, 0xFFFFFF00, 0xFFFFFFFF, "xori"),
    (0x0FF, 1, 6, 0x13, 2, 0xFFFFFF00, 0xFFFFFFFF, "ori"),
    (0x0FF, 1, 7, 0x13, 2, 0xFFFFFF00, 0, "andi"),
    (4, 1, 1, 0x13, 2, 1, 16, "slli"),
    (4, 1, 5, 0x13, 2, 0x80000000, 0x08000000, "srli"),
    (0x400 | 4, 1, 5, 0x13, 2, 0x80000000, 0xF8000000, "srai"),
]
for imm, rs1, f3, op, rd, a, want, name in i_cases:
    bus = Bus()
    cpu = CPU(bus)
    cpu.set_reg(rs1, a)
    execute(cpu, decode(enc_i(imm, rs1, f3, rd, op)), bus)
    check(cpu.get_reg(rd), want, "I " + name)

# 立即数装填
cpu, bus, running = step(enc_u(0x12345000, 1, 0x37))
check(cpu.get_reg(1), 0x12345000, "lui")
check(running, True, "lui keeps running")
cpu, bus, running = step(enc_u(0x1000, 1, 0x17), pc=0x80000100)
check(cpu.get_reg(1), 0x80001100, "auipc adds pc")

# 访存：store 再 load
for name, sw, lw, value, want in [
    ("byte", enc_s(0, 2, 1, 0, 0x23), enc_i(0, 1, 0, 3, 0x03), 0x12345678, 0x78),
    ("halfword", enc_s(0, 2, 1, 1, 0x23), enc_i(0, 1, 2, 3, 0x03), 0x12345678, 0x5678),
    ("word", enc_s(0, 2, 1, 2, 0x23), enc_i(0, 1, 2, 3, 0x03), 0x12345678, 0x12345678),
]:
    bus = Bus()
    cpu = CPU(bus)
    cpu.set_reg(1, BASE + 0x40)
    cpu.set_reg(2, value)
    execute(cpu, decode(sw), bus)
    execute(cpu, decode(lw), bus)
    check(cpu.get_reg(3), want, "store/load " + name)

# 有符号与无符号 load 的区别
for name, lw, want in [
    ("lb", enc_i(0, 1, 0, 3, 0x03), 0xFFFFFF80),
    ("lbu", enc_i(0, 1, 4, 3, 0x03), 0x80),
    ("lh", enc_i(0, 1, 1, 3, 0x03), 0xFFFF8000),
    ("lhu", enc_i(0, 1, 5, 3, 0x03), 0x8000),
]:
    bus = Bus()
    if name in ("lb", "lbu"):
        bus.store8(BASE + 0x50, 0x80)
    else:
        bus.store16(BASE + 0x50, 0x8000)
    cpu = CPU(bus)
    cpu.set_reg(1, BASE + 0x50)
    execute(cpu, decode(lw), bus)
    check(cpu.get_reg(3), want, name + " sign extension")

# 分支：taken 与 not taken
br_cases = [
    (0, 5, 5, -8, BASE - 8, "beq taken"),
    (0, 5, 6, -8, BASE + 4, "beq not taken"),
    (1, 5, 6, -8, BASE - 8, "bne taken"),
    (4, 0xFFFFFFFF, 1, 8, BASE + 8, "blt signed taken"),
    (5, 0xFFFFFFFF, 1, 8, BASE + 4, "bge signed not taken"),
    (6, 0xFFFFFFFF, 1, 8, BASE + 4, "bltu unsigned not taken"),
    (7, 0xFFFFFFFF, 1, 8, BASE + 8, "bgeu unsigned taken"),
]
for f3, a, b, imm, want_pc, name in br_cases:
    bus = Bus()
    cpu = CPU(bus)
    cpu.set_reg(1, a)
    cpu.set_reg(2, b)
    execute(cpu, decode(enc_b(imm, 2, 1, f3, 0x63)), bus)
    check(cpu.get_pc(), want_pc, name)

# 跳转
bus = Bus()
cpu = CPU(bus)
cpu.set_reg(2, 0x80000010)
execute(cpu, decode(enc_j(1024, 1, 0x6F)), bus)
check(cpu.get_reg(1), BASE + 4, "jal link")
check(cpu.get_pc(), BASE + 1024, "jal target")
execute(cpu, decode(enc_i(1, 2, 0, 1, 0x67)), bus)
check(cpu.get_pc(), 0x80000010, "jalr clears low bit")
check(cpu.get_reg(1), BASE + 1028, "jalr link")

# ecall 停机
cpu, bus, running = step(enc_i(0, 0, 0, 0, 0x73))
check(running, False, "ecall stops simulation")

# 非法指令
try:
    step(0x00000000)
    check(False, True, "illegal instruction must raise")
except ValueError:
    check(True, True, "illegal instruction raises ValueError")

# 总线：UART 地址分流与串口读写
bus = Bus()
bus.store8(UART_BASE, ord("A"))
check(bus.uart.output(), "A", "store to UART THR")
bus.uart.feed("B")
check(bus.load8(UART_BASE + 5) & LSR_DR, LSR_DR, "UART LSR reports data ready")
check(bus.load8(UART_BASE + 5) & LSR_THRE, LSR_THRE, "UART LSR reports THRE")
check(bus.load8(UART_BASE), ord("B"), "load from UART RBR")
check(bus.load8(UART_BASE + 5) & LSR_DR, 0, "LSR clears DR after read")

# 总线：普通内存仍按小端工作
bus = Bus()
bus.store32(BASE + 0x80, 0xDEADBEEF)
check(bus.load8(BASE + 0x80), 0xEF, "bus keeps little endian")
check(bus.load16(BASE + 0x82), 0xDEAD, "bus load16")

# 完整程序：数组求和
cpu, bus, steps = run(SUM_PROGRAM, [(SUM_DATA_ADDR, SUM_DATA)], trace=False)
check(cpu.get_reg(3), 150, "array sum result")
check(steps, 32, "array sum step count")
check(bytes(bus.uart.tx_log), bytes([150]), "array sum written to UART")

# 完整程序：串口打印
cpu, bus, steps = run(PRINT_PROGRAM, [(PRINT_DATA_ADDR, PRINT_DATA)], trace=False)
check(bus.uart.output(), "Hi, RV32I!\n", "print program UART output")

print("passed %d, failed %d" % (passed, failed))
if failed:
    raise SystemExit(1)
print("ALL TESTS PASSED")

# 生成第 11 章异常与中断实验的指令存储器镜像
# 基地址 0x00400000，异常入口 0x00400040（偏移 0x40）

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


def b_type(imm, rs2, rs1, funct3, opcode):
    imm &= 0x1fff
    b12 = (imm >> 12) & 1
    b11 = (imm >> 11) & 1
    b10_5 = (imm >> 5) & 0x3f
    b4_1 = (imm >> 1) & 0xf
    return (b12 << 31) | (b10_5 << 25) | ((rs2 & 0x1f) << 20) | \
           ((rs1 & 0x1f) << 15) | ((funct3 & 7) << 12) | \
           (b4_1 << 8) | (b11 << 7) | opcode


def j_type(imm, rd, opcode):
    imm &= 0x1fffff
    b20 = (imm >> 20) & 1
    b19_12 = (imm >> 12) & 0xff
    b11 = (imm >> 11) & 1
    b10_1 = (imm >> 1) & 0x3ff
    return (b20 << 31) | (b10_1 << 21) | (b11 << 20) | \
           (b19_12 << 12) | ((rd & 0x1f) << 7) | opcode


NOP = 0x00000013
ECALL = 0x00000073
EBREAK = 0x00100073
MRET = 0x30200073
ILLEGAL = 0xffffffff

prog = {}

# 主程序：先设置异常入口，再依次触发四种陷入
prog[0x00] = u_type(0x00400, 7, 0x37)               # lui  x7, 0x400       -> 0x00400000
prog[0x04] = i_type(0x040, 7, 0, 7, 0x13)           # addi x7, x7, 0x40    -> 0x00400040
prog[0x08] = i_type(0x305, 7, 0b001, 0, 0x73)       # csrrw x0, mtvec, x7
prog[0x0c] = i_type(10, 0, 0, 1, 0x13)              # addi x1, x0, 10
prog[0x10] = ECALL                                  # trap 1: mcause=8,  mepc=0x00400010
prog[0x14] = i_type(5, 1, 0, 2, 0x13)               # addi x2, x1, 5       -> x2=15
prog[0x18] = ILLEGAL                                # trap 2: mcause=2,  mepc=0x00400018
prog[0x1c] = i_type(33, 0, 0, 3, 0x13)              # addi x3, x0, 33
prog[0x20] = EBREAK                                 # trap 3: mcause=3,  mepc=0x00400020
prog[0x24] = u_type(0x001, 4, 0x37)                 # lui  x4, 1           -> x4=0x1000
prog[0x28] = i_type(1, 4, 0b101, 4, 0x13)           # srli x4, x4, 1       -> x4=0x800
prog[0x2c] = i_type(0x304, 4, 0b010, 0, 0x73)       # csrrs x0, mie, x4    -> mie[11]=1
prog[0x30] = i_type(0x300, 8, 0b110, 0, 0x73)       # csrrsi x0, mstatus, 8 -> MIE=1
prog[0x34] = i_type(55, 0, 0, 5, 0x13)              # addi x5, x0, 55
prog[0x38] = i_type(66, 0, 0, 6, 0x13)              # addi x6, x0, 66
prog[0x3c] = j_type(0, 0, 0x6f)                     # j 0x3c               停机自环

# 异常处理入口（直接模式）
prog[0x40] = i_type(0x342, 0, 0b010, 10, 0x73)      # csrrs x10, mcause, x0
prog[0x44] = i_type(0x341, 0, 0b010, 11, 0x73)      # csrrs x11, mepc, x0
prog[0x48] = i_type(0x343, 0, 0b010, 12, 0x73)      # csrrs x12, mtval, x0
prog[0x4c] = i_type(8, 0, 0, 13, 0x13)              # addi x13, x0, 8
prog[0x50] = b_type(0x70 - 0x50, 13, 10, 0, 0x63)   # beq x10, x13, adjust
prog[0x54] = i_type(2, 0, 0, 13, 0x13)              # addi x13, x0, 2
prog[0x58] = b_type(0x70 - 0x58, 13, 10, 0, 0x63)   # beq x10, x13, adjust
prog[0x5c] = i_type(3, 0, 0, 13, 0x13)              # addi x13, x0, 3
prog[0x60] = b_type(0x70 - 0x60, 13, 10, 0, 0x63)   # beq x10, x13, adjust
prog[0x64] = j_type(0x7c - 0x64, 0, 0x6f)           # j done
prog[0x70] = i_type(4, 11, 0, 14, 0x13)             # addi x14, x11, 4
prog[0x74] = i_type(0x341, 14, 0b001, 0, 0x73)      # csrrw x0, mepc, x14
prog[0x7c] = MRET                                   # mret

words = [prog.get(i * 4, NOP) for i in range(DEPTH)]
out = "D:/aiprojects/workbuddy/riscv入门教程/code/verilog/11_trap/code.hex"
with open(out, "w", encoding="utf-8") as f:
    for w in words:
        f.write("%08x\n" % w)

for off in sorted(prog):
    print("0x%02x: %08x" % (off, prog[off]))
print("wrote", out, len(words), "words")

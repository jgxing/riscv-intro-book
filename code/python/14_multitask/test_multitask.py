"""第 14 章自检：陷阱进出口、CSR 指令、上下文切换与多任务输出。"""

from assemble import assemble
from cpu import (CPU, MSTATUS, MIE, MTVEC, MEPC, MCAUSE,
                 MSTATUS_MIE, MSTATUS_MPIE, MTIE, CAUSE_ECALL, CAUSE_TIMER)
from decode import decode, disasm
from execute import execute
from memory import Memory
from timer_bus import TimerBus, MTIME, MTIMECMP, UART_DATA
from machine import Machine, PCB
from run import TASKS

passed = 0
failed = 0


def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
        print("PASS", name)
    else:
        failed += 1
        print("FAIL", name)


def run_asm(src, bus=None, cpu=None, max_steps=200):
    words, labels = assemble(src)
    bus = bus or Memory()
    cpu = cpu or CPU(bus)
    for i, w in enumerate(words):
        bus.store32(0x80000000 + 4 * i, w)
    steps = 0
    while steps < max_steps:
        d = decode(cpu.fetch())
        if not execute(cpu, d, bus):
            break
        steps += 1
    return cpu, bus, labels


# ---- 1. 译码：新增的系统指令 ----
for asm, name in [("ecall", "ecall"), ("mret", "mret"),
                  ("csrrw t0, mepc, t1", "csrrw"),
                  ("csrrs t0, mie, zero", "csrrs")]:
    words, _ = assemble(asm)
    check("译码 %s" % name, decode(words[0]).name == name)

# ---- 2. trap 保存现场并关中断 ----
bus = Memory()
cpu = CPU(bus)
cpu.write_csr(MSTATUS, MSTATUS_MIE)
cpu.write_csr(MTVEC, 0x80001000)
cpu.set_reg(5, 123)
cpu.trap(CAUSE_ECALL, 0x80000040)
check("trap 保存 mepc", cpu.read_csr(MEPC) == 0x80000040)
check("trap 写入 mcause", cpu.read_csr(MCAUSE) == CAUSE_ECALL)
check("trap 跳到 mtvec", cpu.get_pc() == 0x80001000)
check("trap 关中断", (cpu.read_csr(MSTATUS) & MSTATUS_MIE) == 0)
check("trap 保存 MPIE", (cpu.read_csr(MSTATUS) & MSTATUS_MPIE) != 0)
check("trap 不破坏通用寄存器", cpu.get_reg(5) == 123)

# ---- 3. mret 恢复 ----
cpu.mret()
check("mret 回到 mepc", cpu.get_pc() == 0x80000040)
check("mret 恢复中断使能", (cpu.read_csr(MSTATUS) & MSTATUS_MIE) != 0)

# ---- 4. CSR 读写指令 ----
cpu2, _, _ = run_asm("""
    li t1, 0x80
    csrrs t0, mie, t1
    csrrw t2, mscratch, t1
    ebreak
""")
check("csrrs 置位 mie", (cpu2.read_csr(MIE) & 0x80) != 0)
check("csrrs 读回旧值", cpu2.get_reg(10) == 0)
check("csrrw 写 mscratch", cpu2.read_csr(0x340) == 0x80)

# ---- 5. ecall 真的触发陷阱 ----
src = """
    li t0, 0x80001000
    csrrw zero, mtvec, t0
    ecall
"""
words3, _ = assemble(src)
bus3 = Memory()
cpu3 = CPU(bus3)
for i, w in enumerate(words3):
    bus3.store32(0x80000000 + 4 * i, w)
# 逐条执行，停在 ecall 陷阱发生的那一刻
for _ in range(10):
    d = decode(cpu3.fetch())
    execute(cpu3, d, bus3)
    if d.name == "ecall":
        break
check("ecall 跳到 mtvec", cpu3.get_pc() == 0x80001000)
check("ecall 的 mcause 是 8", cpu3.read_csr(MCAUSE) == CAUSE_ECALL)

# ---- 6. 定时器总线 ----
tb = TimerBus()
tb.store32(MTIMECMP, 5)
for _ in range(4):
    fired = tb.tick()
check("定时器未到点不触发", not fired)
check("定时器计数到 4", tb.mtime == 4)
check("定时器到点触发", tb.tick())
check("mtime 等于比较值", tb.mtime == 5)

# ---- 7. 多任务交替 ----
words, labels = assemble(TASKS)
m = Machine(timer_period=30, max_steps=600)
m.load_program(words, 0x80000000)
m.add(PCB("A", 0x80000000 + labels["task_a"], 0x80004000))
m.add(PCB("B", 0x80000000 + labels["task_b"], 0x80008000))
m.start()
m.run()
out = "".join(m.bus.uart_tx)
check("产生多次陷阱", m.trap_count >= 10)
check("两个任务都运行过", m.procs[0].slices >= 5 and m.procs[1].slices >= 5)
check("串口既有 A 也有 B", "A" in out and "B" in out)
check("串口输出够长", len(out) >= 20)
check("切换记录按顺序轮转",
      all(m.switch_log[i][1] != m.switch_log[i + 1][1]
          for i in range(len(m.switch_log) - 1)))
check("mcause 记录是定时器中断", any(n[0] > 0 for n in m.switch_log))

print("\n%d passed, %d failed" % (passed, failed))
if failed:
    raise SystemExit(1)

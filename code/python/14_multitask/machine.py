"""最小的抢占式多任务内核。

硬件部分由 CPU 的 trap/mret 模拟；这里的 Machine 相当于中断服务程序加调度器：
定时器到点抢占当前任务，把它的寄存器和 pc 存进 PCB，再换上另一个任务接着跑。
"""

from cpu import (CPU, MIE, MSTATUS, MSTATUS_MIE, MTVEC, MEPC,
                 MCAUSE, MTIE, CAUSE_TIMER)
from decode import decode
from execute import execute
from timer_bus import TimerBus


class PCB:
    """进程控制块：保住一个任务被切走那一刻的全部寄存器和返回地址。"""

    def __init__(self, name, entry, stack_top):
        self.name = name
        self.regs = [0] * 32
        self.regs[2] = stack_top       # sp
        self.pc = entry                # 下次从哪里接着跑
        self.state = 1                 # 1=可运行
        self.slices = 0                # 被调度了多少次

    def save(self, cpu, mepc):
        self.regs = cpu.regs[:]
        self.pc = mepc                 # 恢复到那条被中断的指令

    def restore(self, cpu):
        cpu.regs = self.regs[:]
        cpu.set_pc(self.pc)
        self.slices += 1


class Machine:
    def __init__(self, timer_period=30, max_steps=2000):
        self.bus = TimerBus()
        self.cpu = CPU(self.bus)
        self.timer_period = timer_period
        self.max_steps = max_steps
        self.procs = []
        self.current = 0
        self.switch_log = []
        self.trap_count = 0
        # 打开定时器中断和全局中断；mtvec 只是占位，切换由本类接管
        self.cpu.write_csr(MIE, MTIE)
        self.cpu.write_csr(MSTATUS, MSTATUS_MIE)
        self.cpu.write_csr(MTVEC, 0xFFFFFF00)
        self.bus.mtimecmp = timer_period

    def add(self, proc):
        self.procs.append(proc)

    def load_program(self, words, base):
        for i, word in enumerate(words):
            self.bus.mem.store32(base + 4 * i, word)

    def schedule_next(self):
        """轮转法找下一个可运行任务。"""
        n = len(self.procs)
        for k in range(1, n + 1):
            idx = (self.current + k) % n
            if self.procs[idx].state == 1:
                return idx
        return self.current

    def on_timer(self):
        """定时器陷阱：保存现场、切换任务、把比较值推到下一次。"""
        cpu = self.cpu
        mepc = cpu.read_csr(MEPC)
        self.procs[self.current].save(cpu, mepc)
        self.current = self.schedule_next()
        nxt = self.procs[self.current]
        nxt.restore(cpu)
        cpu.write_csr(MEPC, nxt.pc)
        # ISR 结尾必须 mret：它把 MPIE 恢复到 MIE，否则中断再也进不来
        cpu.mret()
        self.bus.mtimecmp = (self.bus.mtime + self.timer_period) & 0xFFFFFFFF
        self.trap_count += 1
        self.switch_log.append((self.trap_count, nxt.name, nxt.pc))

    def start(self):
        """把第一个任务装进 CPU。"""
        self.procs[0].restore(self.cpu)
        self.cpu.write_csr(MEPC, self.procs[0].pc)

    def step(self):
        """执行一条指令；返回 False 表示停机。"""
        cpu = self.cpu
        word = cpu.fetch()
        d = decode(word)
        running = execute(cpu, d, self.bus)
        if not running:
            return False
        fired = self.bus.tick()
        mie = cpu.read_csr(MIE)
        status = cpu.read_csr(MSTATUS)
        pending = self.bus.timer_pending()
        if fired and pending and (mie & MTIE) and (status & MSTATUS_MIE):
            cpu.trap(CAUSE_TIMER, cpu.get_pc())
            self.on_timer()
        return True

    def run(self):
        steps = 0
        while steps < self.max_steps:
            if not self.step():
                break
            steps += 1
        return steps

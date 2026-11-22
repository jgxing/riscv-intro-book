"""CPU 状态：程序计数器、整数寄存器、M 模式 CSR，以及陷阱进出的硬件动作。"""

from memory import BASE

# 本章用到的 M 模式 CSR 地址
MSTATUS = 0x300
MIE = 0x304
MTVEC = 0x305
MSCRATCH = 0x340
MEPC = 0x341
MCAUSE = 0x342
MTVAL = 0x343
MIP = 0x344

# mstatus 里的位
MSTATUS_MIE = 1 << 3      # 全局中断使能
MSTATUS_MPIE = 1 << 7     # 陷进来之前的中断使能
MSTATUS_MPP = 3 << 11     # 陷进来之前的特权模式

# mie / mip 里的机器定时器位
MTIE = 1 << 7

# mcause 常用编码
CAUSE_ECALL = 8           # 来自 ecall 的环境调用异常
CAUSE_TIMER = 0x80000005  # 最高位为 1 表示中断，低位是定时器中断编号 5


class CPU:
    def __init__(self, mem, entry=BASE):
        self.mem = mem
        self.pc = entry
        self.regs = [0] * 32
        # 只实现本章需要的几个 CSR，其余读出来是 0
        self.csrs = {
            MSTATUS: 0, MIE: 0, MTVEC: 0, MSCRATCH: 0,
            MEPC: 0, MCAUSE: 0, MTVAL: 0, MIP: 0,
        }

    def get_pc(self):
        return self.pc

    def set_pc(self, addr):
        self.pc = addr & 0xFFFFFFFF

    def pc_inc4(self):
        self.set_pc(self.pc + 4)

    def get_reg(self, n):
        if n == 0:
            return 0
        return self.regs[n]

    def set_reg(self, n, value):
        if n != 0:
            self.regs[n] = value & 0xFFFFFFFF

    def fetch(self):
        return self.mem.load32(self.pc)

    # ---- CSR 读写 ----
    def read_csr(self, addr):
        return self.csrs.get(addr, 0)

    def write_csr(self, addr, value):
        if addr in self.csrs:
            self.csrs[addr] = value & 0xFFFFFFFF

    # ---- 陷阱进出：这部分模拟的是硬件动作 ----
    def trap(self, cause, epc):
        """进入陷阱：记下返回地址和原因，关中断，跳到 mtvec。"""
        self.csrs[MEPC] = epc & 0xFFFFFFFF
        self.csrs[MCAUSE] = cause & 0xFFFFFFFF
        status = self.csrs[MSTATUS]
        previous_ie = (status & MSTATUS_MIE) >> 3
        status = status & ~(MSTATUS_MIE | MSTATUS_MPIE | MSTATUS_MPP)
        status |= (previous_ie << 7) | (3 << 11)   # MPP=3 表示来自 M 模式
        self.csrs[MSTATUS] = status
        self.set_pc(self.csrs[MTVEC])

    def mret(self):
        """从陷阱返回：恢复中断使能，回到 mepc。"""
        status = self.csrs[MSTATUS]
        previous_ie = (status & MSTATUS_MPIE) >> 7
        status = (status & ~(MSTATUS_MIE | MSTATUS_MPIE)) | (previous_ie << 3)
        status |= MSTATUS_MPIE
        self.csrs[MSTATUS] = status
        self.set_pc(self.csrs[MEPC])

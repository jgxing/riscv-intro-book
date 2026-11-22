"""RV32I 模拟器的内存模型：字节寻址、小端存放，从 0x80000000 开始。"""

BASE = 0x80000000
DEFAULT_SIZE = 64 * 1024


class Memory:
    """一段连续的字节地址空间。"""

    def __init__(self, base=BASE, size=DEFAULT_SIZE):
        self.base = base
        self.mem = bytearray(size)

    def _check(self, addr, length):
        if not (self.base <= addr and addr + length <= self.base + len(self.mem)):
            raise ValueError("address 0x%08x out of range" % addr)

    def load8(self, addr):
        self._check(addr, 1)
        return self.mem[addr - self.base]

    def store8(self, addr, value):
        self._check(addr, 1)
        self.mem[addr - self.base] = value & 0xFF

    def load32(self, addr):
        self._check(addr, 4)
        off = addr - self.base
        return (self.mem[off]
                | (self.mem[off + 1] << 8)
                | (self.mem[off + 2] << 16)
                | (self.mem[off + 3] << 24))

    def store32(self, addr, value):
        self._check(addr, 4)
        off = addr - self.base
        v = value & 0xFFFFFFFF
        self.mem[off] = v & 0xFF
        self.mem[off + 1] = (v >> 8) & 0xFF
        self.mem[off + 2] = (v >> 16) & 0xFF
        self.mem[off + 3] = (v >> 24) & 0xFF

    def load_image(self, path, addr):
        with open(path, "rb") as f:
            data = f.read()
        self._check(addr, len(data))
        off = addr - self.base
        self.mem[off:off + len(data)] = data
        return len(data)

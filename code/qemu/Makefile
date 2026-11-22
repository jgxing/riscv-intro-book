# 需要预先安装 RISC-V GCC 交叉编译器与 qemu-system-riscv32。
# 在装有这两组工具的机器上执行 make run，串口应输出 AB。
# 退出 QEMU：先按 Ctrl+A，松开后再按 X。

CROSS = riscv64-unknown-elf-gcc
QEMU  = qemu-system-riscv32
CFLAGS = -march=rv32i -mabi=ilp32 -nostdlib -nostartfiles -Wl,-T,link.ld -g -O0

.PHONY: all run clean disasm

all: trap.elf

trap.elf: trap.S link.ld
	$(CROSS) $(CFLAGS) -o $@ trap.S

run: trap.elf
	$(QEMU) -M virt -bios none -kernel trap.elf -nographic -monitor none -serial mon:stdio

disasm: trap.elf
	riscv64-unknown-elf-objdump -d trap.elf

clean:
	rm -f trap.elf

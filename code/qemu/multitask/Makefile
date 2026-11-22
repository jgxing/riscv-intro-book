CROSS = riscv64-unknown-elf-
CC    = $(CROSS)gcc
OBJDUMP = $(CROSS)objdump

# -march=rv32i -mabi=ilp32：32 位基本整数指令集
# -nostdlib：裸机，不链接标准库
CFLAGS = -march=rv32i -mabi=ilp32 -nostdlib -O1 -g -T multitask.ld

all: multitask.elf

multitask.elf: main.c start.S platform.h multitask.ld
	$(CC) $(CFLAGS) -o $@ start.S main.c

# 反汇编，配合正文看第一条指令和陷阱向量
disasm: multitask.elf
	$(OBJDUMP) -d multitask.elf > multitask.dump
	@echo "已生成 multitask.dump"

run: multitask.elf
	qemu-system-riscv32 -machine virt -nographic -monitor none -serial stdio \
		-bios none -kernel multitask.elf

clean:
	rm -f multitask.elf multitask.dump

.PHONY: all disasm run clean

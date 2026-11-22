CROSS = riscv64-unknown-elf-
CC    = $(CROSS)gcc
OBJCOPY = $(CROSS)objcopy
OBJDUMP = $(CROSS)objdump
PYTHON ?= python

CFLAGS = -march=rv32i -mabi=ilp32 -nostdlib -O1 -g -T program.ld

all: program.elf program.dump code.hex

program.elf: start.S program.c program.ld
	$(CC) $(CFLAGS) -o $@ start.S program.c

program.dump: program.elf
	$(OBJDUMP) -d -s program.elf > $@

program.bin: program.elf
	$(OBJCOPY) -O binary -j .text program.elf $@

# 把二进制镜像转成 Icarus Verilog 能读的 code.hex（每行一个 32 位字）
code.hex: program.bin
	$(PYTHON) ../../../tools/bin_to_hex.py program.bin code.hex

# 用第 8 章的单周期核跑这个程序
sim: code.hex
	cd ../../verilog/08_single_cycle && \
		iverilog -g2012 -o sim.out alu.v pc.v control.v regfile.v imem.v dmem.v core.v tb_core.v && \
		vvp sim.out

clean:
	rm -f program.elf program.dump program.bin code.hex

.PHONY: all sim clean

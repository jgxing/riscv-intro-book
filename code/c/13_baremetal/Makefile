CROSS   = riscv32-unknown-elf-
CC      = $(CROSS)gcc
OBJDUMP = $(CROSS)objdump
OBJCOPY = $(CROSS)objcopy

CFLAGS = -march=rv32i -mabi=ilp32 -nostdlib -O1 -g -Wall -T link.ld

all: main.elf main.bin main.dis

main.elf: start.S main.c rv32i.h link.ld
	$(CC) $(CFLAGS) -o $@ start.S main.c

main.bin: main.elf
	$(OBJCOPY) -O binary $< $@

main.dis: main.elf
	$(OBJDUMP) -d -S $< > $@

clean:
	rm -f main.elf main.bin main.dis

.PHONY: all clean

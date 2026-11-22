CROSS = riscv64-unknown-elf-
CC    = $(CROSS)gcc

CFLAGS = -march=rv32i -mabi=ilp32 -nostdlib -O1 -T hello.ld

all: hello.elf

hello.elf: hello.c hello.ld
	$(CC) $(CFLAGS) -o $@ hello.c

run: hello.elf
	qemu-system-riscv32 -machine virt -nographic -monitor none -serial stdio -bios none -kernel hello.elf

clean:
	rm -f hello.elf

.PHONY: all run clean

/* QEMU virt 机器，M 模式裸机程序。代码放在 0x80000000 起。 */
OUTPUT_ARCH(riscv)
ENTRY(_start)

SECTIONS
{
    . = 0x80000000;

    .text : {
        *(.text.start)
        *(.text*)
    }

    .rodata : { *(.rodata*) }
    .data  : { *(.data*) }
    .bss   : {
        __bss_start = .;
        *(.bss*)
        __bss_end = .;
    }

    /* 栈顶：QEMU virt 有 128 MiB RAM，从 0x80000000 到 0x88000000 */
    __stack_top = 0x88000000;

    /DISCARD/ : { *(.comment*) *(.note*) }
}

/* 本书单周期 / 五级流水线核的地址布局 */
OUTPUT_ARCH(riscv)
ENTRY(_start)

SECTIONS
{
    . = 0x00400000;             /* 指令内存起点 */

    .text : {
        *(.text.start)
        *(.text*)
        *(.rodata*)             /* 字符串常量跟着指令一起进镜像 */
    }

    . = 0x10000000;             /* 数据内存起点 */
    .data : { *(.data*) }
    .bss  : {
        __bss_start = .;
        *(.bss*)
        __bss_end = .;
    }
}

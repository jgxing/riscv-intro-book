#include <stdint.h>

/* QEMU virt 机器的 16550 UART 数据寄存器 */
#define UART0 ((volatile uint32_t *)0x10000000u)

void main(void)
{
    const char *s = "Hello from RISC-V\n";
    while (*s) {
        *UART0 = (uint32_t)(unsigned char)*s;
        s++;
    }
    for (;;) {
    }
}

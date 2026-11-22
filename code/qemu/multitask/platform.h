#ifndef PLATFORM_H
#define PLATFORM_H

#include <stdint.h>

/* QEMU virt 的 16550 UART 数据寄存器 */
#define UART0 ((volatile uint32_t *)0x10000000u)

/* CLINT：机器定时器与软件中断 */
#define CLINT_MTIME     ((volatile uint64_t *)0x0200BFF8u)
#define CLINT_MTIMECMP  ((volatile uint64_t *)0x02004000u)

/* CSR 读写的内联汇编封装 */
#define read_csr(csr)                                   \
    ({ uint32_t v; asm volatile("csrr %0, " #csr : "=r"(v)); v; })
#define write_csr(csr, v)                               \
    asm volatile("csrw " #csr ", %0" :: "r"(v))
#define set_csr(csr, v)                                 \
    asm volatile("csrs " #csr ", %0" :: "r"(v))
#define clear_csr(csr, v)                               \
    asm volatile("csrc " #csr ", %0" :: "r"(v))

static inline void putchar(char c)
{
    *UART0 = (uint32_t)(unsigned char)c;
}

static inline void puts(const char *s)
{
    while (*s) {
        putchar(*s++);
    }
}

/* 忙等若干个循环，纯延时，给调度器制造切换机会 */
static inline void delay(volatile uint32_t n)
{
    while (n--) {
        asm volatile("nop");
    }
}

#endif

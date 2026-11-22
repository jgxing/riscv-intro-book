#ifndef RV32I_H
#define RV32I_H

#include <stdint.h>

/*
 * 本书第 12 章定义的外设地址。每个寄存器都用一个指针常量表示，
 * volatile 告诉编译器"这个地址的内容会自己变化，别优化掉读写"。
 */
#define MTIME_LO   (*(volatile uint32_t *)0xffff0000u)
#define LED        (*(volatile uint32_t *)0xffff0010u)
#define SWITCH     (*(volatile uint32_t *)0xffff0020u)
#define UART_DATA  (*(volatile uint32_t *)0xffff0030u)
#define UART_STAT  (*(volatile uint32_t *)0xffff0034u)

#define UART_DR    0x01u   /* 接收数据就绪 */
#define UART_THRE  0x20u   /* 发送保持寄存器空 */

/*
 * CSR 读写和 ecall 没有对应的 C 语句，只能用内联汇编。
 * "i"(csr) 要求把 CSR 编号当汇编立即数，"=r" 要求分配一个寄存器接结果。
 */
#define read_csr(csr)                                                       \
    ({ uint32_t value;                                                      \
       __asm__ __volatile__("csrr %0, %1" : "=r"(value) : "i"(csr));        \
       value; })

#define write_csr(csr, val)                                                 \
    __asm__ __volatile__("csrw %0, %1" :: "i"(csr), "r"(val))

static inline void ecall(void)
{
    __asm__ __volatile__("ecall");
}

#endif

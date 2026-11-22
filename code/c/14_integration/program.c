#include <stdint.h>

/* 本书单周期核的外设地址（见第 12 章） */
#define LED    ((volatile uint32_t *)0xffff0010u)
#define UART   ((volatile uint32_t *)0xffff0030u)

/* 求 1+2+...+n，结果写到 LED，并把十进制数字从串口打出来 */
static uint32_t sum_to(uint32_t n)
{
    uint32_t s = 0;
    for (uint32_t i = 1; i <= n; i++) {
        s += i;
    }
    return s;
}

void main(void)
{
    uint32_t s = sum_to(10);   /* 55 */
    *LED = s;

    const char *msg = "sum=55\n";
    while (*msg) {
        *UART = (uint32_t)(unsigned char)*msg++;
    }
    for (;;) {
    }
}

#include "rv32i.h"

/* 轮询状态位，直到发送保持寄存器变空 */
void uart_putc(char c)
{
    while ((UART_STAT & UART_THRE) == 0) {
        /* 等待 */
    }
    UART_DATA = (unsigned char)c;
}

/* 一个会被编译器翻译成循环和加法的小函数 */
int sum_to(int n)
{
    int s = 0;
    for (int i = 1; i <= n; ++i) {
        s += i;
    }
    return s;
}

int main(void)
{
    int s = sum_to(10);       /* 1+2+...+10 = 55 */
    LED = (uint32_t)s;        /* 低 8 位点亮，0x37 */
    uart_putc('H');
    uart_putc('i');
    while (1) {
        /* 停机 */
    }
    return 0;
}

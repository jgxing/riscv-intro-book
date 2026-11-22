# QEMU virt 机器上的机器模式异常处理示例
# 主程序两次执行 ecall，处理程序从 mcause 认出原因，
# 把 mepc 加 4 后返回，并通过串口输出一个字符。

    .option norelax
    .globl _start

    .equ UART0, 0x10000000

_start:
    la      sp, __stack_top
    la      t0, trap_handler
    csrw    mtvec, t0

    li      a0, 0x41                # 字符 A
    ecall
    li      a0, 0x42                # 字符 B
    ecall

1:
    j       1b                      # 停机自环，用 Ctrl+A 再按 X 退出 QEMU

trap_handler:
    csrr    t0, mcause              # 环境调用异常的原因是 8
    csrr    t1, mepc                # mepc 指向 ecall 自己
    addi    t1, t1, 4               # 返回到 ecall 的下一条
    csrw    mepc, t1

    li      t2, UART0
    sb      a0, 0(t2)               # 向 16550 发送寄存器写一个字节

    mret                            # 回到主程序

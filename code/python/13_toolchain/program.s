# 这段汇编等价于 code/c/13_baremetal/main.c 被交叉编译器生成的代码。
# 真机上由 GCC 产生，这里手写出来，好让读者看清每一步对应 C 的哪一句。
# 寄存器约定：s0=求和结果，t0=循环变量 i，a0=函数实参/返回值，
#             a1=外设基址 0xffff0000，t1=循环上界 10。

        lui     sp, 0x8000f             # 栈指针 = 0x8000f000，指向主存顶部
        addi    a0, zero, 10            # 调用 sum_to(10)
        jal     ra, sum_to
        add     s0, a0, zero            # s = 返回值 55

        lui     a1, 0xffff0             # a1 = 0xffff0000，外设基址
        sw      s0, 0x10(a1)            # LED = 55
        addi    t2, zero, 72            # 'H' = 0x48
        sw      t2, 0x30(a1)            # UART_DATA = 'H'
        addi    t2, zero, 105           # 'i' = 0x69
        sw      t2, 0x30(a1)            # UART_DATA = 'i'

stop:   jal     zero, stop              # 停机自环

# int sum_to(int n)  入口参数在 a0，返回值放 a0
sum_to:
        addi    sp, sp, -8              # 让出一个栈槽
        sw      ra, 4(sp)               # 保存返回地址
        sw      s0, 0(sp)               # 保存 s0
        addi    s0, zero, 0             # s = 0
        addi    t0, zero, 1             # i = 1
        addi    t1, zero, 10            # 上界 10
loop:   blt     t1, t0, done            # 若 i > 10 则退出
        add     s0, s0, t0              # s += i
        addi    t0, t0, 1               # i++
        jal     zero, loop
done:   add     a0, s0, zero            # 返回值 = s
        lw      s0, 0(sp)               # 恢复现场
        lw      ra, 4(sp)
        addi    sp, sp, 8
        jalr    zero, ra, 0             # 返回 main

    .section .text.start
    .globl  _start
_start:
    /* 清 .bss：从 __bss_start 到 __bss_end 逐字写零 */
    la      t0, __bss_start
    la      t1, __bss_end
1:
    bge     t0, t1, 2f
    sw      zero, 0(t0)
    addi    t0, t0, 4
    j       1b
2:
    /* 设栈指针，然后调用 C 的 main */
    la      sp, __stack_top
    call    main
3:
    /* main 若返回，停在这里 */
    j       3b

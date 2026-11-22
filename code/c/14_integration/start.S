    .section .text.start
    .align 2
    .global _start
_start:
    la      sp, 0x10010000      /* 数据内存里的栈顶 */
    call    main
1:  j       1b                  /* main 不返回，这里是保险自环 */

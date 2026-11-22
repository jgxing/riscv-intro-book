    .section .text.start
    .align 2
    .global _start
_start:
    /* 机器模式启动：设置栈顶、陷阱向量，然后进入 C 的 kernel_main */
    la      sp, __stack_top
    la      t0, trap_handler
    csrw    mtvec, t0
    call    kernel_main
1:  j       1b

/* ------------------------------------------------------------------
 * trap_handler：所有异常与中断共用一个入口（mtvec 直接模式）。
 * 进来时 MIE 已被硬件清零。这里保存全部整数寄存器到当前任务的内核栈，
 * 调用 C 写的 handle_trap 决定下一个任务，再恢复新任务的现场并 mret。
 * ------------------------------------------------------------------ */
    .align 2
    .global trap_handler
trap_handler:
    /* 本工程全程在 M 模式，任务直接用内核栈，无需 sscratch 交换 */
    addi    sp, sp, -132
    sw      ra,   0(sp)
    sw      gp,   4(sp)
    sw      tp,   8(sp)
    sw      t0,  12(sp)
    sw      t1,  16(sp)
    sw      t2,  20(sp)
    sw      s0,  24(sp)
    sw      s1,  28(sp)
    sw      a0,  32(sp)
    sw      a1,  36(sp)
    sw      a2,  40(sp)
    sw      a3,  44(sp)
    sw      a4,  48(sp)
    sw      a5,  52(sp)
    sw      a6,  56(sp)
    sw      a7,  60(sp)
    sw      s2,  64(sp)
    sw      s3,  68(sp)
    sw      s4,  72(sp)
    sw      s5,  76(sp)
    sw      s6,  80(sp)
    sw      s7,  84(sp)
    sw      s8,  88(sp)
    sw      s9,  92(sp)
    sw      s10, 96(sp)
    sw      s11,100(sp)
    sw      t3, 104(sp)
    sw      t4, 108(sp)
    sw      t5, 112(sp)
    sw      t6, 116(sp)
    csrr    t0, mepc
    sw      t0,120(sp)          /* 120: 被中断的 pc */
    sw      sp,124(sp)          /* 124: 保存的栈指针 */

    mv      a0, sp              /* 把现场指针交给 C 处理函数 */
    call    handle_trap

    /* handle_trap 返回后，a0 是下一个任务的内核栈（含它保存的现场） */
    mv      sp, a0
    lw      t0,120(sp)
    csrw    mepc, t0
    lw      ra,   0(sp)
    lw      gp,   4(sp)
    lw      tp,   8(sp)
    lw      t0,  12(sp)
    lw      t1,  16(sp)
    lw      t2,  20(sp)
    lw      s0,  24(sp)
    lw      s1,  28(sp)
    lw      a0,  32(sp)
    lw      a1,  36(sp)
    lw      a2,  40(sp)
    lw      a3,  44(sp)
    lw      a4,  48(sp)
    lw      a5,  52(sp)
    lw      a6,  56(sp)
    lw      a7,  60(sp)
    lw      s2,  64(sp)
    lw      s3,  68(sp)
    lw      s4,  72(sp)
    lw      s5,  76(sp)
    lw      s6,  80(sp)
    lw      s7,  84(sp)
    lw      s8,  88(sp)
    lw      s9,  92(sp)
    lw      s10, 96(sp)
    lw      s11,100(sp)
    lw      t3, 104(sp)
    lw      t4, 108(sp)
    lw      t5, 112(sp)
    lw      t6, 116(sp)
    addi    sp, sp, 132         /* 撤销入口处的压栈，回到任务原先的栈顶 */
    mret

/* ------------------------------------------------------------------
 * switch_context：协作式上下文切换（也可被调度器直接调用）。
 * a0 = 当前任务的栈指针地址（保存到这里），a1 = 下一个任务的栈指针。
 * 只保存被调用方保存的寄存器 s0-s11 与 ra，符合 RISC-V 调用约定。
 * ------------------------------------------------------------------ */
    .align 2
    .global switch_context
switch_context:
    sw      ra,   0(a0)
    sw      s0,   4(a0)
    sw      s1,   8(a0)
    sw      s2,  12(a0)
    sw      s3,  16(a0)
    sw      s4,  20(a0)
    sw      s5,  24(a0)
    sw      s6,  28(a0)
    sw      s7,  32(a0)
    sw      s8,  36(a0)
    sw      s9,  40(a0)
    sw      s10, 44(a0)
    sw      s11, 48(a0)
    sw      sp,  52(a0)

    mv      sp, a1
    lw      ra,   0(sp)
    lw      s0,   4(sp)
    lw      s1,   8(sp)
    lw      s2,  12(sp)
    lw      s3,  16(sp)
    lw      s4,  20(sp)
    lw      s5,  24(sp)
    lw      s6,  28(sp)
    lw      s7,  32(sp)
    lw      s8,  36(sp)
    lw      s9,  40(sp)
    lw      s10, 44(sp)
    lw      s11, 48(sp)
    lw      sp,  52(sp)
    ret

/* ------------------------------------------------------------------
 * 第一次启动某个任务：把它的入口地址放进 mepc，mret 直接跳过去。
 * a0 = 任务入口，a1 = 任务内核栈（栈顶）
 * ------------------------------------------------------------------ */
    .align 2
    .global start_task
start_task:
    csrw    mepc, a0
    mv      sp, a1
    csrr    t0, mstatus
    li      t1, 0x8
    or      t0, t0, t1          /* 置 MIE，允许中断 */
    csrw    mstatus, t0
    mret

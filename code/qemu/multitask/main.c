#include "platform.h"

/* ---------------- 进程控制块 ---------------- */
#define STACK_SIZE 1024

typedef struct {
    uint32_t *sp;          /* 保存的内核栈指针，切换时用它恢复现场 */
    int pid;
    int state;             /* 0 未使用，1 可运行 */
} pcb_t;

static pcb_t procs[2];
static pcb_t *current;

/* 每个任务一个独立的内核栈。8 字节对齐。 */
static uint8_t stack_a[STACK_SIZE] __attribute__((aligned(8)));
static uint8_t stack_b[STACK_SIZE] __attribute__((aligned(8)));

/* 汇编写的切换函数 */
extern void switch_context(uint32_t **save_sp, uint32_t *next_sp);
extern void start_task(void (*entry)(void), uint32_t *stack_top);

/* ---------------- 定时器与陷阱 ---------------- */
static void timer_init(uint64_t period)
{
    *CLINT_MTIMECMP = *CLINT_MTIME + period;
    set_csr(mie, 1 << 7);       /* 打开机器定时器中断 MTIE */
    set_csr(mstatus, 1 << 3);   /* 打开全局中断 MIE */
}

/* 陷阱现场在栈上的偏移：120 是 mepc，124 是保存的 sp。
 * handle_trap 返回以后，start.S 会把返回值的栈装进 sp。 */
uint32_t *handle_trap(uint32_t *trap_sp)
{
    uint32_t cause = read_csr(mcause);
    uint32_t mepc = read_csr(mepc);

    if (cause & 0x80000000u) {
        /* 中断：目前只有定时器。把比较值推后一个周期。 */
        *CLINT_MTIMECMP = *CLINT_MTIME + 2000000u;
    } else if (cause == 8) {
        /* ecall 系统调用：返回地址要跳过 ecall 那条指令 */
        mepc += 4;
        *(uint32_t *)(trap_sp + 120 / 4) = mepc;
    }

    /* 轮转：把当前任务的保存栈记下来，换到另一个任务 */
    current->sp = (uint32_t *)(trap_sp[124 / 4]);
    current = (current == &procs[0]) ? &procs[1] : &procs[0];
    return current->sp;
}

/* ---------------- 两个任务 ---------------- */
static void task_a(void)
{
    while (1) {
        putchar('A');
        delay(1500000);
    }
}

static void task_b(void)
{
    while (1) {
        putchar('B');
        delay(1500000);
    }
}

/* ---------------- 内核入口 ---------------- */
static void init_proc(pcb_t *p, int pid, uint8_t *stack, void (*entry)(void))
{
    (void)entry;
    p->pid = pid;
    p->state = 1;
    /* 首次启动由 start_task 用 mret 直接跳到入口，这里只需给出栈顶。
     * 第一次定时器中断到来时，trap_handler 会在这个栈上压入真实现场。 */
    p->sp = (uint32_t *)(stack + STACK_SIZE);
}

void kernel_main(void)
{
    puts("multitask start\r\n");

    init_proc(&procs[0], 0, stack_a, task_a);
    init_proc(&procs[1], 1, stack_b, task_b);
    current = &procs[0];

    timer_init(2000000);
    puts("timer on\r\n");

    /* 从 current 的现场直接跳进任务，之后靠定时器中断轮转 */
    start_task(task_a, procs[0].sp);
}

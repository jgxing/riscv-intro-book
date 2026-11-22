# 两个并发任务：各自循环往串口写一个字符，中间忙等一段时间。
# 定时器每 30 个周期抢走 CPU，调度器让 A、B 轮流运行。

.equ UART, 0xFFFF0030
.equ DELAY, 8

# ---------- 任务 A ----------
task_a:
    li t0, UART
    li t1, 65
loop_a:
    sw t1, 0(t0)
    call delay_a
    j loop_a

delay_a:
    li t2, DELAY
wait_a:
    addi t2, t2, -1
    bnez t2, wait_a
    ret

# ---------- 任务 B ----------
task_b:
    li t0, UART
    li t1, 66
loop_b:
    sw t1, 0(t0)
    call delay_b
    j loop_b

delay_b:
    li t2, DELAY
wait_b:
    addi t2, t2, -1
    bnez t2, wait_b
    ret

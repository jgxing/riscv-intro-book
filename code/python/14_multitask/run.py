"""把两个任务汇编、装入、运行，打印串口输出和任务切换轨迹。"""

from assemble import assemble
from memory import BASE
from machine import Machine, PCB

TASKS = open("tasks.s", encoding="utf-8").read()


def build():
    words, labels = assemble(TASKS)
    return words, labels


def main():
    words, labels = build()
    print("任务 A 入口 0x%08x，任务 B 入口 0x%08x"
          % (BASE + labels["task_a"], BASE + labels["task_b"]))

    m = Machine(timer_period=30, max_steps=600)
    m.load_program(words, BASE)
    m.add(PCB("A", BASE + labels["task_a"], 0x80004000))
    m.add(PCB("B", BASE + labels["task_b"], 0x80008000))
    m.start()
    steps = m.run()

    text = "".join(m.bus.uart_tx)
    print("执行指令数：%d" % steps)
    print("串口输出（前 60 字符）：%s" % text[:60])
    print("定时器陷阱次数：%d" % m.trap_count)
    print("任务切换轨迹（前 12 次）：")
    for num, name, pc in m.switch_log[:12]:
        print("  #%2d -> 任务 %s, 从 0x%08x 继续" % (num, name, pc))
    print("任务 A 被调度 %d 次，任务 B 被调度 %d 次"
          % (m.procs[0].slices, m.procs[1].slices))


if __name__ == "__main__":
    main()

"""工具链演示自检：汇编、编码、段布局、运行四条链各查一遍。"""

from assemble import assemble
from build_image import build, run_image
from encode import enc_i, enc_r


def check(name, cond):
    if cond:
        print("PASS", name)
    else:
        print("FAIL", name)
        raise SystemExit(1)


def main():
    # 编码辅助函数本身
    check("addi x1,x0,5 编码",
          enc_i(5, 0, 0, 1, 0x13) == 0x00500093)
    check("add x1,x2,x3 编码",
          enc_r(0, 3, 2, 0, 1, 0x33) == 0x003100B3)

    # 汇编器：标签、伪指令、 lui 立即数
    words, labels = assemble("""
        li a0, 10
        jal ra, fn
        nop
    fn: addi a0, a0, 1
    """)
    check("li/jal/nop 展开为 4 条", len(words) == 4)
    check("标签 fn 指向第 4 条", labels["fn"] == 12)
    check("li 编成 addi", words[0] == enc_i(10, 0, 0, 10, 0x13))

    # 完整程序：段与运行
    prog, syms = build()
    check("sum_to 标签存在", "sum_to" in syms)
    check("stop 标签存在", "stop" in syms)
    check("镜像非空", len(prog) > 10)

    cpu, bus, steps = run_image(prog, trace=False)
    check("求和结果 55", cpu.get_reg(10) == 55)
    check("LED = 0x37", bus.led == 0x37)
    check("串口输出 Hi", "".join(bus.uart_tx) == "Hi")
    # 停机自环会一直执行到步数上限，PC 应停在 stop 那条指令上
    from memory import BASE
    check("PC 停在停机自环", cpu.get_pc() == (BASE + syms["stop"]) & 0xFFFFFFFF)

    print("\nALL TOOLCHAIN TESTS PASSED")


if __name__ == "__main__":
    main()

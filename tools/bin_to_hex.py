"""把二进制镜像转成 Icarus Verilog $readmemh 用的 code.hex。

每 4 个字节合成一个 32 位字（小端），每行输出 8 位十六进制。
指令内存按字寻址，所以少一个字节也不行；末尾不足 4 字节用 0 补齐。
"""

import sys


def main():
    if len(sys.argv) != 3:
        print("用法: python bin_to_hex.py <输入.bin> <输出.hex>")
        raise SystemExit(1)

    src, dst = sys.argv[1], sys.argv[2]
    with open(src, "rb") as f:
        data = f.read()

    if len(data) % 4:
        data += b"\x00" * (4 - len(data) % 4)

    words = []
    for i in range(0, len(data), 4):
        word = (data[i] | (data[i + 1] << 8)
                | (data[i + 2] << 16) | (data[i + 3] << 24))
        words.append("%08x" % word)

    with open(dst, "w", encoding="utf-8") as f:
        f.write("\n".join(words) + "\n")

    print("转换 %d 字节 -> %d 个字，写入 %s" % (len(data), len(words), dst))


if __name__ == "__main__":
    main()

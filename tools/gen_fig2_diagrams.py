from pathlib import Path

FIG = Path('D:/aiprojects/workbuddy/riscv入门教程/figures')
FONT = "font-family=\"'Microsoft YaHei','PingFang SC',sans-serif\""

# ---------- fig2-2 六种指令格式 ----------
rows = [
    ('R 型', '寄存器与寄存器运算', [
        ('funct7', 7, '31:25', 'f'), ('rs2', 5, '24:20', 'r'), ('rs1', 5, '19:15', 'r'),
        ('funct3', 3, '14:12', 'f'), ('rd', 5, '11:7', 'r'), ('opcode', 7, '6:0', 'o')]),
    ('I 型', '短立即数、读内存', [
        ('imm[11:0]', 12, '31:20', 'i'), ('rs1', 5, '19:15', 'r'), ('funct3', 3, '14:12', 'f'),
        ('rd', 5, '11:7', 'r'), ('opcode', 7, '6:0', 'o')]),
    ('S 型', '写内存', [
        ('imm[11:5]', 7, '31:25', 'i'), ('rs2', 5, '24:20', 'r'), ('rs1', 5, '19:15', 'r'),
        ('funct3', 3, '14:12', 'f'), ('imm[4:0]', 5, '11:7', 'i'), ('opcode', 7, '6:0', 'o')]),
    ('B 型', '条件分支', [
        ('12', 1, '', 'i'), ('imm[10:5]', 6, '30:25', 'i'), ('rs2', 5, '24:20', 'r'),
        ('rs1', 5, '19:15', 'r'), ('funct3', 3, '14:12', 'f'), ('imm[4:1]', 4, '11:8', 'i'),
        ('11', 1, '', 'i'), ('opcode', 7, '6:0', 'o')]),
    ('U 型', '装入高 20 位立即数', [
        ('imm[31:12]', 20, '31:12', 'i'), ('rd', 5, '11:7', 'r'), ('opcode', 7, '6:0', 'o')]),
    ('J 型', '长跳转', [
        ('20', 1, '', 'i'), ('imm[10:1]', 10, '30:21', 'i'), ('11', 1, '', 'i'),
        ('imm[19:12]', 8, '19:12', 'i'), ('rd', 5, '11:7', 'r'), ('opcode', 7, '6:0', 'o')]),
]
colors = {
    'o': ('#FCE8E6', '#A32D2D', '#7a2020'),
    'r': ('#E6F1FB', '#185FA5', '#0C447C'),
    'f': ('#E7F3EC', '#3B7A57', '#2d5c43'),
    'i': ('#FDF2E4', '#BA7517', '#7a4f00'),
}
lines = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 600" width="900" height="600" %s>' % FONT,
    '  <title>图 2-2　RV32I 的六种指令格式</title>',
    '  <desc>六行分别表示 R、I、S、B、U、J 六种指令格式的字段划分，opcode、rs1、rs2、rd 与 funct3 在多数格式里位置相同。</desc>',
    '  <rect x="0" y="0" width="900" height="600" fill="#ffffff"/>',
    '  <text x="30" y="40" font-size="18" font-weight="bold" fill="#1f2937">图 2-2　RV32I 的六种指令格式</text>',
    '  <text x="30" y="64" font-size="12.5" fill="#5F5E5A">每行从左到右是最高位 31 到最低位 0</text>',
    '  <text x="140" y="88" font-size="11" fill="#9CA3AF">位 31</text>',
    '  <text x="716" y="88" font-size="11" fill="#9CA3AF">位 0</text>',
]
for idx, (name, usage, fields) in enumerate(rows):
    y = 100 + idx * 85
    lines.append('  <text x="40" y="%d" font-size="16" font-weight="bold" fill="#1f2937">%s</text>' % (y + 22, name))
    lines.append('  <text x="40" y="%d" font-size="11" fill="#5F5E5A">%s</text>' % (y + 40, usage))
    x = 140
    for label, bits, bitrange, kind in fields:
        w = bits * 17
        fill, stroke, text_color = colors[kind]
        lines.append('  <rect x="%d" y="%d" width="%d" height="46" fill="%s" stroke="%s" stroke-width="1.1"/>' % (x, y, w, fill, stroke))
        if bits == 1:
            lines.append('  <text x="%.1f" y="%d" font-size="10" fill="%s" text-anchor="middle">%s</text>' % (x + w / 2, y + 27, text_color, label))
        else:
            fs = 12 if w >= 70 else (10.5 if w >= 48 else 9.5)
            lines.append('  <text x="%.1f" y="%d" font-size="%.1f" font-weight="bold" fill="%s" text-anchor="middle">%s</text>' % (x + w / 2, y + 20, fs, text_color, label))
            lines.append('  <text x="%.1f" y="%d" font-size="9" fill="%s" text-anchor="middle">[%s]</text>' % (x + w / 2, y + 37, text_color, bitrange))
        x += w
lines.append('  <text x="40" y="592" font-size="11.5" fill="#5F5E5A">红：操作码　蓝：寄存器号　绿：辅助操作码　橙：立即数</text>')
lines.append('</svg>')
(FIG / 'fig2-2-formats.svg').write_text('\n'.join(lines), encoding='utf-8')

# ---------- fig2-3 立即数排布 ----------
def imm_set(bit):
    return (
        (20 <= bit <= 31) or
        (7 <= bit <= 11) or
        (25 <= bit <= 31)
    )

specs = [
    ('I 型', lambda b: 20 <= b <= 31, ['imm[11:0] 放在 [31:20]', '取出后符号扩展到 32 位']),
    ('S 型', lambda b: (25 <= b <= 31) or (7 <= b <= 11), ['imm[11:5] 在 [31:25]', 'imm[4:0] 在 [11:7]']),
    ('B 型', lambda b: (b == 31) or (25 <= b <= 30) or (8 <= b <= 11) or b == 7,
     ['拼成 imm[12|10:5|4:1|11|0]', '最低位固定为 0，再符号扩展']),
    ('U 型', lambda b: 12 <= b <= 31, ['imm[31:12] 放在 [31:12]', '低 12 位补 0，不符号扩展']),
    ('J 型', lambda b: (b == 31) or (21 <= b <= 30) or b == 20 or (12 <= b <= 19),
     ['拼成 imm[20|10:1|11|19:12|0]', '最低位固定为 0，再符号扩展']),
]
lines = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 520" width="900" height="520" %s>' % FONT,
    '  <title>图 2-3　六种格式的立即数排布</title>',
    '  <desc>I、S、B、U、J 五种格式中立即数各位在 32 位指令里的位置，以及取出后如何拼接成完整的立即数。</desc>',
    '  <rect x="0" y="0" width="900" height="520" fill="#ffffff"/>',
    '  <text x="30" y="40" font-size="18" font-weight="bold" fill="#1f2937">图 2-3　六种格式的立即数排布</text>',
    '  <text x="30" y="64" font-size="12.5" fill="#5F5E5A">橙色格子是立即数位，灰色是其他字段</text>',
]
for bit in [31, 27, 23, 19, 15, 11, 7, 3, 0]:
    x = 150 + (31 - bit) * 12
    lines.append('  <text x="%d" y="88" font-size="9.5" fill="#9CA3AF" text-anchor="middle">%d</text>' % (x + 6, bit))
for idx, (name, is_imm, notes) in enumerate(specs):
    y = 100 + idx * 82
    lines.append('  <text x="40" y="%d" font-size="15" font-weight="bold" fill="#1f2937">%s</text>' % (y + 27, name))
    for bit in range(32):
        x = 150 + (31 - bit) * 12
        fill = '#FAC775' if is_imm(bit) else '#EDECE8'
        stroke = '#BA7517' if is_imm(bit) else '#D3D1C8'
        lines.append('  <rect x="%d" y="%d" width="12" height="40" fill="%s" stroke="%s" stroke-width="0.5"/>' % (x, y, fill, stroke))
    lines.append('  <text x="570" y="%d" font-size="13" fill="#7a4f00">%s</text>' % (y + 20, notes[0]))
    lines.append('  <text x="570" y="%d" font-size="12" fill="#3a3a38">%s</text>' % (y + 38, notes[1]))
lines.append('  <text x="40" y="508" font-size="11.5" fill="#5F5E5A">B 型和 J 型把立即数位拆开摆放，是为了让寄存器号和操作码留在固定位置，简化译码电路。</text>')
lines.append('</svg>')
(FIG / 'fig2-3-immediates.svg').write_text('\n'.join(lines), encoding='utf-8')

print('generated fig2-2-formats.svg and fig2-3-immediates.svg')

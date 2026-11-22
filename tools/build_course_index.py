import re
from pathlib import Path

BASE = Path('C:/Users/hzxin/AppData/Local/Temp/riscv-pptx-all2')
ROOT = Path('D:/aiprojects/workbuddy/riscv入门教程')
OUT = ROOT / '课件参考索引.md'
FULL = BASE / 'all_text.txt'

manifest = []
for line in (BASE / 'manifest.tsv').read_text(encoding='utf-8').splitlines():
    parts = line.split('\t')
    if len(parts) == 3:
        manifest.append((parts[0], parts[1], parts[2]))

def clean_line(s):
    s = s.strip()
    s = re.sub(r'^[-*•]+\s*', '', s)
    s = re.sub(r'^[nN•]\s*', '', s)
    s = s.replace('\\|', '|')
    s = re.sub(r'&#32;', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def parse_pages(md_text):
    chunks = re.split(r'^## 第 (\d+) 页\s*$', md_text, flags=re.M)
    pages = []
    for i in range(1, len(chunks), 2):
        num = int(chunks[i])
        body = chunks[i + 1]
        body = body.split('### 结构')[0]
        lines = []
        for raw in body.splitlines():
            if raw.startswith('### ') or raw.startswith('# '):
                continue
            if re.match(r'^\*\*c\d+\*\*（', raw):
                continue
            t = clean_line(raw)
            if t and t not in lines:
                lines.append(t)
        pages.append((num, lines))
    return pages

out = ['# RISC-V 教学课件内容索引', '',
       '本文件由 `D:\\RISC-V教学` 下 34 份 PPTX 课件自动提取，供教材写作时检索参考。原始课件未作修改。',
       '每页只保留文字要点，图片内容与板书推导需要时再看原课件。', '']
full_lines = []
page_count = 0
for n, status, path in manifest:
    name = Path(path).name
    md_file = BASE / n / 'slides.md'
    text = md_file.read_text(encoding='utf-8')
    pages = parse_pages(text)
    page_count += len(pages)
    tag = '（备份版）' if ('备份' in name or 'bak' in name or '自动保存' in name) else ''
    out.append('## %s %s%s（%d 页）' % (n, name, tag, len(pages)))
    out.append('')
    for pnum, lines in pages:
        full_lines.append('[%s | %s | 第%d页]' % (n, name, pnum))
        full_lines.extend(lines)
        full_lines.append('')
        brief = ' / '.join(lines[:10])
        if len(brief) > 460:
            brief = brief[:460] + '…'
        out.append('- 第 %d 页：%s' % (pnum, brief))
    out.append('')
OUT.write_text('\n'.join(out), encoding='utf-8')
FULL.write_text('\n'.join(full_lines), encoding='utf-8')
print('index:', OUT, OUT.stat().st_size, 'bytes')
print('full text:', FULL, FULL.stat().st_size, 'bytes')
print('files:', len(manifest), 'pages:', page_count)

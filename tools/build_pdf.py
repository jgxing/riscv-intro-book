#!/usr/bin/env python3
"""把全书 Markdown 合并、转成一份带 O'Reilly 风格版式的 HTML，供 Chrome 打印成 PDF。"""
import html as html_mod
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHAPTERS = sorted((ROOT / 'chapters').glob('第??章_*.md'))
FILES = [ROOT / '前言.md'] + CHAPTERS + [
    ROOT / '附录A_RV32I指令与CSR速查.md',
    ROOT / '附录B_Verilog模块与测试台模板.md',
    ROOT / '附录C_工具链与环境搭建.md',
    ROOT / '参考文献与延伸阅读.md',
]

CSS = r"""
@page { size: A4; margin: 20mm 18mm 18mm 18mm; }
* { box-sizing: border-box; }
html { font-size: 10.5pt; }
body {
  margin: 0; color: #222; line-height: 1.7;
  font-family: "SimSun", "Noto Serif CJK SC", "Source Han Serif SC", serif;
}
.cover-page { page-break-after: always; margin: -20mm -18mm -18mm; }
.cover-page img { width: 210mm; height: 297mm; display: block; }
.title-page { page-break-after: always; padding-top: 55mm; text-align: center; }
.title-page .series { font-family: "Microsoft YaHei", sans-serif; color: #C8102E; font-size: 13pt; letter-spacing: 3px; }
.title-page .booktitle { font-family: "Microsoft YaHei", sans-serif; font-size: 29pt; font-weight: 800; color: #111; margin: 18mm 0 6mm; }
.title-page .subtitle { font-family: "Microsoft YaHei", sans-serif; font-size: 21pt; color: #C8102E; }
.title-page .author { font-family: "Microsoft YaHei", sans-serif; font-size: 15pt; margin-top: 32mm; }
.title-page .affiliation { font-size: 12pt; color: #555; margin-top: 3mm; }
.title-page .repo { font-size: 9pt; color: #777; margin-top: 22mm; word-break: break-all; }
.toc-page { page-break-after: always; }
.toc-page h1 { border-bottom: 3px solid #C8102E; }
ul.toc { list-style: none; padding-left: 0; margin-top: 8mm; }
ul.toc li { margin: 0; padding: 1.2mm 0; border-bottom: 1px dotted #DDD; font-size: 10pt; display: flex; justify-content: space-between; }
ul.toc .toc-num { color: #888; font-family: Consolas, monospace; font-size: 9pt; }
ul.toc a { color: #222; text-decoration: none; }
ul.toc .toc-lv1 { font-family: "Microsoft YaHei", sans-serif; font-weight: 700; margin-top: 4mm; }
ul.toc .toc-lv2 { padding-left: 9mm; color: #444; font-size: 9.5pt; }
h1, h2, h3, h4 { font-family: "Microsoft YaHei", "Noto Sans CJK SC", sans-serif; color: #111; }
h1 {
  font-size: 22pt; color: #C8102E; border-bottom: 3px solid #C8102E;
  padding-bottom: 3mm; margin: 0 0 8mm; page-break-before: always;
}
h2 { font-size: 14pt; margin: 9mm 0 3mm; page-break-after: avoid; }
h3 { font-size: 11.5pt; margin: 6mm 0 2mm; page-break-after: avoid; }
p { margin: 2mm 0; text-align: justify; }
img { max-width: 100%; display: block; margin: 5mm auto 2mm; page-break-inside: avoid; }
p em, figcaption { color: #555; font-size: 9pt; }
pre {
  background: #F6F6F4; border-left: 3px solid #C8102E; padding: 3mm 4mm;
  font-family: Consolas, "Courier New", monospace; font-size: 8.3pt;
  line-height: 1.45; white-space: pre-wrap; page-break-inside: avoid;
  margin: 4mm 0;
}
code { font-family: Consolas, "Courier New", monospace; font-size: 9pt; background: #F2F2F0; padding: 0 1px; }
pre code { background: none; padding: 0; font-size: inherit; }
table { border-collapse: collapse; width: 100%; margin: 4mm 0; font-size: 9pt; page-break-inside: avoid; }
th, td { border: 1px solid #CCC; padding: 1.5mm 2mm; text-align: left; vertical-align: top; }
th { background: #F2F0EC; font-family: "Microsoft YaHei", sans-serif; }
blockquote { border-left: 3px solid #DDD; margin: 4mm 0; padding-left: 4mm; color: #555; }
hr { border: none; border-top: 1px solid #DDD; margin: 8mm 0; }
"""


def main() -> None:
    parts = []
    toc = []
    sec_no = 0
    for path in FILES:
        text = path.read_text(encoding='utf-8')
        text = text.replace('](../figures/', '](figures/')
        out_lines = []
        fence = None
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith('```') or stripped.startswith('~~~'):
                marker = stripped[:3]
                if fence is None:
                    fence = marker
                elif marker == fence:
                    fence = None
                out_lines.append(line)
                continue
            if fence is None:
                m = re.match(r'^(#{1,2}) (.+)$', line)
                if m:
                    sec_no += 1
                    level = len(m.group(1))
                    title = re.sub(r'[*_`]', '', m.group(2)).strip()
                    anchor = 'sec-%03d' % sec_no
                    line = '%s %s {#%s}' % (m.group(1), m.group(2), anchor)
                    toc.append((level, anchor, title))
            out_lines.append(line)
        parts.append('\n'.join(out_lines))

    merged = ROOT / '_book_all.md'
    merged.write_text('\n\n'.join(parts), encoding='utf-8')
    body_path = ROOT / '_book_body.html'
    subprocess.run([
        'pandoc', '-f', 'markdown', '-t', 'html5', '--wrap=none',
        '--no-highlight', str(merged), '-o', str(body_path)
    ], check=True)
    body = body_path.read_text(encoding='utf-8')

    pages_file = ROOT / 'toc_pages.json'
    page_map = json.loads(pages_file.read_text(encoding='utf-8')) if pages_file.exists() else {}
    toc_html = '\n'.join(
        '<li class="toc-lv%d"><a href="#%s">%s</a>%s</li>' % (
            level, anchor, html_mod.escape(title),
            '<span class="toc-num">%s</span>' % page_map[anchor] if page_map.get(anchor) else ''
        )
        for level, anchor, title in toc
    )

    page = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>RISC-V 处理器设计入门：从指令集到五级流水线</title>
<style>%s</style>
</head>
<body>
<section class="cover-page"><img src="cover/cover.png" alt="封面"></section>
<section class="title-page">
  <div class="series">计算机体系结构丛书</div>
  <div class="booktitle">RISC-V 处理器设计入门</div>
  <div class="subtitle">从指令集到五级流水线</div>
  <div class="author">邢建国　著</div>
  <div class="affiliation">浙江工商大学</div>
  <div class="repo">配套代码 https://github.com/jgxing/riscv-intro-book</div>
</section>
<section class="toc-page">
<h1>目录</h1>
<ul class="toc">
%s
</ul>
</section>
%s
</body>
</html>
""" % (CSS, toc_html, body)

    out = ROOT / '_book.html'
    out.write_text(page, encoding='utf-8')
    print('HTML 已生成：%s（%d 个目录条目，正文 %d 字符）' % (out, len(toc), len(body)))


if __name__ == '__main__':
    main()

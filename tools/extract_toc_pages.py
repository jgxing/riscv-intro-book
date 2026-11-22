#!/usr/bin/env python3
"""从已生成的 PDF 中定位各章标题所在页，供目录回填页码。"""
import json
import pathlib
import re

from pypdf import PdfReader

ROOT = pathlib.Path(__file__).resolve().parent.parent
PDF = ROOT / '_book_base.pdf'
HTML = ROOT / '_book.html'

html = HTML.read_text(encoding='utf-8')
items = re.findall(r'<li class="toc-lv1"><a href="#(sec-\d+)">(.*?)</a>', html)
reader = PdfReader(str(PDF))
pages = [(p.extract_text() or '').replace(' ', '').replace('\n', '').replace('\u3000', '') for p in reader.pages]

start = 0
for i, t in enumerate(pages):
    if t.startswith('前言'):
        start = i
        break

result = {}
for anchor, title in items:
    key = re.sub(r'<[^>]+>', '', title).replace(' ', '').replace('\u3000', '')
    found = None
    for i in range(start, len(pages)):
        if key and pages[i].startswith(key):
            found = i + 1
            break
    result[anchor] = found
    print('%-9s %-32s %s' % (anchor, key, found))

(ROOT / 'toc_pages.json').write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8')
print('已写入 toc_pages.json')

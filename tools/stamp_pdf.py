#!/usr/bin/env python3
"""给 Chrome 打印出的基础 PDF 加页脚作者与页码。"""
import io
import pathlib

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = ROOT / '_book_base.pdf'
OUT = ROOT / 'RISC-V处理器设计入门_从指令集到五级流水线.pdf'

pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

reader = PdfReader(str(BASE))
total = len(reader.pages)
width, height = A4

buf = io.BytesIO()
c = canvas.Canvas(buf, pagesize=A4)
for i in range(1, total):
    c.setFont('STSong-Light', 9)
    c.setFillColorRGB(0.55, 0.55, 0.55)
    c.drawString(52, height - 30, 'RISC-V 处理器设计入门')
    c.drawRightString(width - 52, height - 30, '从指令集到五级流水线')
    c.drawString(52, 14, '邢建国  著')
    c.drawRightString(width - 52, 14, '第 %d 页 / 共 %d 页' % (i + 1, total))
    c.showPage()
c.save()
buf.seek(0)
stamps = PdfReader(buf)

writer = PdfWriter()
for i, page in enumerate(reader.pages):
    writer.add_page(page)
    if i >= 1:
        writer.pages[i].merge_page(stamps.pages[i - 1])
with open(OUT, 'wb') as f:
    writer.write(f)

print('最终 PDF：%s（%d 页，%d 字节）' % (OUT, total, OUT.stat().st_size))

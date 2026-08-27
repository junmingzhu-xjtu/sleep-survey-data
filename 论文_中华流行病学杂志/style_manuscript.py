#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""稿件 docx 样式处理: 宋体正文/黑体标题 + 中华流行病学杂志三线表(顶线/栏目线/底线,无竖线)"""
import sys
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt
from docx.enum.text import WD_LINE_SPACING


def set_font(style, ascii_font, east_font, size_pt, bold=None):
    style.font.name = ascii_font
    style.font.size = Pt(size_pt)
    if bold is not None:
        style.font.bold = bold
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts = rpr.makeelement(qn('w:rFonts'), {})
        rpr.append(rfonts)
    rfonts.set(qn('w:ascii'), ascii_font)
    rfonts.set(qn('w:hAnsi'), ascii_font)
    rfonts.set(qn('w:eastAsia'), east_font)


def make_border(edge, val, sz):
    el = OxmlElement('w:' + edge)
    el.set(qn('w:val'), val)
    el.set(qn('w:sz'), str(sz))
    el.set(qn('w:space'), '0')
    el.set(qn('w:color'), '000000')
    return el


def three_line_table(table):
    """三线表: 顶线与底线为粗单线(1.5pt),表头行下为细单线(0.75pt),其余无线"""
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement('w:tblBorders')
    borders.append(make_border('top', 'single', 12))
    borders.append(make_border('bottom', 'single', 12))
    borders.append(make_border('left', 'none', 0))
    borders.append(make_border('right', 'none', 0))
    borders.append(make_border('insideH', 'none', 0))
    borders.append(make_border('insideV', 'none', 0))
    old = tblPr.find(qn('w:tblBorders'))
    if old is not None:
        tblPr.remove(old)
    tblPr.append(borders)
    # 表头行底部细线(栏目线)
    for cell in table.rows[0].cells:
        tcPr = cell._tc.get_or_add_tcPr()
        tcBorders = OxmlElement('w:tcBorders')
        tcBorders.append(make_border('bottom', 'single', 6))
        old_b = tcPr.find(qn('w:tcBorders'))
        if old_b is not None:
            tcPr.remove(old_b)
        tcPr.append(tcBorders)


def apply(path):
    doc = Document(path)
    normal = doc.styles['Normal']
    set_font(normal, 'Times New Roman', '宋体', 12)
    normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    set_font(doc.styles['Heading 1'], 'Times New Roman', '黑体', 16, bold=True)
    set_font(doc.styles['Heading 2'], 'Times New Roman', '黑体', 14, bold=True)
    set_font(doc.styles['Heading 3'], 'Times New Roman', '黑体', 12, bold=True)
    for hs in ('Heading 1', 'Heading 2', 'Heading 3'):
        hpf = doc.styles[hs].paragraph_format
        hpf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        hpf.space_before = Pt(12)
        hpf.space_after = Pt(6)
    try:
        set_font(doc.styles['Table'], 'Times New Roman', '宋体', 9)
    except KeyError:
        pass
    for t in doc.tables:
        three_line_table(t)
    doc.save(path)
    print('styled:', path)


if __name__ == '__main__':
    for p in sys.argv[1:]:
        apply(p)

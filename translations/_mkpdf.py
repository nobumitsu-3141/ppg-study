#!/usr/bin/env python3
"""Markdown-ish 和訳テキスト -> 日本語PDF (reportlab + IPAGothic)"""
import sys, re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                Table, TableStyle, KeepTogether)
from reportlab.lib import colors

FONT = '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf'
pdfmetrics.registerFont(TTFont('IPAG', FONT))

S = {
 'h1': ParagraphStyle('h1', fontName='IPAG', fontSize=15, leading=21,
                      spaceBefore=2, spaceAfter=8, textColor=colors.HexColor('#11304f')),
 'h2': ParagraphStyle('h2', fontName='IPAG', fontSize=12.5, leading=18,
                      spaceBefore=13, spaceAfter=5, textColor=colors.HexColor('#1b4f72')),
 'h3': ParagraphStyle('h3', fontName='IPAG', fontSize=10.8, leading=16,
                      spaceBefore=9, spaceAfter=3, textColor=colors.HexColor('#2c5f7c')),
 'p':  ParagraphStyle('p', fontName='IPAG', fontSize=9.4, leading=16.2,
                      alignment=TA_JUSTIFY, spaceAfter=6),
 'meta': ParagraphStyle('meta', fontName='IPAG', fontSize=8.4, leading=13.5,
                      spaceAfter=3, textColor=colors.HexColor('#555555')),
 'fig': ParagraphStyle('fig', fontName='IPAG', fontSize=8.8, leading=15,
                      alignment=TA_JUSTIFY, spaceAfter=5, leftIndent=7*mm,
                      textColor=colors.HexColor('#20323f')),
 'note': ParagraphStyle('note', fontName='IPAG', fontSize=8.6, leading=14.5,
                      alignment=TA_JUSTIFY, spaceAfter=5, leftIndent=5*mm,
                      textColor=colors.HexColor('#7d4b00')),
 'li': ParagraphStyle('li', fontName='IPAG', fontSize=9.4, leading=16,
                      alignment=TA_JUSTIFY, spaceAfter=3,
                      leftIndent=6*mm, bulletIndent=1.5*mm),
}

def esc(t):
    t = t.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'<i>\1</i>', t)
    t = re.sub(r'`(.+?)`', r'<font face="Courier">\1</font>', t)
    return t

def build(src, out, title, subtitle):
    doc = SimpleDocTemplate(out, pagesize=A4,
        leftMargin=19*mm, rightMargin=17*mm, topMargin=17*mm, bottomMargin=16*mm,
        title=title, author='和訳')
    F=[]
    lines = open(src, encoding='utf-8').read().split('\n')
    tbl=[]
    def flush_tbl():
        nonlocal tbl
        if not tbl: return
        rows=[[Paragraph(esc(c), ParagraphStyle('tc', fontName='IPAG', fontSize=8.2, leading=12.6))
               for c in r] for r in tbl]
        nc=max(len(r) for r in rows)
        rows=[r+[Paragraph('',S['p'])]*(nc-len(r)) for r in rows]
        avail=A4[0]-36*mm
        t=Table(rows, colWidths=[avail/nc]*nc, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#b9c6d0')),
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8eef3')),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
            ('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),
        ]))
        F.append(t); F.append(Spacer(1,7)); tbl=[]

    for ln in lines:
        s=ln.rstrip()
        if s.startswith('|') and s.endswith('|'):
            cells=[c.strip() for c in s.strip('|').split('|')]
            if all(re.fullmatch(r':?-{2,}:?', c) for c in cells if c): continue
            tbl.append(cells); continue
        flush_tbl()
        if not s.strip(): F.append(Spacer(1,3)); continue
        if s.startswith('### '):  F.append(Paragraph(esc(s[4:]), S['h3']))
        elif s.startswith('## '): F.append(Paragraph(esc(s[3:]), S['h2']))
        elif s.startswith('# '):  F.append(Paragraph(esc(s[2:]), S['h1']))
        elif s.startswith('@FIG '): F.append(Paragraph(esc(s[5:]), S['fig']))
        elif s.startswith('@NOTE '): F.append(Paragraph(esc(s[6:]), S['note']))
        elif s.startswith('@META '): F.append(Paragraph(esc(s[6:]), S['meta']))
        elif re.match(r'^[-*] ', s): F.append(Paragraph(esc(s[2:]), S['li'], bulletText='・'))
        elif re.match(r'^\d+\. ', s):
            n=s.split('.',1)[0]; F.append(Paragraph(esc(s.split('. ',1)[1]), S['li'], bulletText=n+'.'))
        elif s.strip()=='---': F.append(Spacer(1,6))
        else: F.append(Paragraph(esc(s), S['p']))
    flush_tbl()

    def deco(cv, d):
        cv.saveState()
        cv.setFont('IPAG', 7.2); cv.setFillColor(colors.HexColor('#8a97a0'))
        cv.drawString(19*mm, 9*mm, subtitle)
        cv.drawRightString(A4[0]-17*mm, 9*mm, '%d' % d.page)
        cv.setStrokeColor(colors.HexColor('#d5dde3')); cv.setLineWidth(0.4)
        cv.line(19*mm, 12*mm, A4[0]-17*mm, 12*mm)
        cv.restoreState()
    doc.build(F, onFirstPage=deco, onLaterPages=deco)
    print('OK ->', out)

if __name__=='__main__':
    build(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

#!/usr/bin/env python3
"""和訳 Markdown -> 日本語PDF (reportlab + IPAGothic)

使い方:  python3 _mkpdf.py <input.md> <output.pdf> "<PDFタイトル>" "<フッタ>"

書式:
  # / ## / ### / ####   見出し
  @META  書誌情報行      @FIG 図表説明     @NOTE 注記・数式
  - / 1.  箇条書き        | a | b |  表     ---  区切り
  **太字**  _斜体_  `等幅`
"""
import sys, re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

FONT = '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf'
pdfmetrics.registerFont(TTFont('IPAG', FONT))

# --- フォントに存在するコードポイント（欠落文字の検出用）---
try:
    from fontTools.ttLib import TTFont as _FT
    _cm = set()
    for _t in _FT(FONT)['cmap'].tables:
        _cm |= set(_t.cmap.keys())
except Exception:
    _cm = None

# 上付き・下付き文字（reportlab の <super>/<sub> に変換して正しく描画する）
SUP = {'⁰':'0','¹':'1','²':'2','³':'3','⁴':'4','⁵':'5','⁶':'6','⁷':'7','⁸':'8','⁹':'9',
       '⁻':'-','⁺':'+','ᵃ':'a','ᵇ':'b','ᶜ':'c','ᵈ':'d','ᵉ':'e','ᶠ':'f','ᵍ':'g','ʰ':'h','ⁱ':'i','ᵀ':'T','ᵗ':'t','ᵐ':'m','ⁿ':'n','ᵏ':'k','ˢ':'s','ʲ':'j'}
SUB = {'₀':'0','₁':'1','₂':'2','₃':'3','₄':'4','₅':'5','₆':'6','₇':'7','₈':'8','₉':'9','ᵢ':'i','ⱼ':'j'}
# IPAGothic に無い記号の安全な置換
FALLBACK = {'⚠️':'※', '⚠':'※', '™':'(TM)', '≥':'≧', '≤':'≦', '️':'', 'ȳ':'mean_y', '∗':'*', '⩾':'≧', '⩽':'≦', 'ﬁ':'fi', 'ﬂ':'fl', '®':'(R)', '©':'(C)'}

_SUP_RE = re.compile('[' + ''.join(SUP) + ']+')
_SUB_RE = re.compile('[' + ''.join(SUB) + ']+')

_missing = set()

def _fix_chars(t):
    for k, v in FALLBACK.items():
        t = t.replace(k, v)
    t = _SUP_RE.sub(lambda m: '<super>%s</super>' % ''.join(SUP[c] for c in m.group()), t)
    t = _SUB_RE.sub(lambda m: '<sub>%s</sub>'   % ''.join(SUB[c] for c in m.group()), t)
    if _cm is not None:
        for c in t:
            if c not in '\n\t' and ord(c) not in _cm:
                _missing.add(c)
    return t

# 本文は左揃え＋CJK 折り返し。両端揃えにすると日本語中のラテン語周辺の
# 空白だけが引き伸ばされ、行内に巨大な空隙ができるため使わない。
def _st(**kw):
    kw.setdefault('fontName', 'IPAG')
    kw.setdefault('alignment', TA_LEFT)
    kw.setdefault('wordWrap', 'CJK')
    return ParagraphStyle(kw.pop('name', 's'), **kw)

S = {
 'h1':   _st(name='h1', fontSize=15,   leading=22,   spaceBefore=2,  spaceAfter=9,
             textColor=colors.HexColor('#11304f')),
 'h2':   _st(name='h2', fontSize=12.5, leading=18,   spaceBefore=15, spaceAfter=5,
             textColor=colors.HexColor('#1b4f72')),
 'h3':   _st(name='h3', fontSize=10.8, leading=16,   spaceBefore=11, spaceAfter=3,
             textColor=colors.HexColor('#2c5f7c')),
 'h4':   _st(name='h4', fontSize=9.8,  leading=15,   spaceBefore=8,  spaceAfter=2,
             textColor=colors.HexColor('#44708a')),
 'p':    _st(name='p',  fontSize=9.4,  leading=16.6, spaceAfter=7),
 'meta': _st(name='me', fontSize=8.4,  leading=13.5, spaceAfter=2,
             textColor=colors.HexColor('#555555')),
 'fig':  _st(name='fg', fontSize=8.8,  leading=15.2, spaceAfter=6, leftIndent=6*mm,
             textColor=colors.HexColor('#20323f')),
 'note': _st(name='nt', fontSize=8.7,  leading=15,   spaceAfter=6, leftIndent=5*mm,
             textColor=colors.HexColor('#7d4b00')),
 'li':   _st(name='li', fontSize=9.4,  leading=16.4, spaceAfter=3,
             leftIndent=6*mm, bulletIndent=1.5*mm),
 'cell': _st(name='c',  fontSize=8.2,  leading=13),
}

def esc(t):
    t = t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'(?<!\w)_([^_\s][^_]*?)_(?!\w)', r'<i>\1</i>', t)
    t = re.sub(r'`(.+?)`', r'<font face="Courier">\1</font>', t)
    t = t.replace('<br>', '<br/>')
    return _fix_chars(t)

def build(src, out, title, footer):
    doc = SimpleDocTemplate(out, pagesize=A4,
        leftMargin=19*mm, rightMargin=17*mm, topMargin=17*mm, bottomMargin=16*mm,
        title=title, author='和訳')
    F, tbl = [], []

    def flush_tbl():
        nonlocal tbl
        if not tbl:
            return
        rows = [[Paragraph(esc(c), S['cell']) for c in r] for r in tbl]
        nc = max(len(r) for r in rows)
        rows = [r + [Paragraph('', S['cell'])] * (nc - len(r)) for r in rows]
        avail = A4[0] - 36*mm
        t = Table(rows, colWidths=[avail/nc]*nc, hAlign='LEFT', repeatRows=1)
        t.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#b9c6d0')),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8eef3')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ]))
        F.append(t); F.append(Spacer(1, 9)); tbl = []

    for ln in open(src, encoding='utf-8').read().split('\n'):
        s = ln.rstrip()
        if s.startswith('|') and s.endswith('|'):
            cells = [c.strip() for c in s.strip('|').split('|')]
            if cells and all(re.fullmatch(r':?-{2,}:?', c) for c in cells if c):
                continue
            tbl.append(cells); continue
        flush_tbl()
        if not s.strip():
            continue                       # 段落間隔は spaceAfter で確保する
        if   s.startswith('#### '):  F.append(Paragraph(esc(s[5:]), S['h4']))
        elif s.startswith('### '):   F.append(Paragraph(esc(s[4:]), S['h3']))
        elif s.startswith('## '):    F.append(Paragraph(esc(s[3:]), S['h2']))
        elif s.startswith('# '):     F.append(Paragraph(esc(s[2:]), S['h1']))
        elif s.startswith('@FIG '):  F.append(Paragraph(esc(s[5:]), S['fig']))
        elif s.startswith('@NOTE '): F.append(Paragraph(esc(s[6:]), S['note']))
        elif s.startswith('@META '): F.append(Paragraph(esc(s[6:]), S['meta']))
        elif re.match(r'^[-*] ', s):
            F.append(Paragraph(esc(s[2:]), S['li'], bulletText='・'))
        elif re.match(r'^\d+\. ', s):
            n, body = s.split('. ', 1)
            F.append(Paragraph(esc(body), S['li'], bulletText=n + '.'))
        elif s.strip() == '---':
            F.append(Spacer(1, 8))
        else:
            F.append(Paragraph(esc(s), S['p']))
    flush_tbl()

    def deco(cv, d):
        cv.saveState()
        cv.setFont('IPAG', 7.2); cv.setFillColor(colors.HexColor('#8a97a0'))
        cv.drawString(19*mm, 9*mm, footer)
        cv.drawRightString(A4[0]-17*mm, 9*mm, '%d' % d.page)
        cv.setStrokeColor(colors.HexColor('#d5dde3')); cv.setLineWidth(0.4)
        cv.line(19*mm, 12*mm, A4[0]-17*mm, 12*mm)
        cv.restoreState()

    doc.build(F, onFirstPage=deco, onLaterPages=deco)
    if _missing:
        print('  !! フォントに無い文字:', ''.join(sorted(_missing)))
    print('OK ->', out)

if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

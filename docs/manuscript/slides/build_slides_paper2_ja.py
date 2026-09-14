#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""論文2（Pulse Wave Database 4,374名）の発表スライドを川副式書式で生成する。

書式ルール（slide-format スキル）:
  - タイトル44pt太字・金BF9000・黒縁取り2.25pt・全スライド同位置・1行
  - タイトル直下に金色下線（y=1.52in・太さ8pt・全幅）
  - 右上に章ナビ（背景・方法・結果・考察・結論。現在章のみティール00A8AA）
  - 本文は22pt以上（出典16pt・章ナビ11ptのみ例外）
  - 図解優先・詳細はノートへ・図と文字を重ねない
  - 対比色はブルー0072B2 × バーミリオンD55E00（＋ティール）。金は構造色として予約

版は 2 つ作る（表以外は同一）:
  A  すべての文字が 22pt 以上。表3 は主要 4 行のみ（残りはノート）
  B  表の中だけ 16〜18pt を許し、表3 は 12 行すべてを載せる

数式だけは画像（matplotlib mathtext・白背景・assets_paper2/*.png）で置く。
同じ式を文字でノートに残す。単純な定義（ΔT・RI・判定規準）は編集可能な文字で置く。

使い方:
    python3 build_slides_paper2_ja.py --variant A --out paper2_ja_A.pptx
    python3 build_slides_paper2_ja.py --variant B --out paper2_ja_B.pptx
    python3 build_slides_paper2_ja.py --selftest

数値の出どころ:
    docs/manuscript/paper2/v2/05_draft_ja_v2.md（和文原稿 v2）
    docs/manuscript/paper2/02_tables.md（表1〜表4・表2b）
    analysis/src/pda.py・analysis/src/pda2.py（凍結版と第2版の定数・式）
    docs/manuscript/v2/05_draft_ja_v2.md（論文1。研究全体の前提）
"""
from __future__ import annotations

import argparse
import os
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets_paper2")

GOLD, INK, WHITE = "BF9000", "1A1A1A", "FFFFFF"
BLUE, VERM, TEAL = "0072B2", "D55E00", "00A8AA"
RED, GREY, DGREY, LGREY, PALE = "C00000", "808080", "595959", "D9D9D9", "F2F2F2"
FONT = "メイリオ"
SW, SH = 13.333, 7.5

CHAPTERS = ["背景", "方法", "結果", "考察", "結論"]

# 章ナビの座標（タイトル幅の上限を決めるので、ここを動かすと check_title も動く）
CHIP_W, CHIP_GAP, CHIP_RIGHT = 0.54, 0.05, 0.15
CHIP_X0 = SW - CHIP_RIGHT - (len(CHAPTERS) * CHIP_W + (len(CHAPTERS) - 1) * CHIP_GAP)
TITLE_X, TITLE_Y, TITLE_W, TITLE_H = 0.55, 0.35, 9.70, 0.95
# lint の「パンくず侵入」判定（推定右端 > 章ナビ左端 − 0.2cm）に合わせた上限
TITLE_MAX_W = CHIP_X0 - 0.0787 - TITLE_X


def _rgb(h):
    return RGBColor.from_string(h)


def _units(text: str) -> float:
    """lint と同じ文字幅ユニット計算（全角=1.0・ASCII=0.56・空白=0.30）。"""
    u = 0.0
    for ch in text:
        o = ord(ch)
        if ch == " ":
            u += 0.30
        elif o <= 0x24F or 0x2080 <= o <= 0x208E:
            u += 0.56
        else:
            u += 1.0
    return u


def width_in(text: str, pt: float) -> float:
    """lint 準拠の推定描画幅（インチ）。Meiryo安全係数1.12込み。"""
    return _units(text) * (pt / 72.0) * 1.12


def check_title(title: str) -> None:
    w = width_in(title, 44)
    assert w <= TITLE_MAX_W, f"タイトルが幅超過 {w:.2f}in > {TITLE_MAX_W:.2f}in: {title}"


def outline_run(run, w_pt=2.25, color=INK):
    """run に文字の縁取り（a:ln）を付ける。rPr の先頭に入れる必要がある。"""
    rPr = run.font._rPr
    ln = rPr.makeelement(qn("a:ln"), {"w": str(int(w_pt * 12700))})
    fill = ln.makeelement(qn("a:solidFill"), {})
    clr = fill.makeelement(qn("a:srgbClr"), {"val": color})
    fill.append(clr)
    ln.append(fill)
    rPr.insert(0, ln)


def set_text(tf, lines, size=24, color=INK, bold=False, align=PP_ALIGN.LEFT,
             space_after=6, line_spacing=1.2):
    """テキストフレームに行を流し込む（各行=1段落・1行に収まる前提）。"""
    tf.word_wrap = True
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        p.line_spacing = line_spacing
        txt, sz, col, bd = ln if isinstance(ln, tuple) else (ln, size, color, bold)
        r = p.add_run()
        r.text = txt
        r.font.size = Pt(sz)
        r.font.bold = bd
        r.font.name = FONT
        r.font.color.rgb = _rgb(col)


def _lines_width(lines, default_pt) -> float:
    w = 0.0
    for ln in lines:
        txt, sz = (ln[0], ln[1]) if isinstance(ln, tuple) else (ln, default_pt)
        w = max(w, width_in(txt, sz))
    return w


def textbox(slide, x, y, w, h, lines, **kw):
    """テキストボックス。w に None を渡すと行の推定幅から自動で決める。"""
    if w is None:
        w = _lines_width(lines, kw.get("size", 24)) + 0.16
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tb.text_frame.margin_left = Inches(0.05)
    tb.text_frame.margin_right = Inches(0.05)
    tb.text_frame.margin_top = Inches(0.02)
    tb.text_frame.margin_bottom = Inches(0.02)
    set_text(tb.text_frame, lines, **kw)
    return tb


def label(slide, cx, cy, text, size=22, color=INK, bold=False):
    """図の中の 1 行ラベル。(cx, cy) を中心に置く。"""
    w = width_in(text, size) + 0.16
    h = (size / 72.0) * 1.9
    return textbox(slide, cx - w / 2, cy - h / 2, w, h, [text],
                   size=size, color=color, bold=bold, align=PP_ALIGN.CENTER,
                   space_after=0, line_spacing=1.0)


def box(slide, x, y, w, h, lines, fill=None, line=None, line_w=1.75,
        shape=MSO_SHAPE.ROUNDED_RECTANGLE, anchor=MSO_ANCHOR.MIDDLE, **kw):
    """塗り箱の中に直接テキストを入れる（別テキストボックスを重ねない）。"""
    sp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill:
        sp.fill.solid()
        sp.fill.fore_color.rgb = _rgb(fill)
    else:
        sp.fill.background()
    if line:
        sp.line.color.rgb = _rgb(line)
        sp.line.width = Pt(line_w)
    else:
        sp.line.fill.background()
    sp.shadow.inherit = False
    tf = sp.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Inches(0.10)
    tf.margin_right = Inches(0.10)
    tf.margin_top = Inches(0.03)
    tf.margin_bottom = Inches(0.03)
    set_text(tf, lines, **kw)
    return sp


def chip(slide, x, y, lines, fill, size=22, h_line=0.46):
    """解析の位置づけを示す小さな色付きチップ（主解析・副次解析 など）。"""
    w = _lines_width(lines, size) + 0.34
    h = h_line * len(lines) + 0.10
    box(slide, x, y, w, h, [(t, size, WHITE, True) for t in lines], fill=fill,
        align=PP_ALIGN.CENTER, space_after=0, line_spacing=1.0)
    return x + w, h


def arrow(slide, x, y, w, h, color=GREY, shape=MSO_SHAPE.RIGHT_ARROW):
    sp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    sp.fill.solid()
    sp.fill.fore_color.rgb = _rgb(color)
    sp.line.fill.background()
    sp.shadow.inherit = False
    return sp


def down_arrow(slide, x, y, w, h, color=GREY):
    return arrow(slide, x, y, w, h, color, MSO_SHAPE.DOWN_ARROW)


def source(slide, text):
    textbox(slide, 0.55, 6.94, 12.3, 0.45, [text], size=16, color=GREY,
            space_after=0, line_spacing=1.0)


def new_slide(prs, title, chapter=None, notes=""):
    """タイトル＋金下線＋章ナビの共通ヘッダを持つスライドを作る。"""
    check_title(title)
    s = prs.slides.add_slide(prs.slide_layouts[5])   # Title Only
    t = s.shapes.title
    t.left, t.top = Inches(TITLE_X), Inches(TITLE_Y)
    t.width, t.height = Inches(TITLE_W), Inches(TITLE_H)
    tf = t.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = title
    r.font.size = Pt(44)
    r.font.bold = True
    r.font.name = FONT
    r.font.color.rgb = _rgb(GOLD)
    outline_run(r)

    ln = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.52), Inches(SW), Pt(0))
    ln.fill.solid()
    ln.fill.fore_color.rgb = _rgb(GOLD)
    ln.line.color.rgb = _rgb(GOLD)
    ln.line.width = Pt(8)
    ln.shadow.inherit = False

    if chapter:
        for i, ch in enumerate(CHAPTERS):
            cur = ch == chapter
            c = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                   Inches(CHIP_X0 + i * (CHIP_W + CHIP_GAP)), Inches(0.06),
                                   Inches(CHIP_W), Inches(0.64))
            c.fill.solid()
            c.fill.fore_color.rgb = _rgb(TEAL if cur else LGREY)
            c.line.fill.background()
            c.shadow.inherit = False
            ctf = c.text_frame
            ctf.word_wrap = False
            ctf.vertical_anchor = MSO_ANCHOR.MIDDLE
            ctf.margin_left = ctf.margin_right = Inches(0.01)
            cp = ctf.paragraphs[0]
            cp.alignment = PP_ALIGN.CENTER
            cr = cp.add_run()
            cr.text = ch
            cr.font.size = Pt(11)
            cr.font.bold = cur
            cr.font.name = FONT
            cr.font.color.rgb = _rgb(WHITE if cur else DGREY)
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


# ============================================================ 表
def _cell_border(cell, color=GREY, w_pt=0.75):
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        for old in tcPr.findall(qn(tag)):
            tcPr.remove(old)
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        ln = tcPr.makeelement(qn(tag), {"w": str(int(w_pt * 12700)), "cap": "flat",
                                        "cmpd": "sng", "algn": "ctr"})
        fill = ln.makeelement(qn("a:solidFill"), {})
        clr = fill.makeelement(qn("a:srgbClr"), {"val": color})
        fill.append(clr)
        ln.append(fill)
        tcPr.append(ln)


def table(slide, x, y, col_w, rows, pt=22, header=True, aligns=None,
          line_h=None, bolds=None):
    """ネイティブの表。rows[0] は見出し行。セル内の改行は "\\n" で明示する。

    lint は表（GraphicFrame）の中の文字サイズを見ないので、22pt 未満を使う版 B は
    このスクリプトの `--selftest` と `count_small_table_runs` で数える。
    """
    n_row, n_col = len(rows), len(col_w)
    line_h = line_h if line_h else (pt / 72.0 * 1.45 + 0.14)
    heights = [line_h * max(1, max(str(c).count("\n") + 1 for c in r)) for r in rows]
    gf = slide.shapes.add_table(n_row, n_col, Inches(x), Inches(y),
                                Inches(sum(col_w)), Inches(sum(heights)))
    tbl = gf.table
    tbl.first_row = False
    tbl.horz_banding = False
    for j, w in enumerate(col_w):
        tbl.columns[j].width = Inches(w)
    for i, h in enumerate(heights):
        tbl.rows[i].height = Inches(h)
    gf.height = Inches(sum(heights))
    for i, row in enumerate(rows):
        head = header and i == 0
        for j, txt in enumerate(row):
            cell = tbl.cell(i, j)
            cell.margin_left = cell.margin_right = Inches(0.06)
            cell.margin_top = cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = _rgb(BLUE if head else (WHITE if i % 2 else PALE))
            al = PP_ALIGN.CENTER if (head or j > 0) else PP_ALIGN.LEFT
            if aligns and not head:
                al = aligns[j]
            bd = head or bool(bolds and i in bolds)
            set_text(cell.text_frame, [(t, pt, WHITE if head else INK, bd)
                                       for t in str(txt).split("\n")],
                     align=al, space_after=0, line_spacing=1.0)
            _cell_border(cell)
    return gf


def count_small_table_runs(path, limit=22.0):
    """表のセルにある 22pt 未満の run を数える（lint は表を見ないので自前で数える）。"""
    prs = Presentation(path)
    n = 0
    for slide in prs.slides:
        for sp in slide.shapes:
            if not getattr(sp, "has_table", False):
                continue
            for row in sp.table.rows:
                for cell in row.cells:
                    for para in cell.text_frame.paragraphs:
                        for r in para.runs:
                            if r.font.size is not None and r.font.size.pt < limit:
                                n += 1
    return n


# ============================================================ 図（すべてネイティブ図形）
def _bezier(p0, p1, p2, p3, n):
    out = []
    for i in range(1, n + 1):
        t = i / n
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def svg_points(d: str, n: int = 14):
    """SVG の path（M・C・L だけ）を折れ線の点列に開く。図1・図2 の原図から起こす。"""
    toks = d.replace(",", " ").split()
    pts, cur, i, cmd = [], (0.0, 0.0), 0, None
    while i < len(toks):
        tk = toks[i]
        if tk in ("M", "C", "L"):
            cmd, i = tk, i + 1
            continue
        if cmd == "M":
            cur = (float(toks[i]), float(toks[i + 1]))
            pts.append(cur)
            i += 2
        elif cmd == "L":
            cur = (float(toks[i]), float(toks[i + 1]))
            pts.append(cur)
            i += 2
        elif cmd == "C":
            p1 = (float(toks[i]), float(toks[i + 1]))
            p2 = (float(toks[i + 2]), float(toks[i + 3]))
            p3 = (float(toks[i + 4]), float(toks[i + 5]))
            pts += _bezier(cur, p1, p2, p3, n)
            cur = p3
            i += 6
        else:
            raise ValueError(f"未対応のコマンド: {tk}")
    return pts


def svg_map(bbox, rect):
    """SVG 座標 (x0,y0,x1,y1) をスライド上の矩形 (X,Y,W,H) インチに移す関数を返す。"""
    x0, y0, x1, y1 = bbox
    X, Y, W, H = rect
    sx, sy = W / (x1 - x0), H / (y1 - y0)
    return lambda p: (X + (p[0] - x0) * sx, Y + (p[1] - y0) * sy)


def poly(slide, pts, color=INK, width_pt=2.0, dash=None, fill=None):
    """折れ線・多角形をフリーフォームで描く（文字を焼き込まないための素の図形）。"""
    fb = slide.shapes.build_freeform(Inches(pts[0][0]), Inches(pts[0][1]))
    fb.add_line_segments([(Inches(px), Inches(py)) for px, py in pts[1:]],
                         close=bool(fill))
    sp = fb.convert_to_shape()
    if fill:
        sp.fill.solid()
        sp.fill.fore_color.rgb = _rgb(fill)
    else:
        sp.fill.background()
    sp.line.color.rgb = _rgb(color)
    sp.line.width = Pt(width_pt)
    if dash:
        from pptx.enum.dml import MSO_LINE_DASH_STYLE
        sp.line.dash_style = getattr(MSO_LINE_DASH_STYLE, dash)
    sp.shadow.inherit = False
    return sp


def dot(slide, x, y, r=0.075, color=INK, fill=WHITE, width_pt=1.75):
    import math
    pts = [(x + r * math.cos(2 * math.pi * k / 16), y + r * math.sin(2 * math.pi * k / 16))
           for k in range(16)]
    return poly(slide, pts + [pts[0]], color=color, width_pt=width_pt, fill=fill)


def brace(slide, x0, x1, y, drop=0.13, color=INK, width_pt=1.5):
    poly(slide, [(x0, y - drop), (x0, y), (x1, y), (x1, y - drop)],
         color=color, width_pt=width_pt)


def _seg_hits_rect(p0, p1, rect, n=36):
    x0, y0, x1, y1 = rect
    for k in range(n + 1):
        t = k / n
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t
        if x0 <= x <= x1 and y0 <= y <= y1:
            return True
    return False


def clear_label(slide, curves, ax, ay, text, size=22, bold=False, pad=0.04,
                bounds=(0.45, 2.20, 12.88, 4.80)):
    """図の線に重ならない位置にラベルを置く。候補を順に試し、空いた所を採る。

    離れた位置にしか置けないときは細い引き出し線を添える。
    重ならない位置が無ければ組み立てを止める（黙ってずらさない）。
    """
    w = width_in(text, size) + 0.16
    h = (size / 72.0) * 1.9
    for dx, dy in ((0, -0.42), (0, 0.36), (0.50, -0.40), (0.50, 0.40),
                   (-0.50, -0.40), (-0.50, 0.40), (0, -0.80), (0, 0.80),
                   (0.80, -0.60), (-0.80, -0.60), (0.80, 0.60), (-0.80, 0.60)):
        cx, cy = ax + dx, ay + dy
        rect = (cx - w / 2 - pad, cy - h / 2 - pad, cx + w / 2 + pad, cy + h / 2 + pad)
        if (rect[0] < bounds[0] or rect[1] < bounds[1]
                or rect[2] > bounds[2] or rect[3] > bounds[3]):
            continue
        if any(_seg_hits_rect(a, b, rect)
               for pts in curves for a, b in zip(pts, pts[1:])):
            continue
        if abs(dx) > 0.6 or abs(dy) > 0.6:
            ex = min(max(ax, cx - w / 2), cx + w / 2)
            ey = cy + (h / 2 if dy < 0 else -h / 2) if abs(dy) > abs(dx) else cy
            if abs(dy) <= abs(dx):
                ex = cx + (w / 2 if dx < 0 else -w / 2)
            k = 0.11 / max(1e-6, ((ax - ex) ** 2 + (ay - ey) ** 2) ** 0.5)
            poly(slide, [(ex, ey), (ax + (ex - ax) * k, ay + (ey - ay) * k)],
                 color=GREY, width_pt=1.0)
        return label(slide, cx, cy, text, size=size, bold=bold)
    raise RuntimeError(f"ラベルを置く場所が無い: {text}")


# ============================================================ 数式（画像・例外）
_FORMULAS = {
    # 凍結版（analysis/src/pda.py の skew_gaussian・model2 をそのまま写した）
    "eq_skew_g": r"$g(t;\,a,\mu,\sigma,\alpha)\;=\;a\,\exp\!\left(-\frac{z^{2}}{2}\right)"
                 r"\left[\,1+\mathrm{erf}\!\left(\frac{\alpha z}{\sqrt{2}}\right)\right],"
                 r"\qquad z=\frac{t-\mu}{\sigma}$",
    "eq_model2": r"$\hat{y}(t)\;=\;g(t;\,a_{1},\mu_{1},\sigma_{1},\alpha_{1})"
                 r"\;+\;g(t;\,a_{2},\ \mu_{1}+\Delta\mu,\ \sigma_{2},\alpha_{2})$",
    # 第2版の採否（analysis/src/pda2.py の acceptance）
    "eq_wang": r"$\mathrm{NRMSE}=\sqrt{\Sigma\,w\,(y-\hat{y})^{2}\,/\,"
               r"\Sigma\,w\,y^{2}}\,,\quad \mathrm{Errx}=\Sigma\,"
               r"\left|t_{k}-\hat{t}_{k}\right|,\quad \mathrm{Erry}=\Sigma\,"
               r"\left|v_{k}-\hat{v}_{k}\right|$",
    # ガンマ基底（analysis/src/pda2.py の gamma_peak）
    "eq_gamma": r"$g(t)=h\,\exp\!\left[(\alpha-1)(\ln u-\ln r)-\beta\,(u-r)\right],"
                r"\qquad u=t-(t_{p}-r),\qquad \beta=\frac{\alpha-1}{r}$",
}

# ノートに残す文字版（画像に焼いた式と同じもの）
FORMULA_TEXT = {
    "eq_skew_g": "g(t; a, μ, σ, α) ＝ a・exp(−z²/2)・[1 ＋ erf(αz/√2)]、z ＝ (t − μ)/σ",
    "eq_model2": "ŷ(t) ＝ g(t; a₁, μ₁, σ₁, α₁) ＋ g(t; a₂, μ₁ ＋ Δμ, σ₂, α₂)",
    "eq_wang": ("NRMSE ＝ sqrt( Σ w (y − ŷ)² / Σ w y² ) ≤ 0.02、"
                "Errx ＝ 計測した特徴点の時刻と模型の特徴点の時刻の差の絶対値の総和 ≤ 6 ms、"
                "Erry ＝ 同じく振幅の差の絶対値の総和 ≤ 0.01"),
    "eq_gamma": ("g(t) ＝ h・exp[(α − 1)(ln u − ln rise) − β(u − rise)]、"
                 "u ＝ t − (t_p − rise)、β ＝ (α − 1)/rise、u > 0"),
}

_RENDER_PT, _RENDER_DPI = 30.0, 400


def render_formulas(outdir=ASSETS):
    """mathtext で式を PNG にする（白背景・400 dpi）。ファイル名は決め打ち。"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    matplotlib.rcParams["mathtext.fontset"] = "cm"
    os.makedirs(outdir, exist_ok=True)
    made = {}
    for name, tex in _FORMULAS.items():
        path = os.path.join(outdir, name + ".png")
        fig = plt.figure(figsize=(0.02, 0.02))
        fig.text(0, 0, tex, fontsize=_RENDER_PT)
        fig.savefig(path, dpi=_RENDER_DPI, bbox_inches="tight", pad_inches=0.08,
                    facecolor="white")
        plt.close(fig)
        made[name] = path
    return made


def place_formula(slide, name, x, y, max_w, max_h=None):
    """式の画像を置く。max_w に収まるよう等倍で縮める。戻り値は (w, h, 実効pt)。"""
    from PIL import Image
    path = os.path.join(ASSETS, name + ".png")
    with Image.open(path) as im:
        w_in, h_in = im.width / _RENDER_DPI, im.height / _RENDER_DPI
    k = min(1.0, max_w / w_in, (max_h / h_in) if max_h else 1.0)
    slide.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w_in * k))
    return w_in * k, h_in * k, _RENDER_PT * k


# ============================================================ 原稿からノートを引く
JA2 = os.path.join(HERE, "..", "paper2", "v2", "05_draft_ja_v2.md")
JA1 = os.path.join(HERE, "..", "v2", "05_draft_ja_v2.md")


def _paras(path):
    with open(path, encoding="utf-8") as fh:
        txt = fh.read()
    return [p.strip() for p in txt.split("\n\n") if p.strip()]


def para(path, key, extra=0):
    """key を含む段落を（続きの extra 段落とともに）原文のまま返す。"""
    ps = _paras(path)
    for i, p in enumerate(ps):
        if key in p:
            return "\n\n".join(ps[i:i + 1 + extra])
    raise KeyError(f"段落が見つからない: {key} ({os.path.basename(path)})")


def notes(*parts):
    return "\n\n".join(p for p in parts if p)


# 文献番号は英文原稿 v2 の文献表の順（スライド24枚目と同じ）
REF = {
    "charlton": "1）Charlton 2019", "rubins": "2）Rubins 2008", "goswami": "3）Goswami 2010",
    "wang": "4）Wang 2013", "epstein": "5）Epstein 2014", "couceiro": "6）Couceiro 2015",
    "tigges": "7）Tigges 2017", "fleisch": "8）Fleischhauer 2020", "basso": "9）Basso 2024",
    "hellqvist": "10）Hellqvist 2024", "dawber": "11）Dawber 1973",
}

REFS_11 = [
    "1）Charlton PH, et al. Am J Physiol Heart Circ Physiol. 2019;317(5):H1062-H1085.",
    "2）Rubins U. Med Biol Eng Comput. 2008;46(12):1271-1276.",
    "3）Goswami D, et al. Cardiovasc Eng. 2010;10(3):109-117.",
    "4）Wang L, et al. Comput Biol Med. 2013;43(11):1661-1672.",
    "5）Epstein S, et al. Annu Int Conf IEEE Eng Med Biol Soc. 2014;2014:1969-1972.",
    "6）Couceiro R, et al. Physiol Meas. 2015;36(9):1801-1825.",
    "7）Tigges T, et al. Annu Int Conf IEEE Eng Med Biol Soc. 2017;2017:4014-4017.",
    "8）Fleischhauer V, et al. Physiol Meas. 2020;41(9):095009.",
    "9）Basso G, et al. Physiol Meas. 2024;45(11):115006.",
    "10）Hellqvist H, et al. Front Cardiovasc Med. 2024;11:1350726.",
    "11）Dawber TR, et al. Angiology. 1973;24(4):244-255.",
]

# 図1・図2 の原図（docs/manuscript/paper2/figures/*.svg）の path をそのまま写したもの
F1_WAVE_A = ("M 38 232 C 62 230, 78 118, 102 84 C 116 62, 136 68, 152 96 "
             "C 172 130, 188 154, 210 160 C 228 165, 240 142, 258 138 "
             "C 276 134, 296 148, 316 176 C 328 196, 338 220, 346 230")
F1_WAVE_B = ("M 418 232 C 442 230, 458 118, 482 84 C 496 62, 516 68, 532 96 "
             "C 552 130, 568 154, 590 160 C 608 165, 620 142, 638 138 "
             "C 656 134, 676 148, 696 176 C 708 196, 718 220, 726 230")
F1_COMP_B1 = ("M 418 232 C 444 230, 460 116, 486 88 C 508 64, 528 108, 546 152 "
              "C 562 190, 578 216, 594 230")
F1_COMP_B2 = "M 540 232 C 572 230, 600 166, 634 160 C 668 154, 696 190, 722 231"
F2_WAVE_A = ("M 38 222 C 62 220, 78 118, 102 86 C 116 66, 136 72, 152 98 "
             "C 172 130, 190 152, 214 160 C 238 168, 264 174, 290 186 "
             "C 312 197, 332 214, 346 220")
F2_COMP_A1 = ("M 38 222 C 62 220, 78 116, 104 90 C 126 66, 146 108, 164 152 "
              "C 180 190, 196 214, 212 221")
F2_COMP_A2 = ("M 142 222 C 170 220, 190 190, 214 186 C 244 181, 274 199, 302 213 "
              "C 318 219, 334 222, 346 222")
F2_WAVE_B = ("M 418 222 C 442 220, 458 118, 482 86 C 496 66, 516 72, 532 98 "
             "C 552 130, 570 152, 594 160 C 618 168, 644 174, 670 186 "
             "C 692 197, 712 214, 726 220")
F2_COMP_B1 = ("M 418 222 C 440 220, 454 110, 478 84 C 500 58, 518 100, 534 142 "
              "C 548 180, 562 210, 578 221")
F2_COMP_B2 = "M 500 222 C 542 219, 580 180, 624 178 C 664 176, 698 202, 726 221"


# ============================================================ 本体
def build(out_path, variant="A"):
    big = variant == "B"          # 表を 16〜18pt で詰める版
    t_pt = 18 if big else 22      # 表1・2・4 の文字
    t3_pt = 16 if big else 22     # 表3 の文字（12 行すべて載せる版で使う）
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(SW), Inches(SH)
    render_formulas()

    # ------------------------------------------------------------ 1 表紙
    s = prs.slides.add_slide(prs.slide_layouts[6])
    tb = textbox(s, TITLE_X, TITLE_Y, 12.35, 0.95,
                 [("成分波分解の血管指標は真値を追わない", 44, GOLD, True)],
                 space_after=0, line_spacing=1.0)
    for p in tb.text_frame.paragraphs:
        for r in p.runs:
            outline_run(r)
    ln = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.52), Inches(SW), Pt(0))
    ln.fill.solid()
    ln.fill.fore_color.rgb = _rgb(GOLD)
    ln.line.color.rgb = _rgb(GOLD)
    ln.line.width = Pt(8)
    ln.shadow.inherit = False
    textbox(s, 0.9, 1.95, 9.6, 1.3, [
        ("光電容積脈波の成分波分解から得た血管指標は", 28, INK, False),
        ("大動脈脈波伝播速度も末梢血管抵抗も追わない", 28, INK, False)],
        space_after=2, line_spacing=1.15)
    box(s, 0.9, 3.45, 11.2, 0.85, [
        ("同一波形の特徴点法との対比・仮想被験者 4,374 名・事前登録", 24, WHITE, True)],
        fill=BLUE, align=PP_ALIGN.CENTER, space_after=0)
    textbox(s, 0.9, 4.70, 9.0, 1.35, [
        ("長崎県五島中央病院麻酔科", 26, INK, False),
        ("川副靖晃", 32, INK, True)], space_after=4, line_spacing=1.15)
    textbox(s, 0.9, 6.25, 6.0, 0.55, [("2026年9月", 24, DGREY, False)],
            space_after=0, line_spacing=1.0)
    s.notes_slide.notes_text_frame.text = notes(
        "【表題】" + para(JA2, "光電容積脈波の成分波分解から得た血管指標は大動脈脈波伝播速度も"),
        "【所属】長崎県五島中央病院麻酔科　川副靖晃",
        para(JA2, "目的：指先の光電容積脈波から血管の指標を作る方法には二つの系統がある"))

    # ------------------------------------------------------------ 2 背景
    s = new_slide(prs, "研究全体の前提", "背景", notes=notes(
        "（論文1〈はじめに〉より。本研究はこの前提そのものを仮想被験者で検証する側にあたる）",
        para(JA1, "非侵襲の連続CO推定は周術期医療の未充足の課題", extra=3)))
    box(s, 2.05, 1.82, 9.2, 0.72,
        [("脈波伝播時間（PWTT）から心拍出量を推定する", 26, WHITE, True)], fill=BLUE)
    down_arrow(s, 6.37, 2.62, 0.6, 0.26)
    box(s, 1.30, 2.96, 10.7, 0.72,
        [("較正定数は年齢・性別・身長・体重で決まり、症例中は固定", 24, WHITE, True)], fill=TEAL)
    down_arrow(s, 6.37, 3.76, 0.6, 0.26)
    box(s, 1.15, 4.10, 11.0, 0.72,
        [("誤差は血管状態（体血管抵抗・動脈エラスタンス）と関連する", 24, WHITE, True)], fill=VERM)
    down_arrow(s, 6.37, 4.90, 0.6, 0.26)
    box(s, 2.20, 5.24, 8.9, 0.90,
        [("案：脈波の血管指標で較正定数を補正する", 28, RED, True)], fill=None, line=RED)
    textbox(s, 1.15, 6.28, 11.0, 0.50,
            [("この案が立つ前提を、真値が分かっている集団で確かめる", 22, INK, False)],
            space_after=0, line_spacing=1.0)
    source(s, "論文1（VitalDB 862例・事前登録）の〈はじめに〉より")

    # ------------------------------------------------------------ 3 背景（図1）
    s = new_slide(prs, "血管指標の2系統", "背景", notes=notes(
        para(JA2, "指尖の光電容積脈波は麻酔中のほぼ全例で連続記録されており"),
        "図1（figures/fig1_two_families.svg）をスライド上で描き直したもの。"
        "a は特徴点法、b は分解法。実線は計測した拍、破線は当てはめた成分。",
        "ΔT_PDA は2成分のピーク時刻の差、RI_PDA は2成分のピーク高さの比である。"
        "RI_PDA は振幅母数の比 a₂/a₁ ではない。"))
    textbox(s, 0.55, 1.72, 5.55, 0.48, [("a　特徴点法", 24, BLUE, True)],
            space_after=0, line_spacing=1.0)
    textbox(s, 6.90, 1.72, 5.55, 0.48, [("b　分解法", 24, VERM, True)],
            space_after=0, line_spacing=1.0)
    ma = svg_map((28, 58, 350, 278), (0.55, 2.75, 5.55, 2.20))
    mb = svg_map((408, 58, 730, 278), (6.90, 2.75, 5.55, 2.20))
    curves = []
    for m, off, wave, col in ((ma, 0, F1_WAVE_A, BLUE), (mb, 380, F1_WAVE_B, VERM)):
        pts = [m(p) for p in svg_points(wave)]
        poly(s, pts, color=col, width_pt=2.6)
        poly(s, [m((28 + off, 232)), m((350 + off, 232))], color=GREY, width_pt=1.0)
        curves.append(pts)
        curves.append([m((28 + off, 232)), m((350 + off, 232))])
    for dd in (F1_COMP_B1, F1_COMP_B2):
        pts = [mb(p) for p in svg_points(dd)]
        poly(s, pts, color=DGREY, width_pt=1.6, dash="DASH")
        curves.append(pts)
    for m, drops in ((ma, ((102, 84), (258, 138))), (mb, ((486, 88), (634, 160)))):
        for px, py in drops:
            pts = [m((px, py + 6)), m((px, 258))]
            poly(s, pts, color=GREY, width_pt=0.75, dash="DASH")
            curves.append(pts)
    marks = ((ma, ((102, 84), (210, 160), (258, 138)), ("S", "切痕", "D")),
             (mb, ((486, 88), (634, 160)), ("g1", "g2")))
    for m, pts, labs in marks:
        for (px, py) in pts:
            X, Y = m((px, py))
            dot(s, X, Y)
            r = 0.075
            curves.append([(X - r, Y - r), (X + r, Y - r), (X + r, Y + r),
                           (X - r, Y + r), (X - r, Y - r)])
    for m, pts, labs in marks:
        for (px, py), tx in zip(pts, labs):
            X, Y = m((px, py))
            clear_label(s, curves, X, Y, tx)
    for m, x0, x1 in ((ma, 102, 258), (mb, 486, 634)):
        y = m((0, 264))[1]
        brace(s, m((x0, 0))[0], m((x1, 0))[0], y)
        label(s, (m((x0, 0))[0] + m((x1, 0))[0]) / 2, y + 0.30, "ΔT", bold=True)
    poly(s, [(6.62, 1.80), (6.62, 5.30)], color=LGREY, width_pt=1.5)
    textbox(s, 0.55, 5.45, 12.25, 1.30, [
        ("ΔT　2つのピークの時刻の差", 22, INK, False),
        ("RI　2つのピークの高さの比", 22, INK, False),
        ("重複切痕　収縮期ピークの後の小さな切れ込み", 22, INK, False)],
        space_after=2, line_spacing=1.05)
    source(s, "図1 を描き直したもの。実線＝計測した拍、破線＝当てはめた成分 g1・g2")

    # ------------------------------------------------------------ 4 背景
    s = new_slide(prs, "なぜ分解法・なぜ2成分", "背景", notes=notes(
        para(JA2, "分解法が提起されたのは特定の問題に対してである"),
        "2成分とした理由（論文1〈方法〉より）：" + para(JA1, "歪みを許すのは、前進波"),
        "歪みガウス基底の原典は Basso 2024、2カーネルの根拠は Fleischhauer 2020 である。"
        "凍結版は論文1（VitalDB 862例）のために凍結した実装で、その後変更していない。"))
    for i, (ttl, body, col) in enumerate((
            ("① 切痕が消える", ["動脈硬化で重複切痕は", "平坦化し、やがて消失", "特徴点法はここで破綻",
                            "分解法は値を返す", "2,3,6）"], VERM),
            ("② 2成分の根拠", ["分解アルゴリズムの", "系統的比較で、2成分の", "模型が雑音と体動に",
                           "最も頑健であった", "8）"], BLUE),
            ("③ 歪みガウス", ["左右非対称の釣り鐘型", "立ち上がりが急で", "下降が緩い波に合う",
                          "", "9）"], TEAL))):
        x = 0.55 + i * 4.05
        box(s, x, 1.80, 3.80, 0.62, [(ttl, 24, WHITE, True)], fill=col,
            align=PP_ALIGN.CENTER, space_after=0)
        textbox(s, x + 0.05, 2.52, 3.70, 2.10,
                [(t, 22, INK, t.endswith("）")) for t in body],
                space_after=2, line_spacing=1.1)
    box(s, 1.15, 4.72, 11.0, 1.05, [
        ("臨床研究のために実装を凍結した", 24, WHITE, True),
        ("本研究はその凍結版を検証する", 24, WHITE, True)], fill=DGREY, space_after=2)
    box(s, 1.15, 5.90, 11.0, 0.80,
        [("問うのは、返ってくる値が真値を追うかである", 26, RED, True)], fill=None, line=RED)
    source(s, "2,3,6）利点の報告　8）2成分の根拠（Fleischhauer 2020）　9）歪みガウス（Basso 2024）")

    # ------------------------------------------------------------ 5 背景
    s = new_slide(prs, "検証されていないこと", "背景", notes=notes(
        para(JA2, "しかし示されてきたことと妥当であることは同じではない", extra=1)))
    box(s, 0.55, 1.80, 6.40, 0.62, [("評価されてきたこと", 24, WHITE, True)], fill=BLUE,
        align=PP_ALIGN.CENTER, space_after=0)
    textbox(s, 0.65, 2.52, 6.20, 2.10, [
        ("・当てはまりの良さ 7）", 22, INK, False),
        ("　補正赤池情報量規準", 22, DGREY, False),
        ("・残差平方和と初期値への鈍感さ 9）", 22, INK, False),
        ("・雑音と体動への頑健性 8）", 22, INK, False),
        ("・特徴点の位置を再現するか 4）", 22, INK, False)],
        space_after=3, line_spacing=1.1)
    box(s, 7.20, 1.80, 5.60, 0.62, [("評価されていないこと", 24, WHITE, True)], fill=VERM,
        align=PP_ALIGN.CENTER, space_after=0)
    textbox(s, 7.30, 2.52, 5.40, 1.10, [
        ("・真値に照らして", 22, INK, False),
        ("　妥当かどうか", 22, INK, True)], space_after=3, line_spacing=1.1)
    box(s, 0.55, 4.90, 12.25, 0.95, [
        ("同定不能　同じ波形をほぼ同じ精度で再現する母数の組が", 24, WHITE, False),
        ("一つに決まらない", 24, WHITE, True)], fill=DGREY, space_after=0)
    textbox(s, 0.55, 6.05, 12.25, 0.75, [
        ("残差に基づく規準は、どの解に落ちてもほとんど変わらない", 24, INK, True)],
        space_after=0, line_spacing=1.1)
    source(s, "4）Wang 2013　7）Tigges 2017　8）Fleischhauer 2020　9）Basso 2024")

    # ------------------------------------------------------------ 6 背景
    s = new_slide(prs, "目的と問い", "背景", notes=notes(
        para(JA2, "この二つを分けるには真値を知る必要がある"),
        para(JA2, "そこで我々は、判定規準を事前に固定したうえで")))
    box(s, 0.55, 1.85, 12.25, 1.35, [
        ("真値が分かっている集団で", 24, WHITE, False),
        ("分解法の ΔT・RI は大動脈脈波伝播速度と末梢血管抵抗を追うか", 26, WHITE, True)],
        fill=BLUE, space_after=4)
    box(s, 0.55, 3.45, 12.25, 1.00, [
        ("同一の波形から直接読んだ特徴点法と比べてどうか", 26, WHITE, True)], fill=VERM)
    box(s, 0.55, 4.70, 12.25, 1.00, [
        ("判定規準は解析の実行前に文書に固定した（事前登録）", 26, RED, True)],
        fill=None, line=RED)
    textbox(s, 0.55, 5.95, 12.25, 0.80, [
        ("大動脈脈波伝播速度はモデルの入力、末梢血管抵抗は入力から決まる量", 22, INK, False)],
        space_after=0, line_spacing=1.1)
    source(s, "1）Charlton 2019（Pulse Wave Database）")

    # ------------------------------------------------------------ 7 方法
    s = new_slide(prs, "Pulse Wave Database", "方法", notes=notes(
        para(JA2, "データ源　Pulse Wave Databaseは動脈網の1次元流体力学モデル"),
        para(JA2, "この基盤が本問いに適する理由は二つある")))
    textbox(s, 0.55, 1.80, 2.3, 0.50, [("年齢層", 24, INK, True)],
            space_after=0, line_spacing=1.0)
    for i, ag in enumerate(("25歳", "35歳", "45歳", "55歳", "65歳", "75歳")):
        box(s, 2.85 + i * 1.10, 1.76, 1.00, 0.56, [(ag, 22, WHITE, True)], fill=TEAL,
            align=PP_ALIGN.CENTER, space_after=0)
    textbox(s, 0.55, 2.55, 6.0, 0.50, [("振った因子（それぞれ 3 水準）", 24, INK, True)],
            space_after=0, line_spacing=1.0)
    for i, fc in enumerate(("大動脈径", "心拍数", "駆出時間", "平均血圧", "脈波伝播速度", "1回拍出量")):
        box(s, 0.55 + (i % 3) * 4.05, 3.10 + (i // 3) * 0.72, 3.80, 0.60,
            [(fc, 22, WHITE, True)], fill=BLUE, align=PP_ALIGN.CENTER, space_after=0)
    box(s, 1.90, 4.62, 9.5, 0.80, [
        ("729名（3水準の全組合せ）× 6層 ＝ 4,374名", 28, WHITE, True)], fill=DGREY)
    textbox(s, 0.55, 5.60, 12.25, 1.20, [
        ("大動脈脈波伝播速度　モデルの入力そのもの", 22, INK, False),
        ("末梢血管抵抗　入力から決まる（平均血圧 ≒ 末梢血管抵抗 × 心拍出量）", 22, INK, False)],
        space_after=3, line_spacing=1.1)
    source(s, "1）Charlton 2019（動脈網の1次元血流モデル・仮想被験者 4,374名）")

    # ------------------------------------------------------------ 8 方法
    s = new_slide(prs, "分解法・凍結版", "方法", notes=notes(
        para(JA2, "分解法の指標　本研究の主たる対象は"),
        para(JA2, "第2成分の位置は第1成分からのオフセットΔμで持たせ"),
        "式（画像で置いたものの文字版）:",
        FORMULA_TEXT["eq_skew_g"], FORMULA_TEXT["eq_model2"],
        "母数の探索範囲（analysis/src/pda.py fit_beat）: a₁ 0.05〜2.50、"
        "μ₁ 0.02〜max(0.60T, t_pk＋0.05) s、σ₁ 0.015〜0.30 s、α₁ 0〜8、a₂ 0.02〜2.00、"
        "Δμ 0.08〜min(0.60, 0.85T) s、σ₂ 0.015〜0.35 s、α₂ 0〜8（T は拍長、"
        "t_pk は正規化した拍の最大値の時刻）。"))
    place_formula(s, "eq_skew_g", 1.30, 1.76, 10.6)
    place_formula(s, "eq_model2", 1.30, 2.70, 10.6)
    textbox(s, 0.55, 3.45, 12.25, 3.05, [
        ("探索範囲　Δμ 0.08〜0.60 s、α 0〜8　母数 8 個・初期値 8 点", 22, INK, False),
        ("信頼領域反射法による非線形最小二乗（残差二乗和が最小の解を採る）", 22, INK, False),
        ("収束検算　次のいずれかに当たる解は棄却する", 22, BLUE, True),
        ("① 母数が探索範囲の境界から 0.001 以内（歪度の下限 0 は除く）", 22, INK, False),
        ("② 2成分のピーク高さの小さい方が 0.02 未満", 22, INK, False),
        ("③ 競合解：残差 1.15 倍以内・Δμ 差 0.03 s 以上・RI 差 0.08 以上", 22, INK, False),
        ("ΔT ＝ 2成分のピーク時刻の差、RI ＝ ピーク高さの比", 22, VERM, True),
    ], space_after=2, line_spacing=1.1)
    source(s, "論文1（VitalDB 862例）のために凍結した実装。ピークは 4,000 点に離散化して数値的に求める")

    # ------------------------------------------------------------ 9 方法
    s = new_slide(prs, "分解法・第2版", "方法", notes=notes(
        para(JA2, "波形の扱い　指尖光電容積脈波を元の標本化周波数500 Hz"),
        "式（画像で置いたものの文字版）:",
        FORMULA_TEXT["eq_wang"], FORMULA_TEXT["eq_gamma"],
        "重み W_KEY ＝ 20（特徴点の周囲。Wang は 1〜100 を探索するので既定は中間）、"
        "低域通過 18 Hz、足を探す範囲は拍の両端それぞれ 8%、ΔT の標準誤差の上限 20 ms、"
        "競合解の残差の許容 1.15 倍（analysis/src/pda2.py の定数）。"))
    textbox(s, 0.55, 1.76, 12.25, 2.65, [
        ("目的　陰性が凍結版の実装に固有かを確かめる（文献5編で作り直した）", 22, INK, False),
        ("前処理　18 Hz 4次 Butterworth 零位相・両端 8% の足で直線基線", 22, INK, False),
        ("特徴点の周囲に重みを置く（重み 20）・型1 の拍のみに規準を当てた", 22, INK, False),
        ("採否は Wang の規準 4）　当てはまりではなく特徴点の位置で決める", 22, BLUE, True),
        ("ΔT の標準誤差が 20 ms を超える当てはめは採用しない", 22, INK, False),
        ("基底は歪みガウスとガンマ　判定は採否を無視した全例（C 段）で読む", 22, VERM, True),
    ], space_after=2, line_spacing=1.1)
    place_formula(s, "eq_wang", 0.70, 4.50, 11.6)
    place_formula(s, "eq_gamma", 0.70, 5.38, 11.6)
    textbox(s, 0.55, 6.05, 12.25, 0.55, [
        ("r ＝ 立ち上がり時間、α ＝ 形状、t_p ＝ ピーク時刻", 22, DGREY, False)],
        space_after=0, line_spacing=1.0)
    source(s, "4）Wang 2013（採否）　9）Basso 2024　7）Tigges 2017（ガンマ）。定数は analysis/src/pda2.py")

    # ------------------------------------------------------------ 10 方法
    s = new_slide(prs, "特徴点法と早期振幅比", "方法", notes=notes(
        para(JA2, "特徴点法の指標　収縮期ピーク、重複切痕、拡張期ピークを波形上で同定した"),
        para(JA2, "早期振幅比　2次微分の最初の谷の時刻をt_b"),
        para(JA2, "なお本稿では第2成分を反射波とは呼ばない")))
    box(s, 0.55, 1.78, 12.25, 1.75, [
        ("特徴点法（同一の波形から直接読む）", 24, WHITE, True),
        ("ΔT ＝ 拡張期ピーク時刻 − 収縮期ピーク時刻", 22, WHITE, False),
        ("RI ＝ 拡張期ピーク高さ ÷ 収縮期ピーク高さ", 22, WHITE, False)],
        fill=BLUE, space_after=3, anchor=MSO_ANCHOR.MIDDLE)
    box(s, 0.55, 3.70, 12.25, 1.55, [
        ("早期振幅比（上行脚のみ・当てはめを伴わない）", 24, WHITE, True),
        ("Am_b/Am_p1 ＝ y(t_b) ÷ y(t_p1)　t_p1 ＝ t_b − y′(t_b) ÷ y″(t_b)", 22, WHITE, False)],
        fill=TEAL, space_after=3)
    box(s, 0.55, 5.42, 12.25, 1.20, [
        ("切痕が無く下降脚に変曲点がある型では", 22, INK, False),
        ("拡張期ピークの代わりに変曲点を用いた 11）", 22, INK, True)],
        fill=PALE, line=GREY, space_after=2)
    source(s, "1）Charlton 2019（同梱の特徴点由来指標）　10）Hellqvist 2024（早期振幅比）　11）Dawber 1973（型）")

    # ------------------------------------------------------------ 11 方法
    s = new_slide(prs, "解析計画（事前登録）", "方法", notes=notes(
        para(JA2, "事前に固定した判定規準　規準は解析用スクリプトを"),
        para(JA2, "陰性を確認する解析　陰性の代替説明に対応する3つの確認"),
        para(JA2, "記述的解析　各因子が指標をどれだけ動かすか"),
        para(JA2, "ソフトウェアと再現性　Python 3.9.6")))
    plan = [
        (0.55, 6.30, TEAL, ["陽性対照"],
         ["同梱の脈波到達時間 × 大動脈PWV", "0.5 以上でなければ表を読まない"]),
        (0.55, 6.30, BLUE, ["主解析"],
         ["分解法 ΔT × 大動脈PWV（負）", "分解法 RI × 末梢血管抵抗（正）"]),
        (0.55, 6.30, BLUE, ["プライマリーアウトカム"],
         ["年齢層内 Spearman |ρ| の6層中央値", "成立＝0.30 以上・全6層で予測の符号"]),
        (7.00, 5.90, DGREY, ["対比"], ["同一の波形の特徴点法"]),
        (7.00, 5.90, VERM, ["副次解析"], ["第2版・基底12条件・公表6条件", "閾値の感度"]),
        (7.00, 5.90, VERM, ["セカンダリーアウトカム"], ["主解析と同じ統計量"]),
        (7.00, 5.90, GREY, ["記述"], ["主効果・1因子掃引・波形の型"]),
    ]
    ys = {0.55: 1.74, 7.00: 1.74}
    for x, w, col, chips, lines in plan:
        y = ys[x]
        chip(s, x, y, chips, col, h_line=0.42)
        textbox(s, x + 0.08, y + 0.58, w - 0.16, 0.46 * len(lines) + 0.08,
                [(t, 22, INK, False) for t in lines], space_after=1, line_spacing=1.08)
        ys[x] = y + 0.58 + 0.46 * len(lines) + 0.14
    source(s, "規準は実行前に日付入りの文書に固定し、実行後に変更していない（doi:10.5281/zenodo.22676038）")

    # ------------------------------------------------------------ 12 結果
    s = new_slide(prs, "陽性対照と主解析", "結果", notes=notes(
        para(JA2, "陽性対照　データベースに同梱された脈波到達時間"),
        para(JA2, "主要な対比　凍結版の分解法によるΔTと大動脈脈波伝播速度"),
        "表1（上段）: 陽性対照 0.571（6/6）合格。分解法・凍結版（歪みガウス2成分）"
        "ΔT × 大動脈PWV 0.223（6/6）、RI × 末梢血管抵抗 0.207（5/6）、判定 不成立。"))
    x2, _ = chip(s, 0.55, 1.74, ["陽性対照"], TEAL)
    chip(s, x2 + 0.18, 1.74, ["主解析"], BLUE)
    table(s, 0.42, 2.45, [4.6, 3.2, 3.2, 1.5], [
        ["指標の作り方", "ΔT × 大動脈PWV", "RI × 末梢血管抵抗", "判定"],
        ["陽性対照\n同梱の脈波到達時間", "0.571（6/6）", "─", "合格"],
        ["分解法・凍結版\n（歪みガウス2成分）", "0.223（6/6）", "0.207（5/6）", "不成立"],
    ], pt=t_pt, line_h=0.60 if big else 0.58)
    box(s, 0.55, 5.60, 12.25, 1.00, [
        ("分解法の ΔT・RI はいずれも規準（0.30 以上）に達しない", 26, RED, True)],
        fill=None, line=RED)
    source(s, "表1 上段。|ρ| は年齢層内 Spearman 順位相関の6層中央値。括弧は予測の符号を持った層の数")

    # ------------------------------------------------------------ 13 結果
    s = new_slide(prs, "特徴点法との対比", "結果", notes=notes(
        para(JA2, "同一の波形から特徴点法で得た指標は"),
        para(JA2, "決定的なのは、同一の被験者の同一の波形に"),
        "表1（下段）: 特徴点法（同一の波形）ΔT 0.710（6/6）・RI 0.504（6/6）成立。"
        "早期振幅比 Am_b/Am_p1 0.836（6/6）成立（RI に相当する量は未検証）。"
        "同じ規準を他の特徴点由来指標に当てると、スティフネス指標 0.710・"
        "2次微分の加齢指数 0.885 が成立し、増大係数 0.143 は不成立。"))
    chip(s, 0.55, 1.74, ["対比"], BLUE)
    table(s, 0.42, 2.45, [4.6, 3.2, 3.2, 1.5], [
        ["指標の作り方", "ΔT × 大動脈PWV", "RI × 末梢血管抵抗", "判定"],
        ["特徴点法（同一の波形）", "0.710（6/6）", "0.504（6/6）", "成立"],
        ["早期振幅比 Am_b/Am_p1", "0.836（6/6）", "未検証", "成立"],
        ["参照：分解法・凍結版", "0.223（6/6）", "0.207（5/6）", "不成立"],
    ], pt=t_pt, line_h=0.60 if big else 0.58, bolds={1, 2})
    box(s, 0.55, 5.15, 12.25, 1.00, [
        ("情報は波形の中にある。限界は取り出し方の側にある", 26, WHITE, True)], fill=BLUE)
    textbox(s, 0.55, 6.30, 12.25, 0.50, [
        ("同じ波形・同じ真値・同じ層で、取り出し方だけを変えた対比", 22, INK, False)],
        space_after=0, line_spacing=1.0)
    source(s, "表1 下段。早期振幅比は上行脚のみを用い、当てはめを伴わない（10）Hellqvist 2024）")

    # ------------------------------------------------------------ 14 結果
    s = new_slide(prs, "副次1：第2版", "結果", notes=notes(
        para(JA2, "主要な対比　凍結版の分解法によるΔTと大動脈脈波伝播速度"),
        "表1（第2版の2行）: 歪みガウス 採択 2/4,374、A・B は判定不能、C 0.167 / "
        "C 0.354（3/6）、判定 不成立。ガンマ 採択 103、A 0.798（3/4 層）・C 0.556 / "
        "A 0.609（4/4）・C 0.280、判定 不成立。"))
    x2, _ = chip(s, 0.55, 1.74, ["副次解析"], VERM)
    chip(s, x2 + 0.18, 1.74, ["セカンダリーアウトカム"], VERM)
    table(s, 0.52, 2.45, [2.6, 2.5, 3.8, 3.4], [
        ["第2版の経路", "採択", "ΔT × 大動脈PWV", "RI × 末梢血管抵抗"],
        ["歪みガウス", "2/4,374", "C 0.167", "C 0.354（3/6）"],
        ["ガンマ", "103", "A 0.798（3/4層）\nC 0.556", "A 0.609（4/4）\nC 0.280"],
        ["採否の規準を\nすべて外す", "77.5%\n91.9%", "0.054（歪みガウス）\n0.554（ガンマ）",
         "─\n0.286（ガンマ）"],
    ], pt=t_pt, line_h=0.58 if big else 0.56)
    box(s, 0.55, 6.00, 12.25, 0.80, [
        ("いずれも規準に達しない。採否の閾値の産物ではない", 26, RED, True)],
        fill=None, line=RED)
    source(s, "表1。A＝各手法が採択した拍、C＝採否を無視した全例。第2版の判定は C 段で読む")

    # ------------------------------------------------------------ 15 結果
    t3_rows = [
        ["歪みガウス（凍結版）", "2", "0.0%", "0.0212", "2%", "0.14（2/4）"],
        ["ガウス（歪みなし）", "2", "0.0%", "0.0491", "4%", "0.54（4/4）"],
        ["ガンマ（凍結の探索範囲）", "3", "15.3%", "0.0071", "93%", "0.56（4/4）"],
        ["ガンマ（広い探索範囲）", "3", "10.2%", "0.0068", "89%", "0.55（4/4）"],
    ]
    t3_all = [
        ["歪みガウス α∈[0,8]（凍結版）", "2", "0.0%", "0.0212", "2%", "0.14（2/4）"],
        ["同", "3", "2.0%", "0.0110", "0%", "0.08（4/4）"],
        ["ガウス（歪みなし）", "2", "0.0%", "0.0491", "4%", "0.54（4/4）"],
        ["同", "3", "0.0%", "0.0191", "86%", "0.55（3/4）"],
        ["同", "4", "1.0%", "0.0145", "94%", "0.28（3/4）"],
        ["同", "5", "1.0%", "0.0084", "92%", "0.52（3/4）"],
        ["歪みガウス α∈[−8,8]（Basso 式）", "2", "0.0%", "0.0212", "2%", "0.14（2/4）"],
        ["同", "3", "2.0%", "0.0111", "0%", "0.12（3/4）"],
        ["ガンマ（凍結の探索範囲）", "3", "15.3%", "0.0071", "93%", "0.56（4/4）"],
        ["同", "4", "22.4%", "0.0051", "99%", "0.35（3/4）"],
        ["ガンマ（広い探索範囲）", "3", "10.2%", "0.0068", "89%", "0.55（4/4）"],
        ["同", "4", "31.6%", "0.0047", "99%", "0.38（3/4）"],
    ]
    s = new_slide(prs, "副次2：基底12条件", "結果", notes=notes(
        para(JA2, "陰性は実装、基底、公表条件のいずれにも由来しない"),
        "表3（12 行すべて。版 A では主要 4 行のみを載せた）:\n" + "\n".join(
            "｜".join(r) for r in t3_all),
        "表3 の列は 基底・成分・Wang 通過・Errx 中央値[ms]・NRMSE 中央値・"
        "母数が境界にある割合・ΔT × PWV |ρ|。Errx 中央値[ms] は上から 40, 24, 30, 14, 15, "
        "13, 40, 23, 12, 10, 12, 8。|ρ| は全例（採否を無視）の年齢層内中央値、"
        "括弧は予測の符号を持った層の数。対象は 120 名から取った切痕のある 98 拍で、"
        "層は 8 拍以上の 4 層である。"))
    x2, _ = chip(s, 0.44, 1.70, ["副次解析"], VERM)
    chip(s, x2 + 0.18, 1.70, ["事後"], RED)
    textbox(s, 3.80, 1.74, 9.0, 0.50, [
        ("当てはまりが良いほど真値との相関は下がる", 24, RED, True)],
        space_after=0, line_spacing=1.0)
    if big:
        table(s, 0.45, 2.30, [4.5, 0.75, 1.45, 1.45, 1.90, 2.35],
              [["基底", "成分", "Wang 通過", "NRMSE", "境界にある割合", "ΔT × PWV の |ρ|"]]
              + t3_all, pt=t3_pt, line_h=0.345)
    else:
        table(s, 0.30, 2.30, [4.3, 0.9, 1.4, 1.35, 2.55, 2.2],
              [["基底", "成分", "Wang\n通過", "NRMSE\n中央値", "母数が\n境界にある割合",
                "ΔT × PWV\nの |ρ|"]] + t3_rows, pt=t3_pt, line_h=0.58)
        textbox(s, 0.55, 5.95, 12.25, 0.95, [
            ("歪みを外した素朴な2ガウスが最もよく追い、当てはまりは最も悪い", 22, INK, False),
            ("成分を増やすと当てはまりは上がり、真値への追従は下がる", 22, INK, False)],
            space_after=2, line_spacing=1.1)
    source(s, "表3（探索・事後）。PWV は大動脈脈波伝播速度。対象は切痕のある 98 拍・4 層")

    # ------------------------------------------------------------ 16 結果
    s = new_slide(prs, "副次3：公表6条件", "結果", notes=notes(
        para(JA2, "陰性は実装、基底、公表条件のいずれにも由来しない"),
        "表4: Tigges 2017（推奨の Gamma M=3）ΔT 0.578（6/6）。"
        "Fleischhauer 2020（2核）0.505（5/6）/ RI 0.314（5/6）。"
        "Couceiro 2015 0.500（6/6）/ R1_d 0.585（6/6）。Wang 2013（全例）0.457（5/6）。"
        "Basso 2024（L=3）RI 0.314（6/6）。Goswami 2010 RI 0.343（5/6）。"
        "参照（同一集団の同梱の特徴点由来）ΔT 0.705・RI 0.501。"
        "対象は系統的に選んだ 624 名。6層の規準はこの部分集合には当てていない。"))
    x2, _ = chip(s, 0.42, 1.70, ["副次解析"], VERM)
    chip(s, x2 + 0.18, 1.70, ["事後"], RED)
    textbox(s, 3.80, 1.74, 9.0, 0.50, [
        ("最良は 0.578。特徴点法の 0.705 に及ばない", 24, RED, True)],
        space_after=0, line_spacing=1.0)
    table(s, 0.42, 2.30, [4.7, 3.9, 3.9], [
        ["条件の出どころ", "ΔT × 大動脈PWV", "RI × 末梢血管抵抗"],
        ["Tigges 2017（Gamma M=3）", "0.578（6/6）", "─"],
        ["Fleischhauer 2020（2核）", "0.505（5/6）", "0.314（5/6）"],
        ["Couceiro 2015", "0.500（6/6）", "R1_d 0.585（6/6）"],
        ["Wang 2013（全例）", "0.457（5/6）", "─"],
        ["Basso 2024（L=3）", "─", "0.314（6/6）"],
        ["Goswami 2010", "─", "0.343（5/6）"],
        ["参照：同梱の特徴点由来", "0.705", "0.501"],
    ], pt=t_pt, line_h=0.55, bolds={7})
    source(s, "表4（探索・事後）。対象は系統的に選んだ 624 名。R1_d の行は事前規準では判定に採らない")

    # ------------------------------------------------------------ 17 結果
    s = new_slide(prs, "何に反応するか", "結果", notes=notes(
        para(JA2, "分解法由来の指標が応答する範囲"),
        para(JA2, "応答は単調でない"),
        para(JA2, "波形の型と真の伝播時間"),
        "表2（括弧内はその因子と指標の年齢層内 Spearman 順位相関）: "
        "大動脈径 特徴点法ΔT −9.4 / 分解法ΔT −12.6（−0.37）/ 分解法RI +33.2（+0.30）/ "
        "早期振幅比 +2.0。心拍数 −2.6 / −10.9（−0.54）/ −40.3（−0.37）/ +4.0。"
        "駆出時間 +4.6 / +0.7（+0.09）/ +3.2（−0.10）/ −1.1。"
        "平均血圧 −15.1 / −7.7（−0.09）/ +24.2（−0.00）/ −4.0。"
        "脈波伝播速度 −31.2 / −17.0（−0.26）/ +33.7（−0.17）/ −7.1。"
        "1回拍出量 +15.9 / −4.1（+0.05）/ +21.6（−0.05）/ −0.2。",
        "表2b 1因子掃引（他の因子は基準値・年齢層の中央値）: 脈波伝播速度 ΔT 332.3 / "
        "352.8 / 251.2、RI 0.325 / 0.254 / 0.647。心拍数 ΔT 382.5 / 352.8 / 321.6。"
        "大動脈径 ΔT 353.6 / 352.8 / 332.1。駆出時間 ΔT 341.2 / 352.8 / 362.9。"
        "平均血圧 ΔT 337.2 / 352.8 / 348.7。1回拍出量 ΔT 339.5 / 352.8 / 356.7。"))
    chip(s, 0.75, 1.70, ["記述"], GREY)
    textbox(s, 2.55, 1.74, 10.2, 0.50, [
        ("ΔT を動かすのは脈波伝播速度だけではない", 24, RED, True)],
        space_after=0, line_spacing=1.0)
    t2_head = ["因子", "分解法 ΔT", "分解法 RI", "特徴点法 ΔT"]
    t2 = [
        ["大動脈径", "−12.6（−0.37）", "+33.2（+0.30）", "−9.4"],
        ["心拍数", "−10.9（−0.54）", "−40.3（−0.37）", "−2.6"],
        ["駆出時間", "+0.7（+0.09）", "+3.2（−0.10）", "+4.6"],
        ["平均血圧", "−7.7（−0.09）", "+24.2（−0.00）", "−15.1"],
        ["脈波伝播速度", "−17.0（−0.26）", "+33.7（−0.17）", "−31.2"],
        ["1回拍出量", "−4.1（+0.05）", "+21.6（−0.05）", "+15.9"],
    ]
    if big:
        t2b = [["因子", "特徴点法 ΔT", "分解法 ΔT", "分解法 RI", "早期振幅比"]]
        early = ["+2.0", "+4.0", "−1.1", "−4.0", "−7.1", "−0.2"]
        for r, e in zip(t2, early):
            t2b.append([r[0], r[3], r[1], r[2], e])
        table(s, 1.20, 2.25, [2.0, 2.0, 2.6, 2.5, 1.8], t2b, pt=t_pt, line_h=0.52,
              bolds={5})
    else:
        table(s, 0.75, 2.25, [2.6, 3.3, 3.3, 2.6], [t2_head] + t2, pt=t_pt,
              line_h=0.52, bolds={5})
    textbox(s, 0.55, 5.95, 12.25, 1.00, [
        ("1因子掃引　脈波伝播速度を動かすと ΔT は 332.3 → 352.8 → 251.2 ms", 22, INK, False),
        ("波形の型　切痕あり 20.4%・変曲点のみ 77.2%・いずれも無し 2.4%", 22, INK, False)],
        space_after=2, line_spacing=1.1)
    source(s, "表2（+1SD と −1SD の平均の差 ÷ 層平均、%）・表2b。括弧内は年齢層内 Spearman 順位相関")

    # ------------------------------------------------------------ 18 考察
    s = new_slide(prs, "示したことと示していないこと", "考察", notes=notes(
        para(JA2, "示したことと示していないこと　光電容積脈波を成分波に分解して得た指標は"),
        para(JA2, "本結果が示していないことが二つある")))
    box(s, 0.55, 1.80, 5.50, 0.62, [("示したこと", 24, WHITE, True)], fill=BLUE,
        align=PP_ALIGN.CENTER, space_after=0)
    textbox(s, 0.65, 2.52, 5.30, 2.20, [
        ("・分解法の指標は追わなかった", 22, INK, False),
        ("・同一の波形の特徴点法は追った", 22, INK, False),
        ("・情報は波形の中にある", 22, INK, True),
        ("・限界は取り出し方の側にある", 22, INK, True)],
        space_after=4, line_spacing=1.1)
    box(s, 6.45, 1.80, 6.45, 0.62, [("示していないこと", 24, WHITE, True)], fill=VERM,
        align=PP_ALIGN.CENTER, space_after=0)
    textbox(s, 6.55, 2.52, 6.25, 2.60, [
        ("・分解法が誤っているとは示していない", 22, INK, False),
        ("　分解由来と特徴点由来は別の量 3）", 22, DGREY, False),
        ("・情報を持たないとも示していない", 22, INK, False),
        ("　脈波伝播速度の主効果 −17.0%", 22, DGREY, False),
        ("・欠けているのは特異性である", 22, INK, True)],
        space_after=3, line_spacing=1.1)
    box(s, 0.55, 5.35, 12.35, 1.20, [
        ("心拍数と大動脈径が同じ程度に動かすため", 24, WHITE, False),
        ("指標の値から脈波伝播速度だけを読み取ることができない", 24, WHITE, True)],
        fill=DGREY, space_after=2)
    source(s, "3）Goswami 2010（分解由来と特徴点由来が構造的に異なる量であることの導出）")

    # ------------------------------------------------------------ 19 考察
    s = new_slide(prs, "失敗の5つの機構", "考察", notes=notes(
        para(JA2, "機構　我々の観測と整合する機構は5つある"),
        para(JA2, "理由は構造的である")))
    mech = [
        "① 同定不能　採択された拍の 87.4% で母数が境界にある",
        "② 応答が単調でない　成分の入れ替わりは採択例の 2.9%",
        "③ 第2成分に対応する生理学的事象が無い可能性 5,10）",
        "④ 前進波の裾の混入　分離は基底の裾の減衰の速さに依存する 3）",
        "⑤ 情報を伴わない自由度　特徴点法は3点、分解法は 8〜20 母数",
    ]
    for i, mx in enumerate(mech):
        box(s, 0.55, 1.85 + i * 0.90, 12.25, 0.72, [(mx, 24, INK, False)],
            fill=PALE, line=DGREY, align=PP_ALIGN.LEFT, space_after=0)
    textbox(s, 0.55, 6.32, 12.25, 0.50, [
        ("どれか一つが正しく他が誤りというものではない（排他的ではない）", 22, INK, False)],
        space_after=0, line_spacing=1.0)
    source(s, "3）Goswami 2010　5）Epstein 2014　10）Hellqvist 2024")

    # ------------------------------------------------------------ 20 考察（図2・図3）
    s = new_slide(prs, "同定不能の実例", "考察", notes=notes(
        "図2（figures/fig2_nonidentifiability.svg）と図3a（fig3_single_factor_sweep.svg）"
        "をスライド上で描き直したもの。図2 の a と b は同じ拍を同じ残差で再現する2つの解で、"
        "取り出される ΔT が違う。",
        para(JA2, "応答は単調でない"),
        "図3a の値（表2b・1因子掃引・年齢層の中央値）: 脈波伝播速度 −1SD で ΔT 332.3 ms、"
        "基準で 352.8 ms、+1SD で 251.2 ms。RI は 0.325 / 0.254 / 0.647 と U 字を描く。"))
    textbox(s, 0.55, 1.88, 3.35, 0.48, [("a　当てはめ A", 22, INK, True)],
            space_after=0, line_spacing=1.0)
    textbox(s, 4.20, 1.88, 3.35, 0.48, [("b　当てはめ B", 22, INK, True)],
            space_after=0, line_spacing=1.0)
    for X, off, wave, c1, c2, x0, x1 in (
            (0.55, 0, F2_WAVE_A, F2_COMP_A1, F2_COMP_A2, 104, 214),
            (4.20, 380, F2_WAVE_B, F2_COMP_B1, F2_COMP_B2, 478, 624)):
        m = svg_map((28 + off, 58, 350 + off, 285), (X, 2.40, 3.35, 2.05))
        poly(s, [m(p) for p in svg_points(wave)], color=VERM, width_pt=2.4)
        poly(s, [m((28 + off, 222)), m((350 + off, 222))], color=GREY, width_pt=1.0)
        for dd in (c1, c2):
            poly(s, [m(p) for p in svg_points(dd)], color=DGREY, width_pt=1.4, dash="DASH")
        for px, py in ((x0, 90 if off == 0 else 84), (x1, 186 if off == 0 else 178)):
            poly(s, [m((px, py + 6)), m((px, 248))], color=GREY, width_pt=0.75, dash="DASH")
        yb = m((0, 261))[1]
        brace(s, m((x0, 0))[0], m((x1, 0))[0], yb, drop=0.10)
        label(s, (m((x0, 0))[0] + m((x1, 0))[0]) / 2, yb + 0.28,
              "ΔT 短い" if off == 0 else "ΔT 長い", bold=True)
    textbox(s, 0.55, 4.88, 7.0, 0.48, [("同じ拍・同じ残差で ΔT が変わる", 22, INK, True)],
            space_after=0, line_spacing=1.0)
    textbox(s, 8.10, 1.80, 4.75, 1.00, [
        ("1因子掃引　ΔT（ms）", 22, INK, True),
        ("332.3 → 352.8 → 251.2", 22, VERM, True)], space_after=2, line_spacing=1.05)
    poly(s, [(8.55, 2.95), (8.55, 4.55), (12.75, 4.55)], color=GREY, width_pt=1.2)
    yv = lambda v: 4.45 - (v - 240.0) / 120.0 * 1.45
    sweep = ((9.25, 332.3), (10.65, 352.8), (12.05, 251.2))
    poly(s, [(px, yv(v)) for px, v in sweep], color=VERM, width_pt=3.0)
    for px, v in sweep:
        dot(s, px, yv(v), r=0.07, color=VERM, fill=VERM)
    for px, tx in zip((9.25, 10.65, 12.05), ("−1SD", "基準", "+1SD")):
        label(s, px, 4.86, tx, size=22, color=DGREY)
    box(s, 0.55, 5.50, 12.35, 0.80, [
        ("同一の波形から得た ΔT は基底によって 264〜640 ms まで動く", 26, RED, True)],
        fill=None, line=RED)
    textbox(s, 0.55, 6.40, 12.25, 0.50, [
        ("脈波伝播速度を上げると ΔT はいったん延びて縮む（単調でない）", 22, INK, False)],
        space_after=0, line_spacing=1.0)
    source(s, "図2 と図3a を描き直したもの。破線＝当てはめた成分。掃引の値は表2b")

    # ------------------------------------------------------------ 21 考察
    s = new_slide(prs, "文献との整合と限界", "考察", notes=notes(
        para(JA2, "本結果は既存の文献と矛盾しない"),
        para(JA2, "限界　本データベースは1次元流体モデルの出力であり")))
    box(s, 0.55, 1.80, 12.25, 1.55, [
        ("分解法の文献が確立した性質", 22, WHITE, False),
        ("当てはまりの良さ・雑音と体動への頑健性・切痕が無くても値を返すこと", 22, WHITE, False),
        ("本研究では検定しておらず、疑ってもいない", 24, WHITE, True)],
        fill=BLUE, space_after=2)
    lims = [
        "① 1次元流体モデルの出力で、光学的な要素を含まない",
        "② 雑音が無く単一拍で、体動を含まない",
        "③ 第2版は切痕のある型1 の拍にしか規準を当てていない",
        "④ Wang の閾値（6 ms・0.01）に原著が外部の根拠を示していない",
        "⑤ 検定した 6編の条件と 12通りの基底についての結論である",
    ]
    for i, lx in enumerate(lims):
        box(s, 0.55, 3.48 + i * 0.68, 12.25, 0.62, [(lx, 22, INK, False)],
            fill=PALE, line=None, align=PP_ALIGN.LEFT, space_after=0)
    source(s, "③ は Wang 2013 からの逸脱であり、第2版の採択が少ない理由の一つである")

    # ------------------------------------------------------------ 22 結論
    s = new_slide(prs, "結論", "結論", notes=notes(
        para(JA2, "血管の性質が既知である4,374名の仮想被験者集団において")))
    box(s, 0.55, 1.90, 12.25, 1.30, [
        ("真値が分かっている集団で", 24, WHITE, False),
        ("分解法の血管指標は真値を追わなかった", 28, WHITE, True)], fill=VERM, space_after=3)
    box(s, 0.55, 3.45, 12.25, 1.30, [
        ("同一の波形の特徴点法は追った", 28, WHITE, True),
        ("情報は波形にあり、限界は取り出し方の側にある", 24, WHITE, False)],
        fill=BLUE, space_after=3)
    box(s, 0.55, 5.00, 12.25, 1.30, [
        ("当てはめは同定不能な問題であり", 24, RED, False),
        ("当てはまりの良さではこの失敗を検出できない", 28, RED, True)],
        fill=None, line=RED, space_after=3)
    source(s, "4,374名・6層・事前に固定した規準（doi:10.5281/zenodo.22676038）")

    # ------------------------------------------------------------ 23 結論
    s = new_slide(prs, "今後", "結論", notes=notes(
        para(JA2, "含意　光電容積脈波から血管指標を構築する研究者にとって"),
        "臨床データでの前提検証は論文1（VitalDB 862例）で、実機のモニタ波形での可測性は"
        "別報で扱う。本稿の結論は、検定した6編の公表条件と12通りの基底についてのもので"
        "あって、脈波分解一般についてのものではない。"))
    box(s, 0.55, 2.10, 12.25, 1.30, [
        ("臨床データでの前提の検証（別報）", 28, WHITE, True)], fill=BLUE)
    box(s, 0.55, 3.70, 12.25, 1.30, [
        ("実機のモニタ波形での可測性（別報）", 28, WHITE, True)], fill=TEAL)
    textbox(s, 0.55, 5.35, 12.25, 1.00, [
        ("重複切痕が得られない場面では、上行脚のみの指標が選択肢となる", 22, INK, False),
        ("本集団では両系統を上回った（0.836）", 22, INK, False)],
        space_after=2, line_spacing=1.1)
    source(s, "10）Hellqvist 2024（早期振幅比 Am_b/Am_p1）")

    # ------------------------------------------------------------ 24 文献
    s = new_slide(prs, "文献", notes=(
        "文献表は英文原稿 v2（docs/manuscript/paper2/v2/01_draft_en_v2.md）の References "
        "から起こし、著者（筆頭 et al.）・誌名・年;巻(号):頁 に短縮した。"
        "1）から9）は論文1 のために 2026-08-30 に PubMed・出版社記録で、"
        "10）は 2026-09-07 に出版社PDFで、11）は 2026-09-09 に PubMed で照合した。"))
    textbox(s, 0.55, 1.85, 12.25, 4.60, [(r, 16, INK, False) for r in REFS_11],
            space_after=6, line_spacing=1.15)
    source(s, "巻号・PMID・DOI を含む完全な記載は英文原稿 v2 の文献表にある")

    prs.save(out_path)
    return prs


# ============================================================ 自己検査
def verify(path):
    """lint が見ない所を自分で確かめる（表のセル幅・文字の取り出し・ノートの有無）。"""
    prs = Presentation(path)
    bad = []
    for i, slide in enumerate(prs.slides, 1):
        texts, has_tbl = [], False
        for sp in slide.shapes:
            if sp.has_text_frame and sp.text_frame.text.strip():
                texts.append(sp.text_frame.text.strip())
            if getattr(sp, "has_table", False):
                has_tbl = True
                tbl = sp.table
                widths = [c.width / 914400 for c in tbl.columns]
                for ri, row in enumerate(tbl.rows):
                    for ci, cell in enumerate(row.cells):
                        if not cell.text.strip():
                            continue
                        texts.append(cell.text.strip())
                        for para_ in cell.text_frame.paragraphs:
                            txt = "".join(r.text for r in para_.runs)
                            pt = max([r.font.size.pt for r in para_.runs
                                      if r.font.size] or [22.0])
                            room = widths[ci] - 0.12
                            if txt and width_in(txt, pt) > room:
                                bad.append(f"p{i} 表セル({ri},{ci}) 幅超過 "
                                           f"{width_in(txt, pt):.2f}in>{room:.2f}in 「{txt}」")
            if sp.shape_type is not None and sp.left is not None:
                if sp.left + sp.width > Inches(SW) + Emu(73152):
                    bad.append(f"p{i} 枠外（右） {(sp.left + sp.width) / 914400:.2f}in")
                if sp.top + sp.height > Inches(SH) + Emu(73152):
                    bad.append(f"p{i} 枠外（下） {(sp.top + sp.height) / 914400:.2f}in")
        rects = []
        for sp in slide.shapes:
            if sp.left is None or sp.width is None:
                continue
            vis = (getattr(sp, "has_table", False) or sp.shape_type == 13
                   or (sp.has_text_frame and sp.text_frame.text.strip()))
            if not vis:
                continue
            rects.append((getattr(sp, "has_table", False),
                          sp.left / 914400, sp.top / 914400,
                          sp.width / 914400, sp.height / 914400))
        for a in range(len(rects)):
            for b in range(a + 1, len(rects)):
                ta, ax_, ay_, aw, ah = rects[a]
                tb_, bx, by, bw, bh = rects[b]
                if not (ta or tb_):
                    continue
                ox = max(0.0, min(ax_ + aw, bx + bw) - max(ax_, bx))
                oy = max(0.0, min(ay_ + ah, by + bh) - max(ay_, by))
                if ox * oy > 0.056:
                    bad.append(f"p{i} 表と重なる {ox * oy:.2f}in²")
        if not texts:
            bad.append(f"p{i} 取り出せる文字が無い")
        if i > 1 and not slide.notes_slide.notes_text_frame.text.strip():
            bad.append(f"p{i} ノートが空")
        if has_tbl and i in (1,):
            bad.append("表紙に表がある")
    return bad


def selftest():
    import tempfile
    ok = True
    for v in ("A", "B"):
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, f"t{v}.pptx")
            build(out, v)
            bad = verify(out)
            small = count_small_table_runs(out)
            print(f"版 {v}: 指摘 {len(bad)} 件・表の中の 22pt 未満 {small} 個")
            for b in bad:
                print("   ", b)
            ok = ok and not bad
    print("自己検査:", "通過" if ok else "不合格")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="論文2 の発表スライドを作る")
    ap.add_argument("--variant", choices=["A", "B"], default="A",
                    help="A=全文字22pt以上 / B=表だけ16〜18pt・表3は12行")
    ap.add_argument("--out", default=None, help="出力する pptx")
    ap.add_argument("--selftest", action="store_true", help="組んでから自分で確かめる")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    out = a.out or os.path.join(HERE, f"paper2_ja_{a.variant}.pptx")
    prs = build(out, a.variant)
    print(f"生成: {out}（{len(prs.slides._sldIdLst)} 枚・版 {a.variant}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

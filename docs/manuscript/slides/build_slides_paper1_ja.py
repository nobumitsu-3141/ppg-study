#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""論文1（VitalDB 862例）の発表スライドを川副式書式で生成する。

書式ルール（slide-format スキル）は論文2 の deck（build_slides_paper2_ja.py）と同一:
  - タイトル44pt太字・金BF9000・黒縁取り2.25pt・全スライド同位置・1行
  - タイトル直下に金色下線（y=1.52in・太さ8pt・全幅）
  - 右上に章ナビ（背景・方法・結果・考察・結論。現在章のみティール00A8AA）
  - 本文は22pt以上（出典16pt・章ナビ11ptのみ例外）
  - 図解優先・詳細はノートへ・図と文字を重ねない
  - 対比色はブルー0072B2 × バーミリオンD55E00（＋ティール）。金は構造色として予約
  - 上付き・下付きの字はスライド面で使わない（10⁻³ → 0.001、a₂/a₁ → a2/a1）

版は 2 つ作る（表以外は同一）:
  A  すべての文字が 22pt 以上。表2 は主要 5 行、表5・表6 は主要行のみ（残りはノート）
  B  表の中だけ 16〜18pt を許し、表2・表5・表6 の全行を載せる

数式だけは画像（matplotlib mathtext・白背景）で置く。同じ式を文字でノートに残す。
eq_skew_g・eq_model2 は論文2 の assets_paper2/ をそのまま参照し、
eq_rel・eq_premise・eq_prop・eq_pe は assets_paper1/ に同じ手口で作る。

図3a（年齢と ΔT）と図4（Bland–Altman）は実データが要り Mac 1 でしか描けないので、
既定では灰色の破線の枠と差し替えの指示を置く。--fig-dir に fig3_quality.png ／
fig4_accuracy.png があれば、縦横比を保って枠の代わりに入れる。

使い方:
    python3 build_slides_paper1_ja.py --variant A --out paper1_ja_A.pptx
    python3 build_slides_paper1_ja.py --variant B --out paper1_ja_B.pptx
    python3 build_slides_paper1_ja.py --selftest

スライド面の数値の出どころ（verify() が機械で照合する）:
    docs/manuscript/03_tables_2to7.md（表2〜表5・表7）
    docs/manuscript/v2/01_draft_en_v2.md の Table 6（本文中の表）
    docs/manuscript/v2/05_draft_ja_v2.md（要旨・本文・表1。ノートの出どころでもある）
    docs/research/results/21_pwtt_decomposition.txt（節4）
    docs/research/results/36_amb_premise_report.txt
    docs/research/results/37_ri_svr_screen.txt
    docs/research/lab_log.md の 2026-08-29（続き2）の 08番の表
    analysis/scripts/07_figures.py（症例フローの段の数）
"""
from __future__ import annotations

import argparse
import os
import re
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
ASSETS = os.path.join(HERE, "assets_paper1")
ASSETS2 = os.path.join(HERE, "assets_paper2")
DEFAULT_FIGDIR = os.path.join(ROOT, "analysis", "figs")
PLACED = []              # 図3a・図4 に画像を入れたか枠にしたか（組み立てのたびに書き直す）

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
COVER_W = 12.35          # 表紙は章ナビが無いので、この幅まで使える


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


def check_title(title: str, max_w: float = TITLE_MAX_W) -> None:
    w = width_in(title, 44)
    assert w <= max_w, f"タイトルが幅超過 {w:.2f}in > {max_w:.2f}in: {title}"


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
        shape=MSO_SHAPE.ROUNDED_RECTANGLE, anchor=MSO_ANCHOR.MIDDLE, dash=None, **kw):
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
        if dash:
            from pptx.enum.dml import MSO_LINE_DASH_STYLE
            sp.line.dash_style = getattr(MSO_LINE_DASH_STYLE, dash)
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
    """SVG の path（M・C・L だけ）を折れ線の点列に開く。"""
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


def tick(slide, x, y0, y1, color=GREY, width_pt=1.25):
    poly(slide, [(x, y0), (x, y1)], color=color, width_pt=width_pt)


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


def fig_slot(slide, fname, x, y, w, h, lines, fig_dir, placed=None):
    """実データの図を置く場所。画像があれば縦横比を保って入れ、無ければ枠を描く。

    図3a・図4 は個票のデータが要るので、確定解析を回した機械（Mac 1）で
    07_figures.py を回して作る。それまでは差し替えの指示を枠の中に置く。
    どちらになったかは placed に記録し、組み立ての最後に表示する。
    """
    path = os.path.join(fig_dir, fname) if fig_dir else ""
    if path and os.path.exists(path):
        from PIL import Image
        with Image.open(path) as im:
            iw, ih = im.width, im.height
        k = min(w / iw, h / ih)
        dw, dh = iw * k, ih * k
        if placed is not None:
            placed.append(f"{fname} 画像 {path}")
        return slide.shapes.add_picture(path, Inches(x + (w - dw) / 2),
                                        Inches(y + (h - dh) / 2), width=Inches(dw))
    if placed is not None:
        placed.append(f"{fname} 枠（差し替えの指示）")
    return box(slide, x, y, w, h, [(t, 22, GREY, False) for t in lines],
               fill=None, line=GREY, line_w=1.5, shape=MSO_SHAPE.RECTANGLE,
               dash="DASH", align=PP_ALIGN.CENTER, space_after=4, line_spacing=1.1)


# ============================================================ 数式（画像・例外）
# assets_paper2 から再利用する 2 つ（論文2 の台本が作ったもの）
REUSED = ("eq_skew_g", "eq_model2")

_FORMULAS = {
    # 主解析（05_draft_ja_v2.md 〈方法〉主解析。式番号は原稿の (7)）
    "eq_rel": r"$\Delta x\%(t)\;=\;\frac{x(t)-x(1)}"
              r"{\max\left(\left|x(1)\right|,\;0.05\cdot\mathrm{median}\left|x\right|\right)}$",
    "eq_premise": r"$\Delta PWTT\%(t)\;=\;\beta_{SI}\,\Delta SI\%(t)\;+\;"
                  r"\beta_{RI}\,\Delta RI\%(t)\;+\;\varepsilon(t)$",
    # 副次解析（同 〈方法〉副次解析。式番号は原稿の (8)）
    "eq_prop": r"$\widehat{CO}_{prop}(t)\;=\;\widehat{CO}_{ctrl}(t)\cdot"
               r"\mathrm{clip}\left(1+c_{SI}\,\Delta SI\%(t)+c_{RI}\,\Delta RI\%(t),"
               r"\;0.3,\;3.0\right)$",
    "eq_pe": r"$\mathrm{PE}\;=\;\frac{1.96\cdot\mathrm{SD}"
             r"\left(\widehat{CO}-CO_{ref}\right)}{\mathrm{mean}\left(CO_{ref}\right)}$",
}

# ノートに残す文字版（画像に焼いた式と同じもの）
FORMULA_TEXT = {
    "eq_skew_g": "g(t; a, μ, σ, α) ＝ a・exp(−z²/2)・[1 ＋ erf(αz/√2)]、z ＝ (t − μ)/σ　(2)",
    "eq_model2": "ŷ(t) ＝ g(t; a₁, μ₁, σ₁, α₁) ＋ g(t; a₂, μ₁ ＋ Δμ, σ₂, α₂)　(3)",
    "eq_rel": "Δx%(t) ＝ (x(t) − x(1))／max(|x(1)|, 0.05・median|x|)",
    "eq_premise": "ΔPWTT%(t) ＝ β_SI・ΔSI%(t) ＋ β_RI・ΔRI%(t) ＋ ε(t)　(7)",
    "eq_prop": ("ĈO_prop(t) ＝ ĈO_ctrl(t)・clip(1 ＋ c_SI・ΔSI%(t) ＋ c_RI・ΔRI%(t), "
                "0.3, 3.0)　(8)"),
    "eq_pe": "PE ＝ 1.96・SD(ĈO − CO_ref)／mean(CO_ref)",
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


def formula_path(name):
    return os.path.join(ASSETS2 if name in REUSED else ASSETS, name + ".png")


def place_formula(slide, name, x, y, max_w, max_h=None):
    """式の画像を置く。max_w に収まるよう等倍で縮める。戻り値は (w, h, 実効pt)。"""
    from PIL import Image
    path = formula_path(name)
    with Image.open(path) as im:
        w_in, h_in = im.width / _RENDER_DPI, im.height / _RENDER_DPI
    k = min(1.0, max_w / w_in, (max_h / h_in) if max_h else 1.0)
    slide.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w_in * k))
    return w_in * k, h_in * k, _RENDER_PT * k


# ============================================================ 原稿からノートを引く
JA1 = os.path.join(HERE, "..", "v2", "05_draft_ja_v2.md")

# スライドにもノートにも出さない語。
#   「大半」  21番 節4 で「末梢区間が大半」という読みを訂正した（正確なのは合計だけ）。
#   「陰性対照」 症例IDとΔTの相関は原因が特定できておらず、発表では扱わない。
DROP_WORDS = ("大半", "陰性対照")


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


def drop_sentences(text, words=DROP_WORDS):
    """DROP_WORDS を含む文だけを落とす（残りは原文のまま）。"""
    blocks = []
    for block in text.split("\n\n"):
        keep = []
        for line in block.split("\n"):
            parts = re.split(r"(?<=。)", line)
            kept = "".join(p for p in parts if not any(w in p for w in words))
            if kept.strip():
                keep.append(kept)
        if keep:
            blocks.append("\n".join(keep))
    return "\n\n".join(blocks)


def notes(*parts):
    return drop_sentences("\n\n".join(p for p in parts if p))


# ============================================================ 数値の照合
# スライド面に出してよい数値の出どころ。(相対パス, 切り出し開始, 切り出し終了)
# 開始・終了が None のときはファイル全体を使う。
NUM_SOURCES = [
    ("docs/manuscript/03_tables_2to7.md", None, None),
    ("docs/manuscript/v2/05_draft_ja_v2.md", None, None),
    ("docs/manuscript/v2/01_draft_en_v2.md", "**Table 6.", "Premise r² is the"),
    ("docs/research/results/21_pwtt_decomposition.txt", "-- 4. 2 区間の変動", None),
    ("docs/research/results/36_amb_premise_report.txt", None, None),
    ("docs/research/results/37_ri_svr_screen.txt", None, None),
    ("docs/research/lab_log.md", "## 2026-08-29（続き2）", "### 代替データ源の調査"),
    ("analysis/scripts/07_figures.py", None, None),
]

# 文献番号の並び（「7,8,10）」「17-20）」など）は照合の対象外にする。
_CITE = re.compile(r"\d+(?:\s*[,\-–〜]\s*\d+)*）")
_AUTHOR_YEAR = re.compile(r"[A-Za-z]\s+(?:19|20)\d{2}")
_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def num_corpus():
    txt = []
    for rel, start, end in NUM_SOURCES:
        with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
            body = fh.read()
        if start:
            i = body.index(start)
            body = body[i:]
        if end:
            body = body[:body.index(end)]
        txt.append(body)
    return "\n".join(txt)


def numbers_in(text):
    """照合の対象になる数値を取り出す（文献番号と著者＋年は除く）。"""
    t = _AUTHOR_YEAR.sub(" ", _CITE.sub(" ", text))
    return [m.group(0) for m in _NUM.finditer(t)]


def _whole_number_at(corpus, i, n):
    """corpus[i:i+n] が、より長い数値の一部になっていないか。"""
    b1 = corpus[i - 1] if i >= 1 else ""
    b2 = corpus[i - 2] if i >= 2 else ""
    a1 = corpus[i + n] if i + n < len(corpus) else ""
    a2 = corpus[i + n + 1] if i + n + 1 < len(corpus) else ""
    if b1.isdigit() or a1.isdigit():
        return False
    if b1 in ".," and b2.isdigit():
        return False
    if a1 in ".," and a2.isdigit():
        return False
    return True


def in_corpus(tok, corpus):
    """数値が出どころに現れるか。より長い数値の一部でしかない一致は採らない。"""
    i = corpus.find(tok)
    while i >= 0:
        if _whole_number_at(corpus, i, len(tok)):
            return True
        i = corpus.find(tok, i + 1)
    return False


# ============================================================ 文献（英文原稿 v2 の References の番号）
REFS = {
    1: "1）Ochiai R, et al. J Clin Monit Comput. 1999;15(7-8):493-501.",
    2: "2）Ishihara H, et al. J Clin Monit Comput. 2004;18(5-6):313-20.",
    3: "3）Sugo Y, et al. Annu Int Conf IEEE Eng Med Biol Soc. 2010;2010:2853-6.",
    4: "4）Sugo Y, et al. Annu Int Conf IEEE Eng Med Biol Soc. 2012;2012:236-9.",
    7: "7）Ishihara H, Tsutsui M. J Clin Monit Comput. 2014;28(4):423-7.",
    8: "8）Biais M, et al. Br J Anaesth. 2015;115(3):403-10.",
    10: "10）Magliocca A, et al. Anesth Analg. 2018;126(1):85-92.",
    11: "11）Sugo Y, Ochiai R. BMC Biomed Eng. 2025;7(1):14.",
    12: "12）Payne RA, et al. J Appl Physiol. 2006;100(1):136-41.",
    13: "13）Zhang G, et al. J Appl Physiol. 2011;111(6):1681-6.",
    15: "15）Djupedal H, et al. Physiol Rep. 2022;10(12):e15355.",
    16: "16）Pilz N, et al. Front Cardiovasc Med. 2023;10:1138356.",
    17: "17）Millasseau SC, et al. Clin Sci (Lond). 2002;103(4):371-7.",
    18: "18）Millasseau SC, et al. J Hypertens. 2006;24(8):1449-56.",
    19: "19）Rubins U. Med Biol Eng Comput. 2008;46(12):1271-1276.",
    20: "20）Goswami D, et al. Cardiovasc Eng. 2010;10(3):109-117.",
    21: "21）Epstein S, et al. Annu Int Conf IEEE Eng Med Biol Soc. 2014;2014:1969-72.",
    22: "22）Couceiro R, et al. Physiol Meas. 2015;36(9):1801-25.",
    26: "26）Ding XR, et al. IEEE Trans Biomed Eng. 2016;63(5):964-72.",
    27: "27）Yang S, et al. IEEE J Biomed Health Inform. 2021;25(4):1018-1030.",
    28: "28）Lee J, et al. J Clin Med. 2019;8(11):1773.",
    29: "29）Lee HC, et al. Sci Data. 2022;9(1):279.",
    33: "33）Critchley LA, Critchley JA. J Clin Monit Comput. 1999;15(2):85-91.",
    39: "39）Charlton PH, et al. Am J Physiol Heart Circ Physiol. 2019;317(5):H1062-H1085.",
    40: "40）Hellqvist H, et al. Front Cardiovasc Med. 2024;11:1350726.",
}
CITED = sorted(REFS)


# ============================================================ 本体
def build(out_path, variant="A", fig_dir=DEFAULT_FIGDIR):
    big = variant == "B"          # 表を 16〜18pt で詰める版
    t_pt = 18 if big else 22      # 表の文字（表6 だけ 16pt）
    t6_pt = 16
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(SW), Inches(SH)
    render_formulas()
    placed = PLACED
    del placed[:]

    # ------------------------------------------------------------ 1 表紙
    cover = "血管指標は PWTT の変動を説明しない"
    check_title(cover, COVER_W)
    s = prs.slides.add_slide(prs.slide_layouts[6])
    tb = textbox(s, TITLE_X, TITLE_Y, COVER_W, 0.95, [(cover, 44, GOLD, True)],
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
    textbox(s, 0.90, 1.95, 11.30, 1.40, [
        ("光電容積脈波から得た動脈スティフネス指標は", 26, INK, False),
        ("術中の脈波伝播時間の変動を説明しない", 26, INK, False)],
        space_after=2, line_spacing=1.15)
    box(s, 0.90, 3.50, 11.30, 0.85, [
        ("公開周術期データベース 862 例・事前登録・参照非依存解析", 24, WHITE, True)],
        fill=BLUE, align=PP_ALIGN.CENTER, space_after=0)
    textbox(s, 0.90, 4.75, 9.00, 1.35, [
        ("長崎県五島中央病院麻酔科", 26, INK, False),
        ("川副靖晃", 32, INK, True)], space_after=4, line_spacing=1.15)
    textbox(s, 0.90, 6.25, 6.00, 0.55, [("2026年9月", 24, DGREY, False)],
            space_after=0, line_spacing=1.0)
    s.notes_slide.notes_text_frame.text = notes(
        "【表題】" + para(JA1, "光電容積脈波から得た動脈スティフネス指標は術中の"),
        "【所属】長崎県五島中央病院麻酔科　川副靖晃",
        para(JA1, "目的：心電図のR波から指先の脈波の立ち上がりまでの時間"))

    # ------------------------------------------------------------ 2 背景
    s = new_slide(prs, "PWTT 法と較正定数", "背景", notes=notes(
        para(JA1, "非侵襲の連続CO推定は周術期医療の未充足の課題", extra=1),
        "図の区間: R 波から橈骨動脈圧の立ち上がりまでが心臓側（前駆出期と中枢の伝播）、"
        "そこから指尖脈波の足までが末梢の伝播である。本研究の探索的解析では前者の"
        "症例内 SD が 12.1 ms、後者が 17.5 ms、PWTT が 19.0 ms であった。"))
    textbox(s, 0.55, 1.74, 12.25, 0.55, [
        ("PWTT ＝ 心電図の R 波から指尖脈波の足までの時間", 24, INK, True)],
        space_after=0, line_spacing=1.0)
    box(s, 1.30, 2.60, 4.30, 0.62, [("前駆出期＋中枢の伝播", 22, WHITE, True)],
        fill=BLUE, align=PP_ALIGN.CENTER, space_after=0)
    box(s, 5.60, 2.60, 6.50, 0.62, [("末梢の伝播（血管の区間）", 22, WHITE, True)],
        fill=VERM, align=PP_ALIGN.CENTER, space_after=0)
    poly(s, [(1.10, 3.34), (12.35, 3.34)], color=DGREY, width_pt=1.5)
    for xt in (1.30, 5.60, 12.10):
        tick(s, xt, 3.22, 3.46)
    label(s, 1.30, 3.78, "R 波", color=DGREY)
    label(s, 5.60, 3.78, "橈骨動脈圧の立ち上がり", color=DGREY)
    label(s, 11.30, 3.78, "指尖脈波の足", color=DGREY)
    textbox(s, 0.55, 4.32, 12.25, 1.36, [
        ("CO は較正定数と ΔPWTT の一次式で推定する 1-3）", 24, INK, False),
        ("較正定数は年齢・性別・身長・体重で決まり、較正後は固定", 24, INK, False),
        ("推定誤差は血管の状態（体血管抵抗など）と関連する 7,8,10）", 24, INK, False)],
        space_after=2, line_spacing=1.05)
    box(s, 0.55, 5.85, 12.25, 0.85, [
        ("較正定数は血管の状態の変化を追わない", 26, WHITE, True)], fill=DGREY)
    source(s, "1-3）PWTT 法の原著　7,8,10）誤差が血管の状態と関連することの報告")

    # ------------------------------------------------------------ 3 背景
    s = new_slide(prs, "補正案とその前提", "背景", notes=notes(
        para(JA1, "そこで直感的な対処が導かれる"),
        para(JA1, "ただしこの戦略は、それ自体が検証されていない前提の上に立つ")))
    for i, (tx, col) in enumerate((("指尖の脈波", TEAL), ("血管指標\nΔT・SI・RI", TEAL),
                                   ("較正定数の補正", BLUE), ("CO の推定", BLUE))):
        x = 0.55 + i * 3.30
        w = 2.75 if i < 3 else 2.35
        box(s, x, 1.80, w, 0.95, [(t, 22, WHITE, True) for t in tx.split("\n")],
            fill=col, align=PP_ALIGN.CENTER, space_after=0, line_spacing=1.05)
        if i < 3:
            arrow(s, x + w + 0.10, 2.13, 0.40, 0.28,
                  VERM if i == 1 else GREY)
    chip(s, 6.28, 2.92, ["前提"], VERM)
    box(s, 0.55, 3.72, 12.25, 1.05, [
        ("術中の PWTT の変動は、この指標が測る血管の状態の変化で起きる", 26, RED, True)],
        fill=None, line=RED)
    box(s, 0.55, 5.15, 12.25, 0.90, [
        ("この前提は検証されていない", 28, WHITE, True)], fill=VERM)
    textbox(s, 0.55, 6.20, 12.25, 0.55, [
        ("補正が有効かを問う前に、前提が成り立つかを問う", 22, INK, False)],
        space_after=0, line_spacing=1.0)
    source(s, "17-20）脈波分解から得るスティフネス指標と反射係数　26）27,28）補正の先行研究")

    # ------------------------------------------------------------ 4 背景
    s = new_slide(prs, "論文2 で示したこと（再掲）", "背景", notes=notes(
        para(JA1, "結果：862例・161,737個の60秒ウィンドウを解析した"),
        para(JA1, "陽性対照はΔTが血管情報を持つことを示すが"),
        "本発表では仮想集団（Pulse Wave Database・4,374名）の結果は背景として扱い、"
        "結果の章には載せない。論文2 として別に報告する。"))
    table(s, 0.60, 1.80, [3.5, 4.3, 2.9, 1.4], [
        ["指標の取り出し方", "ΔT ×\n大動脈脈波伝播速度", "RI ×\n末梢血管抵抗", "判定"],
        ["凍結版の分解法", "0.22", "0.21", "不成立"],
        ["同じ波形の特徴点法", "0.71", "0.50", "成立"],
    ], pt=t_pt, line_h=0.56 if big else 0.60, bolds={2})
    box(s, 0.55, 4.35, 12.25, 0.95, [
        ("限界は脈波そのものではなく、指標の取り出し方の側にある", 24, WHITE, True)],
        fill=BLUE)
    textbox(s, 0.55, 5.50, 12.25, 1.25, [
        ("真値が分かっている仮想被験者 4,374 名 39）での検証", 22, INK, False),
        ("年齢層内の順位相関の絶対値の中央値。規準は 0.3 以上で成立", 22, INK, False),
        ("本発表では、この結果は背景として扱い結果の章には載せない", 22, DGREY, False)],
        space_after=2, line_spacing=1.1)
    source(s, "39）Charlton 2019（Pulse Wave Database）。論文2 として別に報告する")

    # ------------------------------------------------------------ 5 背景
    s = new_slide(prs, "目的と問い", "背景", notes=notes(
        para(JA1, "術中のPWTT変動が心臓側の成分に支配されるならば"),
        para(JA1, "事前に固定した解釈規準")))
    chip(s, 0.55, 1.78, ["主解析"], BLUE)
    box(s, 0.55, 2.40, 12.25, 1.10, [
        ("参照 CO を使わずに、前提がどの程度成り立つかを定量する", 26, WHITE, True)],
        fill=BLUE)
    chip(s, 0.55, 3.80, ["副次解析"], VERM)
    box(s, 0.55, 4.42, 12.25, 1.10, [
        ("較正定数を補正すると参照 CO との一致度は上がるか", 26, WHITE, True)],
        fill=VERM)
    textbox(s, 0.55, 5.75, 12.25, 1.05, [
        ("主解析は参照 CO を用いないので、参照標準の限界の影響を受けない", 22, INK, False),
        ("前提が成り立たなければ、補正の形を変えても機能しない", 22, INK, False)],
        space_after=2, line_spacing=1.1)
    source(s, "主解析＝前提検証（確認的解析）　副次解析＝推定器の比較（参照 CO を用いる）")

    # ------------------------------------------------------------ 6 方法
    s = new_slide(prs, "VitalDB と症例", "方法", notes=notes(
        para(JA1, "デザイン・データ源・倫理"),
        para(JA1, "対象　光電容積脈波・心電図・動脈圧"),
        para(JA1, "参照標準の限界は事前に明記した"),
        para(JA1, "対象と収率"),
        "図1（症例フロー）の段は analysis/scripts/07_figures.py の fig1_flow による。"))
    flow = [("VitalDB 6,388 例", BLUE), ("4 トラックすべてを持つ 874 例", BLUE),
            ("有効ウィンドウ 12 以上　862 例", TEAL), ("161,737 ウィンドウ", DGREY)]
    for i, (tx, col) in enumerate(flow):
        y = 1.78 + i * 1.02
        box(s, 0.55, y, 5.60, 0.66, [(tx, 22, WHITE, True)], fill=col,
            align=PP_ALIGN.CENTER, space_after=0)
        if i < len(flow) - 1:
            down_arrow(s, 3.17, y + 0.72, 0.36, 0.24)
    textbox(s, 6.40, 1.78, 6.45, 1.40, [
        ("トラック別の例数", 22, INK, True),
        ("光電容積脈波 6,157・心電図 6,355", 22, INK, False),
        ("動脈圧 3,645・連続 CO 993", 22, INK, False)],
        space_after=2, line_spacing=1.1)
    textbox(s, 6.40, 3.42, 6.45, 2.20, [
        ("参照 CO の装置", 22, INK, True),
        ("EV1000 545（63%）", 22, INK, False),
        ("Vigileo 301（35%）", 22, INK, False),
        ("CardioQ 11・Vigilance II 5", 22, INK, False),
        ("846 例（98.1%）が動脈圧波形由来", 22, VERM, True)],
        space_after=2, line_spacing=1.08)
    textbox(s, 0.55, 5.95, 12.25, 0.55, [
        ("解析の単位は重複のない 60 秒ウィンドウ", 24, INK, True)],
        space_after=0, line_spacing=1.0)
    source(s, "29）Lee 2022（VitalDB）。段の数は analysis/scripts/07_figures.py の fig1_flow")

    # ------------------------------------------------------------ 7 方法
    s = new_slide(prs, "凍結版 PDA と指標の定義", "方法", notes=notes(
        para(JA1, "脈波分解の模型"),
        para(JA1, "当てはめの採否"),
        para(JA1, "指標の定義"),
        "式（画像で置いたものの文字版）:",
        FORMULA_TEXT["eq_skew_g"], FORMULA_TEXT["eq_model2"],
        "ΔT ＝ t_peak,2 − t_peak,1　(4)／RI ＝ h₂／h₁　(5)／SI ＝ H／ΔT　(6)。"
        "H は身長。RI は振幅母数の比 a₂/a₁ ではなくピーク高さの比である。"))
    place_formula(s, "eq_skew_g", 1.30, 1.70, 10.60)
    place_formula(s, "eq_model2", 1.30, 2.62, 10.60)
    textbox(s, 0.55, 3.42, 12.25, 3.30, [
        ("ΔT ＝ t_peak,2 − t_peak,1　RI ＝ h2／h1　SI ＝ H／ΔT（H は身長）", 22, INK, True),
        ("RI はピーク高さの比であり、振幅母数の比 a2/a1 ではない", 22, INK, False),
        ("採否の検算　次のいずれかに当たる当てはめは採用しない", 22, BLUE, True),
        ("① 母数が探索範囲の境界から 0.001 以内（歪度の下限 0 は除く）", 22, INK, False),
        ("② 2 成分のピーク高さの小さい方が 0.02 未満", 22, INK, False),
        ("③ 競合解　残差 1.15 倍以内・Δμ 差 0.03 s 以上・RI 差 0.08 以上", 22, INK, False),
        ("雑音に応じて 4〜16 拍を平均した拍に当てる", 22, INK, False),
        ("定義は実データを見る前に合成脈波で凍結（ΔT 候補 5・RI 候補 3）", 22, VERM, True)],
        space_after=2, line_spacing=1.08)
    source(s, "論文1 のために凍結した実装。ピークは 4,000 点に離散化して数値的に求める")

    # ------------------------------------------------------------ 8 方法
    s = new_slide(prs, "PWTT の定義と採否の規準", "方法", notes=notes(
        para(JA1, "拍の切り出し"),
        para(JA1, "PWTTはR波から脈波の足までの区間とし"),
        para(JA1, "ウィンドウ・症例の採否"),
        "見かけの遅れの症例中央値は 660 ms（四分位範囲 644〜676）である（表1）。"))
    textbox(s, 0.55, 1.72, 12.25, 1.25, [
        ("PWTT ＝ R 波から指尖脈波の足まで（ウィンドウ内の中央値）", 24, INK, True),
        ("脈波チャネルの見かけの遅れ 660 ms（644〜676）を症例ごとに解消", 24, INK, False),
        ("絶対値は装置遅延を含むので、症例内の変化量だけを解析に用いる", 24, INK, False)],
        space_after=2, line_spacing=1.05)
    gates = ["① 品質指標を通過した拍が 8 以上",
             "② 採用された脈波分解が 2 以上",
             "③ PWTT に寄与する拍が 10 以上",
             "④ 動脈圧がウィンドウの 50% 以上",
             "⑤ 参照 CO が 5 点以上"]
    for i, g in enumerate(gates):
        box(s, 0.55, 3.04 + i * 0.64, 12.25, 0.58, [(g, 22, INK, False)],
            fill=PALE, line=DGREY, align=PP_ALIGN.LEFT, space_after=0)
    textbox(s, 0.55, 6.30, 12.25, 0.55, [
        ("症例は有効ウィンドウ 12 以上（較正 1・評価 11）で採用", 22, INK, True)],
        space_after=0, line_spacing=1.0)
    source(s, "5 つをすべて満たすウィンドウだけを解析した。棄却の理由は症例ごとに記録した")

    # ------------------------------------------------------------ 9 方法
    s = new_slide(prs, "主解析＝前提検証", "方法", notes=notes(
        para(JA1, "主解析　各症例の初回ウィンドウを較正点とし", extra=2),
        "式（画像で置いたものの文字版）:",
        FORMULA_TEXT["eq_rel"], FORMULA_TEXT["eq_premise"],
        "分母に系列の中央絶対値の 5% の床を置いたのは、初回値が 0 近傍の症例で"
        "比が発散するのを防ぐためである。"))
    x2, _ = chip(s, 0.55, 1.66, ["主解析"], BLUE)
    chip(s, x2 + 0.18, 1.66, ["プライマリーアウトカム"], BLUE)
    place_formula(s, "eq_rel", 3.69, 2.34, 10.00, 0.85)
    place_formula(s, "eq_premise", 1.72, 3.36, 10.00, 0.72)
    textbox(s, 0.55, 4.28, 12.25, 2.45, [
        ("原点通過　相対変化は較正点で 0 になるため、定数列を含めない", 22, INK, False),
        ("r² の分母は平均まわりの平方和なので、0 近傍にも負にもなりうる", 22, INK, False),
        ("この指定は凍結した解析コードにある", 22, INK, False),
        ("（タグ sap-v0.3・コミット 407f226・凍結日 2026年8月28日）", 22, DGREY, False),
        ("切片を加えた当てはめは探索として併記する", 22, INK, False),
        ("症例内の係数の符号の一致も報告する", 22, INK, False)],
        space_after=2, line_spacing=1.08)
    source(s, "プライマリーアウトカム＝原点通過の r² と β_SI・β_RI。参照 CO は用いない")

    # ------------------------------------------------------------ 10 方法
    s = new_slide(prs, "品質・陽性対照・RI の扱い", "方法", notes=notes(
        para(JA1, "決定係数が0近傍になる経路には"),
        para(JA1, "自己相関のみでは測定の失敗を否定できない"),
        para(JA1, "陽性対照は症例間で計算され")))
    chip(s, 0.55, 1.68, ["関門（ゲート）"], TEAL)
    textbox(s, 0.55, 2.34, 12.25, 0.95, [
        ("r² が 0 近傍になる経路は 2 つ　前提が偽／測定が雑音に埋もれる", 24, INK, False),
        ("これを分けるため、隣接ウィンドウの 1 次自己相関を事前指定した", 24, INK, False)],
        space_after=3, line_spacing=1.1)
    box(s, 0.55, 3.42, 12.25, 0.78, [
        ("陽性対照　加齢で ΔT は短縮し SI は上昇する 17）", 24, WHITE, True)], fill=TEAL)
    textbox(s, 0.55, 4.34, 12.25, 0.50, [
        ("通らなかった指標は回帰に残すが、その係数から結論を導かない", 22, INK, False)],
        space_after=0, line_spacing=1.0)
    box(s, 0.55, 4.96, 12.25, 1.35, [
        ("RI　陽性対照は向きを予測しないので不通過を根拠にできない", 22, WHITE, False),
        ("症例内変動係数を測定の安定性の指標に用いる", 22, WHITE, True),
        ("（生理的には 0.2〜0.5 に収まるはずの比である）", 22, WHITE, False)],
        fill=VERM, space_after=2, line_spacing=1.08)
    textbox(s, 0.55, 6.40, 12.25, 0.50, [
        ("この判断は主解析の結果を見る前に決めた", 22, RED, True)],
        space_after=0, line_spacing=1.0)
    source(s, "17）Millasseau 2002（加齢とスティフネス指標）　18）RI は年齢との関連が弱く血管作動薬に反応する")

    # ------------------------------------------------------------ 11 方法
    s = new_slide(prs, "副次解析＝推定器の比較", "方法", notes=notes(
        para(JA1, "副次解析　公表されたPWTT型の推定式を再現した"),
        para(JA1, "事前に固定した解釈規準"),
        "式（画像で置いたものの文字版）:",
        FORMULA_TEXT["eq_prop"], FORMULA_TEXT["eq_pe"],
        "補正係数 c は導出 fold において、対照推定器の相対残差 CO_ref/ĈO_ctrl − 1 に"
        "対する原点通過の最小二乗で求めた。説明変数の組は（ΔSI%, ΔRI%）、（ΔMAP%）、"
        "その両方の 3 通りである。"))
    x2, _ = chip(s, 0.55, 1.64, ["副次解析"], VERM)
    chip(s, x2 + 0.18, 1.64, ["セカンダリーアウトカム"], VERM)
    textbox(s, 0.55, 2.22, 12.25, 0.86, [
        ("対照推定器　較正定数を年齢・性別・身長・体重の回帰から求め、", 22, INK, False),
        ("較正点の CO と ΔPWTT の一次式とした 1,3）　症例単位の 5 分割交差検証", 22, INK, False)],
        space_after=2, line_spacing=1.08)
    textbox(s, 0.55, 3.10, 12.25, 0.42, [
        ("提案推定器　その出力に次の乗算補正を加える", 22, INK, True)],
        space_after=0, line_spacing=1.0)
    place_formula(s, "eq_prop", 0.80, 3.54, 11.60, 0.70)
    place_formula(s, "eq_pe", 4.86, 4.26, 11.60, 0.76)
    textbox(s, 0.55, 5.06, 12.25, 0.76, [
        ("補正係数 c は導出 fold の相対残差への原点通過最小二乗", 22, INK, False),
        ("差は症例単位のブートストラップ 2,000 回で検定する 33）", 22, INK, False)],
        space_after=1, line_spacing=1.05)
    box(s, 0.55, 5.84, 12.25, 1.06, [
        ("無益性の規準　提案が対照より PE を有意（両側 5%）に下げなければ", 22, RED, False),
        ("臨床段階に進まない。参照 CO の 98% が動脈圧波形由来なので、", 22, RED, False),
        ("一致度が上がっても精度の向上かどうかは一致度だけでは分けられない", 22, RED, True)],
        fill=None, line=RED, space_after=1, line_spacing=1.05)
    source(s, "1,3）公表された PWTT 型の推定式　33）Critchley 1999（誤差率 PE）")

    # ------------------------------------------------------------ 12 方法
    s = new_slide(prs, "解析計画（事前登録）", "方法", notes=notes(
        para(JA1, "本研究の主解析は確認的解析である"),
        para(JA1, "感度解析　代替指標定義"),
        para(JA1, "解析計画の凍結後に追加した探索的解析")))
    plan = [
        (0.55, 6.20, BLUE, ["主解析（前提検証）"],
         ["ΔPWTT% を ΔSI%・ΔRI% で回帰", "原点通過・参照 CO を用いない"]),
        (0.55, 6.20, BLUE, ["プライマリーアウトカム"],
         ["原点通過の r² と β_SI・β_RI"]),
        (0.55, 6.20, TEAL, ["関門"],
         ["自己相関（雑音でないこと）", "陽性対照（加齢と ΔT・SI）"]),
        (7.00, 5.90, VERM, ["副次解析（推定器の比較）"],
         ["対照推定器と提案推定器", "症例単位の 5 分割交差検証"]),
        (7.00, 5.90, VERM, ["セカンダリーアウトカム"], ["PE の差"]),
        (7.00, 5.90, RED, ["無益性の規準"], ["PE を有意に下げなければ進まない"]),
        (7.00, 5.90, GREY, ["感度解析・探索的（凍結後）"],
         ["表5・表6", "PWTT の分解・指標の交換・SVR"]),
    ]
    ys = {0.55: 1.66, 7.00: 1.66}
    for x, w, col, chips, lines in plan:
        y = ys[x]
        chip(s, x, y, chips, col, h_line=0.42)
        textbox(s, x + 0.08, y + 0.52, w - 0.16, 0.42 * len(lines) + 0.08,
                [(t, 22, INK, False) for t in lines], space_after=1, line_spacing=1.06)
        ys[x] = y + 0.52 + 0.42 * len(lines) + 0.10
    source(s, "SAP doi:10.5281/zenodo.22167118（sap-v0.3・407f226・2026年8月28日）"
              "　コード doi:10.5281/zenodo.22676038（v1.0.0）")

    # ------------------------------------------------------------ 13 結果
    s = new_slide(prs, "症例と測定品質", "結果", notes=notes(
        para(JA1, "対象と収率"),
        para(JA1, "検討した232,451ウィンドウのうち70%"),
        para(JA1, "測定品質　連続ウィンドウ間の1次自己相関"),
        "表3 の全行: 点検したウィンドウ 232,451、すべての品質規準を通過 70%、"
        "棄却はアンサンブルの雑音目標の未達 12%・参照 CO の欠落 6%・動脈圧の欠落 4%・"
        "採用された分解が 2 未満 3%・品質を通過した拍の不足 2%（重複計上を含む）。"
        "当てはめた区間 2,692,082、収束検算をすべて通過 72%、棄却は母数の境界張り付き 22%・"
        "競合解 8%・成分の消失 0.1% 未満。1 次自己相関は PWTT +0.75・ΔT 系 +0.50・"
        "RI +0.43・Am_b/Am_p1 +0.394・平均血圧 +0.695。"))
    textbox(s, 0.55, 1.72, 12.25, 0.55, [
        ("解析に入ったのは 874 例中 862 例（98.6%）・161,737 ウィンドウ", 24, INK, True)],
        space_after=0, line_spacing=1.0)
    textbox(s, 0.55, 2.45, 7.60, 2.60, [
        ("点検した 232,451 ウィンドウの 70% が通過", 22, INK, False),
        ("棄却　雑音目標 12%・参照 CO 6%・動脈圧 4%", 22, DGREY, False),
        ("　　　分解 2 未満 3%・拍不足 2%", 22, DGREY, False),
        ("当てはめた 2,692,082 区間の 72% が通過", 22, INK, False),
        ("棄却　境界 22%・競合解 8%・成分消失 0.1% 未満", 22, DGREY, False)],
        space_after=3, line_spacing=1.1)
    table(s, 8.35, 2.45, [2.90, 1.50], [
        ["1 次自己相関", "値"],
        ["PWTT", "+0.75"],
        ["ΔT 系の指標", "+0.50"],
        ["RI", "+0.43"],
    ], pt=t_pt, line_h=0.56 if big else 0.58)
    box(s, 0.55, 5.60, 12.25, 1.00, [
        ("雑音ではなく、再現性のある生理を追う系列である", 26, WHITE, True)], fill=BLUE)
    source(s, "表3。自己相関は隣接する 60 秒ウィンドウ間の 1 次自己相関（症例中央値）")

    # ------------------------------------------------------------ 14 結果
    s = new_slide(prs, "陽性対照と RI の判定", "結果", notes=notes(
        para(JA1, "測定品質　連続ウィンドウ間の1次自己相関"),
        "図3a（年齢と ΔT の散布図）は analysis/scripts/07_figures.py の fig3_quality で"
        "描く。個票のキャッシュが要るため、確定解析を回した機械でのみ再現できる。"))
    x2, _ = chip(s, 0.55, 1.66, ["陽性対照"], TEAL)
    chip(s, x2 + 0.18, 1.66, ["探索的"], GREY)
    textbox(s, 0.55, 2.34, 7.20, 1.70, [
        ("ΔT × 年齢　ρ −0.197", 24, INK, True),
        ("（95% CI −0.261〜−0.131・p<0.0001）", 22, DGREY, False),
        ("成人 849 例", 22, INK, False),
        ("高血圧既往で短い（259 対 267 ms）", 22, INK, False)],
        space_after=2, line_spacing=1.1)
    textbox(s, 0.55, 4.14, 7.20, 0.90, [
        ("RI × 年齢　+0.041（p 0.23）", 24, INK, True),
        ("文献上も関連が弱く判定できない 18）", 22, DGREY, False)],
        space_after=2, line_spacing=1.1)
    box(s, 0.55, 5.14, 7.20, 1.50, [
        ("RI の症例内変動係数 0.680（ΔT は 0.228）", 22, WHITE, True),
        ("この信号源では妥当性を確立できない", 22, WHITE, False),
        ("報告はするが、結論は導かない", 22, WHITE, True)],
        fill=VERM, space_after=2, line_spacing=1.08)
    fig_slot(s, "fig3_quality.png", 8.05, 2.34, 4.80, 4.30,
             ["図3a　年齢と ΔT", "Mac 1 で 07番を回して", "fig3_quality.png を挿入"],
             fig_dir, placed)
    source(s, "表3。陽性対照は症例間で計算し、参照 CO も症例内変化も用いない")

    # ------------------------------------------------------------ 15 結果
    t2_rows = [
        ["事前指定・原点通過", "0.000", "−0.027\n（−0.033〜−0.021）", "−0.003\n（−0.004〜−0.001）"],
        ["切片あり（探索）", "0.044", "−0.022", "−0.001"],
        ["ΔSI% のみ", "0.041", "−0.022", "─"],
        ["＋ΔHR%（探索）", "0.077", "−0.020", "−0.003"],
        ["ΔMAP% のみ", "0.139", "─", "─"],
    ]
    t2_diag = [
        ["症例内 r² 中央値", "0.101", "─", "─"],
        ["ΔSI% の符号の一致", "78%", "─", "─"],
        ["SI 10% で PWTT", "0.27%", "─", "─"],
    ]
    s = new_slide(prs, "主解析：前提検証", "結果", notes=notes(
        para(JA1, "主解析　862例・161,737ウィンドウにおいて"),
        para(JA1, "症例内のΔSI係数は78%の症例で"),
        "表2 の全行: 事前指定・原点通過 r² 0.000、β ΔSI% −0.027（−0.033〜−0.021）、"
        "β ΔRI% −0.003（−0.004〜−0.001）。切片あり（探索）0.044、−0.022（−0.027〜−0.016）、"
        "−0.001（−0.002〜−0.000）。ΔSI% のみ・原点通過 0.041、−0.022。"
        "ΔSI%＋ΔRI%＋ΔHR%（探索）0.077、−0.020、−0.003（β ΔHR% −0.057）。"
        "ΔMAP% のみ（探索）0.139。症例内診断は 症例内 r² 中央値 0.101、"
        "ΔSI% の符号が予測どおりの症例 78%、"
        "スティフネス指標が 10% 変化すると PWTT は 0.27% 変化する。"))
    x2, _ = chip(s, 0.55, 1.64, ["主解析"], BLUE)
    chip(s, x2 + 0.18, 1.64, ["プライマリーアウトカム"], BLUE)
    head2 = ["モデル", "r²", "β ΔSI%", "β ΔRI%"]
    if big:
        table(s, 0.55, 2.28, [3.35, 1.40, 3.75, 3.75], [head2] + t2_rows + t2_diag,
              pt=t_pt, line_h=0.40, bolds={1})
    else:
        table(s, 0.55, 2.28, [3.35, 1.40, 3.75, 3.75], [head2] + t2_rows,
              pt=t_pt, line_h=0.50, bolds={1})
        textbox(s, 0.55, 5.84, 12.25, 0.42, [
            ("症例内 r² 中央値 0.101・符号の一致 78%・SI 10% で PWTT 0.27%", 22, INK, False)],
            space_after=0, line_spacing=1.0)
    box(s, 0.55, 6.32, 12.25, 0.54, [
        ("前提は量的に成立しない。向きは検出できるが補正には小さすぎる", 24, RED, True)],
        fill=None, line=RED)
    source(s, "表2。括弧は 95% 信頼区間（症例単位ブートストラップ 2,000 回）")

    # ------------------------------------------------------------ 16 結果
    s = new_slide(prs, "何が PWTT を動かすか", "結果", notes=notes(
        para(JA1, "同じデータにおいて、平均血圧単独では0.139"),
        "棒の長さは切片を加えて再当てはめした決定係数に比例させた（血管指標 0.044、"
        "心拍数 0.081、平均血圧 0.139、測定した 4 変数 0.196）。"))
    bars = [("血管指標（ΔSI%・ΔRI%）", 0.044, VERM),
            ("心拍数", 0.081, BLUE),
            ("平均血圧", 0.139, BLUE),
            ("測定した 4 変数", 0.196, TEAL)]
    bar_x, bar_max, bar_w = 4.95, 0.196, 5.50
    for i, (nm, v, col) in enumerate(bars):
        y = 2.05 + i * 0.72
        textbox(s, 0.55, y, 4.30, 0.50, [(nm, 22, INK, False)],
                align=PP_ALIGN.RIGHT, space_after=0, line_spacing=1.0)
        w = bar_w * v / bar_max
        box(s, bar_x, y + 0.02, w, 0.46, [], fill=col, shape=MSO_SHAPE.RECTANGLE)
        textbox(s, bar_x + w + 0.14, y, 1.40, 0.50, [(f"{v:.3f}", 22, INK, True)],
                space_after=0, line_spacing=1.0)
    textbox(s, 0.55, 5.02, 12.25, 0.50, [
        ("自己相関 +0.75 から見積もった再現性のある成分は 56〜75%", 22, INK, False)],
        space_after=0, line_spacing=1.0)
    box(s, 0.55, 5.70, 12.25, 1.00, [
        ("PWTT は動いている。その動きを血管指標が捉えていない", 26, WHITE, True)],
        fill=BLUE)
    source(s, "切片を加えて再当てはめした決定係数。4 変数＝ΔSI%・ΔRI%・心拍数・平均血圧")

    # ------------------------------------------------------------ 17 結果
    s = new_slide(prs, "副次解析：一致度", "結果", notes=notes(
        para(JA1, "副次解析　血管補正は参照との一致度を改善しなかった"),
        "表4 の全行: 対照（PWTT のみ）26.9%、提案（血管補正）27.2%（差 +0.2 ポイント、"
        "95% CI +0.1〜+0.4）、対照＋平均血圧 27.0%（+0.3、+0.2〜+0.5）、"
        "対照＋血管指標＋平均血圧 27.1%（+0.3、+0.1〜+0.5）。"
        "補正推定器の Bland–Altman バイアス −0.07 L/min、"
        "一致限界 −3.28〜+3.14 L/min、4 象限一致率（除外帯 0.5 L/min）0.56。",
        "図4（Bland–Altman）は analysis/scripts/07_figures.py の fig4_accuracy で描く。"))
    x2, _ = chip(s, 0.55, 1.64, ["副次解析"], VERM)
    chip(s, x2 + 0.18, 1.64, ["セカンダリーアウトカム"], VERM)
    table(s, 0.55, 2.28, [3.00, 1.60, 3.00], [
        ["推定器", "誤差率", "対照との差"],
        ["対照\n（PWTT のみ）", "26.9%", "─"],
        ["提案\n（血管補正）", "27.2%", "+0.2\n（+0.1〜+0.4）"],
        ["対照＋平均血圧", "27.0%", "+0.3"],
        ["対照＋血管指標\n＋平均血圧", "27.1%", "+0.3"],
    ], pt=t_pt, line_h=0.42, bolds={2})
    fig_slot(s, "fig4_accuracy.png", 8.30, 2.28, 4.55, 3.35,
             ["図4　Bland–Altman", "Mac 1 で 07番を回して", "fig4_accuracy.png を挿入"],
             fig_dir, placed)
    textbox(s, 0.55, 5.75, 12.25, 1.15, [
        ("Bland–Altman バイアス −0.07 L/min・一致限界 −3.28〜+3.14 L/min", 22, INK, False),
        ("4 象限一致率 0.56　事前指定の無益性の規準に該当した", 22, INK, True),
        ("参照 CO の 98% が動脈圧波形由来なので、この結果だけでは解釈しない", 22, VERM, False)],
        space_after=1, line_spacing=1.05)
    source(s, "表4。症例単位の 5 分割交差検証。差は症例単位ブートストラップ 2,000 回")

    # ------------------------------------------------------------ 18 結果
    t5_rows_a = [
        ["主解析", "0.000", "−0.027", "78%", "+0.2"],
        ["開発 15 例を除外", "0.005", "−0.028", "78%", "+0.2"],
        ["5 分に集約", "─", "─", "─", "0.0"],
        ["20 分に集約", "─", "─", "─", "−0.2"],
        ["心拍数を加える", "0.077", "−0.020", "74%", "─"],
    ]
    t5_rows_b = [
        ["主解析", "862", "161,737", "0.000", "−0.027", "78%", "+0.2（+0.1〜+0.4）"],
        ["開発 15 例を除外", "847", "158,445", "0.005", "−0.028", "78%", "+0.2（+0.1〜+0.3）"],
        ["5 分に集約", "844", "31,934", "─", "─", "─", "0.0（−0.2〜+0.1）"],
        ["20 分に集約", "606", "6,838", "─", "─", "─", "−0.2（−0.5〜+0.0）"],
        ["心拍数を加える", "862", "161,737", "0.077", "−0.020", "74%", "─"],
    ]
    t6_rows = [
        ["主解析（再計算）", "862", "161,737", "0.000", "−0.027", "78%", "+0.2"],
        ["同一定義で再抽出", "862", "161,737", "0.000", "−0.027", "78%", "+0.2"],
        ["立ち上がり間の ΔT", "862", "161,297", "−0.041", "−0.004", "61%", "+0.1"],
        ["振幅母数の比 a2/a1", "862", "161,737", "−0.003", "−0.029", "77%", "+0.2"],
        ["成分の面積比", "862", "161,737", "−0.012", "−0.032", "81%", "+0.2"],
        ["3 成分分解", "858", "153,249", "−0.051", "−0.010", "67%", "+0.3"],
        ["雑音目標 0.002（厳）", "852", "144,112", "0.005", "−0.024", "77%", "+0.2"],
        ["雑音目標 0.004（緩）", "862", "161,542", "−0.001", "−0.029", "78%", "+0.2"],
        ["品質規準 5%（厳）", "852", "137,600", "−0.036", "−0.023", "75%", "+0.4"],
        ["品質規準 20%（緩）", "862", "161,297", "0.004", "−0.028", "78%", "+0.2"],
    ]
    s = new_slide(prs, "感度解析", "結果", notes=notes(
        para(JA1, "感度解析　パイプライン開発に用いた15例を除外しても"),
        "表5 の全行（解析・症例・ウィンドウ・前提 r²・β ΔSI%・符号の一致・ΔPE）:\n"
        + "\n".join("｜".join(r) for r in t5_rows_b)
        + "\n動脈圧波形と独立な参照 16 例（CardioQ 11・Vigilance II 5）の誤差率は"
          "対照 41.0%・提案 41.6%（記述のみ・検定はしない）。"
          "対照推定器の誤差率は 60 秒 26.9%・5 分 24.0%・20 分 21.8% と集約で下がった。",
        "表6 の全行（同じ列）:\n" + "\n".join("｜".join(r) for r in t6_rows)
        + "\n表6 の 9 通りを通じて前提の r² は −0.051 から 0.005、β ΔSI% は −0.004 から"
          "−0.032 の範囲で、ΔPE は +0.1 から +0.4 ポイント（95% CI はいずれも 0 を含まない）。"))
    if big:
        textbox(s, 0.55, 1.58, 12.25, 0.40, [
            ("9 通りすべてで補正は悪化。陰性は定義や規準の産物ではない", 22, RED, True)],
            space_after=0, line_spacing=1.0)
        table(s, 0.67, 2.06, [2.70, 1.00, 1.60, 1.20, 1.30, 1.40, 2.80],
              [["表5　感度解析", "症例", "ウィンドウ", "前提 r²", "β ΔSI%", "符号の一致",
                "ΔPE（95% CI）"]] + t5_rows_b, pt=t6_pt, line_h=0.27)
        table(s, 1.12, 3.78, [3.40, 1.00, 1.60, 1.30, 1.40, 1.40, 1.00],
              [["表6　再抽出を要する 9 通り", "症例", "ウィンドウ", "前提 r²", "β ΔSI%",
                "符号の一致", "ΔPE"]] + t6_rows, pt=t6_pt, line_h=0.27)
    else:
        table(s, 2.07, 2.25, [2.90, 1.40, 1.70, 1.90, 1.30],
              [["解析", "前提 r²", "β ΔSI%", "符号の一致", "ΔPE"]] + t5_rows_a,
              pt=t_pt, line_h=0.56)
        textbox(s, 0.55, 5.68, 12.25, 1.15, [
            ("表6（9 通り）　r² −0.051〜0.005・β ΔSI% −0.004〜−0.032", 22, INK, False),
            ("ΔPE +0.1〜+0.4　独立な参照 16 例は 41.0% 対 41.6%（記述）", 22, INK, False),
            ("9 通りすべてで補正は悪化。陰性は定義や規準の産物ではない", 22, RED, True)],
            space_after=1, line_spacing=1.05)
    source(s, "表5（再抽出を要さない感度解析）・表6（再抽出を要する 9 通り）")

    # ------------------------------------------------------------ 19 結果
    s = new_slide(prs, "探索1：PWTT の分解", "結果", notes=notes(
        para(JA1, "解析計画の凍結後に追加した探索的解析　全身血管抵抗との関連では"),
        "21番 節4（2026-09-13 追加・事後・記述）: 症例内 SD の中央値は T1 12.13 ms "
        "[IQR 9.19–15.81]、T2−T1 17.46 ms [IQR 13.69–23.60]、PWTT 19.00 ms "
        "[IQR 15.70–23.85]。2 区間の変化の症例内相関は Spearman −0.149（負の症例 70%）、"
        "Pearson −0.229（負の症例 77%）。分散分解では交差項 2·Cov が Var(ΔPWTT) の"
        "−0.221（症例中央値。全ウィンドウでは −0.416）を打ち消す。"
        "単独の r² の和 0.607 は両方を用いた 0.977 を下回るので、区間ごとの取り分は"
        "その打ち消しの分だけ歪んでおり、正確なのは合計だけである。"))
    box(s, 0.90, 1.72, 4.10, 0.64, [("T1　180 ms（166〜192）", 22, WHITE, True)],
        fill=BLUE, align=PP_ALIGN.CENTER, space_after=0)
    box(s, 5.10, 1.72, 7.30, 0.64, [("T2 − T1　前駆出期を含まない", 22, WHITE, True)],
        fill=VERM, align=PP_ALIGN.CENTER, space_after=0)
    poly(s, [(0.70, 2.48), (12.60, 2.48)], color=DGREY, width_pt=1.5)
    for xt in (0.90, 5.10, 12.40):
        tick(s, xt, 2.36, 2.60)
    label(s, 1.10, 2.92, "R 波", color=DGREY)
    label(s, 5.10, 2.92, "橈骨動脈圧の立ち上がり", color=DGREY)
    label(s, 11.60, 2.92, "指尖脈波の足", color=DGREY)
    textbox(s, 0.55, 3.30, 12.25, 2.16, [
        ("可測性の関門を通過　自己相関 +0.654・変動係数 0.037", 22, INK, False),
        ("Δ(T2−T1) を ΔT で説明した r² は 0.008（症例内 ρ +0.122）", 22, INK, False),
        ("ΔPWTT では +0.216。打ち消しによる陰性ではない", 22, INK, False),
        ("症例内 SD　T1 12.1 ms・T2−T1 17.5 ms・PWTT 19.0 ms", 22, INK, True),
        ("2 区間の変化は負に相関（Spearman −0.15・負の症例 70%）", 22, INK, False),
        ("区間ごとの取り分は歪む。厳密に成り立つのは合計だけである", 22, DGREY, False)],
        space_after=1, line_spacing=1.0)
    box(s, 0.55, 5.54, 12.25, 0.68, [
        ("末梢区間の SD 17.5 ms は伝播時間の生理的な幅 4〜16 ms を超える", 24, RED, True)],
        fill=None, line=RED)
    textbox(s, 0.55, 6.32, 12.25, 0.50, [
        ("動脈の伝播ではなく、光電容積脈波の立ち上がり時刻の変動である", 24, INK, True)],
        space_after=0, line_spacing=1.0)
    source(s, "21番（節4・事後・記述）。862 例・161,735 ウィンドウ")

    # ------------------------------------------------------------ 20 結果
    s = new_slide(prs, "探索2：指標を替える・SVR", "結果", notes=notes(
        para(JA1, "解析計画の凍結後に追加した探索的解析　全身血管抵抗との関連では"),
        "表7 の全行（いずれも被説明変数は ΔPWTT%・161,638 ウィンドウ）: "
        "ΔAm%（早期振幅比）原点通過 −0.105・切片あり 0.0002・係数 −0.030。"
        "ΔAm%＋ΔMAP% 0.094／0.141・−0.084／−0.078。"
        "ΔSI%＋ΔRI%（主解析の再計算）0.000／0.044・−0.027／−0.003。"
        "ΔMAP% のみ 0.088／0.139・−0.076。症例内診断は 符号の一致 ΔAm% 51%・ΔSI% 80%・"
        "ΔRI% 74%・ΔMAP% 89%、症例内 r² 中央値 0.027／0.051／0.041／0.110、"
        "症例内順位相関の中央値 −0.003／−0.216／−0.131／−0.363。"
        "自己相関は Am_b/Am_p1 0.394・SI 0.496・RI 0.431・平均血圧 0.695。",
        "37番: EV1000 の SVR を持つ症例で、逆向きのウィンドウだけに絞ると "
        "ρ(ΔRI%, ΔSVR%) は +0.031、ρ(ΔRI%, ΔMAP%) は +0.075 であった。"
        "この装置の SVR は（平均血圧−中心静脈圧）／CO で、CO が動脈圧波形由来のため"
        "部分的に循環しており、記述としてのみ用いる。"))
    table(s, 1.15, 1.70, [3.60, 2.70, 2.70, 2.00], [
        ["説明変数", "r²（切片あり）", "r²（原点通過）", "符号の一致"],
        ["ΔAm%（早期振幅比）", "0.0002", "−0.105", "51%"],
        ["ΔSI% ＋ ΔRI%", "0.044", "0.000", "80%"],
        ["ΔMAP% のみ", "0.139", "0.088", "89%"],
    ], pt=t_pt, line_h=0.54 if big else 0.56, bolds={1})
    textbox(s, 0.55, 4.06, 12.25, 0.50, [
        ("症例内 ρ −0.003・早期振幅比の自己相関 0.394（SI 0.496・RI 0.431）", 22, INK, False)],
        space_after=0, line_spacing=1.0)
    box(s, 0.55, 4.62, 12.25, 0.62, [
        ("妥当で同定できる指標に替えても前提は成立しない", 24, RED, True)],
        fill=None, line=RED)
    chip(s, 0.55, 5.38, ["SVR（探索）"], GREY)
    textbox(s, 0.55, 5.98, 12.25, 0.90, [
        ("204 例　RI × SVR +0.098（p 1.7e-05）・SI +0.049（p 0.14）", 22, INK, False),
        ("MAP × SVR +0.334　逆向きのウィンドウでは RI は SVR より MAP を追う", 22, INK, False)],
        space_after=1, line_spacing=1.05)
    source(s, "表7（36番）・37番。逆向きのウィンドウでは SVR +0.031 に対し MAP +0.075")

    # ------------------------------------------------------------ 21 考察
    s = new_slide(prs, "ΔT の陰性は測定の失敗でない", "考察", notes=notes(
        para(JA1, "タイミング指標については、この陰性の結果は測定の失敗ではない"),
        para(JA1, "陽性対照はΔTが血管情報を持つことを示すが")))
    grounds = [
        "① 陽性対照　加齢で短縮（ρ −0.197）・高血圧既往で短い（259 対 267 ms）",
        "② 自己相関　隣接ウィンドウで +0.50。再現性のある系列である",
        "③ 同定可能性　実データを見る前に、真値既知の合成脈波で確立した",
    ]
    for i, g in enumerate(grounds):
        box(s, 0.55, 1.80 + i * 0.86, 12.25, 0.72, [(g, 22, INK, False)],
            fill=PALE, line=DGREY, align=PP_ALIGN.LEFT, space_after=0)
    box(s, 0.55, 4.48, 12.25, 0.95, [
        ("PWTT との関係は、覆い隠されているのではなく存在しない", 26, WHITE, True)],
        fill=BLUE)
    textbox(s, 0.55, 5.66, 12.25, 1.10, [
        ("論文2　処理のない理想波形でも凍結版 ΔT は", 22, INK, False),
        ("大動脈脈波伝播速度と 0.22（特徴点法は 0.71）。概念の側の上限である", 22, INK, False)],
        space_after=2, line_spacing=1.1)
    source(s, "39）Charlton 2019（仮想被験者 4,374 名）。ΔT の陰性は信号源の産物ではない")

    # ------------------------------------------------------------ 22 考察
    s = new_slide(prs, "RI の妥当性を確立できない", "考察", notes=notes(
        para(JA1, "反射係数については妥当性を確立できず"),
        para(JA1, "どの種類の信号処理がこの特有のパターンを生みうるかを特定するため"),
        "08番の表（合成波形・32拍/条件。ΔT 誤差／RI 誤差／収束）: 生波形（対照）"
        "−0.3 ms／+0.7%／32/32。一律の利得正規化 −0.3 ms／+0.7%／32/32。"
        "高域通過 0.3 Hz −3.5 ms／−1.1%／32/32。高域通過 0.5 Hz −7.6 ms／−5.7%／32/32。"
        "高域通過 1.0 Hz −8.6 ms／−8.0%／3/32。拍内 AGC τ=1.00s −0.3 ms／+0.7%／32/32。"
        "τ=0.50s +31.2 ms／+28.0%／27/32。τ=0.25s −9.1 ms／+60.7%／20/32。"
        "τ=0.10s −33.4 ms／+103.9%／13/32。"))
    textbox(s, 0.55, 1.70, 12.25, 1.35, [
        ("症例内変動係数 0.680（ΔT の 3 倍）", 22, INK, True),
        ("血圧との結びつきは ΔT より弱く、年齢とも関連しない（文献上も弱い 18））", 22, INK, False),
        ("生理ではなく雑音の振る舞いである", 22, INK, False)],
        space_after=2, line_spacing=1.08)
    table(s, 1.55, 3.14, [4.60, 2.80, 2.80], [
        ["合成波形に当てた処理", "ΔT 誤差", "RI 誤差"],
        ["一律の利得正規化", "−0.3 ms", "+0.7%"],
        ["高域通過 0.3 Hz", "−3.5 ms", "−1.1%"],
        ["拍内で変わる利得 0.25 s", "−9.1 ms", "+60.7%"],
    ], pt=t_pt, line_h=0.54 if big else 0.56, bolds={3})
    textbox(s, 0.55, 5.56, 12.25, 1.30, [
        ("VitalDB がその処理をしている証拠ではない（機序を絞り込む実験）", 22, DGREY, False),
        ("振幅由来の指標が血管参照に対して機能しなかった報告の独立した再現 22）", 22, INK, False),
        ("論文2　処理のない波形でも凍結版 RI は末梢血管抵抗を追わない（0.21）", 22, INK, False)],
        space_after=1, line_spacing=1.05)
    source(s, "08番（合成波形・32拍/条件）　18）Millasseau 2006　22）Couceiro 2015")

    # ------------------------------------------------------------ 23 考察
    s = new_slide(prs, "生理学的な読みと文献", "考察", notes=notes(
        para(JA1, "生理学的には、本結果は異常ではなく機序に関する文献が予測するとおりである"),
        para(JA1, "通過時間の推定値を光電容積脈波由来の血管指標で補正するという戦略自体は新しくない")))
    box(s, 0.55, 1.72, 12.25, 0.60, [
        ("PWTT は純粋な血管の区間ではない", 24, WHITE, True)], fill=BLUE,
        align=PP_ALIGN.LEFT, space_after=0)
    textbox(s, 0.65, 2.40, 12.15, 1.60, [
        ("R 波起点の PWTT は前駆出期を含む 1）", 22, INK, False),
        ("心電図起点の通過時間は純粋な血管指標として不適 12,13）", 22, INK, False),
        ("前駆出期は交感神経賦活で数十 ms 振れる 15,16）", 22, INK, False),
        ("メーカー側の報告　前駆出期が PWTT 変化の約半分 4）", 22, INK, False)],
        space_after=2, line_spacing=1.08)
    box(s, 0.55, 4.12, 12.25, 0.60, [
        ("補正の戦略自体は新しくない", 24, WHITE, True)], fill=VERM,
        align=PP_ALIGN.LEFT, space_after=0)
    textbox(s, 0.65, 4.80, 12.15, 1.20, [
        ("カフレス血圧 26）・脈波形態 ＋ 脈波到達時間 27,28）", 22, INK, False),
        ("第2成分を末梢の反射に帰属できる保証はない 21）　成績は限定的 22）", 22, INK, False)],
        space_after=2, line_spacing=1.08)
    box(s, 0.55, 6.10, 12.25, 0.74, [
        ("貢献は、低かった成功の事前確率を測定された上限に変えたこと", 24, RED, True)],
        fill=None, line=RED)
    source(s, "1）4）12,13）15,16）21）22）26）27,28）　本研究の分解では T1 と末梢区間の変動は同じ桁")

    # ------------------------------------------------------------ 24 考察
    s = new_slide(prs, "限界", "考察", notes=notes(
        para(JA1, "本研究には複数の限界がある"),
        para(JA1, "公開波形データベースの利用者に対しては")))
    lims = [
        ["① 参照 CO の 98%（862 例中 846 例）が動脈圧波形由来である"],
        ["② 60 秒ウィンドウ　20〜30 分の移動平均を要するとの指摘 11）",
         "　　5 分・20 分に集約しても補正は精度を改善しなかった"],
        ["③ 単一データベース・単一施設・後ろ向き・血管運動負荷の統制なし"],
        ["④ 脈波は表示用の出力　フィルタは非公開・見かけの遅れ 660 ms",
         "　　装置の処理遅延は 460〜475 ms と見積もられる"],
        ["⑤ 脈波の立ち上がり検出の誤差は、すべて末梢区間の項に入る"],
    ]
    y = 1.74
    for ls in lims:
        h = 0.58 + 0.42 * (len(ls) - 1)
        box(s, 0.55, y, 12.25, h, [(t, 22, INK, False) for t in ls],
            fill=PALE, line=None, align=PP_ALIGN.LEFT, space_after=1, line_spacing=1.05)
        y += h + 0.16
    source(s, "11）Sugo 2025（移動平均）。独立した参照は肺動脈熱希釈 5 例と食道ドプラ 11 例")

    # ------------------------------------------------------------ 25 結論
    s = new_slide(prs, "結論", "結論", notes=notes(
        para(JA1, "大規模周術期波形データベースにおいて、拍ごとのPWTTの変動は"),
        para(JA1, "結論：光電容積脈波から得た血管指標でPWTT法の較正定数を補正する")))
    box(s, 0.55, 1.72, 12.25, 1.05, [
        ("前提は量的に成立しない", 28, WHITE, True),
        ("向きは検出できるが、補正に使うには小さすぎる", 24, WHITE, False)],
        fill=VERM, space_after=2)
    box(s, 0.55, 2.98, 12.25, 0.70, [
        ("RI はこの信号源では妥当性を確立できない", 24, WHITE, True)], fill=DGREY)
    textbox(s, 0.55, 3.90, 12.25, 2.45, [
        ("論文2　分解由来の指標は真値を追わず、特徴点法は追った", 22, INK, False),
        ("　→　限界は指標の取り出し方の側にある", 22, BLUE, True),
        ("妥当な指標（早期振幅比）に替えても前提は成立しない", 22, INK, False),
        ("　→　限界は指標の質だけでもない", 22, BLUE, True),
        ("末梢区間の変動は伝播の生理的な幅を超える", 22, INK, False),
        ("　→　通過時間の測定そのものが検討の対象になる", 22, VERM, True)],
        space_after=2, line_spacing=1.08)
    source(s, "862 例・161,737 ウィンドウ・事前登録（SAP doi:10.5281/zenodo.22167118・コード doi:10.5281/zenodo.22676038）")

    # ------------------------------------------------------------ 26 結論
    s = new_slide(prs, "今後", "結論", notes=notes(
        para(JA1, "通過時間型CO推定の系統的で血管状態に関連した誤差はよく記録されており"),
        "(1) 47番（ΔT と血圧の関連を心拍数で調整し、特徴点法と比べる解析）は台本と予測を"
        "固定済みで、実データはまだ回していない。"
        "(2) 論文3（実機のモニタ波形での可測性・840 例）は事前登録の凍結待ちである。"
        "スライド面には、出どころを照合できる数値だけを載せている。"))
    box(s, 0.55, 1.80, 12.25, 1.00, [
        ("ΔT と血圧の関連を心拍数で調整し、特徴点法と比べる", 24, WHITE, True),
        ("台本と予測は固定済み。実データはまだ回していない", 22, WHITE, False)],
        fill=BLUE, space_after=2)
    box(s, 0.55, 3.02, 12.25, 1.00, [
        ("論文3　実機のモニタ波形での可測性", 24, WHITE, True),
        ("事前登録の凍結待ち", 22, WHITE, False)], fill=TEAL, space_after=2)
    textbox(s, 0.55, 4.28, 12.25, 0.50, [
        ("より有望な方向", 24, INK, True)], space_after=0, line_spacing=1.0)
    for i, t in enumerate(("脈波の立ち上がりの計時と装置遅延",
                           "再較正の頻度を上げる",
                           "心臓側の項を直接測る（心音図・インピーダンス）")):
        box(s, 0.55, 4.84 + i * 0.66, 12.25, 0.58, [(t, 22, INK, False)],
            fill=PALE, line=None, align=PP_ALIGN.LEFT, space_after=0)
    source(s, "補正すべき量が補正変数と共変しないなら、指標を正確に測っても補正は機能しない")

    # ------------------------------------------------------------ 27・28 文献
    half = (len(CITED) + 1) // 2
    for k, (ttl, nums) in enumerate((("文献", CITED[:half]), ("文献（続き）", CITED[half:]))):
        s = new_slide(prs, ttl, notes=(
            "文献表は英文原稿 v2（docs/manuscript/v2/01_draft_en_v2.md）の References "
            "から起こし、著者（筆頭 et al.）・誌名・年;巻(号):頁 に短縮した。"
            "番号はその並びのままで、和文原稿の引用番号と同じである。"
            "スライドで引いた番号だけを載せた（" + "・".join(str(n) for n in CITED) + "）。"))
        textbox(s, 0.55, 1.80, 12.25, 4.60, [(REFS[n], 16, INK, False) for n in nums],
                space_after=4, line_spacing=1.15)
        source(s, "巻号・PMID・DOI を含む完全な記載は英文原稿 v2 の文献表にある")

    prs.save(out_path)
    return prs


# ============================================================ 自己検査
def verify(path):
    """lint が見ない所を自分で確かめる（表のセル幅・文字の取り出し・ノート・数値）。"""
    prs = Presentation(path)
    corpus = num_corpus()
    bad = []
    for i, slide in enumerate(prs.slides, 1):
        texts, has_tbl = [], False
        is_refs = bool(slide.shapes.title
                       and slide.shapes.title.text_frame.text.startswith("文献"))
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
        note = (slide.notes_slide.notes_text_frame.text
                if slide.has_notes_slide else "")
        if not note.strip():
            bad.append(f"p{i} ノートが空")
        if has_tbl and i == 1:
            bad.append("表紙に表がある")
        # 数値の照合（文献のスライドは番号の並びなので対象外）
        face = "\n".join(texts)
        if not is_refs:
            for tok in numbers_in(face):
                if not in_corpus(tok, corpus):
                    bad.append(f"p{i} 出どころの無い数値 「{tok}」")
        for w in DROP_WORDS:
            if w in face:
                bad.append(f"p{i} スライド面に「{w}」がある")
            if w in note:
                bad.append(f"p{i} ノートに「{w}」がある")
    return bad


def selftest():
    import shutil
    import tempfile
    ok = True
    from PIL import Image
    for v in ("A", "B"):
        with tempfile.TemporaryDirectory() as td:
            figs = os.path.join(td, "figs")
            os.makedirs(figs)
            for nm in ("fig3_quality.png", "fig4_accuracy.png"):
                Image.new("RGB", (880, 660), "white").save(os.path.join(figs, nm))
            for tag, fd in (("枠", os.path.join(td, "none")), ("画像", figs)):
                out = os.path.join(td, f"t{v}_{tag}.pptx")
                build(out, v, fd)
                bad = verify(out)
                small = count_small_table_runs(out)
                n = len(Presentation(out).slides._sldIdLst)
                print(f"版 {v}（図は{tag}）: {n} 枚・指摘 {len(bad)} 件"
                      f"・表の中の 22pt 未満 {small} 個")
                for b in bad:
                    print("   ", b)
                ok = ok and not bad
            shutil.rmtree(figs, ignore_errors=True)
    print("自己検査:", "通過" if ok else "不合格")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="論文1 の発表スライドを作る")
    ap.add_argument("--variant", choices=["A", "B"], default="A",
                    help="A=全文字22pt以上 / B=表だけ16〜18pt・表2・表5・表6 は全行")
    ap.add_argument("--out", default=None, help="出力する pptx")
    ap.add_argument("--fig-dir", default=DEFAULT_FIGDIR,
                    help="fig3_quality.png・fig4_accuracy.png を探す場所"
                         "（空文字を渡すと探さず、差し替えの指示の枠で組む）")
    ap.add_argument("--selftest", action="store_true", help="組んでから自分で確かめる")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    out = a.out or os.path.join(HERE, f"paper1_ja_{a.variant}.pptx")
    prs = build(out, a.variant, a.fig_dir)
    print(f"生成: {out}（{len(prs.slides._sldIdLst)} 枚・版 {a.variant}）")
    for line in PLACED:
        print("  図:", line)
    return 0


if __name__ == "__main__":
    sys.exit(main())

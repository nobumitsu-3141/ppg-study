# -*- coding: utf-8 -*-
"""新規スライドの共通土台と波形描画ユーティリティ"""
import math
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from deckkit import (clone_slide, strip_content, set_title, set_nav, set_source,
                     add_text, add_box, add_line, add_freeform, add_arrow,
                     set_notes, slide_index, INK, GOLD, BLUE, VERM, TEAL, RED,
                     GREY, LGREY)


class Builder:
    def __init__(self, prs, tpl_slide):
        self.prs = prs
        self.tpl = tpl_slide

    def new(self, after_slide, title, chapter, source=None, notes=None):
        idx = slide_index(self.prs, after_slide)
        s = clone_slide(self.prs, self.tpl, insert_after_idx=idx)
        strip_content(s)
        set_title(s, title)
        set_nav(s, chapter)
        set_source(s, source)
        from deckkit import set_pageno
        set_pageno(s, None)
        if notes:
            set_notes(s, notes)
        return s


# ------------------------------------------------------------ 波形ジェネレータ
def gauss(t, mu, sd, amp):
    return amp * math.exp(-((t - mu) ** 2) / (2 * sd * sd))


def ppg_curve(x0, y0, w, h, comps, n=170, baseline=0.0):
    """comps: [(mu, sd, amp)]  0<=t<=1 で合成し、(x,y) 点列を返す（yは下向き正のPPT座標）"""
    pts = []
    vals = []
    for i in range(n + 1):
        t = i / n
        v = baseline + sum(gauss(t, m, s, a) for (m, s, a) in comps)
        vals.append(v)
    vmax = max(vals) or 1.0
    for i, v in enumerate(vals):
        t = i / n
        pts.append((x0 + w * t, y0 + h - h * (v / vmax)))
    return pts


def comp_curve(x0, y0, w, h, comps, one, n=170):
    """合成波の最大値でスケールしたうえで、成分 one だけを描く"""
    vals = [sum(gauss(i / n, m, s, a) for (m, s, a) in comps) for i in range(n + 1)]
    vmax = max(vals) or 1.0
    pts = []
    m, s, a = one
    for i in range(n + 1):
        t = i / n
        v = gauss(t, m, s, a)
        pts.append((x0 + w * t, y0 + h - h * (v / vmax)))
    return pts


# 若年（切痕が明瞭）→ 高齢（切痕消失）の 4 型
WAVE_YOUNG = [(0.22, 0.085, 1.00), (0.58, 0.12, 0.46)]
WAVE_MID = [(0.22, 0.090, 1.00), (0.50, 0.13, 0.42)]
WAVE_OLD = [(0.23, 0.105, 1.00), (0.40, 0.15, 0.40)]
WAVE_FLAT = [(0.25, 0.130, 1.00), (0.36, 0.20, 0.34)]


def axis(slide, x, y, w, h, color=LGREY):
    add_line(slide, x, y + h, x + w, y + h, color=color, width=1.25)

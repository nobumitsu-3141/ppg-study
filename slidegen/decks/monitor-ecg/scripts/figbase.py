# -*- coding: utf-8 -*-
"""モニター心電図デック 図の共通基盤（パレット・フォント・図形ヘルパ）。
川副式 decklib と配色を統一。図は白背景・太線・最小テキスト。"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle, Polygon, Ellipse

# ---- fonts (Hiragino on macOS) ----
_FCANDS = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W7.ttc",
]
for _p in _FCANDS:
    if os.path.exists(_p):
        try: fm.fontManager.addfont(_p)
        except Exception: pass
REG  = "Hiragino Sans W3"
BOLD = "Hiragino Sans W6"
plt.rcParams["font.family"] = BOLD
plt.rcParams["axes.unicode_minus"] = False
FP      = FontProperties(family=REG)
FPB     = FontProperties(family=BOLD)

# ---- palette (matches decklib) ----
GOLD  = "#BF9000"; GOLDL = "#F2E2B3"; GOLDBG = "#F7ECCF"
TEAL  = "#00A8AA"; TEALD = "#00807F"
INK   = "#262626"
GRAY  = "#808080"; MGRAY = "#A6A6A6"; LGRAY = "#D9D9D9"
BLUE  = "#1F4E79"; BLUEL = "#DDEBF7"
ORANGE= "#8A3B00"; ORANGEL="#FBE5D6"
GREEN = "#548235"; GREENL = "#E2EFDA"
RED   = "#C00000"; REDL  = "#F8D7DA"
WHITE = "#FFFFFF"
# ECG graph-paper grid
GRID_MINOR = "#F0D9D9"
GRID_MAJOR = "#E3A9A9"

FIGDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figs")
FIGDIR = os.path.abspath(FIGDIR)

def newfig(w=9.4, h=5.2):
    fig, ax = plt.subplots(figsize=(w, h), dpi=200)
    fig.patch.set_facecolor("white"); ax.set_facecolor("white")
    return fig, ax

def clean(ax):
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_xticks([]); ax.set_yticks([])

def save(fig, name):
    os.makedirs(FIGDIR, exist_ok=True)
    fig.savefig(os.path.join(FIGDIR, f"{name}.png"), dpi=200,
                bbox_inches="tight", facecolor="white", pad_inches=0.08)
    plt.close(fig)

def T(ax, x, y, s, size=15, color=INK, ha="center", va="center", bold=True, rot=0, fp=None):
    ax.text(x, y, s, ha=ha, va=va, color=color, fontsize=size, rotation=rot,
            fontproperties=(fp if fp else (FPB if bold else FP)), zorder=6)

def box(ax, x, y, w, h, fc, ec="none", txt="", tc=INK, fs=15, bold=True,
        round=0.05, lw=1.4, ha="center", va="center", pad=0.012):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad={pad},rounding_size={round}",
                       fc=fc, ec=ec, lw=lw, zorder=3, mutation_aspect=1)
    ax.add_patch(p)
    if txt:
        tx = x+w/2 if ha=="center" else x+0.06
        T(ax, tx, y+h/2, txt, size=fs, color=tc, ha=ha, va=va, bold=bold)
    return p

def rect(ax, x, y, w, h, fc, ec="none", lw=1.4, z=3):
    r = Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw, zorder=z); ax.add_patch(r); return r

def arrow(ax, x1, y1, x2, y2, color=INK, lw=2.4, style="-|>", ms=15, ls="-", z=5):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=ms,
                        lw=lw, color=color, zorder=z, linestyle=ls, shrinkA=1, shrinkB=1)
    ax.add_patch(a); return a

def chip(ax, x, y, w, h, label, fc, tc=WHITE, fs=13.5):
    """small rounded tag."""
    return box(ax, x, y, w, h, fc, txt=label, tc=tc, fs=fs, round=0.5, pad=0.008)

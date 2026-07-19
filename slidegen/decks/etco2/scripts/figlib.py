"""Shared figure style + capnogram waveform model for the EtCO2 deck (川副式).
Palette matches the user's deck (gold accent4/75%, teal breadcrumb, Office accents)."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ---- Japanese font (macOS: Hiragino), with Latin-symbol fallbacks appended so
# glyphs Hiragino lacks (e.g. superscript minus in HCO3-) still render instead of
# tofu. matplotlib does per-glyph fallback across this list. NOTE: combining
# diacritics (e.g. V + COMBINING DOT ABOVE for "V-dot") are NOT reliably placed
# by matplotlib's text renderer even with a capable font (no glyph-positioning/
# shaping engine) — avoid them in figure text; write "VCO2" not "V̇CO₂".
plt.rcParams["font.family"]   = ["Hiragino Sans", "Hiragino Kaku Gothic ProN",
                                 "Hiragino Maru Gothic ProN", "Noto Sans CJK JP",
                                 "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["svg.fonttype"]  = "none"

# ---- output dir (local scratchpad figs) ----
OUTDIR = os.environ.get("ETCO2_FIGDIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "figs")))

# ---- palette ----
GOLD  = "#BF9000"   # title / key answer / emphasis
GOLDL = "#F2E2B3"   # gold tint
TEAL  = "#00A8AA"   # accent / active
INK   = "#262626"   # main line & text
GRAY  = "#8C8C8C"   # secondary
LGRAY = "#D9D9D9"
BLUE  = "#4472C4";  BLUEL  = "#BDD7EE"
ORANGE= "#ED7D31";  ORANGEL= "#F8CBAD"
GREEN = "#70AD47";  GREENL = "#C5E0B4"
RED   = "#C00000"
WHITE = "#FFFFFF"

def newfig(w=8.6, h=5.0):
    fig, ax = plt.subplots(figsize=(w, h), dpi=200)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    return fig, ax

def clean(ax):
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_xticks([]); ax.set_yticks([])

def save(fig, name):
    os.makedirs(OUTDIR, exist_ok=True)
    fig.savefig(os.path.join(OUTDIR, f"{name}.png"),
                dpi=200, bbox_inches="tight", facecolor="white", pad_inches=0.08)
    plt.close(fig)

def box(ax, x, y, w, h, fc, ec="none", txt="", tc=INK, fs=15, bold=True, round=0.06, lw=1.2, ha="center"):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.01,rounding_size={round}",
                       fc=fc, ec=ec, lw=lw, zorder=3, mutation_aspect=1)
    ax.add_patch(p)
    if txt:
        ax.text(x+w/2 if ha=="center" else x+0.04, y+h/2, txt, ha=ha, va="center",
                color=tc, fontsize=fs, fontweight="bold" if bold else "normal", zorder=4)
    return p

def arrow(ax, x1, y1, x2, y2, color=INK, lw=2.4, style="-|>", ms=16, ls="-"):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=ms,
                        lw=lw, color=color, zorder=5, linestyle=ls,
                        shrinkA=0, shrinkB=0)
    ax.add_patch(a)
    return a

# ---- capnogram (time-based) model ----
# One breath drawn as the classic trapezoid: phase I (dead-space baseline) ->
# phase II (steep expiratory upstroke) -> phase III (alveolar plateau, gentle
# upslope, ends at PetCO2) -> phase 0 (sharp inspiratory downstroke) -> baseline.
def capno_cycle(n=500, t1=0.14, t2=0.10, t3=0.46, down=0.10,
                base=0.0, p0=0.92, ptop=1.00):
    """Return x in [0,1] and y for ONE breath.
    t1/t2/t3 = phase I/II/III widths (fractions); remainder after `down` = inspiration.
    p0 = CO2 at plateau start, ptop = PetCO2 at plateau end (III upslope = ptop-p0)."""
    xs = [0.0, t1, t1+t2, t1+t2+t3, t1+t2+t3+down, 1.0]
    ys = [base, base, p0,   ptop,     base,          base]
    x = np.linspace(0.0, 1.0, n)
    return x, np.interp(x, xs, ys)

def capno_train(cycles=3, n=500, **kw):
    """Tile capno_cycle into `cycles` breaths over x in [0, cycles]."""
    x1, y1 = capno_cycle(n=n, **kw)
    X = np.concatenate([x1 + i for i in range(cycles)])
    Y = np.tile(y1, cycles)
    return X, Y

def sharkfin_cycle(n=500, t1=0.10, base=0.0, ptop=1.0):
    """Obstructive (bronchospasm/COPD): loss of the sharp II->III corner, the whole
    expiratory limb slopes up as a fin. Large alpha angle, no true plateau."""
    xs = [0.0, t1, 0.86, 0.96, 1.0]
    ys = [base, base, ptop, base, base]
    x = np.linspace(0.0, 1.0, n)
    # curve the expiratory limb for the concave 'fin' look
    y = np.interp(x, xs, ys)
    m = (x > t1) & (x < 0.86)
    frac = (x[m]-t1)/(0.86-t1)
    y[m] = base + (ptop-base)*(frac**1.7)
    return x, y

def one_cycle(n=500):
    return np.linspace(0.0, 1.0, n)

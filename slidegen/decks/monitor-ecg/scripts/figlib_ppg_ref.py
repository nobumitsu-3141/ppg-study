"""Shared figure style + PPG waveform model for the PPG deck.
Palette matches the user's deck (gold accent4/75%, teal breadcrumb, Office accents)."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ---- Japanese font ----
for p in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
          "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"]:
    try: fm.fontManager.addfont(p)
    except Exception: pass
plt.rcParams["font.family"]   = "Noto Sans CJK JP"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["svg.fonttype"]  = "none"

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
    fig.savefig(f"/sessions/compassionate-youthful-ritchie/mnt/outputs/figs/{name}.png",
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

# ---- PPG / pressure pulse model ----
def ppg_wave(t, ts=0.30, ws=0.085, A=1.0,
             tr=0.62, wr=0.14, B=0.42, base=0.0):
    """forward (systolic) + reflected (diastolic) gaussians -> pulse with dicrotic notch."""
    fwd = A*np.exp(-((t-ts)**2)/(2*ws**2))
    ref = B*np.exp(-((t-tr)**2)/(2*wr**2))
    # small foot rise
    foot = 0.06*np.exp(-((t-0.16)**2)/(2*0.05**2))
    return base + fwd + ref + foot, fwd, ref

def one_cycle(n=600):
    return np.linspace(0.0, 1.0, n)

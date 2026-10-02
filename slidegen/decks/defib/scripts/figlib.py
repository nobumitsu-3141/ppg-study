"""Shared figure style + waveform models for the defibrillator/DC deck (川副式).
Palette matches the user's deck (gold accent4/75%, teal breadcrumb, Office accents).

Primitives (newfig/clean/save/box/arrow/txt helpers) are unchanged from the EtCO2
deck. The DOMAIN MODELS below are defibrillator-specific and are the clinically
load-bearing part of the figures — ECG with R-sync markers, VF/VT/asystole, the
monophasic vs biphasic shock pulse shapes, and pacing capture / false-capture.
Keep these correct; make_figs.py composes them into the slide figures."""
import os, logging
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ---- Japanese font (macOS: Hiragino Sans, present on this machine), with Latin
# fallbacks appended for glyphs Hiragino lacks. matplotlib does per-glyph fallback.
# NOTE: combining diacritics are NOT reliably placed by matplotlib's text renderer
# — avoid them in figure text. Silence the benign per-glyph findfont chatter.
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
plt.rcParams["font.family"]   = ["Hiragino Sans", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["svg.fonttype"]  = "none"

# ---- output dir (deck figs) ----
OUTDIR = os.environ.get("DEFIB_FIGDIR",
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
RED   = "#C00000";  REDL   = "#F4C7C3"
WHITE = "#FFFFFF"

# ---- figure primitives ----
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

# ================================================================= ECG model =====
def _gauss(x, mu, sig, amp):
    return amp * np.exp(-((x - mu) ** 2) / (2 * sig ** 2))

def ecg_beat(x, r0=0.5, twave=0.25, narrow=True):
    """One PQRST complex over local x in [0,1), R peak at r0 (amp ~1.0).
    narrow=True: normal sinus QRS; narrow=False: wide (paced/VT-like) complex."""
    y = np.zeros_like(x)
    y += _gauss(x, r0 - 0.19, 0.022, 0.13)          # P
    if narrow:
        y += _gauss(x, r0 - 0.028, 0.008, -0.10)    # Q
        y += _gauss(x, r0, 0.011, 1.00)             # R (sharp/narrow)
        y += _gauss(x, r0 + 0.030, 0.010, -0.22)    # S
    else:
        y += _gauss(x, r0, 0.030, 1.00)             # broad R
        y += _gauss(x, r0 + 0.055, 0.030, -0.35)    # broad S
    y += _gauss(x, r0 + 0.17, 0.035, twave)         # T
    return y

def ecg_train(n=1400, beats=4, r0=0.5, narrow=True, twave=0.25):
    """`beats` regular sinus beats over X in [0, beats]. R peaks at integer + r0.
    Returns X, Y, r_positions (list of R-peak x for placing sync markers)."""
    X = np.linspace(0, beats, n)
    Y = np.zeros_like(X)
    for b in range(beats):
        xr = X - b
        m = (xr >= 0) & (xr < 1)
        Y[m] += ecg_beat(xr[m], r0=r0, twave=twave, narrow=narrow)
    return X, Y, [b + r0 for b in range(beats)]

def t_peak_positions(beats=4, r0=0.5):
    """T-wave peak x positions (the vulnerable-period target) for the same train."""
    return [b + r0 + 0.17 for b in range(beats)]

# ---- arrhythmia rhythms (deterministic; seeded so figures are reproducible) ----
def vf_wave(n=1600, span=6.0, coarse=True, seed=7):
    """Ventricular fibrillation: chaotic, no discernible P/QRS/T. coarse vs fine."""
    rng = np.random.default_rng(seed)
    X = np.linspace(0, span, n)
    Y = (0.60 * np.sin(2 * np.pi * 3.3 * X)
         + 0.40 * np.sin(2 * np.pi * 5.9 * X + 1.0)
         + 0.30 * np.sin(2 * np.pi * 8.7 * X + 2.1)
         + 0.20 * np.sin(2 * np.pi * 12.5 * X + 0.7))
    Y += 0.30 * rng.standard_normal(n)
    Y = np.convolve(Y, np.ones(5) / 5, mode="same")
    Y = Y / np.max(np.abs(Y))
    return X, (0.95 if coarse else 0.40) * Y

def vt_wave(n=1400, span=6.0, rate=3.4):
    """Monomorphic VT: regular, wide, uniform sine-like complexes (no P)."""
    X = np.linspace(0, span, n)
    Y = np.sin(2 * np.pi * rate * X)
    Y = np.sign(Y) * np.abs(Y) ** 0.75          # broaden the peaks (wide QRS look)
    return X, 0.92 * Y

def torsades_wave(n=1600, span=6.0, rate=5.0, twist=0.5):
    """Polymorphic VT / torsades: sinusoid with a slowly rotating (spindle) envelope."""
    X = np.linspace(0, span, n)
    env = 0.35 + 0.65 * np.abs(np.sin(np.pi * twist * X))   # spindle amplitude envelope
    Y = env * np.sin(2 * np.pi * rate * X)
    return X, 0.95 * Y / np.max(np.abs(Y))

def asystole_wave(n=900, span=6.0, seed=3):
    """Asystole: near-flat line with minimal baseline wander (a SHOCK-NON-indication)."""
    rng = np.random.default_rng(seed)
    X = np.linspace(0, span, n)
    Y = 0.02 * rng.standard_normal(n)
    Y = np.convolve(Y, np.ones(9) / 9, mode="same")
    return X, Y

def pea_wave(n=1400, beats=5, span=None):
    """PEA: organized-looking (often wide/brady) complexes on the monitor but NO pulse
    — a SHOCK-NON-indication. Returns a slow wide-complex train."""
    beats = beats
    X = np.linspace(0, beats, n)
    Y = np.zeros_like(X)
    for b in range(beats):
        xr = X - b
        m = (xr >= 0) & (xr < 1)
        Y[m] += ecg_beat(xr[m], r0=0.5, twave=0.18, narrow=False) * 0.7
    return X, Y

# ================================================= defibrillation shock pulses ====
def mono_damped_sine(n=500, dur=1.0):
    """Monophasic damped sinusoidal (Edmark-type) waveform: single dominant polarity,
    a rising then decaying lobe. Current stays (essentially) one direction."""
    t = np.linspace(0, dur, n)
    y = np.exp(-2.6 * t) * np.sin(np.pi * t / (dur * 0.55))
    y[t > dur * 0.9] = 0
    y = np.clip(y, 0, None)                      # keep it (near) unipolar
    return t, y / np.max(y)

def biphasic_trunc_exp(n=500, dur=1.0, ph1=0.55):
    """Biphasic truncated exponential (BTE): decaying positive phase, then a shorter
    decaying NEGATIVE phase (polarity reversal). The defining 2-phase shape."""
    t = np.linspace(0, dur, n)
    y = np.zeros_like(t)
    m1 = t < dur * ph1
    y[m1] = np.exp(-2.2 * (t[m1] / (dur * ph1)))                       # + phase, truncated
    m2 = ~m1
    y[m2] = -0.62 * np.exp(-2.2 * ((t[m2] - dur * ph1) / (dur * (1 - ph1))))  # - phase
    y[t > dur * 0.94] = 0                                              # truncation to 0
    return t, y / np.max(np.abs(y))

# ============================================================= transcutaneous pacing
def pacing_ecg(n=1600, beats=5, capture=True, false_capture=False, spike0=0.15):
    """Transcutaneous pacing strip.
      capture=True        -> each pacer spike is followed by a WIDE paced QRS + T (true capture)
      capture=False       -> pacer spikes with NO ventricular response (failure to capture)
      false_capture=True  -> spikes followed by a narrow/small artifact deflection that can be
                             MISTAKEN for capture on the monitor but has no real depolarization
                             (the "pseudo-capture" trap — confirm mechanically, not on ECG).
    Returns X, Y, spike_positions (draw spikes as thin tall vertical lines in make_figs)."""
    X = np.linspace(0, beats, n)
    Y = np.zeros_like(X)
    spikes = []
    for b in range(beats):
        sx = b + spike0
        spikes.append(sx)
        if capture and not false_capture:
            xr = X - b
            m = (xr >= spike0) & (xr < 1)
            Y[m] += (_gauss(X[m], sx + 0.10, 0.032, -0.95)   # broad paced QRS (down)
                     + _gauss(X[m], sx + 0.34, 0.055, 0.34))  # broad T
        elif false_capture:
            m = (X >= sx) & (X < sx + 0.12)
            Y[m] += _gauss(X[m], sx + 0.05, 0.018, 0.18)      # tiny artifact only
    return X, Y, spikes

# ----------------------------------------------------------------- convenience ----
def draw_ecg(ax, X, Y, x0, x1, ymid, yscale, color=INK, lw=2.2, zorder=4):
    """Map a model waveform (X in [0,span], Y in ~[-1,1]) into an axes window
    [x0,x1] horizontally, centered at ymid with half-height yscale."""
    span = X.max() - X.min()
    xx = x0 + (X - X.min()) / span * (x1 - x0)
    ax.plot(xx, ymid + Y * yscale, color=color, lw=lw, zorder=zorder,
            solid_joinstyle="round", solid_capstyle="round")
    return xx

def sync_marker(ax, xpos, ytop, ybot=None, color=TEAL, lw=2.0):
    """Draw a SYNC marker (small triangle/tick above an R wave)."""
    if ybot is None: ybot = ytop - 0.25
    ax.plot([xpos, xpos], [ybot, ytop], color=color, lw=lw, zorder=6)
    ax.scatter([xpos], [ytop], marker="v", s=42, color=color, zorder=7)

# -*- coding: utf-8 -*-
import numpy as np
from matplotlib.patches import FancyBboxPatch, Arc, Circle, Polygon, Rectangle, Wedge
import figlib as F
from fighelp import *

# ==================================================================== local helpers ====
# (Schematic glyphs not covered by figlib's clinical waveform models. ECG/VF/VT/torsades/
#  asystole/PEA/pacing all go through figlib per the deck's rule; these helpers only draw
#  generic shapes: heart silhouette, reentry swirl, body/person icons, a hand-drawn pulse
#  bump train for the arterial/SpO2 waveform (not a figlib model).)

def heart_shape(ax, cx, cy, w, h, fc, ec, lw=2.0, zorder=2, hatch=None, alpha=1.0):
    """Simple schematic heart silhouette (parametric heart curve), centered at (cx,cy),
    bounding box roughly w x h."""
    t = np.linspace(0, 2 * np.pi, 200)
    xs = 16 * np.sin(t) ** 3
    ys = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)
    xs = xs / 16.0
    ys = (ys - ys.min()) / (ys.max() - ys.min()) - 0.5
    pts = list(zip(cx + xs * w, cy + ys * h))
    p = Polygon(pts, closed=True, fc=fc, ec=ec, lw=lw, zorder=zorder, hatch=hatch, alpha=alpha)
    ax.add_patch(p)
    return p

def swirl(ax, cx, cy, r, color, start=0, extent=250, lw=2.2, zorder=5, ry=None):
    """A curved 'reentry wavelet' arrow: an arc with a small triangular arrowhead at
    its leading tip. Used schematically for chaotic reentry loops (not a figlib model —
    this is a generic geometric glyph, not an ECG/VF/VT waveform)."""
    if ry is None:
        ry = r * 0.8
    t1, t2 = np.radians(start), np.radians(start + extent)
    ts = np.linspace(t1, t2, 40)
    xs = cx + r * np.cos(ts)
    ys = cy + ry * np.sin(ts)
    ax.plot(xs, ys, color=color, lw=lw, zorder=zorder, solid_capstyle="round")
    tx, ty = xs[-1] - xs[-2], ys[-1] - ys[-2]
    n = np.hypot(tx, ty); tx, ty = tx / n, ty / n
    px, py = -ty, tx
    ex, ey = xs[-1], ys[-1]
    tip = (ex + tx * 0.14 * r, ey + ty * 0.14 * r)
    b1 = (ex - px * 0.10 * r, ey - py * 0.10 * r)
    b2 = (ex + px * 0.10 * r, ey + py * 0.10 * r)
    ax.add_patch(Polygon([tip, b1, b2], closed=True, fc=color, ec="none", zorder=zorder + 1))

def reentry8(ax, cx, cy, r, color, lw=2.0, zorder=5):
    """Figure-of-eight reentry glyph: two adjoining swirl loops."""
    swirl(ax, cx - r * 0.55, cy, r * 0.6, color, start=200, extent=250, lw=lw, zorder=zorder)
    swirl(ax, cx + r * 0.55, cy, r * 0.6, color, start=20, extent=250, lw=lw, zorder=zorder)

def person_icon(ax, cx, cy, scale, color, zorder=3):
    """Tiny stick-figure body icon (head + trapezoid torso) used as a row marker."""
    ax.add_patch(Circle((cx, cy + 0.30 * scale), 0.14 * scale, fc=color, ec="none", zorder=zorder))
    body = Polygon([(cx - 0.20 * scale, cy - 0.35 * scale), (cx + 0.20 * scale, cy - 0.35 * scale),
                     (cx + 0.13 * scale, cy + 0.14 * scale), (cx - 0.13 * scale, cy + 0.14 * scale)],
                    closed=True, fc=color, ec="none", zorder=zorder)
    ax.add_patch(body)

def torso(ax, cx, cy, w, h, fc, ec, lw=1.8, zorder=2):
    """Simple front-view torso silhouette: rounded rectangle body + circular head."""
    body = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h * 0.80,
                           boxstyle=f"round,pad=0.01,rounding_size={w * 0.16}",
                           fc=fc, ec=ec, lw=lw, zorder=zorder)
    ax.add_patch(body)
    ax.add_patch(Circle((cx, cy + h * 0.40 + h * 0.11), h * 0.11, fc=fc, ec=ec, lw=lw, zorder=zorder))
    return body

def pulse_bump(ax, x0, x1, ymid, yscale, centers, width, color=F.INK, lw=2.2, zorder=4):
    """Hand-drawn arterial/SpO2 pulse-wave bump train (not an ECG/VF/VT model — figlib has
    no pulse-waveform model, so this generic shape is drawn directly). `centers` are x
    positions (data coords, already in [x0,x1]) where a pulse upstroke begins."""
    xs_all, ys_all = [], []
    lo = np.linspace(x0, x1, 30)
    xs_all.append(lo); ys_all.append(np.zeros_like(lo))
    for c in sorted(centers):
        xs = np.linspace(c, min(c + width, x1), 40)
        frac = (xs - c) / width
        y = np.where(frac <= 1, (np.sin(np.pi * np.clip(frac, 0, 1)) ** 0.7)
                      * (1 - 0.18 * np.clip(frac, 0, 1)), 0.0)
        xs_all.append(xs); ys_all.append(y)
    xx = np.concatenate(xs_all); yy = np.concatenate(ys_all)
    order = np.argsort(xx)
    xx, yy = xx[order], yy[order]
    ax.plot(xx, ymid + yy * yscale, color=color, lw=lw, zorder=zorder, solid_joinstyle="round")

def group_frame(ax, x, y, w, h, color, label, fc="white", zorder=1):
    return rbox(ax, x, y, w, h, fc, color, txt_lines=None, title=label, title_color=color,
                title_fs=14, lw=2.2, round_=0.10)

def flowbox(ax, x, y, w, h, fc, ec, lines, colors=None, fs=10.5, lw=1.8, zorder=1):
    """Rounded box with 1-2 lines of text placed by explicit vertical centering (does not
    use rbox's fixed title/txt_line offsets, which overflow short boxes). Used for the
    compact flowchart steps in f0404 where box height is tight."""
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.01,rounding_size={min(w, h) * 0.14}",
                        fc=fc, ec=ec, lw=lw, zorder=zorder)
    ax.add_patch(p)
    n = len(lines)
    lh = 0.30
    cy0 = y + h / 2 + (n - 1) / 2 * lh
    for i, ln in enumerate(lines):
        col = colors[i] if colors else F.INK
        ax.text(x + w / 2, cy0 - i * lh, ln, ha="center", va="center", color=col,
                fontsize=fs, fontweight="bold", zorder=zorder + 3)
    return p


# ======================================================================== CH3 (作用) ====

def f0301():
    """3.1 critical mass hypothesis: VF (chaotic reentry) -> shock (uniform depolarization,
    critical mass) -> return of sinus rhythm; plus a depolarized-mass threshold bar."""
    fig, ax = canvas(9.5, 4.3, 11, 5)

    P1X, P2X, P3X = 1.85, 5.5, 9.15
    HY = 3.3

    # ---- panel 1: VF (chaotic reentry) ----
    heart_shape(ax, P1X, HY, 2.5, 2.6, fc="white", ec=F.INK, lw=2.0, zorder=2)
    swirl(ax, P1X - 0.35, HY + 0.35, 0.55, F.RED, start=10, extent=260)
    swirl(ax, P1X + 0.45, HY + 0.15, 0.45, F.RED, start=140, extent=260)
    swirl(ax, P1X - 0.15, HY - 0.45, 0.5, F.RED, start=260, extent=250)
    swirl(ax, P1X + 0.35, HY - 0.55, 0.4, F.RED, start=60, extent=260)
    ax.add_patch(Circle((P1X + 0.75, HY + 1.05), 0.13, fc=F.GRAY, ec="none", zorder=4))
    txt(ax, P1X + 0.75, HY + 1.32, "SA", color=F.GRAY, fs=10, bold=True)
    txt(ax, P1X, 1.85, "多数のリエントリー波\n（無秩序興奮）", color=F.RED, fs=10, bold=True)

    # ---- discharge arrow panel1 -> panel2 (shock) ----
    shock_bolt(ax, (P1X + P2X) / 2, HY + 0.55, size=0.42, color=F.RED)
    F.arrow(ax, P1X + 1.4, HY, P2X - 1.35, HY, color=F.RED, lw=4.0, ms=22)

    # ---- panel 2: shock -> uniform depolarization (critical mass) ----
    heart_shape(ax, P2X, HY, 2.5, 2.6, fc=F.GOLDL, ec=F.GOLD, lw=2.2, zorder=2, hatch="////")
    txt(ax, P2X, 1.85, "critical mass（臨界量）を\n同時に脱分極＝一斉に不応期", color=F.GOLD, fs=10, bold=True)

    # ---- progression arrow panel2 -> panel3 ----
    F.arrow(ax, P2X + 1.4, HY, P3X - 1.35, HY, color=F.INK, lw=2.6, ms=18)

    # ---- panel 3: SA regains control, sinus rhythm resumes ----
    heart_shape(ax, P3X, HY, 2.5, 2.6, fc=F.GOLDL, ec=F.INK, lw=2.0, zorder=2, alpha=0.45)
    ax.add_patch(Circle((P3X + 0.75, HY + 1.05), 0.15, fc=F.GOLD, ec="none", zorder=4))
    txt(ax, P3X + 0.75, HY + 1.32, "SA", color=F.GOLD, fs=10, bold=True)
    F.arrow(ax, P3X + 0.75, HY + 0.88, P3X, HY + 0.35, color=F.GOLD, lw=2.2, ms=14)
    txt(ax, P3X, 1.85, "洞結節が主導権を回復", color=F.GOLD, fs=10, bold=True)
    ecg_in(ax, P3X - 1.05, P3X + 1.05, HY - 1.05, 0.30, beats=2, narrow=True, twave=0.22, lw=1.6)

    # ---- concept bar: depolarized myocardial mass vs critical-mass threshold ----
    BX0, BX1, BY0, BY1 = 0.5, 10.5, 0.25, 1.15
    THR = BX0 + (BX1 - BX0) * 0.56
    ax.add_patch(Rectangle((BX0, BY0), THR - BX0, BY1 - BY0, fc=F.REDL, ec="none", zorder=1))
    ax.add_patch(Rectangle((THR, BY0), BX1 - THR, BY1 - BY0, fc=F.GREENL, ec="none", zorder=1))
    ax.plot([THR, THR], [BY0 - 0.05, 1.12], color=F.GOLD, lw=2.2, ls="--", zorder=3)
    txt(ax, THR, 1.30, "臨界量", color=F.GOLD, fs=11, bold=True)
    F.arrow(ax, BX0, BY0 - 0.15, BX1, BY0 - 0.15, color=F.GRAY, lw=1.6, ms=12)
    txt(ax, BX0, BY0 - 0.32, "脱分極した心筋量 →増加", color=F.GRAY, fs=9.5, ha="left")
    txt(ax, (BX0 + THR) / 2, (BY0 + BY1) / 2, "一部だけ\n→波が生き残り再びVF", color=F.RED, fs=9.5, bold=True)
    txt(ax, (THR + BX1) / 2, (BY0 + BY1) / 2, "大部分\n→伝播先を失い消える", color=F.GREEN, fs=9.5, bold=True)

    ax.set_xlim(0, 11); ax.set_ylim(0, 5)
    F.save(fig, "f0301")


def f0302():
    """3.2 DFT / ULV dose-response sigmoid: success probability vs relative shock strength."""
    fig, ax = canvas(9.5, 4.3, 11, 5)
    X0, X1 = 1.0, 9.6
    Y0, Y1 = 0.9, 3.6
    B1, B2 = 3.9, 7.1   # band boundaries (weak | DFT-adequate | excessive)

    ax.add_patch(Rectangle((X0, Y0), B1 - X0, Y1 - Y0, fc=F.REDL, ec="none", zorder=1))
    ax.add_patch(Rectangle((B1, Y0), B2 - B1, Y1 - Y0, fc=F.GREENL, ec="none", zorder=1))
    ax.add_patch(Rectangle((B2, Y0), X1 - B2, Y1 - Y0, fc=F.ORANGEL, ec="none", zorder=1))

    # axes
    ax.plot([X0 - 0.2, X1 + 0.2], [Y0, Y0], color=F.INK, lw=1.6, zorder=2)
    ax.plot([X0 - 0.2, X0 - 0.2], [Y0 - 0.05, Y1 + 0.1], color=F.INK, lw=1.6, zorder=2)
    txt(ax, X0 - 0.45, Y0, "0", color=F.GRAY, fs=10, ha="right")
    txt(ax, X0 - 0.45, Y1, "100", color=F.GRAY, fs=10, ha="right")
    txt(ax, X0 - 0.75, (Y0 + Y1) / 2, "除細動\n成功確率(%)", color=F.GRAY, fs=10, ha="center")

    # sigmoid curve
    xs = np.linspace(X0, X1, 300)
    x0c = 5.5
    frac = 1 / (1 + np.exp(-1.05 * (xs - x0c)))
    ys = Y0 + frac * (Y1 - Y0)
    ax.plot(xs, ys, color=F.INK, lw=2.6, zorder=4, solid_capstyle="round")

    # DFT / ULV marker (dashed line kept short so it doesn't cross either label above the plot)
    ax.plot([x0c, x0c], [Y0, Y1 + 0.05], color=F.GOLD, lw=2.2, ls="--", zorder=3)
    txt(ax, x0c, Y1 + 0.75, "除細動閾値(DFT)", color=F.GOLD, fs=12, bold=True)
    txt(ax, x0c, Y1 + 0.35, "ULV（上限脆弱性）≒ DFT", color=F.GOLD, fs=10)

    # left foot: failed shock -> re-VF
    F.arrow(ax, 1.7, 2.15, 1.7, Y0 + 0.35, color=F.RED, lw=2.2, ms=14)
    Xv, Yv = F.vf_wave(n=200, span=1.0, coarse=False, seed=11)
    ax.plot(1.35 + Xv * 0.7, 1.55 + Yv * 0.28, color=F.RED, lw=1.4, zorder=4)
    txt(ax, 1.7, 3.2, "弱すぎ→再VF", color=F.RED, fs=10.5, bold=True)

    txt(ax, B1 + (B2 - B1) * 0.16, 3.2, "DFT以上→\n確実に停止", color=F.GREEN, fs=10, bold=True)
    txt(ax, (B2 + X1) / 2, 3.2, "強すぎ→心筋障害", color=F.ORANGE, fs=10.5, bold=True)
    txt(ax, X1 - 0.3, Y1 + 0.55, "⚡過大", color=F.ORANGE, fs=12, bold=True)

    # supplemental box: biphasic advantage
    rbox(ax, 7.2, 0.95, 3.3, 1.05, F.BLUEL, F.BLUE,
         txt_lines=["二相性＝インピーダンス補償で", "低エネルギー・高成功率、障害も少"],
         tc=F.INK, fs=9.5)

    txt(ax, X0 + (X1 - X0) / 2, 0.15, "ショック強度（相対）　※数値目盛は相対（具体的なJは第4章）",
        color=F.GRAY, fs=10)

    ax.set_xlim(0, 11); ax.set_ylim(0, 5)
    F.save(fig, "f0302")


def f0303():
    """3.3 vulnerable period / R on T: action potential (top) aligned with surface ECG
    (bottom) on a shared time axis; T-wave apex = relative refractory (vulnerable) period."""
    fig, ax = canvas(9.5, 4.3, 11, 5)
    X0, X1 = 1.0, 5.6
    span = X1 - X0

    # refractory bands (shared time axis, drawn behind both traces)
    b_abs = (0.05, 0.60)   # absolute refractory: upstroke..early repolarization
    b_rel = (0.60, 0.85)   # relative refractory / vulnerable period
    for (t0, t1), col in [(b_abs, F.BLUEL), (b_rel, F.REDL)]:
        ax.add_patch(Rectangle((X0 + t0 * span, 2.90), (t1 - t0) * span, 1.80, fc=col, ec="none", zorder=1))

    txt(ax, 0.55, 4.90, "活動電位(AP)", color=F.INK, fs=12, bold=True, ha="left")
    txt(ax, X0 + 0.32 * span, 4.55, "絶対不応期（興奮しない）", color=F.BLUE, fs=9)
    txt(ax, X0 + 0.75 * span, 4.55, "相対不応期＝脆弱期", color=F.RED, fs=9.5, bold=True)

    # ---- action potential (hand-drawn schematic; not an ECG/VF/VT model) ----
    t = np.linspace(0, 1, 400)
    ap = np.where(t < 0.05, -1.0,
         np.where(t < 0.08, -1.0 + (t - 0.05) / 0.03 * 2.0,
         np.where(t < 0.45, 1.0 - 0.15 * (t - 0.08) / 0.37,
         np.where(t < 0.85, 0.85 - 1.85 * np.clip((t - 0.45) / 0.40, 0, 1) ** 1.4,
                   -1.0))))
    AP_Y, AP_S = 3.9, 0.55
    ax.plot(X0 + t * span, AP_Y + ap * AP_S, color=F.INK, lw=2.4, zorder=4)

    txt(ax, 0.55, 2.85, "体表ECG", color=F.INK, fs=12, bold=True, ha="left")

    # ---- surface ECG single beat (figlib model: ecg_beat) ----
    Xe = np.linspace(0, 1, 400)
    Ye = F.ecg_beat(Xe, r0=0.5, twave=0.30, narrow=True)
    ECG_Y, ECG_S = 1.7, 0.85
    xs_ecg = X0 + Xe * span
    ax.plot(xs_ecg, ECG_Y + Ye * ECG_S, color=F.INK, lw=2.2, zorder=4, solid_joinstyle="round")
    tmask = (Xe >= 0.58) & (Xe <= 0.80)
    ax.plot(xs_ecg[tmask], ECG_Y + Ye[tmask] * ECG_S, color=F.RED, lw=2.8, zorder=5)

    t_peak_x = X0 + 0.67 * span
    shock_bolt(ax, t_peak_x, 3.05, size=0.30, color=F.RED)
    txt(ax, t_peak_x + 0.55, 3.05, "R on T", color=F.RED, fs=11, bold=True)

    # ---- branch: -> VF / polymorphic VT ----
    F.arrow(ax, X1 + 0.05, ECG_Y, 6.35, ECG_Y, color=F.RED, lw=2.4, ms=16)
    Xt, Yt = F.torsades_wave(n=400, span=1.0, rate=6.0, twist=0.8)
    ax.plot(6.45 + Xt * 2.35, ECG_Y + Yt * 0.55, color=F.RED, lw=2.0, zorder=4)
    reentry8(ax, 6.9, ECG_Y + 1.15, 0.35, F.RED, lw=1.8)
    txt(ax, 7.6, ECG_Y + 1.15, "→ VF／多形性VT", color=F.RED, fs=11, bold=True)

    # widened slightly (3.6->3.9, using the clear margin to the canvas edge at x=11) and
    # fs reduced a touch (10->8.6): the longer line was wider than the original box
    rbox(ax, 7.0, 0.30, 3.9, 1.10, F.GOLDL, F.GOLD,
         txt_lines=['脈のある頻拍＝T波を避けるため"同期"が必須', "VF＝避けるべきT波がない"],
         tc=F.INK, fs=8.6)

    ax.set_xlim(0, 11); ax.set_ylim(0, 5)
    F.save(fig, "f0303")


def f0304():
    """3.4 asynchronous defibrillation vs synchronized cardioversion: two ECG strips on a
    shared timeline — VF discharged at any instant vs a regular tachycardia SYNC'd to R."""
    fig, ax = canvas(9.5, 4.3, 11, 5)
    X0, X1 = 2.3, 10.6

    # ---- top strip: async (VF) ----
    TY, TS = 4.00, 0.50
    Xv, Yv = F.vf_wave(n=1200, span=6.0, coarse=True, seed=7)
    wave_in(ax, Xv, Yv, X0, X1, TY, TS, color=F.INK, lw=2.0)
    dx = X0 + (X1 - X0) * 0.55
    ax.plot([dx, dx], [TY - TS * 1.05, TY + TS * 1.55], color=F.RED, lw=3.0, zorder=6)
    shock_bolt(ax, dx, TY + TS * 1.80, size=0.28, color=F.RED)
    txt(ax, dx + 0.30, TY + TS * 1.80, "任意のタイミングで即放電（R波・T波がない）", color=F.RED, fs=9, ha="left")
    txt(ax, 1.15, TY, "非同期＝除細動\n（VF/無脈性VT）", color=F.GOLD, fs=11, bold=True)

    # ---- middle gutter note ----
    txt(ax, (X0 + X1) / 2, 2.60, '同じ機械・同じ放電。違いは"R波に合わせるか"だけ', color=F.GOLD, fs=11, bold=True)

    # ---- bottom strip: sync (cardioversion) ----
    BY, BS = 1.00, 0.50
    rx = ecg_in(ax, X0, X1, BY, BS, beats=4, narrow=False, twave=0.32,
                color=F.INK, lw=2.0, mark_r=True, mark_t=True, mark_color=F.TEAL)
    shock_x = rx[1]
    ax.plot([shock_x, shock_x], [BY + BS * 1.05, BY + BS * 2.15], color=F.RED, lw=3.0, zorder=7)
    shock_bolt(ax, shock_x, BY + BS * 2.40, size=0.28, color=F.RED)
    txt(ax, shock_x + 0.30, BY + BS * 2.40, "R波に同期して放電", color=F.RED, fs=9.5, ha="left")
    txt(ax, rx[0] - 0.30, BY + BS * 1.55, "SYNCマーカー＝各R波を検出", color=F.TEAL, fs=9, ha="left")
    txt(ax, 1.15, BY, "同期＝カルディオバージョン\n（脈あり頻拍）", color=F.GOLD, fs=11, bold=True)

    ax.set_xlim(0, 11); ax.set_ylim(0, 5)
    F.save(fig, "f0304")


def f0305():
    """3.5 pacing capture: left = output ladder (below/above threshold), right = electrical
    capture (ECG) confirmed against mechanical capture (pulse waveform)."""
    fig, ax = canvas(9.5, 4.3, 11, 5)

    # ---- left: output ladder ----
    txt(ax, 2.7, 4.78, "典型40–90 mA・レート60–80/min", color=F.GRAY, fs=10)
    ax.plot([1.0, 1.0], [0.5, 4.35], color=F.INK, lw=1.8, zorder=2)
    F.arrow(ax, 1.0, 4.1, 1.0, 4.45, color=F.INK, lw=1.8, ms=12)
    txt(ax, 0.55, 2.5, "出力\nmA\n(低→高)", color=F.INK, fs=9.5, ha="center")

    THR_Y = 2.5
    ax.plot([1.0, 4.5], [THR_Y, THR_Y], color=F.GOLD, lw=2.0, ls="--", zorder=3)
    txt(ax, 4.2, THR_Y, "閾値+約10%\nで維持", color=F.GOLD, fs=8.5, ha="left", bold=True)

    pacing_in(ax, 1.35, 4.35, 1.35, 0.42, beats=3, capture=False, color=F.INK)
    txt(ax, 2.85, 2.05, "捕捉なし（閾値未満）", color=F.RED, fs=10.5, bold=True)

    pacing_in(ax, 1.35, 4.35, 3.65, 0.42, beats=3, capture=True, color=F.INK)
    txt(ax, 2.85, 4.10, "電気的捕捉（閾値以上）", color=F.GOLD, fs=10.5, bold=True)

    # ---- right: two-tier capture confirmation ----
    RX0, RX1 = 5.35, 10.5
    txt(ax, (RX0 + RX1) / 2, 4.30, "①電気的捕捉（モニタ上）", color=F.GOLD, fs=11, bold=True)
    spikes = pacing_in(ax, RX0, RX1, 3.50, 0.55, beats=5, capture=True, color=F.INK)

    txt(ax, (RX0 + RX1) / 2, 2.75, "②機械的捕捉＝有効な脈（触知・SpO2波形・A-line）", color=F.GOLD, fs=11, bold=True)
    row_w = (RX1 - RX0) / 5.0
    centers = [sx + row_w * 0.18 for sx in spikes]
    pulse_bump(ax, RX0, RX1, 1.85, 0.48, centers, width=row_w * 0.55, color=F.TEAL, lw=2.2)

    # fs reduced (9.5->8.3): the longer line was wider than the box
    rbox(ax, RX0, 0.25, RX1 - RX0, 0.95, "white", F.RED,
         txt_lines=["偽捕捉に注意：スパイク＋筋収縮アーチファクトがQRS様でも",
                    "脈がないことがある→必ず脈で確認"],
         tc=F.RED, fs=8.3)

    ax.set_xlim(0, 11); ax.set_ylim(0, 5)
    F.save(fig, "f0305")


# ======================================================================== CH4 (除細) ====

def f0401():
    """4.1 shockable (VF, pulseless VT) vs non-shockable (PEA, asystole) — 4 stacked strips
    inside two colour-framed groups. Rhythm tags sit in a left margin column (not centred
    over the group-frame title) so nothing crosses the waveforms or the frame label."""
    fig, ax = canvas(9.5, 4.3, 11, 5)
    txt(ax, 5.5, 4.90, "脈なし＋VF/無脈性VT＝即ショック", color=F.GOLD, fs=12, bold=True)

    group_frame(ax, 0.4, 2.55, 10.2, 2.15, F.RED, "ショック適応（脈なし＝ショック）")
    group_frame(ax, 0.4, 0.20, 10.2, 2.20, F.TEAL, "ショック非適応（CPRへ）")

    WX0, WX1 = 1.65, 10.05  # waveform x-range (left of this: rhythm tag column)

    # row 1: VF (coarse -> fine)
    Y1 = 3.85
    Xc, Yc = F.vf_wave(n=800, span=1.0, coarse=True, seed=7)
    wave_in(ax, Xc, Yc, WX0, 5.75, Y1, 0.25, color=F.INK, lw=1.7)
    Xf, Yf = F.vf_wave(n=800, span=1.0, coarse=False, seed=7)
    wave_in(ax, Xf, Yf, 5.95, WX1, Y1, 0.25, color=F.INK, lw=1.7)
    txt(ax, 0.75, Y1, "①VF", color=F.GOLD, fs=11, bold=True)
    txt(ax, (WX0 + WX1) / 2, 3.40, "粗いVF → 細いVF（時間経過で振幅低下）", color=F.GOLD, fs=9)

    # row 2: pulseless VT (monomorphic / polymorphic)
    Y2 = 3.05
    Xm, Ym = F.vt_wave(n=700, span=1.0, rate=4.0)
    wave_in(ax, Xm, Ym, WX0, 5.65, Y2, 0.22, color=F.INK, lw=1.7)
    Xp, Yp = F.torsades_wave(n=700, span=1.0, rate=6.0, twist=1.0)
    wave_in(ax, Xp, Yp, 5.95, WX1, Y2, 0.22, color=F.INK, lw=1.7)
    txt(ax, 0.75, Y2, "②無脈性VT", color=F.GOLD, fs=10, bold=True)
    txt(ax, 3.75, 2.65, "単形性", color=F.BLUE, fs=9.5, bold=True)
    txt(ax, 7.95, 2.65, "多形性", color=F.BLUE, fs=9.5, bold=True)

    # row 3: PEA
    Y3 = 1.62
    Xpea, Ypea = F.pea_wave(n=700, beats=5)
    wave_in(ax, Xpea, Ypea, WX0, WX1, Y3, 0.24, color=F.INK, lw=1.7)
    txt(ax, 0.75, Y3, "③PEA", color=F.TEAL, fs=10, bold=True)
    txt(ax, 9.55, 1.92, "脈：なし", color=F.RED, fs=10, bold=True)
    txt(ax, (WX0 + WX1) / 2, 1.20, "波形はあるが脈がない→ショックしても無効", color=F.TEAL, fs=9)

    # row 4: asystole
    Y4 = 0.70
    Xa, Ya = F.asystole_wave(n=500, span=1.0, seed=3)
    wave_in(ax, Xa, Ya, WX0, WX1, Y4, 0.18, color=F.INK, lw=1.7)
    txt(ax, 0.75, Y4, "④心静止", color=F.TEAL, fs=10, bold=True)
    txt(ax, (WX0 + WX1) / 2, 0.32, "ショック非適応→CPR", color=F.TEAL, fs=9.5, bold=True)

    ax.set_xlim(0, 11); ax.set_ylim(0, 5)
    F.save(fig, "f0401")


def f0402():
    """4.2 energy settings table: adult biphasic / adult monophasic / paediatric
    (weight-linked), plus the escalation & default-to-max warning band."""
    fig, ax = canvas(9.5, 4.3, 11, 5)

    TX, TY, TW, TH = 1.6, 1.55, 8.6, 2.35
    rows = [
        [("成人\n二相性", F.BLUE), ("120–200 J\n(不明なら最大)", F.GOLD), ("同等以上", F.GOLD), ("機種の最大まで", F.GOLD)],
        [("成人\n単相性", F.BLUE), ("360 J", F.GOLD), ("360 J", F.GOLD), ("360 J\n(初回から最大)", F.GOLD)],
        [("小児\n(体重連動)", F.BLUE), ("2 J/kg", F.GOLD), ("4 J/kg\n(以後 ≥4 J/kg)", F.GOLD), ("10 J/kg\nまたは成人量", F.RED)],
    ]
    xs, rh = table(ax, TX, TY, TW, TH, ["方式", "初回", "2回目以降", "上限・注意"], rows,
                   col_w=[1.7, 2.2, 2.5, 2.2], fs=10.5, header_fs=12)

    icon_y = [TY + TH - rh * 1.5, TY + TH - rh * 2.5, TY + TH - rh * 3.5]
    person_icon(ax, 0.95, icon_y[0], 0.72, F.BLUE)
    person_icon(ax, 0.95, icon_y[1], 0.72, F.BLUE)
    person_icon(ax, 0.95, icon_y[2], 0.46, F.BLUE)

    rbox(ax, 0.6, 0.35, 9.9, 1.0, "white", F.RED,
         txt_lines=["2回目以降のエネルギーは前回と同等か高く／機種推奨が不明なら最初から最大"],
         tc=F.RED, fs=11, align="center")
    txt(ax, 5.55, 0.55, "小児上限＝10 J/kg または成人量を超えない", color=F.RED, fs=9.5)

    ax.set_xlim(0, 11); ax.set_ylim(0, 5)
    F.save(fig, "f0402")


def f0403():
    """4.3 single shock + immediate CPR timeline (ACLS): rhythm check -> charge (compressions
    continue) -> clear -> 1 shock -> resume compressions immediately -> CPR 2 min -> loop."""
    fig, ax = canvas(9.5, 4.3, 11, 5)
    txt(ax, 5.5, 4.92, "1回ショック→即CPR 2分→リズム確認", color=F.GOLD, fs=12.5, bold=True)

    ax.add_patch(Rectangle((0.35, 3.95), 9.25, 0.32, fc=F.GOLDL, ec=F.GOLD, lw=1.2, zorder=1))
    txt(ax, 5.0, 4.11, "中断（ハンズオフ）は最小＝10秒以内", color=F.GOLD, fs=10.5, bold=True)

    YMID, YH = 2.35, 1.0
    rbox(ax, 0.35, YMID - YH / 2, 1.70, YH, "white", F.INK, title="リズム確認", title_fs=11.5,
         txt_lines=["VF/無脈性VT"], fs=9.0)
    F.arrow(ax, 2.10, YMID, 2.30, YMID, color=F.INK, lw=2.2, ms=14)

    rbox(ax, 2.30, YMID - YH / 2, 1.70, YH, F.GREENL, F.GREEN, title="充電", title_fs=11.5,
         txt_lines=["（圧迫継続）"], fs=9.5)
    F.arrow(ax, 4.05, YMID, 4.20, YMID, color=F.INK, lw=2.2, ms=14)

    ax.add_patch(Rectangle((4.28, 1.70), 0.18, 1.30, fc=F.RED, ec="none", zorder=3))
    txt(ax, 4.37, 3.20, "離れて\n(clear)", color=F.RED, fs=9.5, bold=True)
    F.arrow(ax, 4.55, YMID, 4.75, YMID, color=F.INK, lw=2.2, ms=14)

    shock_bolt(ax, 5.0, YMID, size=0.45, color=F.RED)
    txt(ax, 5.0, 1.45, "ショック 1回", color=F.RED, fs=10.5, bold=True)
    F.arrow(ax, 5.35, YMID, 7.25, YMID, color=F.GOLD, lw=2.4, ms=16)
    txt(ax, 6.3, 2.90, "ただちに胸骨圧迫を再開\n（脈チェックしない）", color=F.INK, fs=9.5, bold=True)

    rbox(ax, 7.30, YMID - YH / 2, 2.30, YH, F.GREENL, F.GREEN, title="CPR 2分", title_fs=11.5,
         txt_lines=["(30:2 または連続圧迫+換気)"], fs=8.4)

    ax.plot([9.60, 9.60], [YMID + YH / 2, 4.55], color=F.GOLD, lw=2.2, zorder=2)
    ax.plot([9.60, 1.20], [4.55, 4.55], color=F.GOLD, lw=2.2, zorder=2)
    F.arrow(ax, 1.20, 4.55, 1.20, YMID + YH / 2 + 0.02, color=F.GOLD, lw=2.2, ms=16)
    txt(ax, 6.9, 4.38, "2分ごとに再評価", color=F.GOLD, fs=10)

    rbox(ax, 3.85, 0.20, 2.55, 0.85, "white", F.RED, txt_lines=None, title="連続スタックは非推奨",
         title_color=F.RED, title_fs=10)
    big_x(ax, 5.1, 0.40, size=0.14, color=F.RED, lw=3.2)

    ax.set_xlim(0, 11); ax.set_ylim(0, 5)
    F.save(fig, "f0403")


def f0404():
    """4.4 shockable vs non-shockable branch (Y-flow): rhythm check splits into VF/pVT
    (shock side, red) vs PEA/asystole (no-shock side, teal), both looping back. Row bands
    are computed bottom-up so the diagonal 'split' arrows have dedicated clear space and
    never cross the top box's own title text."""
    fig, ax = canvas(9.5, 4.3, 11, 5)

    TOPY0, TOPY1 = 4.08, 4.68
    ARROW_GAP, ROW_H, GAP = 0.30, 0.55, 0.10

    row0_top = TOPY0 - ARROW_GAP
    row0_bot = row0_top - ROW_H
    row1_top = row0_bot - GAP
    row1_bot = row1_top - ROW_H
    row2_top = row1_bot - GAP
    row2_bot = row2_top - ROW_H
    row3_top = row2_bot - GAP
    row3_bot = row3_top - ROW_H
    ROWS = [(row0_bot, row0_top), (row1_bot, row1_top), (row2_bot, row2_top), (row3_bot, row3_top)]

    rbox(ax, 4.2, TOPY0, 2.6, TOPY1 - TOPY0, F.GOLDL, F.GOLD, title="リズム確認で2つに分ける",
         title_color=F.GOLD, title_fs=10.3)

    F.arrow(ax, 4.6, TOPY0 - 0.03, 2.85, row0_top + 0.03, color=F.RED, lw=2.2, ms=14)
    F.arrow(ax, 6.4, TOPY0 - 0.03, 8.15, row0_top + 0.03, color=F.TEAL, lw=2.2, ms=14)

    LX, LW = 0.8, 3.6
    RX, RW = 6.6, 3.6

    def step(x, y0, y1, w, fc, ec, lines, colors, fs=9.5):
        flowbox(ax, x, y0, w, y1 - y0, fc, ec, lines, colors=colors, fs=fs)

    step(LX, *ROWS[0], LW, "white", F.RED, ["ショック適応", "(VF/無脈性VT)"], [F.RED, F.RED])
    step(RX, *ROWS[0], RW, "white", F.TEAL, ["ショック非適応", "(PEA/心静止)"], [F.TEAL, F.TEAL])
    step(LX, *ROWS[1], LW, F.REDL, F.RED, ["ショック 1回"], [F.RED], fs=11)
    step(RX, *ROWS[1], RW, F.GREENL, F.TEAL, ["CPR 2分", "(ショックしない)"], [F.INK, F.INK])
    step(LX, *ROWS[2], LW, F.GREENL, F.RED, ["CPR 2分"], [F.INK], fs=11)
    step(RX, *ROWS[2], RW, "white", F.TEAL, ["アドレナリン", "できるだけ早く(以後3-5分ごと)"], [F.TEAL, F.INK], fs=9)
    step(LX, *ROWS[3], LW, "white", F.RED, ["アドレナリン＋抗不整脈", "(難治例)"], [F.RED, F.INK], fs=9)
    step(RX, *ROWS[3], RW, "white", F.TEAL, ["可逆的原因(H&T)を是正"], [F.TEAL], fs=9.5)

    for i in range(3):
        F.arrow(ax, LX + LW / 2, ROWS[i][0] - 0.02, LX + LW / 2, ROWS[i + 1][1] + 0.02, color=F.RED, lw=2.0, ms=13)
        F.arrow(ax, RX + RW / 2, ROWS[i][0] - 0.02, RX + RW / 2, ROWS[i + 1][1] + 0.02, color=F.TEAL, lw=2.0, ms=13)

    # loop back to rhythm check (side arcs, meeting the top box at mid-height on each side)
    TOPMID = (TOPY0 + TOPY1) / 2
    LOOPY = ROWS[3][0] - 0.10
    ax.plot([LX + 0.15, 0.30], [LOOPY, LOOPY], color=F.RED, lw=2.0, zorder=2)
    ax.plot([0.30, 0.30], [LOOPY, TOPMID], color=F.RED, lw=2.0, zorder=2)
    F.arrow(ax, 0.30, TOPMID, 4.15, TOPMID, color=F.RED, lw=2.0, ms=13)

    ax.plot([RX + RW - 0.15, 10.70], [LOOPY, LOOPY], color=F.TEAL, lw=2.0, zorder=2)
    ax.plot([10.70, 10.70], [LOOPY, TOPMID], color=F.TEAL, lw=2.0, zorder=2)
    F.arrow(ax, 10.70, TOPMID, 6.85, TOPMID, color=F.TEAL, lw=2.0, ms=13)
    txt(ax, 5.5, 4.90, "2分ごとに再評価", color=F.GOLD, fs=10)

    # AED note (right-bottom) + H&T list (left-bottom) — manual line placement (not rbox's
    # title/txt_lines offsets, which overflow a box this short at 5 lines of content)
    INFOY1 = ROWS[3][0] - 0.15
    INFOY0 = INFOY1 - 0.90
    rbox(ax, 6.9, INFOY0, 3.75, INFOY1 - INFOY0, F.BLUEL, F.BLUE)
    txt(ax, 8.775, INFOY1 - 0.18, "AED", color=F.BLUE, fs=11, bold=True)
    txt(ax, 8.775, INFOY1 - 0.44, "機械が自動でVF/VTを解析し", color=F.INK, fs=9)
    txt(ax, 8.775, INFOY1 - 0.66, '"ショックが必要です"を音声誘導', color=F.INK, fs=9)

    rbox(ax, 0.15, INFOY0, 6.55, INFOY1 - INFOY0, "white", F.BLUE)
    txt(ax, 3.425, INFOY1 - 0.18, "可逆的原因 H&T", color=F.BLUE, fs=11, bold=True, ha="center")
    # Each H/T category used to be 5 separate stacked lines at a 0.115 line-step, but
    # the actual glyph height at fs8.2 (~0.17) is bigger than that step, so all 5 lines
    # rendered on top of each other (illegible). Same 10 items, same H/T grouping and
    # wording, just laid out as one combined line per category so they fit legibly.
    h_line = "H：低酸素・循環血液量減少・アシドーシス(H+)・低/高カリウム・低体温"
    t_line = "T：緊張性気胸・心タンポナーデ・中毒(Toxins)・血栓(肺塞栓)・血栓(冠動脈)"
    txt(ax, 0.40, INFOY1 - 0.42, h_line, color=F.INK, fs=8.2, ha="left")
    txt(ax, 0.40, INFOY1 - 0.68, t_line, color=F.INK, fs=8.2, ha="left")

    ax.set_xlim(0, 11); ax.set_ylim(0, 5)
    F.save(fig, "f0404")


def f0405():
    """4.5 pad placement: anterolateral (standard, sternal-right + left mid-axillary) vs
    anteroposterior (front + back) — current vector through the cardiac silhouette."""
    fig, ax = canvas(9.5, 4.3, 11, 5)

    # ---- left: anterolateral (standard) ----
    torso(ax, 2.3, 2.75, 2.6, 3.0, fc="#F2F2F2", ec=F.INK, lw=1.8)
    heart_shape(ax, 1.95, 2.55, 1.1, 1.2, fc=F.REDL, ec=F.GRAY, lw=1.0, zorder=2, alpha=0.55)
    p1 = (2.55, 3.55)  # right sternal border, upper
    p2 = (1.55, 1.65)  # left mid-axillary, 5th ICS
    ax.add_patch(Rectangle((p1[0] - 0.22, p1[1] - 0.16), 0.44, 0.32, fc="white", ec=F.INK, lw=1.5, zorder=4))
    ax.add_patch(Rectangle((p2[0] - 0.22, p2[1] - 0.16), 0.44, 0.32, fc="white", ec=F.INK, lw=1.5, zorder=4))
    F.arrow(ax, p1[0] - 0.15, p1[1] - 0.15, p2[0] + 0.15, p2[1] + 0.15, color=F.RED, lw=3.0, ms=18)
    txt(ax, p1[0] + 0.75, p1[1] + 0.15, "胸骨右縁上部", color=F.BLUE, fs=9.5, ha="left")
    txt(ax, p2[0] - 0.20, p2[1] - 0.35, "左中腋窩線\n第5肋間", color=F.BLUE, fs=9.5, ha="right")
    txt(ax, 2.3, 4.55, "前側方（標準）", color=F.GOLD, fs=12, bold=True)
    txt(ax, 2.3, 0.75, "電流が心陰影（左室）を貫く", color=F.GOLD, fs=10)

    # ---- right: anteroposterior ----
    torso(ax, 6.5, 2.75, 2.1, 2.9, fc="#F2F2F2", ec=F.INK, lw=1.8)
    heart_shape(ax, 6.25, 2.55, 0.95, 1.05, fc=F.REDL, ec=F.GRAY, lw=1.0, zorder=2, alpha=0.55)
    pf = (5.95, 2.30)
    ax.add_patch(Rectangle((pf[0] - 0.20, pf[1] - 0.14), 0.40, 0.28, fc="white", ec=F.INK, lw=1.5, zorder=4))
    txt(ax, 6.5, 4.55, "前後（可）", color=F.TEAL, fs=12, bold=True)
    txt(ax, 5.6, 1.15, "前＝左前胸部\n（心尖側）", color=F.BLUE, fs=9, ha="right")

    torso(ax, 9.4, 2.75, 2.1, 2.9, fc="#F2F2F2", ec=F.GRAY, lw=1.8)
    pb = (9.15, 3.35)
    ax.add_patch(Rectangle((pb[0] - 0.20, pb[1] - 0.14), 0.40, 0.28, fc="white", ec=F.GRAY, lw=1.5, ls="--", zorder=4))
    txt(ax, 9.9, 1.15, "後＝左肩甲骨下\n（背部）", color=F.BLUE, fs=9, ha="left")
    F.arrow(ax, pf[0] + 0.65, pf[1] + 0.10, pb[0] - 0.75, pb[1] - 0.10, color=F.RED, lw=2.6, ms=16)
    txt(ax, 7.9, 3.95, "前後も可（AF・カルディオバージョン・\nCIED回避で有利）", color=F.TEAL, fs=9.5, bold=True)

    txt(ax, 5.5, 0.20, "パッド同士を接触させない／貼付薬・水分・体毛は除去", color=F.GRAY, fs=9.5)

    ax.set_xlim(0, 11); ax.set_ylim(0, 5)
    F.save(fig, "f0405")

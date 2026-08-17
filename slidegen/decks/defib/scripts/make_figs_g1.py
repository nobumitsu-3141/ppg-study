# -*- coding: utf-8 -*-
import numpy as np
from matplotlib.patches import FancyBboxPatch, Arc, Circle, Polygon, Rectangle, Wedge
import figlib as F
from fighelp import *

# ------------------------------------------------------------- small icons --
def _ellipse(ax, cx, cy, rx, ry, fc, ec, lw=1.6, zorder=2):
    """Filled ellipse via a polygon approximation (Ellipse patch is not imported)."""
    th = np.linspace(0, 2 * np.pi, 72)
    pts = list(zip(cx + rx * np.cos(th), cy + ry * np.sin(th)))
    ax.add_patch(Polygon(pts, closed=True, fc=fc, ec=ec, lw=lw, zorder=zorder))

def _person(ax, x, y, s=0.32, color=F.GRAY, zorder=4):
    """Very simple person glyph: round head + trapezoid body."""
    ax.add_patch(Circle((x, y + 0.62 * s), 0.30 * s, fc=color, ec="none", zorder=zorder))
    pts = [(x - 0.34 * s, y - 0.55 * s), (x + 0.34 * s, y - 0.55 * s),
           (x + 0.22 * s, y + 0.30 * s), (x - 0.22 * s, y + 0.30 * s)]
    ax.add_patch(Polygon(pts, closed=True, fc=color, ec="none", zorder=zorder))

def _clock(ax, x, y, r=0.16, color=F.INK, zorder=4):
    ax.add_patch(Circle((x, y), r, fc="white", ec=color, lw=1.2, zorder=zorder))
    ax.plot([x, x], [y, y + r * 0.6], color=color, lw=1.3, zorder=zorder + 1)
    ax.plot([x, x + r * 0.5], [y, y], color=color, lw=1.3, zorder=zorder + 1)

def _dial(ax, x, y, r=0.20, color=F.INK, zorder=4):
    ax.add_patch(Circle((x, y), r, fc="white", ec=color, lw=1.3, zorder=zorder))
    ax.plot([x, x + r * 0.7], [y, y + r * 0.55], color=color, lw=1.6, zorder=zorder + 1)


# =========================================================== front matter =
def f00_hero():
    """Hero band under the title: SYNC-marked sinus ECG (left) -> biphasic shock pulse
    (right), thin gold/ink. No text (deck adds the title/caption separately)."""
    fig, ax = canvas(14.0, 2.4, W=14, H=2.4)
    ecg_in(ax, 0.3, 8.5, 1.25, 0.80, beats=4, narrow=True, twave=0.22,
           color=F.INK, lw=2.0, mark_r=True, mark_color=F.GOLD)
    ax.plot([8.95, 8.95], [0.35, 2.15], color=F.LGRAY, lw=1.2, ls=":", zorder=2)
    t, y = F.biphasic_trunc_exp()
    wave_in(ax, t, y, 9.35, 13.6, 1.25, 0.85, color=F.GOLD, lw=2.6)
    F.save(fig, "f00_hero")


# ================================================================ CH 1 ====
def f0101():
    """1.1 Timeline: 1899 -> 2000s, 6 milestones, alternating callouts, 3-era band."""
    fig, ax = canvas(9.8, 5.55, W=12, H=6.2)
    AXIS_Y = 4.00

    segs = [(0.7, 2.24, F.REDL, "実験期"),
            (2.24, 7.88, F.BLUEL, "院内・手動期(1947-1962)"),
            (7.88, 11.3, F.GREENL, "自動化・普及期(1980-)")]
    for xa, xb, col, lab in segs:
        ax.add_patch(Rectangle((xa, 3.16), xb - xa, 0.34, fc=col, ec="none", zorder=1))
        txt(ax, (xa + xb) / 2, 3.06, lab, color=F.GRAY, fs=8.5)

    ax.plot([0.7, 11.3], [AXIS_Y, AXIS_Y], color=F.INK, lw=1.6, zorder=2)
    txt(ax, 0.7, AXIS_Y - 0.30, "1899", color=F.GRAY, fs=10, ha="left")
    txt(ax, 11.3, AXIS_Y - 0.30, "2000s", color=F.GRAY, fs=10, ha="right")

    # each node: (x, year-title, name, event [wrapped to 2 lines where it's long enough
    # to overrun the 2.1-wide box at fs9.5 -- same wording, just a different line break],
    # era-color, up/down, has_pace_marker)
    nodes = [
        (1.3, "1899", "Prevost & Batelli", "イヌでVF誘発\n→AC大電流で停止", F.RED, "up", False),
        (3.18, "1947", "Beck CS", "ヒト初の除細動\n(開胸パドル)", F.BLUE, "down", False),
        (5.06, "1952/56", "Zoll PM", "経皮ペーシング\n→経胸壁除細動", F.BLUE, "up", True),
        (6.94, "1962", "Lown B", "DC除細動+R波同期\nを導入", F.BLUE, "down", False),
        (8.82, "1980", "Mirowski M", "ICD 初植込み", F.GREEN, "up", False),
        (10.7, "1990s-2000s", "二相性/AED", "標準化・公共設置\n(PAD)", F.GREEN, "down", False),
    ]
    for x, yr, name, ev, col, pos, has_pace in nodes:
        ax.add_patch(Circle((x, AXIS_Y), 0.09, fc=col, ec="white", lw=1.2, zorder=4))
        if pos == "up":
            by0, bh = 4.05, 2.0
            near_edge = by0
            bolt_y = AXIS_Y - 0.35
        else:
            by0, bh = 0.86, 2.0
            near_edge = by0 + bh
            bolt_y = AXIS_Y + 0.45
        ax.plot([x, x], [AXIS_Y, near_edge], color=col, lw=1.2, ls=":", zorder=2)
        rbox(ax, x - 1.05, by0, 2.1, bh, "white", F.INK, txt_lines=[name, ev],
             tc=F.INK, fs=9.5, title=yr, title_color=F.GOLD, title_fs=12)
        shock_bolt(ax, x - 0.15, bolt_y, size=0.16, color=F.RED)
        if has_pace:
            sx = x + 0.35
            ax.plot([sx, sx], [bolt_y - 0.14, bolt_y + 0.14], color=F.ORANGE, lw=2.2, zorder=5)
            ax.scatter([sx], [bolt_y + 0.17], marker="^", s=30, color=F.ORANGE, zorder=6)
    F.save(fig, "f0101")


def f0102():
    """1.2 AC (left, red) -> DC/Lown waveform (right, gold), Lown 1962 transition arrow."""
    fig, ax = canvas(9.8, 4.4, W=11, H=5.0)
    # left: AC
    rbox(ax, 0.3, 0.3, 4.5, 4.4, "white", F.RED, title="交流(AC)除細動", title_color=F.RED, title_fs=13)
    tw = np.linspace(0, 1, 300)
    ac_y = np.sin(2 * np.pi * 6 * tw)
    ax.plot(0.7 + tw * 3.7, 3.55 + ac_y * 0.55, color=F.INK, lw=1.6, zorder=3)
    chips = ["高エネルギー", "皮膚熱傷・心筋障害", "再細動を起こしやすい"]
    cy = 2.55
    for c in chips:
        rbox(ax, 0.6, cy, 3.9, 0.55, F.REDL, F.RED, txt_lines=[c], tc=F.INK, fs=10.5)
        cy -= 0.72
    txt(ax, 2.55, 0.55, "※装置が大型（変圧器）", color=F.GRAY, fs=9)

    # center transition arrow
    F.arrow(ax, 5.0, 2.5, 5.8, 2.5, color=F.GOLD, lw=3.4, ms=22)
    txt(ax, 5.4, 2.90, "Lown\n1962", color=F.GOLD, fs=10.5, bold=True)

    # right: DC / Lown
    rbox(ax, 5.9, 0.3, 4.8, 4.4, "white", F.GOLD, title="直流(DC)除細動＝Lown波形",
         title_color=F.GOLD, title_fs=12.5)
    t, y = F.mono_damped_sine()
    wave_in(ax, t, y, 6.3, 9.3, 3.65, 0.55, color=F.GOLD, lw=2.2)
    chips2 = [("単発・短時間パルス", F.GREEN), ("低エネルギーで確実", F.GREEN), ("熱傷・再細動が少ない", F.GREEN)]
    cy = 2.95
    for c, col in chips2:
        # F.box (centered text), not rbox's txt_lines: this box (h=0.42) is too short
        # for rbox's fixed top-anchored offset, which was pushing the text below the box
        F.box(ax, 6.2, cy, 4.2, 0.42, F.GREENL, col, c, tc=F.INK, fs=10, bold=False, lw=1.4)
        cy -= 0.52
    txt(ax, 6.2, 1.15, "※コンデンサ充電→\n放電で小型化", color=F.GRAY, fs=8, ha="left", va="top")
    rbox(ax, 7.5, 0.32, 3.1, 0.68, F.GOLDL, F.GOLD, round_=0.14)
    txt(ax, 9.05, 0.72, "E ＝ ½CV²", color=F.GOLD, fs=14, bold=True)
    txt(ax, 9.05, 0.42, "(第2章2.1で詳述)", color=F.GRAY, fs=7.5)
    F.save(fig, "f0102")


def f0103():
    """1.3 Danger (T-wave shock -> VF) vs safe (R-sync) rows, with a small branch note."""
    fig, ax = canvas(9.8, 4.4, W=11, H=5.0)
    beats = 2
    # top row: danger
    rx = ecg_in(ax, 0.5, 6.6, 4.15, 0.55, beats=beats, mark_t=True)
    tpk = F.t_peak_positions(beats=beats)[0]
    txp = 0.5 + tpk / beats * (6.6 - 0.5)
    F.arrow(ax, txp, 4.85, txp, 4.35, color=F.RED, lw=2.4, ms=16)
    shock_bolt(ax, txp + 0.30, 4.85, size=0.18, color=F.RED)
    F.arrow(ax, 6.75, 4.15, 7.30, 4.15, color=F.RED, lw=2.2, ms=16)
    Xv, Yv = F.vf_wave(span=2.2)
    wave_in(ax, Xv, Yv, 7.40, 10.6, 4.15, 0.5, color=F.RED, lw=1.5)
    txt(ax, 9.0, 4.85, "R on T →\nVF/多形性VT", color=F.RED, fs=9.5, bold=True)
    txt(ax, 3.5, 3.35, "脆弱期（T波頂上）への放電＝危険", color=F.RED, fs=9.5)

    # divider / branch
    ax.plot([0.4, 10.6], [2.55, 2.55], color=F.LGRAY, lw=1.0, ls="--", zorder=1)
    txt(ax, 3.2, 2.78, "VF(P/QRS/T無し) → 非同期＝除細動", color=F.BLUE, fs=9.5)
    txt(ax, 7.6, 2.32, "脈のある頻拍(R波あり) → 同期＝カルディオバージョン", color=F.GREEN, fs=9)

    # bottom row: safe
    rx2 = ecg_in(ax, 0.5, 6.6, 1.15, 0.55, beats=beats, mark_r=True, mark_color=F.GOLD)
    sx = rx2[0] + 0.35
    F.arrow(ax, sx, 1.85, sx, 1.35, color=F.GOLD, lw=2.4, ms=16)
    shock_bolt(ax, sx + 0.30, 1.85, size=0.18, color=F.GOLD)
    txt(ax, 3.5, 0.55, "R波に同期＝T波を避けて放電＝cardioversion", color=F.GOLD, fs=10, bold=True)
    F.save(fig, "f0103")


# ================================================================ CH 2 ====
def f0201():
    """2.1 Left-to-right block diagram: source -> boost -> capacitor -> discharge -> pad -> heart."""
    fig, ax = canvas(9.8, 4.6, W=12, H=5.6)
    y0, bh = 3.1, 1.3
    blocks = [
        (0.3, 1.9, F.BLUEL, F.BLUE, ["電源部", "(商用/バッテリ)"], 9.5),
        (2.25, 3.85, F.BLUEL, F.BLUE, ["昇圧・整流", "(→数千V)"], 9.5),
        (4.20, 6.40, F.GOLDL, F.GOLD, ["コンデンサ", "(キャパシタ)", "＝充電"], 10.5),
        (6.75, 8.45, "#FCE4C0", F.ORANGE, ["放電回路", "(スイッチ+", "インダクタ)"], 9),
        (8.80, 10.30, F.GREENL, F.GREEN, ["電極", "(パッド/パドル)"], 9.5),
    ]
    for xa, xb, fc, ec, lines, fs in blocks:
        rbox(ax, xa, y0 - bh / 2, xb - xa, bh, fc, ec, txt_lines=lines, tc=F.INK, fs=fs)
    for i in range(len(blocks) - 1):
        xa = blocks[i][1]; xb = blocks[i + 1][0]
        F.arrow(ax, xa + 0.05, y0, xb - 0.05, y0, color=F.INK, lw=2.2, ms=16)

    cx3 = (blocks[2][0] + blocks[2][1]) / 2
    ax.add_patch(Rectangle((cx3 - 0.28, y0 - 0.28), 0.09, 0.5, fc=F.GOLD, ec="none", zorder=4))
    ax.add_patch(Rectangle((cx3 + 0.12, y0 - 0.28), 0.09, 0.5, fc=F.GOLD, ec="none", zorder=4))

    charge_cx = (blocks[1][1] + blocks[2][0]) / 2
    disch_cx = (blocks[2][1] + blocks[3][0]) / 2
    _clock(ax, charge_cx - 0.35, y0 + bh / 2 + 0.42, r=0.16)
    txt(ax, charge_cx + 0.10, y0 + bh / 2 + 0.42, "充電＝数秒", color=F.GOLD, fs=9.5, bold=True, ha="left")
    shock_bolt(ax, disch_cx - 0.30, y0 + bh / 2 + 0.42, size=0.15, color=F.GOLD)
    txt(ax, disch_cx + 0.15, y0 + bh / 2 + 0.42, "放電＝ミリ秒", color=F.GOLD, fs=9.5, bold=True, ha="left")

    hx = 10.95
    ax.add_patch(Circle((hx, y0), 0.30, fc="#F4C7C3", ec=F.RED, lw=1.4, zorder=3))
    txt(ax, hx, y0, "心筋", color=F.RED, fs=9, bold=True)
    F.arrow(ax, blocks[4][1] + 0.05, y0, hx - 0.35, y0, color=F.RED, lw=2.2, ms=16)

    rbox(ax, 3.7, 4.75, 3.2, 0.7, F.GOLDL, F.GOLD, round_=0.14)
    txt(ax, 5.3, 5.10, "E ＝ ½CV²", color=F.GOLD, fs=18, bold=True)

    rbox(ax, 0.3, 0.2, 2.6, 1.7, "white", F.GRAY, title="(a) 充電カーブ", title_color=F.GRAY, title_fs=9)
    tc_ = np.linspace(0, 1, 100); vc = 1 - np.exp(-4 * tc_)
    ax.plot(0.55 + tc_ * 2.1, 0.45 + vc * 0.85, color=F.BLUE, lw=1.8, zorder=3)
    txt(ax, 1.6, 0.30, "電圧：数秒でゆっくり上昇", color=F.GRAY, fs=7.2)

    rbox(ax, 3.1, 0.2, 2.6, 1.7, "white", F.GRAY, title="(b) 放電カーブ", title_color=F.GRAY, title_fs=9)
    td = np.linspace(0, 1, 100); vd = np.exp(-6 * td)
    ax.plot(3.35 + td * 2.1, 0.45 + vd * 0.85, color=F.ORANGE, lw=1.8, zorder=3)
    txt(ax, 4.4, 0.30, "電圧：ミリ秒で急降下", color=F.GRAY, fs=7.2)
    F.save(fig, "f0201")


def f0202():
    """2.2 setter(J) -> I=V/TTI -> current depolarizes; small success-rate vs TTI curve."""
    fig, ax = canvas(9.8, 4.4, W=11, H=5.0)
    rbox(ax, 0.3, 2.5, 2.9, 1.7, F.BLUEL, F.BLUE, title="操作者が設定", title_color=F.BLUE, title_fs=11,
         txt_lines=["＝エネルギー(J)"], tc=F.INK, fs=10.5)
    _dial(ax, 1.75, 2.85, r=0.20, color=F.BLUE)
    F.arrow(ax, 3.25, 3.35, 3.9, 3.35, color=F.INK, lw=2.6, ms=18)

    rbox(ax, 4.0, 2.4, 3.3, 1.9, F.GOLDL, F.GOLD, round_=0.12)
    txt(ax, 5.65, 3.35, "I ＝ V / TTI", color=F.GOLD, fs=20, bold=True)

    F.arrow(ax, 7.35, 3.7, 8.0, 4.1, color=F.INK, lw=2.6, ms=18)
    ax.add_patch(Circle((8.7, 4.35), 0.30, fc="#F4C7C3", ec=F.RED, lw=1.4, zorder=4))
    ax.plot([8.55, 8.85], [4.35, 4.35], color=F.RED, lw=1.6, zorder=5)
    F.arrow(ax, 8.55, 4.35, 8.85, 4.35, color=F.RED, lw=0.1, ms=10)
    txt(ax, 8.7, 3.85, "脱分極させるのは\n電流(A)", color=F.RED, fs=9, bold=True)

    # bottom-right small TTI vs current graph
    gx0, gy0, gw, gh = 6.6, 0.55, 3.9, 2.1
    ax.plot([gx0, gx0 + gw], [gy0, gy0], color=F.INK, lw=1.1, zorder=2)
    ax.plot([gx0, gx0], [gy0, gy0 + gh], color=F.INK, lw=1.1, zorder=2)
    txt(ax, gx0 + gw / 2, gy0 - 0.28, "TTI (Ω)", color=F.GRAY, fs=8.5)
    txt(ax, gx0 - 0.18, gy0 + gh * 0.55, "電流(A)", color=F.GRAY, fs=8, ha="right")
    xg = np.linspace(gx0 + 0.1, gx0 + gw - 0.1, 100)
    yg = gy0 + gh * 0.85 * np.exp(-(xg - gx0 - 0.1) / (gw * 0.7))
    ax.add_patch(Rectangle((gx0, gy0), gw * 0.42, gh, fc=F.GREENL, alpha=0.4, ec="none", zorder=1))
    ax.add_patch(Rectangle((gx0 + gw * 0.42, gy0), gw * 0.58, gh, fc=F.REDL, alpha=0.4, ec="none", zorder=1))
    ax.plot(xg, yg, color=F.INK, lw=2.0, zorder=3)
    txt(ax, gx0 + gw * 0.20, gy0 + gh * 0.30, "電流十分", color=F.GREEN, fs=8.5, bold=True)
    txt(ax, gx0 + gw * 0.75, gy0 + gh * 0.15, "電流不足\n→除細動失敗", color=F.RED, fs=8, bold=True)
    txt(ax, gx0 + gw / 2, gy0 + gh + 0.20, "同じJでもTTIが高いと電流が減る", color=F.INK, fs=8)

    rbox(ax, 0.3, 0.05, 6.0, 0.42, "white", F.GRAY, round_=0.10)
    txt(ax, 3.3, 0.26, "だから現代機はインピーダンスを補償して電流を担保する（→2.3・2.4）",
        color=F.GRAY, fs=8, bold=True)
    F.save(fig, "f0202")


def f0203():
    """2.3 Thorax cross-section with 2 pads + up/down TTI factor boxes."""
    fig, ax = canvas(9.8, 4.6, W=11, H=5.2)
    cx, cy, rx, ry = 3.3, 3.1, 1.7, 1.3
    _ellipse(ax, cx, cy, rx, ry, fc="#F2E9DA", ec=F.INK, lw=1.8, zorder=2)
    txt(ax, cx, cy + 0.05, "胸郭断面", color=F.GRAY, fs=9)
    ax.add_patch(Rectangle((cx - 0.5, cy + ry - 0.2), 1.0, 0.42, fc=F.GOLDL, ec=F.GOLD, lw=1.4, zorder=4))
    ax.add_patch(Rectangle((cx + rx - 0.22, cy - 0.5), 0.42, 1.0, fc=F.GOLDL, ec=F.GOLD, lw=1.4, zorder=4))
    txt(ax, cx, cy + ry + 0.45, "前胸部パッド", color=F.INK, fs=8.5)
    txt(ax, cx + rx + 0.75, cy, "側胸部\nパッド", color=F.INK, fs=8.5)
    ax.add_patch(Circle((cx + 0.15, cy - 0.05), 0.20, fc="#F4C7C3", ec=F.RED, lw=1.2, zorder=5))
    ax.plot([cx - 0.05, cx + 0.15, cx + rx - 0.05], [cy + ry - 0.25, cy - 0.05, cy - 0.05],
            color=F.GOLD, lw=2.2, zorder=6)
    txt(ax, cx, cy - 0.85, "TTI 70–80 Ω", color=F.GOLD, fs=13, bold=True)

    # height raised (1.55->1.85, grown mostly upward) -- the 3rd line ("吸気位相...")
    # didn't fit rbox's fixed per-line offsets at the original height and sank below
    # the box's bottom border
    rbox(ax, 6.2, 3.20, 4.3, 1.85, F.REDL, F.RED, title="TTIを上げる要因 ↑", title_color=F.RED, title_fs=11,
         txt_lines=["体格・胸郭が大きい", "体毛・乾いた皮膚・空気層", "吸気位相（肺含気多）"], tc=F.INK, fs=9.5,
         align="left")
    F.arrow(ax, 6.15, 4.0, cx + rx + 0.1, cy + 0.5, color=F.RED, lw=1.8, ms=14)

    rbox(ax, 6.2, 0.6, 4.3, 2.5, F.GREENL, F.GREEN, title="TTIを下げる要因 ↓", title_color=F.GREEN, title_fs=11,
         txt_lines=["大きめパッド", "良い密着・接触圧", "導電ゲル・ゲルパッド", "呼気位相",
                     ("反復ショック(2回目でやや低下)", F.BLUE)], tc=F.INK, fs=9.5, align="left")
    F.arrow(ax, 6.15, 1.6, cx + 0.3, cy - ry - 0.1, color=F.GREEN, lw=1.8, ms=14)

    # height raised (1.0->1.35): title + 2 lines didn't fit the original box and
    # "自動補償" was rendering below the box, partly off-canvas
    rbox(ax, 0.2, 0.15, 3.0, 1.35, F.GOLDL, F.GOLD, txt_lines=["実測インピーダンスに応じ", "自動補償"], tc=F.INK,
         fs=9, title="二相性＝自動補償", title_color=F.GOLD, title_fs=10.5)
    F.save(fig, "f0203")


def f0204():
    """2.4 Monophasic (blue, unipolar) vs biphasic (orange/green, bipolar) pulse shapes."""
    fig, ax = canvas(9.8, 4.4, W=11, H=5.0)
    y0 = 2.3
    ax.plot([0.5, 5.0], [y0, y0], color=F.GRAY, lw=1.2, zorder=2)
    ax.plot([0.5, 0.5], [1.05, 4.5], color=F.GRAY, lw=1.2, zorder=2)
    t, y = F.mono_damped_sine()
    wave_in(ax, t, y, 0.7, 4.85, y0, 1.5, color=F.BLUE, lw=2.4)
    txt(ax, 2.75, 4.75, "単相性 MDS＝一方向・高エネルギー", color=F.BLUE, fs=9.8, bold=True)
    txt(ax, 1.5, 4.05, "360 J", color=F.RED, fs=14, bold=True)
    txt(ax, 2.75, 0.80, "時間 (ms)", color=F.GRAY, fs=9)
    txt(ax, 0.30, 4.5, "電流(A)", color=F.GRAY, fs=8, ha="left")

    ax.plot([6.0, 10.5], [y0, y0], color=F.GRAY, lw=1.2, zorder=2)
    ax.plot([6.0, 6.0], [1.05, 4.5], color=F.GRAY, lw=1.2, zorder=2)
    tb, yb = F.biphasic_trunc_exp()
    xx = 6.2 + tb * (10.3 - 6.2)
    yy = y0 + yb * 1.5
    # split on a CONTIGUOUS time boundary (not y-sign) so phase-1's positive decay
    # doesn't get bridged straight across the negative phase-2 excursion by a
    # single Line2D connecting non-adjacent samples.
    m1 = tb < tb.max() * 0.55
    ax.plot(xx[m1], yy[m1], color=F.ORANGE, lw=2.4, zorder=4, solid_joinstyle="round")
    ax.plot(xx[~m1], yy[~m1], color=F.GREEN, lw=2.4, zorder=4, solid_joinstyle="round")
    txt(ax, 8.25, 4.75, "二相性 BTE／RLB＝双方向・低エネルギー", color=F.GOLD, fs=9.8, bold=True)
    txt(ax, 6.7, 4.05, "120–200 J", color=F.GOLD, fs=13, bold=True)
    txt(ax, 8.25, 1.35, "（RLB＝矩形波状の第1相＋短い第2相）", color=F.GRAY, fs=7.6)
    txt(ax, 8.25, 0.80, "時間 (ms)", color=F.GRAY, fs=9)
    txt(ax, 5.80, 4.5, "電流(A)", color=F.GRAY, fs=8, ha="left")

    rbox(ax, 0.5, 0.10, 10.0, 0.55, F.GOLDL, F.GOLD, round_=0.12)
    txt(ax, 5.5, 0.38, "二相性＝低エネで初回成功率↑・心筋障害↓・現代機の標準", color=F.GOLD, fs=11, bold=True)
    F.save(fig, "f0204")


def f0205():
    """2.5 Pad vs paddle (top) + manual/AED/ICD who-judges (bottom)."""
    fig, ax = canvas(9.8, 4.6, W=11, H=5.2)
    rbox(ax, 0.3, 2.9, 5.0, 2.1, F.GOLDL, F.GOLD, title="粘着パッド（ハンズフリー）", title_color=F.GOLD,
         title_fs=11.5)
    ax.add_patch(Rectangle((1.1, 3.55), 0.9, 1.0, fc="#F2E9DA", ec=F.INK, lw=1.4, zorder=3))
    ax.add_patch(Rectangle((1.25, 4.15), 0.6, 0.28, fc=F.GOLD, ec=F.INK, lw=1.0, zorder=4))
    _person(ax, 4.0, 3.75, s=1.0, color=F.GRAY)
    txt(ax, 4.0, 3.10, "離れて立つ術者", color=F.GRAY, fs=8.5)
    txt(ax, 1.55, 3.05, "現代の標準", color=F.GOLD, fs=9, bold=True)

    rbox(ax, 5.7, 2.9, 5.0, 2.1, F.BLUEL, F.BLUE, title="パドル（手持ち）", title_color=F.BLUE, title_fs=11.5)
    ax.add_patch(Rectangle((6.5, 3.55), 0.9, 1.0, fc="#F2E9DA", ec=F.INK, lw=1.4, zorder=3))
    ax.add_patch(Circle((6.95, 4.3), 0.22, fc=F.BLUE, ec=F.INK, lw=1.0, zorder=4))
    _person(ax, 8.5, 3.75, s=1.0, color=F.GRAY)
    txt(ax, 8.5, 3.10, "近くに立つ術者", color=F.GRAY, fs=8.5)
    ax.plot([6.95, 8.2], [4.3, 3.75], color=F.INK, lw=1.4, ls=":", zorder=2)

    txt(ax, 2.8, 2.55, "安全・連続モニタ/ペーシング可・位置固定", color=F.INK, fs=8.3)
    txt(ax, 8.2, 2.55, "迅速・接触圧でTTI↓／手が塞がる・術者近い", color=F.INK, fs=8.3)

    rbox(ax, 0.3, 0.2, 3.3, 2.0, "#FCE4C0", F.ORANGE, title="①手動除細動器", title_color=F.ORANGE, title_fs=11,
         txt_lines=["医療者が波形を判読", "エネルギー選択", "全モード可", ("判断＝人", F.GOLD)], tc=F.INK, fs=9)
    rbox(ax, 3.85, 0.2, 3.3, 2.0, F.GREENL, F.GREEN, title="②AED（自動体外式）", title_color=F.GREEN, title_fs=11,
         txt_lines=["機械がVF/VTを解析", "音声誘導", "非医療者でも使用可", ("判断＝機械", F.GOLD)], tc=F.INK, fs=9)
    rbox(ax, 7.4, 0.2, 3.3, 2.0, F.BLUEL, F.BLUE, title="③ICD（植込み型）", title_color=F.BLUE, title_fs=11,
         txt_lines=["体内ジェネレータが", "自動検知", "体内で除細動", ("判断＝体内で自動", F.GOLD)], tc=F.INK, fs=9)
    F.save(fig, "f0205")

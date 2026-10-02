#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EtCO2 deck — all matplotlib figures (~45 pts). One function per figure code
f<chapter><section>. Run standalone: writes PNGs into ../figs/ (figlib.OUTDIR)."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Arc, Circle, Polygon, Rectangle
import figlib as F

# ---------------------------------------------------------------- helpers --
def txt(ax, x, y, s, color=F.INK, fs=14, bold=False, ha="center", va="center", zorder=6):
    ax.text(x, y, s, color=color, fontsize=fs, fontweight="bold" if bold else "normal",
            ha=ha, va=va, zorder=zorder)

def canvas(w=8.6, h=5.0, W=10, H=6):
    fig, ax = F.newfig(w, h)
    F.clean(ax)
    ax.set_xlim(0, W); ax.set_ylim(0, H)
    return fig, ax

def rbox(ax, x, y, w, h, fc, ec, txt_lines=None, tc=F.INK, fs=13, title=None, title_color=None,
         title_fs=14, lw=1.4, round_=0.10, align="center"):
    """Rounded box. IMPORTANT: box patch sits at zorder=1 (matplotlib Line2D/Rectangle
    default to zorder=2) so any inset waveform/patch drawn *after* this call is visible
    on top without needing an explicit zorder. Use zorder>=2 explicitly only if you add
    insets *before* calling rbox (rare)."""
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.01,rounding_size={round_}",
                        fc=fc, ec=ec, lw=lw, zorder=1)
    ax.add_patch(p)
    cy = y + h - 0.32
    if title:
        n_lines = title.count("\n") + 1
        ax.text(x + w/2, cy, title, color=title_color or ec, fontsize=title_fs, fontweight="bold",
                ha="center", va="top", zorder=4, linespacing=1.3)
        cy -= 0.40 * n_lines + 0.10
    if txt_lines:
        for ln in txt_lines:
            col = tc
            if isinstance(ln, tuple):
                ln, col = ln
            ax.text(x + (w/2 if align == "center" else 0.18), cy, ln, color=col, fontsize=fs,
                    ha=align, va="top", zorder=4)
            cy -= 0.34
    return p

def capno_in(ax, x0, x1, y0, yscale, cycles=1, color=F.INK, lw=2.6, zorder=4, **kw):
    """Draw `cycles` capnogram breaths mapped into the x-range [x0,x1] (data coords),
    baseline at y0, peak height yscale above baseline. Fixes the common bug of
    forgetting that F.capno_train's x spans [0, cycles], not [0, 1]."""
    cycles = max(1, round(cycles))  # F.capno_train requires an int
    X, Y = F.capno_train(cycles=cycles, **kw)
    xs = x0 + X / cycles * (x1 - x0)
    ys = y0 + Y * yscale
    ax.plot(xs, ys, color=color, lw=lw, zorder=zorder, solid_joinstyle="round")
    return xs, ys


# =========================================================== front matter =
def f00_hero():
    fig, ax = F.newfig(14.0, 2.0)
    F.clean(ax)
    X, Y = F.capno_train(cycles=4, p0=0.94, ptop=1.0)
    ax.plot(X, Y*40, color=F.GOLD, lw=3.4, solid_joinstyle="round")
    ax.set_xlim(-0.02, 4.02); ax.set_ylim(-4, 46)
    F.save(fig, "f00_hero")


# ================================================================ CH 1 ====
def f0101():
    fig, ax = canvas(11.0, 6.2, W=13, H=7.2)
    AXIS_Y = 3.55
    # timeline axis
    ax.plot([0.5, 10.9], [AXIS_Y, AXIS_Y], color=F.INK, lw=1.6, zorder=2)
    for xt, yr in [(0.5, "1750"), (10.9, "1950")]:
        txt(ax, xt, AXIS_Y-0.35, yr, color=F.GRAY, fs=11)
    # 3 lane bands directly under the axis, stacked UPWARD from BAND_Y0 so they
    # stay clear of the down-boxes below (DN box top = DN_Y0+DN_H = 2.05) and
    # of the "1750"/"1950" year labels above (at AXIS_Y-0.35 = 3.20).
    BAND_H, BAND_STEP, BAND_Y0 = 0.26, 0.30, AXIS_Y - 1.35   # -> bands span y=[2.20, 3.06]
    lanes = [("計測工学", 0, F.GREENL), ("赤外物理", 1, F.ORANGEL), ("気体化学", 2, F.BLUEL)]
    for name, k, col in lanes:
        y0 = BAND_Y0 + k * BAND_STEP
        ax.add_patch(Rectangle((0.5, y0), 10.4, BAND_H, fc=col, ec="none", zorder=1))
        txt(ax, 0.15, y0 + BAND_H/2, name, color=F.GRAY, fs=9.5, ha="left")
    nodes = [
        (1.7, "1754–56", "Joseph Black", "CO₂＝“fixed air”", F.BLUE),
        (4.4, "1859–61", "John Tyndall", "赤外吸収を実証", F.BLUE),
        (7.3, "1938", "Lehrer & Luft", "URAS 開発", F.ORANGE),
        (9.7, "1943", "Karl F. Luft", "NDIR 原理を公表", F.ORANGE),
    ]
    UP_Y0, UP_H = AXIS_Y+0.55, 1.75      # up-box zone: clearly above axis
    DN_Y0, DN_H = AXIS_Y-3.25, 1.75      # down-box zone: clearly below lane bands (top=2.05 < band bottom 2.20)
    for i, (x, yr, name, ev, col) in enumerate(nodes):
        y_up = (i % 2 == 0)
        ax.add_patch(Circle((x, AXIS_Y), 0.09, fc=col, ec="white", lw=1.2, zorder=4))
        by0 = UP_Y0 if y_up else DN_Y0
        rbox(ax, x-1.05, by0, 2.1, UP_H, "white", col,
             txt_lines=[name, ev], tc=F.INK, fs=10.5, title=yr, title_color=F.GOLD, title_fs=12)
        near_edge = by0 if y_up else by0 + DN_H   # box edge nearest the axis
        ax.plot([x, x], [AXIS_Y, near_edge], color=col, lw=1.3, zorder=2, ls=":")
    # convergence arrow -> NDIR box
    F.arrow(ax, 10.6, AXIS_Y, 11.55, AXIS_Y, color=F.GOLD, lw=3.0, ms=20)
    rbox(ax, 11.5, AXIS_Y-0.65, 1.3, 1.3, F.GOLDL, F.GOLD, txt_lines=["非分散", "赤外", "ガス分析計"],
         tc=F.INK, fs=9, title="NDIR", title_color=F.GOLD, title_fs=13)
    ax.set_xlim(0, 13.0)
    F.save(fig, "f0101")

def f0102():
    fig, ax = canvas(11.2, 5.2, W=12, H=6)
    # left block: mass spec era
    rbox(ax, 0.4, 1.2, 3.1, 3.6, F.ORANGEL, F.ORANGE,
         txt_lines=["多ガス同時計測", "中央集約型", "高価・大型"],
         tc=F.INK, fs=12.5, title="質量分析の時代", title_color=F.ORANGE, title_fs=13)
    txt(ax, 1.95, 1.55, "1970s〜80s", color=F.GRAY, fs=10.5)
    # middle block: atlas
    rbox(ax, 4.3, 1.2, 3.6, 3.6, F.GREENL, F.GREEN, txt_lines=None,
         title="An Atlas of Capnography", title_color=F.GREEN, title_fs=11.5)
    ax2x, ax2y = 4.55, 3.15
    xs = np.linspace(0, 2.9, 200)
    ys = np.interp(xs, [0, 0.5, 0.9, 2.4, 2.9], [0, 0, 0.7, 0.78, 0])
    ax.plot(ax2x+xs, ax2y+ys, color=F.INK, lw=2.2)
    txt(ax, 4.55, 2.55, "1975 Smalhout & Kalenda", color=F.BLUE, fs=10, ha="left")
    txt(ax, 4.55, 2.2, "正常波形＋アーチファクトを体系化", color=F.INK, fs=10, ha="left")
    # right block: two-method comparison
    rbox(ax, 8.3, 1.2, 3.3, 3.6, F.GOLDL, F.GOLD, txt_lines=None,
         title="専用赤外カプノグラフ", title_color=F.GOLD, title_fs=12)
    txt(ax, 9.95, 3.7, "mainstream", color=F.BLUE, fs=11, bold=True)
    ax.add_patch(Rectangle((8.6, 3.25), 2.7, 0.28, fc="white", ec=F.BLUE, lw=1.1))
    txt(ax, 9.95, 3.0, "sidestream", color=F.ORANGE, fs=11, bold=True)
    ax.add_patch(Rectangle((8.6, 2.15), 2.7, 0.28, fc="white", ec=F.ORANGE, lw=1.1))
    ax.plot([8.35, 11.55], [2.29, 2.29], color=F.GRAY, lw=4, alpha=0.35, zorder=1)
    txt(ax, 9.95, 1.65, "気管チューブに重ねた模式", color=F.GRAY, fs=9)
    # arrows (no cramped inter-box captions; one unifying caption below instead)
    F.arrow(ax, 3.55, 3.0, 4.2, 3.0, color=F.INK, lw=2.2)
    F.arrow(ax, 7.95, 3.0, 8.25, 3.0, color=F.INK, lw=2.2)
    txt(ax, 6.0, 0.55, "多ガス・中央集約 → 1波形・ベッドサイドへ", color=F.GRAY, fs=10.5)
    F.save(fig, "f0102")

def f0103():
    fig, ax = canvas(11.0, 5.6, W=12, H=6.6)
    # top: standards timeline
    ax.plot([0.6, 11.4], [5.5, 5.5], color=F.INK, lw=1.6, zorder=2)
    nodes = [(1.8, "1986", "Harvard 基準\n(Eichhorn)"),
             (4.6, "1986", "ASA 基本モニタ\n採択（推奨）"),
             (7.6, "1990–91", "ASA改訂\n呼気CO₂を要件化"),
             (10.2, "1993", "JSA モニター\n指針 初版")]
    for x, yr, lab in nodes:
        ax.add_patch(Circle((x, 5.5), 0.09, fc=F.BLUE, ec="white", lw=1.2, zorder=4))
        ax.plot([x, x], [5.5, 4.85], color=F.BLUE, lw=1.1, ls=":", zorder=2)
        for i, ln in enumerate(lab.split("\n")):
            txt(ax, x, 4.65-i*0.32, ln, color=F.INK, fs=10)
        txt(ax, x, 5.85, yr, color=F.GOLD, fs=12, bold=True)
    # connecting vertical
    ax.plot([6.0, 6.0], [3.75, 3.35], color=F.GRAY, lw=1.4, ls="--", zorder=1)
    # bottom causal 3-box flow
    rbox(ax, 0.5, 0.35, 3.1, 2.85, "white", F.RED,
         txt_lines=[("食道挿管", F.RED), ("換気不足", F.INK), ("挿管困難", F.INK)], fs=12.5,
         title="クローズドクレーム\n（呼吸関連の重大事故）", title_color=F.INK, title_fs=11)
    F.arrow(ax, 3.7, 1.75, 4.35, 1.75, color=F.INK, lw=2.6)
    rbox(ax, 4.4, 0.55, 3.2, 2.45, F.BLUEL, F.BLUE,
         txt_lines=["パルスオキシメータ＋", "カプノグラフィがあれば", "多くは予防可能"],
         tc=F.INK, fs=11.5)
    F.arrow(ax, 7.7, 1.75, 8.35, 1.75, color=F.INK, lw=2.6)
    rbox(ax, 8.4, 0.55, 3.0, 2.45, F.GOLDL, F.GOLD,
         txt_lines=["麻酔関連死・", "重大合併症の低減"], tc=F.INK, fs=12.5,
         title="必須モニタ化", title_color=F.GOLD, title_fs=13)
    F.save(fig, "f0103")


# ================================================================ CH 2 ====
def f0201():
    fig, ax = canvas(11.0, 5.6, W=12, H=6.6)
    # optical path
    y0 = 4.6
    rbox(ax, 0.4, y0-0.7, 2.1, 1.4, F.BLUEL, F.BLUE, txt_lines=["赤外光源", "(広帯域)"], tc=F.INK, fs=10.5)
    rbox(ax, 3.1, y0-0.7, 2.5, 1.4, "white", F.INK, txt_lines=["○●○  CO₂分子"], tc=F.INK, fs=10, title="サンプルセル", title_color=F.BLUE, title_fs=10.5)
    rbox(ax, 6.1, y0-0.7, 2.3, 1.4, F.GOLDL, F.GOLD, txt_lines=["≈4.26 µmだけ通す"], tc=F.INK, fs=10, title="バンドパスフィルタ", title_color=F.GOLD, title_fs=10.5)
    rbox(ax, 8.9, y0-0.7, 2.1, 1.4, F.BLUEL, F.BLUE, txt_lines=["検出器"], tc=F.INK, fs=10.5, title="サーモパイル", title_color=F.BLUE, title_fs=10.5)
    # light beam (thins after cell = attenuation)
    ax.plot([2.5, 3.1], [y0, y0], color=F.RED, lw=4.5, alpha=0.7, zorder=2)
    ax.plot([5.6, 6.1], [y0, y0], color=F.RED, lw=2.0, alpha=0.7, zorder=2)
    ax.plot([8.4, 8.9], [y0, y0], color=F.RED, lw=1.0, alpha=0.7, zorder=2)
    for x1, x2 in [(2.5, 3.1), (5.6, 6.1), (8.4, 8.9)]:
        F.arrow(ax, x1, y0, x2, y0, color=F.RED, lw=0.1, ms=14)
    F.arrow(ax, 0.55, y0, 0.55, y0, color=F.RED, lw=0.1)  # noop keep style
    txt(ax, 6.0, 6.25, "Beer–Lambert:  I = I₀·e^(−ε·c·L)", color=F.GOLD, fs=13, bold=True)
    # absorption spectrum inset
    rbox(ax, 0.4, 0.3, 10.6, 2.6, "white", F.GRAY, round_=0.08)
    sx0, sy0, sw, sh = 0.9, 0.6, 9.6, 1.9
    ax.plot([sx0, sx0+sw], [sy0, sy0], color=F.INK, lw=1.0)
    ax.plot([sx0, sx0], [sy0, sy0+sh], color=F.INK, lw=1.0)
    txt(ax, sx0+sw/2, sy0-0.28, "波長 (µm)  3 〜 5", color=F.GRAY, fs=9.5)
    txt(ax, sx0-0.15, sy0+sh*0.5, "吸光度", color=F.GRAY, fs=9.5, ha="right")
    wl = np.linspace(3, 5, 400)
    co2 = 1.55*np.exp(-((wl-4.26)**2)/(2*0.045**2))
    n2o = 0.55*np.exp(-((wl-4.5)**2)/(2*0.05**2))
    h2o = 0.32*np.ones_like(wl) + 0.1*np.sin(wl*3)
    xx = sx0 + (wl-3)/2*sw
    ax.fill_between(xx, sy0, sy0+0.35+0*wl, color=F.GRAY, alpha=0.15)
    ax.plot(xx, sy0+h2o, color=F.GRAY, lw=1.2)
    ax.plot(xx, sy0+n2o, color=F.ORANGE, lw=1.6)
    ax.plot(xx, sy0+co2, color=F.RED, lw=2.2)
    band_x = sx0 + (4.26-3)/2*sw
    ax.add_patch(Rectangle((band_x-0.09, sy0), 0.18, sh, fc=F.GOLD, alpha=0.22, zorder=1))
    txt(ax, band_x, sy0+sh+0.22, "CO₂ ≈ 4.26 µm", color=F.GOLD, fs=11, bold=True)
    txt(ax, sx0+(4.5-3)/2*sw, sy0+0.62+0.28, "N₂O≈4.5µm", color=F.ORANGE, fs=8.5)
    F.save(fig, "f0201")

def f0202():
    fig, ax = canvas(11.2, 5.6, W=12, H=6.6)
    # left: mainstream
    rbox(ax, 0.4, 3.1, 5.3, 3.2, "white", F.BLUE, title="メインストリーム＝気道内キュベット", title_color=F.BLUE, title_fs=12)
    ax.plot([0.9, 5.4], [4.15, 4.15], color=F.GRAY, lw=6, alpha=0.35, zorder=1)  # tube
    ax.add_patch(Rectangle((2.5, 3.85), 1.1, 0.6, fc="white", ec=F.INK, lw=1.3, zorder=3))
    txt(ax, 3.05, 4.15, "キュベット", color=F.INK, fs=9)
    ax.add_patch(Circle((2.35, 4.15), 0.14, fc=F.RED, ec="none", zorder=4))
    ax.add_patch(Circle((3.75, 4.15), 0.14, fc=F.BLUE, ec="none", zorder=4))
    txt(ax, 3.05, 3.55, "加温 ≈40℃", color=F.GRAY, fs=9)
    # right: sidestream
    rbox(ax, 6.3, 3.1, 5.3, 3.2, "white", F.ORANGE, title="サイドストリーム＝吸引して測る", title_color=F.ORANGE, title_fs=12)
    ax.plot([6.8, 10.4], [4.65, 4.65], color=F.GRAY, lw=5, alpha=0.35, zorder=1)
    F.arrow(ax, 8.0, 4.45, 8.6, 4.0, color=F.ORANGE, lw=2.0)
    rbox(ax, 8.4, 3.55, 1.5, 0.55, "white", F.INK, txt_lines=None, title="水トラップ", title_color=F.INK, title_fs=8.5)
    rbox(ax, 9.9, 3.45, 1.6, 0.95, F.ORANGEL, F.ORANGE, txt_lines=["測定ベンチ", "+吸引ポンプ"], tc=F.INK, fs=8.5)
    txt(ax, 10.7, 3.28, "50–200 mL/min", color=F.BLUE, fs=9.5, bold=True)
    # bottom comparison bars (green=pros red=cons)
    rows = [("応答", "速い・遅延ほぼ無し", "遅延あり"),
            ("重さ/死腔", "重い・死腔↑（小児注意）", "軽い・非挿管も可"),
            ("水/分泌物", "水滴に強い", "詰まりやすい")]
    y = 2.55
    for label, m_txt, s_txt in rows:
        txt(ax, 0.15, y, label, color=F.GRAY, fs=9.5, ha="left")
        col_m = F.GREEN if "強い" in m_txt or "速い" in m_txt else F.RED
        col_s = F.GREEN if "軽い" in s_txt else F.RED
        rbox(ax, 1.6, y-0.28, 4.1, 0.5, (F.GREENL if col_m==F.GREEN else F.ORANGEL), col_m, txt_lines=[m_txt], tc=F.INK, fs=9)
        rbox(ax, 6.3, y-0.28, 5.3, 0.5, (F.GREENL if col_s==F.GREEN else F.ORANGEL), col_s, txt_lines=[s_txt], tc=F.INK, fs=9)
        y -= 0.75
    F.save(fig, "f0202")

def f0203():
    fig, ax = canvas(11.0, 5.6, W=12, H=6.6)
    # top: true vs displayed waveform
    xt, yt = F.capno_train(cycles=1, p0=0.93, ptop=1.0, t1=0.14, t2=0.10, t3=0.46, down=0.10)
    ax.plot(xt*10+0.6, yt*2.6+3.4, color=F.INK, lw=2.6, label="true")
    # displayed: shifted right + rounded + lower peak (smoothed moving average)
    xd = xt*10+0.6+0.5
    kernel = np.ones(30)/30
    yd = np.convolve(yt, kernel, mode="same")*0.92
    ax.plot(xd, yd*2.6+3.4, color=F.GRAY, lw=2.2, ls="--")
    txt(ax, 6.0, 6.35, "実線＝気道の“真”の波形／破線＝モニタ表示（右へずれ・角が丸い）", color=F.INK, fs=10.5)
    F.arrow(ax, 1.1, 3.42, 1.6, 3.42, color=F.GOLD, lw=1.8, ms=12)
    txt(ax, 1.35, 3.15, "transport delay", color=F.GOLD, fs=9.5)
    ax.plot([2.3, 2.3], [3.5, 5.8], color=F.BLUE, lw=1, ls=":")
    ax.plot([2.75, 2.75], [3.5, 5.95], color=F.BLUE, lw=1, ls=":")
    txt(ax, 3.55, 4.75, "rise time", color=F.BLUE, fs=9.5, ha="left")
    txt(ax, 3.55, 4.45, "(10→90%)", color=F.BLUE, fs=9.5, ha="left")
    # bottom: fast RR / low TV truncation (3 shallow breaths, last plateau clipped)
    ax.plot([0.4, 11.6], [2.05, 2.05], color=F.LGRAY, lw=1, ls="--")
    capno_in(ax, 0.6, 11.4, 0.55, 1.35, cycles=3, color=F.RED, lw=2.4,
             p0=0.55, ptop=0.62, t1=0.08, t2=0.10, t3=0.20, down=0.10)
    txt(ax, 6.0, 0.20, "高RR・低TV → プラトー未到達 → PetCO₂ 過小評価", color=F.RED, fs=11.5, bold=True)
    F.save(fig, "f0203")

def f0205():
    fig, ax = canvas(11.0, 5.6, W=12, H=6.6)
    # top: numeric vs waveform
    rbox(ax, 0.5, 4.1, 4.9, 1.9, "white", F.INK, title="カプノメータ＝数値のみ", title_color=F.GOLD, title_fs=12)
    txt(ax, 2.95, 4.85, "PetCO₂ 40 mmHg", color=F.INK, fs=20, bold=True)
    rbox(ax, 6.6, 4.1, 4.9, 1.9, "white", F.INK, title="カプノグラフ＝波形も表示", title_color=F.GOLD, title_fs=12)
    capno_in(ax, 7.1, 11.3, 4.3, 0.9, cycles=1, color=F.INK, lw=2.4, p0=0.9, ptop=1.0)
    F.arrow(ax, 5.4, 5.05, 6.5, 5.05, color=F.TEAL, lw=2.2)
    txt(ax, 5.95, 5.35, "形・リズムを足す", color=F.TEAL, fs=9)
    # bottom: time-based vs volumetric
    rbox(ax, 0.5, 0.4, 4.9, 3.3, F.BLUEL, F.BLUE, title="時間軸カプノグラム", title_color=F.BLUE, title_fs=12)
    capno_in(ax, 0.85, 5.15, 0.85, 1.9, cycles=2, color=F.INK, lw=2.2, p0=0.9, ptop=1.0)
    txt(ax, 2.95, 0.65, "相I→II→III→0（換気の質・トレンド）", color=F.INK, fs=9)
    rbox(ax, 6.6, 0.4, 4.9, 3.3, F.ORANGEL, F.ORANGE, title="容量軸カプノグラム(volumetric)", title_color=F.ORANGE, title_fs=11.5)
    xv = np.linspace(0, 4.3, 200)
    yv = np.interp(xv, [0, 0.5, 1.6, 4.3], [0, 0, 1.85, 2.05])
    ax.fill_between(xv+7.0, 0.85, yv+0.85, color=F.ORANGE, alpha=0.18)
    ax.plot(xv+7.0, yv+0.85, color=F.INK, lw=2.2)
    txt(ax, 9.05, 0.65, "CO₂ vs 呼気量, 面積=VCO₂", color=F.INK, fs=9)
    txt(ax, 6.0, 3.95, "→ 4章で詳述", color=F.TEAL, fs=10, bold=True)
    F.save(fig, "f0205")


# ================================================================ CH 3 ====
def f0301():
    fig, ax = canvas(11.2, 5.6, W=12, H=6.6)
    # 3-stage flow
    rbox(ax, 0.4, 3.2, 3.1, 2.8, F.ORANGEL, F.ORANGE, title="① 産生", title_color=F.ORANGE, title_fs=14,
         txt_lines=["組織代謝", "RQ ≈ 0.8"], fs=12)
    txt(ax, 1.95, 3.5, "VCO₂ ≈ 200 mL/min", color=F.GOLD, fs=10.5, bold=True)
    F.arrow(ax, 3.6, 4.6, 4.35, 4.6, color=F.INK, lw=2.4)
    rbox(ax, 4.4, 3.2, 3.1, 2.8, F.BLUEL, F.BLUE, title="② 運搬（静脈血）", title_color=F.BLUE, title_fs=13,
         txt_lines=["HCO₃⁻ 60–70%", "カルバミノ 20–30%", "溶存 5–10%"], fs=10.5)
    txt(ax, 5.95, 3.5, "PvCO₂ ≈ 46 mmHg", color=F.GOLD, fs=10.5, bold=True)
    F.arrow(ax, 7.6, 4.6, 8.35, 4.6, color=F.INK, lw=2.4)
    rbox(ax, 8.4, 3.2, 3.1, 2.8, F.GREENL, F.GREEN, title="③ 排泄（肺胞）", title_color=F.GREEN, title_fs=13,
         txt_lines=["VA：肺胞換気"], fs=12)
    txt(ax, 9.95, 3.5, "PACO₂ ≈ 40 mmHg", color=F.GOLD, fs=10.5, bold=True)
    # central formula banner
    rbox(ax, 0.9, 0.5, 10.2, 1.7, F.GOLDL, F.GOLD, round_=0.12)
    txt(ax, 6.0, 1.75, "PaCO₂ = k · VCO₂ / VA", color=F.GOLD, fs=22, bold=True)
    txt(ax, 6.0, 1.05, "k = 0.863（定常状態・STPD→BTPS と分圧換算の定数）", color=F.GRAY, fs=11)
    F.save(fig, "f0301")

def f0302():
    fig, ax = canvas(11.2, 5.6, W=12, H=6.6)
    rbox(ax, 0.4, 0.4, 5.4, 5.9, "white", F.GREEN, title="理想肺（V/Q が均一）", title_color=F.GREEN, title_fs=13)
    ax.add_patch(Circle((1.9, 3.6), 0.75, fc=F.GREENL, ec=F.GREEN, lw=1.5, zorder=2))
    txt(ax, 1.9, 3.6, "肺胞", color=F.INK, fs=11)
    capno_in(ax, 3.0, 5.3, 2.55, 0.9, cycles=1, color=F.INK, lw=2.0, p0=0.9, ptop=1.0)
    for i, (lab, yv) in enumerate([("PACO₂", 3.5), ("PaCO₂", 3.5), ("PetCO₂", 3.5)]):
        pass
    ax.plot([3.0, 5.3], [3.45, 3.45], color=F.GOLD, lw=1.2, ls="--", zorder=3)
    txt(ax, 4.15, 3.68, "PACO₂ ＝ PaCO₂ ＝ PetCO₂ ＝ 40", color=F.GOLD, fs=8, bold=True)
    txt(ax, 4.15, 0.85, "ズレ無し（均一 V/Q）", color=F.GREEN, fs=11, bold=True)

    rbox(ax, 6.2, 0.4, 5.4, 5.9, "white", F.ORANGE, title="現実の肺（V/Q 不均等）", title_color=F.ORANGE, title_fs=13)
    ax.add_patch(Circle((7.6, 4.1), 0.62, fc="#F4C7C3", ec=F.RED, lw=1.3, zorder=2))
    txt(ax, 7.6, 4.1, "灌流良", color=F.INK, fs=9.5)
    ax.add_patch(Circle((8.9, 4.1), 0.62, fc="#F2F2F2", ec=F.GRAY, lw=1.3, zorder=2))
    txt(ax, 8.9, 4.1, "灌流少", color=F.INK, fs=9.5)
    F.arrow(ax, 7.6, 3.45, 8.2, 2.55, color=F.GRAY, lw=1.6)
    F.arrow(ax, 8.9, 3.45, 8.6, 2.55, color=F.GRAY, lw=1.6)
    txt(ax, 8.2, 2.85, "合流", color=F.GRAY, fs=9.5)
    # staircase (small)
    xs0 = 9.4
    ax.add_patch(Rectangle((xs0, 0.75), 0.55, 1.35, fc=F.BLUE, alpha=0.75, zorder=2))
    ax.add_patch(Rectangle((xs0+0.65, 0.75), 0.55, 1.10, fc=F.GREEN, alpha=0.75, zorder=2))
    ax.add_patch(Rectangle((xs0+1.3, 0.75), 0.55, 0.90, fc=F.GOLD, alpha=0.75, zorder=2))
    txt(ax, xs0+0.275, 0.55, "PaCO₂", color=F.BLUE, fs=8)
    txt(ax, xs0+0.925, 0.55, "PACO₂", color=F.GREEN, fs=8)
    txt(ax, xs0+1.575, 0.55, "PetCO₂", color=F.GOLD, fs=8)
    txt(ax, 8.5, 2.2, "差＝a–ET 較差（次節）", color=F.RED, fs=10.5, bold=True)
    F.save(fig, "f0302")

def f0303():
    fig, ax = canvas(11.2, 6.4, W=12, H=7.2)
    bw = 1.5
    bars = [(2.0, "PaCO₂", 45, F.BLUE, 4.2), (4.35, "PACO₂", 38, F.GREEN, 3.3), (6.7, "PetCO₂", 37, F.GOLD, 2.6)]
    base = 1.7
    tops = {}
    for x, lab, val, col, h in bars:
        ax.add_patch(Rectangle((x, base), bw, h, fc=col, alpha=0.85, ec="none", zorder=2))
        txt(ax, x+bw/2, base+h+0.34, lab, color=col, fs=15, bold=True)
        txt(ax, x+bw/2, base+h/2, f"{val}", color="white", fs=16, bold=True)
        tops[lab] = base+h
    txt(ax, 4.35+bw/2, 6.9, "（平均肺胞気）", color=F.GREEN, fs=10.5)
    # step-drop tick marks only (small, no inline text -> explained in the side note instead)
    gx1 = (2.0+bw + 4.35) / 2
    ax.plot([gx1-0.10, gx1+0.10], [tops["PaCO₂"], tops["PaCO₂"]], color=F.RED, lw=1.3)
    ax.plot([gx1-0.10, gx1+0.10], [tops["PACO₂"], tops["PACO₂"]], color=F.RED, lw=1.3)
    ax.plot([gx1, gx1], [tops["PACO₂"], tops["PaCO₂"]], color=F.RED, lw=1.3)
    txt(ax, gx1, tops["PaCO₂"]+0.28, "①", color=F.RED, fs=11, bold=True)
    gx2 = (4.35+bw + 6.7) / 2
    ax.plot([gx2-0.10, gx2+0.10], [tops["PACO₂"], tops["PACO₂"]], color=F.RED, lw=1.3)
    ax.plot([gx2-0.10, gx2+0.10], [tops["PetCO₂"], tops["PetCO₂"]], color=F.RED, lw=1.3)
    ax.plot([gx2, gx2], [tops["PetCO₂"], tops["PACO₂"]], color=F.RED, lw=1.3)
    txt(ax, gx2, tops["PACO₂"]+0.28, "②", color=F.RED, fs=11, bold=True)
    # total a-ET bracket + side note, far right (own column, no crowding)
    bx = 6.7 + bw + 1.15
    ax.plot([bx, bx+0.24, bx+0.24, bx], [tops["PaCO₂"], tops["PaCO₂"], tops["PetCO₂"], tops["PetCO₂"]],
            color=F.GOLD, lw=2.0, zorder=2)
    ty = tops["PaCO₂"]
    txt(ax, bx+0.45, ty+0.05, "a–ET 較差 ＝ PaCO₂ − PetCO₂", color=F.GOLD, fs=13, bold=True, ha="left")
    txt(ax, bx+0.45, ty-0.42, "正常 2–5 mmHg", color=F.INK, fs=12, ha="left")
    txt(ax, bx+0.45, ty-1.05, "① シャント・低V/Q の寄与", color=F.RED, fs=11, ha="left")
    txt(ax, bx+0.45, ty-1.50, "② 肺胞死腔・高V/Q の希釈", color=F.RED, fs=11, ha="left")
    # bottom chips (regulating factors)
    chips = ["死腔↑", "V/Q 不均等", "拡散・時間"]
    cx = 2.3
    for c in chips:
        rbox(ax, cx, 0.15, 1.9, 0.7, F.ORANGEL, F.ORANGE, txt_lines=[c], fs=12, align="center")
        F.arrow(ax, cx+0.95, 0.95, cx+0.95, 1.55, color=F.ORANGE, lw=1.6)
        cx += 2.2
    F.save(fig, "f0303")

def f0304():
    fig, ax = canvas(11.2, 5.8, W=12, H=6.8)
    # upper: dead space schematic
    rbox(ax, 0.4, 3.3, 6.6, 3.2, "white", F.GRAY, title="死腔の3分類", title_color=F.INK, title_fs=13)
    ax.add_patch(Rectangle((0.9, 4.9), 3.0, 0.55, fc=F.LGRAY, ec=F.GRAY, lw=1.2, zorder=2))
    txt(ax, 2.4, 5.17, "解剖学的死腔（伝導気道）", color=F.INK, fs=10)
    txt(ax, 2.4, 4.65, "≈2 mL/kg（成人 約150 mL）", color=F.GRAY, fs=9.5)
    ax.add_patch(Circle((4.9, 4.3), 0.42, fc=F.BLUEL, ec=F.BLUE, lw=1.3, zorder=2))
    txt(ax, 4.9, 4.3, "灌流良", color=F.INK, fs=8)
    ax.add_patch(Circle((5.9, 4.3), 0.42, fc="white", ec=F.RED, lw=1.3, zorder=2))
    txt(ax, 5.9, 4.3, "肺胞死腔", color=F.RED, fs=8)
    txt(ax, 5.4, 3.55, "生理学的死腔 ＝ 解剖学的 ＋ 肺胞死腔", color=F.GOLD, fs=9, bold=True)
    # West zones (right column)
    rbox(ax, 7.3, 3.3, 4.3, 3.2, "white", F.GREEN, title="West zone（肺尖→肺底）", title_color=F.GREEN, title_fs=12)
    zones = [("Zone 1  PA>Pa>Pv（死腔的）", F.GRAY), ("Zone 2  Pa>PA>Pv", F.BLUE), ("Zone 3  Pa>Pv>PA（灌流良好）", F.GREEN)]
    zy = 4.95
    for lab, col in zones:
        rbox(ax, 7.6, zy, 3.7, 0.62, "white", col, txt_lines=[lab], fs=9.5, tc=col)
        zy -= 0.78
    # bottom formulas
    rbox(ax, 0.4, 0.35, 6.6, 2.5, F.GOLDL, F.GOLD, round_=0.10)
    txt(ax, 3.7, 2.35, "Bohr：Vd/Vt = (PACO₂ − PECO₂)/PACO₂", color=F.GOLD, fs=12.5, bold=True)
    txt(ax, 3.7, 1.65, "Enghoff 変法：Vd/Vt = (PaCO₂ − PECO₂)/PaCO₂", color=F.GOLD, fs=12.5, bold=True)
    txt(ax, 3.7, 0.85, "正常 Vd/Vt ≈ 0.2–0.35（麻酔・陽圧換気で 0.4–0.5 まで増加しうる）", color=F.GRAY, fs=10)
    rbox(ax, 7.3, 0.35, 4.3, 2.5, "white", F.RED, txt_lines=[("死腔↑ →", F.INK), ("PetCO₂↓", F.RED), ("a–ET 較差↑", F.RED)],
         fs=15, title=None)
    F.save(fig, "f0304")

def f0305():
    """★backbone figure: central EtCO2 node with 3 converging axes."""
    fig, ax = canvas(11.4, 6.4, W=12, H=7.2)
    cx, cy, r = 6.0, 4.55, 0.95
    ax.add_patch(Circle((cx, cy), r, fc=F.GOLDL, ec=F.GOLD, lw=2.6, zorder=3))
    txt(ax, cx, cy+0.12, "EtCO₂", color=F.GOLD, fs=22, bold=True)
    txt(ax, cx, cy-0.35, "≈ PACO₂", color=F.GOLD, fs=12)
    # top box: production (wider than the two lower boxes -- its first line is the
    # longest content in the figure, so it needs extra width to avoid overflow)
    rbox(ax, cx-2.6, 5.75, 5.2, 1.35, F.ORANGEL, F.ORANGE, title="① 産生 VCO₂（代謝）", title_color=F.ORANGE, title_fs=12.5,
         txt_lines=[("↑：発熱・敗血症・MH・シバリング・駆血解除・CO₂気腹", F.INK), ("↓：低体温・低代謝", F.INK)], fs=9.5)
    F.arrow(ax, cx, 5.70, cx, cy+r+0.05, color=F.ORANGE, lw=2.6)
    # bottom-left: transport
    rbox(ax, 0.3, 1.4, 4.5, 2.1, F.BLUEL, F.BLUE, title="② 運搬 Q（循環・肺血流）", title_color=F.BLUE, title_fs=12.5,
         txt_lines=[("↑：心拍出量↑（洗い出し↑）", F.INK), ("↓：心停止・肺塞栓・出血・低血圧", F.RED)], fs=9.5)
    F.arrow(ax, 3.4, 3.35, cx-r*0.78, cy-r*0.55, color=F.BLUE, lw=2.6)
    # bottom-right: elimination
    rbox(ax, 7.2, 1.4, 4.5, 2.1, F.GREENL, F.GREEN, title="③ 排出 VA（換気）", title_color=F.GREEN, title_fs=12.5,
         txt_lines=[("↑：低換気（RR/TV↓・回路閉塞ぎみ）", F.INK), ("↓：過換気・回路外れ/閉塞で波形消失", F.RED)], fs=9.5)
    F.arrow(ax, 8.6, 3.35, cx+r*0.78, cy-r*0.55, color=F.GREEN, lw=2.6)
    # unifying banner
    rbox(ax, 1.6, 0.15, 8.8, 0.95, "white", F.GOLD, round_=0.14)
    txt(ax, 6.0, 0.62, "異常波形を見たら「産生・運搬・排出のどれ？」と問う", color=F.GOLD, fs=13.5, bold=True)
    F.save(fig, "f0305")


# ================================================================ CH 4 ====
def f0401():
    """★lead figure: 4-phase capnogram with colored phase bands."""
    fig, ax = canvas(11.4, 5.8, W=13, H=6.6)
    ax.set_xlim(-0.3, 13.3)
    # phase boundaries (fractions of one 1.3-cycle waveform): use capno_cycle geometry directly
    t1, t2, t3, down = 0.14, 0.10, 0.46, 0.10
    total_frac = t1+t2+t3+down  # = 0.80; remainder 0.20 is baseline-to-next-breath
    W_ = 12.0  # canvas width used for ~1.3 breaths
    x0 = 0.5
    # single breath scaled to width Wb
    Wb = 9.4
    b1, b2, b3, b4 = x0+t1*Wb, x0+(t1+t2)*Wb, x0+(t1+t2+t3)*Wb, x0+(t1+t2+t3+down)*Wb
    bands = [(x0, b1, F.BLUEL), (b1, b2, F.ORANGEL), (b2, b3, F.GREENL), (b3, b4, F.LGRAY)]
    for xa, xb, col in bands:
        ax.add_patch(Rectangle((xa, 0.9), xb-xa, 4.3, fc=col, alpha=0.55, ec="none", zorder=1))
    # extend a bit of next breath's phase I for context
    ax.add_patch(Rectangle((b4, 0.9), x0+Wb+1.0-b4, 4.3, fc=F.BLUEL, alpha=0.55, ec="none", zorder=1))
    capno_in(ax, x0, x0+Wb, 1.2, 3.6, cycles=1, color=F.INK, lw=3.2, p0=0.92, ptop=1.0,
             t1=t1, t2=t2, t3=t3, down=down)
    # extend flat continuation after the breath for visual completeness
    ax.plot([b4, x0+Wb+1.0], [1.2, 1.2], color=F.INK, lw=3.2, zorder=4)
    petco2_y = 1.2+3.6*1.0
    ax.plot([b2, x0+Wb+1.6], [petco2_y, petco2_y], color=F.GOLD, lw=1.3, ls="--", zorder=3)
    txt(ax, x0+Wb+2.0, petco2_y, "PetCO₂", color=F.GOLD, fs=13, bold=True, ha="left")
    txt(ax, (x0+b1)/2, 4.9, "相I", color=F.BLUE, fs=13, bold=True)
    txt(ax, (b1+b2)/2, 4.9, "相II", color=F.ORANGE, fs=13, bold=True)
    txt(ax, (b2+b3)/2, 4.9, "相III", color=F.GREEN, fs=13, bold=True)
    txt(ax, (b3+b4)/2, 4.9, "相0", color=F.GRAY, fs=13, bold=True)
    txt(ax, (x0+b1)/2, 0.55, "死腔・CO₂≈0", color=F.BLUE, fs=10)
    txt(ax, (b2+b3)/2, 0.55, "肺胞プラトー", color=F.GREEN, fs=10)
    txt(ax, (b3+b4)/2, 0.55, "吸気下降", color=F.GRAY, fs=10)
    txt(ax, 6.3, 5.9, "呼気（相I–III）", color=F.BLUE, fs=11)
    F.save(fig, "f0401")

def f0402():
    fig, ax = canvas(9.6, 5.8, W=11, H=6.6)
    t1, t2, t3, down = 0.14, 0.10, 0.46, 0.10
    x0, Wb = 0.6, 9.0
    b1, b2, b3, b4 = x0+t1*Wb, x0+(t1+t2)*Wb, x0+(t1+t2+t3)*Wb, x0+(t1+t2+t3+down)*Wb
    capno_in(ax, x0, x0+Wb, 1.2, 3.6, cycles=1, color=F.INK, lw=2.8, p0=0.92, ptop=1.0,
             t1=t1, t2=t2, t3=t3, down=down)
    ax.plot([x0, b1], [1.2, 1.2], color=F.INK, lw=2.8, zorder=4)
    # alpha angle arc at (b2, plateau_start) — small radius so it hugs the vertex only
    petco2_y = 1.2+3.6*1.0; p0y = 1.2+3.6*0.92
    ax.add_patch(Arc((b2, p0y), 0.9, 0.9, angle=0, theta1=185, theta2=250, color=F.GOLD, lw=2.4, zorder=5))
    txt(ax, b2+0.75, p0y-0.55, "α角", color=F.GOLD, fs=13, bold=True, ha="left")
    txt(ax, b2+0.75, p0y-0.92, "約100–110°", color=F.GOLD, fs=10.5, ha="left")
    # beta angle arc at (b3, petco2_y)
    ax.add_patch(Arc((b3, petco2_y), 0.9, 0.9, angle=0, theta1=75, theta2=150, color=F.TEAL, lw=2.4, zorder=5))
    txt(ax, b3-1.9, petco2_y+0.55, "β角", color=F.TEAL, fs=13, bold=True, ha="left")
    txt(ax, b3-1.9, petco2_y+0.18, "約90°", color=F.TEAL, fs=10.5, ha="left")
    txt(ax, x0+0.1, 5.9, "α開大→相IIIの傾き増", color=F.GRAY, fs=9.5, ha="left")
    txt(ax, b4+0.3, 2.4, "β開大→\nベースライン上昇", color=F.GRAY, fs=9.5, ha="left")
    txt(ax, 5.6, 0.55, "（詳細は第6章）", color=F.GRAY, fs=9.5)
    F.save(fig, "f0402")

def f0403():
    fig, ax = canvas(11.4, 5.4, W=12, H=6.2)
    for panel, (xoff, p0, lab, col, sub) in enumerate([
            (0.4, 0.90, "正常：ほぼ平坦（軽い＋勾配）", F.GREEN, "α角正常"),
            (6.2, 0.72, "勾配増：シャークフィンの入口", F.ORANGE, "α角開大")]):
        Wb = 5.4
        t1, t2, t3, down = 0.14, 0.10, 0.46, 0.10
        capno_in(ax, xoff+0.3, xoff+0.3+Wb, 1.0, 3.6, cycles=1, color=F.INK, lw=2.6,
                 p0=p0, ptop=1.0, t1=t1, t2=t2, t3=t3, down=down)
        b1 = xoff+0.3+t1*Wb; b2 = xoff+0.3+(t1+t2)*Wb; b3 = xoff+0.3+(t1+t2+t3)*Wb
        # slope trend line over phase III
        ax.plot([b2, b3], [1.0+3.6*p0, 1.0+3.6*1.0], color=col, lw=1.6, ls="--", zorder=3)
        txt(ax, xoff+0.3+Wb/2, 5.55, lab, color=col, fs=13, bold=True)
        txt(ax, xoff+0.3+Wb/2, 0.5, sub, color=col, fs=11.5)
    F.save(fig, "f0403")

def f0404():
    fig, ax = canvas(11.2, 6.0, W=12, H=6.8)
    x0, x1, y0 = 1.0, 11.2, 1.1
    ax.plot([x0, x1], [y0, y0], color=F.INK, lw=1.2)
    ax.plot([x0, x0], [y0, 6.2], color=F.INK, lw=1.2)
    txt(ax, (x0+x1)/2, 0.55, "呼気量 Volume (mL)", color=F.GRAY, fs=11)
    txt(ax, 0.35, 3.6, "PCO₂", color=F.GRAY, fs=11, ha="center")
    xv = np.array([x0, x0+1.0, x0+2.0, x0+7.0, x1])
    yv = np.array([y0, y0, y0+2.6, y0+3.2, y0+3.55])
    xx = np.linspace(x0, x1, 300)
    yy = np.interp(xx, xv, yv)
    ax.fill_between(xx, y0, yy, color=F.GOLDL, alpha=0.35, zorder=1)
    ax.plot(xx, yy, color=F.INK, lw=2.8, zorder=4)
    # Fowler equal-area line at x = x0+2.0 (phase II midpoint-ish)
    xf = x0+2.0
    ax.plot([xf, xf], [y0, y0+2.6], color=F.GOLD, lw=1.8, ls="--", zorder=3)
    txt(ax, xf, y0+2.9, "Fowler 等面積法", color=F.GOLD, fs=11, bold=True)
    txt(ax, xf, y0-0.35, "VDaw", color=F.GOLD, fs=12, bold=True)
    txt(ax, xf-0.55, y0+1.1, "p", color=F.BLUE, fs=13, bold=True)
    txt(ax, xf+0.55, y0+1.6, "q", color=F.BLUE, fs=13, bold=True)
    txt(ax, x0+0.5, y0+0.3, "相I", color=F.BLUE, fs=10.5)
    txt(ax, x0+1.5, y0+1.4, "相II", color=F.ORANGE, fs=10.5)
    txt(ax, x0+5.0, y0+3.6, "相III（肺胞ガス）", color=F.GREEN, fs=11)
    txt(ax, 9.5, y0+2.3, "曲線下面積＝VTCO₂", color=F.GOLD, fs=11.5, bold=True)
    txt(ax, 9.5, y0+1.85, "→ ×RR ＝ VCO₂", color=F.GOLD, fs=11.5, bold=True)
    txt(ax, 2.2, 6.45, "Bohr：VD/VT＝(PACO₂−PECO₂)/PACO₂　Enghoff：PACO₂→PaCO₂", color=F.GRAY, fs=10.5, ha="left")
    F.save(fig, "f0404")

def f0405():
    """Inset for the 4.5 bullets slide: small normal waveform with 4 numbered callouts."""
    fig, ax = canvas(6.2, 6.0, W=7, H=8)
    t1, t2, t3, down = 0.14, 0.10, 0.46, 0.10
    x0, Wb, y0, ys = 0.6, 5.8, 3.0, 3.4
    capno_in(ax, x0, x0+Wb, y0, ys, cycles=1, color=F.INK, lw=3.0, p0=0.92, ptop=1.0,
             t1=t1, t2=t2, t3=t3, down=down)
    ax.plot([x0-0.4, x0], [y0, y0], color=F.INK, lw=3.0, zorder=4)
    b1 = x0+t1*Wb; b2 = x0+(t1+t2)*Wb; b3 = x0+(t1+t2+t3)*Wb
    petco2_y = y0+ys*1.0; p0y = y0+ys*0.92
    # ① baseline
    ax.add_patch(Circle((x0-0.15, y0), 0.28, fc=F.GOLD, ec="none", zorder=6))
    txt(ax, x0-0.15, y0, "①", color="white", fs=12, bold=True, zorder=7)
    # ② steep rise + flat plateau (point at b1-b2 midpoint)
    ax.add_patch(Circle(((b1+b2)/2, y0+ys*0.5), 0.28, fc=F.GOLD, ec="none", zorder=6))
    txt(ax, (b1+b2)/2, y0+ys*0.5, "②", color="white", fs=12, bold=True, zorder=7)
    # ③ height (PetCO2)
    ax.plot([b3+0.3, b3+0.9], [petco2_y, petco2_y], color=F.GOLD, lw=1.4, ls="--", zorder=3)
    ax.add_patch(Circle((b3+1.2, petco2_y), 0.28, fc=F.GOLD, ec="none", zorder=6))
    txt(ax, b3+1.2, petco2_y, "③", color="white", fs=12, bold=True, zorder=7)
    # ④ alpha angle
    ax.add_patch(Circle((b2, 6.7), 0.28, fc=F.GOLD, ec="none", zorder=6))
    txt(ax, b2, 6.7, "④", color="white", fs=12, bold=True, zorder=7)
    F.arrow(ax, b2, 6.42, b2, p0y+0.2, color=F.GOLD, lw=1.6, ms=12)
    F.save(fig, "f0405")


# ================================================================ CH 5 ====
def f0501():
    fig, ax = canvas(11.4, 5.6, W=12, H=6.4)
    ax.plot([6.0, 6.0], [0.6, 6.0], color=F.LGRAY, lw=1.4, ls="--", zorder=1)
    # left: tracheal (6 persistent square waves)
    capno_in(ax, 0.5, 5.6, 1.0, 3.2, cycles=6, color=F.INK, lw=2.2, p0=0.92, ptop=1.0)
    txt(ax, 3.05, 5.7, "気管挿管", color=F.GOLD, fs=15, bold=True)
    txt(ax, 3.05, 5.3, "持続する矩形波（6呼吸）", color=F.GOLD, fs=11)
    for i in range(6):
        txt(ax, 0.5+5.1/6*(i+0.5), 0.7, str(i+1), color=F.GRAY, fs=8.5)
    # right: esophageal (decaying then flat)
    xo = np.linspace(6.4, 11.5, 400)
    yo = np.zeros_like(xo)
    period = (11.5-6.4)/6
    for i in range(2):
        c = 6.4 + period*(i+0.5)
        yo += 0.9*np.exp(-((xo-c)**2)/(2*(period*0.16)**2)) * (0.6**i)
    ax.plot(xo, 1.0+yo*3.2, color=F.RED, lw=2.2, zorder=4)
    ax.plot([6.4, 11.5], [1.0, 1.0], color=F.RED, lw=2.2, zorder=3)
    for i in range(6):
        txt(ax, 6.4+5.1/6*(i+0.5), 0.7, str(i+1), color=F.GRAY, fs=8.5)
    txt(ax, 8.95, 5.7, "食道挿管", color=F.RED, fs=15, bold=True)
    txt(ax, 8.95, 5.3, "数呼吸で消えて平坦", color=F.RED, fs=11)
    F.arrow(ax, 8.5, 2.3, 7.4, 1.15, color=F.RED, lw=1.6, ms=12)
    txt(ax, 8.6, 2.55, "1〜3呼吸で消失", color=F.RED, fs=9.5, ha="left")
    rbox(ax, 2.2, 0.02, 7.6, 0.55, "white", F.RED, round_=0.10,
         txt_lines=[("低肺血流(心停止・重症低心拍出)では気管でも波形が低〜出ないことがある", F.RED)], fs=9.5)
    F.save(fig, "f0501")

def f0502():
    fig, ax = canvas(11.2, 6.0, W=12, H=6.8)
    labels = [("適切", 40, F.GREEN), ("低換気", 55, F.BLUE), ("過換気", 28, F.ORANGE)]
    xw = 0.5
    for lab, pet, col in labels:
        yscale = 1.30*(pet/40)
        capno_in(ax, xw, xw+2.9, 3.55, yscale, cycles=1, color=col, lw=2.2, p0=0.9, ptop=1.0)
        txt(ax, xw+1.45, 3.55+yscale+0.55, f"{lab}  PetCO₂ {pet}", color=col, fs=12, bold=True)
        xw += 3.5
    # bottom trend: EtCO2 flat-drop-to-0 vs SpO2 lagging
    y0 = 0.6
    ax.plot([0.5, 5.0], [y0+1.7, y0+1.7], color=F.INK, lw=2.4, zorder=3)
    ax.plot([5.0, 5.15], [y0+1.7, y0], color=F.INK, lw=2.4, zorder=3)
    ax.plot([5.15, 11.5], [y0, y0], color=F.INK, lw=2.4, zorder=3)
    ax.plot([5.0, 5.0], [y0-0.15, y0+2.0], color=F.RED, lw=1.4, ls=":", zorder=2)
    txt(ax, 5.0, y0+2.25, "回路外れ/無呼吸", color=F.RED, fs=10.5, bold=True)
    # SpO2 stays high then dips later
    xs = np.linspace(0.5, 11.5, 300)
    ys = np.where(xs < 8.3, y0+1.15, y0+1.15 - 1.0*(1-np.exp(-(xs-8.3)/1.0)))
    ax.plot(xs, ys, color=F.GRAY, lw=2.2, zorder=3)
    ax.plot([8.3, 8.3], [y0-0.15, y0+1.4], color=F.GRAY, lw=1.2, ls=":", zorder=2)
    F.arrow(ax, 5.0, y0-0.35, 8.3, y0-0.35, color=F.GOLD, lw=1.8, ms=14)
    txt(ax, 6.6, y0-0.62, "lead ≈ 60 s（中央値, 範囲5–240s）", color=F.GOLD, fs=10, bold=True)
    txt(ax, 11.6, y0+1.7, "EtCO₂", color=F.INK, fs=11, bold=True, ha="left")
    txt(ax, 11.6, y0+1.05, "SpO₂", color=F.GRAY, fs=11, bold=True, ha="left")
    txt(ax, 6.0, 3.1, "EtCO₂は換気異常をSpO₂より先に捉える", color=F.GOLD, fs=12, bold=True)
    F.save(fig, "f0502")

def f0503():
    fig, ax = canvas(11.4, 5.8, W=12, H=6.6)
    # left causal flow
    steps = ["心拍出量↓", "肺血流↓", "肺胞へ運ばれるCO₂↓", "PetCO₂↓"]
    y = 5.8
    for i, s in enumerate(steps):
        rbox(ax, 0.3, y-0.55, 3.6, 0.6, F.BLUEL, F.BLUE, txt_lines=[s], fs=11.5, align="center")
        if i < len(steps)-1:
            F.arrow(ax, 2.1, y-0.58, 2.1, y-0.95, color=F.BLUE, lw=1.8)
        y -= 0.95
    # right: trend with 3 patterns + ROSC
    x0, x1, base = 4.6, 11.5, 1.3
    ax.plot([x0, x1], [base, base], color=F.LGRAY, lw=1, ls="--", zorder=1)
    xr = np.linspace(x0, x1, 400)
    pe = np.where(xr < 6.0, base+2.6, np.where(xr < 6.3, base+2.6-(xr-6.0)/0.3*1.6, base+1.0))
    ax.plot(xr, pe, color=F.ORANGE, lw=2.2, zorder=3)
    lc = np.where(xr < 6.0, base+2.6, base+2.6 - (xr-6.0)/(x1-6.0)*1.8)
    ax.plot(xr, lc, color=F.BLUE, lw=2.2, zorder=3, ls="-.")
    ca = np.where(xr < 6.0, base+2.6, np.maximum(base+2.6-(xr-6.0)*3.2, base+0.05))
    ax.plot(xr, ca, color=F.RED, lw=2.2, zorder=3)
    # ROSC recovery arrow
    F.arrow(ax, 9.6, base+0.05, 10.3, base+2.3, color=F.GREEN, lw=2.2, ms=16)
    txt(ax, 10.5, base+2.5, "循環回復/ROSC", color=F.GREEN, fs=11, bold=True, ha="left")
    txt(ax, 6.6, base+2.9, "肺塞栓：急落・波形は保つ", color=F.ORANGE, fs=10.5, ha="left")
    txt(ax, 8.7, base+1.05, "低心拍出：漸減", color=F.BLUE, fs=10.5, ha="left")
    txt(ax, 6.3, base+0.35, "心停止：≈0", color=F.RED, fs=10.5, ha="left")
    txt(ax, 8.0, 5.9, "EtCO₂ ∝ 肺血流 ∝ 心拍出量", color=F.GOLD, fs=13, bold=True)
    F.save(fig, "f0503")

def f0504():
    fig, ax = canvas(11.4, 6.0, W=12, H=6.8)
    # left: trend rising with ventilation-increase intervention not fully correcting
    x0, x1, base = 0.4, 6.0, 0.9
    xr = np.linspace(x0, x1, 300)
    yr = base + (xr-x0)/(x1-x0)*3.0
    dip = 1.1*np.exp(-((xr-3.6)**2)/(2*0.35**2))
    yr = yr - dip
    ax.plot(xr, yr, color=F.RED, lw=2.4, zorder=3)
    F.arrow(ax, 3.6, base+0.3, 3.6, base+1.7, color=F.GRAY, lw=1.8, ms=14)
    txt(ax, 3.85, base+1.9, "分時換気量↑", color=F.GRAY, fs=10, ha="left")
    txt(ax, 3.05, 5.4, "換気で追いつかない＝産生↑を疑う", color=F.RED, fs=11.5, bold=True)
    # right: differential boxes
    rbox(ax, 6.6, 4.55, 4.9, 1.55, F.GREENL, F.GREEN, title="一過性・局所", title_color=F.GREEN, title_fs=11.5,
         txt_lines=["駆血解除・CO₂気腹の吸収・NaHCO₃投与"], fs=10)
    rbox(ax, 6.6, 2.85, 4.9, 1.5, F.BLUEL, F.BLUE, title="全身性の産生亢進", title_color=F.BLUE, title_fs=11.5,
         txt_lines=["発熱・敗血症・甲状腺クリーゼ"], fs=10)
    rbox(ax, 6.6, 0.7, 4.9, 1.95, "white", F.RED, title="悪性高熱（MH）", title_color=F.RED, title_fs=13,
         txt_lines=[("早期・鋭敏だが", F.INK), ("“単独では非診断”", F.RED),
                     ("随伴: 頻脈・咬筋硬直・混合性アシドーシス", F.INK)], fs=9.5)
    F.save(fig, "f0504")

def f0505():
    fig, ax = canvas(11.6, 5.4, W=12, H=6.2)
    # panel A: curare cleft
    rbox(ax, 0.3, 0.4, 3.5, 5.4, "white", F.GOLD, title="くぼみ＝自発呼吸の再開", title_color=F.GOLD, title_fs=10.5)
    capno_in(ax, 0.7, 3.5, 1.2, 3.0, cycles=2, color=F.INK, lw=2.2, p0=0.9, ptop=1.0)
    ax.plot([1.95, 2.15, 2.35], [1.2+3.0*0.98, 1.2+3.0*0.7, 1.2+3.0*0.98], color=F.RED, lw=2.0, zorder=5)
    txt(ax, 2.15, 1.2+3.0*0.55, "筋弛緩の醒め", color=F.RED, fs=9, bold=True)
    # panel B: shallow/deep breathing density
    rbox(ax, 4.1, 0.4, 3.5, 5.4, "white", F.BLUE, title="浅麻酔：頻呼吸・波形が密", title_color=F.BLUE, title_fs=10.5)
    capno_in(ax, 4.5, 7.3, 3.5, 1.3, cycles=5, color=F.BLUE, lw=1.8, p0=0.9, ptop=1.0)
    capno_in(ax, 4.5, 7.3, 1.2, 1.3, cycles=2, color=F.GREEN, lw=1.8, p0=0.9, ptop=1.0)
    txt(ax, 5.9, 5.0, "浅麻酔（頻呼吸）", color=F.BLUE, fs=9.5)
    txt(ax, 5.9, 2.7, "深麻酔/十分な鎮痛", color=F.GREEN, fs=9.5)
    # panel C: target band
    rbox(ax, 7.9, 0.4, 3.5, 5.4, "white", F.GREEN, title="目標帯へ調整", title_color=F.GREEN, title_fs=11)
    ax.add_patch(Rectangle((8.3, 2.6), 2.7, 0.9, fc=F.GREENL, alpha=0.6, ec="none", zorder=1))
    txt(ax, 9.65, 3.05, "目標 PetCO₂ 35–45", color=F.GREEN, fs=10, bold=True)
    xr = np.linspace(8.3, 11.0, 200)
    yr = 3.9 - (xr-8.3)/2.7*1.0 + 0.15*np.sin((xr-8.3)*6)
    ax.plot(xr, yr, color=F.INK, lw=2.0, zorder=3)
    txt(ax, 9.65, 1.1, "許容的高炭酸：帯を上方修正", color=F.GRAY, fs=9)
    F.save(fig, "f0505")


# ================================================================ CH 6 ====
def f0601():
    fig, ax = canvas(10.4, 6.4, W=11, H=7.2)
    cx0, Wb, y0, ys = 2.6, 5.8, 2.8, 2.9
    capno_in(ax, cx0, cx0+Wb, y0, ys, cycles=1, color=F.INK, lw=2.8, p0=0.92, ptop=1.0)
    ax.plot([cx0-0.5, cx0], [y0, y0], color=F.INK, lw=2.8, zorder=4)
    t1, t2, t3 = 0.14, 0.10, 0.46
    b1, b2, b3 = cx0+t1*Wb, cx0+(t1+t2)*Wb, cx0+(t1+t2+t3)*Wb
    txt(ax, (cx0+b1)/2, y0-0.35, "相I", color=F.GRAY, fs=10)
    txt(ax, (b1+b2)/2, y0-0.35, "相II", color=F.GRAY, fs=10)
    txt(ax, (b2+b3)/2, y0-0.35, "相III", color=F.GRAY, fs=10)
    # 4 corner boxes with leader lines, numbered in read-order with a circular flow arrow
    boxes = [
        (0.3, 5.9, "①ベースライン", F.GOLD, "吸気側は0に戻るか\n（＞0＝リブリージング）", (cx0-0.2, y0)),
        (7.0, 5.9, "②高さ（振幅）", F.GOLD, "PetCO₂ は35–45か\n（高い/低い/消失）", (b2, y0+ys*1.0)),
        (7.0, 0.3, "③形", F.GOLD, "立ち上がりは急峻か\nプラトーは平らか・α角は", (b1, y0+ys*0.5)),
        (0.3, 0.3, "④呼吸数/リズム", F.GOLD, "頻呼吸/徐呼吸・不整\n自発の混入（くぼみ）", (cx0+2.6, y0+ys)),
    ]
    for bx, by, title, col, body, (lx, ly) in boxes:
        rbox(ax, bx, by, 3.4, 1.0, "white", col, title=title, title_fs=12.5, title_color=col,
             txt_lines=[(ln, F.INK) for ln in body.split("\n")], fs=9.5)
        anchor_x = bx+1.7; anchor_y = by if by > 3.6 else by+1.0
        ax.plot([anchor_x, lx], [anchor_y, ly], color=col, lw=1.1, ls=":", zorder=2)
    F.save(fig, "f0601")

def f0602():
    fig, ax = canvas(11.2, 5.4, W=12, H=6.2)
    for xoff, title, col, rebreath in [(0.4, "正常（参照）", F.GOLD, False), (6.2, "リブリージング", F.RED, True)]:
        Wb = 5.2
        base = 1.0 if not rebreath else 1.9
        capno_in(ax, xoff+0.3, xoff+0.3+Wb, base, 3.4, cycles=2, color=(F.GOLD if not rebreath else F.INK),
                 lw=2.4, p0=0.92, ptop=1.0)
        txt(ax, xoff+0.3+Wb/2, 5.6, title, color=col, fs=13.5, bold=True)
        if rebreath:
            ax.plot([xoff+0.3, xoff+0.3+Wb], [1.0, 1.0], color=F.LGRAY, lw=1.2, ls="--", zorder=1)
            ax.plot([xoff+0.3, xoff+0.3+Wb], [base, base], color=F.RED, lw=1.6, ls=":", zorder=3)
            F.arrow(ax, xoff+0.15, 1.0, xoff+0.15, base, color=F.RED, lw=1.6, ms=12)
            txt(ax, xoff-0.15, (1.0+base)/2, "吸気CO₂＞0", color=F.RED, fs=9.5, ha="right")
    # cause boxes under the rebreathing panel (must stay within W=12 or FancyBboxPatch clips)
    causes = ["① CO₂吸収剤の消耗", "② 一方向弁の不良", "③ FGF不足/機械死腔"]
    cx = 6.35
    for c in causes:
        rbox(ax, cx, 0.15, 1.72, 0.6, F.ORANGEL, F.ORANGE, txt_lines=[c], fs=9, align="center")
        cx += 1.82
    F.save(fig, "f0602")

def f0603():
    fig, ax = canvas(11.2, 5.4, W=12, H=6.2)
    # left normal
    Wb = 5.0
    capno_in(ax, 0.6, 0.6+Wb, 1.0, 3.4, cycles=1, color=F.GOLD, lw=2.4, p0=0.92, ptop=1.0)
    txt(ax, 0.6+Wb/2, 5.6, "正常", color=F.GOLD, fs=14, bold=True)
    txt(ax, 0.6+Wb/2, 0.55, "急峻な相II＋平らな相III／α≈100–110°", color=F.GOLD, fs=10)
    # right sharkfin
    x2 = 6.6
    X, Y = F.capno_train(cycles=1, p0=0, ptop=1.0)
    from figlib import sharkfin_cycle
    xs, ys = sharkfin_cycle(ptop=1.0)
    xs2 = x2 + xs*Wb
    ys2 = 1.0 + ys*3.4
    ax.plot(xs2, ys2, color=F.INK, lw=2.6, zorder=4)
    # reference dotted plateau (ghost of normal)
    ax.plot([x2+0.10*Wb, x2+0.86*Wb], [1.0+3.4*1.0, 1.0+3.4*1.0], color=F.RED, lw=1.3, ls=":", zorder=3)
    txt(ax, x2+0.48*Wb, 1.0+3.4*1.0+0.3, "本来のプラトー", color=F.RED, fs=9)
    txt(ax, x2+Wb/2, 5.6, "シャークフィン（閉塞性）", color=F.ORANGE, fs=14, bold=True)
    txt(ax, x2+Wb/2, 0.55, "α角増大（鈍化）／プラトー消失", color=F.ORANGE, fs=10)
    F.arrow(ax, x2+0.55*Wb, 1.0+3.4*0.55, x2+0.30*Wb, 1.0+3.4*0.80, color=F.RED, lw=1.6, ms=12)
    F.save(fig, "f0603")

def f0604():
    fig, ax = canvas(11.2, 5.0, W=12, H=5.8)
    x0, base, ys = 0.5, 1.0, 3.2
    n = 4
    Wb_each = 2.6
    for i in range(n):
        xo = x0 + i*Wb_each
        depth = 0.10 + i*0.10
        t1, t2, t3, down = 0.14, 0.10, 0.46, 0.10
        X, Y = F.capno_cycle(t1=t1, t2=t2, t3=t3, down=down, p0=0.92, ptop=1.0)
        # add a downward notch mid-phase-III
        m = (X > 0.45) & (X < 0.62)
        notch = np.zeros_like(X)
        idxs = np.where(m)[0]
        if len(idxs):
            mid = idxs[len(idxs)//2]
            notch[m] = -depth * np.exp(-((X[m]-X[mid])**2)/(2*0.02**2))
        Yc = Y + notch
        ax.plot(xo+X*Wb_each*0.92, base+Yc*ys, color=F.INK, lw=2.4, zorder=4)
    ax.plot([x0, x0+2.6], [base+ys*1.0, base+ys*1.0], color=F.GOLD, lw=1.2, ls=":", zorder=2)
    txt(ax, x0+1.2, base+ys*1.0+0.28, "本来の平プラトー", color=F.GOLD, fs=9.5, ha="left")
    txt(ax, x0+Wb_each*2.2, base+ys*0.55, "くぼみ＝curare cleft", color=F.RED, fs=12, bold=True)
    F.arrow(ax, x0+0.3, base-0.35, x0+n*Wb_each-1.0, base-0.35, color=F.GRAY, lw=1.6, ms=12)
    txt(ax, x0+n*Wb_each/2, base-0.75, "醒めの進行（くぼみが徐々に深く）", color=F.GRAY, fs=10)
    txt(ax, x0+n*Wb_each/2, base+ys+0.9, "調節換気中のプラトーのくぼみ＝自発呼吸の再出現", color=F.GOLD, fs=12.5, bold=True)
    F.save(fig, "f0604")

def f0605():
    fig, ax = canvas(11.6, 5.6, W=12, H=6.4)
    panels = [
        (0.3, "A 波形消失(フラット・0)", F.RED, "flat", "回路外れ・完全閉塞・抜管・\nサンプリング異常・無呼吸"),
        (3.15, "B 低いが波形あり", F.ORANGE, "low", "大きなリーク・過換気"),
        (6.0, "C 波形残存で漸減", F.BLUE, "decline", "肺塞栓・低心拍出・大出血\n（循環）"),
        (8.85, "D ほぼ0へ急落", F.RED, "arrest", "心停止（第7/8章へ）"),
    ]
    Wp = 2.6
    for xo, title, col, kind, desc in panels:
        base = 0.55
        if kind == "flat":
            capno_in(ax, xo, xo+Wp*0.55, base, 3.0, cycles=1.6, color=F.GOLD, lw=1.8, p0=0.9, ptop=1.0)
            ax.plot([xo+Wp*0.55, xo+Wp], [base, base], color=F.RED, lw=2.4, zorder=4)
        elif kind == "low":
            capno_in(ax, xo, xo+Wp*0.5, base, 3.0, cycles=1.2, color=F.GOLD, lw=1.8, p0=0.9, ptop=1.0)
            capno_in(ax, xo+Wp*0.5, xo+Wp, base, 1.1, cycles=1.2, color=F.ORANGE, lw=2.0, p0=0.85, ptop=1.0)
        elif kind == "decline":
            capno_in(ax, xo, xo+Wp*0.4, base, 3.0, cycles=1.1, color=F.GOLD, lw=1.8, p0=0.9, ptop=1.0)
            # stepped decline using 3 shrinking breaths (form preserved, height falls)
            xx = xo+Wp*0.4
            for k in range(3):
                h = 3.0*(0.72**k)
                capno_in(ax, xx, xx+Wp*0.2, base, h, cycles=1.0, color=F.BLUE, lw=2.0, p0=0.9, ptop=1.0)
                xx += Wp*0.2
        elif kind == "arrest":
            capno_in(ax, xo, xo+Wp*0.35, base, 3.0, cycles=1.0, color=F.GOLD, lw=1.8, p0=0.9, ptop=1.0)
            xr = np.linspace(xo+Wp*0.35, xo+Wp, 100)
            yr = base + 3.0*np.exp(-(xr-xo-Wp*0.35)*4)
            ax.plot(xr, yr, color=F.RED, lw=2.4, zorder=4)
        ax.plot([xo, xo, xo+Wp, xo+Wp], [base-0.35, base+3.35, base+3.35, base-0.35], color=F.LGRAY, lw=0.8, zorder=1)
        txt(ax, xo+Wp/2, 4.35, title, color=col, fs=11, bold=True)
        for k, ln in enumerate(desc.split("\n")):
            txt(ax, xo+Wp/2, 0.05-k*0.3, ln, color=F.INK, fs=9)
    txt(ax, 6.0, 5.85, "波形が“消えてフラット”＝換気/回路/機械／“小さく残る”＝循環（肺血流）", color=F.GOLD, fs=12, bold=True)
    F.save(fig, "f0605")

def f0606():
    fig, ax = canvas(11.2, 5.6, W=12, H=6.4)
    x0, x1, base = 0.6, 11.4, 3.2
    ax.add_patch(Rectangle((x0, base-0.5), x1-x0, 1.0, fc=F.GOLDL, alpha=0.5, ec="none", zorder=1))
    txt(ax, x0+0.2, base, "正常帯 35–45", color=F.GOLD, fs=10, ha="left")
    xr = np.linspace(x0+1.5, x1, 200)
    yu = base + (xr-x0-1.5)/(x1-x0-1.5)*2.0
    ax.plot(xr, yu, color=F.ORANGE, lw=2.4, zorder=3)
    # steep MH branch off the rising line
    xm = np.linspace(x0+6.5, x0+9.0, 80)
    ym = np.interp(x0+6.5, xr, yu) + (xm-x0-6.5)*1.1
    ax.plot(xm, ym, color=F.RED, lw=2.6, zorder=4)
    txt(ax, x0+9.2, ym[-1], "悪性高熱(MH)\n急峻・顕著", color=F.RED, fs=10.5, bold=True, ha="left")
    xd = np.linspace(x0+1.5, x1, 200)
    yd = base - (xd-x0-1.5)/(x1-x0-1.5)*1.8
    ax.plot(xd, yd, color=F.BLUE, lw=2.4, zorder=3)
    txt(ax, x0+0.3, base+2.3, "漸増↑：低換気・産生↑(発熱/敗血症/駆血解除)・CO₂吸収・心拍出↑", color=F.ORANGE, fs=10, ha="left")
    txt(ax, x0+0.3, base-2.3, "漸減↓：過換気・心拍出低下/循環血液量減少・低体温/代謝低下", color=F.BLUE, fs=10, ha="left")
    txt(ax, 6.0, 5.95, "PetCO₂ (mmHg) の分単位トレンド", color=F.GRAY, fs=11)
    F.save(fig, "f0606")

def f0607():
    fig, ax = canvas(10.6, 6.6, W=11, H=7.4)
    quads = [
        (0.3, 3.9, "① 心原性振動", F.BLUE, "cardiogenic"),
        (5.9, 3.9, "② 二相性プラトー", F.GREEN, "biphasic"),
        (0.3, 0.3, "③ リーク波形", F.ORANGE, "leak"),
        (5.9, 0.3, "④ tails［要確認］", F.GRAY, "tails"),
    ]
    Wq, Hq = 4.6, 3.2
    for bx, by, title, col, kind in quads:
        rbox(ax, bx, by, Wq, Hq, "white", col, title=title, title_color=col, title_fs=12.5)
        x0, x1 = bx+0.35, bx+Wq-0.35
        base, ys = by+0.55, Hq-1.5
        # ghost reference
        capno_in(ax, x0, x1, base, ys, cycles=1, color=F.LGRAY, lw=1.4, p0=0.92, ptop=1.0, zorder=2)
        if kind == "cardiogenic":
            t1,t2,t3,down = 0.14,0.10,0.46,0.10
            X, Y = F.capno_cycle(t1=t1,t2=t2,t3=t3,down=down,p0=0.92,ptop=1.0)
            m = X > (t1+t2+t3)
            ripple = np.zeros_like(X)
            ripple[m] = 0.05*np.sin((X[m]-X[m][0])*90)
            ax.plot(x0+X*(x1-x0), base+(Y+ripple)*ys, color=col, lw=2.2, zorder=4)
        elif kind == "biphasic":
            xs = [0, 0.14, 0.24, 0.5, 0.62, 0.70, 0.80, 1.0]
            ys_ = [0, 0, 0.85, 0.90, 0.78, 1.0, 0, 0]
            xx = np.linspace(0,1,200); yy = np.interp(xx, xs, ys_)
            ax.plot(x0+xx*(x1-x0), base+yy*ys, color=col, lw=2.2, zorder=4)
        elif kind == "leak":
            xs = [0, 0.16, 0.5, 0.80, 1.0]
            ys_ = [0, 0, 0.55, 0.35, 0]
            xx = np.linspace(0,1,200); yy = np.interp(xx, xs, ys_)
            ax.plot(x0+xx*(x1-x0), base+yy*ys, color=col, lw=2.2, zorder=4)
        elif kind == "tails":
            t1,t2,t3,down = 0.14,0.10,0.46,0.14
            X, Y = F.capno_cycle(t1=t1,t2=t2,t3=t3,down=down,p0=0.92,ptop=1.0)
            m = (X > (t1+t2+t3)) & (X < (t1+t2+t3+down))
            tail = np.zeros_like(X)
            tail[m] = 0.10
            ax.plot(x0+X*(x1-x0), base+(Y+tail)*ys, color=col, lw=2.2, zorder=4)
    F.save(fig, "f0607")


# ================================================================ CH 7 ====
def f0701():
    fig, ax = canvas(10.6, 6.6, W=11, H=7.4)
    rbox(ax, 3.0, 6.5, 5.0, 0.75, "white", F.RED, txt_lines=[("EtCO₂ 波形が突然ゼロ（平坦）", F.RED)], fs=13, align="center")
    F.arrow(ax, 5.5, 6.45, 5.5, 5.95, color=F.INK, lw=2.0)
    rbox(ax, 2.4, 5.3, 6.2, 0.6, F.GOLDL, F.GOLD, txt_lines=[("胸郭挙上・脈拍・SpO₂ を即確認", F.GOLD)], fs=12, align="center")
    F.arrow(ax, 3.8, 5.25, 1.6, 4.75, color=F.RED, lw=1.8)
    F.arrow(ax, 7.2, 5.25, 8.6, 4.75, color=F.BLUE, lw=1.8)
    rbox(ax, 0.3, 4.05, 2.6, 0.65, "white", F.RED, txt_lines=[("脈拍なし/循環虚脱", F.RED)], fs=10.5, align="center")
    rbox(ax, 0.3, 3.0, 2.6, 0.9, F.ORANGEL, F.RED, txt_lines=[("心停止を想定", F.RED), ("CPR・ACLS（8.1へ）", F.INK)], fs=10.5, align="center")
    F.arrow(ax, 1.6, 4.02, 1.6, 3.95, color=F.RED, lw=1.6)
    rbox(ax, 6.6, 4.05, 4.1, 0.65, F.BLUEL, F.BLUE, txt_lines=[("循環は保たれる → 用手換気に切替（100%O₂）", F.BLUE)], fs=9.5, align="center")
    F.arrow(ax, 8.6, 4.0, 8.6, 3.55, color=F.BLUE, lw=1.6)
    steps = ["①患者：胸郭挙上・両側呼吸音・SpO₂／気胸・重度気管支攣縮",
             "②チューブ：抜管・食道挿管・位置ずれ・屈曲/咬み込み/分泌物閉塞",
             "③回路：接続外れ・人工呼吸器停止・弁/APL・ガス供給",
             "④モニタ：サンプリング外れ/閉塞・水トラップ・較正エラー"]
    y = 3.35
    for s in steps:
        rbox(ax, 5.6, y-0.55, 5.1, 0.6, F.BLUEL, F.BLUE, txt_lines=[s], fs=8.5, align="center")
        y -= 0.68
    txt(ax, 5.5, 0.35, "DOPES：Displacement/Obstruction/Pneumothorax/Equipment/Stomach を脇に併記", color=F.GRAY, fs=9.5)
    F.save(fig, "f0701")

def f0702():
    fig, ax = canvas(11.6, 7.4, W=12, H=8.2)
    # left column: waveform mini + notes
    capno_in(ax, 0.3, 2.6, 6.6, 1.35, cycles=1, color=F.GOLD, lw=2.2, p0=0.9, ptop=1.0)
    capno_in(ax, 2.9, 5.2, 6.6, 0.55, cycles=2, color=F.BLUE, lw=2.2, p0=0.85, ptop=1.0)
    txt(ax, 2.75, 8.05, "形は保持・高さのみ低下", color=F.BLUE, fs=11, bold=True)
    txt(ax, 2.75, 5.9, "（波形の形は保持、高さのみ急落＝肺血流の急減）", color=F.GRAY, fs=8.5)
    txt(ax, 2.6, 1.5, "正常 35–45 mmHg", color=F.GRAY, fs=10.5)
    txt(ax, 2.6, 1.05, "心停止・高度低灌流で", color=F.RED, fs=10)
    txt(ax, 2.6, 0.65, "EtCO₂ <10 mmHg 目安", color=F.RED, fs=10)
    # right column: decision flow, generously spaced
    rbox(ax, 6.6, 7.35, 5.0, 0.7, F.GOLDL, F.GOLD, txt_lines=[("脈拍・血圧・リズムを即確認", F.GOLD)], fs=11.5, align="center")
    F.arrow(ax, 7.6, 7.32, 6.7, 6.75, color=F.RED, lw=1.8)
    F.arrow(ax, 10.6, 7.32, 10.9, 6.75, color=F.ORANGE, lw=1.8)
    rbox(ax, 5.2, 5.55, 3.1, 1.15, "white", F.RED, title="心停止＝CPR", title_color=F.RED, title_fs=12,
         txt_lines=["EtCO₂ しばしば一桁"], fs=10)
    rbox(ax, 8.6, 5.55, 3.2, 1.15, F.ORANGEL, F.ORANGE, title="塞栓／低心拍出", title_color=F.ORANGE, title_fs=12,
         txt_lines=["肺血栓塞栓・空気塞栓・CO₂塞栓・出血"], fs=9.5)
    rbox(ax, 5.2, 3.7, 6.6, 1.55, "#DCF2DC", F.GREEN, title="初動", title_color=F.GREEN, title_fs=13,
         txt_lines=["100%O₂・N₂O中止・昇圧/輸液で循環維持", "外科操作を一旦中断・心エコー/TEEで確認"], fs=10.5)
    rbox(ax, 5.2, 0.4, 6.6, 3.0, "white", F.BLUE, title="空気塞栓の追加初動", title_color=F.BLUE, title_fs=13,
         txt_lines=["術野を心臓より低く・生食で覆う", "Durant体位（左側臥位・頭低位）", "中心静脈カテーテルから空気吸引"], fs=11)
    F.save(fig, "f0702")

def f0703():
    fig, ax = canvas(11.4, 6.0, W=12, H=6.8)
    rbox(ax, 0.3, 5.9, 4.4, 0.7, F.GOLDL, F.GOLD, txt_lines=[("①分時換気量↑（RR・TV）", F.GOLD)], fs=11.5, align="center")
    F.arrow(ax, 4.7, 6.25, 5.5, 6.25, color=F.INK, lw=1.8)
    rbox(ax, 5.6, 5.9, 2.6, 0.7, "white", F.INK, txt_lines=[("②下がるか？", F.INK)], fs=11.5, align="center")
    F.arrow(ax, 6.2, 5.85, 3.0, 4.95, color=F.GREEN, lw=1.8)
    txt(ax, 4.6, 5.4, "Yes", color=F.GREEN, fs=11, bold=True)
    F.arrow(ax, 7.6, 5.85, 9.3, 4.95, color=F.RED, lw=1.8)
    txt(ax, 8.7, 5.4, "No（頻脈・硬直）", color=F.RED, fs=11, bold=True)
    rbox(ax, 0.3, 3.9, 5.4, 1.0, "#DCF2DC", F.GREEN, title="換気起因", title_color=F.GREEN, title_fs=12,
         txt_lines=["設定・自発呼吸出現・回路・CO₂吸収(気腹)", "産生亢進(発熱/敗血症/駆血解除)を評価"], fs=9.5)
    rbox(ax, 6.6, 3.55, 4.9, 1.35, "white", F.RED, title="悪性高熱（MH）を疑う", title_color=F.RED, title_fs=13)
    steps = ["1. 応援要請・MHカート（ダントロレン）", "2. トリガー中止（揮発性麻酔薬・スキサメトニウム）",
             "3. 100%O₂・高新鮮ガス流量(≥10L/min)で過換気", "4. 非トリガー麻酔へ切替（TIVA）",
             "5. ダントロレン 2.5 mg/kg 静注、効果まで反復", "6. 積極的冷却（~38℃で中止）",
             "7. 高K血症・アシドーシス・不整脈の是正", "8. モニタ強化：深部体温・血ガス/K・CK・尿量"]
    y = 3.35
    for s in steps:
        txt(ax, 6.7, y, s, color=F.RED if s.startswith(("5.","2.")) else F.INK, fs=9.5, ha="left")
        y -= 0.36
    txt(ax, 9.0, 0.35, "EtCO₂ の急上昇はMHの最も早く鋭敏な指標", color=F.RED, fs=10.5, bold=True)
    F.save(fig, "f0703")

def f0704():
    fig, ax = canvas(11.4, 6.2, W=12, H=7.0)
    Wb = 5.6
    from figlib import sharkfin_cycle
    xs, ys = sharkfin_cycle(ptop=1.0)
    ax.plot(0.4+xs*Wb, 4.5+ys*1.9, color=F.ORANGE, lw=2.4, zorder=4)
    txt(ax, 0.4+Wb/2, 6.65, "before：シャークフィン（相II緩やか・α角>110°）", color=F.ORANGE, fs=11.5, bold=True)
    F.arrow(ax, 3.2, 4.3, 3.2, 3.15, color=F.GOLD, lw=2.4, ms=18)
    txt(ax, 3.85, 3.7, "治療", color=F.GOLD, fs=12, bold=True)
    capno_in(ax, 0.4, 0.4+Wb, 0.5, 1.9, cycles=1, color=F.GREEN, lw=2.4, p0=0.92, ptop=1.0)
    txt(ax, 0.4+Wb/2, 2.65, "after：矩形化（α角↓・プラトー平坦化・気道内圧↓）", color=F.GREEN, fs=11, bold=True)
    # right column: 3-step response
    rbox(ax, 6.6, 5.1, 5.0, 1.3, "#DCF2DC", F.GREEN, title="①機械的閉塞を除外", title_color=F.GREEN, title_fs=12,
         txt_lines=["チューブ屈曲・咬み込み・分泌物・片肺挿管", "→ 吸引カテ通過・チューブ/カフ確認"], fs=9.5)
    rbox(ax, 6.6, 3.35, 5.0, 1.55, F.BLUEL, F.BLUE, title="②気管支拡張", title_color=F.BLUE, title_fs=12,
         txt_lines=["麻酔深度↑（セボフルラン等の気管支拡張作用）", "プロポフォール/ケタミンも", "β2吸入（サルブタモール回路内）"], fs=9.5)
    rbox(ax, 6.6, 1.1, 5.0, 2.05, "white", F.RED, title="③重症・難治", title_color=F.RED, title_fs=12,
         txt_lines=["アドレナリン（静注/皮下）・抗コリン（イプラトロピウム）",
                     "硫酸マグネシウム・ステロイド",
                     "原因是正（浅麻酔/アナフィラキシー/誤嚥）"], fs=9.5)
    txt(ax, 9.1, 0.55, "呼気時間を延長（呼吸数↓・I:E調整）で auto-PEEP/ガス捕捉回避、許容的高CO₂", color=F.GRAY, fs=9.5)
    F.save(fig, "f0704")


def f0706():
    """Troubleshooting table rendered as a matplotlib table (11 rows x 3 cols)."""
    rows = [
        ("波形が突然ゼロ（平坦）", "回路外れ／完全閉塞・抜管・食道挿管／心停止", "用手換気・100%O₂／患者-チューブ-回路-モニタ確認／\n脈なければCPR", False),
        ("急低下（形は保つ・高さ↓）", "肺塞栓（血栓/空気/CO₂）・急な低心拍出・大量出血", "脈・血圧・リズム評価／100%O₂・昇圧・輸液／\n原因検索（TEE）", False),
        ("漸減トレンド", "過換気・体温低下・心拍出の漸減", "換気設定を見直す／体温・循環をトレンドで評価", False),
        ("漸増トレンド", "低換気・CO₂吸収（気腹）・発熱/代謝亢進", "分時換気量を増やす／原因検索", False),
        ("換気↑でも下がらない急上昇＋頻脈/硬直", "悪性高熱（MH）を疑う", "トリガー中止・100%O₂高流量／\nダントロレン2.5mg/kg／冷却・電解質是正", True),
        ("ベースライン上昇（吸気CO₂>0）", "再呼吸：吸収剤消耗・弁不良・新鮮ガス不足", "新鮮ガス増量／吸収剤交換／弁点検", False),
        ("シャークフィン・相III上り勾配", "気管支攣縮・COPD・チューブ部分閉塞", "チューブ確認・吸引／麻酔深度↑・β2吸入／呼気時間延長", False),
        ("プラトーのくぼみ（curare cleft）", "調節換気中の自発呼吸出現（筋弛緩の醒め）", "鎮静/鎮痛・筋弛緩を評価し追加", False),
        ("小さな規則的振動", "心原性オシレーション", "通常は生理的・介入不要", False),
        ("プラトーに達しない・低くなだらか", "水/分泌物・リーク・低TV・部分閉塞", "サンプリングライン/水トラップ点検・リーク確認", False),
        ("数値だけ低く波形は正常（サイド）", "サンプリング希釈・較正ずれ", "較正・サンプリング流量を確認／a–ET較差で解釈", False),
    ]
    fig, ax = F.newfig(13.0, 7.6)
    F.clean(ax)
    ax.set_xlim(0, 13); ax.set_ylim(0, 7.8)
    headers = ["波形／所見", "主な原因", "初動"]
    colx = [0.2, 3.5, 7.9]
    colw = [3.2, 4.3, 4.9]
    header_h = 0.55
    row_h = (7.8-0.15-header_h) / len(rows)
    ytop = 7.65
    ax.add_patch(Rectangle((0.2, ytop-header_h), 12.6, header_h, fc=F.TEAL, ec="none", zorder=1))
    for cx, cw, h in zip(colx, colw, headers):
        txt(ax, cx+0.1, ytop-header_h/2, h, color="white", fs=13, bold=True, ha="left")
    y = ytop-header_h
    for i, (finding, cause, action, mh) in enumerate(rows):
        rc = "#FBDDDD" if mh else ("#F4F6F8" if i % 2 == 0 else "white")
        ax.add_patch(Rectangle((0.2, y-row_h), 12.6, row_h, fc=rc, ec="#DDDDDD", lw=0.6, zorder=1))
        tcol = F.RED if mh else F.INK
        for cx, cw, txtval, bold in zip(colx, colw, [finding, cause, action],
                                         [mh, False, True]):
            ax.text(cx+0.1, y-row_h/2, txtval, color=(F.RED if (mh and cx==colx[0]) else (F.GOLD if bold else tcol)),
                    fontsize=9.3, fontweight="bold" if (bold or mh) else "normal", ha="left", va="center",
                    wrap=True, zorder=4)
        y -= row_h
    F.save(fig, "f0706")


# ================================================================ CH 8 ====
def f0801():
    fig, ax = canvas(11.4, 7.2, W=12, H=8.2)
    x0, x1 = 0.6, 11.4
    # low-quality band + squiggle (y 1.6-2.5)
    ax.add_patch(Rectangle((x0, 1.6), x1-x0, 0.9, fc="#F4C7C3", alpha=0.4, ec="none", zorder=1))
    xr = np.linspace(x0+0.3, x0+3.5, 100)
    yr = 2.0 + 0.12*np.sin((xr-x0)*8)
    ax.plot(xr, yr, color=F.RED, lw=2.4, zorder=3)
    txt(ax, x0+0.2, 1.3, "EtCO₂ <10 mmHg：圧迫不十分/予後不良の目安", color=F.RED, fs=10, ha="left")
    # rising (quality improves)
    xr2 = np.linspace(x0+3.5, x0+6.5, 100)
    yr2 = np.linspace(yr[-1], 3.8, 100) + 0.08*np.sin((xr2-x0)*8)
    ax.plot(xr2, yr2, color=F.GREEN, lw=2.4, zorder=3)
    txt(ax, x0+4.7, 4.35, "圧迫改善で上昇", color=F.GREEN, fs=11, bold=True)
    # steep ROSC rise + plateau
    xr4 = np.linspace(x0+7.0, x0+7.8, 60)
    yr4 = np.linspace(3.8, 6.8, 60)
    ax.plot(xr4, yr4, color=F.GOLD, lw=3.0, zorder=4)
    ax.plot([x0+7.8, x1], [6.8, 6.8], color=F.GOLD, lw=2.4, zorder=3)
    F.arrow(ax, x0+7.8, 6.85, x0+8.2, 7.25, color=F.GOLD, lw=2.6, ms=16)
    txt(ax, x0+8.5, 7.55, "ROSC を示唆", color=F.GOLD, fs=13, bold=True, ha="left")
    # legend chips at the very bottom (own row, clear of the curve)
    rbox(ax, 0.6, 0.15, 2.9, 0.6, F.BLUEL, F.BLUE, txt_lines=[("質の指標", F.BLUE)], fs=10.5, align="center")
    rbox(ax, 3.7, 0.15, 3.6, 0.6, "#DCF2DC", F.GREEN, txt_lines=[("ROSCの検知(圧迫を止めずに)", F.GREEN)], fs=9.5, align="center")
    rbox(ax, 7.5, 0.15, 3.9, 0.6, F.GOLDL, F.GOLD, txt_lines=[("予後の補助(単独では決めない)", F.GOLD)], fs=9, align="center")
    txt(ax, 6.0, 0.95, "換気を増やしすぎない＝解釈が濁る（過換気で低下）", color=F.GRAY, fs=9.5)
    F.save(fig, "f0801")

def f0802():
    fig, ax = canvas(11.2, 5.8, W=12, H=6.6)
    capno_in(ax, 0.6, 11.0, 3.9, 1.7, cycles=6, color=F.INK, lw=2.0, p0=0.92, ptop=1.0)
    txt(ax, 5.8, 5.9, "気管挿管：持続波形＝気管（6呼吸）", color=F.GOLD, fs=13, bold=True)
    xo = np.linspace(0.6, 11.0, 400)
    yo = np.zeros_like(xo)
    period = (11.0-0.6)/6
    for i in range(2):
        c = 0.6 + period*(i+0.5)
        yo += 0.85*np.exp(-((xo-c)**2)/(2*(period*0.16)**2)) * (0.6**i)
    ax.plot(xo, 0.9+yo*1.5, color=F.RED, lw=2.0, zorder=4)
    ax.plot([0.6, 11.0], [0.9, 0.9], color=F.RED, lw=2.0, zorder=3)
    txt(ax, 5.8, 2.75, "食道挿管：数呼吸で消失＝食道", color=F.RED, fs=13, bold=True)
    icons = ["手術室", "救急", "病院前・搬送", "ICU"]
    cx = 0.7
    for ic in icons:
        rbox(ax, cx, 0.1, 2.55, 0.55, F.BLUEL, F.BLUE, txt_lines=[ic], fs=10, align="center")
        cx += 2.7
    F.save(fig, "f0802")

def f0803():
    fig, ax = canvas(11.2, 5.6, W=12, H=6.4)
    x0, x1 = 0.6, 11.4
    ys_top = 4.3
    xs = np.linspace(x0, x1, 400)
    yspo2 = np.where(xs < 7.5, ys_top, ys_top - 1.0*(1-np.exp(-(xs-7.5)/1.3)))
    ax.plot(xs, yspo2, color=F.GRAY, lw=2.2, zorder=3)
    txt(ax, x0+0.1, ys_top+0.35, "SpO₂（酸素投与下で高値のまま平坦→遅れて低下）", color=F.GRAY, fs=10, ha="left")
    capno_in(ax, x0, x0+6.6, 0.7, 1.4, cycles=5, color=F.BLUE, lw=2.0, p0=0.88, ptop=1.0)
    ax.plot([x0+6.6, x1], [0.7, 0.7], color=F.RED, lw=2.4, zorder=4)
    ax.add_patch(Rectangle((x0+6.6, 0.4), x1-x0-6.6, 2.0, fc="#F4C7C3", alpha=0.35, ec="none", zorder=1))
    txt(ax, (x0+6.6+x1)/2, 2.65, "無呼吸", color=F.RED, fs=11, bold=True)
    ax.plot([x0+6.6, x0+6.6], [0.4, 3.9], color=F.GOLD, lw=1.3, ls=":", zorder=2)
    F.arrow(ax, x0+6.6, 3.6, x0+3.5, 3.6, color=F.GOLD, lw=1.8, ms=14)
    txt(ax, x0+5.0, 3.85, "早期警告（数十秒〜分の先行）", color=F.GOLD, fs=10, ha="center")
    txt(ax, x0+3.3, 0.15, "マイクロストリーム鼻カニュラ", color=F.BLUE, fs=10)
    F.save(fig, "f0803")

def f0804():
    fig, ax = canvas(11.4, 5.8, W=12, H=6.6)
    # left: 2 alveoli
    ax.add_patch(Circle((1.5, 4.3), 0.85, fc=F.GREENL, ec=F.GREEN, lw=1.6, zorder=2))
    txt(ax, 1.5, 4.3, "正常\n換気○・灌流○", color=F.INK, fs=9.5)
    ax.add_patch(Circle((3.5, 4.3), 0.85, fc="#F2F2F2", ec=F.RED, lw=1.6, zorder=2))
    txt(ax, 3.5, 4.3, "塞栓側\n換気○・灌流✕", color=F.RED, fs=9.5)
    txt(ax, 3.5, 3.15, "肺胞死腔", color=F.RED, fs=10.5, bold=True)
    # middle: 2 waveforms overlaid + staircase
    capno_in(ax, 5.3, 8.3, 2.6, 2.4, cycles=1, color=F.GOLD, lw=2.2, p0=0.9, ptop=1.0)
    capno_in(ax, 5.3, 8.3, 2.6, 1.5, cycles=1, color=F.RED, lw=2.2, p0=0.82, ptop=1.0)
    txt(ax, 6.8, 5.4, "正常 vs 急性PE（プラトー低下）", color=F.RED, fs=10, bold=True)
    txt(ax, 9.0, 5.15, "PaCO₂", color=F.BLUE, fs=10)
    txt(ax, 9.0, 4.65, "PACO₂", color=F.GREEN, fs=10)
    txt(ax, 9.0, 4.15, "PetCO₂", color=F.GOLD, fs=10)
    # right: volumetric with Vd/Vt hatch
    x0v, x1v, basev = 8.6, 11.3, 0.7
    xv = np.linspace(x0v, x1v, 200)
    yv = np.interp(xv, [x0v, x0v+0.3, x0v+0.8, x1v], [basev, basev, basev+1.6, basev+1.9])
    ax.plot(xv, yv, color=F.INK, lw=2.0, zorder=3)
    ax.fill_between(xv[(xv>x0v+0.3)&(xv<x0v+0.9)], basev, yv[(xv>x0v+0.3)&(xv<x0v+0.9)],
                     color=F.RED, alpha=0.25, hatch="//", zorder=2)
    txt(ax, 9.9, 0.35, "容量カプノグラフィで Vd/Vt↑", color=F.BLUE, fs=9.5)
    rbox(ax, 0.3, 0.3, 4.6, 1.35, F.GOLDL, F.GOLD, round_=0.1,
         txt_lines=[("肺胞死腔分画 = (PaCO₂−EtCO₂)/PaCO₂", F.GOLD), ("正常 <0.15（低確率+D-dimer陰性で除外補助）", F.INK)], fs=10)
    F.save(fig, "f0804")

def f0805():
    fig, ax = canvas(11.4, 5.8, W=12, H=6.6)
    # left: pneumoperitoneum -> absorption arrow
    ax.add_patch(FancyBboxPatch((0.4, 0.6), 2.6, 2.0, boxstyle="round,pad=0.02,rounding_size=0.15",
                                 fc=F.GOLDL, ec=F.GOLD, lw=1.4, zorder=2))
    txt(ax, 1.7, 1.6, "腹腔\n(CO₂気腹)", color=F.INK, fs=10)
    F.arrow(ax, 1.7, 2.65, 1.7, 3.6, color=F.GOLD, lw=2.4, ms=16)
    txt(ax, 1.7, 3.85, "CO₂吸収", color=F.GOLD, fs=11, bold=True)
    # middle: trend
    x0, x1, base = 3.6, 8.6, 0.8
    xr = np.linspace(x0, x1, 300)
    yr = base + 1.6*(1-np.exp(-(xr-x0)/1.8))
    ax.plot(xr, yr, color=F.INK, lw=2.2, zorder=3)
    yr_v = base + 1.3*(1-np.exp(-(xr-x0)/2.2))
    ax.plot(xr, yr_v, color=F.GRAY, lw=1.6, ls="--", zorder=2)
    xr2 = np.linspace(x0+3.2, x1, 100)
    yr2 = yr[-len(xr2):] + np.linspace(0, 0.9, len(xr2))
    ax.plot(xr2, yr2, color=F.RED, lw=2.2, zorder=4)
    txt(ax, x0+3.4, 3.5, "皮下気腫＝二段上昇", color=F.RED, fs=10, bold=True, ha="left")
    txt(ax, x0+0.1, 3.1, "気腹開始でEtCO₂緩やかに上昇", color=F.GOLD, fs=9.5, ha="left")
    txt(ax, x0+0.1, 0.45, "破線＝分時換気量↑で相殺", color=F.GRAY, fs=9)
    # right: a-ET bars before/after
    ax.add_patch(Rectangle((9.4, 0.8), 0.8, 1.4, fc=F.BLUEL, ec=F.BLUE, lw=1.2, zorder=2))
    txt(ax, 9.8, 0.55, "気腹前\n約5–6", color=F.BLUE, fs=9)
    ax.add_patch(Rectangle((10.5, 0.8), 0.8, 2.0, fc=F.ORANGEL, ec=F.ORANGE, lw=1.2, zorder=2))
    txt(ax, 10.9, 0.55, "気腹中\n約7–8", color=F.ORANGE, fs=9)
    txt(ax, 10.35, 3.15, "a–ET較差", color=F.GRAY, fs=10, ha="center")
    txt(ax, 6.0, 5.9, "長時間・頭低位で PetCO₂ が PaCO₂ を過小評価", color=F.GRAY, fs=11, bold=True)
    F.save(fig, "f0805")

def f0807():
    fig, ax = canvas(11.4, 5.8, W=12, H=6.6)
    ax.add_patch(Circle((1.8, 4.1), 1.1, fc=F.BLUEL, ec=F.BLUE, lw=1.4, zorder=2))
    txt(ax, 1.8, 4.1, "成人", color=F.INK, fs=12)
    ax.add_patch(Circle((4.1, 4.3), 0.55, fc=F.ORANGEL, ec=F.ORANGE, lw=1.4, zorder=2))
    txt(ax, 4.1, 4.3, "乳児", color=F.INK, fs=10)
    txt(ax, 3.0, 2.6, "器具死腔の相対的増大", color=F.ORANGE, fs=10.5, bold=True)
    # middle: dilution comparison waveforms
    capno_in(ax, 5.4, 8.6, 4.4, 1.3, cycles=2, color=F.GRAY, lw=1.8, p0=0.55, ptop=0.62,
             t1=0.10, t2=0.10, t3=0.20, down=0.10)
    txt(ax, 7.0, 6.0, "高流量サイドストリーム＝希釈", color=F.GRAY, fs=9.5)
    capno_in(ax, 5.4, 8.6, 1.9, 1.3, cycles=2, color=F.TEAL, lw=2.2, p0=0.92, ptop=1.0)
    txt(ax, 7.0, 3.45, "マイクロストリーム（約50 mL/min）", color=F.TEAL, fs=9.5, bold=True)
    rbox(ax, 8.9, 3.5, 2.9, 1.9, F.GOLDL, F.GOLD, txt_lines=[("マイクロストリーム", F.GOLD), ("＝低流量・低死腔", F.GOLD), ("→小児に適", F.GOLD)], fs=10, align="center")
    rbox(ax, 8.9, 0.4, 2.9, 1.5, "white", F.RED, txt_lines=[("カフなしチューブの", F.RED), ("リークで過小評価", F.RED)], fs=10, align="center")
    txt(ax, 3.0, 0.5, "正常 EtCO₂ の目安 35–45 mmHg（新生児はやや低め）", color=F.GRAY, fs=9.5)
    F.save(fig, "f0807")


ALL_FIGS = [
    "f00_hero",
    "f0101", "f0102", "f0103",
    "f0201", "f0202", "f0203", "f0205",
    "f0301", "f0302", "f0303", "f0304", "f0305",
    "f0401", "f0402", "f0403", "f0404", "f0405",
    "f0501", "f0502", "f0503", "f0504", "f0505",
    "f0601", "f0602", "f0603", "f0604", "f0605", "f0606", "f0607",
    "f0701", "f0702", "f0703", "f0704", "f0706",
    "f0801", "f0802", "f0803", "f0804", "f0805", "f0807",
]

if __name__ == "__main__":
    g = globals()
    for name in ALL_FIGS:
        g[name]()
        print("saved", name)
    print(f"done: {len(ALL_FIGS)} figures -> {F.OUTDIR}")

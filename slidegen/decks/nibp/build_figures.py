#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIBP講義スライド用の図版13点を生成する。
- design-spec.md の図版スタイル(色トークン・線種)に準拠
- 各 content/chNN.json の figure.spec を基に作図(数値・注記は仕様どおりで創作しない)
- 出力: assets/fig_<id>.png (id の "." は "_" に置換), 背景透過
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import (FancyBboxPatch, Rectangle, Circle, Polygon,
                                 FancyArrowPatch, Arc, Ellipse)
import matplotlib.lines

plt.rcParams["font.family"] = "Hiragino Sans"
plt.rcParams["axes.unicode_minus"] = False

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets")
os.makedirs(OUT, exist_ok=True)

# ---- カラートークン (design-spec.md 準拠) ----
INK = "#262626"
GOLD = "#BF9000"
TEAL = "#00A8AA"
MUTED = "#808080"
NAV_OFF = "#D9D9D9"
BLUE = "#2E6FBF"
BLUE_FILL = "#DAE3F3"
BLUE_FILL_DARK = "#BDD7EE"
ORANGE = "#E8853B"
ORANGE_FILL = "#FCE4D6"
GREEN = "#70AD47"
RED = "#C00000"
CALLOUT_FILL = "#F2E2B3"


def new_fig(w=7.4, h=4.6):
    fig, ax = plt.subplots(figsize=(w, h), dpi=200)
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    return fig, ax


def save(fig, fid):
    name = "fig_" + fid.replace(".", "_") + ".png"
    path = os.path.join(OUT, name)
    fig.savefig(path, transparent=True, bbox_inches="tight", pad_inches=0.10)
    plt.close(fig)
    print("saved", path)


def hline(ax, x0, x1, y, color=INK, lw=2.0, ls="-", zorder=2):
    ax.plot([x0, x1], [y, y], color=color, lw=lw, ls=ls, zorder=zorder,
            solid_capstyle="round")


def vline(ax, x, y0, y1, color=MUTED, lw=1.2, ls="--", zorder=2):
    ax.plot([x, x], [y0, y1], color=color, lw=lw, ls=ls, zorder=zorder)


def dot(ax, x, y, color=RED, r=0.045):
    ax.add_patch(Circle((x, y), r, color=color, zorder=6, ec="none"))


def arrow(ax, xy0, xy1, color=INK, lw=1.8, style="-|>", mut=10, zorder=3):
    a = FancyArrowPatch(xy0, xy1, arrowstyle=style, mutation_scale=mut,
                         color=color, lw=lw, zorder=zorder)
    ax.add_patch(a)


def label(ax, x, y, text, color=INK, size=11, ha="center", va="center",
          weight="normal", zorder=7):
    ax.text(x, y, text, color=color, fontsize=size, ha=ha, va=va,
            weight=weight, zorder=zorder)


def bell(x, peak_x, width, height, base=0.0):
    """釣鐘状カーブ(ガウシアン)"""
    return base + height * np.exp(-((x - peak_x) ** 2) / (2 * width ** 2))


def box(ax, x, y, w, h, fc, ec, lw=1.6, rounding=0.06, zorder=3):
    b = FancyBboxPatch((x, y), w, h,
                        boxstyle=f"round,pad=0,rounding_size={rounding}",
                        fc=fc, ec=ec, lw=lw, zorder=zorder)
    ax.add_patch(b)
    return b


def diamond(ax, cx, cy, w, h, fc, ec, lw=1.6, zorder=3):
    pts = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)]
    p = Polygon(pts, closed=True, fc=fc, ec=ec, lw=lw, zorder=zorder)
    ax.add_patch(p)
    return p


# ======================================================================
# 1.1 血圧測定前史とRiva-Rocci ― カフ触診法の誕生
# ======================================================================
def fig_1_1():
    fig, ax = new_fig(7.6, 4.8)
    # 上腕(縦帯)
    arm_x, arm_w = 1.1, 0.9
    arm_y0, arm_y1 = 0.7, 4.3
    box(ax, arm_x, arm_y0, arm_w, arm_y1 - arm_y0, fc="#F5F5F5", ec=INK, lw=1.6, rounding=0.14)
    label(ax, arm_x + arm_w / 2, arm_y0 + 0.55, "上腕動脈", color=INK, size=11)

    # カフ(横帯)
    cuff_y0, cuff_y1 = 2.55, 3.15
    box(ax, arm_x - 0.35, cuff_y0, arm_w + 0.7, cuff_y1 - cuff_y0,
        fc=BLUE_FILL, ec=BLUE, lw=1.8, rounding=0.08)
    label(ax, arm_x + arm_w / 2, cuff_y1 + 0.32, "カフ(圧迫帯)", color=BLUE, size=11, weight="bold")

    # 手首・触診
    wrist_y = arm_y0 + 0.12
    ax.add_patch(Ellipse((arm_x + arm_w / 2 - 0.18, wrist_y), 0.22, 0.14, fc="#EFEFEF", ec=INK, lw=1.2, zorder=5))
    ax.add_patch(Ellipse((arm_x + arm_w / 2 + 0.18, wrist_y), 0.22, 0.14, fc="#EFEFEF", ec=INK, lw=1.2, zorder=5))
    arrow(ax, (arm_x + arm_w + 0.55, wrist_y + 0.35), (arm_x + arm_w + 0.02, wrist_y + 0.06), color=INK, lw=1.4, mut=9)
    label(ax, arm_x + arm_w + 1.05, wrist_y + 0.55, "橈骨動脈を触知", color=INK, size=10.5, ha="left")

    # チューブ
    ax.plot([arm_x - 0.35, 3.55], [cuff_y0 + 0.30, cuff_y0 + 0.30], color=INK, lw=2.0)

    # 水銀柱マノメータ
    man_x, man_w = 3.55, 0.85
    man_y0, man_y1 = 0.9, 4.1
    box(ax, man_x, man_y0, man_w, man_y1 - man_y0, fc="#F5F5F5", ec=BLUE, lw=1.8, rounding=0.05)
    # 水銀柱(青塗り、下から一定高さ)
    hg_top = man_y0 + (man_y1 - man_y0) * 0.55
    box(ax, man_x + 0.10, man_y0 + 0.08, man_w - 0.20, hg_top - (man_y0 + 0.08),
        fc=BLUE_FILL_DARK, ec="none", rounding=0.02, zorder=2)
    # 目盛
    for i in range(6):
        yy = man_y0 + 0.25 + i * (man_y1 - man_y0 - 0.5) / 5
        ax.plot([man_x + man_w, man_x + man_w + 0.10], [yy, yy], color=INK, lw=1.0)
    label(ax, man_x + man_w / 2, man_y1 + 0.28, "水銀柱マノメータ", color=BLUE, size=11, weight="bold")

    # 減圧の矢印(高→低)
    arrow(ax, (man_x - 0.55, man_y1 - 0.2), (man_x - 0.55, man_y0 + 0.3), color=MUTED, lw=2.0, mut=11)
    label(ax, man_x - 0.85, (man_y0 + man_y1) / 2, "減圧\n高→低", color=MUTED, size=10, ha="center")

    # SBP再出現ライン(赤破線)
    sbp_y = hg_top - 0.05
    hline(ax, arm_x - 0.55, man_x + man_w + 0.25, sbp_y, color=RED, lw=1.6, ls="--", zorder=4)
    dot(ax, man_x + man_w / 2, sbp_y, color=RED)
    label(ax, man_x + man_w + 0.95, sbp_y, "拍動再出現\n=SBP", color=RED, size=11, ha="left", weight="bold")

    # DBP注記
    label(ax, arm_x + arm_w / 2, 0.32, "DBPは得られない", color=MUTED, size=10)

    save(fig, "1.1")


# ======================================================================
# 1.2 Korotkoffの聴診法 ― 血管音5相の確立
# ======================================================================
def fig_1_2():
    fig, ax = new_fig(8.6, 4.9)
    x0, x1 = 0.6, 8.0
    y_top, y_bot = 3.9, 1.2

    # カフ圧主線(右下がり)
    ax.plot([x0, x1], [y_top, y_bot], color=INK, lw=2.4, solid_capstyle="round", zorder=3)
    label(ax, x0 + 0.1, y_top + 0.62, "カフ圧(段階減圧)", color=INK, size=11, ha="left", weight="bold")

    def cuff_y(x):
        return y_top + (y_bot - y_top) * (x - x0) / (x1 - x0)

    # 5相の音バー配置(x位置, バー高さの配列)
    phases = [
        ("I", 2.05, [0.28, 0.30]),
        ("II", 3.15, [0.20, 0.10, 0.22]),
        ("III", 4.35, [0.42, 0.40, 0.44]),
        ("IV", 5.55, [0.16, 0.14]),
    ]
    bar_w = 0.10
    for name, cx, heights in phases:
        n = len(heights)
        spread = 0.5
        xs = np.linspace(cx - spread / 2, cx + spread / 2, n)
        for xx, hh in zip(xs, heights):
            base = cuff_y(xx)
            ax.add_patch(Rectangle((xx - bar_w / 2, base - hh / 2), bar_w, hh,
                                    fc=BLUE, ec="none", zorder=4))

    # V相(消失) - x=6.4付近で音なし
    v_x = 6.4

    # I相 = SBP (赤破線+ドット)
    sbp_x = 2.05 - 0.40
    vline(ax, sbp_x, cuff_y(sbp_x) - 0.55, cuff_y(sbp_x) + 0.55, color=RED, lw=1.6, ls="--")
    dot(ax, sbp_x, cuff_y(sbp_x), color=RED)
    label(ax, sbp_x - 0.10, cuff_y(sbp_x) + 0.35, "I相=SBP", color=RED, size=11, ha="right", weight="bold")

    # II相 聴診間隙帯(グレー破線帯)
    gap_x0, gap_x1 = 2.75, 3.55
    ax.axvspan(gap_x0, gap_x1, color=MUTED, alpha=0.12, zorder=1)
    vline(ax, gap_x0, 0.9, cuff_y(gap_x0) + 0.5, color=MUTED, lw=1.0, ls=":")
    vline(ax, gap_x1, 0.9, cuff_y(gap_x1) + 0.5, color=MUTED, lw=1.0, ls=":")
    label(ax, (gap_x0 + gap_x1) / 2, 0.75, "聴診間隙(gap)が\n生じうる", color=MUTED, size=9.5, ha="center")

    # IV相 muffling(橙)
    label(ax, 5.55, cuff_y(5.55) + 0.55, "IV相=減弱\n(muffling)", color=ORANGE, size=10.5, ha="center", weight="bold")

    # V相 = DBP (赤破線+ドット), 音バー消失点
    vline(ax, v_x, cuff_y(v_x) - 0.55, cuff_y(v_x) + 0.55, color=RED, lw=1.6, ls="--")
    dot(ax, v_x, cuff_y(v_x), color=RED)
    label(ax, v_x + 0.35, cuff_y(v_x) + 0.75, "V相=消失\n=DBP", color=RED, size=11, ha="center", weight="bold")

    # III相ラベル
    label(ax, 4.35, cuff_y(4.35) + 0.62, "III相", color=BLUE, size=10.5, ha="center")

    # 時間軸
    arrow(ax, (x0, 0.5), (x1 + 0.3, 0.5), color=INK, lw=1.6, mut=10)
    label(ax, x1 + 0.15, 0.30, "時間", color=INK, size=11, ha="center")

    save(fig, "1.2")


# ======================================================================
# 2.1 カフ内圧振動(オシレーション)の発生機序
# ======================================================================
def fig_2_1():
    fig, axes = plt.subplots(2, 1, figsize=(8.2, 5.2), dpi=200,
                              gridspec_kw={"height_ratios": [1.35, 1]})
    for ax in axes:
        ax.axis("off")
    x0, x1 = 0.5, 7.5
    xs = np.linspace(x0, x1, 700)

    ax1 = axes[0]
    ax1.set_xlim(0, 8.2)
    ax1.set_ylim(0, 4.4)
    main_y0, main_y1 = 3.4, 1.1
    main = main_y0 + (main_y1 - main_y0) * (xs - x0) / (x1 - x0)
    env = bell(xs, (x0 + x1) / 2, 1.35, 0.42)
    osc = env * np.sin((xs - x0) * 16)
    ax1.plot(xs, main + osc, color=INK, lw=1.6, zorder=3)
    ax1.plot(xs, main, color=MUTED, lw=1.2, ls="--", zorder=2)
    label(ax1, x0 + 0.05, main_y0 + 0.55, "カフ圧(段階減圧)", color=MUTED, size=10.5, ha="left")
    label(ax1, (x0 + x1) / 2, main_y0 + 0.9, "拍動由来の微小振動", color=INK, size=11.5, ha="center", weight="bold")
    arrow(ax1, (x0, 0.55), (x1 + 0.4, 0.55), color=INK, lw=1.4, mut=9)
    label(ax1, x1 + 0.25, 0.30, "時間 / 減圧", color=INK, size=10, ha="center")

    ax2 = axes[1]
    ax2.set_xlim(0, 8.2)
    ax2.set_ylim(0, 2.2)
    envelope = bell(xs, (x0 + x1) / 2, 1.35, 1.55, base=0.15)
    ax2.plot(xs, envelope, color=BLUE, lw=2.2, zorder=3)
    ax2.fill_between(xs, 0.05, envelope, color=BLUE_FILL, zorder=2)
    peak_x = (x0 + x1) / 2
    peak_y = bell(np.array([peak_x]), peak_x, 1.35, 1.55, base=0.15)[0]
    vline(ax2, peak_x, 0.05, peak_y + 0.15, color=RED, lw=1.6, ls="--")
    dot(ax2, peak_x, peak_y, color=RED)
    label(ax2, peak_x, peak_y + 0.35, "ピーク(最大振幅)", color=RED, size=11, ha="center", weight="bold")
    label(ax2, x0 + 0.1, 1.95, "振幅エンベロープ", color=BLUE, size=11.5, ha="left", weight="bold")

    fig.subplots_adjust(hspace=0.08, left=0.02, right=0.98, top=0.98, bottom=0.02)
    save(fig, "2.1")


# ======================================================================
# 2.2 最大振動点=MAP、SBP/DBPはアルゴリズム推定
# ======================================================================
def fig_2_2():
    fig, ax = new_fig(7.6, 4.8)
    x0, x1 = 0.6, 7.0
    ax.set_xlim(0, 7.6)
    ax.set_ylim(0, 4.6)
    xs = np.linspace(x0, x1, 700)
    peak_x = (x0 + x1) / 2
    width = 1.15
    height = 3.1
    base = 0.5
    env = bell(xs, peak_x, width, height, base=base)
    ax.plot(xs, env, color=INK, lw=2.2, zorder=3)
    ax.fill_between(xs, base, env, color=BLUE_FILL, zorder=2)

    peak_y = base + height
    vline(ax, peak_x, base - 0.05, peak_y + 0.25, color=RED, lw=1.8, ls="--")
    dot(ax, peak_x, peak_y, color=RED)
    label(ax, peak_x, peak_y + 0.45, "最大振幅=MAP", color=RED, size=12.5, ha="center", weight="bold")

    # SBP: 立ち上がり側(高圧=左) で最大の約55%
    target_sbp = base + height * 0.55
    # solve gaussian for x < peak_x
    dx = width * np.sqrt(-2 * np.log(0.55))
    sbp_x = peak_x - dx
    vline(ax, sbp_x, base - 0.05, target_sbp, color=RED, lw=1.4, ls="--")
    hline(ax, sbp_x, peak_x, target_sbp, color=MUTED, lw=1.0, ls=":")
    dot(ax, sbp_x, target_sbp, color=RED, r=0.05)
    label(ax, sbp_x - 0.05, base - 0.60, "SBP≒最大の55%\n(立ち上がり)", color=RED, size=10, ha="center")

    # DBP: 下降側(低圧=右) で最大の約85%
    target_dbp = base + height * 0.85
    dx2 = width * np.sqrt(-2 * np.log(0.85))
    dbp_x = peak_x + dx2
    vline(ax, dbp_x, base - 0.05, target_dbp, color=RED, lw=1.4, ls="--")
    hline(ax, peak_x, dbp_x, target_dbp, color=MUTED, lw=1.0, ls=":")
    dot(ax, dbp_x, target_dbp, color=RED, r=0.05)
    label(ax, dbp_x + 0.05, base - 0.60, "DBP≒最大の85%\n(下降)", color=RED, size=10, ha="center")

    # 軸ラベル
    arrow(ax, (x0 - 0.2, base - 0.15), (x1 + 0.3, base - 0.15), color=INK, lw=1.4, mut=9)
    label(ax, (x0 + x1) / 2, base - 1.05, "カフ圧(mmHg)　高 → 低", color=INK, size=11)

    # 注記(比率はメーカ依存)
    ax.text(7.5, 4.4, "比率はメーカ依存・非公開\n(0.55/0.85は例示)", color=RED, fontsize=8.6,
            ha="right", va="top", style="italic")

    save(fig, "2.2")


# ======================================================================
# 2.3 聴診法との対応と相違(上下2段比較)
# ======================================================================
def fig_2_3():
    fig, axes = plt.subplots(2, 1, figsize=(8.0, 5.4), dpi=200)
    x0, x1 = 0.7, 7.3

    # --- 上段: 聴診 ---
    ax1 = axes[0]
    ax1.set_xlim(0, 8.0)
    ax1.set_ylim(0, 2.7)
    ax1.axis("off")
    y_top, y_bot = 1.85, 0.55

    def cuff_y(x):
        return y_top + (y_bot - y_top) * (x - x0) / (x1 - x0)

    ax1.plot([x0, x1], [y_top, y_bot], color=MUTED, lw=1.6, ls="--", zorder=2)
    bar_positions = np.linspace(1.6, 5.6, 9)
    bar_heights = [0.18, 0.16, 0.10, 0.24, 0.30, 0.28, 0.14, 0.12, 0.08]
    for xx, hh in zip(bar_positions, bar_heights):
        base = cuff_y(xx)
        ax1.add_patch(Rectangle((xx - 0.06, base - hh / 2), 0.12, hh, fc=BLUE, ec="none", zorder=3))
    sbp_x1, dbp_x1 = 1.35, 5.95
    dot(ax1, sbp_x1, cuff_y(sbp_x1), color=RED)
    dot(ax1, dbp_x1, cuff_y(dbp_x1), color=RED)
    label(ax1, sbp_x1, cuff_y(sbp_x1) + 0.30, "I相=SBP", color=RED, size=11, weight="bold")
    label(ax1, dbp_x1, cuff_y(dbp_x1) + 0.30, "V相=DBP", color=RED, size=11, weight="bold")
    label(ax1, x0, y_top + 0.62, "上段: 聴診(Korotkoff音)", color=INK, size=12, ha="left", weight="bold")

    # --- 下段: オシロメトリック ---
    ax2 = axes[1]
    ax2.set_xlim(0, 8.0)
    ax2.set_ylim(0, 2.2)
    ax2.axis("off")
    xs = np.linspace(x0, x1, 700)
    peak_x = 3.65
    width = 1.05
    height = 1.35
    base_h = 0.35
    env = bell(xs, peak_x, width, height, base=base_h)
    ax2.plot(xs, env, color=INK, lw=2.0, zorder=3)
    ax2.fill_between(xs, base_h, env, color=BLUE_FILL, zorder=2)
    peak_y = base_h + height
    dot(ax2, peak_x, peak_y, color=RED)
    label(ax2, peak_x, peak_y + 0.35, "最大=MAP", color=RED, size=11, weight="bold")

    dx = width * np.sqrt(-2 * np.log(0.55))
    sbp_x2 = peak_x - dx
    dbp_x2 = peak_x + width * np.sqrt(-2 * np.log(0.85))
    dot(ax2, sbp_x2, bell(np.array([sbp_x2]), peak_x, width, height, base=base_h)[0], color=RED, r=0.045)
    dot(ax2, dbp_x2, bell(np.array([dbp_x2]), peak_x, width, height, base=base_h)[0], color=RED, r=0.045)
    label(ax2, sbp_x2, base_h - 0.28, "SBP点", color=RED, size=10)
    label(ax2, dbp_x2, base_h - 0.28, "DBP点", color=RED, size=10)
    label(ax2, x0, 2.05, "下段: オシロメトリック", color=INK, size=12, ha="left", weight="bold")

    fig.text(0.5, 0.965, "共通軸: カフ圧(mmHg) 高 → 低　―　MAPは聴診のSBPとDBPの間に位置する",
              ha="center", fontsize=11, color=INK)

    fig.subplots_adjust(left=0.03, right=0.97, top=0.90, bottom=0.03, hspace=0.35)

    # 共通ガイド縦線(SBP・MAP・DBPの圧位置): 上段の点から下段の点へ図全体(fig座標)で結ぶ
    for x_top, x_bot in [(sbp_x1, sbp_x2), (dbp_x1, dbp_x2)]:
        top_disp = ax1.transData.transform((x_top, cuff_y(x_top) - 0.1))
        bot_disp = ax2.transData.transform((x_bot, base_h + height + 0.1))
        top_fig = fig.transFigure.inverted().transform(top_disp)
        bot_fig = fig.transFigure.inverted().transform(bot_disp)
        line = matplotlib.lines.Line2D([top_fig[0], bot_fig[0]], [top_fig[1], bot_fig[1]],
                                        transform=fig.transFigure, color=MUTED, lw=1.0, ls=":", zorder=1)
        fig.add_artist(line)

    save(fig, "2.3")


# ======================================================================
# 3.1 カフ幅・ブラダー規格と上腕周囲径
# ======================================================================
def fig_3_1():
    fig, ax = new_fig(7.6, 4.8)
    arm_x, arm_w = 1.3, 1.5
    arm_y0, arm_y1 = 0.7, 4.1
    box(ax, arm_x, arm_y0, arm_w, arm_y1 - arm_y0, fc="#F5F5F5", ec=INK, lw=1.6, rounding=0.16)

    cuff_y0, cuff_y1 = 1.9, 2.9
    box(ax, arm_x - 0.15, cuff_y0, arm_w + 0.30, cuff_y1 - cuff_y0, fc=BLUE_FILL, ec=BLUE, lw=1.8, rounding=0.08)

    # 幅 W の寸法線
    dim_x = arm_x + arm_w + 0.65
    ax.plot([dim_x, dim_x], [cuff_y0, cuff_y1], color=GOLD, lw=1.4)
    ax.plot([dim_x - 0.08, dim_x + 0.08], [cuff_y0, cuff_y0], color=GOLD, lw=1.4)
    ax.plot([dim_x - 0.08, dim_x + 0.08], [cuff_y1, cuff_y1], color=GOLD, lw=1.4)
    label(ax, dim_x + 0.35, (cuff_y0 + cuff_y1) / 2, "カフ幅 W\n≒ 上腕周囲径の\n40%", color=GOLD, size=10.5, ha="left", weight="bold")

    label(ax, arm_x + arm_w / 2, arm_y1 + 0.25, "上腕(周囲径 C)", color=INK, size=11, weight="bold")

    # 断面(円周)小図: ブラダーが周囲の80-100%を包む
    cx, cy, r = 5.8, 3.1, 0.72
    circ = Circle((cx, cy), r, fc="none", ec=INK, lw=1.6, zorder=3)
    ax.add_patch(circ)
    # bladder arc 80-100% (~300 of 360 deg)
    arc = Arc((cx, cy), 2 * r, 2 * r, theta1=-140, theta2=120, color=BLUE, lw=6)
    ax.add_patch(arc)
    label(ax, cx, cy + r + 0.32, "断面(周から見た図)", color=INK, size=10, ha="center")
    label(ax, cx + 0.40, cy - r - 0.30, "ブラダー長 =\n周囲の80〜100%", color=BLUE, size=10, ha="center", weight="bold")

    # 幅:長 ≒ 1:2
    ax.text(4.15, 0.55, "幅:長 ≒ 1:2", color=INK, fontsize=12, ha="center",
            bbox=dict(boxstyle="round,pad=0.35", fc=CALLOUT_FILL, ec=GOLD, lw=1.4))

    # 非適合例(赤×)
    small_x, small_w = 1.55, 0.7
    small_y0, small_y1 = 3.35, 3.7
    box(ax, small_x, small_y0, small_w, small_y1 - small_y0, fc="#FCE9E9", ec=RED, lw=1.4, rounding=0.05)
    ax.plot([small_x + 0.10, small_x + small_w - 0.10], [small_y0 + 0.05, small_y1 - 0.05], color=RED, lw=1.6, zorder=5)
    ax.plot([small_x + 0.10, small_x + small_w - 0.10], [small_y1 - 0.05, small_y0 + 0.05], color=RED, lw=1.6, zorder=5)
    label(ax, small_x + small_w / 2, small_y1 + 0.22, "幅が狭いカフ(不適合)", color=RED, size=9, ha="center")

    save(fig, "3.1")


# ======================================================================
# 3.2 カフと心臓の高さ・静水圧補正
# ======================================================================
def fig_3_2():
    fig, ax = new_fig(8.8, 4.8)
    ax.set_xlim(0, 8.8)
    ax.set_ylim(0, 4.8)

    # 座位の人物(簡略シルエット: 頭・胴体・脚)
    torso_x, torso_y = 1.0, 1.1
    ax.add_patch(Circle((torso_x + 0.35, 3.9), 0.32, fc="#EDEDED", ec=INK, lw=1.5, zorder=3))
    ax.add_patch(FancyBboxPatch((torso_x, 2.2), 0.7, 1.5, boxstyle="round,pad=0,rounding_size=0.15",
                                 fc="#EDEDED", ec=INK, lw=1.5, zorder=3))
    ax.add_patch(FancyBboxPatch((torso_x + 0.02, 0.6), 0.28, 1.7, boxstyle="round,pad=0,rounding_size=0.10",
                                 fc="#EDEDED", ec=INK, lw=1.4, zorder=3))
    ax.add_patch(FancyBboxPatch((torso_x + 0.42, 0.6), 0.28, 1.7, boxstyle="round,pad=0,rounding_size=0.10",
                                 fc="#EDEDED", ec=INK, lw=1.4, zorder=3))
    # 腕(基準腕、心臓レベル)
    ax.add_patch(FancyBboxPatch((torso_x - 0.55, 2.55), 0.55, 0.24, boxstyle="round,pad=0,rounding_size=0.10",
                                 fc="#EDEDED", ec=INK, lw=1.4, zorder=3))

    heart_y = 2.7
    hline(ax, 0.3, 8.6, heart_y, color=GOLD, lw=2.0, ls="--")
    label(ax, 0.35, heart_y + 0.24, "基準=右房(腋窩中線)", color=GOLD, size=11, ha="left", weight="bold")

    # ケースA: カフが基準より10cm低い → 過大 +7.5
    ax_x = 3.0
    a_y = heart_y - 1.05
    box(ax, ax_x, a_y - 0.16, 0.85, 0.32, fc=BLUE_FILL, ec=BLUE, lw=1.6, rounding=0.06)
    label(ax, ax_x + 0.425, a_y, "カフA", color=BLUE, size=9.5)
    vline(ax, ax_x + 0.425, a_y, heart_y, color=RED, lw=1.2, ls=":")
    label(ax, ax_x + 1.05, a_y, "10cm低い → +7.5 mmHg\n(過大評価)", color=RED, size=10, ha="left", va="center", weight="bold")

    # ケースB: カフが基準より10cm高い → 過小 -7.5
    b_y = heart_y + 1.05
    box(ax, ax_x, b_y - 0.16, 0.85, 0.32, fc=BLUE_FILL, ec=BLUE, lw=1.6, rounding=0.06)
    label(ax, ax_x + 0.425, b_y, "カフB", color=BLUE, size=9.5)
    vline(ax, ax_x + 0.425, heart_y, b_y, color=BLUE, lw=1.2, ls=":")
    label(ax, ax_x + 1.05, b_y, "10cm高い → −7.5 mmHg\n(過小評価)", color=BLUE, size=10, ha="left", va="center", weight="bold")

    # 換算式・スケール(右側の独立した列に配置し、ケースA/Bの注記と重ならないようにする)
    sx = 7.55
    ax.text(sx, 4.15, "ΔP ≒ 0.75 mmHg/cm", color=INK, fontsize=11, ha="center", weight="bold",
            bbox=dict(boxstyle="round,pad=0.35", fc=CALLOUT_FILL, ec=GOLD, lw=1.3))
    label(ax, sx, 3.60, "±10cm\n↔ ±7.5 mmHg", color=INK, size=9.8, ha="center")
    label(ax, sx, 3.05, "±20cm\n↔ ±15 mmHg", color=INK, size=9.8, ha="center")

    label(ax, torso_x + 0.35, 0.3, "カフが低い→過大評価／高い→過小評価", color=MUTED, size=9.5, ha="center")

    save(fig, "3.2")


# ======================================================================
# 4.2 中枢〜末梢の部位差(末梢増幅)
# ======================================================================
def fig_4_2():
    fig, ax = new_fig(7.8, 4.8)
    ax.set_xlim(0, 7.8)
    ax.set_ylim(0.5, 5.3)
    t = np.linspace(0, 1, 600)

    def aortic(t):
        # なだらか・丸いピーク SBP~120 DBP~80
        base = 80 + 40 * np.exp(-((t - 0.16) ** 2) / (2 * 0.10 ** 2))
        base += 6 * np.exp(-((t - 0.55) ** 2) / (2 * 0.14 ** 2))
        return base

    def radial(t):
        # 立ち上がり急・ピーク尖り高い SBP~140 DBP~75、ノッチ後に反射波隆起
        peak = 75 + 65 * np.exp(-((t - 0.13) ** 2) / (2 * 0.045 ** 2))
        notch = -8 * np.exp(-((t - 0.30) ** 2) / (2 * 0.02 ** 2))
        reflect = 14 * np.exp(-((t - 0.42) ** 2) / (2 * 0.09 ** 2))
        tail = 75 + 5 * np.exp(-((t - 0.75) ** 2) / (2 * 0.2 ** 2))
        return peak + notch + reflect + (tail - 75)

    x = 0.6 + t * 6.4
    y_ao = aortic(t)
    y_ra = radial(t)
    # scale mmHg(70-145) to plot y (1.0-4.6)
    def scl(v):
        return 1.0 + (v - 70) * (4.6 - 1.0) / (145 - 70)

    ax.plot(x, scl(y_ao), color="#1F3864", lw=2.6, zorder=4, label="大動脈(近位)")
    ax.plot(x, scl(y_ra), color=BLUE, lw=2.2, zorder=3, label="橈骨(末梢)")

    map_v = 93
    hline(ax, 0.5, 7.3, scl(map_v), color=RED, lw=1.4, ls=":", zorder=2)
    label(ax, 7.15, scl(map_v) + 0.14, "MAP ほぼ一定 (約93)", color=RED, size=10, ha="right", weight="bold")

    label(ax, 1.5, scl(y_ao.max()) + 0.35, "大動脈(近位)\nSBP約120・DBP約80", color="#1F3864", size=10, ha="center", weight="bold")
    label(ax, 1.15, scl(y_ra.max()) + 0.28, "橈骨(末梢)\nSBP約140・DBP約75", color=BLUE, size=10, ha="left", weight="bold")

    # 脈圧拡大の両矢印
    arrow(ax, (6.55, scl(80)), (6.55, scl(120)), color="#1F3864", lw=1.3, style="<->", mut=8)
    arrow(ax, (6.85, scl(75)), (6.85, scl(140)), color=BLUE, lw=1.3, style="<->", mut=8)
    label(ax, 6.7, scl(148), "脈圧拡大", color=INK, size=10, ha="center")

    arrow(ax, (0.5, 0.75), (7.5, 0.75), color=INK, lw=1.4, mut=9)
    label(ax, 7.3, 0.55, "時間→", color=INK, size=10.5)

    save(fig, "4.2")


# ======================================================================
# 4.4 NIBP対A-lineの一致度(Bland-Altman)
# ======================================================================
def fig_4_4():
    fig, ax = new_fig(7.6, 5.0)
    ax.set_xlim(0, 7.6)
    ax.set_ylim(0, 5.0)

    plot_x0, plot_x1 = 1.0, 7.0
    plot_y0, plot_y1 = 0.7, 4.5
    mid_y = (plot_y0 + plot_y1) / 2

    # 軸
    ax.plot([plot_x0, plot_x1], [plot_y0, plot_y0], color=INK, lw=1.4)
    ax.plot([plot_x0, plot_x0], [plot_y0, plot_y1], color=INK, lw=1.4)
    label(ax, (plot_x0 + plot_x1) / 2, plot_y0 - 0.35, "平均 (NIBP + A-line)/2 [mmHg]", color=INK, size=10.5)
    ax.text(plot_x0 - 0.35, (plot_y0 + plot_y1) / 2, "差 = NIBP − A-line [mmHg]",
            color=INK, fontsize=10.5, rotation=90, ha="center", va="center")

    rng = np.random.default_rng(7)
    n = 90
    xs = rng.uniform(plot_x0 + 0.3, plot_x1 - 0.3, n)
    bias_y = mid_y + 0.12
    ys = rng.normal(bias_y, 0.42, n)
    ax.scatter(xs, ys, s=14, color=BLUE, alpha=0.55, zorder=3, edgecolors="none")

    # bias線
    hline(ax, plot_x0, plot_x1, bias_y, color="#1F3864", lw=2.0, zorder=4)
    label(ax, plot_x1 + 0.05, bias_y, "平均差(bias)\n(例 +1 mmHg)", color="#1F3864", size=9.5, ha="left", weight="bold")

    # 一致限界(±1.96SD)
    loa_hi, loa_lo = bias_y + 0.42 * 1.96, bias_y - 0.42 * 1.96
    hline(ax, plot_x0, plot_x1, loa_hi, color=MUTED, lw=1.4, ls="--")
    hline(ax, plot_x0, plot_x1, loa_lo, color=MUTED, lw=1.4, ls="--")
    label(ax, plot_x1 + 0.05, loa_hi, "一致限界\n= bias±1.96SD", color=MUTED, size=9.5, ha="left")

    # AAMI/ISO ±5mmHg 基準線(赤)
    aami_hi = mid_y + 0.30
    aami_lo = mid_y - 0.30
    hline(ax, plot_x0, plot_x1, aami_hi, color=RED, lw=1.6, ls="-")
    hline(ax, plot_x0, plot_x1, aami_lo, color=RED, lw=1.6, ls="-")
    label(ax, plot_x0 + 0.1, aami_hi + 0.15, "AAMI/ISO 基準 ±5 mmHg", color=RED, size=9.5, ha="left", weight="bold")

    # 注記ボックス
    ax.text(plot_x1 - 0.05, plot_y1 - 0.05, "平均差 ≦ 5, SD ≦ 8 mmHg", color=INK, fontsize=10.5,
            ha="right", va="top", bbox=dict(boxstyle="round,pad=0.4", fc=CALLOUT_FILL, ec=GOLD, lw=1.4))

    save(fig, "4.4")


# ======================================================================
# 5.4 術中低血圧の許容と臓器保護
# ======================================================================
def fig_5_4():
    fig, ax = new_fig(7.6, 4.8)
    ax.set_xlim(0, 7.6)
    ax.set_ylim(0, 4.8)

    plot_x0, plot_x1 = 1.0, 7.0  # 高(左=plot_x0はMAP高) → 低(右)
    plot_y0, plot_y1 = 0.7, 4.2

    ax.plot([plot_x0, plot_x1], [plot_y0, plot_y0], color=INK, lw=1.4)
    ax.plot([plot_x0, plot_x0], [plot_y0, plot_y1], color=INK, lw=1.4)
    label(ax, (plot_x0 + plot_x1) / 2, plot_y0 - 0.35, "MAP (mmHg)　高(左) → 低(右)", color=INK, size=11)
    ax.text(plot_x0 - 0.35, (plot_y0 + plot_y1) / 2, "AKI・MINS 相対リスク",
            color=INK, fontsize=11, rotation=90, ha="center", va="center")

    # MAP軸: plot_x0=100mmHg, plot_x1=40mmHg (右にいくほど低い)
    def map_to_x(m):
        return plot_x0 + (100 - m) / (100 - 40) * (plot_x1 - plot_x0)

    xs = np.linspace(plot_x0, plot_x1, 500)
    maps = 100 - (xs - plot_x0) / (plot_x1 - plot_x0) * 60
    # リスク曲線: 65未満で立ち上がり、55以下でさらに急峻(負値を渡さないようclip)
    below65 = np.clip(65 - maps, 0, None)
    below55 = np.clip(55 - maps, 0, None)
    risk = 0.15 + (below65 / 10) ** 1.6 * 0.55 + (below55 / 8) ** 1.8 * 0.9
    ys = plot_y0 + risk * 1.0 + 0.05
    ax.fill_between(xs, plot_y0, ys, where=(maps < 65), color=ORANGE_FILL, zorder=2)
    ax.plot(xs, ys, color=ORANGE, lw=2.4, zorder=3)

    for mval in (65, 55):
        xv = map_to_x(mval)
        vline(ax, xv, plot_y0, plot_y1, color=MUTED, lw=1.3, ls="--")
        label(ax, xv, plot_y1 + 0.18, f"MAP {mval}", color=INK, size=10.5, weight="bold")

    arrow(ax, (map_to_x(60), plot_y0 + 1.4), (map_to_x(45), plot_y0 + 2.6), color=RED, lw=1.6, mut=10)
    label(ax, map_to_x(50), plot_y0 + 2.9, "深さ×持続時間で増悪", color=RED, size=10.5, ha="center", weight="bold")

    ax.text((plot_x0 + plot_x1) / 2, plot_y1 + 0.55, "※関連の模式(定量予測ではない)", color=MUTED,
            fontsize=9, ha="center", style="italic")

    save(fig, "5.4")


# ======================================================================
# 6.3 不整脈・心房細動での信頼性低下(2パネル比較)
# ======================================================================
def fig_6_3():
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 4.6), dpi=200)
    x0, x1 = 0.6, 4.2

    # --- 左: 洞調律 ---
    ax1 = axes[0]
    ax1.set_xlim(0, 4.8)
    ax1.set_ylim(0, 4.2)
    ax1.axis("off")
    xs = np.linspace(x0, x1, 500)
    peak_x = (x0 + x1) / 2
    env = bell(xs, peak_x, 0.75, 2.4, base=0.4)
    ax1.plot(xs, env, color=INK, lw=2.2, zorder=3)
    ax1.fill_between(xs, 0.4, env, color=BLUE_FILL, zorder=2)
    peak_y = 0.4 + 2.4
    vline(ax1, peak_x, 0.35, peak_y + 0.2, color=RED, lw=1.5, ls="--")
    dot(ax1, peak_x, peak_y, color=RED)
    label(ax1, peak_x, peak_y + 0.42, "最大振幅点=MAP", color=RED, size=11, weight="bold")
    label(ax1, x0, 3.95, "洞調律：滑らかな釣鐘状", color=INK, size=12, ha="left", weight="bold")
    label(ax1, (x0 + x1) / 2, 0.10, "カフ圧(mmHg) 高→低", color=INK, size=10)

    # --- 右: 心房細動 ---
    ax2 = axes[1]
    ax2.set_xlim(0, 4.8)
    ax2.set_ylim(0, 4.2)
    ax2.axis("off")
    rng = np.random.default_rng(3)
    xs2 = np.linspace(x0, x1, 12)
    heights = np.array([0.6, 1.3, 0.8, 2.1, 1.1, 2.4, 1.5, 1.9, 0.9, 1.6, 0.7, 1.0])
    smooth_x = np.linspace(x0, x1, 400)
    heights_interp = np.interp(smooth_x, xs2, heights)
    noise = 0.12 * np.sin(smooth_x * 22)
    y2 = 0.4 + heights_interp + noise
    ax2.plot(smooth_x, y2, color=INK, lw=2.0, zorder=3)
    ax2.fill_between(smooth_x, 0.4, y2, color=BLUE_FILL, zorder=2)
    # 複数の山を強調する赤引き出し
    peak_idx = np.argmax(heights)
    px = xs2[peak_idx]
    py = 0.4 + heights[peak_idx]
    ax2.annotate("最大点が定まらない\n→ MAP推定不安定", xy=(px, py), xytext=(x1 + 0.15, 3.3),
                 fontsize=10.5, color=RED, weight="bold", ha="left",
                 arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.5))
    dot(ax2, px, py, color=RED)
    # second local max
    idx2 = 5
    dot(ax2, xs2[idx2], 0.4 + heights[idx2], color=RED, r=0.05)
    label(ax2, x0, 3.95, "心房細動：不規則に乱れる", color=INK, size=12, ha="left", weight="bold")
    label(ax2, (x0 + x1) / 2, 0.10, "カフ圧(mmHg) 高→低", color=INK, size=10)

    fig.subplots_adjust(left=0.03, right=0.97, top=0.95, bottom=0.05, wspace=0.15)
    save(fig, "6.3")


# ======================================================================
# 7.1 値が怪しいときの対応アルゴリズム(フローチャート)
# ======================================================================
def fig_7_1():
    fig, ax = new_fig(9.4, 8.5)
    ax.set_xlim(0, 9.4)
    ax.set_ylim(1.5, 10.0)

    cx = 3.0
    w_proc, h_proc = 4.6, 0.75
    w_dia, h_dia = 4.8, 1.1
    side_x0, side_w = 5.9, 3.0  # 側方ボックス(右)の左端・幅: 常にダイヤ右頂点(cx+w_dia/2=5.4)より右

    def proc(y, text, fc=BLUE_FILL, ec=BLUE, size=10.8, h=h_proc):
        box(ax, cx - w_proc / 2, y - h / 2, w_proc, h, fc=fc, ec=ec, lw=1.6, rounding=0.09)
        label(ax, cx, y, text, color=INK, size=size, weight="bold")
        return h

    def dia(y, text):
        diamond(ax, cx, y, w_dia, h_dia, fc="#FFFFFF", ec=INK, lw=1.6)
        label(ax, cx, y, text, color=INK, size=10.8, weight="bold")

    def side_box(y, text, fc, ec, tcolor, h=1.15):
        box(ax, side_x0, y - h / 2, side_w, h, fc=fc, ec=ec, lw=1.6, rounding=0.09)
        label(ax, side_x0 + side_w / 2, y, text, color=tcolor, size=10, weight="bold")

    # 行1: 開始
    y1 = 9.55
    proc(y1, "NIBP値が臨床像と乖離", fc="#F0F0F0", ec=INK)

    # 行2: 判定1
    y2 = 8.10
    arrow(ax, (cx, y1 - h_proc / 2), (cx, y2 + h_dia / 2 + 0.06), color=INK, lw=1.6)
    dia(y2, "脈が触れ、波形は保たれるか？")

    # 「いいえ」→ 右へ赤ボックス(真の異常)
    side_box(y2, "真の血行動態異常\n→ 蘇生・原因検索\n(7.2へ)", "#FCE9E9", RED, RED, h=1.2)
    arrow(ax, (cx + w_dia / 2, y2), (side_x0, y2), color=INK, lw=1.5)
    label(ax, side_x0 - 0.40, y2 + 0.30, "いいえ", color=INK, size=10.5)

    # 行3: artifact点検
    y3 = 6.55
    h3 = 1.05
    arrow(ax, (cx, y2 - h_dia / 2), (cx, y3 + h3 / 2 + 0.06), color=INK, lw=1.6)
    label(ax, cx + 0.32, (y2 - h_dia / 2 + y3 + h3 / 2) / 2, "はい", color=INK, size=10.5, ha="left")
    proc(y3, "artifactを疑い機器を点検：\nカフ幅≒上腕周囲の40%\n・位置(心臓の高さ)・巻きの緩み", size=10.0, h=h3)

    # 行4: 再測定
    y4 = 5.30
    arrow(ax, (cx, y3 - h3 / 2), (cx, y4 + h_proc / 2 + 0.06), color=INK, lw=1.6)
    proc(y4, "静止して再測定(体動/シバリング回避)")

    # 行5: 判定2
    y5 = 3.85
    arrow(ax, (cx, y4 - h_proc / 2), (cx, y5 + h_dia / 2 + 0.06), color=INK, lw=1.6)
    dia(y5, "値は臨床像と整合するか？")

    # 「はい」→ 右へ緑ボックス(モニタ継続)
    side_box(y5, "そのまま\nモニタ継続", "#EAF3E4", GREEN, GREEN, h=0.9)
    arrow(ax, (cx + w_dia / 2, y5), (side_x0, y5), color=INK, lw=1.5)
    label(ax, cx + w_dia / 2 + (side_x0 - (cx + w_dia / 2)) / 2, y5 + 0.28, "はい", color=INK, size=10.5)

    # 行6: 触診/A-line照合
    y6 = 2.35
    arrow(ax, (cx, y5 - h_dia / 2), (cx, y6 + h_proc / 2 + 0.06), color=INK, lw=1.6)
    label(ax, cx + 0.32, (y5 - h_dia / 2 + y6 + h_proc / 2) / 2, "いいえ", color=INK, size=10.5, ha="left")
    proc(y6, "触診法で概算 / A-lineで照合・切替", fc=ORANGE_FILL, ec=ORANGE)

    save(fig, "7.1")


# ======================================================================
# 8.4 体外循環・拍動欠如でのNIBP破綻
# ======================================================================
def fig_8_4():
    fig, ax = new_fig(9.6, 5.0)
    ax.set_xlim(0, 9.6)
    ax.set_ylim(0, 5.0)

    # --- 左パネル: 通常の拍動 ---
    lx0, lx1 = 0.5, 3.5
    t = np.linspace(0, 1, 400)
    wave = 90 + 30 * np.exp(-((t % 0.25 - 0.05) ** 2) / (2 * 0.02 ** 2))
    xs = lx0 + t * (lx1 - lx0)
    ys_scaled = 3.6 + (wave - 90) / 40 * 0.9
    ax.plot(xs, ys_scaled, color="#1F3864", lw=1.8, zorder=3)
    label(ax, (lx0 + lx1) / 2, 4.65, "通常の拍動", color=INK, size=12.5, ha="center", weight="bold")
    label(ax, lx0, 4.35, "動脈圧", color="#1F3864", size=9.5, ha="left")

    peak_x1 = (lx0 + lx1) / 2
    env1_xs = np.linspace(lx0, lx1, 300)
    env1 = bell(env1_xs, peak_x1, 0.55, 1.3, base=0.5)
    ax.plot(env1_xs, env1, color=BLUE, lw=2.0, zorder=3)
    ax.fill_between(env1_xs, 0.5, env1, color=BLUE_FILL, zorder=2)
    peak_y1 = 0.5 + 1.3
    vline(ax, peak_x1, 0.45, peak_y1 + 0.15, color=RED, lw=1.4, ls="--")
    dot(ax, peak_x1, peak_y1, color=RED)
    label(ax, peak_x1, peak_y1 + 0.32, "最大振幅=MAP", color=RED, size=10, weight="bold")
    ax.text((lx0 + lx1) / 2, 0.15, "オシロ測定 成立", color=GREEN, fontsize=11.5, ha="center", weight="bold")

    # 区切り線
    ax.plot([4.0, 4.0], [0.1, 4.8], color=NAV_OFF, lw=1.2)

    # --- 中パネル: 連続流LVAD/CPB ---
    mx0, mx1 = 4.3, 7.1
    xs2 = mx0 + t * (mx1 - mx0)
    wave2 = 84 + 2.5 * np.sin(t * 40)
    ys2 = 3.6 + (wave2 - 84) / 40 * 0.9
    ax.plot(xs2, ys2, color="#1F3864", lw=1.8, zorder=3)
    label(ax, (mx0 + mx1) / 2, 4.65, "連続流LVAD / CPB(非拍動)", color=INK, size=12, ha="center", weight="bold")

    env2_xs = np.linspace(mx0, mx1, 300)
    env2 = 0.55 + 0.05 * np.sin(env2_xs * 30)
    ax.plot(env2_xs, env2, color=BLUE, lw=2.0, zorder=3)
    ax.fill_between(env2_xs, 0.45, env2, color=BLUE_FILL, zorder=2)
    ax.annotate("振幅が出ずNIBP不能", xy=((mx0 + mx1) / 2, 0.6), xytext=((mx0 + mx1) / 2, 1.5),
                fontsize=10.3, color=RED, weight="bold", ha="center",
                arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.5))
    dot(ax, (mx0 + mx1) / 2, 0.58, color=RED)
    ax.text((mx0 + mx1) / 2, 0.15, "オシロ測定 破綻", color=RED, fontsize=11.5, ha="center", weight="bold")

    ax.plot([7.5, 7.5], [0.1, 4.8], color=NAV_OFF, lw=1.2)

    # --- 右パネル: ドプラ法 ---
    rx0, rx1 = 7.8, 9.4
    label(ax, (rx0 + rx1) / 2, 4.65, "ドプラ法", color=INK, size=12.5, ha="center", weight="bold")
    arm_x, arm_w = rx0 + 0.35, 0.55
    box(ax, arm_x, 1.3, arm_w, 2.6, fc="#F5F5F5", ec=INK, lw=1.4, rounding=0.10)
    cuff_y0c = 3.2
    box(ax, arm_x - 0.12, cuff_y0c, arm_w + 0.24, 0.45, fc=BLUE_FILL, ec=BLUE, lw=1.4, rounding=0.06)
    label(ax, arm_x + arm_w / 2, cuff_y0c + 0.95, "上腕カフ", color=BLUE, size=9)
    # probe (triangle)
    probe_y = 1.55
    tri = Polygon([(arm_x + arm_w / 2 - 0.1, probe_y), (arm_x + arm_w / 2 + 0.1, probe_y), (arm_x + arm_w / 2, probe_y - 0.2)],
                  closed=True, fc=INK, ec="none", zorder=4)
    ax.add_patch(tri)
    label(ax, arm_x + arm_w / 2 + 0.55, probe_y - 0.05, "橈骨動脈\nドプラ", color=INK, size=8.7, ha="left")
    arrow(ax, (arm_x - 0.35, cuff_y0c + 0.2), (arm_x - 0.35, 1.5), color=MUTED, lw=1.5, mut=8)
    label(ax, arm_x - 0.6, cuff_y0c - 0.3, "減圧", color=MUTED, size=8.5, ha="center")
    ax.text((rx0 + rx1) / 2, 0.55, "opening pressure\n ≒ MAP", color=GOLD, fontsize=9.6, ha="center", weight="bold")

    save(fig, "8.4")


ALL = {
    "1.1": fig_1_1, "1.2": fig_1_2,
    "2.1": fig_2_1, "2.2": fig_2_2, "2.3": fig_2_3,
    "3.1": fig_3_1, "3.2": fig_3_2,
    "4.2": fig_4_2, "4.4": fig_4_4,
    "5.4": fig_5_4,
    "6.3": fig_6_3,
    "7.1": fig_7_1,
    "8.4": fig_8_4,
}

if __name__ == "__main__":
    for fid, fn in ALL.items():
        fn()
    print(f"done: {len(ALL)} figures -> {OUT}")

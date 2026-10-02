# -*- coding: utf-8 -*-
import numpy as np
from matplotlib.patches import FancyBboxPatch, Arc, Circle, Polygon, Rectangle, Wedge
import figlib as F
from fighelp import *

# ------------------------------------------------------------------ local helpers --
def _pulse_wave(n=1400, cycles=4, kind="pulse"):
    """Small non-ECG schematic waveform for SpO2 pleth / A-line rows in f0605.
    kind='pulse': periodic asymmetric pulsatile wave (systolic upstroke + decay).
    kind='flat' : near-zero line with tiny noise (no effective pulse)."""
    X = np.linspace(0, cycles, n)
    if kind == "flat":
        rng = np.random.default_rng(11)
        Y = 0.03 * rng.standard_normal(n)
        Y = np.convolve(Y, np.ones(9) / 9, mode="same")
        return X, Y
    Y = np.zeros_like(X)
    for b in range(cycles):
        xr = X - b
        m = (xr >= 0) & (xr < 1)
        # fast upstroke + slower decay (dicrotic-ish), built from a damped-sine shape
        t, y = F.mono_damped_sine(n=int(m.sum()) if m.sum() > 0 else 2, dur=1.0)
        if m.sum() > 0:
            Y[m] = np.interp(np.linspace(0, 1, m.sum()), t, y)
    return X, 0.95 * Y


# ================================================================== CH 5 ==========
def f0501():
    """5.1 適応＝脈のある不安定な頻拍：2分岐の決定木。"""
    fig, ax = canvas(9.6, 5.6, W=12, H=6.6)
    cx = 8.2  # shared center for the right (unstable) column

    # root node
    F.box(ax, 2.85, 5.85, 6.1, 0.55, F.WHITE, ec=F.GOLD,
          txt="脈のある頻拍（心拍数が速い・脈は触れる）", tc=F.GOLD, fs=12, lw=2.2)
    F.arrow(ax, 4.7, 5.85, 2.1, 5.35, color=F.GRAY, lw=2.0)
    F.arrow(ax, 7.3, 5.85, cx, 5.35, color=F.RED, lw=2.4)

    # left branch: stable -> pharmacotherapy
    F.box(ax, 0.35, 4.85, 3.5, 0.5, F.LGRAY, ec=F.GRAY,
          txt="安定（不安定サインなし）", tc=F.INK, fs=11.5, lw=1.4)
    F.arrow(ax, 2.1, 4.85, 2.1, 4.22, color=F.GRAY, lw=2.0)
    # 2nd line wrapped into 2 (same wording) and box heightened (top edge kept fixed
    # where the arrow above ends): the single long line was much wider than the box
    F.box(ax, 0.15, 3.22, 3.9, 1.00, F.WHITE, ec=F.GRAY,
          txt="まず薬物療法\n（レート/リズム調整・\nSVTはバルサルバ/アデノシン）",
          tc=F.GRAY, fs=9.5, lw=1.2)

    # right branch: unstable heading
    F.box(ax, cx - 3.225, 4.85, 6.45, 0.5, F.WHITE, ec=F.RED,
          txt="不安定サイン（下記いずれか）", tc=F.RED, fs=12, lw=1.8)

    # 4 unstable-sign boxes (shared x grid reused by rhythm row below)
    sw, gap = 1.5, 0.15
    row_x0 = cx - (4 * sw + 3 * gap) / 2
    xs = [row_x0 + i * (sw + gap) for i in range(4)]
    signs = ["意識障害", "虚血性胸痛", "低血圧・\nショック", "急性心不全\n（肺うっ血）"]
    for x, s in zip(xs, signs):
        F.box(ax, x, 3.65, sw, 0.9, "#FBE5E3", ec=F.RED, txt=s, tc=F.RED, fs=10.5, lw=1.3)

    # gold arrow -> sync cardioversion
    F.arrow(ax, cx, 3.65, cx, 3.18, color=F.GOLD, lw=3.2, ms=20)
    F.box(ax, cx - 2.15, 2.65, 4.3, 0.55, F.GOLDL, ec=F.GOLD,
          txt="同期下カルディオバージョン", tc=F.GOLD, fs=13, lw=2.0)
    F.arrow(ax, cx, 2.65, cx, 2.13, color=F.GOLD, lw=3.0, ms=18)

    # rhythm row (same x grid as signs)
    # "SVT" re-wrapped to 3 lines and fs trimmed 10->9 for the whole row (AF / 心房粗動
    # had margin to spare): the "(narrow・regular)" / "(脈あり・wide" lines were wider
    # than the shared sw=1.5 box
    rhythms = [("AF", F.BLUEL, F.BLUE),
               ("心房粗動", F.GREENL, F.GREEN),
               ("SVT\n(narrow\n・regular)", F.GREENL, F.GREEN),
               ("単形性VT\n(脈あり・wide\nregular)", F.ORANGEL, F.ORANGE)]
    for x, (lab, fc, ec) in zip(xs, rhythms):
        F.box(ax, x, 1.12, sw, 0.9, fc, ec=ec, txt=lab, tc=F.INK, fs=9, lw=1.4)

    # bottom-right red note (dotted-connected from the rhythm row)
    F.box(ax, 6.1, 0.12, 5.6, 0.82, "#FBE5E3", ec=F.RED,
          txt="不安定な多形性VT（不規則）＝同期不能\n→VF扱いで非同期放電（第4章へ）",
          tc=F.RED, fs=10.5, lw=1.6)
    ax.plot([xs[-1] + sw / 2, 9.0], [1.12, 0.94], color=F.RED, lw=1.2, ls=":", zorder=2)
    F.save(fig, "f0501")


def f0502():
    """5.2 SYNCモードの動作：R波同期・T波回避・タイムラグ。"""
    fig, ax = canvas(9.6, 5.0, W=12, H=6.2)
    ymid, yscale = 4.0, 0.95
    rx = ecg_in(ax, 0.6, 8.6, ymid, yscale, beats=4, narrow=True, twave=0.28,
                mark_r=True, mark_t=True)

    # highlight one T-wave (vulnerable period) with a translucent red band, beat idx 2
    tpos_raw = F.t_peak_positions(4)[2]
    tx = 0.6 + tpos_raw / 4 * (8.6 - 0.6)
    ax.add_patch(Rectangle((tx - 0.16, ymid - yscale * 0.55), 0.32, yscale * 1.1,
                            fc=F.RED, alpha=0.16, ec="none", zorder=2))

    # shock delivered right after the beat-3 R wave
    shock_x = rx[2] + 0.18
    shock_bolt(ax, shock_x, ymid + yscale * 0.55, size=0.42, color=F.RED)
    ax.plot([shock_x, shock_x], [ymid + yscale * 0.15, ymid - 1.55], color=F.RED,
            lw=1.2, ls=":", zorder=2)

    # labels
    txt(ax, rx[1], ymid + yscale * 1.55, "同期マーカー\n（R波センシング）", color=F.GOLD, fs=11, bold=True)
    txt(ax, tx, ymid + yscale * 1.55, "脆弱期＝\nT波頂上", color=F.RED, fs=11, bold=True)
    txt(ax, 4.6, ymid + yscale + 1.0, "SYNC", color=F.GOLD, fs=14, bold=True)

    # timeline / button-hold bar below the ECG
    bar_y = ymid - 1.85
    bar_x0 = (rx[1] + rx[2]) / 2 + 0.35
    ax.plot([bar_x0, shock_x], [bar_y, bar_y], color=F.GRAY, lw=9, alpha=0.35, zorder=1,
            solid_capstyle="butt")
    ax.plot([0.6, 8.6], [bar_y, bar_y], color=F.LGRAY, lw=1.0, zorder=0)
    txt(ax, bar_x0, bar_y + 0.42, "ボタン押下", color=F.GRAY, fs=10.5)
    txt(ax, shock_x, bar_y - 0.42, "R波を検出して放電", color=F.RED, fs=10.5, bold=True)
    txt(ax, (bar_x0 + shock_x) / 2, bar_y, "タイムラグ\n（すぐには出ない）", color=F.GRAY, fs=9.5)

    # right note box
    F.box(ax, 9.0, 3.05, 2.85, 2.05, "#FBE5E3", ec=F.RED,
          txt="R波を判別できない波形\n（多形性VT/VF）\n＝同期不能\n→SYNC放電されない\n→非同期へ切替",
          tc=F.RED, fs=9.8, lw=1.5)
    F.save(fig, "f0502")


def f0503():
    """5.3 リズム別エネルギー（確定数値）：4行の一覧表。"""
    fig, ax = canvas(9.8, 5.2, W=11.6, H=6.2)
    x0, y_top, w = 0.5, 5.85, 10.6
    ncol_w = [3.0, 3.0, 4.6]
    xs = [x0, x0 + ncol_w[0], x0 + ncol_w[0] + ncol_w[1]]
    header_h = 0.80
    row_h = 0.72
    headers = ["リズム", "二相性・\n初回エネルギー", "メモ"]
    for xc, wc, lab in zip(xs, ncol_w, headers):
        ax.add_patch(Rectangle((xc, y_top - header_h), wc, header_h, fc=F.TEAL, ec=F.LGRAY, lw=1.0, zorder=2))
        txt(ax, xc + wc / 2, y_top - header_h / 2, lab, color=F.WHITE, fs=11.5, bold=True)

    rows = [
        ("AF（心房細動）", F.BLUEL, F.BLUE, "120–200 J", F.GOLD, "無効なら段階的に増量", F.INK),
        ("心房粗動 / SVT\n（narrow・regular）", F.GREENL, F.GREEN, "50–100 J", F.GOLD, "比較的低エネルギーで有効", F.INK),
        ("単形性VT\n（脈あり・wide・regular）", F.ORANGEL, F.ORANGE, "100 J", F.GOLD, "無効なら増量", F.INK),
        ("多形性VT\n（不安定・不規則）", "#FBE5E3", F.RED, "同期不能→非同期の\n高エネルギー（VF扱い）", F.RED, "第4章へ", F.GRAY),
    ]
    ry = y_top - header_h
    for rlab, rfc, rec, elab, ecol, nlab, ncol in rows:
        ry -= row_h
        ax.add_patch(Rectangle((xs[0], ry), ncol_w[0], row_h, fc=rfc, ec=rec, lw=1.3, zorder=2))
        txt(ax, xs[0] + ncol_w[0] / 2, ry + row_h / 2, rlab, color=rec, fs=11, bold=True)
        ax.add_patch(Rectangle((xs[1], ry), ncol_w[1], row_h, fc=F.WHITE, ec=F.LGRAY, lw=1.0, zorder=2))
        txt(ax, xs[1] + ncol_w[1] / 2, ry + row_h / 2, elab, color=ecol, fs=13.5, bold=True)
        ax.add_patch(Rectangle((xs[2], ry), ncol_w[2], row_h, fc=F.WHITE, ec=F.LGRAY, lw=1.0, zorder=2))
        txt(ax, xs[2] + ncol_w[2] / 2, ry + row_h / 2, nlab, color=ncol, fs=11)

    note_y = ry - 0.85
    F.box(ax, x0, note_y, 5.1, 0.65, F.WHITE, ec=F.GRAY,
          txt="無効なら1段ずつエネルギーを上げる\n（各リズム共通）", tc=F.GRAY, fs=10.2, lw=1.2)
    F.box(ax, x0 + 5.4, note_y, 5.2, 0.65, F.WHITE, ec=F.GRAY,
          txt="単相性は概ね上記の倍量が目安", tc=F.GRAY, fs=11, lw=1.2)
    txt(ax, x0 + w / 2, note_y - 0.35, "小児は 0.5–1 J/kg → 無効なら 2 J/kg（第8章 8.4）",
        color=F.GRAY, fs=10)
    F.save(fig, "f0503")


def f0504():
    """5.4 再武装の落とし穴：正しい手順(上段) vs SYNC入れ直し忘れ(下段)。"""
    fig, ax = canvas(10.2, 5.4, W=13, H=6.2)
    y_top, h = 4.55, 0.68
    # widths of steps 3/4/6 bumped slightly (1.4->1.5, 1.7->1.9): their labels were a
    # touch wider than the box (centers[] below is derived from these widths, so the
    # arrows/labels that reference it stay correctly aligned)
    steps = [
        ("①SYNC ON", F.GOLDL, F.GOLD, F.GOLD, 1.35),
        ("②充電", F.WHITE, F.GRAY, F.GRAY, 1.05),
        ("③放電・1回目\n（同期）", F.WHITE, F.GRAY, F.INK, 1.5),
        ("④再度SYNCを押す\n＝再武装", F.GOLDL, F.GOLD, F.GOLD, 2.0),
        ("⑤充電", F.WHITE, F.GRAY, F.GRAY, 1.05),
        ("⑥放電・2回目\n（同期）", F.WHITE, F.GRAY, F.INK, 1.5),
    ]
    x = 0.5
    centers = []
    lws = [1.4, 1.4, 1.4, 2.6, 1.4, 1.4]
    for (lab, fc, ec, tc_, w), lw in zip(steps, lws):
        F.box(ax, x, y_top, w, h, fc, ec=ec, txt=lab, tc=tc_, fs=9.4, lw=lw)
        centers.append(x + w / 2)
        x += w + 0.42
    for i in range(len(steps) - 1):
        x1 = centers[i] + steps[i][4] / 2 + 0.07
        x2 = centers[i + 1] - steps[i + 1][4] / 2 - 0.07
        col = F.RED if i == 2 else F.INK
        ms = 13 if i == 2 else 16
        F.arrow(ax, x1, y_top + h / 2, x2, y_top + h / 2, color=col, lw=2.0, ms=ms)
    txt(ax, (centers[2] + centers[3]) / 2, y_top + h + 0.3,
        "放電ごとにSYNC自動解除\n（多くの機種）", color=F.RED, fs=10, bold=True)

    # pitfall branch, dropping from step3
    F.arrow(ax, centers[2], y_top, centers[2] - 0.9, 3.05, color=F.RED, lw=2.2)
    py, ph = 2.35, 0.7
    F.box(ax, 1.5, py, 2.3, ph, "#FBE5E3", ec=F.RED, txt="SYNC入れ直し忘れ", tc=F.RED, fs=11, lw=1.6)
    F.arrow(ax, 3.8, py + ph / 2, 4.35, py + ph / 2, color=F.RED, lw=2.0)
    F.box(ax, 4.4, py, 2.5, ph, "#FBE5E3", ec=F.RED, txt="非同期のまま放電", tc=F.RED, fs=11, lw=1.6)
    F.arrow(ax, 6.9, py + ph / 2, 7.45, py + ph / 2, color=F.RED, lw=2.0)

    # mini ECG: shock lands on T wave (R on T)
    ex0, ex1, emid, eys = 7.5, 9.9, py + ph / 2, 0.5
    rxm = ecg_in(ax, ex0, ex1, emid, eys, beats=2, narrow=True, twave=0.28, mark_t=True, mark_r=False)
    tpos = F.t_peak_positions(2)[0]
    tx = ex0 + tpos / 2 * (ex1 - ex0)
    ax.add_patch(Rectangle((tx - 0.14, emid - eys * 0.5), 0.28, eys * 1.3, fc=F.RED, alpha=0.20, ec="none", zorder=2))
    shock_bolt(ax, tx, emid + eys * 1.15, size=0.28, color=F.RED)
    txt(ax, tx, emid + eys * 1.85, "T波に当たる\n（R on T）", color=F.RED, fs=10, bold=True)

    F.arrow(ax, 9.95, py + ph / 2, 10.5, py + ph / 2, color=F.RED, lw=2.0)
    F.box(ax, 10.55, py - 0.05, 2.0, ph + 0.1, "#FBE5E3", ec=F.RED, txt="VF/多形性VT\n誘発リスク", tc=F.RED, fs=10.5, lw=1.8)
    F.save(fig, "f0504")


def f0505():
    """5.5 待機的カルディオバージョンと抗凝固：フロー＋タイムライン。"""
    fig, ax = canvas(10.4, 5.8, W=13, H=6.8)
    F.box(ax, 3.6, 6.2, 5.8, 0.5, F.GOLDL, ec=F.GOLD,
          txt="待機的カルディオバージョン（症候性AF/粗動）", tc=F.GOLD, fs=11.2, lw=2.0)
    txt(ax, 6.5, 5.95, "発症からの時間", color=F.GRAY, fs=10.5)
    F.arrow(ax, 4.9, 6.2, 1.9, 5.35, color=F.GRAY, lw=2.0)
    F.arrow(ax, 8.3, 6.2, 9.8, 5.35, color=F.GRAY, lw=2.0)

    # left: <48h
    F.box(ax, 0.3, 4.35, 3.2, 1.0, F.GREENL, ec=F.GREEN,
          txt="発症 <48時間\n＝相対的に低リスク\n（抗凝固下で施行可）", tc=F.INK, fs=10.3, lw=1.6)

    # right heading
    F.box(ax, 6.9, 4.85, 5.8, 0.5, F.ORANGEL, ec=F.ORANGE,
          txt="48時間以上 or 発症時期不明", tc=F.ORANGE, fs=11.5, lw=1.6)

    # path A (left of the two)
    F.box(ax, 7.0, 3.70, 2.7, 1.0, F.ORANGEL, ec=F.ORANGE,
          txt="経路A：\n前3週間の\n治療的抗凝固", tc=F.INK, fs=9.6, lw=1.4)
    F.arrow(ax, 8.35, 3.70, 8.35, 3.4, color=F.INK, lw=1.8)
    F.box(ax, 7.55, 2.9, 1.6, 0.45, F.WHITE, ec=F.INK, txt="CV", tc=F.INK, fs=11, lw=1.4, bold=True)
    F.arrow(ax, 8.35, 2.9, 8.35, 2.45, color=F.INK, lw=1.8)
    F.box(ax, 7.0, 1.65, 2.7, 0.75, F.ORANGEL, ec=F.ORANGE,
          txt="後4週間の治療的抗凝固", tc=F.INK, fs=9.6, lw=1.4)

    # path B (right)
    F.box(ax, 9.9, 3.70, 2.8, 1.0, F.ORANGEL, ec=F.ORANGE,
          txt="経路B：\nTEEで左房/左心耳の\n血栓を除外", tc=F.INK, fs=9.2, lw=1.4)
    F.arrow(ax, 11.3, 3.70, 11.3, 3.4, color=F.INK, lw=1.8)
    F.box(ax, 10.5, 2.9, 1.6, 0.45, F.WHITE, ec=F.INK, txt="CV", tc=F.INK, fs=11, lw=1.4, bold=True)
    txt(ax, 11.3, 3.55, "血栓なし", color=F.GREEN, fs=9, bold=True)
    F.arrow(ax, 11.3, 2.9, 11.3, 2.45, color=F.INK, lw=1.8)
    F.box(ax, 9.95, 1.65, 2.7, 0.75, F.ORANGEL, ec=F.ORANGE,
          txt="後4週間の治療的抗凝固", tc=F.INK, fs=9.6, lw=1.4)

    # convergence red note
    F.box(ax, 6.9, 0.85, 5.8, 0.65, "#FBE5E3", ec=F.RED,
          txt="左房/左心耳血栓＝塞栓源。放電で洞調律に戻すと飛ぶ", tc=F.RED, fs=10.3, lw=1.6)
    ax.plot([8.35, 9.0], [2.9, 1.5], color=F.RED, lw=1.1, ls=":", zorder=1)
    ax.plot([11.3, 10.6], [2.9, 1.5], color=F.RED, lw=1.1, ls=":", zorder=1)

    # bottom-left timeline
    ax.plot([0.3, 5.2], [1.15, 1.15], color=F.INK, lw=1.4, zorder=2)
    for xt_, lab in [(0.3, "−3週"), (2.75, "CV(0)"), (5.2, "+4週")]:
        ax.plot([xt_, xt_], [1.05, 1.25], color=F.INK, lw=1.4)
        txt(ax, xt_, 0.85, lab, color=F.GOLD, fs=10.5, bold=True)
    ax.plot([0.3, 2.75], [1.45, 1.45], color=F.ORANGE, lw=5, alpha=0.6, zorder=1)
    ax.plot([2.75, 5.2], [1.45, 1.45], color=F.INK, lw=5, alpha=0.35, zorder=1)
    txt(ax, 1.5, 1.68, "経路A：前3週抗凝固", color=F.ORANGE, fs=9, bold=True)
    txt(ax, 4.0, 1.68, "CV後4週抗凝固（共通）", color=F.GRAY, fs=9)
    F.arrow(ax, 1.5, 0.45, 2.6, 0.45, color=F.GREEN, lw=2.2, ms=14)
    txt(ax, 2.0, 0.20, "経路B：TEEで前倒し（−3週の待機を省略）", color=F.GREEN, fs=9)

    F.box(ax, 5.7, 0.05, 7.0, 0.55, F.LGRAY, ec="none",
          txt="当日準備：絶飲食・同意・静脈路・モニタ・蘇生/気道準備・鎮静/麻酔（→5.6）",
          tc=F.GRAY, fs=8.2, lw=0, bold=False)
    F.save(fig, "f0505")


# ================================================================== CH 6 ==========
def f0601():
    """6.1 適応＝症候性徐脈（アトロピン無効・不適）。"""
    fig, ax = canvas(9.6, 5.4, W=11, H=6.4)
    F.box(ax, 3.0, 5.75, 5.0, 0.5, F.GOLDL, ec=F.GOLD, txt="症候性徐脈（不安定）", tc=F.GOLD, fs=13, lw=2.0)
    sw, gap = 1.5, 0.15
    row_x0 = 5.5 - (4 * sw + 3 * gap) / 2
    xs = [row_x0 + i * (sw + gap) for i in range(4)]
    for x, lab in zip(xs, ["低血圧", "意識障害", "虚血性胸痛", "急性心不全"]):
        F.box(ax, x, 5.0, sw, 0.45, F.WHITE, ec=F.GRAY, txt=lab, tc=F.INK, fs=10.5, lw=1.2)
    F.arrow(ax, 5.5, 5.0, 5.5, 4.55, color=F.INK, lw=2.2)
    F.box(ax, 3.6, 4.0, 3.8, 0.5, F.BLUEL, ec=F.BLUE, txt="第一選択＝アトロピン静注", tc=F.BLUE, fs=12, lw=1.8)

    F.arrow(ax, 4.2, 4.0, 1.9, 3.35, color=F.GRAY, lw=1.8)
    F.box(ax, 0.3, 2.85, 3.2, 0.5, F.LGRAY, ec=F.GRAY, txt="反応あり＝経過観察・原因検索", tc=F.INK, fs=10.5, lw=1.2)

    F.arrow(ax, 6.6, 4.0, 7.3, 3.5, color=F.RED, lw=2.6)
    txt(ax, 9.15, 3.85, "無効 or 不適\n（高度AVブロック等）", color=F.RED, fs=10.5, bold=True)
    F.box(ax, 6.4, 2.35, 4.2, 0.55, F.GOLDL, ec=F.GOLD, txt="経皮ペーシング（TCP）＝一時的な橋渡し", tc=F.GOLD, fs=10.0, lw=2.0)
    F.arrow(ax, 8.5, 2.35, 8.5, 1.75, color=F.INK, lw=2.2)
    F.box(ax, 6.4, 1.15, 4.2, 0.55, F.BLUEL, ec=F.BLUE,
          txt="経静脈ペーシング／恒久ペースメーカ（次の一手）", tc=F.BLUE, fs=8.7, lw=1.6)

    F.box(ax, 0.3, 0.25, 4.6, 0.7, "#FBE5E3", ec=F.RED,
          txt="心静止（asystole）＝一般に無効・ルーチン非推奨", tc=F.RED, fs=9.0, lw=1.6)
    F.save(fig, "f0601")


def f0602():
    """6.2 パッド配置とモード：前後配置＋デマンド vs 固定。"""
    fig, ax = canvas(10.4, 5.0, W=13, H=6.2)
    # ---- left: pad placement schematic ----
    txt(ax, 2.6, 5.85, "前後配置（推奨）", color=F.GOLD, fs=13, bold=True)
    ax.add_patch(FancyBboxPatch((1.1, 1.2), 3.0, 4.0, boxstyle="round,pad=0.02,rounding_size=0.4",
                                 fc="#F2F2F2", ec=F.GRAY, lw=1.3, zorder=1))
    # heart shadow
    ax.add_patch(Circle((2.5, 3.6), 0.55, fc="#F4C7C3", ec=F.RED, lw=1.0, alpha=0.7, zorder=2))
    txt(ax, 2.5, 3.6, "心臓", color=F.RED, fs=9)
    # front pad
    ax.add_patch(Rectangle((1.35, 3.15), 0.75, 0.9, fc=F.BLUEL, ec=F.BLUE, lw=1.6, zorder=3))
    txt(ax, 1.05, 4.25, "前パッド\n（左前胸部）", color=F.BLUE, fs=9.5, ha="right")
    # back pad
    ax.add_patch(Rectangle((3.05, 3.15), 0.75, 0.9, fc=F.BLUEL, ec=F.BLUE, lw=1.6, zorder=3))
    txt(ax, 4.25, 4.25, "後パッド\n（背部・左肩甲骨下）", color=F.BLUE, fs=9.5, ha="left")
    F.arrow(ax, 2.10, 3.6, 3.05, 3.6, color=F.RED, lw=1.6, ls="--", ms=10)
    txt(ax, 2.6, 1.55, "電流が心陰影を挟む", color=F.RED, fs=10, bold=True)

    # ---- right: demand vs fixed ----
    ax.plot([5.6, 12.7], [3.0, 3.0], color=F.LGRAY, lw=1.0, zorder=0)

    # demand strip (top): sinus beats with one pause filled by a paced spike+QRS
    dx0, dx1, dymid, dys, beats = 5.7, 12.6, 4.55, 0.55, 5
    X = np.linspace(0, beats, 1400)
    Y = np.zeros_like(X)
    pause_beat = 3
    for b in range(beats):
        if b == pause_beat:
            continue
        xr = X - b
        m = (xr >= 0) & (xr < 1)
        Y[m] += F.ecg_beat(xr[m], r0=0.5, twave=0.22, narrow=True)
    spike_x_local = pause_beat + 0.62
    xr2 = X - pause_beat
    m2 = (xr2 >= 0.5) & (xr2 < 1)
    Y[m2] += F.ecg_beat(xr2[m2] - 0.12, r0=0.5, twave=0.22, narrow=False) * 0.9
    xs_map = dx0 + X / beats * (dx1 - dx0)
    ax.plot(xs_map, dymid + Y * dys, color=F.INK, lw=2.0, zorder=4, solid_joinstyle="round")
    spike_x = dx0 + spike_x_local / beats * (dx1 - dx0)
    ax.plot([spike_x, spike_x], [dymid - dys * 0.3, dymid + dys * 1.3], color=F.TEAL, lw=1.8, zorder=5)
    ax.add_patch(Rectangle((dx0 + (pause_beat) / beats * (dx1 - dx0), dymid - dys * 1.1),
                            (0.55) / beats * (dx1 - dx0), dys * 2.4, fc=F.GREENL, alpha=0.4, ec="none", zorder=1))
    txt(ax, dx0 + (pause_beat + 0.3) / beats * (dx1 - dx0), dymid + dys * 1.9, "ポーズ→\nスパイク＋QRS", color=F.GREEN, fs=9.5, bold=True)
    txt(ax, dx0 + 0.3, dymid + dys * 1.9, "デマンド", color=F.GOLD, fs=12, bold=True)
    txt(ax, dx1 - 0.4, dymid - dys * 1.4, "必要時のみ駆動", color=F.GREEN, fs=10, bold=True)

    # fixed strip (bottom): regular native rhythm + fixed-interval spikes, one coincides
    fx0, fx1, fymid, fys = 5.7, 12.6, 1.55, 0.55
    beats_f = 5
    Xf = np.linspace(0, beats_f, 1400)
    Yf = np.zeros_like(Xf)
    for b in range(beats_f):
        xr = Xf - b
        m = (xr >= 0) & (xr < 1)
        Yf[m] += F.ecg_beat(xr[m], r0=0.5, twave=0.22, narrow=True)
    xsf_map = fx0 + Xf / beats_f * (fx1 - fx0)
    ax.plot(xsf_map, fymid + Yf * fys, color=F.INK, lw=2.0, zorder=4, solid_joinstyle="round")
    spikes_local = [0.15, 1.05, 1.95, 2.5, 3.75, 4.65]  # one (2.5) coincides with native R at 2.5
    for sxl in spikes_local:
        sx = fx0 + sxl / beats_f * (fx1 - fx0)
        collide = abs(sxl - 2.5) < 0.05
        col = F.RED if collide else F.TEAL
        ax.plot([sx, sx], [fymid - fys * 0.3, fymid + fys * 1.3], color=col, lw=1.8, zorder=5)
        if collide:
            ax.add_patch(Circle((sx, fymid + fys * 0.2), 0.22, fc="none", ec=F.RED, lw=1.8, zorder=6))
    coll_x = fx0 + 2.5 / beats_f * (fx1 - fx0)
    txt(ax, coll_x, fymid - fys * 1.5, "競合\n（自己QRS上）", color=F.RED, fs=9.5, bold=True)
    txt(ax, fx0 + 0.3, fymid + fys * 1.9, "固定（非同期）", color=F.GOLD, fs=12, bold=True)
    txt(ax, fx1 - 0.4, fymid - fys * 1.4, "非同期＝競合しうる", color=F.RED, fs=10, bold=True)

    txt(ax, 9.15, 0.35, "通常＝デマンド", color=F.GOLD, fs=11, bold=True)
    F.save(fig, "f0602")


def f0603():
    """6.3 レート設定：60–80/minの数直線＋ペーシングECG。"""
    fig, ax = canvas(9.6, 4.6, W=11, H=5.6)
    ax0, ax1, ay = 0.8, 10.2, 4.55
    ax.plot([ax0, ax1], [ay, ay], color=F.INK, lw=1.6, zorder=2)
    for v in range(30, 101, 10):
        xv = ax0 + (v - 30) / 70 * (ax1 - ax0)
        ax.plot([xv, xv], [ay - 0.08, ay + 0.08], color=F.INK, lw=1.2, zorder=2)
        txt(ax, xv, ay - 0.32, str(v), color=F.GRAY, fs=9.5)
    x60 = ax0 + (60 - 30) / 70 * (ax1 - ax0)
    x80 = ax0 + (80 - 30) / 70 * (ax1 - ax0)
    ax.add_patch(Rectangle((x60, ay - 0.05), x80 - x60, 0.10, fc=F.GOLD, alpha=0.85, zorder=3))
    txt(ax, (x60 + x80) / 2, ay + 0.55, "通常設定域", color=F.GOLD, fs=12.5, bold=True)
    txt(ax, (x60 + x80) / 2, ay + 0.22, "60–80/min", color=F.GOLD, fs=13, bold=True)

    x35 = ax0 + (35 - 30) / 70 * (ax1 - ax0)
    ax.add_patch(Circle((x35, ay), 0.09, fc=F.BLUE, ec="white", lw=1.0, zorder=4))
    txt(ax, x35, ay - 0.55, "自己35\n（例）", color=F.BLUE, fs=9.5)
    F.arrow(ax, x35 + 0.1, ay - 0.05, x60 - 0.1, ay - 0.05, color=F.BLUE, lw=1.8, ls="--")
    txt(ax, (x35 + x60) / 2, ay - 0.85, "自己心拍（補充調律）より上へ", color=F.BLUE, fs=10)

    ymid, yscale = 2.05, 0.85
    pacing_in(ax, 0.8, 10.2, ymid, yscale, beats=5, capture=True)
    txt(ax, 1.3, ymid + yscale * 1.6, "約70/min（捕捉）", color=F.INK, fs=11, bold=True)
    txt(ax, 9.6, ymid - yscale * 1.5, "速すぎない範囲で\n血行動態・症状に合わせ調整", color=F.GRAY, fs=9.5, ha="right")
    F.save(fig, "f0603")


def f0604():
    """6.4 出力(mA)を捕捉まで上げる：漸増→閾値+10%維持。"""
    fig, ax = canvas(9.8, 5.0, W=11.6, H=6.0)
    ax0, ax1, ay = 0.7, 10.9, 0.75
    thr_mA, lo_mA, hi_mA = 55, 40, 90
    def mx(v): return ax0 + v / 110 * (ax1 - ax0)
    thr_x = mx(thr_mA)
    ax.add_patch(Rectangle((ax0, ay - 0.5), thr_x - ax0, 4.9, fc="#FBE5E3", alpha=0.5, ec="none", zorder=0))
    ax.add_patch(Rectangle((thr_x, ay - 0.5), ax1 - thr_x, 4.9, fc=F.GREENL, alpha=0.35, ec="none", zorder=0))
    ax.add_patch(Rectangle((mx(lo_mA), ay - 0.5), mx(hi_mA) - mx(lo_mA), 0.22, fc=F.GRAY, alpha=0.35, zorder=1))
    txt(ax, mx((lo_mA + hi_mA) / 2), ay - 0.75, "40–90 mA＝典型的な捕捉出力（個人差大・目安）", color=F.GRAY, fs=9.5)

    ax.plot([ax0, ax1], [ay, ay], color=F.INK, lw=1.4, zorder=2)
    for v in range(0, 111, 20):
        xv = mx(v)
        ax.plot([xv, xv], [ay - 0.08, ay + 0.08], color=F.INK, lw=1.1, zorder=2)
        txt(ax, xv, ay - 1.05, f"{v}", color=F.GRAY, fs=9.5)
    txt(ax, mx(105), ay - 1.05, "mA", color=F.GRAY, fs=9.5)
    ax.plot([thr_x, thr_x], [ay, 5.4], color=F.GOLD, lw=1.8, ls=":", zorder=2)
    txt(ax, thr_x, 5.6, "捕捉閾値", color=F.GOLD, fs=12, bold=True)
    F.arrow(ax, mx(15), ay + 1.1, mx(95), ay + 1.1, color=F.INK, lw=2.4, ms=16)
    txt(ax, mx(55), ay + 1.4, "漸増", color=F.INK, fs=11, bold=True)

    ymid, ys = 3.7, 0.55
    pacing_in(ax, mx(6), mx(38), ymid, ys, beats=2, capture=False)
    txt(ax, mx(22), ymid + ys * 1.7, "非捕捉", color=F.RED, fs=11, bold=True)
    txt(ax, mx(22), ymid - ys * 1.7, "スパイクのみ・QRSなし", color=F.RED, fs=9.5)

    pacing_in(ax, mx(45), mx(70), ymid, ys, beats=2, capture=True)
    txt(ax, mx(64), ymid + ys * 1.7, "捕捉（電気的）", color=F.GREEN, fs=11, bold=True)

    pacing_in(ax, mx(78), mx(106), ymid, ys, beats=2, capture=True)
    txt(ax, mx(92), ymid + ys * 1.7, "維持＝\n閾値＋約10%", color=F.GOLD, fs=10.5, bold=True)
    F.save(fig, "f0604")


def f0605():
    """6.5 電気的捕捉 vs 機械的捕捉（偽捕捉）：ECG/SpO2脈波/A-lineの3段対比。"""
    fig, ax = canvas(10.2, 5.6, W=12, H=7.2)
    lcx, rcx = 3.1, 9.1
    colw = 5.4

    # column labels moved down 0.30 (6.9->6.60) so they clear the "電気的捕捉≠機械的
    # 捕捉" note above (was only 0.25 away vertically, with overlapping x-ranges too,
    # so "機械的捕捉" and "偽捕捉" were rendering on top of each other). The rest of the
    # panel (ECG/pleth/A-line rows, checkmarks) shifts down by the same 0.30 so none of
    # the internal spacing changes -- there's plenty of clear canvas below.
    txt(ax, lcx, 6.60, "真の捕捉（true capture）", color=F.GREEN, fs=13, bold=True)
    txt(ax, rcx, 6.60, "偽捕捉（false / pseudo-capture）", color=F.RED, fs=13, bold=True)
    txt(ax, 6.1, 7.15, "電気的捕捉 ≠ 機械的捕捉", color=F.GOLD, fs=11.5, bold=True)

    ecg_y, pleth_y, art_y = 5.55, 3.85, 2.25
    row_h = 0.9

    # dotted boxes around ECG rows -> "ECGはそっくり"
    ax.add_patch(Rectangle((lcx - colw / 2 + 0.1, ecg_y - row_h / 2 - 0.05), colw - 0.2, row_h + 0.1,
                            fc="none", ec=F.INK, lw=1.2, ls=":", zorder=2))
    ax.add_patch(Rectangle((rcx - colw / 2 + 0.1, ecg_y - row_h / 2 - 0.05), colw - 0.2, row_h + 0.1,
                            fc="none", ec=F.INK, lw=1.2, ls=":", zorder=2))
    txt(ax, 6.1, ecg_y + row_h / 2 + 0.28, "ECGはそっくり", color=F.INK, fs=10, bold=True)

    pacing_in(ax, lcx - colw / 2 + 0.35, lcx + colw / 2 - 0.35, ecg_y, 0.42, beats=2, capture=True)
    pacing_in(ax, rcx - colw / 2 + 0.35, rcx + colw / 2 - 0.35, ecg_y, 0.42, beats=2, capture=True, false_capture=True)
    txt(ax, lcx - colw / 2 - 0.15, ecg_y, "ECG", color=F.GRAY, fs=10.5, ha="right")

    Xp, Yp_true = _pulse_wave(cycles=3, kind="pulse")
    Xp, Yp_flat = _pulse_wave(cycles=3, kind="flat")
    wave_in(ax, Xp, Yp_true, lcx - colw / 2 + 0.35, lcx + colw / 2 - 0.35, pleth_y, 0.55, color=F.GREEN, lw=2.0)
    wave_in(ax, Xp, Yp_flat, rcx - colw / 2 + 0.35, rcx + colw / 2 - 0.35, pleth_y, 0.55, color=F.RED, lw=2.0)
    txt(ax, lcx - colw / 2 - 0.15, pleth_y, "SpO2脈波", color=F.GRAY, fs=10.5, ha="right")

    Xa, Ya_true = _pulse_wave(cycles=3, kind="pulse")
    Xa, Ya_flat = _pulse_wave(cycles=3, kind="flat")
    wave_in(ax, Xa, Ya_true, lcx - colw / 2 + 0.35, lcx + colw / 2 - 0.35, art_y, 0.5, color=F.GREEN, lw=2.0)
    wave_in(ax, Xa, Ya_flat, rcx - colw / 2 + 0.35, rcx + colw / 2 - 0.35, art_y, 0.5, color=F.RED, lw=2.0)
    txt(ax, lcx - colw / 2 - 0.15, art_y, "A-line", color=F.GRAY, fs=10.5, ha="right")

    check(ax, lcx, art_y - 0.95, size=0.22, color=F.GREEN, lw=3.5)
    txt(ax, lcx + 0.5, art_y - 0.95, "触知脈あり", color=F.GREEN, fs=11, bold=True, ha="left")
    big_x(ax, rcx, art_y - 0.95, size=0.20, color=F.RED, lw=3.5)
    txt(ax, rcx + 0.5, art_y - 0.95, "脈触知できず＝有効拍出なし", color=F.RED, fs=11, bold=True, ha="left")

    F.box(ax, 0.3, 0.15, 11.4, 0.72, F.RED, ec="none",
          txt="ECGだけで捕捉と判断しない——脈・SpO2脈波・A-lineで機械的捕捉を確認",
          tc=F.WHITE, fs=12.5, lw=0, bold=True)
    F.save(fig, "f0605")

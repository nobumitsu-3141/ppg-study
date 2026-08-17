# -*- coding: utf-8 -*-
import numpy as np
from matplotlib.patches import FancyBboxPatch, Arc, Circle, Polygon, Rectangle, Wedge
import figlib as F
from fighelp import *
from matplotlib.patches import Ellipse

# ============================================================== local helpers ====
# (schematic-only primitives shared by several figures in this group; kept local
# so ch7/ch8 composition stays in one file per the group convention.)

def _torso(ax, cx, cy, w, h, fc="#F2E2C8", ec=F.INK, lw=1.3, alpha=1.0, ls="-"):
    """A very simple rounded-rect body/torso silhouette (schematic, not anatomy)."""
    p = FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                        boxstyle=f"round,pad=0.01,rounding_size={min(w,h)*0.18}",
                        fc=fc, ec=ec, lw=lw, alpha=alpha, ls=ls, zorder=2)
    ax.add_patch(p)
    return p

def _heart(ax, cx, cy, w, h, color=F.RED, alpha=0.22, zorder=3):
    """Translucent ellipse standing in for the cardiac shadow (schematic)."""
    ax.add_patch(Ellipse((cx, cy), w, h, fc=color, ec="none", alpha=alpha, zorder=zorder))

def _pad(ax, cx, cy, w=0.62, h=0.40, color=F.TEAL, dashed=False, zorder=5):
    """A defibrillator pad rectangle."""
    ec = color if dashed else "none"
    fc = "none" if dashed else color
    p = FancyBboxPatch((cx - w/2, cy - h/2), w, h, boxstyle="round,pad=0.006,rounding_size=0.06",
                        fc=fc, ec=ec if dashed else "none", lw=1.8 if dashed else 1.0,
                        ls="--" if dashed else "-", zorder=zorder)
    ax.add_patch(p)
    return p

def _magnet(ax, cx, cy, s=0.45, color=F.GOLD):
    """A tiny horseshoe-magnet glyph (Arc + two leg rectangles)."""
    ax.add_patch(Arc((cx, cy), s*1.5, s*1.5, theta1=0, theta2=180, color=color, lw=4.2, zorder=5))
    ax.add_patch(Rectangle((cx - s*0.75, cy - s*0.55), s*0.22, s*0.55, fc=color, ec="none", zorder=5))
    ax.add_patch(Rectangle((cx + s*0.53, cy - s*0.55), s*0.22, s*0.55, fc=color, ec="none", zorder=5))

def _flame(ax, cx, cy, s=0.32, color=F.RED):
    """A tiny flame teardrop (Polygon)."""
    pts = [(cx, cy+s), (cx+0.55*s, cy+0.15*s), (cx+0.30*s, cy-0.15*s),
           (cx+0.15*s, cy-s), (cx-0.15*s, cy-0.55*s), (cx-0.45*s, cy+0.05*s)]
    ax.add_patch(Polygon(pts, closed=True, fc=color, ec="none", alpha=0.9, zorder=7))

def _stack_flow(ax, x, ytop, w, nodes, gap=0.16, arrow_color=F.INK):
    """Stack rounded boxes top-to-bottom with connecting arrows. `nodes` = list of
    dicts: title,lines,fc,ec,tc,h,title_color. A node may override the shared width
    via "w" (e.g. a box with more text) -- it stays centered on the same vertical
    arrow line (x + w/2) as the rest of the stack. Returns bottom y of last node."""
    y = ytop
    prev_bottom = None
    xc = x + w/2
    for i, n in enumerate(nodes):
        h = n.get("h", 0.6)
        nw = n.get("w", w)
        nx = xc - nw/2
        y0 = y - h
        if prev_bottom is not None:
            F.arrow(ax, xc, prev_bottom, xc, y0 + h, color=arrow_color, lw=2.0, ms=13)
        rbox(ax, nx, y0, nw, h, n.get("fc", "white"), n.get("ec", F.INK),
             txt_lines=n.get("lines"), tc=n.get("tc", F.INK), fs=n.get("fs", 11),
             title=n.get("title"), title_color=n.get("title_color", n.get("ec", F.INK)),
             title_fs=n.get("title_fs", 12.5), align=n.get("align", "center"))
        prev_bottom = y0
        y = y0 - gap
    return prev_bottom


# ================================================================== 7.1 ===========
def f0701():
    """Standard operating flow, drawn as two horizontal rows (S-curve) to fit the
    wide canvas: row A left->right (power .. mode branches), row B right->left
    (energy .. CPR). All boxes are defined as explicit [x0,x1] ranges to keep the
    left-edge/width arithmetic unambiguous."""
    fig, ax = canvas(9.5, 4.3, W=11, H=5)

    # ---- Row A (top, y=4.15): steps 1-3 -> mode diamond -> 3 branches ----
    yA = 4.15
    bh = 0.62
    def rowbox(x0, x1, label, **kw):
        F.box(ax, x0, yA-bh/2, x1-x0, bh, kw.pop("fc", "white"), kw.pop("ec", F.INK), label,
              tc=kw.pop("tc", F.INK), fs=11, lw=kw.pop("lw", 1.3), **kw)
    b1 = (0.25, 1.25); b2 = (1.55, 3.15); b3 = (3.45, 4.95)
    rowbox(*b1, "電源ON")
    F.arrow(ax, b1[1], yA, b2[0], yA, lw=2.0)
    rowbox(*b2, "モニタで\nリズム確認")
    F.arrow(ax, b2[1], yA, b3[0], yA, lw=2.0)
    rowbox(*b3, "パッド貼付\n(前側方/前後)")

    # diamond decision (kept well clear of the incoming arrowhead so it never
    # overlaps the box3 arrow, and the diamond's own text)
    dcx, ds = 6.15, 0.68
    F.arrow(ax, b3[1], yA, dcx-ds, yA, lw=2.0)
    diamond = Polygon([(dcx-ds, yA), (dcx, yA+ds*0.68), (dcx+ds, yA), (dcx, yA-ds*0.68)],
                       closed=True, fc=F.GOLDL, ec=F.GOLD, lw=1.6, zorder=3)
    ax.add_patch(diamond)
    txt(ax, dcx, yA, "モードは？", color=F.GOLD, fs=11, bold=True)

    # 3 branch boxes, all starting at the same x, stacked. Height matches the main
    # row (0.62) since a shorter box was found to clip 2-line bold fs11 text.
    bx0, bx1 = dcx+ds+0.30, dcx+ds+0.30+1.70
    y_top, y_mid, y_bot = 4.65, 3.95, 3.25
    bh2 = 0.62
    F.arrow(ax, dcx+ds, yA, bx0, y_top, lw=1.8, color=F.TEAL)
    F.box(ax, bx0, y_top-bh2/2, bx1-bx0, bh2, F.TEAL, "none", "除細動\n（非同期）", tc="white", fs=11, lw=0)
    F.arrow(ax, dcx+ds, yA, bx0, y_mid, lw=1.8, color=F.TEAL)
    F.box(ax, bx0, y_mid-bh2/2, bx1-bx0, bh2, F.TEAL, "none", "同期\n（SYNC）", tc="white", fs=11, lw=0)
    F.arrow(ax, dcx+ds, yA, bx0, y_bot, lw=1.8, color=F.GRAY)
    F.box(ax, bx0, y_bot-bh2/2, bx1-bx0, bh2, F.LGRAY, "none", "ペーシング\n（PACER）", tc=F.INK, fs=11, lw=0)

    # pacer diversion note (dashed, off the main flow) -- placed in the gap below,
    # clear of the branch cluster and clear of row B
    rbox(ax, 3.30, 1.95, 4.20, 0.95, "white", F.GRAY,
         txt_lines=[("別フロー：レート→出力を漸増", F.GRAY), ("→捕捉を機械的に確認（第6章）", F.GRAY)],
         fs=10.5, title=None)
    F.arrow(ax, bx0, y_bot, 7.50, 2.80, lw=1.6, color=F.GRAY, ls=":")

    # ---- Row B (bottom, y=1.10): steps 5-9, right -> left ----
    yB = 1.10
    bhB = 0.65
    def rowboxB(x0, x1, label, **kw):
        F.box(ax, x0, yB-bhB/2, x1-x0, bhB, kw.pop("fc", "white"), kw.pop("ec", F.INK), label,
              tc=kw.pop("tc", F.INK), fs=11, lw=kw.pop("lw", 1.3), **kw)
    n5 = (8.85, 10.70); n6 = (7.00, 8.55); n7 = (4.60, 6.70); n8 = (2.95, 4.30); n9 = (0.30, 2.65)
    rowboxB(*n5, "エネルギー(J)\n選択")
    F.arrow(ax, n5[0], yB, n6[1], yB, lw=2.0)
    rowboxB(*n6, "充電\n（charge）")
    F.arrow(ax, n6[0], yB, n7[1], yB, lw=2.0)
    # called directly (not via rowboxB's fs=11) -- fs reduced to 9.5 since "安全確認（目視
    # 一周）" was wider than this box's width (n7 is narrower than the other row-B boxes)
    F.box(ax, n7[0], yB - bhB / 2, n7[1] - n7[0], bhB, F.REDL, F.RED,
          "離れて！\n安全確認（目視一周）", tc=F.RED, fs=9.5, lw=1.6)
    F.arrow(ax, n7[0], yB, n8[1], yB, lw=2.0, color=F.RED)
    rowboxB(*n8, "放電\n（shock）", fc=F.REDL, ec=F.RED, tc=F.RED, lw=1.6)
    F.arrow(ax, n8[0], yB, n9[1], yB, lw=2.0)
    rowboxB(*n9, "ただちにCPR／\nリズム再評価")

    # merge: defib + sync branches converge, then drop straight down into n5's top
    mx = (n5[0]+n5[1])/2   # 9.775 -- aligned above n5
    conv_y = (y_top+y_mid)/2
    F.arrow(ax, bx1, y_top, mx, conv_y, lw=1.8, color=F.TEAL)
    F.arrow(ax, bx1, y_mid, mx, conv_y, lw=1.8, color=F.TEAL)
    F.arrow(ax, mx, conv_y, mx, yB+bhB/2, lw=2.4, color=F.INK)

    # call-out: 4-step verbal check, as a bottom strip (only fully clear space left)
    rbox(ax, 0.30, 0.05, 10.40, 0.60, "white", F.RED, title=None,
         txt_lines=[("掛け声：①自分、離れます →②スタッフ、離れて →③酸素、離して(1 m以上) →④周囲よし(目視一周)", F.GOLD)],
         fs=10.3)

    F.save(fig, "f0701")


# ================================================================== 7.2 ===========
def f0702():
    fig, ax = canvas(9.5, 4.3, W=11, H=5)

    # top CIED note (badge widened: "CIED" at fs10.5 doesn't fit a 0.5-wide box and was
    # spilling into the caption text that starts right after it)
    F.box(ax, 0.75, 4.62, 0.85, 0.32, F.BLUE, "none", "CIED", tc="white", fs=10.5, lw=0)
    txt(ax, 1.75, 4.78, "CIEDジェネレータ直上を避ける（詳細は第8章）", color=F.RED, fs=11.5, ha="left")

    # ---- left: anterolateral ----
    lx = 2.6
    txt(ax, lx, 4.25, "前側方（anterolateral）", color=F.GOLD, fs=13.5, bold=True)
    _torso(ax, lx, 2.2, 2.3, 3.0)
    _heart(ax, lx, 2.25, 1.35, 1.75)
    padA = (lx+0.55, 3.35)   # right pad: subclavicular
    padB = (lx-0.65, 1.35)   # left pad: mid-axillary, 5th ICS
    _pad(ax, *padA, color=F.TEAL)
    _pad(ax, *padB, color=F.TEAL)
    F.arrow(ax, padA[0], padA[1]-0.2, padB[0], padB[1]+0.2, color=F.TEAL, lw=2.2)
    txt(ax, padA[0]+0.85, padA[1]+0.05, "右パッド\n(右鎖骨下)", color=F.INK, fs=11, ha="left")
    txt(ax, padB[0]-0.9, padB[1]-0.1, "左パッド\n(中腋窩線・5肋間)", color=F.INK, fs=11, ha="left")
    rbox(ax, 0.4, 0.35, 4.4, 0.62, F.GREENL, F.GREEN, txt_lines=[("標準・最速・胸骨圧迫を妨げにくい", F.INK)], fs=11)

    ax.plot([5.5, 5.5], [0.25, 4.65], color=F.LGRAY, lw=1.2, ls="--", zorder=1)

    # ---- right: antero-posterior ----
    rx = 8.3
    txt(ax, rx, 4.25, "前後（antero-posterior）", color=F.GOLD, fs=13.5, bold=True)
    _torso(ax, rx, 2.2, 2.3, 3.0)
    _heart(ax, rx, 2.25, 1.35, 1.75)
    padF = (rx-0.35, 2.55)
    padP = (rx+1.35, 2.55)   # drawn just outside torso = "the other side" (schematic)
    _pad(ax, *padF, color=F.TEAL)
    _pad(ax, *padP, color=F.TEAL, dashed=True)
    F.arrow(ax, padF[0], padF[1], padP[0], padP[1], color=F.TEAL, lw=2.2, style="<|-|>")
    txt(ax, padF[0]-0.05, padF[1]+0.42, "前パッド\n(胸骨左縁〜心尖)", color=F.INK, fs=11)
    txt(ax, padP[0], padP[1]+0.42, "背部パッド\n(左肩甲骨下)", color=F.INK, fs=11)
    # both notes: box + centered 2-line text (not rbox's single top-anchored line) --
    # each one-line string was far wider than its box at fs10.3, running behind the
    # torso shape between the two panels
    F.box(ax, 6.1, 0.9, 4.4, 0.62, F.GREENL, F.GREEN,
          "AF・待機的カルディオバージョン\n／ペーシング／CIED回避で有利", tc=F.INK, fs=9.5, bold=False, lw=1.4)
    F.box(ax, 6.5, 0.15, 3.6, 0.62, "white", F.GOLD,
          "前後 96% vs 前側方 78%\n（待機的AF・Kirchhof 2002）", tc=F.GOLD, fs=9.5, bold=False, lw=1.4)

    F.save(fig, "f0702")


# ================================================================== 7.3 ===========
def f0703():
    fig, ax = canvas(9.5, 4.3, W=11, H=5)

    # formula (top-left)
    rbox(ax, 0.35, 3.95, 3.6, 0.85, F.GOLDL, F.GOLD, txt_lines=None, title="I ＝ V ÷ TTI",
         title_color=F.GOLD, title_fs=20)
    # plain centered box (not rbox's top-anchored txt_lines): this box is too short for
    # rbox's fixed top offset, which was pushing the text past the bottom border
    F.box(ax, 0.35, 3.45, 3.6, 0.42, "white", F.GOLD, "成人の典型 TTI ＝ 70–80 Ω", tc=F.GOLD, fs=11.5, bold=False, lw=1.4)

    # bar chart (bottom-left): qualitative TTI before/after shaving
    bx0, by0 = 0.6, 0.55
    ax.plot([bx0, bx0+3.0], [by0, by0], color=F.INK, lw=1.4, zorder=2)
    bar_w = 0.9
    ax.add_patch(Rectangle((bx0+0.15, by0), bar_w, 1.9, fc=F.GRAY, ec="none", zorder=3))
    ax.add_patch(Rectangle((bx0+1.55, by0), bar_w, 1.0, fc=F.TEAL, ec="none", zorder=3))
    txt(ax, bx0+0.6, by0-0.28, "体毛あり", color=F.INK, fs=11)
    txt(ax, bx0+2.0, by0-0.28, "剃毛後", color=F.INK, fs=11)
    txt(ax, bx0+1.5, by0+2.25, "TTI（模式）", color=F.GRAY, fs=11)
    F.arrow(ax, bx0+2.0, by0+2.05, bx0+2.0, by0+1.2, color=F.GOLD, lw=2.2)

    # 6-item checklist (right column)
    items = [
        ("① パッドをしっかり圧着（密着・浮きなし）", F.TEAL),
        ("② 導電ゲル/ゲルパッドを使う（乾いたパッドは高抵抗）", F.TEAL),
        ("③ 皮膚を乾かす（汗・水を拭く）", F.TEAL),
        ("④ 体毛を除去（多毛は抵抗が大）", F.TEAL),
        ("⑤ パッド同士を触れさせない（接触＝短絡・皮膚アーク）", F.RED),
        ("⑥ 呼気位相で放電（肺の空気が少ない）", F.TEAL),
    ]
    ytop = 4.55
    txt(ax, 7.7, ytop+0.35, "TTIを下げる 6つのレバー", color=F.GOLD, fs=13, bold=True)
    for i, (s, c) in enumerate(items):
        y = ytop - i*0.72
        ax.add_patch(Circle((4.65, y), 0.10, fc=c, ec="none", zorder=4))
        txt(ax, 4.9, y, s, color=c if c == F.RED else F.INK, fs=11, ha="left")

    F.save(fig, "f0703")


# ================================================================== 7.4 ===========
def f0704():
    fig, ax = canvas(9.5, 4.3, W=11, H=5)

    # bed + patient
    ax.add_patch(FancyBboxPatch((2.0, 0.85), 5.6, 1.35, boxstyle="round,pad=0.01,rounding_size=0.12",
                                 fc="#EAF1F8", ec=F.GRAY, lw=1.2, zorder=1))
    _torso(ax, 4.8, 1.9, 3.6, 1.05, fc="#F2E2C8")
    padA = (4.15, 2.05); padB = (5.15, 2.05)
    _pad(ax, *padA, color=F.TEAL, w=0.55, h=0.35)
    _pad(ax, *padB, color=F.TEAL, w=0.55, h=0.35)
    shock_bolt(ax, 4.65, 2.55, size=0.42, color=F.RED)
    _flame(ax, 5.05, 2.65, s=0.34, color=F.ORANGE)
    txt(ax, 4.8, 3.05, "放電アーク＋高濃度O2＝発火", color=F.RED, fs=12, bold=True)

    # O2 source above head, straight arrow to a distance bar (all raised to y~4.45
    # so nothing collides with the callout boxes stacked underneath it)
    ax.add_patch(Circle((1.35, 4.45), 0.28, fc="#D9F2F2", ec=F.TEAL, lw=1.6, zorder=3))
    ax.add_patch(Rectangle((1.10, 4.03), 0.50, 0.15, fc=F.TEAL, ec="none", zorder=3))
    txt(ax, 1.35, 3.75, "酸素源（マスク/バッグ）", color=F.INK, fs=11)
    F.arrow(ax, 1.63, 4.45, 8.5, 4.45, color=F.GOLD, lw=3.2, ms=20)
    ax.plot([8.7, 8.7], [4.10, 4.80], color=F.GOLD, lw=2.4, zorder=5)
    ax.plot([8.55, 8.85], [4.10, 4.10], color=F.GOLD, lw=2.4, zorder=5)
    ax.plot([8.55, 8.85], [4.80, 4.80], color=F.GOLD, lw=2.4, zorder=5)
    txt(ax, 9.35, 4.45, "1 m以上", color=F.GOLD, fs=15, bold=True, ha="left")

    rbox(ax, 0.15, 2.65, 2.6, 0.90, "white", F.TEAL, txt_lines=[("回路（気管チューブ）は", F.INK), ("外さず横へ", F.INK)],
         fs=11, title=None)
    rbox(ax, 7.3, 3.15, 3.3, 0.90, "white", F.TEAL,
         txt_lines=[("離した酸素はベッド/シーツに", F.INK), ("当てず床側・外向きへ", F.INK)], fs=10.5)

    rbox(ax, 0.3, 0.15, 10.4, 0.62, F.REDL, F.RED,
         txt_lines=[("アルコール消毒は乾かしてから／濡れた胸・酸素テント・高流量鼻カニュラに注意", F.RED)], fs=11.5)

    F.save(fig, "f0704")


# ================================================================== 7.6 ===========
def f0706():
    # Slightly larger physical canvas than the group default (a dense 3-col x 8-row
    # reference table needs more room per cell than a schematic figure) -- table_
    # figure_slide's pptx placeholder is also wider than the standard figure box,
    # so this stays consistent with how the table will actually be displayed.
    fig, ax = canvas(10.3, 4.85, W=11.4, H=5.35)
    rows = [
        ["放電したがVF/VT\n持続（無効）",
         "エネルギー不足・パッド不良\n・可逆的原因の未是正",
         ("エネルギー最大化・パッド\n貼替・CPR継続・H&T是正", F.INK)],
        ["充電しない/\n放電できない",
         "電源・バッテリ切れ\n・パッド未接続",
         "電源/ケーブルを挿し直す\n・非同期へ切替・予備機へ"],
        ["パッド接触不良/\nインピーダンス高警告",
         "密着不良・体毛\n・汗/濡れ・パッド劣化",
         "圧着・体毛除去・拭く\n・新パッドに交換（7.3）"],
        ["同期（SYNC）が\nかからない",
         "R波が小さい・電極外れ\n・VFでR波なし",
         "誘導/ゲイン変更\n・VFなら非同期へ切替"],
        [("カルディオバージョンで\nT波放電のリスク", F.RED),
         "放電毎にSYNC自動解除\n（再武装忘れ）",
         "毎回再SYNC・R波確認\nしてから放電（5.4）"],
        ["ペーシングで捕捉しない\n（QRSが続かない）",
         "出力不足・パッド不良\n・重症の代謝異常/虚血",
         "出力を漸増・捕捉閾値\n＋10%維持・前後に貼替"],
        [("モニタ上は捕捉に見えるが\n脈がない（偽捕捉）", F.RED),
         "ペーシングアーチファクト\n・筋収縮を誤認",
         "触知脈・SpO2波形・A-line\nで機械的捕捉を確認"],
    ]
    table(ax, 0.3, 0.35, 10.8, 4.7,
          ["所見", "考えられる原因", "対処"], rows,
          col_w=[3.3, 3.9, 3.6], fs=11, header_fs=13.5)
    F.save(fig, "f0706")


# ================================================================== 8.1 ===========
def f0801():
    fig, ax = canvas(9.5, 4.3, W=11, H=5)

    rbox(ax, 0.3, 4.15, 4.9, 0.70, F.BLUEL, F.BLUE, title="ICD＝除細動器", title_color=F.BLUE, title_fs=14)
    _magnet(ax, 2.75, 3.68, s=0.55)
    F.arrow(ax, 2.75, 3.33, 2.75, 2.98, lw=2.2)
    F.box(ax, 2.75-1.9, 2.15, 3.8, 0.80, F.REDL, F.RED, "頻拍治療（ショック/ATP）\nを一時停止", tc=F.RED, fs=12.5, lw=1.6)
    txt(ax, 2.75, 1.75, "ペーシング機能には無影響\n（設定レートは変わらない）", color=F.GRAY, fs=11)

    rbox(ax, 5.8, 4.15, 4.9, 0.70, F.GREENL, F.GREEN, title="PM＝ペースメーカ", title_color=F.GREEN, title_fs=14)
    _magnet(ax, 8.25, 3.68, s=0.55)
    F.arrow(ax, 8.25, 3.33, 8.25, 2.98, lw=2.2)
    F.box(ax, 8.25-1.9, 2.15, 3.8, 0.80, F.GOLDL, F.GOLD, "非同期（固定レート）\nペーシングに切替", tc=F.GOLD, fs=12.5, lw=1.6)
    txt(ax, 8.25, 1.75, "自己脈に関係なく\n規定レートで打つ", color=F.GRAY, fs=11)

    # bovie/electrocautery warning -- placed in its own clear band below both gray
    # notes (notes bottom ~1.45) and above the banner, so it never collides with them
    ax.plot([2.55, 3.0, 3.45, 3.9], [1.22, 1.34, 1.10, 1.24], color=F.RED, lw=2.0, zorder=6)
    txt(ax, 4.1, 1.20, "電気メスの干渉＝ICD誤作動／PMペーシング抑制", color=F.RED, fs=11, ha="left")

    # box + manually centered 2-line text (not rbox's top-anchored txt_lines, which was
    # pushing the 2nd line past the bottom border for this box height)
    rbox(ax, 0.4, 0.25, 10.2, 0.78, "#D9F2F2", F.TEAL)
    txt(ax, 0.4 + 10.2 / 2, 0.78, "周術期＝モノポーラ電気メスの干渉対策と併せ、機種・設定・ペーシング依存度を確認し、", color=F.INK, fs=11)
    txt(ax, 0.4 + 10.2 / 2, 0.50, "再プログラム or 磁石対応を事前計画", color=F.TEAL, fs=11)

    F.save(fig, "f0801")


# ================================================================== 8.2 ===========
def f0802():
    fig, ax = canvas(9.5, 4.3, W=11, H=5)

    # box + centered text (not rbox's top-anchored txt_lines): this box was too short
    # for the fixed offset, so the text sank past the bottom border
    F.box(ax, 0.3, 4.5, 10.4, 0.45, F.REDL, F.RED,
          "VF/無脈性VTなら、CIEDがあってもショックは遅らせない", tc=F.RED, fs=12.5, bold=False, lw=1.4)

    # main torso (recommended AP)
    _torso(ax, 2.5, 2.35, 2.6, 3.35, fc="#F2E2C8")
    # badge widened: "ジェネレータ" at fs10.8 doesn't fit a 1.15-wide box (right edge kept
    # aligned with the ≥8cm arrow below, so it only grows further left)
    F.box(ax, 1.475, 3.75, 1.6, 0.5, F.BLUE, "none", "ジェネレータ", tc="white", fs=10.8, lw=0)
    _pad(ax, 2.5, 2.15, w=0.7, h=0.42, color=F.TEAL)
    F.arrow(ax, 3.15, 3.75, 3.15, 2.36, style="<|-|>", color=F.GOLD, lw=2.0)
    txt(ax, 3.55, 3.05, "≥8 cm", color=F.GOLD, fs=13.5, bold=True, ha="left")
    rbox(ax, 0.35, 0.2, 4.3, 0.55, "#D9F2F2", F.TEAL, txt_lines=[("前後（AP）配置が望ましい", F.TEAL)], fs=11)

    # back-side inset
    rbox(ax, 4.15, 1.55, 2.05, 2.3, "#F5F7F9", F.GRAY, title="背側（インセット）", title_color=F.GRAY, title_fs=11)
    _torso(ax, 5.15, 2.0, 1.35, 1.35, fc="#F2E2C8")
    _pad(ax, 5.15, 2.05, w=0.6, h=0.4, color=F.TEAL)
    txt(ax, 5.15, 1.62, "背側パッド", color=F.INK, fs=11)

    # bad example: badge widened to fit its text, and moved above the pad+X (was
    # centered exactly on the pad, so the red X was struck straight through the
    # "ジェネレータ" label -- every other big_x() in the deck sits beside its label,
    # not on top of it, so this restores that convention)
    txt(ax, 7.55, 3.85, "悪い例：ジェネレータ直上", color=F.RED, fs=11.5, bold=True)
    _torso(ax, 7.55, 2.3, 2.05, 2.9, fc="#F2E2C8", alpha=0.55)
    F.box(ax, 7.55-0.75, 3.20, 1.5, 0.42, F.BLUE, "none", "ジェネレータ", tc="white", fs=9.8, lw=0)
    _pad(ax, 7.55, 2.50, w=0.85, h=0.42, color=F.TEAL, dashed=True)
    big_x(ax, 7.55, 2.50, size=0.42)

    # fs reduced (10.8->8.0): "（インテロゲーション）" was wider than the 2.0-wide box
    rbox(ax, 8.85, 0.55, 2.0, 3.35, "#D9F2F2", F.TEAL, title="放電後", title_color=F.TEAL, title_fs=12.5,
         txt_lines=[("デバイス点検", F.INK), ("（インテロゲーション）", F.INK), ("設定・閾値・", F.INK),
                    ("リード損傷を確認", F.INK)], fs=8.0)

    F.save(fig, "f0802")


# ================================================================== 8.3 ===========
def f0803():
    fig, ax = canvas(9.5, 4.3, W=11, H=5)
    ax.plot([5.5, 5.5], [0.3, 4.7], color=F.LGRAY, lw=1.4, ls="--", zorder=1)

    # left: open-chest internal paddles
    txt(ax, 2.6, 4.55, "開胸（心臓外科／開心）", color=F.ORANGE, fs=13.5, bold=True)
    ax.add_patch(Circle((2.35, 2.85), 0.55, fc=F.REDL, ec=F.RED, lw=1.4, zorder=2))
    ax.add_patch(Circle((2.85, 2.85), 0.55, fc=F.REDL, ec=F.RED, lw=1.4, zorder=2))
    ax.add_patch(Polygon([(2.1, 2.55), (3.1, 2.55), (2.6, 1.75)], closed=True, fc=F.REDL, ec=F.RED, lw=1.4, zorder=2))
    txt(ax, 2.6, 2.85, "心臓", color=F.RED, fs=11, bold=True)
    ax.add_patch(Rectangle((1.15, 2.65), 0.55, 0.32, fc=F.GRAY, ec="none", zorder=4))
    ax.add_patch(Rectangle((3.4, 2.65), 0.55, 0.32, fc=F.GRAY, ec="none", zorder=4))
    # moved left so it clears the heart circle (was overlapping its top-left edge)
    txt(ax, 1.05, 3.1, "内部パドル", color=F.GRAY, fs=10.5)
    rbox(ax, 0.55, 0.85, 4.1, 0.95, F.GOLDL, F.GOLD,
         txt_lines=[("内部パドル 10–20 J", F.GOLD), ("（低エネルギーから漸増）［要確認］", F.GOLD)], fs=11.5)
    txt(ax, 2.6, 0.55, "体外の約1/10（直接心筋に通電するため／体外 120–200 J）", color=F.ORANGE, fs=10.6)

    # right: external, prone/lateral, drape, AP pads
    txt(ax, 8.3, 4.55, "体外（閉胸・術野の制約）", color=F.GREEN, fs=13.5, bold=True)
    ax.add_patch(Ellipse((8.3, 2.7), 3.4, 1.5, fc="#F2E2C8", ec=F.INK, lw=1.3, zorder=2))
    ax.add_patch(Rectangle((6.75, 2.15), 3.1, 1.1, fc="#EAF1F8", ec=F.GRAY, lw=1.0, alpha=0.55, zorder=3))
    txt(ax, 8.3, 3.55, "滅菌ドレープ・体位（腹臥位/側臥位）", color=F.GRAY, fs=10.5)
    _pad(ax, 7.6, 2.7, w=0.55, h=0.38, color=F.TEAL)
    _pad(ax, 9.0, 2.7, w=0.55, h=0.38, color=F.TEAL, dashed=True)
    txt(ax, 7.6, 3.2, "前パッド", color=F.INK, fs=11)
    txt(ax, 9.0, 3.2, "背側パッド", color=F.INK, fs=11)
    rbox(ax, 6.15, 0.55, 4.3, 0.95, F.GREENL, F.GREEN,
         txt_lines=[("ドレープ・体位で貼付を工夫、", F.GREEN), ("前後配置が有利", F.GREEN)], fs=11.5)

    F.save(fig, "f0803")


# ================================================================== 8.4 ===========
def f0804():
    fig, ax = canvas(9.5, 4.3, W=11, H=5)

    # row0 col0's 2nd line was one long line that ran into col1 ("2 J/kg"); split at a
    # natural point so every line clears the column border. row0 col3's 3-line cell
    # ("≥4 J/kg"/"最大10 J/kg"/"または成人量") needs a taller row than the original
    # rh=0.68 -- see the enlarged table() call below.
    rows = [
        [("除細動\n（VF/無脈性VT\n・非同期）", F.BLUE), ("2 J/kg", F.GOLD), ("4 J/kg", F.GOLD),
         ("≥4 J/kg\n最大10 J/kg\nまたは成人量", F.GOLD)],
        [("同期カルディオ\nバージョン", F.GREEN), ("0.5–1 J/kg", F.GOLD), ("2 J/kg", F.GOLD), ("―", F.INK)],
    ]
    # col_w must sum to the table's own width param (7.3) -- table() lays columns
    # out purely from col_w, so a mismatch silently overruns the intended box. col1/col2
    # were widened slightly too ("0.5-1 J/kg" and the "2回目以降" header were touching
    # their column borders at the original 1.25/1.30).
    table(ax, 0.3, 1.60, 7.3, 3.0, ["適応", "初回", "2回目以降", "上限"], rows,
          col_w=[2.6, 1.45, 1.5, 1.75], fs=11.5, header_fs=12.5)

    # shifted right to clear the wider table; shrunk to keep clear of the canvas edge
    rbox(ax, 7.75, 2.35, 3.0, 2.3, "#F7F0D9", F.GOLD, title="例）体重 20 kg", title_color=F.GOLD, title_fs=13,
         txt_lines=[("除細動 40 J → 80 J", F.INK), ("（上限は成人量まで）", F.GRAY),
                    ("同期 10–20 J → 40 J", F.INK)], fs=12)

    # box + centered text (not rbox's top-anchored txt_lines) and shorter, to clear the
    # taller table above it (table now extends down to y=1.60)
    F.box(ax, 0.3, 0.3, 10.4, 1.0, F.ORANGEL, F.ORANGE,
          "パッド/パドル：乳児（＜1歳・目安＜10 kg）は小児用、\n体格により前後配置、パッド同士を接触させない",
          tc=F.ORANGE, fs=12, bold=False, lw=1.4)

    F.save(fig, "f0804")


# ================================================================== 8.5 ===========
def f0805():
    fig, ax = canvas(9.5, 4.3, W=11, H=5)
    for xv in (3.75, 7.35):
        ax.plot([xv, xv], [0.25, 4.75], color=F.LGRAY, lw=1.2, ls="--", zorder=1)

    # panel 1: pregnancy (torso shortened slightly so the LUD label below it has
    # clearance; it was overlapping the torso's bottom edge)
    txt(ax, 1.85, 4.55, "妊娠", color=F.BLUE, fs=14, bold=True)
    _torso(ax, 1.85, 2.75, 1.9, 2.00, fc="#F2E2C8")
    ax.add_patch(Circle((1.85, 2.4), 0.55, fc=F.BLUEL, ec=F.BLUE, lw=1.4, zorder=3))
    F.arrow(ax, 1.85, 2.4, 1.35, 2.4, color=F.BLUE, lw=2.2)
    txt(ax, 1.85, 1.51, "子宮左方転位（LUD）", color=F.BLUE, fs=11)
    # box + centered text at a smaller fs (not rbox's txt_lines): the string was wider
    # than the 2.9-wide box at fs10.3, so it spilled out past the rounded corners
    F.box(ax, 0.4, 0.7, 2.9, 0.62, F.GOLDL, F.GOLD, "除細動エネルギーは通常量でよい", tc=F.GOLD, fs=8.3, bold=False, lw=1.4)
    txt(ax, 1.85, 0.4, "母体＋胎児モニタ", color=F.GRAY, fs=11)

    # panel 2: hypothermia
    txt(ax, 5.55, 4.55, "低体温", color=F.TEAL, fs=14, bold=True)
    ax.add_patch(FancyBboxPatch((5.35, 2.55), 0.4, 1.55, boxstyle="round,pad=0.01,rounding_size=0.18",
                                 fc="white", ec=F.INK, lw=1.3, zorder=2))
    ax.add_patch(Rectangle((5.4, 2.6), 0.3, 0.85, fc=F.BLUEL, ec="none", zorder=3))
    ax.add_patch(Circle((5.55, 2.55), 0.28, fc=F.BLUEL, ec=F.INK, lw=1.3, zorder=3))
    F.arrow(ax, 6.05, 3.3, 5.95, 2.75, color=F.RED, lw=2.0)
    txt(ax, 6.5, 3.3, "復温を優先", color=F.RED, fs=11.5, bold=True, ha="left")
    txt(ax, 5.55, 1.75, "<30–32°Cでは\nショック・薬剤に反応しにくい", color=F.INK, fs=10.8)
    txt(ax, 5.55, 0.85, "重度（<30°C）は復温まで\nショック・薬剤を保留", color=F.RED, fs=10.8)

    # panel 3: LAST / electrolyte
    txt(ax, 9.15, 4.55, "LAST／電解質", color=F.ORANGE, fs=14, bold=True)
    ax.add_patch(Rectangle((8.75, 2.85), 0.8, 1.05, fc=F.ORANGEL, ec=F.ORANGE, lw=1.3, zorder=2))
    ax.plot([9.15, 9.15], [2.85, 2.35], color=F.GRAY, lw=1.6, zorder=2)
    txt(ax, 9.15, 4.05, "脂肪乳剤（ILE）", color=F.ORANGE, fs=11)
    txt(ax, 9.15, 1.75, "局所麻酔薬中毒\n→ 脂肪乳剤（ILE）", color=F.INK, fs=11)
    txt(ax, 9.15, 0.85, "電解質（K・Mg）\n異常を補正", color=F.INK, fs=11)

    F.save(fig, "f0805")


# ================================================================== 8.7 ===========
def f0807():
    fig, ax = canvas(4.8, 5.4, W=6, H=7)
    x, w = 0.7, 4.6
    nodes = [
        dict(title=None, lines=[("ショック/ペーシング後", F.INK)], fc="white", ec=F.INK, h=0.62, fs=12),
        dict(title=None, lines=[("12誘導ECG", F.GOLD)], fc=F.GOLDL, ec=F.GOLD, h=0.62, fs=13),
        dict(title="原因検索（H&T）", title_color=F.GOLD, w=5.4,
             lines=[("低酸素・循環血液量・電解質・低体温", F.INK), ("中毒・血栓・気胸・タンポナーデ", F.INK)],
             fc="white", ec=F.INK, h=1.45, fs=11, title_fs=13),
        dict(title=None, lines=[("再発予防：抗不整脈薬＋K・Mg補正", F.GOLD)], fc=F.GOLDL, ec=F.GOLD, h=0.62, fs=12),
        # h raised 0.95->1.30: the title + subtitle line didn't fit rbox's fixed
        # top-anchored offsets at 0.95, so "（皮膚熱傷に注意）" was pushed past the
        # bottom border (and the connector arrow struck through it)
        dict(title="皮膚・気道・意識のフォロー", title_color=F.INK,
             lines=[("（皮膚熱傷に注意）", F.RED)], fc="white", ec=F.INK, h=1.30, fs=11.5, title_fs=12.5),
        dict(title=None, lines=[("ROSC後管理／ICUへ", "#FFFFFF")], fc=F.TEAL, ec=F.TEAL, h=0.65, fs=13),
    ]
    _stack_flow(ax, x, 6.85, w, nodes, gap=0.22)
    F.save(fig, "f0807")

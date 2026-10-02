# -*- coding: utf-8 -*-
"""モニター心電図デックの全図を生成 → ../figs/*.png
使い方: python make_figs.py [fig_id ...]   （引数なしで全図）"""
import sys, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import ecglib as E
from figbase import (newfig, save, clean, T, box, rect, arrow, chip,
                     INK, GOLD, GOLDL, GOLDBG, TEAL, TEALD, RED, REDL, GRAY, MGRAY,
                     LGRAY, BLUE, BLUEL, ORANGE, ORANGEL, GREEN, GREENL, WHITE,
                     GRID_MAJOR)

REG = {}   # id -> function
def fig(idn):
    def deco(f): REG[idn] = f; return f
    return deco

# ============================================================
#  低レベル・ヘルパ
# ============================================================
def _lead_tag(ax, txt, x=0.02, y=0.90):
    ax.text(x, y, txt, transform=ax.transAxes, ha="left", va="center",
            fontsize=14, color=INK, fontproperties=None, zorder=7,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.25", fc=WHITE, ec=LGRAY, lw=1))

def _pt(ax, xp, yp, label, ytxt, color=INK, fs=12.5, ha="center", dx=0.0):
    """feature(xp,yp) の近くに縦気味の矢印＋ラベル(ytxtの高さ)。重なり回避のためx=xp+dx。"""
    xt = xp + dx
    arrow(ax, xt, ytxt, xp, yp, color=color, lw=1.5, ms=10)
    va = "bottom" if ytxt > yp else "top"
    T(ax, xt, ytxt + (0.04 if va=="bottom" else -0.04), label, size=fs, color=color, ha=ha, va=va)

def strip_axes(figsize=(9.8, 3.4)):
    fig_, ax = plt.subplots(figsize=figsize, dpi=200)
    fig_.patch.set_facecolor("white"); ax.set_facecolor("white")
    return fig_, ax

def compare(name, panels, ymin=-0.7, ymax=1.5, panelh=1.28, width=10.2,
            right_notes=True, padr=2.0):
    """panels: list of dict(label, t, v, color, notes(str), findings(list of (x,ytxt,yp,text,color)))
       縦に積む。左に誘導/名称ラベル、右の空白域に所見メモ(重なり回避)。"""
    n = len(panels)
    fig_, axes = plt.subplots(n, 1, figsize=(width, panelh*n), dpi=200)
    if n == 1: axes = [axes]
    for ax, p in zip(axes, panels):
        t, v = p["t"], p["v"]
        pymin, pymax = p.get("ymin", ymin), p.get("ymax", ymax)
        t0d, t1d = t[0], t[-1]
        E.ecg_grid(ax, t0d, t1d+padr, pymin, pymax)   # 右に空白の方眼を確保
        ax.plot(t, v, color=p.get("color", INK), lw=1.9, zorder=4,
                solid_capstyle="round", solid_joinstyle="round")
        # label chip (left, above trace)
        ax.text(0.006, 0.87, p["label"], transform=ax.transAxes, ha="left", va="center",
                fontsize=13.5, color=p.get("lcolor", INK), zorder=8,
                bbox=dict(boxstyle="round,pad=0.22", fc=WHITE, ec=p.get("lcolor", LGRAY), lw=1.2))
        if right_notes and p.get("notes"):
            ax.text(0.992, 0.5, p["notes"], transform=ax.transAxes, ha="right", va="center",
                    fontsize=12.5, color=p.get("ncolor", GRAY), zorder=8,
                    bbox=dict(boxstyle="round,pad=0.3", fc="#FBFBFB", ec=LGRAY, lw=0.9))
        for (xp, ytxt, yp, text, col) in p.get("findings", []):
            _pt(ax, xp, yp, text, ytxt, color=col, fs=11.5)
    fig_.subplots_adjust(left=0.03, right=0.985, top=0.98, bottom=0.02, hspace=0.30)
    save(fig_, name)

# ============================================================
#  第4章 正常波形
# ============================================================
@fig("fig_4_1_nsr")
def _():
    fig_, ax = strip_axes((9.8, 3.6))
    b = E.sinus(rate=72, t1=4.2, first=0.45)
    t, v = E.synth(b, 0, 4.2)
    E.draw(ax, t, v, ymin=-0.55, ymax=1.45, lw=2.0)
    _lead_tag(ax, "II 誘導 ・ 25 mm/s")
    rr = 60/72
    for k, bb in enumerate(b[:4]):
        r = bb["r"]
        _pt(ax, r-0.16, 0.16, "P", 0.62, color=GOLD, fs=13, dx=0)
        if k == 1:
            _pt(ax, r, 1.0, "QRS", 1.28, color=INK, fs=12)
            _pt(ax, r+0.34, 0.30, "T", 0.66, color=TEAL, fs=13)
    # regular RR bracket
    r0, r1 = b[1]["r"], b[2]["r"]
    ax.annotate("", xy=(r1, -0.42), xytext=(r0, -0.42),
                arrowprops=dict(arrowstyle="<->", color=TEAL, lw=1.6))
    T(ax, (r0+r1)/2, -0.52, "R-R 一定・PR 一定 0.16s", size=12, color=TEAL)
    save(fig_, "fig_4_1_nsr")

@fig("fig_4_2_normal_values")
def _():
    fig_, ax = strip_axes((9.8, 3.9))
    b = [E.beat(1.2, p_amp=0.18, r_amp=1.05, q=-0.08, s=-0.22, t_amp=0.35)]
    t, v = E.synth(b, 0.2, 2.6)
    E.draw(ax, t, v, ymin=-0.7, ymax=1.7, t0=0.2, t1=2.6, lw=2.2)
    r = 1.2
    _pt(ax, r-0.16, 0.18, "P 幅<0.12s・高<2.5mm", 0.95, color=GOLD, fs=12, dx=-0.28)
    _pt(ax, r-0.03, -0.08, "q 幅<0.04s・<R/4", -0.42, color=INK, fs=11.5, dx=-0.20)
    _pt(ax, r, 1.05, "QRS 幅<0.12s", 1.5, color=INK, fs=12.5, dx=0.12)
    _pt(ax, r+0.34, 0.35, "T 陽性(I・II・V3-6)", 0.98, color=TEAL, fs=12, dx=0.34)
    T(ax, 2.32, 1.35, "QTc上限の目安\n男≲0.45 / 女≲0.46s", size=12, color=RED, ha="center")
    save(fig_, "fig_4_2_normal_values")

@fig("fig_4_3_normal_stt")
def _():
    fig_, ax = strip_axes((9.8, 3.7))
    b = [E.beat(1.0, r_amp=1.0, t_amp=0.34, t_dur=0.18)]
    t, v = E.synth(b, 0.4, 1.9)
    E.draw(ax, t, v, ymin=-0.5, ymax=1.4, t0=0.4, t1=1.9, lw=2.3)
    r = 1.0
    jx = r + 0.06
    ax.plot([jx], [0.02], "o", color=RED, ms=7, zorder=8)
    _pt(ax, jx, 0.02, "J点", 0.5, color=RED, fs=13, dx=-0.10)
    ax.annotate("", xy=(r+0.20, 0.0), xytext=(jx, 0.0),
                arrowprops=dict(arrowstyle="-", color=TEAL, lw=3))
    _pt(ax, r+0.14, 0.0, "ST 等電位(偏位<1mm)", -0.34, color=TEAL, fs=12, dx=0.30)
    _pt(ax, r+0.34, 0.34, "T 非対称(緩→急)", 0.77, color=GOLD, fs=12, dx=0.28)
    T(ax, 1.72, 1.16, "aVR・V1 の T陰性は正常\n正常変異=早期再分極", size=11.5, color=GRAY, ha="center")
    save(fig_, "fig_4_3_normal_stt")

@fig("fig_4_4_monitor_normal")
def _():
    fig_, ax = strip_axes((9.8, 3.5))
    # respiratory sinus arrhythmia: vary RR
    rng = np.random.default_rng(0)
    beats = []; r = 0.4; phase = 0
    while r < 6.2:
        beats.append(E.beat(r))
        hr = 72 + 14*np.sin(2*np.pi*0.25*r)   # breathing modulation
        r += 60/hr
    t, v = E.synth(beats, 0, 6.2)
    E.draw(ax, t, v, ymin=-0.5, ymax=1.4, t0=0, t1=6.2, lw=1.8)
    _lead_tag(ax, "II ・ 25 mm/s ・ 10 mm/mV")
    ax.annotate("", xy=(1.9, -0.4), xytext=(0.5, -0.4),
                arrowprops=dict(arrowstyle="<->", color=TEAL, lw=1.6))
    T(ax, 1.2, -0.5, "吸気=R-R短縮", size=12, color=TEAL)
    ax.annotate("", xy=(4.4, -0.4), xytext=(2.6, -0.4),
                arrowprops=dict(arrowstyle="<->", color=GOLD, lw=1.6))
    T(ax, 3.5, -0.5, "呼気=R-R延長", size=12, color=GOLD)
    T(ax, 4.9, 1.16, "P波正常なら生理的変動\n(呼吸性洞性不整脈)", size=11.5, color=GRAY, ha="center")
    save(fig_, "fig_4_4_monitor_normal")

# ============================================================
#  第6章 異常波形
# ============================================================
@fig("fig_6_2_brady")
def _():
    panels = []
    # 洞徐脈 HR45
    b = E.sinus(rate=45, t1=4.6, first=0.5); t, v = E.synth(b, 0, 4.6)
    panels.append(dict(label="洞徐脈", t=t, v=v, notes="HR≈45 ・ P-QRS 1:1", lcolor=INK))
    # 洞停止
    b = [E.beat(0.5), E.beat(1.3), E.beat(3.4), E.beat(4.2)]  # long pause
    t, v = E.synth(b, 0, 4.6)
    panels.append(dict(label="洞停止/洞房ブロック", t=t, v=v, notes="P波が脱落→ポーズ",
                       findings=[(2.35, 1.05, 0.05, "P欠落", RED)]))
    # I度AVB PR long
    b = E.sinus(rate=68, t1=4.6, first=0.5, pr=0.30); t, v = E.synth(b, 0, 4.6)
    panels.append(dict(label="I度房室ブロック", t=t, v=v, notes="PR 一定に延長(>0.20s)"))
    # Mobitz I Wenckebach: PR increasing then drop
    beats = []
    seq = [0.14, 0.20, 0.28, None]  # PR values; None = dropped
    r = 0.5
    for cyc in range(2):
        for pr in seq:
            if pr is None:
                # dropped QRS: only P
                beats.append(E.beat(r, pr=0.16, p=True, qrs='none', r_amp=0.0,
                                    q=0, s=0, t_amp=0.0, p_amp=0.15))
                # represent dropped: a P with no QRS -> use special: add P only
                r += 0.5
            else:
                beats.append(E.beat(r, pr=pr)); r += 0.8
    t, v = E.synth(beats, 0, r)
    panels.append(dict(label="II度 Mobitz I", t=t, v=v, notes="PR漸増→QRS脱落(群拍)",
                       lcolor=GOLD))
    # Mobitz II: constant PR, sudden drop (3:2)
    beats = []; r = 0.5
    pattern = [1,1,0,1,1,0,1,1,0]
    for cond in pattern:
        if cond:
            beats.append(E.beat(r, pr=0.18)); r += 0.75
        else:
            beats.append(E.beat(r, pr=0.18, qrs='none', r_amp=0.0, q=0, s=0, t_amp=0.0)); r += 0.75
    t, v = E.synth(beats, 0, r)
    panels.append(dict(label="II度 Mobitz II", t=t, v=v, notes="PR一定・突然脱落", lcolor=INK))
    # complete AV block: P regular fast, QRS slow independent
    beats = []
    # P waves at 100/min (0.6s), QRS at 40/min (1.5s) independent
    rp = 0.35
    while rp < 4.6:
        beats.append(E.beat(rp, p=True, qrs='none', r_amp=0.0, q=0, s=0, t_amp=0.0, p_amp=0.16, pr=0)); rp += 0.6
    rq = 0.6
    while rq < 4.6:
        beats.append(E.beat(rq, p=False, qrs='wide', r_amp=0.9, qrs_dur=0.13, t_amp=0.35, t_inv=True)); rq += 1.5
    beats.sort(key=lambda x: x["r"]); t, v = E.synth(beats, 0, 4.6)
    panels.append(dict(label="III度(完全)", t=t, v=v, notes="房室解離：PとQRSが独立", lcolor=RED))
    compare("fig_6_2_brady", panels, panelh=1.12, width=10.4)

@fig("fig_6_3_narrow")
def _():
    panels = []
    b = E.sinus(rate=130, t1=3.4, first=0.3); t, v = E.synth(b, 0, 3.4)
    panels.append(dict(label="洞頻脈", t=t, v=v, notes="先行Pあり・規則的 130", lcolor=INK))
    # AF
    rng = np.random.default_rng(2); r = 0.3; bts = []
    while r < 3.4:
        bts.append(E.beat(r, p=False)); r += 60/rng.uniform(90, 160)
    t, v = E.synth(bts, 0, 3.4, base_fn=E.af_base(0.055))
    panels.append(dict(label="心房細動", t=t, v=v, notes="P波なし・RR絶対不整", lcolor=INK))
    # Aflutter sawtooth, 2:1
    bts = []; r = 0.5
    while r < 3.4:
        bts.append(E.beat(r, p=False)); r += 0.4  # ventricular ~150
    t, v = E.synth(bts, 0, 3.4, base_fn=E.flutter_base(300, 0.16))
    panels.append(dict(label="心房粗動", t=t, v=v, notes="鋸歯状F波・2:1(心室≈150)", lcolor=GOLD))
    # AVNRT: fast regular, no visible P
    b = E.sinus(rate=185, t1=3.4, first=0.25, p=False, s=-0.28); t, v = E.synth(b, 0, 3.4)
    panels.append(dict(label="発作性上室頻拍", t=t, v=v, notes="P見えず・規則的 185", lcolor=INK))
    compare("fig_6_3_narrow", panels, panelh=1.2, width=10.4, ymin=-0.6, ymax=1.35)

@fig("fig_6_4_wide")
def _():
    panels = []
    # VT monomorphic wide regular + independent P (AV dissociation) + a capture/fusion
    bts = []; r = 0.3
    while r < 3.6:
        bts.append(E.beat(r, p=False, qrs='vt', r_amp=1.1, qrs_dur=0.15, t_amp=0.5, t_inv=True, t_center=0.32))
        r += 0.40
    # sprinkle independent P
    rp = 0.15
    pbeats = []
    while rp < 3.6:
        pbeats.append(E.beat(rp, p=True, qrs='none', r_amp=0, q=0, s=0, t_amp=0, p_amp=0.10, pr=0)); rp += 0.63
    allb = sorted(bts+pbeats, key=lambda x: x["r"])
    t, v = E.synth(allb, 0, 3.6)
    panels.append(dict(label="心室頻拍 (VT)", t=t, v=v, notes="幅広・規則的＋房室解離", lcolor=RED,
                       ymin=-0.8, ymax=1.4))
    # SVT with aberrancy: RBBB-like wide, preceding P, regular
    bts = []; r = 0.3
    while r < 3.6:
        bts.append(E.beat(r, pr=0.14, qrs_gauss=[(-0.03,-0.06,0.010),(0.0,0.5,0.012),(0.03,-0.2,0.012),(0.07,0.75,0.016)],
                          qrs_dur=0.13, t_amp=-0.25, t_center=0.30)); r += 0.42
    t, v = E.synth(bts, 0, 3.6)
    panels.append(dict(label="SVT+変行伝導", t=t, v=v, notes="脚ブロック型・先行P・規則的", lcolor=INK,
                       ymin=-0.7, ymax=1.4))
    # WPW: short PR + delta
    bts = E.sinus(rate=78, t1=3.6, first=0.4, pr=0.10, qrs='delta', r_amp=0.9, qrs_dur=0.13, t_amp=-0.2, t_inv=True)
    t, v = E.synth(bts, 0, 3.6)
    panels.append(dict(label="WPW", t=t, v=v, notes="PR短縮<0.12・δ波", lcolor=GOLD,
                       ymin=-0.6, ymax=1.35,
                       findings=[(bts[1]["r"]-0.05, 0.7, 0.25, "δ波", GOLD)]))
    compare("fig_6_4_wide", panels, panelh=1.4, width=10.4)

@fig("fig_6_5_pac_pvc")
def _():
    fig_, ax = strip_axes((10.2, 3.8))
    beats = []
    # sinus baseline with a PAC (early abnormal P + narrow QRS) and a PVC (wide, no P)
    times = [0.5, 1.3, 2.0, 2.9, 3.7, 4.5, 5.3]
    for i, r in enumerate(times):
        if i == 2:  # PAC: early, abnormal P shape
            beats.append(E.beat(r-0.12, pr=0.14, p_amp=0.22, p_dur=0.08))
        elif i == 4:  # PVC wide no P
            beats.append(E.beat(r-0.10, p=False, qrs='pvc', r_amp=1.4, qrs_dur=0.15, t_amp=0.55, t_inv=True, t_center=0.34))
        else:
            beats.append(E.beat(r))
    t, v = E.synth(beats, 0, 6.0)
    E.draw(ax, t, v, ymin=-0.9, ymax=1.7, t0=0, t1=6.0, lw=1.9)
    _lead_tag(ax, "II 誘導")
    _pt(ax, 2.0-0.24, 0.24, "PAC：異所性P先行・幅狭・非代償性", 1.15, color=TEAL, fs=12, dx=0.7)
    _pt(ax, 4.5-0.10, 1.4, "PVC：P波なし・幅広・T逆向き・代償性", 1.6, color=RED, fs=12, dx=-0.2)
    save(fig_, "fig_6_5_pac_pvc")

@fig("fig_6_6_lethal")
def _():
    panels = []
    t, v = E.vf_trace(0, 3.4);
    panels.append(dict(label="心室細動 (VF)", t=t, v=v, notes="波形バラバラ / 除細動可",
                       lcolor=RED, ncolor=RED, ymin=-1.0, ymax=1.0))
    b = []; r = 0.2
    while r < 3.4:
        b.append(E.beat(r, p=False, qrs='vt', r_amp=1.1, qrs_dur=0.15, t_amp=0.5, t_inv=True)); r += 0.30
    t, v = E.synth(b, 0, 3.4)
    panels.append(dict(label="無脈性VT", t=t, v=v, notes="VT波形だが無脈 / 除細動可",
                       lcolor=RED, ncolor=RED, ymin=-0.8, ymax=1.4))
    b = E.sinus(rate=50, t1=3.4, first=0.4, r_amp=0.7, qrs_dur=0.11); t, v = E.synth(b, 0, 3.4)
    panels.append(dict(label="無脈性電気活動 (PEA)", t=t, v=v, notes="波形あるが脈なし / CPR・可逆原因",
                       lcolor=GOLD, ncolor=INK))
    t, v = E.asystole_trace(0, 3.4)
    panels.append(dict(label="心静止 (asystole)", t=t, v=v, notes="平坦・電気活動なし / 非除細動",
                       lcolor=INK, ncolor=INK, ymin=-0.5, ymax=0.5))
    compare("fig_6_6_lethal", panels, panelh=1.3, width=10.4)

@fig("fig_6_7_bbb")
def _():
    # V1 and V6 for RBBB and LBBB
    panels = []
    # RBBB V1: rsR' (M)
    b = [E.beat(0.6+0.85*k, p=True, pr=0.16, p_amp=0.10,
                qrs_gauss=[(-0.02,0.18,0.010),(0.01,-0.25,0.010),(0.05,0.9,0.016)],
                qrs_dur=0.13, st=-0.03, t_amp=-0.22, t_center=0.30) for k in range(4)]
    t, v = E.synth(b, 0, 4.0)
    panels.append(dict(label="RBBB ・ V1", t=t, v=v, notes="rsR′(M型・兎耳)", lcolor=BLUE,
                       ymin=-0.6, ymax=1.3))
    # RBBB V6: wide slurred S
    b = [E.beat(0.6+0.85*k, p_amp=0.10,
                qrs_gauss=[(-0.02,-0.05,0.010),(0.0,0.85,0.012),(0.05,-0.35,0.030)],
                qrs_dur=0.13, t_amp=0.28) for k in range(4)]
    t, v = E.synth(b, 0, 4.0)
    panels.append(dict(label="RBBB ・ V6", t=t, v=v, notes="幅広い slur した S波", lcolor=BLUE,
                       ymin=-0.7, ymax=1.2))
    # LBBB V1: wide QS
    b = [E.beat(0.6+0.85*k, p_amp=0.10,
                qrs_gauss=[(0.0,-0.9,0.032)], qrs_dur=0.14, t_amp=0.3) for k in range(4)]
    t, v = E.synth(b, 0, 4.0)
    panels.append(dict(label="LBBB ・ V1", t=t, v=v, notes="幅広い陰性 QS", lcolor=GOLD,
                       ymin=-1.2, ymax=0.7))
    # LBBB V6: broad notched R, discordant ST-T
    b = [E.beat(0.6+0.85*k, p_amp=0.10,
                qrs_gauss=[(-0.02,0.55,0.020),(0.03,0.85,0.020)], qrs_dur=0.14,
                st=-0.05, t_amp=-0.28, t_center=0.32) for k in range(4)]
    t, v = E.synth(b, 0, 4.0)
    panels.append(dict(label="LBBB ・ V6", t=t, v=v, notes="幅広ノッチR・q欠如・ST-T逆方向", lcolor=GOLD,
                       ymin=-0.6, ymax=1.4))
    compare("fig_6_7_bbb", panels, panelh=1.25, width=10.4)

@fig("fig_6_9_electrolyte")
def _():
    panels = []
    # hyperK stage a: tented T
    b = E.sinus(rate=70, t1=3.4, first=0.4, p_amp=0.12, t_amp=0.75, t_dur=0.09, t_center=0.32)
    t, v = E.synth(b, 0, 3.4)
    panels.append(dict(label="高K (5.5-6.5)", t=t, v=v, notes="尖鋭・基部の狭いテント状T", lcolor=GOLD,
                       ymin=-0.5, ymax=1.4))
    # hyperK advanced: sine wave-ish (wide QRS merging T, no P)
    b = E.sinus(rate=70, t1=3.4, first=0.4, p=False, qrs='wide', qrs_dur=0.18, r_amp=0.9,
                t_amp=0.7, t_dur=0.16, t_center=0.30)
    t, v = E.synth(b, 0, 3.4)
    panels.append(dict(label="高K (>8-9)", t=t, v=v, notes="P消失・QRS-T融合=サインカーブ→VF前兆",
                       lcolor=RED, ncolor=RED, ymin=-0.6, ymax=1.4))
    # hypoK: flat T + U
    b = E.sinus(rate=68, t1=3.4, first=0.4, t_amp=0.10, t_dur=0.14, u=True, u_amp=0.22, u_center=0.52, st=-0.03)
    t, v = E.synth(b, 0, 3.4)
    panels.append(dict(label="低K", t=t, v=v, notes="T平低・U波増高(QT見かけ延長=QU)", lcolor=BLUE,
                       ymin=-0.5, ymax=1.3,
                       findings=[(b[1]["r"]+0.52, 0.6, 0.22, "U波", BLUE)]))
    # hypoCa: long QT (T pushed out)
    b = E.sinus(rate=66, t1=3.4, first=0.4, t_center=0.50, t_amp=0.32, t_dur=0.18)
    t, v = E.synth(b, 0, 3.4)
    panels.append(dict(label="低Ca", t=t, v=v, notes="ST延長でQT延長(T波形は保たれる)", lcolor=TEALD,
                       ymin=-0.5, ymax=1.3))
    compare("fig_6_9_electrolyte", panels, panelh=1.25, width=10.4)

# ============================================================
#  第8章 特殊波形
# ============================================================
@fig("fig_8_1_pacemaker")
def _():
    fig_, ax = strip_axes((9.8, 3.4))
    b = [E.beat(0.6+0.9*k, p=False, spike=1.5, spike_at=-0.02,
                qrs_gauss=[(0.02,-0.9,0.030)], qrs_dur=0.15, t_amp=0.4, t_center=0.34) for k in range(4)]
    t, v = E.synth(b, 0, 4.2)
    E.draw(ax, t, v, ymin=-1.2, ymax=1.7, t0=0, t1=4.2, lw=1.9)
    _lead_tag(ax, "心室ペーシング (VVI様)")
    _pt(ax, 0.6-0.02, 1.5, "ペーシングスパイク", 1.62, color=RED, fs=12, dx=0.55)
    _pt(ax, 0.6+0.05, -0.8, "幅広QRS(LBBB様)・T逆向き", -1.05, color=INK, fs=11.5, dx=0.7)
    T(ax, 3.4, 1.4, "AAI=心房 / VVI=心室 / DDD=両者", size=11.5, color=GRAY, ha="center")
    save(fig_, "fig_8_1_pacemaker")

@fig("fig_8_3_transplant")
def _():
    fig_, ax = strip_axes((9.8, 3.4))
    beats = []
    # donor P + QRS (drives), plus independent recipient P (non-conducted)
    r = 0.55
    while r < 4.4:
        beats.append(E.beat(r, p=True, pr=0.16, p_amp=0.16)); r += 0.85
    rp = 0.30
    while rp < 4.4:
        beats.append(E.beat(rp, p=True, qrs='none', r_amp=0, q=0, s=0, t_amp=0, p_amp=0.09, pr=0)); rp += 0.72
    beats.sort(key=lambda x: x["r"]); t, v = E.synth(beats, 0, 4.4)
    E.draw(ax, t, v, ymin=-0.5, ymax=1.4, t0=0, t1=4.4, lw=1.9)
    _lead_tag(ax, "移植心", y=0.98)
    _pt(ax, 0.55-0.16, 0.16, "ドナーP(QRSを規定)", 0.75, color=GOLD, fs=12, dx=-0.1)
    _pt(ax, 0.30, 0.09, "レシピエントP(非伝導・独立)", 0.55, color=TEAL, fs=11.5, dx=1.0)
    T(ax, 3.6, 1.16, "脱神経→アトロピン無効・レート応答鈍", size=11.5, color=GRAY, ha="center")
    save(fig_, "fig_8_3_transplant")

@fig("fig_8_6_special")
def _():
    panels = []
    b = E.sinus(rate=76, t1=3.2, first=0.4, pr=0.10, qrs='delta', r_amp=0.95, qrs_dur=0.13, t_amp=-0.2, t_inv=True)
    t, v = E.synth(b, 0, 3.2)
    panels.append(dict(label="WPW", t=t, v=v, notes="短いPR＋δ波", lcolor=GOLD, ymin=-0.6, ymax=1.3))
    # Brugada coved ST elevation V1-2
    b = [E.beat(0.5+0.85*k, p_amp=0.10, r_amp=0.3,
                qrs_gauss=[(-0.02,0.1,0.010),(0.0,0.35,0.012),(0.04,0.25,0.016)],
                qrs_dur=0.11, st=0.28, t_amp=-0.22, t_center=0.30) for k in range(3)]
    t, v = E.synth(b, 0, 3.2)
    panels.append(dict(label="Brugada ・ V1-2", t=t, v=v, notes="coved型ST上昇＋陰性T", lcolor=RED, ymin=-0.5, ymax=1.0))
    # early repolarization: J point notch + slight ST elevation
    b = [E.beat(0.5+0.8*k, p_amp=0.12, r_amp=1.0,
                qrs_gauss=[(-0.028,-0.05,0.008),(0.0,1.0,0.011),(0.03,-0.10,0.012),(0.055,0.16,0.010)],
                qrs_dur=0.09, st=0.10, t_amp=0.4, t_center=0.34) for k in range(4)]
    t, v = E.synth(b, 0, 3.2)
    panels.append(dict(label="早期再分極", t=t, v=v, notes="J点上昇(notch/slur)", lcolor=TEAL, ymin=-0.5, ymax=1.4))
    # takotsubo: deep symmetric T inversion + long QT
    b = E.sinus(rate=72, t1=3.2, first=0.4, t_amp=0.55, t_inv=True, t_center=0.44, t_dur=0.20)
    t, v = E.synth(b, 0, 3.2)
    panels.append(dict(label="たこつぼ", t=t, v=v, notes="広範な深い陰性T＋QT延長", lcolor=BLUE, ymin=-1.0, ymax=1.2))
    compare("fig_8_6_special", panels, panelh=1.25, width=10.4)

# ============================================================
#  模式図(schematic)ヘルパ
# ============================================================
def canvas(w=9.8, h=5.2, xlim=(0, 10), ylim=(0, 6)):
    fig_, ax = plt.subplots(figsize=(w, h), dpi=200)
    fig_.patch.set_facecolor("white"); ax.set_facecolor("white")
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect("auto")
    clean(ax)
    return fig_, ax

def timeline(name, events, highlight=(), w=10.6, h=4.4):
    """events: [(year, label)]。水平ゴールド矢印に上下交互で箱。"""
    fig_, ax = canvas(w, h, (0, 10), (0, 6))
    y0 = 3.0
    arrow(ax, 0.3, y0, 9.7, y0, color=GOLD, lw=3, ms=22)
    n = len(events)
    xs = np.linspace(1.0, 9.0, n)
    for i, ((yr, lab), x) in enumerate(zip(events, xs)):
        up = (i % 2 == 0)
        hy = 4.9 if up else 1.1
        hl = (yr in highlight) or (i in highlight)
        fc = GOLDBG if hl else "#F5F7F9"
        ec = GOLD if hl else LGRAY
        tc = INK
        ax.plot([x, x], [y0, hy + (-0.55 if up else 0.55)], color=ec, lw=1.4, zorder=2)
        ax.plot([x], [y0], "o", color=ec, ms=9, zorder=4)
        box(ax, x-1.05, hy-0.55, 2.1, 1.1, fc, ec=ec, lw=1.6, round=0.12)
        T(ax, x, hy+0.24, yr, size=15, color=(GOLD if hl else TEAL))
        T(ax, x, hy-0.20, lab, size=11.5, color=tc)
    save(fig_, name)

def flow_vertical(name, steps, w=8.8, h=5.6, box_w=6.2):
    """steps: [(text, fc, ec, tc)] 縦フロー。"""
    fig_, ax = canvas(w, h, (0, 10), (0, 6))
    n = len(steps); top = 5.7; bot = 0.4
    ys = np.linspace(top, bot, n)
    bh = min(0.9, (top-bot)/n*0.66)
    cx = 5.0
    for i, (txt, fc, ec, tc) in enumerate(steps):
        y = ys[i]
        box(ax, cx-box_w/2, y-bh/2, box_w, bh, fc, ec=ec, lw=1.8, txt=txt, tc=tc, fs=14, round=0.10)
        if i < n-1:
            arrow(ax, cx, y-bh/2-0.02, cx, ys[i+1]+bh/2+0.02, color=GRAY, lw=2.2, ms=15)
    save(fig_, name)

# ---------- 第1章 歴史 ----------
@fig("fig_1_1_prehistory")
def _():
    timeline("fig_1_1_prehistory",
             [("1842", "Matteucci\nカエル心の活動電流"),
              ("1856", "Kölliker&Müller\n心拍同期の電流"),
              ("1872", "Lippmann\n毛細管電位計"),
              ("1887", "Waller\nヒト体表で初記録")],
             highlight=("1887",))

@fig("fig_1_4_monitoring")
def _():
    timeline("fig_1_4_monitoring",
             [("1950s", "オシロスコープ\n床上モニタ"),
              ("1961", "Holter\n長時間記録"),
              ("1962", "CCU\n常時監視"),
              ("1970s", "テレメトリ\n無線監視"),
              ("1980s", "ST自動解析"),
              ("1990s-", "デジタル化\nネットワーク")],
             highlight=("1961", "1962"), w=11.2)

@fig("fig_1_2_einthoven")
def _():
    fig_, ax = canvas(10.0, 5.2, (0, 10), (0, 6))
    # galvanometer (left)
    box(ax, 0.4, 1.6, 2.6, 2.8, "#F5F7F9", ec=TEAL, lw=1.6, round=0.08)
    T(ax, 1.7, 4.1, "弦線電流計", size=13, color=TEAL)
    ax.plot([0.8, 1.2, 1.6, 2.0, 2.4], [3.0, 3.5, 2.6, 3.4, 2.9], color=INK, lw=2)  # string trace
    T(ax, 1.7, 2.0, "石英線の振れを\n光学的に拡大記録", size=10.5, color=GRAY)
    # triangle (right)
    RA = (5.3, 4.6); LA = (9.1, 4.6); LL = (7.2, 1.3)
    tri = plt.Polygon([RA, LA, LL], closed=True, fill=False, ec=GOLD, lw=2.4, zorder=3)
    ax.add_patch(tri)
    for (px, py, lab) in [(RA[0]-0.1, RA[1]+0.25, "右手 −"), (LA[0]+0.1, LA[1]+0.25, "左手 +"), (LL[0], LL[1]-0.35, "左足 +")]:
        T(ax, px, py, lab, size=12, color=INK, ha="center")
        ax.plot([px if lab=='左足 +' else (RA[0] if 'RA' else 0)], [0], alpha=0)
    for p in (RA, LA, LL):
        ax.plot([p[0]], [p[1]], "o", color=INK, ms=9, zorder=5)
    T(ax, 7.2, 4.85, "I", size=16, color=GOLD)
    T(ax, 5.9, 2.9, "II", size=16, color=GOLD)
    T(ax, 8.5, 2.9, "III", size=16, color=GOLD)
    T(ax, 7.2, 3.15, "Einthoven\n三角形", size=12, color=TEAL)
    T(ax, 5.0, 0.5, "1901 弦線電流計   1902-03 記録確立   1924 ノーベル賞", size=12.5, color=INK, ha="center")
    save(fig_, "fig_1_2_einthoven")

@fig("fig_1_3_twelve_lead")
def _():
    fig_, ax = canvas(10.2, 5.2, (0, 10), (0, 6))
    box(ax, 3.3, 4.7, 3.4, 0.9, GOLDBG, ec=GOLD, lw=1.8, round=0.1,
        txt="双極肢誘導 I・II・III", tc=INK, fs=14)
    T(ax, 5.0, 4.4, "Einthoven (1900年代)", size=10.5, color=GRAY)
    # two branches
    box(ax, 0.5, 2.6, 4.0, 1.1, BLUEL, ec=BLUE, lw=1.6, round=0.1,
        txt="Wilson 中心端子 (1934)\n→ 単極胸部 V1–V6 (6)", tc=INK, fs=12.5)
    box(ax, 5.5, 2.6, 4.0, 1.1, "#EAF3E6", ec=GREEN, lw=1.6, round=0.1,
        txt="Goldberger (1942)\n→ 増幅単極肢 aVR/aVL/aVF (3)", tc=INK, fs=12.5)
    arrow(ax, 4.3, 4.6, 2.5, 3.75, color=GRAY, lw=2, ms=14)
    arrow(ax, 5.7, 4.6, 7.5, 3.75, color=GRAY, lw=2, ms=14)
    box(ax, 3.0, 0.5, 4.0, 1.2, GOLD, ec=GOLD, lw=1.8, round=0.1,
        txt="12誘導 標準化\n(1940年代) 3+6+3", tc=WHITE, fs=15)
    arrow(ax, 2.5, 2.55, 4.3, 1.75, color=GRAY, lw=2, ms=14)
    arrow(ax, 7.5, 2.55, 5.7, 1.75, color=GRAY, lw=2, ms=14)
    save(fig_, "fig_1_3_twelve_lead")

# ---------- 第2章 成り立ち ----------
@fig("fig_2_1_action_potential")
def _():
    fig_, ax = canvas(10.0, 5.2, (0, 10), (-95, 40))
    tt = np.linspace(0, 10, 600)
    # build a ventricular AP shape
    ap = np.full_like(tt, -88.0)
    ap += 120*np.clip((tt-1.0)/0.06, 0, 1)*np.exp(-np.clip(tt-1.06,0,None)*0.0)  # phase0 up
    # simpler piecewise
    ap = np.full_like(tt, -88.0)
    for i, x in enumerate(tt):
        if x < 1.0: ap[i] = -88
        elif x < 1.12: ap[i] = -88 + (118)*((x-1.0)/0.12)   # 0 upstroke to +30
        elif x < 1.5: ap[i] = 30 - 20*((x-1.12)/0.38)        # 1 notch to +10
        elif x < 4.2: ap[i] = 10 - 8*((x-1.5)/2.7)           # 2 plateau ~ +2
        elif x < 5.6: ap[i] = 2 - 90*((x-4.2)/1.4)           # 3 repol to -88
        else: ap[i] = -88
    ax.plot(tt, ap, color=INK, lw=2.6, zorder=4)
    ax.axhline(-88, color=LGRAY, lw=1, ls="--")
    # phase labels
    for (x, y, s, c) in [(1.06, -20, "0", GOLD), (1.3, 22, "1", INK), (2.7, 8, "2", GOLD),
                         (4.9, -35, "3", INK), (6.6, -80, "4", INK)]:
        T(ax, x, y, s, size=17, color=c)
    T(ax, 1.06, -46, "INa↑\n急速脱分極", size=10.5, color=GOLD, ha="center")
    T(ax, 2.7, 26, "Ca²+↑ ⇔ K+↑ プラトー", size=11, color=GOLD, ha="center")
    T(ax, 4.9, -12, "K+↑ 再分極", size=10.5, color=INK, ha="center")
    T(ax, 7.2, -80, "静止(IK1)", size=10.5, color=GRAY, ha="center")
    # inset: fast vs slow
    T(ax, 8.9, 18, "速い反応=心筋(Na)\n遅い反応=結節(Ca)\n=4相自然脱分極→自動能", size=10.5, color=TEAL, ha="center")
    save(fig_, "fig_2_1_action_potential")

@fig("fig_2_2_conduction")
def _():
    fig_, ax = canvas(10.0, 5.4, (0, 10), (0, 6))
    # stylized heart outline
    from matplotlib.patches import FancyBboxPatch
    hz = plt.Polygon([(2.0,5.0),(4.6,5.3),(5.2,3.0),(4.3,0.7),(2.6,0.5),(1.2,1.6),(1.3,3.8)],
                     closed=True, fill=True, fc="#FBF6EC", ec=LGRAY, lw=1.4, zorder=1)
    ax.add_patch(hz)
    nodes = [(3.6,4.7,"洞結節 SA"),(3.2,3.4,"房室結節 AV"),(3.0,2.7,"His束"),
             (2.4,1.7,"左脚"),(3.7,1.7,"右脚"),(2.9,0.9,"Purkinje")]
    pts = [(n[0],n[1]) for n in nodes]
    order = [0,1,2]  # SA->AV->His
    for a,b in [(0,1),(1,2),(2,3),(2,4),(3,5),(4,5)]:
        arrow(ax, pts[a][0], pts[a][1], pts[b][0], pts[b][1], color=GOLD, lw=2.0, ms=12)
    for (x,y,lab) in nodes:
        ax.plot([x],[y],"o", color=TEAL, ms=8, zorder=5)
        T(ax, x-0.05, y+0.02, "", size=1)
    T(ax, 3.6,4.95,"洞結節 SA", size=11, color=INK, ha="center")
    T(ax, 4.35,3.5,"房室結節 AV(遅延)", size=10.5, color=RED, ha="left")
    T(ax, 3.05,2.4,"His", size=10.5, color=INK, ha="center")
    T(ax, 1.9,1.5,"左脚", size=10, color=INK); T(ax, 3.95,1.5,"右脚", size=10, color=INK)
    T(ax, 2.9,0.55,"Purkinje", size=10, color=INK, ha="center")
    # right table: speed & automaticity
    tx = 6.2
    box(ax, tx, 0.5, 3.5, 5.0, "#F5F7F9", ec=LGRAY, lw=1.4, round=0.06)
    T(ax, tx+1.75, 5.05, "伝導速度・自動能", size=13, color=TEAL)
    rows = [("SA・AV結節", "≈0.05 m/s (遅)"),
            ("His-Purkinje", "≈2–4 m/s (速)"),
            ("心室筋", "≈0.3–1 m/s"),
            ("", ""),
            ("固有調律 SA", "60–100/分"),
            ("房室接合部", "40–60/分"),
            ("His-Purkinje", "20–40/分")]
    for i,(a,b) in enumerate(rows):
        yy = 4.55 - i*0.58
        if a:
            T(ax, tx+0.2, yy, a, size=11, color=INK, ha="left")
            T(ax, tx+3.3, yy, b, size=11, color=(GOLD if "m/s" in b and "遅" in b else INK), ha="right")
    T(ax, tx+1.75, 2.78, "AV遅延=PR時間", size=11, color=RED)
    save(fig_, "fig_2_2_conduction")

@fig("fig_2_3_vector")
def _():
    fig_, ax = canvas(10.0, 5.2, (0, 10), (0, 6))
    cx, cy = 3.3, 3.0
    rng = np.random.default_rng(4)
    for _ in range(26):
        ang = rng.uniform(-0.5, 0.9); L = rng.uniform(0.4, 0.9)
        arrow(ax, cx-0.2+rng.uniform(-0.6,0.6), cy+rng.uniform(-0.9,0.9),
              cx-0.2+L*np.cos(ang), cy+L*np.sin(ang)+rng.uniform(-0.9,0.9),
              color=LGRAY, lw=1.2, ms=8)
    arrow(ax, cx-0.2, cy, cx+2.4, cy+1.4, color=GOLD, lw=4, ms=24)
    T(ax, cx+2.5, cy+1.7, "心起電力ベクトル(総和)", size=12, color=GOLD, ha="center")
    T(ax, cx-0.7, cy-1.4, "微小ダイポールの総和", size=11, color=GRAY, ha="center")
    # QRS loop
    lx, ly = 7.6, 3.1
    th = np.linspace(0, 2*np.pi, 200)
    loop_x = lx + 1.2*np.cos(th)*(0.6+0.4*np.cos(th))
    loop_y = ly + 1.0*np.sin(th)*(0.6+0.4*np.cos(th))
    ax.plot(loop_x, loop_y, color=TEAL, lw=2.2)
    arrow(ax, lx, ly, lx+1.5, ly+0.7, color=INK, lw=2, ms=14)
    T(ax, lx, ly-1.6, "QRSベクトルループ\n前額面平均=平均電気軸", size=11, color=INK, ha="center")
    save(fig_, "fig_2_3_vector")

@fig("fig_2_4_projection")
def _():
    fig_, ax = canvas(10.0, 5.2, (0, 10), (0, 6))
    cx, cy = 4.6, 3.1
    # lead axes (I horizontal, II +60 down-right, III +120)
    axes_def = [(0, "I", GOLD), (-60, "II", GOLD), (-120, "III", GOLD)]
    import math
    for deg, lab, col in axes_def:
        r = math.radians(deg)
        ax.plot([cx-2.6*math.cos(r), cx+2.6*math.cos(r)],
                [cy-2.6*math.sin(r), cy+2.6*math.sin(r)], color=LGRAY, lw=1.6)
        T(ax, cx+2.85*math.cos(r), cy+2.85*math.sin(r), lab, size=13, color=col)
    # heart vector at -30 deg
    vr = math.radians(-35)
    vx, vy = cx+2.0*math.cos(vr), cy+2.0*math.sin(vr)
    arrow(ax, cx, cy, vx, vy, color=GOLD, lw=3.5, ms=20)
    # projection onto II axis
    r2 = math.radians(-60)
    proj = ( (vx-cx)*math.cos(r2) + (vy-cy)*math.sin(r2) )
    px, py = cx+proj*math.cos(r2), cy+proj*math.sin(r2)
    ax.plot([vx, px], [vy, py], color=INK, lw=1.4, ls="--")
    ax.plot([px], [py], "o", color=TEAL, ms=8)
    T(ax, cx, cy+0.35, "心ベクトル", size=11.5, color=GOLD, ha="center")
    T(ax, 8.6, 2.0, "誘導軸への射影\n= その誘導の波形振幅", size=12, color=INK, ha="center")
    T(ax, 8.6, 4.4, "軸に平行→大\n直交→等電位(≈0)", size=11, color=TEAL, ha="center")
    save(fig_, "fig_2_4_projection")

@fig("fig_2_5_lead_ii")
def _():
    import math
    fig_, ax = canvas(10.0, 5.2, (0, 10), (0, 6))
    cx, cy = 3.2, 3.0
    circ = plt.Circle((cx, cy), 2.2, fill=False, ec=LGRAY, lw=1.4); ax.add_patch(circ)
    # II axis +60 (down-right in ECG convention → draw downward)
    for deg, lab in [(-60, "II 軸 +60°")]:
        r = math.radians(deg)
        ax.plot([cx, cx+2.2*math.cos(r)], [cy, cy+2.2*math.sin(r)], color=TEAL, lw=2.4)
        T(ax, cx+2.4*math.cos(r), cy+2.4*math.sin(r)-0.2, lab, size=12, color=TEAL)
    # mean QRS axis +50, P axis +60 (nearly parallel to II)
    for deg, lab, col in [(-50, "平均QRS軸", GOLD), (-62, "P軸", INK)]:
        r = math.radians(deg)
        arrow(ax, cx, cy, cx+1.9*math.cos(r), cy+1.9*math.sin(r), color=col, lw=3, ms=16)
    T(ax, cx, cy+2.5, "前額面", size=11, color=GRAY, ha="center")
    T(ax, 3.2, 0.4, "P軸・QRS軸 ∥ II軸 → P・QRSが大きく陽性", size=12, color=GOLD, ha="center")
    # small II strip on the right
    b = E.sinus(rate=72, t1=2.4, first=0.3)
    t, v = E.synth(b, 0, 2.4)
    axr = fig_.add_axes([0.66, 0.30, 0.31, 0.42])
    E.draw(axr, t, v, ymin=-0.4, ymax=1.3, lw=1.8)
    axr.text(0.02, 0.86, "II 誘導", transform=axr.transAxes, fontsize=11, color=INK)
    save(fig_, "fig_2_5_lead_ii")

@fig("fig_2_6_signal_chain")
def _():
    fig_, ax = canvas(11.0, 4.8, (0, 11), (0, 6))
    steps = [("① 電極-皮膚", "Ag/AgCl", BLUEL, BLUE),
             ("② 差動増幅", "CMRR ↑", "#EAF3E6", GREEN),
             ("③ 基準電極", "RLD(右下肢)", "#F5F7F9", GRAY),
             ("④ フィルタ", "監視/診断 切替", GOLDBG, GOLD),
             ("⑤ 表示・記録", "25mm/s", BLUEL, TEAL)]
    x = 0.4; bw = 1.98; gap = 0.14; y = 2.6; bh = 1.6
    cxs = []
    for i,(t1,t2,fc,ec) in enumerate(steps):
        bx = x + i*(bw+gap)
        box(ax, bx, y, bw, bh, fc, ec=ec, lw=1.8, txt=t1+"\n"+t2, tc=INK, fs=11.5, round=0.08)
        cxs.append(bx+bw/2)
        if i>0:
            arrow(ax, cxs[i-1]+bw/2, y+bh/2, bx, y+bh/2, color=GRAY, lw=2, ms=13)
    T(ax, 5.5, 4.9, "電極から波形まで", size=14, color=TEAL, ha="center")
    T(ax, 5.5, 1.75, "フィルタ 監視 0.5–40Hz ／ 診断・ST 0.05–150Hz ・ 校正 25mm/s・1mV=10mm",
      size=11, color=INK, ha="center")
    T(ax, 5.5, 1.05, "監視モードはSTを歪める → 虚血監視は診断/STモードへ", size=11.5, color=RED, ha="center")
    save(fig_, "fig_2_6_signal_chain")

# ---------- ラベル付き1拍 ----------
@fig("fig_3_4_complex")
def _():
    fig_, ax = strip_axes((9.8, 4.0))
    b = [E.beat(1.2, p_amp=0.18, r_amp=1.05, q=-0.09, s=-0.24, t_amp=0.34, u=True, u_amp=0.09, u_center=0.56)]
    t, v = E.synth(b, 0.2, 2.6)
    E.draw(ax, t, v, ymin=-0.7, ymax=1.6, t0=0.2, t1=2.6, lw=2.3)
    r = 1.2
    ax.axhline(0.0, color=GRAY, lw=1, ls="--", zorder=1)
    _pt(ax, r-0.16, 0.18, "P 心房脱分極", 0.9, color=GOLD, fs=12.5, dx=-0.30)
    _pt(ax, r, 1.05, "QRS 心室脱分極", 1.48, color=INK, fs=12.5, dx=0.0)
    _pt(ax, r+0.34, 0.34, "T 心室再分極", 0.98, color=TEAL, fs=12.5, dx=0.30)
    _pt(ax, r+0.56, 0.09, "U波", 0.55, color=GRAY, fs=11.5, dx=0.24)
    jx = r+0.075
    ax.plot([jx],[0.02],"o", color=RED, ms=6, zorder=8)
    _pt(ax, jx, 0.02, "J点", -0.42, color=RED, fs=12, dx=0.14)
    T(ax, 0.55, -0.55, "基線(TP/PR)", size=11, color=GRAY, ha="center")
    T(ax, 2.25, 1.3, "心房再分極(Ta)は\nQRSに埋没", size=10.5, color=GRAY, ha="center")
    save(fig_, "fig_3_4_complex")

@fig("fig_3_5_intervals")
def _():
    fig_, ax = strip_axes((10.0, 4.2))
    b = [E.beat(1.3, p_amp=0.17, r_amp=1.0, q=-0.08, s=-0.22, t_amp=0.32)]
    t, v = E.synth(b, 0.2, 2.9)
    E.draw(ax, t, v, ymin=-0.7, ymax=1.7, t0=0.2, t1=2.9, lw=2.2)
    r = 1.3
    # interval bands
    def band(x0, x1, y, color, label):
        ax.add_patch(plt.Rectangle((x0, y-0.06), x1-x0, 0.12, color=color, alpha=0.9, zorder=2))
        ax.annotate("", xy=(x1, y+0.3), xytext=(x0, y+0.3),
                    arrowprops=dict(arrowstyle="<->", color=color, lw=1.6))
        T(ax, (x0+x1)/2, y+0.5, label, size=11.5, color=color)
    band(r-0.16, r-0.03, 1.5, BLUE, "PR 0.12–0.20s")
    band(r-0.03, r+0.06, -0.5, TEAL, "QRS <0.12s")
    band(r-0.03, r+0.42, 1.15, GOLD, "QT")
    T(ax, 2.45, 0.6, "QTc=QT/√RR (Bazett)\n= QT/RR^(1/3) (Fridericia)\n目安 男≲0.45 / 女≲0.46s", size=10.5, color=INK, ha="center")
    save(fig_, "fig_3_5_intervals")

@fig("fig_5_3_st")
def _():
    fig_, ax = strip_axes((9.8, 4.0))
    b = [E.beat(1.2, r_amp=1.0, st=-0.12, t_amp=0.28)]
    t, v = E.synth(b, 0.4, 2.2)
    E.draw(ax, t, v, ymin=-0.7, ymax=1.4, t0=0.4, t1=2.2, lw=2.3)
    r = 1.2
    ax.axhline(0.0, color=GRAY, lw=1.2, ls="--", zorder=1)
    T(ax, 0.65, 0.08, "等電位基準(PR)", size=10.5, color=GRAY, ha="left")
    jx = r+0.075
    ax.plot([jx],[0.0],"o", color=RED, ms=6, zorder=8)
    _pt(ax, jx, 0.0, "J点", 0.5, color=RED, fs=12, dx=-0.12)
    for off, lab in [(0.06, "J+60"), (0.08, "J+80")]:
        mx = jx+off
        yy = np.interp(mx, t, v)
        ax.plot([mx],[yy],"o", color=BLUE, ms=6, zorder=8)
        ax.plot([mx,mx],[0,yy], color=BLUE, lw=1.2, ls=":")
    _pt(ax, jx+0.08, np.interp(jx+0.08,t,v), "J+60/80で計測", -0.45, color=BLUE, fs=11.5, dx=0.4)
    T(ax, 0.85, 1.15, "水平/下降型\nST低下≧1mm=有意", size=11, color=RED, ha="center")
    # trend inset
    axr = fig_.add_axes([0.70, 0.62, 0.27, 0.32])
    xx = np.linspace(0,10,50); yy = -0.2 - 0.6/(1+np.exp(-(xx-6)))
    axr.plot(xx, yy, color=RED, lw=2); axr.axhline(0, color=LGRAY, lw=1)
    axr.set_xticks([]); axr.set_yticks([])
    for s in axr.spines.values(): s.set_color(LGRAY)
    axr.text(0.5, 1.06, "ST トレンド", transform=axr.transAxes, ha="center", fontsize=10, color=INK)
    save(fig_, "fig_5_3_st")

# ---------- 第7章 対応フロー ----------
@fig("fig_7_1_principle")
def _():
    flow_vertical("fig_7_1_principle", [
        ("① 患者を診る：脈・血圧・SpO₂・EtCO₂・意識", GOLDBG, GOLD, INK),
        ("② 脈なし？ → CPR / ACLS へ", REDL, RED, RED),
        ("③ 脈あり：安定か 不安定か を判断", BLUEL, BLUE, INK),
        ("④ 不安定=即対応 / 安定=12誘導で分類", "#F5F7F9", GRAY, INK),
        ("⑤ 原因検索(電解質・低酸素・薬剤・虚血)＋応援・ABC", "#EAF3E6", GREEN, INK),
    ], h=5.6)

@fig("fig_7_3_tachy")
def _():
    fig_, ax = canvas(10.4, 5.4, (0, 10), (0, 6))
    box(ax, 3.6, 5.0, 2.8, 0.8, GOLDBG, ec=GOLD, lw=1.8, txt="脈あり頻脈", tc=INK, fs=14, round=0.1)
    # unstable branch
    box(ax, 0.3, 2.8, 4.2, 1.5, REDL, ec=RED, lw=1.8, round=0.08,
        txt="不安定(低血圧・意識障害\n胸痛・急性心不全)\n→ 同期電気ショック", tc=INK, fs=11.5)
    T(ax, 2.4, 2.4, "narrow規則50-100J / AF120-200J / wide100J", size=9.5, color=RED, ha="center")
    # stable branch
    box(ax, 5.5, 2.8, 4.2, 1.5, BLUEL, ec=BLUE, lw=1.8, round=0.08,
        txt="安定 → QRS幅で分岐", tc=INK, fs=12.5)
    arrow(ax, 4.4, 4.95, 2.4, 4.35, color=RED, lw=2, ms=14)
    arrow(ax, 5.6, 4.95, 7.6, 4.35, color=BLUE, lw=2, ms=14)
    box(ax, 5.5, 1.3, 2.0, 1.1, "#F5F7F9", ec=GRAY, lw=1.4, round=0.08,
        txt="narrow規則\n迷走→アデノシン\n6→12mg", tc=INK, fs=10)
    box(ax, 7.7, 1.3, 2.0, 1.1, "#F5F7F9", ec=GRAY, lw=1.4, round=0.08,
        txt="AF/AFL\nレート/リズム管理", tc=INK, fs=10)
    arrow(ax, 6.5, 2.75, 6.5, 2.45, color=GRAY, lw=1.8, ms=12)
    arrow(ax, 8.0, 2.75, 8.7, 2.45, color=GRAY, lw=1.8, ms=12)
    T(ax, 5.0, 0.5, "アデノシンは不規則調律には使わない", size=11, color=RED, ha="center")
    save(fig_, "fig_7_3_tachy")

@fig("fig_7_4_vf")
def _():
    import math
    fig_, ax = canvas(9.6, 5.6, (0, 10), (0, 6))
    cx, cy, R = 5.0, 3.3, 2.15
    steps = [("質の高いCPR\n中断を最小", GOLDBG, GOLD),
             ("除細動 二相性\n120–200J", REDL, RED),
             ("直後2分間 CPR", "#EAF3E6", GREEN),
             ("リズム確認\n継続なら再ショック", BLUEL, BLUE)]
    angs = [90, 0, -90, 180]
    pos = []
    for i in range(4):
        a = math.radians(angs[i])
        x, y = cx+R*math.cos(a), cy+R*math.sin(a)
        pos.append((x, y))
        box(ax, x-1.05, y-0.5, 2.1, 1.0, steps[i][1], ec=steps[i][2], lw=1.8,
            txt=steps[i][0], tc=INK, fs=11, round=0.1)
    for i in range(4):
        a = pos[i]; b = pos[(i+1) % 4]
        ax.annotate("", xy=b, xytext=a,
                    arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=2.2,
                                    connectionstyle="arc3,rad=-0.26",
                                    shrinkA=28, shrinkB=28, mutation_scale=16))
    box(ax, cx-0.9, cy-0.4, 1.8, 0.8, WHITE, ec=RED, lw=1.6,
        txt="VF / 無脈性VT", tc=RED, fs=11.5, round=0.14)
    T(ax, cx, 0.4, "アドレナリン1mg q3-5分・難治にアミオダロン300→150mg・5H5T是正", size=10.5, color=INK, ha="center")
    save(fig_, "fig_7_4_vf")

# ---------- 第6章 読影フロー ----------
@fig("fig_6_1_read_order")
def _():
    fig_, ax = canvas(9.2, 5.6, (0, 10), (0, 6))
    steps = [("① レート", "300÷大マス / 6秒×10"),
             ("② 調律", "規則性・P-QRS関係"),
             ("③ P波", "有無・向き(IIで陽性)"),
             ("④ PR間隔", "0.12–0.20秒"),
             ("⑤ QRS幅", "<0.12秒"),
             ("⑥ ST / T", "上昇低下・T向き"),
             ("⑦ QT / QTc", "Bazett・目安<0.44s")]
    top, bot = 5.6, 0.5
    ys = np.linspace(top, bot, len(steps))
    for i,(a,b) in enumerate(steps):
        y = ys[i]
        box(ax, 1.0, y-0.32, 2.8, 0.64, GOLDBG if i in (0,1) else "#F5F7F9",
            ec=GOLD if i in (0,1) else LGRAY, lw=1.5, txt=a, tc=INK, fs=13, round=0.12)
        T(ax, 4.2, y, b, size=11.5, color=GRAY, ha="left")
        if i < len(steps)-1:
            arrow(ax, 2.4, y-0.33, 2.4, ys[i+1]+0.33, color=GRAY, lw=1.8, ms=12)
    T(ax, 5.0, 5.9, "まず律 → 次に波 → 最後に間隔と再分極", size=12.5, color=TEAL, ha="center")
    save(fig_, "fig_6_1_read_order")

# ---------- hero (title) ----------
@fig("fig_hero")
def _():
    fig_, ax = plt.subplots(figsize=(11.0, 2.2), dpi=200)
    fig_.patch.set_facecolor("white"); ax.set_facecolor("white")
    b = E.sinus(rate=72, t1=7.5, first=0.4)
    t, v = E.synth(b, 0, 7.5)
    E.ecg_grid(ax, 0, 7.5, -0.5, 1.4, minor=False)
    ax.plot(t, v, color=GOLD, lw=2.6, zorder=4, solid_capstyle="round")
    ax.set_xlim(0, 7.5); ax.set_ylim(-0.5, 1.4)
    save(fig_, "fig_hero")

# ---------- 電極配置 ----------
def _torso(ax):
    body = plt.Polygon([(3.2,5.2),(6.8,5.2),(7.3,4.4),(6.7,1.0),(5.6,0.4),
                        (4.4,0.4),(3.3,1.0),(2.7,4.4)],
                       closed=True, fc="#FBF9F4", ec=LGRAY, lw=1.6, zorder=1)
    ax.add_patch(body)
    # neck/shoulders hint
    ax.add_patch(plt.Circle((5.0,5.6), 0.5, fc="#FBF9F4", ec=LGRAY, lw=1.4, zorder=1))

def _elec(ax, x, y, lab, col, tcol=INK, side="right"):
    ax.add_patch(plt.Circle((x,y), 0.17, fc=col, ec=INK, lw=1.2, zorder=6))
    dx = 0.32 if side=="right" else -0.32
    ha = "left" if side=="right" else "right"
    T(ax, x+dx, y, lab, size=11.5, color=tcol, ha=ha)

@fig("fig_3_1_three_lead")
def _():
    import math
    fig_, ax = canvas(9.6, 5.4, (0, 10), (0, 6)); ax.set_xlim(0,10); ax.set_ylim(0,6)
    _torso(ax)
    RA=(3.4,4.8); LA=(6.6,4.8); LL=(6.0,1.2)
    _elec(ax,*RA,"RA (右手)  白", WHITE, side="left")
    _elec(ax,*LA,"LA (左手)  黒", "#333333", tcol=INK, side="right")
    _elec(ax,*LL,"LL (左足)  赤", RED, side="right")
    tri = plt.Polygon([RA,LA,LL], closed=True, fill=False, ec=GOLD, lw=2.2, ls="-", zorder=4)
    ax.add_patch(tri)
    T(ax,5.0,4.95,"I", size=14, color=GOLD)
    T(ax,4.3,2.9,"II", size=14, color=GOLD)
    T(ax,6.55,2.9,"III", size=14, color=GOLD)
    box(ax, 0.2, 0.3, 3.0, 1.2, "#F5F7F9", ec=LGRAY, lw=1.2, round=0.08,
        txt="I=LA−RA (0°)\nII=LL−RA (+60°)\nIII=LL−LA (+120°)", tc=INK, fs=11)
    T(ax, 8.4, 3.0, "AHA: RA白/LA黒/LL赤\nIEC: R赤/L黄/F緑", size=11, color=GRAY, ha="center")
    T(ax, 8.4, 1.2, "II=心軸に沿い\nP波最大=基本", size=11.5, color=GOLD, ha="center")
    save(fig_, "fig_3_1_three_lead")

@fig("fig_3_2_five_lead")
def _():
    fig_, ax = canvas(9.6, 5.4, (0, 10), (0, 6)); ax.set_xlim(0,10); ax.set_ylim(0,6)
    _torso(ax)
    _elec(ax, 3.4,4.8, "RA 白", WHITE, side="left")
    _elec(ax, 6.6,4.8, "LA 黒", "#333333", side="right")
    _elec(ax, 3.5,1.2, "RL 緑", GREEN, side="left")
    _elec(ax, 6.5,1.2, "LL 赤", RED, side="right")
    # V positions along chest
    vy = 3.4
    vxs = [4.55,4.75,5.05,5.35,5.7,6.05]
    for i,vx in enumerate(vxs):
        ax.add_patch(plt.Circle((vx, vy-0.1*i), 0.09, fc=LGRAY, ec=GRAY, lw=1, zorder=5))
    # V5 highlighted (C electrode)
    ax.add_patch(plt.Circle((vxs[4], vy-0.1*4), 0.16, fc=GOLD, ec=INK, lw=1.3, zorder=6))
    T(ax, vxs[4]+0.35, vy-0.4, "C=V5", size=12, color=GOLD, ha="left")
    T(ax, 5.2, 3.8, "V1→V6", size=10.5, color=GRAY, ha="center")
    box(ax, 0.3, 2.9, 3.3, 1.5, GOLDBG, ec=GOLD, lw=1.4, round=0.08,
        txt="四肢4電極→I/II/III\n・aVR/aVL/aVF (6)\n＋C=V5 → 計7誘導", tc=INK, fs=11)
    T(ax, 8.3, 3.4, "V5=第5肋間\n前腋窩線", size=11.5, color=INK, ha="center")
    T(ax, 8.6, 0.65, "II＋V5併用\nIIで調律・V5で虚血", size=11.5, color=GOLD, ha="center")
    save(fig_, "fig_3_2_five_lead")

@fig("fig_3_6_rate")
def _():
    fig_, ax = strip_axes((10.0, 4.2))
    b = E.sinus(rate=75, t1=3.2, first=0.4); t, v = E.synth(b, 0, 3.2)
    E.draw(ax, t, v, ymin=-0.5, ymax=1.5, t0=0, t1=3.2, lw=1.9)
    # 300-rule numbers between R's (every 0.2s big square)
    T(ax, 1.6, 1.42, "300則: 300/大マス数 → 300・150・100・75・60・50", size=11.5, color=GOLD, ha="center")
    # 6-second bracket
    ax.annotate("", xy=(3.0, -0.4), xytext=(0.2, -0.4),
                arrowprops=dict(arrowstyle="<->", color=TEAL, lw=1.6))
    T(ax, 1.6, -0.52, "6秒法: (6秒内QRS)×10  ← 不整脈向き", size=11.5, color=TEAL)
    save(fig_, "fig_3_6_rate")

@fig("fig_3_6_rate_panel")
def _():
    # 補助: 心拍数 手法パネル(表示は fig_3_6_rate を使用)
    pass

@fig("fig_3_7_axis")
def _():
    import math
    fig_, ax = canvas(9.6, 5.4, (0, 10), (0, 6)); ax.set_aspect("equal")
    cx, cy, R = 3.4, 3.0, 2.2
    ax.add_patch(plt.Circle((cx,cy), R, fill=False, ec=LGRAY, lw=1.4))
    # axes: ECG angle θ, screen point = (cos θ, -sin θ) so +90=down
    for deg, lab in [(0,"I 0°"),(60,"II +60°"),(120,"III +120°"),
                     (-150,"aVR"),(-30,"aVL"),(90,"aVF +90°")]:
        r = math.radians(deg)
        x2,y2 = cx+R*math.cos(r), cy-R*math.sin(r)
        ax.plot([cx*2-x2, x2],[cy*2-y2, y2], color=LGRAY, lw=1.2)
        T(ax, cx+(R+0.35)*math.cos(r), cy-(R+0.35)*math.sin(r), lab, size=11, color=INK)
    # normal axis wedge -30..+90 (teal)
    from matplotlib.patches import Wedge
    ax.add_patch(Wedge((cx,cy), R, -90, 30, width=R*0.9, fc=TEAL, alpha=0.12))
    T(ax, cx, cy-0.2, "正常軸\n−30〜+90°", size=11, color=TEALD, ha="center")
    box(ax, 6.3, 0.6, 3.4, 4.4, "#F5F7F9", ec=LGRAY, lw=1.3, round=0.06)
    T(ax, 8.0, 4.6, "I・aVF で4象限", size=12.5, color=TEAL)
    rows = [("I(+) aVF(+)","正常", INK),
            ("I(+) aVF(−)","左軸疑い(IIで確認)", GOLD),
            ("I(−) aVF(+)","右軸偏位", BLUE),
            ("I(−) aVF(−)","北西(不定)", GRAY)]
    for i,(a,b,c) in enumerate(rows):
        yy = 3.9 - i*0.85
        T(ax, 6.55, yy, a, size=11.5, color=c, ha="left")
        T(ax, 6.55, yy-0.32, b, size=11, color=INK, ha="left")
    save(fig_, "fig_3_7_axis")

# ---------- 第5章 ----------
@fig("fig_5_2_leads")
def _():
    fig_, ax = canvas(10.2, 5.4, (0, 10), (0, 6))
    # top: 3 territories -> leads
    terr = [("前壁中隔 LAD","V1–V4", BLUEL, BLUE),
            ("側壁 LCx","I・aVL・V5–6", "#EAF3E6", GREEN),
            ("下壁 RCA","II・III・aVF", GOLDBG, GOLD)]
    for i,(a,b,fc,ec) in enumerate(terr):
        bx = 0.5 + i*3.15
        box(ax, bx, 4.3, 2.9, 1.3, fc, ec=ec, lw=1.6, round=0.08, txt=a+"\n"+b, tc=INK, fs=12)
    T(ax, 5.1, 5.8, "冠灌流域 と 監視誘導", size=12.5, color=TEAL, ha="center")
    # bottom: sensitivity bars
    data = [("V5",75,GRAY),("V4",61,GRAY),("II",33,GRAY),
            ("II+V5",80,GOLD),("V4+V5",90,TEAL),("II+V4+V5",96,GREEN)]
    x0 = 2.3; scale = 0.062; ytop = 3.4
    for i,(lab,val,col) in enumerate(data):
        yy = ytop - i*0.52
        ax.add_patch(plt.Rectangle((x0, yy-0.16), val*scale, 0.32, fc=col, ec="none", zorder=3))
        T(ax, x0-0.15, yy, lab, size=11.5, color=INK, ha="right")
        T(ax, x0+val*scale+0.15, yy, f"{val}%", size=11.5, color=col, ha="left")
    T(ax, 8.6, 3.2, "術中ST検出感度\n(London 1988)", size=11, color=GRAY, ha="center")
    T(ax, 5.1, 0.25, "標準は II+V5(≈80%)・V4追加で更に向上・3誘導では不足", size=11.5, color=GOLD, ha="center")
    save(fig_, "fig_5_2_leads")

@fig("fig_5_5_artifact")
def _():
    rng = np.random.default_rng(11)
    def base(rate=75, t1=3.2):
        b = E.sinus(rate=rate, t1=t1, first=0.3); return E.synth(b, 0, t1)
    panels = []
    # 電気メス
    t,v = base(); mask = ((t>1.0)&(t<2.2)).astype(float)
    v = v + mask*(0.55*np.sin(2*np.pi*90*t) + rng.normal(0,0.28,size=t.shape))
    panels.append(dict(label="電気メス", t=t, v=v, notes="高振幅ノイズ・通電に同期",
                       ymin=-1.2, ymax=1.8))
    # シバリング
    t,v = base(); v = v + 0.07*np.sin(2*np.pi*9*t) + rng.normal(0,0.03,size=t.shape)
    panels.append(dict(label="シバリング/振戦", t=t, v=v, notes="細かい揺れ・下をQRSが行進",
                       ymin=-0.5, ymax=1.4))
    # 50/60Hz
    t,v = base(); v = v + 0.06*np.sin(2*np.pi*50*t)
    panels.append(dict(label="50/60Hz 交流", t=t, v=v, notes="規則的な細かい鋸歯・電源由来",
                       ymin=-0.5, ymax=1.4))
    # 体動
    t,v = base(); rw = np.cumsum(rng.normal(0,0.08,size=t.shape)); rw -= rw.mean()
    v = v + 0.9*np.interp(t, t, rw)/max(1e-6,np.abs(rw).max())
    panels.append(dict(label="体動", t=t, v=v, notes="大きく不規則・動作に一致",
                       ymin=-1.2, ymax=1.6))
    # 接触不良
    t,v = base(); v = v + 0.35*np.sin(2*np.pi*0.5*t)
    drop = (t>1.6)&(t<2.2); v = np.where(drop, 0.2*np.sin(2*np.pi*0.5*t), v)
    panels.append(dict(label="電極接触不良", t=t, v=v, notes="基線漂動・信号途絶(1誘導)",
                       ymin=-0.8, ymax=1.4))
    # 胸骨圧迫
    t = np.linspace(0,3.2,1600); v = np.zeros_like(t)
    for rr in np.arange(0.3, 3.2, 0.58):
        v += 0.7*np.exp(-((t-rr)**2)/(2*0.05**2))
    panels.append(dict(label="胸骨圧迫", t=t, v=v, notes="圧迫レートに一致・幅広い規則的振れ",
                       ymin=-0.4, ymax=1.3))
    compare("fig_5_5_artifact", panels, panelh=1.15, width=10.6, padr=2.6)

@fig("fig_5_7_rhythm")
def _():
    fig_, ax = canvas(10.4, 5.4, (0, 10), (0, 6))
    cols = ["刺激","自律神経","心電図反応","対処"]
    xs = [0.4, 3.0, 5.4, 8.0]
    ws = [2.5, 2.3, 2.5, 1.9]
    T(ax, 5.2, 5.7, "術中の刺激 → 自律神経 → 調律変化", size=13, color=TEAL, ha="center")
    for x,w,c in zip(xs,ws,cols):
        box(ax, x, 4.7, w, 0.7, TEAL, ec=TEAL, lw=1, txt=c, tc=WHITE, fs=12, round=0.1)
    rows = [("挿管・浅麻酔・疼痛","交感 ↑","洞頻脈・高血圧・PVC","鎮痛/麻酔深度", RED),
            ("気腹・腸間膜牽引","迷走 ↑","洞徐脈・房室ブロック","送気/牽引を解除", GOLD),
            ("眼球圧迫(眼心反射)","三叉-迷走","高度徐脈・洞停止","中止＋アトロピン", RED),
            ("オピオイド","迷走 ↑","徐脈","減量/アトロピン", INK),
            ("抗コリン薬","交感優位","頻脈","経過観察", INK)]
    for i,(a,b,c,d,cc) in enumerate(rows):
        yy = 4.05 - i*0.72
        for x,w,txt,al in zip(xs,ws,[a,b,c,d],["left","center","left","center"]):
            fc = "#FFF6F4" if cc==RED else "#FBFBFB"
            box(ax, x, yy-0.30, w, 0.6, fc, ec=LGRAY, lw=0.8, round=0.06)
            T(ax, x+(0.12 if al=="left" else w/2), yy, txt, size=10.5,
              color=(cc if txt in (c,) else INK), ha=al)
    save(fig_, "fig_5_7_rhythm")

# ---------- 第6章 虚血部位 ----------
@fig("fig_6_8_ischemia")
def _():
    fig_, ax = canvas(10.2, 5.4, (0, 10), (0, 6))
    terr = [("下壁","II・III・aVF\n右冠動脈", GOLDBG, GOLD),
            ("前壁中隔","V1–V4\nLAD", BLUEL, BLUE),
            ("側壁","I・aVL・V5–6\nLCx", "#EAF3E6", GREEN)]
    for i,(a,b,fc,ec) in enumerate(terr):
        bx = 0.5 + i*3.15
        box(ax, bx, 3.9, 2.9, 1.5, fc, ec=ec, lw=1.6, round=0.08, txt=a+"\n"+b, tc=INK, fs=12)
    T(ax, 5.1, 5.7, "虚血の部位対応 と ST/T 変化", size=13, color=TEAL, ha="center")
    # 3 mini waveforms
    defs = [("ST上昇(貫壁)", dict(st=0.30, t_amp=0.3), RED, 0.09),
            ("ST低下(需要型)", dict(st=-0.18, t_amp=0.28), GOLD, 0.42),
            ("冠性T(陰性T)", dict(t_amp=0.5, t_inv=True, t_center=0.40), BLUE, 0.75)]
    for i,(lab,kw,col,fx) in enumerate(defs):
        axm = fig_.add_axes([0.08+ i*0.31, 0.10, 0.26, 0.30])
        b=[E.beat(1.0, r_amp=1.0, **kw)]; t,v=E.synth(b,0.5,1.6)
        E.draw(axm, t,v, ymin=-0.7, ymax=1.4, t0=0.5,t1=1.6, lw=2.0, grid=True)
        axm.set_title(lab, fontsize=11, color=col, loc="center")
    T(ax, 5.1, 3.35, "術中は需要型の心内膜下虚血が多く、水平型ST低下・T変化が主体 → II・V5で監視",
      size=11, color=RED, ha="center")
    save(fig_, "fig_6_8_ischemia")

# ---------- 第8章 小児 ----------
@fig("fig_8_5_peds")
def _():
    fig_, ax = canvas(9.8, 5.2, (0, 10), (0, 6))
    T(ax, 3.0, 5.7, "年齢別 正常心拍数(目安/分)", size=13, color=TEAL, ha="center")
    rows = [("新生児 0–1か月","100–160"),("乳児 1–12か月","100–150"),
            ("幼児 1–3歳","90–140"),("未就学 3–6歳","80–120"),
            ("学童 6–12歳","70–110"),("思春期 12歳–","60–100")]
    for i,(a,b) in enumerate(rows):
        yy = 5.0 - i*0.72
        fc = GOLDBG if i==0 else "#FBFBFB"
        box(ax, 0.4, yy-0.30, 3.7, 0.6, fc, ec=LGRAY, lw=0.9, round=0.06)
        T(ax, 0.6, yy, a, size=11.5, color=INK, ha="left")
        T(ax, 3.9, yy, b, size=11.5, color=GOLD, ha="right")
    box(ax, 5.0, 0.7, 4.6, 4.2, "#F5F7F9", ec=LGRAY, lw=1.3, round=0.06)
    T(ax, 7.3, 4.5, "小児モニタの要点", size=12.5, color=TEAL)
    notes = ["・右室優位 → V1でR優勢","・V1–V3のT波陰転は正常","・成人電極は重なりやすい",
             "・アーチファクトに注意","・出典で幅あり=目安として","・施設のPALS版に合わせる"]
    for i,n in enumerate(notes):
        T(ax, 5.3, 3.9 - i*0.52, n, size=11.5, color=INK, ha="left")
    save(fig_, "fig_8_5_peds")

# ============================================================
if __name__ == "__main__":
    ids = sys.argv[1:]
    if not ids: ids = list(REG.keys())
    for i in ids:
        if i in REG:
            REG[i](); print("saved", i)
        else:
            print("!! unknown", i)

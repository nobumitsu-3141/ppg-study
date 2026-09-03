#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""論文用の図を作る。

設計方針（投稿先の規定と査読対策から決めたもの）
------------------------------------------------
1. **白黒で読めること**が絶対条件。Journal of Anesthesia は購読経路（無料）でも
   印刷カラーに EUR 950 を課金する。よって系列の区別は【線種・マーカー形状・
   直接ラベル】が担い、色は冗長な補助にとどめる。色を落としても情報は失われない。
2. 色は色覚多様性に配慮した Okabe-Ito 系（#0072B2 / #D55E00 / #009E73）。
   隣接ペアのCVD分離を検証済み（最悪 ΔE 11.0・deutan）。
3. 2軸グラフは作らない。ΔPWTT と ΔΔT% は「較正点からの相対変化(%)」に揃えて
   1本の軸に載せる。
4. 目盛り・グリッドは後退させ、データを最前面に置く。

出力
----
    figs/fig1_flow.(pdf|png)   症例フロー
    figs/fig2_premise.(pdf|png) 主結果: 前提検証
    figs/fig3_quality.(pdf|png) 測定品質と陽性対照
    figs/fig4_accuracy.(pdf|png) 副次: 精度（Bland-Altman）

使い方
------
    python scripts/07_figures.py
        全図
    python scripts/07_figures.py --only 2 3
        図2と図3のみ
    python scripts/07_figures.py --dpi 600
        投稿用の解像度
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src.models import _deltas, premise_by_case  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FEAT = DATA / "features"
FIGS = ROOT / "figs"
MIN_WINDOWS = 12

# --- 系列の見た目（色は冗長・線種とマーカーが本体） ---
SERIES = [
    {"color": "#0072B2", "ls": "-",  "marker": "o"},
    {"color": "#D55E00", "ls": "--", "marker": "s"},
    {"color": "#009E73", "ls": ":",  "marker": "^"},
]
INK = "#1a1a1a"
MUTED = "#6b6b6b"
FAINT = "#c8c8c8"


def style() -> None:
    plt.rcParams.update({
        "figure.dpi": 110,
        "savefig.bbox": "tight",
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8,
        "axes.edgecolor": MUTED,
        "axes.linewidth": 0.6,
        "axes.labelcolor": INK,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.frameon": False,
        "legend.fontsize": 7,
        "lines.linewidth": 1.2,
        "grid.color": FAINT,
        "grid.linewidth": 0.5,
    })


def load_cases(min_windows: int = MIN_WINDOWS) -> list[dict]:
    """03_run_analysis.py と同じ規則でキャッシュから症例を組み立てる。"""
    demo = pd.read_csv(DATA / "cases.csv", encoding="utf-8-sig").set_index("caseid")
    cases = []
    for meta_p in sorted(FEAT.glob("case_*_meta.json")):
        try:
            meta = json.loads(meta_p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if meta.get("v") != 3:
            continue
        cid = meta["caseid"]
        csv_p = FEAT / f"case_{cid}.csv"
        if not csv_p.exists():
            continue
        try:
            df = pd.read_csv(csv_p)
        except Exception:
            continue
        if len(df) < min_windows or "si" not in df.columns:
            continue
        if cid not in demo.index:
            continue
        h_cm = float(demo["height"].get(cid, np.nan))
        if not np.isfinite(h_cm) or h_cm < 100:
            continue
        cases.append({
            "caseid": cid, "height": h_cm / 100.0,
            "age": float(demo["age"].get(cid, np.nan)),
            "device": meta.get("device", "?"),
            "t0": df["t0"].to_numpy(float) if "t0" in df else np.arange(len(df)) * 60.0,
            "windows": {k: df[k].to_numpy(float)
                        for k in ["pwtt", "si", "ri", "hr", "map", "co_ref"]},
        })
    return cases


def _int_yticks(ax) -> None:
    """症例数の軸は整数のみにする。"""
    from matplotlib.ticker import MaxNLocator
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))


def _save(fig, name: str, dpi: int) -> None:
    FIGS.mkdir(exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(FIGS / f"{name}.{ext}", dpi=dpi)
    plt.close(fig)
    print(f"  → figs/{name}.pdf / .png")


# ---------------------------------------------------------------- 図1
def fig1_flow(cases: list[dict], dpi: int) -> None:
    """症例フロー。数値は SAP §1.1 の実測値。"""
    n_final = len(cases)
    steps = [
        ("VitalDB cases", "6,388"),
        ("With PPG, ECG, arterial line\nand a continuous CO track", "874"),
        (f"Analysed\n(≥{MIN_WINDOWS} valid 60-s windows)", f"{n_final:,}"),
    ]
    drops = ["No PPG 231 · no ECG 33 · no arterial line 2,743\n· no CO track 5,395 (overlapping)",
             "Insufficient valid windows"]

    fig, ax = plt.subplots(figsize=(4.4, 3.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    ys = [8.6, 5.2, 1.8]
    for (label, n), y in zip(steps, ys):
        ax.add_patch(plt.Rectangle((0.6, y - 0.85), 5.5, 1.7, fill=False,
                                   edgecolor=INK, linewidth=0.8))
        ax.text(0.9, y + 0.28, label, va="center", ha="left", fontsize=7.5, color=INK)
        ax.text(0.9, y - 0.45, f"n = {n}", va="center", ha="left",
                fontsize=8.5, color=INK, fontweight="bold")
    for y0, y1, d in zip(ys[:-1], ys[1:], drops):
        ax.annotate("", xy=(3.3, y1 + 0.85), xytext=(3.3, y0 - 0.85),
                    arrowprops=dict(arrowstyle="-|>", color=INK, linewidth=0.8))
        ax.text(6.4, (y0 + y1) / 2, "Excluded:\n" + d, va="center", ha="left",
                fontsize=6.3, color=MUTED)
    _save(fig, "fig1_flow", dpi)


# ---------------------------------------------------------------- 図2
def fig2_premise(cases: list[dict], dpi: int) -> None:
    """主結果。(a) 代表症例の時系列 (b) 症例内r²分布 (c) 係数分布。"""
    diag = premise_by_case(cases)
    per = pd.DataFrame(diag["per_case"])

    # 代表症例は「症例内r²が中央値に最も近い症例」= 恣意的な選択を避ける
    r2 = per["r2"].to_numpy(float)
    med = np.nanmedian(r2)
    pick = per.iloc[[int(np.nanargmin(np.abs(r2 - med)))]]["caseid"].iloc[0]
    case = next(c for c in cases if c["caseid"] == pick)

    fig = plt.figure(figsize=(7.6, 2.8))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.2, 1, 1], hspace=0.5, wspace=0.55)

    # (a) 較正点からの相対変化。PWTT と ΔT は変動の桁が違うので、
    #     2軸グラフにはせず上下の小倍数にする（各段1系列なので凡例は不要）。
    d = _deltas(case)
    t_min = (case["t0"] - case["t0"][0]) / 60.0
    for i, (key, lab) in enumerate([("dpwtt_rel", "PWTT"), ("dsi", "ΔT")]):
        ax = fig.add_subplot(gs[i, 0])
        s = SERIES[i]
        y = 100 * d[key]
        ax.plot(t_min, y, color=s["color"], ls=s["ls"])
        ax.axhline(0, color=FAINT, lw=0.6, zorder=0)
        ax.set_ylabel(f"Δ{lab} (%)")
        # 外れ値で軸が潰れないよう99パーセンタイルで表示範囲を決め、超過分は注記する
        hi = float(np.nanpercentile(np.abs(y), 99)) if np.isfinite(y).any() else 1.0
        hi = max(hi, 1e-6) * 1.3
        n_out = int(np.sum(np.abs(y) > hi))
        ax.set_ylim(-hi, hi)
        if n_out:
            ax.annotate(f"{n_out} beyond axis", xy=(0.98, 0.08),
                        xycoords="axes fraction", ha="right", fontsize=6, color=MUTED)
        if i == 0:
            ax.set_title(f"a  Representative case (id {pick})", loc="left")
            ax.set_xticklabels([])
        else:
            ax.set_xlabel("Time from calibration (min)")

    # (b) 症例内 r² の分布
    ax = fig.add_subplot(gs[:, 1])
    ax.hist(r2[np.isfinite(r2)], bins=20, color=SERIES[0]["color"],
            alpha=0.75, edgecolor="white", linewidth=0.4)
    ax.axvline(med, color=INK, ls="--", lw=1.0)
    ax.annotate(f"median {med:.2f}", xy=(med, ax.get_ylim()[1] * 0.94),
                xytext=(4, 0), textcoords="offset points", fontsize=7, color=INK)
    ax.set_xlabel("Within-case $r^2$")
    ax.set_ylabel("Cases")
    ax.set_title("b  Variance explained", loc="left")
    _int_yticks(ax)

    # (c) ΔΔT% の係数分布（0に集まることを見せる）
    ax = fig.add_subplot(gs[:, 2])
    b1 = per["b_dsi"].to_numpy(float)
    b1 = b1[np.isfinite(b1)]
    lim = float(np.nanpercentile(np.abs(b1), 98)) if b1.size else 1.0
    ax.hist(np.clip(b1, -lim, lim), bins=20, color=SERIES[1]["color"],
            alpha=0.75, edgecolor="white", linewidth=0.4)
    ax.axvline(0, color=INK, lw=1.0)
    ax.annotate(f"same sign in {diag['sign_consistency']:.0%} of cases",
                xy=(0.03, 0.95), xycoords="axes fraction", fontsize=6.6,
                color=INK, va="top")
    ax.set_xlabel("Within-case coefficient on ΔΔT%")
    ax.set_ylabel("Cases")
    ax.set_title("c  Coefficients", loc="left")
    _int_yticks(ax)

    _save(fig, "fig2_premise", dpi)


# ---------------------------------------------------------------- 図3
def fig3_quality(cases: list[dict], dpi: int) -> None:
    """測定品質。(a) 陽性対照 (b) 自己相関分布 (c) 症例内変動。"""
    diag = premise_by_case(cases)
    per = pd.DataFrame(diag["per_case"])

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5))

    # (a) 陽性対照: 年齢 vs ΔT
    ax = axes[0]
    age = np.array([c["age"] for c in cases], float)
    dt = np.array([1000.0 * c["height"] / np.nanmedian(c["windows"]["si"])
                   for c in cases], float)
    m = np.isfinite(age) & np.isfinite(dt)
    ax.scatter(age[m], dt[m], s=9, facecolor="none",
               edgecolor=SERIES[0]["color"], linewidth=0.7)
    if m.sum() >= 10:
        k, b = np.polyfit(age[m], dt[m], 1)
        xs = np.linspace(np.nanmin(age[m]), np.nanmax(age[m]), 50)
        ax.plot(xs, k * xs + b, color=INK, ls="--", lw=1.0)
        rho = pd.Series(age[m]).rank().corr(pd.Series(dt[m]).rank())
        ax.annotate(f"ρ = {rho:+.2f}   n = {m.sum()}", xy=(0.03, 0.06),
                    xycoords="axes fraction", fontsize=7, color=INK)
    ax.set_xlabel("Age (years)")
    ax.set_ylabel("ΔT (ms)")
    ax.set_title("a  Positive control: ageing", loc="left")

    # (b) 自己相関の分布（3系列を横並びの箱で・直接ラベル）
    ax = axes[1]
    cols = [("ac_pwtt", "PWTT"), ("ac_si", "ΔT"), ("ac_ri", "RI")]
    data = [per[c].dropna().to_numpy(float) for c, _ in cols]
    try:
        bp = ax.boxplot(data, orientation="horizontal", widths=0.55, patch_artist=True,
                        medianprops=dict(color=INK, linewidth=1.1),
                        flierprops=dict(marker=".", markersize=2, markerfacecolor=FAINT,
                                        markeredgecolor="none"))
    except TypeError:  # matplotlib < 3.11
        bp = ax.boxplot(data, vert=False, widths=0.55, patch_artist=True,
                        medianprops=dict(color=INK, linewidth=1.1),
                        flierprops=dict(marker=".", markersize=2, markerfacecolor=FAINT,
                                        markeredgecolor="none"))
    for patch, s in zip(bp["boxes"], SERIES):
        patch.set_facecolor(s["color"]); patch.set_alpha(0.55)
        patch.set_edgecolor(MUTED); patch.set_linewidth(0.6)
    for w in bp["whiskers"] + bp["caps"]:
        w.set_color(MUTED); w.set_linewidth(0.6)
    ax.set_yticks(range(1, len(cols) + 1))
    ax.set_yticklabels([lab for _, lab in cols])
    ax.axvline(0, color=FAINT, lw=0.6, zorder=0)
    ax.set_xlabel("Lag-1 autocorrelation between windows")
    ax.set_title("b  Signals are reproducible", loc="left")
    ax.set_xlim(-0.1, 1.0)

    # (c) 症例内の変動係数（指標が症例内で動いているか）
    ax = axes[2]
    cv = {"ΔT": [], "RI": []}
    for c in cases:
        for lab, key in [("ΔT", "si"), ("RI", "ri")]:
            v = c["windows"][key]
            v = v[np.isfinite(v)]
            if v.size >= 5 and np.median(v) != 0:
                cv[lab].append(float(np.std(v) / abs(np.median(v))))
    for i, (lab, vals) in enumerate(cv.items()):
        s = SERIES[i]
        if vals:
            ax.hist(vals, bins=18, histtype="step", color=s["color"],
                    ls=s["ls"], lw=1.2, label=f"{lab} (median {np.median(vals):.2f})")
    ax.set_xlabel("Within-case coefficient of variation")
    ax.set_ylabel("Cases")
    ax.set_title("c  Indices do vary within case", loc="left")
    ax.legend(loc="upper right")
    _int_yticks(ax)

    fig.tight_layout()
    _save(fig, "fig3_quality", dpi)


# ---------------------------------------------------------------- 図4
def fig4_accuracy(cases: list[dict], dpi: int) -> None:
    """副次: Bland-Altman（対照 vs 提案）。参照が非独立である点は本文で明示する。"""
    from src.models import crossval
    from src.stats import bland_altman, percentage_error

    results = crossval(cases)
    if not results:
        print("  図4: 交差検証の結果が得られないため省略")
        return

    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.7), sharey=True, sharex=True)
    for ax, key, title in zip(axes, ["est_ctrl", "est_prop"],
                              ["a  Control (PWTT-type)", "b  Proposed K(ΔT, RI)"]):
        est = np.concatenate([np.asarray(r[key], float) for r in results])
        ref = np.concatenate([np.asarray(r["co_ref"], float) for r in results])
        m = np.isfinite(est) & np.isfinite(ref)
        est, ref = est[m], ref[m]
        ba = bland_altman(est, ref)
        mean = (est + ref) / 2.0
        diff = est - ref
        ax.scatter(mean, diff, s=5, facecolor="none",
                   edgecolor=SERIES[0]["color"], linewidth=0.4, alpha=0.5)
        for y, ls, lab in [(ba["bias"], "-", "bias"),
                           (ba["loa_high"], "--", "upper LoA"),
                           (ba["loa_low"], "--", "lower LoA")]:
            ax.axhline(y, color=INK, ls=ls, lw=0.9)
            ax.annotate(f"{lab} {y:+.2f}", xy=(ax.get_xlim()[1], y), xytext=(-2, 2),
                        textcoords="offset points", ha="right", fontsize=6.3, color=INK)
        ax.set_xlabel("Mean of estimated and reference CO (L/min)")
        ax.set_title(f"{title}   PE {percentage_error(est, ref):.1f}%", loc="left")
    axes[0].set_ylabel("Estimated − reference CO (L/min)")
    fig.tight_layout()
    _save(fig, "fig4_accuracy", dpi)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", nargs="*", type=int, default=None,
                    help="作る図の番号（例: --only 2 3）")
    ap.add_argument("--dpi", type=int, default=600, help="PNGの解像度（投稿用は600）")
    ap.add_argument("--min-windows", type=int, default=MIN_WINDOWS)
    args = ap.parse_args()

    style()
    cases = load_cases(args.min_windows)
    print(f"症例数 {len(cases)}")
    if len(cases) < 10:
        print("症例が10例未満のため作図しません（本解析の完走後に実行してください）。")
        return

    want = set(args.only) if args.only else {1, 2, 3, 4}
    if 1 in want:
        print("図1 症例フロー"); fig1_flow(cases, args.dpi)
    if 2 in want:
        print("図2 前提検証（主結果）"); fig2_premise(cases, args.dpi)
    if 3 in want:
        print("図3 測定品質と陽性対照"); fig3_quality(cases, args.dpi)
    if 4 in want:
        print("図4 精度（副次）"); fig4_accuracy(cases, args.dpi)
    print("\n完了。figs/ のPDFが投稿用（ベクター）、PNGが確認用です。")
    print("白黒印刷でも読めるよう線種とマーカーで区別しています（カラーは補助）。")


if __name__ == "__main__":
    main()

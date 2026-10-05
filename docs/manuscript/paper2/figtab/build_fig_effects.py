#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""図2 因子ごとの主効果（表2）と 1 因子掃引（表2b）。記述・事前に計画した解析（判定には用いない）。

(a) 振った 6 因子 × 4 指標の年齢層内主効果（+1SD と −1SD の平均の差 ÷ 層平均、%）を横棒で示す。
    分解法の 2 指標には表2 が与える年齢層内 Spearman ρ を棒の先に括弧で添える。
(b) 1 因子掃引（他の因子は基準値、年齢層の中央値）。上が分解法 ΔT（凍結版）、下が分解法 RI（凍結版）。
    −1SD・基準・+1SD を結ぶ線を因子ごとに引き、脈波伝播速度の応答が単調でないことが見えるようにする。
値はすべて `data/paper2_numbers.json`（`../02_tables.md` を機械で読んだもの）から取り、手で打たない。

使い方
    python3 build_fig_effects.py                 和文・英文の両方を out/ に書く
    python3 build_fig_effects.py --lang en       英文だけ
    python3 build_fig_effects.py --selftest      描いた値と JSON の一致・最小文字サイズ・注記・禁止語を確かめる
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import re
import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                      # noqa: E402
from matplotlib.gridspec import GridSpec             # noqa: E402
from matplotlib.patches import Patch                 # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common                                        # noqa: E402
from common import (PALETTE, mm, setup, save, load_numbers,   # noqa: E402
                    check_min_font, texts_of, wrap_text, text_overlaps, texts_outside)

NAME = "fig_effects"
REPO = HERE.parents[3]
LABELS = json.loads((HERE / "data" / "labels.json").read_text(encoding="utf-8"))

# (a) の 4 指標（表2 の列の順）。塗り・縁・ハッチで白黒でも見分ける
INDEX_STYLE = {
    "landmark_dt": dict(fc=PALETTE["landmark"], ec=PALETTE["ink"], hatch=None),
    "pda_dt":      dict(fc=PALETTE["pda"], ec=PALETTE["ink"], hatch="////"),
    "pda_ri":      dict(fc="white", ec=PALETTE["pda"], hatch="xxxx"),
    "amp_ratio":   dict(fc=PALETTE["amp"], ec=PALETTE["ink"], hatch="...."),
}
# (b) の因子ごとの線。脈波伝播速度を強調し、残りは灰色で記号と線種を変える
FACTOR_STYLE = {
    "pwv":             dict(color=PALETTE["pda"], lw=1.6, ls="-", marker="o", mfc=PALETTE["pda"], zorder=5),
    "heart_rate":      dict(color=PALETTE["ink"], lw=1.0, ls=(0, (4, 2)), marker="s", mfc=PALETTE["ink"], zorder=4),
    "aortic_diameter": dict(color=PALETTE["grey"], lw=0.8, ls="-", marker="^", mfc="white", zorder=3),
    "ejection_time":   dict(color=PALETTE["grey"], lw=0.8, ls=(0, (1, 1.5)), marker="v", mfc="white", zorder=3),
    "map":             dict(color=PALETTE["grey"], lw=0.8, ls=(0, (5, 2, 1, 2)), marker="D", mfc="white", zorder=3),
    "stroke_volume":   dict(color=PALETTE["grey"], lw=0.8, ls=(0, (2, 1.5)), marker="x", mfc=PALETTE["grey"], zorder=3),
}

T = {
    "ja": {
        "title_a": "(a) 因子ごとの主効果（表2）",
        "title_b": "(b) 1 因子掃引（表2b）",
        "xlabel_a": "年齢層内の主効果（%）",
        "unit_ms": "[ms]",
        "levels": {"minus1sd": "−1SD", "base": "基準", "plus1sd": "+1SD"},
        "planned": "記述・事前に計画",
        "footer": ("出典: 02_tables.md 表2・表2b（{planned}。lab_log 2026-09-03「研究0 の結果」・「判定の訂正」、追記12）。"
                   "主効果＝その因子が +1SD の被験者の平均と −1SD の平均の差 ÷ 層平均（年齢層内、%）。"
                   "括弧内は分解法の 2 指標と因子の年齢層内 Spearman ρ（表2）。"
                   "(b) は他の 5 因子を基準値に固定した被験者の、年齢層にわたる中央値。"),
    },
    "en": {
        "title_a": "(a) Main effect of each factor (table 2)",
        "title_b": "(b) Single-factor sweep (table 2b)",
        "xlabel_a": "Within-stratum main effect (%)",
        "unit_ms": "[ms]",
        "levels": {"minus1sd": "−1 SD", "base": "reference", "plus1sd": "+1 SD"},
        "planned": "descriptive, planned before the run",
        "footer": ("Source: tables 2 and 2b of 02_tables.md ({planned}; lab_log 2026-09-03, results of study 0 and "
                   "correction of the verdict, and entry 12). Main effect, mean at +1 SD minus mean at −1 SD of the "
                   "factor, divided by the stratum mean (within age strata, %). In parentheses, within-stratum Spearman ρ "
                   "between the factor and the two decomposition indices (table 2). (b) Subjects with the other five "
                   "factors at reference; median over age strata."),
    },
}


def wrap_factor(s: str, lang: str) -> str:
    if lang == "ja":
        return s
    return "\n".join(textwrap.wrap(s, width=16, break_long_words=False))


def fmt_rho(r: float) -> str:
    """表2 の書き方に合わせる（符号付き・小数 2 桁。−0.00 は負の 0 として残す）。"""
    sign = "−" if math.copysign(1.0, r) < 0 else "+"
    return f"({sign}{abs(r):.2f})"


def table2b_keys(t2b: dict) -> tuple[list[str], list[str]]:
    """表2b の列の鍵を JSON から読む（ΔT の 3 列・RI の 3 列、表の順）。"""
    cols = [c["key"] for c in t2b["columns"] if c["kind"] == "num"]
    return [k for k in cols if k.startswith("dt_")], [k for k in cols if k.startswith("ri_")]


def spread(values: list[float], min_gap: float, lo: float, hi: float) -> list[float]:
    """直接ラベルの縦位置が重ならないように、最小間隔を保って広げる（値の順は保つ）。"""
    order = sorted(range(len(values)), key=lambda i: values[i])
    pos = [values[i] for i in order]
    for k in range(1, len(pos)):
        if pos[k] - pos[k - 1] < min_gap:
            pos[k] = pos[k - 1] + min_gap
    over = pos[-1] - hi
    if over > 0:
        pos = [p - over for p in pos]
    for k in range(len(pos) - 2, -1, -1):
        if pos[k + 1] - pos[k] < min_gap:
            pos[k] = pos[k + 1] - min_gap
    under = lo - pos[0]
    if under > 0:
        pos = [p + under for p in pos]
    out = [0.0] * len(values)
    for k, i in enumerate(order):
        out[i] = pos[k]
    return out


def build(lang: str, numbers: dict):
    """図を組む。戻り値は (fig, 描いた値の記録)。記録は自己検査で JSON と突き合わせる。"""
    setup(lang)
    plt.rcParams.update({"xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
                         "hatch.linewidth": 0.5,
                         "font.family": list(plt.rcParams["font.family"]) + ["DejaVu Sans"]})
    tx = T[lang]
    t2 = numbers["tables"]["表2"]
    t2b = numbers["tables"]["表2b"]
    index_keys = [c["key"] for c in t2["columns"] if c["kind"] == "effect"]
    factors = [r["id"] for r in t2["rows"]]                       # 表2 の行の順
    dt_keys, ri_keys = table2b_keys(t2b)
    rows2b = {r["id"]: r for r in t2b["rows"]}
    rec = {"bars": {}, "rho_text": {}, "lines": {}}

    fig = plt.figure(figsize=(mm(150), mm(110)))
    # 右の余白は (b) の直接ラベルの幅（和文は短い）に合わせる
    gs = GridSpec(2, 2, figure=fig, left=0.145, right=0.87 if lang == "ja" else 0.80, top=0.94, bottom=0.34,
                  wspace=0.5, hspace=0.40, width_ratios=[1.45, 1.0])
    ax_a = fig.add_subplot(gs[:, 0])
    ax_dt = fig.add_subplot(gs[0, 1])
    ax_ri = fig.add_subplot(gs[1, 1], sharex=ax_dt)

    # ---------------- (a) 主効果の横棒
    nf = len(factors)
    nk = len(index_keys)
    bh = 0.18
    offs = [(-(nk - 1) / 2 + j) * 0.265 for j in range(nk)]
    for i, fid in enumerate(factors):
        row = t2["rows"][i]
        for j, key in enumerate(index_keys):
            cell = row[key]
            st = INDEX_STYLE[key]
            bars = ax_a.barh(i + offs[j], cell["effect_pct"], height=bh, color=st["fc"], edgecolor=st["ec"],
                             linewidth=0.5, hatch=st["hatch"], zorder=3)
            rec["bars"][(fid, key)] = float(bars[0].get_width())
            if cell.get("rho") is not None:
                v = cell["effect_pct"]
                s = fmt_rho(cell["rho"])
                ax_a.annotate(s, (v, i + offs[j]), xytext=(3 if v >= 0 else -3, 0), textcoords="offset points",
                              ha="left" if v >= 0 else "right", va="center", fontsize=8, color=PALETTE["ink"])
                rec["rho_text"][(fid, key)] = s
    ax_a.axvline(0, color=PALETTE["ink"], lw=0.6, zorder=2)
    ax_a.set_ylim(nf - 0.5, -0.5)
    ax_a.set_yticks(range(nf))
    ax_a.set_yticklabels([wrap_factor(LABELS["factors"][f][lang], lang) for f in factors])
    ax_a.set_xlim(-73, 60)
    ax_a.set_xticks([-40, -20, 0, 20, 40])
    ax_a.set_xticklabels(["−40", "−20", "0", "20", "40"])
    ax_a.set_xlabel(tx["xlabel_a"])
    ax_a.set_title(tx["title_a"], loc="left", fontsize=8)
    ax_a.tick_params(axis="y", length=0)
    handles = [Patch(facecolor=INDEX_STYLE[k]["fc"], edgecolor=INDEX_STYLE[k]["ec"], hatch=INDEX_STYLE[k]["hatch"],
                     linewidth=0.5, label=LABELS["indices"][k][lang]) for k in index_keys]
    # 凡例は図の下、脚注の上に 2 列で置く（(a) の下では横軸の名と重なる）
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.01, 0.17), ncol=2, frameon=False,
               handlelength=1.8, handleheight=0.9, borderaxespad=0, labelspacing=0.35, columnspacing=1.5)

    # ---------------- (b) 1 因子掃引
    x = [0, 1, 2]
    level_names = [tx["levels"][k.split("_", 1)[1]] for k in dt_keys]
    def ylabel(name: str, unit: str) -> str:
        if lang == "ja":
            return name + ("\n" + unit if unit else "")
        return "\n".join(textwrap.wrap((name + " " + unit).strip(), width=18, break_long_words=False))

    for ax, keys, ylab in ((ax_dt, dt_keys, ylabel(LABELS["indices"]["pda_dt"][lang], tx["unit_ms"])),
                           (ax_ri, ri_keys, ylabel(LABELS["indices"]["pda_ri"][lang], ""))):
        ys_all = []
        for fid in factors:
            ys = [rows2b[fid][k]["value"] for k in keys]
            st = FACTOR_STYLE[fid]
            ln, = ax.plot(x, ys, color=st["color"], lw=st["lw"], ls=st["ls"], marker=st["marker"], ms=4,
                          mfc=st["mfc"], mec=st["color"], mew=0.8, zorder=st["zorder"], clip_on=False)
            rec["lines"][(keys[0][:2], fid)] = [float(v) for v in ln.get_ydata()]
            ys_all += ys
        lo, hi = min(ys_all), max(ys_all)
        pad = (hi - lo) * 0.08
        # RI は基準値の数字を点の下に書くので、下に余白を広く取る
        lo_pad = pad if keys is dt_keys else (hi - lo) * 0.22
        ax.set_ylim(lo - lo_pad, hi + pad)
        # 目盛は表示範囲の中だけに置く（範囲外の目盛の文字が残らないように）
        ax.set_yticks([t for t in ax.get_yticks() if lo - lo_pad <= t <= hi + pad])
        lo = lo - lo_pad + pad
        ax.set_xlim(-0.25, 2.25)
        ax.set_xticks(x)
        ax.set_xticklabels(level_names)
        ax.set_ylabel(ylab, fontsize=8)
        # 右端に因子名を直接書く（重ならないように縦に広げ、細い引き出し線で結ぶ）
        ax_h_mm = ax.get_position().height * fig.get_figheight() * 25.4
        gap = 3.6 * (hi - lo + 2 * pad) / ax_h_mm
        ends = [rows2b[f][keys[-1]]["value"] for f in factors]
        ypos = spread(ends, gap, lo - pad, hi + pad)
        for fid, ye, yl in zip(factors, ends, ypos):
            st = FACTOR_STYLE[fid]
            ax.plot([2.04, 2.22], [ye, yl], color=PALETTE["light"], lw=0.5, zorder=1, clip_on=False)
            ax.text(2.27, yl, LABELS["factors"][fid][lang], ha="left", va="center", fontsize=8,
                    color=PALETTE["ink"] if fid in ("pwv", "heart_rate") else PALETTE["grey"], clip_on=False)
        # 脈波伝播速度の 3 値を書く（応答が単調でないことを数で読めるように）
        pv = [rows2b["pwv"][k]["value"] for k in keys]
        fmt = (lambda v: f"{v:.1f}") if keys is dt_keys else (lambda v: f"{v:.3f}")
        if keys is dt_keys:
            places = [(6, -6, "center", "top"), (0, 7, "center", "bottom"), (-5, 0, "right", "center")]
        else:
            places = [(6, 6, "center", "bottom"), (0, -6, "center", "top"), (-5, 0, "right", "center")]
        for xi, v, (dx, dy, ha, va) in zip(x, pv, places):
            ax.annotate(fmt(v), (xi, v), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va,
                        fontsize=8, color=PALETTE["pda"])
    ax_dt.set_title(tx["title_b"], loc="left", fontsize=8)
    plt.setp(ax_dt.get_xticklabels(), visible=True)

    footer = wrap_text(tx["footer"].format(planned=tx["planned"]), lang)
    fig.text(0.01, 0.012, footer, ha="left", va="bottom", fontsize=8, color=PALETTE["ink"], linespacing=1.3)
    return fig, rec


def legend_text(lang: str, numbers: dict) -> str:
    t2 = numbers["tables"]["表2"]
    t2b = numbers["tables"]["表2b"]
    index_keys = [c["key"] for c in t2["columns"] if c["kind"] == "effect"]
    nf, nk = len(t2["rows"]), len(index_keys)
    sep = "・" if lang == "ja" else ", "
    factor_names = sep.join(LABELS["factors"][r["id"]][lang] for r in t2["rows"])
    index_names = sep.join(LABELS["indices"][k][lang] for k in index_keys)
    dt_keys, ri_keys = table2b_keys(t2b)
    rows2b = {r["id"]: r for r in t2b["rows"]}
    arrow = " → "
    pv_dt = arrow.join(f"{rows2b['pwv'][k]['value']:.1f}" for k in dt_keys)
    pv_ri = arrow.join(f"{rows2b['pwv'][k]['value']:.3f}" for k in ri_keys)
    map_dt = arrow.join(f"{rows2b['map'][k]['value']:.1f}" for k in dt_keys)
    if lang == "ja":
        return "\n".join([
            "図2　振った因子ごとの年齢層内主効果（表2）と 1 因子掃引（表2b）― 記述・事前に計画した解析",
            "",
            f"何を示すか: (a) {t2['title']}。{nf} 因子（{factor_names}）× "
            f"{nk} 指標（{index_names}）の横棒。塗り・ハッチで指標を分け、"
            "分解法の 2 指標には表2 の括弧内の値（その因子と指標の年齢層内 Spearman ρ）を棒の先に添えた。"
            f"(b) {t2b['title']}。上が分解法 ΔT（ms）、下が分解法 RI で、−1SD・基準・+1SD での値を因子ごとに結んだ。"
            f"脈波伝播速度（青）の行が最も大きく折れ返り、ΔT は −1SD 側が予測と逆向きに動き（{pv_dt}）、"
            f"RI は U 字を描く（{pv_ri}）。ΔT では平均血圧の行も小さく折れ返る（{map_dt}。lab_log 追記113）。"
            "青の数字は脈波伝播速度の 3 値。",
            "",
            "出典: `02_tables.md` 表2・表2b（`docs/research/roadmap_v1.md` §9）。20番 `20_pwdb_validity.py`"
            "（`data/pwdb/pwdb_indices.csv`。lab_log 2026-09-03「研究0 の結果」の主効果と 1 因子掃引の表）、"
            "特徴点法 ΔT の列は 23番 `23_pwdb_landmarks.py`（lab_log 2026-09-03「判定の訂正」）、"
            "早期振幅比の列は 26番 `26_pwdb_compare.py`（lab_log 追記12 の表3）。"
            "数値は `data/paper2_numbers.json` から台本 `build_fig_effects.py` が読む。",
            "",
            "記述・事前に計画した解析であり（2026-09-03 の事前規準の「機構（記述）」の行）、判定には用いない。",
        ])
    return "\n".join([
        "Figure 2. Within-stratum main effect of each varied factor (table 2) and single-factor sweeps (table 2b): "
        "descriptive analyses planned before the run.",
        "",
        f"What is shown: (a) main effect of each of the {nf} factors ({factor_names}) on {nk} indices ({index_names}), "
        "computed within each age stratum as the mean at +1 SD minus the "
        "mean at −1 SD of the factor, divided by the stratum mean (%). Fill and hatch distinguish the indices; for the two "
        "decomposition indices the within-stratum Spearman ρ between factor and index, as given in table 2, is written in "
        "parentheses at the end of the bar. (b) Single-factor sweeps: the stratum median of decomposition ΔT (ms, top) and "
        "RI (bottom) when one factor is moved across −1 SD, reference and +1 SD while the other five are held at reference. "
        "The response to pulse wave velocity (blue) folds back most: ΔT moves opposite to the prediction on the −1 SD side "
        f"({pv_dt}) and RI is U-shaped ({pv_ri}). For ΔT the mean arterial pressure row also folds back slightly ({map_dt}; "
        "lab_log entry 113). The blue numbers are the three values for pulse wave velocity.",
        "",
        "Source: tables 2 and 2b of `02_tables.md` (`docs/research/roadmap_v1.md` §9). Script 20 `20_pwdb_validity.py` "
        "(`data/pwdb/pwdb_indices.csv`; lab_log 2026-09-03, results of study 0, tables of main effects and single-factor "
        "sweeps); the fiducial-point ΔT column from script 23 `23_pwdb_landmarks.py` (lab_log 2026-09-03, correction of "
        "the verdict); the early amplitude ratio column from script 26 `26_pwdb_compare.py` (lab_log entry 12, table 3). "
        "All numbers are read from `data/paper2_numbers.json` by `build_fig_effects.py`.",
        "",
        "Descriptive, planned before the run (the row 'mechanism (descriptive)' of the prespecified criteria of "
        "2026-09-03); not used for the decision.",
    ])


# ---------------------------------------------------------------- 自己検査

def _banned_terms():
    """用語検査器（analysis/scripts/check_terminology.py）の禁止語の表を読む。写さない。"""
    path = REPO / "analysis" / "scripts" / "check_terminology.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("check_terminology", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.BANNED


def _banned_hits(banned, strings) -> list[str]:
    hits = []
    for s in strings:
        for line in s.split("\n"):
            for term, _alt, allow in banned:
                if term in line and not (allow and re.sub(allow, "", line).find(term) < 0):
                    hits.append(f"{term}: {line[:40]}")
    return hits


def selftest() -> int:
    ok_all = True

    def rep(name, ok, detail=""):
        nonlocal ok_all
        ok_all &= bool(ok)
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))

    banned = _banned_terms()
    for lang in ("ja", "en"):
        print(f"[{lang}]")
        fig, rec = build(lang, load_numbers())
        fresh = load_numbers()
        t2 = fresh["tables"]["表2"]
        t2b = fresh["tables"]["表2b"]
        index_keys = [c["key"] for c in t2["columns"] if c["kind"] == "effect"]
        # (a) 棒の長さ
        exp_bars = {(r["id"], k): r[k]["effect_pct"] for r in t2["rows"] for k in index_keys}
        diff = [k for k in exp_bars if k not in rec["bars"] or abs(rec["bars"][k] - exp_bars[k]) > 1e-12]
        rep(f"(a) 棒の長さが表2 の主効果と一致（{len(exp_bars)} 本）", not diff and len(rec["bars"]) == len(exp_bars),
            f"差 {diff}")
        exp_rho = {(r["id"], k): fmt_rho(r[k]["rho"]) for r in t2["rows"] for k in index_keys if r[k].get("rho") is not None}
        rep(f"(a) ρ の注釈が表2 の括弧内と一致（{len(exp_rho)} 個）", rec["rho_text"] == exp_rho,
            f"{rec['rho_text']} != {exp_rho}")
        raw_rho = {(r["id"], k): r[k]["raw"] for r in t2["rows"] for k in index_keys if r[k].get("rho") is not None}
        rep("(a) ρ の注釈の文字列が表2 の原文に含まれる",
            all(v.replace("(", "（").replace(")", "）") in raw_rho[k] for k, v in exp_rho.items()))
        # (b) 折れ線
        dt_keys, ri_keys = table2b_keys(t2b)
        exp_lines = {}
        for r in t2b["rows"]:
            exp_lines[("dt", r["id"])] = [r[k]["value"] for k in dt_keys]
            exp_lines[("ri", r["id"])] = [r[k]["value"] for k in ri_keys]
        diff = [k for k in exp_lines if k not in rec["lines"]
                or any(abs(a - b) > 1e-12 for a, b in zip(rec["lines"][k], exp_lines[k]))]
        rep(f"(b) 折れ線の値が表2b と一致（{len(exp_lines)} 本 × 3 点）", not diff and len(rec["lines"]) == len(exp_lines),
            f"差 {diff}")
        texts = texts_of(fig)
        joined = "\n".join(texts)
        pv = [r for r in t2b["rows"] if r["id"] == "pwv"][0]
        rep("(b) 脈波伝播速度の 6 値が図に書かれている",
            all(f"{pv[k]['value']:.1f}" in texts for k in dt_keys) and all(f"{pv[k]['value']:.3f}" in texts for k in ri_keys))
        bad_font = check_min_font(fig)
        rep(f"文字はすべて {common.MIN_FONT_PT:g} pt 以上", not bad_font, f"{bad_font[:3]}")
        rep("脚注に「記述・事前に計画」の注記がある", T[lang]["planned"] in joined.replace("\n", ""))
        ov = text_overlaps(fig)
        rep("文字どうしが重ならない", not ov, f"{ov[:3]}")
        outside = texts_outside(fig)
        rep("文字が図の枠からはみ出さない", not outside, f"{outside[:3]}")
        rep("脚注に表2・表2b の出典がある", ("表2・表2b" in joined.replace("\n", "")) if lang == "ja"
            else ("tables 2 and 2b" in joined.replace("\n", " ")))
        verdict_words = ["成立", "合格", " pass", "fail"]
        rep("判定の語（成立・不成立・pass・fail）を図に書いていない", not any(w in joined for w in verdict_words))
        ylabs = [t.get_text().replace("\n", " ") for t in fig.axes[0].get_yticklabels()]
        want = [LABELS["factors"][r["id"]][lang] for r in t2["rows"]]
        rep("(a) 縦軸の因子名が labels.json と同じ（表2 の順）", ylabs == want, f"{ylabs} != {want}")
        leg_labels = [t.get_text() for t in fig.legends[0].get_texts()]
        rep("(a) 凡例の指標名が labels.json と同じ（表2 の列の順）",
            leg_labels == [LABELS["indices"][k][lang] for k in index_keys])
        rep("(b) 6 因子の名が直接書かれている（上下とも）",
            all(sum(t == LABELS["factors"][r["id"]][lang] for t in texts) >= 2 for r in t2["rows"]))
        leg = legend_text(lang, fresh)
        if banned is None:
            print("  （用語検査器が無いので禁止語の確認は飛ばした）")
        else:
            hits = _banned_hits(banned, texts + [leg])
            rep("図と凡例文に禁止語が無い（検査器の表）", not hits, f"{hits[:3]}")
        plt.close(fig)
    print("RESULT", "PASS" if ok_all else "FAIL")
    return 0 if ok_all else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lang", choices=["ja", "en"], default=None, help="省略すると両方")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out-dir", default=str(common.OUT))
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    common.OUT = Path(a.out_dir)
    common.OUT.mkdir(parents=True, exist_ok=True)
    numbers = load_numbers()
    for lang in ([a.lang] if a.lang else ["ja", "en"]):
        fig, _rec = build(lang, numbers)
        paths = save(fig, NAME, lang)
        plt.close(fig)
        lp = common.OUT / f"{NAME}_legend_{lang}.txt"
        lp.write_text(legend_text(lang, numbers) + "\n", encoding="utf-8")
        for p in paths + [lp]:
            print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())

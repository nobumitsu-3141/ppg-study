#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""図7 当てはまりと真値への追従の関係 ― (a) 表3 の NRMSE 対 |ρ|、(b) 表6 の通過率 対 C 段の |ρ|。

(a) 表3（基底関数と成分数の総当たり。120 名から取った型1 の 98 拍・4 層）: 横軸は NRMSE の中央値（対数目盛）、
縦軸は ΔT × 大動脈PWV の年齢層内 Spearman |ρ| の中央値（全例＝C 段）。記号の形は基底の族
（歪みガウス α∈[0,8]・ガウス・歪みガウス α∈[−8,8]・ガンマ（凍結の探索範囲）・ガンマ（広い探索範囲））、記号の横の数字は成分数と、
括弧内に予測の向きを持った層の数／層の数（表3 の x/4。規準は全層で予測の向きを要るので、0.30 を超えても 3/4 の点は満たさない）。
同じ族の点は成分数の順に細線で結ぶ。
(b) 表6（拡張期の下降の扱いを変えた版。型3・3,378 名・6 層）: 横軸は通過率（A 段に残る割合）、縦軸は C 段の |ρ|。
点は版ごとに 1 つで、表6 の (n) の番号と予測の向きを持った層の数（x/6）を添える（名は脚注の対応表。labels.json の short_ja / short_en）。
白抜き＝下降を説明する項を足す案、塗りつぶし＝下降を当てはめの対象から外す・残差の中で小さくする案、灰の四角＝基準。
特徴点法（同梱）の C 段の値を横の点線で引く（図5 と同じ線種）。両方の枠に規準線 0.30（灰の破線）を引く。
2 つの枠は対象が異なる（表3 は型1 の 98 拍、表6 は型3 の 3,378 名）ので、脚注にその旨を書く。
値はすべて `data/paper2_numbers.json`（`../02_tables.md` を機械で読んだもの）から取り、手で打たない。
表3・表6 は探索・事後なので、脚注にその旨と段の注釈（CLAUDE.md §3）を置く。判定（成立・不成立）は図に書かない。

使い方
    python3 build_fig_tradeoff.py                 和文・英文の両方を out/ に書く
    python3 build_fig_tradeoff.py --lang en       英文だけ
    python3 build_fig_tradeoff.py --selftest      描いた値と JSON の一致・最小文字サイズ・注釈・禁止語・文字の重なりを確かめる
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                      # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common                                        # noqa: E402
from common import (PALETTE, L, STAGE_NOTE, mm, setup, save, load_numbers,   # noqa: E402
                    check_min_font, texts_of, text_overlaps, text_marker_overlaps, texts_outside, wrap_text)

NAME = "fig_tradeoff"
REPO = HERE.parents[3]
LABELS = json.loads((HERE / "data" / "labels.json").read_text(encoding="utf-8"))

# (a) 基底の族ごとの記号（形で区別する。歪みガウス α∈[−8,8] は 2 成分で凍結版と同じ点に重なるので、白抜きで大きく描く）
FAMILY_ORDER = ("skewgauss_a08", "gauss", "skewgauss_pm8", "gamma_frozen", "gamma_wide")
FAMILY = {
    "skewgauss_a08": {"marker": "o", "color": PALETTE["pda"], "mfc": PALETTE["pda"], "ms": 4.5, "glyph": "●",
                      "label_dx": 5, "label_dy": -5, "ha": "left"},
    "gauss": {"marker": "s", "color": PALETTE["grey"], "mfc": PALETTE["grey"], "ms": 4.5, "glyph": "■",
              "label_dx": 5, "label_dy": 3, "ha": "left"},
    "skewgauss_pm8": {"marker": "^", "color": PALETTE["amp"], "mfc": "white", "ms": 6.5, "glyph": "△",
                      "label_dx": -5, "label_dy": 3, "ha": "right"},
    "gamma_frozen": {"marker": "D", "color": PALETTE["control"], "mfc": PALETTE["control"], "ms": 4.5, "glyph": "◆",
                     "label_dx": 5, "label_dy": 4, "ha": "left"},
    "gamma_wide": {"marker": "v", "color": PALETTE["control"], "mfc": "white", "ms": 6.0, "glyph": "▽",
                   "label_dx": -5, "label_dy": -4, "ha": "right"},
}
FAMILY_EN = {
    "skewgauss_a08": "Skewed Gaussian α∈[0,8] (frozen version)",
    "gauss": "Gaussian (no skew)",
    "skewgauss_pm8": "Skewed Gaussian α∈[−8,8] (Basso form)",
    "gamma_frozen": "Gamma (frozen search range)",
    "gamma_wide": "Gamma (wide search range)",
}
# (b) 群ごとの記号（白抜き＝項を足す、塗りつぶし＝外す・小さくする、灰の四角＝基準）
GROUP_STYLE = {
    "base": {"marker": "s", "color": PALETTE["grey"], "mfc": PALETTE["grey"], "glyph": "■"},
    "add": {"marker": "o", "color": PALETTE["pda"], "mfc": "white", "glyph": "○"},
    "remove": {"marker": "o", "color": PALETTE["pda"], "mfc": PALETTE["pda"], "glyph": "●"},
}
# (a) の点ごとの注釈の置き場所（記号からのずれ pt と寄せ）。族の既定を上書きする。注釈は「成分数 (層の数)」で幅があるので、
# 近い点どうし（◆3 と ▽3、◆4 と ▽4、●2 と △2）は左右に分け、線や規準線に掛からない側に置く。右端に近い ■2 は左下に置く
A_LABEL = {
    "gauss_m2": (-5, -7, "right"), "gauss_m3": (5, 6, "left"), "gauss_m4": (5, -5, "left"), "gauss_m5": (5, 0, "left"),
    "skewgauss_pm8_m2": (-5, 6, "right"),
    "gamma_frozen_m3": (5, 6, "left"), "gamma_frozen_m4": (5, 0, "left"),
    "gamma_wide_m3": (-5, 0, "right"), "gamma_wide_m4": (-5, 0, "right"),
}
# (b) の注釈「(番号) 層の数」の置き場所（記号からのずれ pt と寄せ）。点が重なる (0)(2) は記号の下に 2 段に置き、
# 記号や隣の注釈に掛かるものは左に置く
B_LABEL = {
    "fb": (0, -7, "center"), "dmu001": (0, -15, "center"), "decay": (-5, 0, "right"),
    "reservoir": (5, 2, "left"), "reservoir_tau015": (5, -2, "left"),
}
MARKER_PT = 4.5
XLIM_A, YLIM_A = (0.0022, 0.07), (0.0, 0.8)     # 左端は ▽4（NRMSE 0.0047）の左に置く注釈が枠に収まる値
XLIM_B, YLIM_B = (0.0, 1.0), (0.0, 0.85)

# 図の寸法（mm）。二段幅 150 mm
W_MM = 150.0
A_LEFT, A_W, B_LEFT, B_W = 13.0, 56.0, 84.0, 64.0
PANEL_H_MM, TOP_MM, XAXIS_MM = 45.0, 9.0, 10.0

T = {
    "ja": {
        "title_a": "(a) 表3: 基底と成分数\n（型1 の {nbeat} 拍）",
        "title_b": "(b) 表6: 下降の扱いの改良案\n（型3・{n3} 名）",
        "xlabel_a": "NRMSE の中央値（対数目盛。左ほど当てはまりが良い）",
        "xlabel_b": "通過率（A 段に残る割合）",
        "ylabel_a": "ΔT × 大動脈PWV の |ρ|（C 段・{ns} 層）",
        "ylabel_b": "ΔT × 大動脈PWV の |ρ|（C 段・{ns} 層）",
        "lm_line": "特徴点法（同梱）{v:.3f}",
        "key_a": "(a) の記号＝基底の族: {items}。数字＝成分数（括弧内は予測の向きを持った層の数／層の数）。同じ族は成分数の順に細線で結ぶ。",
        "key_b": "(b) の記号: ○＝下降を説明する項を足す、●＝下降を当てはめの対象から外す・残差の中で小さくする、■（灰）＝基準。"
                 "番号: {items}。番号の右の数字＝予測の向きを持った層の数／層の数。朱の点線＝特徴点法（同梱）の C 段の値。"
                 "灰の破線＝規準 {thr:.2f}。",
        "subjects": "(a) と (b) は対象が異なる: (a) は {nsub} 名から取った型1（切痕あり）の {nbeat} 拍・{ns_a} 層（表3）、"
                    "(b) は型3（変曲点のみ）の {n3} 名・{ns_b} 層（表6）。縦軸はいずれも年齢層内 Spearman |ρ| の中央値（C 段）。",
        "sep": "、",
        "eq": "＝",
    },
    "en": {
        "title_a": "(a) Table 3: basis and component count\n({nbeat} type-1 beats)",
        "title_b": "(b) Table 6: diastolic-decline variants\n(type 3, n = {n3})",
        "xlabel_a": "Median NRMSE (log scale; smaller means a closer fit)",
        "xlabel_b": "Pass rate (fraction remaining in tier A)",
        "ylabel_a": "|ρ| of ΔT × aortic PWV (tier C, {ns} strata)",
        "ylabel_b": "|ρ| of ΔT × aortic PWV (tier C, {ns} strata)",
        "lm_line": "Fiducial-point {v:.3f}",
        "key_a": "Markers in (a), basis family: {items}. Numbers, component count (in parentheses, strata with the predicted sign / "
                 "strata evaluated). Points of one family are joined in order of component count.",
        "key_b": "Markers in (b): open circle, add a term for the diastolic decline; filled circle, exclude or down-weight the diastolic "
                 "decline; grey square, reference fits. Numbers: {items}. The fraction after a number, strata with the predicted sign / "
                 "strata evaluated. Vermilion dotted line, tier-C value of the fiducial-point analysis (database-supplied). "
                 "Grey dashed line, criterion {thr:.2f}.",
        "subjects": "(a) and (b) are different subject sets: (a) {nbeat} type-1 beats (notch present) from {nsub} subjects, {ns_a} strata "
                    "(table 3); (b) the {n3} type-3 subjects (inflection only), {ns_b} strata (table 6). Both y axes are the median "
                    "within-age-stratum Spearman |ρ| (tier C).",
        "sep": "; ",
        "eq": " = ",
    },
}


# ---------------------------------------------------------------- 値の読み出し

def type3_n(numbers: dict) -> int:
    return next(r for r in numbers["tables"]["表5"]["rows"] if r["id"] == "type3")["n"]


def table3_subjects(numbers: dict) -> tuple[int, int, int]:
    """表3 の対象（被験者数・拍数・層の数）を表3 の前書き（02_tables.md）から読む。"""
    txt = " ".join(numbers["tables"]["表3"]["preamble"]).replace("\n", "")
    m = re.search(r"(\d[\d,]*)\s*名から取った.*?(\d+)\s*拍で、層は.*?(\d+)\s*層", txt)
    if not m:
        raise ValueError(f"表3 の前書きから対象が読めない: {txt[:80]!r}")
    return int(m.group(1).replace(",", "")), int(m.group(2)), int(m.group(3))


def strata_b(numbers: dict) -> int:
    return numbers["meta"]["criterion"]["strata_required"]


def family_name(fid: str, numbers: dict, lang: str) -> str:
    if lang == "en":
        return FAMILY_EN[fid]
    return next(r for r in numbers["tables"]["表3"]["rows"] if r["basis_id"] == fid)["basis_ja"]


def points_a(numbers: dict) -> list[dict]:
    """(a) 表3 の点: (基底の族, 成分数, NRMSE 中央値, |ρ|)。"""
    out = []
    for r in numbers["tables"]["表3"]["rows"]:
        out.append({"id": r["id"], "family": r["basis_id"], "m": r["n_components"]["value"],
                    "x": r["nrmse_median"]["value"], "y": r["dt_pwv"]["rho"], "strata": r["dt_pwv"]["strata"]})
    return out


def points_b(numbers: dict) -> list[dict]:
    """(b) 表6 の点: (版, 通過率, C 段の |ρ|)。特徴点法（通過率なし）は除く。"""
    out = []
    for r in numbers["tables"]["表6"]["rows"]:
        if r["pass_rate"].get("dash") or r["pass_rate"].get("value") is None:
            continue
        out.append({"id": r["id"], "group": LABELS["variants"][r["id"]]["group"], "no": LABELS["variants"][r["id"]]["no"],
                    "x": r["pass_rate"]["value"], "y": r["dt_pwv_C"]["rho"], "strata": r["dt_pwv_C"]["strata"]})
    return out


def a_label(p: dict) -> str:
    """(a) の点の注釈: 成分数と、括弧内に予測の向きを持った層の数／層の数（表3 の x/4）。"""
    return f"{p['m']} ({p['strata']})"


def b_label(p: dict) -> str:
    """(b) の点の注釈: 表6 の (n) の番号と、予測の向きを持った層の数／層の数（C 段の x/6）。"""
    return f"{p['no']} {p['strata']}"


def landmark_c(numbers: dict) -> float:
    return next(r for r in numbers["tables"]["表6"]["rows"] if r["id"] == "landmark")["dt_pwv_C"]["rho"]


def key_items(numbers: dict, lang: str) -> tuple[str, str]:
    """脚注の対応表の文字: (a) の族と記号、(b) の番号と短い名。"""
    tx = T[lang]
    a = tx["sep"].join(f"{FAMILY[f]['glyph']}{tx['eq']}{family_name(f, numbers, lang)}" for f in FAMILY_ORDER)
    b = tx["sep"].join(f"{p['no']} {LABELS['variants'][p['id']]['short_' + lang]}" for p in points_b(numbers))
    return a, b


# ---------------------------------------------------------------- 描画

def build(lang: str, numbers: dict):
    """図を組む。戻り値は (fig, (a) の点, (b) の点, 規準線の y, 特徴点法の線の y)。"""
    setup(lang)
    plt.rcParams.update({"xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
                         "font.family": list(plt.rcParams["font.family"]) + ["DejaVu Sans"]})
    crit = numbers["meta"]["criterion"]["min_median_abs_rho"]
    tx = T[lang]
    nsub, nbeat, ns_a = table3_subjects(numbers)
    n3, ns_b = type3_n(numbers), strata_b(numbers)
    lm = landmark_c(numbers)
    key_a, key_b = key_items(numbers, lang)

    footer_lines = [tx["key_a"].format(items=key_a), tx["key_b"].format(items=key_b, thr=crit),
                    tx["subjects"].format(nsub=f"{nsub:,}", nbeat=nbeat, ns_a=ns_a, n3=f"{n3:,}", ns_b=ns_b),
                    STAGE_NOTE[lang], LABELS["posthoc_note"][lang]]
    footer = "\n".join(wrap_text(s, lang) for s in footer_lines)
    n_footer = footer.count("\n") + 1
    footer_mm = n_footer * 8 * 1.3 / 72 * 25.4 + 2.5
    H_MM = TOP_MM + PANEL_H_MM + XAXIS_MM + footer_mm
    fig = plt.figure(figsize=(mm(W_MM), mm(H_MM)))
    y0, hf = (footer_mm + XAXIS_MM) / H_MM, PANEL_H_MM / H_MM
    ax_a = fig.add_axes([A_LEFT / W_MM, y0, A_W / W_MM, hf])
    ax_b = fig.add_axes([B_LEFT / W_MM, y0, B_W / W_MM, hf])

    # (a) 表3
    pa = points_a(numbers)
    ax_a.set_xscale("log")
    ax_a.set_xlim(*XLIM_A)
    ax_a.set_ylim(*YLIM_A)
    ax_a.set_xticks([0.005, 0.01, 0.02, 0.05])
    ax_a.set_xticklabels(["0.005", "0.01", "0.02", "0.05"])
    ax_a.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax_a.set_yticks([0, 0.2, 0.4, 0.6, 0.8])
    ax_a.set_yticklabels(["0", "0.2", "0.4", "0.6", "0.8"])
    ax_a.set_title(tx["title_a"].format(nbeat=nbeat), fontsize=8, loc="center", pad=3, linespacing=1.1)
    ax_a.set_xlabel(tx["xlabel_a"], fontsize=8)
    ax_a.set_ylabel(tx["ylabel_a"].format(ns=ns_a), fontsize=8)
    ax_a.axhline(crit, color=PALETTE["grey"], lw=0.8, ls=(0, (4, 2)), zorder=1)
    ax_a.text(XLIM_A[1] * 0.93, crit + 0.012, L[lang]["criterion"], ha="right", va="bottom", fontsize=8, color=PALETTE["grey"])
    drawn_a = []
    for fid in FAMILY_ORDER:
        pts = sorted([p for p in pa if p["family"] == fid], key=lambda p: p["m"])
        sty = FAMILY[fid]
        ax_a.plot([p["x"] for p in pts], [p["y"] for p in pts], color=sty["color"], lw=0.6, ls="-", zorder=2)
        ln, = ax_a.plot([p["x"] for p in pts], [p["y"] for p in pts], ls="none", marker=sty["marker"], ms=sty["ms"],
                        mfc=sty["mfc"], mec=sty["color"], mew=1.0, zorder=4 if sty["mfc"] != "white" else 3, label=fid)
        for p, x, y in zip(pts, ln.get_xdata(), ln.get_ydata()):
            dx, dy, ha = A_LABEL.get(p["id"], (sty["label_dx"], sty["label_dy"], sty["ha"]))
            lab = a_label(p)
            ax_a.annotate(lab, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", fontsize=8,
                          color=PALETTE["ink"])
            drawn_a.append({"id": p["id"], "family": fid, "m": p["m"], "x": float(x), "y": float(y), "label": lab})

    # (b) 表6
    pb = points_b(numbers)
    ax_b.set_xlim(*XLIM_B)
    ax_b.set_ylim(*YLIM_B)
    ax_b.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax_b.set_xticklabels(["0", "0.2", "0.4", "0.6", "0.8", "1.0"])
    ax_b.set_yticks([0, 0.2, 0.4, 0.6, 0.8])
    ax_b.set_yticklabels(["0", "0.2", "0.4", "0.6", "0.8"])
    ax_b.set_title(tx["title_b"].format(n3=f"{n3:,}"), fontsize=8, loc="center", pad=3, linespacing=1.1)
    ax_b.set_xlabel(tx["xlabel_b"], fontsize=8)
    ax_b.set_ylabel(tx["ylabel_b"].format(ns=ns_b), fontsize=8)
    ax_b.axhline(crit, color=PALETTE["grey"], lw=0.8, ls=(0, (4, 2)), zorder=1)
    ax_b.text(0.99, crit + 0.012, L[lang]["criterion"], ha="right", va="bottom", fontsize=8, color=PALETTE["grey"])
    ax_b.axhline(lm, color=PALETTE["landmark"], lw=0.8, ls=(0, (1, 1.6)), zorder=1)      # 点線（図5 の特徴点法の線と同じ）
    ax_b.text(0.99, lm + 0.012, tx["lm_line"].format(v=lm), ha="right", va="bottom", fontsize=8, color=PALETTE["landmark"])
    drawn_b = []
    for p in pb:
        sty = GROUP_STYLE[p["group"]]
        ln, = ax_b.plot([p["x"]], [p["y"]], ls="none", marker=sty["marker"], ms=MARKER_PT, mfc=sty["mfc"],
                        mec=sty["color"], mew=1.0, zorder=3, label=p["id"], clip_on=False)   # (8) の 0.012 が軸線に切られないように
        dx, dy, ha = B_LABEL.get(p["id"], (5, 0, "left"))
        lab = b_label(p)
        ax_b.annotate(lab, (p["x"], p["y"]), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center",
                      fontsize=8, color=PALETTE["ink"])
        drawn_b.append({"id": p["id"], "x": float(ln.get_xdata()[0]), "y": float(ln.get_ydata()[0]), "no": p["no"], "label": lab})

    fig.text(0.005, 1.2 / H_MM, footer, ha="left", va="bottom", fontsize=8, color=PALETTE["ink"], linespacing=1.3)
    return fig, drawn_a, drawn_b, crit, lm


# ---------------------------------------------------------------- 凡例文

def legend_text(lang: str, numbers: dict) -> str:
    thr = numbers["meta"]["criterion"]["min_median_abs_rho"]
    nsub, nbeat, ns_a = table3_subjects(numbers)
    n3, ns_b = f"{type3_n(numbers):,}", strata_b(numbers)
    lm = landmark_c(numbers)
    key_a, key_b = key_items(numbers, lang)
    src6 = re.sub(r"^出典[^:：]*[:：]\s*", "", numbers["tables"]["表6"].get("source_paragraph", ""))
    if lang == "ja":
        return "\n".join([
            "図7　当てはまりと真値への追従の関係 ― (a) 表3 の NRMSE 対 |ρ|、(b) 表6 の通過率 対 C 段の |ρ|",
            "",
            f"何を示すか: (a) 基底関数と成分数の総当たり（表3。{nsub} 名から取った型1（切痕あり）の {nbeat} 拍、層は 8 拍以上の {ns_a} 層）。"
            "横軸は波形への当てはまり（NRMSE の中央値、対数目盛。左ほど残差が小さい）、縦軸は ΔT × 大動脈脈波伝播速度の"
            f"年齢層内 Spearman |ρ| の中央値（全例＝C 段）。記号は基底の族（{key_a}）、数字は成分数（括弧内は予測の向きを持った層の数／層の数）、"
            "同じ族は成分数の順に細線で結ぶ。"
            f"(b) 拡張期の下降の扱いを変えた 12 の版（表6。型3 の {n3} 名・{ns_b} 層）。横軸は通過率（凍結版と同じ収束検算で採用になる割合＝"
            f"A 段に残る割合）、縦軸は C 段の |ρ|。番号は表6 の (n)（{key_b}）で、その右の数字は予測の向きを持った層の数／層の数。"
            "白抜きは下降を説明する項を足す案、塗りつぶしは下降を"
            "当てはめの対象から外す・残差の中で小さくする案、灰の四角は基準。朱の点線は特徴点法（同梱）の C 段の値"
            f"（{lm:.3f}）。両方の枠の灰の破線は規準 {thr:.2f}。(a) と (b) は対象が異なるので、値を直接は比べない。判定の札は図に書かず表に任せる。",
            "",
            "出典: `02_tables.md` 表3（31番 `analysis/scripts/31_pwdb_basis_explore.py`。結果の CSV は Mac の "
            "`data/pwdb/pwdb_basis_explore.csv`、lab_log 追記13）と表6（50番 `analysis/scripts/50_reservoir_bench.py` 節C。"
            "`docs/research/results/50_reservoir_bench_BC.txt`・`50_reservoir_bench_C14.txt`、lab_log 追記144・146・147・149・151・152）。"
            "数値は `data/paper2_numbers.json` から台本 `build_fig_tradeoff.py` が読む。",
            "",
            "段の注釈: " + STAGE_NOTE["ja"],
            "",
            "探索・事後の注記: " + LABELS["posthoc_note"]["ja"],
            "",
            f"表3 の前書き（02_tables.md）: {' '.join(numbers['tables']['表3']['preamble'])}",
            "",
            f"表6 の出典の記載（02_tables.md）: {src6}",
        ])
    return "\n".join([
        "Figure 7. Goodness of fit versus tracking of the reference quantity: (a) NRMSE against |ρ| from table 3; "
        "(b) pass rate against tier-C |ρ| from table 6.",
        "",
        f"What is shown: (a) the sweep of basis functions and component counts (table 3; {nbeat} type-1 beats, notch present, "
        f"from {nsub} subjects; {ns_a} strata with at least 8 beats). x, goodness of fit (median NRMSE, log scale; smaller residual "
        "to the left); y, median within-age-stratum Spearman |ρ| of ΔT with aortic PWV (all beats, i.e. tier C). Marker shape, basis "
        f"family ({key_a}); number, component count (in parentheses, the number of strata with the predicted sign over the number "
        "of strata evaluated); points of one family are joined in order of component count. "
        f"(b) the 12 variants that change how the diastolic decline is treated (table 6; the {n3} type-3 subjects, {ns_b} strata). "
        "x, pass rate (fraction accepted by the same convergence checks as the frozen version, i.e. remaining in tier A); y, tier-C |ρ|. "
        f"Numbers are the (n) of table 6 ({key_b}), each followed by the number of strata with the predicted sign over the number of "
        "strata evaluated. Open circles, add a term for the diastolic decline; filled circles, exclude or "
        "down-weight the diastolic decline; grey squares, reference fits. The vermilion dotted line is the tier-C value of the "
        f"database-supplied fiducial-point analysis ({lm:.3f}). The grey dashed line in both panels is the criterion {thr:.2f}. "
        "(a) and (b) are different subject sets, so their values are not compared directly. Verdicts are not written in the figure.",
        "",
        "Source: table 3 of `02_tables.md` (script 31 `analysis/scripts/31_pwdb_basis_explore.py`; result CSV "
        "`data/pwdb/pwdb_basis_explore.csv` on the Mac; lab_log entry 13) and table 6 (script 50 `analysis/scripts/50_reservoir_bench.py`, "
        "part C; `docs/research/results/50_reservoir_bench_BC.txt`, `50_reservoir_bench_C14.txt`; lab_log entries 144, 146, 147, 149, 151, 152). "
        "All numbers are read from `data/paper2_numbers.json` by `build_fig_tradeoff.py`.",
        "",
        "Tier note: " + STAGE_NOTE["en"],
        "",
        "Post-hoc note: " + LABELS["posthoc_note"]["en"],
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


def _verdict_hits(joined: str) -> list[str]:
    s = re.sub(r"(?i)pass\s*rate", "", joined)
    hits = [w for w in ("成立", "不成立") if w in s]
    hits += [m.group(0) for m in re.finditer(r"(?i)\b(pass|passed|fail|failed)\b", s)]
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
        fig, drawn_a, drawn_b, crit, lm = build(lang, load_numbers())
        fresh = load_numbers()
        ea = {p["id"]: p for p in points_a(fresh)}
        da = {p["id"]: p for p in drawn_a}
        rep("(a) の点の数が表3 の行の数（12）", len(drawn_a) == len(ea) == 12 == len(fresh["tables"]["表3"]["rows"]),
            f"描いた {len(drawn_a)}・期待 {len(ea)}")
        diff = [k for k in ea if k not in da or abs(da[k]["x"] - ea[k]["x"]) > 1e-12 or abs(da[k]["y"] - ea[k]["y"]) > 1e-12
                or da[k]["m"] != ea[k]["m"] or da[k]["family"] != ea[k]["family"]]
        rep("(a) の NRMSE・|ρ|・成分数・族が JSON と一致（全点）", not diff, f"差 {diff}")
        bad = [k for k in ea if da.get(k, {}).get("label") != a_label(ea[k])]
        rep("(a) の注釈が「成分数 (予測の向きを持った層の数／層の数)」で JSON の値（全点）", not bad, f"{bad}")
        eb = {p["id"]: p for p in points_b(fresh)}
        db = {p["id"]: p for p in drawn_b}
        rep("(b) の点の数が表6 の通過率を持つ行の数（12）", len(drawn_b) == len(eb) == 12, f"描いた {len(drawn_b)}・期待 {len(eb)}")
        diff = [k for k in eb if k not in db or abs(db[k]["x"] - eb[k]["x"]) > 1e-12 or abs(db[k]["y"] - eb[k]["y"]) > 1e-12
                or db[k]["no"] != eb[k]["no"]]
        rep("(b) の通過率・C 段の |ρ|・番号が JSON と一致（全点）", not diff, f"差 {diff}")
        bad = [k for k in eb if db.get(k, {}).get("label") != b_label(eb[k])]
        rep("(b) の注釈が「(番号) 予測の向きを持った層の数／層の数」で JSON の値（全点）", not bad, f"{bad}")
        rep("(b) の記号が群で分かれる（白抜き＝足す、塗りつぶし＝外す、灰＝基準）", all(
            (ln.get_markerfacecolor() == "white") == (LABELS["variants"][ln.get_label()]["group"] == "add")
            for ln in fig.axes[1].get_lines() if ln.get_label() in eb))
        rep("規準線が meta.criterion の値（両方の枠）", abs(crit - fresh["meta"]["criterion"]["min_median_abs_rho"]) < 1e-12
            and all(any(len(ln.get_ydata()) == 2 and all(abs(y - crit) < 1e-12 for y in ln.get_ydata()) for ln in ax.get_lines())
                    for ax in fig.axes[:2]))
        rep("特徴点法の横線が表6 の C 段の値", abs(lm - landmark_c(fresh)) < 1e-12 and any(
            len(ln.get_ydata()) == 2 and all(abs(y - lm) < 1e-12 for y in ln.get_ydata()) for ln in fig.axes[1].get_lines()))
        rep("(a) の横軸が対数目盛", fig.axes[0].get_xscale() == "log")
        texts = texts_of(fig)
        joined = "\n".join(texts)
        flat = joined.replace("\n", "")
        bad_font = check_min_font(fig)
        rep(f"文字はすべて {common.MIN_FONT_PT:g} pt 以上", not bad_font, f"{bad_font[:3]}")
        rep("段の注釈が脚注にある", STAGE_NOTE[lang].replace(" ", "") in flat.replace(" ", ""))
        rep("探索・事後の注記が脚注にある", LABELS["posthoc_note"][lang].replace(" ", "") in flat.replace(" ", ""))
        nsub, nbeat, ns_a = table3_subjects(fresh)
        rep("対象の違い（表3 の拍数・被験者数・層、型3 の人数・層）が脚注にある",
            all(str(v) in flat for v in (nbeat, nsub, ns_a, strata_b(fresh))) and f"{type3_n(fresh):,}" in flat)
        rep("規準線の札が両方の枠にある", sum(1 for t in texts if t == L[lang]["criterion"]) == 2)
        rep("特徴点法の線の札に表6 の C 段の値がある", f"{landmark_c(fresh):.3f}" in flat)
        vh = _verdict_hits(joined)
        rep("判定の語（成立・不成立・pass・fail）を図に書いていない", not vh, f"{vh}")
        key_a, key_b = key_items(fresh, lang)
        rep("(b) の番号と短い名（labels.json）の対応表が脚注にある", "".join(key_b.split()) in "".join(flat.split()))
        rep("(a) の族の対応表（表3 の基底名）が脚注にある", "".join(key_a.split()) in "".join(flat.split()))
        ov = text_overlaps(fig)
        rep("文字どうしの重なりが無い（描画器の寸法で確認）", not ov, f"{ov[:4]}")
        om = text_marker_overlaps(fig)
        rep("文字と記号の重なりが無い（描画器の寸法で確認）", not om, f"{om[:4]}")
        outside = texts_outside(fig)
        rep("図の縁からはみ出す文字が無い", not outside, f"{outside[:3]}")
        leg = legend_text(lang, fresh)
        if banned is None:
            print("  （用語検査器が無いので禁止語の確認は飛ばした）")
        else:
            hits = _banned_hits(banned, texts + [leg])
            rep("図と凡例文に禁止語が無い（検査器の表）", not hits, f"{hits[:3]}")
        cjk = re.findall(r"[^\n]*[぀-ヿ一-鿿][^\n]*", joined + "\n" + leg) if lang == "en" else []
        rep("英文の図と凡例文に和文が混じっていない", not cjk, f"{cjk[:2]}")
        w_in, h_in = fig.get_size_inches()
        rep("図の幅が 150 mm", abs(w_in * 25.4 - 150) < 0.01)
        print(f"  （図の高さ {h_in * 25.4:.0f} mm）")
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
        fig, *_rest = build(lang, numbers)
        paths = save(fig, NAME, lang)
        plt.close(fig)
        lp = common.OUT / f"{NAME}_legend_{lang}.txt"
        lp.write_text(legend_text(lang, numbers) + "\n", encoding="utf-8")
        for p in paths + [lp]:
            print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())

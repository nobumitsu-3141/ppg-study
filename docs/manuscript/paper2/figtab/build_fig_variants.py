#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""図5 改良案ごとの |ρ|（表6）― 拡張期の下降の扱いを変えた 13 行を、A 段と C 段の点で並べる。

左の枠が ΔT × 大動脈PWV、右の枠が RI × 末梢血管抵抗。縦は表6 の 13 行（表の順）で、
labels.json の variant_groups（基準／下降を説明する項を足す／下降を当てはめの対象から外す・残差の中で小さくする／参考）
ごとに見出しを置く。行名は labels.json の variants[*].short_ja / short_en に (n) の番号を前置したもの。
各行で A 段は白抜き、C 段は塗りつぶしの記号で描き、細線で結ぶ。記号の横に予測の向きを持った層の数（x/6）を添える。
規準線 0.30 を引き、特徴点法（同梱・C 段のみ）は PALETTE["landmark"] で描く。
右端の 2 つの欄に通過率と、同梱の特徴点との ΔT の差（ms・A 段）を印字する。
値はすべて `data/paper2_numbers.json`（`../02_tables.md` を機械で読んだもの）から取り、手で打たない。
表6 は探索・事後なので、脚注にその旨と段の注釈（CLAUDE.md §3）を置く。判定（成立・不成立）は図に書かない。

使い方
    python3 build_fig_variants.py                 和文・英文の両方を out/ に書く
    python3 build_fig_variants.py --lang en       英文だけ
    python3 build_fig_variants.py --selftest      描いた値と JSON の一致・最小文字サイズ・注釈・禁止語・文字の重なりを確かめる
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                  # noqa: E402
from matplotlib.lines import Line2D                              # noqa: E402
from matplotlib.transforms import blended_transform_factory      # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common                                                    # noqa: E402
from common import (PALETTE, L, STAGE_NOTE, mm, setup, save, load_numbers,   # noqa: E402
                    check_min_font, texts_of, text_overlaps, text_marker_overlaps, texts_outside,
                    wrap_text, _wrap_ja)

NAME = "fig_variants"
REPO = HERE.parents[3]
LABELS = json.loads((HERE / "data" / "labels.json").read_text(encoding="utf-8"))

COLS = ("dt_pwv", "ri_pvr")
STAGES = ("A", "C")

# 行の寸法（pt と「行の単位」）。副行（A 段が上・C 段が下）を持つので 1 行を 14 pt にし、
# 副行の中心を 9.2 pt 離す（8 pt の数字が重ならない間隔）
UNIT_PT = 14.0
SUB = 0.33                       # 副行の中心からのずれ（行の単位）
HEAD_H = {1: 0.75, 2: 1.4}       # 見出し行の高さ（見出しの行数ごと）
BOTTOM_SLOT = 0.8                # 規準線の札を置く最下段
XMIN, XMAX = -0.2, 1.1           # 横軸。0 の点（(8) の C 段 0.012）が軸に切られないよう、また記号の左に置く注釈の
                                 # 場所を取るため 0 より左から（軸線は 0〜1.0 だけ描く）

# 横の寸法（mm）。合計 150 mm（二段幅）
W_MM = 150.0
LABEL_MM, GAP_L, PANEL_MM, GAP_AB, GAP_R, RIGHT_MM, MARGIN_R = 41.0, 1.5, 34.0, 5.0, 2.5, 30.0, 2.0
assert abs(LABEL_MM + GAP_L + 2 * PANEL_MM + GAP_AB + GAP_R + RIGHT_MM + MARGIN_R - W_MM) < 1e-9
PASS_X = 0.18                    # 右端の欄の中の通過率の列の位置（欄の幅に対する割合）。差の列は右端にそろえる
MARKER_PT = 4.6                  # 記号の大きさ（pt）
ANN_GAP_PT = 4.0                 # 記号と注釈の間（pt）

# 図の中の語（和・英）。行名・段・注釈は labels.json から取る
T = {
    "ja": {
        "title_dt": "(a) ΔT × 大動脈PWV",
        "title_ri": "(b) RI × 末梢血管抵抗",
        "pass_head": "通過率",
        "offset_head": "特徴点との\nΔT の差 [ms]\n（A 段）",
        "ref_offset": "0（基準）",
        "lm_line": "特徴点法",
        "legend": ("白抜き＝A 段、塗りつぶし＝C 段（同じ案の両段を細線で結ぶ）。■＝特徴点法（同梱・C 段のみ）、縦の点線はその C 段の値。"
                   "数字＝予測の向きを持った層の数／層の数。右の欄＝通過率（A 段に残る割合）と、同梱の特徴点との ΔT の差（A 段）。"),
        "n_note": "型3・{n} 名。値は表6（02_tables.md）。",
    },
    "en": {
        "title_dt": "(a) ΔT × aortic PWV",
        "title_ri": "(b) RI × peripheral\nvascular resistance",
        "pass_head": "Pass\nrate",
        "offset_head": "ΔT offset vs\nfiducial point\n[ms] (tier A)",
        "ref_offset": "0 (reference)",
        "lm_line": "Fiducial-point",
        "legend": ("Open, tier A; filled, tier C (joined by a thin line). Square and dotted line, fiducial-point analysis "
                   "(database-supplied, tier C only). Fraction beside a marker, strata with the predicted sign / strata evaluated. "
                   "Right, pass rate (fraction remaining in tier A) and ΔT offset from the fiducial point (tier A)."),
        "n_note": "Type 3, n = {n}. Values from table 6 of 02_tables.md.",
    },
}


# ---------------------------------------------------------------- 文字の折り返し

def row_label(rid: str, lang: str) -> str:
    """labels.json の短い行名（short_ja / short_en）に (n) の番号を前置する（文字は変えない）。"""
    v = LABELS["variants"][rid]
    s = v["short_" + lang]
    return (v["no"] + " " + s) if v["no"] else s


def wrap_heading(s: str, lang: str) -> str:
    """見出しを左の欄に収める。和文は 17 字を超えるとき「・」の後ろで折る。英文は 32 字で折る。"""
    if lang == "ja":
        if sum(2 if ord(c) > 0x2E7F else 1 for c in s) <= 34:
            return s
        if "・" in s:
            a, b = s.split("・", 1)
            return a + "・\n" + b
        return _wrap_ja(s, 34)
    return "\n".join(textwrap.wrap(s, width=32, break_long_words=False, break_on_hyphens=False))


# ---------------------------------------------------------------- 値の読み出し

def type3_n(numbers: dict) -> int:
    """型3 の被験者数（表5 の行 type3 の n）。"""
    return next(r for r in numbers["tables"]["表5"]["rows"] if r["id"] == "type3")["n"]


def offset_text(cell: dict, lang: str) -> str:
    """同梱の特徴点との ΔT の差の欄の文字。単位は見出しにあるので値だけ。"""
    if cell.get("note"):
        return T[lang]["ref_offset"]
    return f"{cell['value']:+.1f}"


def pass_text(cell: dict) -> str:
    return cell["raw"] if cell.get("dash") else f"{cell['value']:.3f}"


def expected_points(numbers: dict) -> list[dict]:
    """表6 から描くべき点を起こす（自己検査でも同じ関数で JSON を読み直して比べる）。"""
    pts = []
    for row in numbers["tables"]["表6"]["rows"]:
        for col in COLS:
            for st in STAGES:
                cell = row[f"{col}_{st}"]
                if cell.get("rho") is not None:
                    pts.append({"id": row["id"], "col": col, "stage": st, "x": cell["rho"], "strata": cell["strata"]})
    return pts


def plan_rows(numbers: dict, lang: str) -> tuple[list[dict], float]:
    """表6 の行の順に、見出し行とデータ行の縦位置を決める。戻り値は (項目の一覧, 全体の高さ)。"""
    items, y, prev = [], 0.0, None
    for row in numbers["tables"]["表6"]["rows"]:
        g = LABELS["variants"][row["id"]]["group"]
        if g != prev:
            head = wrap_heading(LABELS["variant_groups"][g][lang], lang)
            h = HEAD_H[min(2, head.count("\n") + 1)]
            items.append({"kind": "head", "group": g, "label": head, "top": y, "h": h})
            y += h
            prev = g
        items.append({"kind": "row", "row": row, "label": row_label(row["id"], lang), "top": y, "h": 1.0})
        y += 1.0
    return items, y


# ---------------------------------------------------------------- 描画

_MEASURE_CACHE: dict = {}


def measure_pt(_ax, s: str, fontsize: float = 8.0) -> float:
    """文字 s を描いたときの幅（pt）を描画器で測る（図を描く前に注釈の置き場所を決めるため）。

    本体の図を途中で描くと Axis に余分な目盛が残るので、別の小さな図で測る。
    """
    key = (tuple(plt.rcParams["font.family"]), s, fontsize)
    if key not in _MEASURE_CACHE:
        f = plt.figure(figsize=(1, 1))
        t = f.text(0, 0, s, fontsize=fontsize)
        f.canvas.draw()
        w_px = t.get_window_extent(renderer=f.canvas.get_renderer()).width
        _MEASURE_CACHE[key] = w_px * 72 / f.dpi
        plt.close(f)
    return _MEASURE_CACHE[key]


def build(lang: str, numbers: dict):
    """図を組む。戻り値は (fig, 描いた点の一覧, 右端の欄の文字, 規準線の x, 行名の一覧)。"""
    setup(lang)
    plt.rcParams.update({"xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
                         "font.family": list(plt.rcParams["font.family"]) + ["DejaVu Sans"]})
    t6 = numbers["tables"]["表6"]
    crit = numbers["meta"]["criterion"]["min_median_abs_rho"]
    tx = T[lang]
    items, total = plan_rows(numbers, lang)
    lm_row = next(r for r in t6["rows"] if r["id"] == "landmark")

    footer_lines = [tx["legend"], STAGE_NOTE[lang], LABELS["posthoc_note"][lang],
                    tx["n_note"].format(n=f"{type3_n(numbers):,}")]
    footer = "\n".join(wrap_text(s, lang) for s in footer_lines)
    n_footer = footer.count("\n") + 1

    # 縦の寸法（mm）。行の高さは pt で固定し、図の高さをそこから決める
    plot_mm = (total + BOTTOM_SLOT) * UNIT_PT / 72 * 25.4
    top_mm, xaxis_mm = 10.5, 10.5           # 上: 右端の欄の 3 行の見出し。下: 目盛の数字と横軸の名
    footer_mm = n_footer * 8 * 1.3 / 72 * 25.4 + 2.5
    H_MM = top_mm + plot_mm + xaxis_mm + footer_mm
    fig = plt.figure(figsize=(mm(W_MM), mm(H_MM)))
    y0 = (footer_mm + xaxis_mm) / H_MM
    hf = plot_mm / H_MM
    ax_a = fig.add_axes([(LABEL_MM + GAP_L) / W_MM, y0, PANEL_MM / W_MM, hf])
    ax_b = fig.add_axes([(LABEL_MM + GAP_L + PANEL_MM + GAP_AB) / W_MM, y0, PANEL_MM / W_MM, hf])
    ax_r = fig.add_axes([(W_MM - MARGIN_R - RIGHT_MM) / W_MM, y0, RIGHT_MM / W_MM, hf])
    axes = {"dt_pwv": ax_a, "ri_pvr": ax_b}
    titles = {"dt_pwv": tx["title_dt"], "ri_pvr": tx["title_ri"]}
    for ax in (ax_a, ax_b, ax_r):
        ax.patch.set_visible(False)         # 見出しの区切り線が枠の下で途切れないように、枠の背景を描かない

    drawn, right_cells, labels_drawn = [], [], []
    head_y = items[0]["top"] + items[0]["h"] / 2        # 最初の見出し行（特徴点法の線の札を置く）
    pt_per_unit = (PANEL_MM / 25.4 * 72) / (XMAX - XMIN)
    for col, ax in axes.items():
        ax.set_xlim(XMIN, XMAX)
        ax.set_ylim(total + BOTTOM_SLOT, -0.05)
        ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_xticklabels(["0", "0.2", "0.4", "0.6", "0.8", "1.0"])
        ax.spines["bottom"].set_bounds(0, 1.0)
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.set_title(titles[col], fontsize=8, loc="center", linespacing=1.1)
        # 規準線（全高）と、特徴点法の C 段の値の縦線（データ行の範囲だけ。最下段の規準の札と交わらないように）
        ax.axvline(crit, color=PALETTE["grey"], lw=0.8, ls=(0, (4, 2)), zorder=1)
        ax.text(crit + 0.03, total + BOTTOM_SLOT * 0.55, L[lang]["criterion"], ha="left", va="center",
                fontsize=8, color=PALETTE["grey"])
        lm_x = lm_row[f"{col}_C"]["rho"]
        ax.plot([lm_x, lm_x], [-0.05, total], color=PALETTE["landmark"], lw=0.8, ls=(0, (1, 1.6)), zorder=1)
        ax.text(lm_x + 0.03, head_y, tx["lm_line"], ha="left", va="center", fontsize=8, color=PALETTE["landmark"])

        # 層の数の注釈は記号の右に置く。下の副行（C 段）の注釈・記号と次の行の上の副行（A 段）の注釈・記号は
        # 縦に近いので、横に近いときは一方の注釈を記号の左に移す（左に置くと枠の左端からはみ出すときは、
        # 右側の注釈を相手の記号を越えるまで右へずらす）。注釈の幅は描画器で測る
        side, nudge = {}, {}
        for it in items:
            if it["kind"] == "row":
                for st in STAGES:
                    side[(it["row"]["id"], st)] = "right"
                    nudge[(it["row"]["id"], st)] = 0.0
        r_pt = MARKER_PT / 2 + 0.6                       # 記号の半径と余白（pt）

        def fits_left(x, w):
            # 左端から 0.02（約 1.5 pt。枠と行名の欄の間の余白）まではみ出してよい
            return x - (ANN_GAP_PT + w) / pt_per_unit >= XMIN - 0.02

        for it, nxt in zip(items, items[1:]):
            if it["kind"] != "row" or nxt["kind"] != "row":
                continue
            cc, na = it["row"][f"{col}_C"], nxt["row"][f"{col}_A"]
            if cc.get("rho") is None or na.get("rho") is None:
                continue
            kc, ka = (it["row"]["id"], "C"), (nxt["row"]["id"], "A")
            w_c, w_a = measure_pt(ax, cc["strata"]), measure_pt(ax, na["strata"])
            d = (cc["rho"] - na["rho"]) * pt_per_unit        # C 段の記号が A 段の記号より右にある分（pt）
            a_hits = (ANN_GAP_PT - r_pt < d < ANN_GAP_PT + w_a + r_pt) or (-w_c < d < w_a)
            c_hits = (ANN_GAP_PT - r_pt < -d < ANN_GAP_PT + w_c + r_pt) or (-w_c < d < w_a)
            if not (a_hits or c_hits):
                continue
            if d > 1.7:                                   # A 段の注釈が C 段の記号に掛かる → A を左へ
                if fits_left(na["rho"], w_a):
                    side[ka] = "left"
                else:                                     # 入らなければ C 段の記号と注釈を越えるまで右へ
                    nudge[ka] += d + (ANN_GAP_PT + w_c if side[kc] == "right" else r_pt) + 1.0
            elif d < -1.7:                                # C 段の注釈が A 段の記号に掛かる → C を左へ
                if fits_left(cc["rho"], w_c):
                    side[kc] = "left"
                else:
                    nudge[kc] += -d + (ANN_GAP_PT + w_a if side[ka] == "right" else r_pt) + 1.0
            else:                                         # 記号がほぼ同じ x: 注釈どうしが重なる
                if fits_left(cc["rho"], w_c):
                    side[kc] = "left"
                elif fits_left(na["rho"], w_a):
                    side[ka] = "left"
                else:
                    nudge[kc] += w_a - d + 1.0

        for it in items:
            yc = it["top"] + it["h"] / 2
            if it["kind"] == "head":
                continue
            row = it["row"]
            is_lm = row["id"] == "landmark"
            color = PALETTE["landmark"] if is_lm else PALETTE["pda"]
            marker = "s" if is_lm else "o"
            ca, cc = row[f"{col}_A"], row[f"{col}_C"]
            has_a, has_c = ca.get("rho") is not None, cc.get("rho") is not None

            def put(cell, stage, y, filled):
                ln, = ax.plot([cell["rho"]], [y], marker=marker, ms=MARKER_PT, ls="none",
                              mfc=color if filled else "white", mec=color, mew=1.0, zorder=3)
                left = side[(row["id"], stage)] == "left"
                ax.annotate(cell["strata"], (cell["rho"], y),
                            xytext=(-ANN_GAP_PT if left else ANN_GAP_PT + nudge[(row["id"], stage)], 0),
                            textcoords="offset points", ha="right" if left else "left", va="center",
                            fontsize=8, color=PALETTE["ink"])
                drawn.append({"id": row["id"], "col": col, "stage": stage,
                              "x": float(ln.get_xdata()[0]), "strata": cell["strata"]})

            if has_a and has_c:
                ya, yc2 = yc - SUB, yc + SUB
                ax.plot([ca["rho"], cc["rho"]], [ya, yc2], color=PALETTE["light"], lw=0.8, zorder=2)
                put(ca, "A", ya, False)
                put(cc, "C", yc2, True)
            elif has_c:
                put(cc, "C", yc, True)

    # 行名・見出し・区切り線（左の欄）。x は図の座標、y は左の枠のデータ座標
    tr = blended_transform_factory(fig.transFigure, ax_a.transData)
    x_label_right = LABEL_MM / W_MM
    for it in items:
        yc = it["top"] + it["h"] / 2
        if it["kind"] == "head":
            fig.add_artist(Line2D([0.005, (W_MM - MARGIN_R) / W_MM], [it["top"], it["top"]], transform=tr,
                                  color=PALETTE["light"], lw=0.5, zorder=0))
            fig.text(0.005, yc, it["label"], transform=tr, ha="left", va="center", fontsize=8,
                     color=PALETTE["ink"], linespacing=1.1)
        else:
            fig.text(x_label_right, yc, it["label"], transform=tr, ha="right", va="center",
                     fontsize=8, color=PALETTE["ink"])
            labels_drawn.append(it["label"])
            # 右端の欄: 通過率と、同梱の特徴点との ΔT の差（A 段）。列ごとに別の x に置く
            p_txt = pass_text(it["row"]["pass_rate"])
            o_txt = offset_text(it["row"]["dt_offset_vs_landmark_ms_A"], lang)
            ax_r.text(PASS_X, yc, p_txt, ha="center", va="center", fontsize=8, color=PALETTE["ink"])
            ax_r.text(1.0, yc, o_txt, ha="right", va="center", fontsize=8, color=PALETTE["ink"])
            right_cells.append({"id": it["row"]["id"], "pass": p_txt, "offset": o_txt})
    ax_r.set_xlim(0, 1)
    ax_r.set_ylim(total + BOTTOM_SLOT, -0.05)
    ax_r.axis("off")
    # 欄の見出し（枠の上端にそろえる。長い見出しは 2〜3 行）
    ax_r.text(PASS_X, 1.0, tx["pass_head"], ha="center", va="bottom", fontsize=8, linespacing=1.1,
              transform=ax_r.transAxes)
    ax_r.text(1.0, 1.0, tx["offset_head"], ha="right", va="bottom", fontsize=8, linespacing=1.1,
              transform=ax_r.transAxes)

    # 横軸の名は目盛の数字の下（軸から 6.5 mm 下に上端をそろえる）
    x_mid = (LABEL_MM + GAP_L + PANEL_MM + GAP_AB / 2) / W_MM
    fig.text(x_mid, y0 - 6.5 / H_MM, L[lang]["rho"], ha="center", va="top", fontsize=8)
    fig.text(0.005, 1.2 / H_MM, footer, ha="left", va="bottom", fontsize=8, color=PALETTE["ink"], linespacing=1.3)
    return fig, drawn, right_cells, crit, labels_drawn


# ---------------------------------------------------------------- 凡例文

def legend_text(lang: str, numbers: dict) -> str:
    t6 = numbers["tables"]["表6"]
    thr = numbers["meta"]["criterion"]["min_median_abs_rho"]
    n = f"{type3_n(numbers):,}"
    n_all = f"{numbers['meta']['n_subjects_decision_test']:,}"
    if lang == "ja":
        return "\n".join([
            f"図5　改良案ごとの関連 ― 表6（型3・{n} 名）の年齢層内 Spearman |ρ| の中央値を A 段・C 段で並べる",
            "",
            f"何を示すか: 決定試験の {n_all} 名のうち波形の型3（変曲点のみ）の {n} 名について、拡張期の下降の扱いを変えた"
            "分解法の 12 の版と、参考の特徴点法（同梱）を、表6 の順に縦に並べる。見出しは labels.json の variant_groups"
            "（基準／下降を説明する項を足す／下降を当てはめの対象から外す・残差の中で小さくする／参考）、行名は同じ表の短い名"
            "（short_ja）に表6 の (n) の番号を前置したもの。"
            "(a) は ΔT × 大動脈脈波伝播速度、(b) は RI × 末梢血管抵抗。各行で白抜きが A 段、塗りつぶしが C 段で、細線で結ぶ。"
            f"記号の横の数字は予測の向きを持った層の数／層の数。破線は規準 {thr:.2f}。特徴点法は C 段のみ（四角）で、縦の点線はその値。"
            "右端の 2 つの欄は通過率（凍結版と同じ収束検算を当てたときに採用になる割合＝A 段に残る割合）と、"
            "同梱の特徴点との ΔT の差（ms・A 段）。判定の札は図に書かず表に任せる。",
            "",
            "出典: `02_tables.md` 表6。50番 `analysis/scripts/50_reservoir_bench.py` 節C"
            "（`docs/research/results/50_reservoir_bench_BC.txt`・`50_reservoir_bench_C14.txt`、"
            "lab_log 追記144・146・147・149・151・152）。数値は `data/paper2_numbers.json` から台本 `build_fig_variants.py` が読む。",
            "",
            "段の注釈: " + STAGE_NOTE["ja"],
            "",
            "探索・事後の注記: " + LABELS["posthoc_note"]["ja"],
            "",
            f"表6 の前書き（02_tables.md）: {t6['preamble'][0]}",
        ])
    return "\n".join([
        f"Figure 5. Association by variant: median within-age-stratum Spearman |ρ| of table 6 (type 3, n = {n}) in tiers A and C.",
        "",
        f"What is shown: for the {n} type-3 subjects (inflection only) among the {n_all} of the decision test, the 12 "
        "decomposition variants that change how the diastolic decline is treated, and the database-supplied fiducial-point "
        "analysis as a reference, in the order of table 6. Group headings follow variant_groups of labels.json (reference fits / "
        "add a term for the diastolic decline / exclude or down-weight the diastolic decline / reference); row labels are the "
        "short names (short_en) of the same file prefixed with the (n) numbering of table 6. (a) ΔT × aortic PWV; "
        "(b) RI × peripheral vascular resistance. In each row the open marker is tier A and the filled marker is tier C, joined by "
        "a thin line. The fraction beside a marker is the number of strata with the predicted sign over the number of strata "
        f"evaluated. The dashed line is the criterion {thr:.2f}. "
        "The fiducial-point analysis has tier C only (square); the dotted vertical line marks its value. The two right columns give the "
        "pass rate (fraction accepted by the same convergence checks as the frozen version, i.e. remaining in tier A) and the ΔT "
        "offset from the database-supplied fiducial point (ms, tier A). Verdicts are not written in the figure.",
        "",
        "Source: table 6 of `02_tables.md`. Script 50 `analysis/scripts/50_reservoir_bench.py`, part C "
        "(`docs/research/results/50_reservoir_bench_BC.txt`, `50_reservoir_bench_C14.txt`; lab_log entries 144, 146, 147, 149, 151, 152). "
        "All numbers are read from `data/paper2_numbers.json` by `build_fig_variants.py`.",
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
    """判定の語。通過率（pass rate）は量の名なので除く。"""
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
        fig, drawn, right_cells, crit, labels_drawn = build(lang, load_numbers())
        fresh = load_numbers()
        exp = expected_points(fresh)
        key = lambda p: (p["id"], p["col"], p["stage"])   # noqa: E731
        d = {key(p): (p["x"], p["strata"]) for p in drawn}
        e = {key(p): (p["x"], p["strata"]) for p in exp}
        rep("描いた点の数が表6 から起こした数と同じ（13 行 × 2 枠、A・C 段）", len(drawn) == len(exp) == len(d),
            f"描いた {len(drawn)}・期待 {len(exp)}")
        diff = [k for k in e if k not in d or abs(d[k][0] - e[k][0]) > 1e-12 or d[k][1] != e[k][1]]
        rep("描いた |ρ| と層の数の注釈が JSON と一致（全点）", not diff, f"差 {diff}")
        rows = fresh["tables"]["表6"]["rows"]
        rep("行の数が 13 で表の順", [c["id"] for c in right_cells] == [r["id"] for r in rows] and len(rows) == 13)
        bad_r = []
        for c, r in zip(right_cells, rows):
            pr, of = r["pass_rate"], r["dt_offset_vs_landmark_ms_A"]
            if pr.get("dash"):
                bad_r += [] if c["pass"] == pr["raw"] else [c["id"]]
            else:
                bad_r += [] if abs(float(c["pass"]) - pr["value"]) < 1e-12 else [c["id"]]
            if of.get("note"):
                bad_r += [] if c["offset"].startswith("0") else [c["id"]]
            else:
                bad_r += [] if abs(float(c["offset"]) - of["value"]) < 1e-12 and c["offset"][0] in "+-" else [c["id"]]
        rep("右端の欄（通過率・特徴点との差）が JSON の値", not bad_r, f"{bad_r}")
        rep("規準線が meta.criterion の値", abs(crit - fresh["meta"]["criterion"]["min_median_abs_rho"]) < 1e-12)
        xmin_plotted = min(p["x"] for p in drawn)
        xl = fig.axes[0].get_xlim()
        rep("描いた最小の |ρ| が横軸の左端より内側（記号が軸に切られない）", xl[0] < xmin_plotted - 0.02, f"xlim {xl}")
        texts = texts_of(fig)
        joined = "\n".join(texts)
        flat = joined.replace("\n", "")
        bad_font = check_min_font(fig)
        rep(f"文字はすべて {common.MIN_FONT_PT:g} pt 以上", not bad_font, f"{bad_font[:3]}")
        rep("段の注釈が脚注にある", STAGE_NOTE[lang].replace(" ", "") in flat.replace(" ", ""))
        rep("探索・事後の注記が脚注にある", LABELS["posthoc_note"][lang].replace(" ", "") in flat.replace(" ", ""))
        n3 = f"{type3_n(fresh):,}"
        rep("型3 の被験者数（表5 の n）が脚注にある", n3 in flat)
        rep("規準線の札がある", L[lang]["criterion"] in texts)
        rep("特徴点法の縦線の札がある（両方の枠。行名にも同じ語があるので 2 つ以上）",
            sum(1 for t in texts if t == T[lang]["lm_line"]) >= 2)
        vh = _verdict_hits(joined)
        rep("判定の語（成立・不成立・pass・fail）を図に書いていない", not vh, f"{vh}")
        want = [row_label(r["id"], lang) for r in rows]
        rep("行名が labels.json の variants の短い名（(n) を前置）と同じ（表の順）、各 1 行", labels_drawn == want
            and not any("\n" in s for s in labels_drawn), f"{labels_drawn[:3]} != {want[:3]}")
        heads = ["".join(LABELS["variant_groups"][g][lang].split()) for g in ("base", "add", "remove", "ref")]
        rep("4 つの見出し（variant_groups）がある（折り返しは改行だけ）",
            all(h in "".join(flat.split()) for h in heads))
        rep("枠の題が labels の短い語（1 行の (a)、(b) は 2 行まで）", T[lang]["title_dt"] in texts and T[lang]["title_ri"] in texts
            and "\n" not in T[lang]["title_dt"])
        rep("右端の 2 欄の見出しが別の文字として両方ある", T[lang]["pass_head"] in texts and T[lang]["offset_head"] in texts)
        lm = next(r for r in rows if r["id"] == "landmark")
        rep("特徴点法の縦線の x が表6 の C 段の値（2 点とも）", all(
            any(len(ln.get_xdata()) == 2 and all(abs(x - lm[f"{col}_C"]["rho"]) < 1e-12 for x in ln.get_xdata())
                and ln.get_marker() in ("None", "", None) for ln in ax.get_lines())
            for col, ax in zip(COLS, fig.axes[:2])))
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

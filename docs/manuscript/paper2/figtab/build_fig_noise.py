#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""図6 雑音への頑健性（表6c）― 3 つの当てはめ × 3 つの段 × 雑音 0・1・2% を 2 × 3 の枠に並べる。

上の行が ΔT × 大動脈PWV、下の行が RI × 末梢血管抵抗。列は A 段・B 段・C 段。横軸は雑音（拍の振幅に対する
標準偏差の比、%）、縦軸は年齢層内 Spearman |ρ| の中央値。凍結版（灰・丸）、拍長の 0.65 倍で打ち切る版
（PALETTE["pda"]・四角）、残差を 1 次微分の領域で取る版（PALETTE["amp"]・三角）を記号つきの線で描く。
特徴点法（同梱）は B 段と C 段だけにあり、雑音を足す前の拍の値なので点線（PALETTE["landmark"]・菱形）で描き、
脚注にその旨を書く。規準線 0.30（灰の破線）を引く。通過率（A 段に残る割合）は A 段の枠の中に 3 つの当てはめごとに印字する。
値はすべて `data/paper2_numbers.json`（`../02_tables.md` を機械で読んだもの）から取り、手で打たない。
表6c は探索・事後なので、脚注にその旨と段の注釈（CLAUDE.md §3。B 段の人数と、B 段が 3 つの当てはめの採用を重ねた
分解に有利な部分集合であること）を置く。判定（成立・不成立）は図に書かない。

使い方
    python3 build_fig_noise.py                 和文・英文の両方を out/ に書く
    python3 build_fig_noise.py --lang en       英文だけ
    python3 build_fig_noise.py --selftest      描いた値と JSON の一致・最小文字サイズ・注釈・禁止語・文字の重なりを確かめる
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
from matplotlib.gridspec import GridSpec             # noqa: E402
from matplotlib.lines import Line2D                  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common                                        # noqa: E402
from common import (PALETTE, L, STAGE_NOTE, mm, setup, save, load_numbers,   # noqa: E402
                    check_min_font, texts_of, text_overlaps, text_marker_overlaps, texts_outside, wrap_text)

NAME = "fig_noise"
REPO = HERE.parents[3]
LABELS = json.loads((HERE / "data" / "labels.json").read_text(encoding="utf-8"))

COLS = ("dt_pwv", "ri_pvr")                 # 行（上: ΔT、下: RI）
STAGES = ("A", "B", "C")                    # 列
METHODS = ("fb", "trunc065", "deriv", "landmark")
# 当てはめごとの色・記号・線種（色だけに頼らない: 記号の形と線種で区別できる）
STYLE = {
    "fb": {"color": PALETTE["grey"], "marker": "o", "ls": "-", "mfc": PALETTE["grey"]},
    "trunc065": {"color": PALETTE["pda"], "marker": "s", "ls": "-", "mfc": PALETTE["pda"]},
    "deriv": {"color": PALETTE["amp"], "marker": "^", "ls": "-", "mfc": PALETTE["amp"]},
    "landmark": {"color": PALETTE["landmark"], "marker": "D", "ls": (0, (1, 1.6)), "mfc": "white"},   # 点線（破線は規準線だけ）
}
GLYPH = {"fb": "●", "trunc065": "■", "deriv": "▲"}     # A 段の枠の通過率の行頭に置く記号（マーカーと同じ形）
MARKER_PT = 4.5
XMIN, XMAX = -0.3, 2.3                      # 横軸は雑音の 3 水準を等間隔に置く（0・1・2）
YMAX = 0.92

# 図の寸法（mm）。二段幅 150 mm
W_MM = 150.0
LEFT_MM, RIGHT_MM, WSPACE_MM = 17.0, 2.0, 5.0
PANEL_H_MM, HSPACE_MM, TOP_MM = 44.0, 7.5, 10.5
XAXIS_MM = 10.5

T = {
    "ja": {
        "row": {"dt_pwv": "ΔT × 大動脈PWV", "ri_pvr": "RI × 末梢血管抵抗"},
        "xlabel": "雑音（振幅に対する標準偏差の比）[%]",
        "lm_legend": "{name}（同梱・雑音なし）",
        "legend_note": ("灰の破線＝規準 {thr:.2f}。特徴点法（同梱・点線）は雑音を足す前の拍の値で、雑音の列では同じ条件の比較になって"
                        "いない（B 段で値が動くのは共通例の集まりが変わるため）。A 段の枠内の数字＝通過率（雑音なし／1%／2%。A 段に残る割合）。"),
        "n_note": ("B 段は {nb} 名（雑音 1% で {nb1} 名、2% で {nb2} 名）で、3 つの当てはめの採用を重ねた部分集合であり、分解に有利な集団。"
                   "C 段は型3 の {n3} 名。値は表6c（02_tables.md）。"),
    },
    "en": {
        "row": {"dt_pwv": "ΔT × aortic PWV", "ri_pvr": "RI × peripheral\nvascular resistance"},
        "xlabel": "Noise (SD as a fraction of pulse amplitude) [%]",
        "lm_legend": "{name} (noise-free)",
        "legend_note": ("Grey dashed line, criterion {thr:.2f}. Fiducial-point values (database-supplied; dotted) are from noise-free "
                        "beats, so the noise columns are not a like-for-like comparison (its tier-B value moves with noise only because "
                        "the common subset changes). Numbers in the tier-A panels, pass rate (remaining in tier A) at noise 0 / 1 / 2 %."),
        "n_note": ("Tier B, {nb} subjects ({nb1} at 1 %, {nb2} at 2 %): the intersection of the subjects accepted by all three fits, "
                   "a subset favourable to the decomposition. Tier C, {n3} type-3 subjects. Table 6c of 02_tables.md."),
    },
}


# ---------------------------------------------------------------- 値の読み出し

def type3_n(numbers: dict) -> int:
    return next(r for r in numbers["tables"]["表5"]["rows"] if r["id"] == "type3")["n"]


def tier_b_counts(numbers: dict) -> tuple[int, int, int]:
    """B 段の人数（雑音なし・1%・2%）。meta.stage_definitions.B の文（02_tables.md）から数字を読む。"""
    txt = numbers["meta"]["stage_definitions"]["B"]["text"]
    nums = [int(x.replace(",", "")) for x in re.findall(r"(\d[\d,]*)\s*名", txt)]
    if len(nums) != 3:
        raise ValueError(f"B 段の人数が 3 つ読めない: {txt!r} → {nums}")
    return nums[0], nums[1], nums[2]


def method_name(mid: str, lang: str) -> str:
    return LABELS["variants"][mid]["short_" + lang]


def tier_b_sentence(numbers: dict) -> str:
    """表6c の後書き（02_tables.md）から、B 段が分解に有利な部分集合だと述べた文を取る（太字の印は外す）。"""
    for p in numbers["tables"]["表6c"].get("postscript", []):
        s = p.replace("**", "").replace("\n", "")
        if "B 段" in s and "有利" in s:
            return s.split("。")[0] + "。"
    raise ValueError("表6c の後書きに B 段の性質を述べた文が見つからない")


def source_en(src: str) -> str:
    """表6c の出典の段落（和文）から台本・選択肢・結果ファイル・lab_log の追記番号を取り出し、英文の出典の文にする。"""
    codes = re.findall(r"`([^`]+)`", src)
    scripts = [c for c in codes if c.endswith(".py")]
    opts = [c for c in codes if c.startswith("--")]
    files = [c for c in codes if c.endswith(".txt")]
    part = re.search(r"節\s*([A-Z])", src)
    entries = re.findall(r"追記\s*(\d+)", src)
    if not scripts or not entries:
        raise ValueError(f"出典の段落から台本名か追記番号が読めない: {src[:60]!r}")
    s = "Script " + ", ".join(f"`{c}`" for c in scripts) + (f", part {part.group(1)}" if part else "")
    if opts:
        s += " (options " + ", ".join(f"`{o}`" for o in opts) + ")"
    if files:
        s += "; result files " + ", ".join(f"`{f}`" for f in files)
    s += "; lab_log " + ("entry " if len(entries) == 1 else "entries ") + ", ".join(entries)
    return s + "."


def series(numbers: dict) -> list[dict]:
    """表6c から描くべき系列を起こす（自己検査でも同じ関数で JSON を読み直して比べる）。"""
    t = numbers["tables"]["表6c"]
    out = []
    for row in t["rows"]:
        for col in COLS:
            ys = [row[col][lv]["rho"] for lv in t["noise_levels"]]
            if all(y is not None for y in ys):
                out.append({"id": row["id"], "stage": row["stage"], "col": col, "y": ys})
    return out


def pass_lines(numbers: dict) -> list[tuple[str, str]]:
    """A 段の枠に印字する通過率の行（当てはめの id, 文字）。値は表6c の A 段の行から。"""
    t = numbers["tables"]["表6c"]
    out = []
    for mid in METHODS:
        row = next((r for r in t["rows"] if r["id"] == mid and r["stage"] == "A"), None)
        if row is None or not row.get("pass_rate"):
            continue
        vals = [row["pass_rate"][lv] for lv in t["noise_levels"]]
        out.append((mid, GLYPH[mid] + " " + "/".join(f"{v:.3f}" for v in vals)))
    return out


# ---------------------------------------------------------------- 描画

def _measure(s: str, fontsize: float = 8.0, linespacing: float = 1.1) -> tuple[float, float]:
    """文字の幅と高さ（pt）を別の小さな図で測る。"""
    f = plt.figure(figsize=(1, 1))
    t = f.text(0, 0, s, fontsize=fontsize, linespacing=linespacing)
    f.canvas.draw()
    b = t.get_window_extent(renderer=f.canvas.get_renderer())
    plt.close(f)
    return b.width * 72 / f.dpi, b.height * 72 / f.dpi


def _free_y(ax, lines_xy: list, x_lo: float, x_hi: float, h_units: float, y_lo: float, y_hi: float,
            margin: float) -> float | None:
    """x が [x_lo, x_hi] の範囲で、折れ線（記号つき）と規準線に掛からない高さ h_units の帯を上から探し、
    その中心の y を返す。無ければ None。"""
    import numpy as np
    xs = np.linspace(x_lo, x_hi, 60)
    occupied = []
    for pts, extra in lines_xy:
        px = [p[0] for p in pts]
        py = [p[1] for p in pts]
        ys = np.interp(xs, px, py)
        occupied.append((ys.min() - extra, ys.max() + extra))
    y = y_hi - margin - h_units / 2
    while y - h_units / 2 >= y_lo + margin:
        top, bot = y + h_units / 2, y - h_units / 2
        if all(hi < bot or lo > top for lo, hi in occupied):
            return y
        y -= 0.005
    return None


def build(lang: str, numbers: dict):
    """図を組む。戻り値は (fig, 描いた系列, 通過率の文字, 規準線の y)。"""
    setup(lang)
    plt.rcParams.update({"xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
                         "font.family": list(plt.rcParams["font.family"]) + ["DejaVu Sans"]})
    t6c = numbers["tables"]["表6c"]
    crit = numbers["meta"]["criterion"]["min_median_abs_rho"]
    tx = T[lang]
    levels = t6c["noise_levels"]
    xpos = list(range(len(levels)))
    xticklabels = [f"{float(lv) * 100:g}" for lv in levels]
    nb, nb1, nb2 = tier_b_counts(numbers)
    n3 = type3_n(numbers)

    footer_lines = [tx["legend_note"].format(thr=crit), STAGE_NOTE[lang],
                    tx["n_note"].format(nb=f"{nb:,}", nb1=f"{nb1:,}", nb2=f"{nb2:,}", n3=f"{n3:,}"),
                    LABELS["posthoc_note"][lang]]
    footer = "\n".join(wrap_text(s, lang) for s in footer_lines)
    n_footer = footer.count("\n") + 1
    footer_mm = n_footer * 8 * 1.3 / 72 * 25.4 + 2.5

    H_MM = TOP_MM + 2 * PANEL_H_MM + HSPACE_MM + XAXIS_MM + footer_mm
    fig = plt.figure(figsize=(mm(W_MM), mm(H_MM)))
    panel_w = (W_MM - LEFT_MM - RIGHT_MM - 2 * WSPACE_MM) / 3
    gs = GridSpec(2, 3, figure=fig, left=LEFT_MM / W_MM, right=1 - RIGHT_MM / W_MM,
                  top=1 - TOP_MM / H_MM, bottom=(footer_mm + XAXIS_MM) / H_MM,
                  wspace=WSPACE_MM / panel_w, hspace=HSPACE_MM / PANEL_H_MM)
    stage_name = {k: v[lang] for k, v in LABELS["stages"].items()}
    letters = "abcdef"
    drawn, pass_texts = [], []
    plines = pass_lines(numbers)
    for ri, col in enumerate(COLS):
        for ci, st in enumerate(STAGES):
            ax = fig.add_subplot(gs[ri, ci])
            ax.set_xlim(XMIN, XMAX)
            ax.set_ylim(0, YMAX)
            ax.set_xticks(xpos)
            ax.set_xticklabels(xticklabels if ri == 1 else [])
            ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8])
            if ci == 0:
                ax.set_yticklabels(["0", "0.2", "0.4", "0.6", "0.8"])
                ax.set_ylabel(tx["row"][col], fontsize=8, linespacing=1.1)
            else:
                ax.set_yticklabels([])
                ax.tick_params(axis="y", length=0)
            ax.set_title(f"({letters[ri * 3 + ci]}) {stage_name[st]}", fontsize=8, loc="center", pad=3)
            ax.axhline(crit, color=PALETTE["grey"], lw=0.8, ls=(0, (4, 2)), zorder=1)
            if ri == 0 and ci == 0:
                ax.text(XMIN + 0.05, crit + 0.012, L[lang]["criterion"], ha="left", va="bottom",
                        fontsize=8, color=PALETTE["grey"])
            lines_xy = [([(XMIN, crit), (XMAX, crit)], 0.012)]
            for mid in METHODS:
                row = next((r for r in t6c["rows"] if r["id"] == mid and r["stage"] == st), None)
                if row is None:
                    continue
                ys = [row[col][lv]["rho"] for lv in levels]
                sty = STYLE[mid]
                ln, = ax.plot(xpos, ys, color=sty["color"], marker=sty["marker"], ms=MARKER_PT, ls=sty["ls"],
                              mfc=sty["mfc"], mec=sty["color"], mew=1.0, lw=1.0, zorder=3 if mid != "landmark" else 2,
                              label=f"{mid}/{st}/{col}")
                drawn.append({"id": mid, "stage": st, "col": col, "y": [float(v) for v in ln.get_ydata()]})
                lines_xy.append((list(zip(xpos, ys)), 0.03))
            # A 段の枠: 通過率を当てはめごとに 1 行ずつ、線と記号に掛からない帯に印字する
            if st == "A" and plines:
                block = "\n".join(s for _m, s in plines)
                w_pt, h_pt = _measure(block)
                units_per_pt_x = (XMAX - XMIN) / (panel_w / 25.4 * 72)
                units_per_pt_y = YMAX / (PANEL_H_MM / 25.4 * 72)
                w_u, h_u = w_pt * units_per_pt_x, h_pt * units_per_pt_y
                x_hi = XMAX - 0.08
                y_c = _free_y(ax, lines_xy, x_hi - w_u, x_hi, h_u, 0.0, YMAX, 0.02)
                ha = "right"
                if y_c is None:
                    x_hi, ha = XMIN + 0.08 + w_u, "left"
                    y_c = _free_y(ax, lines_xy, XMIN + 0.08, x_hi, h_u, 0.0, YMAX, 0.02)
                if y_c is None:
                    y_c = YMAX - 0.02 - h_u / 2
                # 行ごとに当てはめの色で描く（1 つの文字列で位置を決め、各行は別の文字として重ねる）
                line_h = h_u / len(plines)
                for k, (mid, s) in enumerate(plines):
                    y_line = y_c + h_u / 2 - line_h * (k + 0.5)
                    ax.text(x_hi, y_line, s, ha=ha, va="center", fontsize=8, color=STYLE[mid]["color"])
                    pass_texts.append({"col": col, "id": mid, "text": s})
    # 共通の横軸の名（下の行の下）と、縦軸の共通の名（左端・縦書き）
    fig.text(LEFT_MM / W_MM + (1 - (LEFT_MM + RIGHT_MM) / W_MM) / 2, (footer_mm + 0.8) / H_MM, tx["xlabel"],
             ha="center", va="bottom", fontsize=8)
    y_mid = ((footer_mm + XAXIS_MM) / H_MM + (1 - TOP_MM / H_MM)) / 2
    fig.text(1.8 / W_MM, y_mid, L[lang]["rho"], ha="center", va="center", fontsize=8, rotation=90)
    # 凡例（図の上）
    handles, names = [], []
    for mid in METHODS:
        sty = STYLE[mid]
        handles.append(Line2D([0], [0], color=sty["color"], marker=sty["marker"], ms=MARKER_PT, ls=sty["ls"],
                              mfc=sty["mfc"], mec=sty["color"], mew=1.0, lw=1.0))
        names.append(tx["lm_legend"].format(name=method_name(mid, lang)) if mid == "landmark" else method_name(mid, lang))
    fig.legend(handles, names, loc="upper center", bbox_to_anchor=(0.5, 1.0), ncol=4, frameon=False, fontsize=8,
               handlelength=2.2, columnspacing=1.2, handletextpad=0.5, borderaxespad=0.3)
    fig.text(0.005, 1.2 / H_MM, footer, ha="left", va="bottom", fontsize=8, color=PALETTE["ink"], linespacing=1.3)
    return fig, drawn, pass_texts, crit


# ---------------------------------------------------------------- 凡例文

def legend_text(lang: str, numbers: dict) -> str:
    t6c = numbers["tables"]["表6c"]
    thr = numbers["meta"]["criterion"]["min_median_abs_rho"]
    nb, nb1, nb2 = tier_b_counts(numbers)
    n3 = f"{type3_n(numbers):,}"
    src = re.sub(r"^出典[^:：]*[:：]\s*", "", t6c.get("source_paragraph", "")).replace("\n", "")
    b_sent = tier_b_sentence(numbers)
    if lang == "ja":
        return "\n".join([
            f"図6　雑音への頑健性 ― 表6c（型3）の 3 つの当てはめを A・B・C 段で、雑音 0・1・2% について並べる",
            "",
            f"何を示すか: 型3（変曲点のみ）の {n3} 名について、凍結版、拍長の 0.65 倍で打ち切る版、残差を 1 次微分の領域で取る版の"
            "年齢層内 Spearman |ρ| の中央値を、雑音を足していない拍と、拍の峰から谷までの振幅の 1%・2% を標準偏差とする"
            "白色ガウス雑音を足した拍とで比べる。上の行は ΔT × 大動脈脈波伝播速度、下の行は RI × 末梢血管抵抗。列は A 段・B 段・C 段。"
            "凍結版は灰の丸、0.65 倍の打ち切りは青の四角、1 次微分の領域は青緑の三角。特徴点法（同梱）は B 段・C 段だけにあり、"
            "雑音を足す前の拍の値なので朱の点線（菱形）で描く（雑音の列では同じ条件の比較になっていない。B 段の値が雑音で変わるのは"
            f"共通例の集まりが変わるため）。灰の破線は規準 {thr:.2f}。A 段の枠の中の数字は通過率（雑音なし／1%／2%。A 段に残る割合）。"
            f"B 段は {nb:,} 名（雑音 1% で {nb1:,} 名、2% で {nb2:,} 名）、C 段は型3 の {n3} 名。{b_sent}判定の札は図に書かず表に任せる。",
            "",
            f"出典: `02_tables.md` 表6c。{src}数値は `data/paper2_numbers.json` から台本 `build_fig_noise.py` が読む。",
            "",
            "段の注釈: " + STAGE_NOTE["ja"],
            "",
            "探索・事後の注記: " + LABELS["posthoc_note"]["ja"],
            "",
            f"表6c の前書き（02_tables.md）: {t6c['preamble'][0]}",
            "",
            f"表6c の後書き（02_tables.md）: {b_sent}",
        ])
    return "\n".join([
        "Figure 6. Robustness to noise: the three fits of table 6c (type 3) in tiers A, B and C at noise 0, 1 and 2 %.",
        "",
        f"What is shown: for the {n3} type-3 subjects (inflection only), the median within-age-stratum Spearman |ρ| of the frozen fit, "
        "the fit truncated at 0.65 of the beat length and the fit with the residual taken in the first-derivative domain, on beats "
        "without added noise and on beats with white Gaussian noise whose SD is 1 % or 2 % of the peak-to-trough pulse amplitude. "
        "Top row, ΔT × aortic PWV; bottom row, RI × peripheral vascular resistance. Columns, tiers A, B and C. Frozen fit, grey circles; "
        "truncation at 0.65T, blue squares; derivative domain, blue-green triangles. The fiducial-point analysis (database-supplied) "
        "exists in tiers B and C only and is computed from noise-free beats, so it is drawn as a vermilion dotted line with diamonds "
        "(the noise columns are therefore not a like-for-like comparison; its tier-B value changes with noise only because the common "
        f"subset changes). The dashed grey line is the criterion {thr:.2f}. Numbers in the tier-A panels are the pass rates (fraction "
        f"remaining in tier A) at noise 0 / 1 / 2 %. Tier B has {nb:,} subjects ({nb1:,} at 1 %, {nb2:,} at 2 %); table 6c describes "
        "it as the intersection of the subjects accepted by all three fits, a subset favourable to the decomposition. Tier C has the "
        f"{n3} type-3 subjects. Verdicts are not written in the figure.",
        "",
        f"Source: table 6c of `02_tables.md`. {source_en(src)} All numbers are read from `data/paper2_numbers.json` by "
        "`build_fig_noise.py`.",
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
        fig, drawn, pass_texts, crit = build(lang, load_numbers())
        fresh = load_numbers()
        exp = series(fresh)
        key = lambda p: (p["id"], p["stage"], p["col"])   # noqa: E731
        d = {key(p): p["y"] for p in drawn}
        e = {key(p): p["y"] for p in exp}
        rep("描いた系列の数が表6c から起こした数と同じ（11 行 × 2 量）", len(drawn) == len(exp) == len(d) == 22,
            f"描いた {len(drawn)}・期待 {len(exp)}")
        diff = [k for k in e if k not in d or len(d[k]) != len(e[k]) or any(abs(a - b) > 1e-12 for a, b in zip(d[k], e[k]))]
        rep("描いた |ρ|（雑音 3 水準）が JSON と一致（全系列）", not diff, f"差 {diff}")
        rep("特徴点法の系列は B 段と C 段だけ", {k[1] for k in d if k[0] == "landmark"} == {"B", "C"})
        want_pass = pass_lines(fresh)
        got = {(p["col"], p["id"]): p["text"] for p in pass_texts}
        rep("A 段の枠の通過率が JSON の値（両方の行・3 つの当てはめ）",
            len(pass_texts) == 2 * len(want_pass) == 6 and all(got.get((c, m)) == s for c in COLS for m, s in want_pass),
            f"{got}")
        rep("規準線が meta.criterion の値（6 枠すべて）", abs(crit - fresh["meta"]["criterion"]["min_median_abs_rho"]) < 1e-12
            and all(any(len(ln.get_ydata()) == 2 and all(abs(y - crit) < 1e-12 for y in ln.get_ydata()) for ln in ax.get_lines())
                    for ax in fig.axes[:6]))
        lv = fresh["tables"]["表6c"]["noise_levels"]
        xt = [t.get_text() for t in fig.axes[3].get_xticklabels()]
        rep("横軸の目盛が JSON の雑音の水準（% に直したもの）", xt == [f"{float(x) * 100:g}" for x in lv], f"{xt}")
        texts = texts_of(fig)
        joined = "\n".join(texts)
        flat = joined.replace("\n", "")
        bad_font = check_min_font(fig)
        rep(f"文字はすべて {common.MIN_FONT_PT:g} pt 以上", not bad_font, f"{bad_font[:3]}")
        rep("段の注釈が脚注にある", STAGE_NOTE[lang].replace(" ", "") in flat.replace(" ", ""))
        nb, nb1, nb2 = tier_b_counts(fresh)
        rep("B 段の人数（雑音なし・1%・2%）が脚注にある", all(f"{n:,}" in flat for n in (nb, nb1, nb2)))
        rep("型3 の被験者数（表5 の n）が脚注にある", f"{type3_n(fresh):,}" in flat)
        rep("探索・事後の注記が脚注にある", LABELS["posthoc_note"][lang].replace(" ", "") in flat.replace(" ", ""))
        rep("特徴点法が雑音なしの値だと脚注にある", ("雑音を足す前" in flat) if lang == "ja" else ("noise-free" in flat))
        rep("B 段が分解に有利な部分集合だと脚注にある",
            ("分解に有利" in flat) if lang == "ja" else ("favourable to the decomposition" in flat))
        rep("規準線の札がある", L[lang]["criterion"] in texts)
        vh = _verdict_hits(joined)
        rep("判定の語（成立・不成立・pass・fail）を図に書いていない", not vh, f"{vh}")
        names = [method_name(m, lang) for m in METHODS]
        rep("凡例の名が labels.json の短い名", all(any(n in t for t in texts) for n in names))
        ov = text_overlaps(fig)
        rep("文字どうしの重なりが無い（描画器の寸法で確認）", not ov, f"{ov[:4]}")
        om = text_marker_overlaps(fig)
        rep("文字と記号の重なりが無い（描画器の寸法で確認）", not om, f"{om[:4]}")
        outside = texts_outside(fig)
        rep("図の縁からはみ出す文字が無い（凡例・脚注が 150 mm に収まる）", not outside, f"{outside[:3]}")
        leg = legend_text(lang, fresh)
        if banned is None:
            print("  （用語検査器が無いので禁止語の確認は飛ばした）")
        else:
            hits = _banned_hits(banned, texts + [leg])
            rep("図と凡例文に禁止語が無い（検査器の表）", not hits, f"{hits[:3]}")
        rep("B 段が分解に有利な部分集合だと凡例文にある（表6c の後書きの文）",
            ("分解に有利" in leg) if lang == "ja" else ("favourable to the decomposition" in leg))
        rep("凡例文に出典（台本・結果ファイル・lab_log の追記番号）がある",
            "50_reservoir_bench.py" in leg and ".txt" in leg and (("追記" in leg) if lang == "ja" else ("lab_log entr" in leg)))
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

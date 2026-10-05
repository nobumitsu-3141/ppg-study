#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""図4 模式図（fig_synthetic）― 合成脈波に凍結版・0.65T の打ち切り・1 次微分の領域の当てはめを重ね、
第2成分の位置が真の反射波の到達からどれだけ離れるかを示す。

**合成脈波の例示であり、PWDB の結果ではない。**脈波は `analysis/scripts/50_reservoir_bench.py`（50番）
節A の `synth_beat`（前進波 ＋ 反射波 ＋ 貯留槽の指数減衰。lab_log 追記141）で作り、当てはめは
同じ台本の `_bounds`・`_frozen_starts`・`_model`・`_components` と、`fit_kind` と同じ解の選び方
（RSS 最小を基本に、特徴点近傍の解が 1.10 倍以内ならそれを採る）で再現する。自己検査で、描いた
ΔT が `fit_kind` の返り値と 0.5 ms 以内で一致することを確かめる。

列は 3 つ: 凍結版（50番の (1)。`src/pda.py` と同じ探索範囲・起点・解の選び方の複製）、
(6b) 拍長の 0.65 倍で打ち切る、(9) 残差を 1 次微分の領域で取る。行は 2 つ: 型3 相当
（反射波の到達 0.10 s。収縮期に重なる）と型1 相当（到達 0.28 s。遅く分離する）。貯留槽の
時定数はどちらも 0.45 s。表題の ΔT は第2成分のピーク − 第1成分のピーク、真値は合成した
反射波のピーク − 前進波のピーク（`synth_beat` の返り値 `dt_s`）。

この図は探索・事後の内容（表6 の (6b)(9)）を扱う。判定には用いない。

使い方
    python3 build_fig_synthetic.py
    python3 build_fig_synthetic.py --lang en
    python3 build_fig_synthetic.py --selftest

出力は `out/fig_synthetic_{ja,en}.{pdf,svg,png}` と `out/fig_synthetic_legend_{ja,en}.txt`。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                      # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.lines import Line2D                 # noqa: E402
from matplotlib.patches import Patch                # noqa: E402
from scipy.optimize import least_squares            # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common                                        # noqa: E402

REPO = HERE.parents[3]
ANALYSIS = REPO / "analysis"
SCRIPT50 = ANALYSIS / "scripts" / "50_reservoir_bench.py"
LABELS = HERE / "data" / "labels.json"
CHECKER = REPO / "analysis" / "scripts" / "check_terminology.py"
NAME = "fig_synthetic"

FONT_PT = 8.0
WIDTH_MM = common.WIDTH_MM["double"]     # 150 mm
DT_TOL_S = 0.5e-3                        # 自己検査: fit_kind との許容差 [s]

# 合成脈波（行）。(鍵, 反射波の到達 [s], 貯留槽の時定数 [s])。50番 節A-2 の型1 相当・型3 相当と同じ到達
BEATS = [("type3", 0.10, 0.45), ("type1", 0.28, 0.45)]
# 当てはめの型（列）。50番の鍵 → labels.json の variants の id
KINDS = [("frozen", "fb"), ("trunc08", "trunc065"), ("deriv", "deriv")]
KIND_COLOR = {"frozen": common.PALETTE["pda"], "trunc08": common.PALETTE["amp"],
              "deriv": common.PALETTE["control"]}
KIND_MARKER = {"frozen": "s", "trunc08": "o", "deriv": "^"}

TEXT = {
    "ja": {
        "synthetic": "合成脈波（例示。PWDB ではない）",
        "title": "ΔT {dt:.1f} ms（真値 {true:.1f} ms）",
        "measured": "合成脈波（当てはめの対象）",
        "comp1": "第1成分",
        "comp2": "第2成分: {k}",
        "true_line": "合成の前進波・反射波のピーク（真値 ΔT を測る 2 点）",
        "trunc": "{frac}T 以降（当てはめに使わない）",
        "cut": "{frac}T",
        "xlabel": "時間 [s]",
        "ylabel": "振幅（正規化）",
        "rows": {"type3": "型3 相当の合成脈波\n反射波が収縮期に重なる",
                 "type1": "型1 相当の合成脈波\n反射波が遅く分離する"},
        "note": "表題の ΔT と真値は合成脈波 1 拍への当てはめの値で、PWDB の結果ではない。真値は合成した反射波の"
                "ピーク − 前進波のピーク（2 本の点線の間隔）。凍結版の列は 50番の (1)（(0) 凍結版本体 src/pda.py の"
                "複製。自己検査で (0) の返り値と一致）。",
    },
    "en": {
        "synthetic": "Synthetic beat (illustration, not PWDB)",
        "title": "ΔT {dt:.1f} ms (true {true:.1f} ms)",
        "measured": "Synthetic beat (fitted signal)",
        "comp1": "Component 1",
        "comp2": "Component 2: {k}",
        "true_line": "Synthetic forward/reflected-wave peaks (true ΔT)",
        "trunc": "Beyond {frac}T (not fitted)",
        "cut": "{frac}T",
        "xlabel": "Time [s]",
        "ylabel": "Amplitude (normalised)",
        "rows": {"type3": "Type-3-like beat\nreflection within systole",
                 "type1": "Type-1-like beat\nreflection separated"},
        "note": "ΔT and the true value in each panel title come from the fit to this one synthetic beat, "
                "not from PWDB. The true value is the peak of the synthetic reflected wave minus the peak of the "
                "forward wave (the two dotted lines). 'Frozen' is variant (1) of script 50, a copy of src/pda.py; "
                "the self-test checks its result against (0), the frozen implementation itself.",
    },
}


# ---------------------------------------------------------------- 50番の読み込みと当てはめ

_M50 = None


def load_m50():
    """50番を名前で読み込む（数字始まりなので import 文では書けない）。`from src import pda, pda2`
    が通るよう analysis/ を sys.path に入れる。"""
    global _M50
    if _M50 is not None:
        return _M50
    if str(ANALYSIS) not in sys.path:
        sys.path.insert(0, str(ANALYSIS))
    spec = importlib.util.spec_from_file_location("m50", SCRIPT50)
    m = importlib.util.module_from_spec(spec)
    sys.modules["m50"] = m
    spec.loader.exec_module(m)
    _M50 = m
    return m


def fit_for_drawing(m50, t: np.ndarray, y: np.ndarray, kind: str) -> dict:
    """`fit_kind` と同じ道筋で当てはめ、描くのに要る母数と成分のピークを返す。

    `fit_kind` は ΔT・RI だけを返して母数を返さないので、同じ部品（`_norm`・`_bounds`・
    `_frozen_starts`・`_model`・`_components`・`pda.component_peak`）と同じ解の選び方で
    ここに写した。対象は 8 母数の型（凍結版の複製・打ち切り・微分領域）だけ。
    """
    if m50.KIND_SHAPE.get(kind) != "plain" or kind == "fb":
        raise ValueError(f"この図が扱うのは 8 母数の型だけ: {kind}")
    ys = m50._norm(y)
    lo, hi, _dmu_lo = m50._bounds(t, ys, kind)
    cut_s = float("nan")
    if kind in m50.KIND_TRUNC:
        if kind in m50.TRUNC_ABS_OF:
            cut_s = float(min(m50.TRUNC_ABS_OF[kind], m50.TRUNC_ABS_MAXFRAC * (t[-1] - t[0])))
        else:
            cut_s = float(m50.TRUNC_FRAC_OF[kind] * (t[-1] - t[0]))
        keep = t <= t[0] + cut_s
        tfit, yfit = t[keep], ys[keep]
    else:
        tfit, yfit = t, ys
    starts, dmu0 = m50._frozen_starts(t, ys, lo, hi, kind, m50.SEED_STARTS)
    if kind == "deriv":
        dy_fit = np.gradient(yfit, tfit)

        def _resid(p):
            return np.gradient(m50._model(p, tfit, kind), tfit) - dy_fit
    else:
        def _resid(p):
            return m50._model(p, tfit, kind) - yfit
    sols = []
    for x0 in starts:
        try:
            sols.append(least_squares(_resid, x0, bounds=(lo, hi), method="trf",
                                      max_nfev=m50.MAX_NFEV))
        except Exception:        # noqa: BLE001  fit_kind と同じ扱い（その起点は捨てる）
            continue
    if not sols:
        raise RuntimeError(f"当てはめが 1 つも成らなかった: {kind}")
    gmin = min(sols, key=lambda r: r.cost)
    near = [r for r in sols
            if abs(r.x[5] - dmu0) <= m50.NEAR_DMU and r.cost <= gmin.cost * m50.NEAR_RSS]
    best = min(near, key=lambda r: r.cost) if near else gmin
    t0f, t1f = float(t[0]), float(t[-1])
    c1, c2 = m50._components(best.x, kind)
    tp1, h1 = m50.pda.component_peak(c1, t0f, t1f)
    tp2, h2 = m50.pda.component_peak(c2, t0f, t1f)
    return {"x": np.asarray(best.x, float), "c1": c1, "c2": c2, "tp1": tp1, "h1": h1,
            "tp2": tp2, "h2": h2, "dt_s": tp2 - tp1, "cut_s": cut_s, "ys": ys}


_CACHE = None


def compute_all() -> dict:
    """2 拍 × 3 型の当てはめ。両言語で同じものを描くので 1 回だけ計算する。"""
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    m50 = load_m50()
    out = {"beats": {}, "fits": {}}
    for key, dt_true, tau in BEATS:
        t, y, tr = m50.synth_beat(dt_true, tau)
        out["beats"][key] = {"t": t, "y": y, "truth": tr, "dt_true": dt_true, "tau": tau}
        for kind, _vid in KINDS:
            out["fits"][(key, kind)] = fit_for_drawing(m50, t, y, kind)
    _CACHE = out
    return out


# ---------------------------------------------------------------- 文字の折り返し（実測）

LINE_MM = FONT_PT * 1.25 * 25.4 / 72.0   # 1 行の高さ [mm]（linespacing 1.25）
_UNIT_RE = re.compile(r"\s+|[^　-ヿ㐀-鿿豈-﫿＀-￯\s]+|.")
KINSOKU_HEAD = "、。，．）」』・〜ー"   # 行頭に置かない
KINSOKU_TAIL = "（「『"               # 行末に置かない


class Measurer:
    """フォントで実際に測って折り返すための物差し（build_fig_timeline.py と同じもの）。"""

    def __init__(self, fontsize: float = FONT_PT):
        self.fig = plt.figure(figsize=(1, 1), dpi=100)
        self.renderer = self.fig.canvas.get_renderer()
        self.fp = FontProperties(family=plt.rcParams["font.family"], size=fontsize)

    def width_mm(self, s: str) -> float:
        if not s:
            return 0.0
        w, _h, _d = self.renderer.get_text_width_height_descent(s, self.fp, ismath=False)
        return w / self.fig.dpi * 25.4

    def close(self):
        plt.close(self.fig)


def wrap_text(s: str, max_mm: float, meas: Measurer, lang: str) -> list[str]:
    """幅 max_mm に収まるよう折り返す。英文は語で、和文は字で（英数の連なりは 1 単位として切らない）。

    和文の禁則は**単位ごと**に送る。行頭に置けない字（、。）など）が次の行の頭に来るとき、
    行末に置けない字（（「）が行の末に残るときは、直前の単位（英数の連なりなら丸ごと）を
    次の行へ送る。送っても 1 行に収まらないときは幅を優先する（数値や識別子を途中で切らない）。
    """
    if lang == "en":
        units = re.findall(r"\S+|\s+", s)
    else:
        units = _UNIT_RE.findall(s)

    def join(us: list[str]) -> str:
        return "".join(us).strip()

    lines: list[str] = []
    cur: list[str] = []
    for u in units:
        if u.isspace():
            if cur and not cur[-1].isspace():
                cur.append(" ")
            continue
        if not join(cur) or meas.width_mm(join(cur + [u])) <= max_mm:
            cur.append(u)
            continue
        head, tail = list(cur), [u]
        if lang == "ja":
            while True:
                while head and head[-1].isspace():
                    head.pop()
                if len(head) <= 1:
                    break
                if not (tail[0][0] in KINSOKU_HEAD or head[-1][-1] in KINSOKU_TAIL):
                    break
                cand = [head[-1]] + tail
                if meas.width_mm(join(cand)) > max_mm:
                    break
                head.pop()
                tail = cand
        lines.append(join(head))
        cur = tail
    if join(cur):
        lines.append(join(cur))
    return lines


# ---------------------------------------------------------------- 描画

MARGIN_MM = 1.0
LEFT_MM, RIGHT_MM = 19.0, 2.0   # 左は行の札と y 軸の名の分
TOP_MM = 14.0                   # 上端から上段の枠の上辺まで（合成の札 1 行 ＋ 列の見出し 2 行）
PANEL_H_MM = 28.5               # 枠 1 つの高さ
HGAP_MM, VGAP_MM = 4.0, 9.0
XLABEL_H_MM = 9.0               # 下段の目盛りの札と軸の名
LEGEND_GAP_MM = 1.5             # 軸の名と凡例の間
NOTE_GAP_MM = 2.5               # 凡例と脚注の間
ROW_LABEL_X_MM = 4.2            # 行の札（縦書き方向）の中心
# 凡例は 2 列（3 列では英文が図の幅を超える）。高さと幅は別の図で実測して配置に使う
LEGEND_KW = dict(ncol=2, frameon=False, handlelength=2.2, columnspacing=1.5, labelspacing=0.4,
                 borderaxespad=0.0, borderpad=0.2, fontsize=FONT_PT)


def _legend_handles(T: dict, labels: dict, lang: str, ink: str, grey: str) -> list:
    handles = [Line2D([], [], color=ink, lw=1.0, label=T["measured"]),
               Line2D([], [], color=grey, lw=0.8, ls=(0, (3, 1.5)), marker="o", ms=3.2,
                      mfc="white", mec=grey, label=T["comp1"])]
    for kind, vid in KINDS:
        handles.append(Line2D([], [], color=KIND_COLOR[kind], lw=1.0, marker=KIND_MARKER[kind],
                              ms=3.6, label=T["comp2"].format(k=_col_header(labels, vid, lang))))
    handles.append(Line2D([], [], color=ink, lw=0.7, ls=(0, (1, 1.4)), label=T["true_line"]))
    handles.append(Patch(fc="#E6E6E6", ec="#BDBDBD", lw=0.0, hatch="////", label=T["trunc"]))
    return handles


def _legend_size_mm(handles: list) -> tuple[float, float]:
    """凡例の (高さ, 幅) [mm] を別の図で実測する（配置の見積もりに手の数値を使わない）。"""
    fig = plt.figure(figsize=(common.mm(WIDTH_MM), 2.0), dpi=100)
    try:
        leg = fig.legend(handles=handles, loc="lower left", **LEGEND_KW)
        fig.canvas.draw()
        bb = leg.get_window_extent(fig.canvas.get_renderer())
        return bb.height / fig.dpi * 25.4, bb.width / fig.dpi * 25.4
    finally:
        plt.close(fig)


def _col_header(labels: dict, vid: str, lang: str) -> str:
    v = labels["variants"][vid]
    short = v[f"short_{lang}"]
    return f"{v['no']} {short}" if vid != "fb" else short


def trunc_frac(m50) -> float:
    """打ち切りの割合。50番の定数（(6b) の `TRUNC_FRAC_OF`）から取り、文字列に手で打たない。"""
    kind = next(k for k, _v in KINDS if k in m50.KIND_TRUNC)
    return float(m50.TRUNC_FRAC_OF[kind])


def fmt_texts(lang: str, m50) -> dict:
    """TEXT[lang] の打ち切りの割合（{frac}）を 50番の定数で埋めたもの。"""
    frac = f"{trunc_frac(m50):.2f}"
    T = dict(TEXT[lang])
    for k in ("trunc", "cut"):
        T[k] = T[k].format(frac=frac)
    return T


def build(lang: str, labels: dict | None = None):
    common.setup(lang, base_pt=FONT_PT)
    plt.rcParams.update({"xtick.labelsize": FONT_PT, "ytick.labelsize": FONT_PT,
                         "legend.fontsize": FONT_PT})
    labels = labels or json.load(open(LABELS, encoding="utf-8"))
    data = compute_all()
    m50 = load_m50()
    T = fmt_texts(lang, m50)
    skew = m50.skew_gaussian
    ink, grey = common.PALETTE["ink"], common.PALETTE["grey"]

    # 脚注は実測で折り返し、その行数から下の余白と図の高さを決める（字数の目安で折らない）
    note = T["note"] + "\n" + labels["posthoc_note"][lang]
    meas = Measurer(FONT_PT)
    try:
        note_lines = [ln for para in note.split("\n")
                      for ln in wrap_text(para, WIDTH_MM - 2 * MARGIN_MM, meas, lang)]
    finally:
        meas.close()
    handles = _legend_handles(T, labels, lang, ink, grey)
    leg_h, leg_w = _legend_size_mm(handles)
    y_note = MARGIN_MM + len(note_lines) * LINE_MM    # 脚注の上端 [mm]
    y_leg = y_note + NOTE_GAP_MM                       # 凡例の下端
    bottom = y_leg + leg_h + LEGEND_GAP_MM + XLABEL_H_MM   # 下段の枠の下辺
    H = TOP_MM + 2 * PANEL_H_MM + VGAP_MM + bottom
    fig = plt.figure(figsize=(common.mm(WIDTH_MM), common.mm(H)))
    panel_w = (WIDTH_MM - LEFT_MM - RIGHT_MM - 2 * HGAP_MM) / 3
    gs = fig.add_gridspec(2, 3, left=LEFT_MM / WIDTH_MM, right=1 - RIGHT_MM / WIDTH_MM,
                          top=1 - TOP_MM / H, bottom=bottom / H,
                          wspace=HGAP_MM / panel_w, hspace=VGAP_MM / PANEL_H_MM)
    record = {"titles": {}, "dt_ms": {}, "true_ms": {}, "shaded": [], "H_mm": H,
              "note_lines": note_lines, "legend_w_mm": leg_w, "legend_h_mm": leg_h,
              "truth_lines": {}, "axes": {}}
    for i, (bkey, _dt_true, _tau) in enumerate(BEATS):
        b = data["beats"][bkey]
        t, tr = b["t"], b["truth"]
        Tb = float(t[-1])
        for j, (kind, vid) in enumerate(KINDS):
            f = data["fits"][(bkey, kind)]
            ax = fig.add_subplot(gs[i, j])
            col = KIND_COLOR[kind]
            if kind in m50.KIND_TRUNC:
                ax.axvspan(float(t[0]) + f["cut_s"], Tb, fc="#E6E6E6", ec="#BDBDBD", lw=0.0,
                           hatch="////", zorder=0)
                ax.text(float(t[0]) + f["cut_s"] + 0.01, 1.08, T["cut"], ha="left", va="top",
                        fontsize=FONT_PT, color=ink, zorder=5)
                record["shaded"].append((bkey, kind, float(t[0]) + f["cut_s"]))
            # 合成の前進波と反射波のピーク（真値 ΔT ＝ その差）。到達の母数 dt_set の位置ではない
            for x_true in (tr["t_fwd"], tr["t_ref"]):
                ax.axvline(x_true, color=ink, lw=0.7, ls=(0, (1, 1.4)), zorder=1)
            record["truth_lines"][(bkey, kind)] = (float(tr["t_fwd"]), float(tr["t_ref"]))
            record["axes"][(bkey, kind)] = ax
            ax.plot(t, skew(t, *f["c1"]), color=grey, lw=0.8, ls=(0, (3, 1.5)), zorder=2)
            ax.plot(t, skew(t, *f["c2"]), color=col, lw=1.0, zorder=3)
            ax.plot(t, f["ys"], color=ink, lw=1.0, zorder=4)
            ax.plot([f["tp1"]], [f["h1"]], marker="o", ms=3.2, mfc="white", mec=grey, mew=0.8,
                    ls="none", zorder=5)
            ax.plot([f["tp2"]], [f["h2"]], marker=KIND_MARKER[kind], ms=3.6, mfc=col, mec=col,
                    ls="none", zorder=5)
            dt_ms, true_ms = 1000.0 * f["dt_s"], 1000.0 * tr["dt_s"]
            title = T["title"].format(dt=dt_ms, true=true_ms)
            if i == 0:
                title = _col_header(labels, vid, lang) + "\n" + title
            ax.set_title(title, fontsize=FONT_PT, pad=3)
            record["titles"][(bkey, kind)] = title
            record["dt_ms"][(bkey, kind)] = dt_ms
            record["true_ms"][(bkey, kind)] = true_ms
            ax.set_xlim(0.0, Tb)
            ax.set_ylim(-0.04, 1.12)
            ax.set_yticks([0.0, 0.5, 1.0])
            ax.set_xticks([0.0, 0.2, 0.4, 0.6, 0.8])
            ax.tick_params(length=2, pad=1.5)
            if i == 1:
                ax.set_xlabel(T["xlabel"], labelpad=1.5)
            else:
                ax.set_xticklabels([])
            if j == 0:
                ax.set_ylabel(T["ylabel"], labelpad=1.5)
            else:
                ax.set_yticklabels([])
        # 行の札（左端・縦書き方向に回転）
        y_mid = 1 - (TOP_MM + i * (PANEL_H_MM + VGAP_MM) + PANEL_H_MM / 2) / H
        fig.text(ROW_LABEL_X_MM / WIDTH_MM, y_mid, T["rows"][bkey], rotation=90, ha="center", va="center",
                 fontsize=FONT_PT, color=ink, linespacing=1.2)

    # 合成の札。列の見出しより上に置く。IPAPGothic に太字が無いので太字は英文だけ
    fig.text(LEFT_MM / WIDTH_MM, 1 - MARGIN_MM / H, T["synthetic"], ha="left", va="top",
             fontsize=FONT_PT, fontweight="bold" if lang == "en" else "normal", color=ink)

    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(MARGIN_MM / WIDTH_MM, y_leg / H),
               **LEGEND_KW)
    fig.text(MARGIN_MM / WIDTH_MM, y_note / H, "\n".join(note_lines), ha="left", va="top",
             fontsize=FONT_PT, color=ink, linespacing=1.25)
    record["texts"] = common.texts_of(fig)
    return fig, record


# ---------------------------------------------------------------- 凡例の文

RESULT_C14 = REPO / "docs" / "research" / "results" / "50_reservoir_bench_C14.txt"


def _result_note(lang: str) -> str:
    """表6・表6c の結果ファイルがこの作業木にあるかを実行時に確かめて添える（無いものを有るとは書かない）。"""
    if RESULT_C14.exists():
        return ""
    return ("。このファイルはこの作業木に無い（lab_log 追記152 は Mac 1 側の出力として記録している。"
            "数値は 02_tables.md を経由して取った）" if lang == "ja"
            else ". This file is not in the present working tree (lab-log entry 152 records it as output on "
            "Mac 1; the numbers were taken through 02_tables.md)")


def legend_text(lang: str, rec: dict) -> str:
    data = compute_all()
    m50 = load_m50()
    frac = f"{trunc_frac(m50):.2f}"
    n_sub = int(common.load_numbers()["meta"]["n_subjects_decision_test"])
    top, bot = (data["beats"][k] for k, _d, _tau in BEATS[:2])   # 上の行・下の行（描く順と同じ）
    dt_set = [f"{b['dt_true']:.2f}" for b in (top, bot)]           # 到達の母数（synth_beat の dt_set）
    dt_true = [f"{1000 * b['truth']['dt_s']:.1f}" for b in (top, bot)]   # 真値（ピークの差）
    tau = f"{top['tau']:.2f}"
    posthoc = json.load(open(LABELS, encoding="utf-8"))["posthoc_note"][lang]
    lines = []
    if lang == "ja":
        lines += [f"図4　合成脈波 1 拍に 3 つの当てはめを重ねた模式図（例示。PWDB ではない）。凍結版がなぜ合成した"
                  f"反射波のピークを取り逃がし、(6b) {frac}T の打ち切りと (9) 1 次微分の領域が第2成分をどこに置くか。",
                  "",
                  f"示しているもの: 行は合成脈波（上: 型3 相当、反射波の到達の母数 {dt_set[0]} s で収縮期に重なる。"
                  f"下: 型1 相当、同 {dt_set[1]} s で遅く分離する。貯留槽の時定数はどちらも {tau} s）、列は当てはめの型。"
                  "各枠は、当てはめの対象（正規化した合成脈波・黒の実線）、第1成分（灰の破線・白抜き丸はピーク）、"
                  "第2成分（列ごとの色・印はピーク）、合成した前進波と反射波のピーク（2 本の点線）。打ち切りの列は "
                  f"{frac}T 以降を網掛けにした（当てはめに使わない区間）。枠の表題の ΔT は第2成分のピーク − "
                  "第1成分のピーク、真値は合成した反射波のピーク − 前進波のピーク（2 本の点線の間隔）。",
                  "",
                  f"到達の母数（{dt_set[0]}・{dt_set[1]} s）と真値（{dt_true[0]}・{dt_true[1]} ms）が一致しないのは、"
                  "合成では反射波の幅と歪度が到達とともに変わり、真値を母数の差ではなくピークの差で定義するため"
                  "（50番 synth_beat の docstring・lab_log 追記141）。",
                  "",
                  f"**表題の数値は合成脈波だけから出した値で、PWDB の {n_sub:,d} 名の結果ではない。**", ""]
        lines.append("当てはめの返り値（ms。自己検査で 50番 fit_kind と 0.5 ms 以内の一致を、凍結版の列は (0) 凍結版本体"
                     "（src/pda.py）との一致も確かめる）:")
        for bkey, _d, _tau in BEATS:
            tr = data["beats"][bkey]["truth"]
            row = f"  {bkey}: 真値 {1000 * tr['dt_s']:.1f}"
            for kind, _v in KINDS:
                row += f"、{kind} {rec['dt_ms'][(bkey, kind)]:.1f}"
            lines.append(row)
        lines += ["",
                  "出どころ: analysis/scripts/50_reservoir_bench.py 節A（synth_beat・_bounds・_frozen_starts・_model・"
                  "_components・fit_kind の解の選び方）。合成脈波の設計と所見は lab_log 追記141、起点と解の選び方を"
                  "凍結版と同一にした経緯は追記143。(6b)(9) の実データでの結果は 02_tables.md 表6・表6c"
                  "（50番 節C。docs/research/results/50_reservoir_bench_C14.txt ほか、追記146・152・158）"
                  + _result_note("ja") + "。",
                  "",
                  "探索・事後の注記: " + posthoc,
                  "",
                  "図の台本: docs/manuscript/paper2/figtab/build_fig_synthetic.py。"]
    else:
        lines += ["Figure 4. Three fits superimposed on one synthetic beat (illustration, not PWDB): why the frozen "
                  f"fit misses the peak of the synthetic reflected wave, and where the truncated fit (6b, {frac}T) and the "
                  "derivative-domain fit (9) place the second component.",
                  "",
                  f"What is shown: rows are synthetic beats (top: type-3-like, reflected-wave arrival parameter {dt_set[0]} s, "
                  f"overlapping systole; bottom: type-1-like, arrival parameter {dt_set[1]} s, separated; reservoir time "
                  f"constant {tau} s in both), columns are the fit variants. Each panel shows the fitted signal (normalised "
                  "synthetic beat, black), component 1 (grey dashed, open circle at its peak), component 2 (colour "
                  "per column, marker at its peak) and the peaks of the synthetic forward and reflected waves (two dotted "
                  f"lines). In the truncation column the region beyond {frac}T is hatched (not fitted). The panel title gives "
                  "ΔT = peak of component 2 − peak of component 1, and the true value = peak of the synthetic "
                  "reflected wave − peak of the forward wave (the spacing of the two dotted lines).",
                  "",
                  f"The arrival parameter ({dt_set[0]} and {dt_set[1]} s) and the true value ({dt_true[0]} and {dt_true[1]} ms) "
                  "differ because, in the generator, the width and skewness of the reflected wave change with its arrival, "
                  "and the true value is defined as a difference of peaks, not of the position parameters "
                  "(docstring of synth_beat in script 50; lab-log entry 141).",
                  "",
                  f"**The numbers in the panel titles come from the synthetic beat only, not from the {n_sub:,d} PWDB "
                  "subjects.**", ""]
        lines.append("Fitted values (ms; the self-test checks agreement with fit_kind of script 50 within 0.5 ms, and the "
                     "frozen column also against (0), the frozen implementation itself in src/pda.py):")
        for bkey, _d, _tau in BEATS:
            tr = data["beats"][bkey]["truth"]
            row = f"  {bkey}: true {1000 * tr['dt_s']:.1f}"
            for kind, _v in KINDS:
                row += f", {kind} {rec['dt_ms'][(bkey, kind)]:.1f}"
            lines.append(row)
        lines += ["",
                  "Source: analysis/scripts/50_reservoir_bench.py section A (synth_beat, _bounds, _frozen_starts, _model, "
                  "_components and the solution rule of fit_kind). Design and findings of the synthetic beats: lab-log "
                  "entry 141; alignment of starts and solution rule with the frozen fit: entry 143. Results of (6b) and (9) "
                  "on PWDB: 02_tables.md Tables 6 and 6c (script 50 section C; docs/research/results/50_reservoir_bench_C14.txt "
                  "and others; entries 146, 152, 158)" + _result_note("en") + ".",
                  "",
                  "Post-hoc note: " + posthoc,
                  "",
                  "Script: docs/manuscript/paper2/figtab/build_fig_synthetic.py."]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- 自己検査

def _banned_terms():
    if not CHECKER.exists():
        return None
    spec = importlib.util.spec_from_file_location("check_terminology", CHECKER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.BANNED


def _has_banned(text: str, banned) -> list[str]:
    hits = []
    for term, _alt, allow in banned:
        if term not in text:
            continue
        if allow and re.sub(allow, "", text).find(term) < 0:
            continue
        hits.append(term)
    return hits


# 判定の語。英語は語の境界で見る（"method" の中の met のような部分一致を拾わないため）
_VERDICT = {"ja": [re.compile("成立")],
            "en": [re.compile(r"\b(not\s+)?met\b", re.I), re.compile(r"\bpass(ed|es|ing)?\b", re.I),
                   re.compile(r"\bfail(ed|s|ure|ing)?\b", re.I)]}


def _has_verdict(text: str, lang: str) -> bool:
    return any(p.search(text) for p in _VERDICT[lang])


def _layout_problems(fig, tol_mm: float = 0.3):
    """描いたあとの文字の枠を測り、図からはみ出す文字と互いに重なる文字の組を返す。"""
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    boxes = [(t.get_text(), t.get_window_extent(rend))
             for t in fig.findobj(matplotlib.text.Text) if t.get_text().strip() and t.get_visible()]
    tol = tol_mm / 25.4 * fig.dpi
    W, Hh = fig.bbox.width, fig.bbox.height
    outside = [sa[:20] for sa, a in boxes
               if a.x0 < -tol or a.y0 < -tol or a.x1 > W + tol or a.y1 > Hh + tol]
    overlap = []
    for i, (sa, a) in enumerate(boxes):
        for sb, b in boxes[i + 1:]:
            if a.x0 < b.x1 - tol and b.x0 < a.x1 - tol and a.y0 < b.y1 - tol and b.y0 < a.y1 - tol:
                overlap.append((sa[:15], sb[:15]))
    return outside, overlap


def _squash(s: str) -> str:
    """空白をすべて除く（折り返しで入った改行と語間の空白を無視して比べるため）。"""
    return re.sub(r"\s+", "", s)


def selftest() -> int:
    results = []

    def check(name, ok, info=""):
        results.append(bool(ok))
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {info}" if info and not ok else ""))

    m50 = load_m50()
    data = compute_all()
    labels = json.load(open(LABELS, encoding="utf-8"))
    banned = _banned_terms()

    # 1. 描く ΔT が fit_kind と一致
    for bkey, _d, _tau in BEATS:
        b = data["beats"][bkey]
        for kind, _v in KINDS:
            ref = m50.fit_kind(b["t"], b["y"], kind)
            got = data["fits"][(bkey, kind)]["dt_s"]
            d = abs(got - ref["dt_s"])
            check(f"ΔT（{bkey}・{kind}）が fit_kind と {1000 * DT_TOL_S:.1f} ms 以内で一致: "
                  f"{1000 * got:.1f} 対 {1000 * ref['dt_s']:.1f} ms", np.isfinite(d) and d <= DT_TOL_S)
            check(f"打ち切りの時刻（{bkey}・{kind}）が fit_kind と同じ",
                  (np.isnan(ref["cut_s"]) and np.isnan(data["fits"][(bkey, kind)]["cut_s"]))
                  or abs(ref["cut_s"] - data["fits"][(bkey, kind)]["cut_s"]) < 1e-9)
    check("合成脈波の真値が synth_beat の返り値（dt_s）と一致",
          all(abs(data["beats"][k]["truth"]["dt_s"] - (data["beats"][k]["truth"]["t_ref"] - data["beats"][k]["truth"]["t_fwd"])) < 1e-12
              for k, _d, _tau in BEATS))
    # 1b. 「凍結版」の列は 50番 (1)（複製）で描く。(0) 凍結版本体（src/pda.py の fit_beat）と同じ値であることを確かめる
    for bkey, _d, _tau in BEATS:
        b = data["beats"][bkey]
        ref0 = m50.fit_kind(b["t"], b["y"], "fb")
        got = data["fits"][(bkey, "frozen")]["dt_s"]
        check(f"凍結版の列（{bkey}）が (0) 凍結版本体 src/pda.py の返り値と {1000 * DT_TOL_S:.1f} ms 以内で一致: "
              f"{1000 * got:.1f} 対 {1000 * ref0['dt_s']:.1f} ms",
              np.isfinite(ref0["dt_s"]) and abs(got - ref0["dt_s"]) <= DT_TOL_S)
    frac = trunc_frac(m50)

    for lang in ("ja", "en"):
        fig, rec = build(lang, labels)
        texts = rec["texts"]
        alltext = "\n".join(texts)
        # 2. 表題の数値が描いた値
        ok = True
        for (bkey, kind), title in rec["titles"].items():
            want = TEXT[lang]["title"].format(dt=1000 * data["fits"][(bkey, kind)]["dt_s"],
                                              true=1000 * data["beats"][bkey]["truth"]["dt_s"])
            ok &= want in title and title in texts
        check(f"[{lang}] 枠の表題の ΔT・真値が当てはめと合成の値そのもの", ok)
        check(f"[{lang}] 打ち切りの網掛けは打ち切りの列だけ（2 枠）",
              sorted(k for _b, k, _x in rec["shaded"]) == ["trunc08", "trunc08"])
        # 2b. 点線は合成の前進波・反射波のピークの位置（各枠 2 本）。到達の母数 dt_set の位置ではない
        ok_lines = len(rec["axes"]) == len(BEATS) * len(KINDS)
        for key, ax in rec["axes"].items():
            xs = sorted(float(ln.get_xdata()[0]) for ln in ax.get_lines()
                        if len(ln.get_xdata()) == 2 and ln.get_xdata()[0] == ln.get_xdata()[1])
            tr = data["beats"][key[0]]["truth"]
            ok_lines &= (len(xs) == 2 and abs(xs[0] - tr["t_fwd"]) < 1e-9 and abs(xs[1] - tr["t_ref"]) < 1e-9
                         and rec["truth_lines"][key] == (float(tr["t_fwd"]), float(tr["t_ref"])))
        check(f"[{lang}] 点線が合成の前進波・反射波のピークの位置にある（各枠 2 本・{len(rec['axes'])} 枠）", ok_lines)
        T = fmt_texts(lang, m50)
        check(f"[{lang}] 打ち切りの札「{T['cut']}」・凡例・列の見出しの割合が 50番の定数 {frac:.2f} と一致",
              T["cut"] == f"{frac:.2f}T" and T["cut"] in texts and T["trunc"] in texts
              and f"{frac:.2f}T" in _col_header(labels, "trunc065", lang))
        # 3. 文字の大きさ
        bad = common.check_min_font(fig)
        check(f"[{lang}] 文字がすべて {common.MIN_FONT_PT:g} pt 以上", not bad, str(bad[:3]))
        # 4. 注記
        check(f"[{lang}] 「合成脈波（例示）」の札がある", TEXT[lang]["synthetic"] in texts)
        check(f"[{lang}] 探索・事後の注記がある", _squash(labels["posthoc_note"][lang]) in _squash(alltext))
        # 5. 判定の語を書かない
        hits = [t[:30] for t in texts if _has_verdict(t, lang)]
        check(f"[{lang}] 図の中に判定の語が無い", not hits, str(hits))
        # 6. 禁止語
        if banned is None:
            print(f"[SKIP] [{lang}] 用語検査器が無いので禁止語の検査は飛ばす")
        else:
            hits = [(t[:30], h) for t in texts for h in _has_banned(t, banned)]
            check(f"[{lang}] 図の文字列に禁止語が無い", not hits, str(hits[:3]))
        w_in, h_in = fig.get_size_inches()
        check(f"[{lang}] 図の幅が {WIDTH_MM:g} mm", abs(w_in * 25.4 - WIDTH_MM) < 0.01)
        check(f"[{lang}] 図の高さが脚注の行数と凡例の実測から決めた値（{rec['H_mm']:.1f} mm）",
              abs(h_in * 25.4 - rec["H_mm"]) < 0.01)
        check(f"[{lang}] 凡例の幅（{rec['legend_w_mm']:.1f} mm）が図の幅に収まる",
              rec["legend_w_mm"] <= WIDTH_MM - 2 * MARGIN_MM)
        # 7. 文字が図の中に収まり、互いに重ならない（合成の札と列の見出し、脚注と下端など）
        outside, overlap = _layout_problems(fig)
        check(f"[{lang}] すべての文字が図の中に収まる", not outside, str(outside[:3]))
        check(f"[{lang}] 文字どうしが重ならない", not overlap, str(overlap[:3]))
        plt.close(fig)

    ok = all(results)
    print(f"\n{'ALL PASS' if ok else 'FAILED'}: {sum(results)}/{len(results)}")
    return 0 if ok else 1


# ---------------------------------------------------------------- 入口

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--lang", choices=["ja", "en"], default=None, help="省略すると両方")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out-dir", default=str(common.OUT))
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    out = Path(a.out_dir)
    common.OUT = out
    labels = json.load(open(LABELS, encoding="utf-8"))
    for lang in ([a.lang] if a.lang else ["ja", "en"]):
        fig, rec = build(lang, labels)
        paths = common.save(fig, NAME, lang)
        plt.close(fig)
        out.mkdir(parents=True, exist_ok=True)
        lp = out / f"{NAME}_legend_{lang}.txt"
        lp.write_text(legend_text(lang, rec), encoding="utf-8")
        for p in paths + [lp]:
            print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())

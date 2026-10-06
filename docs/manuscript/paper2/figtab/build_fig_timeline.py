#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""図3 経過の図（fig_timeline）― 研究0 → 論文2 の節目を日付順に 2 段で描く。

上段（時間軸の上）は**走らせる前に固定・予測したこと**、下段（時間軸の下）は**実行と、それが
示したこと**。節目は `data/timeline.json`（`data/prespec_chronology.json` の chronology から
選び、`docs/research/lab_log.md` の見出しと照合したもの）から読む。数値は節目の文に手で
打たず、`data/paper2_numbers.json`（`../02_tables.md` を機械で読んだもの）から実行時に埋める。

この図は事前規準による判定（2026-09-03・09-06）を**記録として**報告するだけで、新しい判定は
しない。「成立」「不成立」の語はその記録の箱にだけ現れ、「（記録）」を添える。決定試験の後の
下段の節目はすべて探索・事後で、† を付け、脚注にその旨を書く（判定には用いない）。

使い方
    python3 build_fig_timeline.py
    python3 build_fig_timeline.py --lang en
    python3 build_fig_timeline.py --selftest

出力は `out/fig_timeline_{ja,en}.{pdf,svg,png}` と `out/fig_timeline_legend_{ja,en}.txt`。
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
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.patches import FancyBboxPatch       # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common                                        # noqa: E402

REPO = HERE.parents[3]
NAME = "fig_timeline"
TIMELINE = HERE / "data" / "timeline.json"
LABELS = HERE / "data" / "labels.json"
LAB_LOG = REPO / "docs" / "research" / "lab_log.md"
CHECKER = REPO / "analysis" / "scripts" / "check_terminology.py"
RESULTS_DIR = REPO / "docs" / "research" / "results"
# 02_tables.md と lab_log が節目の出典として挙げる結果ファイル。有無は実行時に確かめ、無いものを有るとは書かない
RESULT_FILES = ["33_literature_replica_report.txt", "48_pwdb_by_waveform_type.txt", "50_reservoir_bench.txt",
                "50_reservoir_bench_C.txt", "50_reservoir_bench_BC.txt", "50_reservoir_bench_C14.txt",
                "50_reservoir_bench_B3.txt", "50_reservoir_bench_noise0.01.txt", "50_reservoir_bench_noise0.02.txt",
                "51_wave_separation.txt"]


def missing_results() -> list[str]:
    """出典に挙げた結果ファイルのうち、この作業木に無いもの。"""
    return [f for f in RESULT_FILES if not (RESULTS_DIR / f).exists()]


def _missing_results_note(lang: str) -> str:
    miss = missing_results()
    if not miss:
        return ""
    if lang == "ja":
        return ("このうち " + "・".join(miss) + " はこの作業木に無い（lab_log 追記137・144・152・158 は Mac 1 側の"
                "出力として記録している。図の数値は 02_tables.md を経由して取った）。")
    return (" Of these, " + ", ".join(miss) + " are not in the present working tree (lab-log entries 137, 144, 152 "
            "and 158 record them as output on Mac 1; the numbers in the figure were taken through 02_tables.md).")

LABEL_MAX = {"ja": 40, "en": 44}   # 節目の文の上限（字）
FONT_PT = 8.0           # 本文の文字。投稿先の最小 8 pt
LINE_MM = FONT_PT * 1.25 * 25.4 / 72.0   # 1 行の高さ [mm]（linespacing 1.25）
WIDTH_MM = common.WIDTH_MM["double"]     # 150 mm
MARGIN_MM = 1.0
BOX_W_SLOT = 1.70       # 箱の幅 [枠]。枠 ＝ 日付 1 つぶんの幅
GAP_SLOT = 0.10         # 同じ行の箱の間
TICK_MARGIN_SLOT = 0.30  # 目盛りが箱の端からこれ以上内側に入る
SLOT_LEFT, SLOT_RIGHT_EXTRA = -0.5, 0.5   # 軸の左右の余白 [枠]
PAD_MM = 1.2            # 箱の内側の余白
ROW_GAP_MM = 3.0        # 行の間
BAND_ABOVE_MM = 3.0     # 軸の線から上段の最初の行まで
BAND_BELOW_MM = 7.0     # 軸の線から下段の最初の行まで（日付の札が入る）
DATE_LABEL_MM = 1.4 + LINE_MM   # 軸の線から日付の札の下端まで
HEADER_GAP_MM = 2.0
FOOTER_GAP_MM = 2.5
CORRIDOR_SLOT = 0.05    # 接続線の両側に空いているべき幅 [枠]

POSTHOC_MARK = "†"
KINSOKU_HEAD = "、。，．）」』・〜ー"   # 行頭に置かない
KINSOKU_TAIL = "（「『"               # 行末に置かない

TEXT = {
    "ja": {
        "scale_note": "日付の間隔は経過日数に比例しない。",
        "tick_first": "2026/{m}/{d}",
        "tick": "{m}/{d}",
    },
    "en": {
        "scale_note": "Date spacing is not to scale.",
        "tick_first": "{d} {mon} 2026",
        "tick": "{d} {mon}",
    },
}
MONTH_EN = {8: "Aug", 9: "Sep", 10: "Oct"}


# ---------------------------------------------------------------- 読み込み

def load_timeline(path: Path = TIMELINE) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_labels(path: Path = LABELS) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _dig(node, path):
    for k in path:
        node = node[k]
    return node


def agg_rows(numbers: dict, spec: dict, labels: dict | None = None) -> list[dict]:
    """agg の項目が対象にする行（rows・group・where・stages で選ぶ）。参考の行は除く。"""
    labels = labels or load_labels()
    rows = [r for r in numbers["tables"][spec["table"]]["rows"] if not r.get("reference")]
    if "rows" in spec:
        rows = [r for r in rows if r.get("id") in spec["rows"]]
    if "group" in spec:
        rows = [r for r in rows if labels["variants"].get(r.get("id"), {}).get("group") == spec["group"]]
    for k, v in spec.get("where", {}).items():
        rows = [r for r in rows if r.get(k) == v]
    if "stages" in spec:
        rows = [r for r in rows if r.get("stage") in spec["stages"]]
    return rows


def resolve_value(numbers: dict, spec: dict):
    """values の 1 項目を data/paper2_numbers.json から引く。見つからなければ KeyError。

    1 つの値（table・row・stage・path）、行の集まりの最大・最小（agg）、表の前書きの数（preamble_re）の 3 通り。
    """
    if "meta" in spec:
        return _dig(numbers["meta"], spec["meta"])
    if "preamble_re" in spec:
        text = " ".join(numbers["tables"][spec["table"]]["preamble"])
        m = re.search(spec["preamble_re"], text)
        if not m:
            raise KeyError(f"{spec['table']} の前書きに {spec['preamble_re']} が無い")
        return int(m.group(1).replace(",", ""))
    if "agg" in spec:
        rows = agg_rows(numbers, spec)
        vals = [_dig(r, spec["path"]) for r in rows]
        vals = [v for v in vals if v is not None]
        if not vals:
            raise KeyError(f"{spec} に当たる値が無い")
        if spec["agg"] == "max":
            return max(vals)
        if spec["agg"] == "min":
            return min(vals)
        if spec["agg"] == "absmax":
            return max(abs(v) for v in vals)
        raise KeyError(f"agg {spec['agg']} は扱わない")
    table = numbers["tables"][spec["table"]]
    rows = [r for r in table["rows"]
            if r.get("id") == spec["row"] and ("stage" not in spec or r.get("stage") == spec["stage"])]
    if len(rows) != 1:
        raise KeyError(f"{spec['table']} の行 {spec['row']}（{spec.get('stage', '')}）が {len(rows)} 件")
    node = rows[0]
    for k in spec["path"]:
        node = node[k]
    if node is None:
        raise KeyError(f"{spec} が null")
    return node


def resolve_all(numbers: dict, tl: dict) -> tuple[dict, dict]:
    """(埋める文字列, 生の値) の 2 つの辞書を返す。"""
    strings, raw = {}, {}
    for name, spec in tl["values"].items():
        v = resolve_value(numbers, spec)
        raw[name] = v
        strings[name] = spec["fmt"].format(v)
    return strings, raw


def fill(template: str, strings: dict) -> str:
    s = template
    for k, v in strings.items():
        s = s.replace("{" + k + "}", v)
    if "{" in s or "}" in s:
        raise ValueError(f"埋め残しがある: {s}")
    return s


BOX_KEYS = ("label", "numbers")      # 箱に書く文。出どころ（source・source_en）は凡例文にだけ書く


def milestone_texts(m: dict, lang: str, strings: dict) -> dict:
    """1 つの節目の、箱に書く 2 つの文（label・numbers）と、凡例文に書く出どころ（source）を返す。"""
    label = fill(m[f"label_{lang}"], strings)
    if m.get("post_hoc"):
        label = POSTHOC_MARK + " " + label
    numbers = fill(m[f"numbers_{lang}"], strings) if m.get(f"numbers_{lang}") else ""
    source = m["source"] if lang == "ja" else m["source_en"]
    return {"label": label, "numbers": numbers, "source": source}


# ---------------------------------------------------------------- 文字の折り返し

class Measurer:
    """フォントで実際に測って折り返すための物差し。"""

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


_UNIT_RE = re.compile(r"\s+|[^　-ヿ㐀-鿿豈-﫿＀-￯\s]+|.")


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


# ---------------------------------------------------------------- 配置

def _pack_row(ticks: list[float], w: float, gap: float, m: float, left: float, right: float):
    """同じ行の箱（目盛りの順）を、目盛りを含み・重ならず・左右の端に収まるよう置く。
    返り値は各箱の左端 [枠]。収まらなければ None。"""
    n = len(ticks)
    lo = [0.0] * n
    prev = None
    for i, tk in enumerate(ticks):
        lo[i] = max(tk + m - w, left)
        if prev is not None:
            lo[i] = max(lo[i], prev + w + gap)
        if lo[i] > tk - m or lo[i] + w > right:
            return None
        prev = lo[i]
    hi = [0.0] * n
    nxt = None
    for i in range(n - 1, -1, -1):
        hi[i] = min(ticks[i] - m, right - w)
        if nxt is not None:
            hi[i] = min(hi[i], nxt - gap - w)
        nxt = hi[i]
    out, prev_right = [], None
    for i, tk in enumerate(ticks):
        lo_i = lo[i] if prev_right is None else max(lo[i], prev_right + gap)
        x = min(max(tk - w / 2.0, lo_i), hi[i])
        out.append(x)
        prev_right = x + w
    return out


def assign_rows(items: list[dict], w: float, gap: float, m: float, left: float, right: float):
    """節目を行に割り当てる（日付順に交互。2 行で収まらなければ 3 行、…）。
    各節目に `row`（0 が軸に最も近い）と `x0`（左端 [枠]）を書き込む。"""
    for n_rows in range(2, 7):
        rows = [[] for _ in range(n_rows)]
        for k, it in enumerate(items):
            rows[k % n_rows].append(it)
        placed = []
        ok = True
        for r, row in enumerate(rows):
            xs = _pack_row([it["tick"] for it in row], w, gap, m, left, right)
            if xs is None:
                ok = False
                break
            placed.append((r, row, xs))
        if ok:
            for r, row, xs in placed:
                for it, x in zip(row, xs):
                    it["row"], it["x0"] = r, x
            return n_rows
    raise RuntimeError("節目が多すぎて 6 行でも収まらない")


# ---------------------------------------------------------------- 描画

def build(lang: str, numbers: dict | None = None, tl: dict | None = None,
          labels: dict | None = None):
    """図を組む。返り値は (fig, record)。record は自己検査と凡例文のための記録。"""
    common.setup(lang, base_pt=FONT_PT)
    numbers = numbers or common.load_numbers()
    tl = tl or load_timeline()
    labels = labels or load_labels()
    strings, raw = resolve_all(numbers, tl)
    ms = tl["milestones"]

    dates = sorted({m["date"] for m in ms})
    slot_of = {d: i for i, d in enumerate(dates)}
    n_slot = len(dates)
    slot_mm = (WIDTH_MM - 2 * MARGIN_MM) / (n_slot + SLOT_RIGHT_EXTRA - SLOT_LEFT)
    x_of = lambda s: MARGIN_MM + (s - SLOT_LEFT) * slot_mm   # noqa: E731  枠 → mm
    box_w_mm = BOX_W_SLOT * slot_mm
    text_w_mm = box_w_mm - 2 * PAD_MM

    meas = Measurer(FONT_PT)
    try:
        # 箱ごとの文と行数
        items = {"pre": [], "run": []}
        for idx, m in enumerate(ms):
            tx = milestone_texts(m, lang, strings)
            lines = []
            parts = []
            for key in BOX_KEYS:
                if tx[key]:
                    # 測った幅は 100 dpi の描画器のもので、600 dpi の出力とわずかに違う。箱の縁に掛からないよう 0.8 mm 控える
                    wl = wrap_text(tx[key], text_w_mm - 0.8, meas, lang)
                    for ln in wl:
                        if meas.width_mm(ln) > text_w_mm + 0.3:
                            raise RuntimeError(f"折り返しても箱の幅を超える: {ln}")
                    parts.append((key, wl))
                    lines += wl
            it = {"m": m, "idx": idx, "texts": tx, "parts": parts,
                  "tick": slot_of[m["date"]] + 0.5,
                  "h_mm": 2 * PAD_MM + len(lines) * LINE_MM + 0.6}
            items[m["lane"]].append(it)
        for lane in items:
            # 日付順。同じ日付では「判定の記録」を後に置く（交互の割り当てで軸に近い行に来る）
            items[lane].sort(key=lambda it: (it["m"]["date"], bool(it["m"].get("recorded_decision")), it["idx"]))
            assign_rows(items[lane], BOX_W_SLOT, GAP_SLOT, TICK_MARGIN_SLOT,
                        SLOT_LEFT, n_slot + SLOT_RIGHT_EXTRA)

        # 行の高さ
        def row_heights(lane):
            n = 1 + max(it["row"] for it in items[lane])
            return [max(it["h_mm"] for it in items[lane] if it["row"] == r) for r in range(n)]
        rh = {lane: row_heights(lane) for lane in items}
        upper_h = sum(rh["pre"]) + ROW_GAP_MM * (len(rh["pre"]) - 1)
        lower_h = sum(rh["run"]) + ROW_GAP_MM * (len(rh["run"]) - 1)

        # 見出しと脚注（図の全幅で折り返す）
        full_w = WIDTH_MM - 2 * MARGIN_MM
        header = [tl["lanes"]["pre"][lang], tl["lanes"]["run"][lang]]
        footer_src = [POSTHOC_MARK + " " + labels["posthoc_note"][lang],
                      labels["stage_note"][lang],
                      TEXT[lang]["scale_note"]]
        # 測る描画器（100 dpi）と出力（600 dpi）で幅がわずかに違うので、1 mm 控えて折る（図幅 150 mm を超えないように）
        header_lines = [ln for h in header for ln in wrap_text(h, full_w - 1.0, meas, lang)]
        footer_lines = [ln for ftxt in footer_src for ln in wrap_text(ftxt, full_w - 1.0, meas, lang)]
        header_h = len(header_lines) * LINE_MM
        footer_h = len(footer_lines) * LINE_MM
    finally:
        meas.close()

    H = (MARGIN_MM + header_h + HEADER_GAP_MM + upper_h + BAND_ABOVE_MM + BAND_BELOW_MM
         + lower_h + FOOTER_GAP_MM + footer_h + MARGIN_MM)
    fig = plt.figure(figsize=(common.mm(WIDTH_MM), common.mm(H)))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, WIDTH_MM)
    ax.set_ylim(0, H)
    ax.set_aspect("equal")
    ax.axis("off")

    ink, grey, blue = common.PALETTE["ink"], common.PALETTE["grey"], common.PALETTE["pda"]
    y_top = H - MARGIN_MM
    ax.text(MARGIN_MM, y_top, "\n".join(header_lines), ha="left", va="top",
            fontsize=FONT_PT, linespacing=1.25, color=ink)
    y_ax = y_top - header_h - HEADER_GAP_MM - upper_h - BAND_ABOVE_MM

    # 時間軸
    x_l, x_r = x_of(SLOT_LEFT), x_of(n_slot + SLOT_RIGHT_EXTRA)
    ax.annotate("", xy=(x_r, y_ax), xytext=(x_l, y_ax),
                arrowprops=dict(arrowstyle="-|>", color=ink, lw=0.8, shrinkA=0, shrinkB=0,
                                mutation_scale=8))
    tick_labels = []
    for i, d in enumerate(dates):
        xt = x_of(i + 0.5)
        ax.plot([xt, xt], [y_ax - 0.8, y_ax + 0.8], color=ink, lw=0.6, solid_capstyle="butt")
        y, mo, dd = (int(v) for v in d.split("-"))
        tmpl = TEXT[lang]["tick_first"] if i == 0 else TEXT[lang]["tick"]
        s = tmpl.format(m=mo, d=dd, mon=MONTH_EN.get(mo, str(mo)))
        ax.text(xt, y_ax - 1.4, s, ha="center", va="top", fontsize=FONT_PT, color=ink)
        tick_labels.append(s)

    # 箱
    record_boxes = []
    for lane in ("pre", "run"):
        sign = 1 if lane == "pre" else -1
        base = y_ax + BAND_ABOVE_MM if lane == "pre" else y_ax - BAND_BELOW_MM
        # 行 r の内側の縁の y
        inner_edge = []
        y = base
        for r, h in enumerate(rh[lane]):
            inner_edge.append(y)
            y += sign * (h + ROW_GAP_MM)
        for it in items[lane]:
            m, r = it["m"], it["row"]
            x0 = x_of(it["x0"])
            h = it["h_mm"]
            y_in = inner_edge[r]
            y0 = y_in if sign > 0 else y_in - h           # 箱の下端
            y1 = y0 + h
            post = bool(m.get("post_hoc"))
            rec = bool(m.get("recorded_decision"))
            fc = "#E9F0F7" if lane == "pre" else "white"
            ec = blue if lane == "pre" else ink
            ls = (0, (2.2, 1.4)) if post else "solid"
            lw = 0.9 if rec else 0.6
            ax.add_patch(FancyBboxPatch((x0, y0), box_w_mm, h,
                                        boxstyle="round,pad=0,rounding_size=0.8",
                                        fc=fc, ec=ec, lw=lw, ls=ls, zorder=3))
            # 文（label → numbers → source の順に上から）
            yy = y1 - PAD_MM
            drawn = []
            for key, wl in it["parts"]:
                col = grey if key == "source" else ink
                ax.text(x0 + PAD_MM, yy, "\n".join(wl), ha="left", va="top",
                        fontsize=FONT_PT, linespacing=1.25, color=col, zorder=4)
                drawn.append((key, "".join(wl) if lang == "ja" else " ".join(wl)))
                yy -= len(wl) * LINE_MM
            # 接続線。内側の行に同じ日付の箱があればその箱の外側の縁から、無ければ軸から
            xt = x_of(it["tick"])
            # 上段は軸の線から。下段は日付の札の下から（線が札を横切らないように）
            y_from = y_ax if sign > 0 else y_ax - DATE_LABEL_MM - 0.4
            for other in items[lane]:
                if other is it or other["row"] >= r or other["m"]["date"] != m["date"]:
                    continue
                oy_in = inner_edge[other["row"]]
                oy_out = oy_in + sign * other["h_mm"]
                if sign > 0:
                    y_from = max(y_from, oy_out)
                else:
                    y_from = min(y_from, oy_out)
            y_to = y0 if sign > 0 else y1
            ax.plot([xt, xt], [y_from, y_to], color=ink, lw=0.5, zorder=2)
            record_boxes.append({"id": m["id"], "lane": lane, "row": r, "tick": it["tick"],
                                 "x0_slot": it["x0"], "x1_slot": it["x0"] + BOX_W_SLOT,
                                 "x0": x0, "x1": x0 + box_w_mm, "y0": y0, "y1": y1,
                                 "texts": it["texts"], "drawn": drawn, "y_from": y_from,
                                 "post_hoc": post, "recorded": rec, "date": m["date"]})

    # 脚注
    ax.text(MARGIN_MM, MARGIN_MM + footer_h, "\n".join(footer_lines), ha="left", va="top",
            fontsize=FONT_PT, linespacing=1.25, color=ink)

    record = {"lang": lang, "strings": strings, "raw": raw, "boxes": record_boxes,
              "dates": dates, "ticks": tick_labels, "H_mm": H, "W_mm": WIDTH_MM, "y_ax": y_ax,
              "header": header_lines, "footer": footer_lines,
              "n_rows": {lane: len(rh[lane]) for lane in rh}}
    return fig, record


# ---------------------------------------------------------------- 凡例の文

def describe_spec(spec: dict, lang: str) -> str:
    """values の 1 項目がどこから来たかを、凡例文に書く形にする（表の番号は 02_tables.md のもの）。"""
    if "meta" in spec:
        return "meta." + ".".join(spec["meta"])
    t = spec["table"]
    t_txt = (f"02_tables.md {t}（この集の{common.table_no(t, 'ja')}）" if lang == "ja"
             else f"table {t[1:]} of 02_tables.md ({common.table_no(t, 'en').lower()} of this set)")
    if "preamble_re" in spec:
        return t_txt + (" の前書きの数" if lang == "ja" else ", number in the preamble")
    path = ".".join(spec["path"])
    if "agg" in spec:
        sel = []
        if "rows" in spec:
            sel.append("行 " + "・".join(spec["rows"]) if lang == "ja" else "rows " + ", ".join(spec["rows"]))
        if "group" in spec:
            sel.append((f"群 {spec['group']} の行（labels.json）" if lang == "ja" else f"rows of group {spec['group']} (labels.json)"))
        for k, v in spec.get("where", {}).items():
            sel.append(f"{k} = {v}")
        if "stages" in spec:
            sel.append(("段 " + "・".join(spec["stages"])) if lang == "ja" else "tiers " + ", ".join(spec["stages"]))
        agg = {"max": ("最大", "maximum"), "min": ("最小", "minimum"), "absmax": ("絶対値の最大", "largest absolute value")}[spec["agg"]]
        if lang == "ja":
            return f"{t_txt} の{'、'.join(sel) or '参考を除く全行'}の {path} の{agg[0]}"
        return f"{agg[1]} of {path} over {'; '.join(sel) or 'all non-reference rows'} of {t_txt}"
    stage = spec.get("stage")
    if lang == "ja":
        return f"{t_txt} 行 `{spec['row']}`" + (f"（{stage} 段）" if stage else "") + f" {path}"
    return f"{t_txt}, row `{spec['row']}`" + (f" (tier {stage})" if stage else "") + f", {path}"


def legend_text(lang: str, rec: dict, tl: dict, labels: dict) -> str:
    ms = tl["milestones"]
    n_pre = sum(m["lane"] == "pre" for m in ms)
    n_run = sum(m["lane"] == "run" for m in ms)
    if lang == "ja":
        out = ["図3　研究0（PWDB・決定試験）から改良の探索までの経過。上段は走らせる前に固定・予測したこと、"
               "下段は実行と、それが示したこと。",
               "",
               f"示しているもの: 日付順の節目（上段 {n_pre}・下段 {n_run}）。上段の箱は規則・閾値・予測を実行の前に固定した記録、"
               "下段の箱はその実行の結果で、箱の 2 行目以降はその結果を表す数値。2026-09-03 と 09-06 の下段の箱は事前規準による判定の記録で、"
               "「成立」「不成立」はその記録を写したもの（この図は新しい判定をしない）。† の箱は決定試験の後の"
               "探索・事後の解析で、判定には用いない。日付の間隔は経過日数に比例しない。",
               "",
               "2026-09-15 の順序（この図に関わる同じ日の 5 つの記録。lab_log の追記番号の順）: 追記139 で拡張期の下降への手当ての候補を挙げ、"
               "その (3) が「当てはめの範囲を 0.65T までに切る、または 1 次微分の領域で当てはめる」（実データに当てる前）。"
               "追記141 で合成脈波の診断をし、Δμ の下限が主因と読んだ。追記143 で再当てはめ（節C）の予測 P6〜P10 を固定した。"
               "追記144 で 5 型を 4,374 名に当て、P6〜P9 はいいえ（P10 は配線の検算で はい）、Δμ の下限に張り付いた拍は 1 拍も無く、"
               "合成からの読みは否定された。予測していなかった (6) 0.65T の打ち切り（Δμ の下限 0.01 s と併用）が |ρ| 最大だった。"
               "追記145 で、主の割合を 0.65T のまま選び直さないと取り決めた（0.55T・0.75T は感度の記述だけ）。"
               "上段の 9/15 の箱の 2 行目はこの取り決めで、5 型の実行の後・9 型の実行の前に書いた。"
               "0.65 は追記139 の候補 (3) に由来し、同じ値は第2版の特徴点の探索で切痕を探す上限 `NOTCH_MAX_FRAC`（analysis/src/pda2.py）にもある。"
               "追記144・145 は 0.65 の出どころを「24番・追記139」と書いたが、24番（24_pwdb_pda_ablation.py）にあるのは 0.60·T で、"
               "0.65 は無い（lab_log 追記162 で訂正）。",
               "",
               "選び方による楽観: 9/16〜9/17 の箱の良い版は、当てた 14 型から事後に選んだので、その値は楽観側にある。",
               "",
               "数値の出どころ（すべて 02_tables.md を機械で読んだ data/paper2_numbers.json から実行時に埋めた。表の番号は 02_tables.md のもの）:"]
        for name, spec in tl["values"].items():
            out.append(f"  {name} = {rec['strings'][name]}　← {describe_spec(spec, 'ja')}")
        out += ["",
                "節目の出典（docs/research/lab_log.md の見出しに照合済み）:"]
        for m in ms:
            out.append(f"  {m['date']}　{'上段' if m['lane'] == 'pre' else '下段'}　"
                       f"{fill(m['label_ja'], rec['strings'])}　← {m['source']}")
        out += ["",
                "台本と結果ファイル: 20番（20_pwdb_validity.py）・23番（23_pwdb_landmarks.py）・26番（26_pwdb_compare.py）・"
                "27番・31番・33番・48番（48_pwdb_by_waveform_type.py）・50番（50_reservoir_bench.py 節A・B・C）・"
                "51番（51_pwdb_wave_separation.py）。結果は docs/research/results/ の "
                + "・".join(RESULT_FILES) + "。" + _missing_results_note("ja"),
                "",
                "段の注釈: " + labels["stage_note"]["ja"],
                "探索・事後の注記: " + labels["posthoc_note"]["ja"],
                "",
                "図の台本: docs/manuscript/paper2/figtab/build_fig_timeline.py（data/timeline.json・data/paper2_numbers.json・"
                "data/labels.json を読む）。"]
    else:
        out = ["Figure 3. Course of the study from Study 0 (PWDB decision test) to the exploratory search for an "
               "improved fit. Upper lane: what was fixed or predicted before each run; lower lane: the runs and "
               "what they showed.",
               "",
               f"What is shown: dated milestones ({n_pre} in the upper lane, {n_run} in the lower lane). Upper boxes record rules, "
               "thresholds and predictions fixed before the run; lower boxes record the result of that run, with the numbers that "
               "show it from the second line on. The lower boxes on 3 and 6 September 2026 report the prespecified decisions as "
               "recorded ('pass' / 'fail' are copied from the record; the figure makes no new judgement). Boxes marked † are "
               "exploratory, post hoc analyses run after the decision test and are not used for the decision. Date spacing is not "
               "to scale.",
               "",
               "Order on 15 September 2026 (the five records of that day that bear on this figure, in the order of the lab-log entries): entry 139 listed candidate "
               "remedies for the diastolic decline, of which (3) was 'truncate the fit at 0.65T, or fit in the first-derivative "
               "domain' (before any real data were fitted). Entry 141 diagnosed the frozen fit on synthetic beats and read the Δμ "
               "lower bound as the main cause. Entry 143 fixed the predictions P6–P10 for the refit (part C). Entry 144 fitted five "
               "variants to the 4,374 subjects: P6–P9 no (P10, a wiring check, yes); no beat sat at the Δμ lower bound, so the "
               "reading from the synthetic beats was refuted; the unpredicted variant (6), the 0.65T truncation combined with a Δμ "
               "lower bound of 0.01 s, gave the highest |ρ|. Entry 145 agreed that the main fraction stays at 0.65T and is not "
               "re-selected (0.55T and 0.75T only as a sensitivity description); the second line of the upper box on 15 September is "
               "this agreement, written after the 5-variant run and before the 9-variant run. The value 0.65 comes from candidate (3) "
               "of entry 139; the same value is the notch search limit `NOTCH_MAX_FRAC` (analysis/src/pda2.py) of the rebuilt "
               "fiducial-point detection. Entries 144 and 145 gave its source as 'script 24 and entry 139', but script 24 "
               "(24_pwdb_pda_ablation.py) contains 0.60·T and not 0.65 (corrected in lab-log entry 162).",
               "",
               "Optimism from selection: the better versions in the boxes of 16–17 September were chosen post hoc from the 14 "
               "versions fitted, so their values are optimistic.",
               "",
               "Numbers (all filled at run time from data/paper2_numbers.json, parsed mechanically from 02_tables.md; table numbers "
               "are those of 02_tables.md):"]
        for name, spec in tl["values"].items():
            out.append(f"  {name} = {rec['strings'][name]}  <- {describe_spec(spec, 'en')}")
        out += ["",
                "Milestone sources (cross-checked against the headings of docs/research/lab_log.md):"]
        for m in ms:
            out.append(f"  {m['date']}  {'upper' if m['lane'] == 'pre' else 'lower'}  "
                       f"{fill(m['label_en'], rec['strings'])}  <- {m['source_en']}")
        out += ["",
                "Scripts and result files: scripts 20 (20_pwdb_validity.py), 23 (23_pwdb_landmarks.py), 26 (26_pwdb_compare.py), "
                "27, 31, 33, 48 (48_pwdb_by_waveform_type.py), 50 (50_reservoir_bench.py, sections A, B, C) and "
                "51 (51_pwdb_wave_separation.py). Results in docs/research/results/: "
                + ", ".join(RESULT_FILES) + "." + _missing_results_note("en"),
                "",
                "Tier note: " + labels["stage_note"]["en"],
                "Post-hoc note: " + labels["posthoc_note"]["en"],
                "",
                "Script: docs/manuscript/paper2/figtab/build_fig_timeline.py (reads data/timeline.json, "
                "data/paper2_numbers.json and data/labels.json)."]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- 自己検査

def _banned_terms():
    """用語検査器の禁止語の表を読む（一覧をこの台本に写さない）。検査器が無ければ None。"""
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


# 判定の語。英語は語の境界で見る（"the method" の中の met のような部分一致を拾わないため）
_VERDICT = {"ja": [re.compile("成立")],
            "en": [re.compile(r"\b(not\s+)?met\b", re.I), re.compile(r"\bpass(ed|es|ing)?\b", re.I),
                   re.compile(r"\bfail(ed|s|ure|ing)?\b", re.I)]}
_RECORD_MARK = {"ja": "記録", "en": "recorded"}


def _has_verdict(text: str, lang: str) -> bool:
    return any(p.search(text) for p in _VERDICT[lang])


def _squash(s: str) -> str:
    """空白をすべて除く（折り返しで入った改行と語間の空白を無視して比べるため）。"""
    return re.sub(r"\s+", "", s)


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


def selftest() -> int:
    results = []

    def check(name, ok, info=""):
        results.append(ok)
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {info}" if info and not ok else ""))

    tl = load_timeline()
    labels = load_labels()
    numbers = common.load_numbers()
    banned = _banned_terms()
    ms = tl["milestones"]

    # 1. 節目の文の長さ・欄
    too_long = [(m["id"], lg, len(m[f"label_{lg}"])) for m in ms for lg in ("ja", "en")
                if len(m[f"label_{lg}"]) > LABEL_MAX[lg]]
    check(f"節目の文が和文 {LABEL_MAX['ja']} 字・英文 {LABEL_MAX['en']} 字以内", not too_long, str(too_long))
    check("lane が pre/run のどちらか", all(m["lane"] in ("pre", "run") for m in ms))
    check("日付が YYYY-MM-DD", all(re.fullmatch(r"2026-\d{2}-\d{2}", m["date"]) for m in ms))

    # 1b. 2026-09-15 の順序: 0.65T の候補（追記139）・予測（追記143）・取り決め（追記145）を上段の 1 つの箱に、
    #     5 型の実行（追記144）を下段の 9/15 に、7 型・10 型（追記146・147）を 9/16 に置く
    by_id = {m["id"]: m for m in ms}
    heads_of = lambda mid: " ".join(by_id[mid].get("lab_log_headings", []))   # noqa: E731
    check("9/15 の上段の箱が追記139・143・145 を指す", by_id["u5"]["date"] == "2026-09-15"
          and all(f"追記{k}" in heads_of("u5") for k in (139, 143, 145)))
    check("5 型の実行（追記144）が 9/15 の下段、7 型・10 型（追記146・147）が 9/16 の下段",
          by_id["r6"]["date"] == "2026-09-15" and "追記144" in heads_of("r6")
          and by_id["r6b"]["date"] == "2026-09-16" and all(f"追記{k}" in heads_of("r6b") for k in (146, 147)))

    # 2. lab_log の見出しとの照合
    if LAB_LOG.exists():
        heads = [ln for ln in LAB_LOG.read_text(encoding="utf-8").splitlines() if ln.startswith("## ")]
        missing = [(m["id"], h) for m in ms for h in m.get("lab_log_headings", [])
                   if not any(h in ln for ln in heads)]
        check("節目の出典が lab_log.md の見出しにある", not missing, str(missing))
    else:
        print("[SKIP] lab_log.md が無いので見出しの照合は飛ばす")

    for lang in ("ja", "en"):
        fig, rec = build(lang, numbers, tl, labels)
        texts = common.texts_of(fig)
        alltext = "\n".join(texts)

        # 3. 描いた値が JSON の値と一致する（読み直して比べる）
        fresh = common.load_numbers()
        s2, r2 = resolve_all(fresh, tl)
        same = all(rec["raw"][k] == r2[k] and rec["strings"][k] == s2[k] for k in r2)
        check(f"[{lang}] 埋めた数値が data/paper2_numbers.json の値と一致", same)
        boxes_text = {b["id"]: b for b in rec["boxes"]}
        used = []
        for m in ms:
            for key in (f"label_{lang}", f"numbers_{lang}"):
                tmpl = m.get(key) or ""
                for name in re.findall(r"\{(\w+)\}", tmpl):
                    used.append((m["id"], name))
        present = all(s2[name] in "".join(t for _k, t in boxes_text[mid]["drawn"]) for mid, name in used)
        check(f"[{lang}] 箱の文に埋めた数値の文字列がそのまま現れる（{len(used)} 箇所）", present)

        # 4. 箱の文が JSON の文と一致（折り返しを戻して比べる）
        mism = []
        for m in ms:
            want = milestone_texts(m, lang, s2)
            got = dict(boxes_text[m["id"]]["drawn"])
            for key in BOX_KEYS:
                w = want[key]
                g = got.get(key, "")
                if (w.replace(" ", "") if lang == "ja" else w) != (g.replace(" ", "") if lang == "ja" else g):
                    mism.append((m["id"], key, w, g))
        check(f"[{lang}] 箱の文が timeline.json の文（数値を埋めたもの）と一致", not mism, str(mism[:2]))

        # 4b. 図の中に出どころ（lab_log・追記・台本の番号・02_tables.md の表番号）を書かない。出どころは凡例文にある
        prov_re = (r"追記|lab_log|lab log|02_tables|\d+\s*番|表\s*\d" if lang == "ja"
                   else r"(?i)\bentr(y|ies)\b|lab[_ ]log|02_tables|\bscript\s*\d|\btable\s*\d")
        prov = [t[:30] for t in texts if re.search(prov_re, t)]
        check(f"[{lang}] 図の中に出どころ（lab_log・追記・台本の番号・表番号）を書いていない", not prov, str(prov[:3]))
        leg = legend_text(lang, rec, tl, labels)
        srcs = [m["source"] if lang == "ja" else m["source_en"] for m in ms]
        check(f"[{lang}] 凡例文に全節目の出典がある", all(x and x in leg for x in srcs))
        if lang == "en":
            cjk = [m["id"] for m in ms if re.search(r"[぀-ヿ一-鿿]", m["source_en"])]
            check("[en] 英文の出典に和文が混じっていない", not cjk, str(cjk))

        # 5. 文字の大きさ
        bad = common.check_min_font(fig)
        check(f"[{lang}] 文字がすべて {common.MIN_FONT_PT:g} pt 以上", not bad, str(bad[:3]))

        # 6. 段の注釈・事後の注記
        footer = _squash("".join(rec["footer"]))
        drawn_all = _squash(alltext)
        sn = _squash(labels["stage_note"][lang])
        pn = _squash(POSTHOC_MARK + labels["posthoc_note"][lang])
        check(f"[{lang}] 段の注釈が脚注にある", sn in footer and sn in drawn_all)
        check(f"[{lang}] 探索・事後の注記（{POSTHOC_MARK}）が脚注にある", pn in footer and pn in drawn_all)
        check(f"[{lang}] 決定試験の後の下段の箱に {POSTHOC_MARK} が付く",
              all(b["post_hoc"] == (b["lane"] == "run" and b["date"] > "2026-09-06"
                                     or b["id"] == "r3") for b in rec["boxes"]))

        # 7. 判定の語は「記録」の箱にだけ
        offenders = []
        for b in rec["boxes"]:
            t = " ".join(x for _k, x in b["drawn"])
            if _has_verdict(t, lang) and not (b["recorded"] and _RECORD_MARK[lang] in t.lower()):
                offenders.append(b["id"])
        for ln in rec["header"] + rec["footer"] + rec["ticks"]:
            if _has_verdict(ln, lang):
                offenders.append("header/footer:" + ln[:20])
        check(f"[{lang}] 成立・不成立の語は判定の記録の箱（記録と明記）にだけ現れる", not offenders, str(offenders))
        rec_boxes = [b for b in rec["boxes"] if b["recorded"]]
        check(f"[{lang}] 判定の記録の箱（{len(rec_boxes)} 個）に「{_RECORD_MARK[lang]}」が明記されている",
              bool(rec_boxes) and all(_RECORD_MARK[lang] in " ".join(x for _k, x in b["drawn"]).lower()
                                      for b in rec_boxes))

        # 8. 禁止語
        if banned is None:
            print(f"[SKIP] [{lang}] 用語検査器が無いので禁止語の検査は飛ばす")
        else:
            hits = [(t[:30], h) for t in texts for h in _has_banned(t, banned)]
            check(f"[{lang}] 図の文字列に禁止語が無い", not hits, str(hits[:3]))

        # 9. 幾何: 箱が重ならない・接続線の通り道が空いている・図の幅
        boxes = rec["boxes"]
        overlap = []
        for i, a in enumerate(boxes):
            for b in boxes[i + 1:]:
                if a["x0"] < b["x1"] and b["x0"] < a["x1"] and a["y0"] < b["y1"] and b["y0"] < a["y1"]:
                    overlap.append((a["id"], b["id"]))
        check(f"[{lang}] 箱が重ならない", not overlap, str(overlap))
        blocked = []
        for b in boxes:
            if b["row"] == 0:
                continue
            for a in boxes:
                if a["lane"] != b["lane"] or a["row"] >= b["row"] or a["date"] == b["date"]:
                    continue
                if a["x0_slot"] < b["tick"] + CORRIDOR_SLOT and b["tick"] - CORRIDOR_SLOT < a["x1_slot"]:
                    blocked.append((b["id"], a["id"]))
        check(f"[{lang}] 接続線が他の箱を横切らない", not blocked, str(blocked))
        inside = all(0 <= b["x0"] and b["x1"] <= rec["W_mm"] and 0 <= b["y0"] and b["y1"] <= rec["H_mm"]
                     for b in boxes)
        check(f"[{lang}] 箱が図の中に収まる", inside)
        w_in, h_in = fig.get_size_inches()
        check(f"[{lang}] 図の幅が {WIDTH_MM:g} mm", abs(w_in * 25.4 - WIDTH_MM) < 0.01)
        check(f"[{lang}] 段が 2 段（上・下）で、各段 2 行以内",
              rec["n_rows"] == {"pre": 2, "run": 2}, str(rec["n_rows"]))
        check(f"[{lang}] 日付の札が {len(rec['dates'])} 個", len(rec["ticks"]) == len(rec["dates"]))
        check(f"[{lang}] 下段の接続線は日付の札の下から始まる（札を横切らない）",
              all(b["y_from"] <= rec["y_ax"] - DATE_LABEL_MM for b in boxes if b["lane"] == "run"))
        outside, overlap = _layout_problems(fig)
        check(f"[{lang}] すべての文字が図の中に収まる", not outside, str(outside[:3]))
        check(f"[{lang}] 文字どうしが重ならない", not overlap, str(overlap[:3]))
        cs = common.texts_crossing_spines(fig)
        check(f"[{lang}] 枠の中の文字が軸の線に掛かっていない", not cs, str(cs[:3]))
        tlo = common.text_line_overlaps(fig)
        check(f"[{lang}] 枠の中の文字を線が貫いていない（白い地で隠れる参照の線を除く）", not tlo, str(tlo[:3]))
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
    tl, labels, numbers = load_timeline(), load_labels(), common.load_numbers()
    for lang in ([a.lang] if a.lang else ["ja", "en"]):
        fig, rec = build(lang, numbers, tl, labels)
        paths = common.save(fig, NAME, lang)
        plt.close(fig)
        out.mkdir(parents=True, exist_ok=True)
        lp = out / f"{NAME}_legend_{lang}.txt"
        lp.write_text(legend_text(lang, rec, tl, labels), encoding="utf-8")
        for p in paths + [lp]:
            print(p)
        print(f"  高さ {rec['H_mm']:.1f} mm・上段 {rec['n_rows']['pre']} 行・下段 {rec['n_rows']['run']} 行")
    return 0


if __name__ == "__main__":
    sys.exit(main())

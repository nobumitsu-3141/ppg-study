#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""論文2 図表集の共通部品（配色・フォント・保存・数値の読み込み）。

図の台本（`build_fig_*.py`）はここから取る。値は `data/paper2_numbers.json`（`data/extract_tables.py` が
`../02_tables.md` を機械で読んだもの）からだけ取り、手で打たない。

    from common import load_numbers, setup, save, PALETTE, L
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
from matplotlib import font_manager      # noqa: E402

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "paper2_numbers.json"
OUT = HERE / "out"

# 色覚多様性に配慮した配色（Okabe–Ito）。役割を固定して使う。
PALETTE = {
    "pda": "#0072B2",        # 分解法（凍結版・改良版）
    "landmark": "#D55E00",   # 特徴点法（同梱）
    "amp": "#009E73",        # 早期振幅比
    "control": "#E69F00",    # 陽性対照
    "grey": "#7F7F7F",
    "ink": "#222222",
    "light": "#BBBBBB",
}
CRITERION = 0.30

# 投稿先（Physiological Measurement, IOP 共通の規定）の図幅と最小文字サイズ。
WIDTH_MM = {"single": 85.0, "double": 150.0}   # IOP 共通: 8.5 cm／15 cm
MIN_FONT_PT = 8.0                                # IOP 共通: 最終寸法で 8〜12 pt

JA_FONT_FILES = [
    "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
]


def mm(x: float) -> float:
    """mm → inch（figsize 用）。"""
    return x / 25.4


def setup(lang: str = "ja", base_pt: float = 8.0) -> None:
    """rcParams を整える。文字は編集可能なテキストとして埋め込む。"""
    family = ["Liberation Sans", "DejaVu Sans"]   # Helvetica 互換（IOP の指定書体に合わせる）
    if lang == "ja":
        for p in JA_FONT_FILES:
            if Path(p).exists():
                font_manager.fontManager.addfont(p)
                family = [font_manager.FontProperties(fname=p).get_name()]
                break
    plt.rcParams.update({
        "font.family": family,
        "font.size": base_pt,
        "axes.titlesize": base_pt,
        "axes.labelsize": base_pt,
        "xtick.labelsize": base_pt - 1,
        "ytick.labelsize": base_pt - 1,
        "legend.fontsize": base_pt - 1,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "lines.linewidth": 1.0,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.0,      # 余白を足さない（図幅 150 mm を超えないように）
        "axes.unicode_minus": False,
    })


FIG_MAX_WIDTH_MM = 150.0


def png_size_mm(path: Path, dpi: int = 600) -> tuple[float, float]:
    """書き出した PNG の幅・高さ（mm）。"""
    from PIL import Image
    with Image.open(path) as im:
        w, h = im.size
    return w / dpi * 25.4, h / dpi * 25.4


def table_no(key: str, lang: str) -> str:
    """02_tables.md の表番号（表1・表6c など）を、この集の番号（表2・表9 など）に読み替える（labels.json の table_numbers）。"""
    import json as _json
    tn = _json.loads((HERE / "data" / "labels.json").read_text(encoding="utf-8"))["table_numbers"]
    return tn[key][lang]


def renumber(text: str) -> str:
    """JSON から写した文の中の 02_tables.md の表番号を、この集の番号に読み替える（和文）。"""
    import json as _json
    import re as _re
    tn = _json.loads((HERE / "data" / "labels.json").read_text(encoding="utf-8"))["table_numbers"]
    return _re.sub(r"表(\d+[a-z]?)(?![a-z0-9])", lambda m: tn.get("表" + m.group(1), {"ja": m.group(0)})["ja"], text)


def save(fig, name: str, lang: str, dpi: int = 600) -> list[Path]:
    """PDF・SVG・PNG を `out/` に書く。戻り値は書いたファイル。"""
    OUT.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in ("pdf", "svg", "png"):
        p = OUT / f"{name}_{lang}.{ext}"
        fig.savefig(p, dpi=dpi)
        paths.append(p)
    return paths


def load_numbers(path: Path = DATA) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_min_font(fig, min_pt: float = MIN_FONT_PT) -> list[str]:
    """図の中の全テキストの文字サイズが min_pt 以上かを確かめる。違反の一覧を返す。"""
    bad = []
    for t in fig.findobj(matplotlib.text.Text):
        s = t.get_text().strip()
        if s and t.get_fontsize() < min_pt - 1e-6:
            bad.append(f"{t.get_fontsize():.1f}pt: {s[:30]}")
    return bad


def texts_of(fig) -> list[str]:
    return [t.get_text() for t in fig.findobj(matplotlib.text.Text) if t.get_text().strip()]


_OPENING = "（「『【［〈《"
_CLOSING = "）」』】］〉》、。・，．"


def _wrap_ja(s: str, units: int) -> str:
    """和文を表示幅で折る（全角 2・半角 1 の単位）。

    半角の語（A 段の A、0.30、02_tables.md）の途中では折らず、直前の全角文字か空白の後ろで折る。
    開き括弧の直後では折らず（括弧ごと次の行へ）、閉じ括弧・句読点は行頭に来ないよう前の行にぶら下げる。
    """
    def width(t):
        return sum(2 if ord(c) > 0x2E7F else 1 for c in t)

    lines, cur, safe = [], "", 0
    for ch in s:
        cw = 2 if ord(ch) > 0x2E7F else 1
        if width(cur) + cw > units and cur:
            if ch in _CLOSING:                       # ぶら下げ
                cur += ch
                continue
            cut = len(cur)
            if cur[-1] in _OPENING or (cw == 1 and ord(cur[-1]) <= 0x2E7F):
                cut = safe if 0 < safe < len(cur) else len(cur)
            # 全角の途中で折るときは、少し手前（12 単位以内）に句読点か空白があればそこで折る
            # （「追記12」「分解法」のような語の途中で折れないように）
            if cut == len(cur) and cur[-1] not in _CLOSING and ch not in _CLOSING:
                for pos in range(len(cur) - 1, 0, -1):
                    if width(cur[pos:]) > 12:
                        break
                    if cur[pos - 1] in _CLOSING or cur[pos - 1] == " ":
                        cut = pos
                        break
            while cut > 1 and cur[cut - 1] in _OPENING:
                cut -= 1
            lines.append(cur[:cut].rstrip())
            cur = cur[cut:]
            safe = 0
        cur += ch
        if (cw == 2 and ch not in _OPENING) or ch == " ":
            safe = len(cur)
    if cur:
        lines.append(cur)
    return "\n".join(lines)


def wrap_text(s: str, lang: str, width_ja: int = 102, width_en: int = 112) -> str:
    """脚注の文を図の幅に折る（8 pt・150 mm 幅の目安: 和文 51 字、英文 112 字）。"""
    if lang == "ja":
        return _wrap_ja(s, width_ja)
    return "\n".join(textwrap.wrap(s, width=width_en, break_long_words=False, break_on_hyphens=False))


def _text_boxes(fig):
    """描画器で測った、空でない文字の (短い名, 画素の矩形) の一覧。

    目盛の数字は Axis が保持する余分な Tick（描かれない）を除き、いま使われている目盛だけを数える。
    """
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    tick_ids, active = set(), []
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            for tk in axis.majorTicks + axis.minorTicks:
                tick_ids.update((id(tk.label1), id(tk.label2)))
            if ax.get_visible() and getattr(ax, "axison", True) and axis.get_visible():
                active += axis.get_ticklabels(minor=False) + axis.get_ticklabels(minor=True)
    texts = [t for t in fig.findobj(matplotlib.text.Text) if id(t) not in tick_ids] + active
    out = []
    for t in texts:
        if not t.get_text().strip() or not t.get_visible():
            continue
        b = t.get_window_extent(renderer=r)
        if b.width > 0 and b.height > 0:
            name = t.get_text().replace("\n", " ")[:24]
            out.append((f"{name}@({b.x0 * 72 / fig.dpi:.0f},{b.y0 * 72 / fig.dpi:.0f})pt", b))
    return out


def _intersects(a, b, pad: float) -> bool:
    return (a.x0 + pad < b.x1 - pad and b.x0 + pad < a.x1 - pad
            and a.y0 + pad < b.y1 - pad and b.y0 + pad < a.y1 - pad)


def texts_outside(fig, tol_pt: float = 0.5) -> list[str]:
    """図の縁からはみ出す文字（savefig の bbox="tight" で図が宣言した幅より広くなる原因）。"""
    boxes = _text_boxes(fig)
    fb = fig.bbox
    tol = tol_pt * fig.dpi / 72
    return [name for name, b in boxes
            if b.x0 < fb.x0 - tol or b.x1 > fb.x1 + tol or b.y0 < fb.y0 - tol or b.y1 > fb.y1 + tol]


def text_overlaps(fig, pad_pt: float = 0.3) -> list[str]:
    """図の中の文字どうしの重なり（描画器の寸法で確認）。重なりの一覧を返す。pad_pt だけ縮めてから比べる。"""
    boxes = _text_boxes(fig)
    pad = pad_pt * fig.dpi / 72
    hits = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if _intersects(boxes[i][1], boxes[j][1], pad):
                hits.append(f"{boxes[i][0]!r} × {boxes[j][0]!r}")
    return hits


def text_marker_overlaps(fig, pad_pt: float = 0.3) -> list[str]:
    """文字と、線の記号（マーカー）の重なり。記号は大きさ ms の正方形として比べる。"""
    boxes = _text_boxes(fig)
    pad = pad_pt * fig.dpi / 72
    hits = []
    for ax in fig.axes:
        for ln in ax.get_lines():
            if ln.get_marker() in (None, "None", "", " ") or not ln.get_visible():
                continue
            half = ln.get_markersize() / 2 * fig.dpi / 72
            xy = ln.get_transform().transform(list(zip(ln.get_xdata(), ln.get_ydata())))
            for (px, py) in xy:
                mb = matplotlib.transforms.Bbox([[px - half, py - half], [px + half, py + half]])
                for name, tb in boxes:
                    if _intersects(mb, tb, pad):
                        hits.append(f"{name!r} × marker({ln.get_label()})")
    return sorted(set(hits))


def texts_crossing_spines(fig, pad_pt: float = 0.3) -> list[str]:
    """枠の中に置いた文字（注釈・札）が、見えている軸の線（spine）に掛かっていないか。

    目盛の数字・軸の名・題は枠の外に置くものなので比べない（ax.texts に入る文字だけを見る）。
    文字の矩形を pad_pt だけ縮め、軸の線の矩形（線の太さの幅）と交わるものを返す。
    """
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    pad = pad_pt * fig.dpi / 72
    hits = []
    for ax in fig.axes:
        if not ax.get_visible() or not getattr(ax, "axison", True):
            continue
        spines = [(k, sp.get_window_extent(renderer=r)) for k, sp in ax.spines.items() if sp.get_visible()]
        for t in ax.texts:
            if not t.get_text().strip() or not t.get_visible():
                continue
            b = t.get_window_extent(renderer=r)
            x0, x1, y0, y1 = b.x0 + pad, b.x1 - pad, b.y0 + pad, b.y1 - pad
            for k, sb in spines:
                if x0 < sb.x1 and sb.x0 < x1 and y0 < sb.y1 and sb.y0 < y1:
                    name = t.get_text().replace("\n", " ")[:24]
                    hits.append(f"{name!r} × 軸の線（{k}）")
    return sorted(set(hits))


def _segment_hits_box(p, q, x0, y0, x1, y1) -> bool:
    """線分 p–q が矩形 [x0,x1]×[y0,y1] と交わるか（Liang–Barsky の切り取り）。"""
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for pk, qk in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
        if pk == 0:
            if qk < 0:
                return False
            continue
        t = qk / pk
        if pk < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return False
    return True


def _masks_lines(t) -> bool:
    """文字に白い地（bbox の塗り）があり、線の上に描かれるか。そうなら線は文字の下に隠れるので重なりと数えない。"""
    patch = t.get_bbox_patch()
    if patch is None:
        return False
    fc = matplotlib.colors.to_rgba(patch.get_facecolor())
    return fc[3] > 0.99 and min(fc[:3]) > 0.99


def text_line_overlaps(fig, pad_pt: float = 0.3) -> list[str]:
    """枠の中の文字（注釈・札）を、同じ枠の線（規準線・結ぶ線など）が貫いていないか。

    線は破線でも続いた線として比べる（控えめな側に倒す）。記号だけの線（ls なし）は text_marker_overlaps が見る。
    参照の線（規準線・特徴点法の値の線。label を "ref:" で始める）は、文字に白い地があって線より上に描くもの
    （_masks_lines）なら、線が文字の下に隠れるので数えない。
    """
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    pad = pad_pt * fig.dpi / 72
    hits = []

    def drawn_lines(lines):
        return [ln for ln in lines
                if ln.get_visible() and ln.get_linestyle() not in ("None", "none", "", " ") and ln.get_linewidth() > 0]

    # 図に直接置いた線（見出しの区切り線など）は、図の文字と、すべての枠の文字の両方と比べる
    all_texts = list(fig.texts) + [t for ax in fig.axes for t in ax.texts]
    for ln in drawn_lines(fig.lines):
        xy = ln.get_transform().transform(ln.get_xydata())
        for t in all_texts:
            if not t.get_text().strip() or not t.get_visible():
                continue
            b = t.get_window_extent(renderer=r)
            x0, x1, y0, y1 = b.x0 + pad, b.x1 - pad, b.y0 + pad, b.y1 - pad
            if any(_segment_hits_box(xy[i], xy[i + 1], x0, y0, x1, y1) for i in range(len(xy) - 1)):
                hits.append(f"{t.get_text().replace(chr(10), ' ')[:24]!r} × 図の線（{ln.get_label()}）")
    for ax in fig.axes:
        lines = drawn_lines(ax.get_lines())
        for t in ax.texts:
            if not t.get_text().strip() or not t.get_visible():
                continue
            b = t.get_window_extent(renderer=r)
            x0, x1, y0, y1 = b.x0 + pad, b.x1 - pad, b.y0 + pad, b.y1 - pad
            for ln in lines:
                # 白い地の文字が規準線などの参照の線（label が "ref:" で始まる）の上にあるときは、線が隠れるので数えない。
                # 点を結ぶ線は隠すと途切れて見えるので、白い地があっても重なりと数える
                if _masks_lines(t) and t.get_zorder() > ln.get_zorder() and str(ln.get_label()).startswith("ref:"):
                    continue
                xy = ln.get_transform().transform(ln.get_xydata())
                if any(_segment_hits_box(xy[i], xy[i + 1], x0, y0, x1, y1) for i in range(len(xy) - 1)):
                    name = t.get_text().replace("\n", " ")[:24]
                    hits.append(f"{name!r} × 線（{ln.get_label()}）")
    return sorted(set(hits))


# 枠の中の注釈に敷く白い地（参照の線が注釈を貫かないように、線を注釈の下に隠す）
LABEL_BOX = dict(boxstyle="square,pad=0.12", fc="white", ec="none")


def marker_box(ax, x: float, y: float, ms_pt: float, margin_pt: float = 0.6):
    """データ座標 (x, y) に描いた大きさ ms_pt の記号の矩形（画素）。"""
    fig = ax.figure
    px, py = ax.transData.transform((x, y))
    half = (ms_pt / 2 + margin_pt) * fig.dpi / 72
    return matplotlib.transforms.Bbox([[px - half, py - half], [px + half, py + half]])


def data_segment(ax, p, q):
    """データ座標の線分を画素の線分にする。"""
    return tuple(map(tuple, ax.transData.transform([p, q])))


def vline_segment(ax, x: float):
    """枠の高さいっぱいの縦線（axvline）の画素の線分。"""
    px = ax.transData.transform((x, 0))[0]
    return ((px, ax.bbox.y0), (px, ax.bbox.y1))


def hline_segment(ax, y: float):
    """枠の幅いっぱいの横線（axhline）の画素の線分。"""
    py = ax.transData.transform((0, y))[1]
    return ((ax.bbox.x0, py), (ax.bbox.x1, py))


def place_annotation(ax, text: str, xy, candidates, *, hard_boxes=(), hard_segments=(), soft_segments=(),
                     xbounds=None, pad_pt: float = 0.3, **kw):
    """注釈を、候補の位置のうち、ほかの文字・記号・点を結ぶ線に掛からない（hard が 0 の）位置に置く。

    候補は (dx_pt, dy_pt, ha) か (dx_pt, dy_pt, ha, 段) の並び。hard が 0 の候補のうち、段の小さいもの →
    参照の線に掛かる数（soft）の少ないもの → 先に並べたもの、の順に採る（段は「記号から離す量」のような、
    soft より優先する好みに使う。記号のすぐ横で線に掛かる位置を、線を避けて記号から離れた位置より先に採るため）。
    hard_boxes は画素の矩形、hard_segments・soft_segments は画素の線分、xbounds は (左, 右) の画素。
    戻り値は (注釈, 画素の矩形, hard の数)。hard が 0 にならなければ hard の最も少ない位置に置く
    （自己検査が重なりとして拾う）。
    """
    fig = ax.figure
    r = fig.canvas.get_renderer()
    pad = pad_pt * fig.dpi / 72
    scored = []
    for k, c in enumerate(candidates):
        dx, dy, ha = c[:3]
        tier = c[3] if len(c) > 3 else 0
        ann = ax.annotate(text, xy, xytext=(dx, dy), textcoords="offset points", ha=ha, **kw)
        b = ann.get_window_extent(renderer=r)
        ann.remove()
        x0, x1, y0, y1 = b.x0 + pad, b.x1 - pad, b.y0 + pad, b.y1 - pad
        hard = sum(1 for hb in hard_boxes if x0 < hb.x1 and hb.x0 < x1 and y0 < hb.y1 and hb.y0 < y1)
        hard += sum(1 for p, q in hard_segments if _segment_hits_box(p, q, x0, y0, x1, y1))
        if xbounds is not None and (b.x0 < xbounds[0] or b.x1 > xbounds[1]):
            hard += 1
        soft = sum(1 for p, q in soft_segments if _segment_hits_box(p, q, x0, y0, x1, y1))
        scored.append((hard, tier, soft, k))
        if hard == 0 and soft == 0:            # 段は並びの順に増える前提なので、これより良い候補は無い
            break
    hard, _tier, _soft, k = min(scored)
    dx, dy, ha = candidates[k][:3]
    ann = ax.annotate(text, xy, xytext=(dx, dy), textcoords="offset points", ha=ha, **kw)
    return ann, ann.get_window_extent(renderer=r), hard


# 段の注釈（CLAUDE.md §3: 段を出すときは毎回その場に 1 行）
STAGE_NOTE = {
    "ja": "A 段＝その手法が採用した被験者だけ、B 段＝比べる全手法が採用した共通例、C 段＝採否を無視した全員",
    "en": "Tier A, subjects accepted by the method itself; tier B, subjects accepted by every compared method; tier C, all subjects regardless of acceptance",
}

# 図に共通する語（和・英）
L = {
    "ja": {
        "rho": "年齢層内 Spearman |ρ| の中央値",
        "dt_pwv": "ΔT × 大動脈PWV",
        "ri_pvr": "RI × 末梢血管抵抗",
        "criterion": "規準 0.30",
        "landmark": "特徴点法（同梱）",
        "noise": "雑音（振幅に対する標準偏差の比）",
        "pass": "通過率",
        "posthoc": "探索・事後（判定には用いない）",
    },
    "en": {
        "rho": "Median within-age-stratum Spearman |ρ|",
        "dt_pwv": "ΔT × aortic PWV",
        "ri_pvr": "RI × peripheral vascular resistance",
        "criterion": "criterion 0.30",
        "landmark": "Fiducial-point (database-supplied)",
        "noise": "Noise (SD as a fraction of pulse amplitude)",
        "pass": "Pass rate",
        "posthoc": "Exploratory, post hoc (not used for the decision)",
    },
}

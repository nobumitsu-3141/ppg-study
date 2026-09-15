#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【図・事後】論文2: 切痕の無い型3 では、凍結版の第2成分は拡張期側の特徴点に載らない。

何を描くか
----------
48番（`48_pwdb_by_waveform_type.py`）の節4 は、凍結版 2 カーネル分解の ΔT が特徴点法
（Charlton 同梱）の ΔT より **型1 で中央値 +36.9 ms・型3 で +98.5 ms** 大きいことを数で
示した（lab_log 2026-09-14 追記137。Mac 1・4,374 名）。この台本は同じ差を実波形で描く。
型1（重複切痕と拡張期ピークが極値として残る）の被験者と、型3（極値は無く、下降脚の
変曲点だけが残る）の被験者を左右に並べ、それぞれの拍に

    計測した拍・第1成分・第2成分・2 成分の和・拡張期側の特徴点・第2成分のピーク

を重ねて、**第2成分のピークが拡張期側の特徴点からどれだけ後ろに置かれているか**を示す。
型3 では第2成分のピークは変曲点に載らず、その約 100 ms 後の拡張期の下降の上に来る。

何を描かないか
--------------
**判定は付けない。**26番の事前規準による判定も、48番の事後・記述という位置づけも動かさない。
図に出る 2 名はその年齢層の代表であって、集団の値ではない（集団の値は 48番が出す）。

定義
----
  型                  `pda2.find_landmarks` が拍ごとに付ける区分（48番の `klass_own` と同じ）。
                      1 明瞭な重複切痕と拡張期ピーク（極値）／3 極値は無いが下降の緩む変曲点／
                      4 変曲点が見つからない／5 収縮期ピークが拍の末尾（波形が不正）
  拡張期側の特徴点     型1 では拡張期ピーク、型3 では下降脚の変曲点（`find_landmarks` の dia_t）
  第2成分のピーク      凍結版 2 カーネル分解（`src/pda.py` の `fit_beat`）の第2成分の最大点
  オフセット           第2成分のピーク − 拡張期側の特徴点 [ms]。図の矢印が結ぶ 2 点の差
  正規化した振幅       拍内の最小を 0、最大を 1 とした値（凍結版が当てはめに使う尺度と同じ）

処理は 26番と同じにそろえる。特徴点は `pda2.preprocess`（18 Hz 低域通過・足から足の基線・
振幅正規化）を通した波形から取り、凍結版の当てはめは前処理をしない生の拍に当てる。
**図に描くのは凍結版が見ている拍（前処理をしない拍を正規化したもの）で、特徴点の印は
その拍の上に置く。**印の時刻は `find_landmarks` が返す値そのもの、印の高さは描いた拍から
読んだ値である（前処理の有無で高さが少し違うため）。
拍と標本化周波数は 20番の `load_pwdb`・`beat_of` をそのまま使う（改変しない）。

被験者の選び方
--------------
`--age` の年齢層（PWDB は 25・35・45・55・65・75 歳）の全員に前処理と特徴点の検出を当てて
型を付け、型1 の中で大動脈PWV がその型の中央値に最も近い 1 名と、型3 の中で同じく 1 名を
選ぶ。乱数は使わない（同点は subj_no の小さいほう）。凍結版の当てはめは選んだ 2 名だけに
当てる。`--subjects A,B` で明示もできる（この場合は指定の順に左右へ置く）。

前提
----
PWDB の配布物（Zenodo doi:10.5281/zenodo.3275625）が要る。**Mac 1 にしかない。**
`--selftest` は合成脈波だけで走るので、配布物もネットワークも要らない。

使い方
------
    python3 scripts/49_pwdb_type3_figure.py --selftest
    python3 scripts/49_pwdb_type3_figure.py --age 45
    python3 scripts/49_pwdb_type3_figure.py --subjects 3,4 --out analysis/figs/49_pwdb_type3_mechanism.png

出力は `--out` の PNG と、同じ名前の PDF。`analysis/figs/` は git に入っていない。
終了コード 0 = 図を書き出した、2 = PWDB のファイルが無い・選べる被験者がいない。
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import logging
import sys
import tempfile
import unicodedata
import warnings
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
from matplotlib.lines import Line2D      # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import pda2                                         # noqa: E402
from src.pda import fit_beat, component_peak, skew_gaussian  # noqa: E402

DATA = ROOT / "data"
FIGS = ROOT / "figs"
DEFAULT_OUT = FIGS / "49_pwdb_type3_mechanism.png"
FONT_PATH = Path.home() / ".fonts" / "NotoSansJP[wght].ttf"

AGES = (25, 35, 45, 55, 65, 75)     # PWDB の年齢層
DEFAULT_AGE = 45
NEAR_MS = 40.0                      # 自己検査: 型1 で第2成分のピークが特徴点に載る距離

# 色は Okabe–Ito 系（07番の図と同じ系統）。文字は墨か灰で置き、線の色で塗らない
INK = "#141413"          # 計測した拍・本文
C_COMP1 = "#0072B2"      # 第1成分
C_COMP2 = "#D55E00"      # 第2成分
C_SUM = "#6E6E6E"        # 2 成分の和（参照）
C_LM = "#009E73"         # 特徴点
MUTED = "#6E6E6E"
FAINT = "#C8C8C8"

# 型の説明は 48番の KLASS_LABEL と同じ文言にそろえる
KLASS_LABEL = {
    1: "型1 明瞭な重複切痕と拡張期ピーク（極値）",
    3: "型3 極値は無いが下降の緩む変曲点",
    4: "型4 変曲点が見つからない",
    5: "型5 収縮期ピークが拍の末尾（波形が不正）",
}
DIA_NAME = {1: "拡張期ピーク", 3: "変曲点"}


def _load(stem: str, name: str):
    """数字始まりの台本を名前で読み込む（import 文では書けない）。45番・48番と同じ手口。"""
    p = Path(__file__).resolve().parent / stem
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# 読み込みと拍の復元は 20番のものをそのまま使う（自前で書き直さない。26番・48番と同じ）
M = _load("20_pwdb_validity.py", "m20")


# ---------------------------------------------------------------- 見た目
def setup_font(path=FONT_PATH):
    """日本語のフォントを登録する。無ければ既定のまま（豆腐になっても落ちない）。"""
    from matplotlib import font_manager
    # 可変フォントは重みの既定が 100 として登録されるので、matplotlib が既定の重み（400）を
    # 探して見つからないという通知を毎回出す。図の見た目は変わらないのでこの通知だけ止める。
    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
    fallback = list(plt.rcParamsDefault["font.sans-serif"])[:2]
    p = Path(path)
    if not p.exists():
        plt.rcParams["font.family"] = ["sans-serif"]
        return None
    try:
        font_manager.fontManager.addfont(str(p))
        name = str(font_manager.FontProperties(fname=str(p)).get_name())
    except Exception:                      # noqa: BLE001
        plt.rcParams["font.family"] = ["sans-serif"]
        return None
    plt.rcParams["font.family"] = [name] + fallback
    return name


def style() -> None:
    plt.rcParams.update({
        "figure.dpi": 110,
        "savefig.bbox": "tight",
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8.5,
        "axes.edgecolor": MUTED,
        "axes.linewidth": 0.6,
        "axes.labelcolor": INK,
        "axes.titlecolor": INK,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "legend.frameon": False,
        "legend.fontsize": 7.5,
        "axes.unicode_minus": False,     # 負号は ASCII で出す（どのフォントにもある）
    })


# ---------------------------------------------------------------- 1 拍の計算
def analyse_beat(t, y, fs: float):
    """1 拍に凍結版 2 カーネル分解と特徴点の検出を当てる。図も印字もこの返り値だけを見る。

    特徴点は `pda2.preprocess` を通した波形から、凍結版の当てはめは生の拍から取る
    （26番 `indices_for_subject` と同じ組み合わせ。ここを変えると 48番の値と比べられない）。
    """
    t = np.asarray(t, float)
    y = np.asarray(y, float)
    yz, _amp = pda2.preprocess(t, y, fs)
    if yz is None:
        return None
    lm = pda2.find_landmarks(t, yz)
    fit = fit_beat(t, y)
    c1, c2 = fit["components"]
    p1 = (c1["a"], c1["mu"], c1["sigma"], c1["alpha"])
    p2 = (c2["a"], c2["mu"], c2["sigma"], c2["alpha"])
    tp1, h1 = component_peak(p1, float(t[0]), float(t[-1]))
    tp2, h2 = component_peak(p2, float(t[0]), float(t[-1]))
    y0 = y - float(np.min(y))
    ys = y0 / float(np.max(y0))          # 凍結版が当てはめに使う尺度と同じ正規化
    dia_t = float(lm["dia_t"])
    sys_v = float(lm["sys_v"])
    chk = fit["checks"]
    return {
        "t": t, "ys": ys,
        "y1": skew_gaussian(t, *p1), "y2": skew_gaussian(t, *p2),
        "tp1": tp1, "tp2": tp2, "h1": h1, "h2": h2,
        "dt_v1_ms": (tp2 - tp1) * 1000.0,
        "ri_v1": h2 / max(h1, 1e-12),
        "ok": bool(fit.get("ok", False)),
        "nrmse": float(fit.get("nrmse", np.nan)),
        "checks": chk,
        "klass": int(lm["klass"]),
        "sys_t": float(lm["sys_t"]), "notch_t": float(lm["notch_t"]), "dia_t": dia_t,
        "sys_v": sys_v, "dia_v": float(lm["dia_v"]),
        "dt_own_ms": (dia_t - float(lm["sys_t"])) * 1000.0,
        "ri_own": float(lm["dia_v"]) / sys_v if sys_v > 0 else np.nan,
        "offset_ms": (tp2 - dia_t) * 1000.0,
    }


# ---------------------------------------------------------------- 作図
def _legend_handles():
    return [
        Line2D([], [], color=INK, lw=2.0, label="計測した拍"),
        Line2D([], [], color=C_COMP1, lw=1.4, label="第1成分"),
        Line2D([], [], color=C_COMP2, lw=1.4, label="第2成分"),
        Line2D([], [], color=C_SUM, lw=1.1, ls="--", label="2 成分の和（参照）"),
        Line2D([], [], color=C_LM, marker="^", ls="none", ms=8.0,
               label="特徴点 自前（拡張期ピーク／変曲点）"),
        Line2D([], [], color=C_LM, marker="o", ls="none", ms=9.0, mec="white", mew=0.8,
               label="特徴点 同梱（Digital_PPGdia_T）"),
        Line2D([], [], color=C_COMP2, marker="o", ls="none", ms=9.0, mec="white", mew=0.8,
               label="第2成分のピーク"),
    ]


LABEL_FS = 8.0            # 直接ラベルの文字の大きさ [pt]
LABEL_H = 0.085           # 直接ラベルの高さの目安（y の単位。軸の高さから見積もった）
LABEL_W_PER_CHAR = 0.028  # 直接ラベルの 1 文字の横幅の目安（軸の幅に対する割合）


def _busy(cx: float, cy: float, w: float, h: float, curves: list) -> bool:
    """(cx, cy) を中心とする幅 w・高さ h の枠に、描いた線が入っているか。"""
    for xs, ys in curves:
        m = (xs >= cx - 0.5 * w) & (xs <= cx + 0.5 * w)
        if bool(np.any((ys[m] >= cy - 0.5 * h) & (ys[m] <= cy + 0.5 * h))):
            return True
    return False


def _label(ax, text: str, x: float, y: float, curves: list, dur_ms: float,
           sides: list, color: str = INK) -> None:
    """線に直接ラベルを付ける。候補の向きのうち、ほかの線と重ならない最初のものに置く。

    実データの拍は形がまちまちで、決め打ちの位置では線の上に字が乗ってしまう。
    置き場所だけを自動で選び、文字の内容と色は呼び出し側が決める。
    """
    w = LABEL_W_PER_CHAR * len(text) * dur_ms
    for sx, sy in sides:
        cx = float(np.clip(x + sx * (0.5 * w + 0.012 * dur_ms), 0.5 * w, dur_ms - 0.5 * w))
        cy = float(np.clip(y + sy * (0.5 * LABEL_H + 0.02), -0.06, 0.95))
        if not _busy(cx, cy, w, LABEL_H, curves):
            ax.text(cx, cy, text, ha="center", va="center", fontsize=LABEL_FS,
                    color=color, zorder=9)
            return
    # どの向きも線に当たる拍では、空いている場所を探して引き出し線でつなぐ
    best = None
    for gx in np.linspace(0.5 * w, dur_ms - 0.5 * w, 24):
        for gy in np.linspace(-0.04, 0.95, 18):
            if _busy(gx, gy, w, LABEL_H, curves):
                continue
            d = ((gx - x) / dur_ms) ** 2 + (gy - y) ** 2
            if best is None or d < best[0]:
                best = (d, float(gx), float(gy))
    if best is None:
        ax.text(x, y, text, ha="center", va="center", fontsize=LABEL_FS,
                color=color, zorder=9)
        return
    ax.annotate(text, xy=(x, y), xytext=(best[1], best[2]), ha="center", va="center",
                fontsize=LABEL_FS, color=color, zorder=9,
                arrowprops=dict(arrowstyle="-", color=FAINT, lw=0.6, shrinkA=1.0, shrinkB=3.0))


def draw_panel(ax, res: dict, meta: dict) -> None:
    """1 名分のパネル。実データでも合成脈波でも同じこの関数を通す。"""
    t = res["t"]
    t_ms = t * 1000.0
    dur_ms = float(t_ms[-1])
    ax.plot(t_ms, res["ys"], color=INK, lw=2.0, zorder=5)
    ax.plot(t_ms, res["y1"], color=C_COMP1, lw=1.4, zorder=4)
    ax.plot(t_ms, res["y2"], color=C_COMP2, lw=1.4, zorder=4)
    ax.plot(t_ms, res["y1"] + res["y2"], color=C_SUM, lw=1.1, ls="--", zorder=3)

    def y_at(tt: float) -> float:
        return float(np.interp(tt, t, res["ys"]))

    # 直接ラベル（文字は墨か灰。線の色では塗らない）
    ysum = res["y1"] + res["y2"]
    curves = [(t_ms, res["ys"]), (t_ms, res["y1"]), (t_ms, res["y2"]), (t_ms, ysum)]
    i_half = int(np.argmax(res["ys"] >= 0.5))
    _label(ax, "計測した拍", t_ms[i_half], res["ys"][i_half], curves, dur_ms,
           [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0)])
    _label(ax, "第1成分", res["tp1"] * 1000.0, res["h1"], curves, dur_ms,
           [(1, 0), (1, 1), (0, 1), (1, -1), (-1, 1)])
    _label(ax, "第2成分", res["tp2"] * 1000.0, res["h2"], curves, dur_ms,
           [(0, -1), (1, -1), (0, -2), (0, -3), (1, 0), (1, 1), (0, 1)])
    x_sum = 0.84 * dur_ms
    _label(ax, "2 成分の和", x_sum, float(np.interp(x_sum / 1000.0, t, ysum)), curves, dur_ms,
           [(0, -1), (0, 1), (-1, -1), (-1, 1)], color=MUTED)

    # 特徴点の印
    # 3 つの印はほとんど同じ位置に来ることがある。大きい順に下から重ねて、
    # 重なっても内側の印が見えるようにする（同梱 ● → 第2成分 ● → 自前 ▲）
    dia_lm_ms = float(meta.get("dia_lm_ms", np.nan))
    if np.isfinite(dia_lm_ms):
        ax.plot([dia_lm_ms], [y_at(dia_lm_ms / 1000.0)], marker="o", ms=11.0, color=C_LM,
                mec="white", mew=0.8, ls="none", zorder=6)
    ax.plot([res["tp2"] * 1000.0], [res["h2"]], marker="o", ms=9.0, color=C_COMP2,
            mec="white", mew=0.8, ls="none", zorder=7)
    dia_t = res["dia_t"]
    if np.isfinite(dia_t):
        ax.plot([dia_t * 1000.0], [y_at(dia_t)], marker="^", ms=8.0, color=C_LM,
                ls="none", zorder=8)

    # 矢印で 2 点を結ぶ（オフセットの注記）
    y_arrow, name = 1.06, DIA_NAME.get(res["klass"], "拡張期側の特徴点")
    if np.isfinite(res["offset_ms"]) and np.isfinite(dia_t):
        x0, x1 = dia_t * 1000.0, res["tp2"] * 1000.0
        tops = (y_at(dia_t), res["h2"])
        for x, y_top in ((x0, tops[0]), (x1, tops[1])):
            ax.plot([x, x], [y_top, y_arrow - 0.015], color=FAINT, lw=0.7, ls=":", zorder=2)
        if abs(x1 - x0) >= 0.02 * dur_ms:
            ax.annotate("", xy=(x1, y_arrow), xytext=(x0, y_arrow), zorder=6,
                        arrowprops=dict(arrowstyle="<->", color=INK, lw=0.9,
                                        shrinkA=0.0, shrinkB=0.0))
        else:
            # 2 点がほとんど重なると両矢印は矢の頭だけになる。注記から 1 本引き下ろす
            ax.annotate("", xy=(0.5 * (x0 + x1), max(tops) + 0.03), zorder=6,
                        xytext=(0.5 * (x0 + x1), y_arrow),
                        arrowprops=dict(arrowstyle="->", color=INK, lw=0.9,
                                        shrinkA=0.0, shrinkB=0.0))
        txt = f"第2成分のピーク − {name} ＝ {res['offset_ms']:+.1f} ms"
        frac = float(np.clip(0.5 * (x0 + x1) / dur_ms, 0.28, 0.72))
    else:
        txt = f"{name}が取れないので差は出せない"
        frac = 0.5
    ax.text(frac, y_arrow + 0.035, txt, transform=ax.get_yaxis_transform(),
            ha="center", va="bottom", fontsize=8.5, color=INK)

    info = (f"subj_no {meta.get('subj', '—')}・{meta.get('age_s', '—')}・"
            f"型{res['klass']}・大動脈PWV {meta.get('pwv_s', '—')}")
    ax.text(0.99, 1.30, info, transform=ax.get_yaxis_transform(), ha="right", va="bottom",
            fontsize=8, color=MUTED)
    ax.set_title(KLASS_LABEL.get(res["klass"], f"型{res['klass']}"), pad=22)
    ax.set_xlabel("拍の開始からの時間 [ms]")
    ax.set_xlim(0.0, dur_ms)
    ax.set_ylim(-0.10, 1.42)


SOURCE_LINE = ("PWDB（Charlton 2019）・凍結版 2 カーネル分解（src/pda.py）・"
               "特徴点は pda2.find_landmarks（同梱の dia は pwdb_pw_indices.csv）")


def draw_figure(panels: list, out_path: Path, dpi: int = 300) -> list:
    """2 枚組の図を PNG と PDF に書き出す。実データでも自己検査でも同じこの関数を通す。"""
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.9), sharey=True)
    for ax, (res, meta) in zip(np.atleast_1d(axes), panels):
        draw_panel(ax, res, meta)
    axes[0].set_ylabel("正規化した振幅（拍内の最大を 1 とする）")
    fig.subplots_adjust(left=0.065, right=0.99, top=0.86, bottom=0.26, wspace=0.08)
    fig.legend(handles=_legend_handles(), loc="lower center", bbox_to_anchor=(0.5, 0.075),
               ncol=4, frameon=False)
    fig.text(0.5, 0.015, SOURCE_LINE, ha="center", va="bottom", fontsize=7.5, color=MUTED)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    made = []
    for ext in (".png", ".pdf"):
        p = out_path.with_suffix(ext)
        fig.savefig(p, dpi=dpi)
        made.append(p)
    plt.close(fig)
    return made


# ---------------------------------------------------------------- 印字
def _pad(s: str, w: int, right: bool = False) -> str:
    """表示幅で揃える（日本語は 2 文字分。f 文字列の桁指定は文字数なのでずれる）。48番と同じ。"""
    used = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in str(s))
    fill = " " * max(0, w - used)
    return (fill + str(s)) if right else (str(s) + fill)


def _f(v: float, w: int = 9, prec: int = 1, sign: bool = False) -> str:
    """数値の欄（48番と同じ）。有限でなければ「—」を右詰めで出す。"""
    if not np.isfinite(v):
        return _pad("—", w, right=True)
    return f"{v:>+{w}.{prec}f}" if sign else f"{v:>{w}.{prec}f}"


def describe(res: dict, meta: dict) -> dict:
    """図に出した 1 名の数値を印字し、同じ値を返す（自己検査が有限性を確かめる）。"""
    name = DIA_NAME.get(res["klass"], "拡張期側の特徴点")
    chk = res["checks"]
    vals = {
        "dt_own_ms": res["dt_own_ms"], "dt_lm_ms": float(meta.get("dt_lm_ms", np.nan)),
        "dt_v1_ms": res["dt_v1_ms"], "offset_ms": res["offset_ms"],
        "ri_own": res["ri_own"], "digital_ri": float(meta.get("digital_ri", np.nan)),
        "ri_v1": res["ri_v1"],
    }
    print(f"\n  subj_no {meta.get('subj', '—')}・{meta.get('age_s', '—')}・"
          f"{KLASS_LABEL.get(res['klass'], '型' + str(res['klass']))}・"
          f"大動脈PWV {meta.get('pwv_s', '—')}")
    for lab, v, unit, prec, sign in (
            ("自前の ΔT（dia − sys）", vals["dt_own_ms"], " ms", 1, False),
            ("同梱の ΔT（Digital_PPGdia_T − Digital_PPGsys_T）", vals["dt_lm_ms"], " ms", 1, False),
            ("凍結版 ΔT（第2成分 − 第1成分のピーク）", vals["dt_v1_ms"], " ms", 1, False),
            (f"第2成分のピーク − {name}（図の矢印）", vals["offset_ms"], " ms", 1, True),
            ("自前の RI（dia_v / sys_v）", vals["ri_own"], "", 3, False),
            ("同梱の RI（Digital_RI）", vals["digital_ri"], "", 3, False),
            ("凍結版 RI（第2/第1成分のピーク高さ比）", vals["ri_v1"], "", 3, False)):
        print("    " + _pad(lab, 48) + _f(v, 9, prec, sign) + unit)
    print(f"    収束検算 {'合格' if res['ok'] else '不合格'}"
          f"（境界張り付き {'あり' if chk['boundary_stick'] else 'なし'}"
          f"・振幅ゼロ {'あり' if chk['amp_zero'] else 'なし'}"
          f"・再現性 {'あり' if chk['reproducible'] else 'なし'}"
          f"・nrmse {res['nrmse']:.4f}）")
    return vals


# ---------------------------------------------------------------- 実データ
def resolve_pwdb(arg: str) -> Path:
    """配布物のある場所を決める（既定は data/pwdb、無ければ ~/pwdb）。"""
    if arg:
        return Path(arg).expanduser()
    cands = [DATA / "pwdb", Path.home() / "pwdb"]
    for c in cands:
        if c.exists() and M._find_one(c, "*digital*ppg*.csv") is not None:
            return c
    for c in cands:
        if c.exists():
            return c
    return cands[0]


def resolve_out(s: str) -> Path:
    p = Path(s).expanduser()
    if p.is_absolute():
        return p
    for base in (Path.cwd(), ROOT.parent, ROOT):
        q = base / p
        if q.parent.exists():
            return q
    return Path.cwd() / p


def load_indices(root: Path):
    """同梱の特徴点（pwdb_pw_indices.csv）。単位の換算は 23番の `_to_ms` に任せる。"""
    q = M._find_one(Path(root).expanduser(), "*pw*indice*.csv")
    if q is None:
        return None
    m23 = _load("23_pwdb_landmarks.py", "m23")
    idx = M._read_named(q, ("subj_no",))
    m23._to_ms(idx, ["digital_ppgsys_t", "digital_ppgdia_t", "digital_ppgdic_t"])
    print(f"  同梱の特徴点: {q}")
    return idx.set_index("subj_no")


def _cell(idx, subj: int, col: str) -> float:
    if idx is None or col not in idx.columns or subj not in idx.index:
        return float("nan")
    try:
        return float(idx.loc[subj, col])
    except (TypeError, ValueError):
        return float("nan")


def klass_table(hae, ppg, age, only=None) -> dict:
    """年齢層の全員に前処理と特徴点の検出を当てて型を付ける（凍結版は当てない）。

    age は年齢層（None なら年齢で絞らない）、only は subj_no の集合（被験者を明示した
    ときだけ使う。4,374 名すべてに当てるのは無駄なので、指定の 2 名だけを見る）。
    """
    hr_by = dict(zip(hae["subj_no"].astype(int), hae["HR"].astype(float)))
    age_by = dict(zip(hae["subj_no"].astype(int), hae["age"].astype(float)))
    pwv_by = dict(zip(hae["subj_no"].astype(int), hae["PWV_a"].astype(float)))
    out = {}
    for i in range(len(ppg)):
        subj = int(ppg.iloc[i, 0])
        if only is not None and subj not in only:
            continue
        if age is not None and age_by.get(subj) != float(age):
            continue
        y, fs = M.beat_of(ppg.iloc[i].to_numpy(float), hr_by.get(subj, np.nan))
        if y is None:
            continue
        t = np.arange(y.size) / fs
        yz, _amp = pda2.preprocess(t, y, fs)
        if yz is None:
            continue
        lm = pda2.find_landmarks(t, yz)
        out[subj] = {"klass": int(lm["klass"]), "pwv": float(pwv_by.get(subj, np.nan)),
                     "age": float(age_by.get(subj, np.nan)), "irow": i}
    return out


def pick_subject(rows: dict, klass: int):
    """その型の中で大動脈PWV が中央値に最も近い 1 名（同点は subj_no の小さいほう）。"""
    cand = [(s, r) for s, r in rows.items() if r["klass"] == klass and np.isfinite(r["pwv"])]
    if not cand:
        return None, float("nan")
    med = float(np.median([r["pwv"] for _s, r in cand]))
    subj = min(cand, key=lambda sr: (abs(sr[1]["pwv"] - med), sr[0]))[0]
    return subj, med


def panel_for(subj: int, info: dict, ppg, hae, idx) -> tuple:
    """1 名分の（計算結果, 図と印字に要る付帯情報）を作る。"""
    hr_by = dict(zip(hae["subj_no"].astype(int), hae["HR"].astype(float)))
    row = ppg.iloc[info["irow"]].to_numpy(float)
    y, fs = M.beat_of(row, hr_by.get(subj, np.nan))
    if y is None:
        return None, None
    t = np.arange(y.size) / fs
    res = analyse_beat(t, y, fs)
    if res is None:
        return None, None
    sys_lm = _cell(idx, subj, "digital_ppgsys_t")
    dia_lm = _cell(idx, subj, "digital_ppgdia_t")
    meta = {"subj": subj, "age_s": f"{info['age']:.0f} 歳", "pwv_s": f"{info['pwv']:.2f} m/s",
            "dia_lm_ms": dia_lm, "dt_lm_ms": dia_lm - sys_lm,
            "digital_ri": _cell(idx, subj, "digital_ri")}
    return res, meta


def run_real(args) -> int:
    root = resolve_pwdb(args.pwdb)
    print("=" * 96)
    print("49番 図: 凍結版 2 カーネル分解の第2成分は、切痕の無い型3 で拡張期側の特徴点に載らない")
    print("=" * 96)
    try:
        hae, _cfg, ppg, _extras = M.load_pwdb(root)
    except Exception as e:                  # noqa: BLE001
        # 20番は見つからないときに FileNotFoundError・列が違うときに KeyError を出す。
        # どちらも「この機械では描けない」なので、理由を添えて同じ終わり方にする
        print(f"\nPWDB のファイルが無い（{root}）。")
        print(f"  {e}")
        print("  Zenodo（doi:10.5281/zenodo.3275625）の CSV 版を置いた場所を --pwdb に渡す。")
        print("  合成脈波だけで動かすなら --selftest。")
        return 2
    idx = load_indices(root)
    if idx is None:
        print("  同梱の特徴点は無い（pwdb_pw_indices.csv が見つからない）。同梱の印は描かない。")

    if args.subjects:
        want = [int(s) for s in str(args.subjects).replace("，", ",").split(",") if s.strip()]
        if len(want) != 2:
            print(f"\n--subjects は 2 名で指定する（左右 2 枚組の図なので）。受け取った値 {want}")
            return 2
        rows = klass_table(hae, ppg, None, only=set(want))
        miss = [s for s in want if s not in rows]
        if miss:
            print(f"\n指定した被験者の拍が取れない: {miss}")
            return 2
        chosen = [(s, rows[s], None) for s in want]
        print(f"\n  指定された被験者 {want}（指定の順に左右へ置く）")
    else:
        rows = klass_table(hae, ppg, args.age)
        if not rows:
            print(f"\n{args.age} 歳の年齢層に拍の取れる被験者がいない"
                  f"（PWDB の年齢層は {'・'.join(str(a) for a in AGES)} 歳）。")
            return 2
        cnt = {}
        for r in rows.values():
            cnt[r["klass"]] = cnt.get(r["klass"], 0) + 1
        print(f"\n  {args.age} 歳の年齢層 {len(rows)} 名・型ごとの人数 "
              + "・".join(f"型{k} {cnt[k]} 名" for k in sorted(cnt)))
        chosen = []
        for k in (1, 3):
            subj, med = pick_subject(rows, k)
            if subj is None:
                print(f"\n  型{k} の被験者がこの年齢層にいない。")
                return 2
            print(f"  型{k}: subj_no {subj}（大動脈PWV {rows[subj]['pwv']:.2f} m/s・"
                  f"型{k} の中央値 {med:.2f} m/s に最も近い・{cnt.get(k, 0)} 名から）")
            chosen.append((subj, rows[subj], med))

    panels = []
    for subj, info, _med in chosen:
        res, meta = panel_for(subj, info, ppg, hae, idx)
        if res is None:
            print(f"\n  subj_no {subj} の拍を復元できない。")
            return 2
        panels.append((res, meta))

    print("\n" + "-" * 96)
    print("図に出した 2 名の数値")
    print("-" * 96)
    for res, meta in panels:
        describe(res, meta)

    setup_font()
    style()
    made = draw_figure(panels, resolve_out(args.out), dpi=args.dpi)
    print("\n  " + "\n  ".join(f"→ {p}" for p in made))
    print(f"\n出典: analysis/scripts/49_pwdb_type3_figure.py / subj_no "
          + "・".join(str(m["subj"]) for _r, m in panels))
    return 0


# ---------------------------------------------------------------- 自己検査
def selftest() -> int:
    n_fail = 0

    def rep(name, cond, detail=""):
        nonlocal n_fail
        cond = bool(cond)
        if not cond:
            n_fail += 1
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))

    print("49番 自己検査（合成脈波だけで走る。PWDB もネットワークも要らない）")
    m25 = _load("25_pda2_validate.py", "m25")
    panels = []
    for tag, (t, y, _truth) in (("1", m25.make_beat(notch=True)),
                                ("3", m25.make_beat(notch=False, dt_true=0.11))):
        meta = {"subj": f"合成{tag}", "age_s": "合成脈波", "pwv_s": "—",
                "dia_lm_ms": np.nan, "dt_lm_ms": np.nan, "digital_ri": np.nan}
        panels.append((analyse_beat(t, y, m25.FS), meta))
    res1, res3 = panels[0][0], panels[1][0]
    rep("合成脈波の型が 1 と 3 になる（25番の make_beat をそのまま借りる）",
        res1["klass"] == 1 and res3["klass"] == 3,
        f"切痕あり 型{res1['klass']}・切痕なし 型{res3['klass']}")

    style()
    fam = setup_font()
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "49_selftest.png"
        made = draw_figure(panels, out, dpi=110)
        sizes = [p.stat().st_size if p.exists() else 0 for p in made]
        rep("(1) PNG と PDF ができる",
            len(made) == 2 and all(s > 5000 for s in sizes),
            f"フォント {fam or '既定'}・{[p.suffix + ' ' + str(s) for p, s in zip(made, sizes)]}")

        print("\n  印字（実データと同じ describe を通す）")
        v1 = describe(*panels[0])
        v3 = describe(*panels[1])
        keys = ("dt_own_ms", "dt_v1_ms", "offset_ms", "ri_own", "ri_v1")
        bad = [k for k in keys if not (np.isfinite(v1[k]) and np.isfinite(v3[k]))]
        print()
        rep("(2) 印字される数値（ΔT・オフセット・RI）が有限", not bad,
            f"有限でない列 {bad}" if bad else
            f"ΔT 自前 {v1['dt_own_ms']:.1f}／{v3['dt_own_ms']:.1f} ms・"
            f"凍結版 {v1['dt_v1_ms']:.1f}／{v3['dt_v1_ms']:.1f} ms")

        rep(f"(3) 型1 の拍で第2成分のピークが拡張期ピークから {NEAR_MS:.0f} ms 以内",
            abs(res1["offset_ms"]) <= NEAR_MS, f"{res1['offset_ms']:+.1f} ms")
        rep("（参考）型3 の拍では第2成分のピークが変曲点より後ろに来る",
            res3["offset_ms"] > res1["offset_ms"],
            f"型3 {res3['offset_ms']:+.1f} ms・型1 {res1['offset_ms']:+.1f} ms")

        # (4) フォントが無い機械。登録に失敗しても同じ関数で描けることを確かめる。
        # 日本語の字が無いという通知は、この検査では起きて当たり前なので黙らせる
        fam_none = setup_font(Path(td) / "no_such_font.ttf")
        out2 = Path(td) / "49_selftest_nofont.png"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            made2 = draw_figure(panels, out2, dpi=110)
        rep("(4) フォントが無くても落ちない（豆腐になるだけ）",
            fam_none is None and len(made2) == 2
            and all(p.exists() and p.stat().st_size > 5000 for p in made2),
            f"登録 {fam_none}・{[p.name for p in made2]}")

    # (5)(6) PWDB の配布物はこの機械に無いので、読み込みから作図までの道筋を模擬データで
    # 一度通しておく（23番の `_make_mock`。数値は模擬なので読まない）
    m23 = _load("23_pwdb_landmarks.py", "m23")
    with tempfile.TemporaryDirectory() as td:
        root = m23._make_mock(Path(td) / "exported_data", n=36)
        out3 = Path(td) / "mock.png"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_real(argparse.Namespace(pwdb=str(root), age=45, subjects="9,10",
                                               out=str(out3), dpi=110))
        made3 = sorted(p.name for p in Path(td).glob("mock.*"))
        rep("(5) 模擬 PWDB で実データの道筋（読み込み・型・印字・作図）が通る",
            code == 0 and made3 == ["mock.pdf", "mock.png"]
            and "同梱の特徴点:" in buf.getvalue(),
            f"終了コード {code}・{made3}")
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            code2 = run_real(argparse.Namespace(pwdb=str(root), age=45, subjects="",
                                                out=str(Path(td) / "mock2.png"), dpi=110))
        rep("(6) 型3 の被験者がいない年齢層では図を描かずに終了コード 2",
            code2 == 2 and "型1: subj_no" in buf2.getvalue()
            and not (Path(td) / "mock2.png").exists(),
            f"終了コード {code2}")

    print("\n" + ("自己検証: 通過" if n_fail == 0 else f"自己検証: 失敗 {n_fail} 件"))
    return 0 if n_fail == 0 else 1


# ---------------------------------------------------------------- 入口
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pwdb", type=str, default="",
                    help="PWDB の配布物を置いたフォルダ（既定 data/pwdb、無ければ ~/pwdb）")
    ap.add_argument("--age", type=int, default=DEFAULT_AGE,
                    help=f"年齢層（PWDB は {'・'.join(str(a) for a in AGES)}。既定 {DEFAULT_AGE}）")
    ap.add_argument("--subjects", type=str, default="",
                    help="被験者を明示する（例 3,4。指定の順に左右へ置く）")
    ap.add_argument("--out", type=str, default=str(DEFAULT_OUT),
                    help="書き出す PNG（同じ名前の PDF も作る）")
    ap.add_argument("--dpi", type=int, default=300, help="PNG の解像度（既定 300）")
    ap.add_argument("--selftest", action="store_true",
                    help="合成脈波で作図の筋道を検算する（PWDB は要らない）")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())
    sys.exit(run_real(args))


if __name__ == "__main__":
    main()

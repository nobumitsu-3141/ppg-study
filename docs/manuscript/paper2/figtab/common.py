#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""論文2 図表集の共通部品（配色・フォント・保存・数値の読み込み）。

図の台本（`build_fig_*.py`）はここから取る。値は `data/paper2_numbers.json`（`data/extract_tables.py` が
`../02_tables.md` を機械で読んだもの）からだけ取り、手で打たない。

    from common import load_numbers, setup, save, PALETTE, L
"""
from __future__ import annotations

import json
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

# 投稿先（Physiological Measurement, IOP）の図幅。Understand の結果で確定した値に合わせて直す。
WIDTH_MM = {"single": 85.0, "double": 178.0}
MIN_FONT_PT = 7.0

JA_FONT_FILES = [
    "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
]


def mm(x: float) -> float:
    """mm → inch（figsize 用）。"""
    return x / 25.4


def setup(lang: str = "ja", base_pt: float = 8.0) -> None:
    """rcParams を整える。文字は編集可能なテキストとして埋め込む。"""
    family = ["DejaVu Sans"]
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
        "savefig.pad_inches": 0.02,
        "axes.unicode_minus": False,
    })


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


# 段の注釈（CLAUDE.md §3: 段を出すときは毎回その場に 1 行）
STAGE_NOTE = {
    "ja": "A 段＝その手法が採用した被験者だけ、B 段＝比べる全手法が採用した共通例、C 段＝採否を無視した全員",
    "en": "Stage A = subjects the method itself accepted; B = subjects accepted by every compared method; C = all subjects",
}

# 図に共通する語（和・英）
L = {
    "ja": {
        "rho": "年齢層内 Spearman |ρ| の中央値",
        "dt_pwv": "ΔT × 大動脈脈波伝播速度",
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

# -*- coding: utf-8 -*-
"""合成PPG波形の生成（PDA実装の検証用・スライド5.3の検算に対応）。

真値（成分波パラメータ）が既知の合成拍を作り、fit_beat が
ΔT（成分波ピーク時間差）と RI（高さ比）を復元できるかを確かめる。
"""
from __future__ import annotations

import numpy as np

from .pda import skew_gaussian, component_peak

# 代表2プリセット: 切痕が見える波形 / 切痕が消えた DN-less 波形
PRESETS = {
    "clear_notch": [(1.00, 0.18, 0.055, 3.0), (0.45, 0.42, 0.090, 2.0)],
    "dn_less":     [(1.00, 0.20, 0.075, 3.0), (0.55, 0.34, 0.110, 2.0)],
}


def make_beat(preset: str = "clear_notch", fs: float = 500.0, T: float = 0.9,
              noise: float = 0.01, drift: float = 0.01, seed: int = 0):
    """合成1拍を返す。returns (t, y, truth) / truth = {dt, ri, comps}"""
    comps = PRESETS[preset]
    rng = np.random.default_rng(seed)
    t = np.arange(0.0, T, 1.0 / fs)
    y = np.zeros_like(t)
    for c in comps:
        y += skew_gaussian(t, *c)
    y += noise * rng.standard_normal(t.size)
    y += drift * np.sin(2 * np.pi * t / (2.5 * T) + rng.uniform(0, 2 * np.pi))
    y -= y.min()

    tp1, h1 = component_peak(comps[0], 0, T)
    tp2, h2 = component_peak(comps[1], 0, T)
    truth = {"dt": tp2 - tp1, "ri": h2 / h1, "comps": comps}
    return t, y, truth

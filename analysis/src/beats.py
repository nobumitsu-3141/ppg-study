# -*- coding: utf-8 -*-
"""脈波の1拍切り出しと信号品質指標（SQI）v0（スライド 6.7 Phase 2）。"""
from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks


def segment_beats(pleth: np.ndarray, fs: float, hr_range=(30, 180)) -> list[tuple[int, int]]:
    """脈波の谷（foot）で1拍ずつに切る。返り値: (開始, 終了) 添字のリスト。"""
    x = np.asarray(pleth, float)
    dmin = int(fs * 60.0 / hr_range[1])
    feet, _ = find_peaks(-x, distance=dmin)
    beats = []
    for i0, i1 in zip(feet[:-1], feet[1:]):
        dur = (i1 - i0) / fs
        if 60.0 / hr_range[1] <= dur <= 60.0 / hr_range[0]:
            beats.append((int(i0), int(i1)))
    return beats


def sqi(beat: np.ndarray, fs: float) -> dict:
    """v0 の品質判定。閾値は Phase 2 で実データを見て確定する。"""
    x = np.asarray(beat, float)
    amp = float(np.nanmax(x) - np.nanmin(x))
    n_nan = int(np.isnan(x).sum())
    # クリッピング（同一値の連続）検出
    same = int(np.max(np.diff(np.flatnonzero(np.concatenate(([True], np.diff(x) != 0, [True])))))) if x.size > 2 else 0
    ok = (amp > 0) and (n_nan == 0) and (same < 0.1 * x.size)
    return {"amp": amp, "n_nan": n_nan, "max_flat_run": same, "ok": bool(ok)}


def ensemble_average(beat_list: list[np.ndarray], n_points: int | None = None) -> np.ndarray:
    """複数拍を時間正規化して平均する（v0）。

    DN-less（重なりの強い）拍は 1% ノイズで単拍の分解が不安定になるため、
    PDA前に連続数拍を平均して SNR を稼ぐ（tests/test_pda_synthetic.py の検証参照）。
    """
    if not beat_list:
        raise ValueError("empty beat list")
    n = n_points or int(np.median([len(b) for b in beat_list]))
    xs = np.linspace(0.0, 1.0, n)
    acc = np.zeros(n)
    for b in beat_list:
        tb = np.linspace(0.0, 1.0, len(b))
        acc += np.interp(xs, tb, np.asarray(b, float))
    return acc / len(beat_list)

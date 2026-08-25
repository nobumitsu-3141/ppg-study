# -*- coding: utf-8 -*-
"""成分波からの SI・RI 算出と、ECG＋脈波からの PWTT 算出（スライド 6.3 / 6.7）。"""
from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks


def si_ri_from_fit(fit: dict, height_m: float | None = None) -> dict:
    """fit_beat の結果から ΔT・RI・(身長があれば)SI を計算する。

    ΔT = 成分波ピーク時間差 [s], RI = 第2成分/第1成分 のピーク高さ比,
    SI = 身長[m] / ΔT [m/s]（スライド 6.3「PDAで測る SI・RI」）
    """
    c1, c2 = fit["components"]
    dt = float(c2["t_peak"] - c1["t_peak"])
    ri = float(c2["height"] / max(c1["height"], 1e-12))
    out = {"dt_s": dt, "ri": ri}
    if height_m is not None and dt > 0:
        out["si"] = float(height_m / dt)
    return out


def detect_r_peaks(ecg: np.ndarray, fs: float) -> np.ndarray:
    """簡易R波検出（清浄な信号向け v0）。返り値: サンプル添字。"""
    x = np.asarray(ecg, float)
    x = x - np.nanmedian(x)
    thr = 0.6 * np.nanmax(np.abs(x))
    idx, _ = find_peaks(np.abs(x), height=thr, distance=int(0.3 * fs))
    return idx


def pleth_onset_after(pleth: np.ndarray, fs: float, i_start: int, win_s: float = 0.6) -> int | None:
    """R波後 win_s 秒以内の脈波立ち上がり点（一次微分最大）を返す。"""
    i_end = min(i_start + int(win_s * fs), len(pleth) - 1)
    if i_end - i_start < int(0.05 * fs):
        return None
    seg = np.asarray(pleth[i_start:i_end], float)
    d = np.diff(seg)
    if d.size == 0 or not np.isfinite(d).any():
        return None
    return i_start + int(np.nanargmax(d))


def pwtt_series(ecg: np.ndarray, pleth: np.ndarray, fs: float) -> np.ndarray:
    """拍ごとの PWTT [s]（R波 → 脈波立ち上がり）。esCCO 再現の対照に使う。"""
    out = []
    for i_r in detect_r_peaks(ecg, fs):
        i_on = pleth_onset_after(pleth, fs, i_r)
        if i_on is not None:
            out.append((i_on - i_r) / fs)
    return np.asarray(out)

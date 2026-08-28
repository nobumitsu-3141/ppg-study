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


def detect_r_peaks(ecg: np.ndarray, fs: float, hr_max: float = 200.0) -> np.ndarray:
    """R波検出（Pan-Tompkins 型）。返り値: サンプル添字。

    旧実装は「全体の最大振幅 × 0.6」を閾値にしていたため、記録中に
    アーチファクトが1つでもあると閾値が跳ね上がり、大多数のR波を取り逃した
    （実データ caseid=1 で真の約576拍に対し245個＝42%しか検出できず、
    脈波側の拍数と食い違って解析全体が破綻した）。

    微分→二乗→移動平均でQRSの急峻さを強調し（T波と基線動揺は抑えられる）、
    分位点ベースの頑健な閾値を使う。単発のアーチファクトでは閾値が動かない。
    """
    x = np.asarray(ecg, float)
    x = np.nan_to_num(x - np.nanmedian(x))
    if x.size < int(0.5 * fs):
        return np.array([], dtype=int)
    d = np.diff(x, prepend=x[0])
    w = max(int(0.10 * fs), 3)
    energy = np.convolve(d * d, np.ones(w) / w, mode="same")
    thr = 0.30 * float(np.percentile(energy, 98))
    if thr <= 0:
        return np.array([], dtype=int)
    idx, _ = find_peaks(energy, height=thr, distance=int(60.0 / hr_max * fs))
    # エネルギーのピークから、元波形の局所的な振幅最大（=R波頂点）へ寄せる
    half = max(int(0.05 * fs), 2)
    out = []
    for i in idx:
        a, b = max(0, i - half), min(len(x), i + half)
        if b > a:
            out.append(a + int(np.argmax(np.abs(x[a:b]))))
    return np.unique(out)


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

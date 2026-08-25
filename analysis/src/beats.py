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


# --- アンサンブル拍数の適応決定 ------------------------------------------
# 合成データでの実測（tests/test_index_variants.py）:
#   相対ノイズ 0.0059 を 4拍平均（実効 0.0030）→ DN-less でも正しい解に収束
#   相対ノイズ 0.0116 を 4拍平均（実効 0.0058）→ 40拍中17拍が別解に落ち、
#                                                 うち16拍は収束検算を通過してしまう
#   同じノイズを16拍平均（実効 0.0029）→ ΔT −1.1ms / RI +0.5% に回復
# よって「平均後の実効ノイズを 0.003 以下に保つ」ことを拍数決定の規準とする。
NOISE_TARGET = 0.003


def estimate_noise(beat: np.ndarray) -> float:
    """1拍の相対ノイズ（高周波成分のSD ÷ 振幅）を頑健に推定する。

    白色ノイズなら2階差分の分散は 6σ² になることを使う。
    脈波本体は滑らかなので2階差分にはほとんど寄与しない。
    """
    x = np.asarray(beat, float)
    if x.size < 8:
        return float("nan")
    d2 = x[2:] - 2.0 * x[1:-1] + x[:-2]
    sigma = 1.4826 * float(np.median(np.abs(d2 - np.median(d2)))) / np.sqrt(6.0)
    amp = float(np.max(x) - np.min(x))
    return sigma / max(amp, 1e-12)


def required_ensemble_size(sigma_rel: float, target: float = NOISE_TARGET,
                           lo: int = 4, hi: int = 16) -> tuple[int, bool]:
    """必要なアンサンブル拍数を返す。

    n拍平均でノイズは 1/√n になるので n = (σ_rel / target)²。
    返り値: (実際に使う拍数, 目標ノイズに到達できるか)
    到達できない（＝hi拍でも足りない）ウィンドウは採用しないこと —
    収束検算は誤った解を弾けないため、ここで落とすのが唯一の防壁になる。
    """
    if not np.isfinite(sigma_rel) or sigma_rel <= 0:
        return lo, True
    need = int(np.ceil((sigma_rel / target) ** 2))
    return int(np.clip(need, lo, hi)), need <= hi

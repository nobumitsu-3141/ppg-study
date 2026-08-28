# -*- coding: utf-8 -*-
"""脈波の1拍切り出しと信号品質指標（SQI）v0（スライド 6.7 Phase 2）。"""
from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks


def _smooth(x: np.ndarray, fs: float, win_s: float = 0.02) -> np.ndarray:
    n = max(int(win_s * fs), 3)
    k = np.ones(n) / n
    return np.convolve(x, k, mode="same")


def _foot_before_peak(x: np.ndarray, p: int, fs: float, j_min: int = 0,
                      back_s: float = 0.45) -> int:
    """収縮期ピーク p の手前から、立ち上がり点（foot）を頑健に取る。

    単純な極小値は拍頭付近が平坦なためノイズで位置が定まらず、
    合成データで中央値 +63 ms（最大 +132 ms）ずれた。ずれたまま
    アンサンブル平均すると波形がぼけ、狭い前進波が強く平滑化されて
    RI が系統的に大きく出る（+26%）。
    立ち上がりの開始は2階微分が最大になる点なので、平滑化してからこれを使う。
    """
    j0 = max(j_min, p - int(back_s * fs))
    if p - j0 < 5:
        return j0
    seg = _smooth(np.asarray(x[j0:p + 1], float), fs)
    d2 = np.gradient(np.gradient(seg))
    return j0 + int(np.argmax(d2))


def _feet_from_ecg(pleth: np.ndarray, ecg: np.ndarray, fs: float) -> np.ndarray:
    """R波を時間基準にして脈波の立ち上がり点（foot）を1心拍に1つだけ取る。

    切痕も脈波の極小値なので、極小値だけを頼りにすると1心拍で2点拾ってしまう。
    R波は1心拍に1つしかないため、これを基準にすれば取り違えが起きない。
    """
    from .indices import detect_r_peaks
    r = detect_r_peaks(ecg, fs)
    feet = []
    for i in r:
        j1 = min(i + int(0.6 * fs), len(pleth))
        if j1 - i < int(0.1 * fs):
            continue
        pk = i + int(np.argmax(pleth[i:j1]))          # 収縮期ピーク（最も頑健な目印）
        feet.append(_foot_before_peak(pleth, pk, fs, j_min=i))
    return np.unique(feet)


def _feet_from_pleth(x: np.ndarray, fs: float, hr_range) -> np.ndarray:
    """心電図が無い場合の代替。収縮期ピークの卓立度で切痕を除外してから foot を取る。"""
    lo_s = 60.0 / hr_range[1]
    rng = float(np.percentile(x, 99) - np.percentile(x, 1))
    if rng <= 0:
        return np.array([], dtype=int)
    # 収縮期ピークは切痕後の反射波より卓立している。prominence でこれを分ける。
    pk, _ = find_peaks(x, distance=int(lo_s * fs), prominence=0.25 * rng)
    feet, prev = [], 0
    for p in pk:
        feet.append(_foot_before_peak(x, p, fs, j_min=prev))
        prev = p
    return np.unique(feet)


def segment_beats(pleth: np.ndarray, fs: float, hr_range=(30, 180),
                  ecg: np.ndarray | None = None) -> list[tuple[int, int]]:
    """脈波を1拍ずつに切る。返り値: (開始, 終了) 添字のリスト。

    **ecg を渡すこと**（推奨）。極小値だけで切ると重複切痕（dicrotic notch）を
    foot と誤検出し、1心拍が2つに割れる。実データ（VitalDB caseid=1）では
    脈波のみだと 112拍/分、心電図基準では 56拍/分と2倍の食い違いが出た。
    半分に割れた区間をPDAに渡すと反射波が主ピークになり、RI が 1 を超えるなど
    非生理的な値になる。
    """
    x = np.asarray(pleth, float)
    feet = (_feet_from_ecg(x, np.asarray(ecg, float), fs) if ecg is not None
            else _feet_from_pleth(x, fs, hr_range))
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


def ensemble_average(beat_list: list[np.ndarray], n_points: int | None = None,
                     time_normalize: bool = False) -> np.ndarray:
    """複数拍を平均する。

    既定は**拍頭で揃えて最短長に切る**（時間軸を歪めない）。
    PDA は絶対時間の ΔT と成分波の高さ比を見るため、拍長で正規化して
    伸縮させると RR 変動の分だけ波形がぼけ、狭い前進波が反射波より強く
    平滑化されて **RI が系統的に大きく出る**。
    time_normalize=True で従来の拍長正規化に戻せる（比較用）。

    DN-less（重なりの強い）拍は単拍では分解が不安定なので、PDA前に
    数拍を平均して SNR を稼ぐ（拍数は required_ensemble_size で決める）。
    """
    if not beat_list:
        raise ValueError("empty beat list")
    if time_normalize:
        n = n_points or int(np.median([len(b) for b in beat_list]))
        xs = np.linspace(0.0, 1.0, n)
        acc = np.zeros(n)
        for b in beat_list:
            tb = np.linspace(0.0, 1.0, len(b))
            acc += np.interp(xs, tb, np.asarray(b, float))
        return acc / len(beat_list)
    n = n_points or min(len(b) for b in beat_list)
    return np.mean([np.asarray(b, float)[:n] for b in beat_list], axis=0)


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

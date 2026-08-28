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
    """R波後 win_s 秒以内の脈波立ち上がり点（foot）を返す。

    旧実装は一次微分最大（立ち上がりの中腹）で、実データでは拍ごとの
    ばらつきが大きく（caseid=1 で IQR 96–152ms、隣接ウィンドウ自己相関 +0.34）、
    前提検証を希釈する主因候補だった。拍の切り出しと同じ
    「平滑化2階微分の最大点」（立ち上がりの開始）に統一する。
    """
    from .beats import _foot_before_peak
    i_end = min(i_start + int(win_s * fs), len(pleth))
    if i_end - i_start < int(0.1 * fs):
        return None
    seg = np.asarray(pleth[i_start:i_end], float)
    if not np.isfinite(seg).any():
        return None
    pk = i_start + int(np.nanargmax(seg))
    if pk <= i_start:
        return None
    return _foot_before_peak(pleth, pk, fs, j_min=i_start)


def _rf_pairs(ecg: np.ndarray, pleth: np.ndarray, fs: float):
    """各R波と「その後最初の脈波foot」の対 (v_raw, RR_n) を返す。"""
    from .beats import _feet_from_ecg
    r = detect_r_peaks(ecg, fs)
    feet = _feet_from_ecg(pleth, ecg, fs)
    if len(r) < 3 or len(feet) < 3:
        return [], float("nan")
    rr_med = float(np.median(np.diff(r))) / fs
    pairs, fi = [], 0
    for n, i_r in enumerate(r[:-1]):
        rr_n = (r[n + 1] - i_r) / fs
        while fi < len(feet) and feet[fi] <= i_r + int(0.02 * fs):
            fi += 1
        if fi >= len(feet):
            break
        v = (feet[fi] - i_r) / fs
        if 0.02 < v < 1.5 * rr_med:
            pairs.append((v, rr_n))
    return pairs, rr_med


def estimate_pleth_lag(ecg: np.ndarray, pleth: np.ndarray, fs: float) -> float:
    """症例レベルの脈波遅延 L（装置遅延＋典型PWTT）を推定する [s]。

    VitalDBの脈波チャネルはモニタ内部処理でECGに対し数百msの固定遅延を持ち
    （case 1/17 で約670ms）、遅延がRRを超えると R→次foot の生値は RR を法として
    折り返す。候補 v + k·RR_n (k=0,1,2) のうち、L が症例内でほぼ一定である
    ことを使ってクラスタを同定する。**記録全体で推定すること** — RRの変動が
    大きいほど誤った枝のクラスタは滲み、正しい枝だけが締まる。
    60秒窓の中だけではRRがほぼ一定のため枝を区別できない（実測で確認済み）。
    """
    # 60秒窓ごとに対を取り、症例全体でプールする。
    # 記録全体を一括で処理すると、R波検出の閾値（分位点ベース）が非定常な
    # 振幅変化に追従できず倍数計上や欠落が起きる（実測: RR中央値が半分になった）。
    # 窓単位なら閾値が局所適応し、かつプールにはRRの多様性が残るので
    # 折り返し枝の判別ができる。
    ecg = np.nan_to_num(np.asarray(ecg, float))
    pleth = np.nan_to_num(np.asarray(pleth, float))
    win = int(60 * fs)
    step = max(int(180 * fs), win)
    pairs = []
    for i0 in range(0, max(len(ecg) - win, 1), step):
        pw, _ = _rf_pairs(ecg[i0:i0 + win], pleth[i0:i0 + win], fs)
        pairs.extend(pw)
    if len(pairs) < 30:
        return float("nan")
    varr = np.array([v for v, _ in pairs])
    rarr = np.array([rr for _, rr in pairs])
    branches = np.stack([varr + k * rarr for k in (0, 1, 2)])   # (3, n)
    cands = branches[branches < 3.0]
    hist, edges = np.histogram(cands, bins=np.arange(0.0, 3.02, 0.02))
    # 選択基準は「被覆率」: その遅延で±80ms以内に枝を持つR-foot対の割合。
    # 真の遅延はほぼ全拍を覆う。締まりだけで選ぶと、R直近の偽footが作る
    # 少数の鋭いクラスタを拾ってしまう（実測で確認）。
    top = np.argsort(hist)[::-1][:10]
    best_L, best_cov = float("nan"), 0.0
    for b in top:
        c0 = float(edges[b] + 0.01)
        cov = float(np.mean(np.min(np.abs(branches - c0), axis=0) < 0.08))
        if cov > best_cov:
            near = cands[np.abs(cands - c0) < 0.10]
            best_cov, best_L = cov, float(np.median(near)) if near.size else c0
    return best_L


def pwtt_series(ecg: np.ndarray, pleth: np.ndarray, fs: float,
                lag: float | None = None) -> np.ndarray:
    """拍ごとの PWTT [s]（R波 → 対応する脈波 foot・折り返し展開つき）。

    lag には estimate_pleth_lag() で**症例全体から**推定した値を渡すこと。
    None の場合は渡された区間だけで推定する（短い区間では枝の同定が
    不安定になるため、本解析では必ず症例レベルの lag を渡す）。

    返り値には装置遅延が加算されている（絶対値は症例間比較に使えない）。
    本研究のモデルは症例内のΔのみ使うため、固定遅延は差分で消える。
    """
    ecg = np.nan_to_num(np.asarray(ecg, float))
    pleth = np.nan_to_num(np.asarray(pleth, float))
    pairs, _ = _rf_pairs(ecg, pleth, fs)
    if len(pairs) < 3:
        return np.asarray([])
    L = lag if (lag is not None and np.isfinite(lag)) else estimate_pleth_lag(ecg, pleth, fs)
    if not np.isfinite(L):
        return np.asarray([])
    out = []
    for v, rr_n in pairs:
        best = min((v + k * rr_n for k in (0, 1, 2)), key=lambda x: abs(x - L))
        if abs(best - L) < 0.15:
            out.append(best)
    return np.asarray(out)

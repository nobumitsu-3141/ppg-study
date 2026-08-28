# -*- coding: utf-8 -*-
"""R波検出の頑健性の検証（現実的な合成心電図・実データ不使用）。

実データ（VitalDB caseid=1）で判明した不具合の再現と修正の固定。
旧実装は「記録全体の最大振幅 × 0.6」を閾値にしていたため、体動などの
大振幅アーチファクトが1つでもあると閾値が跳ね上がり、大多数のR波を取り逃した。
実データでは真の約576拍（HR 115）に対し245個＝42%しか検出できず、
脈波側の拍数と食い違って PDA の結果が破綻していた。

実行: analysis/ で  python3 -m tests.test_r_peak_detection
"""
from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks

from src.indices import detect_r_peaks

FS = 500.0


def synth_ecg(hr: float, minutes: float = 5.0, artifact: bool = True, seed: int = 0):
    """P-QRS-T ＋ 基線動揺 ＋ 体動アーチファクトを含む合成心電図。"""
    rng = np.random.default_rng(seed)
    n = int(minutes * 60 * FS)
    x = np.zeros(n)
    rpos, pos, rr0 = [], int(0.2 * FS), 60.0 / hr

    def g(c, a, w):
        i0, i1 = max(0, int(c - 4 * w)), min(n, int(c + 4 * w))
        if i1 > i0:
            tt = np.arange(i0, i1)
            x[i0:i1] += a * np.exp(-0.5 * ((tt - c) / w) ** 2)

    while pos < n - int(rr0 * FS):
        g(pos - int(0.16 * FS), 0.15, 0.020 * FS)      # P波
        g(pos - int(0.02 * FS), -0.12, 0.008 * FS)     # Q波
        g(pos, 1.00, 0.008 * FS)                       # R波
        g(pos + int(0.02 * FS), -0.25, 0.010 * FS)     # S波
        g(pos + int(0.22 * FS), 0.30, 0.045 * FS)      # T波（幅広・誤検出しやすい）
        rpos.append(pos)
        pos += int(rr0 * FS * (1 + 0.04 * rng.standard_normal()))

    t = np.arange(n) / FS
    x += 0.10 * np.sin(2 * np.pi * 0.25 * t) + 0.02 * rng.standard_normal(n)
    if artifact:
        i = n // 3
        w = int(0.3 * FS)
        x[i:i + w] += 3.0 * np.hanning(w)              # R波の3倍の体動アーチファクト
    return x, np.array(rpos)


def legacy_detect(x, fs):
    """旧実装（全体最大振幅に対する固定比）の再現。"""
    y = x - np.nanmedian(x)
    idx, _ = find_peaks(np.abs(y), height=0.6 * np.nanmax(np.abs(y)),
                        distance=int(0.3 * fs))
    return idx


def main() -> None:
    print("== R波検出の頑健性 ==")
    print(f"\n{'条件':<26}{'真の拍数':>9}{'旧':>7}{'新':>7}{'旧率':>8}{'新率':>8}   判定")
    ok = True
    for hr in (55, 75, 115):
        for art in (False, True):
            x, rp = synth_ecg(hr, artifact=art)
            n_old = len(legacy_detect(x, FS))
            n_new = len(detect_r_peaks(x, FS))
            r_old, r_new = n_old / len(rp), n_new / len(rp)
            good = 0.95 <= r_new <= 1.05
            ok &= good
            lab = f"HR {hr} / アーチファクト{'有' if art else '無'}"
            print(f"{lab:<26}{len(rp):>9}{n_old:>7}{n_new:>7}"
                  f"{r_old:>7.0%}{r_new:>8.0%}   {'OK' if good else 'FAIL'}")

    # 検出位置の精度（拍の切り出しの基準になるのでずれは致命的）
    x, rp = synth_ecg(75, artifact=True)
    det = detect_r_peaks(x, FS)
    err = [abs(int(np.min(np.abs(rp - d)))) for d in det]
    med_ms = float(np.median(err)) / FS * 1000
    p95_ms = float(np.percentile(err, 95)) / FS * 1000
    good_pos = p95_ms < 15.0
    ok &= good_pos
    print(f"\n[検出位置の精度] 真のR波とのずれ 中央値 {med_ms:.1f} ms / "
          f"95%点 {p95_ms:.1f} ms   {'OK' if good_pos else 'FAIL'}")

    # T波を拾っていないか（拾うと拍数が倍増する）
    x, rp = synth_ecg(60, artifact=False)
    n = len(detect_r_peaks(x, FS))
    good_t = n <= len(rp) * 1.05
    ok &= good_t
    print(f"[T波の誤検出] 真 {len(rp)} 拍 に対し検出 {n} 拍   "
          f"{'OK（T波は拾っていない）' if good_t else 'FAIL（T波を拾っている）'}")

    if ok:
        print("\nALL PASS")
        print("帰結: 微分→二乗→移動平均で強調し、分位点ベースの閾値を使う。")
        print("      振幅の最大値を基準にすると単発のアーチファクトで検出が壊滅する。")
    else:
        print("\nSOME FAILED")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

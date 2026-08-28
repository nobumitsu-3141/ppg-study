# -*- coding: utf-8 -*-
"""拍の切り出しとアンサンブル整列の検証（合成の連続波形・実データ不使用）。

実データ（VitalDB caseid=1）で判明した2つの不具合を再現し、修正を固定する。

 1. 極小値だけで拍を切ると**重複切痕を foot と誤検出**して1心拍が2つに割れる。
    実データでは脈波のみ 112拍/分 に対し心電図基準 49拍/分 と約2倍の食い違い。
    半分に割れた区間をPDAに渡すと反射波が主ピークになり RI>1 という
    非生理的な値が出る（実データで RI=1.64 を観測）。
 2. 拍頭付近は平坦なので極小値の位置がノイズで定まらず、拍ごとに整列がずれる。
    ずれたままアンサンブル平均すると波形がぼけ、狭い前進波が反射波より強く
    平滑化されて **RI が系統的に大きく出る**。

実行: analysis/ で  python3 -m tests.test_beat_segmentation
"""
from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks

from src.synth import make_beat, PRESETS
from src.beats import (segment_beats, ensemble_average, estimate_noise,
                       required_ensemble_size)
from src.pda import fit_beat, component_peak
from src.indices import si_ri_from_fit

FS = 500.0
HR_BPM = 56.0                      # 実データ caseid=1 に合わせる


def build_record(preset: str, minutes: float = 2.0, seed: int = 0):
    """切痕を持つ拍を連ねた連続波形（心電図つき）。真の拍頭も返す。"""
    rng = np.random.default_rng(seed)
    pl, ec, starts, pos = [], [], [], 0
    rr0 = 60.0 / HR_BPM
    while pos / FS < minutes * 60:
        rr = rr0 * (1 + 0.05 * rng.standard_normal())
        m = int(rr * FS)
        _, y, _ = make_beat(preset=preset, fs=FS, T=rr, noise=0.01,
                            seed=int(rng.integers(1e6)))
        y = y[:m] if len(y) >= m else np.pad(y, (0, m - len(y)))
        e = np.zeros(m)
        e[:int(0.02 * FS)] = 1.2
        pl.append(y); ec.append(e); starts.append(pos); pos += m
    return np.concatenate(pl), np.concatenate(ec), np.array(starts)


def legacy_segment(pleth):
    """旧実装（極小値＋最小間隔のみ）の再現。"""
    feet, _ = find_peaks(-pleth, distance=int(FS * 60.0 / 180))
    return [(int(a), int(b)) for a, b in zip(feet[:-1], feet[1:])
            if 0.333 <= (b - a) / FS <= 2.0]


def run_pda(pleth, beats):
    sig = float(np.median([estimate_noise(pleth[a:b]) for a, b in beats[:40]]))
    n_ens, _ = required_ensemble_size(sig)
    dts, ris = [], []
    for k in range(0, len(beats) - n_ens + 1, n_ens):
        y = ensemble_average([pleth[a:b] for a, b in beats[k:k + n_ens]])
        try:
            f = fit_beat(np.arange(len(y)) / FS, y)
        except Exception:
            continue
        if not f["ok"]:
            continue
        m = si_ri_from_fit(f)
        dts.append(m["dt_s"] * 1000)
        ris.append(m["ri"])
    return (float(np.median(dts)) if dts else float("nan"),
            float(np.median(ris)) if ris else float("nan"), n_ens)


def truth(preset):
    c1, c2 = [tuple(c) for c in PRESETS[preset]]
    tp1, h1 = component_peak(c1, 0, 0.9)
    tp2, h2 = component_peak(c2, 0, 0.9)
    return (tp2 - tp1) * 1000, h2 / h1


def main() -> None:
    print("== 拍の切り出しとアンサンブル整列 ==")
    ok = True

    print("\n[1. 重複切痕による二重検出（旧実装の不具合）]")
    for preset in ("clear_notch", "dn_less"):
        pleth, ecg, starts = build_record(preset)
        n_true = len(starts)
        r_old = len(legacy_segment(pleth)) / n_true
        r_new = len(segment_beats(pleth, FS, ecg=ecg)) / n_true
        r_pl = len(segment_beats(pleth, FS)) / n_true
        print(f"  {preset:<12} 真 {n_true} 拍 ({HR_BPM:.0f}拍/分):  "
              f"旧 {r_old:.2f}x / 新・心電図基準 {r_new:.2f}x / 新・脈波のみ {r_pl:.2f}x")
        good = (r_old > 1.5) and (0.9 <= r_new <= 1.1) and (0.9 <= r_pl <= 1.1)
        ok &= good
        if not good:
            print("    FAIL")
    print("  -> 旧は約2倍に割れ、新はどちらの経路も等倍  "
          f"{'PASS' if ok else 'FAIL'}")

    print("\n[2. foot の整列の一貫性（アンサンブル平均の前提）]")
    for preset in ("clear_notch", "dn_less"):
        pleth, ecg, starts = build_record(preset)
        b = segment_beats(pleth, FS, ecg=ecg)
        off = np.array([f - starts[int(np.argmin(np.abs(starts - f)))] for f, _ in b])
        spread = float(off.max() - off.min()) / FS * 1000
        print(f"  {preset:<12} foot のばらつき {spread:5.1f} ms "
              f"(中央値 {np.median(off) / FS * 1000:+.0f} ms の一定オフセット)")
        good = spread < 40.0          # 一定のオフセットは可。拍ごとのばらつきが問題
        ok &= good
        if not good:
            print("    FAIL: ばらつきが大きいとアンサンブルがぼけて RI が膨らむ")
    print("  -> ばらつきが小さければ整列は健全  PASS" if ok else "  -> FAIL")

    print("\n[3. 連続波形から真値を復元できるか（端から端まで）]")
    print(f"  {'波形':<12}{'方式':<22}{'ΔT誤差':>10}{'RI誤差':>10}   判定")
    for preset in ("clear_notch", "dn_less"):
        dt_t, ri_t = truth(preset)
        pleth, ecg, _ = build_record(preset)
        for lab, beats in (("旧: 極小値のみ", legacy_segment(pleth)),
                           ("新: 心電図基準", segment_beats(pleth, FS, ecg=ecg))):
            dt, ri, _ = run_pda(pleth, beats)
            good = abs(dt - dt_t) < 15 and abs(ri / ri_t - 1) < 0.15
            print(f"  {preset:<12}{lab:<22}{dt - dt_t:>+8.0f}ms{ri / ri_t - 1:>+9.0%}"
                  f"   {'OK' if good else '×'}")
            if lab.startswith("新"):
                ok &= good

    if ok:
        print("\nALL PASS")
        print("帰結: 拍の切り出しには**心電図を必ず渡す**（segment_beats(..., ecg=ecg)）。")
        print("      foot は2階微分で取り、アンサンブルは拍頭を揃えて平均する")
        print("      （拍長で正規化するとRR変動の分だけ RI が膨らむ）。")
    else:
        print("\nSOME FAILED")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

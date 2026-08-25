# -*- coding: utf-8 -*-
"""アンサンブル拍数の適応決定の検証（合成データ・実データ不使用）。

背景: tests/test_index_variants.py で、ノイズが上がると2カーネル分解の解が
二峰化し、誤った解の 16/17 が収束検算を通過してしまうことが判明した。
検算は最後の砦にならないので、前処理側（拍数）で実効ノイズを抑える。

検証:
 1) ノイズ推定器が真値を復元すること
 2) 固定4拍では高ノイズで別解に落ちるが、適応拍数なら落ちないこと
 3) 上限拍数でも目標に届かないウィンドウは「到達不能」として弾けること

実行: analysis/ で  python3 -m tests.test_ensemble_adaptive
"""
from __future__ import annotations

import numpy as np

from src.beats import estimate_noise, required_ensemble_size, ensemble_average, NOISE_TARGET
from src.pda import fit_beat, component_peak
from src.synth import make_beat, PRESETS

FS, T = 500.0, 0.9


def _truth(preset):
    c1, c2 = [tuple(c) for c in PRESETS[preset]]
    tp1, h1 = component_peak(c1, 0.0, T)
    tp2, h2 = component_peak(c2, 0.0, T)
    return tp2 - tp1, h2 / h1


def _fit_n(preset, noise, n_beats, seed0):
    beats = [make_beat(preset=preset, fs=FS, T=T, noise=noise, seed=seed0 + b)[1]
             for b in range(n_beats)]
    y = ensemble_average(beats)
    f = fit_beat(np.arange(len(y)) / FS, y)
    c = f["components"]
    return c[1]["t_peak"] - c[0]["t_peak"], c[1]["height"] / c[0]["height"], bool(f["ok"])


def main() -> None:
    print("== アンサンブル拍数の適応決定 ==")
    ok_all = True

    print("\n[1. ノイズ推定器の精度]")
    worst = 0.0
    for preset in ("clear_notch", "dn_less"):
        for noise in (0.005, 0.01, 0.02, 0.04):
            est, amp = [], []
            for s in range(12):
                _, y, _ = make_beat(preset=preset, T=T, noise=noise, seed=s)
                est.append(estimate_noise(y))
                amp.append(np.max(y) - np.min(y))
            true_rel = noise / float(np.median(amp))
            rel_err = abs(float(np.median(est)) / true_rel - 1)
            worst = max(worst, rel_err)
    print(f"  8条件（切痕あり／DN-less × ノイズ4水準）で推定誤差 最大 {worst:.1%}"
          f"  {'PASS' if worst < 0.05 else 'FAIL'}")
    ok_all &= worst < 0.05

    print("\n[2. 固定4拍 vs 適応拍数（DN-less）]")
    dt_true, ri_true = _truth("dn_less")
    print(f"{'ノイズ':>8}{'σ_rel':>9}{'採用拍数':>9}"
          f"{'固定4拍: 正解率':>17}{'適応: 正解率':>15}")
    for noise in (0.01, 0.02, 0.03):
        _, y0, _ = make_beat(preset="dn_less", T=T, noise=noise, seed=0)
        sigma = estimate_noise(y0)
        n_ad, reachable = required_ensemble_size(sigma)
        good_fix = good_ad = n_trial = 0
        for e in range(20):
            n_trial += 1
            for n_beats, is_ad in ((4, False), (n_ad, True)):
                try:
                    dt, ri, _ = _fit_n("dn_less", noise, n_beats, 7 * e * 97)
                except Exception:
                    continue
                hit = abs(dt - dt_true) < 0.010 and abs(ri / ri_true - 1) < 0.10
                if is_ad:
                    good_ad += hit
                else:
                    good_fix += hit
        print(f"{noise:>8.0%}{sigma:>9.4f}{n_ad:>9d}"
              f"{f'{good_fix}/{n_trial}':>17}{f'{good_ad}/{n_trial}':>15}"
              f"   {'到達可' if reachable else '★到達不能→ウィンドウ棄却'}")
        if reachable:
            passed = good_ad >= 0.9 * n_trial
            ok_all &= passed
            if not passed:
                print(f"    FAIL: 適応拍数でも正解率 {good_ad}/{n_trial}")

    print("\n[3. 到達不能ウィンドウの検出]")
    hi = 16
    rows = [(s, *required_ensemble_size(s)) for s in (0.003, 0.006, 0.012, 0.020, 0.030)]
    for s, n, reach in rows:
        print(f"  σ_rel={s:.3f} → {n:2d}拍 実効{s / np.sqrt(n):.4f}"
              f"  {'採用' if reach else '棄却（上限16拍でも目標0.003に届かない）'}")
    detect = all(r for _, _, r in rows[:3]) and not any(r for _, _, r in rows[3:])
    print(f"  -> 目標{NOISE_TARGET}に届く/届かないを正しく判定  {'PASS' if detect else 'FAIL'}")
    ok_all &= detect

    if ok_all:
        print("\nALL PASS — ノイズに応じて拍数を決め、届かないウィンドウは棄却する運用が有効")
    else:
        print("\nSOME FAILED")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

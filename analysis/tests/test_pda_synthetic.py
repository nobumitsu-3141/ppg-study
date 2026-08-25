# -*- coding: utf-8 -*-
"""C-4: PDA実装の合成波形検証（チェックリスト C-4 / スライド5.3の検算）。

実行: analysis/ ディレクトリで  python3 -m tests.test_pda_synthetic

検証内容:
 1) 切痕が見える波形（単拍・ノイズ1%）: ΔT・RIを厳密に復元できること
 2) DN-less波形（重なり大）:
    - 単拍・ノイズ1%では解が不安定（スライド5.5「解が一意に決まらない」の定量的実証）
      → 統計を記録として出力（合否判定には使わない）
    - 4拍アンサンブル平均（実運用の想定＝ノイズ実効0.5%）では復元できること
 3) 1成分のみの波形に2 kernelを当てた場合、検算がフラグを立てること
"""
from __future__ import annotations

import numpy as np

from src.pda import fit_beat, skew_gaussian
from src.synth import make_beat
from src.beats import ensemble_average
from src.indices import si_ri_from_fit

N_SEEDS = 5


def run_clear() -> bool:
    ok_all = True
    for seed in range(N_SEEDS):
        t, y, truth = make_beat("clear_notch", seed=seed)
        fit = fit_beat(t, y, seed=seed)
        m = si_ri_from_fit(fit)
        e_dt = abs(m["dt_s"] - truth["dt"]) * 1000.0
        e_ri = abs(m["ri"] - truth["ri"]) / truth["ri"]
        ok = (e_dt <= 12.0) and (e_ri <= 0.10) and fit["ok"]
        ok_all &= ok
        print(f"  seed{seed}: dT err {e_dt:5.1f} ms | RI err {100*e_ri:5.1f}% | "
              f"checks_ok={fit['ok']} -> {'PASS' if ok else 'FAIL'}")
    return ok_all


def report_dnless_single():
    errs_dt, errs_ri = [], []
    for seed in range(N_SEEDS):
        t, y, truth = make_beat("dn_less", seed=seed)
        fit = fit_beat(t, y, seed=seed)
        m = si_ri_from_fit(fit)
        errs_dt.append((m["dt_s"] - truth["dt"]) * 1000.0)
        errs_ri.append(100 * (m["ri"] - truth["ri"]) / truth["ri"])
    print(f"  （記録）単拍・ノイズ1%: dT err median {np.median(errs_dt):+.1f} ms, "
          f"RI err median {np.median(errs_ri):+.1f}% — 重なり大では単拍推定が不安定")


def run_dnless_ensemble(n_avg: int = 4) -> bool:
    ok_all = True
    for seed in range(N_SEEDS):
        beats = []
        for k in range(n_avg):
            t, y, truth = make_beat("dn_less", seed=1000 * seed + k)
            beats.append(y)
        y_avg = ensemble_average(beats)
        fit = fit_beat(t, y_avg, seed=seed)
        m = si_ri_from_fit(fit)
        e_dt = abs(m["dt_s"] - truth["dt"]) * 1000.0
        e_ri = abs(m["ri"] - truth["ri"]) / truth["ri"]
        ok = (e_dt <= 10.0) and (e_ri <= 0.10)
        ok_all &= ok
        print(f"  seed{seed}: {n_avg}拍平均 -> dT err {e_dt:5.1f} ms | RI err {100*e_ri:5.1f}% | "
              f"checks_ok={fit['ok']} -> {'PASS' if ok else 'FAIL'}")
    return ok_all


def run_overfit_guard() -> bool:
    fs, T = 500.0, 0.9
    t = np.arange(0, T, 1 / fs)
    rng = np.random.default_rng(1)
    y = skew_gaussian(t, 1.0, 0.22, 0.09, 2.5) + 0.01 * rng.standard_normal(t.size)
    y -= y.min()
    fit = fit_beat(t, y, seed=1)
    flagged = (not fit["ok"])
    print(f"  single-component input -> flagged={flagged} "
          f"(amp_zero={fit['checks']['amp_zero']}, reproducible={fit['checks']['reproducible']}, "
          f"boundary={fit['checks']['boundary_stick']}) -> {'PASS' if flagged else 'FAIL'}")
    return flagged


if __name__ == "__main__":
    print("== PDA synthetic validation (skewed-Gaussian, 2 kernels) ==")
    print("[1. clear_notch 単拍]")
    r1 = run_clear()
    print("[2a. dn_less 単拍（特性の記録）]")
    report_dnless_single()
    print("[2b. dn_less 4拍アンサンブル平均（実運用条件）]")
    r2 = run_dnless_ensemble()
    print("[3. overfit guard]")
    r3 = run_overfit_guard()
    if r1 and r2 and r3:
        print("\nALL PASS — C-4（合成波形での検証）クリア")
        print("運用上の帰結: DN-less拍はPDA前に数拍のアンサンブル平均（または同等のSNR確保）を行うこと。")
    else:
        print("\nSOME FAILED — 実装/許容値を見直すこと")
        raise SystemExit(1)

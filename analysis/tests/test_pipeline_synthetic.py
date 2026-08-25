# -*- coding: utf-8 -*-
"""Phase 3〜5 の機構検証: モデル＋統計＋症例単位交差検証のエンドツーエンドテスト。

実行: analysis/ で  python3 -m tests.test_pipeline_synthetic

判定:
 1) effectコホート（PWTTに血管状態が混入 = 補正の余地が実在）:
    K(SI,RI)補正で percentage error が有意に低下すること（ブートストラップCI上限 < 0）
 2) nullコホート（混入なし = 補正の余地なし）:
    有意な「改善」を検出しないこと（偽陽性ガード。CIが0を跨ぐ）
 3) 参考統計（Bland-Altman・concordance）が破綻なく計算できること
"""
from __future__ import annotations

import numpy as np

from src.synth_cohort import make_cohort
from src.models import crossval
from src.stats import bootstrap_diff_ci, bland_altman, concordance_4q, per_case_pe


def run(effect: bool, seed: int) -> dict:
    cases = make_cohort(n_cases=80, n_windows=30, effect=effect, seed=seed)
    res = crossval(cases, n_folds=5, seed=seed)
    return bootstrap_diff_ci(res, seed=seed), res


def main() -> None:
    print("== pipeline validation (models + stats + case-level 5-fold CV) ==")
    ok = True

    print("[1. effect cohort ― 補正の余地が実在するデータ]")
    n_sig = 0
    for seed in range(3):
        s, res = run(effect=True, seed=seed)
        print(f"  seed{seed}: PE ctrl {s['pe_ctrl_median']:.1f}% -> prop {s['pe_prop_median']:.1f}%  "
              f"ΔPE {s['diff_mean']:+.1f}% [CI {s['ci_low']:+.1f}, {s['ci_high']:+.1f}]  "
              f"significant={s['significant_improvement']}")
        n_sig += s["significant_improvement"]
    print(f"  -> 有意な改善 {n_sig}/3  {'PASS' if n_sig == 3 else 'FAIL'}")
    ok &= (n_sig == 3)

    print("[2. null cohort ― 補正の余地が無いデータ（偽陽性ガード）]")
    n_fp = 0
    for seed in range(3):
        s, _ = run(effect=False, seed=seed)
        print(f"  seed{seed}: ΔPE {s['diff_mean']:+.1f}% [CI {s['ci_low']:+.1f}, {s['ci_high']:+.1f}]  "
              f"significant={s['significant_improvement']}")
        n_fp += s["significant_improvement"]
    print(f"  -> 偽陽性 {n_fp}/3  {'PASS' if n_fp == 0 else 'FAIL'}")
    ok &= (n_fp == 0)

    print("[3. 参考統計の健全性]")
    _, res = run(effect=True, seed=0)
    all_ref = np.concatenate([r["co_ref"] for r in res])
    all_prop = np.concatenate([r["est_prop"] for r in res])
    ba = bland_altman(all_prop, all_ref)
    d_est = np.concatenate([np.diff(r["est_prop"]) for r in res])
    d_ref = np.concatenate([np.diff(r["co_ref"]) for r in res])
    conc = concordance_4q(d_est, d_ref)
    pe = per_case_pe(res, "est_prop")
    sane = np.isfinite(list(ba.values())).all() and 0 <= conc <= 1 and np.isfinite(pe).all()
    print(f"  BA bias {ba['bias']:+.2f} L/min (LoA {ba['loa_low']:+.2f}..{ba['loa_high']:+.2f}) / "
          f"concordance {conc:.2f} / per-case PE finite={np.isfinite(pe).all()}  "
          f"{'PASS' if sane else 'FAIL'}")
    ok &= bool(sane)

    if ok:
        print("\nALL PASS — Phase 3〜5 の解析機構は実データを待つだけの状態")
    else:
        print("\nSOME FAILED")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

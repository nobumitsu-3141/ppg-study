# -*- coding: utf-8 -*-
"""評価統計: percentage error（Critchley法）・Bland-Altman・4象限concordance・
症例単位ブートストラップCI（SAP v0 準拠）。"""
from __future__ import annotations

import numpy as np


def percentage_error(est: np.ndarray, ref: np.ndarray) -> float:
    """Critchley & Critchley: PE = 1.96×SD(bias) / mean(ref) ×100 [%]"""
    bias = np.asarray(est, float) - np.asarray(ref, float)
    return float(100.0 * 1.96 * np.std(bias, ddof=1) / np.mean(ref))


def bland_altman(est: np.ndarray, ref: np.ndarray) -> dict:
    bias = np.asarray(est, float) - np.asarray(ref, float)
    m, s = float(np.mean(bias)), float(np.std(bias, ddof=1))
    return {"bias": m, "loa_low": m - 1.96 * s, "loa_high": m + 1.96 * s}


def concordance_4q(d_est: np.ndarray, d_ref: np.ndarray, excl: float = 0.5) -> float:
    """変化方向の一致率。exclusion zone: |ΔCO_ref| < excl [L/min] を除外。"""
    d_est, d_ref = np.asarray(d_est, float), np.asarray(d_ref, float)
    keep = np.abs(d_ref) >= excl
    if keep.sum() == 0:
        return float("nan")
    return float(np.mean(np.sign(d_est[keep]) == np.sign(d_ref[keep])))


def per_case_pe(results: list[dict], key: str) -> np.ndarray:
    """crossval結果から症例ごとのPEを計算。key: 'est_ctrl' | 'est_prop'"""
    return np.array([percentage_error(r[key], r["co_ref"]) for r in results])


def bootstrap_diff_ci(results: list[dict], n_boot: int = 2000, seed: int = 0) -> dict:
    """症例単位リサンプリングによる ΔPE（提案−対照）の95%CI。負なら提案が優越。"""
    rng = np.random.default_rng(seed)
    pe_c = per_case_pe(results, "est_ctrl")
    pe_p = per_case_pe(results, "est_prop")
    diff = pe_p - pe_c
    n = len(diff)
    boots = np.array([np.mean(diff[rng.integers(0, n, n)]) for _ in range(n_boot)])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {
        "pe_ctrl_median": float(np.median(pe_c)),
        "pe_prop_median": float(np.median(pe_p)),
        "diff_mean": float(np.mean(diff)),
        "ci_low": float(lo), "ci_high": float(hi),
        "significant_improvement": bool(hi < 0),
    }

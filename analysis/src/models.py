# -*- coding: utf-8 -*-
"""対照モデル（PWTT型）と提案モデル（K(SI,RI)補正）、症例単位の交差検証。

SAP v0（docs/research/sap_v0.md）の仕様:
  - 較正は症例内の初回ウィンドウ（実機esCCOの較正手順を模擬）
  - 対照: esCO_ctrl(t) = CO_0 × (1 + b・ΔPWTT(t))          b は導出foldで推定
  - 提案: esCO_prop(t) = esCO_ctrl(t) × (1 + c1・ΔSI%(t) + c2・ΔRI%(t))
          c1, c2 は導出foldの誤差残差への回帰で推定
  - 検証はfold外の症例のみで評価（症例単位5-fold、リーク禁止）
"""
from __future__ import annotations

import numpy as np


def _deltas(case: dict) -> dict:
    """症例内の初回較正点からの変化量を作る。"""
    w = case["windows"]
    return {
        "dpwtt": w["pwtt"] - w["pwtt"][0],
        "dsi": (w["si"] - w["si"][0]) / max(abs(w["si"][0]), 1e-9),
        "dri": (w["ri"] - w["ri"][0]) / max(abs(w["ri"][0]), 1e-9),
        "co_ref": w["co_ref"],
        "co0": w["co_ref"][0],
    }


def fit_control(cases: list[dict]) -> dict:
    """導出foldで対照モデルの傾き b を推定（ΔCO% ~ ΔPWTT のプール回帰）。"""
    x, y = [], []
    for c in cases:
        d = _deltas(c)
        x.append(d["dpwtt"])
        y.append(d["co_ref"] / d["co0"] - 1.0)
    x, y = np.concatenate(x), np.concatenate(y)
    b = float(np.sum(x * y) / max(np.sum(x * x), 1e-12))
    return {"b": b}


def predict_control(case: dict, m: dict) -> np.ndarray:
    d = _deltas(case)
    return d["co0"] * (1.0 + m["b"] * d["dpwtt"])


def fit_correction(cases: list[dict], m_ctrl: dict) -> dict:
    """導出foldで補正係数 c1, c2 を推定（対照モデルの相対誤差 ~ ΔSI%, ΔRI%）。"""
    X, y = [], []
    for c in cases:
        d = _deltas(c)
        est = predict_control(c, m_ctrl)
        resid = d["co_ref"] / np.clip(est, 1e-9, None) - 1.0
        X.append(np.column_stack([d["dsi"], d["dri"]]))
        y.append(resid)
    X, y = np.vstack(X), np.concatenate(y)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return {"c1": float(coef[0]), "c2": float(coef[1])}


def predict_proposed(case: dict, m_ctrl: dict, m_corr: dict) -> np.ndarray:
    d = _deltas(case)
    corr = 1.0 + m_corr["c1"] * d["dsi"] + m_corr["c2"] * d["dri"]
    return predict_control(case, m_ctrl) * np.clip(corr, 0.3, 3.0)


def crossval(cases: list[dict], n_folds: int = 5, seed: int = 0) -> list[dict]:
    """症例単位k-fold。返り値: 症例ごとの {caseid, co_ref, est_ctrl, est_prop}（すべて検証fold時の推定）。"""
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(cases))
    folds = [sorted(order[k::n_folds].tolist()) for k in range(n_folds)]
    out = []
    for k in range(n_folds):
        val_idx = set(folds[k])
        deriv = [c for j, c in enumerate(cases) if j not in val_idx]
        m_ctrl = fit_control(deriv)
        m_corr = fit_correction(deriv, m_ctrl)
        for j in sorted(val_idx):
            c = cases[j]
            out.append({
                "caseid": c["caseid"],
                "co_ref": c["windows"]["co_ref"],
                "est_ctrl": predict_control(c, m_ctrl),
                "est_prop": predict_proposed(c, m_ctrl, m_corr),
            })
    return out

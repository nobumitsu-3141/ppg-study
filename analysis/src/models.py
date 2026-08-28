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


def _rel(x: np.ndarray) -> np.ndarray:
    """初回値からの相対変化。"""
    return (x - x[0]) / max(abs(float(x[0])), 1e-9)


def _deltas(case: dict) -> dict:
    """症例内の初回較正点からの変化量を作る。"""
    w = case["windows"]
    n = len(w["pwtt"])
    dmap = _rel(w["map"]) if "map" in w else np.zeros(n)
    return {
        "dpwtt": w["pwtt"] - w["pwtt"][0],
        "dpwtt_rel": _rel(w["pwtt"]),
        "dsi": _rel(w["si"]),
        "dri": _rel(w["ri"]),
        "dmap": dmap,
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


def fit_correction(cases: list[dict], m_ctrl: dict,
                   regressors: tuple[str, ...] = ("dsi", "dri")) -> dict:
    """導出foldで補正係数を推定（対照モデルの相対誤差 ~ 指定した説明変数）。

    regressors で説明変数を選ぶ:
      ("dsi","dri")        提案モデル（血管指標のみ）
      ("dmap",)            血圧のみ（SAP §7.3 の比較対照）
      ("dsi","dri","dmap") 血管指標＋血圧
    """
    X, y = [], []
    for c in cases:
        d = _deltas(c)
        est = predict_control(c, m_ctrl)
        resid = d["co_ref"] / np.clip(est, 1e-9, None) - 1.0
        X.append(np.column_stack([d[k] for k in regressors]))
        y.append(resid)
    X, y = np.vstack(X), np.concatenate(y)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return {"regressors": tuple(regressors),
            "coef": {k: float(v) for k, v in zip(regressors, coef)}}


def predict_proposed(case: dict, m_ctrl: dict, m_corr: dict) -> np.ndarray:
    d = _deltas(case)
    corr = 1.0
    for k, v in m_corr["coef"].items():
        corr = corr + v * d[k]
    return predict_control(case, m_ctrl) * np.clip(corr, 0.3, 3.0)


def premise_test(cases: list[dict], with_map: bool = True) -> dict:
    """SAP §7.1 前提検証: ΔPWTT は血管指標で説明されるか（参照COを使わない）。

    ΔPWTT%(t) ~ ΔΔT%(t) + ΔRI%(t) [+ ΔMAP%(t)] を全症例プールで回帰し、
    血管指標だけのモデルと切片のみのモデルの残差平方和から寄与を測る。
    返り値の r2_vasc が「血管指標で説明される ΔPWTT の割合」。
    """
    X, Xm, y = [], [], []
    for c in cases:
        d = _deltas(c)
        X.append(np.column_stack([d["dsi"], d["dri"]]))
        Xm.append(np.column_stack([d["dsi"], d["dri"], d["dmap"]]))
        y.append(d["dpwtt_rel"])
    y = np.concatenate(y)
    sst = float(np.sum((y - y.mean()) ** 2))

    def _r2(mat):
        M = np.vstack(mat)
        coef, *_ = np.linalg.lstsq(M, y, rcond=None)
        sse = float(np.sum((y - M @ coef) ** 2))
        return 1.0 - sse / max(sst, 1e-12), coef

    r2_v, coef_v = _r2(X)
    out = {"n_windows": int(y.size), "r2_vasc": r2_v,
           "beta_dsi": float(coef_v[0]), "beta_dri": float(coef_v[1])}
    if with_map:
        r2_vm, coef_vm = _r2(Xm)
        out.update({"r2_vasc_map": r2_vm, "beta_dsi_adj": float(coef_vm[0]),
                    "beta_dri_adj": float(coef_vm[1]), "beta_dmap": float(coef_vm[2])})
    return out


def crossval(cases: list[dict], n_folds: int = 5, seed: int = 0,
             regressors: tuple[str, ...] = ("dsi", "dri")) -> list[dict]:
    """症例単位k-fold。返り値: 症例ごとの {caseid, co_ref, est_ctrl, est_prop}（検証fold時の推定）。"""
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(cases))
    folds = [sorted(order[k::n_folds].tolist()) for k in range(n_folds)]
    out = []
    for k in range(n_folds):
        val_idx = set(folds[k])
        deriv = [c for j, c in enumerate(cases) if j not in val_idx]
        m_ctrl = fit_control(deriv)
        m_corr = fit_correction(deriv, m_ctrl, regressors=regressors)
        for j in sorted(val_idx):
            c = cases[j]
            out.append({
                "caseid": c["caseid"],
                "co_ref": c["windows"]["co_ref"],
                "est_ctrl": predict_control(c, m_ctrl),
                "est_prop": predict_proposed(c, m_ctrl, m_corr),
            })
    return out


def incremental_value(cases: list[dict], n_folds: int = 5, seed: int = 0) -> dict:
    """SAP §7.3: 血圧を超える増分価値があるか。

    参照COが FloTrac 系だと血圧変動と並行して動くため、血管指標による改善が
    「血圧の代理」でないことを示す必要がある。ΔMAP は血管指標と強く共線なので
    係数の生き残りでは判定できない（真の効果でも係数が割れる）。
    そこで **予測性能の増分** で判定する:

      対照            PWTT のみ
      +血圧           対照 + ΔMAP%
      +血管指標       対照 + ΔΔT%・ΔRI%          ← 提案
      +両方           対照 + ΔMAP% + ΔΔT%・ΔRI%

    「+両方」が「+血圧」より percentage error を下げるなら、血管指標は血圧を
    超える情報を持つ。下げないなら血圧の代理にすぎない。
    """
    from .stats import per_case_pe
    sets = {
        "対照": None,
        "+血圧": ("dmap",),
        "+血管指標": ("dsi", "dri"),
        "+両方": ("dsi", "dri", "dmap"),
    }
    out = {}
    for label, regs in sets.items():
        res = crossval(cases, n_folds=n_folds, seed=seed,
                       regressors=regs or ("dsi", "dri"))
        key = "est_ctrl" if regs is None else "est_prop"
        out[label] = float(np.median(per_case_pe(res, key)))
    out["血圧を超える増分"] = out["+血圧"] - out["+両方"]
    return out

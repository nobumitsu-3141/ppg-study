# -*- coding: utf-8 -*-
"""Pulse Decomposition Analysis (PDA) - skewed-Gaussian 2-kernel fit.

1拍のPPG波形を「前進波 + 反射波」の2つの skewed-Gaussian 成分に分解する。
スライド 5.2-5.3 / Basso 2024 (skewed-Gaussian), Fleischhauer 2020 (2カーネル) に準拠。

収束の検算（スライド 5.3「収束の検算」）:
  - boundary_stick : パラメータが境界に張り付いていないか
  - amp_zero       : 振幅ほぼゼロの成分が無いか（本数が多すぎるサイン）
  - reproducible   : 初期値を変えても同じ解に収束するか
  - valley_width   : 時間差を固定した残差プロファイルの谷の幅
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import least_squares
from scipy.special import erf

SQRT2 = np.sqrt(2.0)


def skew_gaussian(t: np.ndarray, a: float, mu: float, sigma: float, alpha: float) -> np.ndarray:
    """Skewed Gaussian (Azzalini型). alpha=0 で通常のGaussian。"""
    z = (t - mu) / sigma
    return a * np.exp(-0.5 * z * z) * (1.0 + erf(alpha * z / SQRT2))


def _unpack(p):
    a1, mu1, s1, al1, a2, dmu, s2, al2 = p
    return (a1, mu1, s1, al1), (a2, mu1 + dmu, s2, al2)


def model2(t: np.ndarray, p) -> np.ndarray:
    c1, c2 = _unpack(p)
    return skew_gaussian(t, *c1) + skew_gaussian(t, *c2)


def component_peak(comp, t0: float, t1: float, n: int = 4000):
    """成分波のピーク時刻と高さ（skew があるので数値的に求める）。"""
    tt = np.linspace(t0, t1, n)
    yy = skew_gaussian(tt, *comp)
    i = int(np.argmax(yy))
    return float(tt[i]), float(yy[i])


def fit_beat(
    t: np.ndarray,
    y: np.ndarray,
    n_starts: int = 8,
    dmu_bounds=(0.08, 0.60),
    alpha_bounds=(0.0, 8.0),
    seed: int = 0,
    compute_valley: bool = False,
) -> dict:
    """1拍を 2 kernel で当てはめ、収束検算つきで結果を返す。

    t: 拍先頭を 0 とした時刻 [s], y: PPG (拍内で足切り・detrend 済みを想定)
    alpha_bounds: 既定は正の skew のみ（前進波・反射波とも急峻な立ち上がり）。
                  これを緩めると DN-less 波形で振幅比の同定性が悪化する。
    compute_valley: 残差の谷幅を計算するか。ok 判定には使わない診断用の値で、
                  当てはめ回数がおよそ3倍になるため既定は False。
                  1症例あたり数千回当てはめる本解析では効いてくる。
    """
    t = np.asarray(t, float)
    y = np.asarray(y, float)
    T = float(t[-1] - t[0])
    y0 = y - float(np.min(y))  # モデルに定数項が無いので床を0に合わせる
    ymax = float(np.max(y0))
    if ymax <= 0:
        raise ValueError("beat has non-positive amplitude")
    ys = y0 / ymax  # 振幅正規化して当てはめ

    i_pk = int(np.argmax(ys))
    t_pk = float(t[i_pk])

    lo = np.array([0.05, 0.02, 0.015, alpha_bounds[0], 0.02, dmu_bounds[0], 0.015, alpha_bounds[0]])
    hi = np.array([2.50, max(0.60 * T, t_pk + 0.05), 0.30, alpha_bounds[1], 2.00, min(dmu_bounds[1], 0.85 * T), 0.35, alpha_bounds[1]])

    def resid(p):
        return model2(t, p) - ys

    # 反射波位置の初期値: 主ピーク後の -d²y/dt² 最小点（ランドマーク方式, スライド5.3-a）
    d2 = np.gradient(np.gradient(ys))
    j0 = i_pk + max(int(0.06 * len(t)), 3)
    j1 = int(0.85 * len(t))
    dmu0 = 0.22
    if j0 < j1:
        j = j0 + int(np.argmin(d2[j0:j1]))
        dmu0 = float(np.clip(t[j] - t_pk + 0.02, dmu_bounds[0] + 0.01, dmu_bounds[1] - 0.01))

    rng = np.random.default_rng(seed)
    base0 = np.array([1.0, max(t_pk - 0.02, 0.05), 0.06, 2.0, 0.45, dmu0, 0.09, 1.0])
    base0 = np.clip(base0, lo + 1e-6, hi - 1e-6)

    # 初期値: ランドマーク + dmu グリッド（異なる解の盆地を意図的に探索）+ ジッタ
    starts = [base0]
    for dg in (0.12, 0.18, 0.26, 0.36, 0.48):
        b = base0.copy()
        b[5] = np.clip(dg, lo[5] + 1e-6, hi[5] - 1e-6)
        starts.append(b)
    while len(starts) < max(n_starts, 6):
        starts.append(np.clip(
            base0 * rng.uniform(0.7, 1.3, size=8)
            + np.array([0, 0.02, 0, 0.5, 0, 0.05, 0, 0.5]) * rng.standard_normal(8),
            lo + 1e-6, hi - 1e-6,
        ))

    sols = []
    for x0 in starts:
        try:
            r = least_squares(resid, x0, bounds=(lo, hi), method="trf", max_nfev=4000)
            sols.append(r)
        except Exception:
            continue
    if not sols:
        raise RuntimeError("fit failed for all starts")

    # 解の選択: RSS最小を基本としつつ、ランドマーク近傍 (|dmu - dmu0| <= 0.06s) に
    # RSSが 1.10倍以内の解があればそちらを優先する（スライド5.3-a の事前情報を prior として使う）。
    gmin = min(sols, key=lambda r: r.cost)
    near = [r for r in sols if abs(r.x[5] - dmu0) <= 0.06 and r.cost <= gmin.cost * 1.10]
    best = min(near, key=lambda r: r.cost) if near else gmin
    p = best.x
    c1, c2 = _unpack(p)
    tp1, h1 = component_peak(c1, t[0], t[-1])
    tp2, h2 = component_peak(c2, t[0], t[-1])
    rss = float(2 * best.cost)
    nrmse = float(np.sqrt(np.mean((model2(t, p) - ys) ** 2)) / (np.max(ys) - np.min(ys)))

    # ---- 収束の検算 ----
    tol = 1e-3
    # alpha の下限 (=0, 対称ガウス) は正当な解なので境界判定から除外する
    lo_chk = np.abs(p - lo) < tol
    lo_chk[[3, 7]] = False
    boundary_stick = bool(np.any(lo_chk) or np.any(np.abs(p - hi) < tol))
    amp_zero = bool(min(h1, h2) < 0.02)
    # 曖昧さの検算: RSSがほぼ同等 (<=1.15倍) なのに dmu が離れた競合解があり、
    # かつその解の RI が大きく異なるなら「この拍では解が定まっていない」(スライド5.5)。
    def _ri_of(r):
        g1, g2 = _unpack(r.x)
        _, gh1 = component_peak(g1, t[0], t[-1])
        _, gh2 = component_peak(g2, t[0], t[-1])
        return gh2 / max(gh1, 1e-9)

    ri_best = _ri_of(best)
    competing = [r for r in sols
                 if r.cost <= best.cost * 1.15 and abs(r.x[5] - p[5]) > 0.03]
    ambiguous = any(abs(_ri_of(r) - ri_best) > 0.08 for r in competing)
    reproducible = not ambiguous

    # 残差の谷: dmu を固定してほかを再当てはめ、RSS(dmu) の谷幅（診断用・既定では計算しない）
    valley_width = float("nan")
    if compute_valley:
        grid = np.linspace(max(lo[5], p[5] - 0.15), min(hi[5], p[5] + 0.15), 13)
        prof = []
        for dfix in grid:
            def resid_fix(q):
                q8 = np.array([q[0], q[1], q[2], q[3], q[4], dfix, q[5], q[6]])
                return model2(t, q8) - ys
            q0 = np.delete(p, 5)
            qlo, qhi = np.delete(lo, 5), np.delete(hi, 5)
            try:
                rr = least_squares(resid_fix, np.clip(q0, qlo + 1e-6, qhi - 1e-6),
                                   bounds=(qlo, qhi), method="trf", max_nfev=1500)
                prof.append(2 * rr.cost)
            except Exception:
                prof.append(np.inf)
        prof = np.array(prof)
        thr = prof.min() * 1.05 + 1e-12
        valley_width = (float(grid[prof <= thr][-1] - grid[prof <= thr][0])
                        if np.any(prof <= thr) else float("nan"))

    return {
        "params": p,
        "scale": ymax,
        "components": [
            {"a": c1[0], "mu": c1[1], "sigma": c1[2], "alpha": c1[3], "t_peak": tp1, "height": h1 * ymax},
            {"a": c2[0], "mu": c2[1], "sigma": c2[2], "alpha": c2[3], "t_peak": tp2, "height": h2 * ymax},
        ],
        "rss": rss,
        "nrmse": nrmse,
        # valley_width_s は診断用に返すが ok 判定には使わない。
        # 別解に落ちた拍と正しい解の拍で 谷幅/ΔT がともに中央値 0.21 と重なり、
        # どこに閾値を置いても弁別できないことを合成データで確認した
        # （閾値0.40〜0.60 で正しい解 23/23 を保持する一方、誤った解も 16/17 が通過）。
        # 誤った解への防壁は前処理側の実効ノイズ管理（src/beats.required_ensemble_size）。
        "checks": {
            "boundary_stick": boundary_stick,
            "amp_zero": amp_zero,
            "reproducible": reproducible,
            "valley_width_s": valley_width,
        },
        "ok": (not boundary_stick) and (not amp_zero) and reproducible,
    }

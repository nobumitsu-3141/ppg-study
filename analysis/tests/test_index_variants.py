# -*- coding: utf-8 -*-
"""指標定義の候補比較（真値既知の合成データ・実データ不使用）。

SAP で「どの定義を主要指標に据えるか」を実データを見る前に凍結するための根拠。

比較する定義:
  時間側  dT_peak     成分波ピーク間（現行）
          dT_dmu      位置パラメータ μ の差
          dT_maxslope 最大傾き点の間
          dT_onset20  各成分の立ち上がり（自ピーク高の20%）間
          dT_onset10  同 10%
  振幅側  RI_peak     成分波ピーク高さ比（現行）
          RI_amp      振幅パラメータ比 a2/a1
          RI_area     成分波面積比

実行: analysis/ で  python3 -m tests.test_index_variants
"""
from __future__ import annotations

import numpy as np

from src.pda import fit_beat, skew_gaussian, component_peak
from src.synth import make_beat, PRESETS
from src.beats import ensemble_average

FS, T = 500.0, 0.9
TT = np.linspace(0.0, T, 6000)
KEYS = ["dT_peak", "dT_dmu", "dT_maxslope", "dT_onset20", "dT_onset10",
        "RI_peak", "RI_amp", "RI_area"]


def _onset_frac(comp, frac):
    y = skew_gaussian(TT, *comp)
    i_pk = int(np.argmax(y))
    idx = np.where(y[:i_pk + 1] >= frac * y[i_pk])[0]
    return float(TT[idx[0]]) if idx.size else float("nan")


def _onset_maxslope(comp):
    y = skew_gaussian(TT, *comp)
    i_pk = max(int(np.argmax(y)), 2)
    return float(TT[int(np.argmax(np.gradient(y, TT)[:i_pk]))])


def indices(c1, c2) -> dict:
    """成分波2本から候補指標をすべて計算する。"""
    tp1, h1 = component_peak(c1, 0.0, T)
    tp2, h2 = component_peak(c2, 0.0, T)
    ar = lambda c: float(np.trapezoid(np.clip(skew_gaussian(TT, *c), 0, None), TT))  # noqa: E731
    return {
        "dT_peak": tp2 - tp1,
        "dT_dmu": c2[1] - c1[1],
        "dT_maxslope": _onset_maxslope(c2) - _onset_maxslope(c1),
        "dT_onset20": _onset_frac(c2, 0.20) - _onset_frac(c1, 0.20),
        "dT_onset10": _onset_frac(c2, 0.10) - _onset_frac(c1, 0.10),
        "RI_peak": h2 / h1,
        "RI_amp": c2[0] / c1[0],
        "RI_area": ar(c2) / ar(c1),
    }


def _fitted(fit):
    c = fit["components"]
    return (tuple(c[0][k] for k in ("a", "mu", "sigma", "alpha")),
            tuple(c[1][k] for k in ("a", "mu", "sigma", "alpha")))


def _fit_ensemble(preset, noise, n_beats, seed0):
    beats = [make_beat(preset=preset, fs=FS, T=T, noise=noise, seed=seed0 + b)[1]
             for b in range(n_beats)]
    y = ensemble_average(beats)
    return fit_beat(np.arange(len(y)) / FS, y)


def _err(key, est, tv):
    return (est - tv) * 1000 if key.startswith("dT") else (est / tv - 1) * 100


def main() -> None:
    print("== 指標定義の候補比較（合成データ・真値既知） ==")

    # --- 1. 良好な条件では全定義が真値を復元する ---
    print("\n[1. 4拍アンサンブル・ノイズ1% ― 誤差中央値]")
    print(f"{'指標':<13}{'切痕あり':>12}{'DN-less':>12}")
    tbl = {}
    for preset in ("clear_notch", "dn_less"):
        truth = indices(*[tuple(c) for c in PRESETS[preset]])
        acc = {k: [] for k in KEYS}
        for e in range(8):
            try:
                f = _fit_ensemble(preset, 0.01, 4, 1000 * e)
            except Exception:
                continue
            est = indices(*_fitted(f))
            for k in KEYS:
                acc[k].append(_err(k, est[k], truth[k]))
        tbl[preset] = {k: float(np.median(acc[k])) for k in KEYS}
    for k in KEYS:
        u = "ms" if k.startswith("dT") else "%"
        print(f"{k:<13}{tbl['clear_notch'][k]:+9.1f}{u:>3}{tbl['dn_less'][k]:+9.1f}{u:>3}")
    worst = max(abs(tbl[p][k]) for p in tbl for k in KEYS if k.startswith("RI"))
    ok1 = worst < 5.0
    print(f"  -> 振幅側の最大誤差 {worst:.1f}%  {'PASS' if ok1 else 'FAIL'}（全定義が使用可能）")

    # --- 2. 同定性の限界では解が二峰化し、検算が素通りさせる ---
    print("\n[2. DN-less・ノイズ2%・4拍 ― 解の二峰性と誤差増幅]")
    truth = indices(*[tuple(c) for c in PRESETS["dn_less"]])
    ep, eo, er, okf = [], [], [], []
    for e in range(40):
        try:
            f = _fit_ensemble("dn_less", 0.02, 4, 7 * e * 97)
        except Exception:
            continue
        est = indices(*_fitted(f))
        ep.append(_err("dT_peak", est["dT_peak"], truth["dT_peak"]))
        eo.append(_err("dT_onset10", est["dT_onset10"], truth["dT_onset10"]))
        er.append(_err("RI_peak", est["RI_peak"], truth["RI_peak"]))
        okf.append(bool(f["ok"]))
    ep, eo, er, okf = map(np.asarray, (ep, eo, er, okf))
    good = np.abs(ep) < 10
    print(f"  正しい解に収束 {good.sum()}/{len(ep)} 拍（残りは別解＝二峰性、スライド5.5）")
    for label, m in (("正しい解", good), ("誤った解", ~good)):
        if m.sum() == 0:
            continue
        a_pk, a_on = np.median(np.abs(ep[m])), np.median(np.abs(eo[m]))
        print(f"  [{label:<5}] ΔT_peak {np.median(ep[m]):+6.1f}ms / "
              f"ΔT_onset10 {np.median(eo[m]):+6.1f}ms / RI_peak {np.median(er[m]):+5.1f}%"
              f" | 立ち上がり系の誤差増幅 {a_on / max(a_pk, 1e-9):.1f}倍"
              f" | 検算通過 {okf[m].sum()}/{m.sum()}")
    leak = int(okf[~good].sum())
    print(f"  -> 誤った解のうち収束検算を通過してしまうもの: {leak}/{int((~good).sum())}"
          f"  ★検算だけでは弾けない → 波形段階のSQIとアンサンブル拍数で担保する")

    # --- 3. 拍数を増やせば回復する ---
    print("\n[3. DN-less・ノイズ2% ― アンサンブル拍数と誤差中央値]")
    print(f"{'指標':<13}" + "".join(f"{f'{n}拍':>12}" for n in (4, 8, 16)))
    res = {}
    for n_beats in (4, 8, 16):
        acc = {k: [] for k in KEYS}
        for e in range(8):
            try:
                f = _fit_ensemble("dn_less", 0.02, n_beats, 10000 * e)
            except Exception:
                continue
            est = indices(*_fitted(f))
            for k in KEYS:
                acc[k].append(_err(k, est[k], truth[k]))
        res[n_beats] = {k: float(np.median(acc[k])) for k in KEYS}
    for k in KEYS:
        u = "ms" if k.startswith("dT") else "%"
        print(f"{k:<13}" + "".join(f"{res[n][k]:+9.1f}{u:>3}" for n in (4, 8, 16)))
    ok3 = abs(res[16]["dT_peak"]) < 3.0 and abs(res[16]["RI_peak"]) < 3.0
    print(f"  -> 16拍で ΔT_peak {res[16]['dT_peak']:+.1f}ms / RI_peak {res[16]['RI_peak']:+.1f}%"
          f"  {'PASS' if ok3 else 'FAIL'}（拍数で回復する）")

    if ok1 and ok3:
        print("\nALL PASS")
        print("帰結: 主要指標は ΔT_peak（＝身長を掛ければSI）と RI_peak（成分波ピーク高さ比）。")
        print("      立ち上がり間ΔTは上流誤差を4〜6倍に増幅するため副次・感度解析に置く。")
    else:
        print("\nSOME FAILED")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

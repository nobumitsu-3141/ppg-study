# -*- coding: utf-8 -*-
"""変種指標（立ち上がり間ΔT・面積比・3カーネル）の同定性を真値既知で確かめる。

11_variants_extract.py の派生指標計算が、真のパラメータから計算した値を
当てはめ経由でも復元できることの検証。実データ不使用。
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import importlib.util

_spec = importlib.util.spec_from_file_location(
    "var", Path(__file__).resolve().parent.parent / "scripts" / "11_variants_extract.py")
var = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(var)

from src.synth import make_beat            # noqa: E402
from src.pda import fit_beat, skew_gaussian  # noqa: E402

FS = 500.0


def truth_variants(comps, T):
    """真のパラメータから派生指標の真値を計算する。"""
    on1 = var._onset(tuple(comps[0]), 0.0, T)
    on2 = var._onset(tuple(comps[1]), 0.0, T)
    tt = np.linspace(0.0, T, 4000)
    a1 = float(np.trapezoid(skew_gaussian(tt, *comps[0]), tt))
    a2 = float(np.trapezoid(skew_gaussian(tt, *comps[1]), tt))
    return {"dt_onset": on2 - on1,
            "a_ratio": comps[1][0] / comps[0][0],
            "area_ratio": a2 / a1}


def main() -> None:
    n_ok = 0
    errs = {"dt_onset": [], "a_ratio": [], "area_ratio": [], "dt3": []}
    N = 20
    for i in range(N):
        T = 0.75 + 0.01 * i
        t, y, tr = make_beat(preset="clear_notch", fs=FS, T=T,
                             noise=0.003, drift=0.003, seed=3000 + i)
        fit = fit_beat(t, np.asarray(y, float), seed=i)
        if not fit.get("ok"):
            continue
        n_ok += 1
        v = var.variant_indices_from_fit(fit, t)
        tv = truth_variants(tr["comps"], T)
        errs["dt_onset"].append(1000 * (v["dt_onset"] - tv["dt_onset"]))
        errs["a_ratio"].append(100 * (v["a_ratio"] - tv["a_ratio"]) / tv["a_ratio"])
        errs["area_ratio"].append(100 * (v["area_ratio"] - tv["area_ratio"]) / tv["area_ratio"])
        f3 = var.fit_beat3(t, np.asarray(y, float), seed=i)
        if f3 is not None:
            errs["dt3"].append(1000 * (f3["dt3"] - tr["dt"]))

    print(f"2カーネル収束 {n_ok}/{N}, 3カーネル成立 {len(errs['dt3'])}/{n_ok}")
    med = {k: float(np.median(v)) if v else float("nan") for k, v in errs.items()}
    print(f"  dt_onset 誤差 中央値 {med['dt_onset']:+.1f} ms")
    print(f"  a_ratio  誤差 中央値 {med['a_ratio']:+.1f} %")
    print(f"  area比   誤差 中央値 {med['area_ratio']:+.1f} %")
    print(f"  dt3      誤差 中央値 {med['dt3']:+.1f} ms（2成分データへの3カーネル）")

    # 判定: 派生指標は当てはめ経由でも真値を大きく外さないこと。
    # 立ち上がり間ΔTは SAP §2.2 で「当てはめ誤差を4〜6倍に増幅」と記録した指標なので
    # 許容を緩くする（±15ms）。面積比・振幅比は±15%、3カーネルΔTは±20ms。
    ok = (abs(med["dt_onset"]) < 15 and abs(med["a_ratio"]) < 15
          and abs(med["area_ratio"]) < 15 and abs(med["dt3"]) < 20
          and n_ok >= 0.8 * N)
    print("ALL PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

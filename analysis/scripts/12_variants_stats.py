#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""変種抽出（11_variants_extract.py）の結果を集計し、主解析と比較する。

各変種について前提検証（ΔPWTT% ~ Δ指標%）と精度評価（対照 vs 補正）を
主解析と同じ機構（src.models）で再計算する。PWTT・HR・MAP・CO は
主解析キャッシュの値を (caseid, t0) で結合して使う。

使い方:
    python scripts/12_variants_stats.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import crossval, premise_test, premise_by_case  # noqa: E402
from src.stats import bootstrap_diff_ci, per_case_pe            # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
FEAT = DATA / "features"
VFEAT = DATA / "features_variants"
MIN_WINDOWS = 12

VARIANTS = [
    ("dt",      "ri",      "再現（主解析と同一定義・当てはめ再実行）"),
    ("dt_onset", "ri",     "立ち上がり間ΔT（20%規約）"),
    ("dt",      "a_ratio", "振幅パラメータ比 a2/a1"),
    ("dt",      "area_ratio", "成分波面積比"),
    ("dt3",     "ri3",     "3カーネルPDA"),
    ("dt_n2",   "ri_n2",   "ノイズ目標 0.002（厳格）"),
    ("dt_n4",   "ri_n4",   "ノイズ目標 0.004（緩和）"),
    ("dt_sqi5", "ri_sqi5", "SQI 同一値連続 <5%（厳格）"),
    ("dt_sqi20", "ri_sqi20", "SQI 同一値連続 <20%（緩和）"),
]


def load_joined() -> dict[int, pd.DataFrame]:
    demo = pd.read_csv(DATA / "cases.csv", encoding="utf-8-sig").set_index("caseid")
    out = {}
    for meta_p in sorted(VFEAT.glob("case_*_meta.json")):
        try:
            meta = json.loads(meta_p.read_text(encoding="utf-8"))
        except Exception:
            continue
        cid = meta["caseid"]
        vp, mp = VFEAT / f"case_{cid}.csv", FEAT / f"case_{cid}.csv"
        if not (vp.exists() and mp.exists()):
            continue
        try:
            v = pd.read_csv(vp)
            m = pd.read_csv(mp)
        except Exception:
            continue
        j = m.merge(v, on="t0", how="inner", suffixes=("", "_v"))
        if len(j) < MIN_WINDOWS or cid not in demo.index:
            continue
        h = float(demo["height"].get(cid, np.nan))
        if not np.isfinite(h) or h < 100:
            continue
        j.attrs["height_m"] = h / 100.0
        out[cid] = j
    return out


def build_cases(joined: dict, dt_col: str, ri_col: str) -> list[dict]:
    """変種の (ΔT, RI) で主解析と同じ形の症例辞書を作る。

    si は 身長/ΔT に組み直す（premise_test の回帰子 ΔSI% の定義を保つ）。
    変種が欠損のウィンドウは落とし、残り≥12の症例のみ採用する。
    """
    cases = []
    for cid, j in joined.items():
        need = ["pwtt", "hr", "map", "co_ref", dt_col, ri_col]
        d = j.dropna(subset=[c for c in need if c in j.columns])
        if len(d) < MIN_WINDOWS or dt_col not in d or ri_col not in d:
            continue
        dt = d[dt_col].to_numpy(float)
        if np.any(dt <= 0):
            keep = dt > 0
            d = d[keep]
            dt = dt[keep]
            if len(d) < MIN_WINDOWS:
                continue
        h = j.attrs["height_m"]
        cases.append({"caseid": cid, "height": h, "windows": {
            "pwtt": d["pwtt"].to_numpy(float),
            "si": h / dt,
            "ri": d[ri_col].to_numpy(float),
            "hr": d["hr"].to_numpy(float),
            "map": d["map"].to_numpy(float),
            "co_ref": d["co_ref"].to_numpy(float),
        }})
    return cases


def main() -> None:
    joined = load_joined()
    print(f"変種キャッシュあり: {len(joined)} 症例")
    if len(joined) < 10:
        print("11_variants_extract.py の完走後に実行してください。")
        return

    print("\n== 変種ごとの前提検証と精度（主解析と同じ機構で再計算） ==")
    print(f"{'変種':<30}{'症例':>5}{'r²':>8}{'βΔSI%':>9}{'βΔRI%':>9}"
          f"{'符号揃い':>7}{'ΔPE [95%CI]':>20}")
    print("-" * 92)
    for dt_col, ri_col, label in VARIANTS:
        cases = build_cases(joined, dt_col, ri_col)
        if len(cases) < 10:
            print(f"{label:<30}{len(cases):>5}   （症例不足）")
            continue
        pt = premise_test(cases, with_map=False)
        diag = premise_by_case(cases)
        res = crossval(cases)
        ci = bootstrap_diff_ci(res)
        print(f"{label:<30}{len(cases):>5}{pt['r2_vasc']:>8.3f}"
              f"{pt['beta_dsi']:>+9.3f}{pt['beta_dri']:>+9.3f}"
              f"{diag['sign_consistency']:>6.0%}"
              f"  {ci['diff_mean']:+.1f} [{ci['ci_low']:+.1f}, {ci['ci_high']:+.1f}]")

    print("\n読み方: どの変種でも r² が 0 近傍のままなら、主結論（前提の弱さ）は")
    print("        指標定義・カーネル数・前処理閾値の選択に依存しない。")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""追加の感度解析（キャッシュ済み特徴量のみで計算・再抽出不要）。

1. ウィンドウ長: 精度評価を60秒→5分→20分の集約で繰り返す。
   応答時間の異なるCOモニタの比較には20〜30分の移動平均が必要という指摘
   （Sugo & Ochiai 2025）への先回り。連続する有効ウィンドウを k 個ずつ
   平均して1ブロックとする（棄却による欠測は詰める。その旨を報告する）。
2. 心拍数交絡: 前提検証の回帰に ΔHR% を加え、血管指標の係数が変わるかを見る
   （Md Lazin 2020 の指摘への対応）。

位置づけ: SAP v0.3.1 に記載した探索的解析。主解析の定義には触れない。

使い方:
    python scripts/09_extra_sensitivity.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import _deltas, _rel, crossval, premise_test  # noqa: E402
from src.stats import bootstrap_diff_ci, per_case_pe          # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
FEAT = DATA / "features"
MIN_WINDOWS = 12
KEYS = ["pwtt", "si", "ri", "hr", "map", "co_ref"]


def load_cases() -> list[dict]:
    demo = pd.read_csv(DATA / "cases.csv", encoding="utf-8-sig").set_index("caseid")
    cases = []
    for meta_p in sorted(FEAT.glob("case_*_meta.json")):
        try:
            meta = json.loads(meta_p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if meta.get("v") != 3:
            continue
        cid = meta["caseid"]
        f = FEAT / f"case_{cid}.csv"
        if not f.exists():
            continue
        try:
            df = pd.read_csv(f)
        except Exception:
            continue
        if len(df) < MIN_WINDOWS or "si" not in df.columns:
            continue
        if cid not in demo.index:
            continue
        h = float(demo["height"].get(cid, np.nan))
        if not np.isfinite(h) or h < 100:
            continue
        cases.append({"caseid": cid, "height": h / 100.0,
                      "windows": {k: df[k].to_numpy(float) for k in KEYS}})
    return cases


def aggregate(case: dict, k: int) -> dict | None:
    """連続する有効ウィンドウ k 個ずつの平均で1ブロックを作る。

    採用は「較正1＋評価5以上」= 6ブロック以上（探索的解析のためここで固定）。
    棄却で生じた時間の飛びは詰める（真に連続な k 分ではない。本文に明記）。
    """
    w = case["windows"]
    n = len(w["pwtt"]) // k
    if n < 6:
        return None
    agg = {key: np.array([np.nanmean(w[key][i * k:(i + 1) * k]) for i in range(n)])
           for key in KEYS}
    return {"caseid": case["caseid"], "height": case["height"], "windows": agg}


def accuracy(cases: list[dict], label: str) -> None:
    res = crossval(cases)
    pe_c = per_case_pe(res, "est_ctrl")
    pe_p = per_case_pe(res, "est_prop")
    ci = bootstrap_diff_ci(res)
    print(f"  {label:14s} 症例 {len(cases):3d}  "
          f"PE 対照 {np.nanmedian(pe_c):5.1f}% / 提案 {np.nanmedian(pe_p):5.1f}%  "
          f"ΔPE {ci['diff_mean']:+.1f} [95%CI {ci['ci_low']:+.1f}, {ci['ci_high']:+.1f}]")


def main() -> None:
    cases = load_cases()
    print(f"キャッシュから {len(cases)} 症例を読み込み")
    if len(cases) < 10:
        print("症例不足。本解析の完走後に実行してください。")
        return

    print("\n== 感度解析A: 精度評価のウィンドウ長（60秒 / 5分 / 20分） ==")
    print("  ※ ブロックは連続する有効ウィンドウを詰めて平均（真の連続時間ではない）")
    accuracy(cases, "60秒(主解析)")
    for k, label in [(5, "5分ブロック"), (20, "20分ブロック")]:
        agg = [a for c in cases if (a := aggregate(c, k)) is not None]
        if len(agg) >= 10:
            accuracy(agg, label)
        else:
            print(f"  {label}: ブロック数を満たす症例が {len(agg)} 例で不足")

    print("\n== 感度解析B: 前提検証への ΔHR% の追加（心拍数交絡の確認） ==")
    pt0 = premise_test(cases, with_map=False)
    print(f"  基本形:      r² {pt0['r2_vasc']:.3f}  "
          f"β ΔSI% {pt0['beta_dsi']:+.3f} / ΔRI% {pt0['beta_dri']:+.3f}"
          f"  (n={pt0['n_windows']:,})")
    X, y = [], []
    for c in cases:
        d = _deltas(c)
        dhr = _rel(c["windows"]["hr"])
        X.append(np.column_stack([d["dsi"], d["dri"], dhr]))
        y.append(d["dpwtt_rel"])
    Xa, ya = np.vstack(X), np.concatenate(y)
    m = np.isfinite(ya) & np.isfinite(Xa).all(axis=1)
    Xa, ya = Xa[m], ya[m]
    coef, *_ = np.linalg.lstsq(Xa, ya, rcond=None)
    sse = float(np.sum((ya - Xa @ coef) ** 2))
    sst = float(np.sum((ya - ya.mean()) ** 2))
    print(f"  +ΔHR%:       r² {1 - sse / max(sst, 1e-12):.3f}  "
          f"β ΔSI% {coef[0]:+.3f} / ΔRI% {coef[1]:+.3f} / ΔHR% {coef[2]:+.3f}"
          f"  (n={m.sum():,})")
    print("  読み方: ΔHR%を加えても血管指標の係数がほぼ不変なら、心拍数交絡では")
    print("          説明されない（＝前提の弱さは心拍数のせいではない）")


if __name__ == "__main__":
    main()

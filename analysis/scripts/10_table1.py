#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""論文の表1（患者・手術・記録の特性）を採用症例から集計する。

キャッシュ済み特徴量（採用基準: 有効ウィンドウ≥12）と cases.csv を突き合わせる。
出力はそのまま原稿に写せる形式。連続量は中央値 (IQR)、カテゴリは n (%)。

使い方:
    python scripts/10_table1.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
FEAT = DATA / "features"
MIN_WINDOWS = 12


def adopted_cases() -> pd.DataFrame:
    rows = []
    for meta_p in sorted(FEAT.glob("case_*_meta.json")):
        try:
            meta = json.loads(meta_p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if meta.get("v") != 3:
            continue
        f = FEAT / f"case_{meta['caseid']}.csv"
        if not f.exists():
            continue
        try:
            n = len(pd.read_csv(f))
        except Exception:
            continue
        if n < MIN_WINDOWS:
            continue
        rows.append({"caseid": meta["caseid"], "n_windows": n,
                     "device": meta.get("device", "?"),
                     "duration_min": meta.get("duration_min", np.nan),
                     "pleth_lag_ms": meta.get("pleth_lag_ms", np.nan)})
    return pd.DataFrame(rows)


def miqr(s, fmt="{:.0f}") -> str:
    v = pd.to_numeric(s, errors="coerce").dropna()
    if len(v) == 0:
        return "—"
    return (fmt + " (" + fmt + "–" + fmt + ")").format(
        v.median(), v.quantile(.25), v.quantile(.75))


def npct(mask: pd.Series) -> str:
    n = int(mask.sum())
    return f"{n} ({100 * n / max(len(mask), 1):.0f}%)"


def main() -> None:
    ad = adopted_cases()
    demo = pd.read_csv(DATA / "cases.csv", encoding="utf-8-sig")
    d = demo.merge(ad, on="caseid", how="inner")
    print(f"採用症例: {len(d)}")
    if len(d) < 10:
        print("本解析の完走後に実行してください。")
        return

    print("\n=== 表1 患者・手術・記録の特性（採用症例） ===\n")
    print("【患者】")
    print(f"  年齢 [歳]           : {miqr(d['age'])}")
    sex = d["sex"].astype(str).str.upper()
    print(f"  男性                : {npct(sex == 'M')}")
    print(f"  身長 [cm]           : {miqr(d['height'])}")
    print(f"  体重 [kg]           : {miqr(d['weight'])}")
    print(f"  BMI [kg/m²]         : {miqr(d['bmi'], '{:.1f}')}")
    asa = pd.to_numeric(d["asa"], errors="coerce")
    for k in (1, 2, 3):
        print(f"  ASA {k}               : {npct(asa == k)}")
    print(f"  ASA ≥4              : {npct(asa >= 4)}")
    print(f"  高血圧の既往        : {npct(pd.to_numeric(d['preop_htn'], errors='coerce') == 1)}")
    print(f"  糖尿病の既往        : {npct(pd.to_numeric(d['preop_dm'], errors='coerce') == 1)}")

    print("\n【手術・麻酔】")
    print(f"  緊急手術            : {npct(pd.to_numeric(d['emop'], errors='coerce') == 1)}")
    for col, label in [("department", "診療科"), ("optype", "術式分類"), ("ane_type", "麻酔法")]:
        vc = d[col].astype(str).replace("nan", "不明").value_counts()
        print(f"  {label}（上位5）:")
        for name, n in vc.head(5).items():
            print(f"    {name:<28s}: {n} ({100 * n / len(d):.0f}%)")

    print("\n【記録・解析】")
    print(f"  記録長 [分]         : {miqr(d['duration_min'])}")
    print(f"  有効ウィンドウ数/例 : {miqr(d['n_windows'])}")
    print(f"  脈波チャネル遅延 [ms]: {miqr(d['pleth_lag_ms'])}")
    print(f"  参照CO装置:")
    for name, n in d["device"].value_counts().items():
        print(f"    {name:<10s}: {n} ({100 * n / len(d):.0f}%)")


if __name__ == "__main__":
    main()

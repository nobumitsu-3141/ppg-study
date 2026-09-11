#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""論文1 の表2・表4・表5 に残った未記入の値を埋める。

`docs/manuscript/03_tables_2to7.md` の `[[read from output]]` を消すための計算だけを行う。
**新しい解析ではない。**主解析と同じ関数・同じ規準・同じ乱数種を使い、既に確定している
数値（表2 の 1 行目、表4 の 1〜2 行目、表5 の 1〜2 行目）が再現することを併せて表示する。
再現しなければ入力が主解析と違うので、その旨を出して止める。

主解析と揃えてあるもの（ここがずれると値が 0.1 ポイント単位で動く）
------------------------------------------------------------------
* **症例の並び** … `src.cases.load_cached_cases`（= data/target_cases.csv の行順）。
  5-fold は乱数種 0 の置換で切るので、並びが変われば fold の割り付けが変わる。
  以前は data/features/ のファイル名順で並べていて、主解析と一致していなかった。
* **符号の揃い** … 症例内回帰は `src.models.premise_by_case` と同じ **切片あり**
  （設計行列 [1, ΔSI%, ΔRI%]）。心拍数を入れる行だけ ΔHR% を末尾に足す。
  心拍数なしの値が premise_by_case と一致するかを毎回検算する。
* **表4 と 16 例の行** … 主解析の `crossval(seed=0)` を 1 回だけ回し、その結果から
  行と症例を抜き出す。**16 例だけで学習し直すことはしない。**

埋める 11 箇所＋信頼区間
------------------------
表2  切片つきモデルの β ΔSI%・β ΔRI%（2 箇所）
     プール係数の 95% 信頼区間（事前指定の原点通過と切片つき、各 2 本）。
     回数・乱数種・区間の取り方は表4 の ΔPE と同じ（症例単位ブートストラップ
     2,000 回・種 0・百分位 2.5／97.5）。正規方程式を症例ごとに足し合わせるので、
     161,737 行を毎回当てはめ直さずに厳密に同じ推定量が出る
表4  「平均血圧を加えた」「血管指標＋平均血圧」の対照との差と 95% 信頼区間（2 箇所）
表5  5 分・20 分に集約したときのウィンドウ数（2 箇所）
     心拍数を投入した前提検証の符号の揃い（1 箇所）
     参照が動脈圧に依存しない 16 例の誤差率と差の向き（2 箇所）

2 台のどちらでも走る
--------------------
必要なのは `data/features/`（主解析の抽出結果）・`data/cases.csv`・`data/target_cases.csv`。
**主解析を回した機械にはこれがある。**無い機械では、何がどれだけ足りないかと、
持ってくる方法・作り直す方法を表示して止まる。ネットワークは要らない。

    python3 scripts/41_fill_tables.py --selftest   合成データで計算の筋道を検算する
    python3 scripts/41_fill_tables.py              表に入れる値を出す
    python3 scripts/41_fill_tables.py --json out.json   機械可読でも出す
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.cases import aggregate, load_cached_cases                      # noqa: E402
from src.models import (_deltas, _rel, crossval, premise_by_case,       # noqa: E402
                        premise_test)
from src.stats import bootstrap_diff_ci, per_case_pe, percentage_error  # noqa: E402

DATA = ROOT / "data"
FEAT = DATA / "features"
N_BOOT = 2000          # 表4 の脚注が指定する回数
SEED = 0               # 主解析と同じ

# 主解析で確定している値。ここが再現しなければ入力が違う
KNOWN = {
    "n_cases": 862, "n_windows": 161_737,
    "r2_origin": 0.000, "beta_dsi": -0.027, "beta_dri": -0.003,
    "r2_intercept": 0.044,
    "pe_ctrl": 26.9, "pe_prop": 27.2,
    "diff": 0.2, "ci_lo": 0.1, "ci_hi": 0.4,
    "pe_ctrl_map": 27.0, "pe_ctrl_vasc_map": 27.1,
    "r2_hr": 0.077, "beta_dsi_hr": -0.020,
    "sign_consistency": 78,
}
TOL = {"r2": 0.002, "beta": 0.002, "pe": 0.15, "diff": 0.05, "n_cases": 0}


# ---------------------------------------------------------------- 入力
# 症例の読み込みと集約は src/cases.py に置いた（09番と共用・主解析と同じ並び）。


def explain_missing() -> None:
    n_csv = len(list(FEAT.glob("case_*.csv"))) if FEAT.exists() else 0
    print("\n**主解析の抽出結果が足りない。**この機械では表を埋められない。\n")
    print(f"  data/features/            {n_csv} 症例分（{KNOWN['n_cases']} 例が要る）")
    for p in (DATA / "cases.csv", DATA / "target_cases.csv"):
        print(f"  {p.relative_to(ROOT).as_posix():25s} {'あり' if p.exists() else '★無し'}")
    print("\n方法1: 主解析を回した機械から持ってくる（数分。こちらが速い）")
    print("  主解析の機械で:")
    print("    tar czf ~/Desktop/features.tgz -C ~/ppg-study/analysis/data \\")
    print("      features cases.csv target_cases.csv")
    print("  この機械で（AirDrop などで受け取ったあと）:")
    print("    tar xzf ~/Desktop/features.tgz -C ~/ppg-study/analysis/data")
    print("\n方法2: この機械で抽出し直す（VitalDB への接続が要る。数時間）")
    print("    python3 scripts/00_download_lists.py")
    print("    python3 scripts/01_track_inventory.py")
    print("    python3 scripts/03_run_analysis.py --limit 900 --jobs 8")
    print("\n  vitaldb の版は requirements.txt で 1.5.8 に固定してある。")
    print("  1.7.2 では波形の再標本化が変わり、拍の型と脈波伝播時間が変わる。")


# ---------------------------------------------------------------- 計算
def premise_with_intercept(cases: list[dict]) -> dict:
    """表2 の「切片つき」の行。設計行列に定数列を足すだけで、他は premise_test と同じ。"""
    X, y = [], []
    for c in cases:
        d = _deltas(c)
        X.append(np.column_stack([np.ones(len(d["dsi"])), d["dsi"], d["dri"]]))
        y.append(d["dpwtt_rel"])
    X, y = np.vstack(X), np.concatenate(y)
    good = np.isfinite(y) & np.isfinite(X).all(axis=1)
    X, y = X[good], y[good]
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    # good で非有限を落としたあと。macOS の Accelerate では、ここで matmul の警告が
    # 出ることがある。値には出ていない（lab_log 追記105）
    sse = float(np.sum((y - X @ coef) ** 2))
    sst = float(np.sum((y - y.mean()) ** 2))
    return {"r2": 1.0 - sse / max(sst, 1e-12),
            "intercept": float(coef[0]), "beta_dsi": float(coef[1]), "beta_dri": float(coef[2]),
            "n_windows": int(y.size)}


def _normal_equations(cases: list[dict]) -> dict:
    """症例ごとに XᵀX と Xᵀy を作る。行の採否は `premise_test` と同じ。

    `premise_test` は ΔMAP% 列の有限性も含めて行を落とすので（血管指標だけの
    モデルでも落とす）、ここでも同じ `good` を使う。ここがずれると β が動く。
    """
    out = {"origin": [], "intercept": []}
    for c in cases:
        d = _deltas(c)
        y = d["dpwtt_rel"]
        X2 = np.column_stack([d["dsi"], d["dri"]])
        Xm = np.column_stack([d["dsi"], d["dri"], d["dmap"]])
        good = np.isfinite(y) & np.isfinite(X2).all(axis=1) & np.isfinite(Xm).all(axis=1)
        yg, Xo = y[good], X2[good]
        Xi = np.column_stack([np.ones(len(yg)), Xo])
        out["origin"].append((Xo.T @ Xo, Xo.T @ yg))
        out["intercept"].append((Xi.T @ Xi, Xi.T @ yg))
    return {k: (np.array([a for a, _ in v]), np.array([b for _, b in v]))
            for k, v in out.items()}


def _rows_used(cases: list[dict]) -> int:
    """`_normal_equations` が実際に使った行数。premise_test のウィンドウ数と一致するはず。"""
    n = 0
    for c in cases:
        d = _deltas(c)
        y = d["dpwtt_rel"]
        X2 = np.column_stack([d["dsi"], d["dri"]])
        Xm = np.column_stack([d["dsi"], d["dri"], d["dmap"]])
        n += int((np.isfinite(y) & np.isfinite(X2).all(axis=1)
                  & np.isfinite(Xm).all(axis=1)).sum())
    return n


def case_windows(cases: list[dict]) -> list[tuple]:
    """症例ごとの (caseid, キャッシュの生のウィンドウ数, 当てはめに使った行数)。

    2 台目の合計が確定値と 1 ウィンドウ食い違う。どの症例かは、主解析を回した機械で
    同じものを出して差分を取れば分かる。そのための出力であって、値の計算には使わない。
    """
    rows = []
    for c in cases:
        d = _deltas(c)
        y = d["dpwtt_rel"]
        X2 = np.column_stack([d["dsi"], d["dri"]])
        Xm = np.column_stack([d["dsi"], d["dri"], d["dmap"]])
        used = int((np.isfinite(y) & np.isfinite(X2).all(axis=1)
                    & np.isfinite(Xm).all(axis=1)).sum())
        rows.append((int(c["caseid"]), int(y.size), used))
    return rows


def _solve(A: np.ndarray, b: np.ndarray) -> np.ndarray:
    try:
        return np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        return np.linalg.lstsq(A, b, rcond=None)[0]


def pooled_beta_ci(cases: list[dict], n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """表2 のプール係数の 95% 信頼区間。症例単位ブートストラップ。

    回数・乱数種・区間の取り方は表4 の ΔPE と同じにする
    （`src.stats.bootstrap_diff_ci`: 復元抽出で症例数ぶん引き、百分位 2.5／97.5）。

    最小二乗の正規方程式は症例ごとに足し合わせられるので、症例を引き直して
    XᵀX と Xᵀy の和を取り直せば、161,737 行を毎回当てはめ直さずに厳密に同じ
    推定量が出る。全症例を 1 回ずつ足した点推定が `premise_test` の β と
    一致することを併せて返し、一致しなければ呼び出し側で止める。
    """
    eq = _normal_equations(cases)
    n = len(cases)
    rng = np.random.default_rng(seed)
    idx = [rng.integers(0, n, n) for _ in range(n_boot)]   # 両モデルで同じ引き直しを使う
    res: dict = {}
    for name, (A, b) in eq.items():
        point = _solve(A.sum(axis=0), b.sum(axis=0))
        boots = np.array([_solve(A[i].sum(axis=0), b[i].sum(axis=0)) for i in idx])
        lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
        res[name] = {"point": point, "lo": lo, "hi": hi,
                     "n_boot": n_boot, "seed": seed, "n_cases": n}
    return res


def sign_consistency(cases: list[dict], with_hr: bool) -> float:
    """症例内で係数が仮説と同じ向き（β ΔSI% が負）だった症例の割合。

    主解析の 78%（`src.models.premise_by_case`）と同じ求め方にする。設計行列は
    **切片つき** の [1, ΔSI%, ΔRI%]。心拍数を入れる行だけ ΔHR% を末尾に足す。
    有限な行が 8 未満の症例は premise_by_case と同じく飛ばし、切片の次の列
    （β ΔSI%）が負の症例を数える。

    以前はここだけ切片なしで回していたため 74%（主解析は 78%）になっていた。
    """
    n_ok = n_tot = 0
    for c in cases:
        d = _deltas(c)
        y = d["dpwtt_rel"]
        cols = [np.ones(len(y)), d["dsi"], d["dri"]]
        if with_hr:
            cols.append(_rel(c["windows"]["hr"]))
        X = np.column_stack(cols)
        m = np.isfinite(y) & np.isfinite(X).all(axis=1)
        if m.sum() < 8:
            continue
        coef, *_ = np.linalg.lstsq(X[m], y[m], rcond=None)
        n_tot += 1
        n_ok += int(coef[1] < 0)
    return 100.0 * n_ok / max(n_tot, 1)


def accuracy(cases: list[dict], regressors=("dsi", "dri"),
             res: list[dict] | None = None) -> dict:
    """交差検証 1 本ぶんの対照 PE・提案 PE・差と 95%CI。

    res を渡したときは回し直さない（表4 の 1 行目と 16 例の行は、主解析と同じ
    `crossval(cases, seed=0, regressors=("dsi","dri"))` の結果を使い回す）。
    """
    if res is None:
        res = crossval(cases, seed=SEED, regressors=regressors)
    ci = bootstrap_diff_ci(res, n_boot=N_BOOT, seed=SEED)
    return {"n_cases": len(cases),
            "pe_ctrl": float(np.nanmedian(per_case_pe(res, "est_ctrl"))),
            "pe_prop": float(np.nanmedian(per_case_pe(res, "est_prop"))),
            "diff": ci["diff_mean"], "lo": ci["ci_low"], "hi": ci["ci_high"]}


# ---------------------------------------------------------------- 出力
def near(a: float, b: float, tol: float) -> str:
    return "一致" if abs(a - b) <= tol else f"★ずれ {a - b:+.3f}"


def write_case_windows(cases: list[dict], path: Path) -> int:
    """症例別のウィンドウ数を CSV に落とす。合計も返す。"""
    rows = case_windows(cases)
    lines = ["caseid,windows_cached,rows_used"]
    lines += [f"{cid},{raw},{used}" for cid, raw, used in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    total = sum(used for _, _, used in rows)
    print(f"\n{path} に症例別のウィンドウ数を書き出した"
          f"（{len(rows)} 症例・当てはめに使った行の合計 {total:,}）")
    return total


def run(cases: list[dict], as_json: Path | None, table2_only: bool = False,
        case_windows_csv: Path | None = None) -> int:
    out: dict = {}
    bad = 0

    print("\n" + "=" * 74)
    print("確定値の再現（ここがずれたら入力が主解析と違う。表に写さないこと）")
    print("=" * 74)
    print(f"  症例数 {len(cases)}（確定 {KNOWN['n_cases']}）  "
          f"{near(len(cases), KNOWN['n_cases'], TOL['n_cases'])}")
    if len(cases) != KNOWN["n_cases"]:
        bad += 1

    pt = premise_test(cases, with_map=False)
    print(f"  表2 1行目 r² {pt['r2_vasc']:.3f}（確定 {KNOWN['r2_origin']:.3f}）  "
          f"{near(pt['r2_vasc'], KNOWN['r2_origin'], TOL['r2'])}")
    print(f"           β ΔSI% {pt['beta_dsi']:+.3f}（確定 {KNOWN['beta_dsi']:+.3f}）  "
          f"{near(pt['beta_dsi'], KNOWN['beta_dsi'], TOL['beta'])}")
    print(f"           ウィンドウ {pt['n_windows']:,}（確定 {KNOWN['n_windows']:,}）")
    if pt["n_windows"] != KNOWN["n_windows"]:
        print(f"           ※ {pt['n_windows'] - KNOWN['n_windows']:+d} ウィンドウの差は未解明。"
              f"bad には数えない")
        print(f"             どの症例かを出すには、この機械と主解析を回した機械の両方で")
        print(f"             --case-windows を付けて回し、出てきた 2 つの表の差を取る")
    for got, want, key in ((pt["r2_vasc"], KNOWN["r2_origin"], "r2"),
                           (pt["beta_dsi"], KNOWN["beta_dsi"], "beta")):
        if abs(got - want) > TOL[key]:
            bad += 1

    print("\n" + "=" * 74)
    print("表2  切片つきモデル（探索的）")
    print("=" * 74)
    pi = premise_with_intercept(cases)
    print(f"  r² {pi['r2']:.3f}（確定 {KNOWN['r2_intercept']:.3f}）  "
          f"{near(pi['r2'], KNOWN['r2_intercept'], TOL['r2'])}")
    if abs(pi["r2"] - KNOWN["r2_intercept"]) > TOL["r2"]:
        bad += 1
    print(f"\n  → 表に入れる:  β per ΔSI% = {pi['beta_dsi']:+.3f}   "
          f"β per ΔRI% = {pi['beta_dri']:+.3f}")
    out["table2_intercept"] = pi

    print("\n" + "=" * 74)
    print(f"表2  プール係数の 95%CI（症例単位ブートストラップ {N_BOOT:,} 回・種 {SEED}）")
    print("=" * 74)
    ci = pooled_beta_ci(cases)
    o, ii = ci["origin"], ci["intercept"]
    # 点推定が premise_test・premise_with_intercept と一致するか（正規方程式の足し算の検算）
    for got, want, lab in ((o["point"][0], pt["beta_dsi"], "原点通過 β ΔSI%"),
                           (o["point"][1], pt["beta_dri"], "原点通過 β ΔRI%"),
                           (ii["point"][1], pi["beta_dsi"], "切片つき β ΔSI%"),
                           (ii["point"][2], pi["beta_dri"], "切片つき β ΔRI%")):
        agree = abs(got - want) <= 1e-9
        print(f"  点推定の照合 {lab:18s} {got:+.6f} 対 {want:+.6f}  "
              f"{'一致' if agree else '★ずれ'}")
        if not agree:
            bad += 1
    # 4 桁で出す。β ΔRI% は 0.001 の桁なので 3 桁だと上限が「-0.000」になり、
    # 区間が 0 を含むのか含まないのかが読めない
    print(f"\n  → 表に入れる（事前指定・原点通過）:")
    print(f"       β per ΔSI% = {o['point'][0]:+.4f} "
          f"(95% CI {o['lo'][0]:+.4f} to {o['hi'][0]:+.4f})")
    print(f"       β per ΔRI% = {o['point'][1]:+.4f} "
          f"(95% CI {o['lo'][1]:+.4f} to {o['hi'][1]:+.4f})")
    print(f"  → 表に入れる（切片つき・探索的）:")
    print(f"       β per ΔSI% = {ii['point'][1]:+.4f} "
          f"(95% CI {ii['lo'][1]:+.4f} to {ii['hi'][1]:+.4f})")
    print(f"       β per ΔRI% = {ii['point'][2]:+.4f} "
          f"(95% CI {ii['lo'][2]:+.4f} to {ii['hi'][2]:+.4f})")
    for nm, lo, hi in (("原点通過 β ΔSI%", o["lo"][0], o["hi"][0]),
                       ("原点通過 β ΔRI%", o["lo"][1], o["hi"][1]),
                       ("切片つき β ΔSI%", ii["lo"][1], ii["hi"][1]),
                       ("切片つき β ΔRI%", ii["lo"][2], ii["hi"][2])):
        print(f"       {nm:16s} 区間は 0 を {'含む' if lo <= 0 <= hi else '含まない'}")
    print("  ※ 「ΔSI% のみ」「ΔHR% を加えた」の行の β は 41番では計算していない"
          "（09番の出力）。同じ要領で足せる")
    out["table2_ci"] = {
        k: {"beta_dsi": float(v["point"][0 if k == "origin" else 1]),
            "dsi_lo": float(v["lo"][0 if k == "origin" else 1]),
            "dsi_hi": float(v["hi"][0 if k == "origin" else 1]),
            "beta_dri": float(v["point"][1 if k == "origin" else 2]),
            "dri_lo": float(v["lo"][1 if k == "origin" else 2]),
            "dri_hi": float(v["hi"][1 if k == "origin" else 2]),
            "n_boot": v["n_boot"], "seed": v["seed"], "n_cases": v["n_cases"]}
        for k, v in ci.items()}

    if case_windows_csv:
        write_case_windows(cases, case_windows_csv)

    if table2_only:
        print("\n" + "=" * 74)
        print("--table2-only なので表4・表5 は出していない（交差検証を回していない）")
        print("=" * 74)
        if as_json:
            as_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"\n{as_json} に書き出した")
        return 1 if bad else 0

    print("\n" + "=" * 74)
    print(f"表4  対照との差（症例単位ブートストラップ {N_BOOT:,} 回・種 {SEED}）")
    print("=" * 74)
    out["table4"] = {}

    # 1 行目は主解析そのもの。ここで回した res を 16 例の行でも使い回す
    res_main = crossval(cases, seed=SEED, regressors=("dsi", "dri"))
    a1 = accuracy(cases, regressors=("dsi", "dri"), res=res_main)
    print(f"  {'Control (PWTT only)':44s} PE {a1['pe_ctrl']:.1f}%"
          f"  （確定 {KNOWN['pe_ctrl']:.1f}%  {near(a1['pe_ctrl'], KNOWN['pe_ctrl'], TOL['pe'])}）")
    print(f"  {'Proposed (vascular correction)':44s} PE {a1['pe_prop']:.1f}%"
          f"  （確定 {KNOWN['pe_prop']:.1f}%  {near(a1['pe_prop'], KNOWN['pe_prop'], TOL['pe'])}）")
    print(f"    差 {a1['diff']:+.1f} points (95% CI {a1['lo']:+.1f} to {a1['hi']:+.1f})"
          f"  （確定 {KNOWN['diff']:+.1f} [{KNOWN['ci_lo']:+.1f}, {KNOWN['ci_hi']:+.1f}]  "
          f"差 {near(a1['diff'], KNOWN['diff'], TOL['diff'])} / "
          f"下限 {near(a1['lo'], KNOWN['ci_lo'], TOL['diff'])} / "
          f"上限 {near(a1['hi'], KNOWN['ci_hi'], TOL['diff'])}）")
    for got, want in ((a1["pe_ctrl"], KNOWN["pe_ctrl"]), (a1["pe_prop"], KNOWN["pe_prop"])):
        if abs(got - want) > TOL["pe"]:
            bad += 1
    for got, want in ((a1["diff"], KNOWN["diff"]), (a1["lo"], KNOWN["ci_lo"]),
                      (a1["hi"], KNOWN["ci_hi"])):
        if abs(got - want) > TOL["diff"]:
            bad += 1
    out["table4"]["Control (PWTT only) / Proposed (vascular correction)"] = a1

    for label, reg, want_pe in (
            ("Control + mean arterial pressure", ("dmap",), KNOWN["pe_ctrl_map"]),
            ("Control + vascular + mean arterial pressure", ("dsi", "dri", "dmap"),
             KNOWN["pe_ctrl_vasc_map"])):
        a = accuracy(cases, regressors=reg)
        print(f"\n  {label:44s} PE 対照 {a['pe_ctrl']:.1f}% / 提案 {a['pe_prop']:.1f}%"
              f"  （提案の確定 {want_pe:.1f}%  {near(a['pe_prop'], want_pe, TOL['pe'])}）")
        if abs(a["pe_prop"] - want_pe) > TOL["pe"]:
            bad += 1
        print(f"    → 表に入れる:  {a['diff']:+.1f} points "
              f"(95% CI {a['lo']:+.1f} to {a['hi']:+.1f})")
        out["table4"][label] = a

    print("\n" + "=" * 74)
    print("表5  感度解析")
    print("=" * 74)
    out["table5"] = {}
    for k, label in ((5, "5 分に集約"), (20, "20 分に集約")):
        agg = [a for c in cases if (a := aggregate(c, k)) is not None]
        nw = sum(len(a["windows"]["pwtt"]) for a in agg)
        print(f"  {label}: 症例 {len(agg)}  → 表に入れる: ウィンドウ数 {nw:,}")
        out["table5"][f"agg{k}_windows"] = nw
        out["table5"][f"agg{k}_cases"] = len(agg)

    sc0 = sign_consistency(cases, with_hr=False)
    sc1 = sign_consistency(cases, with_hr=True)
    sc_ref = premise_by_case(cases)["sign_consistency"] * 100.0
    print(f"\n  符号の揃い  心拍数なし {sc0:.0f}%（確定 {KNOWN['sign_consistency']}%）  "
          f"{near(sc0, KNOWN['sign_consistency'], 1.0)}")
    print(f"    主解析 premise_by_case と突き合わせ: {sc0:.6f}% 対 {sc_ref:.6f}%  "
          f"{'一致' if abs(sc0 - sc_ref) <= 1e-9 else '★ずれ（切片の扱いが違う）'}")
    if abs(sc0 - sc_ref) > 1e-9:
        bad += 1
    if abs(sc0 - KNOWN["sign_consistency"]) > 1.0:
        bad += 1
    print(f"    → 表に入れる:  心拍数を投入したときの符号の揃い = {sc1:.0f}%")
    out["table5"]["sign_consistency_hr"] = sc1

    nonart_ids = {c["caseid"] for c in cases if c.get("device") in ("CardioQ", "Vigilance")}
    nonart_devs = sorted({str(c["device"]) for c in cases if c["caseid"] in nonart_ids})
    sub = [r for r in res_main if r["caseid"] in nonart_ids]
    print(f"\n  参照が動脈圧に依存しない症例: {len(sub)} 例 "
          f"（{', '.join(nonart_devs) or '該当なし'}）")
    print("    ※ 主解析の交差検証結果（表4 1 行目の res）から該当症例を抜き出すだけ。"
          "16 例だけで学習し直さない")
    if len(sub) >= 5:
        pc = float(np.nanmedian(per_case_pe(sub, "est_ctrl")))
        pp = float(np.nanmedian(per_case_pe(sub, "est_prop")))
        direction = "提案が悪い" if pp > pc else ("提案が良い" if pp < pc else "同じ")
        print(f"    → 表に入れる:  Percentage error, control / proposed = "
              f"{pc:.1f}% / {pp:.1f}%")
        print(f"    → 表に入れる:  Direction of the difference = "
              f"{direction}（{pp - pc:+.1f} points, descriptive only, no test）")
        out["table5"]["nonarterial"] = {"n": len(sub), "pe_ctrl": pc, "pe_prop": pp}
    else:
        print("    ★ 症例が少なすぎる。表の 16 例と合うか確かめること")
        bad += 1

    print("\n" + "=" * 74)
    if bad:
        print(f"★ 確定値の再現に {bad} 件のずれがある。**表には写さないこと。**")
        print("  入力が主解析と違う可能性が高い（症例集合・vitaldb の版・特徴量の作り直し）。")
    else:
        print("確定値はすべて再現した。上の「→ 表に入れる」の値を写してよい。")
    print("=" * 74)

    if as_json:
        as_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n{as_json} に書き出した")
    return 1 if bad else 0


# ---------------------------------------------------------------- 自己検査
def selftest() -> int:
    ok = True

    def rep(name, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))

    rng = np.random.default_rng(0)

    def synth(n_cases=40, n_win=30, beta=-0.30, noise=0.02):
        """ΔSI% が ΔPWTT% を beta で動かす合成集団。切片は 0。"""
        cs = []
        for i in range(n_cases):
            si = 1.0 + np.concatenate([[0.0], rng.normal(0, 0.10, n_win - 1)])
            ri = 1.0 + np.concatenate([[0.0], rng.normal(0, 0.10, n_win - 1)])
            hr = 70.0 + np.concatenate([[0.0], rng.normal(0, 5.0, n_win - 1)])
            dsi = (si - si[0]) / abs(si[0])
            pw = 200.0 * (1.0 + beta * dsi + rng.normal(0, noise, n_win))
            pw[0] = 200.0
            co = 5.0 + rng.normal(0, 0.4, n_win)
            cs.append({"caseid": i, "height": 1.65,
                       "windows": {"pwtt": pw, "si": si, "ri": ri, "hr": hr,
                                   "map": 80.0 + rng.normal(0, 5, n_win), "co_ref": co},
                       "device": "EV1000" if i % 3 else "CardioQ"})
        return cs

    cs = synth()
    rep("合成集団を作れる", len(cs) == 40 and len(cs[0]["windows"]["pwtt"]) == 30)

    pi = premise_with_intercept(cs)
    rep("切片つき回帰が仕込んだ係数を取り戻す",
        abs(pi["beta_dsi"] - (-0.30)) < 0.05, f"β ΔSI% {pi['beta_dsi']:+.3f}（仕込み −0.300）")
    rep("切片つきの切片がほぼ 0（相対変化なので）",
        abs(pi["intercept"]) < 0.02, f"切片 {pi['intercept']:+.4f}")
    pt = premise_test(cs, with_map=False)
    rep("切片つきの r² が原点通過の r² 以上",
        pi["r2"] >= pt["r2_vasc"] - 1e-9, f"{pi['r2']:.4f} ≥ {pt['r2_vasc']:.4f}")

    sc = sign_consistency(cs, with_hr=False)
    rep("仕込みが負なら符号の揃いが高い", sc > 90, f"{sc:.0f}%")
    cs_null = synth(beta=0.0, noise=0.20)
    sc_null = sign_consistency(cs_null, with_hr=False)
    rep("効果を消すと符号の揃いが五分に寄る", 30 < sc_null < 70, f"{sc_null:.0f}%")
    rep("心拍数を足しても揃いが壊れない",
        sign_consistency(cs, with_hr=True) > 90)

    # --- プール係数の 95%CI（症例単位ブートストラップ）---
    # 乱数の引き順を変えないよう、既に作ってある cs・cs_null をそのまま使う
    ci = pooled_beta_ci(cs, n_boot=200)          # 検算なので回数は落とす
    o, ii = ci["origin"], ci["intercept"]
    rep("点推定が premise_test の β と厳密に一致する（正規方程式の足し算）",
        abs(o["point"][0] - pt["beta_dsi"]) < 1e-9
        and abs(o["point"][1] - pt["beta_dri"]) < 1e-9,
        f"{o['point'][0]:+.6f} 対 {pt['beta_dsi']:+.6f}")
    rep("点推定が premise_with_intercept の β と厳密に一致する",
        abs(ii["point"][1] - pi["beta_dsi"]) < 1e-9
        and abs(ii["point"][2] - pi["beta_dri"]) < 1e-9,
        f"{ii['point'][1]:+.6f} 対 {pi['beta_dsi']:+.6f}")
    rep("信頼区間が点推定を含む",
        all(lo <= q <= hi for lo, q, hi in zip(o["lo"], o["point"], o["hi"])),
        f"β ΔSI% {o['lo'][0]:+.3f} 〜 {o['hi'][0]:+.3f}")
    rep("下限 < 上限", bool(np.all(o["lo"] < o["hi"]) and np.all(ii["lo"] < ii["hi"])))
    rep("仕込んだ −0.30 を原点通過の区間が覆う",
        o["lo"][0] <= -0.30 <= o["hi"][0], f"{o['lo'][0]:+.3f} 〜 {o['hi'][0]:+.3f}")
    # 「効果が無ければ区間が 0 をまたぐ」は、乱数の 1 引きでは検査にならない。
    # 95% 区間は真値を 20 回に 1 回は外すからで、実際 cs_null の 1 引きでは外れた
    # （点 +0.120・区間 +0.020〜+0.227）。そこで乱数を使わない集団で確かめる。
    # ΔPWTT% を ΔRI% だけで決め（係数 −0.30）、ΔSI% は無関係にする。
    import copy as _copy
    cs_dri = _copy.deepcopy(cs)
    for j, c in enumerate(cs_dri):
        w = c["windows"]
        dri = (w["ri"] - w["ri"][0]) / abs(w["ri"][0])
        k = np.arange(len(dri))
        w["pwtt"] = 200.0 * (1.0 - 0.30 * dri + 0.002 * np.sin(0.7 * k + j))
    cin = pooled_beta_ci(cs_dri, n_boot=200)["origin"]
    rep("ΔSI% が無関係な集団では β ΔSI% の区間が 0 をまたぐ",
        cin["lo"][0] <= 0.0 <= cin["hi"][0],
        f"{cin['lo'][0]:+.4f} 〜 {cin['hi'][0]:+.4f}（点 {cin['point'][0]:+.4f}）")
    rep("同じ集団で β ΔRI% の区間は仕込んだ −0.30 を覆う",
        cin["lo"][1] <= -0.30 <= cin["hi"][1],
        f"{cin['lo'][1]:+.4f} 〜 {cin['hi'][1]:+.4f}（点 {cin['point'][1]:+.4f}）")
    rep("回数を増やしても区間はほぼ動かない",
        abs(pooled_beta_ci(cs, n_boot=800)["origin"]["lo"][0] - o["lo"][0]) < 0.05)
    rep("既定の回数と乱数種が表の脚注どおり",
        pooled_beta_ci.__defaults__ == (N_BOOT, SEED) and (N_BOOT, SEED) == (2000, 0),
        f"{N_BOOT} 回・種 {SEED}")
    # 行の採否が premise_test と同じであること（ΔMAP% だけが欠測の行も落とす）
    import copy as _copy
    cs_nanmap = _copy.deepcopy(cs[:3])
    cs_nanmap[0]["windows"]["map"] = cs_nanmap[0]["windows"]["map"].copy()
    cs_nanmap[0]["windows"]["map"][5] = np.nan
    rows_before = int(_normal_equations(cs[:3])["origin"][0][0][0, 0] > 0) and \
        premise_test(cs[:3], with_map=False)["n_windows"]
    rows_after = premise_test(cs_nanmap, with_map=False)["n_windows"]
    A0 = _normal_equations(cs_nanmap)["origin"][0]
    rep("ΔMAP% だけが欠測の行も落ちる（premise_test と同じ扱い）",
        rows_after == rows_before - 1, f"{rows_before} → {rows_after} 行")
    rep("正規方程式の行数の合計が premise_test のウィンドウ数と一致する",
        int(round(sum(np.linalg.norm(a) > 0 for a in A0))) == 3
        and _rows_used(cs_nanmap) == rows_after,
        f"{_rows_used(cs_nanmap)} 対 {rows_after}")
    # 症例別のウィンドウ数（機械どうしの突き合わせ用の出力）
    cw = case_windows(cs_nanmap)
    rep("症例別のウィンドウ数が症例ごとに 1 行",
        len(cw) == len(cs_nanmap) and [r[0] for r in cw] == [c["caseid"] for c in cs_nanmap],
        f"{len(cw)} 行")
    rep("症例別の『使った行数』の合計が premise_test のウィンドウ数と一致する",
        sum(r[2] for r in cw) == rows_after, f"{sum(r[2] for r in cw)} 対 {rows_after}")
    rep("欠測のある症例だけ 生の数 > 使った行数 になる",
        cw[0][1] == cw[0][2] + 1 and all(r[1] == r[2] for r in cw[1:]),
        f"{[(r[1], r[2]) for r in cw]}")
    with tempfile.TemporaryDirectory() as td:
        csvp = Path(td) / "cw.csv"
        tot = write_case_windows(cs_nanmap, csvp)
        body = csvp.read_text(encoding="utf-8").splitlines()
        rep("CSV は見出し 1 行 + 症例数",
            body[0] == "caseid,windows_cached,rows_used"
            and len(body) == len(cs_nanmap) + 1 and tot == rows_after,
            f"{len(body)} 行・合計 {tot}")

    sc_ref = premise_by_case(cs)["sign_consistency"] * 100.0
    rep("符号の揃いが主解析 premise_by_case と一致する（切片あり）",
        abs(sc - sc_ref) < 1e-9, f"{sc:.6f}% 対 {sc_ref:.6f}%")

    a5 = [x for c in cs if (x := aggregate(c, 5)) is not None]
    rep("5 個ずつの集約でブロック数が 1/5 になる",
        a5 and len(a5[0]["windows"]["pwtt"]) == 6, f"{len(a5[0]['windows']['pwtt']) if a5 else 0} ブロック")
    rep("集約でブロックが 6 未満の症例は落ちる", aggregate(cs[0], 20) is None)
    rep("集約が装置の情報を保つ", a5[0].get("device") == cs[0]["device"])

    acc = accuracy(cs[:30])
    rep("精度評価が値を返す", np.isfinite(acc["pe_ctrl"]) and np.isfinite(acc["diff"]))
    rep("ブートストラップの信頼区間が差を挟む",
        acc["lo"] <= acc["diff"] <= acc["hi"],
        f"{acc['diff']:+.2f} [{acc['lo']:+.2f}, {acc['hi']:+.2f}]")
    a1 = accuracy(cs[:30]); a2 = accuracy(cs[:30])
    rep("同じ種で二度回すと同じ値（再現する）",
        a1 == a2, "種を固定しているので一致するはず")

    nonart = [c for c in cs if c.get("device") in ("CardioQ", "Vigilance")]
    rep("装置で絞り込める", 0 < len(nonart) < len(cs), f"{len(nonart)}/{len(cs)} 例")

    rep("確定値の表が主解析の数と一致している",
        KNOWN["n_cases"] == 862 and KNOWN["n_windows"] == 161_737)
    rep("ブートストラップ回数が表の脚注どおり 2,000", N_BOOT == 2000)
    rep("乱数種が主解析と同じ 0", SEED == 0)

    # --- 症例の並び: target_cases.csv の行順か（ファイル名順ではないか） ---
    from src import cases as cases_mod

    # 行順 7 → 100 → 20。ファイル名順なら 100 が先に来るので区別がつく
    plan = [(7, "EV1000", 170.0, 20), (100, "Vigileo", 165.0, 20),
            (20, "CardioQ", 158.0, 20), (3, None, 160.0, 20),
            (40, "EV1000", 80.0, 20), (55, "EV1000", 172.0, 5)]
    with tempfile.TemporaryDirectory() as td:
        data = Path(td)
        (data / "features").mkdir()
        tc_rows, demo_rows = [], []
        for cid, dev, h_cm, n_win in plan:
            row = {"caseid": cid}
            for d in ("Vigileo", "EV1000", "Vigilance", "CardioQ"):
                row[f"{d}_CO"] = (d == dev)
            tc_rows.append(row)
            demo_rows.append({"caseid": cid, "height": h_cm})
            pd.DataFrame({
                "t0": np.arange(n_win) * 60.0,
                "pwtt": 0.25 + 0.01 * rng.standard_normal(n_win),
                "si": 8.0 + rng.standard_normal(n_win),
                "ri": 0.5 + 0.05 * rng.standard_normal(n_win),
                "hr": 70.0 + 5 * rng.standard_normal(n_win),
                "map": 80.0 + 5 * rng.standard_normal(n_win),
                "co_ref": 5.0 + 0.3 * rng.standard_normal(n_win),
            }).to_csv(data / "features" / f"case_{cid}.csv", index=False)
        pd.DataFrame(tc_rows).to_csv(data / "target_cases.csv", index=False)
        pd.DataFrame(demo_rows).to_csv(data / "cases.csv", index=False, encoding="utf-8-sig")

        keep = (cases_mod.DATA, cases_mod.FEAT)
        try:
            cases_mod.DATA, cases_mod.FEAT = data, data / "features"
            got = cases_mod.load_cached_cases(verbose=False)
            got_ids = [c["caseid"] for c in got]
            got_devs = [c["device"] for c in got]
            lim_ids = [c["caseid"] for c in cases_mod.load_cached_cases(limit=2, verbose=False)]
            name_ids = [int(p.stem.split("_")[1])
                        for p in sorted((data / "features").glob("case_*.csv"))]
        finally:
            cases_mod.DATA, cases_mod.FEAT = keep

    rep("症例の並びが target_cases.csv の行順（ファイル名順ではない）",
        got_ids == [7, 100, 20] and name_ids[0] != got_ids[0],
        f"読み込み {got_ids} / ファイル名順なら {name_ids}")
    rep("装置なし・身長100cm未満・ウィンドウ不足の症例は落ちる",
        got_ids == [7, 100, 20], f"採用 {got_ids}（3・40・55 が落ちるはず）")
    rep("参照CO装置は pick_device が決める",
        got_devs == ["EV1000", "Vigileo", "CardioQ"], f"{got_devs}")
    rep("limit は先頭から数える", lim_ids == [7, 100], f"{lim_ids}")

    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true", help="合成データで計算の筋道を検算する")
    ap.add_argument("--json", type=str, default=None, help="値を JSON でも書き出す")
    ap.add_argument("--case-windows", type=str, default=None,
                    help="症例別のウィンドウ数を CSV に書き出す"
                         "（機械どうしでウィンドウ数が食い違うときの突き合わせ用）")
    ap.add_argument("--table2-only", action="store_true",
                    help="表2 と信頼区間だけ出す（交差検証を回さないので短い）")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())

    missing = [p for p in (FEAT, DATA / "cases.csv", DATA / "target_cases.csv") if not p.exists()]
    if missing or len(list(FEAT.glob("case_*.csv"))) < 100:
        explain_missing()
        sys.exit(2)

    cases = load_cached_cases()
    if len(cases) < 100:
        explain_missing()
        sys.exit(2)
    sys.exit(run(cases, Path(args.json) if args.json else None,
                 table2_only=args.table2_only,
                 case_windows_csv=Path(args.case_windows) if args.case_windows else None))


if __name__ == "__main__":
    main()

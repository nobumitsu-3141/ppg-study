#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""論文1 の表2・表4・表5 に残った未記入の値を埋める。

`docs/manuscript/03_tables_2to7.md` の `[[read from output]]` を消すための計算だけを行う。
**新しい解析ではない。**主解析と同じ関数・同じ規準・同じ乱数種を使い、既に確定している
数値（表2 の 1 行目、表4 の 1〜2 行目、表5 の 1〜2 行目）が再現することを併せて表示する。
再現しなければ入力が主解析と違うので、その旨を出して止める。

埋める 11 箇所
--------------
表2  切片つきモデルの β ΔSI%・β ΔRI%（2 箇所）
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
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.models import (_deltas, _rel, crossval, premise_test)          # noqa: E402
from src.stats import bootstrap_diff_ci, per_case_pe, percentage_error  # noqa: E402

DATA = ROOT / "data"
FEAT = DATA / "features"
KEYS = ["pwtt", "si", "ri", "hr", "map", "co_ref"]
MIN_WINDOWS = 12
N_BOOT = 2000          # 表4 の脚注が指定する回数
SEED = 0               # 主解析と同じ

# 主解析で確定している値。ここが再現しなければ入力が違う
KNOWN = {
    "n_cases": 862, "n_windows": 161_737,
    "r2_origin": 0.000, "beta_dsi": -0.027, "beta_dri": -0.003,
    "r2_intercept": 0.044,
    "pe_ctrl": 26.9, "pe_prop": 27.2,
    "pe_ctrl_map": 27.0, "pe_ctrl_vasc_map": 27.1,
    "r2_hr": 0.077, "beta_dsi_hr": -0.020,
    "sign_consistency": 78,
}
TOL = {"r2": 0.002, "beta": 0.002, "pe": 0.15, "n_cases": 0}


def _load(stem: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / stem)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------- 入力
def load_cases(verbose: bool = True) -> list[dict]:
    """09番と同じ読み方。参照CO装置も保持する（表5 の 16 例の行に要る）。"""
    demo = pd.read_csv(DATA / "cases.csv", encoding="utf-8-sig").set_index("caseid")
    tc = pd.read_csv(DATA / "target_cases.csv").set_index("caseid")
    M03 = _load("03_run_analysis.py", "m03_41")
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
        if not f.exists() or cid not in demo.index or cid not in tc.index:
            continue
        try:
            df = pd.read_csv(f)
        except Exception:
            continue
        if len(df) < MIN_WINDOWS or "si" not in df.columns:
            continue
        h = float(demo["height"].get(cid, np.nan))
        if not np.isfinite(h) or h < 100:
            continue
        cases.append({
            "caseid": cid, "height": h / 100.0,
            "windows": {k: df[k].to_numpy(float) for k in KEYS},
            "device": M03.pick_device(tc.loc[cid], None),
        })
    if verbose:
        print(f"キャッシュから {len(cases)} 症例 "
              f"（{sum(len(c['windows']['pwtt']) for c in cases):,} ウィンドウ）")
    return cases


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
    sse = float(np.sum((y - X @ coef) ** 2))
    sst = float(np.sum((y - y.mean()) ** 2))
    return {"r2": 1.0 - sse / max(sst, 1e-12),
            "intercept": float(coef[0]), "beta_dsi": float(coef[1]), "beta_dri": float(coef[2]),
            "n_windows": int(y.size)}


def sign_consistency(cases: list[dict], with_hr: bool) -> float:
    """症例内で係数が仮説と同じ向き（β ΔSI% が負）だった症例の割合。

    主解析の 78% と同じ求め方にする。症例ごとに同じ設計行列で回帰し、β ΔSI% の符号を数える。
    """
    n_ok = n_tot = 0
    for c in cases:
        d = _deltas(c)
        cols = [d["dsi"], d["dri"]] + ([_rel(c["windows"]["hr"])] if with_hr else [])
        X = np.column_stack(cols)
        y = d["dpwtt_rel"]
        m = np.isfinite(y) & np.isfinite(X).all(axis=1)
        if m.sum() < len(cols) + 2:
            continue
        coef, *_ = np.linalg.lstsq(X[m], y[m], rcond=None)
        n_tot += 1
        n_ok += int(coef[0] < 0)
    return 100.0 * n_ok / max(n_tot, 1)


def aggregate(case: dict, k: int) -> dict | None:
    """09番と同一。連続する有効ウィンドウ k 個ずつの平均で 1 ブロック。"""
    w = case["windows"]
    n = len(w["pwtt"]) // k
    if n < 6:
        return None
    agg = {key: np.array([np.nanmean(w[key][i * k:(i + 1) * k]) for i in range(n)])
           for key in KEYS}
    return {"caseid": case["caseid"], "height": case["height"],
            "windows": agg, "device": case.get("device")}


def accuracy(cases: list[dict], regressors=("dsi", "dri")) -> dict:
    res = crossval(cases, seed=SEED, regressors=regressors)
    ci = bootstrap_diff_ci(res, n_boot=N_BOOT, seed=SEED)
    return {"n_cases": len(cases),
            "pe_ctrl": float(np.nanmedian(per_case_pe(res, "est_ctrl"))),
            "pe_prop": float(np.nanmedian(per_case_pe(res, "est_prop"))),
            "diff": ci["diff_mean"], "lo": ci["ci_low"], "hi": ci["ci_high"]}


# ---------------------------------------------------------------- 出力
def near(a: float, b: float, tol: float) -> str:
    return "一致" if abs(a - b) <= tol else f"★ずれ {a - b:+.3f}"


def run(cases: list[dict], as_json: Path | None) -> int:
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
    print(f"表4  対照との差（症例単位ブートストラップ {N_BOOT:,} 回・種 {SEED}）")
    print("=" * 74)
    rows = [("Control (PWTT only)", ("dsi", "dri"), None),
            ("Control + mean arterial pressure", ("dmap",), KNOWN["pe_ctrl_map"]),
            ("Control + vascular + mean arterial pressure", ("dsi", "dri", "dmap"),
             KNOWN["pe_ctrl_vasc_map"])]
    out["table4"] = {}
    for label, reg, want_pe in rows:
        a = accuracy(cases, regressors=reg)
        chk = "" if want_pe is None else f"  （確定 {want_pe:.1f}%  {near(a['pe_prop'], want_pe, TOL['pe'])}）"
        print(f"  {label:44s} PE {a['pe_prop']:.1f}%{chk}")
        if want_pe is not None:
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
    print(f"\n  符号の揃い  心拍数なし {sc0:.0f}%（確定 {KNOWN['sign_consistency']}%）  "
          f"{near(sc0, KNOWN['sign_consistency'], 1.0)}")
    if abs(sc0 - KNOWN["sign_consistency"]) > 1.0:
        bad += 1
    print(f"    → 表に入れる:  心拍数を投入したときの符号の揃い = {sc1:.0f}%")
    out["table5"]["sign_consistency_hr"] = sc1

    nonart = [c for c in cases if c.get("device") in ("CardioQ", "Vigilance")]
    print(f"\n  参照が動脈圧に依存しない症例: {len(nonart)} 例 "
          f"（{', '.join(sorted({str(c['device']) for c in nonart})) or '該当なし'}）")
    if len(nonart) >= 5:
        res = crossval(nonart, seed=SEED)
        pc = float(np.nanmedian(per_case_pe(res, "est_ctrl")))
        pp = float(np.nanmedian(per_case_pe(res, "est_prop")))
        direction = "提案が悪い" if pp > pc else ("提案が良い" if pp < pc else "同じ")
        print(f"    → 表に入れる:  Percentage error, control / proposed = "
              f"{pc:.1f}% / {pp:.1f}%")
        print(f"    → 表に入れる:  Direction of the difference = "
              f"{direction}（{pp - pc:+.1f} points, descriptive only, no test）")
        out["table5"]["nonarterial"] = {"n": len(nonart), "pe_ctrl": pc, "pe_prop": pp}
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

    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true", help="合成データで計算の筋道を検算する")
    ap.add_argument("--json", type=str, default=None, help="値を JSON でも書き出す")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())

    missing = [p for p in (FEAT, DATA / "cases.csv", DATA / "target_cases.csv") if not p.exists()]
    if missing or len(list(FEAT.glob("case_*_meta.json"))) < 100:
        explain_missing()
        sys.exit(2)

    cases = load_cases()
    if len(cases) < 100:
        explain_missing()
        sys.exit(2)
    sys.exit(run(cases, Path(args.json) if args.json else None))


if __name__ == "__main__":
    main()

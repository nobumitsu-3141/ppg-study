#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""研究1b B-1: PWTT を分解し、陰性が前駆出期に隠されていないかを検証する。

問題意識
--------
研究1は「血管指標は症例内の ΔPWTT をほとんど説明しない」で終わった。しかしここには
解釈上の落とし穴がある。

    PWTT = 前駆出期（PEP） + 動脈伝播時間（ATT）

両者が逆向きに動けば互いを打ち消し、ΔPWTT は変化しない。**血管指標が動脈成分を
正しく測っていても、陰性に見えうる。** すなわち研究1が示したのは「血管指標は ΔPWTT を
説明しない」であって「血管指標は動脈伝播時間を測れていない」ではない。

分解
----
    T1      = R波 → 橈骨動脈圧の立ち上がり   = PEP + 中枢の動脈伝播
    T2      = R波 → 指尖PPGの立ち上がり      = PEP + 中枢 + 末梢 + 装置遅延
    T2 − T1 = 橈骨→指尖の伝播時間            = 末梢動脈区間（**PEPを含まない**）

装置遅延は症例内で定数なので、症例内の変化量をとれば相殺される。

問うこと
--------
  Q1（最優先）  Δ(T2−T1) と ΔT は関連するか
                関連すれば、血管指標は動脈成分を正しく測れていたことになり、
                研究1の陰性は前駆出期による見かけのものだったと確定する
  Q2            ΔPWTT のうち Δ(T2−T1) が説明するのは何%か
                ごく一部なら PWTT の変動は PEP と中枢側が支配していると直接示せる
  Q3（参考）    動脈圧由来の指標（τ=RC・dP/dt_max）で ΔPWTT を説明できるか
                動脈圧は利得制御を経ないため、PPGの測定限界か概念の限界かを切り分ける

いずれも参照心拍出量を用いない。

前提
----
`scripts/03_run_analysis.py`（data/features/）と `scripts/15_art_indices.py`
（data/features_art/）が完走していること。

使い方
------
    python scripts/21_pwtt_decomposition.py
    python scripts/21_pwtt_decomposition.py --selftest
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DATA = Path(__file__).resolve().parent.parent / "data"
FEAT = DATA / "features"
AFEAT = DATA / "features_art"

MIN_WIN = 12          # 症例採用に必要な有効ウィンドウ数（主解析と同じ）
GATE_AC = 0.30        # 可測性ゲート: 窓間自己相関の下限
GATE_CV = 0.50        # 可測性ゲート: 症例内変動係数の上限


# ---------------------------------------------------------------- 部品
def _rel(x: np.ndarray) -> np.ndarray:
    """初回値からの相対変化。分母の床は主解析（src.models._rel）と同じ規約。"""
    x = np.asarray(x, float)
    scale = float(np.nanmedian(np.abs(x)))
    denom = max(abs(float(x[0])), 0.05 * scale, 1e-9)
    return (x - x[0]) / denom


def _ac1(x: np.ndarray) -> float:
    """1次自己相関。測定ノイズが支配する系列では0近傍になる。"""
    x = np.asarray(x, float)
    g = np.isfinite(x)
    x = x[g]
    if x.size < 8 or np.ptp(x) == 0:
        return float("nan")
    a, b = x[:-1], x[1:]
    return float(np.corrcoef(a, b)[0, 1])


def _spearman(x, y) -> float:
    from scipy.stats import rankdata
    x, y = np.asarray(x, float), np.asarray(y, float)
    g = np.isfinite(x) & np.isfinite(y)
    if g.sum() < 8 or np.ptp(x[g]) == 0 or np.ptp(y[g]) == 0:
        return float("nan")
    return float(np.corrcoef(rankdata(x[g]), rankdata(y[g]))[0, 1])


def _r2_origin(y: np.ndarray, X: list[np.ndarray]) -> tuple[float, np.ndarray]:
    """原点を通す当てはめ。主解析（src.models.premise_test）と同じ規約。"""
    M = np.column_stack(X)
    g = np.isfinite(y) & np.isfinite(M).all(axis=1)
    if g.sum() < 30:
        return float("nan"), np.full(len(X), np.nan)
    y2, M2 = y[g], M[g]
    coef, *_ = np.linalg.lstsq(M2, y2, rcond=None)
    sse = float(np.sum((y2 - M2 @ coef) ** 2))
    sst = float(np.sum((y2 - y2.mean()) ** 2))
    return 1.0 - sse / max(sst, 1e-12), coef


def _drift(x: np.ndarray) -> float:
    """系列の系統的な傾き（正規化）。装置遅延が症例内で漂っていないかの代理。"""
    x = np.asarray(x, float)
    g = np.isfinite(x)
    if g.sum() < 10:
        return float("nan")
    t = np.arange(x.size)[g]
    v = x[g]
    b = np.polyfit(t, v, 1)[0]
    return float(b * (t[-1] - t[0]) / max(abs(np.median(v)), 1e-9))


# ---------------------------------------------------------------- 症例
def case_frame(caseid: int):
    """主解析と動脈圧指標を t0 で結合し、症例内の変化量を作る。"""
    import pandas as pd
    try:
        m = pd.read_csv(FEAT / f"case_{caseid}.csv")
        a = pd.read_csv(AFEAT / f"case_{caseid}.csv")
    except Exception:
        return None
    d = m.merge(a, on="t0", how="inner").sort_values("t0").reset_index(drop=True)
    d = d[np.isfinite(d["t1_ms"]) & np.isfinite(d["pwtt"]) & np.isfinite(d["si"])]
    if len(d) < MIN_WIN:
        return None

    t2 = d["pwtt"].to_numpy(float) * 1000.0        # ms（装置遅延を含む）
    t1 = d["t1_ms"].to_numpy(float)                # ms
    per = t2 - t1                                  # 末梢動脈区間（＋定数の装置遅延）
    si = d["si"].to_numpy(float)

    out = {"caseid": caseid, "n": len(d),
           "t1_med": float(np.median(t1)), "per_med": float(np.median(per)),
           "t2_med": float(np.median(t2))}
    # ΔT は SI の逆数に比例する。症例内では身長が約分されるので相対変化は厳密に求まる
    out["d_dt"] = si[0] / si - 1.0
    out["d_pwtt"] = _rel(t2)
    out["d_per"] = _rel(per)
    out["d_t1"] = _rel(t1)
    out["d_ri"] = _rel(d["ri"].to_numpy(float))
    out["d_tau"] = _rel(d["tau_ms"].to_numpy(float)) if "tau_ms" in d else np.full(len(d), np.nan)
    out["d_dpdt"] = _rel(d["dpdt_max"].to_numpy(float)) if "dpdt_max" in d else np.full(len(d), np.nan)
    out["d_map"] = _rel(d["map"].to_numpy(float)) if "map" in d else np.full(len(d), np.nan)

    # 可測性
    out["ac_per"] = _ac1(per)
    out["ac_t1"] = _ac1(t1)
    out["cv_per"] = float(np.nanstd(per) / max(abs(np.nanmedian(per)), 1e-9))
    out["drift_per"] = _drift(per)
    # Q1: 症例内での関連
    out["rho_per_dt"] = _spearman(out["d_per"], out["d_dt"])
    out["rho_pwtt_dt"] = _spearman(out["d_pwtt"], out["d_dt"])
    return out


# ---------------------------------------------------------------- 報告
def report(cases: list[dict]) -> None:
    import pandas as pd
    if not cases:
        print("結合できた症例がありません。03 と 15 が完走しているか確認してください。")
        return
    df = pd.DataFrame([{k: v for k, v in c.items() if not isinstance(v, np.ndarray)}
                       for c in cases])
    n_case = len(df)
    n_win = int(df["n"].sum())

    print(f"\n{'='*72}\n研究1b B-1: PWTT の分解（PEPを含まない末梢動脈区間）\n{'='*72}")
    print(f"\n{n_case} 症例 / {n_win:,} ウィンドウ")

    # ---- 健全性: T1 は生理的な範囲か ----
    t1m = df["t1_med"].to_numpy(float)
    lo, hi = np.percentile(t1m, [25, 75])
    print(f"\n-- 測定の健全性 --")
    print(f"  T1（R波→橈骨動脈圧立ち上がり）  中央値 {np.median(t1m):.0f} ms [IQR {lo:.0f}–{hi:.0f}]")
    if 100 <= np.median(t1m) <= 300:
        print("     生理的な想定帯（PEP 約80–120 ms ＋ 大動脈→橈骨 約60–100 ms）の中")
    else:
        print("     ** 想定帯の外。動脈圧チャネルにも装置遅延がある可能性を疑うこと **")
    perm = df["per_med"].to_numpy(float)
    print(f"  T2−T1（末梢区間＋装置遅延）      中央値 {np.median(perm):.0f} ms"
          f" [IQR {np.percentile(perm,25):.0f}–{np.percentile(perm,75):.0f}]")
    print(f"     ※ 装置遅延（中央値660 ms）を含むため絶対値は解釈しない。症例内Δのみ使う")

    # ---- 可測性ゲート ----
    ac = float(np.nanmedian(df["ac_per"]))
    cv = float(np.nanmedian(df["cv_per"]))
    dr = float(np.nanmedian(np.abs(df["drift_per"])))
    print(f"\n-- 可測性ゲート（事前指定）--")
    print(f"  Δ(T2−T1) の窓間自己相関  中央値 {ac:+.3f}   要 ≥ {GATE_AC}   "
          f"{'通過' if ac >= GATE_AC else '不通過'}")
    print(f"  T2−T1 の症例内変動係数    中央値 {cv:.3f}   要 ≤ {GATE_CV}   "
          f"{'通過' if cv <= GATE_CV else '不通過'}")
    print(f"  T2−T1 の症例内ドリフト    中央値 {dr:.3f}（相対）")
    gate = (ac >= GATE_AC) and (cv <= GATE_CV)
    if not gate:
        print("\n  ** ゲート不通過。以下の結果は参考値として読むこと **")
        print("     橈骨→指尖は伝播30〜50 msの短区間であり、ノイズに埋もれた可能性がある")

    # ---- Q2: ΔPWTT の内訳 ----
    d_pwtt = np.concatenate([c["d_pwtt"] for c in cases])
    d_per = np.concatenate([c["d_per"] for c in cases])
    d_t1 = np.concatenate([c["d_t1"] for c in cases])
    d_dt = np.concatenate([c["d_dt"] for c in cases])
    d_ri = np.concatenate([c["d_ri"] for c in cases])
    d_tau = np.concatenate([c["d_tau"] for c in cases])
    d_dpdt = np.concatenate([c["d_dpdt"] for c in cases])
    d_map = np.concatenate([c["d_map"] for c in cases])

    print(f"\n-- Q2: ΔPWTT を何が説明するか（原点通過・主解析と同じ規約）--")
    for lab, X in [("Δ(T2−T1) 末梢動脈区間のみ", [d_per]),
                   ("ΔT1 前駆出期＋中枢", [d_t1]),
                   ("両方", [d_per, d_t1]),
                   ("ΔT（血管指標・再掲）", [d_dt]),
                   ("ΔMAP（参考）", [d_map])]:
        r2, coef = _r2_origin(d_pwtt, X)
        cs = "  ".join(f"β={c:+.3f}" for c in coef)
        print(f"  {lab:<28} r² = {r2:7.3f}   {cs}")

    # ---- Q1（最優先）----
    print(f"\n-- Q1（最優先）: 末梢動脈区間の変化を血管指標は説明するか --")
    for lab, y, X in [("Δ(T2−T1) ~ ΔT", d_per, [d_dt]),
                      ("Δ(T2−T1) ~ ΔT + ΔRI", d_per, [d_dt, d_ri]),
                      ("ΔPWTT   ~ ΔT（比較）", d_pwtt, [d_dt])]:
        r2, coef = _r2_origin(y, X)
        cs = "  ".join(f"β={c:+.3f}" for c in coef)
        print(f"  {lab:<28} r² = {r2:7.3f}   {cs}")

    rp = df["rho_per_dt"].to_numpy(float)
    rw = df["rho_pwtt_dt"].to_numpy(float)
    fin_p, fin_w = rp[np.isfinite(rp)], rw[np.isfinite(rw)]
    if fin_p.size >= 5:
        from scipy.stats import binomtest
        pos = int((fin_p > 0).sum())
        pv = binomtest(pos, fin_p.size, 0.5).pvalue
        print(f"\n  症例内 順位相関の中央値")
        print(f"    rho(Δ(T2−T1), ΔT) = {np.median(fin_p):+.3f}"
              f"   符号の揃い {max(pos, fin_p.size-pos)/fin_p.size:.0%}"
              f"   p={pv:.3g}   (n={fin_p.size})")
        if fin_w.size:
            print(f"    rho(ΔPWTT,   ΔT) = {np.median(fin_w):+.3f}   (n={fin_w.size})")
        print("\n  読み方: 前者が後者より明確に大きければ、研究1の陰性は前駆出期に")
        print("          隠されていたことになる。同程度なら血管指標は末梢動脈区間も")
        print("          説明できていない（概念の側の問題）。")

    # ---- Q3（参考）----
    print(f"\n-- Q3（参考）: 動脈圧由来の指標で ΔPWTT を説明できるか --")
    for lab, X in [("Δτ（RC時定数）", [d_tau]),
                   ("ΔdP/dt_max", [d_dpdt]),
                   ("両方", [d_tau, d_dpdt])]:
        r2, coef = _r2_origin(d_pwtt, X)
        cs = "  ".join(f"β={c:+.3f}" for c in coef)
        print(f"  {lab:<28} r² = {r2:7.3f}   {cs}")
    print("  ※ 動脈圧はパルスオキシメータの利得制御を経ないため、これらが説明すれば")
    print("    PPGの測定限界、説明しなければ概念の限界という切り分けになる")

    outp = DATA / "pwtt_decomposition.csv"
    df.to_csv(outp, index=False)
    print(f"\n症例別の結果: {outp}")


# ---------------------------------------------------------------- 自己検証
def selftest() -> int:
    print("== 21_pwtt_decomposition 自己検証（合成データ）==\n")
    ok = True
    rng = np.random.default_rng(0)
    n = 120

    # 仕込み: 末梢区間は ΔT と強く連動、PEP は逆向きに動いて ΔPWTT を打ち消す
    dt_true = rng.normal(0, 0.10, n)
    per = 40.0 * (1.0 + 0.8 * dt_true) + rng.normal(0, 0.3, n)
    pep = 150.0 * (1.0 - 0.8 * dt_true * 40.0 / 150.0) + rng.normal(0, 0.3, n)
    t1 = pep + 60.0
    t2 = t1 + per

    d_per = _rel(per); d_pwtt = _rel(t2); d_dt = _rel(1.0 + dt_true)
    r_per, _ = _r2_origin(d_per, [d_dt])
    r_pwtt, _ = _r2_origin(d_pwtt, [d_dt])
    c1 = np.isfinite(r_per) and r_per > 0.8
    c2 = np.isfinite(r_pwtt) and r_pwtt < 0.3
    ok &= c1 and c2
    print(f"  打ち消しの検出: r²(Δ(T2−T1)~ΔT)={r_per:.3f}（要 >0.8）  {'PASS' if c1 else 'FAIL'}")
    print(f"                  r²(ΔPWTT  ~ΔT)={r_pwtt:.3f}（要 <0.3）  {'PASS' if c2 else 'FAIL'}")
    print("  → 打ち消しがある場合に、この解析が両者を区別できることを確認した")

    ac = _ac1(np.cumsum(rng.normal(0, 1, 200)))
    acn = _ac1(rng.normal(0, 1, 200))
    a_ok = ac > 0.8 and abs(acn) < 0.3
    ok &= a_ok
    print(f"\n  自己相関: 滑らかな系列 {ac:+.3f} / 白色雑音 {acn:+.3f}  {'PASS' if a_ok else 'FAIL'}")

    r_ok = (not np.isfinite(_spearman(np.ones(50), np.arange(50.0)))
            and abs(_spearman(np.arange(50.0), np.arange(50.0) ** 3) - 1.0) < 1e-9)
    ok &= r_ok
    print(f"  順位相関: 定数入力でNaN・単調変換で1.0  {'PASS' if r_ok else 'FAIL'}")

    d = _drift(np.arange(50.0) + 100.0)
    d_ok = np.isfinite(d) and d > 0.3
    ok &= d_ok
    print(f"  ドリフト検出: 単調増加系列で {d:.3f}  {'PASS' if d_ok else 'FAIL'}")

    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())

    ids = sorted(int(p.stem.split("_")[1]) for p in AFEAT.glob("case_*.csv"))
    if args.limit:
        ids = ids[:args.limit]
    print(f"{len(ids)} 症例を読み込みます", flush=True)
    cases = []
    for k, cid in enumerate(ids, 1):
        c = case_frame(cid)
        if c:
            cases.append(c)
        if k % 200 == 0:
            print(f"  [{k}/{len(ids)}] 採用 {len(cases)}", flush=True)
    report(cases)


if __name__ == "__main__":
    main()

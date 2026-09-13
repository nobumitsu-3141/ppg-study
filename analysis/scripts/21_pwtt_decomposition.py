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

4. 2 区間の変動の大きさと相関（2026-09-13 追加・事後・記述）
------------------------------------------------------------
Q2 は ΔPWTT を Δ(T2−T1) だけ／ΔT1 だけで当てはめた r² を出す。この 2 つの和は、両方を
用いた r² を大きく下回った（2026-09-03 の実行）。PWTT = T1 + (T2−T1) は正の重みの恒等式
なので、これは **2 区間の変化が症例内で負に相関している**ことを意味する。考えられる原因は
橈骨動脈圧の立ち上がりの検出誤差で、T1 に ＋、T2−T1 に − で入り、PWTT では打ち消される。
そこで問う。**2 区間の変化はどれだけ大きく、どれだけ負に相関しているか。** 節4 は ms 単位の
症例内 SD、ΔT1 と Δ(T2−T1) の症例内相関（Spearman・Pearson）、
Var(ΔPWTT) = Var(ΔT1) + Var(Δ(T2−T1)) + 2·Cov の分散分解を出す。
**既存の節（可測性ゲート・Q1・Q2・Q3）の計算にも印字にも触れない。**

予測（2026-09-13、計算の前に固定）: (P1) ΔT1 と Δ(T2−T1) の症例内相関の中央値は負で、−0.1 より小さい。(P2) ms 単位の症例内 SD は ΔT1 と Δ(T2−T1) で同じ桁で、比は 0.5〜2 の範囲に入る。(P3) 分散分解の交差項 2·Cov は負で、その大きさは Var(ΔPWTT) の 20% 以上である。理由: 橈骨動脈圧の立ち上がりの検出誤差が T1 と T2−T1 に逆符号で入り、PWTT では打ち消されるから。当たっても外れても判定は付けない（記述）。

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

# 節4 の予測（2026-09-13。**計算の前に固定した。** docstring と同文）
PRED_RHO_MAX = -0.10     # P1: ΔT1 と Δ(T2−T1) の症例内相関の中央値はこれより小さい
PRED_RATIO = (0.5, 2.0)  # P2: ms 単位の症例内 SD の比 SD(T1)/SD(T2−T1) が入る範囲
PRED_CROSS_MIN = 0.20    # P3: 交差項 2·Cov の大きさ ÷ Var(ΔPWTT) の下限


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


def _pearson(x, y) -> float:
    """積率相関。欠測・定数入力・最少本数の扱いは _spearman と同じ規約にそろえる。"""
    x, y = np.asarray(x, float), np.asarray(y, float)
    g = np.isfinite(x) & np.isfinite(y)
    if g.sum() < 8 or np.ptp(x[g]) == 0 or np.ptp(y[g]) == 0:
        return float("nan")
    return float(np.corrcoef(x[g], y[g])[0, 1])


def _ms_dev(x) -> np.ndarray:
    """初回ウィンドウの値からの差（ms のまま。_rel と違って規格化しない）。

    T2 = T1 + (T2−T1) なので、この差どうしでは
    ΔPWTT(ms) = ΔT1(ms) + Δ(T2−T1)(ms) が厳密に成り立つ。節4 の分散分解はこれを使う。
    """
    x = np.asarray(x, float)
    return x - x[0]


def _var_split(a, b) -> tuple:
    """Var(a+b) = Var(a) + Var(b) + 2Cov(a,b) の各項（母分散・ddof=0）。

    返すのは (Var(a), Var(b), 2Cov(a,b), Var(a+b))。Var(a+b) は 3 項の和からではなく
    直接計算するので、和との一致が数値誤差の検査になる。
    """
    a, b = np.asarray(a, float), np.asarray(b, float)
    g = np.isfinite(a) & np.isfinite(b)
    if g.sum() < 2:
        return float("nan"), float("nan"), float("nan"), float("nan")
    a, b = a[g] - a[g].mean(), b[g] - b[g].mean()
    s = a + b
    return (float(np.mean(a * a)), float(np.mean(b * b)),
            2.0 * float(np.mean(a * b)), float(np.mean(s * s)))


def _frac(x: float, tot: float) -> float:
    """分散の取り分 x / tot。母数が 0 以下なら NaN。"""
    return float(x / tot) if np.isfinite(tot) and tot > 0 else float("nan")


def _med_iqr(v) -> tuple:
    """有限値だけの (中央値, 第1四分位, 第3四分位, 個数)。"""
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return float("nan"), float("nan"), float("nan"), 0
    return (float(np.median(v)), float(np.percentile(v, 25)),
            float(np.percentile(v, 75)), int(v.size))


def _neg_frac(v) -> float:
    """有限値のうち負の値の割合。"""
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    return float((v < 0).mean()) if v.size else float("nan")


def _pad(s: str, w: int, right: bool = False) -> str:
    """表示幅で揃える（日本語は 2 文字分。f 文字列の桁指定は文字数なのでずれる）。"""
    import unicodedata
    used = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in str(s))
    fill = " " * max(0, w - used)
    return (fill + str(s)) if right else (str(s) + fill)


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

    # 節4（事後・記述）で使う ms 単位の症例内変化。ndarray なので症例別 CSV には出ない
    out["ms_t1"], out["ms_per"] = _ms_dev(t1), _ms_dev(per)

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
    q2_r2 = {}      # 節4 が参照する。印字は変えない
    for key, lab, X in [("per", "Δ(T2−T1) 末梢動脈区間のみ", [d_per]),
                        ("t1", "ΔT1 前駆出期＋中枢", [d_t1]),
                        ("both", "両方", [d_per, d_t1]),
                        ("dt", "ΔT（血管指標・再掲）", [d_dt]),
                        ("map", "ΔMAP（参考）", [d_map])]:
        r2, coef = _r2_origin(d_pwtt, X)
        q2_r2[key] = r2
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

    # 節4 は既存の節すべてのあとに足した（上の印字は 1 字も変えていない）
    section4(cases, q2_r2)


# ---------------------------------------------------------------- 節4（事後・記述）
def section4(cases: list[dict], q2_r2: dict) -> dict:
    """2 区間（T1 と T2−T1）の変動の大きさと、その変化の症例内相関を記述する。

    2026-09-13 に足した事後の記述である。**既存の節（可測性ゲート・Q1・Q2・Q3）の
    計算にも印字にも触れない。**使うのは case_frame が作った ms 単位の変化量
    （ms_t1・ms_per）と、Q1・Q2 の回帰と同じ Δ（_rel）だけである。
    返り値は自己検証のための要約で、印字した値と同じものを入れる。
    """
    print("\n-- 4. 2 区間の変動の大きさと相関（2026-09-13 追加・事後・記述）--")
    if not cases:
        print("  症例がないので計算しない。")
        return {}

    n_case = len(cases)
    n_win = int(sum(int(c["n"]) for c in cases))
    sd1, sd2, sdp, cv1, cv2, rat = [], [], [], [], [], []
    rho, pea, f_1, f_2, f_x, res = [], [], [], [], [], []
    for c in cases:
        a = np.asarray(c["ms_t1"], float)
        b = np.asarray(c["ms_per"], float)
        va, vb, cross, vtot = _var_split(a, b)
        s1, s2 = float(np.nanstd(a)), float(np.nanstd(b))
        sd1.append(s1)
        sd2.append(s2)
        sdp.append(float(np.nanstd(a + b)))
        cv1.append(s1 / max(abs(float(c["t1_med"])), 1e-9))
        cv2.append(float(c["cv_per"]))
        rat.append(s1 / s2 if s2 > 0 else float("nan"))
        rho.append(_spearman(c["d_t1"], c["d_per"]))
        pea.append(_pearson(c["d_t1"], c["d_per"]))
        f_1.append(_frac(va, vtot))
        f_2.append(_frac(vb, vtot))
        f_x.append(_frac(cross, vtot))
        res.append(abs(va + vb + cross - vtot) / max(abs(vtot), 1e-12))

    pa = np.concatenate([np.asarray(c["ms_t1"], float) for c in cases])
    pb = np.concatenate([np.asarray(c["ms_per"], float) for c in cases])
    pva, pvb, pcross, pvtot = _var_split(pa, pb)
    pres = abs(pva + pvb + pcross - pvtot) / max(abs(pvtot), 1e-12)

    def row(lab: str, v, fmt: str = "{:8.3f}", unit: str = "", sep: str = "–") -> None:
        m, lo, hi, k = _med_iqr(v)
        print(f"    {_pad(lab, 26)}{fmt.format(m)}{unit}"
              f"   [IQR {fmt.format(lo).strip()}{sep}{fmt.format(hi).strip()}]   n={k}")

    print(f"  対象は上の節と同じ {n_case} 症例（有効ウィンドウ {MIN_WIN} 以上）"
          f"・{n_win:,} ウィンドウ。")
    print("  症例内変動の定義: ウィンドウごとの値の標準偏差（ddof=0）。既存の cv_per と")
    print("  同じで、隣接ウィンドウ間の差の標準偏差ではない。Δ は Q1・Q2 の回帰と同じ")
    print("  _rel（初回ウィンドウの値からの相対変化）。分散分解だけは ms 単位で行う")
    print("  （T2 = T1 + (T2−T1) なので ΔPWTT(ms) = ΔT1(ms) + Δ(T2−T1)(ms) が厳密に成り立つ）。")

    print("\n  4-1 症例内の変動の大きさ（中央値 [IQR]）")
    row("T1 の症例内 SD", sd1, "{:8.2f}", " ms")
    row("T2−T1 の症例内 SD", sd2, "{:8.2f}", " ms")
    row("PWTT(=T2) の症例内 SD", sdp, "{:8.2f}", " ms")
    row("T1 の変動係数", cv1, "{:8.4f}", "   ")
    row("T2−T1 の変動係数（再掲）", cv2, "{:8.4f}", "   ")
    row("SD(T1) / SD(T2−T1)", rat, "{:8.3f}", "   ")
    rr = np.asarray(rat, float)
    rr = rr[np.isfinite(rr)]
    in_rng = (float(((rr >= PRED_RATIO[0]) & (rr <= PRED_RATIO[1])).mean())
              if rr.size else float("nan"))
    print(f"      比が {PRED_RATIO[0]:g}〜{PRED_RATIO[1]:g} に入る症例  {in_rng:.0%}")

    print("\n  4-2 2 区間の変化の症例内相関（ΔT1 と Δ(T2−T1)。Δ は Q1・Q2 と同じ _rel）")
    for lab, v in [("Spearman", rho), ("Pearson", pea)]:
        m, lo, hi, k = _med_iqr(v)
        print(f"    {_pad(lab, 26)}{m:+8.3f}   [IQR {lo:+.3f}, {hi:+.3f}]"
              f"   負の症例 {_neg_frac(v):.0%}   n={k}")

    print("\n  4-3 分散分解 Var(ΔPWTT) = Var(ΔT1) + Var(Δ(T2−T1)) + 2·Cov（ms²）")
    print("    症例ごとの取り分（Var(ΔPWTT) に対する比。中央値 [IQR]）")
    row("Var(ΔT1)", f_1, "{:+8.3f}", sep=", ")
    row("Var(Δ(T2−T1))", f_2, "{:+8.3f}", sep=", ")
    row("2·Cov（交差項）", f_x, "{:+8.3f}", sep=", ")
    print(f"    3 項の和と Var(ΔPWTT) の相対差  最大 {float(np.nanmax(res)):.1e}"
          f"（恒等式なので数値誤差だけ）")
    print(f"\n    全ウィンドウをまとめた分解（{pa.size:,} ウィンドウ。"
          f"症例ごとに初回ウィンドウからの差に")
    print("    してからまとめた。症例をまたぐ平均の違いは差をとった時点で消えている）")
    for lab, v in [("Var(ΔPWTT)", pvtot), ("Var(ΔT1)", pva),
                   ("Var(Δ(T2−T1))", pvb), ("2·Cov（交差項）", pcross)]:
        f = "" if lab == "Var(ΔPWTT)" else f"   （{_frac(v, pvtot):+.3f}）"
        print(f"      {_pad(lab, 18)}{v:12.1f} ms²{f}")
    print(f"      3 項の和との相対差 {pres:.1e}")

    r_per = float(q2_r2.get("per", float("nan")))
    r_t1 = float(q2_r2.get("t1", float("nan")))
    r_both = float(q2_r2.get("both", float("nan")))
    print("\n    Q2 の r² との対応（この実行で Q2 が計算した値をそのまま使う）")
    print(f"      r²(Δ(T2−T1) のみ) {r_per:.3f} ＋ r²(ΔT1 のみ) {r_t1:.3f}"
          f" = {r_per + r_t1:.3f}   両方 {r_both:.3f}")
    lt = bool(np.isfinite(r_per + r_t1 - r_both) and (r_per + r_t1) < r_both)
    print(f"      単独の和 − 両方 = {r_per + r_t1 - r_both:+.3f}"
          f"   単独の和は両方を下回るか  {'はい' if lt else 'いいえ'}")
    print("      PWTT = T1 + (T2−T1) は正の重みの恒等式なので、2 区間の変化が症例内で")
    print("      無相関なら、単独の r² の和は両方を用いた r² とほぼ等しくなる。和が下回るのは、")
    print("      2 区間の変化が負に相関して互いを打ち消していることに対応する。区間ごとの")
    print("      取り分（Q2 の 2 つの単独 r²）はこの打ち消しの分だけ歪んでおり、そのまま")
    print("      「末梢側が大半」とは読めない。正確なのは合計だけである。")

    m_rho, m_pea, m_rat, m_x = (_med_iqr(rho)[0], _med_iqr(pea)[0],
                                _med_iqr(rat)[0], _med_iqr(f_x)[0])
    p1 = bool(np.isfinite(m_rho) and m_rho < PRED_RHO_MAX)
    p2 = bool(np.isfinite(m_rat) and PRED_RATIO[0] <= m_rat <= PRED_RATIO[1])
    p3 = bool(np.isfinite(m_x) and m_x < 0 and abs(m_x) >= PRED_CROSS_MIN)
    print("\n  4-4 予測との照合（予測は 2026-09-13 に、計算の前に固定した。docstring と同文）")
    print(f"    P1 症例内相関の中央値が負で {PRED_RHO_MAX:.1f} より小さい"
          f"   {'はい' if p1 else 'いいえ'}")
    print(f"       （判定は Spearman の中央値 {m_rho:+.3f} で行う。"
          f"Pearson の中央値は {m_pea:+.3f}）")
    print(f"    P2 ms 単位の症例内 SD の比 SD(T1)/SD(T2−T1) が"
          f" {PRED_RATIO[0]:g}〜{PRED_RATIO[1]:g} に入る   {'はい' if p2 else 'いいえ'}")
    print(f"       （中央値 {m_rat:.3f}。この範囲に入る症例は {in_rng:.0%}）")
    print(f"    P3 交差項 2·Cov が負で、その大きさが Var(ΔPWTT) の"
          f" {PRED_CROSS_MIN:.0%} 以上   {'はい' if p3 else 'いいえ'}")
    print(f"       （症例ごとの比の中央値 {m_x:+.3f}。"
          f"全ウィンドウでは {_frac(pcross, pvtot):+.3f}）")
    print("    ※ 当たっても外れても成立・不成立の判定は付けない（事後・記述）。")
    print(f"\n  出典: analysis/scripts/21_pwtt_decomposition.py（節4）/ "
          f"{n_case} 症例・{n_win:,} ウィンドウ")

    return {"n_case": n_case, "n_win": n_win,
            "sd_t1_med": _med_iqr(sd1)[0], "sd_per_med": _med_iqr(sd2)[0],
            "cv_t1_med": _med_iqr(cv1)[0], "ratio_med": m_rat, "ratio_in": in_rng,
            "rho_med": m_rho, "pearson_med": m_pea,
            "rho_neg": _neg_frac(rho), "pearson_neg": _neg_frac(pea),
            "f_t1_med": _med_iqr(f_1)[0], "f_per_med": _med_iqr(f_2)[0],
            "cross_med": m_x, "resid_max": float(np.nanmax(res)), "q2_sum_lt_both": lt,
            "pool": (pva, pvb, pcross, pvtot), "pool_resid": float(pres),
            "p1": p1, "p2": p2, "p3": p3}


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

    # ---- 節4（2026-09-13 追加）: 2 区間の変動の大きさと相関 ----
    import io
    from contextlib import redirect_stdout

    def fake(cid: int, t1, per) -> dict:
        """節4 が使う要素だけを case_frame と同じ規約で作る。"""
        t1, per = np.asarray(t1, float), np.asarray(per, float)
        return {"caseid": cid, "n": int(t1.size),
                "t1_med": float(np.median(t1)),
                "cv_per": float(np.nanstd(per) / max(abs(np.nanmedian(per)), 1e-9)),
                "d_t1": _rel(t1), "d_per": _rel(per),
                "ms_t1": _ms_dev(t1), "ms_per": _ms_dev(per)}

    rng4 = np.random.default_rng(21)
    SD1, SD2, SDJ, NW = 6.0, 9.0, 5.0, 200
    jit_cases, ind_cases = [], []
    for k in range(6):
        a4 = 180.0 + rng4.normal(0, SD1, NW)          # T1 の真の変動
        b4 = 479.0 + rng4.normal(0, SD2, NW)          # T2−T1 の真の変動
        dj = rng4.normal(0, SDJ, NW)                  # 橈骨の立ち上がりの検出誤差
        jit_cases.append(fake(100 + k, a4 + dj, b4 - dj))   # T1 に ＋、T2−T1 に −
        ind_cases.append(fake(200 + k, a4, b4))             # 検出誤差なし・独立
    q2fake = {"per": 0.50, "t1": 0.10, "both": 0.95}

    buf1, buf2 = io.StringIO(), io.StringIO()
    with redirect_stdout(buf1):
        sj = section4(jit_cases, q2fake)
    with redirect_stdout(buf2):
        section4(jit_cases, q2fake)
    with redirect_stdout(io.StringIO()):
        si = section4(ind_cases, q2fake)

    e1, e2 = float(np.hypot(SD1, SDJ)), float(np.hypot(SD2, SDJ))
    s_ok = abs(sj["sd_t1_med"] - e1) < 1.0 and abs(sj["sd_per_med"] - e2) < 1.0
    ok &= s_ok
    print(f"\n  節4 仕込んだ SD の復元: T1 {sj['sd_t1_med']:.2f}（要 {e1:.2f}±1.0）"
          f" / T2−T1 {sj['sd_per_med']:.2f}（要 {e2:.2f}±1.0）  {'PASS' if s_ok else 'FAIL'}")

    n_ok = (sj["rho_med"] < PRED_RHO_MAX and sj["pearson_med"] < 0
            and sj["cross_med"] < 0 and abs(sj["cross_med"]) >= PRED_CROSS_MIN)
    ok &= n_ok
    print(f"  節4 検出誤差 δ を T1 に ＋・T2−T1 に − で入れたとき:"
          f" Spearman 中央値 {sj['rho_med']:+.3f}（要 < {PRED_RHO_MAX:.2f}）")
    print(f"      Pearson {sj['pearson_med']:+.3f}（要 < 0）・2·Cov/Var(ΔPWTT)"
          f" {sj['cross_med']:+.3f}（要 < {-PRED_CROSS_MIN:.2f}）  {'PASS' if n_ok else 'FAIL'}")

    a_ok = sj["resid_max"] <= 1e-9 and sj["pool_resid"] <= 1e-9
    ok &= a_ok
    print(f"  節4 分散分解の一致（3 項の和と Var(ΔPWTT)）: 症例ごと最大"
          f" {sj['resid_max']:.1e}・全ウィンドウ {sj['pool_resid']:.1e}"
          f"（要 ≤ 1e-9・相対）  {'PASS' if a_ok else 'FAIL'}")

    i_ok = abs(si["rho_med"]) < 0.15 and abs(si["cross_med"]) < 0.15
    ok &= i_ok
    print(f"  節4 検出誤差なし・独立な雑音のとき: Spearman 中央値 {si['rho_med']:+.3f}"
          f"・2·Cov/Var(ΔPWTT) {si['cross_med']:+.3f}"
          f"（要 どちらも |·| < 0.15）  {'PASS' if i_ok else 'FAIL'}")

    txt = buf1.getvalue()
    pl = [x for x in txt.splitlines() if x.strip().startswith(("P1 ", "P2 ", "P3 "))]
    t_ok = (txt == buf2.getvalue() and len(txt) > 500 and len(pl) == 3
            and all(("はい" in x) or ("いいえ" in x) for x in pl))
    ok &= t_ok
    print(f"  節4 2 回描いて同じ文字列・P1〜P3 が はい／いいえ 付きで出る"
          f"  {'PASS' if t_ok else 'FAIL'}")
    print("  → 検出誤差が逆符号で入ると 2 区間の変化が負に相関することと、"
          "分散分解が恒等式として閉じることを確認した")

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

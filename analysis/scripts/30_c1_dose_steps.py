#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""研究1c C-1: 昇圧薬の用量ステップを自然実験として、PWTT の構成要素がどう動くかを見る。

SAP-1c（docs/research/sap_1c_v0.md）の実装。**SAP を凍結（タグ sap-1c-v*）するまで
実データの統計は走らせない**（--stats はタグを確かめ、無ければ止まる。--unfrozen-ok で
強行できるが、報告に「未凍結」と刻まれる）。

問い（SAP §2）
--------------
  主     フェニレフリンの増量に対し Δ(T2−T1)（橈骨→指尖）は一貫した向きに動くか。事前予測は短縮
  副次1  ΔT1（R波→動脈圧立ち上がり＝前駆出期＋中枢）。事前予測は延長
  副次2  ΔPWTT（＝ΔT2）。記述
  副次3  ΔT・RI（凍結版 PDA。--pda で抽出したときだけ）。記述のみ。妥当性の証拠には使わない

解析単位（SAP §3）
------------------
  用量ステップ: 1 Hz の投与レート r(t) が、直前 120 秒の定常値（±10% 以内）に対し ±30% 以上変わり、
  変わった後の水準を後の窓の終わり（180 秒）まで ±10% で保つ時点。on→off・off→on も数える。
  増量と減量を分ける。前の窓 = 直前 120 秒、後の窓 = ウォッシュイン 60 秒を挟んだ 120 秒。
  主解析と同じ 60 秒窓の特徴量のうち、前後の区間に**完全に入る**窓を使い、前後いずれかで
  窓が 1 つも無いステップは落とす。前後の区間に他の血管作動薬のレート変化が入るステップも落とす。
  体位変換・遮断解除は VitalDB に構造化された記録が無いので自動では除外できない（限界）。

統計（SAP §4。実装の細目は SAP v0.1 に書いた）
-----------------------------------------------
  ステップごとの Δ = 後の窓の中央値 − 前の窓の中央値（ms と相対の両方）。
  平均 Δ の 95% 信頼区間は**症例をまとめて再抽出するブートストラップ**（症例をランダム効果と
  みなす混合効果モデルの代わり。外部ライブラリ無しで同じ層化を実現する）。
  症例が 30 未満なら症例ごとの中央値の符号検定に切り替える（SAP）。
  増量と減量で向きが反転することを要求する。MAP・HR の変化を共変量にした回帰の切片
  （MAP・HR が動かなかったときの効果）を併記し、調整で消える効果は陽性と判定しない。

陰性対照（SAP §5）
------------------
  レミフェンタニル・プロポフォールのレート変化（同じ定義・同じ Δ）、および昇圧薬を投与していない
  区間から症例ごとに同数だけ無作為に取った擬似ステップ。ここで動けば手順がドリフトを拾っている。

段（使い方）
------------
    python3 scripts/30_c1_dose_steps.py --selftest
        合成データで検出・除外・統計・判定・抽出を検算（ネットワーク不要・1〜2 分）
    python3 scripts/30_c1_dose_steps.py --extract --jobs 4
        PLETH・ECG・ART を持ち Orchestra/PHEN_RATE のある症例の 60 秒窓の特徴量と 1 Hz のレートを
        data/c1/ に置く（参照 CO は要らない。主解析のキャッシュとは別に作る）
    python3 scripts/30_c1_dose_steps.py --extract --jobs 8 --pda
        凍結版 PDA の ΔT・RI も抽出する（副次3。CPU を食う）
    python3 scripts/30_c1_dose_steps.py --stats
        SAP を凍結したタグがあることを確かめ、主解析 → 陰性対照 → 調整の順に出す。
        出力: data/c1/steps.csv（ステップ別の Δ）と data/c1/c1_report.txt（表の全文）
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.beats import (segment_beats, sqi, ensemble_average,  # noqa: E402
                       estimate_noise, required_ensemble_size)
from src.indices import (pwtt_series, detect_r_peaks, estimate_pleth_lag,  # noqa: E402
                         si_ri_from_fit)

FS = 500.0
WIN_S = 60.0
DATA = ROOT / "data"
C1 = DATA / "c1"

# --- 解析単位の定数（SAP §3。26番の実行前に固定した値と同じ流儀で、結果を見て動かさない）
STEP_FRAC = 0.30        # 直前の定常値に対する相対変化の下限
PRE_S = 120.0           # 前の窓（ベースライン）
WASHIN_S = 60.0         # ウォッシュイン
POST_S = 120.0          # 後の窓
HOLD_TOL = 0.10         # 定常とみなす幅（中央値に対する相対）
MDE_MS = 3.0            # 主要判定の最小効果量（増量で 3 ms 以上の短縮）
N_BOOT = 2000           # 症例ブートストラップの回数
MIN_CASES_MIXED = 30    # これ未満なら症例ごとの中央値の符号検定に切り替える（SAP §4）
MIN_STEPS_CONTROL = 5   # 陰性対照の群を評価するのに要る最小ステップ数

# --- トラック（短い名前 → Orchestra のトラック名）
PRESSOR = "PHEN"
OTHER_VASOACTIVE = ["NEPI", "EPI", "VASO", "DOPA", "DOBU", "MRN", "NTG", "NPS", "PGE1", "DTZ",
                    "DEX2", "DEX4", "OXY", "AMD"]
CONTROLS = {"レミフェンタニル": ["RFTN20", "RFTN50"], "プロポフォール": ["PPF20"]}
RATE_TRACK = lambda short: f"Orchestra/{short}_RATE"  # noqa: E731
WAVE_TRACKS = ["SNUADC/PLETH", "SNUADC/ECG_II", "SNUADC/ART"]

# --- 指標の一覧（列, 表示名, 増量に対する事前予測の符号, 役割）。符号 0 は記述のみ
PANEL = [
    ("t2t1_ms", "T2−T1（橈骨→指尖）[ms]", -1, "主"),
    ("t1_ms",   "T1（R→動脈圧）[ms]",     +1, "副次1"),
    ("pwtt_ms", "PWTT（T2）[ms]",          0, "副次2 記述"),
    ("dt_ms",   "ΔT 凍結版PDA [ms]",       0, "副次3 記述"),
    ("ri",      "RI 凍結版PDA",            0, "副次3 記述"),
]
COVARS = ["map", "hr"]

META_V = 1


def _load(stem: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / stem)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# ================================================================ 用量ステップ
def _steady(seg: np.ndarray, tol: float = HOLD_TOL):
    """区間が定常か（中央値の ±tol 以内、または全て 0）。返り値 (定常か, 水準)。NaN は 0 とみなす。"""
    x = np.nan_to_num(np.asarray(seg, float), nan=0.0)
    if x.size == 0:
        return False, float("nan")
    lev = float(np.median(x))
    if lev <= 0:
        return bool(np.all(x <= 0)), 0.0
    return bool(np.all(np.abs(x - lev) <= tol * lev)), lev


def dose_steps(rate: np.ndarray, frac: float = STEP_FRAC, pre_s: float = PRE_S,
               hold_s: float = WASHIN_S + POST_S, tol: float = HOLD_TOL) -> list:
    """1 Hz のレートから用量ステップを取り出す。

    返り値: [{"t": 秒, "pre": 直前の水準, "post": 後の水準, "direction": +1/−1}, …]
    定義は SAP §3（前 120 秒が定常、後 180 秒が定常、相対変化 ≥ frac または on/off）。
    小刻みなランプは、後の区間が定常になる最後の変化だけがステップになる。
    """
    r = np.nan_to_num(np.asarray(rate, float), nan=0.0)
    n = r.size
    out = []
    pre_n, hold_n = int(round(pre_s)), int(round(hold_s))
    for i in range(1, n):
        if r[i] == r[i - 1]:
            continue
        if i - pre_n < 0 or i + hold_n > n:
            continue
        ok_pre, lev_pre = _steady(r[i - pre_n:i], tol)
        ok_post, lev_post = _steady(r[i:i + hold_n], tol)
        if not (ok_pre and ok_post) or lev_post == lev_pre:
            continue
        if lev_pre > 0 and abs(lev_post - lev_pre) < frac * lev_pre:
            continue
        out.append({"t": float(i), "pre": lev_pre, "post": lev_post,
                    "direction": 1 if lev_post > lev_pre else -1})
    return out


def changes_within(rate: np.ndarray, t_a: float, t_b: float, tol: float = HOLD_TOL) -> bool:
    """区間 [t_a, t_b] でレートが動いたか（相対 tol 超、または on/off）。NaN は 0。"""
    r = np.nan_to_num(np.asarray(rate, float), nan=0.0)
    a, b = max(int(t_a), 0), min(int(t_b) + 1, r.size)
    if b - a < 2:
        return False
    seg = r[a:b]
    lev = float(np.median(seg))
    if lev <= 0:
        return bool(np.any(seg > 0))
    return bool(np.any(np.abs(seg - lev) > tol * lev))


# ================================================================ 窓の対応づけと Δ
def pair_windows(t0: np.ndarray, t_s: float):
    """前の区間 [t_s−PRE, t_s) と後の区間 [t_s+WASHIN, t_s+WASHIN+POST) に完全に入る窓の添字。"""
    t0 = np.asarray(t0, float)
    pre = np.flatnonzero((t0 >= t_s - PRE_S) & (t0 + WIN_S <= t_s))
    post = np.flatnonzero((t0 >= t_s + WASHIN_S) & (t0 + WIN_S <= t_s + WASHIN_S + POST_S))
    return pre, post


def _median_finite(v) -> float:
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    return float(np.median(v)) if v.size else float("nan")


def step_deltas(feat, t_s: float, cols: list) -> dict | None:
    """1 ステップの Δ（後 − 前）を列ごとに。前後いずれかに窓が無ければ None。"""
    pre, post = pair_windows(feat["t0"].to_numpy(float), t_s)
    if pre.size == 0 or post.size == 0:
        return None
    out = {"n_pre": int(pre.size), "n_post": int(post.size)}
    for c in cols:
        if c not in feat:
            out[f"{c}_pre"] = out[f"{c}_post"] = out[f"d_{c}"] = out[f"rel_{c}"] = float("nan")
            continue
        a = _median_finite(feat[c].to_numpy(float)[pre])
        b = _median_finite(feat[c].to_numpy(float)[post])
        out[f"{c}_pre"], out[f"{c}_post"] = a, b
        out[f"d_{c}"] = b - a
        out[f"rel_{c}"] = (b - a) / a if (np.isfinite(a) and a != 0) else float("nan")
    return out


def collect_steps(cases: dict, drug_cols: list, label: str, confounders: list) -> list:
    """薬剤 drug_cols（同じ薬の別濃度は合算しない。列ごとに別のステップ）のステップを集める。

    cases: {caseid: (features DataFrame, rates DataFrame)}。confounders の列が前後の区間で
    動いたステップは落とす（理由を数える）。
    """
    rows, why = [], Counter()
    cols = [c for c, *_ in PANEL] + COVARS
    for cid, (feat, rates) in sorted(cases.items()):
        for dc in drug_cols:
            if dc not in rates:
                continue
            r = rates[dc].to_numpy(float)
            for st in dose_steps(r):
                t_s = st["t"]
                a, b = t_s - PRE_S, t_s + WASHIN_S + POST_S
                bad = [c for c in confounders if c in rates and c != dc
                       and changes_within(rates[c].to_numpy(float), a, b)]
                if bad:
                    why[f"交絡（{'・'.join(bad)} が動いた）"] += 1
                    continue
                d = step_deltas(feat, t_s, cols)
                if d is None:
                    why["前後の窓なし"] += 1
                    continue
                rows.append({"set": label, "caseid": int(cid), "drug": dc, "t": t_s,
                             "pre_rate": st["pre"], "post_rate": st["post"],
                             "direction": st["direction"], **d})
    return rows, why


def pseudo_steps(cases: dict, n_by_case: dict, rng, quiet_cols: list) -> list:
    """昇圧薬を投与していない区間から、症例ごとに n_by_case[cid] 個の擬似ステップを無作為に取る。"""
    rows = []
    cols = [c for c, *_ in PANEL] + COVARS
    for cid, (feat, rates) in sorted(cases.items()):
        n_want = int(n_by_case.get(cid, 0))
        if n_want <= 0 or "t" not in rates:
            continue
        t_all = rates["t"].to_numpy(float)
        if t_all.size == 0:
            continue
        cand = []
        for t_s in np.arange(PRE_S, float(t_all[-1]) - WASHIN_S - POST_S, 30.0):
            a, b = t_s - PRE_S, t_s + WASHIN_S + POST_S
            if PRESSOR in rates:
                r = np.nan_to_num(rates[PRESSOR].to_numpy(float), nan=0.0)
                if np.any(r[int(a):int(b) + 1] > 0):
                    continue
            if any(c in rates and changes_within(rates[c].to_numpy(float), a, b) for c in quiet_cols):
                continue
            if step_deltas(feat, t_s, ["t0"]) is None:
                continue
            cand.append(float(t_s))
        if not cand:
            continue
        pick = rng.choice(len(cand), size=min(n_want, len(cand)), replace=False)
        for k in sorted(pick):
            t_s = cand[k]
            d = step_deltas(feat, t_s, cols)
            rows.append({"set": "擬似ステップ（非投与区間）", "caseid": int(cid), "drug": "none",
                         "t": t_s, "pre_rate": 0.0, "post_rate": 0.0, "direction": 0, **d})
    return rows


# ================================================================ 統計
def cluster_boot_mean(v: np.ndarray, cid: np.ndarray, n_boot: int = N_BOOT, seed: int = 0):
    """ステップの平均と、症例をまとめて再抽出した 95% 区間。"""
    v, cid = np.asarray(v, float), np.asarray(cid)
    g = np.isfinite(v)
    v, cid = v[g], cid[g]
    if v.size == 0:
        return float("nan"), float("nan"), float("nan")
    cases = np.unique(cid)
    idx = {c: np.flatnonzero(cid == c) for c in cases}
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.choice(cases, size=cases.size, replace=True)
        sel = np.concatenate([idx[c] for c in pick])
        means[b] = v[sel].mean()
    return float(v.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def by_case_sign_test(v: np.ndarray, cid: np.ndarray):
    """症例ごとの中央値 → その中央値・符号検定の p・症例数。"""
    from scipy.stats import binomtest
    v, cid = np.asarray(v, float), np.asarray(cid)
    med = []
    for c in np.unique(cid):
        x = v[(cid == c) & np.isfinite(v)]
        if x.size:
            med.append(float(np.median(x)))
    med = np.asarray(med)
    if med.size == 0:
        return float("nan"), float("nan"), 0
    nz = med[med != 0]
    p = float(binomtest(int((nz > 0).sum()), int(nz.size), 0.5).pvalue) if nz.size else float("nan")
    return float(np.median(med)), p, int(med.size)


def adjusted_intercept(v, dmap, dhr, cid, n_boot: int = N_BOOT, seed: int = 0):
    """Δ = b0 + b1·ΔMAP + b2·ΔHR の切片（MAP・HR が動かなかったときの効果）と症例ブートストラップ区間。"""
    v, dmap, dhr, cid = (np.asarray(x, float) for x in (v, dmap, dhr, cid))
    g = np.isfinite(v) & np.isfinite(dmap) & np.isfinite(dhr)
    v, dmap, dhr, cid = v[g], dmap[g], dhr[g], cid[g]
    if v.size < 5 or np.unique(cid).size < 3:
        return float("nan"), float("nan"), float("nan"), int(v.size)
    X = np.column_stack([np.ones(v.size), dmap, dhr])

    def fit(sel):
        Xs, ys = X[sel], v[sel]
        try:
            beta, *_ = np.linalg.lstsq(Xs, ys, rcond=None)
            return float(beta[0])
        except Exception:      # noqa: BLE001
            return float("nan")
    b0 = fit(np.arange(v.size))
    cases = np.unique(cid)
    idx = {c: np.flatnonzero(cid == c) for c in cases}
    rng = np.random.default_rng(seed)
    bs = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.choice(cases, size=cases.size, replace=True)
        bs[b] = fit(np.concatenate([idx[c] for c in pick]))
    bs = bs[np.isfinite(bs)]
    if bs.size < n_boot // 2:
        return b0, float("nan"), float("nan"), int(v.size)
    return b0, float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)), int(v.size)


def summarize(rows: list, col: str, direction: int | None, seed: int = 0) -> dict:
    """1 つの指標 × 1 つの方向（None なら全部）の要約。"""
    sel = [r for r in rows if (direction is None or r["direction"] == direction)
           and np.isfinite(r.get(f"d_{col}", np.nan))]
    out = {"n": len(sel), "n_cases": len({r["caseid"] for r in sel})}
    if not sel:
        return out
    v = np.array([r[f"d_{col}"] for r in sel])
    rel = np.array([r[f"rel_{col}"] for r in sel])
    cid = np.array([r["caseid"] for r in sel])
    out["mean"], out["lo"], out["hi"] = cluster_boot_mean(v, cid, seed=seed)
    out["rel_mean"] = float(np.nanmean(rel)) if np.isfinite(rel).any() else float("nan")
    out["case_med"], out["sign_p"], out["n_cases_med"] = by_case_sign_test(v, cid)
    dmap = np.array([r.get("d_map", np.nan) for r in sel])
    dhr = np.array([r.get("d_hr", np.nan) for r in sel])
    out["adj_b0"], out["adj_lo"], out["adj_hi"], out["adj_n"] = adjusted_intercept(v, dmap, dhr, cid, seed=seed)
    out["dmap_mean"] = float(np.nanmean(dmap)) if np.isfinite(dmap).any() else float("nan")
    out["dhr_mean"] = float(np.nanmean(dhr)) if np.isfinite(dhr).any() else float("nan")
    return out


def _fmt(x, w=7, d=1):
    return f"{x:>{w}.{d}f}" if np.isfinite(x) else f"{'—':>{w}}"


def _ci(s: dict, key="mean", lo="lo", hi="hi", d=1):
    if s.get("n", 0) == 0 or not np.isfinite(s.get(key, np.nan)):
        return "—"
    return f"{s[key]:+.{d}f} [{s[lo]:+.{d}f}, {s[hi]:+.{d}f}]"


def primary_verdict(inc: dict, dec: dict, controls: dict, n_cases_total: int) -> tuple:
    """主要判定（SAP §6）。返り値 (判定, 根拠の一覧)。事後に緩めない。"""
    notes = []
    if inc.get("n", 0) == 0:
        return "判定できない（増量ステップなし）", notes
    small = inc["n_cases"] < MIN_CASES_MIXED
    if small:
        eff = np.isfinite(inc["case_med"]) and inc["case_med"] <= -MDE_MS and inc["sign_p"] < 0.05
        notes.append(f"症例 {inc['n_cases']} < {MIN_CASES_MIXED}: 症例ごとの中央値の符号検定で判定"
                     f"（中央値 {inc['case_med']:+.1f} ms, p={inc['sign_p']:.3f}）")
    else:
        eff = np.isfinite(inc["hi"]) and inc["mean"] <= -MDE_MS and inc["hi"] < 0
        notes.append(f"平均 {_ci(inc)} ms（症例ブートストラップ）")
    rev = dec.get("n", 0) > 0 and np.isfinite(dec.get("mean", np.nan)) and dec["mean"] > 0
    notes.append("減量で向きが反転: " + ("あり" if rev else ("なし" if dec.get("n", 0) else "減量ステップなし")))
    adj = np.isfinite(inc.get("adj_hi", np.nan)) and inc["adj_hi"] < 0
    notes.append(f"MAP・HR 調整後の切片 {_ci(inc, 'adj_b0', 'adj_lo', 'adj_hi')} ms → "
                 + ("残る" if adj else "消える／評価できない"))
    evaluable = {k: s for k, s in controls.items() if s.get("n", 0) >= MIN_STEPS_CONTROL}
    moved = [k for k, s in evaluable.items()
             if np.isfinite(s.get("lo", np.nan)) and (s["lo"] > 0 or s["hi"] < 0)]
    if not evaluable:
        notes.append("陰性対照: 評価できる群がない（各群 5 ステップ未満）")
    else:
        notes.append("陰性対照: " + ("動かない" if not moved else "動いた（" + "・".join(moved) + "）")
                     + f"（評価した群: {'・'.join(evaluable)}）")
    if not eff:
        return "動かない → (ii) 装置側の揺らぎ。血管補正の路線は終了", notes
    if not rev:
        return "増量で動くが減量で反転しない → 時間依存の交絡を疑う。陽性と判定しない", notes
    if not adj:
        return "増量で動くが MAP・HR の調整で消える → 陽性と判定しない", notes
    if not evaluable:
        return "動くが陰性対照が評価できない → 保留", notes
    if moved:
        return "動くが陰性対照でも動く → 手順がドリフトを拾っている。判定は保留", notes
    return "成立 → (i) 形態依存の検出ずれ。立ち上がり時刻が血管トーヌス情報を担っている", notes


# ================================================================ 報告
def report(rows_by_set: dict, n_cases_total: int, seed: int = 0, frozen: str = "") -> dict:
    print("=" * 78)
    print("研究1c C-1: 昇圧薬の用量ステップに対する PWTT 構成要素の応答（SAP-1c）")
    print("=" * 78)
    if frozen:
        print(frozen)
    print(f"対象症例 {n_cases_total}。ステップの定義: 直前 {PRE_S:.0f} 秒が定常（±{HOLD_TOL:.0%}）、"
          f"相対変化 ≥ {STEP_FRAC:.0%} または on/off、後 {WASHIN_S + POST_S:.0f} 秒が定常。"
          f"前の窓 {PRE_S:.0f} 秒・ウォッシュイン {WASHIN_S:.0f} 秒・後の窓 {POST_S:.0f} 秒。")
    print(f"平均の 95% 区間は症例ブートストラップ（{N_BOOT} 回, seed {seed}）。"
          f"症例 {MIN_CASES_MIXED} 未満なら症例ごとの中央値の符号検定。最小効果量 {MDE_MS:.0f} ms。\n")

    main_rows = rows_by_set.get("フェニレフリン", [])
    summary = {}
    for label, rows in rows_by_set.items():
        n_inc = sum(1 for r in rows if r["direction"] > 0)
        n_dec = sum(1 for r in rows if r["direction"] < 0)
        n_cid = len({r["caseid"] for r in rows})
        print("-" * 78)
        print(f"{label}: ステップ {len(rows)}（増量 {n_inc}・減量 {n_dec}・症例 {n_cid}）")
        print("-" * 78)
        print(f"{'指標':<28}{'向き':<6}{'n':>4}{'症例':>5}  {'平均 Δ [95%]':<26}{'相対':>7}"
              f"  {'症例中央値':>9}{'符号p':>7}  {'調整後 切片 [95%]':<24}")
        for col, name, sign, role in PANEL:
            if not any(np.isfinite(r.get(f"d_{col}", np.nan)) for r in rows):
                continue
            dirs = [(+1, "増量"), (-1, "減量")] if any(r["direction"] for r in rows) else [(0, "—")]
            for dval, dname in dirs:
                s = summarize(rows, col, dval if dval else None, seed=seed)
                summary[(label, col, dval)] = s
                if s["n"] == 0:
                    continue
                dd = 3 if col == "ri" else 1
                print(f"{name:<28}{dname:<6}{s['n']:>4}{s['n_cases']:>5}  {_ci(s, d=dd):<26}"
                      f"{_fmt(100 * s['rel_mean'], 6, 1)}%  {_fmt(s['case_med'], 9, dd)}"
                      f"{_fmt(s['sign_p'], 7, 3)}  {_ci(s, 'adj_b0', 'adj_lo', 'adj_hi', d=dd):<24}")
        # 共変量は向きごとに（増減を合わせると相殺して見える）
        for dval, dname in ((+1, "増量"), (-1, "減量"), (0, "擬似")):
            cm, ch = summarize(rows, "map", dval if dval else None, seed=seed), summarize(rows, "hr", dval if dval else None, seed=seed)
            if cm.get("n", 0) and (dval or not any(r["direction"] for r in rows)):
                print(f"  共変量の変化（{dname}）: ΔMAP {_ci(cm)} mmHg・ΔHR {_ci(ch)} /分")
    # --- 主要判定
    inc = summary.get(("フェニレフリン", "t2t1_ms", +1), {"n": 0})
    dec = summary.get(("フェニレフリン", "t2t1_ms", -1), {"n": 0})
    controls = {}
    for label in rows_by_set:
        if label == "フェニレフリン":
            continue
        for dval, dname in ((+1, "増量"), (-1, "減量"), (0, "")):
            s = summary.get((label, "t2t1_ms", dval))
            if s and s.get("n", 0):
                controls[f"{label}{('・' + dname) if dname else ''}"] = s
    verdict, notes = primary_verdict(inc, dec, controls, n_cases_total)
    print("\n" + "-" * 78 + "\n主要判定 Δ(T2−T1)・フェニレフリン増量（SAP §6。事後に緩めない）\n" + "-" * 78)
    for n_ in notes:
        print("  " + n_)
    print(f"  → **{verdict}**")
    t1 = summary.get(("フェニレフリン", "t1_ms", +1), {"n": 0})
    if t1.get("n", 0):
        print(f"  副次1 ΔT1（増量・事前予測は延長）: {_ci(t1)} ms → "
              + ("予測の向き" if t1["mean"] > 0 else "予測と逆") + "（記述に留める）")
    print("\n読み方（SAP §6）: 増量で ≥ 3 ms 短縮・区間が 0 を含まない・減量で反転・調整で残る・陰性対照が"
          "動かない、のすべてで (i)。動かなければ (ii)。陰性対照でも動けば手順を疑い保留。")
    return {"verdict": verdict, "summary": summary}


class _Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for f in self.streams:
            f.write(s)

    def flush(self):
        for f in self.streams:
            f.flush()


# ================================================================ 読み込みと実行
def load_cases(c1_dir: Path) -> dict:
    import pandas as pd
    cases = {}
    for fp in sorted(c1_dir.glob("features_case_*.csv")):
        cid = int(re.search(r"features_case_(\d+)\.csv", fp.name).group(1))
        rp = c1_dir / f"rates_case_{cid}.csv"
        if not rp.exists():
            continue
        try:
            feat, rates = pd.read_csv(fp), pd.read_csv(rp)
        except Exception:      # noqa: BLE001
            continue
        if len(feat) == 0 or "t0" not in feat or "t" not in rates:
            continue
        cases[cid] = (feat, rates)
    return cases


def run_stats(c1_dir: Path, seed: int = 0, frozen_note: str = "", out_dir: Path | None = None) -> dict:
    import pandas as pd
    cases = load_cases(c1_dir)
    if not cases:
        raise SystemExit(f"{c1_dir} に features_case_*.csv / rates_case_*.csv がありません（先に --extract）")
    confounders = OTHER_VASOACTIVE + sum(CONTROLS.values(), [])
    rows_by_set, why_all = {}, {}
    rows, why = collect_steps(cases, [PRESSOR], "フェニレフリン", confounders)
    rows_by_set["フェニレフリン"] = rows
    why_all["フェニレフリン"] = why
    n_by_case = Counter(r["caseid"] for r in rows)
    for label, cols in CONTROLS.items():
        r2, w2 = collect_steps(cases, cols, label, [PRESSOR] + OTHER_VASOACTIVE
                               + [c for c in sum(CONTROLS.values(), []) if c not in cols])
        rows_by_set[label] = r2
        why_all[label] = w2
    rng = np.random.default_rng(seed)
    rows_by_set["擬似ステップ（非投与区間）"] = pseudo_steps(cases, n_by_case, rng,
                                                        OTHER_VASOACTIVE + sum(CONTROLS.values(), []))
    out_dir = C1 if out_dir is None else out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    allrows = [r for rows in rows_by_set.values() for r in rows]
    pd.DataFrame(allrows).to_csv(out_dir / "steps.csv", index=False)
    old = sys.stdout
    with open(out_dir / "c1_report.txt", "w", encoding="utf-8") as fh:
        sys.stdout = _Tee(old, fh)
        try:
            for label, why in why_all.items():
                if why:
                    print(f"  {label}: 落としたステップ " + "、".join(f"{k} {v}" for k, v in why.items()))
            res = report(rows_by_set, len(cases), seed=seed, frozen=frozen_note)
        finally:
            sys.stdout = old
    print(f"\nステップ別の Δ: {out_dir / 'steps.csv'}\n表の全文: {out_dir / 'c1_report.txt'}")
    return res


def sap_frozen_tag() -> str | None:
    """SAP-1c を凍結したタグ（sap-1c-v*）があれば返す。無ければ None。"""
    import subprocess
    try:
        out = subprocess.run(["git", "tag", "-l", "sap-1c-v*"], cwd=ROOT, capture_output=True,
                             text=True, timeout=10).stdout.split()
    except Exception:      # noqa: BLE001
        return None
    return sorted(out)[-1] if out else None


# ================================================================ 抽出（Mac・vitaldb）
def window_c1(pleth, ecg, art, t0: float, lag: float, art15, with_pda: bool, height_m=None) -> dict:
    """1 窓分。品質不足の項目は NaN（窓ごと棄却はしない。指標ごとに前後の窓の有無で落とす）。"""
    nan = float("nan")
    i0, i1 = int(t0 * FS), int((t0 + WIN_S) * FS)
    seg_p = np.nan_to_num(np.asarray(pleth[i0:i1], float))
    seg_e = np.nan_to_num(np.asarray(ecg[i0:i1], float))
    seg_a = np.asarray(art[i0:i1], float)
    out = {"t0": float(t0), "pwtt_ms": nan, "t1_ms": nan, "t2t1_ms": nan, "hr": nan, "map": nan,
           "n_pwtt": 0, "n_t1": 0, "dt_ms": nan, "ri": nan}
    if seg_p.size < int(WIN_S * FS) * 0.9 or not np.any(seg_p):
        return out
    pw = pwtt_series(seg_e, seg_p, FS, lag=lag)
    out["n_pwtt"] = int(pw.size)
    if pw.size >= 10:
        out["pwtt_ms"] = float(np.median(pw) * 1000.0)
    t1 = art15._t1_series(np.nan_to_num(seg_a), seg_e, FS)
    out["n_t1"] = int(t1.size)
    if t1.size >= 5:
        out["t1_ms"] = float(np.median(t1) * 1000.0)
    if np.isfinite(out["pwtt_ms"]) and np.isfinite(out["t1_ms"]):
        out["t2t1_ms"] = out["pwtt_ms"] - out["t1_ms"]
    r = detect_r_peaks(seg_e, FS)
    if r.size >= 20:
        rr = np.diff(r) / FS
        rr = rr[(rr > 0.3) & (rr < 1.5)]
        if rr.size >= 10:
            out["hr"] = 60.0 / float(np.median(rr))
    a = seg_a[np.isfinite(seg_a) & (seg_a > 20) & (seg_a < 300)]
    if a.size >= int(0.5 * WIN_S * FS):
        out["map"] = float(np.mean(a))
    if with_pda:
        from src.pda import fit_beat
        beats = segment_beats(seg_p, FS, ecg=seg_e)
        good = [(s, e) for s, e in beats if sqi(seg_p[s:e], FS)["ok"]]
        dts, ris = [], []
        if len(good) >= 8:
            sigma = float(np.nanmedian([estimate_noise(seg_p[s:e]) for s, e in good]))
            n_ens, reachable = required_ensemble_size(sigma)
            if reachable and len(good) >= 2 * n_ens:
                for k in range(0, len(good) - n_ens + 1, n_ens):
                    y = ensemble_average([seg_p[s:e] for s, e in good[k:k + n_ens]])
                    tt = np.arange(len(y)) / FS
                    try:
                        fit = fit_beat(tt, y)
                    except Exception:      # noqa: BLE001
                        continue
                    if not fit.get("ok", False):
                        continue
                    m = si_ri_from_fit(fit)
                    if m["dt_s"] > 0:
                        dts.append(m["dt_s"] * 1000.0)
                        ris.append(m["ri"])
        if len(dts) >= 2:
            out["dt_ms"], out["ri"] = float(np.median(dts)), float(np.median(ris))
    return out


def _vitaldb_loader(caseid: int, rate_tracks: list):
    import vitaldb
    wav = vitaldb.load_case(caseid, WAVE_TRACKS, 1 / FS)
    arrays = {"pleth": wav[:, 0].astype(np.float32), "ecg": wav[:, 1].astype(np.float32),
              "art": wav[:, 2].astype(np.float32)}
    rates = {}
    if rate_tracks:
        num = vitaldb.load_case(caseid, rate_tracks, 1.0)
        if num is not None and num.size:
            for j, tr in enumerate(rate_tracks):
                rates[tr.split("/")[1].replace("_RATE", "")] = np.asarray(num[:, j], float)
    return arrays, rates


def extract_case_c1(caseid: int, rate_tracks: list, with_pda: bool, loader=_vitaldb_loader,
                    out_dir: Path | None = None) -> tuple:
    """1 症例の 60 秒窓の特徴量と 1 Hz のレートを data/c1/ に置く。返り値 (caseid, 窓数, エラー)。"""
    import pandas as pd
    out_dir = C1 if out_dir is None else out_dir
    fp, rp, mp = (out_dir / f"features_case_{caseid}.csv", out_dir / f"rates_case_{caseid}.csv",
                  out_dir / f"case_{caseid}_meta.json")
    tag = "pda" if with_pda else "base"
    if fp.exists() and rp.exists() and mp.exists():
        try:
            m = json.loads(mp.read_text(encoding="utf-8"))
            if m.get("v") == META_V and m.get("mode") == tag:
                return caseid, len(pd.read_csv(fp)), None
        except Exception:      # noqa: BLE001
            pass
    arrays, rates = loader(caseid, rate_tracks)
    pleth, ecg, art = arrays["pleth"], arrays["ecg"], arrays["art"]
    art15 = _load("15_art_indices.py", "m15")
    dur = len(pleth) / FS
    lag = estimate_pleth_lag(ecg, pleth, FS)
    rows = [window_c1(pleth, ecg, art, float(t0), lag, art15, with_pda)
            for t0 in np.arange(0, dur - WIN_S, WIN_S)]
    df = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(fp, index=False)
    n = max((v.size for v in rates.values()), default=0)
    rdf = pd.DataFrame({"t": np.arange(n, dtype=float)})
    for k, v in rates.items():
        col = np.full(n, np.nan)
        col[:v.size] = v
        rdf[k] = col
    rdf.to_csv(rp, index=False)
    mp.write_text(json.dumps({"v": META_V, "mode": tag, "caseid": caseid, "duration_min": round(dur / 60, 1),
                              "pleth_lag_ms": round(lag * 1000) if np.isfinite(lag) else None,
                              "n_windows": len(df),
                              "n_t2t1": int(np.isfinite(df["t2t1_ms"]).sum()) if len(df) else 0,
                              "rate_tracks": sorted(rates)}, ensure_ascii=False), encoding="utf-8")
    return caseid, len(df), None


def _extract_one(args_tuple):
    caseid, rate_tracks, with_pda = args_tuple
    try:
        return extract_case_c1(caseid, rate_tracks, with_pda)
    except Exception as e:      # noqa: BLE001
        return caseid, None, f"失敗: {e}"


def run_extract(limit: int, jobs: int, with_pda: bool) -> None:
    import pandas as pd
    trks_p = DATA / "trks.csv"
    if not trks_p.exists():
        raise SystemExit("data/trks.csv がありません（先に scripts/01_track_inventory.py。Mac で）")
    t = pd.read_csv(trks_p)
    by_case = {int(c): set(g["tname"]) for c, g in t.groupby("caseid")}
    todo = []
    for cid, names in sorted(by_case.items()):
        if not all(w in names for w in WAVE_TRACKS) or RATE_TRACK(PRESSOR) not in names:
            continue
        rate_tracks = sorted(n for n in names if n.startswith("Orchestra/") and n.endswith("_RATE"))
        todo.append((cid, rate_tracks, with_pda))
        if len(todo) >= limit:
            break
    print(f"PLETH・ECG・ART と {RATE_TRACK(PRESSOR)} を持つ症例 {len(todo)} 例を抽出します（jobs={jobs}）")
    done, fail = 0, Counter()
    if jobs > 1:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(max_workers=jobs) as ex:
            futs = [ex.submit(_extract_one, a) for a in todo]
            for f in as_completed(futs):
                cid, n, err = f.result()
                if err:
                    fail[err[:40]] += 1
                    print(f"  case {cid}: {err}", flush=True)
                else:
                    done += 1
    else:
        for a in todo:
            cid, n, err = _extract_one(a)
            if err:
                fail[err[:40]] += 1
                print(f"  case {cid}: {err}", flush=True)
            else:
                done += 1
    print(f"完了 {done} 例。失敗 {sum(fail.values())} 例 {dict(fail)}")


# ================================================================ 自己検証
def _synth_cases(n_cases: int, effect_ms: float, seed: int, dur_min: int = 90) -> dict:
    """統計段の合成材料。60 秒窓の特徴量と 1 Hz のレートを、既知のステップと効果で作る。"""
    import pandas as pd
    rng = np.random.default_rng(seed)
    cases = {}
    for k in range(n_cases):
        cid = 1000 + k
        n_s = dur_min * 60
        t = np.arange(n_s, dtype=float)
        phen = np.zeros(n_s)
        # 増量 → 減量 → 増量（ランプ）→ 減量、を時間をずらして置く。最後のは 120 秒しか保たない（数えない）
        lvl = float(rng.uniform(0.2, 0.6))
        plan = [(600, lvl), (1500, lvl * 1.6), (2400, lvl * 0.9), (3000, lvl * 0.95), (3060, lvl * 1.0),
                (3120, lvl * 1.5), (4000, lvl * 0.7), (4900, lvl * 1.4), (5020, lvl * 0.7)]
        for ts, v in plan:
            phen[ts:] = v
        rftn = np.full(n_s, 0.1)
        rftn[700:] = 0.15                      # フェニレフリン増量の 100 秒後 → 交絡でフェニレフリンのステップが落ちる
        rftn[2000:] = 0.1
        ppf = np.full(n_s, 4.0)
        ppf[3600:] = 5.5
        nepi = np.zeros(n_s)
        nepi[4050:] = 0.05                     # 4000 秒の減量の直後 → 交絡で落ちる
        rates = pd.DataFrame({"t": t, "PHEN": phen, "RFTN20": rftn, "PPF20": ppf, "NEPI": nepi})
        # 特徴量: T2−T1 はフェニレフリンの水準に比例して短縮（効果は増量で −effect_ms）
        t0s = np.arange(0, n_s - WIN_S, WIN_S)
        base = 30.0 + rng.normal(0, 4)
        lv = np.array([np.nan_to_num(phen[int(t0):int(t0 + WIN_S)]).mean() for t0 in t0s])
        rel = (lv - lvl) / max(lvl * 0.6, 1e-9)         # 増量ステップ（×1.6）で 1
        t2t1 = base - effect_ms * rel + rng.normal(0, 0.8, t0s.size)
        t1 = 180.0 + 4.0 * rel + rng.normal(0, 1.5, t0s.size)
        mapv = 75.0 + 10.0 * rel + rng.normal(0, 2, t0s.size)
        hr = 70.0 - 5.0 * rel + rng.normal(0, 1.5, t0s.size)
        feat = pd.DataFrame({"t0": t0s, "pwtt_ms": 660.0 + t1 + t2t1, "t1_ms": t1, "t2t1_ms": t2t1,
                             "hr": hr, "map": mapv})
        drop = rng.random(t0s.size) < 0.1           # 品質で落ちた窓
        cases[cid] = (feat[~drop].reset_index(drop=True), rates)
    return cases


def _synth_waveforms(dur_s: float, t2t1_before_s: float, t2t1_after_s: float, t_switch: float,
                     seed: int = 0):
    """抽出段の合成材料: 心電図・動脈圧・脈波。脈波の足は R + T1 + (T2−T1) + 装置遅延 0.66 s。"""
    from scipy.special import erf
    rng = np.random.default_rng(seed)
    n = int(dur_s * FS)
    idx = np.arange(n)
    ecg = np.zeros(n)
    art = np.full(n, 60.0)
    pleth = np.full(n, 50.0)
    t1, lag = 0.18, 0.66
    t_r = 0.0
    while t_r < dur_s + 2:
        i_r = int(t_r * FS)
        if 0 <= i_r < n:
            ecg[i_r:i_r + 5] = 1.0
        tt = (idx - (i_r + int(t1 * FS))) / FS
        art = art + 45.0 * np.exp(-0.5 * ((tt - 0.11) / 0.055) ** 2) + 18.0 * np.exp(-0.5 * ((tt - 0.29) / 0.075) ** 2)
        art = art + 26.0 * 0.5 * (1 + erf((tt - 0.06) / (0.03 * np.sqrt(2)))) * np.exp(-np.clip(tt, 0, None) / 1.5)
        d = t2t1_before_s if t_r < t_switch else t2t1_after_s
        tp = (idx - (i_r + int(round((t1 + d + lag) * FS)))) / FS
        pleth = pleth + 40.0 * (0.5 * (1 + erf((tp - 0.05) / (0.02 * np.sqrt(2))))
                                * np.exp(-np.clip(tp, 0, None) / 0.35)
                                + 0.35 * np.exp(-0.5 * ((tp - 0.30) / 0.07) ** 2))
        t_r += float(rng.uniform(0.85, 1.05))           # RR を揺らす（遅延の枝の同定に要る）
    pleth = pleth + rng.normal(0, 0.15, n)
    art = art + rng.normal(0, 0.3, n)
    return ecg.astype(np.float32), art.astype(np.float32), pleth.astype(np.float32)


def selftest() -> int:
    import contextlib
    import io
    import tempfile
    import pandas as pd
    ok = True

    def rep(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}{('  ' + detail) if detail else ''}", flush=True)

    print("== 30_c1_dose_steps 自己検証（合成データ・ネットワーク不要） ==\n")
    # --- 1. ステップの検出
    r = np.zeros(3000)
    r[600:] = 0.4
    r[1500:] = 0.64            # +60%
    r[2000:] = 0.66            # +3%（数えない）
    r[2500:] = 0.4             # −39%
    r[2900:] = 0.8             # 100 秒しか保たない（数えない）
    st = dose_steps(r)
    rep("用量ステップの検出（on・+60%・−39% の 3 つ。+3% と保持不足は数えない）",
        [(s["t"], s["direction"]) for s in st] == [(600.0, 1), (1500.0, 1), (2500.0, -1)],
        str([(s["t"], s["direction"]) for s in st]))
    ramp = np.zeros(3000)
    ramp[600:] = 0.4
    for k, v in enumerate((0.44, 0.48, 0.52, 0.56, 0.60)):
        ramp[1500 + 30 * k:] = v
    st2 = dose_steps(ramp)
    rep("小刻みなランプ（10% 刻み・30 秒ごと）はステップとしない（直前の定常値が無い。帰無仮説の側に寄る）",
        [s["t"] for s in st2] == [600.0], str([(s["t"], round(s["post"], 2)) for s in st2]))
    r3 = r.copy()
    r3[1400:1410] = np.nan
    rep("NaN は 0 として扱い、直前 120 秒に欠測があるステップは定常でないとして落とす（欠測の縁も拾わない）",
        [s["t"] for s in dose_steps(r3)] == [600.0, 2500.0], str([s["t"] for s in dose_steps(r3)]))
    rep("changes_within: 区間内の変化を拾い、定常なら拾わない",
        changes_within(r, 1400, 1600) and not changes_within(r, 700, 1400) and changes_within(r, 500, 700))
    # --- 2. 窓の対応づけ
    t0 = np.arange(0, 3000, 60.0)
    pre, post = pair_windows(t0, 1500.0)
    rep("前後の窓は区間に完全に入るものだけ（t=1500 → 前 1380・1440、後 1560・1620）",
        list(t0[pre]) == [1380.0, 1440.0] and list(t0[post]) == [1560.0, 1620.0])
    pre, post = pair_windows(t0, 1530.0)
    rep("グリッドからずれたステップでは前後 1 窓ずつ（t=1530 → 前 1440、後 1620）",
        list(t0[pre]) == [1440.0] and list(t0[post]) == [1620.0], f"{list(t0[pre])} / {list(t0[post])}")
    # --- 3. 統計段（効果あり）
    cases = _synth_cases(40, effect_ms=5.0, seed=1)
    with tempfile.TemporaryDirectory() as td:
        od = Path(td)
        for cid, (feat, rates) in cases.items():
            feat.to_csv(od / f"features_case_{cid}.csv", index=False)
            rates.to_csv(od / f"rates_case_{cid}.csv", index=False)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            res = run_stats(od, seed=0, frozen_note="（自己検証）", out_dir=od / "out")
        out = buf.getvalue()
        steps = pd.read_csv(od / "out" / "steps.csv")
        ph = steps[steps["set"] == "フェニレフリン"]
        # 仕込み: 増量 600（RFTN で落ちる）・1500・3120（ランプの最後）・4900（120 秒しか保たない）、
        #         減量 2400・4000（NEPI で落ちる）・5020
        per_case = ph.groupby("caseid")["t"].apply(lambda s: sorted(s))
        expect = [1500.0, 2400.0, 3120.0, 5020.0]
        exact = sum(1 for v in per_case if list(v) == expect) / max(len(per_case), 1)
        rep("フェニレフリンのステップが症例ごとに期待どおり（交絡・保持不足を落とし、ランプは 1 つ。"
            "品質で窓が落ちた症例だけ欠ける）",
            all(set(v) <= set(expect) for v in per_case) and exact >= 0.85 and len(per_case) == 40,
            f"完全一致 {exact:.0%}・例: {list(per_case.iloc[0])}")
        rep("交絡で落とした理由が出ている", "交絡" in out)
        s_inc = res["summary"][("フェニレフリン", "t2t1_ms", +1)]
        s_dec = res["summary"][("フェニレフリン", "t2t1_ms", -1)]
        rep("増量の Δ(T2−T1) が仕込んだ −5 ms を回復（±1.5）し、区間が 0 を含まない",
            abs(s_inc["mean"] + 5.0) < 1.5 and s_inc["hi"] < 0, _ci(s_inc))
        rep("減量で向きが反転する", s_dec["n"] > 0 and s_dec["mean"] > 0, _ci(s_dec))
        rep("MAP・HR で調整しても効果が残る（仕込みは独立）", np.isfinite(s_inc["adj_hi"]) and s_inc["adj_hi"] < 0,
            _ci(s_inc, "adj_b0", "adj_lo", "adj_hi"))
        ctl = [res["summary"].get(k) for k in res["summary"] if k[0] != "フェニレフリン" and k[1] == "t2t1_ms"]
        ctl = [s for s in ctl if s and s.get("n", 0) >= MIN_STEPS_CONTROL]
        rep("陰性対照（レミフェンタニル・プロポフォール・擬似）は動かない（区間が 0 を含む）",
            ctl and all(s["lo"] <= 0 <= s["hi"] for s in ctl), f"評価した群 {len(ctl)}")
        rep("擬似ステップが症例ごとに同数だけ取られている",
            (steps[steps["set"].str.startswith("擬似")].groupby("caseid").size().reindex(per_case.index).fillna(0)
             == per_case.apply(len)).all())
        rep("主要判定が「成立」", res["verdict"].startswith("成立"), res["verdict"])
        t1s = res["summary"][("フェニレフリン", "t1_ms", +1)]
        rep("副次1 ΔT1 が仕込んだ延長（+4 ms）を回復", abs(t1s["mean"] - 4.0) < 1.5, _ci(t1s))
        buf2 = io.StringIO()
        with contextlib.redirect_stdout(buf2):
            res2 = run_stats(od, seed=0, frozen_note="（自己検証）", out_dir=od / "out2")
        rep("同じ種で同じ結果（決定性）", res2["summary"][("フェニレフリン", "t2t1_ms", +1)] == s_inc)
        rep("表の全文と steps.csv が書かれる", (od / "out" / "c1_report.txt").exists() and len(steps) > 0)
    # --- 4. 統計段（効果なし・小さい症例数 → 符号検定の規則）
    cases0 = _synth_cases(12, effect_ms=0.0, seed=2)
    with tempfile.TemporaryDirectory() as td:
        od = Path(td)
        for cid, (feat, rates) in cases0.items():
            feat.to_csv(od / f"features_case_{cid}.csv", index=False)
            rates.to_csv(od / f"rates_case_{cid}.csv", index=False)
        with contextlib.redirect_stdout(io.StringIO()):
            res0 = run_stats(od, seed=0, out_dir=od / "out")
        rep("効果なし・症例 12 では符号検定に切り替わり「動かない」", res0["verdict"].startswith("動かない"),
            res0["verdict"])
    # --- 5. 判定の規則（単体）
    inc = {"n": 40, "n_cases": 35, "mean": -4.0, "lo": -5.0, "hi": -3.0, "case_med": -4.0, "sign_p": 0.001,
           "adj_b0": -3.8, "adj_lo": -5.0, "adj_hi": -2.5}
    dec = {"n": 20, "mean": 3.0}
    quiet = {"レミ": {"n": 10, "lo": -1.0, "hi": 1.0}}
    loud = {"レミ": {"n": 10, "lo": 1.0, "hi": 3.0}}
    rep("判定: 効果・反転・調整・陰性対照が揃えば成立", primary_verdict(inc, dec, quiet, 35)[0].startswith("成立"))
    rep("判定: 陰性対照が動けば保留", "保留" in primary_verdict(inc, dec, loud, 35)[0])
    rep("判定: 反転しなければ陽性としない", "反転しない" in primary_verdict(inc, {"n": 5, "mean": -1.0}, quiet, 35)[0])
    rep("判定: 調整で消えれば陽性としない",
        "調整" in primary_verdict({**inc, "adj_hi": 0.5}, dec, quiet, 35)[0])
    rep("判定: 効果が 3 ms 未満なら「動かない」", primary_verdict({**inc, "mean": -2.0, "hi": -1.0}, dec, quiet, 35)[0]
        .startswith("動かない"))
    rep("判定: 陰性対照が評価できなければ保留", "評価できない" in primary_verdict(inc, dec, {}, 35)[0])
    # --- 6. 抽出段（合成波形。脈波の足の遅延を途中で −5 ms にする）
    # 遅延は標本の整数倍にする（500 Hz: 16 → 13 標本 = −6 ms）。そうしないと丸めで仕込みがずれる
    ecg, art, pleth = _synth_waveforms(9 * 60, 0.032, 0.026, t_switch=4.5 * 60, seed=3)
    rates = {"PHEN": np.r_[np.zeros(270), np.full(270, 0.3)]}

    def loader(cid, tracks):
        return {"pleth": pleth, "ecg": ecg, "art": art}, rates
    with tempfile.TemporaryDirectory() as td:
        od = Path(td)
        cid, n, err = extract_case_c1(9001, ["Orchestra/PHEN_RATE"], False, loader=loader, out_dir=od)
        feat = pd.read_csv(od / "features_case_9001.csv")
        fin = np.isfinite(feat["t2t1_ms"]).sum()
        rep("抽出が通り、窓ごとに T2−T1・T1・HR・MAP が出る", err is None and fin >= 6
            and np.isfinite(feat["t1_ms"]).sum() >= 6 and np.isfinite(feat["hr"]).all() and np.isfinite(feat["map"]).all(),
            f"窓 {n}・T2−T1 有限 {fin}")
        pre_v = feat.loc[feat["t0"] < 4 * 60, "t2t1_ms"].median()
        post_v = feat.loc[feat["t0"] >= 5 * 60, "t2t1_ms"].median()
        rep("脈波の遅延を −6 ms にすると Δ(T2−T1) が −6 ms（±2）になる", abs((post_v - pre_v) + 6.0) < 2.0,
            f"前 {pre_v:.1f} → 後 {post_v:.1f} ms")
        rdf = pd.read_csv(od / "rates_case_9001.csv")
        rep("レートが 1 Hz の CSV に残る", list(rdf.columns) == ["t", "PHEN"] and len(rdf) == 540)
        cid2, n2, err2 = extract_case_c1(9001, ["Orchestra/PHEN_RATE"], False, loader=loader, out_dir=od)
        rep("キャッシュがあれば再抽出しない", err2 is None and n2 == n)
    # --- 7. 凍結の門番
    rep("SAP の凍結タグの照会が例外を出さない（現在: %s）" % (sap_frozen_tag() or "なし"), True)
    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


# ================================================================ main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--extract", action="store_true", help="特徴量とレートを data/c1/ に抽出（Mac・vitaldb）")
    ap.add_argument("--stats", action="store_true", help="キャッシュから統計（SAP の凍結タグが要る）")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--limit", type=int, default=10000)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--pda", action="store_true", help="凍結版 PDA の ΔT・RI も抽出（副次3・CPU を食う）")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--unfrozen-ok", action="store_true",
                    help="SAP 未凍結でも統計を出す（報告に『未凍結』と刻まれる。事前指定の確認用）")
    args = ap.parse_args()
    if args.jobs < 1:
        ap.error("--jobs は 1 以上")
    if args.selftest:
        sys.exit(selftest())
    if args.extract:
        run_extract(args.limit, args.jobs, args.pda)
    if args.stats:
        tag = sap_frozen_tag()
        if tag is None and not args.unfrozen_ok:
            raise SystemExit("SAP-1c を凍結したタグ（sap-1c-v*）がありません。SAP §8: 凍結 → タグ → Zenodo の後で"
                             "統計を出すこと。事前指定の確認のためだけに出すなら --unfrozen-ok。")
        note = (f"SAP-1c 凍結タグ: {tag}" if tag else
                "**注意: SAP-1c は未凍結。この表は事前指定の確認用であり、判定に使ってはならない。**")
        run_stats(C1, seed=args.seed, frozen_note=note)
    if not (args.extract or args.stats):
        ap.print_help()


if __name__ == "__main__":
    main()

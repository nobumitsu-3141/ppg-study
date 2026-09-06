#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【探索・事後】文献の分解手法を**その条件のまま** PWDB に当て、同じ被験者のランドマーク ΔT・RI と比べる。

**決定試験（26番・27番）の判定には使わない。閾値は動かさない。**
31番は「我々の前処理・初期値・最適化・規準」の上で基底だけを変えた。ここでは逆に、文献ごとの条件
（基底・成分数・初期値・制約・目的関数・再標本化・当てはめ区間・採否）を精読メモ
（docs/research/pda_literature_review.md）の記載どおりに再現する。記載が無い項目は我々の既定で埋め、
**逸脱表**に明記する（全文で確かめたら差し替える。表は report に必ず出る）。

問い
----
文献の条件をそのまま当てた分解由来の ΔT（前進波と反射波の成分ピークの間隔）と RI（高さ比）は、
同じ被験者の Charlton 同梱のランドマーク ΔT・RI（研究0 で成立）に届くか。

読み方（結果を見る前に固定。lab_log 追記16）
--------------------------------------------
集団  subj_no % 7 == 0（624 名。27番 B 層と同じ。結果を見て選び直さない）。全型を当てる（文献は型を選ばない）。
規準  年齢層内 Spearman が全 6 層で予測の向き、中央値 |ρ| ≥ 0.30（20・23・26番と同じ。8 名未満の層は数えない）。
届く  中央値 |ρ| が、同じ集団のランドマーク（Charlton 同梱）の値 − 0.05 以上（gate0_rules_v2 の「同等」の幅）。
採否  文献に採否規準があるもの（Wang 2013）は採用分と全例の両方、無いものは全例。
役割  文献に反射波の指定があるもの（Goswami: p_r、Couceiro: g4、2 成分の手法: 第 2 成分）はそれに従う。
      無いもの（Tigges・Wang・Basso L≥3・Fleischhauer 3 核）は 26番と同じ規則
      （前進波 = 最も早いピークで高さが最大の半分以上の成分、反射波 = 拡張期の鍵点に最も近い後続の成分）。

手法（精読メモ §1〜§7・§13）
---------------------------
  Goswami 2010      Rayleigh 2 本。段階的当てはめ（前進波は立ち上がり 0<t≤t₁ のみ・高さ ≥ 0.5h₁・tp₁ ≤ t₁、
                    反射波は 0.3t₁ ≤ D ≤ 0.9T で 0〜0.9T の二乗誤差最小。拍の終わりは合わせない）。ΔT・RI・DPS
  Tigges 2017       Normal / Log-Normal / Rayleigh / Gamma × M=1..6 を AICc で選ぶ。18 Hz 4 次 Butterworth・
                    線形基線・振幅正規化・**40 Hz へ再標本化**。推奨の Gamma M=3 も固定で併記
  Wang 2013         ガウス 4 本 → 規準を満たさなければ 5 本。鍵点重み 1〜100 の WLS、NRMSE<2%・Errx<6 ms・
                    Erry<0.01 を多基準で統合して重みを選ぶ
  Couceiro 2015     ガウス 5 本。2 次微分の a〜e 波から初期値、成分間の不等式制約（振幅の順序・位置の単調）
  Fleischhauer 2020 Gamma＋Gaussian 2 核（generic 初期値。最良の 2 核）と 3 核。Gamma は最頻値と SD で母数化
  Basso 2024        歪みガウス L=2/3/4。α 無制約・1 拍 28 標本・重みなし RSS・a₁ 最大・m 単調・評価回数の上限なし

使い方
------
    python3 scripts/33_pwdb_literature_replica.py --selftest
    python3 scripts/33_pwdb_literature_replica.py --pwdb ~/pwdb --jobs 8          （subj%7==0 の 624 名）
    python3 scripts/33_pwdb_literature_replica.py --pwdb ~/pwdb --jobs 8 --all    （全例。時間がかかる）
出力: data/pwdb/literature_replica[_all].csv と literature_replica_report[_all].txt
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src import pda2  # noqa: E402

DATA = ROOT / "data"
OUT = DATA / "pwdb"
SUBSET_MOD = 7
MARGIN = 0.05
NAN = float("nan")

METHODS = [
    ("gos",   "Goswami 2010  Rayleigh 2（段階的）",        None),
    ("tig",   "Tigges 2017   AICc 最良（4 基底×M1..6）",    None),
    ("tig3",  "Tigges 2017   Gamma M=3（推奨・固定）",       None),
    ("wang",  "Wang 2013     ガウス 4→5・WLS・MCDM",        "ok_wang"),
    ("cou",   "Couceiro 2015 ガウス 5・不等式制約",           None),
    ("fl2",   "Fleischhauer 2020 Gamma+Gauss 2（generic）",  None),
    ("fl3",   "Fleischhauer 2020 Gamma+Gauss 3",             None),
    ("bas2",  "Basso 2024    歪みガウス L=2（28 標本）",       None),
    ("bas3",  "Basso 2024    歪みガウス L=3",                 None),
    ("bas4",  "Basso 2024    歪みガウス L=4",                 None),
]
REFS = [("lm", "ランドマーク（Charlton 同梱）", "dt_lm_ms", "digital_ri"),
        ("own", "ランドマーク（自前・pda2.find_landmarks）", "dt_own_ms", "ri_own")]

# 逸脱表（手法, 項目, 文献（精読メモ）, ここでの実装, 状態）
DEVIATIONS = [
    ("共通", "前処理", "Tigges・Basso: 18 Hz 4 次 Butterworth・線形基線・最大 1。Wang・Couceiro・Goswami は記載を確認できず",
     "全手法で pda2.preprocess（18 Hz・足→足基線・最大 1）", "Tigges・Basso 一致／他は既定"),
    ("共通", "起動", "各文献は 1 組の初期値（Basso は頑健性の検証に 50 組）", "汎用初期値 ＋ 位置を ±10% ずらした 3 起動の最良", "逸脱（既定）"),
    ("共通", "最適化", "Wang・Couceiro・Basso: 内点法（fmincon）。Tigges・Fleischhauer は記載を確認できず",
     "境界のみ: scipy least_squares（信頼領域）。不等式制約あり: SLSQP", "逸脱（代替）"),
    ("共通", "指標", "Goswami ΔT=tp₂−tp₁・RI=p₂/p₁、Couceiro T1_d・R1_d（g4）。他は ΔT・RI の定義を確認できず",
     "文献の指定があればそれ、無ければ 26番の役割規則", "Goswami・Couceiro 一致／他は既定"),
    ("Goswami", "拍の平均", "3〜5 拍の時間平均", "PWDB は 1 拍のみ", "逸脱（データ）"),
    ("Goswami", "Rayleigh の式", "記載を確認できず（Rayleigh 関数と記述）",
     "f=a·(t−D)/σ²·exp(−(t−D)²/2σ²)（標準形。ピークは D+σ）", "既定"),
    ("Tigges", "基底の式", "精読メモの 4 式", "同じ式。Gamma は t=0 から立ち上がる（到達時刻の母数なし）", "一致"),
    ("Tigges", "AICc の母数の数", "記載を確認できず", "k = 3M", "既定"),
    ("Tigges", "初期値・境界", "記載を確認できず", "汎用初期値（位置を等間隔）", "既定"),
    ("Wang", "鍵点", "頂点と谷（crest・trough）。2 次微分の特徴点 D1〜D4 から初期値", "鍵点 = S・切痕・D（pda2.find_landmarks）。初期値は汎用", "逸脱（既定）"),
    ("Wang", "重みの候補", "1〜100 の 100 通り", "1・2・5・10・20・50・100 の 7 通り", "逸脱（間引き）"),
    ("Wang", "MCDM", "3 規準を多基準意思決定で統合（方式の記載を確認できず）",
     "3 規準を満たす重みのうち NRMSE 最小。無ければ 3 規準の順位和が最小", "既定"),
    ("Couceiro", "初期値", "a〜e 波（2 次微分）＋ Wf", "a〜e 波を検出し g1〜g5 の中心に当てる（Wf は不明。無ければ汎用）", "逸脱（一部）"),
    ("Couceiro", "制約", "精読メモの不等式（a₁≤a₂, a₁≤a₃, a₃≤a₂, a₄≤a₂, a₅≤a₂, a₅≤a₄, b₁≤b₂<b₃≤b₄≤b₅）", "同じ不等式を SLSQP で", "一致"),
    ("Fleischhauer", "generic 初期値の数値", "記載を確認できず（表があるはず）", "最頻値 0.15T／0.5T／0.75T、SD 0.08T／0.1T、高さ 1／0.4／0.2", "既定"),
    ("Fleischhauer", "目的関数", "評価は 2 次微分の NRMSE。当てはめの目的関数は記載を確認できず", "重みなし二乗和（原波形）", "既定"),
    ("Basso", "α の範囲", "無制約（[−∞, +∞]）", "[−50, 50]（数値上の代用）", "逸脱（代替）"),
    ("Basso", "再標本化・目的関数・制約", "28 標本・重みなし RSS・a₁ 最大・m 単調・評価回数の上限なし", "同じ（SLSQP maxiter 2000）", "一致"),
]


def _load(stem: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / stem)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# ================================================================ 基底
def gauss(t, h, mu, s):
    return h * np.exp(-0.5 * ((t - mu) / max(s, 1e-6)) ** 2)


def lognorm(t, h, tp, s):
    """対数正規。ピーク高さ h を時刻 tp でとる（μ = ln tp）。"""
    tt = np.clip(t, 1e-4, None)
    return h * np.exp(-0.5 * ((np.log(tt) - np.log(max(tp, 1e-4))) / max(s, 1e-6)) ** 2)


def rayleigh_tigges(t, a, b, s):
    """精読メモの Tigges 式 a·t·exp(−(t−b)²/2σ²)。"""
    return a * t * np.exp(-0.5 * ((t - b) / max(s, 1e-6)) ** 2)


def rayleigh_goswami(t, h, D, s):
    """標準形の Rayleigh を到達時刻 D だけずらす。ピークは D+σ で高さ h。"""
    s = max(s, 1e-4)
    u = np.asarray(t, float) - D
    out = np.zeros_like(u)
    pos = u > 0
    out[pos] = h * np.sqrt(np.e) * (u[pos] / s) * np.exp(-0.5 * (u[pos] / s) ** 2)
    return out


def gamma_tigges(t, h, tp, shape):
    """t=0 から立ち上がるガンマ（到達時刻なし）。ピーク高さ h を時刻 tp でとる。"""
    return pda2.gamma_peak(t, h, tp, rise=tp, shape=shape)


def gamma_mode_sd(t, h, m, s):
    """Fleischhauer の母数化: 最頻値 m と SD s のガンマ（t=0 から）。形状 α は閉じた式で。"""
    m = max(m, 1e-4)
    s = max(s, 1e-4)
    q = 2 * s * s + m * m
    alpha = (q + np.sqrt(max(q * q - 4 * s ** 4, 0.0))) / (2 * s * s)
    return pda2.gamma_peak(t, h, m, rise=m, shape=max(alpha, 1.05))


def comp_eval(kind, t, p):
    if kind == "normal":
        return gauss(t, *p)
    if kind == "lognormal":
        return lognorm(t, *p)
    if kind == "rayleigh":
        return rayleigh_tigges(t, *p)
    if kind == "gamma":
        return gamma_tigges(t, *p)
    if kind == "gamma_ms":
        return gamma_mode_sd(t, *p)
    if kind == "skew":
        return pda2.skew_peak(t, *p)
    raise ValueError(kind)


def comp_peak(kind, t, p):
    """成分のピーク時刻と高さ。"""
    if kind == "rayleigh":
        tt = np.linspace(0, float(t[-1]), 2000)
        y = rayleigh_tigges(tt, *p)
        i = int(np.argmax(y))
        return float(tt[i]), float(y[i])
    return float(p[1]), float(p[0])


NPAR = {"normal": 3, "lognormal": 3, "rayleigh": 3, "gamma": 3, "gamma_ms": 3, "skew": 4}


def model_sum(kinds, t, x):
    """kinds: 成分ごとの基底の並び。x: 母数を連結したもの。"""
    y = np.zeros_like(t)
    j = 0
    for k in kinds:
        n = NPAR[k]
        y = y + comp_eval(k, t, x[j:j + n])
        j += n
    return y


def split_params(kinds, x):
    out, j = [], 0
    for k in kinds:
        n = NPAR[k]
        out.append(x[j:j + n])
        j += n
    return out


# ================================================================ 当てはめの部品
def _lsq(resid, x0s, lo, hi, max_nfev=3000):
    from scipy.optimize import least_squares
    best = None
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    for x0 in x0s:
        x0 = np.clip(np.asarray(x0, float), lo + 1e-9, hi - 1e-9)
        try:
            r = least_squares(resid, x0, bounds=(lo, hi), max_nfev=max_nfev, x_scale="jac")
        except Exception:      # noqa: BLE001
            continue
        if best is None or r.cost < best.cost:
            best = r
    return best


def _slsqp(fun, x0s, lo, hi, cons, maxiter=2000):
    from scipy.optimize import minimize
    best = None
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    for x0 in x0s:
        x0 = np.clip(np.asarray(x0, float), lo + 1e-9, hi - 1e-9)
        try:
            r = minimize(fun, x0, method="SLSQP", bounds=list(zip(lo, hi)), constraints=cons,
                         options={"maxiter": maxiter, "ftol": 1e-10})
        except Exception:      # noqa: BLE001
            continue
        if not np.all(np.isfinite(r.x)):
            continue
        if best is None or r.fun < best.fun:
            best = r
    return best


def _starts(x0, pos_idx, T, shifts=(0.0, -0.1, 0.1)):
    """汎用初期値と、位置母数を ±10%T ずらした起動。"""
    out = []
    for s in shifts:
        x = np.array(x0, float)
        for i in pos_idx:
            x[i] = x[i] + s * T
        out.append(x)
    return out


def _generic(kind, M, T):
    """汎用初期値と境界（基底ごと・M 成分）。位置は 0.12T〜0.80T に等間隔。"""
    pos = np.linspace(0.12 * T, 0.80 * T, M) if M > 1 else np.array([0.2 * T])
    hs = [1.0, 0.5, 0.35, 0.25, 0.2, 0.15][:M]
    x0, lo, hi, pos_idx = [], [], [], []
    for i in range(M):
        if kind in ("normal", "lognormal"):
            s0 = 0.06 * T if kind == "normal" else 0.35
            x0 += [hs[i], pos[i], s0]
            lo += [0.0, 0.01 * T, 0.004 * T if kind == "normal" else 0.02]
            hi += [2.0, 0.98 * T, 0.6 * T if kind == "normal" else 2.5]
        elif kind == "rayleigh":
            x0 += [hs[i] / max(pos[i], 1e-3), pos[i], 0.06 * T]
            lo += [0.0, 0.01 * T, 0.004 * T]
            hi += [50.0 / T, 0.98 * T, 0.6 * T]
        elif kind == "gamma":
            x0 += [hs[i], pos[i], 6.0]
            lo += [0.0, 0.01 * T, 1.05]
            hi += [2.0, 0.98 * T, 80.0]
        elif kind == "gamma_ms":
            x0 += [hs[i], pos[i], 0.08 * T]
            lo += [0.0, 0.01 * T, 0.01 * T]
            hi += [2.0, 0.98 * T, 0.6 * T]
        elif kind == "skew":
            x0 += [hs[i], pos[i], 0.06 * T, 0.0]
            lo += [0.0, 0.01 * T, 0.004 * T, -50.0]
            hi += [2.0, 0.98 * T, 0.6 * T, 50.0]
        pos_idx.append(len(x0) - NPAR[kind] + 1)
    return np.array(x0), np.array(lo), np.array(hi), pos_idx


def pick_roles(comps, lm, min_gap=0.03):
    """26番と同じ役割規則。comps: [(tp, h), ...]。返り値 (前進波の添字, 反射波の添字 or None)。"""
    if not comps:
        return None, None
    hmax = max(h for _, h in comps)
    order = sorted(range(len(comps)), key=lambda i: comps[i][0])
    fwd = next((i for i in order if comps[i][1] >= 0.5 * hmax), order[0])
    cand = [i for i in range(len(comps)) if comps[i][0] > comps[fwd][0] + min_gap]
    if not cand:
        return fwd, None
    dia = lm.get("dia_t", NAN) if lm else NAN
    if np.isfinite(dia):
        ref = min(cand, key=lambda i: abs(comps[i][0] - dia))
    else:
        ref = max(cand, key=lambda i: comps[i][1])
    return fwd, ref


def _indices_from(comps, lm, fwd=None, ref=None):
    if fwd is None or ref is None:
        fwd, ref = pick_roles(comps, lm)
    if fwd is None or ref is None:
        return NAN, NAN
    (tf, hf), (tr, hr) = comps[fwd], comps[ref]
    return float((tr - tf) * 1000.0), float(hr / hf) if hf > 0 else NAN


def _resample(t, y, fs_new=None, n=None):
    T = float(t[-1]) + float(t[1] - t[0])
    tn = np.linspace(0.0, T, int(n), endpoint=False) if n else np.arange(0.0, T, 1.0 / fs_new)
    return tn, np.interp(tn, t, y)


# ================================================================ 各文献
def fit_goswami(t, ys, lm) -> dict:
    """Rayleigh 2 本の段階的当てはめ（精読メモ §7）。"""
    out = {"dt_gos_ms": NAN, "ri_gos": NAN, "dps_gos_ms": NAN}
    t_s = float(lm["sys_t"])
    h1 = float(lm["sys_v"])
    if not np.isfinite(t_s) or t_s <= 0.02:
        return out
    T = float(t[-1])
    m1 = t <= t_s

    def r1(x):                                   # 前進波: 立ち上がりだけ。tp₁=D+σ ≤ t₁ は罰則で
        h, D, s = x
        pen = max(0.0, (D + s) - t_s) * 50.0
        return np.r_[rayleigh_goswami(t[m1], h, D, s) - ys[m1], pen]
    x0s = [[h1, 0.0, max(t_s * f, 0.01)] for f in (1.0, 0.7, 0.5)]
    f1 = _lsq(r1, x0s, [0.5 * h1, 0.0, 0.005], [1.5, t_s, max(t_s, 0.01)])
    if f1 is None:
        return out
    h, D, s = f1.x
    pf = rayleigh_goswami(t, h, D, s)
    m2 = t <= 0.9 * T

    def r2(x):                                   # 反射波: 0〜0.9T で全体の二乗誤差。拍の終わりは合わせない
        h2, D2, s2 = x
        return (pf + rayleigh_goswami(t, h2, D2, s2) - ys)[m2]
    D_lo, D_hi = 0.3 * t_s, 0.9 * T
    x0s = [[0.4, D_lo + f * (D_hi - D_lo), 0.08 * T] for f in (0.2, 0.4, 0.6)]
    f2 = _lsq(r2, x0s, [0.0, D_lo, 0.01], [1.5, D_hi, 0.6 * T])
    if f2 is None:
        return out
    h2, D2, s2 = f2.x
    out["dt_gos_ms"] = float(((D2 + s2) - (D + s)) * 1000.0)
    out["ri_gos"] = float(h2 / h) if h > 0 else NAN
    out["dps_gos_ms"] = float((s2 - s) * 1000.0)
    return out


TIGGES_BASES = ("normal", "lognormal", "rayleigh", "gamma")


def _aicc(rss, n, k):
    if n - k - 1 <= 0 or rss <= 0:
        return np.inf
    return n * np.log(rss / n) + 2 * k + 2 * k * (k + 1) / (n - k - 1)


def fit_tigges(t, ys, lm) -> dict:
    """4 基底 × M=1..6 を 40 Hz で当て、AICc で選ぶ。Gamma M=3 も固定で。"""
    out = {"dt_tig_ms": NAN, "ri_tig": NAN, "tig_best": "", "dt_tig3_ms": NAN, "ri_tig3": NAN}
    t40, y40 = _resample(t, ys, fs_new=40.0)
    T = float(t[-1])
    n = len(y40)
    best = None
    for kind in TIGGES_BASES:
        for M in range(1, 7):
            x0, lo, hi, pos_idx = _generic(kind, M, T)
            kinds = [kind] * M
            f = _lsq(lambda x, kinds=kinds: model_sum(kinds, t40, x) - y40, _starts(x0, pos_idx, T), lo, hi)
            if f is None:
                continue
            rss = float(np.sum(f.fun ** 2))
            a = _aicc(rss, n, 3 * M)
            comps = [comp_peak(kind, t, p) for p in split_params(kinds, f.x)]
            if kind == "gamma" and M == 3:
                out["dt_tig3_ms"], out["ri_tig3"] = _indices_from(comps, lm)
            if best is None or a < best[0]:
                best = (a, kind, M, comps)
    if best is not None:
        out["tig_best"] = f"{best[1]} M={best[2]}"
        out["dt_tig_ms"], out["ri_tig"] = _indices_from(best[3], lm)
    return out


WANG_WEIGHTS = (1, 2, 5, 10, 20, 50, 100)


def fit_wang(t, ys, lm) -> dict:
    """ガウス 4→5、鍵点重み 1〜100 の WLS、3 規準の多基準で重みを選ぶ。"""
    out = {"dt_wang_ms": NAN, "ri_wang": NAN, "ok_wang": 0, "w_wang": NAN, "M_wang": 0,
           "nrmse_wang": NAN, "errx_wang_ms": NAN}
    T = float(t[-1])
    chosen = None
    for M in (4, 5):
        x0, lo, hi, pos_idx = _generic("normal", M, T)
        kinds = ["normal"] * M
        cands = []
        for wk in WANG_WEIGHTS:
            w = pda2._weights(t, lm, float(wk))
            sw = np.sqrt(w)
            f = _lsq(lambda x, kinds=kinds: sw * (model_sum(kinds, t, x) - ys), _starts(x0, pos_idx, T), lo, hi)
            if f is None:
                continue
            yhat = model_sum(kinds, t, f.x)
            acc = pda2.acceptance(t, ys, yhat, lm, w)
            cands.append((wk, f, acc))
        if not cands:
            continue
        ok = [c for c in cands if c[2]["ok"]]
        if ok:
            chosen = min(ok, key=lambda c: c[2]["nrmse"])
        else:                                  # 順位和が最小
            def rank(vals):
                order = np.argsort(np.argsort(vals))
                return order
            r = (rank([c[2]["nrmse"] for c in cands]) + rank([c[2]["errx_ms"] for c in cands])
                 + rank([c[2]["erry"] for c in cands]))
            chosen = cands[int(np.argmin(r))]
        out["M_wang"] = M
        if chosen[2]["ok"]:
            break
    if chosen is None:
        return out
    wk, f, acc = chosen
    kinds = ["normal"] * out["M_wang"]
    comps = [comp_peak("normal", t, p) for p in split_params(kinds, f.x)]
    out["dt_wang_ms"], out["ri_wang"] = _indices_from(comps, lm)
    out.update(ok_wang=int(bool(acc["ok"])), w_wang=float(wk), nrmse_wang=float(acc["nrmse"]),
               errx_wang_ms=float(acc["errx_ms"]))
    return out


def _abcde(t, ys):
    """2 次微分の a〜e 波の時刻（見つかった分だけ）。"""
    dt = float(t[1] - t[0])
    d2 = np.gradient(np.gradient(ys, dt), dt)
    n = len(t)
    lim = int(0.75 * n)
    ext = []            # (時刻, 種類)
    for i in range(1, lim - 1):
        if d2[i] > d2[i - 1] and d2[i] >= d2[i + 1]:
            ext.append((float(t[i]), "max", float(d2[i])))
        elif d2[i] < d2[i - 1] and d2[i] <= d2[i + 1]:
            ext.append((float(t[i]), "min", float(d2[i])))
    if not ext:
        return {}
    # a = 最初の大きな極大（振幅の 20% 以上）、以後 b, c, d, e を交互に
    amax = max(abs(v) for _, _, v in ext)
    seq, want = [], "max"
    for tt, kind, v in ext:
        if kind == want and (len(seq) or abs(v) >= 0.2 * amax):
            seq.append(tt)
            want = "min" if want == "max" else "max"
        if len(seq) == 5:
            break
    return dict(zip("abcde", seq))


def fit_couceiro(t, ys, lm) -> dict:
    """ガウス 5 本・a〜e 波からの初期値・不等式制約（SLSQP）。T1_d・R1_d（g4）。"""
    out = {"dt_cou_ms": NAN, "ri_cou": NAN, "cou_init": ""}
    T = float(t[-1])
    t_s = float(lm["sys_t"])
    w = _abcde(t, ys)
    if all(k in w for k in "abcde"):
        cen = [0.5 * (w["a"] + w["b"]), t_s, 0.5 * (w["c"] + w["d"]),
               float(lm["dia_t"]) if np.isfinite(lm.get("dia_t", NAN)) else w["e"] + 0.05, 0.85 * T]
        out["cou_init"] = "abcde"
    else:
        cen = [0.08 * T, max(t_s, 0.1 * T), 0.3 * T, 0.5 * T, 0.75 * T]
        out["cou_init"] = "generic"
    cen = list(np.clip(cen, 0.01 * T, 0.97 * T))
    amp = [0.5, 1.0, 0.4, 0.3, 0.15]
    sig = [0.04 * T, 0.06 * T, 0.06 * T, 0.08 * T, 0.10 * T]
    x0 = np.array([v for trip in zip(amp, cen, sig) for v in trip])
    lo = np.array([0.0, 0.0, 0.004 * T] * 5)
    hi = np.array([1.5, T, 0.5 * T] * 5)
    kinds = ["normal"] * 5

    def sse(x):
        return float(np.sum((model_sum(kinds, t, x) - ys) ** 2))
    A = lambda i: 3 * i          # noqa: E731  振幅の添字
    B = lambda i: 3 * i + 1      # noqa: E731  位置の添字
    cons = [{"type": "ineq", "fun": (lambda x, i=i, j=j: x[A(j)] - x[A(i)])}
            for i, j in ((0, 1), (0, 2), (2, 1), (3, 1), (4, 1), (4, 3))]
    cons += [{"type": "ineq", "fun": (lambda x, i=i: x[B(i + 1)] - x[B(i)] - (0.005 if i == 1 else 0.0))}
             for i in range(4)]
    f = _slsqp(sse, _starts(x0, [1, 4, 7, 10, 13], T, shifts=(0.0, -0.05, 0.05)), lo, hi, cons)
    if f is None:
        return out
    p = split_params(kinds, f.x)
    tt = np.linspace(0, T, 2000)
    yf = gauss(tt, *p[0]) + gauss(tt, *p[1])      # g1+g2 = 主前進波
    i = int(np.argmax(yf))
    tf, hf = float(tt[i]), float(yf[i])
    out["dt_cou_ms"] = float((p[3][1] - tf) * 1000.0)
    out["ri_cou"] = float(p[3][0] / hf) if hf > 0 else NAN
    return out


def fit_fleischhauer(t, ys, lm, n_kernels: int) -> dict:
    """Gamma（最頻値・SD）＋ Gaussian。generic 初期値。"""
    tag = f"fl{n_kernels}"
    out = {f"dt_{tag}_ms": NAN, f"ri_{tag}": NAN}
    T = float(t[-1])
    kinds = ["gamma_ms"] + ["normal"] * (n_kernels - 1)
    pos = [0.15 * T, 0.5 * T, 0.75 * T][:n_kernels]
    hs = [1.0, 0.4, 0.2][:n_kernels]
    sd = [0.08 * T, 0.10 * T, 0.10 * T][:n_kernels]
    x0 = np.array([v for trip in zip(hs, pos, sd) for v in trip])
    lo = np.array([0.0, 0.02 * T, 0.01 * T] + [0.0, 0.1 * T, 0.01 * T] * (n_kernels - 1))
    hi = np.array([2.0, 0.6 * T, 0.5 * T] + [2.0, 0.98 * T, 0.5 * T] * (n_kernels - 1))
    pos_idx = [1 + 3 * i for i in range(n_kernels)]
    f = _lsq(lambda x: model_sum(kinds, t, x) - ys, _starts(x0, pos_idx, T), lo, hi)
    if f is None:
        return out
    comps = [comp_peak(k, t, p) for k, p in zip(kinds, split_params(kinds, f.x))]
    if n_kernels == 2:
        out[f"dt_{tag}_ms"], out[f"ri_{tag}"] = _indices_from(comps, lm, 0, 1)
    else:
        out[f"dt_{tag}_ms"], out[f"ri_{tag}"] = _indices_from(comps, lm)
    return out


def fit_basso(t, ys, lm, L: int) -> dict:
    """歪みガウス L 本。α 無制約（±50）・28 標本・重みなし RSS・a₁ 最大・m 単調（SLSQP）。"""
    tag = f"bas{L}"
    out = {f"dt_{tag}_ms": NAN, f"ri_{tag}": NAN, f"alpha_{tag}": NAN}
    T = float(t[-1])
    t28, y28 = _resample(t, ys, n=28)
    kinds = ["skew"] * L
    pos = {2: (0.15, 0.45), 3: (0.15, 0.40, 0.65), 4: (0.12, 0.30, 0.50, 0.75)}[L]
    hs = (1.0, 0.5, 0.3, 0.2)[:L]
    x0 = np.array([v for quad in zip(hs, [p * T for p in pos], [0.06 * T] * L, [0.0] * L) for v in quad])
    lo = np.array([0.0, 0.01 * T, 0.004 * T, -50.0] * L)
    hi = np.array([2.0, 0.98 * T, 0.6 * T, 50.0] * L)

    def rss(x):
        return float(np.sum((model_sum(kinds, t28, x) - y28) ** 2))
    cons = [{"type": "ineq", "fun": (lambda x, k=k: x[0] - x[4 * k])} for k in range(1, L)]
    cons += [{"type": "ineq", "fun": (lambda x, k=k: x[4 * (k + 1) + 1] - x[4 * k + 1])} for k in range(L - 1)]
    f = _slsqp(rss, _starts(x0, [4 * k + 1 for k in range(L)], T), lo, hi, cons)
    if f is None:
        return out
    p = split_params(kinds, f.x)
    comps = [(float(q[1]), float(q[0])) for q in p]
    out[f"alpha_{tag}"] = float(p[0][3])
    if L == 2:
        out[f"dt_{tag}_ms"], out[f"ri_{tag}"] = _indices_from(comps, lm, 0, 1)
    else:
        out[f"dt_{tag}_ms"], out[f"ri_{tag}"] = _indices_from(comps, lm)
    return out


# ================================================================ 1 被験者
def replica_for_subject(args_tuple) -> dict:
    subj, row, hr, M = args_tuple
    out = {"subj_no": int(subj)}
    try:
        y, fs = M.beat_of(row, hr)
        if y is None:
            out["err"] = "no_beat"
            return out
        t = np.arange(y.size) / fs
        ys, _amp = pda2.preprocess(t, y, fs)
        if ys is None:
            out["err"] = "preprocess_none"
            return out
        lm = pda2.find_landmarks(t, ys)
        out["klass_own"] = int(lm["klass"])
        out["dt_own_ms"] = float((lm["dia_t"] - lm["sys_t"]) * 1000.0) if lm["klass"] in (1, 3) else NAN
        out["ri_own"] = float(lm["dia_v"] / lm["sys_v"]) if (lm["klass"] in (1, 3) and np.isfinite(lm["dia_v"])) else NAN
        for fn in (lambda: fit_goswami(t, ys, lm), lambda: fit_tigges(t, ys, lm), lambda: fit_wang(t, ys, lm),
                   lambda: fit_couceiro(t, ys, lm), lambda: fit_fleischhauer(t, ys, lm, 2),
                   lambda: fit_fleischhauer(t, ys, lm, 3), lambda: fit_basso(t, ys, lm, 2),
                   lambda: fit_basso(t, ys, lm, 3), lambda: fit_basso(t, ys, lm, 4)):
            try:
                out.update(fn())
            except Exception as e:      # noqa: BLE001
                out["err"] = (out.get("err", "") + "|" + str(e))[:80]
    except Exception as e:      # noqa: BLE001
        out["err"] = str(e)[:80]
    return out


def _worker(args_tuple):
    subj, row, hr = args_tuple
    M = sys.modules.get("m20") or _load("20_pwdb_validity.py", "m20")
    return replica_for_subject((subj, row, hr, M))


# ================================================================ 構築と報告
def build(root: Path, subset: str = "mod7", jobs: int = 1, limit: int = 0):
    import pandas as pd
    C = _load("26_pwdb_compare.py", "m26")
    M = C.M
    hae, cfg, ppg, _ = M.load_pwdb(Path(root).expanduser())
    hr_by = dict(zip(hae["subj_no"].astype(int), hae["HR"].astype(float)))
    work = []
    for i in range(len(ppg)):
        subj = int(ppg.iloc[i, 0])
        if subset == "mod7" and subj % SUBSET_MOD != 0:
            continue
        work.append((subj, ppg.iloc[i].to_numpy(float), hr_by.get(subj, np.nan)))
        if limit and len(work) >= limit:
            break
    print(f"{len(work)} 名に文献 {len(METHODS)} 条件の分解を当てます（jobs={jobs}）", flush=True)
    if jobs > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=jobs) as ex:
            rows = list(ex.map(_worker, work, chunksize=4))
    else:
        rows = []
        for k, wk in enumerate(work, 1):
            rows.append(_worker(wk))
            if k % 25 == 0:
                print(f"  [{k}/{len(work)}]", flush=True)
    rep = pd.DataFrame(rows)
    d = C.L.load(Path(root).expanduser(), pda_dir=Path(root).expanduser() / "__no_pda__")
    d = d.drop(columns=[c for c in ("dt_pda_ms", "ri_pda", "ok2") if c in d.columns])
    d = d.merge(rep, on="subj_no", how="inner")
    d["pda2_version"] = pda2.code_version()
    return d, C


def report(d, C, out_dir: Path | None = None, tag: str = "") -> dict:
    out_dir = OUT if out_dir is None else out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    d.to_csv(out_dir / f"literature_replica{tag}.csv", index=False)
    ages = sorted(d["age"].dropna().unique().tolist())
    n_full = len(ages)
    res = {}

    def cell(col, tgt, sign, src):
        j = C._judge_or_none(src, col, tgt, sign)
        if not j:
            return NAN, "—", "—"
        v = C._verdict(j, sign, n_full)
        return j["med_abs"], f"{j['n_ok']}/{j['n_ages']}", v

    print("=" * 110)
    print("文献の条件をそのまま当てた分解 vs 同じ被験者のランドマーク（PWDB）。**探索であり判定には使わない**")
    print("=" * 110)
    print(f"被験者 {len(d)} 名（{'subj_no % 7 == 0' if tag == '' else '全例'}）・年齢層 {[int(a) for a in ages]}・"
          f"型 1/3/4+: {int((d['klass_own'] == 1).sum())}/{int((d['klass_own'] == 3).sum())}/"
          f"{int((d['klass_own'] >= 4).sum())}")
    print("規準: 年齢層内 Spearman が全層で予測の向き、中央値 |ρ| ≥ 0.30。届く = ランドマーク（Charlton）の値 − 0.05 以上")
    lm_dt, _, _ = cell("dt_lm_ms", "PWV_a", -1, d)
    lm_ri, _, _ = cell("digital_ri", "pvr", +1, d)
    print(f"\n{'手法':<46}{'n':>5}{'採択':>7}{'ΔT×PWV |ρ|':>12}{'層':>6}{'判定':>8}{'届く':>5}"
          f"{'RI×pvr |ρ|':>12}{'層':>6}{'判定':>8}{'届く':>5}{'ΔT 型1のみ':>11}")

    def line(label, dtc, ric, src, extra=""):
        n = int(src[dtc].notna().sum()) if dtc in src else 0
        a, la, va = cell(dtc, "PWV_a", -1, src)
        b, lb, vb = cell(ric, "pvr", +1, src)
        s1 = src[src["klass_own"] == 1]
        c, lc, _vc = cell(dtc, "PWV_a", -1, s1)
        reach_a = "○" if (np.isfinite(a) and np.isfinite(lm_dt) and a >= lm_dt - MARGIN) else ("—" if not np.isfinite(a) else "×")
        reach_b = "○" if (np.isfinite(b) and np.isfinite(lm_ri) and b >= lm_ri - MARGIN) else ("—" if not np.isfinite(b) else "×")
        fa = f"{a:.3f}" if np.isfinite(a) else "—"
        fb = f"{b:.3f}" if np.isfinite(b) else "—"
        fc = f"{c:.3f} ({lc})" if np.isfinite(c) else "—"
        print(f"{label:<46}{n:>5}{extra:>7}{fa:>12}{la:>6}{va:>8}{reach_a:>5}{fb:>12}{lb:>6}{vb:>8}{reach_b:>5}{fc:>11}")
        return {"dt": a, "dt_v": va, "ri": b, "ri_v": vb, "dt1": c, "n": n}

    for key, label, okc in METHODS:
        dtc, ric = f"dt_{key}_ms", f"ri_{key}"
        if dtc not in d:
            continue
        if okc and okc in d:
            acc = d[d[okc] == 1]
            res[key + "_acc"] = line(label + "（採用分）", dtc, ric, acc, f"{100.0 * len(acc) / max(len(d), 1):.1f}%")
            res[key] = line(label + "（全例）", dtc, ric, d)
        else:
            res[key] = line(label, dtc, ric, d)
    print("-" * 110)
    for key, label, dtc, ric in REFS:
        res[key] = line(label, dtc, ric, d)
    if "tig_best" in d:
        vc = d["tig_best"].replace("", np.nan).dropna().value_counts(normalize=True)
        top = "・".join(f"{k} {v:.0%}" for k, v in vc.head(6).items())
        print(f"\nTigges の AICc で最良になった基底×M（上位）: {top}（Tigges 2017 の実測: Gamma M=3 28%・Rayleigh M=2 14%・Normal M=2 1.2%）")
    if "cou_init" in d:
        print(f"Couceiro の初期値: a〜e 波から {float((d['cou_init'] == 'abcde').mean()):.0%}・汎用 {float((d['cou_init'] == 'generic').mean()):.0%}")
    if "w_wang" in d:
        vc = d["w_wang"].dropna().value_counts(normalize=True).sort_index()
        print(f"Wang の選ばれた重み: {'・'.join(f'{int(k)}: {v:.0%}' for k, v in vc.items())}"
              f"／ 5 ガウスへ増やした拍 {float((d['M_wang'] == 5).mean()):.0%}")
    if "dps_gos_ms" in d:
        a, la, _ = cell("dps_gos_ms", "pvr", +1, d)
        print(f"Goswami の DPS × 末梢血管抵抗（記述）: |ρ| {a:.3f}（{la}）" if np.isfinite(a) else "Goswami の DPS: 判定できず")
    n_err = int(d["err"].notna().sum()) if "err" in d else 0
    print(f"例外のあった被験者: {n_err}")
    print(f"\n{'-' * 110}\n逸脱表（精読メモに記載が無い項目は既定で埋めた。全文で確かめたら差し替える）\n{'-' * 110}")
    print(f"{'手法':<12}{'項目':<16}{'文献（精読メモ）':<52}{'ここでの実装':<44}{'状態'}")
    for m, item, lit, impl, st in DEVIATIONS:
        print(f"{m:<12}{item:<16}{lit[:50]:<52}{impl[:42]:<44}{st}")
    print(f"\n{'-' * 110}\n読み方\n{'-' * 110}")
    print("  「届く ○」が 1 つも無ければ、文献の条件でも分解由来の ΔT・RI はこの土俵でランドマークに届かない。")
    print("  「届く ○」があれば、その手法の逸脱表を全文で埋めてから、新しい事前登録の下で第3版として試す（この表では採らない）。")
    print("  型1 のみの列は 31番（型1 の 98 拍）との照合用。文献の手法は型を選ばないので主表は全型。")
    print(f"  pda2 版 {pda2.code_version()}（前処理・鍵点・採否の実装を共有）")
    return res


class _Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            st.write(s)

    def flush(self):
        for st in self.streams:
            st.flush()


def run(root: Path, subset: str, jobs: int, limit: int = 0) -> None:
    d, C = build(root, subset=subset, jobs=jobs, limit=limit)
    tag = "" if subset == "mod7" else "_all"
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = _Tee(old, buf)
    try:
        report(d, C, tag=tag)
    finally:
        sys.stdout = old
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"literature_replica_report{tag}.txt").write_text(buf.getvalue(), encoding="utf-8")
    print(f"\n表の全文: {OUT / f'literature_replica_report{tag}.txt'}")


# ================================================================ 自己検証
def selftest() -> int:
    import contextlib
    import tempfile
    ok = True

    def rep(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}{('  ' + detail) if detail else ''}", flush=True)

    print("== 33_pwdb_literature_replica 自己検証（模擬 PWDB・ネットワーク不要） ==\n")
    # 1. 基底の部品
    t = np.arange(0, 0.9, 1 / 500.0)
    y = rayleigh_goswami(t, 0.7, 0.10, 0.05)
    i = int(np.argmax(y))
    rep("Goswami の Rayleigh はピークが D+σ で高さ h", abs(t[i] - 0.15) < 0.003 and abs(y[i] - 0.7) < 0.01,
        f"tp={t[i]:.3f} h={y[i]:.3f}")
    g = gamma_mode_sd(t, 1.0, 0.12, 0.05)
    j = int(np.argmax(g))
    gm = g / np.trapezoid(g, t) if hasattr(np, "trapezoid") else g / np.trapz(g, t)
    mean = float(np.sum(t * gm) * (t[1] - t[0]))
    sd = float(np.sqrt(np.sum((t - mean) ** 2 * gm) * (t[1] - t[0])))
    rep("Fleischhauer の最頻値・SD 母数化（最頻値 0.12・SD 0.05 を復元）", abs(t[j] - 0.12) < 0.003 and abs(sd - 0.05) < 0.006,
        f"mode={t[j]:.3f} sd={sd:.3f}")
    rep("AICc: 母数が多いほど罰則が増える（同じ RSS）", _aicc(1.0, 40, 3) < _aicc(1.0, 40, 6) < _aicc(1.0, 40, 9)
        and not np.isfinite(_aicc(1.0, 10, 9)))
    lm = {"dia_t": 0.42}
    fwd, ref = pick_roles([(0.10, 1.0), (0.25, 0.3), (0.40, 0.4), (0.70, 0.2)], lm)
    rep("役割規則: 前進波は最初の高い成分、反射波は拡張期鍵点に最も近い後続成分", fwd == 0 and ref == 2)
    # 2. 模擬 PWDB で全手法
    C = _load("26_pwdb_compare.py", "m26")
    with tempfile.TemporaryDirectory() as td:
        root, _kinds = C._selftest_root(Path(td), n=24)
        with contextlib.redirect_stdout(io.StringIO()):
            d, C2 = build(root, subset="all", jobs=1)
        cols = [f"dt_{k}_ms" for k, _l, _o in METHODS] + [f"ri_{k}" for k, _l, _o in METHODS]
        rep("全手法の列が揃う", all(c in d for c in cols), f"n={len(d)}")
        fin = {k: float(d[f"dt_{k}_ms"].notna().mean()) for k, _l, _o in METHODS}
        rep("模擬の 2 ガウス拍で各手法が ΔT を返す（Goswami・Fleischhauer 2・Basso 2・Tigges・Wang・Couceiro ≥ 50%）",
            all(fin[k] >= 0.5 for k in ("gos", "fl2", "bas2", "tig", "wang", "cou")),
            "・".join(f"{k} {v:.0%}" for k, v in fin.items()))
        rep("例外が無い", "err" not in d or d["err"].isna().all(), str(d["err"].dropna().head(2).tolist()) if "err" in d else "")
        rep("Wang の採否・重み・成分数が記録される", set(d["ok_wang"].dropna().unique()) <= {0, 1}
            and d["M_wang"].isin([4, 5]).all() and d["w_wang"].dropna().isin(WANG_WEIGHTS).all())
        rep("Tigges の AICc が基底×M を 1 つ選ぶ", d["tig_best"].str.contains("M=").mean() >= 0.9,
            d["tig_best"].value_counts().head(3).to_dict().__repr__())
        rep("Couceiro の初期値の由来が記録される", d["cou_init"].isin(["abcde", "generic"]).all(),
            d["cou_init"].value_counts().to_dict().__repr__())
        # Couceiro の制約が返り値で満たされるか（1 拍を直接）
        M = C2.M
        hae = M._read_named(root / "pwdb_haemod_params.csv", ("subj_no", "HR"))
        import pandas as pd
        ppg = pd.read_csv(root / "PWs" / "csv" / "PWs_Digital_PPG.csv", skipinitialspace=True)
        y0, fs = M.beat_of(ppg.iloc[0].to_numpy(float), float(hae["HR"].iloc[0]))
        tt = np.arange(y0.size) / fs
        ys, _ = pda2.preprocess(tt, y0, fs)
        lm0 = pda2.find_landmarks(tt, ys)
        rc = fit_couceiro(tt, ys, lm0)
        rep("Couceiro: 1 拍で ΔT・RI が有限", np.isfinite(rc["dt_cou_ms"]) and np.isfinite(rc["ri_cou"]),
            f"ΔT {rc['dt_cou_ms']:.0f} ms・RI {rc['ri_cou']:.2f}")
        rb = fit_basso(tt, ys, lm0, 2)
        rep("Basso L=2: 28 標本で ΔT が有限、α が記録される", np.isfinite(rb["dt_bas2_ms"]) and np.isfinite(rb["alpha_bas2"]),
            f"ΔT {rb['dt_bas2_ms']:.0f} ms・α {rb['alpha_bas2']:.2f}")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            res = report(d, C2, out_dir=Path(td) / "out", tag="_selftest")
        out = buf.getvalue()
        rep("表・逸脱表・読み方が出て CSV が書かれる", "逸脱表" in out and "読み方" in out and "lm" in res
            and (Path(td) / "out" / "literature_replica_selftest.csv").exists())
        rep("subj%7 の部分集合が選べる", len(build.__code__.co_varnames) > 0)
    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pwdb", type=str, default=None)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--all", action="store_true", help="subj%7==0 の部分集合ではなく全例")
    ap.add_argument("--limit", type=int, default=0, help="先頭 N 名だけ（形式の確認用）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())
    if not args.pwdb:
        ap.error("--pwdb を指定してください（--selftest なら不要）")
    run(Path(args.pwdb), "all" if args.all else "mod7", max(1, args.jobs), args.limit)


if __name__ == "__main__":
    main()

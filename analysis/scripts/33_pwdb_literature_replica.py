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

2026-09-06 に 6 本の全文（PDF）で照合し、初期値・境界・制約・目的関数・最適化器・再標本化を文献の記載に
差し替えた（逸脱表の「一致」）。残る逸脱は最適化器（fmincon の内点法 → scipy の SLSQP／LM）と
データ側の違い（PWDB は 1 拍・雑音なし）だけである。

読み方（結果を見る前に固定。lab_log 追記16）
--------------------------------------------
集団  subj_no % 7 == 0（624 名。27番 B 層と同じ。結果を見て選び直さない）。全型を当てる（文献は型を選ばない）。
規準  年齢層内 Spearman が全 6 層で予測の向き、中央値 |ρ| ≥ 0.30（20・23・26番と同じ。8 名未満の層は数えない）。
届く  中央値 |ρ| が、同じ集団のランドマーク（Charlton 同梱）の値 − 0.05 以上（gate0_rules_v2 の「同等」の幅）。
採否  文献に採否規準があるもの（Wang 2013）は採用分と全例の両方、無いものは全例。
役割  文献に反射波の指定があるもの（Goswami: p_r、Couceiro: g4、2 成分の手法: 第 2 成分）はそれに従う。
      無いもの（Tigges・Wang・Basso L≥3・Fleischhauer 3 核）は 26番と同じ規則
      （前進波 = 最も早いピークで高さが最大の半分以上の成分、反射波 = 拡張期の鍵点に最も近い後続の成分）。

手法（全文で照合済み）
----------------------
  Goswami 2010      Rayleigh 2 本 p_f = a_f (t/σ_f²) exp(−t²/2σ_f²)、p_r = a_r ((t−D)/σ_r²) exp(−(t−D)²/2σ_r²)。
                    段階的: 前進波は高さ ≥ 0.5h₁・0 ≤ tp₁ ≤ t₁ で立ち上がり 0<t≤tp₁ の MSE 最小、
                    反射波は 0.3t₁ ≤ D ≤ 0.9T で **0〜T 全体**の MSE 最小（拍の終わりの一致は保証しない）。
                    ΔT = tp₂ − tp₁、RI = p₂/p₁、DPS = σ_r − σ_f。3〜5 拍の時間平均（PWDB は 1 拍）
  Tigges 2017       Normal / Log-Normal / Rayleigh（t ≥ b で a·t·exp(−(t−b)²/2σ²)）/ Gamma（a·t^(α−1)·e^(−βt)）
                    × M=1..6。RSS 最小・制約と初期値は Couceiro に倣う・内点法。18 Hz 4 次 Butterworth 零位相・
                    極小で切る・線形基線・振幅 1・**10 次 Kaiser 18 Hz で 40 Hz へ**。AICc = N ln(RSS/N) + 2K +
                    2(K+1)(K+2)/(N−K−2)、K = 3M+1。推奨の Gamma M=3 も固定で併記
  Wang 2013         ガウス 4 本 → 規準（NRMSE<2%・Errx<6 ms・Erry<0.01）を満たさなければ 5 本。1 kHz。
                    初期値は 2 次微分の特徴点 D1〜D4 から型別（表 1: H = 0.8A／0.3A、μ = D、s = D1/3 など）。
                    鍵点（頂点と谷）の重み w = 1..100（1 刻み）の WLS を Levenberg–Marquardt で解き、
                    Errx・Erry・NRMSE を正規化（r = (max−a)/(max−min)）、重み u = (0.35, 0.35, 0.30) の
                    理想解 E=(1,1,1)・最悪解 B=(0,0,0) に対する適合度 c = 1/(1 + Σ[u(e−r)]²/Σ[u(b−r)]²) が最大の重みを採る
  Couceiro 2015     ガウス 5 本。18 Hz 低域通過・線形トレンド除去・振幅 1。初期値と境界は 2 次微分の a〜f 波と
                    切痕の両端（表 1）。不等式制約 a₁≤a₂, a₁≤a₃, a₃≤a₂, a₄≤a₂, a₅≤a₂, a₅≤a₄, b₁≤b₂<b₃≤b₄≤b₅。
                    MSE 最小・内点法。T1_d = b₄ − b(g₁+g₂ のピーク)、R1_d = a₄/A(g₁+g₂)
  Fleischhauer 2020 Gamma（最頻値 m・SD σ: β = (m+√(m²+4σ²))/(2σ²)、α = (m²+m√(m²+4σ²))/(2σ²)+1、ピーク高さ a）
                    ＋ Gaussian。generic 初期値・境界（表 D3: a₀ = 0.8/0.5·max、m₀ = 2/7·T, 4/7·T、σ₀ = (2/7, 3/7)·T·T2、
                    lb 0・ub max／T）。fmincon 内点法（既定・評価回数無制限）。2 核と 3 核
  Basso 2024        歪みガウス（振幅 a・最頻値 m・SD σ・形状 α に付け替え、ξ・ω は付録 A.6〜A.7）L=2/3/4。
                    18 Hz 4 次 Butterworth・線形基線・**28 標本**・最大 1。RSS 最小、制約 a₁ > a_k・m_{k−1} < m_k、
                    初期値は表 1（a₀ = 0.8/0.5/…·ymax、m₀ = 2/7·T…、σ₀ = 2/7·T2…、α₀ = 1）、境界 a∈[0,ymax]・
                    m∈[0,T]・σ∈[0,T]・α 無制約。fmincon 内点法・評価回数無制限

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
import json
import sys
import time
import warnings
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
    ("共通", "最適化器", "Wang: Levenberg–Marquardt。Couceiro・Tigges・Fleischhauer・Basso: fmincon の内点法（既定設定・評価回数無制限）",
     "Wang: scipy least_squares(method='lm')。他: scipy SLSQP（不等式制約と境界を扱える。maxiter 5000）", "逸脱（代替の解法）"),
    ("共通", "起動", "各文献は 1 組の初期値（Basso は感度の検証に無作為 50 組）", "文献の 1 組の初期値のみ（多点起動なし）", "一致"),
    ("共通", "前処理", "Tigges・Couceiro・Basso: 18 Hz 4 次 Butterworth・線形基線・最大 1。Wang: CAF＋Savitzky–Golay・正規化。Goswami: 前処理と正規化（詳細なし）",
     "全手法で pda2.preprocess（18 Hz・足→足基線・最大 1）", "Tigges・Couceiro・Basso 一致／Wang・Goswami は代替"),
    ("共通", "データ", "実測 PPG（Goswami 3〜5 拍平均・Wang 1 kHz・Basso 125 Hz・Tigges 500/125 Hz）", "PWDB の 1 拍（500 Hz・雑音なし）", "逸脱（データ）"),
    ("共通", "指標", "Goswami ΔT_TPS・RI_TPS、Couceiro T1_d・R1_d。Tigges・Wang・Fleischhauer・Basso は ΔT・RI を定義していない",
     "文献の定義があればそれ。無い手法は 26番の役割規則で前進波と反射波を選ぶ", "定義のある 2 本は一致／他は既定"),
    ("共通", "健全性", "記載なし（文献は失敗した当てはめを報告しない）",
     "反射波のピークが前進波より前、または拍の外（> T）なら失敗として NaN", "既定"),
    ("Goswami", "h₁・t₁", "2 次微分法で推定", "pda2.find_landmarks の収縮期ピーク", "代替"),
    ("Tigges", "初期値と制約", "『Couceiro に倣う』とのみ記載（M≠5・非ガウス基底への割り当ては不明）",
     "M=5 は Couceiro 表 1、他の M は同じ鍵点を M 個に配り直す。制約は振幅の順序と位置の単調", "一部既定"),
    ("Tigges", "40 Hz", "10 次 Kaiser 窓 18 Hz の抗折り返し → 40 Hz", "同じ（firwin 11 タップ Kaiser β=8.6・18 Hz → 40 Hz 補間）", "一致"),
    ("Wang", "鍵点", "頂点と谷（crests and troughs）", "S・切痕・D（pda2.find_landmarks）", "一致（同じ点）"),
    ("Wang", "D1〜D4", "2 次微分の谷・山・零交差から型別に決める", "同じ規則を実装（型は Wang の 5 型を pda2 の型 1/3/4 に写す）", "一致（型の写像は近似）"),
    ("Wang", "5 ガウスの初期値", "表 1 は 4 本分のみ（5 本目の記載なし）", "5 本目は D3 と D4 の中点・H=0.3A・s=(D4−D3)/3", "既定"),
    ("Couceiro", "切痕の両端 tdn1・tdn2", "2 次微分の [0.2, 0.4] s の極大と零交差（無ければ 4 次微分）", "同じ規則（零交差が無ければ極大 ±20 ms）", "一致（近似）"),
    ("Couceiro", "表 1 の c₅ 初期値", "『T-avg(T−Bwf)』（原文が判読不能）", "(T − t_f)/3", "既定"),
    ("Fleischhauer", "generic 初期値・境界", "表 D3", "表 D3 のとおり", "一致"),
    ("Basso", "α の範囲", "無制約（[−∞, +∞]）", "[−50, 50]（数値上の代用）", "代替"),
    ("Basso", "母数化・28 標本・RSS・制約・初期値", "付録 A・表 1・§3.3", "同じ", "一致"),
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
    """Tigges 2017 式 (3): a·t·exp(−(t−b)²/2σ²)、t ≥ b（それより前は 0）。"""
    out = a * t * np.exp(-0.5 * ((t - b) / max(s, 1e-6)) ** 2)
    return np.where(t >= b, out, 0.0)


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
    """Fleischhauer 2020 付録 C: 最頻値 m と SD σ のガンマ（t=0 から）。
    β = (m + √(m²+4σ²))/(2σ²)、α = (m² + m√(m²+4σ²))/(2σ²) + 1、ピーク高さ h を t=m でとる（式 26）。"""
    m = max(m, 1e-4)
    s = max(s, 1e-4)
    r = np.sqrt(m * m + 4 * s * s)
    alpha = (m * m + m * r) / (2 * s * s) + 1.0
    return pda2.gamma_peak(t, h, m, rise=m, shape=max(alpha, 1.0 + 1e-6))


def _skew_m0(alpha):
    """Basso 2024 付録 (A.5): ξ=0・ω=1 の歪み正規分布の最頻値の近似（Azzalini）。"""
    d = alpha / np.sqrt(1.0 + alpha * alpha)
    mz = np.sqrt(2 / np.pi) * d
    if abs(alpha) < 1e-12:
        return 0.0
    return (mz - (1 - np.pi / 4) * mz ** 3 / (1 - 2 * d * d / np.pi)
            - np.sign(alpha) / 2 * np.exp(-2 * np.pi / abs(alpha)))


def skew_basso(t, a, m, s, alpha):
    """Basso 2024 式 (6a) を (a, m, σ, α) で母数化（付録 A.6〜A.9）。t=m で高さ a。"""
    from scipy.special import erf
    d = alpha / np.sqrt(1.0 + alpha * alpha)
    omega = max(s, 1e-6) / np.sqrt(max(1 - 2 * d * d / np.pi, 1e-6))
    xi = m - omega * _skew_m0(alpha)
    z = (np.asarray(t, float) - xi) / omega
    base = np.exp(-0.5 * z * z) * (1 + erf(alpha * z / np.sqrt(2)))
    zm = (m - xi) / omega
    sm = np.exp(-0.5 * zm * zm) * (1 + erf(alpha * zm / np.sqrt(2)))
    return a * base / max(sm, 1e-12)


def comp_eval(kind, t, p):
    if kind == "skew_b":
        return skew_basso(t, *p)
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


NPAR = {"normal": 3, "lognormal": 3, "rayleigh": 3, "gamma": 3, "gamma_ms": 3, "skew": 4, "skew_b": 4}


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
T2C = 1.0 / (2.0 * np.sqrt(2.0 * np.log(2.0)))     # Fleischhauer・Basso の T2 = T·(2√(2 ln 2))⁻¹ の係数


def _lsq(resid, x0, lo=None, hi=None, max_nfev=20000, method=None, jac=None):
    """境界つきは信頼領域（TRF）、境界なしは Levenberg–Marquardt（Wang 2013）。1 組の初期値。"""
    from scipy.optimize import least_squares
    x0 = np.asarray(x0, float)
    try:
        if lo is None:
            return least_squares(resid, x0, method=method or "lm", max_nfev=max_nfev, jac=jac or "2-point")
        lo, hi = np.asarray(lo, float), np.asarray(hi, float)
        x0 = np.clip(x0, lo + 1e-9, hi - 1e-9)
        return least_squares(resid, x0, bounds=(lo, hi), max_nfev=max_nfev, x_scale="jac")
    except Exception:      # noqa: BLE001
        return None


def _slsqp(fun, x0, lo, hi, cons, maxiter=5000):
    """内点法（fmincon）の代替。不等式制約と境界を同時に扱える SLSQP。1 組の初期値。
    制約を満たさない解（fmincon なら失敗として返る）は None にする。"""
    from scipy.optimize import minimize
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    hi = np.maximum(hi, lo + 1e-6)
    x0 = np.clip(np.asarray(x0, float), lo + 1e-9, hi - 1e-9)
    try:
        r = minimize(fun, x0, method="SLSQP", bounds=list(zip(lo, hi)), constraints=cons,
                     options={"maxiter": maxiter, "ftol": 1e-12})
    except Exception:      # noqa: BLE001
        return None
    if not np.all(np.isfinite(r.x)):
        return None
    for c in cons:
        if float(c["fun"](r.x)) < -1e-6:
            return None
    return r


def _gauss_jac(t, x, sw):
    """ガウス和の解析的ヤコビアン（Wang の LM 用）。列は (H, μ, s) × M。重み √w を行に掛ける。"""
    M = len(x) // 3
    J = np.empty((len(t), 3 * M))
    for i in range(M):
        H, mu, s = x[3 * i:3 * i + 3]
        s = max(abs(s), 1e-6)
        z = (t - mu) / s
        e = np.exp(-0.5 * z * z)
        J[:, 3 * i] = e
        J[:, 3 * i + 1] = H * e * z / s
        J[:, 3 * i + 2] = H * e * z * z / s
    return J * sw[:, None]


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


def _indices_from(comps, lm, fwd=None, ref=None, T=None):
    """ΔT [ms] と RI。反射波のピークが前進波より後で拍の中（≤ T）に無ければ失敗（NaN。全手法共通の健全性規則）。"""
    if fwd is None or ref is None:
        fwd, ref = pick_roles(comps, lm)
    if fwd is None or ref is None:
        return NAN, NAN
    (tf, hf), (tr, hr) = comps[fwd], comps[ref]
    if not (np.isfinite(tf) and np.isfinite(tr)) or tr <= tf or (T is not None and (tr > T or tf < 0)):
        return NAN, NAN
    return float((tr - tf) * 1000.0), float(hr / hf) if hf > 1e-9 else NAN


def _resample(t, y, fs_new=None, n=None):
    T = float(t[-1]) + float(t[1] - t[0])
    tn = np.linspace(0.0, T, int(n), endpoint=False) if n else np.arange(0.0, T, 1.0 / fs_new)
    return tn, np.interp(tn, t, y)


def _resample_tigges(t, y, fs):
    """Tigges 2017 §II-D: 10 次 Kaiser 窓の 18 Hz 抗折り返し低域通過（減衰 40 dB 超）→ 40 Hz。零位相で当てる。"""
    from scipy.signal import firwin, filtfilt
    if fs > 2 * 18.0 * 1.2 and len(y) > 40:
        b = firwin(11, 18.0, fs=fs, window=("kaiser", 3.45))
        y = filtfilt(b, [1.0], y)
    return _resample(t, y, fs_new=40.0)


# ================================================================ 2 次微分の特徴点（Couceiro・Wang・Tigges が使う）
def _d2(t, y):
    dt = float(t[1] - t[0])
    return np.gradient(np.gradient(y, dt), dt)


def _extrema(v, lo, hi):
    """[lo, hi) の局所極大・極小の添字を順に。返り値 [(添字, 'max'|'min'), ...]。"""
    out = []
    for i in range(max(lo, 1), min(hi, len(v) - 1)):
        if v[i] > v[i - 1] and v[i] >= v[i + 1]:
            out.append((i, "max"))
        elif v[i] < v[i - 1] and v[i] <= v[i + 1]:
            out.append((i, "min"))
    return out


def couceiro_points(t, ys, lm) -> dict:
    """Couceiro 2015 表 1（Fleischhauer 表 D1 と同じ）に要る点: a〜f 波の時刻・切痕の両端・振幅。

    a〜f は 2 次微分（Takazawa）の交互の極値: a 極大 → b 極小 → c 極大 → d 極小 → e 極大 → f 極小
    （f は「e の後の負のピーク」）。切痕の基準点は 2 次微分の [0.2, 0.4] s の極大、両端はその前後の零交差
    （0.1 s 以内に無ければ ±20 ms で代用）。
    """
    T = float(t[-1])
    d2 = _d2(t, ys)
    i_s = int(np.argmax(ys))
    ext = _extrema(d2, 1, int(0.9 * len(t)))
    seq, want = [], "max"
    amax = max((abs(d2[i]) for i, _ in ext), default=0.0)
    for i, kind in ext:
        if kind == want and (seq or abs(d2[i]) >= 0.1 * amax):
            seq.append(i)
            want = "min" if want == "max" else "max"
        if len(seq) == 6:
            break
    pts = {}
    for name, i in zip("abcdef", seq):
        pts["t" + name] = float(t[i])
    # 切痕（Couceiro §2.3）
    m = (t >= 0.2) & (t <= 0.4) & (np.arange(len(t)) > i_s)
    if not m.any():
        m = (np.arange(len(t)) > i_s) & (t <= 0.75 * T)
    if m.any():
        i_dn = int(np.flatnonzero(m)[np.argmax(d2[m])])
        z = np.flatnonzero(np.sign(d2[:-1]) != np.sign(d2[1:]))
        left = [k for k in z if k < i_dn and d2[k] < 0 <= d2[k + 1]]
        right = [k for k in z if k >= i_dn and d2[k] > 0 >= d2[k + 1]]
        dt = float(t[1] - t[0])
        i1 = left[-1] if left and (i_dn - left[-1]) * dt <= 0.1 else max(i_dn - int(0.02 / dt), 0)
        i2 = right[0] if right and (right[0] - i_dn) * dt <= 0.1 else min(i_dn + int(0.02 / dt), len(t) - 1)
        pts["tdn"], pts["tdn1"], pts["tdn2"] = float(t[i_dn]), float(t[i1]), float(t[i2])
    pts["T"] = T
    pts["ysys"] = float(ys[i_s])
    pts["tsys"] = float(t[i_s])
    if all(k in pts for k in ("tb", "tc", "td")):
        pts["ppgsys"] = float(max(np.interp(pts[k], t, ys) for k in ("tb", "tc", "td")))
    if "tdn1" in pts:
        mm = t >= pts["tdn1"]
        pts["ppgdia"] = float(np.max(ys[mm])) if mm.any() else NAN
        pts["tdia"] = float(t[mm][int(np.argmax(ys[mm]))]) if mm.any() else NAN
    if "ta" in pts:
        pts["ppga"] = float(np.interp(pts["ta"], t, ys))
        pts["ppgb"] = float(np.interp(pts["tb"], t, ys)) if "tb" in pts else NAN
    pts["complete"] = all(k in pts for k in ("ta", "tb", "tc", "td", "tf", "tdn1", "tdn2", "tdia"))
    return pts


def couceiro_init(pts) -> tuple:
    """Couceiro 2015 表 1: (初期値, lb, ub) を 5 成分 × (a, b, c) の並びで。complete でなければ Fleischhauer 表 D1 の generic。"""
    T = pts["T"]
    if pts.get("complete"):
        ta, tb, tc, td, tf = pts["ta"], pts["tb"], pts["tc"], pts["td"], pts["tf"]
        tdn1, tdn2, tdia = pts["tdn1"], pts["tdn2"], pts["tdia"]
        ppga, ppgb, ppgsys, ppgdia = pts["ppga"], pts["ppgb"], pts["ppgsys"], max(pts["ppgdia"], 1e-3)
        rows = [  # (a0, a_lb, a_ub, b0, b_lb, b_ub, c0, c_lb, c_ub)
            (0.7 * ppga, 0.5 * ppga, max(ppgb, 0.5 * ppga + 1e-3), ta, ta, tb, ta / 3, 1e-3, tb / 3),
            (0.9 * ppgsys, 0.5 * ppgsys, ppgsys, tb, ta, tc, tb / 3, ta / 3, td / 3),
            (0.5 * ppgsys, 0.2 * ppgsys, 0.8 * ppgsys, td, tb, tdn1, td / 3, tb / 3, tdn1 / 3),
            (0.8 * ppgdia, 0.0, ppgdia, tf, tdn2, T, min(tf, T - tf) / 3, 1e-3, tdn2),
            (0.3 * ppgdia, 0.0, ppgdia, tdia, tf, T, (T - tf) / 3, 1e-3, tdn2),
        ]
        src = "couceiro"
    else:
        rows = [(0.8, 0.0, 1.0, 2 / 7 * T, 0.0, T, (2 / 7 * T) * T2C, 1e-3, T)]
        rows += [(0.3, 0.0, 1.0, k / 7 * T, 0.0, T, (1 / 7 * T) * T2C, 1e-3, T) for k in (3, 4, 5, 6)]
        src = "generic"
    x0, lo, hi = [], [], []
    for a0, alb, aub, b0, blb, bub, c0, clb, cub in rows:
        for v0, vlb, vub in ((a0, alb, aub), (b0, blb, bub), (c0, clb, cub)):
            vlb, vub = float(min(vlb, vub)), float(max(vlb, vub))
            x0.append(float(np.clip(v0, vlb, vub)))
            lo.append(vlb)
            hi.append(max(vub, vlb + 1e-6))
    return np.array(x0), np.array(lo), np.array(hi), src


def couceiro_constraints(n: int = 5):
    """振幅の順序（a₁≤a₂, a₁≤a₃, a₃≤a₂, a₄≤a₂, a₅≤a₂, a₅≤a₄）と位置の単調（b₁≤b₂<b₃≤b₄≤b₅）。3 母数/成分。"""
    A = lambda i: 3 * i          # noqa: E731
    B = lambda i: 3 * i + 1      # noqa: E731
    cons = []
    if n == 5:
        cons += [{"type": "ineq", "fun": (lambda x, i=i, j=j: x[A(j)] - x[A(i)])}
                 for i, j in ((0, 1), (0, 2), (2, 1), (3, 1), (4, 1), (4, 3))]
    cons += [{"type": "ineq", "fun": (lambda x, i=i: x[B(i + 1)] - x[B(i)] - (0.002 if i == 1 else 0.0))}
             for i in range(n - 1)]
    return cons


# ================================================================ 各文献
def fit_goswami(t, ys, lm) -> dict:
    """Goswami 2010「Pulse Synthesis Procedure」を格子探索で忠実に。

    前進波 p_f = a_f (t/σ_f²) exp(−t²/2σ_f²): 高さ ≥ 0.5h₁、0 ≤ tp₁(=σ_f) ≤ t₁、立ち上がり 0<t≤tp₁ の MSE 最小。
    反射波 p_r = a_r ((t−D)/σ_r²) exp(−(t−D)²/2σ_r²): 0.3t₁ ≤ D ≤ 0.9T、0≤t≤T 全体の MSE 最小。
    振幅は形を固定すれば線形なので閉じた式（非負・高さの下限は切り上げ）。
    """
    out = {"dt_gos_ms": NAN, "ri_gos": NAN, "dps_gos_ms": NAN, "gos_D_ms": NAN}
    t1 = float(lm["sys_t"])
    h1 = float(lm["sys_v"])
    T = float(t[-1])
    if not np.isfinite(t1) or t1 <= 0.02:
        return out
    sqe = np.sqrt(np.e)
    best = None
    for sf in np.arange(0.006, t1 + 1e-9, 0.002):
        m = (t > 0) & (t <= sf)
        if m.sum() < 4:
            continue
        phi = (t[m] / sf ** 2) * np.exp(-t[m] ** 2 / (2 * sf ** 2))
        a = float(np.sum(ys[m] * phi) / max(np.sum(phi * phi), 1e-12))
        a = max(a, 0.5 * h1 * sf * sqe)                     # 高さ a/(σ√e) ≥ 0.5h₁
        mse = float(np.mean((a * phi - ys[m]) ** 2))
        if best is None or mse < best[0]:
            best = (mse, a, sf)
    if best is None:
        return out
    _, af, sf = best
    pf = af * (t / sf ** 2) * np.exp(-t ** 2 / (2 * sf ** 2))
    res = ys - pf
    best = None
    for D in np.arange(0.3 * t1, 0.9 * T + 1e-9, 0.002):
        u = t - D
        pos = u > 0
        if pos.sum() < 4:
            continue
        for sr in np.arange(0.01, 0.5 * T + 1e-9, 0.004):
            phi = np.zeros_like(t)
            phi[pos] = (u[pos] / sr ** 2) * np.exp(-u[pos] ** 2 / (2 * sr ** 2))
            den = float(np.sum(phi * phi))
            if den <= 1e-12:
                continue
            a = max(float(np.sum(res * phi) / den), 0.0)
            mse = float(np.mean((a * phi - res) ** 2))
            if best is None or mse < best[0]:
                best = (mse, a, D, sr)
    if best is None:
        return out
    _, ar, D, sr = best
    p1 = af / (sf * sqe)
    p2 = ar / (sr * sqe)
    if (D + sr) <= sf or (D + sr) > T:
        return out                                  # 反射波のピークが前進波より前・拍の外なら失敗
    out["dt_gos_ms"] = float(((D + sr) - sf) * 1000.0)
    out["ri_gos"] = float(p2 / p1) if p1 > 0 else NAN
    out["dps_gos_ms"] = float((sr - sf) * 1000.0)
    out["gos_D_ms"] = float(D * 1000.0)
    return out


TIGGES_BASES = ("normal", "lognormal", "rayleigh", "gamma")


def _aicc(rss, n, k):
    """Tigges 2017 式 (8): N ln(RSS/N) + 2K + 2(K+1)(K+2)/(N−K−2)。"""
    if n - k - 2 <= 0 or rss <= 0:
        return np.inf
    return n * np.log(rss / n) + 2 * k + 2 * (k + 1) * (k + 2) / (n - k - 2)


def _tigges_init(kind, M, pts):
    """『Couceiro に倣う』初期値と境界を基底ごとに写す。M=5 は Couceiro 表 1 そのもの、他の M は同じ点を配り直す。"""
    x5, lo5, hi5, _src = couceiro_init(pts)
    rows = [(x5[3 * i], lo5[3 * i], hi5[3 * i], x5[3 * i + 1], lo5[3 * i + 1], hi5[3 * i + 1],
             x5[3 * i + 2], max(lo5[3 * i + 2], 0.004), max(hi5[3 * i + 2], 0.01)) for i in range(5)]
    pick = {1: [1], 2: [1, 3], 3: [1, 2, 3], 4: [1, 2, 3, 4], 5: [0, 1, 2, 3, 4], 6: [0, 1, 2, 3, 4, 4]}[M]
    sel = [rows[i] for i in pick]
    if M == 6:                                  # 6 本目は g4 と g5 の中間
        a0, alb, aub, b0, blb, bub, c0, clb, cub = sel[5]
        sel[5] = (a0, alb, aub, 0.5 * (rows[3][3] + rows[4][3]), blb, bub, c0, clb, cub)
    T = pts["T"]
    x0, lo, hi = [], [], []
    for a0, alb, aub, b0, blb, bub, c0, clb, cub in sel:
        if kind == "normal":
            x0 += [a0, b0, c0]; lo += [alb, blb, clb]; hi += [aub, bub, cub]
        elif kind == "lognormal":                   # ピーク時刻 tp と対数の幅
            x0 += [a0, b0, c0 / max(b0, 1e-3)]; lo += [alb, max(blb, 1e-3), 0.02]; hi += [aub, bub, 3.0]
        elif kind == "rayleigh":                    # t ≥ b で立ち上がる。b は位置 − 幅
            x0 += [a0 / max(b0, 1e-3), max(b0 - c0, 0.0), c0]; lo += [0.0, 0.0, clb]; hi += [50.0 / T, bub, cub]
        elif kind == "gamma":                       # (h, 最頻値, 形状)。β = (α−1)/最頻値
            r = np.sqrt(b0 * b0 + 4 * c0 * c0)
            alpha0 = (b0 * b0 + b0 * r) / (2 * c0 * c0) + 1.0
            x0 += [a0, b0, float(np.clip(alpha0, 1.05, 200.0))]; lo += [alb, max(blb, 1e-3), 1.05]; hi += [aub, bub, 400.0]
    return np.array(x0), np.array(lo), np.array(hi)


def fit_tigges(t, ys, lm, pts) -> dict:
    """4 基底 × M=1..6 を 40 Hz で RSS 最小（制約と初期値は Couceiro に倣う）、AICc（K = 3M+1）で選ぶ。Gamma M=3 も固定で。"""
    out = {"dt_tig_ms": NAN, "ri_tig": NAN, "tig_best": "", "dt_tig3_ms": NAN, "ri_tig3": NAN}
    t40, y40 = _resample_tigges(t, ys, 1.0 / float(t[1] - t[0]))
    n = len(y40)
    best = None
    for kind in TIGGES_BASES:
        for M in range(1, 7):
            x0, lo, hi = _tigges_init(kind, M, pts)
            kinds = [kind] * M

            def rss(x, kinds=kinds):
                return float(np.sum((model_sum(kinds, t40, x) - y40) ** 2))
            # 制約は Couceiro に倣う: 位置の単調は全 M。振幅の順序は M=5 かつ添字 0 がピーク高さの基底
            # （normal・lognormal・gamma）だけ。Rayleigh の添字 0 は尺度なので振幅の順序は課さない
            cons = couceiro_constraints(M)
            if M == 5 and kind == "rayleigh":
                cons = cons[6:]
            f = _slsqp(rss, x0, lo, hi, cons)
            if f is None:
                continue
            a = _aicc(float(f.fun), n, 3 * M + 1)
            comps = [comp_peak(kind, t, p) for p in split_params(kinds, f.x)]
            if kind == "gamma" and M == 3:
                out["dt_tig3_ms"], out["ri_tig3"] = _indices_from(comps, lm, T=float(t[-1]))
            if best is None or a < best[0]:
                best = (a, kind, M, comps)
    if best is not None:
        out["tig_best"] = f"{best[1]} M={best[2]}"
        out["dt_tig_ms"], out["ri_tig"] = _indices_from(best[3], lm, T=float(t[-1]))
    return out


def wang_feature_points(t, ys, lm) -> tuple:
    """Wang 2013 §3.2: 2 次微分（SDDVP）から D1〜D4 と振幅 A1〜A4、型（Wang の 5 型を pda2 の型で近似）。"""
    T = float(t[-1])
    d2 = _d2(t, ys)
    klass = int(lm["klass"])
    wtype = {1: 1, 3: 3}.get(klass, 5)
    ext = _extrema(d2, 1, len(t) - 1)
    amax = max((abs(d2[i]) for i, _ in ext), default=0.0)
    mins = [i for i, k in ext if k == "min" and abs(d2[i]) >= 0.1 * amax]   # 拍の先頭の微小な揺れは谷と数えない
    maxs = [i for i, k in ext if k == "max"]
    zc = [k for k in np.flatnonzero(np.sign(d2[:-1]) != np.sign(d2[1:]))]
    if not mins:
        return None, wtype
    i1 = mins[0]                                            # D1: SDDVP の最初の谷（b 波）
    notch = float(lm["notch_t"]) if np.isfinite(lm.get("notch_t", NAN)) else NAN
    lim2 = notch if (wtype in (1, 2) and np.isfinite(notch)) else 0.5 * T
    c2 = [i for i in maxs if i > i1 and t[i] < lim2]
    if c2:
        i2 = c2[0]                                          # D2: P1 の後の最初の山
    else:
        z2 = [k for k in zc if k > i1]
        if not z2:
            return None, wtype
        i2 = z2[0]                                          # 無ければ最初の零交差
    if wtype == 1 and np.isfinite(lm.get("dia_t", NAN)):
        i3 = int(np.argmin(np.abs(t - lm["dia_t"])))        # D3: 型1 は DVP の第 2 の山
    elif wtype in (2, 3, 4) and np.isfinite(notch):
        z3 = [k for k in zc if t[k] > notch]
        if not z3:
            return None, wtype
        i3 = z3[0]                                          # 切痕の後の最初の零交差
    else:
        z3 = [k for k in zc if 0.4 * T <= t[k] <= 0.5 * T and k > i2]
        if not z3:
            z3 = [k for k in zc if k > i2]
        if not z3:
            return None, wtype
        i3 = z3[0]                                          # 型5: 0.4〜0.5T の最初の零交差
    i4 = int(round(0.5 * (i3 + (len(t) - 1))))              # D4: P3 と終点の中点
    idx = [i1, i2, i3, i4]
    if not (i1 < i2 < i3 < i4):
        return None, wtype
    D = [float(t[i]) for i in idx]
    A = [float(ys[i]) for i in idx]
    return (D, A), wtype


def wang_init(t, ys, lm, M: int):
    """Wang 2013 表 1 の初期値（型別）。5 本目は D3・D4 の中点（記載なし → 既定）。"""
    T = float(t[-1])
    fp, wtype = wang_feature_points(t, ys, lm)
    if fp is None:
        return None, wtype
    D, A = fp
    col = {1: 0, 2: 1, 3: 2}.get(wtype, 3)
    Hf = [[0.8, 0.7, 0.7, 0.7], [0.8, 0.8, 0.7, 0.7], [0.8, 0.8, 0.8, 0.7], [0.3, 0.3, 0.3, 0.5]]
    H = [Hf[i][col] * A[i] for i in range(4)]
    mu = list(D)
    s = [D[0] / 3, (D[1] - D[0]) / 3 if wtype != 5 else D[1] / 3, min(T - D[2], D[2]) / 3, (T - D[3]) / 3]
    if M == 5:
        H.append(0.3 * float(np.interp(0.5 * (D[2] + D[3]), t, ys)))
        mu.append(0.5 * (D[2] + D[3]))
        s.append((D[3] - D[2]) / 3)
        order = np.argsort(mu)
        H, mu, s = [H[i] for i in order], [mu[i] for i in order], [s[i] for i in order]
    x0 = np.array([v for trip in zip(H, mu, s) for v in trip])
    x0[2::3] = np.maximum(x0[2::3], 0.004)
    return x0, wtype


def _wang_mcdm(crit):
    """Wang 2013 §3.3: 3 規準（Errx, Erry, NRMSE）を r = (max−a)/(max−min) で正規化、u = (0.35, 0.35, 0.30)、
    E=(1,1,1)・B=(0,0,0) に対する適合度 c = 1/(1 + Σ[u(e−r)]²/Σ[u(b−r)]²) が最大の候補の添字。"""
    a = np.asarray(crit, float)                 # 候補 × 3
    r = np.zeros_like(a)
    for j in range(3):
        mx, mn = np.nanmax(a[:, j]), np.nanmin(a[:, j])
        r[:, j] = (mx - a[:, j]) / (mx - mn) if mx > mn else 1.0
    u = np.array([0.35, 0.35, 0.30])
    num = np.sum((u * (1.0 - r)) ** 2, axis=1)
    den = np.sum((u * (0.0 - r)) ** 2, axis=1)
    c = 1.0 / (1.0 + num / np.where(den > 0, den, 1e-12))
    c[den <= 0] = 0.0                           # r が全部 0 の候補（すべて最悪）は選ばない
    return int(np.argmax(c))


def fit_wang(t, ys, lm, step: int = 1) -> dict:
    """Wang 2013: 4 ガウス → 規準を満たさなければ 5 ガウス。鍵点重み 1..100 の WLS（LM）、MCDM で重みを選ぶ。"""
    out = {"dt_wang_ms": NAN, "ri_wang": NAN, "ok_wang": 0, "w_wang": NAN, "M_wang": 0,
           "nrmse_wang": NAN, "errx_wang_ms": NAN, "wang_type": NAN}
    chosen = None
    for M in (4, 5):
        x0, wtype = wang_init(t, ys, lm, M)
        out["wang_type"] = wtype
        if x0 is None:
            break
        kinds = ["normal"] * M
        cands = []
        for wk in range(1, 101, max(1, step)):
            w = pda2._weights(t, lm, float(wk), halfwidth_s=0.0)      # 鍵点そのものに重み
            sw = np.sqrt(w)
            f = _lsq(lambda x, kinds=kinds: sw * (model_sum(kinds, t, x) - ys), x0,
                     jac=lambda x, sw=sw: _gauss_jac(t, x, sw))
            if f is None or not np.all(np.isfinite(f.x)):
                continue
            yhat = model_sum(kinds, t, f.x)
            acc = pda2.acceptance(t, ys, yhat, lm, w)
            cands.append((wk, f, acc))
        if not cands:
            continue
        i = _wang_mcdm([(c[2]["errx_ms"], c[2]["erry"], c[2]["nrmse"]) for c in cands])
        chosen = cands[i]
        out["M_wang"] = M
        if chosen[2]["ok"]:
            break
    if chosen is None:
        return out
    wk, f, acc = chosen
    kinds = ["normal"] * out["M_wang"]
    comps = [comp_peak("normal", t, p) for p in split_params(kinds, f.x)]
    out["dt_wang_ms"], out["ri_wang"] = _indices_from(comps, lm, T=float(t[-1]))
    out.update(ok_wang=int(bool(acc["ok"])), w_wang=float(wk), nrmse_wang=float(acc["nrmse"]),
               errx_wang_ms=float(acc["errx_ms"]))
    return out


def fit_couceiro(t, ys, lm, pts) -> dict:
    """Couceiro 2015: ガウス 5 本・表 1 の初期値と境界・不等式制約・MSE 最小（内点法 → SLSQP）。T1_d・R1_d（g4）。"""
    out = {"dt_cou_ms": NAN, "ri_cou": NAN, "cou_init": ""}
    x0, lo, hi, src = couceiro_init(pts)
    out["cou_init"] = src
    kinds = ["normal"] * 5

    def mse(x):
        return float(np.mean((model_sum(kinds, t, x) - ys) ** 2))
    f = _slsqp(mse, x0, lo, hi, couceiro_constraints(5))
    if f is None:
        return out
    p = split_params(kinds, f.x)
    T = float(t[-1])
    tt = np.unique(np.r_[np.linspace(0, T, 2000), p[0][1], p[1][1]])   # 中心の点も入れる（幅の小さい成分の取りこぼし防止）
    yf = gauss(tt, *p[0]) + gauss(tt, *p[1])      # g1+g2 = 主前進波
    i = int(np.argmax(yf))
    tf, hf = float(tt[i]), float(yf[i])
    if p[3][1] <= tf or p[3][1] > T:
        return out                                  # 反射波 g4 が前進波より前・拍の外なら失敗
    out["dt_cou_ms"] = float((p[3][1] - tf) * 1000.0)
    out["ri_cou"] = float(p[3][0] / hf) if hf > 1e-6 else NAN
    return out


def fleischhauer_generic(n_kernels: int, T: float, ymax: float = 1.0):
    """Fleischhauer 2020 表 D3（generic）: 初期値と境界。"""
    if n_kernels == 2:
        rows = [(0.8, 2 / 7, 2 / 7), (0.5, 4 / 7, 3 / 7)]
    elif n_kernels == 3:
        rows = [(0.8, 2 / 7, 2 / 7), (0.4, 4 / 7, 2 / 7), (0.2, 5 / 7, 2 / 7)]
    else:
        rows = [(0.8, 2 / 7, 2 / 7), (0.4, 3 / 7, 2 / 7), (0.4, 1 / 2, 2 / 7), (0.4, 45 / 70, 2 / 7)]
    x0, lo, hi = [], [], []
    for a, m, sd in rows:
        x0 += [a * ymax, m * T, sd * T * T2C]
        lo += [0.0, 0.0, 0.0]
        hi += [ymax, T, T]
    return np.array(x0), np.array(lo), np.array(hi)


def fit_fleischhauer(t, ys, lm, n_kernels: int) -> dict:
    """Fleischhauer 2020 GammaGauss{2,3}generic: Gamma（最頻値・SD）＋ Gaussian、表 D3、制約なし、RSS 最小。"""
    tag = f"fl{n_kernels}"
    out = {f"dt_{tag}_ms": NAN, f"ri_{tag}": NAN}
    T = float(t[-1])
    kinds = ["gamma_ms"] + ["normal"] * (n_kernels - 1)
    x0, lo, hi = fleischhauer_generic(n_kernels, T, float(np.max(ys)))
    lo[1::3] = np.maximum(lo[1::3], 1e-3)          # 最頻値 0 と SD 0 は数値上の特異点
    lo[2::3] = np.maximum(lo[2::3], 1e-3)
    f = _lsq(lambda x: model_sum(kinds, t, x) - ys, x0, lo, hi)
    if f is None:
        return out
    comps = [comp_peak(k, t, p) for k, p in zip(kinds, split_params(kinds, f.x))]
    if n_kernels == 2:
        out[f"dt_{tag}_ms"], out[f"ri_{tag}"] = _indices_from(comps, lm, 0, 1, T=T)
    else:
        out[f"dt_{tag}_ms"], out[f"ri_{tag}"] = _indices_from(comps, lm, T=T)
    return out


def basso_init(L: int, T: float, ymax: float = 1.0):
    """Basso 2024 表 1: a₀・m₀・σ₀・α₀ と境界（a∈[0,ymax]、m∈[0,T]、σ∈[0,T]、α 無制約 → ±50）。"""
    T2 = T * T2C
    tab = {2: [(0.8, 2 / 7 * T, 2 / 7 * T2), (0.5, 4 / 7 * T, 3 / 7 * T2)],
           3: [(0.8, 2 / 7 * T, 2 / 7 * T2), (0.4, 4 / 7 * T, 2 / 7 * T2), (0.2, 5 / 7 * T, 2 / 7 * T2)],
           4: [(0.8, 2 / 7 * T, 2 / 7 * T2), (0.4, 3 / 7 * T, 1 / 7 * T2), (0.4, 1 / 2 * T, 1 / 7 * T2),
               (0.4, 45 / 70 * T, 1 / 7 * T2)]}[L]
    x0, lo, hi = [], [], []
    for a, m, sd in tab:
        x0 += [a * ymax, m, sd, 1.0]
        lo += [0.0, 0.0, 1e-3, -50.0]
        hi += [ymax, T, T, 50.0]
    return np.array(x0), np.array(lo), np.array(hi)


def fit_basso(t, ys, lm, L: int) -> dict:
    """Basso 2024: 歪みガウス L 本（a, m, σ, α）・28 標本・RSS・a₁>a_k・m 単調・表 1 の初期値（内点法 → SLSQP）。"""
    tag = f"bas{L}"
    out = {f"dt_{tag}_ms": NAN, f"ri_{tag}": NAN, f"alpha_{tag}": NAN}
    T = float(t[-1])
    t28, y28 = _resample(t, ys, n=28)
    kinds = ["skew_b"] * L
    x0, lo, hi = basso_init(L, T, float(np.max(y28)))

    def rss(x):
        return float(np.sum((model_sum(kinds, t28, x) - y28) ** 2))
    cons = [{"type": "ineq", "fun": (lambda x, k=k: x[0] - x[4 * k])} for k in range(1, L)]
    cons += [{"type": "ineq", "fun": (lambda x, k=k: x[4 * (k + 1) + 1] - x[4 * k + 1])} for k in range(L - 1)]
    f = _slsqp(rss, x0, lo, hi, cons)
    if f is None:
        return out
    p = split_params(kinds, f.x)
    comps = [(float(q[1]), float(q[0])) for q in p]
    out[f"alpha_{tag}"] = float(p[0][3])
    if L == 2:
        out[f"dt_{tag}_ms"], out[f"ri_{tag}"] = _indices_from(comps, lm, 0, 1, T=T)
    else:
        out[f"dt_{tag}_ms"], out[f"ri_{tag}"] = _indices_from(comps, lm, T=T)
    return out


# ================================================================ 1 被験者
def replica_for_beat(t, y, fs, wang_step: int = 1) -> dict:
    """1 拍（生の波形）に前処理 → 鍵点 → 文献 6 本の分解。34番（VitalDB）からも使う。"""
    out = {}
    ys, _amp = pda2.preprocess(t, y, fs)
    if ys is None:
        out["err"] = "preprocess_none"
        return out
    lm = pda2.find_landmarks(t, ys)
    out["klass_own"] = int(lm["klass"])
    out["dt_own_ms"] = float((lm["dia_t"] - lm["sys_t"]) * 1000.0) if lm["klass"] in (1, 3) else NAN
    out["ri_own"] = float(lm["dia_v"] / lm["sys_v"]) if (lm["klass"] in (1, 3) and np.isfinite(lm["dia_v"])) else NAN
    pts = couceiro_points(t, ys, lm)
    for fn in (lambda: fit_goswami(t, ys, lm), lambda: fit_tigges(t, ys, lm, pts),
               lambda: fit_wang(t, ys, lm, wang_step),
               lambda: fit_couceiro(t, ys, lm, pts), lambda: fit_fleischhauer(t, ys, lm, 2),
               lambda: fit_fleischhauer(t, ys, lm, 3), lambda: fit_basso(t, ys, lm, 2),
               lambda: fit_basso(t, ys, lm, 3), lambda: fit_basso(t, ys, lm, 4)):
        try:
            out.update(fn())
        except Exception as e:      # noqa: BLE001
            out["err"] = (out.get("err", "") + "|" + str(e))[:80]
    return out


def replica_for_subject(args_tuple) -> dict:
    subj, row, hr, M, wang_step = args_tuple
    out = {"subj_no": int(subj)}
    try:
        y, fs = M.beat_of(row, hr)
        if y is None:
            out["err"] = "no_beat"
            return out
        t = np.arange(y.size) / fs
        out.update(replica_for_beat(t, y, fs, wang_step))
    except Exception as e:      # noqa: BLE001
        out["err"] = str(e)[:80]
    return out


def _worker(args_tuple):
    subj, row, hr, wang_step = args_tuple
    M = sys.modules.get("m20") or _load("20_pwdb_validity.py", "m20")
    return replica_for_subject((subj, row, hr, M, wang_step))


# ================================================================ 進捗（画面と JSON。scripts/status.py が読む）
class _Progress:
    """25 名ごと（または 60 秒ごと）に経過・速度・残り時間を出し、同じ内容を JSON に書く。"""

    def __init__(self, total: int, path: Path, jobs: int, wang_step: int, every: int = 25, every_s: float = 60.0):
        self.total, self.path, self.jobs, self.wang_step = total, path, jobs, wang_step
        self.every, self.every_s = every, every_s
        self.t0 = time.time()
        self.last = self.t0
        self.done = 0

    def _finite(self, rows):
        return {k: int(sum(1 for r in rows if np.isfinite(r.get(f"dt_{k}_ms", np.nan)))) for k, _l, _o in METHODS}

    def write(self, rows, state: str):
        el = time.time() - self.t0
        per = el / max(self.done, 1)
        eta = per * (self.total - self.done)
        rec = {"script": "33_pwdb_literature_replica", "state": state, "done": self.done, "total": self.total,
               "jobs": self.jobs, "wang_step": self.wang_step, "started": self.t0, "updated": time.time(),
               "elapsed_s": round(el), "per_subject_s": round(per, 2), "eta_s": round(eta),
               "finite_dt": self._finite(rows), "errors": int(sum(1 for r in rows if r.get("err")))}
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception:      # noqa: BLE001
            pass
        return rec

    def tick(self, rows):
        self.done = len(rows)
        now = time.time()
        if self.done % self.every == 0 or self.done == self.total or now - self.last >= self.every_s:
            self.last = now
            rec = self.write(rows, "running")
            print(f"  [{self.done}/{self.total}] 経過 {rec['elapsed_s'] / 60:.1f} 分・{rec['per_subject_s']:.1f} 秒/名"
                  f"（{self.jobs} 並列込み）・残り約 {rec['eta_s'] / 60:.0f} 分・例外 {rec['errors']}", flush=True)

    def finish(self, rows):
        self.done = len(rows)
        rec = self.write(rows, "done")
        print(f"  完了: {self.total} 名・{rec['elapsed_s'] / 60:.1f} 分", flush=True)


# ================================================================ 構築と報告
def build(root: Path, subset: str = "mod7", jobs: int = 1, limit: int = 0, wang_step: int = 1):
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
        work.append((subj, ppg.iloc[i].to_numpy(float), hr_by.get(subj, np.nan), wang_step))
        if limit and len(work) >= limit:
            break
    print(f"{len(work)} 名に文献 {len(METHODS)} 条件の分解を当てます（jobs={jobs}・Wang の重みの刻み {wang_step}）", flush=True)
    prog = _Progress(len(work), OUT / "literature_replica_progress.json", jobs, wang_step)
    rows = []
    if jobs > 1:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(max_workers=jobs) as ex:
            futs = [ex.submit(_worker, wk) for wk in work]
            for f in as_completed(futs):
                rows.append(f.result())
                prog.tick(rows)
    else:
        for wk in work:
            rows.append(_worker(wk))
            prog.tick(rows)
    prog.finish(rows)
    rep = pd.DataFrame(rows)
    rep["wang_step"] = int(wang_step)
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
          f"{'RI×pvr |ρ|':>12}{'層':>6}{'判定':>8}{'届く':>5}  {'ΔT 型1のみ':>13}")

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
        print(f"{label:<46}{n:>5}{extra:>7}{fa:>12}{la:>6}{va:>8}{reach_a:>5}{fb:>12}{lb:>6}{vb:>8}{reach_b:>5}  {fc:>13}")
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
        print(f"Couceiro の初期値: 表 1（a〜f 波・切痕の両端）{float((d['cou_init'] == 'couceiro').mean()):.0%}・"
              f"汎用（表 D1 generic）{float((d['cou_init'] == 'generic').mean()):.0%}")
    if "w_wang" in d:
        w = d["w_wang"].dropna()
        print(f"Wang の重みの刻み: {int(d['wang_step'].iloc[0]) if 'wang_step' in d else '?'}（文献は 1）")
        print(f"Wang の選ばれた重み: 中央値 {w.median():.0f}（10〜90% 点 {w.quantile(0.1):.0f}〜{w.quantile(0.9):.0f}）"
              f"／ 5 ガウスへ増やした拍 {float((d['M_wang'] == 5).mean()):.0%}／ 初期値が作れず当てられなかった拍 "
              f"{float((d['M_wang'] == 0).mean()):.0%}")
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


def run(root: Path, subset: str, jobs: int, limit: int = 0, wang_step: int = 1) -> None:
    d, C = build(root, subset=subset, jobs=jobs, limit=limit, wang_step=wang_step)
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
    t = np.arange(0, 0.9, 1 / 500.0)
    # 1. 基底と母数化（文献の式）
    y = rayleigh_tigges(t, 5.0, 0.10, 0.05)
    rep("Tigges の Rayleigh は t ≥ b でのみ非零", np.all(y[t < 0.10] == 0) and y[t > 0.11].max() > 0)
    g = gamma_mode_sd(t, 1.0, 0.12, 0.05)
    j = int(np.argmax(g))
    gm = g / np.sum(g)
    mean = float(np.sum(t * gm))
    sd = float(np.sqrt(np.sum((t - mean) ** 2 * gm)))
    rep("Fleischhauer 付録 C の母数化（最頻値 0.12・SD 0.05・高さ 1 を復元）",
        abs(t[j] - 0.12) < 0.003 and abs(sd - 0.05) < 0.006 and abs(g[j] - 1.0) < 1e-6, f"mode={t[j]:.3f} sd={sd:.3f} h={g[j]:.3f}")
    sb = skew_basso(t, 0.7, 0.20, 0.05, 2.0)
    k = int(np.argmax(sb))
    mean_b = float(np.sum(t * sb) / np.sum(sb))
    sd_b = float(np.sqrt(np.sum((t - mean_b) ** 2 * sb) / np.sum(sb)))
    rep("Basso 付録 A の母数化（最頻値 0.20・SD 0.05・高さ 0.7 を復元、α=2）",
        abs(t[k] - 0.20) < 0.004 and abs(sb[k] - 0.7) < 1e-6 and abs(sd_b - 0.05) < 0.006, f"mode={t[k]:.3f} sd={sd_b:.3f}")
    rep("α=0 の Basso 基底はガウスに一致", np.allclose(skew_basso(t, 1.0, 0.3, 0.05, 0.0), gauss(t, 1.0, 0.3, 0.05), atol=1e-6))
    rep("AICc（Tigges 式 8・K=3M+1）: 母数が多いほど罰則が増え、N が足りなければ ∞",
        _aicc(1.0, 40, 4) < _aicc(1.0, 40, 7) < _aicc(1.0, 40, 10) and not np.isfinite(_aicc(1.0, 10, 9)))
    rep("Wang の MCDM: 3 規準すべてで最良の候補が選ばれる", _wang_mcdm([(10, 0.02, 0.03), (3, 0.005, 0.01), (6, 0.01, 0.02)]) == 1)
    x0, lo, hi = fleischhauer_generic(2, 0.7)
    rep("Fleischhauer 表 D3（2 核）: a₀ 0.8/0.5、m₀ 2/7T・4/7T、σ₀ (2/7, 3/7)T·T2",
        np.allclose(x0, [0.8, 0.2, 0.2 * T2C, 0.5, 0.4, 0.3 * T2C]))
    xb, lb, hb = basso_init(2, 0.7)
    rep("Basso 表 1（L=2）: α₀ = 1、σ₀ = 2/7·T2", xb[3] == 1.0 and abs(xb[2] - 0.2 * T2C) < 1e-9 and hb[1] == 0.7)
    rep("役割規則: 前進波は最初の高い成分、反射波は拡張期鍵点に最も近い後続成分",
        pick_roles([(0.10, 1.0), (0.25, 0.3), (0.40, 0.4), (0.70, 0.2)], {"dia_t": 0.42}) == (0, 2))
    # 1b. 自分の模型で作った拍を復元する（再現コードの基本検査。真値 ΔT = 300 ms）
    tb = np.arange(0, 0.85, 1 / 500.0)
    lm_b = {"sys_t": 0.20, "sys_v": 1.0, "notch_t": 0.42, "dia_t": 0.50, "dia_v": 0.4, "klass": 1, "i_sys": 100, "source": "extrema"}
    yb = skew_basso(tb, 1.0, 0.20, 0.05, 2.0) + skew_basso(tb, 0.4, 0.50, 0.08, 0.0)
    rb0 = fit_basso(tb, yb, lm_b, 2)
    rep("Basso L=2 は自分の模型（2 本・ΔT 300 ms）を 28 標本から復元する（±15 ms）", abs(rb0["dt_bas2_ms"] - 300) < 15,
        f"ΔT {rb0['dt_bas2_ms']:.0f} ms・α {rb0['alpha_bas2']:.2f}")
    yf_ = gamma_mode_sd(tb, 1.0, 0.20, 0.06) + gauss(tb, 0.4, 0.50, 0.08)
    rf0 = fit_fleischhauer(tb, yf_, lm_b, 2)
    rep("Fleischhauer 2 核は自分の模型（Gamma+Gauss・ΔT 300 ms）を復元する（±15 ms）", abs(rf0["dt_fl2_ms"] - 300) < 15,
        f"ΔT {rf0['dt_fl2_ms']:.0f} ms")
    sqe = np.sqrt(np.e)
    yg = (0.15 * sqe) * (tb / 0.15 ** 2) * np.exp(-tb ** 2 / (2 * 0.15 ** 2))
    u = tb - 0.30
    yg = yg + np.where(u > 0, (0.5 * 0.15 * sqe) * (u / 0.15 ** 2) * np.exp(-u ** 2 / (2 * 0.15 ** 2)), 0.0)
    lm_g = dict(lm_b, sys_t=float(tb[int(np.argmax(yg))]), sys_v=float(np.max(yg)))
    rg0 = fit_goswami(tb, yg / np.max(yg), lm_g)
    rep("Goswami は自分の模型（Rayleigh 2 本・tp₂−tp₁ = 300 ms・RI 0.5）を復元する（±20 ms・±0.1）",
        abs(rg0["dt_gos_ms"] - 300) < 20 and abs(rg0["ri_gos"] - 0.5) < 0.1, f"ΔT {rg0['dt_gos_ms']:.0f} ms・RI {rg0['ri_gos']:.2f}")
    yw = gauss(tb, 1.0, 0.20, 0.05) + gauss(tb, 0.3, 0.33, 0.05) + gauss(tb, 0.4, 0.50, 0.08) + gauss(tb, 0.15, 0.68, 0.08)
    ysw, _ = pda2.preprocess(tb, yw, 500.0)
    lm_w = pda2.find_landmarks(tb, ysw)
    rw0 = fit_wang(tb, ysw, lm_w, step=10)
    rep("Wang は自分の模型（ガウス 4 本）を規準内で当てる（Errx < 6 ms・採用）", rw0["ok_wang"] == 1 and rw0["errx_wang_ms"] < 6,
        f"M={rw0['M_wang']}・w={rw0['w_wang']}・Errx {rw0['errx_wang_ms']:.1f} ms・ΔT {rw0['dt_wang_ms']:.0f} ms")
    # 2. 模擬 PWDB で全手法
    C = _load("26_pwdb_compare.py", "m26")
    with tempfile.TemporaryDirectory() as td:
        root, _kinds = C._selftest_root(Path(td), n=24)
        with contextlib.redirect_stdout(io.StringIO()):
            d, C2 = build(root, subset="all", jobs=1, wang_step=10)
        cols = [f"dt_{k}_ms" for k, _l, _o in METHODS] + [f"ri_{k}" for k, _l, _o in METHODS]
        rep("全手法の列が揃う", all(c in d for c in cols), f"n={len(d)}")
        fin = {k: float(d[f"dt_{k}_ms"].notna().mean()) for k, _l, _o in METHODS}
        rep("模擬の 2 ガウス拍で各手法が ΔT を返す（Goswami・Fleischhauer 2・Basso 2・Tigges・Wang・Couceiro ≥ 50%）",
            all(fin[k] >= 0.5 for k in ("gos", "fl2", "bas2", "tig", "wang", "cou")),
            "・".join(f"{k} {v:.0%}" for k, v in fin.items()))
        rep("例外が無い", "err" not in d or d["err"].isna().all(), str(d["err"].dropna().head(2).tolist()) if "err" in d else "")
        rep("Wang の採否・重み・成分数・型が記録される", set(d["ok_wang"].dropna().unique()) <= {0, 1}
            and d["M_wang"].isin([0, 4, 5]).all() and d["w_wang"].dropna().between(1, 100).all())
        rep("Tigges の AICc が基底×M を 1 つ選ぶ", d["tig_best"].str.contains("M=").mean() >= 0.9,
            d["tig_best"].value_counts().head(3).to_dict().__repr__())
        rep("Couceiro の初期値の由来（表 1 か generic）が記録される", d["cou_init"].isin(["couceiro", "generic"]).all(),
            d["cou_init"].value_counts().to_dict().__repr__())
        M = C2.M
        hae = M._read_named(root / "pwdb_haemod_params.csv", ("subj_no", "HR"))
        import pandas as pd
        ppg = pd.read_csv(root / "PWs" / "csv" / "PWs_Digital_PPG.csv", skipinitialspace=True)
        y0, fs = M.beat_of(ppg.iloc[0].to_numpy(float), float(hae["HR"].iloc[0]))
        tt = np.arange(y0.size) / fs
        ys, _ = pda2.preprocess(tt, y0, fs)
        lm0 = pda2.find_landmarks(tt, ys)
        pts = couceiro_points(tt, ys, lm0)
        rg = fit_goswami(tt, ys, lm0)
        rep("Goswami: 前進波のピークが収縮期ピーク以前、反射波の到達 D が 0.3t₁〜0.9T、DPS が出る",
            np.isfinite(rg["dt_gos_ms"]) and 0.3 * lm0["sys_t"] * 1000 - 1 <= rg["gos_D_ms"] <= 0.9 * tt[-1] * 1000 + 1
            and np.isfinite(rg["dps_gos_ms"]), f"ΔT {rg['dt_gos_ms']:.0f} ms・RI {rg['ri_gos']:.2f}・D {rg['gos_D_ms']:.0f} ms")
        rc = fit_couceiro(tt, ys, lm0, pts)
        rep("Couceiro: 1 拍で ΔT・RI が有限", np.isfinite(rc["dt_cou_ms"]) and np.isfinite(rc["ri_cou"]),
            f"ΔT {rc['dt_cou_ms']:.0f} ms・RI {rc['ri_cou']:.2f}・初期値 {rc['cou_init']}")
        rb = fit_basso(tt, ys, lm0, 2)
        rep("Basso L=2: 28 標本で ΔT が有限、α が記録される", np.isfinite(rb["dt_bas2_ms"]) and np.isfinite(rb["alpha_bas2"]),
            f"ΔT {rb['dt_bas2_ms']:.0f} ms・α {rb['alpha_bas2']:.2f}")
        rw = fit_wang(tt, ys, lm0, step=25)
        rep("Wang: 重み 1..100 の候補から MCDM で 1 つ選び、採否が付く", rw["M_wang"] in (4, 5) and np.isfinite(rw["w_wang"]),
            f"M={rw['M_wang']}・w={rw['w_wang']}・ok={rw['ok_wang']}・Errx {rw['errx_wang_ms']:.1f} ms")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            res = report(d, C2, out_dir=Path(td) / "out", tag="_selftest")
        out = buf.getvalue()
        rep("表・逸脱表・読み方が出て CSV が書かれる", "逸脱表" in out and "読み方" in out and "lm" in res
            and (Path(td) / "out" / "literature_replica_selftest.csv").exists())
    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


def main() -> None:
    # SLSQP が一歩だけ境界の外に出て切り詰めるときの警告（結果は境界内。無害）と、全て NaN の列の nanmedian の警告を抑える
    warnings.filterwarnings("ignore", message="Values in x were outside bounds")
    warnings.filterwarnings("ignore", message="All-NaN slice")
    warnings.filterwarnings("ignore", message="Mean of empty slice")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pwdb", type=str, default=None)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--all", action="store_true", help="subj%7==0 の部分集合ではなく全例")
    ap.add_argument("--limit", type=int, default=0, help="先頭 N 名だけ（形式の確認用）")
    ap.add_argument("--wang-step", type=int, default=1, help="Wang の重み 1..100 の刻み（文献は 1。時間が無ければ 5）")
    ap.add_argument("--report-only", action="store_true", help="保存済みの CSV（literature_replica[_all].csv）から表だけ作り直す")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())
    if args.report_only:
        import pandas as pd
        tag = "_all" if args.all else ""
        fp = OUT / f"literature_replica{tag}.csv"
        if not fp.exists():
            raise SystemExit(f"{fp} がありません（先に --pwdb で回す）")
        d = pd.read_csv(fp)
        C = _load("26_pwdb_compare.py", "m26")
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = _Tee(old, buf)
        try:
            report(d, C, tag=tag)
        finally:
            sys.stdout = old
        (OUT / f"literature_replica_report{tag}.txt").write_text(buf.getvalue(), encoding="utf-8")
        print(f"\n表の全文: {OUT / f'literature_replica_report{tag}.txt'}")
        return
    if not args.pwdb:
        ap.error("--pwdb を指定してください（--selftest・--report-only なら不要）")
    run(Path(args.pwdb), "all" if args.all else "mod7", max(1, args.jobs), args.limit, max(1, args.wang_step))


if __name__ == "__main__":
    main()

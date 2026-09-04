# -*- coding: utf-8 -*-
"""PDA 第2版 ― 文献の指摘を取り込んだ脈波分解。

`src/pda.py`（凍結版）の点検で見つかった問題への対処をまとめたもの。
凍結版は研究1の解析に使ったまま残し、本モジュールは並行して検証する。

対処した問題（`docs/research/pda_literature_review.md` 参照）
-----------------------------------------------------------
(1) 拡張期の減衰を表す項が無く、第2カーネルが吸収して拍長に引きずられていた
    → **貯留槽を明示的に扱う。2つの経路を用意して同じ規準で比べる**
(2) 鍵点の位置が正しいかを検算していなかった（Wang 2013）
    → **Errx・Erry・NRMSE を採否の規準にする**
(3) 基底関数の裾が拡張期に合わない
    → **ガンマ経路を用意**（裾が exp(−βt) で Windkessel と同形）
(4) 成分間の不等式制約が無く役割が入れ替わっていた（Couceiro 2015）
    → **ピーク時刻の単調性と振幅の大小を制約する**
(5) 微分に依存する初期化は雑音に弱い（Fleischhauer 2020）
    → **汎用初期値を主、ランドマーク由来を副とする多点起動**
(6) 拍ごとの線形ベースライン除去をしていなかった（Tigges 2017・Wang 2013）
    → **前処理に入れる**
(7) 残差が一様重みだった（Wang 2013）
    → **鍵点に重みを置く WLS**

2つの経路
---------
    route="two_stage"   貯留槽を拡張期後半だけで当てはめて差し引き、
                        残差を歪みガウス2成分に分解する。
                        歪みガウスは進行波に適した形であり、貯留槽は
                        進行波の無い区間で錨づけるので反射波から振幅を盗まない
    route="gamma3"      ガンマ3成分を同時に当てはめ、最も遅い成分を貯留槽とみなす。
                        Tigges 2017 が実測7,805拍の AICc で選んだ模型

どちらも**成分は3つ**（前進波・反射波・貯留槽）である。物理的に数えるべき対象の数と、
AICc がデータから選んだ数が一致する。18 Hz に帯域制限した1拍の独立な標本は 24〜40 点しか
なく、成分あたり3母数として5成分（16母数）は過剰母数化になる。

母数の取り方
------------
振幅・位置・幅ではなく **ピーク高さ・ピーク時刻・幅・歪度**で持つ。
こうすると ΔT と RI が母数そのものの差と比になり、条件数が良くなるうえ、
**拍ごとに ΔT・RI の標準誤差が出せる**。「この拍の RI は 0.42 ± 0.15 だから使わない」
という選別ができる。凍結版の3つの収束検算より実質的な検算になる。

次数の適応
----------
既定は3成分。**当てはまりでは上げない**（カーネルを増やせば必ず当てはまるので全例が上がる）。
上げるのは同定性が損なわれたときだけである。すなわち Errx が閾値を超えるか、
ΔT の異なる競合解が残差で拮抗する場合に、収縮後期波を1つ足して4成分にする。
上げた拍の割合を必ず報告すること。
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import least_squares
from scipy.signal import butter, filtfilt
from scipy.special import erf

SQRT2 = np.sqrt(2.0)

# --- 採否の規準（Wang 2013 の閾値。amplitude を1に正規化した波形に対して）
ERRX_MS = 6.0      # 鍵点の時間位置の絶対誤差の総和 [ms]
ERRY = 0.01        # 鍵点の振幅の絶対誤差の総和
NRMSE_MAX = 0.02   # 重み付き正規化二乗平均平方根誤差
W_KEY = 20.0       # 鍵点に置く重み（Wang は 1〜100 を探索。既定は中間）
LOWPASS_HZ = 18.0  # Tigges 2017・Couceiro 2015 に合わせる
# ΔT の標準誤差の上限 [ms]。研究1で観測した症例内 ΔPWTT の標準偏差が 18 ms なので、
# それを超える誤差の拍は問いに何も寄与しない。当てはまりの規準（NRMSE・Errx・Erry）
# だけでは、成分の振幅が潰れて時刻が同定できていない解を通してしまう
# （`scripts/25_pda2_validate.py` T4 で σ=11,725 ms の解が採用されるのを確認した）。
SE_DT_MAX_MS = 20.0


# ============================================================ 基底関数
def _skew_tables(n: int = 1601):
    """歪みガウスの形状 f(z)=exp(−z²/2)(1+erf(αz/√2)) について、
    α ごとのピーク位置 m(α)[z単位] とピーク値 v(α) を数値表にする。

    これがあると (ピーク高さ, ピーク時刻) で母数化できる。閉じた式が無いので表引きする。
    """
    # Basso 2024 は α に境界を置かない（左歪みも許す）。左歪みを禁じると、
    # 反射波の歪みが下限 0 に潰れてモデルが α に無感応になり、共分散が壊れる
    # （実際に起きた。25番 T4 参照）。ここでは対称に [−8, 8] とする。
    alphas = np.linspace(-8.0, 8.0, n)
    zz = np.linspace(-6.0, 6.0, 6001)
    m = np.empty(n)
    v = np.empty(n)
    for i, a in enumerate(alphas):
        f = np.exp(-0.5 * zz * zz) * (1.0 + erf(a * zz / SQRT2))
        j = int(np.argmax(f))
        m[i] = zz[j]
        v[i] = f[j]
    return alphas, m, v


_A_GRID, _M_GRID, _V_GRID = _skew_tables()


def _skew_mv(alpha):
    a = np.clip(alpha, _A_GRID[0], _A_GRID[-1])
    return np.interp(a, _A_GRID, _M_GRID), np.interp(a, _A_GRID, _V_GRID)


def skew_peak(t: np.ndarray, h: float, tp: float, w: float, alpha: float) -> np.ndarray:
    """歪みガウス。**ピーク高さ h をちょうど時刻 tp でとる**ように母数化してある。

    進行波（前進波・反射波）に適した形。裾は exp(−z²/2) で速く落ちるため、
    拡張期の下降（Windkessel の exp(−t/RC)）を表すのには向かない。
    """
    m, v = _skew_mv(alpha)
    mu = tp - m * w
    z = (t - mu) / w
    return (h / v) * np.exp(-0.5 * z * z) * (1.0 + erf(alpha * z / SQRT2))


def gamma_peak(t: np.ndarray, h: float, tp: float, rise: float,
               shape: float) -> np.ndarray:
    """ガンマ関数。到達時刻 tp−rise から立ち上がり、ピーク高さ h を時刻 tp でとる。

        u = t − (tp − rise)
        g = h · exp[(α−1)·(ln u − ln rise) − β(u − rise)],   β = (α−1)/rise,  u > 0

    Γ(α) を陽に計算しないので、Fleischhauer 2020 が報告した倍精度の発散が起きない。
    裾が exp(−βu) なので**拡張期の下降をそのまま表せる**。shape=α>1 を要求する。

    位置母数について
    ----------------
    Tigges 2017 のガンマには到達時刻の母数が無く、全成分が拍の先頭から立ち上がる。
    そのため遅れて到達する反射波を表しきれず、拍が短い（心拍が速い）ときに成分が
    入れ替わって破綻する（`scripts/25_pda2_validate.py` T3 で HR 80 以上で確認。
    ΔT の心拍を通じた幅 155 ms）。Couceiro 2015 のガウスは位置母数を持つ。
    基底関数の形だけを比べる 2×2 の対照を成り立たせるため、形はガンマのまま
    **到達時刻だけ**を母数に加えた。立ち上がり時間 rise = tp − 到達時刻 として持つので、
    箱型の境界だけで「到達は必ずピークより前」が保証でき、ピーク母数化も保たれる。
    """
    r = max(float(rise), 1e-4)
    a1 = max(shape - 1.0, 1e-6)
    beta = a1 / r
    out = np.zeros_like(t)
    u = np.asarray(t, float) - (float(tp) - r)
    pos = u > 1e-9
    uu = u[pos]
    out[pos] = h * np.exp(a1 * (np.log(uu) - np.log(r)) - beta * (uu - r))
    return out


def component_sd(kind: str, w: float, shape: float) -> float:
    """成分の標準偏差。基底関数の種類によらず比べられるようにする。

    Goswami 2010 の差分パルス幅 DPS = σ_reflected − σ_forward を計算するために要る。
    同論文では健常 30 歳で 10 ms、高血圧 55 歳で 90 ms と大きく開いた。
    Lee 2011（真の熱希釈 SVR 参照）と Awad 2007 も、脈波の幅が反射係数より
    末梢血管抵抗をよく弁別すると報告しており、幅は独立に支持されている。
    """
    if kind == "skew":
        # 歪み正規分布: σ = ω·sqrt(1 − 2δ²/π),  δ = α/√(1+α²)   （Basso 2024 付録）
        d = float(shape) / np.sqrt(1.0 + float(shape) ** 2)
        return float(w) * np.sqrt(max(1.0 - 2.0 * d * d / np.pi, 1e-9))
    # ガンマ: 形状 α・率 β=(α−1)/rise のとき σ = √α/β = √α·rise/(α−1)
    a1 = max(float(shape) - 1.0, 1e-6)
    return float(np.sqrt(max(shape, 1e-9)) * float(w) / a1)


# ============================================================ 前処理
def preprocess(t: np.ndarray, y: np.ndarray, fs: float,
               lowpass_hz: float = LOWPASS_HZ, detrend: bool = True):
    """低域通過 → 拍ごとの線形ベースライン除去 → 振幅正規化。

    Tigges 2017・Wang 2013 の前処理に合わせる。凍結版は最小値を引くだけだった。
    """
    y = np.asarray(y, float)
    if lowpass_hz and fs > 2.5 * lowpass_hz:
        b, a = butter(4, lowpass_hz / (fs / 2.0), btype="low")
        y = filtfilt(b, a, y)
    if detrend and len(y) > 3:
        # 両端を結ぶ直線を引く（拍は極小点で切り出してある前提）
        base = np.linspace(y[0], y[-1], len(y))
        y = y - base
    y = y - float(np.min(y))
    amp = float(np.max(y))
    if amp <= 0:
        return None, 0.0
    return y / amp, amp


# ============================================================ ランドマーク
def _refine(t: np.ndarray, y: np.ndarray, i: int):
    """極値の位置と値を放物線補間で副標本精度にする。

    500 Hz では標本間隔が 2 ms あり、補間しないと鍵点1つあたり最大 2 ms の
    離散化誤差が乗る。鍵点3つで 6 ms となり、Wang の閾値と同じ大きさになってしまう。
    """
    if i <= 0 or i >= len(y) - 1:
        return float(t[i]), float(y[i])
    a, b, c = float(y[i - 1]), float(y[i]), float(y[i + 1])
    den = a - 2.0 * b + c
    if abs(den) < 1e-15:
        return float(t[i]), float(y[i])
    d = 0.5 * (a - c) / den
    d = float(np.clip(d, -1.0, 1.0))
    dt = float(t[1] - t[0])
    return float(t[i] + d * dt), float(b - 0.25 * (a - c) * d)


def find_landmarks(t: np.ndarray, y: np.ndarray) -> dict:
    """収縮期ピーク・重複切痕・拡張期ピークを探し、波形型を判定する。

    まず波形そのものの極値を探し、見つからなければ2次微分の特徴点で代用する。
    Dawber の分類に倣い、どこまで見つかったかで型を返す。
    型ごとに成績を出せるようにするための情報でもある。

    返り値の klass:
        1 明瞭な重複切痕と拡張期ピークがある
        2 切痕は無いが下降が水平になる（2次微分で代用）
        3 切痕は無いが下降の角度が明瞭に変わる（2次微分で代用）
        4 収縮期内に反射波が乗る（拡張期ピークが収縮期側にある）
        5 何も見つからない
    """
    n = len(t)
    i_sys = int(np.argmax(y))
    sys_t, sys_v = _refine(t, y, i_sys)
    out = {"sys_t": sys_t, "sys_v": sys_v, "i_sys": i_sys,
           "notch_t": np.nan, "dia_t": np.nan, "dia_v": np.nan,
           "klass": 5, "source": "none"}
    if i_sys >= n - 5:
        return out

    seg = y[i_sys:]
    ts = t[i_sys:]
    # --- 1. 波形そのものの極小 → 極大
    d = np.diff(seg)
    up = np.flatnonzero((d[:-1] <= 0) & (d[1:] > 0))    # 極小
    if up.size:
        j_min = int(up[0]) + 1
        rest = seg[j_min:]
        if rest.size > 3:
            d2 = np.diff(rest)
            dn = np.flatnonzero((d2[:-1] > 0) & (d2[1:] <= 0))   # 極大
            if dn.size:
                j_max = j_min + int(dn[0]) + 1
                nt, _ = _refine(t, y, i_sys + j_min)
                dt_, dv = _refine(t, y, i_sys + j_max)
                out.update(notch_t=nt, dia_t=dt_, dia_v=dv, klass=1, source="extrema")
                return out

    # --- 2. 2次微分で代用（切痕が見えない波形）
    d2y = np.gradient(np.gradient(y))
    k0 = i_sys + max(3, int(0.04 * n))
    k1 = int(0.92 * n)
    if k0 < k1:
        j = k0 + int(np.argmax(d2y[k0:k1]))          # 下降が緩む点＝切痕の代用
        out["notch_t"] = _refine(t, d2y, j)[0]
        k2 = j + max(3, int(0.03 * n))
        if k2 < k1:
            j2 = k2 + int(np.argmin(d2y[k2:k1]))     # その後の凸＝拡張期ピークの代用
            out.update(dia_t=_refine(t, -d2y, j2)[0], dia_v=float(y[j2]),
                       klass=3, source="d2")
        else:
            out.update(klass=2, source="d2")
    # --- 3. 収縮期内の肩（型4）
    if not np.isfinite(out["dia_t"]):
        k0b, k1b = max(3, int(0.25 * i_sys)), i_sys
        if k1b - k0b > 4:
            j3 = k0b + int(np.argmin(d2y[k0b:k1b]))
            if y[j3] > 0.3:
                out.update(dia_t=float(t[j3]), dia_v=float(y[j3]), klass=4, source="d2_sys")
    return out


def early_features(t: np.ndarray, y: np.ndarray) -> dict:
    """Hellqvist 2024 の早期振幅比 Am_b/Am_p1 と、その母点 p1・b を返す。

    Hellqvist 2024（Front Cardiovasc Med 11:1350726）は指尖 PPG から既知の特徴量 136 と
    新規 13 を作り、機械学習で大動脈硬化を推定した（33名・頸大腿PWV を参照）。
    最も重要だったのは新しい振幅比 **Am_b / Am_p1** で、頸大腿PWV と r = −0.81、
    大動脈PWV と r = −0.75。既報のどれより強い（硬さ指数と中枢PWV は r = 0.58〜0.66、
    加齢指数 (b−c−d−e)/a は r = 0.65、ばね定数は r = −0.72）。

    同論文は明示的にこう書いている ──
      「大動脈硬化を推定するには、硬さ指数のように S と D の**ピーク間の時間**に頼る
        指標ではなく、波形のこの早期部分にもっと注目すべきである」

    **我々の ΔT はまさに「S と D のピーク間の時間」である。** だから同じ土俵に並べる。

    定義
    ----
    p1  収縮期ピークの新しい求め方。1次微分の最初の山 w（最大傾斜）の後、下降の
        初期の直線部分に接線を引き、その零交点を p1 とする。ここでは下降が最も急な点
        （＝2次微分の最初の谷。標準命名の b 波）で接線を取る:

            t_p1 = t_b − d1(t_b) / d2(t_b)

        Hellqvist は「6つの波形型すべてで機能した」と報告している。型1では収縮期ピーク S と
        一致することが多く、他の型では前収縮期切痕と一致することがある。
        **切痕の無い波形（我々の未解決問題）でも収縮期ピークを定義できる**点が要である。
    b   2次微分の最初の谷。
    比  Am_b / Am_p1 = y(t_b) / y(t_p1)。どちらも拍の立ち上がり側の振幅である。
        伝播が速いほど（硬いほど）比は小さくなる、というのが報告されている向き。

    y は前処理済み（基線 0・最大 1）を想定する。比なので正規化は打ち消し合う。
    """
    t = np.asarray(t, float)
    y = np.asarray(y, float)
    n = len(t)
    out = {"p1_t": np.nan, "p1_v": np.nan, "b_t": np.nan, "b_v": np.nan,
           "w_t": np.nan, "amb_amp1": np.nan}
    if n < 16:
        return out
    dt = float(np.median(np.diff(t)))
    if not np.isfinite(dt) or dt <= 0:
        return out
    d1 = np.gradient(y, dt)
    d2 = np.gradient(d1, dt)
    i_sys = int(np.argmax(y))
    if i_sys < 4:
        return out
    i_w = int(np.argmax(d1[:i_sys]))                     # 1次微分の最初の山
    out["w_t"] = float(t[i_w])
    lo, hi = max(i_w + 1, 2), min(i_sys + 1, n - 2)      # b は w と収縮期ピークの間
    if hi - lo < 2:
        return out
    i_b = lo + int(np.argmin(d2[lo:hi]))
    t_b = _refine(t, -d2, i_b)[0]                        # 副標本精度で谷を取る
    if not np.isfinite(t_b):
        t_b = float(t[i_b])
    d1_b = float(np.interp(t_b, t, d1))
    d2_b = float(np.interp(t_b, t, d2))
    if not (d2_b < 0):                                   # 下降していなければ接線を引けない
        return out
    t_p1 = t_b - d1_b / d2_b                             # 接線の零交点
    if not (t_b < t_p1 <= t[-1]):
        return out
    am_b = float(np.interp(t_b, t, y))
    am_p1 = float(np.interp(t_p1, t, y))
    if not (am_p1 > 1e-6):
        return out
    out.update(p1_t=float(t_p1), p1_v=am_p1, b_t=float(t_b), b_v=am_b,
               amb_amp1=am_b / am_p1)
    return out


def _key_indices(t: np.ndarray, lm: dict) -> np.ndarray:
    """鍵点（収縮期ピーク・切痕・拡張期ピーク）の標本番号。"""
    idx = [lm["i_sys"]]
    for k in ("notch_t", "dia_t"):
        if np.isfinite(lm[k]):
            idx.append(int(np.argmin(np.abs(t - lm[k]))))
    return np.unique(np.array(idx, int))


def _weights(t: np.ndarray, lm: dict, w_key: float = W_KEY, halfwidth: int = 3):
    """鍵点とその近傍に重みを置く（Wang 2013 の WLS）。"""
    w = np.ones_like(t)
    for i in _key_indices(t, lm):
        a, b = max(0, i - halfwidth), min(len(t), i + halfwidth + 1)
        w[a:b] = w_key
    return w


# ============================================================ 貯留槽
def reservoir_shape(t: np.ndarray, t_a: float, tau: float, rise_exp: float = 2.0):
    """貯留槽の形（振幅1に正規化）。立ち上がりの形は固定し、当てはめない。"""
    s = np.clip((t - t[0]) / max(t_a - t[0], 1e-6), 0.0, 1.0) ** rise_exp
    return s * np.exp(-np.maximum(t - t_a, 0.0) / max(tau, 1e-3))


def estimate_reservoir_tau(t: np.ndarray, y: np.ndarray, lm: dict) -> dict:
    """**進行波が消えたあとの区間だけ**で時定数 τ を決める。

    最初の実装では窓の開始を拡張期ピークに置いたが、そこは反射波の頂上であり、
    その裾は窓の中まで伸びる。反射波を貯留槽と誤認して振幅を過大に見積もり、
    差し引いた残差が負に振れて当てはめが破綻した。
    窓は**拡張期ピークから十分に離した位置**から始める。

    振幅 d はここでは決めない。波と同時に決めることで、貯留槽が
    収縮期の波から振幅を盗むことも、過剰に差し引くことも防ぐ。
    """
    T = float(t[-1] - t[0])
    base = lm["dia_t"] + 0.10 if np.isfinite(lm["dia_t"]) else t[0] + 0.62 * T
    t_a = float(np.clip(max(base, t[0] + 0.62 * T), t[0] + 0.45 * T, t[0] + 0.85 * T))
    m = t >= t_a
    if m.sum() < 6:
        return {"t_a": t_a, "tau": 0.35, "ok": False}
    tt, yy = t[m] - t_a, y[m]

    def resid(p):
        return p[0] * np.exp(-tt / max(p[1], 1e-3)) - yy

    best = None
    for tau0 in (0.15, 0.30, 0.60, 1.00):
        try:
            r = least_squares(resid, [max(float(yy[0]), 1e-3), tau0],
                              bounds=([0.0, 0.08], [1.5, 2.0]), max_nfev=400)
        except Exception:
            continue
        if best is None or r.cost < best.cost:
            best = r
    if best is None:
        return {"t_a": t_a, "tau": 0.35, "ok": False}
    return {"t_a": t_a, "tau": float(best.x[1]), "d_hint": float(best.x[0]), "ok": True}


# ============================================================ 当てはめ
def _multistart(resid, starts, lo, hi, max_nfev=1200):
    """複数の初期値から当てはめ、残差の小さい順に返す。

    x_scale="jac" は母数ごとの尺度をヤコビアンから自動で決める。本問題は母数の
    列ノルムが 0.2〜140 と 600 倍開いており（振幅・時刻・幅・歪みが混在する）、
    既定の等倍尺度だと信頼領域が最も敏感な母数に合わせて縮み、反復回数が跳ね上がる。
    """
    sols = []
    for x0 in starts:
        try:
            r = least_squares(resid, np.clip(x0, lo + 1e-9, hi - 1e-9),
                              bounds=(lo, hi), method="trf", x_scale="jac",
                              max_nfev=max_nfev)
            sols.append(r)
        except Exception:
            continue
    sols.sort(key=lambda r: r.cost)
    return sols


def _wave_starts(t, y, lm, n_waves: int):
    """汎用初期値を主、ランドマーク由来を副とする（Fleischhauer 2020）。

    微分に依存する初期化は雑音を増幅するので、汎用値を先頭に置く。
    """
    T = float(t[-1] - t[0])
    t0 = float(t[0])
    sys_t, sys_v = lm["sys_t"], lm["sys_v"]
    generic = [(sys_v, sys_t, 0.06, 2.0)]
    for k in range(1, n_waves):
        generic.append((0.35 * sys_v, t0 + (0.30 + 0.22 * k) * T, 0.09, 1.0))
    out = [np.array([v for c in generic for v in c], float)]

    if np.isfinite(lm["dia_t"]):
        lmk = [(sys_v, sys_t, 0.06, 2.0)]
        dia_v = lm["dia_v"] if np.isfinite(lm["dia_v"]) else 0.35 * sys_v
        lmk.append((max(dia_v, 0.05), lm["dia_t"], 0.09, 1.0))
        for k in range(2, n_waves):
            lmk.append((0.15 * sys_v, min(lm["dia_t"] + 0.18 * k, t0 + 0.9 * T), 0.10, 1.0))
        out.append(np.array([v for c in lmk for v in c], float))

    for frac in (0.34, 0.46, 0.58):
        g = [(sys_v, sys_t, 0.06, 2.0)]
        for k in range(1, n_waves):
            g.append((0.35 * sys_v, t0 + min(frac + 0.20 * (k - 1), 0.88) * T, 0.09, 1.0))
        out.append(np.array([v for c in g for v in c], float))
    return out


def _augment_start(x, n: int, has_tail: bool, step: int = 4):
    """n 成分の解に、最も間隔の広いところへ小さい成分を1つ挟んだ初期値を作る。

    増やす前の解は既に良い場所にいるので、そこから温め直した1点を汎用初期値に
    **足す**。汎用初期値の代わりにはしない（1点に絞ったら良い最適解を取り逃し、
    当てはまりが半分に落ちて採択率が 0% になった）。
    """
    tail = list(np.asarray(x, float)[step * n:]) if has_tail else []
    ks = [list(np.asarray(x, float)[step * k:step * (k + 1)]) for k in range(n)]
    ks.sort(key=lambda c: c[1])
    i = 0
    if len(ks) > 1:
        i = int(np.argmax([ks[j + 1][1] - ks[j][1] for j in range(len(ks) - 1)]))
    hmax = max(c[0] for c in ks)
    new = [0.25 * hmax, 0.5 * (ks[i][1] + ks[i + 1][1]) if len(ks) > 1 else ks[0][1] + 0.1,
           float(np.mean([c[2] for c in ks])), float(np.mean([c[3] for c in ks]))]
    ks.insert(i + 1, new)
    return np.array([v for c in ks for v in c] + tail, float)


ALPHA_MIN = 0.0    # 歪み母数の下限。0 は「右歪みのみ許す」
# Basso 2024 は α に境界を置かない（「α の範囲について事前知識がないから」）。
# しかし**前進波については事前知識がある**。伝播する脈波は立ち上がりが速く減衰が遅い、
# すなわち右歪みである。左歪み（速く減衰し遅く立ち上がる）は進行波として非生理的である。
# α を見直すきっかけになった共分散の破綻（α が下限 0 に潰れてモデルが無感応になる）は、
# 境界近傍の母数を固定する処理で独立に解決済みなので、下限を外す必要はない。
# ただし文献と割れる選択なので、27番の感度解析で −8 に緩めた場合を検定する。
# 参考（合成波・真値は α=2.5 と 1.2 の右歪みなので優劣は決められない）:
#   α≥0: ΔT誤差 +5.9 / 心拍交絡 13.4 ms      α≥−8: ΔT誤差 +8.4 / 心拍交絡 15.7 ms


def _wave_bounds(t, n_waves: int, min_gap: float = 0.03, alpha_min: float = ALPHA_MIN):
    T = float(t[-1] - t[0])
    t0 = float(t[0])
    lo, hi = [], []
    for k in range(n_waves):
        lo += [0.02 if k else 0.30, t0 + 0.01, 0.012, alpha_min]
        hi += [1.60, t0 + (0.55 if k == 0 else 0.95) * T, 0.28, 8.0]
    return np.array(lo, float), np.array(hi, float), min_gap


def _order_penalty(p, n_waves: int, min_gap: float):
    """ピーク時刻の単調性と、前進波が最大であることを罰則で課す（Couceiro 2015 の制約）。

    least_squares は不等式制約を直接扱えないので、残差に罰則項を足す。
    """
    tp = [p[4 * k + 1] for k in range(n_waves)]
    h = [p[4 * k] for k in range(n_waves)]
    pen = []
    for k in range(1, n_waves):
        pen.append(50.0 * max(0.0, min_gap - (tp[k] - tp[k - 1])))   # tp は単調増加
        pen.append(50.0 * max(0.0, h[k] - h[0]))                     # 前進波が最大
    return np.array(pen)


def fit_waves(t, y, lm, n_waves: int = 2, w=None, min_gap: float = 0.03, res=None,
              starts=None, n_generic=None, alpha_min: float = ALPHA_MIN):
    """歪みガウス n 本を当てはめる。res を渡すと貯留槽項を同時に当てはめる。

    貯留槽は**時定数を固定し振幅だけ自由**にする。時定数は進行波の無い区間で
    決めてあるので、この項が反射波の位置を動かすことはない。振幅を同時に決めるのは、
    先に差し引くと過剰に引いて残差が負に振れるためである。
    """
    lo, hi, gap = _wave_bounds(t, n_waves, min_gap, alpha_min)
    w = np.ones_like(t) if w is None else w
    sw = np.sqrt(w)
    rshape = None
    if res is not None:
        rshape = reservoir_shape(t, res["t_a"], res["tau"])
        lo = np.append(lo, 0.0)
        hi = np.append(hi, 1.2)

    def model(p):
        out = np.zeros_like(t)
        for k in range(n_waves):
            out = out + skew_peak(t, p[4 * k], p[4 * k + 1], p[4 * k + 2], p[4 * k + 3])
        if rshape is not None:
            out = out + p[4 * n_waves] * rshape
        return out

    def resid(p):
        return np.concatenate([(model(p) - y) * sw, _order_penalty(p, n_waves, gap)])

    gen = _wave_starts(t, y, lm, n_waves)
    if n_generic is not None:
        gen = gen[:max(n_generic, 0)]
    starts = (list(starts) if starts is not None else []) + gen
    if rshape is not None:
        d0 = float(res.get("d_hint", 0.3))
        starts = [x if len(x) == 4 * n_waves + 1 else np.append(x, np.clip(d0, 0.0, 1.2))
                  for x in starts]
    sols = _multistart(resid, starts, lo, hi)
    if not sols:
        return None
    return {"sols": sols, "model": model, "n": n_waves, "kind": "skew",
            "reservoir_shape": rshape, "lo": lo, "hi": hi}


def fit_gamma(t, y, lm, n_kernels: int = 3, w=None, min_gap: float = 0.03,
              starts=None, n_generic=None):
    """ガンマ n 本を同時に当てはめる（最も遅い成分が貯留槽の役をする）。

    母数は成分ごとに (高さ, ピーク時刻, 立ち上がり時間, 形状) の 4 つ。歪みガウス側と
    同じ並びなので、標準誤差の伝播も採否の検算も共通のコードで扱える。
    """
    T = float(t[-1] - t[0])
    t0 = float(t[0])
    lo, hi = [], []
    for k in range(n_kernels):
        lo += [0.02 if k else 0.30, t0 + 0.02, 0.015, 1.05]
        hi += [1.60, t0 + (0.55 if k == 0 else 0.95) * T, 0.35, 40.0]
    lo, hi = np.array(lo, float), np.array(hi, float)
    w = np.ones_like(t) if w is None else w
    sw = np.sqrt(w)

    def model(p):
        out = np.zeros_like(t)
        for k in range(n_kernels):
            out = out + gamma_peak(t, p[4 * k], p[4 * k + 1], p[4 * k + 2], p[4 * k + 3])
        return out

    def resid(p):
        return np.concatenate([(model(p) - y) * sw,
                               _order_penalty(p, n_kernels, min_gap)])

    gen4 = _wave_starts(t, y, lm, n_kernels)
    if n_generic is not None:
        gen4 = gen4[:max(n_generic, 0)]
    xs = [np.clip(np.asarray(x, float), lo, hi) for x in (starts or [])]
    for s4 in gen4:
        g = []
        for k in range(n_kernels):
            g += [s4[4 * k], s4[4 * k + 1],
                  min(max(1.6 * s4[4 * k + 2], 0.02), 0.30), 4.0 + 2.0 * k]
        xs.append(np.clip(np.array(g, float), lo, hi))
    sols = _multistart(resid, xs, lo, hi)
    if not sols:
        return None
    return {"sols": sols, "model": model, "n": n_kernels, "kind": "gamma",
            "lo": lo, "hi": hi}


# ============================================================ 採否の検算
def acceptance(t, y, yhat, lm, w=None, nrmse_max: float = NRMSE_MAX,
               errx_ms: float = ERRX_MS, erry_max: float = ERRY) -> dict:
    """Wang 2013 の規準で当てはめの採否を決める。

    **当てはまりの良さではなく、鍵点が正しい位置に来たかを見る。**
    凍結版の検算（境界張り付き・振幅ゼロ・再現性）は最適化が収束したかを見るだけで、
    成分が意図した特徴の上に載ったかを見ていなかった。
    """
    w = np.ones_like(t) if w is None else w
    denom = np.sum(w * y * y)
    nrmse = float(np.sqrt(np.sum(w * (y - yhat) ** 2) / max(denom, 1e-12)))

    lm_hat = find_landmarks(t, yhat)
    errx = 0.0
    erry = 0.0
    n_match = 0
    for kt, kv in (("sys_t", "sys_v"), ("notch_t", None), ("dia_t", "dia_v")):
        a, b = lm[kt], lm_hat[kt]
        if np.isfinite(a) and np.isfinite(b):
            errx += abs(a - b) * 1000.0
            n_match += 1
            if kv:
                va, vb = lm[kv], lm_hat[kv]
                if np.isfinite(va) and np.isfinite(vb):
                    erry += abs(va - vb)
        elif np.isfinite(a) and not np.isfinite(b):
            # 模型側で鍵点が消えたら不合格に倒す。閾値を緩めて走らせる感度解析では
            # 罰則も一緒に緩むが、それは Errx 規準を切ったという意味なので整合する。
            errx += (errx_ms if np.isfinite(errx_ms) else ERRX_MS) * 2.0
    return {"nrmse": nrmse, "errx_ms": float(errx), "erry": float(erry),
            "n_landmark_matched": n_match, "klass": lm["klass"],
            "ok": bool(nrmse <= nrmse_max and errx <= errx_ms and erry <= erry_max
                       and n_match >= 2)}


# ============================================================ 役割と指標
def assign_roles(peaks: list, lm: dict, has_reservoir_kernel: bool, t=None) -> dict:
    """成分に前進波・反射波・貯留槽の役を割り当てる。

    **当てはめに決めさせない。** 規則を先に決め、制約で順序を固定したうえで、
    ランドマークに最も近い成分を反射波とする。決められなければその旨を返す。

    貯留槽カーネルの見分け方
    ------------------------
    以前は「最も遅くピークをとる成分」を無条件に貯留槽としていた。ガンマに位置母数を
    入れてからはこれが成り立たない。裾で拡張期の下降を担う成分が、拡張期ピークより
    手前でピークをとりうるからである（実際、ガンマ真値の波形で真の反射波が貯留槽と
    誤認され、手前の小さい成分が反射波にされていた）。
    そこで**拡張期ピークより十分後ろ、かつ拍の後半でピークをとる成分だけ**を貯留槽の
    候補とし、該当が無ければ貯留槽カーネルは無いものとして扱う。
    """
    order = sorted(range(len(peaks)), key=lambda i: peaks[i][0])
    fwd = order[0]
    cand = order[1:]
    res = None
    if has_reservoir_kernel and len(cand) >= 2:
        lim = -np.inf
        if np.isfinite(lm.get("dia_t", np.nan)):
            lim = max(lim, lm["dia_t"] + 0.08)
        if t is not None and len(t) > 1:
            lim = max(lim, float(t[0]) + 0.60 * float(t[-1] - t[0]))
        if peaks[cand[-1]][0] > lim:
            res = cand[-1]
            cand = cand[:-1]
    if not cand:
        return {"forward": fwd, "reflected": None, "reservoir": res, "rule": "none"}
    if np.isfinite(lm["dia_t"]) and len(cand) > 1:
        ref = min(cand, key=lambda i: abs(peaks[i][0] - lm["dia_t"]))
        rule = "landmark"
    else:
        ref = cand[0]
        rule = "order"
    return {"forward": fwd, "reflected": ref, "reservoir": res, "rule": rule}


def _peaks_and_se(sol, n, kind, t, lo=None, hi=None):
    """成分のピーク（時刻・高さ）と、母数の共分散行列を返す。

    ピーク母数化してあるので、ΔT と RI は母数の差と比になり、
    誤差伝播がそのまま書ける。
    """
    p = sol.x
    step = 4          # 歪みガウス・ガンマとも (高さ, ピーク時刻, 幅, 形) の 4 母数
    peaks = [(float(p[step * k + 1]), float(p[step * k])) for k in range(n)]
    sds = [component_sd(kind, p[step * k + 2], p[step * k + 3]) for k in range(n)]
    cov = None
    try:
        J = np.asarray(sol.jac, float)
        m, q = J.shape
        # 境界に張り付いた母数は動けない。線形化した共分散は境界を知らないので、
        # そのままだと平坦な方向の曲率を分散に化けさせる。まず least_squares の
        # active_mask で自由な母数だけを残す。
        try:
            free = np.asarray(sol.active_mask, int) == 0
        except Exception:
            free = np.ones(q, bool)
        # scipy の active_mask は「厳密に境界上」しか印を付けない。実際には境界の
        # ごく近くまで潰れた母数（たとえば反射波の歪み α が 3e-4）でモデルが
        # ほぼ無感応になり、規格化ヤコビアンの最小特異値が 3e-7 まで落ちる。
        # この平坦方向を逆行列に含めると分散が 10^14 桁に化け、共分散を通じて
        # ΔT の標準誤差まで壊す。境界に十分近い母数は固定として扱う。
        if lo is not None and hi is not None:
            lo_a, hi_a = np.asarray(lo, float), np.asarray(hi, float)
            if lo_a.size == q and hi_a.size == q:
                rng = np.maximum(hi_a - lo_a, 1e-12)
                pinned = ((np.abs(p - lo_a) <= 1e-3 * rng)
                          | (np.abs(hi_a - p) <= 1e-3 * rng))
                free = free & ~pinned
        Jf = J[:, free]
        dof = max(m - int(free.sum()), 1)
        s2 = 2.0 * sol.cost / dof
        # 列の尺度が桁違いなので規格化してから、**J そのものの**特異値分解で逆行列を作る
        # （JᵀJ を作ると条件数が二乗される）。
        sc = np.sqrt((Jf * Jf).sum(axis=0))
        sc[~np.isfinite(sc) | (sc <= 0)] = 1.0
        Jn = Jf / sc
        if not np.isfinite(Jn).all():
            raise ValueError("jacobian not finite")
        with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
            _u, sv, Vt = np.linalg.svd(Jn, full_matrices=False)
            if sv[-1] <= sv[0] * 1e-6:      # 規格化しても特異 → 本当に同定できていない
                raise ValueError("rank deficient")
            cf = s2 * ((Vt.T / sv ** 2) @ Vt) / np.outer(sc, sc)
        cov = np.zeros((q, q), float)
        ix = np.flatnonzero(free)
        cov[np.ix_(ix, ix)] = cf
        if not np.isfinite(cov).all():
            cov = None
    except Exception:
        cov = None
    return peaks, cov, step, sds


def indices(peaks, cov, step, roles, sds=None) -> dict:
    """ΔT と RI を、標準誤差つきで返す。"""
    f, r = roles["forward"], roles["reflected"]
    if r is None:
        return {"dt_ms": np.nan, "ri": np.nan, "dt_se_ms": np.nan, "ri_se": np.nan,
                "dps_ms": np.nan}
    tf, hf = peaks[f]
    tr, hr = peaks[r]
    dt = (tr - tf) * 1000.0
    ri = hr / max(hf, 1e-9)
    dt_se = ri_se = np.nan
    if cov is not None:
        it_f, it_r = step * f + 1, step * r + 1
        ih_f, ih_r = step * f, step * r
        try:
            v = cov[it_r, it_r] + cov[it_f, it_f] - 2 * cov[it_r, it_f]
            dt_se = float(np.sqrt(max(v, 0.0)) * 1000.0)
            # デルタ法: RI = hr/hf
            g = np.array([1.0 / hf, -hr / (hf * hf)])
            c = np.array([[cov[ih_r, ih_r], cov[ih_r, ih_f]],
                          [cov[ih_f, ih_r], cov[ih_f, ih_f]]])
            ri_se = float(np.sqrt(max(g @ c @ g, 0.0)))
        except Exception:
            pass
    # Goswami 2010 の差分パルス幅。反射波が前進波よりどれだけ広がったか
    dps = (sds[r] - sds[f]) * 1000.0 if sds is not None else np.nan
    return {"dt_ms": float(dt), "ri": float(ri), "dt_se_ms": dt_se, "ri_se": ri_se,
            "dps_ms": float(dps) if np.isfinite(dps) else np.nan}


def _ambiguous(sols, step, roles, tol_cost: float = 1.15, tol_dt: float = 0.20) -> bool:
    """ΔT の異なる競合解が残差で拮抗していないか。"""
    if len(sols) < 2:
        return False
    best = sols[0]
    f, r = roles["forward"], roles["reflected"]
    if r is None:
        return True
    dt0 = best.x[step * r + 1] - best.x[step * f + 1]
    for s in sols[1:]:
        if s.cost <= best.cost * tol_cost:
            dt1 = s.x[step * r + 1] - s.x[step * f + 1]
            if dt0 > 0 and abs(dt1 - dt0) > tol_dt * dt0:
                return True
    return False


# ============================================================ 入口
def decompose(t, y, fs: float, route: str = "two_stage",
              n_waves: int = None, escalate: bool = True,
              w_key: float = W_KEY, preprocessed: bool = False,
              lowpass_hz: float = LOWPASS_HZ, min_gap: float = 0.03,
              resample_hz: float = 0.0, fit_frac: float = 1.0,
              alpha_min: float = ALPHA_MIN,
              nrmse_max: float = NRMSE_MAX, errx_ms: float = ERRX_MS,
              erry_max: float = ERRY, se_dt_max_ms: float = SE_DT_MAX_MS) -> dict:
    """1拍を分解して ΔT・RI とその標準誤差、採否の判定を返す。

    route="two_stage"  貯留槽を差し引いてから歪みガウス2成分
    route="gamma3"     ガンマ3成分を同時に当てはめ、最も遅い成分を貯留槽とみなす
    escalate=True      採否（当てはまり）または同定性の規準を満たさない場合に成分を1つ増やす

    成分を増やすことの代償
    ----------------------
    合成波（真値は2成分＋貯留槽）で確かめたところ、3波に増やすと波形の当てはまりは
    良くなる（NRMSE 0.017〜0.029 → 0.007〜0.013）が、**ΔT は真値から遠ざかる**
    （+3.7 ms → +5.9 ms）。反射波が2つに割れ、後ろ側が反射波の役を取るためである。
    採否規準は当てはまりを見ているので、採用された拍のほうが ΔT の誤差が大きい、
    という一見あべこべな結果になる。増やしたかどうかは `escalated` で返すので、
    下流では**必ず層別して読むこと**。
    """
    t = np.asarray(t, float)
    if preprocessed:
        ys, amp = np.asarray(y, float), 1.0
    else:
        ys, amp = preprocess(t, y, fs, lowpass_hz=lowpass_hz)
    if ys is None:
        return {"ok": False, "reason": "amplitude"}

    # 感度解析用の2条件（既定では何もしない）
    #   resample_hz  Tigges 2017 は AICc のため 40 Hz へ、Basso 2024 は 1拍 28 標本
    #                （平均 42 Hz）へ落としている。500 Hz のまま当てはめると標本数が
    #                15 倍になり、情報の薄い拡張期の裾が二乗和を支配する
    #   fit_frac     Goswami 2010 は「関心のある母数は 0〜0.9T に収まる」として
    #                拍の終わりを当てはめていない。貯留槽項を置く代わりの方針
    if resample_hz and resample_hz > 0:
        n_new = max(int(round((t[-1] - t[0]) * resample_hz)) + 1, 16)
        t_new = np.linspace(float(t[0]), float(t[-1]), n_new)
        ys = np.interp(t_new, t, ys)
        t = t_new
    if fit_frac and fit_frac < 1.0:
        keep = t <= t[0] + fit_frac * (t[-1] - t[0])
        if keep.sum() >= 16:
            t, ys = t[keep], ys[keep]

    lm = find_landmarks(t, ys)
    w = _weights(t, lm, w_key)

    def _run(nw, starts=None, n_generic=None):
        if route == "two_stage":
            rp = estimate_reservoir_tau(t, ys, lm)
            fit = fit_waves(t, ys, lm, n_waves=nw, w=w, res=rp, min_gap=min_gap,
                            starts=starts, n_generic=n_generic, alpha_min=alpha_min)
            if fit is None:
                return None
            rp = dict(rp, d=float(fit["sols"][0].x[4 * nw]))
            return fit, fit["model"](fit["sols"][0].x), rp, True
        fit = fit_gamma(t, ys, lm, n_kernels=nw, w=w, min_gap=min_gap,
                        starts=starts, n_generic=n_generic)
        if fit is None:
            return None
        return fit, fit["model"](fit["sols"][0].x), {"ok": False}, True

    nw0 = n_waves if n_waves else (2 if route == "two_stage" else 3)
    got = _run(nw0)
    if got is None:
        return {"ok": False, "reason": "fit_failed", "klass": lm["klass"]}
    fit, yhat, rp, _ = got
    peaks, cov, step, sds = _peaks_and_se(fit["sols"][0], fit["n"], fit["kind"], t,
                                          fit.get("lo"), fit.get("hi"))
    roles = assign_roles(peaks, lm, has_reservoir_kernel=(route != "two_stage"), t=t)
    acc = acceptance(t, ys, yhat, lm, w, nrmse_max=nrmse_max,
                     errx_ms=errx_ms, erry_max=erry_max)
    amb = _ambiguous(fit["sols"], step, roles)
    n_used = nw0
    escalated = False

    # --- 採否または同定性の規準を満たさない場合に成分を増やす（収縮後期波を足す）
    if escalate and (not acc["ok"] or amb):
        warm = [_augment_start(fit["sols"][0].x, nw0, has_tail=(route == "two_stage"))]
        # 汎用初期値は削らない。1点に絞ると良い最適解を取り逃し、当てはまりが
        # 半分に落ちて採択率が 0% になった（NRMSE 0.0067 → 0.0132）。温め初期値は
        # **足すだけ**にして、速さは x_scale="jac" の分だけ取る。
        got2 = _run(nw0 + 1, starts=warm)
        if got2 is not None:
            fit2, yhat2, rp2, _ = got2
            peaks2, cov2, step2, sds2 = _peaks_and_se(
                fit2["sols"][0], fit2["n"], fit2["kind"], t,
                fit2.get("lo"), fit2.get("hi"))
            roles2 = assign_roles(peaks2, lm, has_reservoir_kernel=(route != "two_stage"), t=t)
            acc2 = acceptance(t, ys, yhat2, lm, w, nrmse_max=nrmse_max,
                          errx_ms=errx_ms, erry_max=erry_max)
            amb2 = _ambiguous(fit2["sols"], step2, roles2)
            if acc2["ok"] and not amb2:
                fit, yhat, rp = fit2, yhat2, rp2
                peaks, cov, step, sds = peaks2, cov2, step2, sds2
                roles, acc, amb = roles2, acc2, amb2
                n_used, escalated = nw0 + 1, True

    ix = indices(peaks, cov, step, roles, sds)
    se_ok = np.isfinite(ix["dt_se_ms"]) and ix["dt_se_ms"] <= se_dt_max_ms
    reason = ""
    if not acc["ok"]:
        reason = "landmark_or_fit"
    elif amb:
        reason = "ambiguous"
    elif roles["reflected"] is None:
        reason = "no_reflected"
    elif not se_ok:
        reason = "dt_se"
    return {
        "ok": bool(acc["ok"] and not amb and roles["reflected"] is not None and se_ok),
        "reason": reason,
        "route": route, "n_components": n_used + (1 if route == "two_stage" else 0),
        "n_waves": n_used, "escalated": escalated, "ambiguous": amb,
        "role_rule": roles["rule"], "klass": lm["klass"], "lm_source": lm["source"],
        "amp": amp, "reservoir": rp, "landmarks": lm, "peaks": peaks,
        **ix, **{k: acc[k] for k in ("nrmse", "errx_ms", "erry", "n_landmark_matched")},
    }

# -*- coding: utf-8 -*-
"""PDA 第2版 ― 文献の指摘を取り込んだ脈波分解。

`src/pda.py`（凍結版）の点検で見つかった問題への対処をまとめたもの。
凍結版は研究1の解析に使ったまま残し、本モジュールは並行して検証する。

対処した問題（`docs/research/pda_literature_review.md` 参照）
-----------------------------------------------------------
(1) 拡張期の減衰を第2カーネルが吸収して拍長に引きずられていた
    → **成分を1つ増やして減衰を担わせる。歪みガウスとガンマの2経路を同じ規準で比べる**
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
    route="skew"    歪みガウス2成分（不足なら3）。Basso 2024 と同じ混合模型。
                    歪みガウスは進行波に適した形（立ち上がりが速く減衰が遅い）
    route="gamma"   ガンマ3成分（不足なら4）。Tigges 2017 が実測7,805拍の AICc で選んだ
                    模型に、到達時刻の母数を足したもの。裾が exp(−βt) なので
                    最も遅い成分が拡張期の減衰をそのまま担える

貯留槽項は置かない。1拍を線形ベースライン除去した波形では減衰が末尾で強制的に 0 になり、
時定数を正しく推定できない（合成波で真値の半分以下）。膝をどこに置いても振幅が 0 に潰れるか
当てはまりが壊れるかで、機能しなかった。減衰は成分を1つ増やすことで担わせる。

18 Hz に帯域制限した1拍の独立な標本は 24〜40 点しかなく、成分あたり4母数として
5成分（20母数）は過剰母数化になる。既定は 2〜3 成分（歪みガウス）・3〜4 成分（ガンマ）。

母数の取り方
------------
振幅・位置・幅ではなく **ピーク高さ・ピーク時刻・幅・歪度**で持つ。
こうすると ΔT と RI が母数そのものの差と比になり、条件数が良くなるうえ、
**拍ごとに ΔT・RI の標準誤差が出せる**。「この拍の RI は 0.42 ± 0.15 だから使わない」
という選別ができる。凍結版の3つの収束検算より実質的な検算になる。

次数の適応
----------
既定は歪みガウス2成分・ガンマ3成分。採否の規準（NRMSE・Errx・Erry）を満たさないか、
ΔT の異なる競合解が残差で拮抗する場合に、収縮後期波を1つ足して4成分にする。
増やした拍では波形の当てはまりは良くなるが ΔT は真値から約 2 ms 遠ざかる（合成波）ので、
**増やしたかどうかを必ず返し、下流で層別する**。
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import least_squares
from scipy.signal import butter, filtfilt
from scipy.special import erf

SQRT2 = np.sqrt(2.0)


def code_version() -> str:
    """このファイル自身の内容のハッシュ（先頭 12 桁）。

    26番が被験者別 CSV に書き、27番が読むときに照合する。pda2 を変えた後に 26番を回し直さず
    27番だけ回すと、古い分解結果に新しい閾値を当てることになる。それを黙って通さないため。
    """
    import hashlib
    try:
        return hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:12]
    except Exception:
        return "unknown"

# --- 採否の規準（Wang 2013 の閾値。amplitude を1に正規化した波形に対して）
ERRX_MS = 6.0      # 鍵点の時間位置の絶対誤差の総和 [ms]
ERRY = 0.01        # 鍵点の振幅の絶対誤差の総和
NRMSE_MAX = 0.02   # 重み付き正規化二乗平均平方根誤差
W_KEY = 20.0       # 鍵点に置く重み（Wang は 1〜100 を探索。既定は中間）
LOWPASS_HZ = 18.0  # Tigges 2017・Couceiro 2015 に合わせる
FOOT_SEARCH_FRAC = 0.08   # 基線の足を探す範囲（拍の両端それぞれ 8%）
# ΔT の標準誤差の上限 [ms]。研究1で観測した症例内 ΔPWTT の標準偏差が 18 ms なので、
# それを超える誤差の拍は問いに何も寄与しない。当てはまりの規準（NRMSE・Errx・Erry）
# だけでは、成分の振幅が潰れて時刻が同定できていない解を通してしまう
# （`scripts/25_pda2_validate.py` T4 で σ=11,725 ms の解が採用されるのを確認した）。
SE_DT_MAX_MS = 20.0
# この値は3か所で使う。(1) ΔT の標準誤差の上限、(2) 競合解の ΔT の広がりの許容、
# (3) 反射波の候補が2つあるときの「僅差」の下限。いずれも「これを超える不確かさの拍は
# 研究1の症例内 ΔPWTT の標準偏差（18 ms）より大きく、問いに何も寄与しない」という同じ根拠。
# `decompose(se_dt_max_ms=…)` は 3 か所すべてに同じ値を渡す（1 か所だけ動かすと根拠と食い違う）。
# 一意性の検査で「競合解」とみなす残差の許容（最良解の何倍まで）。**根拠なく決めた**閾値の
# 一つで、27番 B 層で 1.05・1.5 を検定する。
TOL_COST = 1.15


# ============================================================ 基底関数
def _skew_tables(n: int = 1601):
    """歪みガウスの形状 f(z)=exp(−z²/2)(1+erf(αz/√2)) について、
    α ごとのピーク位置 m(α)[z単位] とピーク値 v(α) を数値表にする。

    これがあると (ピーク高さ, ピーク時刻) で母数化できる。閉じた式が無いので表引きする。
    """
    # 表は [−8, 8] で作る。既定の下限は ALPHA_MIN=0（右歪みのみ）だが、感度解析で
    # −8 まで緩めるので、表はその範囲を覆っておく。
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
    # NaN・定数・短すぎる拍を弾く。内部に NaN があると呼び出し側が詰めて波形を
    # つなぎ合わせてしまうので、ここで落とす（PWDB は末尾を NaN で埋めている）
    if y.size < 8 or not np.isfinite(y).all() or float(np.ptp(y)) <= 0:
        return None, 0.0
    if lowpass_hz and fs > 2.5 * lowpass_hz:
        b, a = butter(4, lowpass_hz / (fs / 2.0), btype="low")
        padlen = 3 * max(len(a), len(b))
        if y.size > padlen:                       # filtfilt は padlen より長い列を要求する
            y = filtfilt(b, a, y)
    if detrend and len(y) > 3:
        # 足（この拍の立ち上がり点）から次の足への直線を引く。
        # 両端の標本をそのまま使うと、切り出し位置が数 ms ずれただけで基線が傾き、
        # RI が 10% 動く（合成波で ±4 ms のずれに対し 0.517〜0.573）。ΔT は時刻の差なので
        # 影響を受けないが、RI は振幅の比なので基線に敏感である。
        # Basso 2024 と同様に、両端それぞれ拍の 8% の範囲で最小値を探して足とする。
        n = len(y)
        k = max(2, int(round(FOOT_SEARCH_FRAC * n)))
        i0 = int(np.argmin(y[:k]))
        i1 = n - k + int(np.argmin(y[n - k:]))
        if i1 > i0:
            slope = (y[i1] - y[i0]) / (i1 - i0)
            base = y[i0] + slope * (np.arange(n) - i0)
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


# 切痕・拡張期ピークを探す窓（拍の先頭からの割合）。駆出時間は心拍 50〜120 で
# 0.30〜0.55T なので、切痕が 0.65T より後ろに来ることは生理的にない。
# 鍵点を探す窓。駆出時間は心拍 50〜120 で 0.30〜0.55T なので、切痕が 0.65T より後に
# 来ることは生理的にない。拡張期ピークは切痕から 0.25T 以内
NOTCH_MAX_FRAC = 0.65
DIA_MAX_FRAC = 0.85
NOTCH_MIN_FRAC = 0.05      # 収縮期ピークからこれだけ離す（ピーク自身の曲率を拾わない）
# 以下2つは数値的な守り（微小な揺らぎを特徴と誤認しない）であって科学的な閾値ではない。
# 18 Hz に帯域制限した後なので、この程度の揺らぎは残らない
EXTREMA_MIN_PROM = 0.01    # 極値による切痕・拡張期ピークに要求する最小の高低差（振幅 1 の波形）
PROXY_MIN_PROM = 0.05      # 肩（1次微分の局所極大）に要求する顕著さ（最大傾斜に対する割合）


def _local_extrema(v: np.ndarray, lo: int, hi: int):
    """v[lo:hi] の局所極小・局所極大の添字（元配列の添字で返す）。"""
    seg = v[lo:hi]
    d = np.diff(seg)
    mins = np.flatnonzero((d[:-1] <= 0) & (d[1:] > 0)) + 1 + lo
    maxs = np.flatnonzero((d[:-1] > 0) & (d[1:] <= 0)) + 1 + lo
    return mins, maxs


def find_landmarks(t: np.ndarray, y: np.ndarray, force_proxy: bool = False,
                   allow_proxy: bool = True) -> dict:
    """収縮期ピーク・重複切痕・拡張期ピークを探し、波形型を判定する。

    手順
    ----
    1. 波形そのものの極小（切痕）→ 極大（拡張期ピーク）。Wang 2013 の鍵点そのもの。
       窓は切痕 ≤ 0.65T、拡張期ピーク ≤ 0.85T に限る（生理的上限）
    2. 極値が無い波形（Dawber II〜III）では **1次微分の局所極値**で代用する。
       収縮期ピークの後、下降が最も速い点（d1 の局所極小）を切痕の代用、
       その後で下降が最も緩む点（d1 の局所極大＝肩）を拡張期ピークの代用とする。
       どちらも「傾きの変化」という同じ量の極値なので、定義が単純で安定する。
       肩の顕著さは**両側**で測る（直前の d1 極小からの立ち上がりと、その後 d1 が再び
       どれだけ下がるかの小さい方）。片側だけだと、反射波が無く単調に減衰して平坦になる
       波形で、平坦部の微小な揺らぎが「肩」に化ける（直前の極小が最速下降点なので
       顕著さが最大傾斜そのものになる）。6巡目の検査で反射波なしの合成波が型3になった
       以前は2次微分の最大を切痕の代用にしていたが、切痕の無い波形では
       **収縮期ピーク自身の曲率**が最大になり、ピーク直後の無意味な点を拾っていた
       （型3〜4で ΔT 誤差 38〜55 ms の一因）。
    3. 以前あった「立ち上がり側で2次微分の谷を探して型4とする」手順は削除した。
       立ち上がり側の d2 の谷は b 波（最大減速点）であって肩ではなく、
       dia_t < sys_t という無意味な鍵点を作っていた。

    force_proxy=True は、データ側が代用点（型3）だったときに**模型側も同じ方法で**
    鍵点を取るための指定。allow_proxy=False は逆に、データ側が極値（型1）だったときに
    模型側にも極値を要求する指定（極値が無ければ鍵点なし＝不合格に倒す）。
    どちらも、定義の違う鍵点同士で Errx を取らないためにある。

    返り値の klass:
        1 明瞭な重複切痕と拡張期ピークがある（極値）
        3 極値は無いが、下降の緩む肩がある（1次微分の局所極値で代用）
        4 窓の中に肩が見つからない（Dawber IV に相当）
        5 収縮期ピークが拍の末尾にある（波形が不正）
    prom は鍵点の顕著さ。型1 では拡張期ピーク−切痕の高低差（閾値 EXTREMA_MIN_PROM）、
    型3〜4 では肩の顕著さ（最大傾斜に対する比。閾値 PROXY_MIN_PROM。型4 は閾値未満だった
    最大の値）。閾値の近傍にどれだけの拍があるかを 26番が表にして、型の割り当てが
    閾値に敏感でないかを監視する。
    """
    n = len(t)
    T = float(t[-1] - t[0])
    t0 = float(t[0])
    i_sys = int(np.argmax(y))
    sys_t, sys_v = _refine(t, y, i_sys)
    out = {"sys_t": sys_t, "sys_v": sys_v, "i_sys": i_sys,
           "notch_t": np.nan, "notch_v": np.nan, "dia_t": np.nan, "dia_v": np.nan,
           "klass": 5, "source": "none", "prom": np.nan}
    if i_sys >= n - 5:
        return out
    i_lo = max(i_sys + 2, int(np.searchsorted(t, sys_t + NOTCH_MIN_FRAC * T)))
    i_notch_hi = min(n - 2, int(np.searchsorted(t, t0 + NOTCH_MAX_FRAC * T)))
    i_dia_hi = min(n - 2, int(np.searchsorted(t, t0 + DIA_MAX_FRAC * T)))
    if i_lo >= i_notch_hi - 2:
        out["klass"] = 4
        return out

    # --- 1. 波形そのものの極小 → 極大
    if not force_proxy:
        mins, _ = _local_extrema(y, i_lo, i_notch_hi + 1)
        if mins.size:
            j_min = int(mins[0])
            _, maxs = _local_extrema(y, j_min, i_dia_hi + 1)
            # 拡張期ピークは切痕より EXTREMA_MIN_PROM 以上高いこと（振幅 1 の波形で 1%）。
            # 微小な揺らぎを「明瞭な切痕」と誤認して、その位置で Errx を取らないため
            if maxs.size and float(y[int(maxs[0])] - y[j_min]) >= EXTREMA_MIN_PROM:
                j_max = int(maxs[0])
                nt, nv = _refine(t, y, j_min)
                dt_, dv = _refine(t, y, j_max)
                out.update(notch_t=nt, notch_v=nv, dia_t=dt_, dia_v=dv,
                           klass=1, source="extrema", prom=float(y[j_max] - y[j_min]))
                return out

    # --- 2. 1次微分の局所極値で代用（切痕の無い波形）
    if not allow_proxy:
        out["klass"] = 4
        return out
    d1 = np.gradient(y)
    mins1, maxs1 = _local_extrema(d1, i_sys + 1, i_dia_hi + 1)
    maxs1 = maxs1[(maxs1 >= i_lo) & (maxs1 <= i_dia_hi)]
    best = None
    best_any = 0.0                          # 閾値に関係なく最大の顕著さ（型4 の監視用）
    scale = float(np.max(np.abs(d1[i_sys:i_dia_hi + 1]))) or 1.0
    for j in maxs1:
        prev = mins1[mins1 < j]
        if not prev.size:
            continue
        k = int(prev[-1])
        # 両側の顕著さ: 直前の極小からの立ち上がり と 以後の再下降 の小さい方。
        # 以後の再下降は拍の末尾まで見る（肩の後に下降が再開しなければ肩ではなく減衰の終わり）
        prom = float(min(d1[j] - d1[k], d1[j] - float(np.min(d1[j:]))))
        best_any = max(best_any, prom / scale)
        if prom >= PROXY_MIN_PROM * scale and (best is None or prom > best[0]):
            best = (prom, k, int(j))
    if best is not None:
        _, k, j = best
        nt, _ = _refine(t, -d1, k)          # 最速下降点
        dt_, _ = _refine(t, d1, j)          # 肩
        nv = float(np.interp(nt, t, y))
        dv = float(np.interp(dt_, t, y))
        out.update(notch_t=float(nt), notch_v=nv, dia_t=float(dt_), dia_v=dv,
                   klass=3, source="d1", prom=float(best[0] / scale))
        return out
    out["klass"] = 4
    out["prom"] = float(best_any)
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


def _weights(t: np.ndarray, lm: dict, w_key: float = W_KEY, halfwidth_s: float = 0.006):
    """鍵点とその近傍（±6 ms）に重みを置く（Wang 2013 の WLS）。

    近傍の幅は**時間**で指定する。標本数で指定すると、40 Hz へ落とす感度条件で
    ±3 標本が ±75 ms に膨らみ、比較にならない。
    """
    w = np.ones_like(t)
    dt = float(np.median(np.diff(t))) if len(t) > 1 else 1.0
    halfwidth = max(1, int(round(halfwidth_s / max(dt, 1e-9))))
    for i in _key_indices(t, lm):
        a, b = max(0, i - halfwidth), min(len(t), i + halfwidth + 1)
        w[a:b] = w_key
    return w


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
    sc = T / T_REF                         # 幅は拍長で尺度化する（Basso 2024）
    wf, wr = 0.06 * sc, 0.09 * sc
    sys_t, sys_v = lm["sys_t"], lm["sys_v"]
    generic = [(sys_v, sys_t, wf, 2.0)]
    for k in range(1, n_waves):
        generic.append((0.35 * sys_v, t0 + (0.30 + 0.22 * k) * T, wr, 1.0))
    out = [np.array([v for c in generic for v in c], float)]

    if np.isfinite(lm["dia_t"]):
        lmk = [(sys_v, sys_t, wf, 2.0)]
        dia_v = lm["dia_v"] if np.isfinite(lm["dia_v"]) else 0.35 * sys_v
        lmk.append((max(dia_v, 0.05), lm["dia_t"], wr, 1.0))
        for k in range(2, n_waves):
            lmk.append((0.15 * sys_v, min(lm["dia_t"] + 0.18 * k * sc, t0 + 0.9 * T),
                        0.10 * sc, 1.0))
        out.append(np.array([v for c in lmk for v in c], float))

    for frac in (0.34, 0.46, 0.58):
        g = [(sys_v, sys_t, wf, 2.0)]
        for k in range(1, n_waves):
            g.append((0.35 * sys_v, t0 + min(frac + 0.20 * (k - 1), 0.88) * T, wr, 1.0))
        out.append(np.array([v for c in g for v in c], float))
    return out


def _augment_start(x, n: int, step: int = 4):
    """n 成分の解に、最も間隔の広いところへ小さい成分を1つ挟んだ初期値を作る。

    増やす前の解は既に良い場所にいるので、そこから温め直した1点を汎用初期値に
    **足す**。汎用初期値の代わりにはしない（1点に絞ったら良い最適解を取り逃し、
    当てはまりが半分に落ちて採択率が 0% になった）。
    """
    ks = [list(np.asarray(x, float)[step * k:step * (k + 1)]) for k in range(n)]
    ks.sort(key=lambda c: c[1])
    i = 0
    if len(ks) > 1:
        i = int(np.argmax([ks[j + 1][1] - ks[j][1] for j in range(len(ks) - 1)]))
    hmax = max(c[0] for c in ks)
    new = [0.25 * hmax, 0.5 * (ks[i][1] + ks[i + 1][1]) if len(ks) > 1 else ks[0][1] + 0.1,
           float(np.mean([c[2] for c in ks])), float(np.mean([c[3] for c in ks]))]
    ks.insert(i + 1, new)
    return np.array([v for c in ks for v in c], float)


ALPHA_MIN = 0.0    # 歪み母数の下限。0 は「右歪みのみ許す」
# Basso 2024 は α に境界を置かない（「α の範囲について事前知識がないから」）。
# しかし**前進波については事前知識がある**。伝播する脈波は立ち上がりが速く減衰が遅い、
# すなわち右歪みである。左歪み（速く減衰し遅く立ち上がる）は進行波として非生理的である。
# α を見直すきっかけになった共分散の破綻（α が下限 0 に潰れてモデルが無感応になる）は、
# 境界近傍の母数を固定する処理で独立に解決済みなので、下限を外す必要はない。
# ただし文献と割れる選択なので、27番の感度解析で −8 に緩めた場合を検定する。
# 参考（合成波・真値は α=2.5 と 1.2 の右歪みなので優劣は決められない）:
#   α≥0: ΔT誤差 +5.9 / 心拍交絡 13.4 ms      α≥−8: ΔT誤差 +8.4 / 心拍交絡 15.7 ms


T_REF = 60.0 / 70.0    # 幅の尺度の基準拍長（心拍 70）。ここでは従来値と一致する


def _wave_bounds(t, n_waves: int, min_gap: float = 0.03, alpha_min: float = ALPHA_MIN):
    T = float(t[-1] - t[0])
    t0 = float(t[0])
    sc = T / T_REF
    lo, hi = [], []
    for k in range(n_waves):
        lo += [0.02 if k else 0.30, t0 + 0.01, 0.012 * sc, alpha_min]
        hi += [1.60, t0 + (0.55 if k == 0 else 0.95) * T, 0.28 * sc, 8.0]
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


def fit_waves(t, y, lm, n_waves: int = 2, w=None, min_gap: float = 0.03,
              starts=None, n_generic=None, alpha_min: float = ALPHA_MIN):
    """歪みガウス n 本を当てはめる（Basso 2024 と同じ混合模型）。

    貯留槽項について
    ----------------
    以前は Windkessel の減衰を表す貯留槽項を同時に当てはめていたが、削除した。
    理由は2つ。(1) 1拍を線形ベースライン除去した波形では減衰が末尾で強制的に 0 になり、
    時定数が真値の半分以下に過小推定される（合成波で 0.151 対 0.35）。膝をどこに置いても
    振幅が 0 に潰れるか当てはまりが壊れるかのどちらかで、機能しなかった。
    (2) 減衰は成分を1つ増やせば担える（合成波で 90% の拍がそうなっていた）。
    Basso 2024・Tigges 2017・Goswami 2010 のいずれも貯留槽項を持たない。
    """
    lo, hi, gap = _wave_bounds(t, n_waves, min_gap, alpha_min)
    w = np.ones_like(t) if w is None else w
    sw = np.sqrt(w)

    def model(p):
        out = np.zeros_like(t)
        for k in range(n_waves):
            out = out + skew_peak(t, p[4 * k], p[4 * k + 1], p[4 * k + 2], p[4 * k + 3])
        return out

    def resid(p):
        return np.concatenate([(model(p) - y) * sw, _order_penalty(p, n_waves, gap)])

    gen = _wave_starts(t, y, lm, n_waves)
    if n_generic is not None:
        gen = gen[:max(n_generic, 0)]
    starts = (list(starts) if starts is not None else []) + gen
    sols = _multistart(resid, starts, lo, hi)
    if not sols:
        return None
    return {"sols": sols, "model": model, "n": n_waves, "kind": "skew", "lo": lo, "hi": hi}


def fit_gamma(t, y, lm, n_kernels: int = 3, w=None, min_gap: float = 0.03,
              starts=None, n_generic=None):
    """ガンマ n 本を同時に当てはめる（最も遅い成分が貯留槽の役をする）。

    母数は成分ごとに (高さ, ピーク時刻, 立ち上がり時間, 形状) の 4 つ。歪みガウス側と
    同じ並びなので、標準誤差の伝播も採否の検算も共通のコードで扱える。
    """
    T = float(t[-1] - t[0])
    t0 = float(t[0])
    sc = T / T_REF
    lo, hi = [], []
    for k in range(n_kernels):
        lo += [0.02 if k else 0.30, t0 + 0.02, 0.015 * sc, 1.05]
        hi += [1.60, t0 + (0.55 if k == 0 else 0.95) * T, 0.35 * sc, 40.0]
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

    # データ側と同じ種類の鍵点を模型側に要求する（定義の違う鍵点を比べない）。
    # データが極値なら模型も極値（無ければ鍵点なし→不合格）、データが代用点なら模型も代用点
    src = lm.get("source")
    lm_hat = find_landmarks(t, yhat, force_proxy=(src == "d1"), allow_proxy=(src != "extrema"))
    errx = 0.0
    erry = 0.0
    n_match = 0
    for kt, kv in (("sys_t", "sys_v"), ("notch_t", "notch_v"), ("dia_t", "dia_v")):
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

    減衰を担う成分の見分け方
    ------------------------
    成分が3つ以上あるとき、最も遅い成分が拡張期の減衰を担っている（進行波ではない）
    ことがある。以前は「最も遅くピークをとる成分」を無条件にそう扱っていたが、
    ガンマに位置母数を入れてからは成り立たない（真の反射波が減衰成分と誤認された）。
    そこで**拡張期ピークより十分後ろ、かつ拍の後半でピークをとる成分だけ**を減衰成分の
    候補とし、該当が無ければ全成分を進行波として扱う。歪みガウス・ガンマ両経路に同じ規則を使う。

    迷いの記録
    ----------
    候補が2つ以上あるとき、拡張期の鍵点に最も近い成分を反射波とするが、**2番目の候補との
    差（ref_margin_ms）**を残す。僅差なら選択は実質くじ引きで、ΔT はその差だけ動く。
    `decompose` はこれが 20 ms 未満なら曖昧として落とす（ΔT の標準誤差の上限と同じ根拠）。
    ref_gap_ms は選んだ成分と拡張期の鍵点の距離で、役割の妥当性を事後に検算するために残す。
    """
    order = sorted(range(len(peaks)), key=lambda i: peaks[i][0])
    fwd = order[0]
    cand = order[1:]
    res = None
    out = {"forward": fwd, "reflected": None, "reservoir": None, "rule": "none",
           "ref_gap_ms": np.nan, "ref_margin_ms": np.nan}
    if has_reservoir_kernel and len(cand) >= 2:
        lim = -np.inf
        if np.isfinite(lm.get("dia_t", np.nan)):
            lim = max(lim, lm["dia_t"] + 0.08)
        if t is not None and len(t) > 1:
            lim = max(lim, float(t[0]) + 0.60 * float(t[-1] - t[0]))
        if peaks[cand[-1]][0] > lim:
            res = cand[-1]
            cand = cand[:-1]
    out["reservoir"] = res
    if not cand:
        return out
    dia = lm.get("dia_t", np.nan)
    if np.isfinite(dia) and len(cand) > 1:
        # 拡張期の鍵点に最も近い成分を反射波とする。**どれだけ僅差だったかを残す。**
        # 2つの候補が拡張期の鍵点からほぼ等距離なら、どちらを選ぶかは実質くじ引きであり、
        # ΔT はその差だけ動く。僅差の下限は ΔT の標準誤差の上限（20 ms）に結ぶ。
        ds = sorted((abs(peaks[i][0] - dia) * 1000.0, i) for i in cand)
        out.update(reflected=ds[0][1], rule="landmark",
                   ref_gap_ms=float(ds[0][0]), ref_margin_ms=float(ds[1][0] - ds[0][0]))
        return out
    ref = cand[0]
    out.update(reflected=ref, rule="single" if len(cand) == 1 else "order",
               ref_gap_ms=float(abs(peaks[ref][0] - dia) * 1000.0) if np.isfinite(dia) else np.nan,
               ref_margin_ms=np.inf)
    return out


PARAM_NAMES = ("h", "tp", "w", "a")     # 成分ごとの母数の並び（高さ・ピーク時刻・幅／立ち上がり・形）


def pinned_params(sol, lo, hi, kind: str = "skew") -> list:
    """境界に張り付いた母数の一覧（"k:名前:lo|hi"）。

    探索範囲（1c の定数）が解を決めていないかを監視する。歪み α の下限 0 は対称ガウスという
    正当な解なので数えない。26番が採用分の割合と内訳を表 1 に出す。
    """
    p = np.asarray(sol.x, float)
    lo_a, hi_a = np.asarray(lo, float), np.asarray(hi, float)
    out = []
    if lo_a.size != p.size or hi_a.size != p.size:
        return out
    rng = np.maximum(hi_a - lo_a, 1e-12)
    for i in range(p.size):
        k, j = divmod(i, 4)
        name = PARAM_NAMES[j]
        if abs(p[i] - lo_a[i]) <= 1e-3 * rng[i]:
            if name == "a" and kind == "skew":
                continue                       # α=0 は正当な解
            out.append(f"{k}:{name}:lo")
        elif abs(hi_a[i] - p[i]) <= 1e-3 * rng[i]:
            out.append(f"{k}:{name}:hi")
    return out


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


def competing_spread_ms(sols, step, roles, tol_cost: float = TOL_COST) -> float:
    """残差が最良解の tol_cost 倍以内にある競合解の間で、ΔT が最良解からどれだけ離れるか [ms]。

    多点起動の解は無料で手に入る「経験的な不確かさ」である。Wald の標準誤差は線形化に
    依存し、平坦な尾根の上では桁違いに膨らむ（心拍 130 の合成波で Wald 709 ms に対し
    ブートストラップ 15 ms）。一方で条件数は良否を分けない（採用例でも 1e5 に達する）。
    競合解の広がりは、線形化にも条件数にも頼らない直接の量なので併記する。

    競合解の成分はスロット番号ではなく、**最良解の前進波・反射波にピーク時刻が最も近い成分**で
    対応づける。3成分のとき、中間成分と最後の成分のどちらが反射波の役かは解ごとに変わりうるので、
    スロット番号で比べると別の成分同士を比べてしまう。
    """
    if len(sols) < 2:
        return 0.0
    best = sols[0]
    f, r = roles["forward"], roles["reflected"]
    if r is None:
        return float("nan")
    n = len(best.x) // step
    tf0, tr0 = best.x[step * f + 1], best.x[step * r + 1]
    dt0 = (tr0 - tf0) * 1000.0
    spread = 0.0
    for s in sols[1:]:
        if s.cost > best.cost * tol_cost:
            continue
        tps = np.array([s.x[step * k + 1] for k in range(n)])
        kf = int(np.argmin(np.abs(tps - tf0)))
        kr = int(np.argmin(np.abs(tps - tr0)))
        if kf == kr:                     # 対応づけが潰れたら、その解は別の分解になっている
            return float("inf")
        dt1 = (tps[kr] - tps[kf]) * 1000.0
        spread = max(spread, abs(dt1 - dt0))
    return float(spread)


def _ambiguous(sols, step, roles, tol_cost: float = TOL_COST,
               tol_dt_ms: float = None) -> bool:
    """ΔT の異なる競合解が残差で拮抗していないか。

    競合解（残差が最良解の tol_cost 倍以内）の ΔT が最良解と tol_dt_ms 以上違えば曖昧とする。
    以前は相対 20% だったが、ΔT 200 ms なら 40 ms の差を見逃す。心拍 130 の合成波で、
    ブートストラップの ΔT が 204 ms と 175 ms の二峰に割れているのに曖昧と判定されなかった。
    差の許容は**絶対値**で、ΔT の標準誤差の上限（SE_DT_MAX_MS）と同じ 20 ms に結ぶ。
    根拠も同じ（研究1の症例内 ΔPWTT の SD 18 ms）。これで閾値が一つ減る。

    競合解の成分は最良解の前進波・反射波にピーク時刻が最も近いもので対応づける
    （`competing_spread_ms` 参照）。対応づけが潰れる解（両方が同じ成分に落ちる）は
    別の分解に収束しているので、無条件に曖昧とする。
    """
    if tol_dt_ms is None:
        tol_dt_ms = SE_DT_MAX_MS
    if roles["reflected"] is None:
        return True
    sp = competing_spread_ms(sols, step, roles, tol_cost)
    # inf は対応づけが潰れた（別の分解に収束した競合解がある）印、nan は反射波なし。
    # どちらも曖昧。以前は `np.isfinite(sp) and sp > tol` と書いていて inf を
    # 「曖昧でない」と扱っていた（説明と逆。6巡目 K5）
    if not np.isfinite(sp):
        return True
    return bool(sp > tol_dt_ms)


def ambiguity_flags(sols, step, roles, tol_cost: float = TOL_COST,
                    tol_dt_ms: float = SE_DT_MAX_MS) -> bool:
    """`decompose` が使う曖昧判定の合成。3 つのどれかで曖昧とする。

      (1) 競合解の ΔT が拮抗する（`_ambiguous`: 広がり > tol_dt_ms、対応づけが潰れた inf、反射波なし）
      (2) 前進波がスロット 0 でない（順序の罰則が守られておらず役割が信用できない）
      (3) 反射波の候補が 2 つ以上あって僅差（ref_margin_ms < tol_dt_ms。選択がくじ引き）

    27番 A 層は同じ論理を保存された材料（dtsp・marg・fwd0）から再計算する（`recompute_amb`）。
    ここを変えたらそちらも変えること。自己検証が 26番の実出力で 100% 一致を検算する。
    """
    return bool(_ambiguous(sols, step, roles, tol_cost=tol_cost, tol_dt_ms=tol_dt_ms)
                or roles["forward"] != 0
                or (np.isfinite(roles["ref_margin_ms"]) and roles["ref_margin_ms"] < tol_dt_ms))


# ============================================================ 入口
ROUTES = ("skew", "gamma")


def decompose(t, y, fs: float, route: str = "skew",
              n_waves: int = None, escalate: bool = True,
              w_key: float = W_KEY, preprocessed: bool = False,
              lowpass_hz: float = LOWPASS_HZ, min_gap: float = 0.03,
              resample_hz: float = 0.0, fit_frac: float = 1.0,
              alpha_min: float = ALPHA_MIN,
              nrmse_max: float = NRMSE_MAX, errx_ms: float = ERRX_MS,
              erry_max: float = ERRY, se_dt_max_ms: float = SE_DT_MAX_MS,
              tol_cost: float = TOL_COST, accept_proxy: bool = False) -> dict:
    """1拍を分解して ΔT・RI とその標準誤差、採否の判定を返す。

    route="skew"       歪みガウス2成分（不足なら3）。Basso 2024 と同じ混合模型
    route="gamma"      ガンマ3成分（不足なら4）。Tigges 2017 が AICc で選んだ模型に
                       到達時刻の母数を足したもの。最も遅い成分が拡張期の減衰を担う
    escalate=True      採否（当てはまり）または曖昧（競合解・役割）の規準を満たさない場合に
                       成分を1つ増やす。**ΔT の標準誤差の超過では増やさない**。SE が大きいのは
                       成分が重なって時刻が同定できないことの表れで、成分を増やしても
                       平坦な谷は平坦なままである（合成波の心拍 130 で確認）
    se_dt_max_ms       ΔT の不確かさの上限 [ms]。標準誤差・競合解の広がり・反射波の僅差の
                       3 か所に同じ値を使う（根拠が同じなので 1 か所だけ動かさない）
    tol_cost           競合解とみなす残差の許容（最良解の何倍まで）
    accept_proxy       型3（鍵点が代用点）の拍を採用に含めるか。**既定は含めない**（下記）

    型3（切痕なし・肩の代用点）を採用しない理由
    ---------------------------------------------
    合成の切痕なし波形で、Wang の規準・SE・曖昧判定をすべて通った当てはめの ΔT が真値から
    +23 ms ずれた（ガンマ経路・心拍 70。Wald SE 9 ms・競合解の広がり 15 ms で、どちらも誤差を
    過小に見積もる）。規準を外して 3 波を採用させると +50 ms ずれる。切痕の無い波形では
    反射波の位置を決める鋭い特徴が無く、肩は真のピークより約 30 ms 構造的に遅れるので、
    肩を再現する当てはめは反射波をその遅れの分だけ後ろに置く。**分解が同定できない**。
    したがって型3 の拍は理由 proxy_landmarks で採用しない。当てはめと診断量は返すので、
    27番 A 層の「型3 を含める」の行で結論が変わらないかは検定できる。

    返り値の診断量（26番が保存し、27番が採否を再計算するのに使う）
        ambiguous / dt_spread_ms / ref_margin_ms / fwd0   曖昧判定とその材料
        n_saturated / n_starts / best_saturated          多点起動のうち max_nfev に達した数と、
                                                         最良解がそうだったか（収束の監視）

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
        if ys.size < 8 or not np.isfinite(ys).all():
            ys = None
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

    if route not in ROUTES:
        raise ValueError(f"route は {ROUTES} のいずれか: {route!r}")

    def _run(nw, starts=None, n_generic=None):
        if route == "skew":
            fit = fit_waves(t, ys, lm, n_waves=nw, w=w, min_gap=min_gap,
                            starts=starts, n_generic=n_generic, alpha_min=alpha_min)
        else:
            fit = fit_gamma(t, ys, lm, n_kernels=nw, w=w, min_gap=min_gap,
                            starts=starts, n_generic=n_generic)
        if fit is None:
            return None
        return fit, fit["model"](fit["sols"][0].x)

    nw0 = n_waves if n_waves else (2 if route == "skew" else 3)
    got = _run(nw0)
    if got is None:
        return {"ok": False, "reason": "fit_failed", "klass": lm["klass"]}
    fit, yhat = got
    peaks, cov, step, sds = _peaks_and_se(fit["sols"][0], fit["n"], fit["kind"], t,
                                          fit.get("lo"), fit.get("hi"))
    # 成分が3つ以上あれば、最も遅い成分が拡張期の減衰を担っている可能性を両経路とも同じ規則で見る
    roles = assign_roles(peaks, lm, has_reservoir_kernel=True, t=t)
    acc = acceptance(t, ys, yhat, lm, w, nrmse_max=nrmse_max,
                     errx_ms=errx_ms, erry_max=erry_max)
    # 前進波は母数の第0スロットのはず（順序の罰則が守られていれば）。守られていなければ
    # 役割の割り当てそのものが信用できないので、曖昧として扱う
    def _amb_of(sols, step_, roles_):
        return ambiguity_flags(sols, step_, roles_, tol_cost=tol_cost, tol_dt_ms=se_dt_max_ms)

    amb = _amb_of(fit["sols"], step, roles)
    n_used = nw0
    escalated = False
    escalation_tried = False

    # --- 採否または同定性の規準を満たさない場合に成分を増やす（収縮後期波を足す）
    # 鍵点が 2 つ揃わない拍（型4〜5）は、成分を増やしても Errx が計算できないので増やさない。
    # 4,374 名の 1 割がこれなら、無駄な当てはめを 1 割分省ける
    can_help = acc["n_landmark_matched"] >= 2
    if escalate and can_help and (not acc["ok"] or amb):
        escalation_tried = True
        warm = [_augment_start(fit["sols"][0].x, nw0)]
        # 汎用初期値は削らない。1点に絞ると良い最適解を取り逃し、当てはまりが
        # 半分に落ちて採択率が 0% になった（NRMSE 0.0067 → 0.0132）。温め初期値は
        # **足すだけ**にして、速さは x_scale="jac" の分だけ取る。
        got2 = _run(nw0 + 1, starts=warm)
        if got2 is not None:
            fit2, yhat2 = got2
            peaks2, cov2, step2, sds2 = _peaks_and_se(
                fit2["sols"][0], fit2["n"], fit2["kind"], t,
                fit2.get("lo"), fit2.get("hi"))
            roles2 = assign_roles(peaks2, lm, has_reservoir_kernel=True, t=t)
            acc2 = acceptance(t, ys, yhat2, lm, w, nrmse_max=nrmse_max,
                          errx_ms=errx_ms, erry_max=erry_max)
            amb2 = _amb_of(fit2["sols"], step2, roles2)
            if acc2["ok"] and not amb2:
                fit, yhat = fit2, yhat2
                peaks, cov, step, sds = peaks2, cov2, step2, sds2
                roles, acc, amb = roles2, acc2, amb2
                n_used, escalated = nw0 + 1, True

    ix = indices(peaks, cov, step, roles, sds)
    ix["dt_spread_ms"] = competing_spread_ms(fit["sols"], step, roles, tol_cost)
    se_ok = np.isfinite(ix["dt_se_ms"]) and ix["dt_se_ms"] <= se_dt_max_ms
    # 収束の監視。least_squares の status 0 は max_nfev に達して止まった印。最良解がそれなら
    # ΔT は平坦な谷の途中で止まった値で、Wald の共分散も停留点のものではない。
    # 採否には使わない（新しい規準を足さない）が、26番が率を報告する
    n_sat = int(sum(1 for s_ in fit["sols"] if getattr(s_, "status", 1) == 0))
    best_sat = bool(getattr(fit["sols"][0], "status", 1) == 0)
    # 探索範囲の境界に張り付いた母数（表 1 で監視。採否には使わない）
    pinned = pinned_params(fit["sols"][0], fit.get("lo"), fit.get("hi"), fit["kind"])
    proxy_ok = bool(accept_proxy or lm["klass"] != 3)
    reason = ""
    if acc["n_landmark_matched"] < 2 and lm["klass"] >= 4:
        reason = "no_landmarks"                 # データ側に鍵点が無い（型4〜5）
    elif not proxy_ok:
        reason = "proxy_landmarks"              # 型3: 代用点しか無く分解が同定できない（上記）
    elif not acc["ok"]:
        reason = "landmark_or_fit"
    elif roles["reflected"] is None:       # _ambiguous は反射波が無いとき True を返すので先に見る
        reason = "no_reflected"
    elif amb:
        reason = "ambiguous"
    elif not se_ok:
        # dt_se: 標準誤差が上限を超えた。no_se: 共分散が計算できない（母数が境界に潰れた・
        # ヤコビアンが特異）。後者は「同定できていない」の直接の印なので分けて数える
        reason = "dt_se" if np.isfinite(ix["dt_se_ms"]) else "no_se"
    return {
        "ok": bool(acc["ok"] and not amb and roles["reflected"] is not None and se_ok and proxy_ok),
        "reason": reason,
        "route": route, "n_components": n_used, "n_waves": n_used, "escalated": escalated, "escalation_tried": escalation_tried,
        "ambiguous": amb, "fwd0": bool(roles["forward"] == 0),
        "n_saturated": n_sat, "n_starts": int(len(fit["sols"])), "best_saturated": best_sat,
        "n_pinned": int(len(pinned)), "pinned": " ".join(pinned),
        "role_rule": roles["rule"], "ref_gap_ms": roles["ref_gap_ms"],
        "ref_margin_ms": roles["ref_margin_ms"],
        "klass": lm["klass"], "lm_source": lm["source"],
        "amp": amp, "landmarks": lm, "peaks": peaks,
        **ix, **{k: acc[k] for k in ("nrmse", "errx_ms", "erry", "n_landmark_matched")},
    }

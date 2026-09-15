#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【探索・事後】論文2: 当てはめの型を変えると真の反射波の到達を追えるか（節A・合成）と、
凍結版 ΔT が下限で詰まる性質は実データにも出るか（節B・PWDB）。

**これは事後の探索であり、論文2 の事前規準による判定（26番）は動かさない。**
26番（`26_pwdb_compare.py`）で下した判定はそのまま有効で、この台本の出力はすべて
「探索的（事後）」として読む。この台本は成立・不成立の判定を出さない。

なぜ必要か
----------
48番 節4（`48_pwdb_by_waveform_type.py`）で、凍結版 PDA の第2成分のピークは特徴点法の
拡張期側の点より、型1 で +36.9 ms・型3 で +98.5 ms 遅かった（lab_log 2026-09-14 追記140）。
なぜそうなるかを合成脈波で調べたところ、**凍結版の ΔT は真の反射波の到達が約 150 ms を
下回ると下限で詰まり、真値が違っても同じ値を返す。**貯留槽の時定数 0.45 s のとき、
真の ΔT → 凍結版が返した ΔT [ms] は次のとおりであった。

    332→332・300→298・268→264・234→228・158→162・138→142・118→134・98→132・78→174・58→174

最後の 2 拍は真値が 20 ms 違うのに返り値が同じ 174 ms である。長い側（真値 230 ms 以上）の
誤差は 0〜6 ms なので、失敗は精度ではなく**短い側で順位が消えること**である。26番・48番は
年齢層内の順位相関で判定するので、この詰まりはそのまま ρ の低下になる。

同じ拍での順位相関 ρ（時定数 0.45 s ／ 0.30 s）は、凍結版 0.71／0.81、Δμ の下限を 0.01 s に
緩めると 0.89／0.95、貯留槽を前進波の畳み込みで持つと 1.00／1.00、0.65T までで当てはめると
0.95／0.99、参考の特徴点法 1.00／1.00 であった（監督者が合成脈波で実測した値。
lab_log 2026-09-15 追記141。この台本の節A はこの実測を台本の流儀で作り直したものである）。

節A（合成・既定で走る）
-----------------------
当てはめの型を 6 通り並べ、真の反射波の到達を追えるかを測る。

  合成脈波   前進波（歪みガウス）＋ 反射波（歪みガウス）＋ 貯留槽（指数減衰）。反射波は
             早く到達するほど幅が広くなり歪みが消える（硬い血管の波形）。雑音は標準偏差
             0.002。**真値は反射波のピーク − 前進波のピーク**（母数の差ではない）
  当てはめ   (1) 凍結版 2 カーネル（`src/pda.py` の探索範囲と同じ。Δμ の下限 0.08 s）
             (2) Δμ の下限を 0.01 s に緩める
             (3) 自由な指数減衰を足す（24番 の A1 と同じ形。d·exp(−(t−t0)/τ)）
             (4) 貯留槽を前進波の畳み込みで持つ（res(t) = g·∫g1(s)·e^{−(t−s)/τ}ds。母数は
                 g と τ の 2 つ）
             (5) 第2成分の形を第1成分に縛る（σ2 = c·σ1・α2 = α1）
             (6) 0.65T までで当てはめる
             いずれも `scipy.optimize.least_squares`（trf・起点 4 点・max_nfev 3000）で、
             **収束検算は課さない**（この節が見たいのは下限で詰まるかどうかで、採否ではない）
  掃引       貯留槽の時定数 3 通り（0.45・0.35・0.25 s）× 反射波の到達 10 通り（0.30〜0.08 s）。
             時定数を年齢層に見立て、層の中で到達だけを振る（26番の年齢層内 Spearman を模す）
  出す表     型ごとに、時定数の層ごとの 順位相関 ρ・|誤差| の中央値・下限の詰まり、および
             1 拍ずつの表（真値・型・各当てはめの返り値と誤差・特徴点法）

**下限の詰まりの規準（計算の前に決めた）**: 真値の小さいほうから 3 拍で、返り値の範囲が
20 ms 未満なら「あり」と印字する。範囲は詰まりを取り逃がすことがあるので（返り値が下限の
手前で折り返すと範囲は広く出る）、同じ表に**返り値の最小値**と**下位 3 拍の範囲**も並べる。
真値の最小値と返り値の最小値の差が、追えなくなった大きさである。

参考として `pda2.preprocess` → `find_landmarks` の特徴点法（dia_t − sys_t）も同じ拍で出す。

節B（実データ・`--csv` があれば走る）
-------------------------------------
既存の `data/pwdb/pwdb_compare.csv`（26番の出力・確認的解析を回した機械では 4,374 行）の
**列だけを読む。新しい当てはめはしない**（数秒で終わる）。読む列は `age`・`klass_own`・
`dt_v1_ms`（凍結版 ΔT）・`dt_lm_ms`（特徴点法 ΔT・Charlton 同梱）・`ok_v1`（26番の A 段）。

  B1  型（`klass_own`）ごとに、凍結版 ΔT と特徴点法 ΔT の分布（5・10・25・50・75・90・95
      パーセンタイルと最小・最大）
  B2  下限の検査。特徴点法 ΔT を 20 ms 刻みの区間に分け、区間ごとに凍結版 ΔT の中央値・
      四分位範囲・人数を出す（特徴点法が短い区間でも凍結版が下がらなければ、下限で詰まって
      いる）。あわせて凍結版 ΔT の最小値・下位 5% と、探索範囲の下限（Δμ 0.08 s ＝ 80 ms）
      との差を印字する
  B3  型ごとに ρ(dt_v1_ms, dt_lm_ms)（年齢層内 Spearman の中央値。**符号つき**。同じ量を
      測っているなら正になるはずで、|ρ| では順位が壊れて負に振れたときに見えなくなる）と、
      特徴点法 ΔT が短い側の半数・長い側の半数に分けたときのそれぞれの ρ
  B4  予測との照合（下記 P1〜P3）。**判定は付けない**（事後・記述）

凍結版の列は 26番の A 段（`ok_v1 == 1`。その手法が自分で採用した例だけ）で計算し、C 段
（採否を無視した全例）は参考として添える。48番 節4 の +36.9 ms・+98.5 ms が A 段の値だから
である。年齢層内 Spearman の規約は 26番・48番と共有する（`20_pwdb_validity.py` の
`_spearman`・`_judge` をそのまま読み込む。層は `age` の相異なる値、1 層 8 名以上）。
短い側・長い側は**年齢層ごとに**その層の `dt_lm_ms` の中央値で二分する（層をまたいだ
中央値で切ると、年齢と混ざる）。半数それぞれにも 1 層 8 名以上を要求する。

予測（2026-09-15、実データを見る前に固定した）
----------------------------------------------
(P1) 実データでも凍結版 ΔT には下限の詰まりがある: 型3 で、特徴点法 ΔT が最も短い区間
     （下から 2 区間）でも凍結版 ΔT の中央値は 140 ms を下回らない。根拠: 合成では 150 ms を
     下回る真値に対して返り値が下がらなかった。
(P2) 型3 では、特徴点法 ΔT が短い側の半数の ρ(dt_v1_ms, dt_lm_ms) が、長い側の半数より
     0.15 以上小さい。根拠: 下限で詰まるのは短い側だけなので、順位が壊れるのも短い側である。
(P3) 型1 では (P2) の差が 0.15 未満。根拠: 型1 は真の到達が長く、下限で詰まる範囲に入らない。

予測の本文と数値の規準（140 ms・0.15・下から 2 区間）は 2026-09-15 に固定したものから変えて
いない。語だけは用語の決まり（`docs/research/terminology.md`）に従い「下限で詰まる」と書く。

前提と限界
----------
合成脈波は監督者が作ったもので PWDB ではない。反射波の幅と到達の結び付け方は仮定である。
1 層 10 拍なので ρ の差（0.71 対 0.89）は 1〜2 組の入れ替わりに当たる。RI は測っていない。
節B の CSV が抜粋（この環境の複製は 24 行）だと 1 層 8 名に満たず、どの ρ も計算できない。
その場合も落ちずに「—」と人数不足を印字するが、**その数値は読んではいけない。**

版は確認的解析と同じにそろえる（Python 3.9.6・NumPy 2.0.2・SciPy 1.13.1・pandas 2.3.3）。

使い方
------
    python3 scripts/50_reservoir_bench.py --selftest
    python3 scripts/50_reservoir_bench.py
    python3 scripts/50_reservoir_bench.py --csv data/pwdb/pwdb_compare.csv
    python3 scripts/50_reservoir_bench.py --section B --csv data/pwdb/pwdb_compare.csv

`--section A|B|AB`（既定 AB。CSV が無ければ A だけ）。`--fast` は節A の掃引を 2 層 × 5 拍に
減らす（自己検査と同じ掃引。本番の表ではない）。自己検査は合成だけで走る（CSV もネット
ワークも要らない）。節A の本番（3 層 × 10 拍 × 6 型）はこの環境で約 15 秒である。
結果は print するので、残すときは tee で `docs/research/results/50_reservoir_bench.txt` に
落とす。

終了コード 0 = 通常、2 = 節B を頼まれたのに CSV が無い・要る列が無い。
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import sys
import unicodedata
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import pda2                      # noqa: E402  ROOT を通してから読む
from src.pda import skew_gaussian         # noqa: E402  凍結版と同じ歪みガウス


def _load(stem: str, name: str):
    """数字始まりの台本を名前で読み込む（import 文では書けない）。45番・48番と同じ手口。"""
    p = Path(__file__).resolve().parent / stem
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# 順位相関の規約は 20番のものをそのまま使う（自前で書き直さない。26番・45番・48番と同じ）
M = _load("20_pwdb_validity.py", "m20")

DATA = ROOT / "data"
DEFAULT_CSV = DATA / "pwdb" / "pwdb_compare.csv"

MIN_PER_AGE = 8        # 1 年齢層に要る人数。26番・45番・48番の MIN_PER_AGE と同じ
N_AGES_FULL = 6        # PWDB の年齢層（25・35・45・55・65・75 歳）


# ---------------------------------------------------------------- 表示の部品
def _pad(s, w: int, right: bool = False) -> str:
    """表示幅で揃える（日本語は 2 文字分。f 文字列の桁指定は文字数なのでずれる）。"""
    used = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in str(s))
    fill = " " * max(0, w - used)
    return (fill + str(s)) if right else (str(s) + fill)


def _f(v: float, w: int = 9, prec: int = 3, sign: bool = False) -> str:
    if not np.isfinite(v):
        return _pad("—", w, right=True)
    return f"{v:>+{w}.{prec}f}" if sign else f"{v:>{w}.{prec}f}"


def _n(v: float, prec: int = 3, sign: bool = False) -> str:
    """文中に埋める数値（桁揃えをしない）。"""
    if not np.isfinite(v):
        return "—"
    return f"{v:+.{prec}f}" if sign else f"{v:.{prec}f}"


def _yn(b: bool) -> str:
    return "はい" if b else "いいえ"


def _ari(b: bool) -> str:
    return "あり" if b else "なし"


# ================================================================ 節A（合成）
# 合成脈波の母数。監督者の試作（scratchpad/bench.py）と同じ値で、変えると節A の数値が変わる。
FS = 500.0                 # 標本化周波数 [Hz]
HR_SYN = 70.0              # 心拍数 [1/min]。拍長 T = 60 / HR
TP_F = 0.12                # 前進波のピークの目安 [s]
A_FWD, SIG_FWD, AL_FWD = 1.0, 0.045, 2.5     # 前進波（歪みガウス）の高さ・幅・歪度
A_REF = 0.45               # 反射波の高さ
W_REF_A, W_REF_B = 0.055, 0.16   # 反射波の幅 = W_REF_A + W_REF_B × 到達 [s]
AL_REF = 1.2               # 反射波の歪度（早く到達する拍では 0 にする）
DT_SKEW = 0.18             # 到達がこれ以下なら歪度 0（硬い血管の、幅が広く対称な反射波）
D_RES = 0.45               # 貯留槽の大きさ
RES_PEAK_LAG = 0.05        # 貯留槽が減衰に入る時刻 = 前進波のピーク + 到達 + これ [s]
RES_MAX_FRAC = 0.55        # ただし拍長のこの割合を超えない
NOISE_SD = 0.002           # 雑音の標準偏差

# 当てはめの型。(鍵, 番号, 表の見出し, 説明)
# 番号は波形の型（klass_own）と混ざらないよう括弧付きで書く。(5)(6) は試作と同じ設定で、
# 形の拘束・打ち切りに加えて Δμ の下限も 0.01 s に緩めてある（2 つ変わっている）。
# (5b)(6b) は同じ拘束・打ち切りで Δμ の下限を凍結版のまま 0.08 s にした版で、
# **一度に 1 つだけ変えたときの効き**を読むために 2026-09-15 に足した。
KINDS = [
    ("frozen", "(1)", "凍結版", "凍結版 2 カーネル（src/pda.py と同じ探索範囲・Δμ の下限 0.08 s）"),
    ("relax", "(2)", "Δμ0.01", "Δμ の下限を 0.01 s に緩める（ほかは凍結版のまま）"),
    ("decay", "(3)", "減衰項", "自由な指数減衰を足す（24番 A1 と同じ形・d·exp(−(t−t0)/τ)）"),
    ("conv", "(4)", "畳み込み", "貯留槽を前進波の畳み込みで持つ（res = g·∫g1(s)·e^{−(t−s)/τ}ds）"),
    ("tied", "(5)", "形を縛る", "第2成分の形を第1成分に縛る（σ2 = c·σ1・α2 = α1）＋ Δμ の下限 0.01 s"),
    ("tied08", "(5b)", "形を縛る", "同じ形の拘束で、Δμ の下限は凍結版のまま 0.08 s"),
    ("trunc", "(6)", "0.65T", "0.65T までで当てはめる ＋ Δμ の下限 0.01 s"),
    ("trunc08", "(6b)", "0.65T", "同じ打ち切りで、Δμ の下限は凍結版のまま 0.08 s"),
]
KIND_KEYS = [k for k, _no, _h, _l in KINDS]
KIND_NO = {k: no for k, no, _h, _l in KINDS}
KIND_HEAD = {k: h for k, _no, h, _l in KINDS}
KIND_LABEL = {k: l for k, _no, _h, l in KINDS}

# 模型の形（母数の並び）と、当てはめに使う範囲。(5b) は (5) と、(6b) は (6) と同じ形で、
# 違うのは Δμ の下限だけである。
KIND_SHAPE = {"frozen": "plain", "relax": "plain", "decay": "decay", "conv": "conv",
              "tied": "tied", "tied08": "tied", "trunc": "plain", "trunc08": "plain"}
KIND_TRUNC = ("trunc", "trunc08")

# 当てはめの設定。凍結版と同じ探索範囲を使う型と、Δμ の下限を緩める型を分ける。
DMU_LO_FROZEN = 0.08       # `src/pda.py` の dmu_bounds の下限 [s]
DMU_LO_RELAX = 0.01
KIND_DMU_FROZEN = ("frozen", "decay", "conv", "tied08", "trunc08")
N_STARTS = 4               # 起点の数（試作と同じ）
MAX_NFEV = 3000
TRUNC_FRAC = 0.65          # (6)(6b) が当てはめに使う範囲（拍長に対する割合）

# 掃引
TAUS_FULL = (0.45, 0.35, 0.25)
DTS_FULL = (0.30, 0.27, 0.24, 0.21, 0.18, 0.16, 0.14, 0.12, 0.10, 0.08)
TAUS_FAST = (0.45, 0.35)
# 自己検査の掃引。下位 3 拍を本番と同じ到達（0.12・0.10・0.08 s）にそろえてある。
# 下限の詰まりは下位 3 拍で測るので、ここが本番と違うと同じものを検査できない。
DTS_FAST = (0.24, 0.18, 0.12, 0.10, 0.08)
SEED_A = 0                 # 雑音の乱数種。拍ごとに同じ種を使う（試作と同じ）

MIN_BEATS_A = 3            # 節A の ρ を計算するのに要る拍数（節B の 8 名以上とは別）
FLOOR_N = 3                # 下限の詰まりを見る拍数（真値の小さいほうから）
# いま使う規準（2026-09-15 に差し替えた）: その 3 拍の**返り値の最小**が、その 3 拍の
# **真値の最大**より FLOOR_GAP_MS 以上大きいとき「あり」。
FLOOR_GAP_MS = 30.0
# 差し替える前の規準（参考として表に残す）: その 3 拍の返り値の範囲が FLOOR_RANGE_MS
# 未満なら「あり」。凍結版は返り値が下限の手前で折り返すので、範囲では取り逃がす。
FLOOR_RANGE_MS = 20.0


def synth_beat(dt_true: float, tau: float, seed: int = SEED_A, hr: float = HR_SYN):
    """前進波（歪みガウス）＋ 反射波（歪みガウス）＋ 貯留槽（指数減衰）の 1 拍を作る。

    反射波は早く到達するほど幅が広くなり歪みが消える（硬い血管の波形）。
    真値は**反射波のピーク − 前進波のピーク**で、母数（μ）の差ではない。幅と歪度が
    到達によって変わるので、両者は一致しない。
    """
    T = 60.0 / hr
    t = np.arange(0.0, T, 1.0 / FS)
    w_ref = W_REF_A + W_REF_B * dt_true
    al_ref = AL_REF if dt_true > DT_SKEW else 0.0
    fwd = skew_gaussian(t, A_FWD, TP_F - 0.02, SIG_FWD, AL_FWD)
    ref = skew_gaussian(t, A_REF, TP_F + dt_true - 0.02, w_ref, al_ref)
    t_a = min(RES_MAX_FRAC * T, TP_F + dt_true + RES_PEAK_LAG)
    rise = np.clip(t / max(t_a, 1e-6), 0.0, 1.0) ** 2
    res = D_RES * rise * np.exp(-np.maximum(t - t_a, 0.0) / tau)
    y = fwd + ref + res
    y = y + NOISE_SD * np.random.default_rng(seed).standard_normal(y.size)
    t_ref = float(t[int(np.argmax(ref))])
    t_fwd = float(t[int(np.argmax(fwd))])
    return t, y, {"dt_s": t_ref - t_fwd, "t_ref": t_ref, "t_fwd": t_fwd,
                  "tau": tau, "dt_set": dt_true}


def _norm(y: np.ndarray) -> np.ndarray:
    """当てはめの前に 0〜1 に正規化する（凍結版 `fit_beat` と同じ扱い）。"""
    y = np.asarray(y, float)
    y = y - float(np.min(y))
    return y / max(float(np.max(y)), 1e-12)


def _peak_on(comp, t: np.ndarray):
    """成分のピーク時刻と高さ（歪みがあるので μ とは違う。拍の標本の上で探す）。"""
    g = skew_gaussian(t, *comp)
    i = int(np.argmax(g))
    return float(t[i]), float(g[i])


def _bounds(t: np.ndarray, ys: np.ndarray, kind: str):
    """型ごとの探索範囲。8 母数の並びは `src/pda.py` と同じ

    (a1, mu1, sigma1, alpha1, a2, Δμ, sigma2, alpha2)。型5 は末尾 2 つを σ の比 c に
    置き換え（7 母数）、型3・型4 は減衰の (g, τ) を足す（10 母数）。
    """
    T = float(t[-1] - t[0])
    t_pk = float(t[int(np.argmax(ys))])
    shape = KIND_SHAPE[kind]
    dmu_lo = DMU_LO_FROZEN if kind in KIND_DMU_FROZEN else DMU_LO_RELAX
    lo = [0.05, 0.02, 0.015, 0.0, 0.02, dmu_lo, 0.015, 0.0]
    hi = [2.50, max(0.60 * T, t_pk + 0.05), 0.30, 8.0,
          2.00, min(0.60, 0.85 * T), 0.35, 8.0]
    if shape == "tied":
        lo, hi = lo[:6] + [0.5], hi[:6] + [4.0]
    elif shape == "decay":
        lo, hi = lo + [0.0, 0.05], hi + [1.0, 1.50]
    elif shape == "conv":
        lo, hi = lo + [0.0, 0.05], hi + [3.0, 1.50]
    return lo, hi, dmu_lo


def _components(p, kind: str):
    """母数から 2 成分（歪みガウス 4 母数ずつ）を取り出す。"""
    c1 = (p[0], p[1], p[2], p[3])
    if KIND_SHAPE[kind] == "tied":
        c2 = (p[4], p[1] + p[5], p[2] * p[6], p[3])
    else:
        c2 = (p[4], p[1] + p[5], p[6], p[7])
    return c1, c2


def _model(p, tt: np.ndarray, kind: str) -> np.ndarray:
    c1, c2 = _components(p, kind)
    out = skew_gaussian(tt, *c1) + skew_gaussian(tt, *c2)
    shape = KIND_SHAPE[kind]
    if shape == "decay":
        out = out + p[8] * np.exp(-(tt - tt[0]) / max(p[9], 1e-3))
    elif shape == "conv":
        g1 = skew_gaussian(tt, *c1)
        dt = float(tt[1] - tt[0])
        kern = np.exp(-(tt - tt[0]) / max(p[9], 1e-3)) * dt
        out = out + p[8] * np.convolve(g1, kern)[:tt.size]
    return out


def _starts(kind: str, dmu_lo: float, lo, hi):
    """起点 4 点（試作と同じ。Δμ を 0.05 s ずつずらして別の解も探す）。"""
    out = []
    shape = KIND_SHAPE[kind]
    for s in range(N_STARTS):
        x0 = [0.9, 0.10 + 0.01 * s, 0.05, 2.0, 0.4,
              max(dmu_lo, 0.10 + 0.05 * s), 0.08, 1.0]
        if shape == "tied":
            x0 = x0[:6] + [1.6]
        elif shape in ("decay", "conv"):
            x0 = x0 + [0.3, 0.35]
        out.append([min(max(v, l), h) for v, l, h in zip(x0, lo, hi)])
    return out


def fit_kind(t: np.ndarray, y: np.ndarray, kind: str) -> dict:
    """1 拍を型 `kind` で当てはめ、ΔT [s]・RI・残差を返す。

    **収束検算（境界張り付き・別解の有無）は課さない。**この節が見たいのは真値の順位を
    追えるかどうかで、採否ではない（凍結版の採否は 26番の A 段が決めている）。
    """
    ys = _norm(y)
    lo, hi, dmu_lo = _bounds(t, ys, kind)
    if kind in KIND_TRUNC:
        keep = t <= t[0] + TRUNC_FRAC * (t[-1] - t[0])
        tfit, yfit = t[keep], ys[keep]
    else:
        tfit, yfit = t, ys
    best = None
    for x0 in _starts(kind, dmu_lo, lo, hi):
        try:
            r = least_squares(lambda p: _model(p, tfit, kind) - yfit, x0,
                              bounds=(lo, hi), method="trf", max_nfev=MAX_NFEV)
        except Exception:
            continue
        if best is None or r.cost < best.cost:
            best = r
    if best is None:
        return {"dt_s": float("nan"), "ri": float("nan"), "ok": False,
                "cost": float("nan")}
    c1, c2 = _components(best.x, kind)
    t1, h1 = _peak_on(c1, t)
    t2, h2 = _peak_on(c2, t)
    return {"dt_s": t2 - t1, "ri": h2 / max(h1, 1e-9), "ok": True,
            "cost": float(best.cost)}


def fiducial_dt(t: np.ndarray, y: np.ndarray) -> dict:
    """参考: 特徴点法（`pda2.preprocess` → `find_landmarks`）の ΔT = dia_t − sys_t。"""
    ys, _amp = pda2.preprocess(t, y, FS)
    if ys is None:
        return {"dt_s": float("nan"), "ri": float("nan"), "klass": -1}
    lm = pda2.find_landmarks(t, ys)
    klass = int(lm["klass"])
    if not (np.isfinite(lm["dia_t"]) and np.isfinite(lm["sys_t"])):
        return {"dt_s": float("nan"), "ri": float("nan"), "klass": klass}
    return {"dt_s": float(lm["dia_t"] - lm["sys_t"]),
            "ri": float(lm["dia_v"] / max(lm["sys_v"], 1e-12)), "klass": klass}


def sweep(taus, dts, seed: int = SEED_A, kinds=None) -> dict:
    """時定数 × 到達の掃引。返り値は時定数ごとの真値・返り値・型（すべて ms）。"""
    kinds = list(KIND_KEYS) if kinds is None else list(kinds)
    out = {}
    for tau in taus:
        rec = {"tau": float(tau), "dt_set": [], "truth": [], "klass": [], "fid": [],
               "got": dict((k, []) for k in kinds)}
        for dt in dts:
            t, y, tr = synth_beat(dt, tau, seed=seed)
            rec["dt_set"].append(1000.0 * dt)
            rec["truth"].append(1000.0 * tr["dt_s"])
            for k in kinds:
                r = fit_kind(t, y, k)
                rec["got"][k].append(1000.0 * r["dt_s"] if np.isfinite(r["dt_s"])
                                     else float("nan"))
            f = fiducial_dt(t, y)
            rec["fid"].append(1000.0 * f["dt_s"] if np.isfinite(f["dt_s"])
                              else float("nan"))
            rec["klass"].append(f["klass"])
        out[float(tau)] = rec
    return out


def floor_check(truth_ms, got_ms) -> dict:
    """下限の詰まり（規準は計算の前に決めた。docstring 節A を参照）。

    真値の小さいほうから FLOOR_N 拍を取り、返り値の範囲が FLOOR_RANGE_MS 未満なら
    「あり」。範囲だけでは取り逃がすので、返り値の最小値（掃引の全拍）と、その 3 拍の
    真値の範囲も返す。
    """
    truth = np.asarray(truth_ms, float)
    got = np.asarray(got_ms, float)
    order = np.argsort(truth)[:FLOOR_N]
    v = got[order]
    tv = truth[order]
    fin = v[np.isfinite(v)]
    all_fin = got[np.isfinite(got)]
    out = {"n": int(fin.size), "lo": float("nan"), "hi": float("nan"),
           "rng": float("nan"), "truth_rng": float(np.max(tv) - np.min(tv)),
           "flag": False, "got_min": float("nan"),
           "truth_min": float(np.min(truth)) if truth.size else float("nan")}
    if all_fin.size:
        out["got_min"] = float(np.min(all_fin))
    if fin.size >= 2:
        out["lo"], out["hi"] = float(np.min(fin)), float(np.max(fin))
        out["rng"] = out["hi"] - out["lo"]
        out["flag"] = bool(out["rng"] < FLOOR_RANGE_MS)
    return out


def summarise_a(res: dict) -> dict:
    """型 × 時定数の (ρ, |誤差| 中央値, 下限の詰まり)。ρ は 20番の `_spearman`。"""
    out = {}
    for tau, rec in res.items():
        truth = np.asarray(rec["truth"], float)
        series = [(k, np.asarray(rec["got"][k], float)) for k in rec["got"]]
        series.append(("fid", np.asarray(rec["fid"], float)))
        for key, got in series:
            rho, n = M._spearman(truth, got, min_n=MIN_BEATS_A)
            err = got - truth
            out[(key, tau)] = {
                "rho": rho, "n": int(n),
                "mae": float(np.nanmedian(np.abs(err))) if np.any(np.isfinite(err))
                else float("nan"),
                "bias": float(np.nanmedian(err)) if np.any(np.isfinite(err))
                else float("nan"),
                "floor": floor_check(truth, got)}
    return out


def _kind_no(key: str) -> str:
    """当てはめの型の番号（波形の型 klass_own と混ざらないよう括弧付きで書く）。"""
    return KIND_NO.get(key, "（参考）")


def print_a_legend(taus, dts, seed: int) -> None:
    print("\n" + "-" * 100)
    print("A0. 合成脈波と当てはめの型")
    print("-" * 100)
    print("  合成脈波 = 前進波（歪みガウス）＋ 反射波（歪みガウス）＋ 貯留槽（指数減衰）。")
    print(f"  反射波は早く到達するほど幅が広くなり歪みが消える（幅 = {W_REF_A} + "
          f"{W_REF_B} × 到達 [s]、到達 {DT_SKEW} s 以下で歪度 0）。")
    print(f"  雑音は標準偏差 {NOISE_SD}（乱数種 {seed}・拍ごとに同じ種）。"
          f"標本化 {FS:.0f} Hz・心拍数 {HR_SYN:.0f}/min。")
    print("  **真値は反射波のピーク − 前進波のピーク**（母数 μ の差ではない。幅と歪度が")
    print("  到達で変わるので両者は一致しない）。")
    print(f"  掃引: 貯留槽の時定数 {list(taus)} s × 反射波の到達 {list(dts)} s。")
    print("  時定数を年齢層に見立て、層の中で到達だけを振る（26番の年齢層内 Spearman を模す）。")
    print("  時定数が小さいほど高齢に相当する（PWDB は加齢で末梢血管コンプライアンスを減らす）。")
    print("\n  当てはめの型（**波形の型 klass_own とは別のもの**。番号は括弧付きで書く）:")
    for k in KIND_KEYS:
        print("    " + _pad(_kind_no(k), 8) + _pad(KIND_HEAD[k], 11) + KIND_LABEL[k])
    print("    " + _pad("（参考）", 8) + _pad("特徴点法", 11)
          + "pda2.preprocess → find_landmarks の dia_t − sys_t")
    print(f"  当てはめは least_squares（trf・起点 {N_STARTS} 点・max_nfev {MAX_NFEV}）。"
          "**収束検算は課さない。**")


def print_a_matrix(summ: dict, taus) -> None:
    """型 × 時定数の順位相関 ρ だけを 1 枚にまとめる。"""
    print("\n" + "-" * 100)
    print("A1. 順位相関 ρ（真の ΔT と、当てはめが返した ΔT。20番の `_spearman`・層ごとに"
          f" {len(list(taus))} 通りの時定数）")
    print("-" * 100)
    head = "  " + _pad("当てはめの型", 32)
    for tau in taus:
        head += _pad(f"時定数 {tau:.2f} s", 15, right=True)
    print(head)
    for k in KIND_KEYS + ["fid"]:
        lab = (f"{_kind_no(k)} {KIND_HEAD[k]}" if k in KIND_HEAD else "（参考）特徴点法")
        line = "  " + _pad(lab, 32)
        for tau in taus:
            line += _f(summ[(k, float(tau))]["rho"], 15, prec=2, sign=True)
        print(line)
    print("  ρ が 1.00 なら真値の順位を完全に追えている。1 層の拍数が少ないので、"
          "0.71 と 0.89 の差は 1〜2 組の入れ替わりに当たる。")


def print_a_layer(rec: dict, summ: dict, tau: float) -> None:
    """時定数 1 層ぶんの表（まとめ → 1 拍ずつ）。"""
    truth = np.asarray(rec["truth"], float)
    print(f"\n  --- 貯留槽の時定数 {tau:.2f} s（{truth.size} 拍・真値 "
          f"{np.min(truth):.0f}〜{np.max(truth):.0f} ms）---")
    print("    " + _pad("当てはめの型", 16) + _pad("ρ", 9, right=True)
          + _pad("|誤差|中央値", 14, right=True) + _pad("全拍の最小", 14, right=True)
          + _pad("下位3拍の返り値", 18, right=True) + _pad("下限の詰まり", 14, right=True))
    for k in KIND_KEYS + ["fid"]:
        s = summ[(k, tau)]
        fl = s["floor"]
        lab = (f"{_kind_no(k)} {KIND_HEAD[k]}" if k in KIND_HEAD else "（参考）特徴点法")
        rngs = ("—" if not np.isfinite(fl["rng"])
                else f"{fl['lo']:.0f}〜{fl['hi']:.0f} ({fl['rng']:.0f})")
        print("    " + _pad(lab, 16) + _f(s["rho"], 9, prec=2, sign=True)
              + _pad(f"{s['mae']:.0f} ms" if np.isfinite(s["mae"]) else "—", 14, right=True)
              + _pad(f"{fl['got_min']:.0f} ms" if np.isfinite(fl["got_min"]) else "—",
                     14, right=True)
              + _pad(rngs, 18, right=True)
              + _pad(_ari(fl["flag"]), 14, right=True))
    f0 = summ[(KIND_KEYS[0], tau)]["floor"]
    print(f"    「下限の詰まり」は真値の小さいほうから {FLOOR_N} 拍の返り値の範囲が "
          f"{FLOOR_RANGE_MS:.0f} ms 未満のとき「あり」（規準は計算の前に決めた）。")
    print(f"    その {FLOOR_N} 拍の真値の範囲は {f0['truth_rng']:.0f} ms、真値の最小は "
          f"{f0['truth_min']:.0f} ms である。「全拍の最小」は掃引の 10 拍を通した返り値の"
          "最小で、")
    print("    これが真値の最小より大きいほど、短い側を追えていない（下限で詰まっている）。")

    print("\n    1 拍ずつ（返り値 [ms] と、括弧内は 返り値 − 真値）")
    head = _pad("真値[ms]", 9, right=True) + _pad("波形の型", 9, right=True)
    for k in KIND_KEYS:
        head += _pad(f"{_kind_no(k)}{KIND_HEAD[k]}", 12, right=True)
    head += _pad("特徴点法", 12, right=True)
    print("    " + head)
    for i, tv in enumerate(rec["truth"]):
        line = _pad(f"{tv:.0f}", 9, right=True) + _pad(str(rec["klass"][i]), 9, right=True)
        for k in KIND_KEYS + ["fid"]:
            v = rec["got"][k][i] if k in rec["got"] else rec["fid"][i]
            line += (_pad("—", 12, right=True) if not np.isfinite(v)
                     else f"{v:>6.0f}({v - tv:+4.0f})")
        print("    " + line)
    print("    「波形の型」は特徴点法（pda2.find_landmarks）が付けた klass_own である"
          "（1 = 極値あり、3 = 変曲点で代用）。")


def section_a(taus=TAUS_FULL, dts=DTS_FULL, seed: int = SEED_A) -> dict:
    """節A: 当てはめの型を 6 通り並べ、真の反射波の到達を追えるかを測る（合成）。"""
    print("\n" + "=" * 100)
    print("節A 合成脈波: 当てはめの型を変えると、真の反射波の到達を追えるか")
    print("=" * 100)
    print_a_legend(taus, dts, seed)
    res = sweep(taus, dts, seed=seed)
    summ = summarise_a(res)
    print_a_matrix(summ, taus)
    print("\n" + "-" * 100)
    print("A2. 時定数の層ごとの表")
    print("-" * 100)
    for tau in taus:
        print_a_layer(res[float(tau)], summ, float(tau))
    print(f"\n  出典: この台本（50番）の節A が合成脈波から計算した値"
          f"（時定数 {len(list(taus))} 通り × 到達 {len(list(dts))} 通り × "
          f"当てはめ {len(KIND_KEYS)} 型・乱数種 {seed}）。")
    return {"res": res, "summ": summ, "taus": tuple(float(v) for v in taus),
            "dts": tuple(dts), "seed": seed}


# ================================================================ 節B（実データ）
KLASS_COL = "klass_own"
KLASSES = (1, 3, 4, 5)
KLASS_LABEL = {
    1: "型1 明瞭な重複切痕と拡張期ピーク（極値）",
    3: "型3 極値は無いが下降の緩む変曲点",
    4: "型4 変曲点が見つからない",
    5: "型5 収縮期ピークが拍の末尾（波形が不正）",
}
KLASS_SHORT = {1: "型1 極値あり", 3: "型3 変曲点で代用", 4: "型4 変曲点なし",
               5: "型5 波形が不正"}
COL_V1 = "dt_v1_ms"        # 凍結版 2 カーネルの ΔT（26番の出力）
COL_LM = "dt_lm_ms"        # 特徴点法の ΔT（Charlton 同梱）
COL_OK = "ok_v1"           # 26番の A 段（その手法が自分で採用した例）
NEED_B = ("age", KLASS_COL, COL_V1, COL_LM)

BIN_MS = 20.0              # B2 の区間の幅
PCTS = (5, 10, 25, 50, 75, 90, 95)
DMU_LO_MS = 1000.0 * DMU_LO_FROZEN   # 凍結版の探索範囲の下限 Δμ 0.08 s ＝ 80 ms

# 予測の規準（docstring の P1〜P3。2026-09-15 に、実データを見る前に固定した）
PRED_P1_FLOOR_MS = 140.0   # P1 型3: 下から 2 区間でも凍結版 ΔT の中央値がこれを下回らない
PRED_P1_N_BINS = 2         # P1 で見る区間の数（下から）
PRED_RHO_GAP = 0.15        # P2 型3: 短い側の ρ が長い側より これ以上小さい／P3 型1: 未満


def _colv(d: pd.DataFrame, c: str) -> np.ndarray:
    if c not in d.columns:
        return np.full(len(d), np.nan)
    return pd.to_numeric(d[c], errors="coerce").to_numpy(dtype=float)


def stage_a(d: pd.DataFrame) -> pd.DataFrame:
    """26番の A 段（ok_v1 == 1）。列が無ければそのまま返す（C 段と同じになる）。"""
    if COL_OK not in d.columns:
        return d
    return d[pd.to_numeric(d[COL_OK], errors="coerce") == 1]


def subset(d: pd.DataFrame, k: int) -> pd.DataFrame:
    return d[_colv(d, KLASS_COL) == float(k)]


def missing_cols(d: pd.DataFrame) -> list:
    return [c for c in NEED_B if c not in d.columns]


def dist_of(d: pd.DataFrame, col: str) -> dict:
    """1 列の分布（人数・最小・パーセンタイル・最大）。"""
    v = _colv(d, col)
    v = v[np.isfinite(v)]
    out = {"n": int(v.size), "min": float("nan"), "max": float("nan"),
           "p": dict((q, float("nan")) for q in PCTS)}
    if v.size:
        out["min"], out["max"] = float(np.min(v)), float(np.max(v))
        out["p"] = dict((q, float(np.percentile(v, q))) for q in PCTS)
    return out


def floor_bins(d: pd.DataFrame) -> dict:
    """特徴点法 ΔT を BIN_MS 刻みの区間に分け、区間ごとの凍結版 ΔT を要約する。

    対応のある行（両方が有限）だけを使う。返り値の `bins` は区間の下端をキーにした
    辞書で、下端の小さい順に並べれば「特徴点法が短い区間で凍結版が下がるか」が読める。
    """
    x, y = _colv(d, COL_LM), _colv(d, COL_V1)
    g = np.isfinite(x) & np.isfinite(y)
    x, y = x[g], y[g]
    out = {"n": int(x.size), "bins": [], "v1_min": float("nan"),
           "v1_p5": float("nan"), "lm_min": float("nan")}
    if x.size == 0:
        return out
    out["v1_min"] = float(np.min(y))
    out["v1_p5"] = float(np.percentile(y, 5))
    out["lm_min"] = float(np.min(x))
    idx = np.floor(x / BIN_MS).astype(int)
    for b in np.unique(idx):
        sel = idx == b
        v = y[sel]
        q1, q3 = (float(q) for q in np.percentile(v, [25, 75]))
        out["bins"].append({"lo": float(b) * BIN_MS, "hi": float(b + 1) * BIN_MS,
                            "n": int(sel.sum()), "med": float(np.median(v)),
                            "q1": q1, "q3": q3,
                            "lm_med": float(np.median(x[sel]))})
    return out


def rho_rows(d: pd.DataFrame, half=None) -> list:
    """年齢層ごとの (年齢, ρ(dt_v1_ms, dt_lm_ms), n)。

    `half` が "short"／"long" のときは、**その年齢層の** `dt_lm_ms` の中央値で二分した
    片側だけを使う（層をまたいだ中央値で切ると年齢と混ざる）。ρ は 20番の `_spearman`
    （対応のある行だけ・1 層 MIN_PER_AGE 名以上）。
    """
    out = []
    if "age" not in d.columns or len(d) == 0:
        return out
    for age, g in d.groupby("age", sort=True):
        x, y = _colv(g, COL_V1), _colv(g, COL_LM)
        keep = np.isfinite(x) & np.isfinite(y)
        if half is not None and int(keep.sum()) >= 2:
            thr = float(np.median(y[keep]))
            keep = keep & ((y <= thr) if half == "short" else (y > thr))
        r, n = M._spearman(x[keep], y[keep], min_n=MIN_PER_AGE)
        out.append((float(age), r, int(n)))
    return out


def strat(rows: list, sign: int = 1) -> dict:
    """年齢層をまたいだまとめ。中央値・向きの層数は 20番の `_judge` に任せる。"""
    fin = [(a, r, n) for a, r, n in rows if np.isfinite(r)]
    j = M._judge(rows, sign) if rows else None
    return {"rows": rows,
            "med": float(np.median([r for _a, r, _n in fin])) if fin else float("nan"),
            "med_abs": j["med_abs"] if j else float("nan"),
            "n_ok": j["n_ok"] if j else 0,
            "n_ages": j["n_ages"] if j else 0,
            "min_n": min(n for _a, _r, n in fin) if fin else 0,
            "n_tot": int(sum(n for _a, _r, n in fin))}


def print_b1(d: pd.DataFrame, klasses) -> dict:
    """B1 型ごとの ΔT の分布。"""
    print("\n" + "-" * 100)
    print("B1. 型ごとの ΔT の分布（凍結版と特徴点法。単位 ms）")
    print("-" * 100)
    print("  段 A は 26番の A 段（ok_v1 == 1。凍結版が自分で採用した例）、段 C は採否を"
          "無視した全例。")
    out = {}
    for k in klasses:
        g = subset(d, k)
        ga = stage_a(g)
        print(f"\n  {KLASS_LABEL.get(k, f'型{k}')}  n = {len(g)} 名（A 段 {len(ga)} 名）")
        if len(g) == 0:
            print("    該当なし")
            continue
        print("    " + _pad("列", 12) + _pad("段", 4) + _pad("n", 7, right=True)
              + _pad("最小", 8, right=True)
              + "".join(_pad(f"p{q}", 8, right=True) for q in PCTS)
              + _pad("最大", 8, right=True))
        for col in (COL_V1, COL_LM):
            for stg, gg in (("A", ga), ("C", g)):
                s = dist_of(gg, col)
                out[(k, col, stg)] = s
                print("    " + _pad(col, 12) + _pad(stg, 4) + _pad(s["n"], 7, right=True)
                      + _f(s["min"], 8, prec=1)
                      + "".join(_f(s["p"][q], 8, prec=1) for q in PCTS)
                      + _f(s["max"], 8, prec=1))
    print("\n  出典: この台本（50番）の節B が CSV の既存列から計算した値。"
          "**新しい当てはめはしていない。**")
    return out


def print_b2(d: pd.DataFrame, klasses) -> dict:
    """B2 下限の検査（特徴点法 ΔT の区間ごとに凍結版 ΔT を並べる）。"""
    print("\n" + "-" * 100)
    print(f"B2. 下限の検査: 特徴点法 ΔT を {BIN_MS:.0f} ms 刻みの区間に分け、区間ごとの"
          " 凍結版 ΔT（A 段）")
    print("-" * 100)
    print("  特徴点法 ΔT が短い区間でも凍結版 ΔT の中央値が下がらなければ、凍結版は下限で"
          "詰まっている。")
    print("  対応のある行（両方が有限）だけを使う。")
    out = {}
    for k in klasses:
        g = stage_a(subset(d, k))
        res = floor_bins(g)
        out[k] = res
        print(f"\n  {KLASS_LABEL.get(k, f'型{k}')}  対応のある行 {res['n']} 名（A 段）")
        if res["n"] == 0:
            print("    対応のある行が無い")
            continue
        print("    " + _pad("特徴点法 ΔT の区間", 22) + _pad("人数", 7, right=True)
              + _pad("凍結版 ΔT 中央値", 18, right=True)
              + _pad("四分位範囲", 22, right=True)
              + _pad("特徴点法 ΔT 中央値", 20, right=True))
        for b in res["bins"]:
            iqr = f"[{b['q1']:.1f}〜{b['q3']:.1f}]"
            print("    " + _pad(f"[{b['lo']:.0f}, {b['hi']:.0f})", 22)
                  + _pad(b["n"], 7, right=True) + _f(b["med"], 18, prec=1)
                  + _pad(iqr, 22, right=True) + _f(b["lm_med"], 20, prec=1))
        print(f"    凍結版 ΔT の最小 {_n(res['v1_min'], 1)} ms・下位 5% "
              f"{_n(res['v1_p5'], 1)} ms。探索範囲の下限 Δμ {DMU_LO_FROZEN} s "
              f"（＝ {DMU_LO_MS:.0f} ms）との差は "
              f"{_n(res['v1_min'] - DMU_LO_MS, 1, sign=True)} ms・"
              f"{_n(res['v1_p5'] - DMU_LO_MS, 1, sign=True)} ms。")
        print(f"    特徴点法 ΔT の最小は {_n(res['lm_min'], 1)} ms である。")
    print("\n  Δμ は母数（μ2 − μ1）の下限で、ΔT は成分のピーク間隔である。歪みがあると")
    print("  ピークは μ からずれるので、ΔT が 80 ms を下回ることはありうる。80 ms は")
    print("  それでも目安になる（下限より下には母数を動かせない）。")
    print("  出典: この台本（50番）の節B が CSV の既存列から計算した値。")
    return out


def print_b3(d: pd.DataFrame, klasses) -> dict:
    """B3 型ごとの ρ(dt_v1_ms, dt_lm_ms) と、特徴点法 ΔT の短い側・長い側。"""
    print("\n" + "-" * 100)
    print("B3. 型ごとの ρ(dt_v1_ms, dt_lm_ms)（年齢層内 Spearman の中央値。符号つき）")
    print("-" * 100)
    print(f"  層は `age` の相異なる値、1 層 {MIN_PER_AGE} 名以上（20番の `_spearman`）。")
    print("  短い側・長い側は**年齢層ごとに**その層の dt_lm_ms の中央値で二分した半数で、")
    print("  半数それぞれにも 1 層 8 名以上を要求する（足りない層は数えない）。")
    print("  下限で詰まっているなら、短い側で ρ が落ちる。")
    print("    " + _pad("型", 20) + _pad("段", 4) + _pad("ρ 全体", 13, right=True)
          + _pad("ρ 短い側", 13, right=True) + _pad("ρ 長い側", 13, right=True)
          + _pad("差 長−短", 11, right=True) + _pad("層", 5, right=True)
          + _pad("最小n", 8, right=True))
    out = {}
    for k in klasses:
        g = subset(d, k)
        for stg, gg in (("A", stage_a(g)), ("C", g)):
            s_all = strat(rho_rows(gg))
            s_sh = strat(rho_rows(gg, half="short"))
            s_lg = strat(rho_rows(gg, half="long"))
            gap = s_lg["med"] - s_sh["med"]
            out[(k, stg)] = {"all": s_all, "short": s_sh, "long": s_lg, "gap": gap}
            lab = KLASS_SHORT.get(k, f"型{k}")
            print("    " + _pad(lab, 20) + _pad(stg, 4)
                  + _f(s_all["med"], 13, prec=3, sign=True)
                  + _f(s_sh["med"], 13, prec=3, sign=True)
                  + _f(s_lg["med"], 13, prec=3, sign=True)
                  + _f(gap, 11, prec=3, sign=True)
                  + _pad(s_all["n_ages"], 5, right=True)
                  + _pad(s_all["min_n"] or "—", 8, right=True))
    print("  「層」「最小n」は ρ 全体のもの。短い側・長い側は人数が半分になるので、"
          "層が減ることがある。")
    print("  出典: この台本（50番）の節B が CSV の既存列から計算した値。")
    return out


def print_b4(b2: dict, b3: dict) -> dict:
    """B4 予測との照合（P1〜P3）。**判定は付けない**（事後・記述）。"""
    print("\n" + "-" * 100)
    print("B4. 予測との照合（予測は 2026-09-15 に、実データを見る前に固定した。docstring と同文）")
    print("-" * 100)
    print("  (P1) 型3 で、特徴点法 ΔT が最も短い区間（下から 2 区間）でも凍結版 ΔT の")
    print(f"       中央値は {PRED_P1_FLOOR_MS:.0f} ms を下回らない。")
    print(f"  (P2) 型3 では、特徴点法 ΔT が短い側の半数の ρ が長い側の半数より "
          f"{PRED_RHO_GAP:.2f} 以上小さい。")
    print(f"  (P3) 型1 では (P2) の差が {PRED_RHO_GAP:.2f} 未満。")

    res3 = b2.get(3, {"bins": [], "n": 0})
    low = res3["bins"][:PRED_P1_N_BINS]
    ev1 = len(low) == PRED_P1_N_BINS
    p1 = ev1 and all(np.isfinite(b["med"]) and b["med"] >= PRED_P1_FLOOR_MS for b in low)
    print(f"\n  P1 型3・特徴点法 ΔT が下から {PRED_P1_N_BINS} 区間の凍結版 ΔT 中央値:")
    for b in low:
        print(f"     [{b['lo']:.0f}, {b['hi']:.0f}) ms  n = {b['n']}  "
              f"凍結版 ΔT の中央値 {_n(b['med'], 1)} ms"
              + ("  ★ この区間は 8 名未満で、中央値は不安定である"
                 if b["n"] < MIN_PER_AGE else ""))
    if ev1:
        print(f"     → {PRED_P1_FLOOR_MS:.0f} ms を下回らない: {_yn(p1)}")
    else:
        print(f"     → 照合できない（対応のある行の区間が {len(low)} しかない）")

    g3 = b3.get((3, "A"), {})
    g1 = b3.get((1, "A"), {})
    gap3 = g3.get("gap", float("nan"))
    gap1 = g1.get("gap", float("nan"))
    p2 = bool(np.isfinite(gap3) and gap3 >= PRED_RHO_GAP)
    p3 = bool(np.isfinite(gap1) and gap1 < PRED_RHO_GAP)
    print(f"\n  P2 型3（A 段）  ρ 短い側 {_n(g3.get('short', {}).get('med', float('nan')), 3, sign=True)}"
          f"・長い側 {_n(g3.get('long', {}).get('med', float('nan')), 3, sign=True)}"
          f"・差 {_n(gap3, 3, sign=True)}")
    print(f"     → 差が {PRED_RHO_GAP:.2f} 以上: "
          + (_yn(p2) if np.isfinite(gap3) else "照合できない（層の人数が足りない）"))
    print(f"\n  P3 型1（A 段）  ρ 短い側 {_n(g1.get('short', {}).get('med', float('nan')), 3, sign=True)}"
          f"・長い側 {_n(g1.get('long', {}).get('med', float('nan')), 3, sign=True)}"
          f"・差 {_n(gap1, 3, sign=True)}")
    print(f"     → 差が {PRED_RHO_GAP:.2f} 未満: "
          + (_yn(p3) if np.isfinite(gap1) else "照合できない（層の人数が足りない）"))

    hit = sum(1 for v in (p1, p2, p3) if v)
    ev = sum(1 for v in (ev1, np.isfinite(gap3), np.isfinite(gap1)) if v)
    print(f"\n  まとめ: 予測 3 条のうち照合できたのは {ev} 条、そのうち「はい」は {hit} 条。")
    if ev < 3:
        print("  照合できなかった条は、人数が足りないか対応のある行が無いためである"
              "（この CSV が抜粋なら、確認的解析の機械で走らせ直す）。")
    print("  **この節は事後の記述であり、判定（成立・不成立）は付けない。**"
          "26番の事前規準による判定は動かない。")
    return {"P1": p1, "P2": p2, "P3": p3, "hit": hit, "n_eval": ev,
            "p1_bins": low, "gap3": gap3, "gap1": gap1}


def section_b(d: pd.DataFrame, src: str) -> dict:
    """節B: 凍結版 ΔT が下限で詰まる性質は実データにも出るか（既存列だけを読む）。"""
    print("\n" + "=" * 100)
    print("節B 実データ（PWDB）: 凍結版 ΔT は下限で詰まっているか")
    print("=" * 100)
    miss = missing_cols(d)
    if miss:
        print(f"  入力 {src}")
        print(f"  ★ 列が無い: {miss}。節B は計算できない（26番 `26_pwdb_compare.py` の"
              "出力が要る）。")
        return {"state": 2, "missing": miss}
    ages = sorted(pd.to_numeric(d["age"], errors="coerce").dropna().unique().tolist())
    kl = _colv(d, KLASS_COL)
    seen = sorted(set(int(v) for v in kl[np.isfinite(kl)]))
    n_ok = int(np.sum(pd.to_numeric(d[COL_OK], errors="coerce") == 1)) \
        if COL_OK in d.columns else -1
    print(f"  入力 {src}（26番の出力。**既存列だけを読み、新しい当てはめはしない**）")
    print(f"  行数 {len(d)} 名（確認的解析を回した機械では 4,374 名）"
          f"・年齢層 {[int(a) for a in ages]}・型の値 {seen}")
    print(f"  A 段（{COL_OK} == 1）{n_ok} 名"
          if n_ok >= 0 else f"  {COL_OK} の列が無いので A 段と C 段は同じになる")
    short = [int(a) for a in ages
             if int((pd.to_numeric(d["age"], errors="coerce") == a).sum()) < MIN_PER_AGE]
    if len(d) < 100:
        print(f"  ★ この CSV は {len(d)} 行の抜粋である（1 層 "
              f"{len(d) // max(len(ages), 1)} 名）。**ここから出る数値は読んではいけない。**")
    elif short:
        print(f"  ★ {MIN_PER_AGE} 名に満たない年齢層がある: {short}")
    klasses = list(KLASSES) + sorted(set(seen) - set(KLASSES))
    out = {"state": 0}
    out["b1"] = print_b1(d, klasses)
    out["b2"] = print_b2(d, klasses)
    out["b3"] = print_b3(d, klasses)
    out["b4"] = print_b4(out["b2"], out["b3"])
    return out


# ---------------------------------------------------------------- まとめ
def report(section: str, d=None, src: str = "", taus=TAUS_FULL, dts=DTS_FULL,
           seed: int = SEED_A) -> dict:
    """節A・節B を印字する。返り値は計算した値と終了コード。"""
    print("\n" + "=" * 100)
    print("50番 探索的（事後）: 当てはめの型と、凍結版 ΔT が下限で詰まること")
    print("=" * 100)
    print("  論文2・探索的（事後）。**判定（成立・不成立）は付けない。**事前規準による")
    print("  判定は 26番のものが有効で、この台本の出力は事後の記述である。")
    out = {"code": 0}
    if "A" in section:
        out["A"] = section_a(taus, dts, seed=seed)
    if "B" in section:
        if d is None:
            print("\n  節B は CSV が無いので走らせない（--csv で 26番の出力を渡す）。")
            out["code"] = 2
        else:
            out["B"] = section_b(d, src)
            if out["B"]["state"] != 0:
                out["code"] = 2
    print("\n" + "-" * 100)
    a_txt = (f"節A 合成脈波（時定数 {len(list(taus))} 通り × 到達 {len(list(dts))} 通り × "
             f"当てはめ {len(KIND_KEYS)} 型・雑音 SD {NOISE_SD}・乱数種 {seed}）"
             if "A" in section else "節A なし")
    b_txt = (f"節B {src}（{len(d)} 名・型の列 {KLASS_COL}・A 段 {COL_OK} == 1）"
             if ("B" in section and d is not None) else "節B なし")
    print(f"  出典: analysis/scripts/50_reservoir_bench.py / {a_txt} / {b_txt}")
    print("  年齢層内 Spearman の規約は 20番 `20_pwdb_validity.py` の `_spearman`・`_judge`")
    print(f"  をそのまま使う（1 層 {MIN_PER_AGE} 名以上・層は `age` の相異なる値）。")
    return out


# ---------------------------------------------------------------- 自己検査
# 節B の部品を試す合成データ。型3 だけ凍結版 ΔT を FLOOR_SYN_MS で止め、型1 は特徴点法に
# 載せる。これで P1・P2 が「はい」、P3 も「はい」になるはずである。
AGES_SYN = (25, 35, 45, 55, 65, 75)
N_PER_AGE_SYN = 300
LM_LO_SYN, LM_HI_SYN = 60.0, 260.0     # 特徴点法 ΔT の範囲 [ms]
FLOOR_SYN_MS = 150.0                   # 型3 に仕込む下限 [ms]
JIT_SYN_MS = 4.0                       # 当てはめの雑音 [ms]
P_KLASS1_SYN = 0.35


def synth_b(seed: int = 0) -> pd.DataFrame:
    """節B の部品を試す合成データ（型3 は下限で詰まり、型1 は詰まらない）。"""
    rng = np.random.default_rng(seed)
    frames = []
    for age in AGES_SYN:
        n = N_PER_AGE_SYN
        lm = rng.uniform(LM_LO_SYN, LM_HI_SYN, n)
        klass = np.where(rng.random(n) < P_KLASS1_SYN, 1.0, 3.0)
        jit = rng.normal(0.0, JIT_SYN_MS, n)
        v1 = np.where(klass == 1.0, lm + jit, np.maximum(lm, FLOOR_SYN_MS) + jit)
        frames.append(pd.DataFrame({"age": age, KLASS_COL: klass, COL_LM: lm,
                                    COL_V1: v1, COL_OK: 1}))
    return pd.concat(frames, ignore_index=True)


def selftest() -> int:
    n_fail = 0

    def rep(name, cond, detail=""):
        nonlocal n_fail
        cond = bool(cond)
        if not cond:
            n_fail += 1
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))

    print("50番 自己検査（合成だけで走る。CSV もネットワークも要らない）")
    print(f"  節A の掃引は {len(TAUS_FAST)} 層 × {len(DTS_FAST)} 拍に減らす"
          f"（本番は {len(TAUS_FULL)} 層 × {len(DTS_FULL)} 拍）。")

    import inspect
    rep("順位相関の規約を 20番と共有している（_spearman・_judge・層の人数）",
        M.CRIT_RHO == 0.30
        and inspect.signature(M._by_age).parameters["min_n"].default == MIN_PER_AGE,
        f"CRIT_RHO {M.CRIT_RHO} / 層の人数 {MIN_PER_AGE}")

    # --- 合成脈波そのもの
    t, y, tr = synth_beat(0.20, 0.45)
    rep("合成脈波を作れる（真値は成分のピークの差で、母数の差とは違う）",
        t.size == int(round(FS * 60.0 / HR_SYN)) and np.isfinite(tr["dt_s"])
        and abs(tr["dt_s"] - 0.20) > 0.005,
        f"{t.size} 標本・真値 {1000 * tr['dt_s']:.0f} ms（設定 200 ms）")

    # --- (a-1) 下限の詰まりの検出器そのもの
    truth5 = np.array([250.0, 200.0, 150.0, 100.0, 50.0])
    stuck = np.array([250.0, 200.0, 152.0, 151.0, 150.0])   # 下限 150 ms で止めた列
    prop = np.array([255.0, 205.0, 155.0, 105.0, 55.0])     # 真値に比例する列
    f_stuck, f_prop = floor_check(truth5, stuck), floor_check(truth5, prop)
    rep("(a) 検出器: 人工的に下限で止めた列で「あり」",
        f_stuck["flag"] and f_stuck["rng"] < FLOOR_RANGE_MS,
        f"下位 {FLOOR_N} 拍の範囲 {f_stuck['rng']:.0f} ms・返り値の最小 "
        f"{f_stuck['got_min']:.0f} ms")
    rep("(a) 検出器: 真値に比例する列では「なし」",
        (not f_prop["flag"]) and f_prop["rng"] >= FLOOR_RANGE_MS,
        f"下位 {FLOOR_N} 拍の範囲 {f_prop['rng']:.0f} ms")

    # --- 節A を減らした掃引で 1 回走らせる（(a-2)・(b)・(e) で使い回す）
    buf = io.StringIO()
    with redirect_stdout(buf):
        a0 = section_a(TAUS_FAST, DTS_FAST, seed=SEED_A)
    txt_a0 = buf.getvalue()
    summ, res = a0["summ"], a0["res"]
    rep("節A が減らした掃引で最後まで印字される",
        "A2. 時定数の層ごとの表" in txt_a0 and len(txt_a0) > 1000,
        f"{len(txt_a0)} 文字・{len(TAUS_FAST)} 層 × {len(DTS_FAST)} 拍")

    # --- (a-2) 凍結版が短い側で下限に詰まる（本文の所見そのもの）
    det = []
    for tau in TAUS_FAST:
        rec = res[float(tau)]
        truth = np.asarray(rec["truth"], float)
        got = np.asarray(rec["got"]["frozen"], float)
        order = np.argsort(truth)
        d2 = abs(got[order[0]] - got[order[1]])          # 真値が 20 ms 違う 2 拍
        gap = summ[("frozen", float(tau))]["floor"]["got_min"] - float(np.min(truth))
        det.append((tau, d2, gap, summ[("frozen", float(tau))]["floor"]["flag"]))
    rep("(a) 凍結版は短い側で下限に詰まる（真値が 20 ms 違う 2 拍で返り値の差 1 ms 未満）",
        all(dd < 1.0 for _t, dd, _g, _f2 in det),
        "・".join(f"時定数 {t_:.2f}s 差 {dd:.1f} ms" for t_, dd, _g, _f2 in det))
    rep("(a) 凍結版の返り値の最小は真値の最小より 60 ms 以上大きい（短い側を追えない）",
        all(g >= 60.0 for _t, _d, g, _f2 in det),
        "・".join(f"時定数 {t_:.2f}s +{g:.0f} ms" for t_, _d, g, _f2 in det))
    print("    参考: 規準どおりの「下限の詰まり」の印字は "
          + "・".join(f"時定数 {t_:.2f}s {_ari(f2)}" for t_, _d, _g, f2 in det)
          + f"（真値の小さいほうから {FLOOR_N} 拍の返り値の範囲が "
            f"{FLOOR_RANGE_MS:.0f} ms 未満か）。")

    # --- (b) 畳み込み貯留槽の ρ が凍結版より大きい
    pairs = [(tau, summ[("frozen", float(tau))]["rho"], summ[("conv", float(tau))]["rho"])
             for tau in TAUS_FAST]
    rep("(b) 畳み込み貯留槽の ρ が凍結版より大きい（両層）",
        all(np.isfinite(a) and np.isfinite(b) and b > a for _t, a, b in pairs),
        "・".join(f"時定数 {t_:.2f}s 凍結版 {a:+.2f} → 畳み込み {b:+.2f}"
                  for t_, a, b in pairs))

    # --- (c) 節B の計算部品を、下限で詰まる列を人工的に作った表で確かめる
    db = synth_b(seed=0)
    bufb = io.StringIO()
    with redirect_stdout(bufb):
        sb = section_b(db, "合成データ（自己検査）")
    txt_b = bufb.getvalue()
    rep("(c) 節B が合成の表で最後まで印字される",
        sb["state"] == 0 and "B4. 予測との照合" in txt_b,
        f"{len(db)} 行・{len(txt_b)} 文字")
    b2, b4 = sb["b2"], sb["b4"]
    low3 = b2[3]["bins"][:PRED_P1_N_BINS]
    rep("(c) P1: 型3 は下から 2 区間でも凍結版 ΔT の中央値が下がらない",
        b4["P1"] and all(abs(b["med"] - FLOOR_SYN_MS) < 3.0 for b in low3),
        "・".join(f"[{b['lo']:.0f},{b['hi']:.0f}) 中央値 {b['med']:.1f} ms" for b in low3)
        + f"（仕込んだ下限 {FLOOR_SYN_MS:.0f} ms）")
    rep("(c) P2: 型3 は短い側の ρ が長い側より 0.15 以上小さい",
        b4["P2"], f"差 {_n(b4['gap3'], 3, sign=True)}")
    rep("(c) P3: 型1（下限を仕込んでいない）は差が 0.15 未満",
        b4["P3"], f"差 {_n(b4['gap1'], 3, sign=True)}")
    rep("(c) 型1 の凍結版 ΔT の最小は特徴点法に追随する（下限を仕込んでいない）",
        b2[1]["v1_min"] < FLOOR_SYN_MS - 40.0,
        f"型1 の最小 {b2[1]['v1_min']:.1f} ms・型3 の最小 {b2[3]['v1_min']:.1f} ms")
    rep("(c) 下限を仕込まない表では P1 が「いいえ」になる（検査が効いている）",
        not _p1_of(synth_b_nofloor(seed=0)),
        "型3 にも下限を仕込まない合成データで照合した")

    # --- (d) 列が無い CSV
    d_miss = db.drop(columns=[COL_V1])
    bufm = io.StringIO()
    with redirect_stdout(bufm):
        out_m = report("B", d_miss, "合成データ（列を抜いた）")
    txt_m = bufm.getvalue()
    rep("(d) 列が無い CSV で落ちずに「列が無い」と印字し、終了コード 2 になる",
        out_m["code"] == 2 and "列が無い" in txt_m and COL_V1 in txt_m,
        f"終了コード {out_m['code']}")

    # --- (e) 同じ乱数種なら出力が同一
    def render(seed):
        b = io.StringIO()
        with redirect_stdout(b):
            section_a(TAUS_FAST, DTS_FAST, seed=seed)
        return b.getvalue()

    t_same, t_other = render(SEED_A), render(SEED_A + 1)
    rep("(e) 同じ乱数種なら出力が同一", t_same == txt_a0, f"{len(t_same)} 文字")
    rep("(e) 乱数種を変えれば値は変わる（比較が効いている）", t_other != txt_a0)

    # --- 既定の CSV があれば節B を走らせる（動くことの確認だけ）
    print("\n  --- 既定の CSV で節B を走らせる（動くことの確認だけ）---")
    if DEFAULT_CSV.exists():
        d_real = pd.read_csv(DEFAULT_CSV)
        bufr = io.StringIO()
        with redirect_stdout(bufr):
            out_r = report("B", d_real, str(DEFAULT_CSV))
        txt_r = bufr.getvalue()
        rep("既定の CSV で節B が例外なく最後まで印字される",
            out_r["code"] == 0 and "B4. 予測との照合" in txt_r,
            f"{len(d_real)} 行・終了コード {out_r['code']}・{len(txt_r)} 文字")
        if len(d_real) < 100:
            rows = out_r["B"]["b3"].get((3, "A"), {}).get("all", {})
            rep("抜粋では 8 名以上の年齢層が無く、ρ が計算できないことが表に出る",
                rows.get("n_ages", 0) == 0,
                f"評価できた層 {rows.get('n_ages', 0)}")
            print(f"  ★ この機械の {DEFAULT_CSV.name} は {len(d_real)} 行の抜粋である。")
            print("  ★ **ここから出る数値は読んではいけない。**確認的解析の機械の"
                  " 4,374 行で走らせること。")
    else:
        rep("既定の CSV が無い機械でも自己検査は通る", True, f"{DEFAULT_CSV} が無い")

    print("\n" + ("自己検証: 通過" if n_fail == 0 else f"自己検証: 失敗 {n_fail} 件"))
    return 0 if n_fail == 0 else 1


def synth_b_nofloor(seed: int = 0) -> pd.DataFrame:
    """(c) の対照。型3 にも下限を仕込まない（P1 が「いいえ」になるはず）。"""
    d = synth_b(seed=seed)
    rng = np.random.default_rng(seed + 1)
    d[COL_V1] = _colv(d, COL_LM) + rng.normal(0.0, JIT_SYN_MS, len(d))
    return d


def _p1_of(d: pd.DataFrame) -> bool:
    """P1 だけを静かに計算する（自己検査の対照用）。"""
    b = floor_bins(stage_a(subset(d, 3)))
    low = b["bins"][:PRED_P1_N_BINS]
    return bool(low) and len(low) == PRED_P1_N_BINS and all(
        np.isfinite(x["med"]) and x["med"] >= PRED_P1_FLOOR_MS for x in low)


# ---------------------------------------------------------------- 入口
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=str, default=None,
                    help="26番の出力（既定 data/pwdb/pwdb_compare.csv があれば使う）")
    ap.add_argument("--section", type=str, default="AB", choices=("A", "B", "AB"),
                    help="走らせる節（既定 AB。CSV が無ければ A だけ）")
    ap.add_argument("--fast", action="store_true",
                    help="節A の掃引を 2 層 × 5 拍に減らす（自己検査と同じ。本番の表ではない）")
    ap.add_argument("--seed", type=int, default=SEED_A, help="節A の雑音の乱数種")
    ap.add_argument("--selftest", action="store_true",
                    help="合成だけで計算の筋道を検算する（CSV もネットワークも要らない）")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())

    d, src = None, ""
    want_b = "B" in args.section
    if want_b:
        p = Path(args.csv) if args.csv else DEFAULT_CSV
        if not p.exists() and not p.is_absolute():
            p = ROOT / str(args.csv)
        if p.exists():
            d, src = pd.read_csv(p), str(p)
        elif args.csv:
            print(f"\n{args.csv} が無い。26番（26_pwdb_compare.py）の出力が要る。")
            print("確認的解析を回した機械には data/pwdb/pwdb_compare.csv がある（4,374 行）。")
            sys.exit(2)
        else:
            print(f"\n{DEFAULT_CSV} が無いので節A だけを走らせる"
                  "（節B は --csv で 26番の出力を渡す）。")
            args.section = args.section.replace("B", "") or "A"

    taus = TAUS_FAST if args.fast else TAUS_FULL
    dts = DTS_FAST if args.fast else DTS_FULL
    if args.fast:
        print("\n  ★ --fast: 節A の掃引を減らしている。**本番の表ではない。**")
    out = report(args.section, d, src, taus=taus, dts=dts, seed=args.seed)
    sys.exit(out["code"])


if __name__ == "__main__":
    main()

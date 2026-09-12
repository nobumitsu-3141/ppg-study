#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探索的（事後）: RI を心拍数で調整すると、末梢血管抵抗の指標として良くなるか。

**これは事後の探索であり、論文2 の事前規準による判定は動かさない。**
26番（`26_pwdb_compare.py`）で下した判定はそのまま有効で、この台本の出力は
すべて「探索的（事後）」として読む。著者の問い（2026-09-12）は次のとおり。

    反射指数 RI を心拍数で調整したら（心拍数で割る／心拍数を回帰で除く）、
    末梢血管抵抗の指標として良くなるか。

調整を試す理由は、20番の因子別主効果（lab_log 2026-09-03 の表）で、凍結版 PDA の RI を
最も動かす因子が心拍数（主効果 −40.3%・年齢層内 ρ −0.37）だからである。真値である
末梢血管抵抗そのものも心拍数に依存するので、心拍数の寄与を除けば残りが抵抗を
より強く反映する可能性がある。

予測（2026-09-12。**計算の前に固定した。**監督者による）
----------------------------------------------------------
心拍数で調整すると、分解由来 RI と末梢血管抵抗の年齢層内相関は**いくらか上がるが、
特徴点由来 RI の水準には及ばない。**理由は 2 つある。

(i) 分解の応答が脈波伝播速度に対して単調でない。第2成分が拾う波が入れ替わる
    （20番: 脈波伝播速度 +1 SD で RI は 0.254 → 0.647 に跳ぶ。lab_log 2026-09-03）。
    これは心拍数とは独立の体制の変化なので、心拍数を除いても残る。
(ii) 大動脈径の主効果が +33.2% と大きい（同表。心拍数は −40.3%、脈波伝播速度は +33.7%）。
     心拍数を除いても大動脈径の寄与は残る。

数値で書くと

    ri_v1       未調整 約 0.21 → 調整後は最大でも 約 0.40
    digital_ri  未調整 約 0.50 から ほとんど動かない
    ri_v2・ri_v2g・amb_amp1  事前の数値予測は置かない（参考として同じ表に出す）

照合の規準（これも計算の前に決める。`予測との照合` の節はこの 3 条で判定する）

    P1  ri_v1 の 5 通りの調整の最大値が、未調整より大きい
    P2  その最大値が 0.40 以下であり、かつ digital_ri の未調整値を下回る
        （相関の大きさが特徴点由来 RI に及ばない）
    P3  digital_ri は 5 通りのどれも未調整との差が 0.05 以内

計算するもの
------------
指標 ri_v1・ri_v2・ri_v2g・digital_ri・amb_amp1 と真値 pvr（末梢血管抵抗）について、
26番と同じ年齢層内 Spearman ρ の規約で、次の 5 通りを並べる。amb_amp1 は論文2 の目標が
大動脈PWV なのでその行も出す。**ri_v1 は 26番の A 段（`ok_v1 == 1`）、それ以外
（ri_v2・ri_v2g・digital_ri・amb_amp1）は C 段（採否を無視した全例）で計算する**
（`データ` の節を参照。V1_STAGE_A）。

    1 未調整            Spearman(指標, 真値)
    2 心拍数で割る       Spearman(指標 / HR, 真値)
    3 心拍数を回帰で除く  年齢層内で指標を [1, HR] に最小二乗回帰した残差と真値の Spearman
    4 心拍数と駆出時間     同じく [1, HR, lvet] の残差
    5 偏順位相関         指標・真値・HR を順位に直してからの偏相関（3 の裏取り）

規約は 26番・23番・20番と共有する（`20_pwdb_validity.py` の `_spearman`・`_by_age`・
`_judge` をそのまま読み込む）。年齢層は `age` の相異なる値（6 層）、1 層に 8 名以上、
まとめは年齢層をまたいだ |ρ| の中央値と、予測の向きの層数である。**判定（成立・不成立）は
出さない。**事前規準による判定は 26番のものが有効で、事後の探索で上書きしない。

指標が NaN の行（当てはめが採用されなかった拍）は指標ごとに除く。除いたあとの人数を
層ごとに数え、表には層の最小 n を出す。

データ
------
`data/pwdb/pwdb_compare.csv`（26番の出力）。**確認的解析を回した機械では 4,374 行**
（仮想被験者 1 名 1 行）。この台本はまず未調整の値が論文2 の既知の値
（ri_v1 0.207・digital_ri 0.504・amb_amp1 × 大動脈PWV 0.836。lab_log 2026-09-03／09-09）を
再現するかを照合し、ずれていればその旨を出す。**ri_v1 は凍結版（`*_v1`）なので、26番の
A 段（`ok_v1 == 1`。確認的解析を回した機械では 4,374 例中 4,036 例）だけで照合する。**
論文2 の 0.207 はこの段で計算されているためで、採否を無視した C 段（全例）では再現しない。
digital_ri・amb_amp1 は採否と無関係な指標なので、従来どおり対応のある行（pairwise-complete）・
26番の C 段（採否を無視した全例）で照合する。ri_v1 の C 段の値は 1 行だけ参考に出す
（照合の合否には使わない）。以降の表（節 1・節 2・節 3）でも同じ規則で、ri_v1 が絡む行は
すべて A 段、それ以外（digital_ri・amb_amp1・ri_v2・ri_v2g）は C 段のまま計算する。
**クラウド側の複製は 24 行しかなく、
1 層 4 名で 8 名に満たないため、どの ρ も計算できない。**自己検査で動くことだけを確かめる
用途にしか使えない。

使い方
------
自己検査（CSV は要らない。合成データで筋道を検算する）

    python3 analysis/scripts/45_ri_hr_adjust.py --selftest

本番（既定は data/pwdb/pwdb_compare.csv）

    python3 analysis/scripts/45_ri_hr_adjust.py
    python3 analysis/scripts/45_ri_hr_adjust.py --csv data/pwdb/pwdb_compare.csv

終了コード 0 = 既知の値と一致、1 = ★ずれ（入力が論文2 と違う）、2 = 照合できない
（層の人数が足りない。24 行の複製はここに落ちる）。
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _load(stem: str, name: str):
    """数字始まりの台本を名前で読み込む（import 文では書けない）。26番と同じ手口。"""
    p = Path(__file__).resolve().parent / stem
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# 判定の規約は 20番のものをそのまま使う（自前で書き直さない。26番と同じ）
M = _load("20_pwdb_validity.py", "m20")

DATA = ROOT / "data"
DEFAULT_CSV = DATA / "pwdb" / "pwdb_compare.csv"

MIN_PER_AGE = 8        # 1 年齢層に要る人数。26番の MIN_PER_AGE と同じ
N_AGES_FULL = 6        # PWDB の年齢層（25・35・45・55・65・75 歳）

# 論文2 で確定している未調整の値（lab_log 2026-09-03 の表・2026-09-09 の 26番の表）。
# ここが再現しなければ入力が論文2 と違うので、表全体を読んではいけない。
# ri_v1 の 0.207 は 26番の A 段（ok_v1 == 1）で計算されている（V1_STAGE_A）。
# digital_ri・amb_amp1 は採否と無関係なので、従来どおり C 段（採否を無視した全例）
KNOWN = {("ri_v1", "pvr"): 0.207,
         ("digital_ri", "pvr"): 0.504,
         ("amb_amp1", "PWV_a"): 0.836}
TOL_KNOWN = 0.02

# 予測の規準（docstring の P1〜P3。計算の前に固定した）
PRED_RI_V1_MAX = 0.40      # ri_v1 の調整後はここを超えない
PRED_DIGITAL_MOVE = 0.05   # digital_ri はここより動かない

# (列, 真値, 予測の向き, 表示名)。向き 0 は事前の向きの予測が無い行（記述のみ）
PAIRS = [
    ("ri_v1",      "pvr",   +1, "RI 凍結PDA 2カーネル × 末梢血管抵抗"),
    ("ri_v2",      "pvr",   +1, "RI 第2版 歪みガウス × 末梢血管抵抗"),
    ("ri_v2g",     "pvr",   +1, "RI 第2版 ガンマ × 末梢血管抵抗"),
    ("digital_ri", "pvr",   +1, "RI 特徴点 × 末梢血管抵抗"),
    # 早期振幅比と末梢血管抵抗の関連は論文2 で未検証（向きの予測を置いていない）
    ("amb_amp1",   "pvr",    0, "早期振幅比 Am_b/Am_p1 × 末梢血管抵抗"),
    # 論文2 での目標は大動脈PWV。向きは 26番の PAIRS と同じ負
    ("amb_amp1",   "PWV_a", -1, "早期振幅比 Am_b/Am_p1 × 大動脈PWV"),
]

# 凍結版 (*_v1) は 26番の A 段（ok_v1 == 1）で計算する。論文2 の 0.207 がその段の値だから
# （2026-09-12 の訂正。データ の節を参照）。ri_v2・ri_v2g・digital_ri・amb_amp1 は対象外で、
# 採否を無視した C 段（全例）のまま計算する
V1_STAGE_A = {"ri_v1": "ok_v1"}


def _stage_for(d: pd.DataFrame, col: str) -> pd.DataFrame:
    """*_v1 の指標は ok_v1 == 1（A 段）に絞る。それ以外はそのまま（C 段）を返す。"""
    okc = V1_STAGE_A.get(col)
    if okc and okc in d.columns:
        return d[pd.to_numeric(d[okc], errors="coerce") == 1]
    return d


INDEX_LABEL = {"ri_v1": "ri_v1      凍結PDA 2カーネル",
               "ri_v2": "ri_v2      第2版 歪みガウス",
               "ri_v2g": "ri_v2g     第2版 ガンマ",
               "digital_ri": "digital_ri 特徴点",
               "amb_amp1": "amb_amp1   早期振幅比"}

# (キー, 表示名, 追加で必要な列)
ADJUST = [
    ("unadj", "未調整", ()),
    ("div",   "心拍数で割る", ("HR",)),
    ("res_h", "心拍数を回帰で除く", ("HR",)),
    ("res_hl", "心拍数と駆出時間を除く", ("HR", "lvet")),
    ("part",  "偏順位相関（HR を与える）", ("HR",)),
]
ADJ_KIND = {k: (lab, extra) for k, lab, extra in ADJUST}


# ---------------------------------------------------------------- 計算の部品
def _ols_resid(y: np.ndarray, covs: list[np.ndarray]) -> np.ndarray:
    """y を [1, covs...] に最小二乗回帰した残差。共変量が一定でも落ちない。"""
    A = np.column_stack([np.ones(y.size)] + [np.asarray(c, float) for c in covs])
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    return y - A @ beta


def _partial_spearman(x: np.ndarray, y: np.ndarray, z: np.ndarray) -> float:
    """順位に直してからの偏相関 ρ(x, y | z)。3 の裏取り。"""
    from scipy.stats import rankdata
    rx, ry, rz = rankdata(x), rankdata(y), rankdata(z)
    if min(np.ptp(rx), np.ptp(ry), np.ptp(rz)) == 0:
        return float("nan")
    rxy = float(np.corrcoef(rx, ry)[0, 1])
    rxz = float(np.corrcoef(rx, rz)[0, 1])
    ryz = float(np.corrcoef(ry, rz)[0, 1])
    den = np.sqrt(max(0.0, (1.0 - rxz ** 2) * (1.0 - ryz ** 2)))
    if den <= 1e-12:
        return float("nan")
    return float(np.clip((rxy - rxz * ryz) / den, -1.0, 1.0))


def _col(g: pd.DataFrame, c: str) -> np.ndarray:
    return pd.to_numeric(g[c], errors="coerce").to_numpy(dtype=float)


def rho_one(g: pd.DataFrame, idx: str, tgt: str, kind: str) -> tuple[float, int]:
    """1 つの年齢層の ρ と n。指標・真値・調整に要る列で対応のある行だけを使う。"""
    _lab, extra = ADJ_KIND[kind]
    need = [idx, tgt] + [c for c in extra]
    if any(c not in g.columns for c in need):
        return float("nan"), 0
    vals = {c: _col(g, c) for c in dict.fromkeys(need)}
    keep = np.ones(len(g), dtype=bool)
    for c in vals:
        keep &= np.isfinite(vals[c])
    n = int(keep.sum())
    if n < MIN_PER_AGE:
        return float("nan"), n
    x, y = vals[idx][keep], vals[tgt][keep]
    if kind == "unadj":
        return M._spearman(x, y, min_n=MIN_PER_AGE)[0], n
    if kind == "div":
        h = vals["HR"][keep]
        if np.any(h == 0):
            return float("nan"), n
        return M._spearman(x / h, y, min_n=MIN_PER_AGE)[0], n
    if kind in ("res_h", "res_hl"):
        r = _ols_resid(x, [vals[c][keep] for c in extra])
        return M._spearman(r, y, min_n=MIN_PER_AGE)[0], n
    if kind == "part":
        return _partial_spearman(x, y, vals["HR"][keep]), n
    raise ValueError(f"未知の調整: {kind}")


def rows_by_age(d: pd.DataFrame, idx: str, tgt: str, kind: str) -> list[tuple]:
    """年齢層ごとの (年齢, ρ, n)。26番と同じく `age` の相異なる値が層である。"""
    out = []
    for age, g in d.groupby("age", sort=True):
        r, n = rho_one(g, idx, tgt, kind)
        out.append((float(age), r, n))
    return out


def summarise(d: pd.DataFrame, idx: str, tgt: str, sign: int, kind: str) -> dict:
    """年齢層をまたいだまとめ。中央値・向きの層数は 20番の `_judge` に任せる。"""
    rows = rows_by_age(d, idx, tgt, kind)
    j = M._judge(rows, sign)
    fin = [(a, r, n) for a, r, n in rows if np.isfinite(r)]
    return {"rows": rows,
            "med_abs": j["med_abs"] if j else float("nan"),
            "n_ok": j["n_ok"] if j else 0,
            "n_ages": j["n_ages"] if j else 0,
            "med": float(np.median([r for _a, r, _n in fin])) if fin else float("nan"),
            "min_n": min(n for _a, _r, n in fin) if fin else 0,
            "n_tot": int(sum(n for _a, _r, n in fin))}


def _f(v: float, w: int = 9, prec: int = 3, sign: bool = False) -> str:
    if not np.isfinite(v):
        return _pad("—", w, right=True)
    return f"{v:>+{w}.{prec}f}" if sign else f"{v:>{w}.{prec}f}"


def _n(v: float, sign: bool = False) -> str:
    """文中に埋める数値（桁揃えをしない）。"""
    if not np.isfinite(v):
        return "—"
    return f"{v:+.3f}" if sign else f"{v:.3f}"


def _pad(s: str, w: int, right: bool = False) -> str:
    """表示幅で揃える（日本語は 2 文字分。f 文字列の桁指定は文字数なのでずれる）。"""
    import unicodedata
    used = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in str(s))
    fill = " " * max(0, w - used)
    return (fill + str(s)) if right else (str(s) + fill)


# ---------------------------------------------------------------- 表
def hr_main_effect(d: pd.DataFrame, pairs: list[tuple]) -> dict:
    """心拍数が指標をどれだけ動かすか（年齢層内 Spearman(指標, HR) の中央値）。
    *_v1 の指標（ri_v1）は ok_v1 == 1（A 段）で計算する（V1_STAGE_A）。"""
    print(f"\n{'-' * 92}")
    print("1. 心拍数が指標をどれだけ動かすか（年齢層内 Spearman(指標, HR)。真値は関係しない）")
    print("-" * 92)
    print(_pad("指標", 30) + _pad("ρ中央値", 11, right=True)
          + _pad("|ρ|中央値", 12, right=True) + _pad("層", 6, right=True)
          + _pad("最小n", 8, right=True))
    idxs = list(dict.fromkeys(c for c, _t, _s, _l in pairs))
    got = {}
    for idx in idxs:
        s = summarise(_stage_for(d, idx), idx, "HR", 0, "unadj")
        got[idx] = s
        print(_pad(INDEX_LABEL.get(idx, idx), 30) + _f(s["med"], 11, sign=True)
              + _f(s["med_abs"], 12) + f"{s['n_ages']:>6}{s['min_n']:>8}")
    print("  出典: この台本（45番）が --csv の CSV から計算した値。ri_v1 は 26番の A 段")
    print("  （ok_v1 == 1）、それ以外は C 段（採否を無視した全例）。20番の因子別主効果")
    print("  （lab_log 2026-09-03）では凍結版 RI の心拍数主効果 −40.3%（ρ −0.37）、")
    print("  大動脈径 +33.2%（ρ +0.30）、脈波伝播速度 +33.7%（ρ −0.17、非単調）である。")
    v1_idxs = [idx for idx in idxs if idx in V1_STAGE_A]
    if v1_idxs:
        print("  参考: C 段（採否を無視した全例）:")
        for idx in v1_idxs:
            s_c = summarise(d, idx, "HR", 0, "unadj")
            print(f"    {INDEX_LABEL.get(idx, idx).strip()}: "
                  f"ρ中央値 {_n(s_c['med'], sign=True)}・|ρ|中央値 {_n(s_c['med_abs'])}・"
                  f"層 {s_c['n_ages']}・最小n {s_c['min_n']}")
    return got


def compute_all(d: pd.DataFrame, pairs: list[tuple]) -> dict:
    """指標 × 真値 × 調整のまとめを全部作る（表示はしない）。
    *_v1 の指標（V1_STAGE_A）は ok_v1 == 1（A 段）に絞って計算する。"""
    out = {}
    for col, tgt, sign, _lab in pairs:
        dd = _stage_for(d, col)
        for kind, _l, _e in ADJUST:
            out[(col, tgt, kind)] = summarise(dd, col, tgt, sign, kind)
    return out


def compute_all_c_stage(d: pd.DataFrame, pairs: list[tuple]) -> dict:
    """V1_STAGE_A にある指標だけ、参考として C 段（採否を無視した全例）でも計算する。
    `d` はそのまま（絞らずに）渡すこと。「参考: C 段」の行を出すためだけに使う。"""
    return {(col, tgt, kind): summarise(d, col, tgt, sign, kind)
            for col, tgt, sign, _lab in pairs if col in V1_STAGE_A
            for kind, _l, _e in ADJUST}


def adjustment_table(res: dict, pairs: list[tuple], res_c: dict | None = None) -> None:
    """指標 × 調整の表。中央値 |ρ|・ρ の中央値（符号つき）・予測の向きの層・最小 n。

    `res` の *_v1 の行（V1_STAGE_A）は ok_v1 == 1（A 段）で計算されている前提。
    `res_c`（`compute_all_c_stage` の戻り値）を渡すと、その行のあとに C 段
    （採否を無視した全例）を「参考」として 1 行添える。「何も失わない」ための行で、
    判定には使わない。
    """
    res_c = res_c or {}
    print(f"\n{'-' * 92}")
    print("2. 調整ごとの年齢層内 Spearman ρ（探索的・事後）")
    print("-" * 92)
    if any(col in V1_STAGE_A for col, *_r in pairs):
        print("  ri_v1 の行は 26番の A 段（ok_v1 == 1）で計算する。それ以外は C 段（採否を")
        print("  無視した全例）のまま。ri_v1 の C 段は各行のあとに「参考」として 1 行添える。")
    print(_pad("指標 × 真値", 38) + _pad("調整", 27)
          + _pad("中央値|ρ|", 10, right=True) + _pad("ρ中央値", 10, right=True)
          + _pad("向きの層", 10, right=True) + _pad("最小n", 8, right=True))
    for col, tgt, sign, lab in pairs:
        first = True
        for kind, adj_lab, _extra in ADJUST:
            s = res[(col, tgt, kind)]
            ok = f"{s['n_ok']}/{s['n_ages']}" if sign and s["n_ages"] else "—"
            print(_pad(lab if first else "", 38) + _pad(adj_lab, 27)
                  + _f(s["med_abs"], 10) + _f(s["med"], 10, sign=True)
                  + _pad(ok, 10, right=True) + _pad(s["min_n"] or "—", 8, right=True))
            first = False
        exp = {1: "正", -1: "負", 0: "事前の向きの予測なし"}[sign]
        print(_pad("", 38) + f"（予測の向き {exp}・全 {N_AGES_FULL} 層中、"
              f"{MIN_PER_AGE} 名以上の層だけ数える）")
        if col in V1_STAGE_A and res_c:
            parts = [f"{adj_lab} {_n(res_c[(col, tgt, kind)]['med_abs'])}"
                     for kind, adj_lab, _extra in ADJUST
                     if (col, tgt, kind) in res_c]
            if parts:
                print(_pad("", 38) + "参考: C 段（採否を無視した全例）: " + "・".join(parts))
    print("  「向きの層」は予測の向きに一致した層数／ρ を計算できた層数。")
    print("  **判定（成立・不成立）は出さない。**事前規準による判定は 26番のものが有効で、")
    print("  この表は事後の探索なので上書きしない。")


def check_known(d: pd.DataFrame, res: dict, res_c: dict | None = None) -> tuple[int, list[str]]:
    """未調整の値が論文2 の既知の値を再現するか。

    `res`（`compute_all` の戻り値）は ri_v1（V1_STAGE_A）を ok_v1 == 1（A 段）で、
    それ以外を C 段（採否を無視した全例）で計算してある。論文2 の 0.207 は A 段の値
    なので、ここも A 段で照合する（2026-09-12 の訂正。従来は C 段で照合して ★ずれ に
    なっていた）。`res_c`（`compute_all_c_stage`）を渡すと、ri_v1 の C 段の値を
    「参考」として添える（何も失わない）。
    """
    res_c = res_c or {}
    print(f"\n{'-' * 92}")
    print(f"0. 未調整の値が論文2 と一致するか（許容差 {TOL_KNOWN}）")
    print("-" * 92)
    print("  ri_v1 は 26番の A 段（ok_v1 == 1）で照合する。論文2 の 0.207 がその段の値")
    print("  だから。digital_ri・amb_amp1 は採否と無関係なので、従来どおり C 段（採否を")
    print("  無視した全例）で照合する。")
    print(_pad("指標 × 真値", 38) + _pad("論文2", 9, right=True)
          + _pad("この機械", 10, right=True) + _pad("差", 9, right=True)
          + _pad("段", 4, right=True) + "  照合")
    notes, cannot = [], False
    for (col, tgt), known in KNOWN.items():
        s = res.get((col, tgt, "unadj"))
        got = s["med_abs"] if s else float("nan")
        lab = next((l for c, t, _s, l in PAIRS if c == col and t == tgt), f"{col} × {tgt}")
        stg = "A" if col in V1_STAGE_A else "C"
        if not np.isfinite(got):
            mark = "照合できない（8 名以上の年齢層が無い）"
            cannot = True
        elif abs(got - known) <= TOL_KNOWN:
            mark = "一致"
        else:
            mark = "★ずれ"
            notes.append(f"{lab}: 論文2 {known:.3f} に対し {got:.3f}")
        d_ = got - known if np.isfinite(got) else float("nan")
        print(_pad(lab, 38) + f"{known:>9.3f}" + _f(got, 10)
              + _f(d_, 9, sign=True) + _pad(stg, 4, right=True) + "  " + mark)
    state = 1 if notes else (2 if cannot else 0)
    print("  出典: 論文2 側は lab_log 2026-09-03 の表（凍結版 RI 0.207）と 2026-09-09 の")
    print("  26番の表（特徴点 RI 0.504・早期振幅比 × 大動脈PWV 0.836）。")
    print("  照合は対応のある行（pairwise-complete）。段 A の行は 26番の A 段（その手法が")
    print("  自分で採用した例だけ）、段 C の行は採否を無視した全例（26番の C 段）。")
    if res_c:
        print("  参考: C 段（採否を無視した全例。何も失わないための行で、照合の合否には")
        print("  使わない）:")
        for (col, tgt), known in KNOWN.items():
            if col not in V1_STAGE_A:
                continue
            s_c = res_c.get((col, tgt, "unadj"))
            lab = next((l for c, t, _s, l in PAIRS if c == col and t == tgt), f"{col} × {tgt}")
            got_c = s_c["med_abs"] if s_c else float("nan")
            dc = got_c - known if np.isfinite(got_c) else float("nan")
            print(f"    {lab}: 中央値|ρ| {_n(got_c)}（論文2 {known:.3f} との差 {_n(dc, sign=True)}）・"
                  f"層 {s_c['n_ages'] if s_c else 0}・最小n {s_c['min_n'] if s_c else 0}")
    if state == 1:
        print("\n  ★ 入力が論文2 と違う。**この先の表を論文2 の続きとして読んではいけない。**")
        for n in notes:
            print(f"    {n}")
    elif state == 2:
        print("\n  ★ この CSV では年齢層に 8 名以上が揃わず、照合できない。")
    return state, notes


def compare_prediction(res: dict, state: int) -> None:
    """予測との照合。予測は docstring に固定してある（計算の前に書いた）。"""
    print(f"\n{'-' * 92}")
    print("3. 予測との照合（予測は 2026-09-12 に、計算の前に固定した。docstring と同文）")
    print("-" * 92)
    print("  予測: 心拍数で調整すると分解由来 RI と末梢血管抵抗の年齢層内相関はいくらか上がるが、")
    print("        特徴点由来 RI の水準には及ばない。理由は (i) 分解の応答が脈波伝播速度に対して")
    print("        単調でなく（第2成分が拾う波が入れ替わる）、これは心拍数と独立の体制の変化で")
    print("        あること、(ii) 大動脈径の主効果 +33.2% が残ること。")
    print(f"        数値では ri_v1 約 0.21 → 最大でも 約 {PRED_RI_V1_MAX:.2f}、")
    print(f"        digital_ri は 約 0.50 から差 {PRED_DIGITAL_MOVE:.2f} 以内で動かない。")
    print("        ri_v2・ri_v2g・amb_amp1 には事前の数値予測を置いていない（参考）。")
    print("  ri_v1 は 26番の A 段（ok_v1 == 1）で計算した res から取る（未調整 約 0.21 は")
    print("  A 段の値。論文2 の 0.207 と同じ段）。")

    def spread(col, tgt):
        """未調整の値と、4 通りの調整の最大・最小・最大を与えた調整の名前。"""
        un = res[(col, tgt, "unadj")]["med_abs"] if (col, tgt, "unadj") in res else float("nan")
        adj = {k: res[(col, tgt, k)]["med_abs"] for k, _l, _e in ADJUST
               if k != "unadj" and (col, tgt, k) in res
               and np.isfinite(res[(col, tgt, k)]["med_abs"])}
        if not adj:
            return un, float("nan"), float("nan"), "—"
        k = max(adj, key=lambda q: adj[q])
        return un, adj[k], min(adj.values()), ADJ_KIND[k][0]

    if state == 2:
        print("\n  この CSV では ρ を計算できないので照合できない（層の人数が足りない）。")
        return

    un_v1, best_v1, _lo_v1, how_v1 = spread("ri_v1", "pvr")
    un_dg, best_dg, lo_dg, _how_dg = spread("digital_ri", "pvr")
    move_dg = (max(abs(best_dg - un_dg), abs(lo_dg - un_dg))
               if np.isfinite(best_dg) and np.isfinite(un_dg) else float("nan"))

    print(f"\n  ri_v1       未調整 {_n(un_v1)} → 調整後の最大 {_n(best_v1)}（{how_v1}）")
    p1 = np.isfinite(best_v1) and np.isfinite(un_v1) and best_v1 > un_v1
    p2 = (np.isfinite(best_v1) and best_v1 <= PRED_RI_V1_MAX
          and np.isfinite(un_dg) and best_v1 < un_dg)
    print(f"    P1 未調整より上がった  {'はい' if p1 else 'いいえ'}"
          f"（差 {_n(best_v1 - un_v1, sign=True)}）")
    print(f"    P2 {PRED_RI_V1_MAX:.2f} 以下、かつ特徴点由来 RI の未調整 {_n(un_dg)} を下回る"
          f"（相関の大きさが及ばない）  {'はい' if p2 else 'いいえ'}")
    print(f"    → ri_v1 は予測の{'内側' if (p1 and p2) else '外側'}")

    print(f"\n  digital_ri  未調整 {_n(un_dg)} → 調整後は {_n(lo_dg)}〜{_n(best_dg)}"
          f"、未調整との最大の差 {_n(move_dg)}")
    p3 = np.isfinite(move_dg) and move_dg <= PRED_DIGITAL_MOVE
    print(f"    P3 差が {PRED_DIGITAL_MOVE:.2f} 以内  {'はい' if p3 else 'いいえ'}")
    print(f"    → digital_ri は予測の{'内側' if p3 else '外側'}")

    print("\n  ri_v2・ri_v2g・amb_amp1: 事前の数値予測が無いので照合しない（表 2 に値だけ出した）。")
    inside = p1 and p2 and p3
    print(f"\n  まとめ: 予測（P1・P2・P3）は{'すべて満たされた' if inside else '満たされなかった条がある'}。")
    print("  **この節は事後の探索であり、論文2 の事前規準による判定（26番）は動かない。**")


def report(d: pd.DataFrame, src: str, pairs: list[tuple] | None = None) -> int:
    pairs = pairs if pairs is not None else PAIRS
    ages = sorted(pd.to_numeric(d["age"], errors="coerce").dropna().unique().tolist())
    print(f"\n{'=' * 92}")
    print("45番 探索的（事後）: RI を心拍数で調整すると末梢血管抵抗の指標として良くなるか")
    print(f"{'=' * 92}")
    print(f"  出典: analysis/scripts/45_ri_hr_adjust.py / 入力 {src}")
    print(f"  被験者 {len(d)} 名・年齢層 {[int(a) for a in ages]}"
          f"（1 層に {MIN_PER_AGE} 名以上を要求。確認的解析の機械では 4,374 名）")
    print(f"  規約は 20番・23番・26番と共有（CRIT_RHO {M.CRIT_RHO} は参考として載せるだけで、"
          "この台本は判定を出さない）")
    print("  ri_v1（V1_STAGE_A）は 26番の A 段（ok_v1 == 1）、それ以外は C 段（採否を無視した")
    print("  全例）で計算する（2026-09-12 の訂正。ri_v1 の C 段は各節に「参考」として添える）。")
    res = compute_all(d, pairs)
    res_c = compute_all_c_stage(d, pairs)
    state, _notes = check_known(d, res, res_c)
    hr_main_effect(d, pairs)
    adjustment_table(res, pairs, res_c)
    compare_prediction(res, state)
    return state


# ---------------------------------------------------------------- 自己検査
# 合成データの仕込み。指標 = A_RES * z(抵抗) + B_HR * z(心拍数) + 雑音。
# 心拍数の項は**加法**なので、心拍数で割っても取り除けない（(b) の検査）。
A_RES, B_HR, S_NOISE = 0.5, 0.5, 0.5
N_PER_AGE, N_AGES_SYN = 200, 6
SYN_PAIRS = [("idx_syn", "pvr", +1, "合成 指標 × 抵抗"),
             ("idx_hr", "pvr", +1, "合成 心拍数だけの指標 × 抵抗")]


def _spearman_of_normal(r: float) -> float:
    """2 変量正規の Pearson r に対する Spearman ρ の期待値。"""
    return 6.0 / np.pi * np.arcsin(r / 2.0)


def synth(seed: int = 0, nan_frac: float = 0.0) -> pd.DataFrame:
    """6 年齢層 × 200 名。抵抗と心拍数は独立（(d) の検査を素直にするため）。"""
    rng = np.random.default_rng(seed)
    rows = []
    for k in range(N_AGES_SYN):
        n = N_PER_AGE
        zr = rng.normal(0, 1, n)
        zh = rng.normal(0, 1, n)
        idx = A_RES * zr + B_HR * zh + rng.normal(0, S_NOISE, n)
        idx_hr = zh + rng.normal(0, S_NOISE, n)
        if nan_frac > 0:
            # 当てはめが採用されなかった拍を模す。層ごとに落とす割合を変える
            drop = rng.random(n) < (nan_frac * (k + 1) / N_AGES_SYN)
            idx = np.where(drop, np.nan, idx)
        rows.append(pd.DataFrame({
            "age": 25 + 10 * k,
            "HR": 70.0 + 12.0 * zh,
            "lvet": 300.0 + 20.0 * rng.normal(0, 1, n) - 0.5 * (12.0 * zh),
            "pvr": 1.5e8 * np.exp(0.3 * zr),
            "idx_syn": idx,
            "idx_hr": idx_hr}))
    return pd.concat(rows, ignore_index=True)


def selftest() -> int:
    ok = True

    def rep(name, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))

    print("45番 自己検査（合成データ。CSV は要らない）")

    # --- 規約を 20番と共有しているか（自前で書き直していない）
    import inspect
    rep("判定の規約を 20番と共有している（_spearman・_judge・層の人数）",
        M.CRIT_RHO == 0.30
        and inspect.signature(M._by_age).parameters["min_n"].default == MIN_PER_AGE,
        f"CRIT_RHO {M.CRIT_RHO} / 層の人数 {MIN_PER_AGE}")

    d = synth(seed=0)
    rep("合成データを作れる（6 層 × 200 名）",
        len(d) == N_PER_AGE * N_AGES_SYN and d["age"].nunique() == N_AGES_SYN,
        f"{len(d)} 行・{d['age'].nunique()} 層")

    # 未調整の経路が 20番の _by_age と一字一句同じ値になるか
    mine = [r for _a, r, _n in rows_by_age(d, "idx_syn", "pvr", "unadj")]
    theirs = [r for _a, r, _n in M._by_age(d, "idx_syn", "pvr", min_n=MIN_PER_AGE)]
    rep("未調整の ρ が 20番の _by_age と一致する",
        np.allclose(mine, theirs, equal_nan=True),
        f"最大差 {np.nanmax(np.abs(np.array(mine) - np.array(theirs))):.2e}")

    s = {k: summarise(d, "idx_syn", "pvr", +1, k) for k, _l, _e in ADJUST}
    un, di, re_, pa = (s["unadj"]["med_abs"], s["div"]["med_abs"],
                       s["res_h"]["med_abs"], s["part"]["med_abs"])

    # (a) 期待値は仕込んだ定数から出る。指標も抵抗も正規（抵抗は単調変換）なので
    #     Spearman は 2 変量正規の式で書ける
    tot = np.sqrt(A_RES ** 2 + B_HR ** 2 + S_NOISE ** 2)
    exp_un = _spearman_of_normal(A_RES / tot)
    exp_re = _spearman_of_normal(A_RES / np.sqrt(A_RES ** 2 + S_NOISE ** 2))
    rep("(a) 未調整が仕込みどおり", abs(un - exp_un) < 0.05,
        f"{un:.3f}（期待 {exp_un:.3f}）")
    rep("(a) 心拍数を回帰で除くと仕込みどおり上がる", abs(re_ - exp_re) < 0.05,
        f"{re_:.3f}（期待 {exp_re:.3f}）")
    rep("(a) 上がり幅が仕込みどおり", abs((re_ - un) - (exp_re - exp_un)) < 0.05,
        f"{re_ - un:+.3f}（期待 {exp_re - exp_un:+.3f}）")

    # (b) 心拍数の項は加法なので、割っても取り除けない
    rep("(b) 心拍数で割っても取り戻せない（加法の仕込みだから）",
        abs(di - un) < 0.02 and (re_ - di) > 0.08,
        f"割る {di:.3f}・未調整 {un:.3f}・回帰で除く {re_:.3f}")

    # (c) 偏順位相関は 3 の裏取り。両者は厳密には一致しない（3 は生の値で回帰してから
    #     順位に直し、5 は順位に直してから偏相関を取る。順位化と回帰の順序が違う）。
    #     仕込みの下では系統差はこの程度（0.02 以内）に収まる
    d_rows = dict((a, r) for a, r, _n in s["res_h"]["rows"])
    p_rows = dict((a, r) for a, r, _n in s["part"]["rows"])
    worst = max(abs(d_rows[a] - p_rows[a]) for a in d_rows)
    rep("(c) 偏順位相関が回帰の残差と一致する（中央値で 0.02 以内）",
        abs(re_ - pa) <= 0.02,
        f"残差 {re_:.3f}・偏相関 {pa:.3f}・差 {abs(re_ - pa):.4f}（層ごとの最大差 {worst:.3f}）")

    # (d) 心拍数だけで作った指標は、調整の前後どちらでも抵抗と関連しない
    h = {k: summarise(d, "idx_hr", "pvr", +1, k)["med_abs"] for k, _l, _e in ADJUST}
    rep("(d) 心拍数だけの指標は抵抗と関連しない（調整の前後とも）",
        all(v < 0.10 for v in h.values()),
        "・".join(f"{ADJ_KIND[k][0]} {v:.3f}" for k, v in h.items()))

    # (e) 対応のある行の扱い。NaN が増えれば n は減るが落ちない
    dn = synth(seed=0, nan_frac=0.9)
    sn = summarise(dn, "idx_syn", "pvr", +1, "res_h")
    n_by_age = [n for _a, _r, n in sn["rows"]]
    rep("(e) 指標の NaN で n が減り、落ちない",
        sn["n_tot"] < s["res_h"]["n_tot"] and min(n_by_age) < N_PER_AGE
        and np.isfinite(sn["med_abs"]),
        f"層ごとの n {n_by_age}（NaN 無しは各 {N_PER_AGE}）・中央値|ρ| {sn['med_abs']:.3f}")
    d8 = synth(seed=0)
    d8.loc[d8.index[:N_PER_AGE - 5], "idx_syn"] = np.nan   # 25 歳層を 5 名に減らす
    s8 = summarise(d8, "idx_syn", "pvr", +1, "unadj")
    rep("(e) 8 名に満たない層は数えない（層数が減る）",
        s8["n_ages"] == N_AGES_SYN - 1 and s8["rows"][0][2] == 5,
        f"層数 {s8['n_ages']}（25 歳層の n {s8['rows'][0][2]}）")
    dnan = synth(seed=0)
    dnan["idx_syn"] = np.nan
    snan = summarise(dnan, "idx_syn", "pvr", +1, "res_h")
    rep("(e) 指標が全欠でも落ちない（層数 0・中央値は —）",
        snan["n_ages"] == 0 and not np.isfinite(snan["med_abs"]), f"層数 {snan['n_ages']}")

    # (f) 同じ乱数種なら出力が一字一句同じ
    def render(seed):
        buf = io.StringIO()
        with redirect_stdout(buf):
            ds = synth(seed=seed)
            adjustment_table(compute_all(ds, SYN_PAIRS), SYN_PAIRS)
            hr_main_effect(ds, SYN_PAIRS)
        return buf.getvalue()

    t0, t0b, t1 = render(0), render(0), render(1)
    rep("(f) 同じ乱数種なら出力が同一", t0 == t0b, f"{len(t0)} 文字")
    rep("(f) 乱数種を変えれば値は変わる（比較が効いている）", t0 != t1)

    # (g) 2026-09-12 の訂正の検算: ok_v1 = 0 の行にだけ別の関係（符号を反転した関係）を
    #     仕込むと、A 段（既定の計算）はそれを無視し、C 段（参考の行）には混ざって出るか
    dg = synth(seed=9).copy()
    dg["ri_v1"] = dg["idx_syn"].to_numpy(copy=True)
    rng_g = np.random.default_rng(109)
    bad = rng_g.random(len(dg)) < 0.5
    dg.loc[bad, "ri_v1"] = -dg.loc[bad, "idx_syn"].to_numpy()  # ok_v1 = 0 の行だけ関係を反転する
    dg["ok_v1"] = np.where(bad, 0, 1)

    v1_pairs = [("ri_v1", "pvr", +1, "検算 ri_v1 × 抵抗")]
    a_stage = compute_all(dg, v1_pairs)[("ri_v1", "pvr", "unadj")]["med_abs"]
    c_stage = summarise(dg, "ri_v1", "pvr", +1, "unadj")["med_abs"]
    c_stage_fn = compute_all_c_stage(dg, v1_pairs)[("ri_v1", "pvr", "unadj")]["med_abs"]
    rep("(g) ok_v1 = 0 の行に別の関係（符号反転）を仕込むと、A 段はそれを無視する",
        abs(a_stage - exp_un) < 0.08,
        f"A 段 {a_stage:.3f}（未仕込みの期待値 {exp_un:.3f}・仕込んだ ok_v1=0 は "
        f"{int(bad.sum())}/{len(dg)} 名）")
    rep("(g) 同じ仕込みで C 段（参考の行）は混ざって A 段と明確に違う値になる",
        np.isfinite(c_stage) and abs(c_stage - a_stage) > 0.15,
        f"C 段 {c_stage:.3f}・A 段 {a_stage:.3f}・差 {abs(c_stage - a_stage):.3f}")
    rep("(g) compute_all_c_stage（参考の行で使う関数）が同じ C 段の値を返す",
        abs(c_stage_fn - c_stage) < 1e-9)

    # 部品そのものの検算
    y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    x1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    rep("最小二乗の残差が共変量と直交する",
        abs(float(np.dot(_ols_resid(y + 3 * x1, [x1]), x1))) < 1e-9)
    rep("共変量が一定でも残差を返す（駆出時間が動かない CSV で落ちない）",
        np.all(np.isfinite(_ols_resid(y, [np.ones(5), x1]))))
    rng = np.random.default_rng(1)
    a_ = rng.normal(0, 1, 400)
    b_ = rng.normal(0, 1, 400)
    rep("独立な 2 列の偏相関がほぼ 0", abs(_partial_spearman(a_, b_, rng.normal(0, 1, 400))) < 0.12)
    rep("交絡だけで結ばれた 2 列は偏相関で消える",
        abs(_partial_spearman(a_ + b_, 2 * a_ + rng.normal(0, .01, 400), a_)) < 0.15)

    # --- 実データ側の関数が動くことの確認（この機械の CSV は 24 行の自己検査用）
    print("\n  --- 実データ側の関数を既定の CSV で走らせる（動くことの確認だけ）---")
    if DEFAULT_CSV.exists():
        d_real = pd.read_csv(DEFAULT_CSV)
        buf = io.StringIO()
        with redirect_stdout(buf):
            st = report(d_real, str(DEFAULT_CSV))
        rep("既定の CSV で report() が落ちない",
            isinstance(st, int) and "45番 探索的（事後）" in buf.getvalue(),
            f"{len(d_real)} 行・終了コード {st}")
        if len(d_real) < 100:
            print(f"  ★ この機械の {DEFAULT_CSV.name} は {len(d_real)} 行（1 層 "
                  f"{len(d_real) // N_AGES_FULL} 名）で、自己検査用の部分集合である。")
            print("  ★ **ここから出る数値は読んではいけない。**確認的解析の機械の 4,374 行で走らせること。")
    else:
        rep("既定の CSV が無い機械でも自己検査は通る", True, f"{DEFAULT_CSV} が無い")

    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=str, default=str(DEFAULT_CSV),
                    help="26番の出力（既定 data/pwdb/pwdb_compare.csv）")
    ap.add_argument("--selftest", action="store_true",
                    help="合成データで計算の筋道を検算する（CSV は要らない）")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())

    p = Path(args.csv)
    if not p.exists() and not p.is_absolute():
        p = ROOT / args.csv
    if not p.exists():
        print(f"\n{args.csv} が無い。26番（26_pwdb_compare.py）の出力が要る。")
        print("確認的解析を回した機械には data/pwdb/pwdb_compare.csv がある（4,374 行）。")
        sys.exit(2)
    d = pd.read_csv(p)
    missing = [c for c in ("age", "HR", "lvet", "pvr") if c not in d.columns]
    if missing:
        print(f"\n{p} に要る列が無い: {missing}")
        sys.exit(2)
    sys.exit(report(d, str(p)))


if __name__ == "__main__":
    main()

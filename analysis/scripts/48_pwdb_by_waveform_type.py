#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【探索・事後】論文2: 波形の型ごとに ΔT・RI は真値とどれだけ関連するか（PWDB）。

なぜ必要か
----------
26番（`26_pwdb_compare.py`）は PWDB の被験者を全部まとめて 1 つの表にし、事前規準に
照らして判定を下した。その表の主な値は次のとおりである（lab_log 2026-09-03／09-09）。

    ΔT × 大動脈脈波伝播速度   特徴点法（同梱） 0.710 ／ 凍結版 PDA 0.223（A 段）
    RI × 末梢血管抵抗         特徴点法（同梱） 0.504 ／ 凍結版 PDA 0.207（A 段）

**この全例の値は、波形の型が混ざったまま出している。**PWDB の被験者は、重複切痕と
拡張期ピークが極値として残っている型（型1）と、極値は消えて下降脚の変曲点しか残らない
型（型3）と、変曲点も見つからない型（型4）に分かれる。分解法（PDA）の第2成分の位置は
拡張期側の特徴点に合わせて決まるので、型が変われば同じ列でも別の当たり方をするはずで、
全例の 1 つの数字はその平均にすぎない。型ごとに分ければ、0.223 と 0.710 の差が
「どの型で生じているか」が見える。

**26番の判定（成立・不成立）は動かさない。**この台本は事後・記述であり、判定は付けない。
事前規準の 0.30（20番の `CRIT_RHO`）は参考として印字するだけで、これに照らした合否は
書かない。

定義
----
  型（`klass_own`）  `pda2.find_landmarks` が拍ごとに付ける区分（Dawber 1973 を
                     Wang 2013 が細分した型に対応する）
        1  明瞭な重複切痕と拡張期ピークがある（極値として取れる）
        3  極値は無いが、下降の緩む変曲点がある（1 次微分の局所極値で代用）
        4  変曲点が見つからない（Dawber IV に相当）
        5  収縮期ピークが拍の末尾にある（波形が不正）
  ΔT [ms]           拡張期側の特徴点と収縮期ピークの時間差。特徴点法は
                    `dt_lm_ms`（Charlton 同梱）・`dt_own_ms`（自前の
                    `pda2.find_landmarks`）、分解法は `dt_v1_ms`（凍結版 2 カーネル）・
                    `dt_v2_ms`（第2版 歪みガウス）・`dt_v2g_ms`（第2版 ガンマ）
  RI                第2成分／第1成分 のピーク高さ比。特徴点法は `digital_ri`（同梱）、
                    分解法は `ri_v1`・`ri_v2`・`ri_v2g`。**自前の特徴点法に RI の列は無い**
  真値              ΔT の相手は `PWV_a`（大動脈脈波伝播速度）、RI の相手は `pvr`
                    （末梢血管抵抗）。PWDB は数値模型なのでどちらも既知である
  早期振幅比        `amb_amp1`（Am_b/Am_p1。Hellqvist 2024）。参考として 1 行だけ出す
  A 段／C 段        26番の段。A 段はその手法が自分で採用した例だけ（`ok_v1 == 1` など）、
                    C 段は採否を無視した全例。凍結版は A 段と C 段の両方、第2版 ガンマは
                    A 段と C 段、第2版 歪みガウスは C 段だけ（A 段は 2 名しか無い）、
                    特徴点法と早期振幅比は採否が無いので C 段だけ

問うこと
--------
  節1  型は年齢層にどう分布するか（`klass_own` と `klass_v2` は一致するか）
  節2  型ごとの採択率はどれだけか（第2版は規則で型1 しか採らない）
  節3  型ごとに、ΔT・RI は真値とどれだけ関連するか（年齢層内 Spearman）
  節4  型ごとに、分解法の ΔT・RI は特徴点法のそれと一致するか（同じ量を測っているか）

規約は 26番・23番・20番と共有する（`20_pwdb_validity.py` の `_spearman`・`_judge` を
そのまま読み込む）。年齢層は `age` の相異なる値（6 層）、1 層に 8 名以上、まとめは
年齢層をまたいだ |ρ| の中央値と、予測の向きを持つ層数である。

予測（2026-09-14、計算の前に固定。当たっても外れても成立・不成立の判定は付けない。事後・記述）
------------------------------------------------------------------------------------------
(P1) 特徴点法（同梱）の ΔT × 大動脈PWV は、型1 と型3 のどちらでも |ρ| の中央値が 0.30
     以上で、評価できた全層で負。根拠: 表1 の 0.710 は型3 が 77% を占める全例の値なので、
     型3 でも追っていなければこの値にならない。
(P2) 凍結版 ΔT（A 段）は、型1 では特徴点法（同梱）の ΔT との |差| の中央値が 5 ms 未満で、
     大動脈PWV との |ρ| の中央値が 0.30 以上。型3 では |差| の中央値が 20 ms 以上で、
     |ρ| の中央値が 0.30 未満。根拠: 24 名の抜粋（この環境の pwdb_compare.csv）で型1 の
     5 名は差 2 ms 未満、型3 の 1 名は 79 ms。全例の 0.223 は型3 が 77% を占めることで
     説明できる、という読み。
(P3) 凍結版 RI（A 段）は、型1 では特徴点法（同梱）の RI との |差| の中央値が 0.01 未満で、
     末梢血管抵抗との |ρ| の中央値が特徴点法の型1 の値と 0.05 以内で一致する。型3 では
     一致しない（|差| の中央値 0.05 以上）。根拠: 同じ抜粋で型1 の 5 名は RI の差が
     0.0001 未満。
(P4) 型4 は 8 名以上の年齢層が 3 層以下で、|ρ| の中央値は出ても層数が判定に足りない。
     根拠: 型4 は 105 名で、切痕の消失は高齢層に偏る。
(P5) 型1 の割合は年齢層とともに単調に減る（25 歳層で最大、75 歳層で最小）。根拠: 加齢で
     重複切痕は平坦化し消失する（論文2 背景）。

前提
----
入力は `data/pwdb/pwdb_compare.csv`（26番の出力）。**確認的解析を回した機械では 4,374 行**
（仮想被験者 1 名 1 行）。この台本はまず全例・型を分けない値が論文2 の既知の値
（0.223・0.207・0.710・0.504・0.836）を再現するかを照合し、1 つでも外れたら表を出さずに
終了コード 2 で止まる。**この環境（クラウド側）の複製は 24 行の抜粋で、1 層 4 名しか
無いのでどの ρ も計算できない。**`--allow-partial` を付けたときだけ照合を飛ばして
最後まで印字するが、その数値は読んではいけない。

版は確認的解析と同じにそろえる（Python 3.9.6・NumPy 2.0.2・SciPy 1.13.1・pandas 2.3.3）。

使い方
------
    python3 scripts/48_pwdb_by_waveform_type.py --selftest
    python3 scripts/48_pwdb_by_waveform_type.py
    python3 scripts/48_pwdb_by_waveform_type.py --csv data/pwdb/pwdb_compare.csv --allow-partial

自己検査は合成データだけで走る（CSV もネットワークも要らない）。結果は print するので、
残すときは tee で `docs/research/results/48_pwdb_by_waveform_type.txt` に落とす。

終了コード 0 = 既知の値と一致（または `--allow-partial` の参考実行）、
2 = 照合が外れた・入力が足りない。
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

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _load(stem: str, name: str):
    """数字始まりの台本を名前で読み込む（import 文では書けない）。45番・46番と同じ手口。"""
    p = Path(__file__).resolve().parent / stem
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# 判定の規約は 20番のものをそのまま使う（自前で書き直さない。26番・45番・46番と同じ）
M = _load("20_pwdb_validity.py", "m20")

DATA = ROOT / "data"
DEFAULT_CSV = DATA / "pwdb" / "pwdb_compare.csv"

MIN_PER_AGE = 8        # 1 年齢層に要る人数。26番・45番・46番の MIN_PER_AGE と同じ
N_AGES_FULL = 6        # PWDB の年齢層（25・35・45・55・65・75 歳）

KLASS_COL = "klass_own"
KLASSES = (1, 3, 4, 5)
KLASS_LABEL = {
    1: "型1 明瞭な重複切痕と拡張期ピーク（極値）",
    3: "型3 極値は無いが下降の緩む変曲点",
    4: "型4 変曲点が見つからない",
    5: "型5 収縮期ピークが拍の末尾（波形が不正）",
}

# 論文2 で確定している全例・型を分けない値（lab_log 2026-09-03 の表・2026-09-09 の 26番の表）。
# ここが再現しなければ入力が論文2 と違うので、型ごとの表を読んではいけない。
# 凍結版（*_v1）は 26番の A 段（ok_v1 == 1）の値、それ以外は C 段（採否を無視した全例）。
# 鍵は (列, 真値, 採否の列)。
KNOWN = {
    ("dt_v1_ms", "PWV_a", "ok_v1"): (0.223, -1, "ΔT 凍結版 2カーネル × 大動脈PWV"),
    ("ri_v1", "pvr", "ok_v1"): (0.207, +1, "RI 凍結版 2カーネル × 末梢血管抵抗"),
    ("dt_lm_ms", "PWV_a", None): (0.710, -1, "ΔT 特徴点 同梱 × 大動脈PWV"),
    ("digital_ri", "pvr", None): (0.504, +1, "RI 特徴点 同梱 × 末梢血管抵抗"),
    ("amb_amp1", "PWV_a", None): (0.836, -1, "早期振幅比 × 大動脈PWV"),
}
TOL_KNOWN = 0.02

# 節3 の行。(キー, 列, 真値, 予測の向き, 採否の列（None は C 段）, 段, 表示名, 群)
ROWS = [
    ("dt_lm_C", "dt_lm_ms", "PWV_a", -1, None, "C", "特徴点 同梱      dt_lm_ms", "dt"),
    ("dt_own_C", "dt_own_ms", "PWV_a", -1, None, "C", "特徴点 自前      dt_own_ms", "dt"),
    ("dt_v1_A", "dt_v1_ms", "PWV_a", -1, "ok_v1", "A", "凍結版 2カーネル dt_v1_ms", "dt"),
    ("dt_v1_C", "dt_v1_ms", "PWV_a", -1, None, "C", "凍結版 2カーネル dt_v1_ms", "dt"),
    ("dt_v2_C", "dt_v2_ms", "PWV_a", -1, None, "C", "第2版 歪みガウス dt_v2_ms", "dt"),
    ("dt_v2g_A", "dt_v2g_ms", "PWV_a", -1, "ok_v2g", "A", "第2版 ガンマ    dt_v2g_ms", "dt"),
    ("dt_v2g_C", "dt_v2g_ms", "PWV_a", -1, None, "C", "第2版 ガンマ    dt_v2g_ms", "dt"),
    ("ri_lm_C", "digital_ri", "pvr", +1, None, "C", "特徴点 同梱      digital_ri", "ri"),
    ("ri_v1_A", "ri_v1", "pvr", +1, "ok_v1", "A", "凍結版 2カーネル ri_v1", "ri"),
    ("ri_v1_C", "ri_v1", "pvr", +1, None, "C", "凍結版 2カーネル ri_v1", "ri"),
    ("ri_v2_C", "ri_v2", "pvr", +1, None, "C", "第2版 歪みガウス ri_v2", "ri"),
    ("ri_v2g_A", "ri_v2g", "pvr", +1, "ok_v2g", "A", "第2版 ガンマ    ri_v2g", "ri"),
    ("ri_v2g_C", "ri_v2g", "pvr", +1, None, "C", "第2版 ガンマ    ri_v2g", "ri"),
    ("amb_C", "amb_amp1", "PWV_a", -1, None, "C", "早期振幅比      amb_amp1", "ref"),
]
GROUPS = [
    ("dt", "ΔT × 大動脈脈波伝播速度 PWV_a（予測の向き 負）"),
    ("ri", "RI × 末梢血管抵抗 pvr（予測の向き 正）"),
    ("ref", "参考: 早期振幅比 × 大動脈脈波伝播速度 PWV_a（予測の向き 負）"),
]

# 節4 で比べる組。(キー, 分解の列, 特徴点の列, 採否の列, 許容差, 単位の表示, 小数桁, 表示名)
AGREE = [
    ("v1_dt", "dt_v1_ms", "dt_lm_ms", "ok_v1", 5.0, " ms", 1,
     "凍結版 dt_v1_ms − 特徴点 同梱 dt_lm_ms（A 段）"),
    ("v1_ri", "ri_v1", "digital_ri", "ok_v1", 0.01, "", 4,
     "凍結版 ri_v1 − 特徴点 同梱 digital_ri（A 段）"),
    ("v2g_dt", "dt_v2g_ms", "dt_lm_ms", "ok_v2g", 5.0, " ms", 1,
     "第2版 ガンマ dt_v2g_ms − 特徴点 同梱 dt_lm_ms（A 段）"),
]

# 予測の規準（docstring の P1〜P5。2026-09-14 に、計算の前に固定した）。
PRED_RHO = M.CRIT_RHO       # 0.30。**参考として印字するだけで、合否の判定には使わない**
PRED_DT_MATCH_MS = 5.0      # P2 型1: ΔT の |差| の中央値がこれ未満
PRED_DT_MISS_MS = 20.0      # P2 型3: ΔT の |差| の中央値がこれ以上
PRED_RI_MATCH = 0.01        # P3 型1: RI の |差| の中央値がこれ未満
PRED_RI_MISS = 0.05         # P3 型3: RI の |差| の中央値がこれ以上
PRED_RHO_CLOSE = 0.05       # P3 型1: |ρ| の中央値が特徴点法とこれ以内で一致する
PRED_K4_MAX_AGES = 3        # P4 型4: 8 名以上の年齢層がこれ以下


# ---------------------------------------------------------------- 表示の部品
def _pad(s: str, w: int, right: bool = False) -> str:
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


def _pct(v: float, prec: int = 1) -> str:
    return "—" if not np.isfinite(v) else f"{100.0 * v:.{prec}f}%"


def _yn(b: bool) -> str:
    return "はい" if b else "いいえ"


# ---------------------------------------------------------------- 計算の部品
EMPTY = {"rows": [], "med_abs": float("nan"), "med": float("nan"), "n_ok": 0,
         "n_ages": 0, "min_n": 0, "max_n": 0, "n_tot": 0}


def _col(d: pd.DataFrame, c: str) -> np.ndarray:
    if c not in d.columns:
        return np.full(len(d), np.nan)
    return pd.to_numeric(d[c], errors="coerce").to_numpy(dtype=float)


def _stage(d: pd.DataFrame, ok_col: "str | None") -> pd.DataFrame:
    """A 段（その手法が自分で採用した例だけ）に絞る。ok_col が None なら C 段のまま。"""
    if ok_col is None:
        return d
    if ok_col not in d.columns:
        return d.iloc[0:0]
    return d[pd.to_numeric(d[ok_col], errors="coerce") == 1]


def rows_by_age(d: pd.DataFrame, x: str, y: str) -> list:
    """年齢層ごとの (年齢, ρ, n)。層は `age` の相異なる値（26番・20番と同じ）。

    ρ は 20番の `_spearman`（対応のある行だけ・1 層 MIN_PER_AGE 名以上）で計算する。
    20番の `_by_age` と同じ値になることは自己検査で確かめる。
    """
    out = []
    if "age" not in d.columns or len(d) == 0:
        return out
    for age, g in d.groupby("age", sort=True):
        r, n = M._spearman(_col(g, x), _col(g, y), min_n=MIN_PER_AGE)
        out.append((float(age), r, n))
    return out


def strat(d: pd.DataFrame, x: str, y: str, sign: int) -> dict:
    """年齢層内 Spearman の一式。中央値と向きの層数は 20番の `_judge` に任せる。"""
    if len(d) == 0 or x not in d.columns or y not in d.columns:
        return dict(EMPTY)
    rows = rows_by_age(d, x, y)
    fin = [(a, r, n) for a, r, n in rows if np.isfinite(r)]
    if not fin:
        out = dict(EMPTY)
        out["rows"] = rows
        return out
    j = M._judge(rows, sign)
    return {"rows": rows,
            "med_abs": j["med_abs"],
            "med": float(np.median([r for _a, r, _n in fin])),
            "n_ok": j["n_ok"],
            "n_ages": j["n_ages"],
            "min_n": min(n for _a, _r, n in fin),
            "max_n": max(n for _a, _r, n in fin),
            "n_tot": int(sum(n for _a, _r, n in fin))}


def diff_stats(d: pd.DataFrame, a_col: str, b_col: str, tol: float) -> dict:
    """a − b の中央値・四分位範囲・|差| の中央値・|差| が tol 以内の割合。"""
    a, b = _col(d, a_col), _col(d, b_col)
    g = np.isfinite(a) & np.isfinite(b)
    n = int(g.sum())
    if n == 0:
        return {"n": 0, "med": float("nan"), "q1": float("nan"), "q3": float("nan"),
                "med_abs": float("nan"), "frac": float("nan"), "tol": tol}
    v = a[g] - b[g]
    q1, q3 = (float(x) for x in np.percentile(v, [25, 75]))
    return {"n": n, "med": float(np.median(v)), "q1": q1, "q3": q3,
            "med_abs": float(np.median(np.abs(v))),
            "frac": float(np.mean(np.abs(v) <= tol)), "tol": tol}


def klass_of(d: pd.DataFrame) -> np.ndarray:
    return _col(d, KLASS_COL)


def subset(d: pd.DataFrame, k: int) -> pd.DataFrame:
    return d[klass_of(d) == float(k)]


def ages_with_min(d: pd.DataFrame, min_n: int = MIN_PER_AGE) -> list:
    """その部分集合で min_n 名以上いる年齢層（真値の欠測は見ない。人数だけ）。"""
    if "age" not in d.columns or len(d) == 0:
        return []
    c = pd.to_numeric(d["age"], errors="coerce").value_counts()
    return sorted(float(a) for a, n in c.items() if n >= min_n)


# ---------------------------------------------------------------- 節0
def section0(d: pd.DataFrame, src: str, allow_partial: bool) -> dict:
    """入力の確認と、全例・型を分けない既知値の照合。"""
    print("\n" + "-" * 100)
    print(f"0. 入力の確認と、全例・型を分けない既知値の照合（許容差 {TOL_KNOWN}）")
    print("-" * 100)
    ages = sorted(pd.to_numeric(d["age"], errors="coerce").dropna().unique().tolist())
    kl = klass_of(d)
    n_missing = int(np.sum(~np.isfinite(kl)))
    seen = sorted(set(int(v) for v in kl[np.isfinite(kl)]))
    print(f"  入力 {src}")
    print(f"  行数 {len(d)} 名（確認的解析を回した機械では 4,374 名）"
          f"・年齢層 {[int(a) for a in ages]}")
    print(f"  型の列 {KLASS_COL}: 値 {seen}"
          + (f"・欠測 {n_missing} 名" if n_missing else "・欠測なし"))
    need = [c for c, _t, _o in KNOWN] + [r[1] for r in ROWS] + ["age", KLASS_COL, "klass_v2"]
    miss = [c for c in dict.fromkeys(need) if c not in d.columns]
    if miss:
        print(f"  ★ 要る列が無い: {miss}")

    print("\n  " + _pad("指標 × 真値", 40) + _pad("段", 4, right=True)
          + _pad("論文2", 9, right=True) + _pad("この機械", 10, right=True)
          + _pad("差", 9, right=True) + _pad("層", 5, right=True) + "  照合")
    bad, cannot, got = [], [], {}
    for (col, tgt, ok_col), (known, sign, lab) in KNOWN.items():
        s = strat(_stage(d, ok_col), col, tgt, sign)
        got[(col, tgt)] = s
        v = s["med_abs"]
        stg = "A" if ok_col else "C"
        if allow_partial:
            mark = "照合なし（参考実行）"
        elif not np.isfinite(v):
            mark = "照合できない（8 名以上の年齢層が無い）"
            cannot.append(lab)
        elif abs(v - known) <= TOL_KNOWN:
            mark = "一致"
        else:
            mark = "★ずれ"
            bad.append(f"{lab}: 論文2 {known:.3f} に対し {v:.3f}")
        print("  " + _pad(lab, 40) + _pad(stg, 4, right=True) + f"{known:>9.3f}"
              + _f(v, 10) + _f(v - known if np.isfinite(v) else float("nan"), 9, sign=True)
              + _pad(s["n_ages"], 5, right=True) + "  " + mark)
    print("  出典（論文2 側）: 凍結版 0.223・0.207 は lab_log 2026-09-03 の表、")
    print("  特徴点 同梱 0.710・0.504 と早期振幅比 0.836 は 2026-09-09 の 26番の表。")
    print("  段 A は 26番の A 段（その手法が自分で採用した例だけ）、段 C は採否を無視した全例。")
    print("  照合は対応のある行（pairwise-complete）・年齢層内 Spearman の中央値 |ρ|。")

    state = 0
    if allow_partial:
        print("\n  参考実行（全例の表ではない）。照合を飛ばしたので、この先の数値は")
        print("  論文2 の続きとして読んではいけない。")
    elif bad:
        state = 2
        print("\n  ★ 入力が論文2 と違うので表を読んではいけない。")
        for b in bad:
            print(f"    {b}")
    elif cannot:
        state = 2
        print("\n  ★ 入力が論文2 と違うので表を読んではいけない"
              f"（{len(cannot)} 件が照合できない。1 層 {MIN_PER_AGE} 名に満たない）。")
        for c in cannot:
            print(f"    {c}")
    return {"state": state, "known": got, "bad": bad, "cannot": cannot,
            "ages": ages, "n_missing": n_missing}


# ---------------------------------------------------------------- 節1
def section1(d: pd.DataFrame) -> dict:
    """型の分布（年齢層 × 型）と、klass_own と klass_v2 の一致。"""
    print("\n" + "-" * 100)
    print("1. 型の分布（年齢層 × 型。型の列 klass_own）")
    print("-" * 100)
    kl = klass_of(d)
    age = _col(d, "age")
    ages = sorted(set(float(a) for a in age[np.isfinite(age)]))
    extra = sorted(set(int(v) for v in kl[np.isfinite(kl)]) - set(KLASSES))
    cols = list(KLASSES) + extra
    n_missing = int(np.sum(~np.isfinite(kl)))

    head = "  " + _pad("年齢", 8)
    for k in cols:
        head += _pad(f"型{k}", 16, right=True)
    if n_missing:
        head += _pad("欠測", 10, right=True)
    head += _pad("層の計", 9, right=True)
    print(head)

    cells, n_cells = {}, 0
    for a in ages:
        sel = age == a
        n_a = int(sel.sum())
        line = "  " + _pad(f"{int(a)} 歳", 8)
        for k in cols:
            n_k = int(np.sum(sel & (kl == float(k))))
            cells[(a, k)] = n_k
            n_cells += n_k
            line += _pad(f"{n_k} ({100.0 * n_k / n_a:.1f}%)" if n_a else "—", 16, right=True)
        if n_missing:
            n_m = int(np.sum(sel & ~np.isfinite(kl)))
            n_cells += n_m
            line += _pad(n_m, 10, right=True)
        line += _pad(n_a, 9, right=True)
        print(line)

    line = "  " + _pad("合計", 8)
    tot = {}
    for k in cols:
        tot[k] = int(np.sum(kl == float(k)))
        line += _pad(f"{tot[k]} ({100.0 * tot[k] / len(d):.1f}%)" if len(d) else "—",
                     16, right=True)
    if n_missing:
        line += _pad(n_missing, 10, right=True)
    line += _pad(len(d), 9, right=True)
    print(line)
    print("  括弧内はその年齢層に占める割合（合計の行だけは全体に占める割合）。")

    # 型1 の割合（P5 で使う）
    p1 = []
    for a in ages:
        n_a = int(np.sum(age == a))
        p1.append((a, cells.get((a, 1), 0) / n_a if n_a else float("nan")))
    print("  型1 の割合: " + "・".join(f"{int(a)}歳 {_pct(p)}" for a, p in p1))

    # klass_own と klass_v2 の一致
    kv = _col(d, "klass_v2")
    g = np.isfinite(kl) & np.isfinite(kv)
    agree = float(np.mean(kl[g] == kv[g])) if g.any() else float("nan")
    print(f"  klass_own と klass_v2 が一致: {int(np.sum(kl[g] == kv[g]))} / {int(g.sum())} "
          f"= {_pct(agree)}（両方が取れた行だけ）")
    return {"cells": cells, "cols": cols, "ages": ages, "tot": tot,
            "n_missing": n_missing, "n_cells": n_cells + 0, "p_klass1": p1,
            "agree_v2": agree}


# ---------------------------------------------------------------- 節2
def section2(d: pd.DataFrame) -> dict:
    """型ごとの採択率（その手法が自分で採用した割合）。"""
    print("\n" + "-" * 100)
    print("2. 型ごとの採択率（その手法が自分で採用した割合。A 段に残る割合）")
    print("-" * 100)
    oks = [("ok_v1", "凍結版 2カーネル"), ("ok_v2", "第2版 歪みガウス"),
           ("ok_v2g", "第2版 ガンマ")]
    print("  " + _pad("型", 42) + _pad("n", 8, right=True)
          + "".join(_pad(lab, 20, right=True) for _c, lab in oks))
    out = {}
    kl = klass_of(d)
    extra = sorted(set(int(v) for v in kl[np.isfinite(kl)]) - set(KLASSES))
    for k in list(KLASSES) + extra:
        g = subset(d, k)
        line = "  " + _pad(KLASS_LABEL.get(k, f"型{k}"), 42) + _pad(len(g), 8, right=True)
        for c, _lab in oks:
            v = _col(g, c)
            r = float(np.nanmean(v)) if len(g) and np.isfinite(v).any() else float("nan")
            out[(k, c)] = r
            line += _pad(_pct(r), 20, right=True)
        print(line)
    print("  第2版（歪みガウス・ガンマ）は型3 以降を規則で採用しない（型3 は代用点しか")
    print("  無く分解が同定できないので proxy_landmarks、型4・型5 は no_landmarks。pda2）。")
    print("  したがって型3 以降の第2版の採択率は 0 になる。そのまま印字する。")
    return out


# ---------------------------------------------------------------- 節3
def _row_line(lab: str, stg: str, s: dict, sign: int) -> str:
    ok = f"{s['n_ok']}/{s['n_ages']}" if s["n_ages"] else "—"
    rng = f"{s['min_n']}〜{s['max_n']}" if s["n_ages"] else "—"
    return ("    " + _pad(lab, 30) + _pad(stg, 4, right=True)
            + _f(s["med_abs"], 11) + _f(s["med"], 10, sign=True)
            + _pad(s["n_ages"], 7, right=True) + _pad(ok, 9, right=True)
            + _pad(rng, 14, right=True) + _pad(s["n_tot"] or "—", 9, right=True))


def _age_line(s: dict) -> str:
    if not s["rows"]:
        return "年齢層が取れない"
    return "・".join(f"{int(a)}歳 {_n(r, sign=True)}({n})" for a, r, n in s["rows"])


def section3(d: pd.DataFrame) -> dict:
    """本表。型ごとに、年齢層内 Spearman の中央値 |ρ| などを並べる。"""
    print("\n" + "-" * 100)
    print("3. 本表: 型ごとの年齢層内 Spearman（探索的・事後。判定は付けない）")
    print("-" * 100)
    print(f"  年齢層は `age` の相異なる値、1 層 {MIN_PER_AGE} 名以上の層だけ数える"
          f"（全 {N_AGES_FULL} 層）。")
    print("  「向きの層」は予測の向き（ΔT×PWV は負、RI×抵抗は正）に一致した層数／評価できた層数。")
    print(f"  参考: 26番の事前規準は中央値 |ρ| ≥ {PRED_RHO:.2f} かつ全層で予測の向き"
          "（20番の CRIT_RHO）。")
    print("  **この台本は成立・不成立を付けない。**事前規準による判定は 26番のものが有効で、")
    print("  事後の探索で上書きしない。")

    out, short = {}, {}
    kl = klass_of(d)
    extra = sorted(set(int(v) for v in kl[np.isfinite(kl)]) - set(KLASSES))
    for k in list(KLASSES) + extra:
        g = subset(d, k)
        print(f"\n  {KLASS_LABEL.get(k, f'型{k}')}  n = {len(g)} 名")
        if len(g) < MIN_PER_AGE:
            short[k] = len(g)
            print(f"    n 不足（{MIN_PER_AGE} 名未満なのでどの年齢層でも ρ を計算できない）")
            continue
        n_ages_pop = len(ages_with_min(g))
        print(f"    {MIN_PER_AGE} 名以上いる年齢層 {n_ages_pop} / {N_AGES_FULL}"
              f"（真値・指標の欠測を見ない人数だけの数）")
        for grp, title in GROUPS:
            rows = [r for r in ROWS if r[7] == grp]
            if not rows:
                continue
            print(f"    {title}")
            print("    " + _pad("指標", 30) + _pad("段", 4, right=True)
                  + _pad("|ρ|中央値", 11, right=True) + _pad("ρ中央値", 10, right=True)
                  + _pad("評価層", 7, right=True) + _pad("向きの層", 9, right=True)
                  + _pad("層のn", 14, right=True) + _pad("計n", 9, right=True))
            for key, col, tgt, sign, ok_col, stg, lab, _grp in rows:
                s = strat(_stage(g, ok_col), col, tgt, sign)
                out[(k, key)] = s
                print(_row_line(lab, stg, s, sign))
                if k in (1, 3):
                    print("      年齢層別 ρ(n): " + _age_line(s))
    if short:
        print(f"\n  n 不足の型: " + "・".join(f"型{k} {n} 名" for k, n in sorted(short.items())))
    print("\n  年齢層別の行は型1 と型3 についてだけ印字する（型4・型5 は層が揃わない）。")
    print("  出典: この台本（48番）が --csv の CSV から計算した値。")
    return {"s": out, "short": short}


# ---------------------------------------------------------------- 節4
def section4(d: pd.DataFrame) -> dict:
    """型ごとの一致（分解の成分が特徴点に載っているか）。"""
    print("\n" + "-" * 100)
    print("4. 型ごとの一致（分解法の ΔT・RI は特徴点法のそれと同じ値か）")
    print("-" * 100)
    print("  中央値 [四分位範囲]・|差| の中央値・|差| が許容差以内の割合。対応のある行だけ。")
    print("  同じ値になるなら、分解の第2成分は特徴点法が見ている拡張期側の点に載っている。")
    out = {}
    kl = klass_of(d)
    extra = sorted(set(int(v) for v in kl[np.isfinite(kl)]) - set(KLASSES))
    for k in list(KLASSES) + extra:
        g = subset(d, k)
        print(f"\n  {KLASS_LABEL.get(k, f'型{k}')}  n = {len(g)} 名")
        if len(g) == 0:
            print("    該当なし")
            continue
        for key, a_col, b_col, ok_col, tol, unit, prec, lab in AGREE:
            ga = _stage(g, ok_col)
            s = diff_stats(ga, a_col, b_col, tol)
            out[(k, key)] = s
            if s["n"] == 0:
                print(f"    {lab}: 対応のある行が無い（A 段 {len(ga)} 名）")
                continue
            tol_s = f"{tol:g}{unit}"
            print(f"    {lab}")
            print(f"      中央値 {_n(s['med'], prec, sign=True)}{unit} "
                  f"[IQR {_n(s['q1'], prec, sign=True)}{unit}〜"
                  f"{_n(s['q3'], prec, sign=True)}{unit}]"
                  f"・|差| 中央値 {_n(s['med_abs'], prec)}{unit}"
                  f"・|差| ≤ {tol_s} が {_pct(s['frac'])}"
                  f"（n = {s['n']}・A 段 {len(ga)} 名）")
    print("\n  出典: この台本（48番）が --csv の CSV から計算した値。")
    return out


# ---------------------------------------------------------------- 節5
def _ge(v: float, thr: float) -> bool:
    return bool(np.isfinite(v) and v >= thr)


def _lt(v: float, thr: float) -> bool:
    return bool(np.isfinite(v) and v < thr)


def section5(res1: dict, res3: dict, res4: dict, d: pd.DataFrame) -> dict:
    """予測との照合。予測は docstring に固定してある（計算の前に書いた）。"""
    print("\n" + "-" * 100)
    print("5. 予測との照合（予測は 2026-09-14 に、計算の前に固定した。docstring と同文）")
    print("-" * 100)
    print("  **当たっても外れても成立・不成立の判定は付けない。**事後・記述である。")
    s3, s4 = res3["s"], res4

    # 型の n が 8 名に満たないと節3・節4 にその型の行が無い（「n 不足」の 1 行だけ）。
    # 人数の欄は 0、ρ や差の欄は NaN を返して、照合の行を落とさずに「いいえ」にする。
    n_fields = ("n_ok", "n_ages", "min_n", "max_n", "n_tot", "n")

    def g3(k, key, field):
        s = s3.get((k, key))
        if s is None:
            return 0 if field in n_fields else float("nan")
        return s[field]

    def g4(k, key, field):
        s = s4.get((k, key))
        if s is None:
            return 0 if field in n_fields else float("nan")
        return s[field]

    def all_signed(k, key):
        s = s3.get((k, key))
        return bool(s and s["n_ages"] > 0 and s["n_ok"] == s["n_ages"])

    # (P1)
    print("\n  (P1) 特徴点法（同梱）の ΔT × 大動脈PWV は、型1 と型3 のどちらでも |ρ| の")
    print(f"       中央値が {PRED_RHO:.2f} 以上で、評価できた全層で負。")
    p1_parts = []
    for k in (1, 3):
        p1_parts.append(f"型{k} |ρ|中央値 {_n(g3(k, 'dt_lm_C', 'med_abs'))}"
                        f"・向きの層 {int(g3(k, 'dt_lm_C', 'n_ok'))}/"
                        f"{int(g3(k, 'dt_lm_C', 'n_ages'))}")
    p1 = all(_ge(g3(k, "dt_lm_C", "med_abs"), PRED_RHO) and all_signed(k, "dt_lm_C")
             for k in (1, 3))
    print(f"       実測: " + "、".join(p1_parts))
    print(f"       → {_yn(p1)}")

    # (P2)
    print(f"\n  (P2) 凍結版 ΔT（A 段）は、型1 では特徴点法（同梱）の ΔT との |差| の中央値が")
    print(f"       {PRED_DT_MATCH_MS:g} ms 未満で、大動脈PWV との |ρ| の中央値が"
          f" {PRED_RHO:.2f} 以上。型3 では |差| の")
    print(f"       中央値が {PRED_DT_MISS_MS:g} ms 以上で、|ρ| の中央値が {PRED_RHO:.2f} 未満。")
    p2_1 = (_lt(g4(1, "v1_dt", "med_abs"), PRED_DT_MATCH_MS)
            and _ge(g3(1, "dt_v1_A", "med_abs"), PRED_RHO))
    p2_3 = (_ge(g4(3, "v1_dt", "med_abs"), PRED_DT_MISS_MS)
            and _lt(g3(3, "dt_v1_A", "med_abs"), PRED_RHO))
    p2 = p2_1 and p2_3
    print(f"       実測: 型1 |差|中央値 {_n(g4(1, 'v1_dt', 'med_abs'), 1)} ms"
          f"・|ρ|中央値 {_n(g3(1, 'dt_v1_A', 'med_abs'))} → {_yn(p2_1)}")
    print(f"             型3 |差|中央値 {_n(g4(3, 'v1_dt', 'med_abs'), 1)} ms"
          f"・|ρ|中央値 {_n(g3(3, 'dt_v1_A', 'med_abs'))} → {_yn(p2_3)}")
    print(f"       → {_yn(p2)}")

    # (P3)
    print(f"\n  (P3) 凍結版 RI（A 段）は、型1 では特徴点法（同梱）の RI との |差| の中央値が")
    print(f"       {PRED_RI_MATCH:g} 未満で、末梢血管抵抗との |ρ| の中央値が特徴点法の型1 の値と")
    print(f"       {PRED_RHO_CLOSE:g} 以内で一致する。型3 では一致しない"
          f"（|差| の中央値 {PRED_RI_MISS:g} 以上）。")
    gap1 = abs(g3(1, "ri_v1_A", "med_abs") - g3(1, "ri_lm_C", "med_abs"))
    p3_1 = (_lt(g4(1, "v1_ri", "med_abs"), PRED_RI_MATCH)
            and bool(np.isfinite(gap1) and gap1 <= PRED_RHO_CLOSE))
    p3_3 = _ge(g4(3, "v1_ri", "med_abs"), PRED_RI_MISS)
    p3 = p3_1 and p3_3
    print(f"       実測: 型1 |差|中央値 {_n(g4(1, 'v1_ri', 'med_abs'), 4)}"
          f"・|ρ|中央値 凍結版 {_n(g3(1, 'ri_v1_A', 'med_abs'))} / "
          f"特徴点 {_n(g3(1, 'ri_lm_C', 'med_abs'))}（差 {_n(gap1)}） → {_yn(p3_1)}")
    print(f"             型3 |差|中央値 {_n(g4(3, 'v1_ri', 'med_abs'), 4)} → {_yn(p3_3)}")
    print(f"       → {_yn(p3)}")

    # (P4)
    print(f"\n  (P4) 型4 は {MIN_PER_AGE} 名以上の年齢層が {PRED_K4_MAX_AGES} 層以下で、")
    print("       |ρ| の中央値は出ても層数が判定に足りない。")
    g4_sub = subset(d, 4)
    n4_ages = len(ages_with_min(g4_sub))
    p4 = n4_ages <= PRED_K4_MAX_AGES
    print(f"       実測: 型4 は {len(g4_sub)} 名・{MIN_PER_AGE} 名以上の年齢層 {n4_ages} 層"
          f"（ΔT 特徴点 同梱 の評価できた層 {int(g3(4, 'dt_lm_C', 'n_ages'))} 層・"
          f"|ρ|中央値 {_n(g3(4, 'dt_lm_C', 'med_abs'))}）")
    print(f"       → {_yn(p4)}")

    # (P5)
    print("\n  (P5) 型1 の割合は年齢層とともに単調に減る（25 歳層で最大、75 歳層で最小）。")
    ps = [p for _a, p in res1["p_klass1"]]
    p5 = (len(ps) >= 2 and all(np.isfinite(p) for p in ps)
          and all(ps[i] > ps[i + 1] for i in range(len(ps) - 1)))
    print("       実測: " + "・".join(f"{int(a)}歳 {_pct(p)}" for a, p in res1["p_klass1"]))
    print(f"       → {_yn(p5)}")

    hit = sum(int(x) for x in (p1, p2, p3, p4, p5))
    print(f"\n  まとめ: 予測 5 条のうち「はい」は {hit} 条。")
    print("  **この節は事後の探索であり、論文2 の事前規準による判定（26番）は動かない。**")
    return {"P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5, "hit": hit}


# ---------------------------------------------------------------- 節6
def section6(d: pd.DataFrame, src: str) -> None:
    print("\n" + "-" * 100)
    print("6. 出典")
    print("-" * 100)
    print(f"  入力 {src}（26番 `26_pwdb_compare.py` の出力）")
    print("  年齢層内 Spearman の規約は 20番 `20_pwdb_validity.py` の `_spearman`・`_judge`")
    print(f"  をそのまま使う（1 層 {MIN_PER_AGE} 名以上・層は `age` の相異なる値）。")
    print(f"  出典: analysis/scripts/48_pwdb_by_waveform_type.py / {len(d)} 名"
          f"・型の列 {KLASS_COL}")


# ---------------------------------------------------------------- まとめ
def report(d: pd.DataFrame, src: str, allow_partial: bool = False) -> tuple:
    """全節を印字する。返り値は (終了コード, 計算した値の辞書)。"""
    print("\n" + "=" * 100)
    print("48番 探索的（事後）: 波形の型ごとに ΔT・RI は真値とどれだけ関連するか（PWDB）")
    print("=" * 100)
    print("  論文2・探索的（事後）。**判定（成立・不成立）は付けない。**事前規準による")
    print("  判定は 26番のものが有効で、この台本の出力は事後の記述である。")
    out = {}
    r0 = section0(d, src, allow_partial)
    out["s0"] = r0
    if r0["state"] != 0:
        print("\n  照合が外れたので、型ごとの表は印字しない。"
              "入力を確かめるか、参考実行なら --allow-partial を付ける。")
        section6(d, src)
        return r0["state"], out
    out["s1"] = section1(d)
    out["s2"] = section2(d)
    out["s3"] = section3(d)
    out["s4"] = section4(d)
    out["s5"] = section5(out["s1"], out["s3"], out["s4"], d)
    section6(d, src)
    return 0, out


# ---------------------------------------------------------------- 自己検査
# 合成データの仕込み（節 `--selftest`）。型1 は分解が特徴点に載り、型3 は載らない。
N_PER_AGE_SYN = 660                      # 6 層で 3,960 名（4,000 名程度）
AGES_SYN = (25, 35, 45, 55, 65, 75)
P_KLASS1_SYN = (0.95, 0.90, 0.82, 0.70, 0.55, 0.40)   # 単調に減る（P5 の仕込み）
N_KLASS4_SYN = {55: 6, 65: 8, 75: 10}    # 型4 は 55 歳以上の層にだけ、各 6〜10 名
PWV_BASE_SYN = (4.0, 6.0, 7.3, 8.3, 9.2, 10.3)
DT_A_SYN, DT_B_SYN, DT_S_SYN = 400.0, 20.0, 24.0      # ΔT = A − B × PWV + 雑音
RI_A_SYN, RI_B_SYN, RI_S_SYN = 0.35, 0.08, 0.08       # RI = A + B × z(抵抗) + 雑音
V1_JIT_MS, V1_JIT_RI = 0.5, 0.002        # 型1 の分解は特徴点に載る（1 ms 未満の雑音）


def synth(seed: int = 0) -> pd.DataFrame:
    """合成データ。型1 では分解が特徴点に載り、型3・型4 では真値と無関係になる。"""
    rng = np.random.default_rng(seed)
    frames = []
    subj = 0
    for k, age in enumerate(AGES_SYN):
        n = N_PER_AGE_SYN
        n4 = N_KLASS4_SYN.get(age, 0)
        n1 = int(round(P_KLASS1_SYN[k] * (n - n4)))
        n3 = n - n4 - n1
        klass = np.concatenate([np.full(n1, 1.0), np.full(n3, 3.0), np.full(n4, 4.0)])
        z_pwv = rng.normal(0, 1, n)
        z_res = rng.normal(0, 1, n)
        pwv = PWV_BASE_SYN[k] + 1.2 * z_pwv
        # 特徴点法（同梱）は全型で大動脈PWV を追う（負の相関）
        dt_lm = DT_A_SYN - DT_B_SYN * pwv + rng.normal(0, DT_S_SYN, n)
        dt_own = dt_lm + rng.normal(0, 5.0, n)
        dt_own = np.where(klass == 4.0, np.nan, dt_own)      # 型4 は特徴点が取れない
        digital_ri = RI_A_SYN + RI_B_SYN * z_res + rng.normal(0, RI_S_SYN, n)
        # 凍結版: 型1 は特徴点に載る。型3・型4 は真値と無関係な値になる
        on = klass == 1.0
        dt_v1 = np.where(on, dt_lm + rng.normal(0, V1_JIT_MS, n),
                         np.where(klass == 3.0, rng.normal(165.0, 25.0, n),
                                  rng.normal(60.0, 20.0, n)))
        ri_v1 = np.where(on, digital_ri + rng.normal(0, V1_JIT_RI, n),
                         np.where(klass == 3.0, rng.normal(0.25, 0.10, n),
                                  rng.normal(0.05, 0.03, n)))
        ok_v1 = np.where(on, rng.random(n) < 0.95,
                         np.where(klass == 3.0, rng.random(n) < 0.92,
                                  rng.random(n) < 0.50)).astype(int)
        # 第2版は規則で型1 しか採らない
        ok_v2 = np.where(on, rng.random(n) < 0.62, False).astype(int)
        ok_v2g = np.where(on, rng.random(n) < 0.40, False).astype(int)
        dt_v2 = dt_v1 + rng.normal(0, 2.0, n)
        ri_v2 = ri_v1 - 0.007 + rng.normal(0, 0.004, n)
        dt_v2g = dt_v1 + 20.0 + rng.normal(0, 8.0, n)
        ri_v2g = 0.75 * ri_v1 + rng.normal(0, 0.01, n)
        klass_v2 = np.where(rng.random(n) < 0.03, 5.0, klass)   # 3% だけ食い違わせる
        frames.append(pd.DataFrame({
            "subj_no": np.arange(subj + 1, subj + n + 1),
            "age": float(age),
            "PWV_a": pwv,
            "pvr": 1.5e8 * np.exp(0.3 * z_res),
            KLASS_COL: klass,
            "klass_v2": klass_v2,
            "dt_lm_ms": dt_lm,
            "dt_own_ms": dt_own,
            "digital_ri": digital_ri,
            "dt_v1_ms": dt_v1, "ri_v1": ri_v1, "ok_v1": ok_v1,
            "dt_v2_ms": dt_v2, "ri_v2": ri_v2, "ok_v2": ok_v2,
            "dt_v2g_ms": dt_v2g, "ri_v2g": ri_v2g, "ok_v2g": ok_v2g,
            "amb_amp1": 1.0 - 0.01 * pwv + rng.normal(0, 0.004, n)}))
        subj += n
    return pd.concat(frames, ignore_index=True)


def selftest() -> int:
    n_fail = 0

    def rep(name, cond, detail=""):
        nonlocal n_fail
        cond = bool(cond)
        if not cond:
            n_fail += 1
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))

    print("48番 自己検査（合成データだけで走る。CSV もネットワークも要らない）")

    # --- 規約を 20番と共有しているか（自前で書き直していない）
    import inspect
    rep("判定の規約を 20番と共有している（_spearman・_judge・層の人数）",
        M.CRIT_RHO == 0.30
        and inspect.signature(M._by_age).parameters["min_n"].default == MIN_PER_AGE,
        f"CRIT_RHO {M.CRIT_RHO} / 層の人数 {MIN_PER_AGE}")

    d = synth(seed=0)
    n_exp = N_PER_AGE_SYN * len(AGES_SYN)
    rep("合成データを作れる（6 年齢層・型1/3/4）",
        len(d) == n_exp and d["age"].nunique() == len(AGES_SYN)
        and sorted(set(int(v) for v in d[KLASS_COL])) == [1, 3, 4],
        f"{len(d)} 名・型 {sorted(d[KLASS_COL].value_counts().to_dict().items())}")

    # 年齢層ごとの ρ が 20番の _by_age と一致するか（写し取っていないことの確認）
    mine = [r for _a, r, _n in rows_by_age(d, "dt_lm_ms", "PWV_a")]
    theirs = [r for _a, r, _n in M._by_age(d, "dt_lm_ms", "PWV_a", min_n=MIN_PER_AGE)]
    rep("年齢層ごとの ρ が 20番の _by_age と一致する",
        np.allclose(mine, theirs, equal_nan=True),
        f"最大差 {np.nanmax(np.abs(np.array(mine) - np.array(theirs))):.2e}")

    # --- 合成データで全節を回す（参考実行。KNOWN は合わない）
    buf = io.StringIO()
    with redirect_stdout(buf):
        code_p, out = report(d, "合成データ（自己検査）", allow_partial=True)
    txt = buf.getvalue()
    rep("--allow-partial なら合成データでも最後まで印字して終わる",
        code_p == 0 and "6. 出典" in txt and "参考実行（全例の表ではない）" in txt,
        f"終了コード {code_p}・{len(txt)} 文字")

    buf2 = io.StringIO()
    with redirect_stdout(buf2):
        code_s, out_s = report(d, "合成データ（自己検査）", allow_partial=False)
    rep("KNOWN の照合が外れた表では終了コード 2 になる",
        code_s == 2 and "表を読んではいけない" in buf2.getvalue()
        and "s3" not in out_s,
        f"終了コード {code_s}・ずれ {len(out_s['s0']['bad'])} 件")

    s3, s4, s1 = out["s3"]["s"], out["s4"], out["s1"]

    # (a) 節3 型1: 凍結版も特徴点も 0.30 以上
    v1_1 = s3[(1, "dt_v1_A")]["med_abs"]
    lm_1 = s3[(1, "dt_lm_C")]["med_abs"]
    rep("(a) 節3 型1 で凍結版と特徴点の |ρ| がどちらも 0.30 以上",
        v1_1 >= 0.30 and lm_1 >= 0.30,
        f"凍結版 {v1_1:.3f}・特徴点 {lm_1:.3f}")

    # (b) 節3 型3: 凍結版は 0.30 未満、特徴点は 0.30 以上
    v1_3 = s3[(3, "dt_v1_A")]["med_abs"]
    lm_3 = s3[(3, "dt_lm_C")]["med_abs"]
    rep("(b) 節3 型3 で凍結版が 0.30 未満・特徴点が 0.30 以上",
        v1_3 < 0.30 and lm_3 >= 0.30,
        f"凍結版 {v1_3:.3f}・特徴点 {lm_3:.3f}")

    # (c) 節3 型4: 評価できた層数が 3 以下
    n4 = s3[(4, "dt_lm_C")]["n_ages"]
    rep("(c) 節3 型4 の評価できた層数が 3 以下", n4 <= 3,
        f"{n4} 層（型4 は {int((d[KLASS_COL] == 4).sum())} 名）")

    # (d) 節4 の |差| の中央値
    dd1 = s4[(1, "v1_dt")]["med_abs"]
    dd3 = s4[(3, "v1_dt")]["med_abs"]
    rep("(d) 節4 の型1 の |差| 中央値が 5 ms 未満・型3 が 20 ms 以上",
        dd1 < 5.0 and dd3 >= 20.0, f"型1 {dd1:.2f} ms・型3 {dd3:.1f} ms")
    ri1 = s4[(1, "v1_ri")]["med_abs"]
    ri3 = s4[(3, "v1_ri")]["med_abs"]
    rep("(d) 節4 の型1 の RI の |差| 中央値が 0.01 未満・型3 が 0.05 以上",
        ri1 < 0.01 and ri3 >= 0.05, f"型1 {ri1:.4f}・型3 {ri3:.4f}")

    # (e) 節5 の P1〜P5 がすべて「はい」
    p = out["s5"]
    rep("(e) 節5 の P1〜P5 がすべて「はい」", p["hit"] == 5,
        "・".join(f"{k} {_yn(p[k])}" for k in ("P1", "P2", "P3", "P4", "P5")))

    # (f) 年齢層 × 型の人数表の合計が総数に一致する
    rep("(f) 年齢層 × 型の人数表の合計が総数に一致する",
        s1["n_cells"] == len(d) and sum(s1["tot"].values()) == len(d),
        f"表の合計 {s1['n_cells']}・型ごとの合計 {sum(s1['tot'].values())}・総数 {len(d)}")

    # (g) 段の絞り込みが効いているか（ok_v1 = 0 の行に別の関係を仕込むと A 段は無視する）
    dg = synth(seed=3).copy()
    bad = (_col(dg, "ok_v1") == 0) & (klass_of(dg) == 1.0)
    dg.loc[bad, "dt_v1_ms"] = 900.0 - dg.loc[bad, "dt_lm_ms"].to_numpy()
    a_stage = strat(_stage(subset(dg, 1), "ok_v1"), "dt_v1_ms", "PWV_a", -1)["med_abs"]
    c_stage = strat(subset(dg, 1), "dt_v1_ms", "PWV_a", -1)["med_abs"]
    rep("(g) A 段（ok_v1 == 1）は ok_v1 = 0 に仕込んだ別の関係を無視する",
        np.isfinite(a_stage) and abs(a_stage - s3[(1, "dt_v1_A")]["med_abs"]) < 0.05,
        f"A 段 {a_stage:.3f}・仕込み前 {s3[(1, 'dt_v1_A')]['med_abs']:.3f}"
        f"・C 段 {c_stage:.3f}（仕込んだ行 {int(bad.sum())} 名）")

    # (h) 8 名に満たない型は「n 不足」の 1 行だけになる
    d5 = synth(seed=0).copy()
    idx = d5.index[:5]
    d5.loc[idx, KLASS_COL] = 5.0
    buf3 = io.StringIO()
    with redirect_stdout(buf3):
        _c, out5 = report(d5, "合成データ（型5 を 5 名）", allow_partial=True)
    rep("(h) 8 名未満の型は「n 不足」の 1 行だけになる",
        out5["s3"]["short"].get(5) == 5 and (5, "dt_lm_C") not in out5["s3"]["s"]
        and "n 不足" in buf3.getvalue(),
        f"型5 {out5['s3']['short'].get(5)} 名")

    # (i) 部品そのものの検算
    dz = pd.DataFrame({"age": [25.0] * 10, "x": np.arange(10.0),
                       "y": -np.arange(10.0), "ok": [1] * 5 + [0] * 5})
    sz = strat(dz, "x", "y", -1)
    rep("(i) 完全な負の関係で ρ = −1・向きの層 1/1",
        abs(sz["med"] + 1.0) < 1e-9 and sz["n_ok"] == 1 and sz["n_ages"] == 1,
        f"ρ {sz['med']:.3f}")
    rep("(i) A 段の絞り込みが行数を減らす", len(_stage(dz, "ok")) == 5)
    rep("(i) 採否の列が無いときの A 段は空になる（黙って C 段に落ちない）",
        len(_stage(dz, "ok_v2g")) == 0)
    ds = diff_stats(pd.DataFrame({"a": [1.0, 2.0, 3.0, 100.0], "b": [1.0, 1.0, 1.0, 1.0]}),
                    "a", "b", 5.0)
    rep("(i) 差の中央値・|差| の中央値・許容差以内の割合",
        ds["n"] == 4 and abs(ds["med"] - 1.5) < 1e-9 and abs(ds["med_abs"] - 1.5) < 1e-9
        and abs(ds["frac"] - 0.75) < 1e-9, f"中央値 {ds['med']}・割合 {ds['frac']}")
    rep("(i) 対応のある行が無ければ落ちずに n = 0 を返す",
        diff_stats(pd.DataFrame({"a": [np.nan], "b": [1.0]}), "a", "b", 5.0)["n"] == 0)
    rep("(i) 列が無くても落ちない（空の一式を返す）",
        strat(dz, "no_such_col", "y", -1)["n_ages"] == 0)

    # (j) 同じ乱数種なら出力が一字一句同じ
    def render(seed):
        b = io.StringIO()
        with redirect_stdout(b):
            report(synth(seed=seed), "合成データ", allow_partial=True)
        return b.getvalue()

    t0, t0b, t1 = render(1), render(1), render(2)
    rep("(j) 同じ乱数種なら出力が同一", t0 == t0b, f"{len(t0)} 文字")
    rep("(j) 乱数種を変えれば値は変わる（比較が効いている）", t0 != t1)

    # --- 既定の CSV があれば、実データ側の道筋も走らせる（動くことの確認だけ）。
    #     この環境の複製は 24 行の抜粋なので、数値は読めない。CSV が無い機械でも通る。
    print("\n  --- 既定の CSV で報告の道筋を走らせる（動くことの確認だけ）---")
    if DEFAULT_CSV.exists():
        d_real = pd.read_csv(DEFAULT_CSV)
        b4 = io.StringIO()
        with redirect_stdout(b4):
            code_r, out_r = report(d_real, str(DEFAULT_CSV), allow_partial=True)
        t_real = b4.getvalue()
        rep("既定の CSV で --allow-partial の報告が例外なく最後まで印字される",
            code_r == 0 and "6. 出典" in t_real and "参考実行（全例の表ではない）" in t_real,
            f"{len(d_real)} 行・終了コード {code_r}・{len(t_real)} 文字")
        b5 = io.StringIO()
        with redirect_stdout(b5):
            code_n, _o = report(d_real, str(DEFAULT_CSV), allow_partial=False)
        rep("既定の CSV は --allow-partial 無しでは終了コード 2 で止まる",
            code_n == 2, f"終了コード {code_n}")
        if len(d_real) < 100:
            short = out_r["s3"]["short"]
            no_age = all(s["n_ages"] == 0 for s in out_r["s3"]["s"].values())
            rep("層の人数が足りないことが表に出る（評価層 0・n 不足）",
                no_age and bool(short),
                f"評価できた層が 0 の行 {len(out_r['s3']['s'])} 本・"
                f"n 不足の型 {sorted(short.items())}")
            print(f"  ★ この機械の {DEFAULT_CSV.name} は {len(d_real)} 行"
                  f"（1 層 {len(d_real) // N_AGES_FULL} 名）の抜粋である。")
            print("  ★ **ここから出る数値は読んではいけない。**確認的解析の機械の"
                  " 4,374 行で走らせること。")
    else:
        rep("既定の CSV が無い機械でも自己検査は通る", True, f"{DEFAULT_CSV} が無い")

    print("\n" + ("自己検証: 通過" if n_fail == 0 else f"自己検証: 失敗 {n_fail} 件"))
    return 0 if n_fail == 0 else 1


# ---------------------------------------------------------------- 入口
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=str, default=str(DEFAULT_CSV),
                    help="26番の出力（既定 data/pwdb/pwdb_compare.csv）")
    ap.add_argument("--allow-partial", action="store_true",
                    help="既知値の照合を飛ばして最後まで印字する（参考実行。数値は読めない）")
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
    miss = [c for c in ("age", KLASS_COL, "PWV_a", "pvr") if c not in d.columns]
    if miss:
        print(f"\n{p} に要る列が無い: {miss}")
        sys.exit(2)
    code, _out = report(d, str(p), allow_partial=args.allow_partial)
    sys.exit(code)


if __name__ == "__main__":
    main()

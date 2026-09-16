#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【探索・事後】論文2: 分解の第2成分は真の後進波か、弱点は分解か PPG という量か（PWDB）

なぜこの台本が要るか（lab_log 追記148 の W2・W3、追記149）
--------------------------------------------------------
論文2 は、凍結版の分解法（指尖 PPG に歪みガウス 2 成分を当てる）が真の大動脈脈波伝播速度を
特徴点法よりはるかに追えないことを示した（年齢層内 Spearman 0.223 対 0.710、4,374 名）。
だがこれまでの検査は**すべて間接**である。分解が返す ΔT・RI と、真の血行動態量との順位相関を
見ているだけで、次の 2 つは一度も直接には問われていない。

  W2  第2成分は本当に真の後進波か
      PWDB は部位ごとの圧 P(t) と流速 U(t) を配布している。線形の波の分離を使えば、
      その部位の**真の前進波・後進波**が作れる。順位相関ではなくミリ秒で突き合わせられる。

  W3  弱点は分解の側か、PPG が圧ではないことの側か
      PWDB の指尖 PPG は末梢 Windkessel の容積である（Charlton 2019 式 A1）。
      圧・流速を低域通過して裾を長くした量なので、前進波の形からしてすでに圧とは違う。
      **同じ凍結版の分解を指尖の圧波形に当てて** PPG と比べ、圧では成り立つのに PPG では
      成り立たないなら、弱点は分解ではなく PPG という量への変換にある。そのときは
      論文2 の主張を「分解の作り方に固有」から「PPG に当てたときの分解に固有」へ狭める。

事前に登録した予測は無い
------------------------
**この台本は探索・事後であり、26番（`26_pwdb_compare.py`）の事前規準による判定は動かさない。**
予測を登録していないので、成立・不成立の判定は下さない。すべての表の見出しにこの注記を出す。

波の分離の約束（実行前にここに固定する）
--------------------------------------
  対象の拍   26番と同じ（20番の `load_pwdb` → `beat_of`。拍長 60/HR から標本化周波数を復元）。
             同じ被験者の PPG・圧・流速の 3 行を同じやり方で末尾の詰め物だけ落として使う。
  基線       その拍の最小値を引く。`dP = P − min(P)`、`dU = U − min(U)`。
             **文献の標準は拡張期の値を引くことである。**PWDB の拍は立ち上がりで切り出されて
             いるので拡張期の値と拍内最小値はほぼ一致するが、流速は収縮期後期に最小になる拍が
             あり、そこでは両者は一致しない。ここでは拍内最小値を採る（下の「判断が要った点」）。
  ρc 主      収縮期初期の P–U ループの傾き。立ち上がりの足から dU/dt が最大になる時刻までの
             区間で、`dP` を `dU` に**原点を通して**回帰する（ρc = Σ dP·dU / Σ dU²）。
             後進波がまだ届いていない区間なので P と U は比例する、という標準の仮定による。
  ρc 検      二乗和法（Davies 2006）。`ρc = √(Σ(dP−平均)² / Σ(dU−平均)²)` を拍全体で計算する。
             **指標には主を使い、検は列として並べて、選び方でどれだけ変わるかを読ませる。**
  分離       `P_f = (dP + ρc·dU)/2`、`P_b = (dP − ρc·dU)/2`（Westerhof 1972）。
  真の指標   `ΔT_true = t_peak(P_b) − t_peak(P_f)` [ms]、`RI_true = max(P_b)/max(P_f)`。
             `P_b` のピークが拍の最初または最後の標本にある、または `max(P_b) ≤ 0` のときは
             **評価できない**として数え、その被験者の真の指標は欠測にする。
             これに加えて、`max(P_b)` が `max(P_f)` の 1e-6 倍以下の拍も評価できないとする
             （後進波がまったく無い拍では P_b が丸め誤差の大きさになり、山の位置が端数で
             決まってしまうため。生理的な規準ではなく数値の守り。`EPS_PB_REL`）。
  単位       ρc の単位は（配布物の圧の単位）/（配布物の流速の単位）である。ΔT_true は時刻の差、
             RI_true は圧どうしの比なので、どちらもこの単位に依らない。

計算するもの（被験者ごと）
--------------------------
  1  ρc 主・ρc 検と、その比
  2  真の前進波・後進波と ΔT_true・RI_true（評価できない被験者の数も数える）
  3  凍結版の分解を**指尖 PPG** に当てた ΔT・RI・採否（26番と同じ `pda.fit_beat`）
  4  凍結版の分解を**指尖の圧波形**に当てた ΔT・RI・採否（同じ関数・同じ引数）
     `fit_beat` は内部で最小値を引いて最大値で割るので、圧をそのまま渡せば PPG と同じ正規化になる
  5  波形の型 `klass_own`（26番と同じ `pda2.preprocess` → `find_landmarks`）
  6  Charlton 同梱の特徴点 ΔT・RI（23番の `load`）

表
--
  D0  検算: 3 の列が 26番の `dt_v1_ms`・`ri_v1`・`ok_v1`・`klass_own` と一致するか（`--csv`）
  D1  ρc の分布（年齢層別。主・検・比）
  D2  真の後進波の指標の分布（波形の型 × 年齢層。評価できない数も）
  D3  W2 第2成分は真の後進波に一致するか（差の中央値・|差| の中央値・まとめた順位相関）
  D4  W3 圧波形に当てるとどうなるか（年齢層内の順位相関。PPG・圧・特徴点を並べる）
  D5  読み（3 つの問いと、それに関わる数値。結論は書かない）

段（CLAUDE.md 節3。段を使う表の直前に毎回 1 行で出す）
  A 段  その手法が自分で採用した被験者だけ（`ok == 1`）
  C 段  採否を無視した全員
  **B 段はこの台本には無い**（比べる手法の採否がそろう部分集合を作らない）。

使い方
------
    python3 scripts/51_pwdb_wave_separation.py --pwdb ~/pwdb --jobs 8
    python3 scripts/51_pwdb_wave_separation.py --pwdb ~/pwdb --limit 600 --jobs 4
    python3 scripts/51_pwdb_wave_separation.py --pwdb ~/pwdb --csv data/pwdb/pwdb_compare.csv
    python3 scripts/51_pwdb_wave_separation.py --selftest

配布物に指尖の圧・流速が無いときは、22番（`22_pwdb_fetch.py`）で取り出す。22番の取り出しの
規則に `*digital*_p.csv`・`*digital*_u.csv`・`*digital*_a.csv` を足してある。

被験者ごとの計算は `data/pwdb/51_wave_sep.csv` に記録し、次の実行では当てはめ直さない
（`--limit` のときは `51_wave_sep_limitN.csv`。`--no-resume` で全員当てはめ直す）。
結果は print するので、残すときは tee で `docs/research/results/51_wave_separation.txt` に落とす。

終了コード 0 = 通常、2 = `--pwdb` が無い・配布物に必要なファイルが無い。

出典
----
Charlton P.H. et al. Modelling arterial pulse waves in healthy ageing.
Am J Physiol Heart Circ Physiol 2019. doi:10.5281/zenodo.3275625
Westerhof N. et al. Forward and backward waves in the arterial system.
Cardiovasc Res 1972;6:648-56.（P_f・P_b の分離）
Davies J.E. et al. Use of simultaneous pressure and velocity measurements to estimate
arterial wave speed at a single site in humans. Am J Physiol 2006;290:H878-85.（二乗和法）
"""
from __future__ import annotations

import argparse
import fnmatch
import importlib.util
import sys
import unicodedata
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import pda2                            # noqa: E402  波形の型（26番と同じ手順）
from src.pda import component_peak, fit_beat, skew_gaussian   # noqa: E402  凍結版の分解
from src.indices import si_ri_from_fit          # noqa: E402  ΔT・RI の取り出し方も凍結版


def _load(stem: str, name: str):
    """数字始まりの台本を名前で読み込む（import 文では書けない）。26番・50番と同じ手口。"""
    p = Path(__file__).resolve().parent / stem
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# 読み込み・順位相関・判定の約束は 20番のものをそのまま使う（自前で書き直さない）
M = _load("20_pwdb_validity.py", "m20")

DATA = ROOT / "data"
OUT = DATA / "pwdb"
DEFAULT_CSV = OUT / "pwdb_compare.csv"      # 26番の出力（D0 の検算に使う）
CACHE_NAME = "51_wave_sep.csv"

MIN_PER_AGE = 8            # 1 年齢層に要る人数。20番 `_by_age` の既定・26番・50番と同じ
MIN_N_POOL = 20            # まとめた順位相関に要る人数。20番 `_spearman` の既定・26番 MIN_N と同じ
PROGRESS_EVERY = 200       # 進み具合を印字する間隔 [名]（50番 節C と同じ）
CKPT_EVERY = 400           # 途中の記録を書く間隔 [名]（同上）
KLASSES = (1, 3, 4)        # 表で分ける波形の型（これに「全」を足す）
SIGN_DT = -1               # ΔT × 大動脈脈波伝播速度 の予測の向き（26番・48番・50番と同じ）
SIGN_RI = +1               # RI × 末梢血管抵抗 の予測の向き（同上）
COL_PWV = "PWV_a"          # 大動脈脈波伝播速度（真値）
COL_PVR = "pvr"            # 末梢血管抵抗（真値）
COL_LM_DT = "dt_lm_ms"     # 特徴点法の ΔT（Charlton 同梱）
COL_LM_RI = "digital_ri"   # 特徴点法の RI（同梱）
KLASS_COL = "klass_own"
KLASS_LABEL = {1: "型1 明瞭な重複切痕と拡張期ピーク（極値）",
               3: "型3 極値は無いが下降の緩む変曲点",
               4: "型4 変曲点が見つからない",
               5: "型5 収縮期ピークが拍の末尾（波形が不正）"}

# D0 の許容。50番 節C の C0 と同じ値（(0) は同じ `fit_beat` を呼ぶので厳しくてよい）
TOL_DT_MS = 1e-6
TOL_RI = 1e-9

# 表の見出しに毎回出す注記（50番と同じ言い回し）
POSTHOC = ("探索・事後であり、26番の事前規準による判定は動かさない。"
           "この台本に事前登録した予測は無い。")

_L = None                  # 23番（真値と同梱の特徴点の読み込み）。要るときだけ読む


def _landmarks_module():
    """23番を必要になったときだけ読み込む（自己検証の模擬作りでも使う）。"""
    global _L
    if _L is None:
        _L = _load("23_pwdb_landmarks.py", "m23")
    return _L


# ---------------------------------------------------------------- 表示の部品
def _pad(s, w: int, right: bool = False) -> str:
    """表示幅で揃える（日本語は 2 文字分。f 文字列の桁指定は文字数なのでずれる）。50番と同じ。"""
    used = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in str(s))
    fill = " " * max(0, w - used)
    return (fill + str(s)) if right else (str(s) + fill)


def _n(v: float, prec: int = 3, sign: bool = False) -> str:
    """文中に埋める数値（桁揃えをしない）。50番と同じ。"""
    if not np.isfinite(v):
        return "—"
    return f"{v:+.{prec}f}" if sign else f"{v:.{prec}f}"


def _q4(v) -> tuple:
    """有限値の (人数, 中央値, 第1四分位, 第3四分位)。"""
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return 0, float("nan"), float("nan"), float("nan")
    return (int(v.size), float(np.median(v)),
            float(np.percentile(v, 25)), float(np.percentile(v, 75)))


def _iqr_txt(rec: tuple, prec: int = 1) -> str:
    """「中央値 [第1四分位–第3四分位]」。"""
    _cnt, med, q1, q3 = rec
    if not np.isfinite(med):
        return "—"
    return f"{med:.{prec}f} [{q1:.{prec}f}–{q3:.{prec}f}]"


def _colv(d: pd.DataFrame, c: str) -> np.ndarray:
    if c not in d.columns:
        return np.full(len(d), np.nan)
    return pd.to_numeric(d[c], errors="coerce").to_numpy(dtype=float)


def print_stage_note() -> None:
    """A 段・C 段の 1 行の定義。**段を使う表の直前に毎回出す**（CLAUDE.md 節3）。"""
    print("  段: A 段 = その手法が自分で採用した被験者だけ（ok == 1）、"
          "C 段 = 採否を無視した全員（この台本に B 段は無い）。")


def print_posthoc() -> None:
    """表の見出しに出す注記。**すべての表に出す。**"""
    print(f"  【{POSTHOC}】")


def stage_of(d: pd.DataFrame, ok_col) -> pd.DataFrame:
    """A 段（その手法が採用した例だけ）に絞る。`ok_col` が None なら C 段のまま。50番と同じ。"""
    if ok_col is None:
        return d
    if ok_col not in d.columns:
        return d.iloc[0:0]
    return d[pd.to_numeric(d[ok_col], errors="coerce") == 1]


def subset_klass(d: pd.DataFrame, k):
    return d if k is None else d[_colv(d, KLASS_COL) == float(k)]


def _ktypes():
    """表で分ける型の一覧（型1・型3・型4 と「全」）。"""
    return [(k, f"型{k}") for k in KLASSES] + [(None, "全")]


def judge_by_age(d: pd.DataFrame, x: str, y: str, sign: int):
    """年齢層内 Spearman の一式。20番の `_by_age`・`_judge` をそのまま使う（48番・50番と同じ）。"""
    if len(d) == 0 or x not in d.columns or y not in d.columns or "age" not in d.columns:
        return None, []
    rows = M._by_age(d, x, y, min_n=MIN_PER_AGE)
    return M._judge(rows, sign), rows


def _cell(j) -> str:
    """表のます目「|ρ| の中央値（向きの合った層／評価できた層）成立・不成立」。50番と同じ。"""
    if not j:
        return "—"
    return (f"{j['med_abs']:.3f}（{j['n_ok']}/{j['n_ages']}）"
            + ("成立" if j["pass"] else "不成立"))


# ================================================================ ファイルの所在
# 20番の `NEEDED`（血行動態の真値・モデル入力・指尖PPG）に足す分。配布版で階層が変わりうるので
# 名前のパターンで root 以下を再帰的に探す（大文字小文字は無視）のは 20番と同じ。
# 実配布版（Zenodo 2019-07-07 の CSV 形式）の該当メンバーは
#   exported_data/PWs/csv/PWs_Digital_P.csv    指尖の圧
#   exported_data/PWs/csv/PWs_Digital_U.csv    指尖の流速
#   exported_data/PWs/csv/PWs_Digital_A.csv    指尖の内腔断面積（この台本では使わない）
# である（`pwdb_onset_times.csv` の見出しが Digital_P, Digital_U, Digital_A, Digital_PPG と
# 並んでいることから、部位名＋量の記号という命名であることが分かる）。
# `*digital*_p.csv` は `pws_digital_ppg.csv` に**合わない**（末尾が `_ppg.csv` であって
# `_p.csv` ではない）ので、PPG の行を圧として取り違えることはない。逆に 20番の
# `*digital*ppg*.csv` は `pws_digital_p.csv` に合わない（`ppg` を含まない）。
# (キー, パターン, 説明, 必須か)
NEEDED_51 = {
    "p": ("*digital*_p.csv", "指尖の圧 PWs_Digital_P.csv", True),
    "u": ("*digital*_u.csv", "指尖の流速 PWs_Digital_U.csv", True),
    "a": ("*digital*_a.csv", "指尖の内腔断面積 PWs_Digital_A.csv", False),
}


def _extract_from_zips(root: Path, patterns) -> list:
    """root 以下の zip から、patterns に合うメンバーだけを取り出す（20番と同じ手順）。

    20番の `_extract_from_zips` は 20番自身の `NEEDED` しか見ないので、圧・流速は
    取り出されない。同じ書き方でパターンだけを差し替える。
    """
    got = []
    for z in sorted(root.rglob("*.zip")):
        try:
            with zipfile.ZipFile(z) as zf:
                for member in zf.namelist():
                    name = Path(member).name.lower()
                    if any(fnmatch.fnmatch(name, pat) for pat in patterns):
                        dest = root / "extracted"
                        dest.mkdir(parents=True, exist_ok=True)
                        zf.extract(member, dest)
                        got.append(dest / member)
        except zipfile.BadZipFile:
            continue
    return got


def locate_51_files(root: Path) -> dict:
    """20番の 3 ファイルに加えて、指尖の圧・流速（あれば内腔断面積）の実パスを返す。

    見つからないものがあれば、何が足りないかを添えて `FileNotFoundError` を出す。
    呼び出し側はそれを捕まえて終了コード 2 にする（50番が `--pwdb` を欠いたときと同じ扱い）。
    """
    root = Path(root).expanduser()
    found = dict(M.locate_pwdb_files(root))          # 真値・モデル入力・指尖PPG（無ければ例外）
    got = {k: M._find_one(root, pat) for k, (pat, _lab, _req) in NEEDED_51.items()}
    if any(v is None for k, v in got.items() if NEEDED_51[k][2]):
        pats = [NEEDED_51[k][0] for k, v in got.items() if v is None]
        hit = _extract_from_zips(root, pats)
        if hit:
            print(f"  zip から {len(hit)} ファイルを取り出した: {root / 'extracted'}", flush=True)
            got = {k: M._find_one(root, pat) for k, (pat, _l, _r) in NEEDED_51.items()}
    missing = [NEEDED_51[k][1] for k, v in got.items() if v is None and NEEDED_51[k][2]]
    if missing:
        raise FileNotFoundError("必要なファイルが見つかりません: " + " / ".join(missing))
    found.update({k: v for k, v in got.items() if v is not None})
    return found


def print_missing(detail: str) -> None:
    """必要なファイルが無いときの案内（50番 `print_no_pwdb` と同じ扱いで終了コード 2 にする）。"""
    print(f"\n  {detail}")
    print("  この台本は PWDB の配布物に加えて**指尖の圧と流速**が要る。")
    print("  例: python3 scripts/51_pwdb_wave_separation.py --pwdb ~/pwdb --jobs 8")
    print("  取り出し方: python3 scripts/22_pwdb_fetch.py --out ~/pwdb \"<zip の直リンク>\"")
    print("  22番の取り出しの規則には PWs_Digital_P.csv・PWs_Digital_U.csv・"
          "PWs_Digital_A.csv を足してある。")


# ================================================================ 波の分離
MIN_LOOP_N = 4             # ρc 主 の回帰に要る最小の標本数
# 後進波が**まったく無い**（P と U が厳密に比例する）拍では、P_b は丸め誤差の大きさ
# （前進波の 1e-14 倍ほど）になり、符号も山の位置も浮動小数の端数で決まる。
# `max(P_b) ≤ 0` だけではこれを捕まえられないので、前進波に対する比で下限を置く。
# **生理的な規準ではなく、数値的に 0 と区別できない後進波を除くためだけの値である。**
# 実 PWDB の RI_true は 0.1〜0.5 の程度なので、この下限が実データに触ることはない。
EPS_PB_REL = 1e-6


def rho_c_loop(dp: np.ndarray, du: np.ndarray) -> dict:
    """収縮期初期の P–U ループの傾き（原点を通す回帰）で ρc を推定する。

    区間は「立ち上がりの足」から「dU/dt が最大になる時刻」まで。後進波がまだ届いて
    いない区間では P と U が比例する、という標準の仮定による。足は拍の前 1/3 で
    `dU` が最小になる標本とする（PWDB の拍は立ち上がりで切り出されているので通常は先頭）。
    区間が `MIN_LOOP_N` 標本に満たないときは `dU` の最大までのばし、それでも足りなければ
    推定しない（欠測）。
    """
    n = du.size
    out = {"rhoc": float("nan"), "i0": -1, "i1": -1, "n": 0}
    if n < MIN_LOOP_N * 2:
        return out
    i0 = int(np.argmin(du[:max(2, n // 3)]))
    i_pk = int(np.argmax(du))
    if i_pk <= i0 + 1:
        return out
    d1 = np.gradient(du)
    i1 = i0 + int(np.argmax(d1[i0:i_pk + 1]))
    if i1 - i0 + 1 < MIN_LOOP_N:
        i1 = i_pk
    if i1 - i0 + 1 < MIN_LOOP_N:
        return out
    x, y = du[i0:i1 + 1], dp[i0:i1 + 1]
    den = float(np.sum(x * x))
    if not np.isfinite(den) or den <= 0:
        return out
    out.update(rhoc=float(np.sum(x * y) / den), i0=int(i0), i1=int(i1), n=int(i1 - i0 + 1))
    return out


def rho_c_sumsq(dp: np.ndarray, du: np.ndarray) -> float:
    """二乗和法（Davies 2006）。`ρc = √(Σ(dP−平均)² / Σ(dU−平均)²)` を拍全体で計算する。

    平均を引くので基線の取り方には依らない。前進波と後進波が等しく寄与するという
    仮定が要るので、ここでは検算として並べるだけで、指標には使わない。
    """
    a = float(np.sum((dp - np.mean(dp)) ** 2))
    b = float(np.sum((du - np.mean(du)) ** 2))
    if not np.isfinite(a) or not np.isfinite(b) or b <= 0 or a < 0:
        return float("nan")
    return float(np.sqrt(a / b))


def separate(t: np.ndarray, p: np.ndarray, u: np.ndarray) -> dict:
    """1 拍の圧と流速から、真の前進波・後進波と ΔT_true・RI_true を返す。

    基線はその拍の最小値（docstring「波の分離の約束」）。ρc は主（P–U ループ）を使う。
    """
    p = np.asarray(p, float)
    u = np.asarray(u, float)
    dp = p - float(np.min(p))
    du = u - float(np.min(u))
    # 基線の取り方が効くのは、P と U の最小値が**違う標本**に来るときだけである。
    # そのとき P_b は定数 (min P − ρc·min U)/2 だけ下がる（上がる）。ピーク時刻は動かないので
    # ΔT_true は影響を受けないが、高さの比である RI_true は影響を受ける。
    # 実データでどれだけ起きているかを読めるように、ずれを列として残す。
    i_mp, i_mu = int(np.argmin(p)), int(np.argmin(u))
    loop = rho_c_loop(dp, du)
    ss = rho_c_sumsq(dp, du)
    out = {"min_i_p": i_mp, "min_i_u": i_mu,
           "min_gap_ms": (float(t[i_mu]) - float(t[i_mp])) * 1000.0,
           "same_min": int(i_mp == i_mu),
           "rhoc_loop": loop["rhoc"], "rhoc_ss": ss,
           "rhoc_ratio": (ss / loop["rhoc"]) if (np.isfinite(ss) and np.isfinite(loop["rhoc"])
                                                 and loop["rhoc"] != 0) else float("nan"),
           "loop_i0": loop["i0"], "loop_i1": loop["i1"], "loop_n": loop["n"],
           "pf_peak_ms": float("nan"), "pb_peak_ms": float("nan"),
           "pf_max": float("nan"), "pb_max": float("nan"),
           "dt_true_ms": float("nan"), "ri_true": float("nan"),
           "true_ok": 0, "why_true": "rhoc_none"}
    rhoc = loop["rhoc"]
    if not np.isfinite(rhoc) or rhoc <= 0:
        return out
    pf = 0.5 * (dp + rhoc * du)
    pb = 0.5 * (dp - rhoc * du)
    i_f, i_b = int(np.argmax(pf)), int(np.argmax(pb))
    out["pf_peak_ms"] = float(t[i_f]) * 1000.0
    out["pb_peak_ms"] = float(t[i_b]) * 1000.0
    out["pf_max"] = float(pf[i_f])
    out["pb_max"] = float(pb[i_b])
    # 評価できない拍: 後進波の高さが 0 以下、前進波に対して数値的に 0、
    # またはピークが拍の端にある（そもそも山が無い）
    if not (out["pb_max"] > 0) or not (out["pf_max"] > 0):
        out["why_true"] = "pb_nonpos"
        return out
    if out["pb_max"] <= EPS_PB_REL * out["pf_max"]:
        out["why_true"] = "pb_tiny"
        return out
    if i_b == 0 or i_b == pb.size - 1:
        out["why_true"] = "pb_edge"
        return out
    out["dt_true_ms"] = out["pb_peak_ms"] - out["pf_peak_ms"]
    out["ri_true"] = out["pb_max"] / out["pf_max"]
    out["true_ok"] = 1
    out["why_true"] = "-"
    return out


# ================================================================ 1 被験者
# 記録（CSV）に残す列。**再開の判定はこの一覧がすべて入っているかで行う。**
NUM_COLS = ("fs", "n_samp_ppg", "n_samp_p", "n_samp_u", "same_n",
            "min_i_p", "min_i_u", "min_gap_ms", "same_min",
            "rhoc_loop", "rhoc_ss", "rhoc_ratio", "loop_i0", "loop_i1", "loop_n",
            "pf_peak_ms", "pb_peak_ms", "pf_max", "pb_max", "dt_true_ms", "ri_true",
            "true_ok", "dt_ppg_ms", "ri_ppg", "ok_ppg", "nrmse_ppg",
            "dt_pres_ms", "ri_pres", "ok_pres", "nrmse_pres",
            "klass_own", "sys_own_ms", "dia_own_ms", "done")
TXT_COLS = ("why", "why_true")
CACHE_COLS = NUM_COLS + TXT_COLS
TXT_NONE = "-"             # 文字の列の「空」（欠測と区別できるように印を書く。50番の PIN_NONE と同じ）


def _empty_row(subj: int) -> dict:
    out = {"subj_no": int(subj)}
    for c in NUM_COLS:
        out[c] = float("nan")
    for c in TXT_COLS:
        out[c] = TXT_NONE
    for c in ("same_n", "true_ok", "ok_ppg", "ok_pres"):
        out[c] = 0
    out["done"] = 1
    return out


def wave_sep_subject(args_tuple):
    """1 被験者の 1 拍について、波の分離と 2 通りの分解を計算する。

    例外は握りつぶさず `why` に残し、値は欠測にする（1 名で落ちても走り続ける。26番・50番と同じ）。
    """
    subj, row_ppg, row_p, row_u, hr = args_tuple
    out = _empty_row(subj)
    why = []
    try:
        y, fs = M.beat_of(row_ppg, hr)
        if y is None:
            out["why"] = "no_beat_ppg"
            return out
        t = np.arange(y.size) / fs
        out["fs"] = float(fs)
        out["n_samp_ppg"] = int(y.size)

        # --- 波形の型（26番と同じ手順で自分で付ける）
        try:
            ys, _amp = pda2.preprocess(t, y, fs)
            if ys is None:
                why.append("preprocess_none")
            else:
                lm = pda2.find_landmarks(t, ys)
                out["klass_own"] = int(lm["klass"])
                out["sys_own_ms"] = float(lm["sys_t"]) * 1000.0
                out["dia_own_ms"] = float(lm["dia_t"]) * 1000.0
        except Exception as e:                    # noqa: BLE001
            why.append(("EXC:klass:" + str(e))[:40])

        # --- 凍結版の分解を PPG に当てる（26番 `indices_for_subject` と同じ呼び方）
        try:
            fit = fit_beat(t, y)
            ix = si_ri_from_fit(fit)
            out["dt_ppg_ms"] = ix["dt_s"] * 1000.0
            out["ri_ppg"] = ix["ri"]
            out["ok_ppg"] = int(bool(fit.get("ok", False)))
            out["nrmse_ppg"] = float(fit.get("nrmse", np.nan))
        except Exception as e:                    # noqa: BLE001
            why.append(("EXC:ppg:" + str(e))[:40])

        # --- 圧と流速（PPG と同じやり方で拍にする）
        if row_p is None or row_u is None:
            why.append("no_pu_row")
            out["why"] = ";".join(why)[:120]
            return out
        yp, fs_p = M.beat_of(row_p, hr)
        yu, fs_u = M.beat_of(row_u, hr)
        if yp is None or yu is None:
            why.append("no_beat_pu")
            out["why"] = ";".join(why)[:120]
            return out
        out["n_samp_p"] = int(yp.size)
        out["n_samp_u"] = int(yu.size)
        out["same_n"] = int(yp.size == yu.size == y.size)
        m = int(min(yp.size, yu.size))
        tp = np.arange(m) / fs_p
        yp, yu = yp[:m], yu[:m]

        # --- 凍結版の分解を圧波形に当てる（同じ関数・同じ引数）
        try:
            fitp = fit_beat(tp, yp)
            ixp = si_ri_from_fit(fitp)
            out["dt_pres_ms"] = ixp["dt_s"] * 1000.0
            out["ri_pres"] = ixp["ri"]
            out["ok_pres"] = int(bool(fitp.get("ok", False)))
            out["nrmse_pres"] = float(fitp.get("nrmse", np.nan))
        except Exception as e:                    # noqa: BLE001
            why.append(("EXC:pres:" + str(e))[:40])

        # --- 波の分離
        try:
            out.update(separate(tp, yp, yu))
        except Exception as e:                    # noqa: BLE001
            why.append(("EXC:sep:" + str(e))[:40])
    except Exception as e:                        # noqa: BLE001
        why.append(("EXC:" + str(e))[:60])
    out["why"] = (";".join(why)[:120]) or TXT_NONE
    return out


# ================================================================ 記録と再開
def _stride(ppg, limit: int):
    """先頭 N 名ではなく等間隔に N 名（26番 `_stride`・50番 `c_stride` と同じ式）。

    PWDB は被験者が年齢順に並んでいる可能性があり、先頭だけ取ると 1 つの年齢層に偏る。
    年齢層内の順位相関で読むので全層が要る。
    """
    if limit >= len(ppg):
        return ppg
    idx = np.unique(np.linspace(0, len(ppg) - 1, limit).round().astype(int))
    return ppg.iloc[idx]


def _cache_path(cache_csv, limit: int) -> Path:
    """記録の置き場。`--limit` のときは別名にする（26番・50番の CSV と同じ規約）。"""
    if cache_csv:
        return Path(cache_csv).expanduser()
    return OUT / (f"51_wave_sep_limit{limit}.csv" if limit else CACHE_NAME)


def _cached_rows(path: Path) -> dict:
    """記録（CSV）を被験者番号をキーにした辞書で読む。読めなければ空で返す（50番と同じ）。"""
    if not path.exists():
        return {}
    try:
        # `float_precision="round_trip"` を付ける。既定の速い読み方は最後の 1 ビットが
        # ずれることがあり、再開して書き直すだけで記録の数字が変わってしまう。
        old = pd.read_csv(path, float_precision="round_trip")
    except Exception as e:                        # noqa: BLE001
        print(f"  記録 {path} を読めない（{e}）。最初から計算する。", flush=True)
        return {}
    if "subj_no" not in old.columns:
        print(f"  記録 {path} に subj_no の列が無い。最初から計算する。", flush=True)
        return {}
    out = {}
    for rec in old.to_dict("records"):
        try:
            out[int(rec["subj_no"])] = rec
        except (TypeError, ValueError):
            continue
    return out


def _has_row(rec) -> bool:
    """記録にその被験者の結果が入っているか（`CACHE_COLS` が**すべて**あるか）。

    欠測そのものは正しい結果でありうる（後進波が立たない拍の `dt_true_ms` など）ので、
    「有限であること」ではなく「列があること」で判定し、計算が終わった印として
    `done` を見る。50番は有限を要求するが、この台本は 1 名につき当てはめを 2 回するため、
    正しく欠測になった被験者を毎回当てはめ直すと費用が大きい。
    """
    if not rec:
        return False
    for c in CACHE_COLS:
        if c not in rec or rec[c] is None:
            return False
    try:
        return int(float(rec["done"])) == 1
    except (TypeError, ValueError):
        return False


def _order_cols(df: pd.DataFrame) -> pd.DataFrame:
    """記録の列を決まった順に並べる（再開して書き直しても同じ CSV になる）。"""
    order = ["subj_no"] + [c for c in NUM_COLS if c != "done"] + list(TXT_COLS) + ["done"]
    order += ["python_version", "numpy_version", "scipy_version"]
    order = [c for c in order if c in df.columns]
    rest = [c for c in df.columns if c not in order]
    return df[order + rest]


def _row_of(mat: np.ndarray, idx: dict, subj: int):
    i = idx.get(int(subj))
    return None if i is None else mat[i]


def build(root: Path, limit: int = 0, jobs: int = 1, cache_csv=None, resume: bool = True):
    """PWDB を読み、波の分離と 2 通りの分解を計算し、記録（CSV）を書き直して表を返す。

    返り値は (この実行で使う表, 記録の場所, 内訳)。表は今回の被験者だけに絞るが、記録には
    前の実行で計算した被験者も残す（再開できるようにするため）。50番 節C と同じ規約。
    """
    root = Path(root).expanduser()
    files = locate_51_files(root)
    path = _cache_path(cache_csv, limit)
    hae, _cfg, ppg, _extras = M.load_pwdb(root)
    print(f"  読み込み元: {files['p']}\n            {files['u']}", flush=True)
    if "a" in files:
        print(f"  （内腔断面積 {files['a']} もあるが、この台本では使わない）", flush=True)
    pres = pd.read_csv(files["p"], skipinitialspace=True)
    flow = pd.read_csv(files["u"], skipinitialspace=True)
    print(f"  表の大きさ PPG {ppg.shape} ・圧 {pres.shape} ・流速 {flow.shape}"
          f"（列数は最長の拍に合わせた詰め物込み）", flush=True)
    pmat, umat = pres.to_numpy(float), flow.to_numpy(float)
    p_idx = {int(v): i for i, v in enumerate(pmat[:, 0]) if np.isfinite(v)}
    u_idx = {int(v): i for i, v in enumerate(umat[:, 0]) if np.isfinite(v)}

    if limit and limit < len(ppg):
        ppg = _stride(ppg, limit)
        print(f"  --limit: 等間隔に {len(ppg)} 名を取る（26番と同じ。全年齢層を含めるため）",
              flush=True)
    hr_by = dict(zip(hae["subj_no"].astype(int), hae["HR"].astype(float)))
    have = _cached_rows(path) if resume else {}
    if have:
        print(f"  記録を読んだ: {path}（{len(have)} 名）", flush=True)

    subjects, work, n_cache = [], [], 0
    for i in range(len(ppg)):
        subj = int(ppg.iloc[i, 0])
        subjects.append(subj)
        if _has_row(have.get(subj)):
            n_cache += 1
            continue
        work.append((subj, ppg.iloc[i].to_numpy(float),
                     _row_of(pmat, p_idx, subj), _row_of(umat, u_idx, subj),
                     hr_by.get(subj, np.nan)))
    print(f"\n  {len(subjects)} 名中 {len(work)} 名を計算する"
          f"（記録から {n_cache} 名を再利用）/ jobs={jobs}", flush=True)

    import platform
    import time
    import scipy
    meta = {"python_version": platform.python_version(),
            "numpy_version": np.__version__, "scipy_version": scipy.__version__}
    path.parent.mkdir(parents=True, exist_ok=True)

    def _absorb(r: dict) -> None:
        r.update(meta)
        s_ = int(r["subj_no"])
        base = dict(have.get(s_, {}))
        base.update(r)
        have[s_] = base

    def _write() -> pd.DataFrame:
        df_ = _order_cols(pd.DataFrame([have[s_] for s_ in sorted(have)]))
        df_.to_csv(path, index=False)
        return df_

    t_start = time.time()
    n_done = 0

    def _tick(r: dict) -> None:
        nonlocal n_done
        _absorb(r)
        n_done += 1
        if n_done % PROGRESS_EVERY == 0 or n_done == len(work):
            el = time.time() - t_start
            eta = el / n_done * (len(work) - n_done)
            print(f"  [{n_done}/{len(work)}] {el:.0f} 秒経過・残り約 {eta:.0f} 秒", flush=True)
        if n_done % CKPT_EVERY == 0 and n_done < len(work):
            _write()
            print(f"  途中の記録を書いた: {path}（{len(have)} 名）", flush=True)

    if work and jobs > 1:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(max_workers=jobs) as ex:
            futs = [ex.submit(wave_sep_subject, w) for w in work]
            for fut in as_completed(futs):
                _tick(fut.result())
    elif work:
        for w in work:
            _tick(wave_sep_subject(w))

    df = _write()
    print(f"  被験者ごとの記録: {path}（{len(df)} 名・{len(df.columns)} 列）", flush=True)
    keep = df[df["subj_no"].isin(subjects)].reset_index(drop=True)
    return keep, path, {"n_calc": len(work), "n_cache": n_cache, "n_sub": len(subjects)}


# ================================================================ 表 D0
def print_d0(d: pd.DataFrame, has26: bool) -> dict:
    """D0 検算: PPG に当てた分解が 26番の列を再現するか。"""
    print("\n" + "-" * 100)
    print("D0. 検算: 指尖 PPG に当てた凍結版の分解は 26番の列（dt_v1_ms・ri_v1・ok_v1・"
          "klass_own）と同じか")
    print("-" * 100)
    print_posthoc()
    out = {"state": "照合できない", "n": 0, "dt": float("nan"), "ri": float("nan"),
           "n_ok_diff": -1, "n_klass_diff": -1, "match": False}
    if not has26:
        print("  26番の出力が無いので照合できない（--csv で 26番の CSV を渡す）。")
        return out

    def _pair(a_col: str, b_col: str, is_value: bool):
        a, b = _colv(d, a_col), _colv(d, b_col)
        g = np.isfinite(a) & np.isfinite(b)
        if not g.any():
            return 0, float("nan")
        if is_value:
            return int(g.sum()), float(np.max(np.abs(a[g] - b[g])))
        return int(g.sum()), float(np.sum(a[g] != b[g]))

    n_dt, out["dt"] = _pair("dt_ppg_ms", "dt_v1_ms", True)
    n_ri, out["ri"] = _pair("ri_ppg", "ri_v1", True)
    n_ok, v_ok = _pair("ok_ppg", "ok_v1", False)
    n_kl, v_kl = _pair(KLASS_COL, KLASS_COL + "_26", False)
    out["n"] = n_dt
    out["n_ok_diff"] = int(v_ok) if np.isfinite(v_ok) else -1
    out["n_klass_diff"] = int(v_kl) if np.isfinite(v_kl) else -1
    print(f"  対応のある行 ΔT {n_dt} 名・RI {n_ri} 名・採否 {n_ok} 名・型 {n_kl} 名")
    print(f"  |dt_ppg_ms − dt_v1_ms| の最大  {_n(out['dt'], 9)} ms（許容 {TOL_DT_MS:g}）")
    print(f"  |ri_ppg − ri_v1| の最大        {_n(out['ri'], 12)}（許容 {TOL_RI:g}）")
    print("  ok_ppg ≠ ok_v1 の人数          "
          + (str(out["n_ok_diff"]) if out["n_ok_diff"] >= 0 else "—（照合できない）"))
    print("  klass_own ≠ klass_own_26 の人数 "
          + (str(out["n_klass_diff"]) if out["n_klass_diff"] >= 0 else "—（照合できない）"))
    if not (n_dt and n_ri and n_ok):
        print("  → 照合できない（対応のある行が無い。26番の CSV がこの被験者を含まない）")
        return out
    ok_v = bool(out["dt"] <= TOL_DT_MS and out["ri"] <= TOL_RI and out["n_ok_diff"] == 0)
    out["match"] = bool(ok_v and (out["n_klass_diff"] in (0, -1)))
    out["state"] = "一致" if out["match"] else "食い違いあり"
    print(f"  → {out['state']}")
    if not out["match"]:
        print("  ★ ここは `src/pda.py` の `fit_beat` をそのまま呼ぶので 26番と一致するはずである。")
        print("  食い違うなら入力の拍か版が 26番と違う（この先の表はその前提で読む）。")
    print("  出典: この台本（51番）が PWDB の拍から計算した値と、26番の出力の突き合わせ。")
    return out


# ================================================================ 表 D1
def print_d1(d: pd.DataFrame) -> dict:
    """D1 ρc の分布（年齢層別。主・検・比）。"""
    print("\n" + "-" * 100)
    print("D1. ρc（特性インピーダンス）の分布: 年齢層ごとの中央値と四分位範囲")
    print("-" * 100)
    print_posthoc()
    print("  主 = 収縮期初期の P–U ループの傾き（足から dU/dt 最大まで、原点を通す回帰）。")
    print("  検 = 二乗和法 √(Σ(dP−平均)²/Σ(dU−平均)²)（Davies 2006）。**指標には主を使う。**")
    print("  単位は（配布物の圧の単位）/（配布物の流速の単位）。ΔT_true・RI_true はこれに依らない。")
    print("  " + _pad("年齢層", 10) + _pad("n", 7, right=True)
          + _pad("ρc 主 中央値 [四分位範囲]", 34, right=True)
          + _pad("ρc 検 中央値 [四分位範囲]", 34, right=True)
          + _pad("比 検/主 の中央値", 20, right=True))
    out = {}
    ages = sorted(pd.to_numeric(d.get("age", pd.Series(dtype=float)),
                                errors="coerce").dropna().unique().tolist())
    for age in ages + [None]:
        g = d if age is None else d[_colv(d, "age") == float(age)]
        lab = "全" if age is None else f"{int(age)} 歳"
        a = _q4(_colv(g, "rhoc_loop"))
        b = _q4(_colv(g, "rhoc_ss"))
        r = _q4(_colv(g, "rhoc_ratio"))
        out[age] = {"n": len(g), "loop": a, "ss": b, "ratio": r}
        print("  " + _pad(lab, 10) + _pad(len(g), 7, right=True)
              + _pad(_iqr_txt(a, 2), 34, right=True) + _pad(_iqr_txt(b, 2), 34, right=True)
              + _pad(_n(r[1], 3), 20, right=True))
    n_bad = int(np.sum(~np.isfinite(_colv(d, "rhoc_loop"))))
    print(f"  ρc 主 を推定できなかった被験者 {n_bad} 名"
          f"（回帰の区間が {MIN_LOOP_N} 標本に満たない・dU が増えない拍）")
    sm = _colv(d, "same_min")
    gap = _colv(d, "min_gap_ms")
    n_sm, n_hv = int(np.nansum(sm)), int(np.isfinite(sm).sum())
    out["same_min"] = {"n": n_sm, "of": n_hv, "gap": _q4(gap)}
    print(f"  基線の取り方の効き: P と U の最小値が同じ標本に来た被験者 {n_sm}/{n_hv} 名・"
          f"ずれ（U の最小 − P の最小）の中央値 {_n(_q4(gap)[1], 1)} ms")
    print("    ずれがあると P_b は定数だけ上下する。**ピーク時刻は動かないので ΔT_true は"
          "影響を受けず、高さの比である RI_true だけが影響を受ける。**")
    print("  出典: この台本（51番）が PWDB の指尖の圧・流速から計算した値。")
    return out


# ================================================================ 表 D2
def print_d2(d: pd.DataFrame) -> dict:
    """D2 真の後進波の指標の分布（波形の型 × 年齢層）。"""
    print("\n" + "-" * 100)
    print("D2. 真の後進波の指標の分布: 波形の型 × 年齢層（C 段）")
    print("-" * 100)
    print_posthoc()
    print_stage_note()
    print("  ΔT_true = t_peak(P_b) − t_peak(P_f) [ms]、RI_true = max(P_b)/max(P_f)。")
    print("  「評価できない」は P_b のピークが拍の端にある、max(P_b) ≤ 0、または")
    print(f"  max(P_b) ≤ {EPS_PB_REL:g}·max(P_f)（数値的に 0。生理的な規準ではない）の被験者。")
    out = {}
    ages = sorted(pd.to_numeric(d.get("age", pd.Series(dtype=float)),
                                errors="coerce").dropna().unique().tolist())
    for kt, _nm in _ktypes():
        g0 = subset_klass(d, kt)
        lab = KLASS_LABEL.get(kt, "全例（型を分けない）")
        n_bad = int(np.sum(_colv(g0, "true_ok") != 1))
        print(f"\n  {lab}  n = {len(g0)} 名（評価できない {n_bad} 名）")
        print("    " + _pad("年齢層", 10) + _pad("n", 7, right=True)
              + _pad("ΔT_true 中央値 [四分位範囲] ms", 36, right=True)
              + _pad("RI_true 中央値 [四分位範囲]", 34, right=True))
        for age in ages + [None]:
            g = g0 if age is None else g0[_colv(g0, "age") == float(age)]
            a = _q4(_colv(g, "dt_true_ms"))
            b = _q4(_colv(g, "ri_true"))
            out[(kt, age)] = {"n": len(g), "dt": a, "ri": b}
            print("    " + _pad("全" if age is None else f"{int(age)} 歳", 10)
                  + _pad(a[0], 7, right=True)
                  + _pad(_iqr_txt(a, 1), 36, right=True) + _pad(_iqr_txt(b, 3), 34, right=True))
    why = d["why_true"].astype(str) if "why_true" in d.columns else pd.Series(dtype=str)
    why = why[(why != TXT_NONE) & (why != "")]
    if len(why):
        print(f"\n  評価できない理由の内訳: {why.value_counts().head(5).to_dict()}")
        print("    pb_edge = P_b のピークが拍の端・pb_nonpos = max(P_b) ≤ 0・"
              f"pb_tiny = max(P_b) ≤ {EPS_PB_REL:g}·max(P_f)（数値的に 0）・"
              "rhoc_none = ρc 主 を推定できない")
    print("  出典: この台本（51番）が PWDB の指尖の圧・流速から計算した値。")
    return out


# ================================================================ 表 D3
D3_ROWS_DT = [("分解（PPG）", "dt_ppg_ms", "ok_ppg", "A"),
              ("分解（PPG）", "dt_ppg_ms", None, "C"),
              ("分解（圧）", "dt_pres_ms", "ok_pres", "A"),
              ("分解（圧）", "dt_pres_ms", None, "C"),
              ("（参考）特徴点", COL_LM_DT, None, "C")]
D3_ROWS_RI = [("分解（PPG）", "ri_ppg", "ok_ppg", "A"),
              ("分解（PPG）", "ri_ppg", None, "C"),
              ("分解（圧）", "ri_pres", "ok_pres", "A"),
              ("分解（圧）", "ri_pres", None, "C"),
              ("（参考）特徴点", COL_LM_RI, None, "C")]


def _d3_block(d: pd.DataFrame, rows: list, true_col: str, unit: str, prec: int) -> dict:
    out = {}
    for kt, nm in _ktypes():
        g0 = subset_klass(d, kt)
        print(f"\n  {KLASS_LABEL.get(kt, '全例（型を分けない）')}  n = {len(g0)} 名")
        print("    " + _pad("手法（段）", 22) + _pad("n", 7, right=True)
              + _pad(f"差の中央値{unit}", 18, right=True)
              + _pad(f"|差| の中央値{unit}", 20, right=True)
              + _pad("ρ（まとめ）", 14, right=True) + _pad("ρ の n", 9, right=True))
        for lab, col, ok_col, stg in rows:
            g = stage_of(g0, ok_col)
            x, tv = _colv(g, col), _colv(g, true_col)
            ok = np.isfinite(x) & np.isfinite(tv)
            dif = x[ok] - tv[ok]
            med = float(np.median(dif)) if dif.size else float("nan")
            amed = float(np.median(np.abs(dif))) if dif.size else float("nan")
            r, nr = M._spearman(x, tv, min_n=MIN_N_POOL)
            out[(nm, lab, stg)] = {"n": int(ok.sum()), "med": med, "amed": amed,
                                   "rho": r, "n_rho": nr}
            print("    " + _pad(f"{lab} {stg}", 22) + _pad(int(ok.sum()), 7, right=True)
                  + _pad(_n(med, prec, sign=True), 18, right=True)
                  + _pad(_n(amed, prec), 20, right=True)
                  + _pad(_n(r, 3, sign=True), 14, right=True)
                  + _pad(nr if nr else "—", 9, right=True))
    return out


def print_d3(d: pd.DataFrame) -> dict:
    """D3 W2: 分解の第2成分は真の後進波に一致するか。"""
    print("\n" + "-" * 100)
    print("D3. W2 分解の第2成分は真の後進波に一致するか（波形の型 × 段）")
    print("-" * 100)
    print_posthoc()
    print_stage_note()
    print("  差 = （手法の値）−（真の値）。ΔT は ms、RI は比。ρ はまとめた Spearman"
          f"（20番 `_spearman`・{MIN_N_POOL} 名以上。年齢層で分けない）。")
    print("  対応のある行（両方が有限）だけを使う。特徴点（同梱）は採否が無いので C 段だけ。")
    out = {}
    print("\n  [ΔT] 手法の ΔT と ΔT_true = t_peak(P_b) − t_peak(P_f)")
    out["dt"] = _d3_block(d, D3_ROWS_DT, "dt_true_ms", "[ms]", 1)
    print("\n  [RI] 手法の RI と RI_true = max(P_b)/max(P_f)")
    out["ri"] = _d3_block(d, D3_ROWS_RI, "ri_true", "", 3)
    print("\n  出典: この台本（51番）が PWDB の拍から計算した値（特徴点の 2 行は Charlton 同梱）。")
    return out


# ================================================================ 表 D4
D4_ROWS_DT = [("(a) 分解（PPG）", "dt_ppg_ms", "ok_ppg", "A"),
              ("(a) 分解（PPG）", "dt_ppg_ms", None, "C"),
              ("(b) 分解（圧）", "dt_pres_ms", "ok_pres", "A"),
              ("(b) 分解（圧）", "dt_pres_ms", None, "C"),
              ("(c) 特徴点（同梱）", COL_LM_DT, None, "C")]
D4_ROWS_RI = [("(a) 分解（PPG）", "ri_ppg", "ok_ppg", "A"),
              ("(a) 分解（PPG）", "ri_ppg", None, "C"),
              ("(b) 分解（圧）", "ri_pres", "ok_pres", "A"),
              ("(b) 分解（圧）", "ri_pres", None, "C"),
              ("(c) 特徴点（同梱）", COL_LM_RI, None, "C")]


def _d4_matrix(d: pd.DataFrame, rows: list, tgt: str, sign: int) -> dict:
    types = _ktypes()
    print("  " + _pad("手法（段）", 22)
          + "".join(_pad(nm, 19, right=True) for _k, nm in types))
    out = {}
    for lab, col, ok_col, stg in rows:
        line = "  " + _pad(f"{lab} {stg}", 22)
        for kt, nm in types:
            g = stage_of(subset_klass(d, kt), ok_col)
            j, ages = judge_by_age(g, col, tgt, sign)
            out[(nm, lab, stg)] = {"j": j, "rows": ages, "n": len(g)}
            line += _pad(_cell(j), 19, right=True)
        print(line)
    return out


def print_d4(d: pd.DataFrame) -> dict:
    """D4 W3: 圧波形に当てるとどうなるか（年齢層内の順位相関）。"""
    print("\n" + "-" * 100)
    print("D4. W3 同じ分解を指尖の圧波形に当てるとどうなるか（波形の型 × 段。年齢層内 Spearman）")
    print("-" * 100)
    print_posthoc()
    print_stage_note()
    print(f"  層は `age` の相異なる値、1 層 {MIN_PER_AGE} 名以上（20番の `_by_age`・`_judge`）。")
    print("  ます目は **|ρ| の中央値（予測の向きに合った層数／評価できた層数）** と、")
    print(f"  20番 `_judge` の規準（|中央値| ≥ {M.CRIT_RHO:.2f} かつ全層で向きが合う）に対する")
    print("  **規準 成立／不成立**。**この印は事後の記述であり、26番の判定は動かない。**")
    out = {}
    print(f"\n  [ΔT × 大動脈脈波伝播速度 {COL_PWV}]（予測の向き 負）")
    out["dt"] = _d4_matrix(d, D4_ROWS_DT, COL_PWV, SIGN_DT)
    print(f"\n  [RI × 末梢血管抵抗 {COL_PVR}]（予測の向き 正）")
    out["ri"] = _d4_matrix(d, D4_ROWS_RI, COL_PVR, SIGN_RI)

    print("\n  採択率（各手法が自分で採用した割合。分母は型ごとの全員＝C 段）")
    print("  " + _pad("手法", 22) + "".join(_pad(nm, 19, right=True) for _k, nm in _ktypes()))
    rates = {}
    for lab, ok_col in (("(a) 分解（PPG）", "ok_ppg"), ("(b) 分解（圧）", "ok_pres")):
        line = "  " + _pad(lab, 22)
        for kt, nm in _ktypes():
            g = subset_klass(d, kt)
            v = _colv(g, ok_col)
            n = int(np.isfinite(v).sum())
            rate = float(np.nanmean(v)) if n else float("nan")
            rates[(nm, lab)] = {"n": n, "rate": rate}
            line += _pad(f"{100.0 * rate:.1f}%（{n}）" if np.isfinite(rate) else "—",
                         19, right=True)
        print(line)
    out["rates"] = rates
    print("  採否は凍結版 `fit_beat` の収束の検算（境界張り付き・高さ 0.02・競合解の RI 差 0.08）。")
    print("  出典: この台本（51番）が PWDB の拍から計算した値（(c) は Charlton 同梱の列）。")
    return out


# ================================================================ 表 D5
def print_d5(d: pd.DataFrame, d2: dict, d3: dict, d4: dict) -> dict:
    """D5 読み: 3 つの問いと、それに関わる数値（結論は書かない）。"""
    print("\n" + "-" * 100)
    print("D5. 読み: この台本が答えるために作られた 3 つの問いと、それに関わる数値")
    print("-" * 100)
    print_posthoc()
    print_stage_note()
    print("  **ここでは数値を並べるだけで、結論は書かない。**判定は 26番の事前規準にしかない。")
    out = {}

    # --- (i) 第2成分は真の後進波に載るか（W2）
    print("\n  (i) 分解の第2成分は真の後進波に載るか（W2。D3 の値）")
    for lab, stg in (("分解（PPG）", "A"), ("分解（PPG）", "C"),
                     ("分解（圧）", "A"), ("分解（圧）", "C"), ("（参考）特徴点", "C")):
        rec = d3["dt"].get(("全", lab, stg))
        rec_r = d3["ri"].get(("全", lab, stg))
        if not rec:
            continue
        print(f"    {_pad(lab + ' ' + stg + ' 段', 22)}"
              f"ΔT 差の中央値 {_n(rec['med'], 1, sign=True)} ms・"
              f"|差| {_n(rec['amed'], 1)} ms・ρ {_n(rec['rho'], 3, sign=True)}"
              f"（n {rec['n_rho']}）"
              + (f" / RI 差 {_n(rec_r['med'], 3, sign=True)}・"
                 f"ρ {_n(rec_r['rho'], 3, sign=True)}" if rec_r else ""))
        out[f"i:{lab}:{stg}"] = rec
    n_bad = int(np.sum(_colv(d, "true_ok") != 1))
    print(f"    真の後進波を評価できなかった被験者 {n_bad} / {len(d)} 名")

    # --- (ii) 圧のほうが PPG より良いか（W3）
    print("\n  (ii) 分解は PPG より圧波形のほうが良い成績を出すか（W3。D4 の値）")
    for key, tgt, lab_t in (("dt", COL_PWV, f"ΔT × {COL_PWV}"),
                            ("ri", COL_PVR, f"RI × {COL_PVR}")):
        for lab in ("(a) 分解（PPG）", "(b) 分解（圧）", "(c) 特徴点（同梱）"):
            for stg in ("A", "C"):
                rec = d4[key].get(("全", lab, stg))
                if not rec:
                    continue
                print(f"    {_pad(lab_t, 20)}{_pad(lab + ' ' + stg + ' 段', 24)}"
                      f"{_cell(rec['j'])}")
                out[f"ii:{key}:{lab}:{stg}"] = rec["j"]

    # --- (iii) 真の ΔT 自体が大動脈脈波伝播速度と関連するか（どの分解でも超えられない上限）
    print("\n  (iii) 真の後進波の ΔT_true 自体が、年齢層内で大動脈脈波伝播速度と関連するか")
    print("      これは分解がどれだけ良くても超えられない**上限**である（真値どうしの関係）。")
    for col, tgt, sign, lab in (("dt_true_ms", COL_PWV, SIGN_DT, f"ΔT_true × {COL_PWV}"),
                                ("ri_true", COL_PVR, SIGN_RI, f"RI_true × {COL_PVR}")):
        for kt, nm in _ktypes():
            g = subset_klass(d, kt)
            j, rows = judge_by_age(g, col, tgt, sign)
            out[f"iii:{col}:{nm}"] = j
            print(f"    {_pad(lab, 22)}{_pad(nm, 6)}{_cell(j)}"
                  + ("  年齢層別 " + "・".join(f"{int(a)}歳 {_n(r, 2, sign=True)}({n})"
                                               for a, r, n in rows) if rows else ""))
    print("\n  出典: この台本（51番）が PWDB の拍と真値から計算した値。")
    return out


# ================================================================ 報告
def report(d: pd.DataFrame, has26: bool, info: dict, path: Path) -> dict:
    ages = sorted(pd.to_numeric(d.get("age", pd.Series(dtype=float)),
                                errors="coerce").dropna().unique().tolist())
    kl = _colv(d, KLASS_COL)
    seen = sorted(set(int(v) for v in kl[np.isfinite(kl)]))
    print("\n" + "=" * 100)
    print("51番 PWDB: 分解の第2成分は真の後進波か／弱点は分解か PPG という量か"
          "（探索・事後。26番の判定は動かない）")
    print("=" * 100)
    print(f"  被験者 {len(d)} 名・年齢層 {[int(a) for a in ages]}・型の値 {seen}")
    same = _colv(d, "same_n")
    n_same = int(np.nansum(same))
    n_have = int(np.isfinite(same).sum())
    print(f"  標本数の照合: PPG・圧・流速の 3 行の標本数が一致した被験者 {n_same}/{n_have} 名"
          f"（一致しない {n_have - n_same} 名。分離は短いほうに合わせて計算する）")
    if "why" in d.columns:
        why = d["why"].astype(str)
        why = why[(why != TXT_NONE) & (why != "") & (why != "nan")]
        if len(why):
            print(f"  計算の失敗 {len(why)} 名: {why.value_counts().head(5).to_dict()}")
    print(f"  記録: {path}（今回 {info.get('n_calc', 0)} 名を計算・"
          f"{info.get('n_cache', 0)} 名を再利用）")
    if len(d) < 100:
        print(f"  ★ この実行は {len(d)} 名の抜粋である（1 層 "
              f"{len(d) // max(len(ages), 1)} 名）。**ここから出る数値は読んではいけない。**")
    print(f"  【{POSTHOC}】")

    out = {"n": len(d)}
    out["d0"] = print_d0(d, has26)
    out["d1"] = print_d1(d)
    out["d2"] = print_d2(d)
    out["d3"] = print_d3(d)
    out["d4"] = print_d4(d)
    out["d5"] = print_d5(d, out["d2"], out["d3"], out["d4"])
    return out


def run(root, limit: int = 0, jobs: int = 1, cache_csv=None, resume: bool = True,
        csv26=None) -> dict:
    """配布物を読み、計算し、表を出す。返り値に終了コードを入れる。"""
    root = Path(root).expanduser()
    try:
        df, path, info = build(root, limit=limit, jobs=jobs, cache_csv=cache_csv,
                               resume=resume)
    except FileNotFoundError as e:
        print_missing(str(e))
        return {"code": 2}
    L = _landmarks_module()
    d = L.load(root, pda_dir=root / "__no_pda__")
    d = d.drop(columns=[c for c in ("dt_pda_ms", "ri_pda", "ok2") if c in d.columns])
    n_truth = len(d)
    d = d.merge(df, on="subj_no", how="inner")
    print(f"\n  真値・同梱の特徴点 {n_truth} 名・この台本の計算 {len(df)} 名 → "
          f"突き合わせ {len(d)} 名（内部結合。26番と同じ扱い）", flush=True)
    has26 = False
    if csv26 is not None:
        p26 = Path(csv26).expanduser()
        if not p26.exists() and not p26.is_absolute():
            p26 = ROOT / str(csv26)
        if p26.exists():
            d26 = pd.read_csv(p26)
            cols = [c for c in ("subj_no", "dt_v1_ms", "ri_v1", "ok_v1", KLASS_COL)
                    if c in d26.columns]
            d = d.merge(d26[cols], on="subj_no", how="left", suffixes=("", "_26"))
            has26 = "dt_v1_ms" in d.columns
            print(f"  26番の列を結合した（{p26}・{len(d26)} 行）。D0 の検算に使う。", flush=True)
        else:
            print(f"  {p26} が無いので D0 の検算は飛ばす。", flush=True)
    for c in (COL_PWV, COL_PVR, COL_LM_DT, COL_LM_RI, "age", KLASS_COL, KLASS_COL + "_26"):
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    out = report(d, has26, info, path)
    out["code"] = 0
    out["d"] = d
    return out


# ================================================================ 自己検証
# 模擬の圧・流速は、**真の前進波と後進波を仕込んで**作る。
#   f(t)  前進波（歪みガウス 1 本。拡張期まで裾を引く）
#   b(t)  後進波（歪みガウス 1 本。到達を大動脈脈波伝播速度の関数にする）
#   P = f + b + P0      U = (f − b)/ρc
# この作り方だと、拍の最後の標本で f が最小・b がほぼ 0 になるので、P の最小値と U の
# 最小値が**同じ標本**で起こる。すると `dP − ρc·dU = 2b` が厳密に成り立ち、分離は
# 誤差なく b を復元する。ρc も収縮期初期（b がまだ届かない区間）で厳密に出る。
# **模擬の PPG（20番の `_make_mock`）と模擬の圧・流速は別々に作っている。**到達の式
# （0.42 − 0.022·PWV）だけを共有しているので D3 の差は小さく出るが、それは仕込みであって
# 手法の良さではない。ここで確かめるのは処理系（読み込み・分離・記録・表）である。
MOCK_FS = 500.0
MOCK_AMP = 40.0            # 前進波の大きさ [圧の単位]
MOCK_P0 = 80.0             # 拡張期の圧
MOCK_MU_F, MOCK_SIG_F, MOCK_AL_F = 0.11, 0.20, 3.0
MOCK_SIG_B, MOCK_AL_B = 0.075, 1.0
MOCK_NO_B_EVERY = 16       # この間隔の被験者には後進波を仕込まない（評価できない経路の検査）


def _mock_pu(root: Path) -> dict:
    """模擬 PWDB に `PWs_Digital_P.csv` と `PWs_Digital_U.csv` を書き足す。

    返り値は被験者番号 → 仕込んだ値（ρc・後進波のピーク時刻・後進波の有無）。
    """
    hae = M._read_named(root / "pwdb_haemod_params.csv", ("subj_no", "HR", "PWV_a"))
    cfg = M._read_named(root / "pwdb_model_configs.csv", ("subj_no", "pvr"))
    m = hae.merge(cfg[["subj_no", "pvr"]], on="subj_no")
    ppg = pd.read_csv(root / "PWs" / "csv" / "PWs_Digital_PPG.csv", skipinitialspace=True)
    pm = ppg.to_numpy(float)
    n_col = pm.shape[1]
    truth, rows_p, rows_u = {}, [], []
    for k in range(len(pm)):
        subj = int(pm[k, 0])
        n_s = int(np.isfinite(pm[k, 1:]).sum())
        r = m[m["subj_no"] == subj].iloc[0]
        pwv, pvr = float(r["PWV_a"]), float(r["pvr"]) / 1e8
        t = np.arange(n_s) / MOCK_FS
        dt_b = 0.42 - 0.022 * pwv                       # 20番の模擬 PPG と同じ到達の式
        ri_b = 0.10 + 0.12 * (pvr - 0.8) / 1.4          # 抵抗が大きいほど後進波が大きい
        rhoc = 10.0 * pwv                               # 特性インピーダンス（仕込む真値）
        absent = (k % MOCK_NO_B_EVERY == 0)
        cf = (MOCK_AMP, MOCK_MU_F, MOCK_SIG_F, MOCK_AL_F)
        cb = (0.0 if absent else MOCK_AMP * ri_b, MOCK_MU_F + dt_b, MOCK_SIG_B, MOCK_AL_B)
        f = skew_gaussian(t, *cf)
        b = skew_gaussian(t, *cb)
        p = f + b + MOCK_P0
        u = (f - b) / rhoc
        tb, _hb = component_peak(cb, t[0], t[-1])
        tf, _hf = component_peak(cf, t[0], t[-1])
        truth[subj] = {"rhoc": rhoc, "tb_ms": tb * 1000.0, "tf_ms": tf * 1000.0,
                       "absent": bool(absent), "n": n_s,
                       "same_min": bool(int(np.argmin(p)) == int(np.argmin(u)))}
        for src, sink in ((p, rows_p), (u, rows_u)):
            row = np.full(n_col, np.nan)
            row[0] = subj
            row[1:1 + n_s] = src
            sink.append(row)
    hdr = "Subject Number, " + ", ".join(f"pt{j}" for j in range(1, n_col))
    for name, rows in (("PWs_Digital_P.csv", rows_p), ("PWs_Digital_U.csv", rows_u)):
        q = root / "PWs" / "csv" / name
        with open(q, "w") as fh:
            fh.write(hdr + "\n")
        with open(q, "a") as fh:
            np.savetxt(fh, np.array(rows), delimiter=",", fmt="%.10g")
    return truth


def _selftest_root(td: Path, n: int = 96):
    """自己検証用の模擬 PWDB（決定的）。26番の `_selftest_root` と同じ組み立て方。"""
    L = _landmarks_module()
    root = L._make_mock(Path(td) / "exported_data", n=n)   # 真値・入力・PPG・同梱の特徴点
    truth = _mock_pu(root)
    return root, truth


def selftest(jobs: int = 4) -> int:
    import contextlib
    import io
    import tempfile
    import time
    t_all = time.time()
    print("== 51_pwdb_wave_separation 自己検証（模擬PWDB・ネットワーク不要） ==\n")
    print("  模擬の圧・流速には**真の前進波と後進波を仕込んである**ので、分離には正解がある。")
    print("  模擬の PPG（20番の `_make_mock`）とは別々に作っており、共有しているのは到達の式")
    print("  だけである。ここで確かめるのは処理系（読み込み・分離・記録・表）であって、")
    print("  手法の優劣ではない。優劣は実 PWDB でしか決まらない。\n")
    ok = True

    def rep(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}{('  ' + detail) if detail else ''}",
              flush=True)

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        root, truth = _selftest_root(td, n=96)
        rep("模擬の圧・流速で P と U の最小値が同じ標本に来る（分離に正解がある作り）",
            all(v["same_min"] for v in truth.values()),
            f"{sum(v['same_min'] for v in truth.values())}/{len(truth)} 名")

        # --- (1) 見つからないときは終了コード 2
        bad = td / "no_pu"
        (bad / "PWs" / "csv").mkdir(parents=True, exist_ok=True)
        for q in ("pwdb_haemod_params.csv", "pwdb_model_configs.csv",
                  "pwdb_pw_indices.csv", "pwdb_model_variations.csv", "pwdb_onset_times.csv"):
            if (root / q).exists():
                (bad / q).write_text((root / q).read_text())
        (bad / "PWs" / "csv" / "PWs_Digital_PPG.csv").write_text(
            (root / "PWs" / "csv" / "PWs_Digital_PPG.csv").read_text())
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            out_bad = run(bad, limit=4, jobs=1, cache_csv=td / "nope.csv")
        rep("圧・流速が無い配布物なら名前を挙げて終了コード 2 になる",
            out_bad["code"] == 2 and "PWs_Digital_P.csv" in buf.getvalue()
            and "PWs_Digital_U.csv" in buf.getvalue(),
            f"終了コード {out_bad['code']}")

        # --- (2) 本体を走らせる
        cache = td / "cache" / "51_wave_sep.csv"
        buf1 = io.StringIO()
        t0 = time.time()
        with contextlib.redirect_stdout(buf1):
            out1 = run(root, jobs=jobs, cache_csv=cache, csv26=td / "no26.csv")
        txt1 = buf1.getvalue()
        print(f"    模擬 96 名の計算に {time.time() - t0:.0f} 秒", flush=True)
        d = out1["d"]
        rep("模擬 96 名で最後まで走り、終了コード 0",
            out1["code"] == 0 and len(d) == 96, f"n={len(d)}・{len(txt1)} 文字")
        rep("3 つのファイルの標本数が被験者ごとに一致した",
            int(np.nansum(_colv(d, "same_n"))) == 96,
            f"{int(np.nansum(_colv(d, 'same_n')))}/96 名")
        rep("基線の取り方の効き（P と U の最小値の標本のずれ）が列と表に出ている",
            int(np.nansum(_colv(d, "same_min"))) == 96
            and "基線の取り方の効き" in txt1,
            f"同じ標本 {int(np.nansum(_colv(d, 'same_min')))}/96 名・"
            f"ずれの中央値 {float(np.nanmedian(_colv(d, 'min_gap_ms'))):.1f} ms")

        # --- (3) ρc と P_b のピーク時刻の復元
        have_b = d[[not truth[int(s)]["absent"] for s in d["subj_no"]]]
        err_r = np.array([abs(float(r["rhoc_loop"]) - truth[int(r["subj_no"])]["rhoc"])
                          / truth[int(r["subj_no"])]["rhoc"] for _i, r in have_b.iterrows()])
        rep("ρc 主（P–U ループ）が仕込んだ値を 5% 以内で復元する",
            bool(np.all(err_r <= 0.05)),
            f"相対誤差 最大 {100 * float(np.max(err_r)):.2f}%・中央値 "
            f"{100 * float(np.median(err_r)):.2f}%")
        err_t = np.array([abs(float(r["pb_peak_ms"]) - truth[int(r["subj_no"])]["tb_ms"])
                          for _i, r in have_b.iterrows()])
        rep("復元した P_b のピーク時刻が仕込んだ位置の 5 ms 以内",
            bool(np.all(err_t <= 5.0)),
            f"最大 {float(np.max(err_t)):.2f} ms・中央値 {float(np.median(err_t)):.2f} ms")
        ratio = _colv(have_b, "rhoc_ratio")
        rep("二乗和法の ρc も列として出ており、主との比が印字される",
            np.isfinite(_colv(have_b, "rhoc_ss")).all() and np.isfinite(ratio).all()
            and "ρc 検 中央値" in txt1,
            f"比 検/主 の中央値 {float(np.median(ratio)):.3f}"
            f"（範囲 {float(np.min(ratio)):.3f}–{float(np.max(ratio)):.3f}）")

        # --- (4) 後進波を仕込まなかった被験者
        no_b = d[[truth[int(s)]["absent"] for s in d["subj_no"]]]
        reasons = set(no_b["why_true"].astype(str))
        rep("後進波を仕込まなかった被験者は ΔT_true が欠測で、評価できない数に数えられる",
            len(no_b) > 0 and bool(np.all(~np.isfinite(_colv(no_b, "dt_true_ms"))))
            and bool(np.all(~np.isfinite(_colv(no_b, "ri_true"))))
            and bool(np.all(_colv(no_b, "true_ok") == 0))
            and reasons <= {"pb_nonpos", "pb_tiny", "pb_edge"}
            and "評価できない" in txt1,
            f"{len(no_b)} 名・理由 {sorted(reasons)}")
        rep("後進波を仕込んだ被験者は全員 ΔT_true が取れている（守りが効きすぎていない）",
            bool(np.all(_colv(have_b, "true_ok") == 1)),
            f"{int(np.nansum(_colv(have_b, 'true_ok')))}/{len(have_b)} 名")

        # --- (5) 表がすべて出て、段の定義と事後の注記が付いている
        heads = ["D0. 検算", "D1. ρc", "D2. 真の後進波", "D3. W2", "D4. W3", "D5. 読み"]
        rep("D0〜D5 の表がこの順で印字される",
            all(h in txt1 for h in heads)
            and [txt1.index(h) for h in heads] == sorted(txt1.index(h) for h in heads),
            "・".join(heads))
        rep("段を使う表（D2・D3・D4・D5）の直前に段の 1 行の定義が出ている",
            all(txt1.count("段: A 段 = その手法が自分で採用した被験者だけ") >= 4
                for _ in (0,)),
            f"{txt1.count('段: A 段 = その手法が自分で採用した被験者だけ')} 回")
        rep("すべての表の見出しに「探索・事後・事前登録した予測は無い」の注記がある",
            txt1.count(POSTHOC) >= len(heads),
            f"{txt1.count(POSTHOC)} 回（表 {len(heads)} 個）")
        rep("D0 は 26番の CSV が無いと「照合できない」になる",
            out1["d0"]["state"] == "照合できない")

        # --- (6) 再開すると当てはめ 0 件で、記録の中身が一致する
        before = cache.read_text()
        buf2 = io.StringIO()
        with contextlib.redirect_stdout(buf2):
            out2 = run(root, jobs=1, cache_csv=cache, csv26=td / "no26.csv")
        rep("再開すると計算 0 名で、記録の中身が一字一句同じ",
            "96 名中 0 名を計算する" in buf2.getvalue() and cache.read_text() == before
            and out2["code"] == 0)

        # --- (7) --limit は等間隔で、記録は _limitN の名前になる
        buf3 = io.StringIO()
        with contextlib.redirect_stdout(buf3):
            out3 = run(root, limit=6, jobs=1, cache_csv=td / "lim.csv", csv26=None)
        # 名前の規約（26番・50番と同じ）は既定の置き場で確かめる。ここでは書き込まない
        rep("--limit は等間隔に取り、記録は 51_wave_sep_limitN.csv になる",
            out3["code"] == 0 and len(out3["d"]) == 6
            and _cache_path(None, 6).name == "51_wave_sep_limit6.csv"
            and _cache_path(None, 0).name == CACHE_NAME
            and "等間隔に 6 名を取る" in buf3.getvalue(),
            f"n={len(out3['d'])}・{_cache_path(None, 6).name}")

        # --- (8) D0 の検算（自分の列を 26番の名前に付け替えた CSV を渡す）
        fake = d[["subj_no", "dt_ppg_ms", "ri_ppg", "ok_ppg", KLASS_COL]].rename(
            columns={"dt_ppg_ms": "dt_v1_ms", "ri_ppg": "ri_v1", "ok_ppg": "ok_v1"})
        p26 = td / "fake26.csv"
        fake.to_csv(p26, index=False)
        buf4 = io.StringIO()
        with contextlib.redirect_stdout(buf4):
            out4 = run(root, jobs=1, cache_csv=cache, csv26=p26)
        c0 = out4["d0"]
        rep("D0 は 26番の CSV を渡すと差の最大・採否と型の食い違いの数を出す",
            c0["state"] == "一致" and c0["dt"] <= TOL_DT_MS and c0["ri"] <= TOL_RI
            and c0["n_ok_diff"] == 0 and c0["n_klass_diff"] == 0,
            f"ΔT 最大差 {c0['dt']:.3g} ms・RI {c0['ri']:.3g}・採否 {c0['n_ok_diff']}・"
            f"型 {c0['n_klass_diff']}")

    print(f"\n  自己検証の所要 {time.time() - t_all:.0f} 秒")
    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


# ================================================================ 入口
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pwdb", type=str, default=None,
                    help="PWDB の配布物を置いたフォルダ（指尖の圧・流速も要る）")
    ap.add_argument("--csv", type=str, default=None,
                    help="26番の出力（D0 の検算。既定 data/pwdb/pwdb_compare.csv があれば使う）")
    ap.add_argument("--limit", type=int, default=0,
                    help="全体から等間隔に N 名だけ計算する（先頭 N 名ではない。0=全員）")
    ap.add_argument("--jobs", type=int, default=1, help="並列数（26番・50番と同じ）")
    ap.add_argument("--cache-csv", type=str, default=None,
                    help="記録の場所（既定 data/pwdb/51_wave_sep.csv。--limit なら "
                         "51_wave_sep_limitN.csv）")
    ap.add_argument("--no-resume", action="store_true",
                    help="記録を使わずに全員を計算し直す（既定は再開する）")
    ap.add_argument("--selftest", action="store_true",
                    help="模擬の配布物で計算の筋道を検算する（配布物もネットワークも要らない）")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())
    if args.jobs < 1:
        ap.error("--jobs は 1 以上")
    if args.limit < 0:
        ap.error("--limit は 0 以上（0 = 全員）")
    if not args.pwdb:
        print_missing("--pwdb を指定してください（--selftest なら不要）。")
        sys.exit(2)
    csv26 = args.csv if args.csv else (str(DEFAULT_CSV) if DEFAULT_CSV.exists() else None)
    out = run(Path(args.pwdb), limit=args.limit, jobs=args.jobs,
              cache_csv=args.cache_csv, resume=not args.no_resume, csv26=csv26)
    sys.exit(out.get("code", 0))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探索的（事後）: 第2成分が収縮期に入る割合（成分の入れ替わり）と、同梱 PTT と真の伝播時間の差。

**これは事後の探索であり、論文2 の事前規準による判定は動かさない。**
26番（`26_pwdb_compare.py`）で下した判定はそのまま有効で、この台本の出力は
すべて「探索的（事後）」として読む。著者の問い（2026-09-12）は 2 つある。

    Q1 凍結版の分解で第2成分が収縮期に入る（成分の入れ替わり）のはどれくらいの頻度か。
       入れ替わった被験者を除くと判定は変わるか。
    Q2 同梱の脈波到達時間が年齢層内で大動脈PWV と 0.571 しか相関しないのはなぜか。
       立ち上がり時刻の表から出した真の伝播時間は −0.99 なのに、である。

予測（2026-09-12。**計算の前に固定した。**監督者による）
----------------------------------------------------------
**Q1 について。**入れ替わりは脈波伝播速度 +1 SD と、心拍数が速い／駆出時間が短い側に
集まる。全体ではおよそ 20〜40% の被験者で起きる。入れ替わった被験者を除いても
|ρ| は 0.30 には届かない。除外はまさに最も硬い被験者を取り除く操作で、脈波伝播速度の
幅を狭めるから、相関は下がるか横ばいになると考えられる。**もし除外後に |ρ| が 0.30 を
超えたなら、そのことをはっきり書く。それは所見である。**

**Q2 について。**候補は 2 つある。

    (a) 検出のずれ。同梱の到達時間は波形上で検出した特徴点であり、検出点は波形の形と
        ともに動く。形は心拍数や大動脈径でも変わる。この場合、|d| は小さく（数 ms）、
        1 周期に相当する外れ値は出ず、d は心拍数か大動脈径と相関する。
    (b) 周期の取り違え（第2版 README に書いた仮説）。この場合、|d| が 1 周期ほどの
        部分集団が出る。

どちらをデータが支持するかを述べる。

照合の規準（これも計算の前に決める。`3. 予測との照合` の節はこの 6 条で判定する）

    Q1-P1  入れ替わりの全体の割合が 0.20 以上 0.40 以下
    Q1-P2  入れ替わりが (i) 脈波伝播速度 +1 SD で −1 SD より多い、(ii) 心拍数 +1 SD で
           −1 SD より多い、(iii) 駆出時間 −1 SD（短い）で +1 SD より多い
    Q1-P3  入れ替わりを除いた年齢層内の中央値 |ρ| が、ΔT × 大動脈PWV・RI × 末梢血管抵抗
           のどちらも 0.30 未満（超えたら「予測に反して上がった」と明記する）
    Q2-P1  (a) の側: |d| の中央値が 20 ms 未満（大多数のずれが小さい）
    Q2-P2  (a) の側: d と心拍数、または d と大動脈径の年齢層内 |ρ| が 0.30 以上
    Q2-P3  (b) の側: 半周期を超える割合が 0.05 以上
           P1 と P3 の組み合わせで (a)／(b)／両方が混じる／どちらでもない を述べる。
           **両方が立つことはありうる。**その場合はそう書き、どちらか一方に寄せない。

計算するもの
------------
**Q1。**凍結版（`*_v1`）が CSV に持っているのは ΔT（`dt_v1_ms`）と RI（`ri_v1`）だけで、
成分のピーク時刻そのものは保存されていない（26番 `26_pwdb_compare.py` の
`out.update(dt_v1_ms=ix["dt_s"] * 1000.0, ri_v1=ix["ri"], ...)` の行）。そこで

    第2成分のピーク時刻 ≈ digital_ppgsys_t + dt_v1_ms   （**近似である**）

とし、これが切痕の時刻 `digital_ppgdic_t` より早ければ「入れ替わり」とする。つまり
第2成分が拡張期波ではなく収縮期後半の波を拾っている状態である。近似の誤差は、第2版が
成分ピークの絶対時刻を保存している（`tf_v2_ms`・`tr_v2_ms`。26番の同じ関数）ので、
`tf_v2_ms − digital_ppgsys_t` の分布として表に出す。第2版の厳密なピーク時刻による
入れ替わりの割合も参考に並べる。

特徴点の時刻は PWDB 同梱の値である（23番 `23_pwdb_landmarks.py` の `_to_ms` で ms に
換算してから 26番の CSV に入っている）。

    digital_ppgsys_t  収縮期ピークの時刻
    digital_ppgdic_t  切痕（dicrotic notch）の時刻
    digital_ppgdia_t  拡張期ピークの時刻

**Q2。**同梱の脈波到達時間は `digital_ptt`（26番の PAIRS の
`("digital_ptt", "PWV_a", -1, None, "PTT      モデル出力（陽性対照）")` の行。これが
陽性対照の 0.571 を出した列）。真の伝播時間は `ptt_root_fin_ms`
＝ `on_digital_ppg − on_aorticroot_p`（20番 `20_pwdb_validity.py` の `report` が
`pwdb_onset_times.csv` から作る列。これが −0.99 を出した量）。

    d = digital_ptt − ptt_root_fin_ms   [ms]
    半周期 = 60 / HR / 2 秒 = 30000 / HR  [ms]

**`ptt_root_fin_ms` は 26番の CSV には入っていない。**26番は立ち上がり時刻の表を
結合していない。この台本は次の順に探す。

    1 `--csv` の CSV に `ptt_root_fin_ms`（または `on_digital_ppg` と `on_aorticroot_p`）がある
    2 `--indices`（既定 `data/pwdb/pwdb_indices.csv`。20番の被験者別出力）にある
    3 `--pwdb` のフォルダにある `pwdb_onset_times.csv`（20番の `load_extras` で読む）

どれも無ければ Q2 の真値側は計算せず、そのことを出力に書く（終了コード 2）。

規約
----
年齢層内 Spearman ρ の規約は 26番・23番・20番と共有する（`20_pwdb_validity.py` の
`_spearman`・`_by_age`・`_judge` をそのまま読み込む）。年齢層は `age` の相異なる値
（6 層）、1 層に 8 名以上、まとめは年齢層をまたいだ |ρ| の中央値と、予測の向きの層数である。
因子の水準は 20番の `_factor_effects` と同じ規則で `var_pwv` 等から読む
（`> 0.5` を +1 SD、`< -0.5` を −1 SD、それ以外を基準）。**判定（成立・不成立）は
出さない。**事前規準による判定は 26番のものが有効で、事後の探索で上書きしない。

相関は対応のある行（pairwise-complete）で取る。これは 26番の C 段（採否を無視した全例）に
当たる。26番にはもう一つ A 段（その手法が自分で採用した例だけ＝`ok_v1 == 1`）があるので、
節 0 ではその値も参考に出す（照合の合否には使わない）。

データ
------
`data/pwdb/pwdb_compare.csv`（26番の出力）。**確認的解析を回した機械では 4,374 行**
（仮想被験者 1 名 1 行）。**クラウド側の複製は 24 行しかなく、1 層 4 名で 8 名に
満たないため、どの ρ も計算できない。**自己検査で動くことだけを確かめる用途にしか
使えない。

使い方
------
自己検査（CSV は要らない。合成データで筋道を検算する）

    python3 analysis/scripts/46_pwdb_swap_and_ptt.py --selftest

本番（既定は data/pwdb/pwdb_compare.csv）

    python3 analysis/scripts/46_pwdb_swap_and_ptt.py
    python3 analysis/scripts/46_pwdb_swap_and_ptt.py --csv data/pwdb/pwdb_compare.csv

真の伝播時間も照合する（立ち上がり時刻の表がある機械）

    python3 analysis/scripts/46_pwdb_swap_and_ptt.py --pwdb ~/pwdb
    python3 analysis/scripts/46_pwdb_swap_and_ptt.py --indices data/pwdb/pwdb_indices.csv

終了コード 0 = 既知の値と一致、1 = ★ずれ（入力が論文2 と違う）、2 = 照合できない
（層の人数が足りない、または真の伝播時間が手に入らない。24 行の複製はここに落ちる）。
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
    """数字始まりの台本を名前で読み込む（import 文では書けない）。26番・45番と同じ手口。"""
    p = Path(__file__).resolve().parent / stem
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# 判定の規約は 20番のものをそのまま使う（自前で書き直さない。26番・45番と同じ）
M = _load("20_pwdb_validity.py", "m20")
# 時刻列の秒→ms 換算は 23番のものを使う（同じ規則で二度書かない）
L = _load("23_pwdb_landmarks.py", "m23")

DATA = ROOT / "data"
DEFAULT_CSV = DATA / "pwdb" / "pwdb_compare.csv"
DEFAULT_INDICES = DATA / "pwdb" / "pwdb_indices.csv"

MIN_PER_AGE = 8        # 1 年齢層に要る人数。26番・45番の MIN_PER_AGE と同じ
N_AGES_FULL = 6        # PWDB の年齢層（25・35・45・55・65・75 歳）
N_FULL = 4374          # 確認的解析を回した機械の行数

# 論文2 で確定している年齢層内の中央値 |ρ|。ここが再現しなければ入力が論文2 と違う。
# (指標, 真値) -> (中央値|ρ|, 予測の向き, 表示名, 出典)
KNOWN = {
    ("dt_v1_ms", "PWV_a"):
        (0.223, -1, "ΔT 凍結PDA × 大動脈PWV",
         "lab_log 2026-09-03 の Q1 の表"),
    ("ri_v1", "pvr"):
        (0.207, +1, "RI 凍結PDA × 末梢血管抵抗",
         "lab_log 2026-09-03 の Q2 の表"),
    ("digital_ptt", "PWV_a"):
        (0.571, -1, "同梱 PTT × 大動脈PWV（陽性対照）",
         "lab_log 2026-09-03 の表／26番 2026-09-09（0.571）"),
    ("ptt_root_fin_ms", "PWV_a"):
        (0.99, -1, "立ち上がり時刻表の真の伝播時間 × 大動脈PWV",
         "lab_log 2026-09-03 §5 真の伝播時間（−0.99）"),
}
TOL_KNOWN = 0.02

# 予測の規準（docstring の Q1-P1〜Q2-P3。計算の前に固定した）
PRED_SWAP_LO, PRED_SWAP_HI = 0.20, 0.40   # Q1-P1 入れ替わりの全体の割合
PRED_RHO_RISE = 0.30                      # Q1-P3 除外後にここを超えたら「上がった」と書く
PRED_D_SMALL_MS = 20.0                    # Q2-P1 |d| の中央値がこれ未満なら検出のずれ側
PRED_D_RHO = 0.30                         # Q2-P2 d と心拍数／大動脈径の |ρ|
PRED_CYCLE_FRAC = 0.05                    # Q2-P3 半周期を超える割合

# 因子の水準を読む列（20番の FACTORS と同じ名前）と、予測が名指しする向き
FACTOR_COLS = [("pwv", "脈波伝播速度"), ("hr", "心拍数"), ("lvet", "駆出時間"),
               ("dia", "大動脈径"), ("mbp", "平均血圧"), ("sv", "1回拍出量")]
LEVEL_LABEL = {-1: "−1 SD", 0: "基準", +1: "+1 SD"}

# 入れ替わりの判定に要る列
T_SYS, T_DIC, T_DIA = "digital_ppgsys_t", "digital_ppgdic_t", "digital_ppgdia_t"
DT_V1, RI_V1, OK_V1 = "dt_v1_ms", "ri_v1", "ok_v1"

# Q1 の年齢層内相関で並べる対。(指標, 真値, 予測の向き, 表示名)
Q1_PAIRS = [(DT_V1, "PWV_a", -1, "ΔT 凍結PDA × 大動脈PWV"),
            (RI_V1, "pvr", +1, "RI 凍結PDA × 末梢血管抵抗")]

# 数値に直しておく列（文字列のまま渡すと 20番の _by_age が落ちる）
NUMERIC = [T_SYS, T_DIC, T_DIA, DT_V1, RI_V1, OK_V1, "age", "HR", "lvet",
           "PWV_a", "pvr", "dia_asca", "digital_ptt", "tf_v2_ms", "tr_v2_ms",
           "subj_no", "ptt_root_fin_ms", "on_digital_ppg", "on_aorticroot_p"] \
          + [f"var_{f}" for f, _lab in FACTOR_COLS]


# ---------------------------------------------------------------- 表示の部品
def _pad(s: str, w: int, right: bool = False) -> str:
    """表示幅で揃える（日本語は 2 文字分。f 文字列の桁指定は文字数なのでずれる）。"""
    import unicodedata
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


def _pct(v: float) -> str:
    return "—" if not np.isfinite(v) else f"{100.0 * v:.1f}%"


def _yn(b) -> str:
    return "—" if b is None else ("はい" if b else "いいえ")


# ---------------------------------------------------------------- 計算の部品
def _col(d: pd.DataFrame, c: str) -> np.ndarray:
    if c not in d.columns:
        return np.full(len(d), np.nan)
    return pd.to_numeric(d[c], errors="coerce").to_numpy(dtype=float)


EMPTY = {"rows": [], "med_abs": float("nan"), "med": float("nan"),
         "n_ok": 0, "n_ages": 0, "min_n": 0, "n_tot": 0}


def strat(d: pd.DataFrame, x: str, y: str, sign: int = 0) -> dict:
    """年齢層内 Spearman の一式。規約は 20番の `_by_age`・`_judge` をそのまま使う。"""
    if len(d) == 0 or "age" not in d.columns or x not in d.columns or y not in d.columns:
        return dict(EMPTY)
    rows = M._by_age(d, x, y, min_n=MIN_PER_AGE)
    fin = [(a, r, n) for a, r, n in rows if np.isfinite(r)]
    if not fin:
        out = dict(EMPTY)
        out["rows"] = rows
        return out
    j = M._judge(rows, sign)
    return {"rows": rows,
            "med_abs": j["med_abs"],
            "med": float(np.median([r for _a, r, _n in fin])),
            "n_ok": j["n_ok"], "n_ages": j["n_ages"],
            "min_n": min(n for _a, _r, n in fin),
            "n_tot": int(sum(n for _a, _r, n in fin))}


def levels_of(v: np.ndarray) -> np.ndarray:
    """因子の水準（−1 / 0 / +1）。規則は 20番の `_factor_effects` と同じ。"""
    out = np.full(v.size, np.nan)
    out[v > 0.5] = 1.0
    out[v < -0.5] = -1.0
    out[(v >= -0.5) & (v <= 0.5)] = 0.0
    return out


def add_swap(d: pd.DataFrame) -> pd.DataFrame:
    """第2成分のピーク時刻（近似）と入れ替わりの旗を足す。元の表は書き換えない。"""
    d = d.copy()
    for c in NUMERIC:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    sys_t, dic_t, dt1 = _col(d, T_SYS), _col(d, T_DIC), _col(d, DT_V1)
    t2 = sys_t + dt1
    d["t2_v1_ms"] = t2
    ok = np.isfinite(t2) & np.isfinite(dic_t)
    swap = np.full(len(d), np.nan)
    swap[ok] = (t2[ok] < dic_t[ok]).astype(float)
    d["swap_v1"] = swap
    # 第2版は成分ピークの絶対時刻を持つ（26番の tf_v2_ms・tr_v2_ms）。厳密な入れ替わり
    tr2 = _col(d, "tr_v2_ms")
    ok2 = np.isfinite(tr2) & np.isfinite(dic_t)
    sw2 = np.full(len(d), np.nan)
    sw2[ok2] = (tr2[ok2] < dic_t[ok2]).astype(float)
    d["swap_v2"] = sw2
    # 近似の誤差: 同梱の収縮期ピークを第1成分のピーク時刻に使ったときのずれ
    d["tf_minus_sys_ms"] = _col(d, "tf_v2_ms") - sys_t
    return d


def frac(flag: np.ndarray) -> tuple[float, int, int]:
    """旗（1/0/NaN）の割合・該当数・判定できた数。"""
    ok = np.isfinite(flag)
    n = int(ok.sum())
    if n == 0:
        return float("nan"), 0, 0
    k = int(np.nansum(flag[ok]))
    return k / n, k, n


def q(v: np.ndarray, ps=(5, 25, 50, 75, 95)) -> list[float]:
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return [float("nan")] * len(ps)
    return [float(x) for x in np.percentile(v, ps)]


# ---------------------------------------------------------------- 真の伝播時間
def attach_true_ptt(d: pd.DataFrame, indices: Path | None,
                    pwdb: Path | None) -> tuple[pd.DataFrame, str]:
    """真の伝播時間 `ptt_root_fin_ms` を足す。26番の CSV には入っていないので外から探す。

    返り値は (表, どこから取ったかの説明)。取れなければ説明だけを返す。
    """
    d = d.copy()
    if "ptt_root_fin_ms" in d.columns and np.isfinite(_col(d, "ptt_root_fin_ms")).any():
        return d, "--csv の CSV に ptt_root_fin_ms があった"
    if {"on_digital_ppg", "on_aorticroot_p"} <= set(d.columns):
        d["ptt_root_fin_ms"] = _col(d, "on_digital_ppg") - _col(d, "on_aorticroot_p")
        return d, "--csv の CSV の on_digital_ppg − on_aorticroot_p から作った"

    if indices is not None and Path(indices).exists() and "subj_no" in d.columns:
        idx = pd.read_csv(indices)
        if "subj_no" in idx.columns:
            if "ptt_root_fin_ms" not in idx.columns and \
                    {"on_digital_ppg", "on_aorticroot_p"} <= set(idx.columns):
                idx["ptt_root_fin_ms"] = (pd.to_numeric(idx["on_digital_ppg"], errors="coerce")
                                          - pd.to_numeric(idx["on_aorticroot_p"], errors="coerce"))
            if "ptt_root_fin_ms" in idx.columns:
                d = d.merge(idx[["subj_no", "ptt_root_fin_ms"]], on="subj_no", how="left")
                return d, f"{indices}（20番の被験者別出力）から結合した"

    if pwdb is not None and "subj_no" in d.columns:
        try:
            extras = M.load_extras(Path(pwdb))
        except Exception as e:                                   # noqa: BLE001
            return d, f"--pwdb を読めなかった: {str(e)[:60]}"
        if "onsets" in extras:
            on = M._onsets_ms(extras["onsets"])
            on = on.copy()
            on["ptt_root_fin_ms"] = (pd.to_numeric(on["on_digital_ppg"], errors="coerce")
                                     - pd.to_numeric(on["on_aorticroot_p"], errors="coerce"))
            d = d.merge(on[["subj_no", "ptt_root_fin_ms"]], on="subj_no", how="left")
            return d, f"{pwdb} の pwdb_onset_times.csv から結合した（20番の load_extras）"
        return d, f"{pwdb} に立ち上がり時刻の表が無かった"
    return d, "見つからない"


def add_diff(d: pd.DataFrame) -> pd.DataFrame:
    """d = 同梱 PTT − 真の伝播時間、および半周期。"""
    d = d.copy()
    d["d_ptt_ms"] = _col(d, "digital_ptt") - _col(d, "ptt_root_fin_ms")
    hr = _col(d, "HR")
    with np.errstate(divide="ignore", invalid="ignore"):
        cyc = np.where(hr > 0, 60000.0 / hr, np.nan)        # 1 心周期 [ms]
    d["cycle_ms"] = cyc
    d["halfcycle_ms"] = cyc / 2.0
    return d


# ---------------------------------------------------------------- 節 0
def check_known(d: pd.DataFrame, have_true: bool) -> tuple[int, list[str]]:
    """節 0。既知の 4 つの値（0.223・0.207・0.571・−0.99）を再現するか。"""
    print(f"\n{'-' * 100}")
    print(f"0. 論文2 の既知の値を再現するか（年齢層内 Spearman の中央値 |ρ|。許容差 {TOL_KNOWN}）")
    print("-" * 100)
    print(_pad("指標 × 真値", 44) + _pad("論文2", 9, right=True)
          + _pad("この機械", 10, right=True) + _pad("差", 9, right=True)
          + _pad("向きの層", 10, right=True) + "   照合")
    notes, cannot = [], False
    for (col, tgt), (known, sign, lab, _src) in KNOWN.items():
        if col == "ptt_root_fin_ms" and not have_true:
            print(_pad(lab, 44) + f"{known:>9.3f}" + _pad("—", 10, right=True)
                  + _pad("—", 9, right=True) + _pad("—", 10, right=True)
                  + "   照合できない（真の伝播時間の列が無い）")
            cannot = True
            continue
        s = strat(d, col, tgt, sign)
        got = s["med_abs"]
        if not np.isfinite(got):
            mark = "照合できない（8 名以上の年齢層が無い）"
            cannot = True
        elif abs(got - known) <= TOL_KNOWN:
            mark = "一致"
        else:
            mark = "★ずれ"
            notes.append(f"{lab}: 論文2 {known:.3f} に対し {got:.3f}")
        ok = f"{s['n_ok']}/{s['n_ages']}" if s["n_ages"] else "—"
        print(_pad(lab, 44) + f"{known:>9.3f}" + _f(got, 10)
              + _f(got - known if np.isfinite(got) else float("nan"), 9, sign=True)
              + _pad(ok, 10, right=True) + f"   {mark}")
    print("  出典（論文2 側）:")
    for (_c, _t), (known, _s, lab, src) in KNOWN.items():
        print(f"    {lab} {known:.3f} … {src}")
    print("  この機械の側はすべて、この台本（46番）が --csv の CSV から計算した値。")
    print("  照合は対応のある行（pairwise-complete）で、26番の C 段（採否を無視した全例）に当たる。")
    # 20番の Q1・Q2 は ok2（2カーネルが収束した 92%）で計算されている。26番の A 段に当たる
    if OK_V1 in d.columns:
        a = d[_col(d, OK_V1) == 1]
        for col, tgt, sign in ((DT_V1, "PWV_a", -1), (RI_V1, "pvr", +1)):
            s_a = strat(a, col, tgt, sign)
            print(f"  （参考）26番 A 段（{OK_V1} == 1 の {len(a)} 名だけ）の {col} × {tgt}: "
                  f"中央値|ρ| {_n(s_a['med_abs'])}・層 {s_a['n_ages']}・最小n {s_a['min_n']}")
        print("  （20番の Q1・Q2 は 2カーネルが収束した例＝A 段で計算されている。採択 92% なので")
        print("    C 段とは近いが同じではない。照合の合否は上の C 段で見る。）")
    state = 1 if notes else (2 if cannot else 0)
    if state == 1:
        print("\n  ★ 入力が論文2 と違う。**この先の表を論文2 の続きとして読んではいけない。**")
        for x in notes:
            print(f"    {x}")
    elif state == 2:
        print("\n  ★ 照合できない項がある。**この先の数値を論文2 の続きとして読んではいけない。**")
    return state, notes


# ---------------------------------------------------------------- 節 1（Q1）
def q1_report(d: pd.DataFrame) -> dict:
    print(f"\n{'-' * 100}")
    print("1. Q1 第2成分が収縮期に入る割合（成分の入れ替わり）と、除いたときの年齢層内相関")
    print("-" * 100)
    print("  定義: 第2成分のピーク時刻 < 切痕の時刻 digital_ppgdic_t なら「入れ替わり」")
    print("        （第2成分が拡張期波ではなく収縮期後半の波を拾っている）。")
    print("  **凍結版は CSV に ΔT しか持たないので、第2成分のピーク時刻は近似である**:")
    print(f"        t2 ≈ {T_SYS} + {DT_V1}（26番の out.update(dt_v1_ms=..., ri_v1=...) の行）。")

    out: dict = {}
    sw = _col(d, "swap_v1")
    f_all, k_all, n_all = frac(sw)
    n_undef = int(np.isfinite(_col(d, DT_V1)).sum() - n_all) if DT_V1 in d.columns else 0
    out["frac_all"], out["k_all"], out["n_all"] = f_all, k_all, n_all
    print(f"\n  1a. 全体: 入れ替わり {k_all} / 判定できた {n_all} 名 = {_pct(f_all)}"
          f"（切痕か ΔT が欠けて判定できない {max(0, n_undef)} 名は除く）")

    # 近似の検算（第2版は成分ピークの絶対時刻を持つ）
    off = _col(d, "tf_minus_sys_ms")
    if np.isfinite(off).any():
        o5, o25, o50, o75, o95 = q(off)
        print(f"      近似の検算: tf_v2_ms − {T_SYS} の中央値 {o50:.1f} ms"
              f"（四分位 {o25:.1f}〜{o75:.1f}・5–95% {o5:.1f}〜{o95:.1f}、"
              f"{int(np.isfinite(off).sum())} 名）。")
        print("      これが 0 に近いほど、同梱の収縮期ピークを第1成分のピーク時刻に使う近似が効く。")
    f2, k2, n2 = frac(_col(d, "swap_v2"))
    out["frac_v2"] = f2
    if n2:
        print(f"      （参考）第2版の厳密なピーク時刻 tr_v2_ms による入れ替わり: "
              f"{k2} / {n2} = {_pct(f2)}。別の分解なので値は一致しない。")

    # 1b. 年齢層ごと
    print("\n  1b. 年齢層ごとの入れ替わりの割合")
    print("      " + _pad("年齢", 8) + _pad("入れ替わり", 12, right=True)
          + _pad("判定できた n", 14, right=True) + _pad("割合", 9, right=True))
    rows_age = []
    if "age" in d.columns:
        for age, g in d.groupby("age", sort=True):
            fa, ka, na = frac(_col(g, "swap_v1"))
            rows_age.append((float(age), fa, ka, na))
            print("      " + _pad(f"{int(age)} 歳", 8) + _pad(ka, 12, right=True)
                  + _pad(na, 14, right=True) + _pad(_pct(fa), 9, right=True))
    out["by_age"] = rows_age

    # 1c. 因子の水準ごと
    print("\n  1c. 振った因子の水準ごとの入れ替わりの割合"
          "（水準は 20番の `_factor_effects` と同じ規則で var_* から読む）")
    print("      " + _pad("因子", 16) + "".join(_pad(LEVEL_LABEL[lv], 20, right=True)
                                                for lv in (-1, 0, 1)))
    by_factor: dict = {}
    for f, lab in FACTOR_COLS:
        c = f"var_{f}"
        if c not in d.columns:
            continue
        lv = levels_of(_col(d, c))
        cells, line = {}, "      " + _pad(lab, 16)
        for want in (-1, 0, 1):
            sel = lv == want
            fa, ka, na = frac(_col(d, "swap_v1")[sel])
            cells[want] = (fa, ka, na)
            line += _pad(f"{_pct(fa)} ({ka}/{na})", 20, right=True)
        by_factor[f] = cells
        print(line)
    out["by_factor"] = by_factor
    if not by_factor:
        print("      （var_* の列が無いので水準別は出せない）")
    else:
        print("      括弧内は 入れ替わり数／判定できた数。ある水準の n が 0 なら、この CSV に")
        print("      その水準の被験者がいない（部分集合ではよく起きる）。")

    # 1c'. 入れ替わった側の心拍数・駆出時間（水準列が無くても読める記述）
    print("\n  1c'. 入れ替わった側とそうでない側の心拍数・駆出時間・大動脈PWV（中央値）")
    print("      " + _pad("群", 22) + _pad("n", 7, right=True)
          + _pad("HR [bpm]", 12, right=True) + _pad("LVET [ms]", 12, right=True)
          + _pad("PWV_a [m/s]", 13, right=True))
    grp = {}
    for name, sel in (("入れ替わりあり", sw == 1), ("入れ替わりなし", sw == 0)):
        g = d[sel]
        vals = tuple(float(np.nanmedian(_col(g, c))) if len(g) and np.isfinite(_col(g, c)).any()
                     else float("nan") for c in ("HR", "lvet", "PWV_a"))
        grp[name] = (len(g),) + vals
        print("      " + _pad(name, 22) + _pad(len(g), 7, right=True)
              + _f(vals[0], 12, 1) + _f(vals[1], 12, 1) + _f(vals[2], 13, 2))
    out["groups"] = grp

    # 1d. 除外して年齢層内相関を取り直す
    print("\n  1d. 入れ替わりを除くと年齢層内 Spearman ρ は変わるか（探索的・事後）")
    print("      " + _pad("指標 × 真値", 34) + _pad("部分集合", 22)
          + _pad("中央値|ρ|", 11, right=True) + _pad("ρ中央値", 10, right=True)
          + _pad("向きの層", 10, right=True) + _pad("最小n", 8, right=True)
          + _pad("計 n", 8, right=True))
    subsets = [("(a) 全例", d),
               ("(b) 入れ替わりを除く", d[sw == 0]),
               ("(c) 入れ替わりだけ", d[sw == 1])]
    tbl: dict = {}
    for col, tgt, sign, lab in Q1_PAIRS:
        first = True
        for sname, sub in subsets:
            s = strat(sub, col, tgt, sign)
            tbl[(col, tgt, sname)] = s
            ok = f"{s['n_ok']}/{s['n_ages']}" if s["n_ages"] else "—"
            print("      " + _pad(lab if first else "", 34) + _pad(sname, 22)
                  + _f(s["med_abs"], 11) + _f(s["med"], 10, sign=True)
                  + _pad(ok, 10, right=True) + _pad(s["min_n"] or "—", 8, right=True)
                  + _pad(s["n_tot"] or "—", 8, right=True))
            first = False
    out["rho"] = tbl
    print("      「向きの層」は予測の向き（ΔT×PWV は負、RI×抵抗は正）に一致した層数／ρ を")
    print(f"      計算できた層数。1 層 {MIN_PER_AGE} 名以上（20番の `_by_age` の既定）。")
    print("      **判定（成立・不成立）は出さない。**事前規準による判定は 26番のものが有効で、")
    print("      この表は事後の探索なので上書きしない。")
    print("      出典: この台本（46番）が --csv の CSV から計算した値。")
    return out


# ---------------------------------------------------------------- 節 2（Q2）
def q2_report(d: pd.DataFrame, have_true: bool, src_true: str) -> dict:
    print(f"\n{'-' * 100}")
    print("2. Q2 同梱の脈波到達時間と、立ち上がり時刻表の真の伝播時間との差 d")
    print("-" * 100)
    print("  同梱の到達時間 = digital_ptt（26番の PAIRS の陽性対照の行。0.571 を出した列）")
    print("  真の伝播時間   = ptt_root_fin_ms = on_digital_ppg − on_aorticroot_p")
    print("                   （20番の report が pwdb_onset_times.csv から作る列。−0.99 を出した量）")
    print("  d = digital_ptt − ptt_root_fin_ms [ms]、半周期 = 60/HR/2 秒 = 30000/HR [ms]")
    print(f"  真の伝播時間の出どころ: {src_true}")

    out: dict = {}
    if not have_true:
        print("\n  ★ 真の伝播時間が手に入らないので d は計算できない。")
        print("    **26番の pwdb_compare.csv は立ち上がり時刻の表を結合していない。**")
        print("    次のどちらかで渡すと計算できる。")
        print("        python3 analysis/scripts/46_pwdb_swap_and_ptt.py --pwdb ~/pwdb")
        print("        python3 analysis/scripts/46_pwdb_swap_and_ptt.py --indices data/pwdb/pwdb_indices.csv")
        # 真値が無くても同梱側の年齢層内相関だけは出せる（0.571 の再現）
        s = strat(d, "digital_ptt", "PWV_a", -1)
        print(f"\n  参考: 同梱 PTT × 大動脈PWV の年齢層内 中央値|ρ| {_n(s['med_abs'])}"
              f"（負の層 {s['n_ok']}/{s['n_ages']}・最小n {s['min_n']}）")
        out["supplied"] = s
        return out

    dd = _col(d, "d_ptt_ms")
    half = _col(d, "halfcycle_ms")
    cyc = _col(d, "cycle_ms")
    ok = np.isfinite(dd)
    n = int(ok.sum())
    d5, d25, d50, d75, d95 = q(dd)
    a50 = float(np.nanmedian(np.abs(dd))) if n else float("nan")
    out.update(n=n, med=d50, iqr=(d25, d75), med_abs=a50)
    print(f"\n  2a. d の分布（{n} 名）")
    print(f"      中央値 {_n(d50, 1)} ms・四分位 {_n(d25, 1)}〜{_n(d75, 1)} ms"
          f"（四分位範囲 {_n(d75 - d25, 1)} ms）・5–95% {_n(d5, 1)}〜{_n(d95, 1)} ms")
    print(f"      |d| の中央値 {_n(a50, 1)} ms")
    c5, c25, c50, c75, c95 = q(cyc)
    print(f"      参考: 心周期 60/HR の中央値 {_n(c50, 1)} ms（5–95% {_n(c5, 1)}〜{_n(c95, 1)}）、"
          f"半周期の中央値 {_n(c50 / 2.0, 1)} ms")

    big = np.full(len(d), np.nan)
    m = ok & np.isfinite(half)
    big[m] = (np.abs(dd[m]) > half[m]).astype(float)
    f_big, k_big, n_big = frac(big)
    out["frac_half"] = f_big
    # 「ほぼ 1 周期」の帯（0.8〜1.2 周期）。(b) 周期の取り違えの署名
    near = np.full(len(d), np.nan)
    m2 = ok & np.isfinite(cyc) & (cyc > 0)
    r_ = np.abs(dd[m2]) / cyc[m2]
    near[m2] = ((r_ >= 0.8) & (r_ <= 1.2)).astype(float)
    f_near, k_near, n_near = frac(near)
    out["frac_near_cycle"] = f_near
    # 周期超えを除いた側の散らばり（検出のずれの大きさは、こちらで読む）
    inl = ok & np.isfinite(half) & (np.abs(dd) <= half)
    i25, i50, i75 = (q(np.abs(dd[inl]), ps=(25, 50, 75)) if inl.any()
                     else [float("nan")] * 3)
    out["med_abs_inlier"] = i50
    print("\n  2b. 周期に相当する大きさのずれがあるか")
    print(f"      |d| > 半周期（30000/HR ms）: {k_big} / {n_big} = {_pct(f_big)}")
    print(f"      |d| が 1 周期の 0.8〜1.2 倍:  {k_near} / {n_near} = {_pct(f_near)}")
    print(f"      周期超えを除いた {int(inl.sum())} 名の |d|: 中央値 {_n(i50, 1)} ms"
          f"（四分位 {_n(i25, 1)}〜{_n(i75, 1)}）")
    print("      周期ほどの大きさのずれは周期の取り違えを指す。小さな散らばりだけなら")
    print("      波形上の検出のずれを指す。両方が同時にあることもある。")

    print("\n  2c. d は何と動くか（年齢層内 Spearman。形に依存する検出のずれなら形の因子と相関する）")
    print("      " + _pad("対", 34) + _pad("中央値|ρ|", 11, right=True)
          + _pad("ρ中央値", 10, right=True) + _pad("層", 6, right=True)
          + _pad("最小n", 8, right=True))
    corr = {}
    for tgt, lab in (("HR", "d × 心拍数 HR"), ("dia_asca", "d × 大動脈径 dia_asca"),
                     ("PWV_a", "d × 大動脈PWV"), ("lvet", "d × 駆出時間 lvet")):
        s = strat(d, "d_ptt_ms", tgt, 0)
        corr[tgt] = s
        print("      " + _pad(lab, 34) + _f(s["med_abs"], 11) + _f(s["med"], 10, sign=True)
              + f"{s['n_ages']:>6}{s['min_n']:>8}")
    out["corr"] = corr

    print("\n  2d. 2 つの量そのものと大動脈PWV の年齢層内 Spearman（節 0 の再現と同じ値）")
    print("      " + _pad("対", 44) + _pad("中央値|ρ|", 11, right=True)
          + _pad("ρ中央値", 10, right=True) + _pad("向きの層", 10, right=True)
          + _pad("最小n", 8, right=True))
    for col, lab, known in (("digital_ptt", "同梱 PTT × 大動脈PWV", 0.571),
                            ("ptt_root_fin_ms", "真の伝播時間 × 大動脈PWV", 0.99)):
        s = strat(d, col, "PWV_a", -1)
        out[col] = s
        ok_ = f"{s['n_ok']}/{s['n_ages']}" if s["n_ages"] else "—"
        print("      " + _pad(lab, 44) + _f(s["med_abs"], 11) + _f(s["med"], 10, sign=True)
              + _pad(ok_, 10, right=True) + _pad(s["min_n"] or "—", 8, right=True)
              + f"   （論文2 {known:.3f}）")
    print("      出典: この台本（46番）が --csv と立ち上がり時刻の表から計算した値。")
    print("      論文2 側は lab_log 2026-09-03（同梱 PTT 0.571・真の伝播時間 −0.99）。")
    return out


# ---------------------------------------------------------------- 節 3
def compare_prediction(q1: dict, q2: dict, state: int, have_true: bool) -> None:
    print(f"\n{'-' * 100}")
    print("3. 予測との照合（予測は 2026-09-12 に、計算の前に固定した。docstring と同文）")
    print("-" * 100)
    print("  Q1 の予測: 入れ替わりは脈波伝播速度 +1 SD と、心拍数が速い／駆出時間が短い側に集まる。")
    print(f"             全体でおよそ {PRED_SWAP_LO:.0%}〜{PRED_SWAP_HI:.0%}。入れ替わりを除いても")
    print(f"             |ρ| は {PRED_RHO_RISE:.2f} には届かない（除外は最も硬い被験者を取り除き、")
    print("             脈波伝播速度の幅を狭めるから、下がるか横ばいになる）。")
    print("  Q2 の予測: (a) 検出のずれ（|d| は数 ms・1 周期の外れ値なし・d は心拍数か大動脈径と相関）")
    print("             (b) 周期の取り違え（|d| が 1 周期ほどの部分集団が出る）。どちらかを述べる。")

    if state == 2:
        print("\n  この CSV では節 0 の照合が通らないので、予測の照合もしない（層の人数か真値の列が足りない）。")
        return

    # --- Q1
    f_all = q1.get("frac_all", float("nan"))
    p1 = np.isfinite(f_all) and PRED_SWAP_LO <= f_all <= PRED_SWAP_HI
    print(f"\n  Q1-P1 全体の入れ替わり {_pct(f_all)} が "
          f"{PRED_SWAP_LO:.0%}〜{PRED_SWAP_HI:.0%} の内側  {_yn(p1)}")

    bf = q1.get("by_factor", {})

    def cell(f, lv):
        return bf.get(f, {}).get(lv, (float("nan"), 0, 0))[0]

    conds = [("pwv", +1, -1, "脈波伝播速度 +1 SD > −1 SD"),
             ("hr", +1, -1, "心拍数 +1 SD > −1 SD"),
             ("lvet", -1, +1, "駆出時間 −1 SD（短い） > +1 SD")]
    p2_each = []
    for f, hi, lo, lab in conds:
        a, b = cell(f, hi), cell(f, lo)
        c = bool(np.isfinite(a) and np.isfinite(b) and a > b)
        p2_each.append(c if (np.isfinite(a) and np.isfinite(b)) else None)
        print(f"  Q1-P2 {lab}: {_pct(a)} 対 {_pct(b)}  "
              f"{_yn(c if (np.isfinite(a) and np.isfinite(b)) else None)}")
    p2 = all(x is True for x in p2_each)

    print("  Q1-P3 入れ替わりを除いたあとの中央値|ρ|")
    p3_ok, risen = True, []
    for col, tgt, _sign, lab in Q1_PAIRS:
        s_a = q1["rho"].get((col, tgt, "(a) 全例"), EMPTY)
        s_b = q1["rho"].get((col, tgt, "(b) 入れ替わりを除く"), EMPTY)
        s_c = q1["rho"].get((col, tgt, "(c) 入れ替わりだけ"), EMPTY)
        print(f"        {_pad(lab, 32)} 全例 {_n(s_a['med_abs'])} → 除外後 {_n(s_b['med_abs'])}"
              f"（差 {_n(s_b['med_abs'] - s_a['med_abs'], sign=True)}）"
              f"・入れ替わりだけ {_n(s_c['med_abs'])}")
        if np.isfinite(s_b["med_abs"]) and s_b["med_abs"] >= PRED_RHO_RISE:
            p3_ok = False
            risen.append((lab, s_a["med_abs"], s_b["med_abs"]))
    print(f"        どちらも {PRED_RHO_RISE:.2f} 未満  {_yn(p3_ok)}")
    if risen:
        print(f"\n    ★ **予測に反して、除外後の |ρ| が {PRED_RHO_RISE:.2f} を超えた。これは所見である。**")
        for lab, a, b in risen:
            print(f"      {lab}: 全例 {_n(a)} → 除外後 {_n(b)}")
        print("      ただしこれは事後の探索であり、事前規準による判定（26番）は動かない。")
    print(f"    → Q1 は予測の{'内側' if (p1 and p2 and p3_ok) else '外側'}"
          f"（P1 {_yn(p1)}・P2 {_yn(p2)}・P3 {_yn(p3_ok)}）")

    # --- Q2
    if not have_true:
        print("\n  Q2 は真の伝播時間が手に入らないので照合できない（--pwdb か --indices を渡す）。")
        return
    a50 = q2.get("med_abs", float("nan"))
    f_big = q2.get("frac_half", float("nan"))
    f_near = q2.get("frac_near_cycle", float("nan"))
    r_hr = q2.get("corr", {}).get("HR", EMPTY)["med_abs"]
    r_di = q2.get("corr", {}).get("dia_asca", EMPTY)["med_abs"]
    a50_in = q2.get("med_abs_inlier", float("nan"))
    qp1 = bool(np.isfinite(a50) and a50 < PRED_D_SMALL_MS)
    qp2 = bool((np.isfinite(r_hr) and r_hr >= PRED_D_RHO)
               or (np.isfinite(r_di) and r_di >= PRED_D_RHO))
    qp3 = bool(np.isfinite(f_big) and f_big >= PRED_CYCLE_FRAC)
    print(f"\n  Q2-P1 |d| の中央値 {_n(a50, 1)} ms < {PRED_D_SMALL_MS:.0f} ms  {_yn(qp1)}")
    print(f"  Q2-P2 d × 心拍数 {_n(r_hr)} または d × 大動脈径 {_n(r_di)} が "
          f"{PRED_D_RHO:.2f} 以上  {_yn(qp2)}")
    print(f"  Q2-P3 半周期超え {_pct(f_big)} ≥ {PRED_CYCLE_FRAC:.0%}  {_yn(qp3)}"
          f"（1 周期の 0.8〜1.2 倍は {_pct(f_near)}）")
    shape = ("。さらに d は心拍数か大動脈径と相関する（形に依存する検出のずれ）" if qp2
             else f"。ただし d は心拍数とも大動脈径とも {PRED_D_RHO:.2f} 以上では"
                  "相関しない（形の因子では説明しきれない）")
    if qp1 and not qp3:
        verdict = "(a) 検出のずれ"
        why = f"|d| の中央値が {_n(a50, 1)} ms と小さく、周期に相当する外れ値が出ない" + shape
    elif qp3 and not qp1:
        verdict = "(b) 周期の取り違え"
        why = (f"|d| の中央値が {_n(a50, 1)} ms と大きく、半周期を超える被験者が "
               f"{_pct(f_big)}、うち 1 周期近傍が {_pct(f_near)}")
    elif qp1 and qp3:
        verdict = "(a) と (b) の両方"
        why = (f"大多数は |d| の中央値 {_n(a50, 1)} ms の小さな検出のずれだが、"
               f"{_pct(f_big)} の被験者は半周期を超え、うち 1 周期近傍が {_pct(f_near)}。"
               f"周期超えを除いた |d| の中央値は {_n(a50_in, 1)} ms" + shape)
    else:
        verdict = "どちらの型にも当てはまらない"
        why = (f"|d| の中央値 {_n(a50, 1)} ms は {PRED_D_SMALL_MS:.0f} ms 以上だが、"
               f"半周期超えは {_pct(f_big)} しかない。中間の大きさの系統差である" + shape)
    print(f"    → データが支持するのは **{verdict}**。理由: {why}。")
    print("    **この節は事後の探索であり、論文2 の事前規準による判定（26番）は動かない。**")


# ---------------------------------------------------------------- 本体
def report(d_in: pd.DataFrame, src: str, indices: Path | None = None,
           pwdb: Path | None = None) -> int:
    d = d_in.copy()
    for c in NUMERIC:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    # 時刻列が秒なら ms に直す（規則は 23番の `_to_ms` を借りる）
    L._to_ms(d, [T_SYS, T_DIA, T_DIC, "digital_ptt"])
    d = add_swap(d)
    d, src_true = attach_true_ptt(d, indices, pwdb)
    d = add_diff(d)
    have_true = ("ptt_root_fin_ms" in d.columns
                 and bool(np.isfinite(_col(d, "ptt_root_fin_ms")).any()))

    ages = sorted(pd.to_numeric(d["age"], errors="coerce").dropna().unique().tolist()) \
        if "age" in d.columns else []
    print(f"\n{'=' * 100}")
    print("46番 探索的（事後）: 成分の入れ替わりの頻度と、同梱 PTT と真の伝播時間の差")
    print(f"{'=' * 100}")
    print(f"  出典: analysis/scripts/46_pwdb_swap_and_ptt.py / 入力 {src}")
    print(f"  被験者 {len(d)} 名・年齢層 {[int(a) for a in ages]}"
          f"（1 層に {MIN_PER_AGE} 名以上を要求。確認的解析の機械では {N_FULL} 名）")
    print(f"  規約は 20番・23番・26番・45番と共有（CRIT_RHO {M.CRIT_RHO} は参考として載せるだけで、"
          "この台本は判定を出さない）")

    state, _notes = check_known(d, have_true)
    q1 = q1_report(d)
    q2 = q2_report(d, have_true, src_true)
    compare_prediction(q1, q2, state, have_true)
    if len(d) < 100:
        print(f"\n  ★ この入力は {len(d)} 行（1 層 {len(d) // max(1, N_AGES_FULL)} 名）で、"
              "自己検査用の部分集合である。")
        print(f"  ★ **ここから出る数値は読んではいけない。**確認的解析の機械の {N_FULL} 行で走らせること。")
    return state


# ---------------------------------------------------------------- 自己検査
# 合成データの仕込み。
#   入れ替わり  var_pwv == +1 かつ 3 の倍数でない被験者に**だけ**植える
#   d の型     d = A_HR * HR + 雑音（検出のずれ）。cycle_frac の割合に 1 周期を足す
N_PER_AGE_SYN, N_AGES_SYN = 120, 6
A_HR, S_D_MS = 0.05, 0.5      # d = A_HR * HR + N(0, S_D_MS)。A_HR > 0 なので ρ(d, HR) は正
SWAP_EARLY_MS, NOSWAP_LATE_MS = 20.0, 40.0   # 切痕からどれだけ早い／遅いところに置くか


def _planted_swap(k: np.ndarray, lv_pwv: np.ndarray) -> np.ndarray:
    """仕込む入れ替わり。脈波伝播速度 +1 SD の被験者のうち 3 の倍数でない番号。"""
    return (lv_pwv > 0.5) & (k % 3 != 0)


def synth(seed: int = 0, n_per_age: int = N_PER_AGE_SYN, cycle_frac: float = 0.0,
          nan_frac: float = 0.0) -> tuple[pd.DataFrame, dict]:
    """6 年齢層 × n 名。因子は 3 水準の総当たりに近い並びで振る。"""
    rng = np.random.default_rng(seed)
    n = n_per_age * N_AGES_SYN
    k = np.arange(n)
    lv = np.column_stack([(k // (3 ** j)) % 3 - 1 for j in range(len(FACTOR_COLS))])
    order = rng.permutation(n)
    lv = lv[order]
    age = 25 + 10 * (k % N_AGES_SYN)

    lv_map = {f: lv[:, j].astype(float) for j, (f, _lab) in enumerate(FACTOR_COLS)}
    hr = 70.0 + 12.0 * lv_map["hr"] + rng.normal(0, 6.0, n)
    lvet = 300.0 + 20.0 * lv_map["lvet"] + rng.normal(0, 8.0, n)
    pwv = 4.0 + 0.09 * (age - 25) + 1.2 * lv_map["pwv"] + rng.normal(0, 0.3, n)
    pvr = 1.5e8 * np.exp(0.25 * lv_map["mbp"] + rng.normal(0, 0.2, n))
    dia = 30.0 + 2.0 * lv_map["dia"] + rng.normal(0, 0.8, n)

    sys_t = np.full(n, 110.0)
    dic_t = 250.0 + 30.0 * rng.normal(0, 1, n)
    dia_t = dic_t + 60.0

    planted = _planted_swap(k[order], lv_map["pwv"])
    dt1 = np.where(planted,
                   dic_t - sys_t - SWAP_EARLY_MS,
                   dic_t - sys_t + NOSWAP_LATE_MS)
    ri1 = 0.25 + 0.12 * (np.log(pvr) - np.log(1.5e8)) + 0.25 * planted + rng.normal(0, 0.05, n)

    ptt_true = 50.0 + 1200.0 / pwv                     # 真の伝播時間。PWV と強く負
    dptt = A_HR * hr + rng.normal(0, S_D_MS, n)        # 検出のずれ
    cycle = 60000.0 / hr
    off = np.zeros(n, dtype=bool)
    if cycle_frac > 0:
        n_off = int(round(cycle_frac * n))
        off[rng.permutation(n)[:n_off]] = True
        dptt = dptt + off * cycle
    ptt_sup = ptt_true + dptt

    # 第2版の成分ピーク（近似の検算に使う列）。第1成分は収縮期ピークのすぐそば
    tf2 = sys_t + rng.normal(0, 2.0, n)

    d = pd.DataFrame({
        "subj_no": k + 1, "age": age, "HR": hr, "lvet": lvet,
        "PWV_a": pwv, "pvr": pvr, "dia_asca": dia,
        T_SYS: sys_t, T_DIC: dic_t, T_DIA: dia_t,
        DT_V1: dt1, RI_V1: ri1, OK_V1: 1,
        "tf_v2_ms": tf2, "tr_v2_ms": tf2 + dt1,
        "digital_ptt": ptt_sup, "ptt_root_fin_ms": ptt_true})
    for j, (f, _lab) in enumerate(FACTOR_COLS):
        d[f"var_{f}"] = lv[:, j]

    if nan_frac > 0:
        drop = rng.random(n) < nan_frac
        d.loc[drop, DT_V1] = np.nan
        drop2 = rng.random(n) < nan_frac
        d.loc[drop2, "digital_ptt"] = np.nan
        drop3 = rng.random(n) < (nan_frac / 3.0)
        d.loc[drop3, T_DIC] = np.nan

    truth = {"planted": planted, "cycle_off": off, "lv": lv_map, "n": n}
    return d, truth


def selftest() -> int:
    ok = True

    def rep(name, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))

    print("46番 自己検査（合成データ。CSV は要らない）")

    # --- 規約を 20番と共有しているか（自前で書き直していない）
    import inspect
    rep("判定の規約を 20番と共有している（_spearman・_by_age・_judge・層の人数）",
        M.CRIT_RHO == 0.30
        and inspect.signature(M._by_age).parameters["min_n"].default == MIN_PER_AGE
        and callable(M._spearman) and callable(M._judge),
        f"CRIT_RHO {M.CRIT_RHO} / 層の人数 {MIN_PER_AGE}")
    rep("時刻の秒→ms 換算を 23番と共有している", callable(L._to_ms))

    d0, t0 = synth(seed=0)
    rep("合成データを作れる（6 層 × 120 名、因子は 3 水準）",
        len(d0) == N_PER_AGE_SYN * N_AGES_SYN and d0["age"].nunique() == N_AGES_SYN
        and set(np.unique(d0["var_pwv"])) == {-1, 0, 1},
        f"{len(d0)} 行・{d0['age'].nunique()} 層")

    # --- (i) 仕込んだ入れ替わりを正確に取り戻せるか
    s0 = add_swap(d0)
    got = _col(s0, "swap_v1")
    rep("(i) 入れ替わりの旗が仕込みと 1 名残らず一致する",
        np.array_equal(got, t0["planted"].astype(float)),
        f"不一致 {int((got != t0['planted'].astype(float)).sum())} 名")

    buf = io.StringIO()
    with redirect_stdout(buf):
        q1 = q1_report(s0)
    exp_frac = float(t0["planted"].mean())
    rep("(i) 全体の割合が仕込みと厳密に一致する",
        q1["frac_all"] == exp_frac,
        f"報告 {q1['frac_all']:.6f}・仕込み {exp_frac:.6f}")
    # 水準別も厳密に一致するか（脈波伝播速度・心拍数・駆出時間）
    worst, worst_lab = 0.0, ""
    for f, _lab in FACTOR_COLS:
        lvv = t0["lv"][f]
        for want in (-1, 0, 1):
            sel = levels_of(lvv) == want
            e = float(t0["planted"][sel].mean()) if sel.sum() else float("nan")
            g = q1["by_factor"][f][want][0]
            dif = 0.0 if (not np.isfinite(e) and not np.isfinite(g)) else abs(g - e)
            if dif > worst:
                worst, worst_lab = dif, f"{f} {want}"
    rep("(i) 水準別の割合が仕込みと厳密に一致する（6 因子 × 3 水準）",
        worst == 0.0, f"最大差 {worst:.1e}" + (f"（{worst_lab}）" if worst else ""))
    rep("(i) 仕込みどおり脈波伝播速度 +1 SD だけに入れ替わりがある",
        q1["by_factor"]["pwv"][1][0] > 0 and q1["by_factor"]["pwv"][0][0] == 0
        and q1["by_factor"]["pwv"][-1][0] == 0,
        "・".join(f"{LEVEL_LABEL[l]} {_pct(q1['by_factor']['pwv'][l][0])}" for l in (-1, 0, 1)))
    # 除外の 3 段が別の集団を見ていること
    a_ = q1["rho"][(DT_V1, "PWV_a", "(a) 全例")]["n_tot"]
    b_ = q1["rho"][(DT_V1, "PWV_a", "(b) 入れ替わりを除く")]["n_tot"]
    c_ = q1["rho"][(DT_V1, "PWV_a", "(c) 入れ替わりだけ")]["n_tot"]
    rep("(i) (a) 全例 = (b) 除外 + (c) 入れ替わりだけ（人数が合う）",
        a_ == b_ + c_ and b_ > 0 and c_ > 0, f"全例 {a_} = 除外 {b_} + 入れ替わり {c_}")

    # --- (ii) 検出のずれの型: d = A_HR * HR + 雑音 → ρ(d, HR) は正
    d2 = add_diff(add_swap(synth(seed=1, cycle_frac=0.0)[0]))
    s_hr = strat(d2, "d_ptt_ms", "HR", 0)
    rep("(ii) d と心拍数の年齢層内 ρ が仕込んだ向き（正）",
        np.isfinite(s_hr["med"]) and s_hr["med"] > 0.5 and s_hr["n_ok"] == s_hr["n_ages"],
        f"ρ中央値 {s_hr['med']:+.3f}・層 {s_hr['n_ages']}")
    dd2 = _col(d2, "d_ptt_ms")
    rep("(ii) |d| の中央値が数 ms（検出のずれの大きさ）",
        float(np.nanmedian(np.abs(dd2))) < PRED_D_SMALL_MS,
        f"{float(np.nanmedian(np.abs(dd2))):.2f} ms（仕込み A_HR*HR ≈ {A_HR * 70:.1f} ms）")
    big2 = np.abs(dd2) > _col(d2, "halfcycle_ms")
    rep("(ii) 周期の取り違えを仕込まなければ半周期超えは 0",
        float(np.mean(big2)) == 0.0, f"{float(np.mean(big2)):.4f}")
    buf = io.StringIO()
    with redirect_stdout(buf):
        q2a = q2_report(d2, True, "合成")
    rep("(ii) 節 2 が (a) 検出のずれ側の数値を出す",
        q2a["frac_half"] == 0.0 and q2a["corr"]["HR"]["med"] > 0.5,
        f"半周期超え {q2a['frac_half']:.4f}・ρ(d, HR) 中央値 {q2a['corr']['HR']['med']:+.3f}")

    # --- (iii) 1 周期のずれを 5% に仕込む
    d3 = add_diff(add_swap(synth(seed=2, cycle_frac=0.05)[0]))
    _t3 = synth(seed=2, cycle_frac=0.05)[1]
    big3 = np.abs(_col(d3, "d_ptt_ms")) > _col(d3, "halfcycle_ms")
    rep("(iii) 半周期を超える割合が仕込んだ 0.05 と厳密に一致する",
        float(np.mean(big3)) == 0.05, f"{float(np.mean(big3)):.6f}")
    rep("(iii) 半周期を超えるのは 1 周期を足した被験者と完全に同じ",
        np.array_equal(big3, _t3["cycle_off"]),
        f"不一致 {int((big3 != _t3['cycle_off']).sum())} 名")
    buf = io.StringIO()
    with redirect_stdout(buf):
        q2b = q2_report(d3, True, "合成")
    rep("(iii) 節 2 が半周期超え 0.05・1 周期近傍 0.05 を報告する",
        q2b["frac_half"] == 0.05 and q2b["frac_near_cycle"] == 0.05,
        f"半周期超え {q2b['frac_half']:.4f}・1 周期近傍 {q2b['frac_near_cycle']:.4f}")
    rep("(iii) 真の伝播時間 × 大動脈PWV が強い負（仕込み 50 + 1200/PWV）",
        q2b["ptt_root_fin_ms"]["med"] < -0.9,
        f"ρ中央値 {q2b['ptt_root_fin_ms']['med']:+.3f}")

    # --- (iv) 欠測の扱い
    d4in, t4 = synth(seed=3, cycle_frac=0.05, nan_frac=0.4)
    d4 = add_diff(add_swap(d4in))
    f4, k4, n4 = frac(_col(d4, "swap_v1"))
    rep("(iv) ΔT と切痕の欠測で判定できる人数が減り、落ちない",
        0 < n4 < t4["n"] and np.isfinite(f4),
        f"判定できた {n4} / {t4['n']} 名・割合 {_pct(f4)}")
    sw4 = _col(d4, "swap_v1")
    fin4 = np.isfinite(sw4)
    rep("(iv) 欠測を除いた分だけを見れば仕込みと一致する",
        np.array_equal(sw4[fin4], t4["planted"][fin4].astype(float)))
    dd4 = _col(d4, "d_ptt_ms")
    rep("(iv) d の欠測が 同梱 PTT の欠測と一致する",
        int(np.isfinite(dd4).sum()) == int(np.isfinite(_col(d4, "digital_ptt")).sum()),
        f"d が有限 {int(np.isfinite(dd4).sum())} 名")
    d5 = add_swap(synth(seed=4)[0].assign(**{DT_V1: np.nan}))
    f5, _k5, n5 = frac(_col(d5, "swap_v1"))
    rep("(iv) ΔT が全欠でも落ちない（判定できた 0 名・割合は —）",
        n5 == 0 and not np.isfinite(f5), f"判定できた {n5} 名")
    d6 = synth(seed=4)[0].drop(columns=["ptt_root_fin_ms"])
    buf = io.StringIO()
    with redirect_stdout(buf):
        st6 = report(d6, "合成（真の伝播時間なし）")
    out6 = buf.getvalue()
    # 合成データは論文2 の値そのものではないので節 0 は ★ずれ（終了コード 1）になる。
    # ここで確かめるのは「真の伝播時間の列が無くても落ちず、無いと書く」ことである
    rep("(iv) 真の伝播時間の列が無くても report() が落ちず、無い旨を書く",
        st6 == 1 and "真の伝播時間が手に入らない" in out6
        and "照合できない（真の伝播時間の列が無い）" in out6,
        f"終了コード {st6}（合成データなので節 0 は ★ずれ）")
    rep("(iv) 真の伝播時間が無くても節 1 と節 2 の参考値は出る",
        "1. Q1 第2成分が収縮期に入る割合" in out6 and "参考: 同梱 PTT × 大動脈PWV" in out6)

    # --- (vi) 真の伝播時間を外から結合する 3 つの経路
    import tempfile
    base, _tb = synth(seed=5, n_per_age=2)              # 12 名（20番の模擬 PWDB と同じ人数）
    want = _col(base, "ptt_root_fin_ms")
    no_col = base.drop(columns=["ptt_root_fin_ms"])
    with tempfile.TemporaryDirectory() as td:
        p_idx = Path(td) / "pwdb_indices.csv"
        base[["subj_no", "ptt_root_fin_ms"]].to_csv(p_idx, index=False)
        got, how = attach_true_ptt(no_col, p_idx, None)
        rep("(vi) --indices（20番の被験者別出力）から真の伝播時間を結合できる",
            np.allclose(_col(got, "ptt_root_fin_ms"), want) and "20番の被験者別出力" in how, how)
        # 立ち上がり時刻の 2 列から作る経路
        raw = no_col.copy()
        raw["on_aorticroot_p"] = 0.0
        raw["on_digital_ppg"] = want
        got2, how2 = attach_true_ptt(raw, None, None)
        rep("(vi) on_digital_ppg − on_aorticroot_p から作れる",
            np.allclose(_col(got2, "ptt_root_fin_ms"), want) and "on_digital_ppg" in how2, how2)
        # --pwdb 経路（20番の模擬 PWDB を作って load_extras・_onsets_ms を通す）
        b = io.StringIO()
        with redirect_stdout(b):
            root, _truth = M._make_mock(Path(td) / "exported_data", n=12)
            got3, how3 = attach_true_ptt(no_col, None, root)
        v3 = _col(got3, "ptt_root_fin_ms")
        rep("(vi) --pwdb の pwdb_onset_times.csv から結合できる（20番の load_extras 経由）",
            bool(np.isfinite(v3).all()) and len(v3) == 12
            and "pwdb_onset_times.csv" in how3,
            f"{how3} / 12 名すべて有限 {bool(np.isfinite(v3).all())}")
        rep("(vi) 立ち上がり時刻が秒なら ms に換算される（真の伝播時間が 10〜1000 ms の範囲）",
            bool(np.isfinite(v3).all() and 10.0 < float(np.nanmedian(v3)) < 1000.0),
            f"中央値 {float(np.nanmedian(v3)):.1f} ms")
    got4, how4 = attach_true_ptt(no_col, None, None)
    rep("(vi) どこにも無ければ無いと言う（作り話をしない）",
        "ptt_root_fin_ms" not in got4.columns and how4 == "見つからない", how4)

    # --- (v) 同じ乱数種なら出力が一字一句同じ
    def render(seed):
        b = io.StringIO()
        with redirect_stdout(b):
            ds, _ = synth(seed=seed, cycle_frac=0.05)
            report(ds, f"合成 seed={seed}")
        return b.getvalue()

    r0, r0b, r1 = render(0), render(0), render(1)
    rep("(v) 同じ乱数種なら出力が同一", r0 == r0b, f"{len(r0)} 文字")
    rep("(v) 乱数種を変えれば値は変わる（比較が効いている）", r0 != r1)

    # --- 部品そのものの検算
    rep("水準の読み方が 20番と同じ（>0.5 が +1 SD、<-0.5 が −1 SD、間は基準）",
        list(levels_of(np.array([-1.0, -0.6, -0.4, 0.0, 0.4, 0.6, 1.0]))) ==
        [-1.0, -1.0, 0.0, 0.0, 0.0, 1.0, 1.0])
    rep("水準が欠測なら NaN（どの水準にも数えない）",
        not np.isfinite(levels_of(np.array([np.nan]))[0]))
    fr, kk, nn = frac(np.array([1.0, 0.0, np.nan, 1.0]))
    rep("割合は判定できた行だけで取る", (fr, kk, nn) == (2 / 3, 2, 3), f"{kk}/{nn}")
    rep("全部欠測なら割合は NaN", not np.isfinite(frac(np.full(3, np.nan))[0]))
    hc = add_diff(pd.DataFrame({"HR": [60.0, 120.0], "digital_ptt": [1.0, 1.0],
                                "ptt_root_fin_ms": [0.0, 0.0]}))
    rep("半周期 = 30000/HR ms（60 bpm で 500 ms、120 bpm で 250 ms）",
        list(hc["halfcycle_ms"]) == [500.0, 250.0], f"{list(hc['halfcycle_ms'])}")

    # --- 実データ側の関数が動くことの確認（この機械の CSV は 24 行の自己検査用）
    print("\n  --- 実データ側の関数を既定の CSV で走らせる（動くことの確認だけ）---")
    if DEFAULT_CSV.exists():
        d_real = pd.read_csv(DEFAULT_CSV)
        buf = io.StringIO()
        with redirect_stdout(buf):
            st = report(d_real, str(DEFAULT_CSV),
                        indices=DEFAULT_INDICES if DEFAULT_INDICES.exists() else None)
        rep("既定の CSV で report() が落ちない",
            isinstance(st, int) and "46番 探索的（事後）" in buf.getvalue(),
            f"{len(d_real)} 行・終了コード {st}")
        if len(d_real) < 100:
            rep("24 行の部分集合では照合できない（終了コード 2）", st == 2, f"終了コード {st}")
            print(f"  ★ この機械の {DEFAULT_CSV.name} は {len(d_real)} 行（1 層 "
                  f"{len(d_real) // N_AGES_FULL} 名）で、自己検査用の部分集合である。")
            print("  ★ **ここから出る数値は読んではいけない。**"
                  f"確認的解析の機械の {N_FULL} 行で走らせること。")
    else:
        rep("既定の CSV が無い機械でも自己検査は通る", True, f"{DEFAULT_CSV} が無い")

    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=str, default=str(DEFAULT_CSV),
                    help="26番の出力（既定 data/pwdb/pwdb_compare.csv）")
    ap.add_argument("--indices", type=str, default=str(DEFAULT_INDICES),
                    help="20番の被験者別出力（真の伝播時間 ptt_root_fin_ms を持つ）")
    ap.add_argument("--pwdb", type=str, default=None,
                    help="PWDB の配布物を置いたフォルダ（pwdb_onset_times.csv を読む）")
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
        print(f"確認的解析を回した機械には data/pwdb/pwdb_compare.csv がある（{N_FULL} 行）。")
        sys.exit(2)

    ip = Path(args.indices)
    if not ip.exists() and not ip.is_absolute():
        ip = ROOT / args.indices
    d = pd.read_csv(p)
    missing = [c for c in ("age", "HR", T_SYS, T_DIC, DT_V1, RI_V1, "PWV_a", "pvr")
               if c not in d.columns]
    if missing:
        print(f"\n{p} に要る列が無い: {missing}")
        sys.exit(2)
    sys.exit(report(d, str(p), indices=ip if ip.exists() else None,
                    pwdb=Path(args.pwdb) if args.pwdb else None))


if __name__ == "__main__":
    main()

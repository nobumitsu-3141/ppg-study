#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""論文3（実機での同定性）の事前登録に書く症例数を見積もる。

何のための計算か
----------------
`docs/manuscript/paper3/00_decision.md` の「出すとしたらの設計」に
[[決める。同定率の症例中央値の 95% 信頼区間が ±0.05 に入る規模を先に計算する]]
と残してある箇所を埋める。**新しい所見を出す解析ではない。**予備的検討（32番・20 例）の
同定率を母集団の代わりに使い、症例数を増やしたときに同定率の症例中央値の
95% 信頼区間の半幅がどこまで狭くなるかを数えるだけである。

事前規準（32番・lab_log 追記14）は 2 つある。

    同定率の症例中央値 ≥ 0.70               `id_` で始まる列。値は 0〜1
    ウィンドウ間自己相関の症例中央値 ≥ 0.30   `ac_` で始まる列。値は −1〜1

**両方を満たして初めて「同定できる」と判定するので、要る症例数は 2 つの見積りの
大きいほうである。**どちらの規準でも、半幅 ±0.05 で合否が分かれるのは中央値が閾値に
近い指標なので、例数を決めるのはその指標になる（予備的検討では、同定率は特徴点法の ΔT が
0.67、自己相関は Am_b/Am_p1 が 0.36 で最も近い）。各接頭辞の列はすべて報告する。

自己相関は、隣り合うウィンドウの対が 10 未満の症例では出せず欠測になる（32番）。
欠測はその列でだけ落とし、残った症例数を明記する。同定率は全例で出るはずなので、
欠測があれば入力を疑う印（★）として出す。

2 つの数え方
------------
方法A（主）平滑化ブートストラップ
    予備的検討の値から n 例を復元抽出し、N(0, h²) の雑音を足して値の取りうる範囲
    （同定率は [0,1]、自己相関は [−1,1]）に丸め、中央値を取る。
    これを 2,000 回。百分位 2.5／97.5 を 95% 信頼区間とし、半幅 =（上限 − 下限）/ 2。
    h は Silverman の目安 h = 0.9 · min(SD, IQR/1.34) · n_pilot^(−1/5)。
    雑音を足すのは、20 個しかない値をそのまま引き直すと中央値が高々 20 通りの値しか
    取らず、区間の幅が例数にほとんど反応しなくなるためである。
    min(SD, IQR/1.34) が 0 になる場合（全例が同じ値）は h = 0、すなわち雑音を足さない。

方法B（照合）中央値の分布に依らない区間（順序統計量・符号検定）
    大きさ n の標本の順序統計量 [X_(k), X_(n−k+1)] を中央値の区間とする。
    k は被覆確率 P(k ≤ Bin(n, 1/2) ≤ n − k) ≥ 0.95 を満たす中で最大のもの
    （k を大きくするほど区間は狭い）。n = 20 で k = 6、n = 100 で k = 40。
    方法A で作った 2,000 本の標本それぞれにこの区間を当て、半幅の平均を報告する。

**方法A が主、方法B は照合である。**方法B は正規性も平滑化も仮定しないかわりに、
被覆確率が 0.95 ちょうどにならず（n = 20 で 0.959）区間がやや広めに出る。

入力と出力
----------
入力  docs/research/results/32_vitaldb_landmark_summary_v158.csv（20 行・vitaldb 1.5.8）
出力  docs/research/results/43_paper3_sample_size.txt（画面に出すものと同じ）

    python3 scripts/43_paper3_sample_size.py --selftest
        合成データで計算の筋道を検算する。CSV は要らない
    python3 scripts/43_paper3_sample_size.py
        32番のまとめから例数を見積もり、結果ファイルに書き出す
    python3 scripts/43_paper3_sample_size.py --csv PATH --out PATH
        入力・出力の場所を指定する
"""
from __future__ import annotations

import argparse
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CSV_DEFAULT = REPO / "docs" / "research" / "results" / "32_vitaldb_landmark_summary_v158.csv"
OUT_DEFAULT = REPO / "docs" / "research" / "results" / "43_paper3_sample_size.txt"

SEED = 0                                   # 主解析・41番と同じ
N_BOOT = 2000                              # 41番（表2・表4 の脚注）と同じ回数
RUN_DATE = "2026-09-12"

N_GRID = list(range(20, 501, 5))           # 例数の候補
SHOW_N = [20, 30, 40, 50, 60, 80, 100, 150, 200, 300, 400, 500]   # 表に出す例数
TARGETS = (0.05, 0.04, 0.03)               # 半幅の目標。0.05 が事前登録に書く値
PILOT_N = 20                               # 予備的検討の症例数
CRITERION = 0.70                           # 事前規準その1 同定率（32番）
CRITERION_AC = 0.30                        # 事前規準その2 ウィンドウ間自己相関（32番）
MIN_PAIRS = 10                             # 自己相関に要る隣り合うウィンドウの対の数（32番）

# 事前規準は 2 つあり、列の接頭辞・閾値・値の取りうる範囲・欠測の意味が違う。
# 両方について例数を出し、大きいほうを採る。
BLOCKS = (
    {"prefix": "id_", "name": "同定率", "threshold": CRITERION, "domain": (0.0, 1.0),
     "driver_expect": "id_ens_dt_lm_ms", "nan_is_bad": True, "nan_by_npair": False},
    {"prefix": "ac_", "name": "ウィンドウ間自己相関", "threshold": CRITERION_AC,
     "domain": (-1.0, 1.0), "driver_expect": "ac_ens_amb", "nan_is_bad": False,
     "nan_by_npair": True},
)

# 00_decision.md（32番の報告）が書いている予備的検討の中央値。小数 2 桁で照合する
EXPECT_MED = {"id_ens_dt_lm_ms": 0.67, "id_ens_amb": 0.95,
              "ac_ens_dt_lm_ms": 0.64, "ac_ens_amb": 0.36}

# 指標の呼び名（32番 の INDICES と同じ）。接頭辞を外した部分で引く。
# 同じ指標について同定率と自己相関の 2 つの列があるので、呼び名は共通である。
INDEX_LABEL = {
    "ens_dt_lm_ms": "特徴点法の ΔT（平均拍）",
    "ens_amb": "Am_b/Am_p1 早期振幅比（平均拍）",
    "pwtt_ms": "PWTT（陽性対照）",
    "ens_dt1_ms": "型1 だけの ΔT（平均拍）",
}


# ---------------------------------------------------------------- 道具
def silverman_h(x: np.ndarray) -> float:
    """平滑化の幅 h = 0.9 · min(SD, IQR/1.34) · n^(−1/5)（Silverman の目安）。

    SD は不偏（ddof=1）。min が 0 になる予備的検討（全例が同じ値・四分位範囲が 0）では
    h = 0 を返し、雑音を足さない普通のブートストラップになる。
    """
    x = np.asarray(x, dtype=float)
    n = x.size
    if n < 2:
        return 0.0
    sd = float(np.std(x, ddof=1))
    q25, q75 = (float(v) for v in np.percentile(x, [25, 75]))
    spread = min(sd, (q75 - q25) / 1.34)
    h = 0.9 * spread * n ** (-0.2)
    return float(h) if np.isfinite(h) and h > 0 else 0.0


@lru_cache(maxsize=None)
def order_stat_k(n: int, conf: float = 0.95) -> int:
    """中央値の区間 [X_(k), X_(n−k+1)] の k。分布を仮定しない（符号検定）。

    被覆確率は P(k ≤ Bin(n, 1/2) ≤ n − k) = 1 − 2·P(Bin(n, 1/2) ≤ k−1)。
    k を大きくするほど区間は狭く、被覆確率は小さくなるので、**被覆が conf 以上である中で
    最大の k** を返す（= 被覆 conf 以上のうち最も狭い区間）。n = 20 で 6、n = 100 で 40。
    どの k でも被覆が足りない小さい n（n ≤ 5）では 1 を返す（区間は [最小値, 最大値]）。
    二項係数は整数で足すので丸め誤差が入らない。
    """
    tot = 1 << n
    c = 1          # Bin(n, k−1) の二項係数
    acc = 1        # k−1 までの二項係数の和
    best = 1
    for k in range(1, n // 2 + 1):
        if 1.0 - 2.0 * (acc / tot) >= conf:
            best = k
        else:
            break
        c = c * (n - (k - 1)) // k
        acc += c
    return best


@lru_cache(maxsize=None)
def order_stat_coverage(n: int, k: int) -> float:
    """[X_(k), X_(n−k+1)] の被覆確率 1 − 2·P(Bin(n, 1/2) ≤ k−1)。"""
    if k < 1:
        return 1.0
    acc, c = 1, 1
    for i in range(1, k):
        c = c * (n - (i - 1)) // i
        acc += c
    return 1.0 - 2.0 * (acc / (1 << n))


def boot_at_n(x: np.ndarray, n: int, h: float, rng: np.random.Generator,
              n_boot: int = N_BOOT, domain: tuple[float, float] = (0.0, 1.0)) -> dict:
    """n 例を取り直したときの中央値の分布を 1 つ作り、方法A・方法B の半幅を返す。

    予備的検討の値から n 個を復元抽出 → N(0, h²) を足す → domain に丸める → 並べ替える。
    方法A は中央値の百分位 2.5／97.5、方法B は各標本の順序統計量の区間で、その半幅の平均。

    domain は値の取りうる範囲で、指標によって違う（同定率は [0,1]、自己相関は [−1,1]）。
    ここを間違えると、端に寄った予備的検討で区間が片側だけ切られて狭く出る。
    """
    s = x[rng.integers(0, x.size, size=(n_boot, n))]
    s += rng.normal(0.0, h, size=s.shape)
    np.clip(s, domain[0], domain[1], out=s)
    s.sort(axis=1)
    med = s[:, n // 2] if n % 2 else 0.5 * (s[:, n // 2 - 1] + s[:, n // 2])
    lo, hi = (float(v) for v in np.percentile(med, [2.5, 97.5]))
    k = order_stat_k(n)
    return {"n": n, "k": k,
            "a_lo": lo, "a_hi": hi, "a_hw": 0.5 * (hi - lo),
            "b_lo": float(np.mean(s[:, k - 1])), "b_hi": float(np.mean(s[:, n - k])),
            "b_hw": float(np.mean(0.5 * (s[:, n - k] - s[:, k - 1]))),
            "med_mid": float(np.median(med)),
            "smin": float(s.min()), "smax": float(s.max())}


def first_at_or_below(rows: list[dict], key: str, target: float) -> int | None:
    """半幅が目標以下になる最小の例数。候補の中に無ければ None。"""
    for r in rows:
        if r[key] <= target:
            return int(r["n"])
    return None


def stays_at_or_below(rows: list[dict], key: str, target: float) -> int | None:
    """それ以降すべての候補で半幅が目標以下になる最小の例数。

    ブートストラップの半幅は例数に対して単調に減るとは限らない（引き直しの揺れがある）。
    たまたま 1 点だけ下回った例数を採らないための添え物で、事前登録に書く値は
    `first_at_or_below` のほうである。
    """
    out = None
    for r in reversed(rows):
        if r[key] <= target:
            out = int(r["n"])
        else:
            break
    return out


def analyse_column(x: np.ndarray, grid: list[int] | None = None,
                   n_boot: int = N_BOOT, seed: int = SEED,
                   targets: tuple[float, ...] = TARGETS,
                   domain: tuple[float, float] = (0.0, 1.0)) -> dict:
    """1 つの列について、例数ごとの半幅と、目標を満たす最小の例数を出す。

    乱数の生成器は **列ごとに作り直す。**こうすると列の並び順を変えても値が動かない。
    列を足しても、既にある列の値は 1 つも動かない。
    """
    grid = list(N_GRID if grid is None else grid)
    x = np.asarray(x, dtype=float)
    rng = np.random.default_rng(seed)
    h = silverman_h(x)
    rows = [boot_at_n(x, n, h, rng, n_boot, domain) for n in grid]
    # 予備的検討そのものの精度（方法A）。**生成器を作り直して引く。**
    # こうすると上の格子の引き直しに一切影響しないので、欠測を落として 20 例でない列
    # （自己相関）でも同じやり方で出せる。予備的検討が 20 例で格子の先頭も 20 なら、
    # 引き直しの中身は rows[0] と同一になる（自己検査で確かめている）。
    pilot = (boot_at_n(x, int(x.size), h, np.random.default_rng(seed), n_boot, domain)
             if x.size >= 2 else None)
    xs = np.sort(x)
    k20 = order_stat_k(x.size)
    return {
        "n_pilot": int(x.size), "h": h, "domain": domain,
        "median": float(np.median(x)), "sd": float(np.std(x, ddof=1)),
        "iqr": float(np.subtract(*np.percentile(x, [75, 25]))),
        "min": float(xs[0]), "max": float(xs[-1]),
        "rows": rows,
        # 方法B のほうは予備的検討の値に直接当てる（引き直さない）
        "pilot_a": (pilot["a_lo"], pilot["a_hi"]) if pilot else None,
        "pilot_b_k": k20,
        "pilot_b": (float(xs[k20 - 1]), float(xs[x.size - k20])),
        "pilot_b_cov": order_stat_coverage(x.size, k20),
        "chosen": {t: {"a": first_at_or_below(rows, "a_hw", t),
                       "b": first_at_or_below(rows, "b_hw", t),
                       "a_stay": stays_at_or_below(rows, "a_hw", t),
                       "b_stay": stays_at_or_below(rows, "b_hw", t)} for t in targets},
    }


# ---------------------------------------------------------------- 出力
def disp_width(s: str) -> int:
    """表示したときの桁数。全角（W・F）は 2 桁と数える。見出しを数字の列に揃えるため。"""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)


def lpad(s: str, w: int) -> str:
    return " " * max(0, w - disp_width(s)) + s


def rpad(s: str, w: int) -> str:
    return s + " " * max(0, w - disp_width(s))


def rel(p: Path) -> str:
    """リポジトリからの相対パス。--csv で外の場所を指したときは絶対パスのまま出す。"""
    try:
        return p.resolve().relative_to(REPO).as_posix()
    except ValueError:
        return str(p)


def fmt_n(v: int | None) -> str:
    return f"{v:>4d}" if v is not None else ">500"


def label_of(col: str) -> str:
    """列名から指標の呼び名を引く。接頭辞（id_・ac_）を外した部分が指標を指す。"""
    return INDEX_LABEL.get(col.split("_", 1)[1], "（32番の指標）")


def drop_missing(values: np.ndarray) -> tuple[np.ndarray, int]:
    """欠測を落とした配列と、落とした数を返す。

    自己相関は隣り合うウィンドウの対が足りない症例で出ない。その症例はその列でだけ落とす。
    """
    x = np.asarray(values, dtype=float)
    na = int(np.isnan(x).sum())
    return x[~np.isnan(x)], na


def pick_driver(res: dict[str, dict], cols: list[str], threshold: float) -> str:
    """例数を決める列を選ぶ。予備的検討の中央値が閾値に最も近い列である。

    閾値は規準ごとに違う（同定率 0.70・自己相関 0.30）。半幅 ±0.05 で合否が分かれるのは
    中央値が閾値に近い指標なので、そこが要る例数を決める。同じ距離なら列名の順で決める。
    """
    return min(cols, key=lambda c: (abs(res[c]["median"] - threshold), c))


def npair_check(df: pd.DataFrame, col: str) -> tuple[bool, int] | None:
    """自己相関の欠測が「対が MIN_PAIRS 未満」の症例と一致するかを確かめる。

    (一致したか, 対が足りない症例数) を返す。対応する npair_ 列が無ければ None。
    一致しなければ欠測の理由が別にあるということなので、呼び出し側で印を付ける。
    """
    npc = "npair_" + col.split("_", 1)[1]
    if npc not in df.columns:
        return None
    na = np.asarray(df[col].isna().to_numpy())
    few = np.asarray(df[npc].to_numpy(dtype=float) < MIN_PAIRS)
    return bool(np.array_equal(na, few)), int(few.sum())


def combine_n(n_id: int | None, n_ac: int | None) -> tuple[int | None, str]:
    """2 つの規準に要る例数から、両方を満たす例数（大きいほう）と、決めた側を返す。

    None は「候補の中に無い（>500）」の意味で、その側が決める。
    """
    if n_id is None and n_ac is None:
        return None, "どちらも候補の外"
    if n_id is None:
        return None, BLOCKS[0]["name"]
    if n_ac is None:
        return None, BLOCKS[1]["name"]
    if n_id == n_ac:
        return n_id, "どちらも同じ"
    return (n_id, BLOCKS[0]["name"]) if n_id > n_ac else (n_ac, BLOCKS[1]["name"])


def dom_text(domain: tuple[float, float]) -> str:
    """値の取りうる範囲の書き方。0〜1 と −1〜1。"""
    return f"{domain[0]:g}〜{domain[1]:g}".replace("-", "−")


def fmt_v(v: float, signed: bool, w: int = 9, dec: int = 3) -> str:
    """自己相関は負になりうるので符号を付けて出す。同定率は付けない。"""
    return format(v, f"{'+' if signed else ''}{w}.{dec}f")


def build_report(df: pd.DataFrame, blocks: list[dict], csv_path: Path,
                 bad: list[str], notes: list[str]) -> list[str]:
    """画面と結果ファイルに出す行を作る。数値はすべて出どころを併記する。"""
    L: list[str] = []
    W = 98

    L.append("=" * W)
    L.append("論文3（実機での同定性）の症例数の見積り")
    L.append("事前規準の 2 つの量それぞれについて、症例中央値の 95% 信頼区間の半幅が")
    L.append("0.05 以下になる症例数を出し、大きいほうを採る")
    L.append("=" * W)
    L.append(f"スクリプト        analysis/scripts/{Path(__file__).name}")
    L.append(f"入力 CSV          {rel(csv_path)}")
    src = ("32番の予備的検討・vitaldb 1.5.8" if csv_path.resolve() == CSV_DEFAULT.resolve()
           else "--csv で指定した入力")
    L.append(f"症例数            {len(df)} 例（{src}）")
    indent = "使った列          "
    for b in blocks:
        B = b["B"]
        L.append(f"{indent}{B['name']}（{B['prefix']}・値は {dom_text(B['domain'])}）")
        L.append(f"                    {', '.join(b['cols'])}")
        indent = "                  "
    L.append("                  （その接頭辞で始まる列をすべて拾った）")
    L.append(f"引き直しの回数    {N_BOOT:,} 回")
    L.append(f"乱数種            {SEED}（列ごとに生成器を作り直すので列の並び順に依らない）")
    L.append(f"実行日            {RUN_DATE}")
    L.append(f"事前規準          同定率の症例中央値 ≥ {CRITERION:.2f} かつ "
             f"ウィンドウ間自己相関の症例中央値 ≥ {CRITERION_AC:.2f}")
    L.append("                  （32番・lab_log 追記14。両方を満たして「同定できる」と判定する）")
    if bad:
        L.append("")
        for x in bad:
            L.append(f"★ {x}")
    if notes:
        L.append("")
        for x in notes:
            L.append(f"注 {x}")

    L.append("")
    L.append("-" * W)
    L.append("0. 入力の確認（値はすべて上の CSV の列から。中央値ほかは欠測を落とした症例での値）")
    L.append("-" * W)
    for b in blocks:
        B = b["B"]
        signed = B["domain"][0] < 0
        L.append(f"  [{B['name']}] 規準 ≥ {B['threshold']:.2f}・値は {dom_text(B['domain'])}")
        L.append("  " + rpad("列", 20) + lpad("欠測", 5) + lpad("採用", 5) + lpad("中央値", 9)
                 + lpad("最小", 9) + lpad("最大", 9) + lpad("SD", 9) + lpad("IQR", 9)
                 + "   指標")
        for c in b["cols"]:
            r, (n_used, n_na) = b["res"][c], b["used"][c]
            L.append(f"  {c:20s}{n_na:>5d}{n_used:>5d}"
                     + fmt_v(r["median"], signed) + fmt_v(r["min"], signed)
                     + fmt_v(r["max"], signed)
                     + f"{r['sd']:>9.3f}{r['iqr']:>9.3f}   {label_of(c)}")
        if B["nan_by_npair"]:
            agree = [v for v in b["npair"].values() if v is not None]
            if agree:
                L.append(f"    欠測の理由: 隣り合うウィンドウの対が {MIN_PAIRS} 未満"
                         f"（npair_ 列）。{len(agree)} 列すべてで"
                         f"{'一致した' if all(a for a, _ in agree) else '★一致しない'}")
        L.append("")

    L.append("  00_decision.md（32番の報告）が書いている予備的検討の中央値との照合")
    for b in blocks:
        for c in b["cols"]:
            if c not in EXPECT_MED:
                continue
            r = b["res"][c]
            got = round(r["median"], 2)
            L.append(f"  {c:20s} 中央値 {r['median']:.4f} → 小数 2 桁で {got:.2f}"
                     f"（00_decision.md は {EXPECT_MED[c]:.2f}）  "
                     f"{'一致' if abs(got - EXPECT_MED[c]) < 1e-9 else '★ずれ'}")

    L.append("")
    L.append("-" * W)
    L.append("1. 数え方（2 つの規準で同じ。違うのは値の範囲と閾値だけ）")
    L.append("-" * W)
    L.append("  方法A（主）平滑化ブートストラップ")
    L.append("    予備的検討の値から n 例を復元抽出し、N(0, h²) を足して値の範囲に丸め、")
    L.append(f"    中央値を取る。これを {N_BOOT:,} 回。百分位 2.5／97.5 を 95% 信頼区間とし、")
    L.append("    半幅 =（上限 − 下限）/ 2。h = 0.9 · min(SD, IQR/1.34) · n_pilot^(−1/5)")
    L.append("    （Silverman の目安。n_pilot は欠測を落としたあとの症例数）。")
    L.append("    雑音を足すのは、20 個ほどの値をそのまま引き直すと中央値が数十通りしか取らず、")
    L.append("    区間の幅が例数にほとんど反応しなくなるためである。")
    L.append("    丸める範囲は同定率が [0,1]、自己相関が [−1,1]。")
    L.append("  方法B（照合）中央値の分布に依らない区間")
    L.append("    大きさ n の標本の順序統計量 [X_(k), X_(n−k+1)]。k は")
    L.append("    P(k ≤ Bin(n, 1/2) ≤ n − k) ≥ 0.95 を満たす中で最大のもの（最も狭い区間）。")
    L.append("    方法A の各標本にこの区間を当て、半幅の平均を出す。被覆は 0.95 ちょうどに")
    L.append("    ならず（n = 20 で 0.959、n = 100 で 0.965）、方法A より広めに出る。")

    for b in blocks:
        B = b["B"]
        signed = B["domain"][0] < 0
        thr = B["threshold"]
        for c in b["cols"]:
            r = b["res"][c]
            by_n = {row["n"]: row for row in r["rows"]}
            L.append("")
            L.append("-" * W)
            L.append(f"2. [{B['name']}] {c}   {label_of(c)}")
            L.append("-" * W)
            L.append(f"  予備的検討 {r['n_pilot']} 例: 中央値 {fmt_v(r['median'], signed, 0)}・"
                     f"SD {r['sd']:.3f}・IQR {r['iqr']:.3f}・平滑化の幅 h {r['h']:.4f}")
            if r["pilot_a"]:
                lo, hi = r["pilot_a"]
                L.append(f"  いまの精度 方法A（n={r['n_pilot']} の引き直し {N_BOOT:,} 回）: "
                         f"{fmt_v(lo, signed, 0)} 〜 {fmt_v(hi, signed, 0)}"
                         f"（半幅 {0.5 * (hi - lo):.3f}）  "
                         f"{thr:.2f} を{'含む' if lo <= thr <= hi else '含まない'}")
            blo, bhi = r["pilot_b"]
            L.append(f"  いまの精度 方法B（{r['n_pilot']} 個の値そのもの・k={r['pilot_b_k']}・"
                     f"被覆 {r['pilot_b_cov']:.3f}）: "
                     f"{fmt_v(blo, signed, 0)} 〜 {fmt_v(bhi, signed, 0)}"
                     f"（半幅 {0.5 * (bhi - blo):.3f}）  "
                     f"{thr:.2f} を{'含む' if blo <= thr <= bhi else '含まない'}")
            L.append("")
            L.append("    " + lpad("例数", 6) + lpad("方法A 半幅", 12) + lpad("方法B 半幅", 12)
                     + lpad("方法B の k", 11) + lpad("方法A 95%区間", 23))
            for n in SHOW_N:
                row = by_n.get(n)
                if row is None:
                    continue
                L.append(f"    {n:>6d}{row['a_hw']:>12.4f}{row['b_hw']:>12.4f}{row['k']:>11d}"
                         + fmt_v(row["a_lo"], signed, 13) + " 〜"
                         + fmt_v(row["a_hi"], signed, 7))
            L.append("")
            L.append("    " + lpad("目標の半幅", 12) + lpad("方法A", 8) + lpad("方法B", 8)
                     + "      （参考）それ以降ずっと下回る例数 方法A／方法B")
            for t in TARGETS:
                ch = r["chosen"][t]
                L.append("    " + lpad(f"≤ {t:.2f}", 12)
                         + f"{fmt_n(ch['a']):>8}{fmt_n(ch['b']):>8}"
                         + f"      {fmt_n(ch['a_stay']).strip()}／{fmt_n(ch['b_stay']).strip()}")

    L.append("")
    L.append("=" * W)
    L.append("3. まとめ（例数の候補は 20 から 500 まで 5 きざみ。>500 は候補の中に無いという意味）")
    L.append("=" * W)
    L.append("  A は方法A（平滑化ブートストラップ）、B は方法B（順序統計量）。単位は症例数。")
    for b in blocks:
        B = b["B"]
        signed = B["domain"][0] < 0
        L.append("")
        L.append(f"  [{B['name']}] 規準 ≥ {B['threshold']:.2f}")
        L.append("  " + rpad("列（*=例数を決める列）", 22) + lpad("中央値", 8)
                 + lpad(f"{B['threshold']:.2f} との差", 12)
                 + "".join(lpad(f"≤{t:.2f} A／B", 18) for t in TARGETS))
        for c in b["cols"]:
            r = b["res"][c]
            line = ("  " + rpad(("* " if c == b["driver"] else "  ") + c, 22)
                    + fmt_v(r["median"], signed, 8)
                    + f"{abs(r['median'] - B['threshold']):>12.3f}")
            for t in TARGETS:
                ch = r["chosen"][t]
                line += lpad(f"{fmt_n(ch['a'])}／{fmt_n(ch['b'])}", 18)
            L.append(line)

    L.append("")
    L.append("=" * W)
    L.append("4. 事前登録に書く症例数")
    L.append("=" * W)
    for b in blocks:
        B, d = b["B"], b["res"][b["driver"]]
        ch = d["chosen"][0.05]
        signed = B["domain"][0] < 0
        L.append(f"  {B['name']} ≥ {B['threshold']:.2f}  "
                 f"例数を決める列 {b['driver']}（{label_of(b['driver'])}）")
        L.append(f"    予備的検討の中央値 {fmt_v(d['median'], signed, 0)} が閾値に最も近い"
                 f"（差 {abs(d['median'] - B['threshold']):.3f}・採用 {d['n_pilot']} 例）")
        L.append(f"    半幅 ≤ 0.05 に要る症例数: 方法A {fmt_n(ch['a']).strip()} 例 ／ "
                 f"方法B {fmt_n(ch['b']).strip()} 例")
    if len(blocks) == 2:
        c0 = blocks[0]["res"][blocks[0]["driver"]]["chosen"][0.05]
        c1 = blocks[1]["res"][blocks[1]["driver"]]["chosen"][0.05]
        na, wa = combine_n(c0["a"], c1["a"])
        nb, wb = combine_n(c0["b"], c1["b"])
        L.append(f"  症例数 n = 2 つの大きいほう: "
                 f"方法A {fmt_n(na).strip()} 例（{wa}が決めた）／ "
                 f"方法B {fmt_n(nb).strip()} 例（{wb}が決めた）")
    else:
        L.append("  ★ 規準の片方しか計算できていないので、2 つの大きいほうは出せない")
    L.append(f"  出どころ: {Path(__file__).name}・{csv_path.name}")
    n_cols = sum(len(b["cols"]) for b in blocks)
    L.append(f"            {len(df)} 例・{n_cols} 列・引き直し {N_BOOT:,} 回・"
             f"乱数種 {SEED}・{RUN_DATE}")
    L.append("=" * W)
    return L


# ---------------------------------------------------------------- 本体
def run(csv_path: Path, out_path: Path | None) -> int:
    if not csv_path.exists():
        print(f"★ 入力が無い: {csv_path}")
        print("  32番（32_vitaldb_landmark_report_v158）の症例別まとめが要る。")
        return 2
    df = pd.read_csv(csv_path)

    bad: list[str] = []
    notes: list[str] = []
    blocks: list[dict] = []
    warned = False
    for B in BLOCKS:
        cols = [c for c in df.columns if c.startswith(B["prefix"])]
        if not cols:
            bad.append(f"{B['prefix']} で始まる列が無いので {B['name']} の例数は出せない")
            continue
        if B["driver_expect"] not in cols:
            print(f"★ {B['name']} の例数を決めるはずの列 {B['driver_expect']} が CSV に無い。")
            print(f"  見つかった {B['prefix']} 列: {', '.join(cols)}")
            print("  どの列がどの指標かを確かめてから回すこと。ここでは続けない。")
            return 2

        lo, hi = B["domain"]
        res: dict[str, dict] = {}
        used: dict[str, tuple[int, int]] = {}
        npair: dict[str, tuple[bool, int] | None] = {}
        keep: list[str] = []
        for c in cols:
            x, n_na = drop_missing(df[c].to_numpy(dtype=float))
            if n_na:
                msg = f"{c}: 欠測 {n_na} 例を落として {x.size} 例で計算した"
                if B["nan_is_bad"]:
                    bad.append(msg + "（同定率は全例で出るはずなので入力を確かめること）")
                else:
                    notes.append(msg + f"（隣り合うウィンドウの対が {MIN_PAIRS} 未満の症例）")
            if x.size < 2:
                bad.append(f"{c}: 使える症例が {x.size} 例しかないので飛ばした")
                continue
            if x.min() < lo or x.max() > hi:
                bad.append(f"{c} が {dom_text(B['domain'])} に収まっていない"
                           f"（{x.min():.3f}〜{x.max():.3f}）")
            keep.append(c)
            res[c] = analyse_column(x, domain=B["domain"])
            used[c] = (int(x.size), n_na)
            # 自己相関の欠測が対の不足で説明できるかを確かめる。同定率の列には当てない
            # （こちらは欠測が無いのが正しいので、npair との一致を見ても意味がない）
            npair[c] = npair_check(df, c) if B["nan_by_npair"] else None

        if B["driver_expect"] not in keep:
            bad.append(f"{B['name']}: {B['driver_expect']} が使えないので例数を出せない")
            continue
        dis = [c for c, v in npair.items() if v is not None and not v[0]]
        if dis:
            bad.append(f"{', '.join(dis)}: 欠測が npair < {MIN_PAIRS} の症例と一致しない。"
                       f"欠測の理由が対の不足以外にある")

        for c in keep:
            if c not in EXPECT_MED:
                continue
            got = round(res[c]["median"], 2)
            if abs(got - EXPECT_MED[c]) > 1e-9:
                bad.append(f"{c} の中央値が {res[c]['median']:.4f}（小数 2 桁で {got:.2f}）で、"
                           f"00_decision.md の {EXPECT_MED[c]:.2f} と違う")
                warned = True

        driver = pick_driver(res, keep, B["threshold"])
        if driver != B["driver_expect"]:
            bad.append(f"{B['name']}: {B['threshold']:.2f} に最も近い列が {driver} で、"
                       f"想定していた {B['driver_expect']} ではない")
        blocks.append({"B": B, "cols": keep, "res": res, "used": used,
                       "npair": npair, "driver": driver})

    if warned:
        bad.append("  この見積りを事前登録に写す前に、入力が予備的検討と同じものか確かめること")
    if not blocks:
        print("★ 例数を出せる列が 1 つも無い。列は: " + ", ".join(df.columns))
        return 2

    lines = build_report(df, blocks, csv_path, bad, notes)
    print("\n".join(lines))
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\n{rel(out_path)} に書き出した")
    return 1 if bad else 0


# ---------------------------------------------------------------- 自己検査
def selftest() -> int:
    ok = True

    def rep(name, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))

    grid = list(range(20, 501, 20))        # 検算なので候補を粗くする
    nb = 800                               # 同じく回数を落とす

    # --- 方法B の k（分布を仮定しない区間） ---
    k20, k100 = order_stat_k(20), order_stat_k(100)
    rep("n=20 の k が 6（古典的な (X_(6), X_(15)) の区間）", k20 == 6, f"k={k20}")
    rep("n=100 の k が 40", k100 == 40, f"k={k100}")
    rep("k の被覆は 0.95 以上、k+1 では 0.95 未満（最も狭い区間を選んでいる）",
        order_stat_coverage(20, 6) >= 0.95 > order_stat_coverage(20, 7)
        and order_stat_coverage(100, 40) >= 0.95 > order_stat_coverage(100, 41),
        f"n=20 {order_stat_coverage(20, 6):.4f}／{order_stat_coverage(20, 7):.4f}  "
        f"n=100 {order_stat_coverage(100, 40):.4f}／{order_stat_coverage(100, 41):.4f}")
    rep("k は 1 以上 n/2 以下", all(1 <= order_stat_k(n) <= n // 2 for n in (20, 51, 200, 500)),
        f"n=500 で k={order_stat_k(500)}")
    rep("例数が増えると区間は中央に寄る（k/n が 0.5 に近づく）",
        order_stat_k(20) / 20 < order_stat_k(100) / 100 < order_stat_k(500) / 500,
        f"{k20 / 20:.3f} < {k100 / 100:.3f} < {order_stat_k(500) / 500:.3f}")

    # --- 平滑化の幅 ---
    rng = np.random.default_rng(0)
    x_norm = np.clip(rng.normal(0.60, 0.10, PILOT_N), 0.0, 1.0)
    sd = float(np.std(x_norm, ddof=1))
    iqr = float(np.subtract(*np.percentile(x_norm, [75, 25])))
    want_h = 0.9 * min(sd, iqr / 1.34) * PILOT_N ** (-0.2)
    rep("h が Silverman の式どおり", abs(silverman_h(x_norm) - want_h) < 1e-12,
        f"h={silverman_h(x_norm):.5f}")
    rep("全例が同じ値なら h = 0", silverman_h(np.full(PILOT_N, 0.5)) == 0.0)

    # --- (1) 同じ乱数種なら同じ値 ---
    r1 = analyse_column(x_norm, grid=grid, n_boot=nb)
    r2 = analyse_column(x_norm, grid=grid, n_boot=nb)
    same = ([q["a_hw"] for q in r1["rows"]] == [q["a_hw"] for q in r2["rows"]]
            and [q["b_hw"] for q in r1["rows"]] == [q["b_hw"] for q in r2["rows"]]
            and r1["chosen"] == r2["chosen"])
    rep("同じ乱数種で二度回すと 1 ビットも違わない", same,
        f"半幅 n=20 {r1['rows'][0]['a_hw']:.6f} / 二度目 {r2['rows'][0]['a_hw']:.6f}")
    r3 = analyse_column(x_norm, grid=grid, n_boot=nb, seed=1)
    rep("乱数種を変えれば値は動く（ただし少し）",
        r3["rows"][0]["a_hw"] != r1["rows"][0]["a_hw"]
        and abs(r3["rows"][0]["a_hw"] - r1["rows"][0]["a_hw"]) < 0.02,
        f"種0 {r1['rows'][0]['a_hw']:.4f} 対 種1 {r3['rows'][0]['a_hw']:.4f}")

    # --- (2) 全例が同じ値なら半幅は常に 0 ---
    rd = analyse_column(np.full(PILOT_N, 0.5), grid=grid, n_boot=200)
    rep("全例が同じ値なら、どの例数でも半幅は 0（方法A・方法B とも）",
        all(q["a_hw"] == 0.0 and q["b_hw"] == 0.0 for q in rd["rows"]),
        f"最大 {max(max(q['a_hw'], q['b_hw']) for q in rd['rows']):.1e}")
    rep("全例が同じ値なら目標 0.05 は n=20 で満たす", rd["chosen"][0.05]["a"] == 20)

    # --- (3) 例数を 4 倍にすると半幅はおよそ半分 ---
    rr = analyse_column(x_norm, grid=[100, 400], n_boot=N_BOOT)
    ratio = rr["rows"][1]["a_hw"] / rr["rows"][0]["a_hw"]
    rep("n=400 の半幅が n=100 のおよそ半分（1/√4）", 0.35 <= ratio <= 0.65,
        f"{rr['rows'][0]['a_hw']:.4f} → {rr['rows'][1]['a_hw']:.4f}  比 {ratio:.3f}")
    ratio_b = rr["rows"][1]["b_hw"] / rr["rows"][0]["b_hw"]
    rep("方法B でも同じ比になる", 0.35 <= ratio_b <= 0.65, f"比 {ratio_b:.3f}")

    # --- (4)(5) 平滑化した値が [0,1] に収まる ---
    x_edge = np.clip(rng.normal(0.97, 0.05, PILOT_N), 0.0, 1.0)     # 上端に張りつく予備的検討
    re_ = analyse_column(x_edge, grid=grid, n_boot=nb)
    rep("平滑化した値はすべて [0,1] に収まる（上端に張りつく列でも）",
        all(0.0 <= q["smin"] and q["smax"] <= 1.0 for q in r1["rows"] + re_["rows"]),
        f"最小 {min(q['smin'] for q in r1['rows'] + re_['rows']):.3f}・"
        f"最大 {max(q['smax'] for q in r1['rows'] + re_['rows']):.3f}")

    # --- (6) 目標が厳しいほど要る例数は増える ---
    c5, c4, c3 = (r1["chosen"][t]["a"] for t in (0.05, 0.04, 0.03))
    b5, b3 = r1["chosen"][0.05]["b"], r1["chosen"][0.03]["b"]
    rep("目標 0.03 に要る例数 ≥ 目標 0.05 に要る例数（方法A）",
        c5 is not None and c3 is not None and c3 >= c5, f"0.05→{c5} 例・0.03→{c3} 例")
    rep("目標 0.04 はその間", c4 is not None and c5 <= c4 <= c3, f"0.04→{c4} 例")
    rep("方法B でも同じ向き", b5 is not None and b3 is not None and b3 >= b5,
        f"0.05→{b5} 例・0.03→{b3} 例")

    # --- 半幅そのものの筋 ---
    # 方法B の被覆は 0.95 ちょうどではなく上回るので、半幅は方法A より広くなるのが筋である。
    # ただし例数が多い所では両者がほぼ重なり、引き直しの揺れで 0.0005 ほど逆転することがある
    # （下の 0.001 はその許容。平均では必ず方法B のほうが広い）。
    dif = [q["b_hw"] - q["a_hw"] for q in r1["rows"]]
    rep("方法B の半幅は方法A より広い（被覆が 0.95 を上回るぶん）",
        min(dif) > -0.001 and float(np.mean(dif)) > 0.0,
        f"差の平均 {np.mean(dif):+.5f}・最小 {min(dif):+.5f}"
        f"（n=20 で A {r1['rows'][0]['a_hw']:.4f} ≤ B {r1['rows'][0]['b_hw']:.4f}）")
    rep("例数を増やすと半幅は狭くなる（両端で比べる）",
        r1["rows"][-1]["a_hw"] < r1["rows"][0]["a_hw"]
        and r1["rows"][-1]["b_hw"] < r1["rows"][0]["b_hw"],
        f"A {r1['rows'][0]['a_hw']:.4f} → {r1['rows'][-1]['a_hw']:.4f}")
    rep("方法A の区間が予備的検討の中央値を挟む",
        r1["rows"][0]["a_lo"] <= r1["median"] <= r1["rows"][0]["a_hi"],
        f"{r1['rows'][0]['a_lo']:.3f} ≤ {r1['median']:.3f} ≤ {r1['rows'][0]['a_hi']:.3f}")
    rep("いまの精度（方法B・20 個の値そのもの）が X_(6) 〜 X_(15)",
        r1["pilot_b"] == (float(np.sort(x_norm)[5]), float(np.sort(x_norm)[14])),
        f"{r1['pilot_b'][0]:.3f} 〜 {r1['pilot_b'][1]:.3f}")

    # --- 中央値の取り方が np.median と一致するか（並べ替え済みの配列から取っている） ---
    m = rng.random((7, 8))
    ms = np.sort(m, axis=1)
    mine = 0.5 * (ms[:, 3] + ms[:, 4])
    rep("偶数個の中央値が np.median と一致する（並べ替え済みから取る）",
        np.allclose(mine, np.median(m, axis=1)))
    mo = rng.random((7, 9))
    rep("奇数個でも一致する",
        np.allclose(np.sort(mo, axis=1)[:, 4], np.median(mo, axis=1)))

    # --- 目標を満たす最小の例数の拾い方 ---
    fake = [{"n": 20, "a_hw": 0.09}, {"n": 25, "a_hw": 0.049}, {"n": 30, "a_hw": 0.051},
            {"n": 35, "a_hw": 0.048}, {"n": 40, "a_hw": 0.047}]
    rep("最小の例数は最初に下回った所（揺れても最初を採る）",
        first_at_or_below(fake, "a_hw", 0.05) == 25)
    rep("『それ以降ずっと下回る』は 35 になる",
        stays_at_or_below(fake, "a_hw", 0.05) == 35)
    rep("候補の中に無ければ None", first_at_or_below(fake, "a_hw", 0.001) is None
        and fmt_n(None).strip() == ">500")

    # --- 列の拾い方（接頭辞ごとに全部）---
    d = pd.DataFrame({"caseid": [1, 2, 3], "n_windows": [10, 20, 30],
                      "id_a": [0.1, 0.5, 0.9], "id_b": [1.0, 1.0, 1.0],
                      "ac_a": [0.3, 0.3, 0.3], "ac_b": [-0.2, 0.1, 0.4],
                      "med_a": [1.0, 2.0, 3.0]})
    rep("規準ごとに接頭辞で列を拾う（id_ と ac_ を取り違えない）",
        [c for c in d.columns if c.startswith("id_")] == ["id_a", "id_b"]
        and [c for c in d.columns if c.startswith("ac_")] == ["ac_a", "ac_b"])
    rd2 = analyse_column(d["id_b"].to_numpy(float), grid=[20, 100], n_boot=100)
    rep("すべて 1.0 の列でも落ちない（h=0・半幅 0）",
        rd2["h"] == 0.0 and rd2["rows"][0]["a_hw"] == 0.0,
        f"中央値 {rd2['median']:.2f}・半幅 {rd2['rows'][0]['a_hw']:.3f}")

    # --- 自己相関の列（値は −1〜1・閾値 0.30・欠測あり）---
    x_hi = np.clip(rng.normal(0.95, 0.06, PILOT_N), -1.0, 1.0)    # +1 に張りつく
    x_lo = np.clip(rng.normal(-0.93, 0.09, PILOT_N), -1.0, 1.0)   # −1 に張りつく
    rhi = analyse_column(x_hi, grid=grid, n_boot=nb, domain=(-1.0, 1.0))
    rlo = analyse_column(x_lo, grid=grid, n_boot=nb, domain=(-1.0, 1.0))
    allrows = rhi["rows"] + rlo["rows"]
    rep("自己相関の平滑化した値は [−1,1] に収まる（両端に張りつく予備的検討でも）",
        all(-1.0 <= q["smin"] and q["smax"] <= 1.0 for q in allrows),
        f"最小 {min(q['smin'] for q in allrows):+.3f}・最大 {max(q['smax'] for q in allrows):+.3f}")
    rep("−1 側は 0 で切られない（同定率の範囲を当てていない）",
        min(q["smin"] for q in rlo["rows"]) < 0.0,
        f"最小 {min(q['smin'] for q in rlo['rows']):+.3f}")
    rep("+1 を超えない（上端に張りつく列で丸めが効いている）",
        max(q["smax"] for q in rhi["rows"]) == 1.0,
        f"最大 {max(q['smax'] for q in rhi['rows']):+.3f}")
    r01 = analyse_column(x_lo, grid=[20], n_boot=nb, domain=(0.0, 1.0))
    rep("値の範囲を取り違えると値が変わる（−1〜1 の列に 0〜1 を当てると全部 0 に潰れる）",
        r01["rows"][0]["smax"] == 0.0 and r01["rows"][0]["a_hw"] == 0.0
        and rlo["rows"][0]["a_hw"] > 0.0,
        f"0〜1 を当てた半幅 {r01['rows'][0]['a_hw']:.4f} 対 "
        f"−1〜1 の半幅 {rlo['rows'][0]['a_hw']:.4f}")

    # --- 例数を決める列の選び方（閾値は規準ごとに違う）---
    m_id = {"id_dt": 0.62, "id_amb": 0.95, "id_dt1": 0.08}
    m_ac = {"ac_dt": 0.64, "ac_amb": 0.36, "ac_pwtt": 0.99}
    f_id = {k: {"median": v} for k, v in m_id.items()}
    f_ac = {k: {"median": v} for k, v in m_ac.items()}
    rep("同定率の例数を決めるのは 0.70 に最も近い列",
        pick_driver(f_id, list(m_id), CRITERION) == "id_dt",
        f"{pick_driver(f_id, list(m_id), CRITERION)}（0.62）")
    rep("自己相関の例数を決めるのは 0.30 に最も近い列",
        pick_driver(f_ac, list(m_ac), CRITERION_AC) == "ac_amb",
        f"{pick_driver(f_ac, list(m_ac), CRITERION_AC)}（0.36）")
    rep("同じ列でも閾値が変われば選ばれる列が変わる",
        pick_driver(f_ac, list(m_ac), CRITERION) == "ac_dt",
        f"0.70 を当てると {pick_driver(f_ac, list(m_ac), CRITERION)}（0.64）")

    # --- 欠測（自己相関は対が 10 未満だと出ない）---
    xx, n_na = drop_missing(np.array([0.5, np.nan, 0.2, np.nan, 0.9]))
    rep("欠測を落として、落とした数と残った数が分かる",
        n_na == 2 and xx.size == 3 and np.allclose(xx, [0.5, 0.2, 0.9]),
        f"欠測 {n_na} 例・採用 {xx.size} 例")
    d_ac = pd.DataFrame({"ac_x": [0.5, np.nan, 0.2, 0.1], "npair_x": [50, 8, 30, 10],
                         "ac_y": [0.5, 0.4, np.nan, 0.1], "npair_y": [50, 8, 30, 10]})
    rep(f"欠測が対 {MIN_PAIRS} 未満と一致する列としない列を見分ける",
        npair_check(d_ac, "ac_x") == (True, 1) and npair_check(d_ac, "ac_y") == (False, 1),
        f"ac_x {npair_check(d_ac, 'ac_x')}・ac_y {npair_check(d_ac, 'ac_y')}")
    rep("npair_ 列が無ければ確かめようがないので None",
        npair_check(pd.DataFrame({"ac_z": [0.1, 0.2]}), "ac_z") is None)
    r19 = analyse_column(x_norm[:19], grid=grid, n_boot=nb, domain=(-1.0, 1.0))
    rep("欠測で 19 例になっても、いまの精度と方法B の区間が出せる",
        r19["n_pilot"] == 19 and r19["pilot_a"] is not None
        and r19["pilot_b_k"] == order_stat_k(19),
        f"n_pilot {r19['n_pilot']}・k {r19['pilot_b_k']}")

    # --- 2 つの規準を合わせる（要る例数は大きいほう）---
    nm_id, nm_ac = BLOCKS[0]["name"], BLOCKS[1]["name"]
    rep("要る例数は 2 つの大きいほう（同定率が決める場合）",
        combine_n(315, 280) == (315, nm_id), f"{combine_n(315, 280)}")
    rep("自己相関が決める場合", combine_n(120, 300) == (300, nm_ac), f"{combine_n(120, 300)}")
    rep("同じ例数なら『どちらも同じ』", combine_n(200, 200) == (200, "どちらも同じ"))
    rep("候補の外（>500）があればそちらが決める",
        combine_n(None, 300) == (None, nm_id) and combine_n(300, None) == (None, nm_ac)
        and combine_n(None, None)[0] is None)

    # --- 列を足しても既にある列の値が動かないこと ---
    ra = analyse_column(x_norm, grid=[PILOT_N, 100], n_boot=nb)
    rep("いまの精度は格子の n=20 と同じ中身（生成器を作り直しても引き直しは同じ）",
        ra["pilot_a"] == (ra["rows"][0]["a_lo"], ra["rows"][0]["a_hi"]),
        f"{ra['pilot_a'][0]:.6f} 〜 {ra['pilot_a'][1]:.6f}")
    rep("列名から指標の呼び名を引ける（接頭辞が違っても同じ指標）",
        label_of("id_ens_amb") == label_of("ac_ens_amb") != "（32番の指標）",
        label_of("ac_ens_amb"))

    # --- 定数 ---
    rep("引き直しの回数が 41番と同じ 2,000", N_BOOT == 2000)
    rep("乱数種が主解析と同じ 0", SEED == 0)
    rep("例数の候補が 20 から 500 まで 5 きざみ",
        N_GRID[0] == 20 and N_GRID[-1] == 500 and len(N_GRID) == 97)
    rep("表に出す例数がすべて候補に入っている", all(n in N_GRID for n in SHOW_N))
    rep("事前規準が 32番と同じ 2 つ（同定率 0.70・自己相関 0.30）",
        CRITERION == 0.70 and CRITERION_AC == 0.30)
    rep("規準ごとの値の範囲が正しい（同定率 0〜1・自己相関 −1〜1）",
        BLOCKS[0]["domain"] == (0.0, 1.0) and BLOCKS[1]["domain"] == (-1.0, 1.0)
        and [b["prefix"] for b in BLOCKS] == ["id_", "ac_"])
    rep("例数を決める見込みの列と中央値が 00_decision.md と合っている",
        BLOCKS[0]["driver_expect"] == "id_ens_dt_lm_ms"
        and BLOCKS[1]["driver_expect"] == "ac_ens_amb"
        and EXPECT_MED["id_ens_dt_lm_ms"] == 0.67 and EXPECT_MED["ac_ens_amb"] == 0.36,
        "同定率 0.67・自己相関 0.36")
    rep(f"自己相関に要る隣り合う対の数が 32番と同じ {MIN_PAIRS}", MIN_PAIRS == 10)

    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true", help="合成データで計算の筋道を検算する")
    ap.add_argument("--csv", type=str, default=None, help="入力の CSV（既定は 32番のまとめ）")
    ap.add_argument("--out", type=str, default=None, help="結果ファイル（既定は 43 番の txt）")
    ap.add_argument("--no-write", action="store_true", help="画面に出すだけで書き出さない")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())

    out = None if args.no_write else Path(args.out) if args.out else OUT_DEFAULT
    sys.exit(run(Path(args.csv) if args.csv else CSV_DEFAULT, out))


if __name__ == "__main__":
    main()

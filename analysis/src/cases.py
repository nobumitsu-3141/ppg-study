# -*- coding: utf-8 -*-
"""主解析（scripts/03_run_analysis.py）と同じ並び・同じ規準で症例を組み立てる。

なぜ 1 か所に置くか
--------------------
03 番は data/target_cases.csv の **行順** に症例を並べて crossval(seed=0) に渡す。
5-fold は乱数種 0 の置換で切るので、**並びが変われば fold の割り付けが変わり**、
percentage error も信頼区間も 0.1 ポイント単位で動く。
41・09・12・07 番はそれぞれ data/features/ の **ファイル名順** で並べていたため、
症例の集合は同じでも主解析と割り付けが一致していなかった。並べ方をここへ集約する。

採否の規準（03 番 main() の組み立てと同じ）
--------------------------------------------
  1. data/target_cases.csv を先頭の行から順に見る
  2. pick_device(row, None) が None の行（使えるCOトラックが無い）は飛ばす
  3. data/cases.csv の height が欠損または 100cm 未満なら飛ばす
  4. ここまで通った症例が limit 件に達したら打ち切る（既定 900 ＝ 主解析の --limit）
  5. data/features/case_{id}.csv が読めない、または行数が MIN_WINDOWS 未満なら飛ばす
meta.json の有無・版は条件にしない（03 番 --stats-only と同じ）。
pick_device と MIN_WINDOWS は 03 番の実物を読み込んで使う（写し取ると黙ってずれる）。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FEAT = DATA / "features"
KEYS = ["pwtt", "si", "ri", "hr", "map", "co_ref"]
LIMIT = 900                 # 主解析の --limit 900

_M03 = None                 # 03_run_analysis.py（読み込みは 1 回だけ）


def _m03():
    """03_run_analysis.py を読み込む。pick_device と MIN_WINDOWS を借りるため。"""
    global _M03
    if _M03 is None:
        spec = importlib.util.spec_from_file_location(
            "_m03_for_cases", ROOT / "scripts" / "03_run_analysis.py")
        m = importlib.util.module_from_spec(spec)
        sys.modules["_m03_for_cases"] = m
        spec.loader.exec_module(m)
        _M03 = m
    return _M03


def min_windows() -> int:
    """症例採用に必要な有効ウィンドウ数（03 番の定数）。"""
    return int(_m03().MIN_WINDOWS)


def case_order(limit: int = LIMIT) -> list[tuple[int, str, float]]:
    """主解析と同じ並びの (caseid, 参照CO装置, 身長[m])。target_cases.csv の行順。"""
    m03 = _m03()
    tc = pd.read_csv(DATA / "target_cases.csv")
    demo = pd.read_csv(DATA / "cases.csv")[["caseid", "height"]].set_index("caseid")
    todo: list[tuple[int, str, float]] = []
    n_try = 0
    for _, row in tc.iterrows():
        if n_try >= limit:
            break
        caseid = int(row["caseid"])
        dev = m03.pick_device(row, None)
        if dev is None:
            continue
        h_cm = float(demo["height"].get(caseid, np.nan))
        if not np.isfinite(h_cm) or h_cm < 100:
            continue
        n_try += 1
        todo.append((caseid, dev, h_cm / 100.0))
    return todo


def load_cached_cases(limit: int = LIMIT, min_windows: int | None = None,
                      verbose: bool = True) -> list[dict]:
    """data/features/ のキャッシュから、主解析と同じ並び・同じ規準で症例を組み立てる。

    返り値の 1 症例:
        {"caseid": int, "height": float(m), "device": str,
         "windows": {"pwtt","si","ri","hr","map","co_ref" → float の ndarray}}
    """
    min_w = min_windows if min_windows is not None else _m03().MIN_WINDOWS
    cases: list[dict] = []
    for cid, dev, h_m in case_order(limit):
        f = FEAT / f"case_{cid}.csv"
        if not f.exists():
            continue
        try:
            df = pd.read_csv(f)
        except Exception:
            continue        # 有効ウィンドウ0の症例は空CSV。採用基準未満なので対象外
        if len(df) < min_w:
            continue
        cases.append({
            "caseid": cid, "height": h_m,
            "windows": {k: df[k].to_numpy(float) for k in KEYS},
            "device": dev,
        })
    if verbose:
        print(f"キャッシュから {len(cases)} 症例 "
              f"（{sum(len(c['windows']['pwtt']) for c in cases):,} ウィンドウ）")
    return cases


def aggregate(case: dict, k: int) -> dict | None:
    """連続する有効ウィンドウ k 個ずつの平均で1ブロックを作る（09・41 番で共用）。

    採用は「較正1＋評価5以上」= 6ブロック以上（探索的解析のためここで固定）。
    棄却で生じた時間の飛びは詰める（真に連続な k 分ではない。本文に明記）。
    """
    w = case["windows"]
    n = len(w["pwtt"]) // k
    if n < 6:
        return None
    agg = {key: np.array([np.nanmean(w[key][i * k:(i + 1) * k]) for i in range(n)])
           for key in KEYS}
    return {"caseid": case["caseid"], "height": case["height"],
            "windows": agg, "device": case.get("device")}

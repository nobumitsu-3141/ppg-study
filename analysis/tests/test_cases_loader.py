# -*- coding: utf-8 -*-
"""src/cases.py の検査: 症例の並びが主解析と同じ target_cases.csv の行順になるか。

なぜ検査するか
--------------
交差検証の 5-fold は乱数種 0 の置換で切る。症例の並びが変われば fold の割り付けが
変わり、percentage error も信頼区間も 0.1 ポイント単位で動く。41・09・12・07 番は
以前 data/features/ の **ファイル名順** で並べていて、主解析（03 番）の
target_cases.csv の **行順** と一致していなかった。その取り違えを検出する。

合成データで見分けがつくようにしてある: 行順は 7 → 100 → 20 だが、
ファイル名順なら case_100 が先に来る。

実行:
    analysis/ で  python3 -m tests.test_cases_loader
    pytest があれば  python3 -m pytest tests/test_cases_loader.py -q
"""
from __future__ import annotations

import contextlib
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import cases as cases_mod  # noqa: E402

DEVICES = ("Vigileo", "EV1000", "Vigilance", "CardioQ")

# (caseid, 参照CO装置, 身長cm, 有効ウィンドウ数)
#   7   採用
#   100 採用（ファイル名順なら先頭に来る＝並びの取り違えを検出する）
#   20  採用
#   3   COトラック無し   → pick_device が None
#   40  身長 100cm 未満  → 除外
#   55  ウィンドウ不足   → MIN_WINDOWS(12) 未満
PLAN = [(7, "EV1000", 170.0, 20), (100, "Vigileo", 165.0, 20), (20, "CardioQ", 158.0, 20),
        (3, None, 160.0, 20), (40, "EV1000", 80.0, 20), (55, "EV1000", 172.0, 5)]
ORDER = [7, 100, 20, 55]    # case_order（症例一覧だけで決まる。特徴量は見ない）
KEPT = [7, 100, 20]         # load_cached_cases（55 はウィンドウ不足で落ちる）


def _write(data: Path) -> None:
    """03 番・11 番が書くのと同じ書式の小さな入力一式を作る。"""
    rng = np.random.default_rng(0)
    (data / "features").mkdir(parents=True, exist_ok=True)
    tc_rows, demo_rows = [], []
    for cid, dev, h_cm, n_win in PLAN:
        row = {"caseid": cid}
        for d in DEVICES:
            row[f"{d}_CO"] = (d == dev)
        tc_rows.append(row)
        demo_rows.append({"caseid": cid, "height": h_cm})
        pd.DataFrame({
            "t0": np.arange(n_win) * 60.0,
            "pwtt": 0.25 + 0.01 * rng.standard_normal(n_win),
            "si": 8.0 + rng.standard_normal(n_win),
            "ri": 0.5 + 0.05 * rng.standard_normal(n_win),
            "hr": 70.0 + 5 * rng.standard_normal(n_win),
            "map": 80.0 + 5 * rng.standard_normal(n_win),
            "co_ref": 5.0 + 0.3 * rng.standard_normal(n_win),
        }).to_csv(data / "features" / f"case_{cid}.csv", index=False)
    pd.DataFrame(tc_rows).to_csv(data / "target_cases.csv", index=False)
    pd.DataFrame(demo_rows).to_csv(data / "cases.csv", index=False, encoding="utf-8-sig")


@contextlib.contextmanager
def fixture():
    """一時ディレクトリに合成データを作り、src.cases の参照先をそこへ向ける。"""
    with tempfile.TemporaryDirectory() as td:
        data = Path(td)
        _write(data)
        keep = (cases_mod.DATA, cases_mod.FEAT)
        cases_mod.DATA, cases_mod.FEAT = data, data / "features"
        try:
            yield data
        finally:
            cases_mod.DATA, cases_mod.FEAT = keep


def test_case_order_follows_target_cases_rows():
    """case_order は target_cases.csv の行を上から順に見る（特徴量の有無は見ない）。"""
    with fixture():
        order = cases_mod.case_order()
    assert [cid for cid, _dev, _h in order] == ORDER
    assert [dev for _cid, dev, _h in order] == ["EV1000", "Vigileo", "CardioQ", "EV1000"]
    assert [round(h, 2) for _cid, _dev, h in order] == [1.70, 1.65, 1.58, 1.72]


def test_loader_is_not_filename_order():
    """ファイル名順（case_100 が先頭）で並べていないこと。"""
    with fixture() as data:
        got = [c["caseid"] for c in cases_mod.load_cached_cases(verbose=False)]
        by_name = [int(p.stem.split("_")[1])
                   for p in sorted((data / "features").glob("case_*.csv"))]
    assert got == KEPT
    assert by_name[0] == 100 and got[0] == 7


def test_loader_skips_unusable_cases():
    """装置なし・身長100cm未満・ウィンドウ不足の症例は落ちる。"""
    with fixture():
        cases = cases_mod.load_cached_cases(verbose=False)
    assert [c["caseid"] for c in cases] == KEPT
    assert [c["device"] for c in cases] == ["EV1000", "Vigileo", "CardioQ"]
    c0 = cases[0]
    assert set(c0["windows"]) == set(cases_mod.KEYS)
    assert len(c0["windows"]["co_ref"]) == 20
    assert c0["windows"]["pwtt"].dtype == float


def test_limit_counts_from_the_top():
    """limit は target_cases.csv の先頭から数える（03 番の --limit と同じ）。"""
    with fixture():
        assert [c["caseid"] for c in cases_mod.load_cached_cases(limit=2, verbose=False)] == [7, 100]
        assert [cid for cid, _d, _h in cases_mod.case_order(limit=1)] == [7]


def test_min_windows_comes_from_the_main_script():
    """採用に要るウィンドウ数は 03 番の定数（写し取らない）。"""
    assert cases_mod.min_windows() == 12
    with fixture():
        assert [c["caseid"] for c in
                cases_mod.load_cached_cases(min_windows=25, verbose=False)] == []


def main() -> int:
    ok = True
    for name, fn in sorted(globals().items()):
        if not (name.startswith("test_") and callable(fn)):
            continue
        try:
            fn()
            print(f"  [PASS] {name}")
        except AssertionError as e:
            ok = False
            print(f"  [FAIL] {name}  {e}")
    print("ALL PASS" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
"""P1-1: 装置別のCOトラック×波形トラックの保有状況を集計する。

実行:  python3 scripts/01_track_inventory.py
入力:  data/cases.csv, data/trks.csv（scripts/00 で取得）
出力:  画面に集計表、data/target_cases.csv（4トラックが揃う症例の一覧）

スライド6.7の「552例」がどのトラック定義で再現されるかをここで確定させる。
参照COの装置内訳（Vigileo/EV1000/Vigilance/CardioQ）も出す —
FloTrac系（動脈圧由来）と熱希釈系（Vigilance II）は解析で区別する（6.9改訂の根拠）。
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"

# 波形トラック（SNUADC = 500Hz ADC）。実名は下の「候補一覧」出力で必ず確認する。
WAVE_PATTERNS = {
    "pleth": r"^SNUADC/PLETH",
    "ecg": r"^SNUADC/ECG",
    "art": r"^SNUADC/ART",
}
# COを持ちうる装置のトラック（CO/CI/SV系の数値トラック）
CO_PATTERN = r"^(Vigileo|EV1000|Vigilance|CardioQ)/(CO|CI|SV|SVI)$"


def check_csv(path: Path) -> None:
    """壊れた入力を分かりやすく弾く（gzipのまま保存されている等）。"""
    if not path.exists():
        raise SystemExit(f"{path} がありません。先に python scripts/00_download_lists.py を実行してください。")
    with open(path, "rb") as f:
        head = f.read(2)
    if head == b"\x1f\x8b":
        raise SystemExit(
            f"{path} が gzip のまま保存されています（展開されていない）。\n"
            "python scripts/00_download_lists.py を再実行してください（展開に対応済み）。")


def main() -> None:
    for name in ("trks.csv", "cases.csv"):
        check_csv(DATA / name)
    trks = pd.read_csv(DATA / "trks.csv", low_memory=False)
    cases = pd.read_csv(DATA / "cases.csv", low_memory=False)
    print(f"cases: {cases.shape[0]}  tracks: {trks.shape[0]}")

    # --- まず名前の候補を目視確認（命名が変わっていたらパターンを直す） ---
    names = trks["tname"].dropna().unique()
    print("\n[候補一覧] SNUADC 系:")
    print(sorted(n for n in names if n.startswith("SNUADC")))
    print("\n[候補一覧] CO 装置系:")
    print(sorted(n for n in names if re.match(r"^(Vigileo|EV1000|Vigilance|CardioQ)/", n)))

    # --- 症例ごとの保有フラグ ---
    have = pd.DataFrame({"caseid": cases["caseid"]}).set_index("caseid")
    for key, pat in WAVE_PATTERNS.items():
        ids = trks.loc[trks["tname"].str.match(pat, na=False), "caseid"].unique()
        have[key] = have.index.isin(ids)
    co_trks = trks[trks["tname"].str.match(CO_PATTERN, na=False)].copy()
    co_trks["device"] = co_trks["tname"].str.split("/").str[0]
    for dev in ["Vigileo", "EV1000", "Vigilance", "CardioQ"]:
        ids = co_trks.loc[co_trks["device"] == dev, "caseid"].unique()
        have[f"co_{dev}"] = have.index.isin(ids)
    have["co_any"] = have[[c for c in have.columns if c.startswith("co_")]].any(axis=1)

    # --- 集計 ---
    print("\n[集計]")
    for c in have.columns:
        print(f"  {c:12s}: {int(have[c].sum()):5d} 例")
    target = have[have["pleth"] & have["ecg"] & have["art"] & have["co_any"]]
    print(f"\n  4トラック（pleth+ecg+art+CO系）が揃う症例: {len(target)} 例"
          f"  ← スライド6.7の552例と照合すること")
    print("  うち装置別（重複あり）:")
    for dev in ["Vigileo", "EV1000", "Vigilance", "CardioQ"]:
        print(f"    {dev:10s}: {int(target[f'co_{dev}'].sum()):5d} 例")

    out = DATA / "target_cases.csv"
    target.reset_index().to_csv(out, index=False)
    print(f"\nsaved: {out}")


if __name__ == "__main__":
    main()

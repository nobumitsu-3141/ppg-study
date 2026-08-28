# -*- coding: utf-8 -*-
"""P1-1: 装置別のCOトラック×波形トラックの保有状況を集計する。

実行:  python scripts/01_track_inventory.py
入力:  data/cases.csv, data/trks.csv（scripts/00 で取得）
出力:  画面に集計表、data/target_cases.csv（計画書の選択基準を満たす症例の一覧）

スライド6.7の「心拍出量＋500Hz脈波＋心電図＋動脈圧＝552例」がどのトラック定義で
再現されるかをここで確定させる。参照COの装置内訳も出す —
FloTrac系（Vigileo/EV1000: 動脈圧由来）と熱希釈系（Vigilance II: 肺動脈カテ）は
解析で区別する。後者は「真の参照値」であり、前者は解析対象と同じ信号領域から
導出されるため一致度の解釈が異なる（6.9改訂の根拠）。
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"

WAVE_PATTERNS = {
    "pleth": r"^SNUADC/PLETH",
    "ecg": r"^SNUADC/ECG",
    "art": r"^SNUADC/ART",
}
DEVICES = ["Vigileo", "EV1000", "Vigilance", "CardioQ"]
# 解析で実際に使うのは CO トラックのみ。CI/SV/SVI しか無い症例は使えないので分けて数える。
CO_STRICT = r"^(%s)/CO$" % "|".join(DEVICES)
CO_LOOSE = r"^(%s)/(CO|CI|SV|SVI)$" % "|".join(DEVICES)


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


def device_flags(trks: pd.DataFrame, index, pattern: str, suffix: str) -> pd.DataFrame:
    """装置ごとの保有フラグ列を作る。"""
    sub = trks[trks["tname"].str.match(pattern, na=False)].copy()
    sub["device"] = sub["tname"].str.split("/").str[0]
    out = pd.DataFrame(index=index)
    for dev in DEVICES:
        out[f"{dev}{suffix}"] = index.isin(sub.loc[sub["device"] == dev, "caseid"].unique())
    return out


def main() -> None:
    for name in ("trks.csv", "cases.csv"):
        check_csv(DATA / name)
    trks = pd.read_csv(DATA / "trks.csv", low_memory=False)
    cases = pd.read_csv(DATA / "cases.csv", low_memory=False)
    print(f"cases: {cases.shape[0]:,}  tracks: {trks.shape[0]:,}")

    names = trks["tname"].dropna().unique()
    print("\n[候補一覧] SNUADC 系:")
    print("  " + ", ".join(sorted(n for n in names if n.startswith("SNUADC"))))
    print("[候補一覧] CO装置系:")
    print("  " + ", ".join(sorted(n for n in names if re.match(r"^(%s)/" % "|".join(DEVICES), n))))

    idx = pd.Index(cases["caseid"].unique(), name="caseid")
    have = pd.DataFrame(index=idx)
    for key, pat in WAVE_PATTERNS.items():
        have[key] = idx.isin(trks.loc[trks["tname"].str.match(pat, na=False), "caseid"].unique())
    strict = device_flags(trks, idx, CO_STRICT, "_CO")
    loose = device_flags(trks, idx, CO_LOOSE, "_any")
    have = pd.concat([have, strict, loose], axis=1)
    have["co_strict"] = strict.any(axis=1)
    have["co_loose"] = loose.any(axis=1)

    print("\n[波形トラックの保有]")
    for k in WAVE_PATTERNS:
        print(f"  {k:6s}: {int(have[k].sum()):6,d} 例")
    base = have["pleth"] & have["ecg"]
    print(f"  pleth+ecg          : {int(base.sum()):6,d} 例")
    print(f"  pleth+ecg+art      : {int((base & have['art']).sum()):6,d} 例")

    print("\n[CO系トラックの保有（装置別）]")
    print(f"  {'装置':<12}{'CO のみ':>10}{'CO/CI/SV/SVI':>15}")
    for dev in DEVICES:
        print(f"  {dev:<12}{int(have[f'{dev}_CO'].sum()):>10,d}{int(have[f'{dev}_any'].sum()):>15,d}")
    print(f"  {'いずれか':<12}{int(have['co_strict'].sum()):>10,d}{int(have['co_loose'].sum()):>15,d}")

    print("\n[コホート候補]")
    coh = {
        "A  pleth+ecg+CO           （動脈圧を求めない）": base & have["co_strict"],
        "B  pleth+ecg+art+CO       （計画書の選択基準）": base & have["art"] & have["co_strict"],
        "C  pleth+ecg+art+CO系いずれか（CI/SV/SVIも可）": base & have["art"] & have["co_loose"],
    }
    for label, m in coh.items():
        print(f"  {label}: {int(m.sum()):5,d} 例")
    target = have[coh["B  pleth+ecg+art+CO       （計画書の選択基準）"]]
    print(f"\n  ← スライド6.7の552例と照合するのは B。今回 {len(target):,} 例。")

    print("\n  装置別内訳（B・重複あり）:")
    for dev in DEVICES:
        print(f"    {dev:<12}: {int(target[f'{dev}_CO'].sum()):5,d} 例")

    print("\n[各装置がBから落ちる理由]")
    print(f"  {'装置':<12}{'CO保有':>8}{'→B残':>7}   {'欠落の内訳（重複あり）'}")
    for dev in DEVICES:
        d = have[have[f"{dev}_CO"]]
        kept = int((d["pleth"] & d["ecg"] & d["art"]).sum())
        miss = " / ".join(f"{k}欠 {int((~d[k]).sum())}" for k in WAVE_PATTERNS)
        print(f"  {dev:<12}{len(d):>8,d}{kept:>7,d}   {miss}")

    out = DATA / "target_cases.csv"
    target.reset_index().to_csv(out, index=False)
    print(f"\nsaved: {out}  ({len(target):,} 例)")
    print("次: python scripts/02_fetch_case.py <caseid>")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""P0-3の前段: VitalDB の症例一覧・トラック一覧をダウンロードする。

実行（Mac のターミナル, analysis/ で）:
    python3 scripts/00_download_lists.py

※ このスクリプトは api.vitaldb.net に接続する。事前に vitaldb.net で
   アカウント登録とデータ利用規約への同意を済ませておくこと（P0-1）。
   引用要件: Lee HC, et al. Sci Data 2022;9:279 (PMID 35676300)。
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
URLS = {
    "cases.csv": "https://api.vitaldb.net/cases",   # 症例ごとの臨床情報（年齢・身長・体重など）
    "trks.csv": "https://api.vitaldb.net/trks",     # トラック一覧（caseid, tname, tid）
}


def main() -> None:
    DATA.mkdir(exist_ok=True)
    for name, url in URLS.items():
        out = DATA / name
        print(f"downloading {url} -> {out}")
        urllib.request.urlretrieve(url, out)
        print(f"  {out.stat().st_size/1e6:.1f} MB")
    print("done. 次: python3 scripts/01_track_inventory.py")


if __name__ == "__main__":
    main()

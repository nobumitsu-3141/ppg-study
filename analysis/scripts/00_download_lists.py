# -*- coding: utf-8 -*-
"""P0-3の前段: VitalDB の症例一覧・トラック一覧をダウンロードする。

実行（Mac のターミナル, analysis/ で・仮想環境を有効にした状態）:
    python scripts/00_download_lists.py

※ このスクリプトは api.vitaldb.net に接続する。事前に vitaldb.net で
   アカウント登録とデータ利用規約への同意を済ませておくこと（P0-1）。
   引用要件: Lee HC, et al. Sci Data 2022;9:279 (PMID 35676300)。

注意: api.vitaldb.net は Content-Encoding: gzip で応答する。
      urllib.request.urlretrieve は本体を展開せずそのまま保存するため、
      圧縮バイトが .csv として残り、後段の read_csv が
      UnicodeDecodeError（0x8b = gzip の識別バイト）で落ちる。
      そのため下の fetch() で明示的に展開してから保存する。
"""
from __future__ import annotations

import gzip
import urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
URLS = {
    "cases.csv": "https://api.vitaldb.net/cases",   # 症例ごとの臨床情報（年齢・身長・体重など）
    "trks.csv": "https://api.vitaldb.net/trks",     # トラック一覧（caseid, tname, tid）
}
UA = "ppg-study/0.1 (academic research; https://github.com/nobumitsu-3141/ppg-study)"


def fetch(url: str, timeout: int = 300) -> bytes:
    """URL を取得し、gzip なら展開して返す。

    Content-Encoding ヘッダがある場合と、ヘッダ無しで本体だけ gzip の場合の
    両方に対応する（識別バイト 1f 8b で判定）。
    """
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=timeout) as res:
        raw = res.read()
        enc = (res.headers.get("Content-Encoding") or "").lower()
    if "gzip" in enc or raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return raw


def main() -> None:
    import pandas as pd
    DATA.mkdir(exist_ok=True)
    for name, url in URLS.items():
        out = DATA / name
        print(f"downloading {url}")
        out.write_bytes(fetch(url))
        # ここで読めることを確認しておく（壊れていれば次のスクリプトを待たずに分かる）
        df = pd.read_csv(out, low_memory=False)
        cols = ", ".join(map(str, df.columns[:8])) + (" …" if df.shape[1] > 8 else "")
        print(f"  -> {out}  {out.stat().st_size / 1e6:.1f} MB  "
              f"{df.shape[0]:,} 行 × {df.shape[1]} 列")
        print(f"     列: {cols}")
    print("\ndone. 次: python scripts/01_track_inventory.py")


if __name__ == "__main__":
    main()

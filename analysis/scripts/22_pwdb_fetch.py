#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""研究0: PWDB の巨大 zip から、必要な3ファイルだけを HTTP Range で取り出す。

Zenodo の配布物は数十 GB の zip だが、本研究に要るのは
  pwdb_haemod_params.csv / pwdb_model_configs.csv / PWs_Digital_PPG.csv
の3本だけで、合計しても数十 MB である。zip は末尾の「中央ディレクトリ」に
全メンバーの位置が書かれているので、Range リクエストで末尾だけ読み、
必要なメンバーの区間だけを取れば、全体を落とす必要がない。

使い方（URL は Zenodo の記録ページで Download を右クリック → リンクをコピー）:
    python scripts/22_pwdb_fetch.py --list "https://zenodo.org/records/3275625/files/<zip名>?download=1"
        中身の一覧（フォルダ別の件数と、取り出す対象）だけ表示する
    python scripts/22_pwdb_fetch.py --out ~/pwdb "https://zenodo.org/records/3275625/files/<zip名>?download=1"
        3ファイルを ~/pwdb に取り出す。そのあと 20_pwdb_validity.py --pwdb ~/pwdb
    python scripts/22_pwdb_fetch.py --selftest
        ローカルの模擬サーバで動作を確認する（ネットワーク不要）

サーバが Range に応じない（HTTP 206 を返さない）場合や、配布物が zip でない
（tar.gz・.mat）場合は使えない。そのときは
    curl -L -C - -o <ファイル名> "<URL>"
で再開可能な全体取得に切り替える。
"""
from __future__ import annotations

import argparse
import fnmatch
import io
import shutil
import sys
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

PATTERNS = ["*haemod*param*.csv", "*model*config*.csv", "*digital*ppg*.csv"]
CHUNK = 4 << 20          # 1回の Range で最低これだけ先読みする（要求回数を減らす）
UA = "ppg-study-pwdb-fetch/1.0"


class HttpFile(io.RawIOBase):
    """HTTP Range で読む、シーク可能なファイル風オブジェクト。zipfile にそのまま渡せる。"""

    def __init__(self, url: str, chunk: int = CHUNK):
        super().__init__()
        self.url, self.chunk = url, chunk
        self.pos = 0
        self.buf, self.buf_start = b"", 0
        self.fetched, self.requests = 0, 0
        self.size = self._probe()

    def _request(self, start: int, end: int) -> bytes:
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={start}-{end}",
                                                        "User-Agent": UA})
        with urllib.request.urlopen(req, timeout=180) as r:
            if r.status != 206:
                raise RuntimeError(f"サーバが Range に応じません（HTTP {r.status}）。"
                                   "curl -L -C - で全体を取得してください")
            data = r.read()
        self.requests += 1
        self.fetched += len(data)
        return data

    def _probe(self) -> int:
        req = urllib.request.Request(self.url, headers={"Range": "bytes=0-0", "User-Agent": UA})
        with urllib.request.urlopen(req, timeout=180) as r:
            if r.status != 206:
                raise RuntimeError(f"サーバが Range に応じません（HTTP {r.status}）。"
                                   "curl -L -C - で全体を取得してください")
            cr = r.headers.get("Content-Range", "")
            r.read()
        try:
            return int(cr.rsplit("/", 1)[1])
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"Content-Range を解釈できません: {cr!r}") from e

    # --- io 契約 ---
    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, off: int, whence: int = 0) -> int:
        if whence == 0:
            self.pos = off
        elif whence == 1:
            self.pos += off
        elif whence == 2:
            self.pos = self.size + off
        else:
            raise ValueError(whence)
        self.pos = max(0, self.pos)
        return self.pos

    def read(self, n: int = -1) -> bytes:
        if n is None or n < 0:
            n = self.size - self.pos
        if n <= 0 or self.pos >= self.size:
            return b""
        n = min(n, self.size - self.pos)
        hit = self.buf_start <= self.pos and self.pos + n <= self.buf_start + len(self.buf)
        if not hit:
            start = self.pos
            end = min(max(self.pos + n, self.pos + self.chunk), self.size) - 1
            self.buf, self.buf_start = self._request(start, end), start
        off = self.pos - self.buf_start
        out = self.buf[off:off + n]
        self.pos += len(out)
        return out

    def readinto(self, b) -> int:
        data = self.read(len(b))
        b[:len(data)] = data
        return len(data)


def _wanted(names: list[str], patterns: list[str]) -> list[str]:
    return [n for n in names
            if any(fnmatch.fnmatch(Path(n).name.lower(), p) for p in patterns)]


def fetch(url: str, out: Path | None, patterns: list[str] = PATTERNS,
          list_only: bool = False) -> dict:
    hf = HttpFile(url)
    print(f"アーカイブ {hf.size / 1e9:.2f} GB。中央ディレクトリを読む …", flush=True)
    try:
        zf = zipfile.ZipFile(hf)
    except zipfile.BadZipFile as e:
        raise SystemExit("zip として読めません。tar.gz や .mat の配布物は Range では取り出せないので、"
                         "curl -L -C - で全体を取得してください。") from e
    with zf:
        names = zf.namelist()
        want = _wanted(names, patterns)
        print(f"  メンバー {len(names):,} 件（ここまでの読み取り {hf.fetched / 1e6:.1f} MB・{hf.requests} 回）")
        if list_only or not want:
            top = Counter(n.split("/")[0] if "/" in n else "(root)" for n in names)
            print("  フォルダ別の件数:")
            for k, v in top.most_common(20):
                print(f"    {k:<40} {v:>8,}")
            print("  取り出す対象:" if want else "  必要ファイルが見当たりません。上の一覧から名前を確かめてください。")
            for n in want:
                print(f"    {n}  ({zf.getinfo(n).file_size / 1e6:.1f} MB)")
            return {"names": names, "want": want, "fetched": hf.fetched, "size": hf.size}
        assert out is not None
        out.mkdir(parents=True, exist_ok=True)
        for n in want:
            info = zf.getinfo(n)
            dest = out / Path(n).name
            print(f"  取り出し {n}  ({info.file_size / 1e6:.1f} MB)", flush=True)
            with zf.open(info) as src, open(dest, "wb") as dst:
                shutil.copyfileobj(src, dst, 1 << 20)
    print(f"完了: 取得 {hf.fetched / 1e6:.1f} MB / 全体 {hf.size / 1e9:.2f} GB"
          f"（要求 {hf.requests} 回）→ {out}")
    return {"names": names, "want": want, "fetched": hf.fetched, "size": hf.size}


# ---------------------------------------------------------------- 自己検証
def selftest() -> int:
    """Range 対応の模擬サーバに巨大ダミー入りの zip を置き、必要3本だけが取れることを確かめる。"""
    import http.server
    import os
    import tempfile
    import threading

    ok = True
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        big = os.urandom(24 << 20)                       # 圧縮の効かない 24 MB のダミー
        zpath = td / "pwdb_big.zip"
        with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("exported_data/junk/wave_dummy.bin", big)
            zf.writestr("exported_data/pwdb_haemod_params.csv", "Subject Number, age [y]\n1, 55\n2, 65\n")
            zf.writestr("exported_data/pwdb_model_configs.csv", "Subject Number, age [y]\n1, 55\n2, 65\n")
            zf.writestr("exported_data/PWs/csv/PWs_Digital_PPG.csv", "Subject Number, pt1\n1, 0.1\n2, 0.2\n")
            zf.writestr("exported_data/PWs/csv/PWs_Radial_P.csv", "x\n" * 1000)
        total = zpath.stat().st_size

        class RangeHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *a, **k):
                super().__init__(*a, directory=str(td), **k)

            def log_message(self, *a):  # 静かに
                pass

            def do_GET(self):
                p = Path(td) / self.path.lstrip("/").split("?")[0]
                rng = self.headers.get("Range")
                data = p.read_bytes()
                if rng and rng.startswith("bytes="):
                    a, b = rng[6:].split("-")
                    a = int(a)
                    b = int(b) if b else len(data) - 1
                    b = min(b, len(data) - 1)
                    self.send_response(206)
                    self.send_header("Content-Range", f"bytes {a}-{b}/{len(data)}")
                    self.send_header("Content-Length", str(b - a + 1))
                    self.end_headers()
                    self.wfile.write(data[a:b + 1])
                else:
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)

        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), RangeHandler)
        th = threading.Thread(target=srv.serve_forever, daemon=True)
        th.start()
        url = f"http://127.0.0.1:{srv.server_address[1]}/pwdb_big.zip?download=1"
        try:
            out = td / "out"
            r = fetch(url, out)
            got = sorted(q.name for q in out.iterdir())
            want = ["PWs_Digital_PPG.csv", "pwdb_haemod_params.csv", "pwdb_model_configs.csv"]
            c1 = got == want
            c2 = (out / "PWs_Digital_PPG.csv").read_text().startswith("Subject Number, pt1")
            c3 = r["fetched"] < 0.5 * total
            ok = c1 and c2 and c3
            print(f"  必要3本だけ取り出せた  {'PASS' if c1 else 'FAIL'}  {got}")
            print(f"  中身が正しい          {'PASS' if c2 else 'FAIL'}")
            print(f"  全体の半分未満の読み取りで済んだ  {'PASS' if c3 else 'FAIL'}"
                  f"  ({r['fetched'] / 1e6:.1f} MB / {total / 1e6:.1f} MB)")
        finally:
            srv.shutdown()
    print("ALL PASS" if ok else "FAILED")
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", nargs="?", help="zip の直リンク（Zenodo の Download のリンク）")
    ap.add_argument("--out", type=Path, default=Path("~/pwdb").expanduser(),
                    help="取り出し先（既定 ~/pwdb）")
    ap.add_argument("--list", action="store_true", help="中身の一覧だけ表示する")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())
    if not args.url:
        ap.error("zip の URL を指定してください（--selftest なら不要）")
    fetch(args.url, None if args.list else args.out.expanduser(), list_only=args.list)


if __name__ == "__main__":
    main()

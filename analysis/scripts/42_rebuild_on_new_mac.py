#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主解析を回していない機械で、表を埋めるところまで一本で走らせる。

`data/features/` が無い機械（2 台目）で 41番を動かすには、VitalDB から取得して特徴量を
作り直す必要がある。その一連（00番 → 01番 → 03番 → 41番）を順に呼ぶだけの台本である。
**解析の中身には一切触れない。**

いちばん大事なこと ― 時間をかける前に版を照合する
--------------------------------------------------
確認的解析は Python 3.9.6・NumPy 2.0.2・SciPy 1.13.1・pandas 2.3.3・vitaldb 1.5.8 で
回した。**版が違うと特徴量が変わりうる。**とくに vitaldb は 1.7.2 で波形の再標本化が
変わり（欠測の埋め方・±20 ms のずれ）、拍の型と脈波伝播時間が変わる。
数時間かけたあとで「使えない数字だった」となるのを避けるため、**取得を始める前に
版を照合して、違えば既定で止まる。**

なお 41番は最後に確定値（症例数 862、表2 の r² 0.000・β −0.027 など）の再現を検査する。
**そこを通らなければ表には写せない。**この台本の版の照合は、その手前で気づくためのもの。

使い方（analysis/ の中で）
    python3 scripts/42_rebuild_on_new_mac.py --selftest   台本の筋道を検算する
    python3 scripts/42_rebuild_on_new_mac.py --check      版と進み具合だけ見る（数秒）
    python3 scripts/42_rebuild_on_new_mac.py --run        取得から表の値まで通す（数時間）

途中で止めてよい。03番は症例ごとに `data/features/` へ書くので、
**もう一度 `--run` すれば続きから進む。**
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FEAT = DATA / "features"

# 確認的解析を回した環境（原稿 §2.10 と requirements.txt に記載）
REF = {"python": "3.9.6", "numpy": "2.0.2", "scipy": "1.13.1",
       "pandas": "2.3.3", "vitaldb": "1.5.8"}
# vitaldb だけは違うと結果が変わることが分かっている（lab_log 追記22）
CRITICAL = {"vitaldb"}
N_TARGET = 862          # 主解析の解析症例数
LIMIT = 900             # target_cases.csv の先頭から見る症例数（874 例を含む余裕）


def versions() -> dict:
    import platform
    got = {"python": platform.python_version()}
    for mod in ("numpy", "scipy", "pandas", "vitaldb"):
        try:
            got[mod] = __import__(mod).__version__
        except Exception:
            got[mod] = None
    return got


def check_versions(got: dict) -> tuple[list, list]:
    hard, soft = [], []
    for k, want in REF.items():
        g = got.get(k)
        if g is None:
            (hard if k in CRITICAL else soft).append((k, "未導入", want))
        elif g != want:
            (hard if k in CRITICAL else soft).append((k, g, want))
    return hard, soft


def progress() -> dict:
    n_meta = len(list(FEAT.glob("case_*_meta.json"))) if FEAT.exists() else 0
    return {
        "cases_csv": (DATA / "cases.csv").exists(),
        "trks_csv": (DATA / "trks.csv").exists(),
        "target_csv": (DATA / "target_cases.csv").exists(),
        "n_extracted": n_meta,
    }


def show(got: dict, hard: list, soft: list, pr: dict) -> None:
    print("== 版の照合（確認的解析を回した環境と比べる） ==")
    for k, want in REF.items():
        g = got.get(k) or "未導入"
        mark = "一致" if g == want else ("★違う" if k in CRITICAL else "違う")
        print(f"  {k:8s} {str(g):10s} （確認的解析 {want}）  {mark}")
    if hard:
        print("\n  ★ 結果が変わりうる違いがある。既定では取得を始めない。")
        for k, g, w in hard:
            print(f"     {k}: {g} → {w} に合わせること")
        print(f"     pip install 'vitaldb=={REF['vitaldb']}'")
    elif soft:
        print("\n  版の違いはあるが、いずれも結果を変えると分かっているものではない。")
        print("  最後に 41番が確定値の再現を検査するので、そこで判定される。")

    print("\n== 進み具合 ==")
    print(f"  data/cases.csv          {'あり' if pr['cases_csv'] else '無し'}")
    print(f"  data/trks.csv           {'あり' if pr['trks_csv'] else '無し'}")
    print(f"  data/target_cases.csv   {'あり' if pr['target_csv'] else '無し'}")
    print(f"  抽出済みの症例          {pr['n_extracted']} / {N_TARGET} 例")
    if pr["n_extracted"]:
        print(f"                          （残り約 {max(0, N_TARGET - pr['n_extracted'])} 例）")


def step(label: str, cmd: list[str]) -> int:
    print(f"\n{'=' * 74}\n{label}\n  $ {' '.join(cmd)}\n{'=' * 74}", flush=True)
    t0 = time.time()
    rc = subprocess.call(cmd, cwd=str(ROOT))
    dt = time.time() - t0
    print(f"\n  → 終了コード {rc}（{dt / 60:.1f} 分）", flush=True)
    return rc


def run(jobs: int, force: bool) -> int:
    got = versions()
    hard, soft = check_versions(got)
    pr = progress()
    show(got, hard, soft, pr)
    if hard and not force:
        print("\n止めた。版を合わせてからやり直すか、承知のうえなら --force を付ける。")
        return 2

    py = sys.executable
    if not (pr["cases_csv"] and pr["trks_csv"]):
        if step("① VitalDB の症例一覧・トラック一覧を取得（数分）",
                [py, "scripts/00_download_lists.py"]):
            return 1
    else:
        print("\n① 一覧は取得済み。飛ばす")

    if not pr["target_csv"]:
        if step("② 選択基準を満たす症例の一覧を作る（数秒）",
                [py, "scripts/01_track_inventory.py"]):
            return 1
    else:
        print("② 対象症例の一覧は作成済み。飛ばす")

    print(f"\n③ 特徴量の抽出。**ここが数時間かかる。**途中で止めてよい。"
          f"\n   もう一度 --run すれば {FEAT.relative_to(ROOT).as_posix()} の続きから進む。")
    if step("③ 主解析の特徴量を抽出（数時間）",
            [py, "scripts/03_run_analysis.py", "--limit", str(LIMIT), "--jobs", str(jobs)]):
        return 1

    return step("④ 表に入れる値を出す", [py, "scripts/41_fill_tables.py"])


def selftest() -> int:
    ok = True

    def rep(name, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))

    rep("確認的解析の版が原稿・requirements と一致",
        REF["vitaldb"] == "1.5.8" and REF["python"] == "3.9.6" and REF["numpy"] == "2.0.2",
        f"vitaldb {REF['vitaldb']} / python {REF['python']}")
    rep("vitaldb だけを結果が変わる違いとして扱う", CRITICAL == {"vitaldb"})

    h, s = check_versions({"python": "3.9.6", "numpy": "2.0.2", "scipy": "1.13.1",
                           "pandas": "2.3.3", "vitaldb": "1.5.8"})
    rep("すべて一致なら止めない", not h and not s)
    h, s = check_versions({"python": "3.11.0", "numpy": "2.0.2", "scipy": "1.13.1",
                           "pandas": "2.3.3", "vitaldb": "1.5.8"})
    rep("python だけ違うのは警告どまり", not h and len(s) == 1, f"soft={s}")
    h, s = check_versions({"python": "3.9.6", "numpy": "2.0.2", "scipy": "1.13.1",
                           "pandas": "2.3.3", "vitaldb": "1.7.2"})
    rep("vitaldb が違うと止める側に入る", len(h) == 1 and h[0][0] == "vitaldb", f"hard={h}")
    h, s = check_versions({"python": "3.9.6", "numpy": "2.0.2", "scipy": "1.13.1",
                           "pandas": "2.3.3", "vitaldb": None})
    rep("vitaldb 未導入も止める側に入る", len(h) == 1 and h[0][1] == "未導入")

    pr = progress()
    rep("進み具合を数えられる", set(pr) == {"cases_csv", "trks_csv", "target_csv", "n_extracted"})
    rep("抽出済みの数が 0 以上の整数", isinstance(pr["n_extracted"], int) and pr["n_extracted"] >= 0,
        f"{pr['n_extracted']} 例")

    rep("--limit が 874 例を含む余裕を持つ", LIMIT > 874, f"{LIMIT}")
    rep("目標症例数が主解析と同じ 862", N_TARGET == 862)
    for s_ in ("00_download_lists.py", "01_track_inventory.py",
               "03_run_analysis.py", "41_fill_tables.py"):
        rep(f"呼び出す {s_} が実在する", (ROOT / "scripts" / s_).exists())
    import re as _re
    src_imports = _re.findall(r"^\s*(?:from|import)\s+src\b",
                              Path(__file__).read_text(encoding="utf-8"), _re.M)
    rep("この台本は解析の中身に触れない（src を import しない）",
        not src_imports, str(src_imports))

    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--check", action="store_true", help="版と進み具合だけ見る")
    ap.add_argument("--run", action="store_true", help="取得から表の値まで通す")
    ap.add_argument("--jobs", type=int, default=4, help="並列に処理する症例数（既定4）")
    ap.add_argument("--force", action="store_true",
                    help="版が違っても取得を始める（41番の再現検査で判定させる）")
    a = ap.parse_args()

    if a.selftest:
        sys.exit(selftest())
    if a.run:
        sys.exit(run(a.jobs, a.force))
    got = versions()
    h, s = check_versions(got)
    show(got, h, s, progress())
    if not a.check:
        print("\n通すときは --run を付ける。")
    sys.exit(0)


if __name__ == "__main__":
    main()

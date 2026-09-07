#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""走行中の解析の進捗をまとめて表示する。

    python scripts/status.py

稼働中のプロセス、出力ファイル数、直近の処理速度から見積もった残り時間、
各ログの末尾を1画面にまとめる。1日1回これを打てば全体の状況が分かる。
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# (表示名, 出力glob, 総数の目安, プロセス名の一部, ログファイル)
JOBS = [
    ("代替定義抽出",   DATA / "features_variants", "case_*.csv", 862, "11_variants_extract", "variants_run.log"),
    ("早期振幅比抽出", DATA / "features_amb",      "case_*.csv", 862, "35_amb_premise_extract", "amb_run.log"),
    ("動脈圧指標", DATA / "features_art",      "case_*.csv", 862, "15_art_indices",      "art_run.log"),
    ("血管トーヌス", DATA / "vasotone",        "case_*.csv", 232, "16_vasotone",         "vaso_run.log"),
    ("PWDB検証",   DATA / "pwdb",              "*.csv",        1, "20_pwdb_validity",    "pwdb_run.log"),
    ("VitalDB 同定（32番）", DATA / "vitaldb_landmark", "case_*.csv", 20, "32_vitaldb_landmark", None),
    ("C-1 抽出（30番）", DATA / "c1",           "features_case_*.csv", 103, "30_c1_dose_steps", None),
]

# 進捗を JSON に書く解析（表示名, JSON, プロセス名の一部）。26番のような一括 map の解析は出力が出るまで進捗が無い
PROGRESS = [
    ("文献再現（33番）", DATA / "pwdb" / "literature_replica_progress.json", "33_pwdb_literature_replica"),
    ("VitalDB 手法比較（34番）", DATA / "vitaldb_methods" / "progress.json", "34_vitaldb_methods_compare"),
]


def running(pattern: str) -> list[str]:
    try:
        out = subprocess.run(["pgrep", "-fl", pattern], capture_output=True,
                             text=True, timeout=10).stdout
    except Exception:
        return []
    # シェル自身（コマンド行に名前を含む bash・zsh）と status.py 自身は数えない
    skip = {"bash", "sh", "zsh", "-bash", "-zsh", "login"}
    return [l for l in out.splitlines()
            if l.strip() and "caffeinate" not in l and "status.py" not in l
            and (len(l.split()) < 2 or l.split()[1] not in skip)]


def rate_and_eta(files: list[Path], done: int, total: int):
    """直近の処理速度から残り時間を見積もる。再開をまたいでも直近だけを見る。"""
    if done < 3:
        return None, None
    ts = sorted(f.stat().st_mtime for f in files)
    recent = ts[-min(30, len(ts)):]
    span = recent[-1] - recent[0]
    if span <= 0:
        return None, None
    per = span / (len(recent) - 1)              # 1件あたり秒
    left = max(total - done, 0)
    return per, left * per


def fmt_dur(sec: float) -> str:
    if sec < 3600:
        return f"{sec/60:.0f}分"
    if sec < 86400:
        return f"{sec/3600:.1f}時間"
    return f"{sec/86400:.1f}日"


def bar(done: int, total: int, w: int = 24) -> str:
    if total <= 0:
        return ""
    k = min(int(w * done / total), w)
    return "[" + "#" * k + "." * (w - k) + "]"


def main() -> None:
    now = time.time()
    print(f"\n{'='*70}")
    print(f"解析の進捗   {time.strftime('%Y-%m-%d %H:%M', time.localtime(now))}")
    print(f"{'='*70}")

    any_running = False
    for name, d, glob, total, proc, log in JOBS:
        procs = running(f"scripts/{proc}")
        alive = bool(procs)
        any_running |= alive
        files = sorted(d.glob(glob)) if d.exists() else []
        done = len(files)

        state = "稼働中" if alive else ("完了?" if done >= total else "停止")
        print(f"\n■ {name}   {state}")
        if total > 1:
            pct = 100 * done / total
            print(f"   {bar(done, total)} {done:>5} / {total}  ({pct:.1f}%)")
        else:
            print(f"   出力 {done} 件")

        if done:
            last = max(f.stat().st_mtime for f in files)
            age = now - last
            print(f"   最終出力: {fmt_dur(age)}前", end="")
            if alive and age > 1800:
                print("   ← 30分以上更新なし。ログを確認すること", end="")
            print()

        if alive and total > 1:
            per, eta = rate_and_eta(files, done, total)
            if per:
                print(f"   速度: {per/60:.1f}分/例   残り約 {fmt_dur(eta)}"
                      f"（完了予定 {time.strftime('%m/%d %H:%M', time.localtime(now + eta))}）")

        lp = ROOT / log if log else None
        if lp is not None and lp.exists():
            try:
                tail = [l for l in lp.read_text(errors="replace").splitlines()
                        if l.strip() and "NotOpenSSLWarning" not in l and "warnings.warn" not in l]
                if tail:
                    print(f"   ログ: {tail[-1][:82]}")
            except Exception:
                pass
        elif alive and log:
            print(f"   （ログ {log} が見つかりません）")

    for name, jp, proc in PROGRESS:
        procs = running(f"scripts/{proc}")
        alive = bool(procs)
        any_running |= alive
        if not jp.exists():
            if alive:
                print(f"\n■ {name}   稼働中（進捗ファイルはまだ無い。最初の 25 名か 60 秒で書かれる）")
            continue
        try:
            rec = json.loads(jp.read_text(encoding="utf-8"))
        except Exception:
            continue
        done, total = int(rec.get("done", 0)), int(rec.get("total", 0))
        state = "稼働中" if alive else ("完了" if rec.get("state") == "done" else "停止（途中）")
        print(f"\n■ {name}   {state}")
        if total:
            print(f"   {bar(done, total)} {done:>5} / {total}  ({100 * done / max(total, 1):.1f}%)"
                  f"   {rec.get('jobs', '?')} 並列・Wang の刻み {rec.get('wang_step', '?')}")
        age = now - float(rec.get("updated", now))
        per = float(rec.get("per_subject_s", rec.get("per_window_s", 0)))
        unit = "名" if "per_subject_s" in rec else "窓"
        if rec.get("state") == "loading":
            print(f"   症例の読み込み {rec.get('cases_done', '?')} / {rec.get('cases_total', '?')}（窓の当てはめはこの後）")
        print(f"   最終更新: {fmt_dur(age)}前   経過 {fmt_dur(float(rec.get('elapsed_s', 0)))}"
              f"   {per:.1f} 秒/{unit}", end="")
        if alive and rec.get("state") != "done":
            eta = float(rec.get("eta_s", 0))
            print(f"   残り約 {fmt_dur(eta)}（完了予定 {time.strftime('%m/%d %H:%M', time.localtime(now + eta))}）", end="")
        print()
        fin = rec.get("finite_dt", {})
        if fin and done:
            print("   ΔT が出た割合: " + "・".join(f"{k} {v / done:.0%}" for k, v in fin.items()) + f"   例外 {rec.get('errors', 0)}")
        if alive and age > 900:
            print("   ← 15 分以上更新なし。プロセスの CPU を確認すること（top）")

    print(f"\n{'-'*70}")
    if not any_running:
        print("稼働中のプロセスはありません。")
    print("次にやること: docs/research/checklist_timeline.md")
    print()


if __name__ == "__main__":
    main()

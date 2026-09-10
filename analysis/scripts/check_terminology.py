#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用語の決まり（docs/research/terminology.md）を機械で確かめる。

なぜ要るか
----------
`terminology.md` は 2026-09-07 に制定されているが、**文書に書いただけでは守られなかった。**
2026-09-09 の作業で「錨」を再び使った。同じ表に禁止と明記されている語である。
人が覚えていることを前提にした規則は破られるので、機械が落とすようにする。

決まりの本体
------------
1. **造語をしない。**文献にある用語をそのまま使う。訳語が定まっていないものは原語を併記する。
2. **比喩で説明しない。**読み手が原論文に戻れなくなる。
3. **医学・生理の内容は、原文の語か、広く受け入れられている訳語で書く。**

使い方
------
    既定の対象を検査する
        python3 scripts/check_terminology.py
    歴史的文書も含めて一覧する
        python3 scripts/check_terminology.py --all
    対象を指定する
        python3 scripts/check_terminology.py path ...

終了コード 0 = 禁止語なし、1 = 禁止語あり。
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# 規則の制定日。lab_log.md はこれ以降の追記だけを検査する
# （制定前の追記は当時の記録であり、書き換えない）。
RULE_DATE = date(2026, 9, 7)

# 行末にこれを置いた行は検査しない。禁止語を**引用している**行のための印である
# （「『錨』は使わない」のような文。使用ではなく言及なので機械には区別できない）。
# markdown では表示されず、python では通常のコメントになる。
PRAGMA = "用語の引用"

# 検査しない文書（規則制定より前に書かれた読み物。歴史的記録として残す）
SKIP = {
    "PPG_reflection_wave_localisation.md",
    "PPG_reflection_wave_localisation.html",
    "iliac_reflection_identifiability.md",
    "docs/research/terminology.md",          # 言い換え表そのもの
    "CLAUDE.md",                             # 決まりを書いた文書（禁止語を引用する）
    "analysis/scripts/check_terminology.py",  # このファイル
}

# 禁止語。(語, 言い換え, 許される文脈の正規表現)
BANNED = [
    ("錨",       "基準点／照合先（何を指すのか具体に書く）", None),
    ("鍵点",     "特徴点（fiducial point）", None),
    ("土俵",     "データセット／条件", None),
    ("配管",     "解析の流れ／処理系", None),
    ("天井",     "上限／到達しうる最大値", r"天井効果"),
    ("化ける",   "別の量になる／〜の解釈に変わる", None),
    ("足切り",   "除外基準／不成立と判定する条件", None),
    ("予行",     "予備的検討／同じ手順を先に試すこと", None),
    ("売り文句", "主張されている利点", None),
    ("ふらつき", "症例内変動（何を測った量か書く）", None),
    ("窓",       "ウィンドウ（解析ウィンドウ）",
                 r"窓関数|窓口|ウィンドウ|Kaiser\s*窓|ハミング窓|ハニング窓|ハン窓|方形窓"),
    ("帯域",     "説明できる分散の大きさ（比喩で書かない）",
                 r"帯域制限|帯域幅|通過帯域|阻止帯域|帯域特性|帯域無制限"),
    ("桁が足りない", "効果量が事前に定めた最小効果量に達しない（具体に書く）", None),
    ("路線が閉じ",   "事前規準に照らして無益性と判定した", None),
    ("判定が閉じ",   "事前規準に照らして無益性と判定した", None),
    ("路線が終了",   "〜は中止する／〜を主指標には用いない", None),
    # terminology.md の表にありながら実装が漏れていた 2 件（2026-09-09 の 4 巡目で気づいた）
    # カタカナ語に ASCII の除外規則は効かない（識別子は ASCII なので衝突しない）
    ("ランドマーク", "特徴点（fiducial point）／特徴点法", None),
    # 英文側。散文の landmark だけを見る。コード内の識別子（find_landmarks・
    # no_landmarks・dt_lm_ms）と逆引用符で囲んだ部分は除く
    ("landmark",   "fiducial point / fiducial-point analysis",
                   r"`[^`]*`|[A-Za-z_.]landmark|landmark[A-Za-z_]|\"landmark\"|'landmark'"),
    ("指標が届",     "相関の大きさが〜に及ばない／〜を説明できない", None),
    ("指標はいずれも届", "相関の大きさが〜に及ばない／〜を説明できない", None),
]

# 要注意語。落とさないが一覧に出す（文脈しだいで正しいことがある）
WARN = [
    ("肩",   "変曲点（下降脚の変曲点）", r"肩書|肩代わり"),
    ("変種", "指標の定義を変えた版／代替定義", None),
    ("病的", "偏った／条件を満たさない（データの説明に病理の語を使わない）",
             r"病的肥満|病的骨折|病的反射"),
]

DEFAULT_TARGETS = ["docs", "analysis/scripts", "analysis/src", "analysis/README.md", "README.md", "tools"]
SUFFIX = {".md", ".py", ".html", ".txt"}

# 既知の残件を記録しておき、**増えたときだけ落とす。**
# 規則の制定（2026-09-07）より前に書かれた文書には残っている。それを一度に直すと
# 差分が読めなくなるので、件数を固定して「これ以上増やさない」ことを守る。
# 直したら `--update-baseline` で記録しなおす。
BASELINE = ROOT / "docs" / "research" / "terminology_baseline.json"

# ここは残件を許さない。投稿する文章そのものだから。
STRICT = ("docs/manuscript/",)


def lab_log_cutoff(path: Path, text: str) -> int:
    """lab_log.md で、規則制定日以降の追記が始まる行番号を返す（1 始まり）。"""
    if path.name != "lab_log.md":
        return 1
    pat = re.compile(r"^##\s*(\d{4})-(\d{2})-(\d{2})")
    for i, ln in enumerate(text.splitlines(), 1):
        m = pat.match(ln)
        if m and date(*(int(g) for g in m.groups())) >= RULE_DATE:
            return i
    return len(text.splitlines()) + 1


def scan(path: Path, check_all: bool) -> tuple[list, list]:
    rel = path.relative_to(ROOT).as_posix()
    if not check_all and rel in SKIP:
        return [], []
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return [], []
    start = 1 if check_all else lab_log_cutoff(path, text)
    bad, warn = [], []
    for no, ln in enumerate(text.splitlines(), 1):
        if no < start or PRAGMA in ln:
            # 禁止語そのものを引用する行（規則の説明・訂正の記録）は除く。
            # 使用ではなく言及なので、機械には区別できない。行末に印を置く。
            continue
        for table, sink in ((BANNED, bad), (WARN, warn)):
            for term, alt, allow in table:
                if term not in ln:
                    continue
                if allow and re.sub(allow, "", ln).find(term) < 0:
                    continue
                sink.append((rel, no, term, alt, ln.strip()[:90]))
    return bad, warn


def load_baseline() -> dict:
    import json
    if not BASELINE.exists():
        return {}
    return json.loads(BASELINE.read_text(encoding="utf-8"))


def main() -> int:
    import json
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="*", default=None)
    ap.add_argument("--all", action="store_true", help="歴史的文書も含めて検査する")
    ap.add_argument("--quiet", action="store_true", help="件数だけ出す")
    ap.add_argument("--list", action="store_true", help="残件を既定値と比べずに全部出す")
    ap.add_argument("--update-baseline", action="store_true",
                    help="残件の記録を今の状態に書きなおす（直したあとに実行する）")
    a = ap.parse_args()

    files: list[Path] = []
    for t in (a.targets or DEFAULT_TARGETS):
        p = (ROOT / t) if not Path(t).is_absolute() else Path(t)
        if p.is_dir():
            files += [q for q in sorted(p.rglob("*")) if q.suffix in SUFFIX]
        elif p.is_file():
            files.append(p)
    bad, warn = [], []
    for f in files:
        b, w = scan(f, a.all)
        bad += b
        warn += w

    now: dict[str, int] = {}
    for rel, *_ in bad:
        now[rel] = now.get(rel, 0) + 1

    if a.update_baseline:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(dict(sorted(now.items())), ensure_ascii=False, indent=2)
                            + "\n", encoding="utf-8")
        print(f"残件の記録を更新した: {BASELINE.relative_to(ROOT)}（{sum(now.values())} 件）")
        return 0

    base = load_baseline()
    # 増えたファイルだけを落とす。投稿原稿（STRICT）は残件を認めない。
    over = {f: (n, base.get(f, 0)) for f, n in now.items()
            if n > base.get(f, 0) or f.startswith(STRICT)}
    shown = bad if (a.list or not base) else [r for r in bad if r[0] in over]

    if not a.quiet:
        for label, rows in (("禁止", shown), ("要注意", warn if a.list else [])):
            if not rows:
                continue
            print(f"\n【{label}】{len(rows)} 件")
            for rel, no, term, alt, ln in rows:
                print(f"  {rel}:{no}  「{term}」→ {alt}")
                print(f"      {ln}")
    print(f"\n検査 {len(files)} ファイル・禁止 {sum(now.values())} 件"
          f"（記録済みの残件 {sum(base.values())} 件）・要注意 {len(warn)} 件")
    if over:
        print("\n★ 増えた、または投稿原稿に残っている:")
        for f, (n, b) in sorted(over.items()):
            print(f"  {f}: {n} 件（記録は {b} 件）")
        print("\n造語と比喩を使わない（docs/research/terminology.md）。文献の語か定訳で書くこと。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

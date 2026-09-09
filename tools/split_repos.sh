#!/usr/bin/env bash
# リポジトリを 3 つに分ける。**実行前に必ず本文（tools/README_split.md）を読むこと。**
#
#   1) nobumitsu-3141/ppg-study          … 公開のまま。main は文献レビューのハブだけで機微な資料は無い
#   2) <公開・新規>  ppg-pda-analysis    … 解析コードと凍結した事前登録。Zenodo DOI はこれに付ける
#   3) <非公開・新規> ppg-study-private  … 原稿・実験ノート・倫理文書・依頼書・報告書
#
# **機微な資料は作業ブランチ claude/slide-references-formatting-ynthk7 にしか無い。**
# main には入っていない（2026-09-09 に GitHub API で確認）。したがって履歴の書き換えは要らず、
# 2) と 3) を作ったうえで**作業ブランチをリモートから消す**のが最小の手当てになる。
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$SRC/../ppg-split}"
mkdir -p "$OUT"

# ── 2) 公開する解析リポジトリ（履歴は作り直す。過去の版に機微な資料が入っているため）
PUB="$OUT/ppg-pda-analysis"
rm -rf "$PUB"; mkdir -p "$PUB/analysis" "$PUB/preregistration"
cp -R "$SRC/analysis/src"     "$PUB/analysis/"
cp -R "$SRC/analysis/scripts" "$PUB/analysis/"
cp    "$SRC/analysis/README.md" "$PUB/analysis/" 2>/dev/null || true
cp    "$SRC/analysis/.gitignore" "$PUB/analysis/" 2>/dev/null || true
rm -rf "$PUB/analysis/scripts/__pycache__" "$PUB/analysis/src/__pycache__"
# 論文が引く事前登録と判定規準だけを入れる（実験ノート・原稿は入れない）
for f in sap_v0.md sap_1_amb_exploratory_v0.md sap_1c_v0.md sap_1d_v0.md \
         gate0_rules_v2.md terminology.md; do
  cp "$SRC/docs/research/$f" "$PUB/preregistration/" 2>/dev/null || true
done
cp "$SRC/LICENSE" "$PUB/"
cp "$SRC/setup_mac.sh" "$PUB/" 2>/dev/null || true
cp "$SRC/tools/public_README.md"   "$PUB/README.md"
cp "$SRC/tools/public_CITATION.cff" "$PUB/CITATION.cff"
cp "$SRC/tools/public_zenodo.json" "$PUB/.zenodo.json"

# ── 3) 非公開のリポジトリ
PRI="$OUT/ppg-study-private"
rm -rf "$PRI"; mkdir -p "$PRI"
cp -R "$SRC/docs" "$PRI/"
cp    "$SRC/CLAUDE.md" "$PRI/" 2>/dev/null || true
cp -R "$SRC/slides" "$PRI/" 2>/dev/null || true
cp -R "$SRC/local-reviews" "$PRI/" 2>/dev/null || true

echo "作成した:"
echo "  公開   $PUB          （$(find "$PUB" -type f | wc -l | tr -d ' ') ファイル）"
echo "  非公開 $PRI          （$(find "$PRI" -type f | wc -l | tr -d ' ') ファイル）"
echo ""
echo "**公開する側に機微な語が残っていないかを検査する**"
if grep -rl "一ノ宮\|大雅\|五島中央\|長崎大学" "$PUB" 2>/dev/null; then
  echo "  ★ 上のファイルに実名・施設名が残っている。公開前に必ず消すこと。"; exit 1
else
  echo "  実名・施設名の検出なし"
fi

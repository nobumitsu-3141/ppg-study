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
SRC_SHA="$(git -C "$SRC" rev-parse --short HEAD 2>/dev/null || echo unknown)"

# 作業木だけ入れ替え、.git は残す。**初回だけ git init する。**
# 毎回 init し直すと走らせるたびに無関係な根コミットができ、リリースのタグが
# 枝から切り離される（2026-09-09 に v1.0.0 で実際に起きた）。
reset_worktree() {
  local d="$1" stash
  if [ -d "$d/.git" ]; then
    stash="$(mktemp -d)"
    mv "$d/.git" "$stash/.git"
    rm -rf "$d"; mkdir -p "$d"
    mv "$stash/.git" "$d/.git"; rmdir "$stash"
  else
    rm -rf "$d"; mkdir -p "$d"
    git -C "$d" init -q -b main
  fi
}

# 内容が変わっていれば commit する。変わっていなければ何もしない。
commit_if_changed() {
  local d="$1" msg
  git -C "$d" add -A
  if git -C "$d" diff --cached --quiet 2>/dev/null; then
    echo "  変更なし: $(basename "$d")"
    return 0
  fi
  if git -C "$d" rev-parse --verify -q HEAD >/dev/null; then
    msg="$SRC_SHA から同期"
  else
    msg="初回: $(basename "$d")"
  fi
  git -C "$d" \
      -c user.name="$(git -C "$SRC" config user.name 2>/dev/null || echo nobumitsu-3141)" \
      -c user.email="$(git -C "$SRC" config user.email 2>/dev/null || echo noreply@example.com)" \
      commit -q -m "$msg"
}

# ── 2) 公開する解析リポジトリ
PUB="$OUT/ppg-pda-analysis"
reset_worktree "$PUB"
mkdir -p "$PUB/analysis" "$PUB/preregistration"
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
cp "$SRC/tools/public_LICENSE" "$PUB/LICENSE"
cp "$SRC/LICENSE"              "$PUB/LICENSE-docs"
cp "$SRC/setup_mac.sh" "$PUB/" 2>/dev/null || true
cp "$SRC/tools/public_README.md"   "$PUB/README.md"
cp "$SRC/tools/public_CITATION.cff" "$PUB/CITATION.cff"
cp "$SRC/tools/public_zenodo.json" "$PUB/.zenodo.json"

# ── 3) 非公開のリポジトリ
PRI="$OUT/ppg-study-private"
reset_worktree "$PRI"
cp -R "$SRC/docs" "$PRI/"
cp    "$SRC/CLAUDE.md" "$PRI/" 2>/dev/null || true
cp -R "$SRC/slides" "$PRI/" 2>/dev/null || true
cp -R "$SRC/local-reviews" "$PRI/" 2>/dev/null || true

commit_if_changed "$PUB"
commit_if_changed "$PRI"

echo "作成した:"
echo "  公開   $PUB   （$(git -C "$PUB" ls-files | wc -l | tr -d ' ') ファイル）"
echo "  非公開 $PRI （$(git -C "$PRI" ls-files | wc -l | tr -d ' ') ファイル）"
echo ""
echo "**公開する側に機微な語が残っていないかを検査する**"
if grep -rl "一ノ宮\|大雅\|五島中央\|長崎大学" "$PUB" --exclude-dir=.git 2>/dev/null; then
  echo "  ★ 上のファイルに実名・施設名が残っている。公開前に必ず消すこと。"; exit 1
else
  echo "  実名・施設名の検出なし"
fi
echo ""
if git -C "$PUB" remote get-url origin >/dev/null 2>&1; then
  echo "次にやること"
  echo "  cd $PUB"
  echo "  git push origin main"
  echo ""
  echo "  cd $PRI"
  echo "  git push origin main"
  echo ""
  echo "履歴は積み上がるので --force は要らない。拒否されたら、遠隔に手を入れた"
  echo "覚えがないか確かめること。**黙って --force を足さない。**"
else
  echo "次にやること（**この 2 つのディレクトリの中で**実行する。元のリポジトリでは実行しない）"
  echo "  1. GitHub で空のリポジトリを 2 つ作る。README・.gitignore・ライセンスは追加しない"
  echo "       ppg-pda-analysis   … 公開"
  echo "       ppg-study-private  … 非公開"
  echo "  2. 下を順に実行する。git remote -v が何も出さないことを先に確かめる"
  echo "     （何か出たら場所が違うので、そのまま続けない）"
  echo "     cd $PUB"
  echo "     git remote -v"
  echo "     git remote add origin https://github.com/nobumitsu-3141/ppg-pda-analysis.git"
  echo "     git push -u origin main"
  echo "  3. cd $PRI"
  echo "     git remote -v"
  echo "     git remote add origin https://github.com/nobumitsu-3141/ppg-study-private.git"
  echo "     git push -u origin main"
  echo ""
  echo "  SSH 鍵を使っている場合は https://github.com/ を git@github.com: に置き換える"
fi

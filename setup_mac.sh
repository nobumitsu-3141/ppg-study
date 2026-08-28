#!/bin/bash
# PPG研究 解析環境の Mac セットアップ（初回・再構築とも同じコマンドでよい）
#   bash setup_mac.sh
# このスクリプトはリポジトリ内にあるので、初回だけは README の
# 「初回セットアップ」のコピペブロックを使うこと。
set -u
cd "$(dirname "$0")"
BRANCH=claude/slide-references-formatting-ynthk7

echo "=== 1. 最新を取得 ==="
git fetch origin "$BRANCH" && git checkout "$BRANCH" && git pull origin "$BRANCH" || {
  echo "git の取得に失敗しました。ネットワークとリポジトリの状態を確認してください。"; exit 1; }

echo "=== 2. Python を選択 ==="
# 実際に実行して 3.9 以上か確かめる。[-x] だけだと、Xcode CLT 未導入時の
# /usr/bin/python3（インストールを促すだけのスタブ）を通してしまう。
PY=""
for c in /opt/homebrew/bin/python3 /usr/local/bin/python3 "$(command -v python3 || true)"; do
  [ -n "$c" ] && [ -x "$c" ] || continue
  if "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
[ -z "$PY" ] && {
  echo "python3（3.9以上）が見つかりません。"
  echo "  新しいMacで初回なら、先に  xcode-select --install  を実行して完了を待つ。"
  echo "  それでも駄目なら https://www.python.org/downloads/ のインストーラで導入して再実行。"
  exit 1; }
echo "使用: $PY ($("$PY" --version 2>&1))"

echo "=== 3. 仮想環境と依存ライブラリ ==="
cd analysis || exit 1
[ -d .venv ] || "$PY" -m venv .venv
source .venv/bin/activate
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt || { echo "依存の導入に失敗しました。"; exit 1; }
python - <<'PYEOF' || { echo "ライブラリの読み込みに失敗しました。上のエラーを確認してください。"; exit 1; }
import numpy, scipy, pandas, vitaldb
print(f"  numpy {numpy.__version__} / scipy {scipy.__version__} / "
      f"pandas {pandas.__version__} / vitaldb {getattr(vitaldb, '__version__', '?')}")
PYEOF

echo
echo "=== 準備完了 ==="
echo "次回からこのウィンドウで作業するには:"
echo "  cd $(pwd) && source .venv/bin/activate"
echo
echo "VitalDB の取得と集計を続けて実行するには:"
echo "  python scripts/00_download_lists.py && python scripts/01_track_inventory.py"

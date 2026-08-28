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
PY=""
for c in /opt/homebrew/bin/python3 /usr/local/bin/python3 "$(command -v python3 || true)"; do
  [ -x "$c" ] && PY="$c" && break
done
[ -z "$PY" ] && { echo "python3 が見つかりません。"; exit 1; }
echo "使用: $PY ($("$PY" --version 2>&1))"

echo "=== 3. 仮想環境と依存ライブラリ ==="
cd analysis
[ -d .venv ] || "$PY" -m venv .venv
source .venv/bin/activate
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt || { echo "依存の導入に失敗しました。"; exit 1; }
python - <<'PYEOF'
import numpy, scipy, pandas, vitaldb
print(f"  numpy {numpy.__version__} / scipy {scipy.__version__} / "
      f"pandas {pandas.__version__} / vitaldb {vitaldb.__version__}")
PYEOF

echo
echo "=== 準備完了 ==="
echo "次回からこのウィンドウで作業するには:"
echo "  cd $(pwd) && source .venv/bin/activate"
echo
echo "VitalDB の取得と集計を続けて実行するには:"
echo "  python scripts/00_download_lists.py && python scripts/01_track_inventory.py"

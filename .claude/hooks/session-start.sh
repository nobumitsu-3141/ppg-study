#!/bin/bash
# SessionStart フック: Web(claude.ai)の Claude Code セッションで slidegen(川副式スライド
# 組版機構)の依存を自動整備する。これにより新規セッション・他Macの Web セッションでも
# clone 直後に「編集 → build → lint」が動く。
#
# ローカル Mac では各自の venv/uv 環境を使うため、このフックは何もしない。
set -euo pipefail

# Web(リモート)環境以外では何もしない。
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

SETUP="${CLAUDE_PROJECT_DIR:-.}/slidegen/setup-linux.sh"
if [ -f "$SETUP" ]; then
  bash "$SETUP"
else
  echo "slidegen/setup-linux.sh が見つからないためスキップ" >&2
fi

#!/usr/bin/env bash
# Linux(claude.ai の Claude Code 等)で slidegen を動かすための初期化。冪等。
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "[1/4] Python 依存"
python3 -m pip install --quiet --break-system-packages -r "$HERE/requirements.txt" 2>/dev/null \
  || python3 -m pip install --quiet -r "$HERE/requirements.txt"

echo "[2/4] Meiryo → Noto Sans CJK JP の対応づけ"
mkdir -p "$HOME/.config/fontconfig"
cp "$HERE/fontconfig/meiryo-alias.conf" "$HOME/.config/fontconfig/fonts.conf"
fc-cache -f >/dev/null 2>&1 || true
m="$(fc-match Meiryo 2>/dev/null || echo '?')"
case "$m" in
  *"CJK JP"*) echo "      OK: $m" ;;
  *) echo "      ⚠ 未解決: $m  (fonts-noto-cjk が未導入の可能性)" ;;
esac

echo "[3/4] 出力先ディレクトリ"
# out/ は .gitignore で除外しているため、クローン直後は存在しない。
# build スクリプトは ../out/*.pptx へ直接書くので、無いと FileNotFoundError になる。
for d in "$HERE"/decks/*/; do
  mkdir -p "$d/out" "$d/figs"
done
echo "      OK: decks/*/out, decks/*/figs を作成"

echo "[4/4] 目視確認用 LibreOffice"
command -v soffice >/dev/null 2>&1 && echo "      OK: $(soffice --version 2>/dev/null | head -1)" \
                                   || echo "      ⚠ soffice なし。pptx→PNG の目視確認は不可"
echo "完了。build 手順は README 第3節。"

#!/usr/bin/env bash
# 別の Mac で解析を継続するための立ち上げ。何度実行してもよい（既存物は壊さない）。
#
#   bash analysis/scripts/setup_new_mac.sh
#   bash analysis/scripts/setup_new_mac.sh --skip-lists   # VitalDB の一覧取得を省く
#   bash analysis/scripts/setup_new_mac.sh --skip-tests   # 自己検査を省く
#
# やること
#   1. python3 と仮想環境を用意し、requirements.txt を入れる
#   2. VitalDB の症例・トラック一覧を取得する（再生成できるので複製しない）
#   3. **複製が要るデータ**の有無を数え、足りなければ rsync のコマンドを表示する
#   4. 自己検査を回して、この端末で同じ結果が出ることを確かめる
#
# このスクリプトはデータを削除しない。上書きもしない。

set -uo pipefail

SKIP_LISTS=0
SKIP_TESTS=0
for a in "$@"; do
  case "$a" in
    --skip-lists) SKIP_LISTS=1 ;;
    --skip-tests) SKIP_TESTS=1 ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    *) echo "不明な引数: $a"; exit 2 ;;
  esac
done

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # analysis/
DATA="$HERE/data"
VENV="$HERE/.venv"
ok=1
say() { printf '%s\n' "$*"; }
hdr() { printf '\n\033[1m%s\033[0m\n%s\n' "$1" "----------------------------------------------------------------------"; }
bad() { ok=0; printf '  [要対応] %s\n' "$*"; }

hdr "1. 実行環境"
if ! command -v python3 >/dev/null 2>&1; then
  bad "python3 がありません。Xcode Command Line Tools を入れてください: xcode-select --install"
else
  say "  python3: $(python3 --version 2>&1) ($(command -v python3))"
fi
if [ ! -d "$VENV" ]; then
  say "  仮想環境を作ります: $VENV"
  python3 -m venv "$VENV" || bad "仮想環境を作れませんでした"
fi
if [ -x "$VENV/bin/python" ]; then
  PY="$VENV/bin/python"
  say "  依存を導入します（既に入っていれば数秒）"
  "$VENV/bin/pip" install -q --upgrade pip >/dev/null 2>&1
  if "$VENV/bin/pip" install -q -r "$HERE/requirements.txt"; then
    say "  導入済み: $("$PY" -c 'import numpy,scipy,pandas;print("numpy",numpy.__version__,"scipy",scipy.__version__,"pandas",pandas.__version__)' 2>&1)"
    "$PY" -c 'import vitaldb' 2>/dev/null && say "  vitaldb: あり" || bad "vitaldb を読み込めません"
  else
    bad "requirements.txt の導入に失敗しました"
  fi
else
  PY="python3"
  bad "仮想環境の python が見つかりません"
fi

hdr "2. 再生成できるデータ（複製しない）"
mkdir -p "$DATA"
if [ "$SKIP_LISTS" = "1" ]; then
  say "  --skip-lists のため省略"
elif [ -s "$DATA/cases.csv" ] && [ -s "$DATA/trks.csv" ] && [ -s "$DATA/target_cases.csv" ]; then
  say "  症例・トラック一覧はすでにあります（再取得しません）"
else
  say "  VitalDB から一覧を取得します（数分・ネットワークが要ります）"
  ( cd "$HERE" && "$PY" scripts/00_download_lists.py && "$PY" scripts/01_track_inventory.py ) \
    || bad "一覧の取得に失敗しました。ネットワークを確認して再実行してください"
fi
for f in cases.csv trks.csv target_cases.csv; do
  [ -s "$DATA/$f" ] && say "  $f: $(wc -l < "$DATA/$f" | tr -d ' ') 行" || bad "$f がありません"
done

hdr "3. 複製が要るデータ（再計算に数日かかる）"
say "  これらは公開リポジトリに置けないので git では運べません。"
say "  元の Mac から直接コピーしてください（下にコマンドを出します）。"
printf '\n  %-24s %8s  %s\n' "ディレクトリ" "ファイル数" "状態"
need_copy=()
check_dir() {   # 名前 期待数 説明
  local d="$1" want="$2" note="$3" n=0
  [ -d "$DATA/$d" ] && n=$(ls -1 "$DATA/$d" 2>/dev/null | wc -l | tr -d ' ')
  local st="不足"
  if [ "$n" -ge "$want" ]; then st="そろっている"; else need_copy+=("$d"); fi
  printf '  %-24s %8s  %s（目安 %s／%s）\n' "$d" "$n" "$st" "$want" "$note"
}
check_dir features          1724 "主解析の特徴量・862例×2ファイル" 
check_dir features_variants 1724 "変種抽出・862例×2ファイル"
check_dir features_art       862 "動脈圧指標"
check_dir vasotone           232 "SVR・昇圧薬"

hdr "4. PWDB（研究0・再ダウンロードできる）"
if [ -d "$HOME/pwdb" ] && [ -n "$(ls -A "$HOME/pwdb" 2>/dev/null)" ]; then
  say "  ~/pwdb: あり（$(du -sh "$HOME/pwdb" 2>/dev/null | cut -f1)）"
else
  say "  ~/pwdb: なし。Zenodo doi:10.5281/zenodo.3275625 から次の6つを ~/pwdb/ に置く"
  say "    pwdb_haemod_params.csv / pwdb_model_configs.csv / pwdb_model_variations.csv"
  say "    pwdb_onset_times.csv / pwdb_pw_indices.csv / PWs_csv.zip（展開不要・計265MB）"
fi

if [ "$SKIP_TESTS" != "1" ]; then
  hdr "5. 自己検査（この端末で同じ結果が出るか）"
  for t in 20_pwdb_validity 23_pwdb_landmarks 21_pwtt_decomposition 16_vasotone 15_art_indices; do
    printf '  %-24s ' "$t"
    if ( cd "$HERE" && "$PY" "scripts/$t.py" --selftest >/tmp/st_$t.log 2>&1 ); then
      echo "PASS"
    else
      echo "FAIL（/tmp/st_$t.log を見てください）"; ok=0
    fi
  done
  printf '  %-24s ' "12_variants_stats"
  if ( cd "$HERE" && "$PY" scripts/12_variants_stats.py --selftest >/tmp/st_12.log 2>&1 ); then echo "PASS"; else echo "FAIL（/tmp/st_12.log）"; ok=0; fi
fi

hdr "まとめ"
if [ "${#need_copy[@]}" -gt 0 ]; then
  say "  次のデータを元の Mac からコピーしてください。"
  say "  元の Mac で（この端末の名前は「システム設定 → 一般 → 情報」で確認できます）:"
  say ""
  for d in "${need_copy[@]}"; do
    say "    rsync -av --progress ~/ppg-study/analysis/data/$d/ \\"
    say "      <このMacのユーザ名>@<このMacの名前>.local:~/ppg-study/analysis/data/$d/"
  done
  say ""
  say "  同じ LAN にない場合は、外付けドライブか AirDrop でフォルダごと運んでください。"
  say "  合計は 200 MB 程度です（数日かけて計算した結果ですが、容量は小さい）。"
  say "  **公開リポジトリ・共有クラウドには置かないこと**（docs/research/data_management_v0.md）。"
else
  say "  データはそろっています。"
fi
say ""
say "  次にやること: analysis/ で"
say "    $VENV/bin/python scripts/status.py"
say "    詳しくは docs/research/setup_new_machine.md と docs/research/checklist_timeline.md"
[ "$ok" = "1" ] && { say ""; say "  立ち上げは完了しました。"; exit 0; } || { say ""; say "  上の [要対応] を片付けてから再実行してください。"; exit 1; }

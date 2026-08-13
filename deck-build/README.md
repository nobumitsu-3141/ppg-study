# deck-build ― SpO2/PPG 波形解析デック v6.6 → v6.7 の改訂スクリプト

v6.6 の `.pptx` を入力に、python-pptx で改訂版 v6.7 を組み立てる一連のスクリプト。
元デックの版面（メイリオ・44/46pt 金色タイトル・章ナビ・出典 10.5pt）を複製して
新ページを作るので、**川副式の書式は自動的に引き継がれる**。

## 実行順

```bash
pip install python-pptx lxml
cp <v6.6 の pptx> deck_v66.pptx

python3 stage1.py    # 出典書式の統一・目次修正・誤記修正      → deck_s1.pptx
python3 stage2a.py   # 2 / 20 / 49 / 60 の改訂ページを挿入     → deck_s2a.pptx
python3 stage2b.py   # 61 / 62 の改訂＋6章（解析まとめ）新設   → deck_s2b.pptx
python3 stage2c.py   # 66 / 67 の改訂（DN-less）               → deck_s2c.pptx
python3 stage2d.py   # 7.2 PDA 解説＋重要文献 9 枚を挿入       → deck_s2d.pptx
python3 stage3.py    # 参考文献ページ再構成・ページ番号再採番  → deck_v67.pptx
python3 fixup.py deck_v67.pptx deck_v67f.pptx   # 版面の自動微調整
```

## 各ファイルの役割

| ファイル | 役割 |
|---|---|
| `deckkit.py` | スライド複製・タイトル/章ナビ/出典/ページ番号の設定・図形と波形の描画 |
| `newpages.py` | 新規ページの共通土台（`Builder`）と PPG 波形ジェネレータ |
| `refs.py` | 参考文献レジストリ（1–52）と出典文字列の組み立て |
| `stage1helpers.py` | 章立て（目次）の定義と、章扉・メニューの本文差し替え |
| `stage1.py` 〜 `stage3.py` | 上表のとおり |
| `fixup.py` | 新規ページのテキストボックス高さを推定描画高さに合わせ、折返しを報告 |

## 設計上の約束

- **既存ページは消さない。** 改訂版は元ページの**直後**に挿入する。
- 参考文献の番号 1–29 は v6.6 のまま据え置き、追加分を 30 以降に採番する。
  そのため既存ページの引用番号を書き換える必要がない。
- ページ番号は「同じタイトルが連続するビルドアップ群＝1 論理ページ」として
  可視スライドのみに採番する（非表示スライドには付けない）。

## 検証

```bash
python3 <pptx skill>/scripts/office/validate.py deck_v67f.pptx --original deck_v66.pptx
python3 <slide-format skill>/scripts/slide_lint.py deck_v67f.pptx
```

実寸の目視確認は本番の PowerPoint（メイリオ）で行うこと。

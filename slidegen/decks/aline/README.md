# 観血的動脈圧測定 スライド（濃紺×ゴールド / Meiryo）

- `../観血的動脈圧測定.pptx` … 完成品（PowerPointで直接編集可）
- 再生成: 図版 `python dz.py` → 組版 `python build.py`（python-pptx / matplotlib / Pillow が必要）
- `aline_content.json` … 医学本文・出典（Opus執筆）。文言修正はここを編集して build.py を再実行
- `aline_structure_brief.md` … 構成設計書（章立て・各スライドの図仕様）
- 波形図は matplotlib 生成の PNG（figs/）。PowerPoint上では画像なので、形を変える場合は dz.py を編集して再生成

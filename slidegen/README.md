# slidegen — 川副式スライド組版機構

麻酔科レクチャー用 PowerPoint デックを、テキストのソース（`content/`）と図（`figs/`）から
機械的に組み立てるための一式である。Mac ローカルに散在していた機構を、他の Mac や
Web 上の Claude Code からも「編集 → build → lint」を回せるよう共有リポジトリへ移した。

用語: **lint（リント）** はここでは「組版ルールに対する静的検査」を指す。
**pptx** は Office Open XML 形式の PowerPoint ファイル、
**PPG（photoplethysmography：光電容積脈波）**、
**SpO₂（peripheral oxygen saturation：経皮的動脈血酸素飽和度）** である。

---

## 1. 中身

```
slidegen/
├── README.md                    … 本ファイル
├── requirements.txt             … Python 依存（版付き）
├── .gitignore                   … 大容量バイナリの除外規則
├── lib/
│   ├── decklib.py               … 川副式ビルダー本体（正典 = defib 版）
│   └── slide_lint.py            … 組版ルールの機械検査
├── template/
│   └── _template_kawazoe.pptx   … 川副式テンプレート（81 KB・全デック共通）
├── docs/
│   ├── 川副式スライド書式ルール.md  … 書式ルール（slide-format スキル本体）
│   └── decklib-forks.md         … decklib が 4 分岐している件の記録
└── decks/
    ├── defib/                   … 除細動器（8 章 71 枚）
    ├── etco2/                   … EtCO₂ / カプノグラフィ（8 章 60 枚）
    ├── aline/                   … 観血的動脈圧 A-line（38 枚）
    ├── monitor-ecg/             … モニター心電図（8 章 66 枚）
    └── nibp/                    … 非観血的血圧 NIBP（※ 第 8 節の既知の問題を参照）
```

各デックは**自己完結**である。`scripts/` に自分用の `decklib.py` と
`_template_kawazoe.pptx` を同梱しており、クローン直後にそのままビルドできる。

`_template_kawazoe.pptx` は 4 デックすべてで**バイト単位で同一**
（md5 `362e257195cfa32ffb1ecc83bf533ffc`）。
`スライド作成ルール.md` も 5 デックすべてで同一（md5 `6e48e5ba57d3ed4b82cb3574f3c43656`）。

---

## 2. 依存とセットアップ

**基準環境は CPython 3.12**（Mac ローカルの uv 仮想環境）。
Linux / CPython 3.10 でもビルド成功を確認済みである。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` の実体は `python-pptx` / `Pillow` / `matplotlib` / `numpy` / `PyYAML` の 5 つ。
**`PyYAML` は Mac の基準 venv に入っていなかったが、defib デックのビルドに必須**である
（`content/ch*.md` を YAML として読むため）。移行にあたり明示的に追加した。

---

## 3. build 手順

図（`figs/`）は**リポジトリに含まれていない**（第 7 節）。
初回は図の生成から始める。作業ディレクトリ（cwd）がデックごとに違う点に注意する。

### defib（除細動器）

```bash
cd decks/defib/scripts
python3 make_figs.py          # figs/*.png を生成（g1〜g4 に分かれている場合は make_figs_g1.py … も実行）
python3 build_defib_deck.py   # → ../out/除細動器を使いこなす.pptx
```

### etco2（EtCO₂）

```bash
cd decks/etco2/scripts
python3 make_figs.py
python3 build_etco2_deck.py   # → ../out/EtCO2モニタリング.pptx
```

### aline（観血的動脈圧）

```bash
cd decks/aline/scripts
python3 build_aline_white.py  # → ../out/観血的動脈圧測定.pptx
```

図は `../figs` を直接参照する。ソースは `../aline_content.json`。

### monitor-ecg（モニター心電図）

```bash
cd decks/monitor-ecg/scripts
python3 make_figs.py
python3 build_deck.py         # → ../モニター心電図.pptx（out/ ではなくデック直下）
```

### 環境変数

`figlib.py` は図の出力先を環境変数で上書きできる。既定は `<deck>/figs`。

| 変数 | 対象 | 既定値 |
|---|---|---|
| `ETCO2_FIGDIR` | etco2（および同型の figlib を使うデック） | `<deck>/figs` |

---

## 4. lint 手順

pptx を作ったら必ず実行する。**FONT<22 / TITLE 左詰め / 枠外はみ出し（OOB）/ 重なり が
すべて 0 になるまで**直して再実行する。

```bash
python3 lib/slide_lint.py decks/etco2/out/EtCO2モニタリング.pptx
```

複数まとめても良い。

```bash
python3 lib/slide_lint.py decks/*/out/*.pptx
```

### 移行時点の実測

| デック | 枚数 | サイズ | lint |
|---|---|---|---|
| defib | 71 | 4.6 MB | **0 違反** |
| monitor-ecg | 66 | 4.7 MB | **0 違反** |
| etco2 | 60 | 4.3 MB | **0 違反** |
| aline | 38 | 2.2 MB | **0 違反** |
| nibp | — | — | ビルド不可（第 8 節） |

etco2 については、再ビルドした pptx が Mac 上の既存 pptx と
**全 60 枚のタイトル文字列が一致**することも確認した。機構は正しく移設されている。

---

## 5. フォント — メイリオ（Meiryo）の扱い

**メイリオはこのリポジトリに含めない。含める必要もない。**

フォントには 3 つの役割があり、混同しやすいので分けて記す。

### (1) pptx 本文 → メイリオ（Meiryo）

`decklib.py` は `JP = "Meiryo"` を **書体名の文字列として** OOXML の
`a:latin` / `a:ea` / `a:cs` に書き込む。フォントファイルを読むことも埋め込むこともしない。

- **ビルドにメイリオのインストールは不要**である。Linux でも問題なくビルドできる。
- メイリオは Microsoft Office に同梱される商用フォントであり、**再配布はライセンス上できない**。
  しかし機構は名前しか使わないため、**コミットできないことが実害にならない**。
- 表示側の話として、メイリオが入っていない環境（Linux + LibreOffice 等）で開くと
  別書体に置換されて表示される。**最終的な実寸の目視確認は、メイリオが入った
  PowerPoint（Mac / Windows）で行うこと。**

`decklib.py` と `slide_lint.py` はこの置換を見越して、横幅 `JP_W = 1.12`・
行高 `JP_H = 1.18` の安全係数を掛けて幅を見積もっている
（本番の PowerPoint のメイリオは、置換先のヒラギノより大きく描画されるため）。

### (2) 図（matplotlib）→ ヒラギノ、Linux では Noto へフォールバック

`figlib.py` の書体指定は次のとおりで、matplotlib はグリフ単位でフォールバックする。

```
["Hiragino Sans", "Hiragino Kaku Gothic ProN", "Hiragino Maru Gothic ProN",
 "Noto Sans CJK JP", "Arial Unicode MS", "DejaVu Sans"]
```

Linux にヒラギノは無いが **Noto Sans CJK JP が拾われるため、図は正しく生成される**
（検証済み）。字形が macOS 版と厳密には一致しない点だけ注意する。

### (3) 幅の実測（PIL）→ macOS のフォントファイルを直接開く ★ 移植性の問題

`nibp` のビルドだけは、タイトル幅を測るために macOS のシステムフォントを
**実ファイルとして開く**。これが Linux では失敗する。第 8 節を参照。

---

## 6. 川副式ルール（維持すべき制約）

詳細は `docs/川副式スライド書式ルール.md`。要点のみ:

- タイトルは **44 pt 固定**・全スライド同一・**1 行**（収まらなければ文言を短くする。縮小しない）
- スライド内の全テキストが **22 pt 以上**。例外は出典のみで 10.5 / 12 / 16 pt
- **1 行 1 論点**。枠内厳守。**単語の途中で改行しない**
- 日本語書体はメイリオで統一
- **臨床数値・単位・薬剤量・出典は改変も丸めもしない。** 削った本文はスピーカーノートに全文残す

---

## 7. 意図的に除外したもの

大容量バイナリのため未コミット。`.gitignore` で除外している。

| 対象 | 規模 | 復元方法 |
|---|---|---|
| `figs/` の図 | 589 枚・約 17 MB | 各デックの `make_figs*.py` で再生成できる |
| `out/` の完成 pptx | 約 58 MB | build で再生成できる |
| `assets/`（nibp） | 74 枚・約 1 MB | 元ソース由来。再生成手順は未整備 |
| `.venv/`（monitor-ecg） | 約 159 MB | `pip install -r requirements.txt` で再構築 |
| メイリオ本体 | — | 商用ライセンスのため再配布不可。第 5 節のとおり不要 |

`aline` の `figs/` は `make_figs` 相当のスクリプトが同梱されておらず、
**図の再生成手順が現時点で未確認**である。Mac 側の `figs/` を手で持ち込む必要がある。

---

## 8. 既知の問題

### 8.1 nibp は Linux でビルドできない

`decks/nibp/build_deck.py:52` が macOS のシステムフォントを実ファイルとして開く。

```python
_TITLE_METRIC_FONT = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
```

Linux では `OSError: cannot open resource` で停止する。**Mac では正常に動く。**
移行にあたり**このコードは変更していない**（挙動を変えないため）。
Linux でも通したい場合は、この 1 行をフォールバック付きに直すのが最小の修正である。

```python
_TITLE_METRIC_CANDIDATES = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",                    # macOS
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",              # Linux
]
```

`monitor-ecg/scripts/figbase.py` も同じヒラギノのパスを持つが、こちらは
図の生成時のみ使われ、ビルド自体は Linux でも完走する。

### 8.2 decklib.py が 4 つに分岐している

`defib` / `etco2` / `aline` / `monitor-ecg` がそれぞれ別版を持つ。
`lib/decklib.py` には最新・最大の `defib` 版を正典として置いたが、
**シグネチャが異なるため各デックへの drop-in 置換はできない。**
現状は各デックが自分の版を同梱したまま動く構成を維持している。
詳細と収束手順は `docs/decklib-forks.md`。

### 8.3 SpO₂ PPG デックのソースは存在しない

本移行の当初の目的の一つは SpO₂ PPG デックのソース一式の移設であったが、
**このデックは decklib による組版産物ではない。**

- `SpO2(PPG)波形解析の流れ 3.4 → 4.15` の 7 世代は、いずれも PowerPoint で
  直接編集されたファイルである（`cp:revision` が 22 → 37 と増加している。
  生成物であれば revision はリセットされる）
- `content/` に相当する本文データ、build スクリプト、専用テンプレートのいずれも
  Mac 上に存在しない
- 唯一の関連コードは `monitor-ecg/scripts/figlib_ppg_ref.py`
  （PPG 波形の作図ライブラリ。冒頭に "for the PPG deck" とある）

したがって SpO₂ PPG デックは **slidegen の対象外**である。
この機構で組み直す場合は、既存 pptx から本文を抽出して `content/` を新規に起こす
工程が別途必要になる。

---

## 9. 出所

移行元は Mac ローカルの以下。移行時に**内容の改変は行っていない**。

| 移行先 | 移行元 |
|---|---|
| `decks/*` | `~/Desktop/{defib,etco2,aline,monitor-ecg,nibp}-slides/` |
| `lib/decklib.py` | `~/Desktop/defib-slides/scripts/decklib.py` |
| `lib/slide_lint.py` | `~/.claude/skills/slide-format/scripts/slide_lint.py` |
| `template/_template_kawazoe.pptx` | `~/Desktop/defib-slides/scripts/_template_kawazoe.pptx` |
| `docs/川副式スライド書式ルール.md` | `~/.claude/skills/slide-format/SKILL.md` |

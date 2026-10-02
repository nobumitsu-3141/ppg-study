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
├── setup-linux.sh               … Linux / claude.ai 用の初期化（依存＋フォント対応づけ）
├── .gitignore                   … 大容量バイナリの除外規則
├── fontconfig/
│   └── meiryo-alias.conf        … Meiryo → Noto Sans CJK JP（漢字の中国語字体化を防ぐ）
├── tools/
│   └── render_check.py          … pptx を PNG 化して目視確認する
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

### Linux / claude.ai（Web の Claude Code）で作業する場合

```bash
bash slidegen/setup-linux.sh
```

Python 依存に加え、**メイリオの対応づけ**（第 5 節）と**出力先ディレクトリの作成**を行う。
所要 1 分。以降は Mac と同じ手順で動く。

`out/` と `figs/` は `.gitignore` で除外しているためクローン直後に存在せず、
**これを作らずに build すると `FileNotFoundError` で落ちる。**
`setup-linux.sh` を使わない場合は手で `mkdir -p decks/*/out decks/*/figs` すること。

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

### 図（figs/）の再生成 — Linux でも動く

`figs/` は未コミットなので、クリーンクローン後はまず図を作る。**Linux で完走することを実証済み。**

| デック | Linux 生成 | Mac 原本 | 判定 |
|---|---|---|---|
| etco2 | 41 枚 | 41 枚 | ✅ |
| monitor-ecg | 41 枚 | 41 枚 | ✅ |
| defib | 40 枚 | 40 枚 | ✅ |
| aline | — | 76 枚 | ❌ 生成スクリプトが同梱されていない |

日本語グリフの欠落（豆腐）は発生しない。ヒラギノが無くても Noto Sans CJK JP が拾われる。

**ただし Linux で作った図は Mac 版とバイト単位で一致しない**（etco2 で 41/41 が相違）。
字形がヒラギノから Noto に変わるためである。**Linux で再生成した図をそのままコミットすると、
1 つのデックの中で図の字形が混在する。** 図を差し替えるときは、そのデックの図を
すべて同じ環境で作り直すこと。

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

### 目視確認（lint では捕まらないもの）

lint は座標とフォントサイズしか見ない。文字の重なりや図の収まりは描画しないと分からない。

```bash
python3 tools/render_check.py decks/etco2/out/EtCO2モニタリング.pptx --slides 1,5,12
```

LibreOffice で PDF 化し `pdftoppm` で 1 枚ずつ PNG にする。**Linux の描画は代替フォントに
よるもので、本番のメイリオより字面が小さい。ここで「ちょうど収まっている」ものは本番で溢れうる。**

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
#### ★ Linux では放置すると漢字が中国語字体になる

メイリオが無い Linux で `fc-match Meiryo` を引くと、fontconfig は日本語フォントに
たどり着けず **Droid Sans Fallback** に落ちる。実際に LibreOffice で PDF 化して
埋め込みフォントを調べると、次のように **Noto Sans CJK SC（Simplified Chinese：簡体字中国語）**
が混入していた。

```
BAAAAA+DejaVuSans-Bold      CAAAAA+DroidSansFallback
DAAAAA+NotoSansCJKsc-Bold   EAAAAA+NotoSansCJKsc-Regular   ← SC = 簡体字中国語
FAAAAA+NotoSansCJKjp-Regular ...
```

日本語と簡体字では同じ符号位置でも字形が異なる（直・骨・今・令 など）。
**プレビューが中国語字体になっていることに気づかないまま体裁を判断する**のが最大の危険である。

対策は `fontconfig/meiryo-alias.conf`（`setup-linux.sh` が導入する）。
これを入れた後に再変換すると **SC 参照 0 件・JP 参照 8 件**となり解消する。
**デック側のコードは一切変更しない。**

- 表示側の話として、メイリオが入っていない環境で開くと別書体に置換される。
  **最終的な実寸の目視確認は、メイリオが入った PowerPoint（Mac / Windows）で行うこと。**

`decklib.py` と `slide_lint.py` はこの置換を見越して、横幅 `JP_W = 1.12`・
行高 `JP_H = 1.18` の安全係数を掛けて幅を見積もっている。

この係数の内訳を実測した結果は次のとおり。

- **横幅**: 和文の全角文字は、どの CJK フォントでも送り幅が 1 em で共通である
  （44 pt で 16 字＝704 px が Noto と Droid で完全に一致した）。
  したがって `JP_W = 1.12` は**フォント間の字幅差ではなく経験的な安全余裕**である。
  実際に差が出るのは欧文・数字のプロポーショナル幅の部分に限られる。
- **行高**: こちらは実際に差がある。44 pt で Noto Sans CJK JP が 65 px、
  Droid Sans Fallback が 58 px と **約 12 % 違う**。`JP_H = 1.18` はこれに対応する。

両環境に同一のフォントを置けば、これらの係数は原理的に 1.00 にでき、
lint の推定と実描画が一致するようになる（第 5.4 節）。

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

### 5.4 メイリオを続けるか、乗り換えるか

メイリオ（Meiryo）は Microsoft が Windows Vista 向けに開発した ClearType 最適化書体で、
画面可読性は高い。**書体そのものに問題は無い。** 問題は「Mac にしか無い」という一点に集約される。

| 論点 | メイリオ継続 | 共通フォントへ乗り換え |
|---|---|---|
| ライセンス | 再配布不可（ただし名前しか使わないので同梱不要） | **SIL Open Font License。リポジトリに同梱できる** |
| Linux での描画 | 代替フォント。対応づけを忘れると中国語字体 | **Mac と同一の描画** |
| lint の精度 | 安全係数 1.12 / 1.18 で近似 | **係数 1.00 にでき、推定＝実測** |
| 既存 5 デックへの影響 | なし | **全デックの再ビルドと目視確認が必要** |
| 本番 PowerPoint | 確実に出る | フォント導入が必要（Mac・院内 PC 双方） |

**現時点の推奨は「メイリオ継続 ＋ `meiryo-alias.conf` で対応づけ」である。**
既存 5 デックが lint 0 違反で完成しており、乗り換えの利得より再検証の手間が上回る。

将来乗り換えるなら候補は 2 つ。いずれも SIL Open Font License で、
Mac・Windows・Linux に同じものを置ける。

- **BIZ UDPGothic**（モリサワ）― ユニバーサルデザイン書体。はね・ゲタを省いて字形を単純化し、
  大きめのサイズで使っても全体の均衡が崩れないよう調整されている。教育・行政文書向けに
  設計され、エンドユーザー評価にもとづく可読性を持つ。**投影して後方席から読む用途に最も近い設計思想。**
  Windows 10 1809 以降に同梱、Google Fonts / Google Workspace で配布。
  P は kana がプロポーショナル。全角揃えにしたい表組みには `BIZ UDGothic`（P なし）を使う。
- **Noto Sans JP / 源ノ角ゴシック**（Google・Adobe）― 最も入手しやすく、
  本番・プレビュー環境の一致という一点では最も確実。字面はやや大きめ。

乗り換える場合の最小手順は、`decklib.py` の `JP = "Meiryo"` を書き換え、
`slide_lint.py` の `JP_W` / `JP_H` を 1.00 に戻し、**全デックを再ビルドして
lint 0 違反と目視を通す**こと。デック単位で段階的に移行してよい。

参考:
- [BIZ UDPGothic — Google Fonts](https://fonts.google.com/specimen/BIZ%2BUDPGothic)
- [Morisawa BIZ UD fonts added to Google Fonts（Google Fonts Blog）](https://fonts.googleblog.com/2022/04/morisawa-biz-universal-design-ud.html)
- [モリサワ BIZ UD が Google Fonts で利用可能に（モリサワ）](https://en.morisawa.co.jp/about/news/6772)
- [Meiryo font family — Microsoft Learn](https://learn.microsoft.com/en-us/typography/font-list/meiryo)

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

### 8.2 aline はクリーンクローンからビルドできない

`aline` だけ `make_figs` 相当のスクリプトが同梱されておらず、`figs/` の 76 枚を
再生成できない。**Mac の `~/Desktop/aline-slides/figs/` を手で持ち込む必要がある。**
他の 4 デックは Linux で図から完全に再生成できることを実証済み。

### 8.3 decklib.py が 4 つに分岐している

`defib` / `etco2` / `aline` / `monitor-ecg` がそれぞれ別版を持つ。
`lib/decklib.py` には最新・最大の `defib` 版を正典として置いたが、
**シグネチャが異なるため各デックへの drop-in 置換はできない。**
現状は各デックが自分の版を同梱したまま動く構成を維持している。
詳細と収束手順は `docs/decklib-forks.md`。

### 8.4 SpO₂ PPG デックのソースは存在しない

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

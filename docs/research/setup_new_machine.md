# 別の端末で解析を継続する

**改訂**: 2026-09-03

結論から書く。**継続できる。** ただし運ぶものは3種類に分かれ、扱いがそれぞれ違う。

| 種類 | 中身 | 運び方 | 手間 |
|---|---|---|---|
| コードと文書 | スクリプト・原稿・解析計画・記録 | `git clone` | 数分 |
| 再生成できるデータ | VitalDB の症例・トラック一覧、PWDB | その端末で取り直す | 一覧は数分、PWDB は 265 MB |
| **複製が要るデータ** | `analysis/data/features*` ほか | **元の端末から直接コピー** | 合計 200 MB 程度。**再計算すると数日** |

最後の1つが要点である。数日かけて計算した結果だが、容量は小さい。
`analysis/.gitignore` で `data/` を除外してあるので git では運べない（公開リポジトリであり、
再配布しない規約でもある。`data_management_v0.md`）。

---

## 手順

### 1. リポジトリを取る

```
git clone https://github.com/nobumitsu-3141/ppg-study.git ~/ppg-study
cd ~/ppg-study
git checkout claude/slide-references-formatting-ynthk7
```

### 2. 立ち上げスクリプトを走らせる

```
bash analysis/scripts/setup_new_mac.sh
```

これが順に、Python の仮想環境を作り、`requirements.txt` を入れ、VitalDB の一覧を取り直し、
**足りないデータを数えて rsync のコマンドを表示し**、各スクリプトの自己検査を回す。
何度実行してもよく、既存のデータを消したり上書きしたりしない。

`python3` が無いと言われたら `xcode-select --install` を先に実行する。

### 3. 複製が要るデータを運ぶ

スクリプトが表示するコマンドをそのまま使う。同じ LAN にあるなら rsync が速い。

```
# 元の Mac 側で実行する
rsync -av --progress ~/ppg-study/analysis/data/features/ \
  <新しいMacのユーザ名>@<新しいMacの名前>.local:~/ppg-study/analysis/data/features/
```

新しい Mac の名前は「システム設定 → 一般 → 情報」で分かる。事前に元の Mac ではなく
**受け側**で「システム設定 → 一般 → 共有 → リモートログイン」を入にしておく。

同じ LAN にないなら、外付けドライブか AirDrop でフォルダごと運ぶ。
**共有クラウド（iCloud の共有フォルダ等）には置かない。**

運んだあとは件数を確かめる。

```
cd ~/ppg-study/analysis
.venv/bin/python scripts/status.py
```

`features` と `features_variants` が 862、`features_art` が 862、`vasotone` が 232 なら揃っている。

### 4. PWDB（研究0 を続けるなら）

Zenodo（doi:10.5281/zenodo.3275625）から次の6つを `~/pwdb/` に置く。合計 265 MB。
44.3 GB は記録全体の合計で、`.mat` は不要である。

```
pwdb_haemod_params.csv   pwdb_model_configs.csv   pwdb_model_variations.csv
pwdb_onset_times.csv     pwdb_pw_indices.csv      PWs_csv.zip（展開不要）
```

---

## 何を持って行かなくてよいか

- `analysis/.venv/` — 端末ごとに作る。持ち込むと壊れる
- `analysis/figs/` — `07_figures.py` で作り直せる
- `data/cases.csv`・`trks.csv`・`target_cases.csv` — 立ち上げスクリプトが取り直す
- 波形そのもの — 保存していない。必要なつど VitalDB から取得している

---

## 作業の分担

このクラウドのセッション（claude.ai/code）は端末に紐づかない。どの Mac からでも同じ
会話を開いて続けられる。Mac が要るのは次の2つだけである。

1. **VitalDB からの波形取得**（クラウドからも到達できるが、862例規模は Mac で走らせている）
2. **重い計算**（変種抽出は8コアで数日）

原稿・解析計画・スクリプトの編集はクラウド側で行い、`git push` → Mac で `git pull` → 実行、
という往復で進めてきた。新しい Mac でもこの形は変わらない。

2台の Mac を同時に使うなら、**同じ抽出を同時に走らせないこと**。
症例単位のキャッシュなので壊れはしないが、VitalDB への同時接続が増えるだけで速くならない。
分けるなら症例範囲で分け、あとで `data/features*/` を片方に集める。

---

## 元の Mac を手放す前に

`analysis/data/` を丸ごとコピーしておく。ここにしか無いものが入っている。

```
rsync -av ~/ppg-study/analysis/data/ /Volumes/<外付け>/ppg-study-data-$(date +%Y%m%d)/
```

`~/pwdb/` は Zenodo から取り直せるので、無理に運ばなくてよい。

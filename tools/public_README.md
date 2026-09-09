# ppg-pda-analysis

光電容積脈波の**脈波分解（pulse decomposition analysis, PDA）**から作った指標が血管の情報を
持つか、そしてそれで脈波伝播時間による心拍出量推定（esCCO）を補正できるかを検証した
一連の解析のコードと、確認的解析の前に凍結した事前登録である。

**患者データは含まない。**解析は公開データベース（VitalDB、Pulse Wave Database）に対して走る。

## 中身

| 場所 | 内容 |
|---|---|
| `analysis/src/` | 凍結した脈波分解（歪みガウス2成分）、指標の定義、拍の切り出しと品質判定、統計 |
| `analysis/scripts/` | 各解析。確認的解析と探索的解析を担う 37 本中 23 本に `--selftest` があり、ネットワーク不要で検算できる。取得・図・表のスクリプトには無い（`analysis/README.md` に一覧） |
| `analysis/tests/` | 真値既知の合成データによる測定系の検証。`python3 -m tests.test_pda_synthetic` のように走らせる |
| `preregistration/` | 統計解析計画（凍結時点のもの）と判定規準、用語の決まり |

## 再現の手順

```sh
pip install -r analysis/requirements.txt
python3 analysis/scripts/39_ri_svr_standalone.py --selftest
python3 analysis/scripts/39_ri_svr_standalone.py --lists
python3 analysis/scripts/39_ri_svr_standalone.py --run --jobs 4
```

39番は**自己完結**しており、このリポジトリのコードと VitalDB への接続だけで最初から走る。

**他のスクリプトには前提がある。**中間生成物を要するもの（37番・38番は 16番と主解析の出力が要る）と、
Pulse Wave Database の取得が要るもの（20番台の PWDB 系）がある。依存関係は
`analysis/README.md` に書いてある。**`--selftest` は合成データで完結するように書いてあるが、
PWDB 系の一部は実データを参照するため、データを取得していない状態では通らない。**

## 事前登録と判定規準について

`preregistration/` の各計画は、**確認的解析を走らせる前に凍結し、タグを付けてある。**
閾値・判定規準・中止規準は結果を見たあとで変えていない。変えた場合はその旨と理由を
記録している。

各計画の文中に `lab_log.md 追記N` という参照がある。これは日々の実験ノートで、
**未発表の結果と患者データに触れる記述を含むため公開していない。**参照は出所を
示すためのもので、解析を再現するのに要る閾値・規準・手順はいずれも
`preregistration/` の各文書の中に書いてある。

## 引用

`CITATION.cff` を参照。v1.0.0 は Zenodo に保存してある。

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22676039.svg)](https://doi.org/10.5281/zenodo.22676039)

    doi:10.5281/zenodo.22676039

版を上げるたびに Zenodo が新しい DOI を発行する。**論文が引いているのは v1.0.0 の
DOI である。**その版のコードで結果が出ているためで、以後の版を指してしまうと
再現の対象が変わる。

## ライセンス

コード（`analysis/src/`・`analysis/scripts/`・`setup_mac.sh`）は **MIT**（`LICENSE`）。
`preregistration/` の文書は散文なので **CC BY 4.0**（`LICENSE-docs`）。
Zenodo の記録には、上載の種別が software であることに合わせて MIT を載せている。

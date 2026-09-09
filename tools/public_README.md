# ppg-pda-analysis

光電容積脈波の**脈波分解（pulse decomposition analysis, PDA）**から作った指標が血管の情報を
持つか、そしてそれで脈波伝播時間による心拍出量推定（esCCO）を補正できるかを検証した
一連の解析のコードと、確認的解析の前に凍結した事前登録である。

**患者データは含まない。**解析は公開データベース（VitalDB、Pulse Wave Database）に対して走る。

## 中身

| 場所 | 内容 |
|---|---|
| `analysis/src/` | 凍結した脈波分解（歪みガウス2成分）、指標の定義、拍の切り出しと品質判定、統計 |
| `analysis/scripts/` | 各解析。**すべてに `--selftest` がある**（ネットワーク不要で検算できる） |
| `preregistration/` | 統計解析計画（凍結時点のもの）と判定規準、用語の決まり |

## 再現の手順

```sh
pip install numpy pandas scipy vitaldb
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
記録している（記録そのものは非公開の実験ノートにある）。

## 引用

`CITATION.cff` を参照。版ごとの DOI は Zenodo にある。

## ライセンス

CC BY 4.0（`LICENSE`）。

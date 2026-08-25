# PPG研究 解析コード（チェックリスト C-1〜C-4 / 事前① VitalDB）

スライド「PPG波形解析 8.7」6.6〜6.7 の解析パイプライン。
チェックリスト（準備C・事前①）の実装部分がここに入っている。

## セットアップ（Mac・初回のみ）

```bash
cd analysis
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## まず動作確認（C-4: 合成波形でのPDA検証）

```bash
python3 -m tests.test_pda_synthetic
```

クラウドセッション（2026-08-25）での検証結果:

- 切痕あり波形（単拍・ノイズ1%）: ΔT誤差 ≤1.3 ms, RI誤差 ≤2.4% で復元
- DN-less波形（重なり大）: 単拍・ノイズ1%では不安定（ΔT −16 ms / RI +21% 中央値）
  → **4拍アンサンブル平均で ΔT ≤2.8 ms / RI ≤2.7% に回復**
- 1成分だけの波形に2カーネルを当てると収束検算がフラグを立てる（過剰カーネル検出）

**運用上の帰結**: DN-less拍はPDAの前に連続数拍のアンサンブル平均を行う（P4の前処理に組み込み済み）。
これはスライド5.5「解が一意に決まらない／振幅側が弱い」の定量的実証でもある。

## 指標定義の候補比較（SAP凍結の根拠）

```bash
python3 -m tests.test_index_variants
```

SI・RIの定義には複数の候補がある（ピーク間ΔT／立ち上がり間ΔT／μ差、ピーク高さ比／振幅パラメータ比／面積比）。
実データを見る前に主要定義を凍結するため、真値既知の合成データで同定性を比較する。
クラウドセッション（2026-08-25）での結果:

- 良好な条件（4拍・ノイズ1%）では**全定義が真値を復元**する（振幅側の誤差 ≤2.8%）
- 同定性の限界（DN-less・ノイズ2%・4拍）では解が**二峰化**し、40拍中17拍が別解に落ちる。
  そのうち **16/17 が収束検算を通過してしまう** → 検算だけでは弾けない。
  波形段階のSQIとアンサンブル拍数で担保する
- 立ち上がり間ΔT（前進波の始まり→反射波の始まり）は、当てはめ誤差を **4〜6倍に増幅**する
  （正しい解に収束した拍でも ΔT_peak 1.1ms に対し ΔT_onset10 は 6.5ms）
- アンサンブル拍数を 4→16 に増やすと DN-less・2% でも ΔT_peak −1.1ms / RI_peak +0.5% に回復

**帰結（SAPに固定する）**: 主要指標は **ΔT_peak**（身長を掛ければSI）と **RI_peak**（成分波ピーク高さ比）。
立ち上がり間ΔTは副次・感度解析に置く。SI は身長が症例内で一定なので、
症例内の相対変化（ΔSI%）では身長が完全に約分される — ΔT をそのまま使っても結論は変わらない
（合成コホートで ΔPE の差は 0.1〜0.3ポイント、有意性の判定は不変）。

## 解析機構の検証（Phase 3〜5: モデル・統計・交差検証）

```bash
python3 -m tests.test_pipeline_synthetic
```

真値既知の合成コホート（80例×30ウィンドウ）で、対照モデル（PWTT型）→
K(SI,RI)補正→症例単位5-fold CV→ブートストラップCI の一連を検証する。
クラウドセッション（2026-08-25）での結果:

- effectコホート（PWTTに血管状態が混入＝補正の余地が実在）: 3シード全てで
  ΔPE（提案−対照）の95%CI上限 < 0（有意な改善を正しく検出）
- nullコホート（混入なし）: 3シードとも有意差なし（**偽陽性ゼロ** — 改善が無いのに
  「改善あり」と言ってしまわないことの確認）
- Bland-Altman・4象限concordanceが破綻なく計算できること

つまり実データで有意差が出ても出なくても、それが機構のバグではなく
データの答えだと言える状態になっている。

## VitalDB（事前①）の実行順

※ 事前に vitaldb.net でアカウント登録・利用規約に同意（P0-1）、
   倫理委員会への該当性照会の回答を確認（P0-2）してから。

```bash
python3 scripts/00_download_lists.py   # 症例・トラック一覧の取得
python3 scripts/01_track_inventory.py  # P1-1: 装置別CO×波形の保有集計（552例の再現）
python3 scripts/02_fetch_case.py 1     # P0-3: 1症例で波形取得→PDA→PWTTの動作確認
python3 scripts/03_run_analysis.py     # 本解析: まず20例でパイロット（--limit で拡大）
```

`03_run_analysis.py` は 波形→拍→SQI→4拍アンサンブル→PDA→SI・RI と PWTT・HR・参照CO を
60秒ウィンドウごとに抽出して `data/features/` にキャッシュし、合成テストと同じ機構
（症例単位5-fold CV＋ブートストラップCI）で ΔPE・Bland-Altman・concordance を出す。
SQI閾値・採否基準は v0 仮置き — Phase 2 でパイロット結果を見て確定し、SAPに固定してから
本解析（全例）を回すこと。

引用要件: Lee HC, et al. *Sci Data* 2022;9:279（PMID 35676300, DOI 10.1038/s41597-022-01411-5）。

## 構成

| ファイル | 内容 |
|---|---|
| `src/pda.py` | skewed-Gaussian 2カーネルのPDA。ランドマーク初期値（5.3-a）＋dmuグリッド多点スタート（5.3-c）＋収束検算（境界張り付き・振幅ゼロ・競合解の曖昧さ・残差の谷幅） |
| `src/indices.py` | 成分波からの ΔT・RI・SI、ECG＋脈波からの PWTT |
| `src/beats.py` | 拍切り出し・SQI v0・アンサンブル平均 |
| `src/synth.py` | 真値既知の合成PPG（切痕あり／DN-less） |
| `src/models.py` | 対照モデル（PWTT型）と提案モデル（K(SI,RI)補正）、症例単位k-fold CV（リーク禁止） |
| `src/stats.py` | percentage error（Critchley）・Bland-Altman・4象限concordance・症例単位ブートストラップCI |
| `src/synth_cohort.py` | 真値既知の合成コホート（effect/null）— モデル・統計の機構検証用 |
| `tests/test_pda_synthetic.py` | C-4 の検証（上記結果を再現） |
| `tests/test_pipeline_synthetic.py` | Phase 3〜5 の機構検証（有意差の検出＋偽陽性ガード） |
| `tests/test_index_variants.py` | SI・RI の定義候補の同定性比較（SAP凍結の根拠） |
| `scripts/00〜02` | VitalDB のデータ取得と P1-1 集計（要インターネット。クラウドセッションからは vitaldb.net に接続不可のためMacで実行する） |
| `scripts/03_run_analysis.py` | 本解析ランナー: 特徴量抽出（キャッシュ付き）→CV→統計。P0-2通過後にMacで実行 |

## 注意

- `data/` はダウンロードした公開データ置き場。**リポジトリにはコミットしない**（.gitignore済み）。
- SQI閾値・除外基準は Phase 2 で実データを見て確定し、確定値は統計解析計画（docs/research/sap_v0.md）に固定する。
- 参照COの装置内訳（FloTrac系＝動脈圧由来／Vigilance II＝肺動脈カテ熱希釈）は解析で区別する。

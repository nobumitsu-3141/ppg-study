# analysis — 解析コード

`src/` に凍結した測定系、`scripts/` に各解析、`tests/` に真値既知の合成データによる検証がある。
**患者データは含まない。**`data/` は `.gitignore` で除外してあり、公開されていない。

## 動かす

```sh
pip install -r analysis/requirements.txt
```

`vitaldb` の版は固定してある。1.7.2 は波形の再標本化が変わり（欠測の埋め方・±20 ms のずれ）、
拍の型と脈波伝播時間が変わるため、研究1 の抽出に使った 1.5.8 を指定している。

検証は `analysis/` の中で走らせる。

```sh
python3 -m tests.test_pda_synthetic
python3 -m tests.test_pipeline_synthetic
```

解析スクリプトの検算は `--selftest` である。**37 本中 23 本にある。**取得（00〜02番）、
主解析ランナー（03番）、診断・図・表（05〜14番）には無い。これらは取得済みの、あるいは
既に抽出した特徴量に対して走るためである。28番は `--selftest` を持たず、そのまま実行すると
不変条件の検査になる。

```sh
python3 scripts/39_ri_svr_standalone.py --selftest
```

## 何が何を要るか

| 種別 | スクリプト | 要るもの |
|---|---|---|
| 自己完結 | 39番 | ネットワーク（VitalDB）だけ。最初から走る |
| 合成データのみ | `tests/` 全部・25番・28番 | 何も要らない |
| VitalDB の取得が要る | 00〜03番・05番・32番・34番・40番 | vitaldb.net への接続 |
| 中間生成物が要る | 37番・38番・41番 | 16番と主解析の出力（`data/features/`・`data/vasotone/`） |
| Pulse Wave Database が要る | 20・23・24・26・27・29・31・33番 | 22番で取得（doi:10.5281/zenodo.3275625） |

**`--selftest` は 23 本すべてが、データを 1 つも置いていない状態で通る**（2026-09-10 に
clone 直後と同じ木で確認）。走行中に `data/` へ書き出されるのは 26番の照合用 CSV と
33番の進捗の 2 ファイルだけである。

**27番は 26番の後に走らせること。**27番は 26番が残す照合用の出力を読んで、採否と曖昧判定の
再計算が 26番の保存値と一致するかを検算する。その出力が無い、または `pda2` の版が違う場合は
検算を省略し、省略したことを画面に出したうえで `ALL PASS` と表示する。**単独実行の
`ALL PASS` は 27番だけの検査であって、26番との整合は含まない。**

## 構成

| ファイル | 内容 |
|---|---|
| `src/pda.py` | 凍結版の脈波分解。歪みガウス2成分。特徴点による初期値、Δμ の格子多点スタート、収束の検算（境界張り付き・振幅ゼロ・競合解の曖昧さ・残差の谷の幅） |
| `src/pda2.py` | 第2版。歪みガウスとガンマの2経路、Wang 2013 の採否規準、ΔT の標準誤差、曖昧判定。凍結版は研究1 のためにそのまま残してある |
| `src/indices.py` | 成分波からの ΔT・RI・SI、R波検出（Pan-Tompkins 型）、心電図と脈波からの脈波伝播時間 |
| `src/beats.py` | 拍の切り出し（心電図基準・2階微分による足）、信号品質指標、拍頭を揃えたアンサンブル、雑音推定と拍数の適応決定 |
| `src/synth.py` | 真値既知の合成光電容積脈波（重複切痕あり／切痕なし） |
| `src/synth_cohort.py` | 真値既知の合成集団（効果あり／帰無）。モデルと統計の機構検証用 |
| `src/models.py` | 対照モデル（脈波伝播時間型）と提案モデル（K(SI,RI) 補正）、症例単位 k-fold 交差検証、前提検証と増分価値 |
| `src/stats.py` | percentage error（Critchley）、Bland-Altman、4象限 concordance、症例単位ブートストラップ信頼区間 |
| `tests/test_pda_synthetic.py` | 凍結版の分解が真値を復元するか。切痕なしの拍では単拍で解が定まらず、アンサンブル平均で定まることを含む |
| `tests/test_r_peak_detection.py` | R波検出の頑健性（アーチファクト耐性・T波の誤検出） |
| `tests/test_beat_segmentation.py` | 拍の切り出し（重複切痕の二重検出）と整列 |
| `tests/test_ensemble_adaptive.py` | 雑音に応じた拍数の決定と棄却規準 |
| `tests/test_index_variants.py` | SI・RI の定義候補の同定性の比較（凍結の根拠） |
| `tests/test_variant_indices.py` | 代替定義の指標の算出 |
| `tests/test_pipeline_synthetic.py` | モデル・統計・交差検証の機構（有意差の検出と偽陽性の抑止） |
| `tests/test_reference_independence.py` | 参照心拍出量の血圧依存による見かけの改善を見抜けるか |
| `scripts/00〜02` | VitalDB の一覧取得と症例取得（要インターネット） |
| `scripts/03_run_analysis.py` | 主解析。特徴量抽出（キャッシュ付き）→交差検証→統計 |
| `scripts/05_diagnose_waveform.py` | 実波形の素性診断（値の分布、R波で揃えた平均テンプレート、テンプレートへの当てはめ） |
| `scripts/06〜19` | 陽性対照、図、処理の影響、感度解析、表1、代替定義、指標の寄与、立ち上がりの傾き、動脈圧由来の指標、血管緊張度 |
| `scripts/20_pwdb_validity.py` | Pulse Wave Database での凍結版の妥当性（判定規準の本体） |
| `scripts/22_pwdb_fetch.py` | Pulse Wave Database の取得 |
| `scripts/23_pwdb_landmarks.py` | 特徴点法の指標（Charlton 同梱値）の妥当性、模擬データの生成 |
| `scripts/24_pwdb_pda_ablation.py` | 分解の条件を1つずつ外したときの妥当性の変化 |
| `scripts/25_pda2_validate.py` | 第2版の合成波検証 T1〜T13 |
| `scripts/26_pwdb_compare.py` | 決定試験。第2版・凍結版・特徴点法・早期振幅比を同じ真値・同じ規準で並べる |
| `scripts/27_threshold_sensitivity.py` | 閾値の感度解析（当てはめ直し不要の層と、部分集合で当てはめ直す層） |
| `scripts/28_pda2_invariants.py` | 乱数で作った拍での不変条件の検査。例に依存しない検査である |
| `scripts/29_pwdb_reject_diag.py` | 採択率が極端に低いときに原因を記述する。閾値は動かさない |
| `scripts/30_c1_dose_steps.py` | 昇圧薬の用量ステップに対する脈波伝播時間の構成要素の応答。抽出（`--extract`）と統計（`--stats`） |
| `scripts/31_pwdb_basis_explore.py` | 【探索・事後】基底関数を同じ規準で並べる。判定には使わない |
| `scripts/32_vitaldb_landmark_identifiability.py` | モニタ波形で特徴点法の ΔT と早期振幅比が同定でき、ウィンドウ間で再現するか |
| `scripts/33_pwdb_literature_replica.py` | 【探索・事後】文献6編の分解手法をその条件のまま当て、同じ被験者の特徴点法と比べる。逸脱表つき |
| `scripts/34_vitaldb_methods_compare.py` | 【探索】我々の条件と文献の条件を同じウィンドウ・同じ平均拍で並べ、同定率・再現性・級内相関を比べる |
| `scripts/35_amb_premise_extract.py` | 【探索・凍結後】早期振幅比だけを抽出する軽量版（**当てはめを行わない**） |
| `scripts/36_amb_premise_stats.py` | 【探索・凍結後】35番の結果を研究1 に結合し、4通りの説明を同じウィンドウで比べる |
| `scripts/37_ri_svr_screen.py` | 【探索】RI と末梢血管抵抗の関係の走査。判別試験と用量反応を含む |
| `scripts/38_couceiro_svr.py` | 【探索】Couceiro の指標について同じ検討を行う |
| `scripts/39_ri_svr_standalone.py` | 【探索】37番と同じ問いを、中間生成物なしで最初から走らせる自己完結版 |
| `scripts/40_downsample_125hz.py` | 【探索】500 Hz を 125 Hz に間引いたときに各指標が保たれるか。3 通りの間引き方で比べる |
| `scripts/41_fill_tables.py` | 論文1 の表2・表4・表5 に残った未記入の値を出す。主解析と同じ関数・規準・乱数種を使い、確定済みの値が再現することを併せて表示する。再現しなければ止まる。`data/features/` が要る |
| `scripts/42_rebuild_on_new_mac.py` | 主解析を回していない機械で、取得から表の値まで一本で走らせる台本（00→01→03→41）。**取得を始める前に版を照合し、`vitaldb` が違えば止まる。**途中で止めても続きから進む |
| `scripts/check_terminology.py` | 文書の用語検査（`preregistration/terminology.md` の規則。記録との差分だけを見る） |

## 事前登録

`preregistration/` に、確認的解析の前に凍結した統計解析計画と判定規準がある。
実行順と読み方は `preregistration/gate0_rules_v2.md`、用語の決まりは
`preregistration/terminology.md` にある。閾値の由来、決定試験の判定の経緯、
実験ノートは非公開の記録に置いてある。

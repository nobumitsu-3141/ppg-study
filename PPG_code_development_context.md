# PPG/APG 研究 ― コード開発コンテキスト（新規事項のみ）

本ドキュメントは、別途の研究相談セッションからの引き継ぎ資料（`HANDOFF.md` 相当）のうち、**既存の各成果物（`README.md`、`SpO2_PPG_waveform_analysis_flow.*`、`PPG_dicrotic_notch_resistance_review.html`、`PPG_LVET_six_factors_figures.html`、`PPG_fig2_factor_references_4_2.html`、`t2_pi_normalization.html`）でまだ扱っていない新規事項だけ**を抜き出して収めたものである。今後の信号処理・notch 検出・データ解析パイプライン等のコード作業の起点として使う。

> **重複について**：引き継ぎ資料の大半（dicrotic notch が複合信号であること、加齢に伴う notch 消失機序、PPG 振幅と SVR の相関が弱く幅の方が良好であること、Tusman 2019 の 6 クラス分類、Δ 追跡の設計思想、AGC と帯域制限の区別、PWV を結果指標として扱う原則、Takazawa 1998・Awad 2007・Pal 2024（IEM）・Mulder 2022・Chowienczyk・Millasseau・Cannesson・Chételat/Sola 2018 などの文献、および PPG/APG/SDPTG/SVR/MAP/PWV/PI/PVI/SPI/LVET/AIx/rPPG/dP·dt などの用語）は既存文書に反映済みのため、本書では再掲しない。所在は末尾「§6 既存文書で網羅済みの事項」を参照。

---

## 1. 追加文献（既存の参考文献リストに未収録のもの）

既存文書の参考文献に含まれていない、新たに参照すべき一次文献。初出用語はフルスペル＋日本語訳を併記する（用語集 §5 に準拠）。

| 文献 | 内容 | リンク |
|------|------|--------|
| **Echeverría NI, Tusman G, et al. (2023)** *Rev Esp Anestesiol Reanim* 70:187–246 | PPG 波形分類による低血圧検出の感度・特異度を、ニューラルネットワーク（neural network）を用いて一般外科手術患者で検証 | https://doi.org/10.1016/j.redar.2022.01.011 |
| **Coutrot M, et al. (2019)** *Br J Anaesth* 122(5):605-612 | 麻酔導入時 61 例で、**Dicpleth**（相対 dicrotic notch 高比）と PI の変動が術中低血圧（IOH）の検出および昇圧薬ボーラスへの血管反応追跡に有用であることを示した proof-of-concept | https://doi.org/10.1016/j.bja.2019.01.037 |

> 注：既存の `SpO2_PPG_waveform_analysis_flow.md` には Coutrot が**共著**として別論文（Joachim J, Coutrot M, Millasseau S, et al. の MAP 実時間推定）で登場するが、上表の Coutrot 2019（BJA、Dicpleth の proof-of-concept）は別論文であり未収録。

---

## 2. 実装対象の指標定義（コードで算出できるようにするもの）

引き継ぎ資料が挙げる、優先的に実装すべき定量指標。既存文書では概念に触れていても**明示的な算出定義**として未整理のもの。

- **Dicpleth（Relative Dicrotic Notch Height Ratio：相対的重複切痕高比）**
  収縮期振幅に対する dicrotic notch の相対的な高さの比。Coutrot 2019 で導入。低血圧検出・昇圧薬反応追跡の指標。
- **SPD（Systolic Phase Duration：収縮期相持続時間）**
  収縮期の開始（駆出開始）から notch までの時間。
- **収縮期立ち上がりの傾き（Systolic Upstroke Slope）**
  心収縮力（contractility）の変化を、前負荷（preload）や SVR の変化と区別する鍵となる特徴。Mulder 2022 の in silico シミュレーションでの感度は **前負荷低下 2.02 / 収縮力低下 0.80 / 後負荷低下 −0.02** とされ、この傾きは前負荷変化に最も敏感。
- **2 次元評価**
  振幅（amplitude）と notch height を組み合わせた 2 次元評価は、単一指標より情報量が多い。可視化・分類ロジックはこの 2 軸を保持する設計にする。

---

## 3. コード作業の実装方針（Next Steps）

1. **notch 検出アルゴリズム**：Pal 2024 の **IEM（Iterative Envelope Mean：反復エンベロープ平均）**法を第一候補として実装を検討する（DOI: https://doi.org/10.1016/j.cmpb.2024.108283。※本文献自体は既存の `PPG_dicrotic_notch_resistance_review.html` に既出）。
2. **分類ロジック**：Tusman 2019 の 6 クラス視覚的 PPG 分類（notch 位置と PPG 振幅から Class I〜VI を判定。Class I–II＝血管収縮／notch 位置 >50%・振幅小、Class III＝正常、Class IV–VI＝血管拡張／notch 位置 <20%・振幅大）を**ルールベース**で実装可能。
3. **優先算出指標**：Dicpleth・SPD・収縮期立ち上がりの傾き（§2）を最初に算出できるようにする。
4. **命名・コメント規約**：用語集（§5・および既存文書の用語定義）に従い、初出の専門用語はコード内コメント・ドキュメントでフルスペル＋日本語訳を併記する。
5. **未解決の論点（実装・検証時に留意）**：
   - notch height の「垂直方向の高さ」「時間的位置」「振幅比」のうち、どの次元が独立した臨床的意味を持つか。
   - SVR・1 回拍出量・収縮力・動脈コンプライアンスの寄与を、単一の視覚的 notch 評価からどこまで分離できるか（原理的な限界があることに留意）。

---

## 4. 国内デバイス動向（Device Landscape in Japan）

APG（加速度脈波）取得の実機選定に関する調査メモ。既存文書には未収録。

- **日本光電（Nihon Kohden）**：現時点で APG 機能を提供する製品は**確認されていない**。
- 代替候補として確認済みの国内販売デバイス：
  - **YKC（TAS9VIEW）**
  - **Medicore Japan**
  - **Dynapulse SDP-100**
  - **Health Promotion Inc.**

※ 各社の仕様・薬事状況は変わりうるため、実機導入検討時は各社公式サイトで再確認する。

> **要確認の不整合**：`README.md`（§7 ロードマップ）は加速度脈波専用機を「**Fukuda Denshi** SDP-100」と記載するが、本引き継ぎ資料は同型番を「**Dynapulse** SDP-100」とする。製造元表記が食い違うため、実機確認時にどちらが正しいかを確定させること。

---

## 5. 用語集への追加（既存文書に未収録の略語のみ）

既存文書の用語定義に加えて用いる略語。既出のもの（PPG/APG/SDPTG/SVR/MAP/PWV/PI/PVI/SPI/LVET/AIx/rPPG/dP·dt など）は再掲しない。

| 略語 | フルスペル | 日本語訳 |
|---|---|---|
| Dicpleth | Relative Dicrotic Notch Height Ratio | 相対的重複切痕高比 |
| SPD | Systolic Phase Duration | 収縮期相持続時間 |
| Cvasc | Vascular Compliance | 血管コンプライアンス |
| VA coupling | Ventriculo-Arterial Coupling | 心室・動脈カップリング |
| Ea/Ees | Arterial Elastance / End-systolic Elastance | 動脈エラスタンス／収縮末期エラスタンス比（VA coupling の指標。既存文書の「エラスタンス」記述も参照） |
| iPPG | Imaging Photoplethysmography | 撮像（カメラ）光電容積脈波 |

---

## 6. 既存文書で網羅済みの事項（本書では扱わない）

引き継ぎ資料のうち以下は既存成果物に反映済みのため、重複を避けて本書からは除外した。所在は下表のとおり。

| 事項 | 所在 |
|------|------|
| 研究目的・中心仮説（notch height と後負荷／昇圧薬タイミング） | `README.md` §1、`SpO2_PPG_waveform_analysis_flow.*`、`PPG_dicrotic_notch_resistance_review.html` |
| dicrotic notch が複合信号であること（SVR・SV・収縮力・動脈コンプライアンス） | `SpO2_PPG_waveform_analysis_flow.*`、`PPG_fig2_factor_references_4_2.html` |
| 加齢に伴う notch 消失機序（PWV 増加 → 反射波が収縮期ピークに融合） | `SpO2_PPG_waveform_analysis_flow.*`（§6）、`PPG_dicrotic_notch_resistance_review.html` |
| PPG 振幅は SVR との相関が弱く、幅（width）の方が良好（Awad 2007） | `README.md` §10、`SpO2_PPG_waveform_analysis_flow.*` |
| Tusman 2019 の 6 クラス視覚的 PPG 分類 | `SpO2_PPG_waveform_analysis_flow.*` ほか |
| rPPG による昇圧薬投与時の波形変化（症例シリーズ 2025、NA 増量で MAP・PI 上昇） | `t2_pi_normalization.html`（PMC12898464） |
| Mulder 2022 / Takazawa 1998 / Pal 2024（IEM）/ Chowienczyk / Millasseau / Cannesson / Chételat・Sola 2018 | 各 HTML の参考文献欄 |
| Δ（個人内相対変化）追跡の設計思想、AGC と帯域制限の区別、PWV を結果指標とする原則 | `README.md` §4、`SpO2_PPG_waveform_analysis_flow.*` |
| 標準用語（PPG/APG/SDPTG/SVR/MAP/PWV/PI/PVI/SPI/LVET/AIx/rPPG/dP·dt） | 既存文書の用語定義 |

> **引用検証メモ**：`t2_pi_normalization.html` の「rPPG 昇圧薬症例シリーズ 2025」（PMC12898464）は著者を「Coutrot M, et al.」と記しているが、引き継ぎ資料はこの rPPG 昇圧薬症例シリーズを **Rubins U, et al. (2025, *J Clin Med*, DOI: 10.3390/jcm15031118)** に帰属させている。本プロジェクトは引用の厳格な検証を方針としているため、いずれの著者が正しいかを一次情報で確認し、必要なら該当箇所を訂正すること。

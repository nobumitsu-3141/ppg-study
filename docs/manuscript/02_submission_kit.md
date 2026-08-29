# 投稿キット（カバーレター・チェックリスト・定型文）

**作成**: 2026-08-29 ／ 投稿先が確定したら誌名・書式をここに反映する。

---

## 1. カバーレター（雛形）

> 陰性結果の論文では、カバーレターが「なぜこれを載せる価値があるのか」を
> エディタに納得させる唯一の場になる。**査読に回すかどうかはここで決まる。**

```
Dear Editor,

We submit for your consideration our manuscript entitled
"[[TITLE]]", for publication as an [[Original Article / Technical Note]] in
[[JOURNAL]].

Estimation of cardiac output from pulse-wave transit time is attractive because it
requires only signals that are already recorded in every anaesthetised patient. Its
error, however, is not random: several groups have shown that agreement with reference
cardiac output degrades in proportion to the patient's vascular state. Since the
calibration constant of this method is derived from demographic variables and then held
fixed, correcting it with a continuously available vascular marker is an intuitive and
frequently suggested remedy.

We report that the premise underlying that remedy does not hold. In 874 surgical cases
from a public perioperative waveform database, the within-case variation of pulse-wave
transit time was largely unexplained by simultaneously measured photoplethysmographic
indices of arterial stiffness and wave reflection.

Three features of the study may be of particular interest to your readers:

1. The primary analysis uses no reference cardiac output at all. Reference standards in
   open databases are predominantly derived from the arterial pressure waveform and are
   therefore not independent of the vascular state under study. We prespecified a
   reference-free test of the premise so that the principal conclusion does not depend on
   the quality of the reference.

2. We show that the null result is not a measurement failure. The indices retain
   substantial between-window autocorrelation, indicating that they track a reproducible
   physiological signal; identifiability of every index definition was established on
   synthetic pulses with known ground truth before any patient data were examined.

3. We document a processing delay of approximately 670 ms in the photoplethysmographic
   channel of this widely used database. Because it exceeds the cardiac cycle at higher
   heart rates, transit times computed without accounting for it are aliased rather than
   merely offset. We believe this is of immediate practical value to other groups using
   these data.

The analysis plan, including all index definitions and thresholds, was frozen before any
waveform was examined, and both the plan and the complete analysis code are publicly
available.

This manuscript is original, has not been published elsewhere, and is not under
consideration by another journal. [[All authors have approved the submission and declare
no conflicts of interest.]] The institutional ethics committee determined that review was
not required, as the study used only anonymised, publicly released data.

We hope you find the work suitable for [[JOURNAL]] and look forward to your response.

Yours sincerely,

[[Nobumitsu Kawazoe, MD]]
Department of Anesthesiology, [[Goto Chuoh Hospital]], Nagasaki, Japan
[[email]] / ORCID [[xxxx-xxxx-xxxx-xxxx]]
```

**書くときの注意**
- 陰性であることを隠さない。隠すと査読で必ず露見し、心証を悪くする
- 「前提が成り立たなかった」＝**情報のある陰性**である点を前面に出す
- 装置遅延の発見は**他の研究者への実利**として売る。エディタは実用性に反応する

---

## 2. 投稿までのチェックリスト

### 結果が出たら（解析完了後）

- [ ] 874例の結果を Results に反映（表1〜5、図1〜4）
- [ ] パイロット15例を除外した感度解析を実施し、結論が変わらないことを確認
- [ ] 非FloTrac部分集合（29例）の記述統計
- [ ] 代替指標定義（立ち上がり間ΔT・a₂/a₁・面積比）の感度解析
- [ ] §7.6 の解釈規準に照らして結論を確定（**規準は事後に変えない**）

### 原稿の整備

- [ ] Abstract を最後に書く（構造化・語数は投稿先規定に合わせる）
- [ ] 参考文献を投稿先の書式に整形（引用管理ソフトを使う）
- [ ] 図を投稿先の解像度規定に合わせて書き出し（通常 300–600 dpi、TIFF/EPS）
- [ ] 白黒印刷でも読める配色にする（色覚多様性への配慮も兼ねる）
- [ ] 語数・図表数が投稿先の上限内か確認

### 添付書類

- [ ] **STROBE チェックリスト**（観察研究の報告基準。多くの誌で必須）
- [ ] 事前登録の記述（SAP v0.3 を凍結した日付とGitHubのコミットを引用できる形に）
- [ ] データ利用可能性の記述（下記定型文）
- [ ] 倫理の記述（下記定型文）
- [ ] COI申告書（全著者）
- [ ] ORCID の取得と登録

### 投稿前の最終確認

- [ ] **英文校正**（非母語話者・初投稿では必須。掲載料ゼロの誌を選ぶ分、ここに費用を回す）
- [ ] 共著者・謝辞の確定（解析を単独で行った場合も、助言者は謝辞に）
- [ ] プレプリント（medRxiv・無料）を出すかどうかを投稿先規定で確認して決める
- [ ] 推薦査読者の候補を3〜5名（esCCO・PWTT・PPG脈波解析の著者から）

---

## 3. 定型文

### 倫理

```
This study analysed only anonymised data that are publicly available without
restriction. The institutional ethics committee of [[Goto Chuoh Hospital]] was consulted
and determined that review by the committee was not required (response dated 28 August
2026). The original database was approved by the Institutional Review Board of Seoul
National University Hospital, and the requirement for written informed consent was waived
by that board. [[出典: VitalDB の原著論文の記載に合わせて確認・調整する]]
```

### データおよびコードの利用可能性

```
The data analysed in this study are publicly available from VitalDB
(https://vitaldb.net). The complete analysis code, the prespecified statistical analysis
plan and the synthetic-data verification suite are available at [[GitHub URL]].
```

> **注意**: リポジトリは現在公開設定。投稿時にURLを示す前提なら公開のままでよいが、
> 個票データ（`analysis/data/`）は`.gitignore`で除外されており**公開されていない**ことを
> 確認済み。この状態を維持する。

### 資金

```
This research received no specific grant from any funding agency in the public,
commercial, or not-for-profit sectors.
```

### 著者貢献（単著の場合）

```
[[NK]] designed the study, wrote the analysis code, performed the analysis and wrote the
manuscript.
```

---

## 4. リジェクトされた場合の動き方

1. **査読前リジェクト（エディタキック）** → 次の誌へ即転送。原稿はほぼそのまま、
   カバーレターだけ書き直す。落ち込む必要はなく、スコープ不一致が理由のことが多い
2. **査読つきリジェクト** → 査読コメントは**次の投稿での最大の資産**。
   指摘を反映してから次へ出す。同じ指摘で二度落ちないようにする
3. **大幅修正（major revision）** → 原則すべての指摘に一つずつ回答する。
   同意できない指摘にも根拠を示して丁寧に反論してよい（黙殺だけは避ける）

---

## 5. Zenodo で事前登録に第三者DOIを付ける手順（無料・約10分）

GitHubのコミット履歴だけでは「事後に書き換えていない」ことの第三者証明として弱い。
Zenodo（CERN運営・無料）でリポジトリのスナップショットにDOIを発行する。

1. https://zenodo.org を開き **「Sign in with GitHub」** でログイン
2. 右上メニュー → **GitHub** ページで `nobumitsu-3141/ppg-study` のスイッチを **ON**
3. GitHubのリポジトリページ → **Releases → Draft a new release**
   - Tag: `sap-v0.3`（作成済み。SAP凍結コミット 407f226 を指す）
   - Title: `SAP v0.3 (frozen measurement pipeline)`
   - 説明: Statistical analysis plan frozen on 2026-08-28 (commit 407f226),
     before the confirmatory analysis. Archived for timestamping.
   - **Publish release**
4. 数分後にZenodoが自動アーカイブし **DOI (10.5281/zenodo.XXXXXXX)** を発行
5. 原稿 §2.1 の `[[Zenodo DOI; commit hash; 28 August 2026]]` に記入

注意: DOI発行日は今日になるが、タグの指すコミット日付とGitHub履歴が凍結日を
裏づける。原稿には「frozen on 28 August 2026 (commit 407f226; archived at doi:...)」
と正確に書く。

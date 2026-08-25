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

## VitalDB（事前①）の実行順

※ 事前に vitaldb.net でアカウント登録・利用規約に同意（P0-1）、
   倫理委員会への該当性照会の回答を確認（P0-2）してから。

```bash
python3 scripts/00_download_lists.py   # 症例・トラック一覧の取得
python3 scripts/01_track_inventory.py  # P1-1: 装置別CO×波形の保有集計（552例の再現）
python3 scripts/02_fetch_case.py 1     # P0-3: 1症例で波形取得→PDA→PWTTの動作確認
```

引用要件: Lee HC, et al. *Sci Data* 2022;9:279（PMID 35676300, DOI 10.1038/s41597-022-01411-5）。

## 構成

| ファイル | 内容 |
|---|---|
| `src/pda.py` | skewed-Gaussian 2カーネルのPDA。ランドマーク初期値（5.3-a）＋dmuグリッド多点スタート（5.3-c）＋収束検算（境界張り付き・振幅ゼロ・競合解の曖昧さ・残差の谷幅） |
| `src/indices.py` | 成分波からの ΔT・RI・SI、ECG＋脈波からの PWTT |
| `src/beats.py` | 拍切り出し・SQI v0・アンサンブル平均 |
| `src/synth.py` | 真値既知の合成PPG（切痕あり／DN-less） |
| `tests/test_pda_synthetic.py` | C-4 の検証（上記結果を再現） |
| `scripts/00〜02` | VitalDB のデータ取得と P1-1 集計（要インターネット。クラウドセッションからは vitaldb.net に接続不可のためMacで実行する） |

## 注意

- `data/` はダウンロードした公開データ置き場。**リポジトリにはコミットしない**（.gitignore済み）。
- SQI閾値・除外基準は Phase 2 で実データを見て確定し、確定値は統計解析計画（docs/research/sap_v0.md）に固定する。
- 参照COの装置内訳（FloTrac系＝動脈圧由来／Vigilance II＝肺動脈カテ熱希釈）は解析で区別する。

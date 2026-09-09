# リポジトリの分離と Zenodo DOI ― 手順と、実行前に知っておくこと

## 現状（2026-09-09 に GitHub API で確認）

`nobumitsu-3141/ppg-study` は**公開**で、**GitHub Pages が有効**である（`index.html` が
サイトとして配信されている）。

**既定ブランチ `main` には `docs/` も `analysis/` も無い。**文献レビューのハブ（ルートの
HTML・Markdown と `local-reviews/`・`refs/`）だけである。原稿・実験ノート・倫理文書・
依頼書は**作業ブランチ `claude/slide-references-formatting-ynthk7` にしか無い。**
したがって履歴の全面的な書き換えは要らない。

## ★ 先に対処が要るもの（分離とは別の問題）

**`local-reviews/PI_summary_anesthesia.html` が `main` にあり、公開サイトとして配信されている。**
この文書には**第三者の実名・所属・その方の研究の内容**が含まれる。

    新谷 亮祐（長崎大学麻酔科 助手）
    単施設前向き探索的研究（長崎大学病院）

**対処済み（2026-09-09）。**著者の指示により削除した。

- `main` から当該ファイルを削除（コミット `9759c0b`）。**公開サイトからは消えた。**
- 文献地図（`refs/PPG_literature_map_all_chapters.html`）の参照行も削除し、
  同じ行に併記されていた別ファイルの目録だけを戻した。
- 作業ブランチの実体も削除した。

**残る論点: 履歴には残っている。**`git log` を辿れば読める。完全に消すには
`git filter-repo` で履歴を書き換え、force-push したうえで GitHub に
キャッシュの破棄を依頼する必要がある。**複製された分までは消せない。**
公開期間は 2026-08-18 頃から 2026-09-09 まで（ファイルの作成日時から推定）。
本人への連絡が要るかどうかを含め、判断は著者が行う。

## 分離の設計

| リポジトリ | 公開 | 中身 |
|---|---|---|
| `ppg-study`（現行） | 公開のまま | 文献レビューのハブ。Pages はここが配信する |
| `ppg-pda-analysis`（新規） | **公開** | 解析コードと凍結した事前登録。**Zenodo DOI はこれに付ける** |
| `ppg-study-private`（新規） | **非公開** | 原稿・実験ノート・倫理文書・依頼書・報告書・スライド |

**新しい公開リポジトリは履歴を作り直す。**現行の作業ブランチの過去の版に機微な資料が
入っているためである。

## 手順

```sh
bash tools/split_repos.sh ~/ppg-split
```

機微な語の検査が通ることを確認する。次に GitHub 上で 2 つのリポジトリを作り、
それぞれで初回コミットを作る。

```sh
cd ~/ppg-split/ppg-pda-analysis
git init -b main && git add -A
git commit -m "初回: 解析コードと凍結した事前登録"
git remote add origin git@github.com:nobumitsu-3141/ppg-pda-analysis.git
git push -u origin main

cd ~/ppg-split/ppg-study-private
git init -b main && git add -A
git commit -m "初回: 原稿・実験ノート・倫理文書"
git remote add origin git@github.com:nobumitsu-3141/ppg-study-private.git
git push -u origin main
```

そのうえで、**現行リポジトリの作業ブランチをリモートから消す。**

```sh
git push origin --delete claude/slide-references-formatting-ynthk7
```

**この操作の前に、上の 2 つの push が終わっていることを必ず確かめること。**
作業ブランチには本研究のすべてが入っており、消すと GitHub 側の控えが無くなる。

## Zenodo DOI

**この作業には Zenodo へのログインが要るので、著者が行う。**

1. <https://zenodo.org> に GitHub アカウントでログインする。
2. 設定の GitHub 連携で `ppg-pda-analysis` の**スイッチを入れる**。
   （スイッチを入れた**後**に作ったリリースだけが Zenodo に取り込まれる。）
3. GitHub でリリースを作る。タグは `v1.0.0` のように付ける。
4. 数分で Zenodo に登録され、**版ごとの DOI と、全版を指す concept DOI** が発行される。
5. `CITATION.cff` に `doi:` と `version:`、`date-released:` を書き足して push し、
   次のリリースからは自動で反映されるようにする。
6. 論文の Data availability に **concept DOI** を書く（版が増えても指し先が変わらない）。

`.zenodo.json` は用意してある。**ORCID は入れていない。**取得しているなら
`.zenodo.json` の `creators[0].orcid` と `CITATION.cff` の `orcid:` に足すこと。
査読誌によっては著者識別子を求められる。

## ライセンスについて（確認が要る）

現行の `LICENSE` は **CC BY 4.0** で、文書には適切だが**コードの慣行ではない**。
特許の扱いと派生物の条件が明確でないため、コードを再利用する側が判断に迷う。
公開する解析リポジトリには **MIT** か **Apache-2.0** を当てるのが通例である
（Apache-2.0 は特許条項を含む）。**文書とコードでライセンスを分けるのが最も素直**で、
`ppg-pda-analysis` のコードを MIT、同梱する事前登録の文書を CC BY 4.0 とする形にできる。
**この判断は著者が行う。**現状は CC BY 4.0 のまま複製してある。

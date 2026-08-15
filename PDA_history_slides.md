# PDA の歴史スライド（第5章 5.1 の直後に追加）

PPG 講義デック（`PPG_7.2_PDA_history.pptx`）の第5章「PDA（波形分解）」に、
**PDA の理論的な源流（医学以外の分野）** と **医療分野への応用の歴史** を扱う
スライド3枚と、それに対応する参考文献スライド1枚を追加した記録。

- 挿入位置：`5.1 PDA とは`（順番45枚目 / p.45）の直後
- 解説レベル：大学入学レベル（前提知識を仮定しない）
- 書式：既存デックの体裁を踏襲（タイトル46pt・本文22pt以上・Meiryo・右上章ナビ・出典行）
- ページ番号：総ページを 68 → 72 に更新し、挿入位置以降を +3 で振り直し
- 章扉（p.44）の小見出しを `5.1 PDA とは` → `5.1 PDA とは・歴史` に更新

配色は既存の色覚セーフ配色を踏襲した。ブルー `0072B2` ＝ 医学の外、
バーミリオン `D55E00` ＝ 医療（PPG）、ティール `00A8AA` ＝ 計算の道具、
ゴールド `BF9000` ＝ 構造色（まとめ帯）。

---

## p.46 「5.1 源流は医学の外」

「重なった波を成分の山の足し算に分ける」という発想は医学由来ではなく、
数学・物理・地球物理・分析化学で先に確立している、という趣旨。カード4枚。

| 年 | 分野 | 事項 | スライド上の一行説明 |
|---|---|---|---|
| 1805 | 数学 | 最小二乗法（Legendre） | 実測に最もよく合う数値を選ぶ |
| 1822 | 物理 | フーリエ解析（Fourier） | 波は単純な波の足し算で表せる |
| 1957 | 地球物理 | 地震波の分解（Robinson） | 記録を反射の重ね合わせと読む |
| 1966 | 分析化学 | 重なった山の分離（Fraser & Suzuki） | 分光のピークを成分に分ける |

まとめ帯：**「波を成分の山に分ける」道具は 医学の外で完成していた**

補足（ノートに記載）：

- Legendre の最小二乗法は 5.3「当てはめの計算」で最小化している残差平方和そのもの。
  Gauss も 1809 年に独立して発表している。
- Robinson の predictive deconvolution は「反射の重ね合わせを分解して反射の時刻を読む」
  という点で PDA と同型の問題。
- Fraser & Suzuki が導入した非対称ガウス型関数（Fraser–Suzuki 関数）は、
  Basso 2024 の skewed-Gaussian（文献44 / 5.5⑦）と同じ発想。

## p.47 「5.1 当てはめの道具」

分解の発想があっても、実際に数値を求める手段がなければ使えない。その手段も
医学の外で用意された、という趣旨。カード2枚＋まとめ帯。

| 年 | 事項 | 役割 |
|---|---|---|
| 1944・1963 | Levenberg–Marquardt 法 | 非線形の当てはめを反復で解く／高さ・位置・幅を自動で決める |
| 1974 | 赤池情報量規準 AIC | 成分波を何本使うかを選ぶ／モデル選択の一般的な基準 |

まとめ帯：**この2つで 山の高さ・位置・幅 が機械的に求まる／
PPG の PDA も この一般的な道具立ての上に成り立つ**

Tigges 2017（文献43）は補正版の AICc を用いて基底関数と次数を総当たり比較している。
逆にいえば AIC が選ぶのは「データをよく説明する」モデルであって
「生理学的に正しい」モデルではなく、5.6 の限界①②に直結する。

## p.48 「5.1 医療応用の歴史」

圧波形の時代（圧と流量の実測が必要）→ PPG の時代（光の1信号のみ）という
2相構成の年表。行ごとに `圧波形` / `PPG` のチップを付け、色と併せて冗長に区別。

| 年 | 区分 | 内容 |
|---|---|---|
| 1899 | 圧波形 | Frank：動脈系を Windkessel で数式化 |
| 1972 | 圧波形 | Westerhof：圧波形を前進波と後退波に分離 |
| 1990 | 圧波形 | Parker：波の強さから反射の時刻を解析 |
| 2008 | PPG | Rubins：PPG をガウス関数の和に当てはめ（文献40） |
| 2011 | PPG | Baruch：動脈脈波を5つの成分波に分解（PDA の呼称） |
| 2012〜 | PPG | Couceiro・Tigges ら：PPG での PDA が本格化 |

まとめ帯：**圧と流量の実測が要った分離を PPG 1 本で行うのが PDA**

Westerhof 以来の「前進波と後退波に分ける」作業は、本来は圧と流量という2つの実測を
必要とした。PDA はそれを PPG という1本の信号だけで行おうとするもので、
だからこそ解が一意に決まらないという限界（5.6）を抱える。

Baruch 2011 は、末梢動脈脈波を5つの成分波（第1波は左室駆出、残りは中心動脈にある
2か所の反射部位からの反射・再反射）の重ね合わせとみなす手法を
Pulse Decomposition Analysis (PDA) と呼び、下半身陰圧による出血模擬で
第1・第3成分波の時間差 T13 と脈圧の関係を検討した。

## p.72 「参考文献（5）」

追加した文献（番号は既存リストの続き）。

48. Legendre AM. Nouvelles méthodes pour la détermination des orbites des comètes. Paris: Firmin Didot; 1805.
49. Fourier J. Théorie analytique de la chaleur. Paris: Firmin Didot; 1822.
50. Robinson EA. Predictive decomposition of seismic traces. Geophysics 1957;22:767–78.
51. Fraser RDB, Suzuki E. Resolution of overlapping absorption bands by least squares procedures. Anal Chem 1966;38:1770–3.
52. Levenberg K. A method for the solution of certain non-linear problems in least squares. Q Appl Math 1944;2:164–8.
53. Marquardt DW. An algorithm for least-squares estimation of nonlinear parameters. J Soc Ind Appl Math 1963;11:431–41.
54. Akaike H. A new look at the statistical model identification. IEEE Trans Automat Contr 1974;19:716–23.
55. Frank O. Die Grundform des arteriellen Pulses. Z Biol 1899;37:483–526.
56. Westerhof N, Sipkema P, van den Bos GC, Elzinga G. Forward and backward waves in the arterial system. Cardiovasc Res 1972;6:648–56.
57. Parker KH, Jones CJH. Forward and backward running waves in the arteries: analysis using the method of characteristics. J Biomech Eng 1990;112:322–6.
58. Baruch MC, et al. Pulse Decomposition Analysis of the digital arterial pulse during hemorrhage simulation. Nonlinear Biomed Phys 2011;5:1.

---

## 検証

- `validate.py --original`（OOXML スキーマ・関係・コンテンツタイプ）：PASSED
- 川副式 `slide_lint.py`：総違反件数が元デック（96枚）と同一の 339 件。
  追加した4枚が新たに出した違反は 0 件（FONT<22・枠外・折返し・重なり いずれも 0）。
- 実寸の目視確認は本番 PowerPoint（メイリオ）で行うこと。
  作業環境に LibreOffice の Impress フィルタがなく、描画による確認ができないため、
  テキストボックスはメイリオ想定の安全係数（幅 ×1.12・行高 ×1.18）で余裕を持たせてある。

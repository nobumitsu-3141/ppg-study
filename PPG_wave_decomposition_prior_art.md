# 反射波の数学的分離から SI・RI を再計算する ― 先行技術調査

**先行技術調査と、新規性がどこに残っているかの確定**

本プロジェクトは、光電容積脈波を前進波と反射波の重ね合わせとしてモデル化し、そのパラメータからスティフネス指数 SI と反射指数 RI を定義し直して血圧・血管抵抗と対比する、という設計を立てていた。本稿はその設計に対する事前技術調査である。結論から言えば、**中核のアイデアは既出であり、血圧・総末梢血管抵抗との対比まで 2015 年に実施済み**である。

検索実施：2026-08-05 ／ データベース：PubMed（NCBI E-utilities）／ 収載 25 文献

---

## 結論

- **分解した反射波のピーク高から RI を計算した報告**は複数ある。最初期は Rubins 2008 で、ガウス当てはめから反射指数 RI とオーグメンテーション指数 AI を算出し、微分法と比較している。
- **分解した反射波のピーク時刻から SI を計算した報告**もある。Goswami 2010 が 2 波合成モデルから SI・RI・脈波伝播速度を明示的に導出している。
- **それを血圧・血管抵抗と対比した報告**もある。Couceiro 2015 が 5 ガウス分解から SI・RI・時間差・振幅比を算出し、血圧と総末梢血管抵抗係数に対比している。しかも**振幅比はすべての参照値と低相関**という結果である。

したがって、**「推定式で SI・RI を計算し直し、血圧・SVR との関連を調べる」という設問そのものに新規性はない。** 残っている空白は、指標の定義ではなく**検証の条件**の側にある（§9）。

---

## 1. 本稿の目的

本リポジトリの設計原則の一つに「エビデンスの強さを均一に扱わない」がある。同じ精神を、自分たちの提案そのものにも向ける必要がある。すなわち**「未検証である」ことと「未提案である」ことは別の軸**であり、前者だけを確認して後者を確認しないまま新規性を語ってはならない、ということである。

本稿は、本プロジェクトが立てていた次の設問に対する事前技術調査である。

> 光電容積脈波の一拍を複数の基底関数の和としてモデル化し、第一成分を前進波・第二成分を反射波と対応づけたうえで、そのパラメータから SI（＝身長 ÷ 時間差）と RI（＝振幅比）を定義し直す。そして血圧・全身血管抵抗との関連を調べる。

この設問は**既に複数回実施されている**。

---

## 2. 検索の方法

データベースは PubMed（NCBI E-utilities の esearch／esummary／efetch）。検索実施日は 2026 年 8 月 5 日。題名・抄録フィールド（`[tiab]`）に対して以下の検索式を用い、得られた文献の抄録を確認して選別した。

```
"pulse decomposition analysis"[tiab]
"multi-Gaussian"[tiab] AND (photoplethysmog*[tiab] OR PPG[tiab] OR pulse[tiab])
photoplethysmog*[tiab] AND decompos*[tiab] AND reflect*[tiab]
photoplethysmog*[tiab] AND Gaussian[tiab]
(photoplethysmog*[tiab] OR PPG[tiab]) AND "reflection index"[tiab]
(photoplethysmog*[tiab] OR PPG[tiab]) AND "stiffness index"[tiab] AND (fitting[tiab] OR model*[tiab] OR decompos*[tiab])
(photoplethysmog*[tiab] OR PPG[tiab]) AND ("vascular resistance"[tiab] OR "peripheral resistance"[tiab])
    AND (Gaussian[tiab] OR decompos*[tiab] OR "wave separation"[tiab])
(photoplethysmog*[tiab] OR PPG[tiab] OR plethysmog*[tiab]) AND (decompos*[tiab] OR Gaussian[tiab] OR "curve fitting"[tiab])
    AND (anesthes*[tiab] OR anaesthes*[tiab] OR intraoperative[tiab] OR perioperative[tiab] OR vasopressor*[tiab])
("stiffness index"[tiab] OR "reflection index"[tiab]) AND (photoplethysmog*[tiab] OR "digital volume pulse"[tiab])
    AND ("systemic vascular resistance"[tiab] OR "total peripheral resistance"[tiab])
```

最後の 2 式は「周術期での分解由来指標」という本プロジェクトの関心そのものを狙ったもので、それぞれ **3 件**と **7 件**しか該当せず、**分解由来の SI・RI を全身血管抵抗と対比した研究は 1 件も無かった**。この空振りが、§9 で述べる空白の根拠になっている。

---

## 3. A 群 ― 分解由来の SI・RI を直接扱った研究

本プロジェクトの設問と正面から重なる群である。**新規性を否定するのはこの 7 件**である。

| 文献 | P（対象） | I（解析手法・指標） | C（比較対照） | O（結果） |
|---|---|---|---|---|
| **Rubins 2008**<br>PMID 18855034 | 健常者 40 名。指と耳の光電容積脈波を同時記録し、拍ごとに解析 | 収縮期波と拡張期波を分離し、それぞれを 2 つのガウス関数の和で当てはめ。直達波と 3 つの反射波の時刻、**オーグメンテーション指数 AI と反射指数 RI** を算出 | 同一波形から微分法で求めた同じ指標 | ガウス当てはめ法で従来の微分法と同等に波形解析が可能であることを示した。**「分解由来の RI」はここが最初期** |
| **Goswami 2010**<br>PMID 20734136 | 健常者および治療中の高血圧者から得た指尖容積脈波 113 信号 | Rayleigh 関数による 2 波合成（TPS）モデル。**反射指数 RI・スティフネス指数 SI・脈波伝播速度・立ち上がり遅延を導出**し、新指標 DPS を提案 | 従来のランドマーク／微分法で求めた同指標 | TPS モデルは従来法とよく一致。**「分解由来の SI」もここで既に揃っている** |
| **Couceiro 2015**<br>PMID 26235798 | ① 健常＋心血管疾患 68 名（駆出時間の検証）　② 循環動態が不安定な 43 名（血圧・血管抵抗の検証） | 5 ガウス分解。SI・RI に加え、**T1_d・T1_2（モデルの前進波と反射波の時間差）**、**R1_d・R1_2（その振幅比）**を算出 | 心エコーによる左室駆出時間／血圧・**総末梢血管抵抗係数 TPRI** の参照値 | 駆出時間の絶対誤差 15.41 ± 13.66 ms（ρ = 0.78）。**最高相関は T1_2 と TPRI の ρ = 0.45**。**R1_2 はすべての参照値と低相関**。失神例では SI と収縮期・平均血圧が ρ = 0.57 |
| **Grabovskis 2015**<br>PMID 25751027 | 若年健常者 14 名。大腿動脈部の光電容積脈波（波長 880 nm） | 二段階の多ガウス当てはめ。カフを 0・40・80・200 mmHg で加圧し、片側の局所血管抵抗と動脈スティフネスを段階的に上昇させる | 同時記録した血管超音波（径・血流線速度）と Finapres 動脈圧、および加圧前のベースライン | 加圧の増大に伴い、**反射波と直達波の遅延が短縮し、両者の振幅比が増大**した |
| **Wang A 2018**<br>PMID 28347756 | 健常者 65 名（女性 18・男性 47）の指尖光電容積脈波 | 幅と振幅を正規化した波形を 3 つのガウス波に分解し、9 パラメータと、**時間差 T1,2・T1,3** および**振幅比 R1,2・R1,3** を算出 | 運動負荷 0・50・75・100・125 W の各段階と、その後 4 分間の回復相 | 負荷増大とともに H2・N1–N3・W1–W2 が増加し H3 が減少（P < 0.05）。T1,2 は安静時 10.6 ± 1.2 から 100 W で 14.4 ± 2.3 へ延長（正規化値） |
| **Park 2022**<br>PMID 35297776 | 参加者 757 名から取得した光電容積脈波 | ガウス混合モデルで各拍を**入射波と反射波に分解**し、基本 26・合成 52 の特徴量を定義。人工ニューラルネットで回帰 | 実年齢（血管年齢の代理） | **反射波の振幅由来の特徴量**と波形の歪度が実年齢と比較的強く相関。推定の二乗平均平方根誤差は 10.0 年 |
| **Baruch 2014**<br>PMID 25005686 | 心臓カテーテル検査を受ける患者 63 名（男性 38・女性 25、平均 62.7 歳） | Pulse Decomposition Analysis。末梢動脈圧脈を 5 成分の重ね合わせと見なす。**振幅比 P2P1 と時間差 T13** | 中心ラインカテーテルで実測した中心動脈圧 | 中心動脈で 5 成分を直接観察。**P2P1 と収縮期圧、T13 と脈圧に有意な相関**（収縮期 R² = 0.92、拡張期 R² = 0.78、P < 0.0001） |

> **この表が意味すること** ― 「点を探すのをやめ、波を当てはめる」という発想の転換も、そこから SI・RI を作り直すことも、血圧・血管抵抗と対比することも、すべて既に行われている。2008 年に RI が、2010 年に SI と RI が揃い、2015 年には血圧と総末梢血管抵抗係数への対比まで終わっている。さらに、成績が芳しくない。Couceiro 2015 で最も期待された**振幅比 R1_2 ―― すなわちモデル由来の RI ―― は、すべての参照値と低い相関しか示さなかった**。時間側の T1_2 ですら ρ = 0.45 である。本プロジェクトが「時間の軸を優先する」という設計原則を独立に導いていたことは正しかったが、その時間の軸ですら既に試されて中程度にとどまっている。

---

## 4. B 群 ― 分解モデルそのものの方法論

「どの基底関数を、いくつ使うか」を扱う群。ここを読むと、**モデル選択が決着していない**ことがわかる。これは裏を返せば、逆問題が一意に解けていないことの表れである。

| 文献 | P（対象データ） | I（提案手法） | C（比較対照） | O（結果） |
|---|---|---|---|---|
| **Wang L 2013**<br>PMID 24209911 | 実測の脈波（1 周期分） | ガウス波の個数を**適応的に 4 または 5 個**とする多ガウスモデル。重み付き最小二乗で推定し、重みを多基準意思決定法で選択 | 固定個数（3・4・5 個）で分解する従来の各手法 | 脈波の特徴点位置の推定誤差に着目し、従来法が誤差を軽視していた点を改善したと主張 |
| **Tigges 2017**<br>PMID 29060777 | 想定しうる波形形態を網羅した指尖容積脈波 **7,805 拍** | 4 種類の基底関数と妥当な範囲のモデル次数で分解し、修正赤池情報量規準（AICc）でモデル選択 | 基底関数の種類とカーネル数の総当たり | **3 個の Gamma 基底関数の線形重ね合わせ**が最良として最も多く選択された（該当割合は原著参照）。ガウス関数が唯一の正解ではない |
| **Fleischhauer 2020**<br>PMID 33021236 | 撮像光電容積脈波（PPGI）の模擬データおよび実測データ | 既出の各種脈波分解アルゴリズムを、ノイズ・体動耐性と形態情報の保存という観点で比較 | 基底関数の種類（Gamma／Gaussian／両者の組合せ）とカーネル数 | **Gamma と Gaussian の組合せが優位**。**カーネル 2 個**がノイズ・体動に最も頑健（14.09% の改善）で、形態保存も多カーネルと同等 |
| **Basso 2024**<br>PMID 39577084 | MIMIC-III 波形データベースの光電容積脈波 **8,000 拍** | 非対称な形態を表現できる **skewed-Gaussian モデル**を提案。残差二乗和・Bland–Altman・初期値ランダム化で評価 | 参照となる Gamma–Gaussian モデル | 参照モデルより有意に高精度。**初期値の選び方に対する感度が低く一貫して頑健**。逆に言えば従来モデルは初期値で答えが動く |
| **Sorelli 2018**<br>PMID 29993447 | 健常・非喫煙者 54 名のレーザードップラー血流信号から得た脈波 **20,935 波形** | 多ガウス分解で得た輪郭特徴を入力とするサポートベクターマシンで血管年齢を分類 | 被験者の実年齢 | 当てはめは平均 R² = 0.98。30 回の学習・検証で相関 r = 0.808、平均 AUC 0.953 |

---

## 5. C 群 ― 圧波形での波分離（流量を代用する系譜）

古典的な波分離は圧と流量の両方を必要とする。流量を何かで代用する試みの系譜であり、**多ガウス分解はこの文脈でも既に「流量を要らなくする手段」として使われている**。

| 文献 | P（対象） | I（手法） | C（比較対照） | O（結果） |
|---|---|---|---|---|
| **Westerhof 2006**<br>PMID 16940207 | ヒト大動脈圧波形 | 実測流量の代わりに**三角形で近似した流量波形**を用いて波分離を行う | 実測流量を用いた古典的波分離 | 校正されていない大動脈圧のみからでも反射の定量が可能であるとの原理実証 |
| **Kips 2009**<br>PMID 19075098 | Asklepios 研究の参加者 **2,500 名超**（35〜55 歳） | 三角近似流量、およびより生理的な形状の流量波形を用いた反射量・伝播時間の推定 | 実測圧＋実測流量による参照値、Doppler 超音波による頸大腿伝播時間 | 反射量の一致は三角近似で R² = 0.55、生理的流量波形で R² = 0.74。大動脈伝播時間は R² < 0.29 |
| **Manoj 2021**<br>PMID 34892381 | 動脈系の脈波（圧・径波形） | **多ガウス分解による前進波・後進波の分離**。単一の脈波だけで済む点を新規性として主張 | 三角波形にもとづくインピーダンス法 | 単一波形から前進・後進成分の分離に成功したと報告 |
| **Manoj 2022**<br>PMID 35537402 | 健常仮想被験者データベース。頸動脈という**非大動脈部位** | 重み付き・時間シフトした多ガウスで圧波形を分解し組み替えて前進圧波と後進圧波を得る（MGDWSA）。流量は不要 | 流量にもとづく参照波分離法 | 当てはめ RMSE < 0.35 mmHg、前進・後進波の群平均 < 2.5 mmHg。脈圧 r > 0.96、反射定量指標 r > 0.83、バイアスは有意でない |
| **Guberti 2025**<br>PMID 40014240 | 5 日間の敗血症モデル動物 | 動脈圧から動脈血流を推定する自己回帰外生入力（ARX）モデルを提案 | 三角近似、個別化した生理的流量波形、**多ガウス圧分解** | 敗血症下では**ブラックボックス型のモデル化が他の流量推定法より優れていた** |

---

## 6. D 群 ― SI・RI の原典と、妥当性への異論

| 文献 | P（対象） | I（手法・指標） | C（比較対照） | O（結果） |
|---|---|---|---|---|
| **Millasseau 2002**<br>PMID 12241535 | 無症状の被験者 87 名（21〜68 歳、女性 29 名） | 指尖容積脈波の**直達波と反射波の時間差**と被験者身長から SI_DVP を定義 | 頸大腿脈波伝播速度、ニトログリセリン投与前後 | SI の原典。被験者内変動係数は小さく個人内追跡には十分。集団内で個人を序列づけるには相関が不足する |
| **Chowienczyk 1999**<br>PMID 10588217 | 2 型糖尿病患者および対照 | 指尖容積脈波の変曲点位置を最大振幅に対する比として表した反射指数（IP_DVP） | アルブテロールとニトログリセリンの局所・全身投与、Doppler による大動脈伝播時間 | RI の原典。硝酸薬は反射を減じて変曲点位置を下げる。**内皮依存性の反応が 2 型糖尿病で鈍化** |
| **Epstein 2014**<br>PMID 25570367 | 手の主要動脈を含む **75 本の動脈網**を表現した非線形 1 次元脈波伝播モデル | 壁スティフネス・末梢抵抗・末梢コンプライアンス・末梢反射を個別に変化させ、模擬した指尖の面積波形から SI を算出 | 同一モデルから得た大動脈脈波伝播速度 aPWV | **SI は aPWV の直接の代用ではない**。さらに**第 2 ピークは末梢反射ではなく動脈網内部のインピーダンス不整合が主因**であり、上肢の末梢反射はむしろ**第 1 ピークの到達時刻を遅らせる** |

> **分解が上手くいっても解釈は保証されない** ― Epstein 2014 の指摘は、本プロジェクトの手法が前提にしている物理的帰属そのものを揺さぶる。**「2 番目の山＝末梢からの反射波」というラベルは自明ではない。** 当てはまりの良さがいくら改善しても、この帰属が誤っていれば、そこから作った RI・SI の生理学的意味は変わってしまう。検証設計としては、**真値が既知の仮想被験者による検証を先に置くべき**だという結論になる。

---

## 7. E 群 ― 周術期における PPG 形態解析

周術期に PPG の形から循環を読む試みは存在する。しかし**そのいずれも、分解由来の SI・RI を血管抵抗と対比してはいない**。

| 文献 | P（対象） | I（手法） | C（比較対照） | O（結果） |
|---|---|---|---|---|
| **Coutrot 2019**<br>PMID 30916032 | プロポフォール・レミフェンタニルの目標制御導入を受ける 61 名 | 1 分間隔で平均動脈圧・**相対的重複切痕高比 Dicpleth**・灌流指数 PI を記録（**ランドマーク法**であり分解ではない） | 術中低血圧（平均動脈圧の 20% 超の低下）の発生、昇圧薬ボーラス投与の前後 | Dicpleth と PI の相対変化が術中低血圧を精度よく検出し、昇圧薬への血管反応の追跡にも使えるとする原理実証 |
| **Aguet 2023**<br>PMID 36735652 | 麻酔導入時の患者 | oBPM で前処理・特徴抽出、Lasso で特徴選択、3 種の機械学習で血圧を推定（**分解由来の SI・RI ではない**） | 参照血圧、従来の oBPM 技術 | 収縮期血圧推定の誤差標準偏差を 20% 以上削減。急速な血圧変化の追随性も評価 |
| **Lee QY 2011**<br>PMID 21693795 | 集中治療室の異質な患者集団 48 名 | PPG 波形の特徴量と心拍数・平均動脈圧を入力に、ベイズ則の分類器で全身血管抵抗を 3 区分（< 900／900–1200／> 1200 dyn·s·cm⁻⁵）に分類（**分解ではない**） | 実測された全身血管抵抗の区分 | ガウス分布モデルで κ = 0.57、ノンパラメトリックモデルで κ = 0.51 |
| **Gratz 2017**<br>PMID 28327093 | 開腹大手術を予定された 24 名（パイロット研究） | Pulse Decomposition Analysis を用いる指カフ式連続非侵襲血圧計 CareTaker | 橈骨動脈カテーテルによる観血動脈圧、ANSI/AAMI/ISO 81060-2:2013 の許容基準 | **分解由来の指標が術中に実装され観血動脈圧と比較された唯一の系譜**。ただし評価対象は血圧であって SI・RI ではない |
| **Khanna 2024**<br>PMID 37458916 | 心臓外科術後 ICU 患者 41 名。259.7 時間、15,583 対の測定点 | 装着型無線 PDA デバイスで収縮期面積の積分と動脈スティフネス推定から心拍出量を算出 | 肺動脈カテーテルによる連続熱希釈心拍出量 | 分解由来の指標が**術後 ICU で熱希釈法と比較**された例。評価対象は心拍出量であって血管抵抗ではない |

---

## 8. F 群 ― 検証に用いる基盤データ・ツール

| 文献 | 内容 | 本プロジェクトでの用途 |
|---|---|---|
| **Charlton 2019**<br>PMID 31442381 | 25〜75 歳の心血管特性を文献レビューで同定し、それを入力として生成した**仮想被験者 4,374 名**の脈波データベース。圧・流速・内腔断面積・光電容積脈波を同時出力し、生成条件が既知 | **真値が既知の検証**。圧と流量が揃うため古典的波分離で前進波・反射波の参照値を計算でき、Epstein 2014 が提起した帰属の問題にも答えられる |
| **Lee HC 2022**<br>PMID 35676300 | VitalDB。手術患者 **6,388 症例**の高分解能多パラメータ生体信号。486,451 の波形・数値トラック | 実患者の周術期波形での検出成功率と再現性の評価 |
| **Goda 2024**<br>PMID 38478997 | pyPPG。特徴点検出器を **19,000 時間・9,100 万拍超**で検証し、標準化された 74 のバイオマーカーを実装 | 比較対象となる**ランドマーク法の実装**。分解法と同一の拍で直接対決させるための基準線 |

---

## 9. 読み取れること、そして残っている新規性

### 9.1 一覧から読み取れる 4 点

1. **中核のアイデアは 2008 年に既出である。** ガウス当てはめから RI を出す（Rubins 2008）、SI と RI を揃える（Goswami 2010）、血圧・総末梢血管抵抗と対比する（Couceiro 2015）という順で既に完結している。
2. **振幅側の成績が一貫して弱い。** Couceiro 2015 の R1_2 はすべての参照値と低相関だった。「タイミングを振幅より優先する」という本プロジェクトの原則は正しいが、その時間側でも ρ = 0.45 にとどまる。
3. **モデル選択が決着していない。** Gaussian・Gamma・skewed-Gaussian・Rayleigh、カーネル数も 2〜5 と割れており、研究ごとに「最良」が異なる。逆問題が一意に解けていないことの直接の表れであり、Basso 2024 の初期値依存性と同じ根を持つ。
4. **「第 2 ピーク＝末梢反射」という物理的帰属が、数値モデルからは支持されていない。** Epstein 2014 は第 2 ピークの主因を動脈網内部のインピーダンス不整合に帰し、SI が aPWV の代用ではないと結論している。

### 9.2 残っている新規性 ― 5 つの軸

新規性は**指標の定義ではなく、検証の条件**の側にしか残っていない。強い順に。

1. **周術期・全身麻酔下という設定。** 先行研究の対象は健常者・傾斜台・カフ圧迫・運動負荷・高血圧外来・血管年齢コホートである。**麻酔導入時や昇圧薬投与時に、分解由来指標が観血血圧と較正済み全身血管抵抗の変化を追随するかは未検証**。周術期に近い先行例（Coutrot 2019、Aguet 2023、Lee 2011、Gratz 2017、Khanna 2024）はいずれも設問がずれている。検索でも該当 0 件。
2. **退化した波形における「救済」という仮説そのもの。** 一峰性化・shoulder 化してランドマーク法が破綻する拍で、モデル法が値を返し**かつその値が血管抵抗と関連するか**を、**主要評価項目として事前規定した研究は見当たらない**。年齢層・スティフネス層別の検出成功率を主要アウトカムに置き、ランドマーク法（pyPPG 等）と同一の拍で直接対決させる設計であれば、Epstein 2014 の提起にも同時に答えられる。
3. **自動ゲイン制御と帯域制限のある実機モニタ波形での成立性。** 先行研究はすべて研究用 PPG か観血動脈圧である。臨床パルスオキシメータの表示波形で分解が安定に解けるかは、この構想全体の**必要条件**でありながら誰も確認していない。
4. **絶対値の相関ではなく、変化の追随性としての評価。** 先行研究はプールした相関係数を報告している。**昇圧薬で血管抵抗を動かしたときの変化方向の一致率**（concordance rate・polar plot）という評価軸は未実施であり、統計的要求も相関より緩い。Millasseau 2002 の「被験者内変動は小さいが被験者間の相関は不足する」という構造とも整合する。
5. **識別可能性を出力として報告すること。** Basso 2024 が初期値依存性を定量したところまでで、**拍ごとに振幅比と時間差の信頼区間を出し、識別不能な拍を事前規定で除外する**運用は標準になっていない。

---

## 10. 本プロジェクトへの帰結 ― 設問の書き換え

| | 設問 | 状態 |
|---|---|---|
| 調査前 | PPG を前進波と反射波に分解し、そのパラメータから SI・RI を定義し直して、血圧・全身血管抵抗との関連を調べる | **既出**（Rubins 2008／Goswami 2010／Couceiro 2015） |
| 調査後 | 既に提案されている分解由来指標を、**① 周術期・全身麻酔下**、**② 自動ゲイン制御と帯域制限のある実機波形**、**③ ランドマーク法が破綻する退化波形**という 3 つの未検証条件で評価し、ランドマーク法との直接対決および変化の追随性を主要評価項目として、**検証あるいは反証する** | **空白**（該当研究 0 件） |

> **設計上の含意** ― Couceiro 2015 の結果を踏まえると、**主要評価項目は振幅側ではなく時間側（前進波と反射波の時間差）に置くべき**である。事前確率は低めに見積もるのが妥当であり、**陰性結果でも情報価値が出る設計**にしておく必要がある。「分解由来指標は周術期の血管抵抗変化を追随しない」という結論であっても、本リポジトリの他の提案（較正係数の動的補正など）の前提を否定する重要な知見になる。

---

## 11. 本調査の限界

- **検索範囲。** PubMed の題名・抄録フィールドに限っている。会議録の一部、非収載誌、そして**特許は未探索**である。とくに Pulse Decomposition Analysis を製品化している系譜（CareTaker／Vitalstream）は、分解由来の振幅比・時間差を広く押さえている可能性が高く、実装を検討するなら別途の特許調査が必要になる。
- **本文の未入手。** Couceiro 2015 と Tigges 2017 は本文が有料で取得できていない。とくに Couceiro 2015 について、**同論文中の SI・RI が原波形由来（比較対照）かモデル由来かを確定できていない**。抄録の並びからは前者と読めるが、確定には本文が要る。ただし Goswami 2010 が明示的にモデルから SI・RI を導いているため、本稿の結論は変わらない。
- **選別の主観性。** 系統的レビューの手続き（二重スクリーニング、除外理由の記録）は踏んでいない。本稿は網羅性を保証するものではなく、**新規性の主張を否定するには十分な反例が見つかった**ことを示す文書である。
- **数値の扱い。** 本稿に記した数値はすべて各原著の抄録に記載された値である。抄録に無い数値は記載していない。

---

## 12. 全文献一覧（PMID・URL）

**A 群 ― 分解由来の SI・RI**

**[A1]** Rubins U. Finger and ear photoplethysmogram waveform analysis by fitting with Gaussians. *Med Biol Eng Comput*. 2008;46(12):1271-6. <https://pubmed.ncbi.nlm.nih.gov/18855034/>

**[A2]** Goswami D, et al. A new two-pulse synthesis model for digital volume pulse signal analysis. *Cardiovasc Eng*. 2010;10(3):109-17. <https://pubmed.ncbi.nlm.nih.gov/20734136/>

**[A3]** Couceiro R, et al. Assessment of cardiovascular function from multi-Gaussian fitting of a finger photoplethysmogram. *Physiol Meas*. 2015;36(9):1801-25. <https://pubmed.ncbi.nlm.nih.gov/26235798/>

**[A4]** Grabovskis A, et al. Two-stage multi-Gaussian fitting of conduit artery photoplethysmography waveform during induced unilateral hemodynamic events. *J Biomed Opt*. 2015;20(3):035004. <https://pubmed.ncbi.nlm.nih.gov/25751027/>（正誤表 <https://pubmed.ncbi.nlm.nih.gov/25813914/>）

**[A5]** Wang A, et al. Gaussian modelling characteristics changes derived from finger photoplethysmographic pulses during exercise and recovery. *Microvasc Res*. 2018;117:15-21. <https://pubmed.ncbi.nlm.nih.gov/28347756/>

**[A6]** Park J, et al. Vascular Aging Estimation Based on Artificial Neural Network Using Photoplethysmogram Waveform Decomposition. *JMIR Med Inform*. 2022;10(3):e33439. <https://pubmed.ncbi.nlm.nih.gov/35297776/>

**[A7]** Baruch MC, et al. Validation of the pulse decomposition analysis algorithm using central arterial blood pressure. *Biomed Eng Online*. 2014;13:96. <https://pubmed.ncbi.nlm.nih.gov/25005686/>

**[A8]** Baruch MC, et al. Pulse Decomposition Analysis of the digital arterial pulse during hemorrhage simulation. *Nonlinear Biomed Phys*. 2011;5(1):1. <https://pubmed.ncbi.nlm.nih.gov/21226911/>

**B 群 ― 分解モデルの方法論**

**[B1]** Wang L, et al. Multi-Gaussian fitting for pulse waveform using Weighted Least Squares and multi-criteria decision making method. *Comput Biol Med*. 2013;43(11):1661-72. <https://pubmed.ncbi.nlm.nih.gov/24209911/>

**[B2]** Tigges T, et al. Model selection for the Pulse Decomposition Analysis of fingertip photoplethysmograms. *Annu Int Conf IEEE Eng Med Biol Soc*. 2017;2017:4014-7. <https://pubmed.ncbi.nlm.nih.gov/29060777/>

**[B3]** Fleischhauer V, et al. Pulse decomposition analysis in photoplethysmography imaging. *Physiol Meas*. 2020;41(9):095009. <https://pubmed.ncbi.nlm.nih.gov/33021236/>

**[B4]** Basso G, et al. A skewed-Gaussian model for pulse decomposition analysis of photoplethysmography signals. *Physiol Meas*. 2024;45(11). <https://pubmed.ncbi.nlm.nih.gov/39577084/>

**[B5]** Sorelli M, et al. Detecting Vascular Age Using the Analysis of Peripheral Pulse. *IEEE Trans Biomed Eng*. 2018;65(12):2742-50. <https://pubmed.ncbi.nlm.nih.gov/29993447/>

**[B6]** Couceiro R, et al. Multi-Gaussian fitting for the assessment of left ventricular ejection time from the photoplethysmogram. *Annu Int Conf IEEE Eng Med Biol Soc*. 2012;2012:3951-4. <https://pubmed.ncbi.nlm.nih.gov/23366792/>

**C 群 ― 圧波形での波分離**

**[C1]** Westerhof BE, et al. Quantification of wave reflection in the human aorta from pressure alone: a proof of principle. *Hypertension*. 2006;48(4):595-601. <https://pubmed.ncbi.nlm.nih.gov/16940207/>

**[C2]** Kips JG, et al. Evaluation of noninvasive methods to assess wave reflection and pulse transit time from the pressure waveform alone. *Hypertension*. 2009;53(2):142-9. <https://pubmed.ncbi.nlm.nih.gov/19075098/>

**[C3]** Manoj R, et al. Separation of Forward-Backward Waves in the Arterial System using Multi-Gaussian Approach from Single Pulse Waveform. *Annu Int Conf IEEE Eng Med Biol Soc*. 2021;2021:5547-50. <https://pubmed.ncbi.nlm.nih.gov/34892381/>

**[C4]** Manoj R, et al. Arterial pressure pulse wave separation analysis using a multi-Gaussian decomposition model. *Physiol Meas*. 2022;43(5). <https://pubmed.ncbi.nlm.nih.gov/35537402/>

**[C5]** Guberti D, et al. Estimation of pulse wave analysis indices from invasive arterial blood pressure only for a clinical assessment of wave reflection in a 5-day septic animal experiment. *Med Biol Eng Comput*. 2025. <https://pubmed.ncbi.nlm.nih.gov/40014240/>

**D 群 ― SI・RI の原典と妥当性**

**[D1]** Millasseau SC, et al. Determination of age-related increases in large artery stiffness by digital pulse contour analysis. *Clin Sci (Lond)*. 2002;103(4):371-7. <https://pubmed.ncbi.nlm.nih.gov/12241535/>

**[D2]** Chowienczyk PJ, et al. Photoplethysmographic assessment of pulse wave reflection: blunted response to endothelium-dependent beta2-adrenergic vasodilation in type II diabetes mellitus. *J Am Coll Cardiol*. 1999;34(7):2007-14. <https://pubmed.ncbi.nlm.nih.gov/10588217/>

**[D3]** Epstein S, et al. Numerical assessment of the stiffness index. *Annu Int Conf IEEE Eng Med Biol Soc*. 2014;2014:1969-72. <https://pubmed.ncbi.nlm.nih.gov/25570367/>

**E 群 ― 周術期の PPG 形態解析**

**[E1]** Coutrot M, et al. Noninvasive continuous detection of arterial hypotension during induction of anaesthesia using a photoplethysmographic signal: proof of concept. *Br J Anaesth*. 2019;122(5):605-12. <https://pubmed.ncbi.nlm.nih.gov/30916032/>

**[E2]** Aguet C, et al. Blood pressure monitoring during anesthesia induction using PPG morphology features and machine learning. *PLoS One*. 2023;18(2):e0279252. <https://pubmed.ncbi.nlm.nih.gov/36735652/>

**[E3]** Lee QY, et al. Multivariate classification of systemic vascular resistance using photoplethysmography. *Physiol Meas*. 2011;32(8):1117-32. <https://pubmed.ncbi.nlm.nih.gov/21693795/>

**[E4]** Gratz I, et al. Continuous Non-invasive finger cuff CareTaker comparable to invasive intra-arterial pressure in patients undergoing major intra-abdominal surgery. *BMC Anesthesiol*. 2017;17(1):48. <https://pubmed.ncbi.nlm.nih.gov/28327093/>

**[E5]** Khanna AK, et al. Agreement between cardiac output estimation with a wireless, wearable pulse decomposition analysis device and continuous thermodilution in post cardiac surgery intensive care unit patients. *J Clin Monit Comput*. 2024;38(1):139-46. <https://pubmed.ncbi.nlm.nih.gov/37458916/>

**F 群 ― 基盤データ・ツール**

**[F1]** Charlton PH, et al. Modeling arterial pulse waves in healthy aging: a database for in silico evaluation of hemodynamics and pulse wave indexes. *Am J Physiol Heart Circ Physiol*. 2019;317(5):H1062-85. <https://pubmed.ncbi.nlm.nih.gov/31442381/>

**[F2]** Lee HC, et al. VitalDB, a high-fidelity multi-parameter vital signs database in surgical patients. *Sci Data*. 2022;9(1):279. <https://pubmed.ncbi.nlm.nih.gov/35676300/>

**[F3]** Goda MA, Charlton PH, Behar JA. pyPPG: a Python toolbox for comprehensive photoplethysmography signal analysis. *Physiol Meas*. 2024;45(4). <https://pubmed.ncbi.nlm.nih.gov/38478997/>

---

本稿は研究・教育を目的とした文献的整理であり、個別の臨床判断を指示・保証するものではない。各文献の記述はすべて原著の抄録にもとづく要約であり、原文の複製ではない。数値を引用する際は必ず一次文献を参照されたい。URL は本稿作成時点（2026 年 8 月）に到達を確認したもの。

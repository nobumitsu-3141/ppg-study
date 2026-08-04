# 反射波の位置は同定できるか

**PPG 波形上の可視特徴を解剖学的反射部位に帰属させることの限界と、RI／SI による術中後負荷評価の設計**

---

## 本稿の位置づけ

本リポジトリの中核レビューは、波形を「前進波＋反射波」の合成として読む枠組みを §2 に置いている。しかしそこで扱われる「反射波」は一貫して**単数**であり、その反射がどこから来たのかは問われていない。成果物 8（`SDPPG_prognostic_evidence_and_diastolic_gap.md`）§4.2 は「後期収縮期の augmentation」と「拡張期反射」を初めて二種類に分けたが、その帰属の妥当性は検証されていなかった。

本稿は、次の四つの問いに文献で答える。

1. PPG 波形で、近位由来と遠位由来の反射波が 2 つ目視できる条件はあるか
2. それは血管が柔らかいほど容易か
3. 高齢者で 1 つだけ見えるとき、それは遠位からの反射と考えてよいか
4. 動脈圧波形の反射波成分と PPG の反射波成分は成因が同じか

そのうえで、**反射波の位置を後負荷評価に使うという構想そのもの**を再構成し、その脆弱性と適応できない状況を列挙し、波形の類型ごとに何が同定可能かを図示する。

> **図について**：本文中の図 1（重ね合わせの原理）と図 2（波形類型の退化系列）は HTML 版（`PPG_reflection_wave_localisation.html`）にインライン SVG として収録している。本 Markdown 版は編集用ソースであり、図は含まない。

本稿は文献レビューであり、第 6 節の指標設計は**提案**である。臨床判断の根拠としてはならない。

---

## 0. 四つの問いへの短答

| 問い | 答え |
|---|---|
| **Q1** 2 つ目視できる条件はあるか | **「2 つの隆起が見える」ことはある。ただし「反射が 2 つ」ではない。**見えるのは後期収縮期の二次隆起と拡張期ピークであり、両者を解剖学的な近位／遠位反射部位に帰属させる試みは、反証可能な形では検証されていない |
| **Q2** 柔らかいほど容易か | **時間軸については Yes**（実測 PPG で支持）。ただし「加齢で反射波が拡張期から収縮期へ移動する」という説明は誤りで、正しくは**分解能**の問題。振幅側は別問題で、急性には壁の硬さではなく末梢トーヌスが支配する |
| **Q3** 1 つなら遠位反射か | **向きの直感は主要モデルと一致する。**しかし「1 つ見える＝遠位」と同定してはならない。可視性は反射の個数ではなく**位相の重ね合わせ**で決まる |
| **Q4** 成因は同じか | **成因は同じ、信号は別物、指標値は互換でない**という三分法が正確 |

---

## 1. 参考文献マトリクス ― 何を補強するために引いたか

本節は、本稿および本リポジトリの反射波に関する議論で用いる一次文献を、**「どの主張を補強するために引いたか」「PICO」「エビデンス区分」**とともに一覧する。エビデンス区分は本プロジェクトの原則に従う。

- **(A) 実測 PPG あり** ― 光電容積脈波そのもので検証された
- **(B) 現象は実測・機序はモデル** ― 波形変化は観察されるが原因帰属はモデル依存
- **(C) 動脈圧外挿・モデル** ― 観血的動脈圧・動脈径・in silico からの外挿で、実測 PPG での検証がない
- **(D) 未確認** ― 本調査で一次情報に到達できなかった

PICO は臨床試験の枠組みであり、総説・数理モデル・信号処理研究には本来適用できない。該当しない項目は「―」とし、研究デザインを併記する。

### 1.1 反射の物理と部位論（主に §2・§4 を支える）

| # | 文献 | 補強する主張 | P | I | C | O | 区分 |
|---|---|---|---|---|---|---|---|
| 1 | Latham RD, et al. *Circulation* 1985;72:1257-69 | 動脈系に**複数の反射部位が実在する**。反射係数は部位で大きく異なる | 心カテ施行患者 | 大動脈内 6 点同時マイクロマノメトリ＋Valsalva・両側大腿動脈圧迫 | 基礎条件 | 部位別反射係数（近位下行大動脈 γ=0.05、腎動脈接合部 γ=0.43、大動脈終末分岐 γ=0.13）。大腿圧迫で遠位反射が増強 | C |
| 2 | Burattini R, et al. *Circ Res* 1991;68:85-99 | **可視隆起の数は反射の数と一致しない。**図 1 の直接の典拠 | イヌ 10 頭 | 薬理学的介入下の大動脈圧測定＋非対称 T 管モデル同定 | 基礎条件（群 A） | 群 D＝硬化により body-end 反射が収縮期へ移動し head-end 反射に重畳。群 B＝2 反射が分離していても body-end のピークが head-end の谷と一致し拡張期変動が消失 | C |
| 3 | Campbell KB, et al. *Am J Physiol* 1989;256:H1684-9 | **反射部位の同定は原理的に不能。**有効長 L の厳密解が無限個存在する | ― | 解析的検討 | ― | 「いずれの L も実在の反射部位と対応する必要がない」 | C |
| 4 | Westerhof BE, et al. *Hypertension* 2008;52:478-83 | 反射部位の位置は定義できず、帰還時刻から PWV は計算できない | ― | モデル解析 | ― | 「to define the location of a reflection site is elusive」 | C |
| 5 | Westerhof BE, Westerhof N. *Physiol Meas* 2018;39:124006 | 単一反射部位の管モデルでは大動脈の波動伝播と波形を説明できない | ― | 均一管モデルの検証 | 実測波形 | 反射波の心臓到達時刻は PWV にほとんど依存しない | C |
| 6 | Davies JE, et al. *Hypertension* 2012;60:778-85 | **遠位大動脈に単一の優勢な反射部位は存在しない**（horizon effect） | ヒト 19 名 | 10 cm 間隔の血管内圧＋ドプラ流速 | 近位 vs 遠位測定点 | 反射部位までの時間 近位 48±5 ms vs 遠位 42±4 ms（P=0.3） | C |
| 7 | Sugawara J, et al. *Hypertension* 2010;56:920-5 | 加齢で有効反射長が**遠位化**する（8 と対立） | 208 名 | MRI 三次元動脈長トレース | 年齢層間 | 有効反射長は加齢で増加、65 歳以降に著明 | C |
| 8 | Phan TS, et al. *J Am Heart Assoc* 2016;5:e003733 | 加齢で反射は早く帰るが**遠位化の証拠はない**（7 と対立、未決着） | n=48／n=164 | 位相コントラスト MRI 流量＋波動分離 | 年齢層間 | RWTT −15.0／−9.07 ms/decade、有効反射距離増大なし | C |
| 9 | Westerhof N, et al. *Hypertension* 2015;66:93-8 | **波動分離には圧と流量の両方が必要**（PPG は容積 1 チャネル） | ― | 方法論総説 | ― | 分離原理の定式化 | C |
| 10 | Westerhof BE, et al. *Hypertension* 2006;48:595-601 | 圧単独からの反射定量は原理的には可能 | ヒト | 圧単独からの波動分離 | 圧＋流量による分離 | proof of principle | C |
| 11 | Kips JG, et al. *Hypertension* 2009;53:142-9 | **1 チャネル分離が最も苦手なのが timing**＝部位同定に必要な量 | Asklepios コホート >2,500 名 | 圧単独分離法の外部検証 | 圧＋流量による分離 | 反射量 R²=0.55–0.74、大動脈通過時間 R²<0.29 | C |
| 12 | Baksi AJ, et al. *J Am Coll Cardiol* 2009;54:2087-92 | **「加齢で反射波が拡張期から収縮期へ移動する」は誤り。**§3 の説明を訂正する根拠 | 64 研究・13,770 名・4–91 歳 | 動脈圧波形の反射到達時刻のメタ解析 | 年齢層間 | 反射到達は全年齢で収縮期内（加重平均 136 ms、99%CI 130–141）。収縮期持続 328 ms。加齢変化 −0.7 ms/年 | C |
| 13 | Politi MT, et al. *Comput Biol Med* 2016;72:54-64 | 重複切痕は大動脈弁閉鎖のみに帰属できない | 血管手術患者 | フェニレフリン投与（末梢血管抵抗の選択的変化） | 投与前 | 観血動脈圧で切痕が修飾される。Navier–Stokes モデルで機序提示 | C |

### 1.2 指尖 PPG 輪郭の成因と指標定義（§3・§6 を支える）

| # | 文献 | 補強する主張 | P | I | C | O | 区分 |
|---|---|---|---|---|---|---|---|
| 14 | Chowienczyk PJ, et al. *J Am Coll Cardiol* 1999;34:2007-14 | **RI の定義。拡張期側特徴は指の局所現象ではなく系統的な波動反射**である（局所／全身解離） | 健常者・2 型糖尿病 | 上腕動注（局所）vs 全身投与の β₂ 刺激薬 | 局所投与 vs 全身投与 | 前腕血流 3 倍超でも IP_DVP 不変、全身投与では用量依存性に低下。第 1–第 2 ピーク間時間 vs 大動脈通過時間 r=0.75（n=20, p<0.0001） | A |
| 15 | Millasseau SC, et al. *Clin Sci (Lond)* 2002;103:371-7 | **SI の定義**と大動脈スティフネスとの対応 | 87 名 | 指尖容積脈波の輪郭解析 | 頸大腿 PWV | SI_DVP vs cf-PWV r=0.65。SI=0.63+0.086×age+0.042×MAP。週間隔の被験者内 CV 9.6% | A |
| 15b | Millasseau SC, et al. *Am J Hypertens* 2003;16:467-72 | **SI と RI の二重解離**＝急性変化を支配するのはトーヌスであってスティフネスではない | 横断 124 名／薬理 **10 名** | ニトログリセリン（3–300 µg/min）・アンジオテンシン II 静注 | ベースライン | SI は年齢と R=0.63 だが薬物でほぼ不変、RI は AII で用量依存増加・GTN で減少。**薬理データは n=10** | A |
| 16 | Millasseau SC, et al. *Hypertension* 2000;36:952-6 | 指尖容積脈波から末梢圧波形が伝達関数で再構成できる | 60 名 | DVP → 圧の一般化伝達関数 | 橈骨動脈圧・指動脈圧 | RMS 誤差 4.4±2.0／4.3±1.9 mmHg。高血圧・NTG に非依存 | A |
| 17 | Millasseau SC, et al. *J Hypertens* 2006;24:1449-56 | 拡張期波の振幅は**小動脈の筋トーヌス**に依存する | ― | 総説 | ― | 輪郭解析の整理 | B |
| 18 | Takazawa K, et al. *Hypertension* 1998;32:365-70 | **SDPPG の a–e 波の定義**、および PPG-AIx＝後期収縮期ピーク／前期収縮期ピーク | 薬物 39 例＋疫学 600 例 | 血管作動薬投与＋心カテ同時記録 | 投与前 | d/a vs 上行大動脈 AIx r=0.80。AII で d/a 低下、NTG で上昇 | A |
| 19 | Iketani T, et al. *Hypertens Res* 2000;23:451-8 | 後期収縮期ピークを「**末梢反射波**」に帰属させる立場（20 と競合） | 本態性高血圧 60 例 | 指尖 PPG の AI 算出 | 左室心筋重量係数 | LVMI vs AI r=0.60、負の d/a と r=0.63 | A |
| 20 | Elgendi M. *Curr Cardiol Rev* 2012;8:14-25 | 上肢は前進波・反射波の共通経路であり、両者の**相対時相にほとんど影響しない** | ― | 総説 | ― | ΔT は鎖骨下動脈起始部から見かけの反射部位までの往復時間に対応 | B |
| 21 | Charlton PH, et al. *Am J Physiol Heart Circ Physiol* 2022;322:H493-H522 | **反射波は「循環全体からの多数の反射が時間的に拡がった単一の合成波」**（VascAgeNet の現在の立場） | ― | 総説 | ― | ΔT ≈ 4×大動脈 PTT、r=0.75。Dawber 4 クラスの逐語記載。「高齢者では典型的に見えなくなる（class 4）」 | B |
| 22 | Alastruey J, et al. *Am J Physiol Heart Circ Physiol* 2023;325:H1-H29 | **「少数の明確な反射部位という考えはおそらく過度の単純化」**「変曲点もショルダー点も反射波の帰還と直接には結びつけられない」 | ― | 総説（モデル側） | ― | 部位帰属そのものへの否定的評価 | C |
| 23 | Rubins U. *Med Biol Eng Comput* 2008;46:1271-6 | PPG をガウス分解すると直達波＋**3 反射波**になる（成分数は設計仮定） | 健常 40 名 | 指・耳同時 PPG のガウス当てはめ | ― | 直達波と 3 反射波の時刻を算出 | B |
| 24 | Couceiro R, et al. *Physiol Meas* 2015;36:1801-25 | 同じ PPG に**5 ガウス**を当てる立場もある（成分数の恣意性） | 健常＋心血管疾患 68 名 | 5 ガウス関数モデル | 参照法による LVET | LVET 絶対誤差 15.41±13.66 ms、ρ=0.78 | B |
| 25 | Tigges T, et al. *EMBC* 2017:4014-7 | **成分数はデータ駆動でも一意に決まらない** | 実測指尖 DVP 7,805 拍 | AICc によるモデル選択 | 複数の成分数・関数形 | 最良モデル 3 成分ガンマは全拍の **28.1%**、次点 2 成分レイリー 14.4% | A |
| 26 | Baruch MC, et al. *Nonlinear Biomed Phys* 2011;5:1 | **部位帰属を試みた代表例**。ただし部位名はモデルの前提であり、センサは PPG ではない | 健常若年 15 名（24.4±3.0 歳） | 下半身陰圧＋Pulse Decomposition Analysis | LBNP 段階間 | #2＝腎反射（70–140 ms）、#3＝腸骨反射（180–400 ms）。**CareTaker 圧電式圧センサであり光電容積脈波ではない** | C |
| 27 | Nagasawa T, et al. *Appl Sci* 2022;12:1798 | 指尖 PPG の sech 波分解を腎動脈・腸骨分岐に帰属させた唯一の実測 PPG 例 | ― | ― | ― | **PubMed 非収載・全文未確認。Zanelli 2023 が引用している事実のみ確認** | D |

### 1.3 加齢・スティフネスによる波形退化（§5・§6 を支える）

| # | 文献 | 補強する主張 | P | I | C | O | 区分 |
|---|---|---|---|---|---|---|---|
| 28 | Zanelli S, et al. *Front Physiol* 2023;14:1176753 | **本稿で最も重要な実測証拠。**二次収縮期波と重複切痕は**ともに最若年で最も明瞭で、同方向に加齢消失する** | 300 名・約 11,057 拍 | pOpmètre（Axelife）赤色/赤外透過型 1 kHz、臥位 5 分安静後のクラスタリング | クラスタ間（年齢層） | 最若年クラスタが明瞭な切痕と二次収縮期波を同時に示す。加齢で収縮期ピークが幅広くなり二次収縮期波が消失 | A |
| 29 | Cunningham JW, et al. *Circ Genom Precis Med* 2023;16:e003676 | **「高齢者では何も見えない」は誇張。**切痕欠如は 14% にとどまる | UK Biobank 169,787 名 | 生 PPG からの切痕欠如の自動判定（ResNet） | 切痕あり群 | 切痕欠如 25,286 名（14%）。欠如群は高齢（61.5 vs 56.5 歳）、女性が多い（66% vs 52%） | A |
| 30 | Charlton PH, et al. *Am J Physiol Heart Circ Physiol* 2019;317:H1062-H1085 | 加齢に伴う指標変化の in silico 基準値。**PPG は終端 windkessel の血液量から生成**されている | in silico（25–75 歳） | 1D 血行動態モデル | 年齢層間 | 頸動脈 AIx 2.3±10.4 → 41.5±9.1%、反射波到達 122.4±9.1 → 80.2±13.2 ms、RI 0.18±0.08 → 0.41±0.13、SI 6.2±1.0 → 10.3±3.4 m/s。**二次収縮期ピークが現れる PPG は側頭動脈・耳であって指尖ではない** | C |
| 31 | Allen J, Murray A. *Physiol Meas* 2003;24:297-307 | 加齢で立ち上がり脚が延長し切痕が減衰する（多部位） | 健常 116 名（13–72 歳） | 耳・示指・母趾の両側 PPG | 年齢との回帰 | 全部位で収縮期立ち上がり脚の延長（p<0.05）と重複切痕の減衰（p<0.05） | A |
| 32 | Allen J, et al. *Physiol Meas* 2020;41:074001 | 立ち上がり時間の加齢変化（指で +1.9 ms/年） | 304 名 | 多部位 PPG | 年齢との回帰 | 部位別の立ち上がり時間の加齢変化 | A |
| 33 | Simonetti GD, et al. *Pediatr Nephrol* 2008;23:439-44 | **最も柔らかい集団では指標の妥当性がむしろ悪化する**という逆説 | 健常小児 79 名（8–15 歳、平均 11.4 歳） | DVP の SI 算出 | 頸大腿 PWV 同時測定 | SI vs cfPWV は r²=0.07（P=0.02）。「RI>90%＝高血管トーヌス」個体を除外して r²=0.13（P=0.001） | A |
| 34 | Suboh MZ, et al. *Front Public Health* 2022;10:920946 | **加齢で拡張期ピークが shoulder 化し、局所最大として同定できなくなる** | ― | 四次微分までを用いた特徴点検出 | ― | 微分による切痕・拡張期ピークの同定法。同定困難化を明記 | B |
| 35 | Wilkinson IB, et al. *J Physiol* 2000;525:263-70 | AIx の**心拍数依存性**（補正の必要） | ペースメーカ患者 22 名（平均 63 歳） | 段階ペーシング 60→110 bpm | ペーシング速度間 | AIx は HR と逆相関（10 bpm で約 4% 低下）、拍出時間も逆相関（r=−0.51） | C |
| 36 | Brillante DG, et al. *Blood Press* 2008;17:116-23 | RI・SI は横断的には年齢と関連する（因果ではない） | 健常ボランティア | 非侵襲デジタル PPG | 年齢・血圧 | スティフネス指数の横断的関連 | A |

### 1.4 周術期の実測（§6 を支える）

| # | 文献 | 補強する主張 | P | I | C | O | 区分 |
|---|---|---|---|---|---|---|---|
| 37 | Awad AA, et al. *J Clin Monit Comput* 2007;21:365-72 | **振幅は SVR に鈍感、切痕を含む「幅」の方が良い**。第 1 階層指標の根拠 | 14 例 | 指・耳 PPG | 熱希釈法による SVR | 振幅 r=−0.15、幅 r=0.56 | A |
| 38 | Tusman G, et al. *J Clin Monit Comput* 2019;33:815-24 | 切痕位置＋振幅の 2 軸分類が血行動態イベントを検出する | 心臓外科 15 例 | PPG 6 クラス視覚分類 | 収縮期血圧・SVR・血管コンプライアンス | 低血圧・高血圧エピソードの正診率およそ 97–98% | A |
| 39 | Joachim J, et al. *J Clin Monit Comput* 2021;35:395-404 | 切痕相対位置＋PI から MAP を実時間推定しうる | 全身麻酔中の患者 | 切痕相対位置＋灌流指数 | 観血的 MAP | パイロット研究 | A |
| 40 | Coutrot M, et al. *Br J Anaesth* 2019;122:605-12 | **Dicpleth（相対切痕高比）の proof-of-concept**。第 1 階層指標の直接の先行研究 | 麻酔導入 61 例 | Dicpleth・PI の変動 | 術中低血圧・昇圧薬ボーラス | 術中低血圧の検出と血管反応追跡に有用 | A |
| 41 | Cannesson M, et al. *Crit Care* 2005;9:R562-8 | 前負荷は振幅の**呼吸性変動**を介してのみ実測 PPG で裏づけられる | 機械換気 22 例 | ΔPOP | 動脈脈圧変動 ΔPP | 良好な相関 | A |

### 1.5 信号処理・計測系（§5・§6 を支える）

| # | 文献 | 補強する主張 | P | I | C | O | 区分 |
|---|---|---|---|---|---|---|---|
| 42 | Goda MÁ, et al. *Physiol Meas* 2024;45:045001（pyPPG） | **微分上の点は生波形の目視より頑健。**および f 点の操作的定義は既に存在する | 219 点ベンチマーク | p1・p2 は三次微分上、f は二次微分上で e 直後の最初の極小として定義 | 人手アノテーション | 除外点数 dn 29／c 7／d 7／p2 2／f 0。p1 の MAE 1(1) ms、p2 は 2(3) ms、f は 3(8) ms | A |
| 43 | Pal R, et al. *Comput Methods Programs Biomed* 2024;254:108283 | **切痕タイミング検出では PPG は動脈圧と同等以上**。IEM 法が第一候補 | MLORD 17,327 患者 | 反復エンベロープ平均（IEM）法 | 二次微分法 | IEM で平均誤差 ABP 0.0047 s／PPG 0.0046 s。検出可能 SNR は ABP ≥−9 dB／PPG ≥−12 dB（**PPG の方が低 SNR まで頑健**）。二次微分法では ABP 0.0693 s／PPG 0.0968 s | A |
| 44 | Liu H, et al. *Physiol Meas* 2021;42(7) | **フィルタが時相をずらす。**フィルタ設定の固定が必須である根拠 | 健常 36 名・6 部位 | IIR フィルタ条件の変更 | フィルタ条件間・部位間 | 測定部位・特徴種別・交互作用いずれも p<0.001。二次微分最大のシフトが最大、指が最大 | A |
| 45 | Alian AA, Shelley KH. *Best Pract Res Clin Anaesthesiol* 2014;28:395-406 | **モニタ表示波形は生信号ではない** | ― | 総説 | ― | 「増幅され高度にフィルタされた計測値で、メーカーが拍動成分を強調するよう最適化している」 | B |
| 46 | Shelley KH. *Anesth Analg* 2007;105:S31-S36 | 生信号への自由なアクセスと提示の標準化が鍵 | ― | 総説 | ― | 解析の前提条件 | B |
| 47 | Lee HC, et al. *Sci Data* 2022;9:279（VitalDB） | **段階 0 の検証が今日実行可能である**根拠 | 周術期患者 | 高分解能バイタル波形の公開 | ― | GE TramRac-4A の plethysmogram を 500 Hz で記録 | A |
| 48 | Pilt K, Reiu A. *Med Biol Eng Comput* 2024;62:1049-59 | **経壁圧（プローブ装着圧）が指標値を変える** | 51 名 | 経壁圧の変更 | 経壁圧条件間 | 経壁圧 10–20 mmHg でのみ PPGAI 対 AIx@75 が良好 | A |

### 1.6 圧と容積の乖離（§4 を支える）

| # | 文献 | 補強する主張 | P | I | C | O | 区分 |
|---|---|---|---|---|---|---|---|
| 49 | Langewouters GJ, et al. *J Biomech* 1984;17:425-35 | 圧-断面積関係は **arctangent 型の強い非線形** | ヒト屍体大動脈 | 静的圧-径測定 | ― | 非線形の定式化 | C |
| 50 | Imura T, et al. *Circ Res* 1990;66:1413-9 | **径は圧に対し位相が遅れる** | 15 名 | 腹部大動脈の in vivo 圧-径 | ― | 基本波（1.2±0.3 Hz）で位相遅れ −6.7±2.1 度 | C |
| 51 | Vermeersch SJ, et al. *Physiol Meas* 2008;29:1267-80 | **径を圧に較正しても AIx は大きくずれる** | 2,026 名 | 頸動脈径波形の圧較正 | トノメトリ由来 AIx | 線形較正 +1.9(10.1)%、指数較正 +5.4(10.6)% 過大評価 | C |
| 52 | Volkov MV, et al. *Sci Rep* 2017;7:13298 | **PPG の容積源そのものが未確定**（動脈容積説への疑義） | ― | ビデオ毛細管顕微鏡＋同時 PPG | ― | 毛細血管赤血球密度変調が波形成因である可能性 | A |
| 53 | Hsiu H, et al. *Photomed Laser Surg* 2012;30:77-84 | **同じ刺激で圧と PPG の変化が乖離する**実測 | 29 名 | 寒冷刺激 | 橈骨動脈圧波 vs 指尖 PPG | 圧波は C4-C10／P3-P10 が変化、PPG は C5-C10 と P3・P4 のみ | A |
| 54 | Herranz Olazabal J, et al. *Bioengineering* 2023;10:101 | 同一指同時記録で**形態は有意に乖離**。時刻の同等性は示されていない | 8 名・2,599 拍 | 指動脈圧・PPG・SPG の同時記録 | 相互比較 | 形態 MAD は PPG 0.17 vs SPG 0.09。PAT は ECG-PPG r=0.67 vs ECG-SPG r=0.65 で**有意差なし＝検出力不足** | A |
| 55 | Pilt K, et al. *Physiol Meas* 2014;35:2027-36 | PPG 由来の**振幅軸**指標と大動脈 AIx@75 の相関 | 健常 24 名＋2 型糖尿病 20 名 | PPGAI | SphygmoCor 由来 aortic AIx@75 | r=0.85 | A |
| 56 | Clarenbach CF, et al. *Hypertens Res* 2012;35:228-33 | **異種の軸を並べてはならない**という警告例 | ― | PPG 由来 **SI（時間軸）** | 橈骨トノメトリ AIx | r=0.48。**これを「PPG-AIx 対 圧 AIx」と記述するのは誤り** | A |
| 57 | Heffernan KS, et al. *Eur J Appl Physiol* 2012;112:2871-9 | 末梢 AIx と観血的中心指標の相関は必ずしも高くない | 左心カテ 59 例 | PAT 由来 AIx | 大動脈 pulsatility・圧増幅 | r=0.45／r=−0.28 | A |
| 58 | Cox JR, et al. *Pulse (Basel)* 2024;12:95-105 | 単一伝達関数では不十分で、入力に応じた切替が要る | 21 名 | selective transfer function | 橈骨トノメトリ＋既存 GTF | 3 つの伝達関数の切替が必要 | C |

### 1.7 本調査で確認できなかったもの（区分 D）

| 事項 | 状況 |
|---|---|
| Nagasawa T, et al. *Appl Sci* 2022;12:1798 | PubMed 非収載、出版社サイトから全文取得できず。**指尖 PPG で部位帰属を試みた唯一の候補**であり、優先的に入手すべき |
| Dawber TR, et al. *Angiology* 1973;24:244-55（PMID 4699520） | PubMed に抄録がない。4 クラス分類の定義は Charlton 2022・Cunningham 2023 の逐語記載を経由した**二次情報**。測定モダリティ・対象数・クラス別年齢分布はいずれも未確認 |
| Baruch MC, et al. *Biomed Eng Online* 2014;13:96（心カテ 63 例） | 「5 成分の存在を中心動脈内カテーテルで確認した」のか「PDA 推定値と中心圧の相関を示しただけ」なのかが未確認。**部位帰属が検証されたことがあるかを左右する** |
| 臨床モニタ（日本光電ほか）の AGC 実装と帯域特性 | メーカー非公開。AGC が拍内で作用するか、拡張期の小振幅成分が保存されるかはいずれも未検証。特許明細書からの復元が唯一の現実的経路 |
| Millasseau 2002 の年齢別 ΔT 実測表 | 本稿で用いる年齢別 ΔT 値は回帰式からの算術換算であり、原著の実測表ではない |
| Charlton 2022 の「ΔT ≈ 4×大動脈 PTT」の回帰係数 | Chowienczyk 1999 原著の係数そのものは未確認（総説による要約）。単純な往復（2×）と整合しないため、経路論に直接効く |

---

## 2. 「反射波を近位・遠位に帰属させるのはナンセンスか」

結論から言えば、**「ナンセンス」は言い過ぎだが、「部位（site）の同定」としては成立しない。**「経路（path）」の話としてなら作業仮説として使える。この区別が本稿全体の要である。

### 2.1 部位としては成立しない ― 三重の否定

第一に、**有効反射長から部位を逆算する問題は非一意である。**Campbell らは有効長 L の厳密解が無限個存在することを解析的に示し、「いずれの L も実在の反射部位と対応する必要がない」と結論した [3]。Westerhof BE らも「反射部位の位置を定義することは捉えどころがない」と述べ、反射波の帰還時刻から PWV を計算することを否定している [4][5]。

第二に、**実測すると単一の優勢な反射部位が見つからない。**Davies らはヒト 19 名で 10 cm 間隔の血管内圧とドプラ流速を同時記録し、反射部位までの時間が近位 48±5 ms・遠位 42±4 ms（P=0.3）と有意差を示さないことから、「遠位大動脈に単一の優勢な反射部位は存在しない」と結論した（horizon effect）[6]。

第三に、**PPG 領域の標準的総説が明示的に否定している。**VascAgeNet の総説は「少数の明確な反射部位という考えはおそらく過度の単純化である」「詳細なモデル解析は、変曲点もショルダー点も反射波の帰還と直接には結びつけられないことを示唆する」と述べる [22]。同グループの PPG 側総説も、反射波を「循環全体からの多数の反射が時間的に拡がった単一の合成波」として扱う [21]。

第四に、**PPG に固有の不利がある。**波動分離には圧と流量の両方が必要であり [9]、圧単独でも原理的には可能だが [10]、その外部検証では反射量が R²=0.55–0.74 なのに対し**大動脈通過時間は R²<0.29 と不良**であった [11]。1 チャネルからの分離が最も苦手とするのが timing であり、部位同定に必要なのはまさに timing である。PPG は容積 1 チャネルなので事情はさらに悪い。

### 2.2 経路としてなら成立する ― ただし区分は (C)

一方で、**「拡張期側の隆起はおおむね大動脈〜下半身経路を往復した反射成分を主とする」という向きの主張は、主要モデルと一致し、実測 PPG からの支持もある。**

Burattini らの非対称 T 管モデルでは、head-end（頭頸部・上肢）経路は短く反射が収縮期早期に戻るのに対し、**拡張期変動を作っているのは body-end（体幹・下肢）反射そのものである** [2]。Latham らのヒト大動脈内 6 点同時測定でも、両側大腿動脈圧迫により遠位反射が増強することが示されている [1]。

実測 PPG 側では、Chowienczyk らの局所／全身解離が最も強い証拠である。上腕動注で前腕血流を 3 倍以上に増やしても指尖容積脈波の変曲点位置は不変で、全身投与では用量依存性に低下した。さらに第 1–第 2 ピーク間時間が大動脈通過時間と r=0.75（n=20, p<0.0001）で相関した [14]。すなわち拡張期側の特徴は**指の局所トーヌスだけの現象ではなく、系統的な波動反射を反映している**。Elgendi の整理によれば、上肢は前進波と反射波の共通経路であるため両者の相対時相にほとんど影響を与えず、ΔT は鎖骨下動脈起始部から見かけの反射部位までの往復時間に対応する [20]。

**ただしこれはすべて「経路長が長い」という話であって、「腸骨分岐で反射した」という部位の同定ではない。**エビデンス区分は (C) である。

### 2.3 部位を書き込んだ手法は存在するが、検証されていない

指尖 PPG の分解成分に部位名を与えた研究は実在する [26][27]。しかし Baruch の Pulse Decomposition Analysis は CareTaker という**圧電式圧センサ**による信号であって光電容積脈波ではなく、健常若年 15 名の下半身陰圧検証にとどまる [26]。腎動脈・腸骨という部位名は**モデルに最初から書き込まれた前提**であって、データから同定されたものではない。

成分数についても同様である。同じ実測 PPG に、Rubins は直達波＋3 反射波 [23]、Couceiro は 5 ガウス [24] を当てている。Tigges らは 7,805 拍で AICc によるデータ駆動のモデル選択を行ったが、最良モデル（3 成分ガンマ）が選ばれたのは全拍の **28.1%** にすぎず、次点（2 成分レイリー）が 14.4% であった [25]。すなわち**成分数はデータからも一意には決まらない**。

したがって正確な言い方は「文献が 0 件」ではなく、**「帰属を試みた文献は存在するが、選択的介入による解離など反証可能な形で検証したものはゼロ」**である。

### 2.4 決定的な理由 ― 可視個数は反射の個数ではない

以上の議論すべてに優先する、より単純で強い理由がある。**波形上に見える隆起の数は、反射波の数の代理にならない。**

Burattini らのイヌ 10 頭の実験は、この一点を実験的に示している [2]。

- **群 D（n=3）**：硬化により body-end 反射が収縮期へ移動し head-end 反射に重畳した結果、**2 つの反射があるのに拡張期変動は 1 つに融合した**
- **群 B（n=2）**：2 つの反射が時間的に明確に分離していたにもかかわらず、body-end のピークが head-end の谷と一致したため、**拡張期変動が消失した（0 個に見えた）**

同じ 2 つの反射から、可視隆起は 2 個にも 1 個にも 0 個にもなる。**可視性は反射の個数ではなく位相の重ね合わせで決まる。**これを HTML 版の図 1 に示す（分離・融合・相殺の三状態）。

---

## 3. いま検討している理論の再構成

本節は、これまでの議論から浮かび上がっている作業理論を明示的に書き下す。批判の対象を固定するためである。

### 3.1 理論の骨格

> **作業理論**：光電容積脈波は前進波と反射波の合成である。反射波の**時間位置**は脈波の伝播速度と経路長で決まり、**高さ**は反射の大きさ（末梢血管トーヌス）で決まる。したがって、波形上で反射波に対応する特徴の位置と高さを同定し、その**個人内ベースラインからの相対変化（Δ）**を追えば、較正なしに術中の後負荷（全身血管抵抗・血管トーヌス）の変化を非侵襲に追跡できる。

この理論は五段の推論からなる。

| 段 | 主張 | 依拠する文献 | 区分 |
|---|---|---|---|
| ① | 波形＝前進波＋反射波の合成である | [21][22] | B |
| ② | 波形上の可視特徴（切痕・拡張期ピーク・後期収縮期隆起）は反射波の帰還に対応する | [14][18][20] | B〜C |
| ③ | その**時間位置**は経路長と PWV で決まる（→ SI・ΔT） | [15][20] | A（相関）／C（機序） |
| ④ | その**高さ**は末梢血管トーヌスで決まる（→ RI） | [14][15b][17] | A |
| ⑤ | ゆえに個人内 Δ を追えば後負荷変化を追跡できる | [37][38][39][40] | A（切痕系のみ） |

### 3.2 この理論に本稿が加える修正

**修正 1 ― ②は文献的に支持されていない。**Alastruey らは「変曲点もショルダー点も反射波の帰還と直接には結びつけられない」と明記している [22]。②を前提に置くのではなく、**「可視特徴は反射情報を含むが、反射波そのものではない」**と弱めるべきである。

**修正 2 ― ③と④は独立で、しかも時間スケールが違う。**Millasseau らの二重解離が決定的である。SI は年齢と R=0.63 で相関するが血管作動薬ではほとんど動かず、RI は AII で用量依存増加・GTN で減少した [15b]。**すなわち術中の急性後負荷変化を映すのは④（振幅軸）であって③（時間軸）ではない。**ただしこの薬理データは n=10 であり、124 名は横断部分である。

**修正 3 ― 「加齢で反射波が拡張期から収縮期へ移動する」という説明は使えない。**Baksi らは 64 研究・13,770 名のメタ解析で、動脈圧波形の反射到達が全年齢で収縮期内（加重平均 136 ms、収縮期持続 328 ms）であり、加齢変化は −0.7 ms/年にすぎないと示した [12]。正しい説明は「移動」ではなく**「2 つの極大の間隔＝分解能」**である。

**修正 4 ― 近位／遠位の弁別は理論に組み込めない。**§2 のとおりである。したがって理論は**「単一の合成反射情報の Δ を追う」**という形に限定される。

---

## 4. 理論の脆弱性

推論の各段が破れうる点を、破れの重大度とともに列挙する。

| # | 脆弱性 | 破れると何が起きるか | 根拠 | 重大度 |
|---|---|---|---|---|
| 1 | **可視特徴が存在しない**（高スティフネス・高齢） | 指標が計算不能。検出できた症例のみを解析する選択バイアスが必ず入る | [29][34] | 致命的 |
| 2 | **可視特徴と反射波の帰還が対応しない** | ②が破れ、位置の解釈が失われる。Δ の追跡は残るが「反射波を見ている」とは言えなくなる | [22] | 高 |
| 3 | **位相の重ね合わせにより個数が一致しない** | 「見えた 1 つ」が何の重ね合わせか不明。部位帰属も個数の解釈も不能 | [2] | 高 |
| 4 | **反射部位・有効長の逆問題が非一意** | 時間位置から解剖学的情報を取り出せない | [3][4][6] | 高 |
| 5 | **後負荷・壁スティフネス・前負荷・収縮力が同じ特徴を動かす** | 切痕位置の変化を後負荷の変化と読めない | [37][41]、および本リポジトリ成果物 4 | 高 |
| 6 | **容積≠圧**（非線形変換・局所コンプライアンス） | 圧波形で成り立つ関係が PPG で成り立つ保証がない | [49][50][51][53][54] | 中〜高 |
| 7 | **PPG の容積源そのものが未確定** | 「動脈壁の圧-径関係」を指 PPG に持ち込む前提が崩れる | [52] | 中 |
| 8 | **AGC と帯域制限**（モニタ波形は生信号ではない） | 拡張期の小振幅成分が保存される保証がない。実装は非公開 | [45][46]、区分 D | 中〜高 |
| 9 | **フィルタが時相をずらす** | 異なるフィルタ設定間で時間指標を比較できない。二次微分ベースの点で影響最大、指で最大 | [44] | 中 |
| 10 | **心拍数交絡** | 拡張期短縮で拡張期側が圧縮される。AIx は HR と逆相関 | [35] | 中 |
| 11 | **時間スケールの不一致** | SI・RI は安静時の半ば慢性的な血管特性として検証されており、1 拍ごとの急性変化には未検証 | [15][15b] | 中 |
| 12 | **プローブ経壁圧・部位・体温** | 装着圧が変われば指標値が変わる | [48] | 中 |
| 13 | **成分分解の成分数が一意でない** | 分解に基づく議論はすべて設計仮定に依存 | [23][24][25] | 中 |
| 14 | **最も柔らかい集団で妥当性が悪化する** | 若年で「よく見える」ことが「よく測れる」を意味しない | [33] | 中 |

**最も重い脆弱性は 1 と 5 である。**1 は指標が存在しなくなる問題、5 は指標が存在しても解釈できない問題であり、後者の方が実は厄介である。切痕位置は SVR・1 回拍出量・収縮力・動脈コンプライアンスの合成信号であり、単一の視覚的評価からこれらを分離することには原理的な限界がある。

---

## 5. 適応できない状況

理論が原理的に、あるいは実務上成立しない状況を列挙する。**このリストは研究プロトコルの除外基準の原案として使える。**

### 5.1 波形が要件を満たさない

| 状況 | 理由 |
|---|---|
| **高齢・高スティフネス例（波形類型 T1a・T0）** | 拡張期ピークが局所最大として存在せず、RI・ΔT が定義できない [29][34]。第 6 節の階層化が必要 |
| **深麻酔・強い血管拡張（PI 高値）** | 反射が小さく拡張期成分が消える。柔らかい血管でも起こる [15b] |
| **低体温・末梢循環不全・昇圧薬高用量** | 信号品質低下と局所トーヌスの極端化 |
| **頻脈** | 拡張期短縮により拡張期側が切り詰められる [35] |
| **不整脈（心房細動など）** | 拍ごとに拡張期長が変動し、ΔT・RI が拍間で不安定になる |

### 5.2 反射の物理的前提が崩れる

| 状況 | 理由 |
|---|---|
| **大動脈弁閉鎖不全** | 拡張期の逆流により切痕・拡張期部分が変形する |
| **大動脈内バルーンパンピング（IABP）** | 拡張期に人工的な増強波が加わり、反射由来の特徴と区別できない |
| **体外循環・補助循環（非拍動流）** | 前進波そのものが存在せず、枠組みが成立しない |
| **大動脈遮断・REBOA** | 反射経路が物理的に変わる。**逆に、これは検証の好機でもある（第 7 節）** |
| **測定側上肢の神経ブロック・交感神経遮断** | 局所トーヌスが全身と乖離する。本リポジトリが既出の NCT04179097 が扱う論点 |
| **下肢切断・大血管再建後** | 経路長が変化する。**これも検証の好機である** |

### 5.3 計測系が要件を満たさない

| 状況 | 理由 |
|---|---|
| **モニタ画面上の目視評価のみ** | 表示波形は増幅・高度フィルタ済みで拍動成分強調に最適化されている [45]。測定として成立しない |
| **フィルタ設定が不明・可変** | 時間指標が設定間で比較できない [44] |
| **プローブ部位・装着圧が管理されていない** | 経壁圧の変化が指標値を変える [48] |
| **サンプリング周波数が不明** | ただしこれは律速ではない。VitalDB は 500 Hz で二次微分に十分 [47] |

### 5.4 対象集団による制約

| 状況 | 理由 |
|---|---|
| **小児** | SI と cfPWV の相関が r²=0.07 と弱く、高血管トーヌス例で推定が破綻する [33] |
| **身長の極端例** | SI ≡ 身長/ΔT なので身長が定義に内在する。個人内 Δ では消えるが、群間比較では交絡する |
| **群間・個人間の絶対値比較** | 本理論は個人内 Δ にのみ妥当性が主張できる。絶対値の較正は本プロジェクトの設計思想から外れる |

---

## 6. 波形類型と反射波同定の可否

### 6.1 可視特徴は最大いくつか

問いは「目視上ありえる反射波との合成個数は 0–2 か 3 か」であった。答えは**数える対象を定義すると一意に決まる**。

| 数える対象 | 最大数 | 内訳 |
|---|---|---|
| **反射由来とされる隆起** | **2** | 後期収縮期の二次隆起（P2／secondary systolic wave）と拡張期ピーク |
| **可視 landmark 全体** | **3** | 上記 2 つ＋重複切痕 |
| **原波形上の局所最大** | **3** | 前期収縮期ピーク P1、後期収縮期ピーク P2、拡張期ピーク |

**重複切痕を「反射波」に数えてはならない。**切痕は駆出終了に対応する境界であって反射波の隆起ではないため、数えると二重計上になる。

**拡張期ピークのさらに後に続く第 2・第 3 の振動は、実測 PPG では確認できなかった。**PubMed で `"tricrotic"[tiab]` は 0 件である。多重反射（reverberation）の理論的根拠は存在するが、それはイヌ大動脈圧とモデルの話であって PPG ではない。したがって**「3 つ以上の反射隆起」は区分 D（未検証）**として扱う。

### 6.2 五つの波形類型

HTML 版の図 2 は、前進波と二つの反射成分（短経路・長経路）の合成として、加齢・硬化に伴う退化の系列を示す。分類は Dawber の 4 クラス（[21] 経由）に P2 の有無を加えたものである。

| 類型 | 可視 landmark | 局所最大の数 | Dawber 対応 | 典型 |
|---|---|---|---|---|
| **T3** | P2・切痕・拡張期ピーク | 3 | class 1 の一部 | 最若年・高コンプライアンス |
| **T2** | 切痕・拡張期ピーク | 2 | class 1 | 若年〜中年 |
| **T1b** | 切痕（変曲点）・拡張期 shoulder | 1 | class 2 | 中年〜高齢 |
| **T1a** | 下降脚の勾配変化のみ | 1 | class 3 | 高齢 |
| **T0** | なし（単峰性） | 1 | class 4 | 高齢・高スティフネス（UK Biobank で 14%） |

**加齢方向は一方向である。**Zanelli らの 300 名・約 11,057 拍の実測で、二次収縮期波と重複切痕は**ともに最若年クラスタで最も明瞭であり、同方向に加齢消失する** [28]。すなわち T3 → T0 へ退化する。「高齢ほど AIx が上がるから P2 が見えやすくなる」は誤りで、AIx が高い状態とは P1 と P2 が融合した単一の幅広い後期収縮期ピークであり、**振幅比は上がるが目視での分離可視性は下がる**。

### 6.3 類型ごとに何が同定可能か

| 類型 | 拡張期ピーク（RI・ΔT） | 切痕（Dicpleth） | P2（PPG-AIx） | 反射の帰属 |
|---|---|---|---|---|
| **T3** | ○ 局所最大として同定可 | ○ | ○ 生波形でも可 | 経路としてのみ（区分 C）。近位／遠位の弁別は**不可** |
| **T2** | ○ | ○ | △ 三次微分でのみ | 同上 |
| **T1b** | × 局所最大なし。**f 点（SDPPG 上の e 直後の極小）で代替**、ただし検証が要る | ○ | × | 帰属の根拠なし |
| **T1a** | × | △ IEM 法で時刻のみ推定可 [43] | × | 帰属の根拠なし |
| **T0** | × | × | × | 同定対象が存在しない |

**いずれの類型でも、近位反射と遠位反射を弁別することはできない。**T3・T2 において「拡張期ピークは長経路（大動脈〜下半身）反射を主とする」と呼ぶことは作業仮説として許容できるが（区分 C）、これは経路の話であって部位の同定ではない。

### 6.4 実装上の警告 ― フォールバックが黙って発火する

pyPPG は、f 点の極小が見つからない場合に **f = e にフォールバック**し、拡張期ピークが原波形に局所最大として存在しない場合に**一次微分の局所極大にフォールバック**する。すなわち T1b 以下の波形をアルゴリズムに通すと、この二つが警告なく発火する。

**帰結として、「見えた 1 つ」が何を指すかが実装依存になる。**研究設計では「見えた反射波の本数」を一次アウトカムにしてはならず、**微分ベースの操作的定義を事前に固定し、フォールバックの発火をログに記録して層別解析する**必要がある。

---

## 7. RI／SI を中心とした術中後負荷評価の設計

以上を踏まえ、「どの反射波の位置をどのように求めるのが合理的か」に答える。

### 7.1 結論 ― SI を主軸にしてはならない

**SI（＝身長/ΔT）は術中の急性後負荷評価には適さない。**理由は三つある。

1. **薬理学的に動かない。**Millasseau らの二重解離で、SI は血管作動薬でほとんど変化しなかった [15b]
2. **測っている対象が違う。**SI は大動脈スティフネスの指標として cf-PWV に対して検証されており [15]、後負荷（SVR）の指標ではない
3. **時間スケールが違う。**SI は安静時被験者の半ば慢性的な血管特性として検証されており、1 拍ごとの急性変動には未検証である

**SI は術前ベースラインの血管特性把握に限定して使う。**これは本リポジトリ成果物 10 の「取得容易性とエビデンスの逆相関」とも整合する。

**RI（＝拡張期ピーク高/収縮期ピーク高）は後負荷に近い。**Chowienczyk らが小血管トーヌスを反映すると示し [14]、Millasseau らの二重解離で薬物に応答した [15b]。しかし**RI は拡張期ピークという最も退化しやすい landmark を必要とする**（第 6 節）。したがって RI をそのまま主軸に据えると、最も評価したい高齢例で計算不能になる。

### 7.2 推奨する三階層の指標設計

この矛盾を解く方法は、**退化しない landmark を主軸に置き、RI を条件付きの第 2 階層に降ろすこと**である。

**第 1 階層 ― Dicpleth（相対的重複切痕高比）。全例で取得を試みる。**

切痕時刻における原波形の振幅を収縮期ピーク振幅で割った比である。**この指標は切痕が局所最小である必要がなく、変曲点でよい。**pyPPG の dn 定義がまさにこれで、「拡張期ピークがあればその直前の局所最小、なければ収縮期ピークと f 点の間の変曲点」とされる [42]。したがって T1a まで定義できる。

- 実測 PPG での裏づけ：Awad ら（切痕を含む幅が SVR と r=0.56、振幅は r=−0.15）[37]、Tusman ら（6 クラス分類で低血圧・高血圧の正診率 97–98%）[38]、Joachim ら（切痕相対位置＋PI で MAP 実時間推定）[39]、Coutrot ら（麻酔導入 61 例で Dicpleth の proof-of-concept）[40]
- 検出法：IEM 法を第一候補とする。17,327 患者・PPG 342 万拍で平均誤差 0.0046 s、検出可能 SNR は −12 dB まで（動脈圧の −9 dB より頑健）[43]

**第 2 階層 ― RI。拡張期ピークが局所最大として同定できる症例のみ。**

事前に検出成功基準を定義し、**検出できなかった症例を明示して層別する**。これを怠ると選択バイアスが必ず入る。T1b 以下では f 点（SDPPG 上で e 直後の最初の極小）による代替が考えられるが、これは本リポジトリ成果物 8 の仮説そのものであり、まだ検証されていない。

**第 3 階層 ― SI・PPG-AIx。術前ベースラインの特性把握のみ。**

術中 Δ の主軸には使わない。

### 7.3 位置をどう求めるか ― 操作的定義

1. **生波形の目視は使わない。**モニタ表示波形は増幅・高度フィルタ済みである [45]
2. **微分ベースで固定する。**切痕時刻は SDPPG の e 点、拡張期ピーク時刻は f 点、P2 は三次微分上の定義 [42]。微分上の点の方が頑健である（219 点ベンチマークで p2 の除外は 2 拍、生波形の dn は 29 拍＝13%）
3. **フォールバックを無効化するか、発火をログに残す**（第 6.4 節）
4. **フィルタ設定を固定し、明示する。**フィルタ由来の時間シフトは部位・特徴種別・交互作用のいずれも p<0.001 で有意であり、二次微分ベースの点で最大、指で最大である [44]
5. **すべて個人内 Δ として運用する。**導入前ベースラインを基準とする

### 7.4 測定プロトコルの最低条件

- 生波形のエクスポート（Vital Recorder 等）、500 Hz 以上 [47]
- フィルタ条件の記録と固定 [44]
- プローブ部位・装着圧の固定 [48]
- 末梢温・PI の同時記録
- 心拍数の同時記録（拡張期長の交絡と AIx@75 補正のため）[35]
- 体位の固定

### 7.5 検証の順序

**段階 0（最優先・今日実行可能）**：VitalDB の公開波形で、**年齢群別に波形類型 T3〜T0 の出現頻度を出す**。これが研究全体の実行可能性を決める。本リポジトリ成果物 7 の段階 0 と同じ作業であり、理論的議論だけが先行して未実施のまま残っている。

**段階 1**：同時記録された観血的動脈圧から算出した SVR（または MAP・CO）の Δ と、Dicpleth の Δ の対応を見る。

**段階 2**：昇圧薬ボーラス前後の Δ を見る（Coutrot 2019 の追試）[40]。

**段階 3**：前向き研究。

### 7.6 近位／遠位の弁別を検証したいなら

本稿は部位帰属を否定したが、**否定を覆しうる検証設計は存在する**。いずれも「下半身循環を選択的に操作したとき、拡張期側の特徴だけが選択的に動くか」を見るものである。

| 設計 | 内容 | 実行可能性 |
|---|---|---|
| **両大腿駆血** | 両大腿に収縮期圧以上の駆血帯。対照として両上腕駆血 | Latham らがヒト大動脈内圧で同等の操作を行っている [1] ので、PPG 版は技術的に実行可能 |
| **下半身陰圧（LBNP）の既存データ再解析** | PubMed に LBNP × PPG の研究が複数あるが、いずれも compensatory reserve index の機械学習研究で、反射波の帰属を評価項目にしていない | **新規前向き研究を待たずに再解析できる** |
| **下肢切断者の指尖 PPG** | 下半身の経路長が物理的に短縮している自然実験 | 下半身反射仮説の最も直接的な検証。文献上、誰も試みていない |
| **大動脈遮断・REBOA 症例** | 反射経路が術中に一変する | 症例数は限られるが観察可能 |

---

## 8. まとめ

1. **PPG で「2 つの隆起が見える」ことはある**（後期収縮期の二次隆起と拡張期ピーク）。実測での直接証拠は Zanelli らの 300 名・約 11,057 拍 [28]。しかしこれは「反射が 2 つ」を意味しない。
2. **柔らかいほど分離して見えやすい**のは時間軸の話として正しい。ただし「加齢で反射波が拡張期から収縮期へ移動する」という説明は使えない [12]。正しくは分解能の問題である。
3. **高齢者で 1 つだけ見えても、それを遠位反射と同定することはできない。**向きの直感は主要モデルと一致するが [1][2]、可視性は位相の重ね合わせで決まり [2]、反射部位という概念自体が同定不能である [3][6][22]。
4. **動脈圧と PPG の反射波は、成因は同じ、信号は別物、指標値は互換でない。**成因の同一性を支える最強の実測証拠は Chowienczyk らの局所／全身解離 [14] である。
5. **部位（site）としての帰属は成立しないが、経路（path）としての解釈は作業仮説として許容できる**（区分 C）。
6. **術中後負荷評価の主軸は Dicpleth に置くべきである。**RI は最も退化しやすい landmark を必要とするため第 2 階層に降ろし、SI は術前特性の把握に限定する。
7. **最優先の作業は VitalDB での波形類型の頻度算出**である。これが研究全体の実行可能性を決める。

---

| **実務メモ（一人麻酔科の視点）** 本稿の帰結は、実は現場的にはむしろ楽観的である。「反射波がどこから来たか」を知る必要はそもそもない。必要なのは、**退化しにくい landmark を一つ決めて、導入前からの変化を同じ条件で追い続けること**である。切痕の相対位置はその条件を満たし、麻酔導入 61 例での先行研究もある [40]。一方で、モニタ画面を目視して「反射波が 2 つ見えるから柔らかい」と読むことには、測定としての裏づけがない。生波形を取り出し、微分上で点を定義し、フィルタ条件を固定する——この三つが揃って初めて、この理論は検証可能な形になる。 |
| --- |

---

## 参考文献

本文中の [n] は §1 のマトリクスの番号に対応する。URL は本稿作成時点（2026 年）に到達を確認したもの。区分 D の項目は §1.7 を参照。

**[1]** Latham RD, Westerhof N, Sipkema P, et al. Regional wave travel and reflections along the human aorta: a study with six simultaneous micromanometric pressures. *Circulation*. 1985;72(6):1257-69. PMID 4064270. <https://pubmed.ncbi.nlm.nih.gov/4064270/>

**[2]** Burattini R, Knowlen GG, Campbell KB. Two arterial effective reflecting sites may appear as one to the heart. *Circ Res*. 1991;68(1):85-99. PMID 1984875. <https://pubmed.ncbi.nlm.nih.gov/1984875/>

**[3]** Campbell KB, Lee LC, Frasch HF, Noordergraaf A. Pulse reflection sites and effective length of the arterial system. *Am J Physiol*. 1989;256(6 Pt 2):H1684-9. PMID 2735437. <https://pubmed.ncbi.nlm.nih.gov/2735437/>

**[4]** Westerhof BE, van den Wijngaard JP, Murgo JP, Westerhof N. Location of a reflection site is elusive: consequences for the calculation of aortic pulse wave velocity. *Hypertension*. 2008;52(3):478-83. PMID 18695144. <https://pubmed.ncbi.nlm.nih.gov/18695144/>

**[5]** Westerhof BE, Westerhof N. Uniform tube models with single reflection site do not explain aortic wave travel and pressure wave shape. *Physiol Meas*. 2018;39(12):124006. PMID 30523888. <https://pubmed.ncbi.nlm.nih.gov/30523888/>

**[6]** Davies JE, Alastruey J, Francis DP, et al. Attenuation of wave reflection by wave entrapment creates a "horizon effect" in the human aorta. *Hypertension*. 2012;60(3):778-85. PMID 22802223. <https://pubmed.ncbi.nlm.nih.gov/22802223/>

**[7]** Sugawara J, Hayashi K, Tanaka H. Distal shift of arterial pressure wave reflection sites with aging. *Hypertension*. 2010;56(5):920-5. PMID 20876449. <https://pubmed.ncbi.nlm.nih.gov/20876449/>

**[8]** Phan TS, Li JK, Segers P, et al. Aging is associated with an earlier arrival of reflected waves without a distal shift in reflection sites. *J Am Heart Assoc*. 2016;5(9):e003733. PMID 27572821. <https://pubmed.ncbi.nlm.nih.gov/27572821/>

**[9]** Westerhof N, Segers P, Westerhof BE. Wave separation, wave intensity, the reservoir-wave concept, and the instantaneous wave-free ratio: presumptions and principles. *Hypertension*. 2015;66(1):93-8. PMID 26015448. <https://pubmed.ncbi.nlm.nih.gov/26015448/>

**[10]** Westerhof BE, Guelen I, Westerhof N, Karemaker JM, Avolio A. Quantification of wave reflection in the human aorta from pressure alone: a proof of principle. *Hypertension*. 2006;48(4):595-601. PMID 16940207. <https://pubmed.ncbi.nlm.nih.gov/16940207/>

**[11]** Kips JG, Rietzschel ER, De Buyzere ML, et al. Evaluation of noninvasive methods to assess wave reflection and pulse transit time from the pressure waveform alone. *Hypertension*. 2009;53(2):142-9. PMID 19075098. <https://pubmed.ncbi.nlm.nih.gov/19075098/>

**[12]** Baksi AJ, Treibel TA, Davies JE, et al. A meta-analysis of the mechanism of blood pressure change with aging. *J Am Coll Cardiol*. 2009;54(22):2087-92. PMID 19926018. <https://pubmed.ncbi.nlm.nih.gov/19926018/>

**[13]** Politi MT, Ghigo A, Fernández JM, et al. The dicrotic notch analyzed by a numerical model. *Comput Biol Med*. 2016;72:54-64. PMID 27016670. <https://pubmed.ncbi.nlm.nih.gov/27016670/>

**[14]** Chowienczyk PJ, Kelly RP, MacCallum H, et al. Photoplethysmographic assessment of pulse wave reflection: blunted response to endothelium-dependent beta2-adrenergic vasodilation in type II diabetes mellitus. *J Am Coll Cardiol*. 1999;34(7):2007-14. PMID 10588217. <https://pubmed.ncbi.nlm.nih.gov/10588217/>

**[15]** Millasseau SC, Kelly RP, Ritter JM, Chowienczyk PJ. Determination of age-related increases in large artery stiffness by digital pulse contour analysis. *Clin Sci (Lond)*. 2002;103(4):371-7. PMID 12241535. <https://pubmed.ncbi.nlm.nih.gov/12241535/>

**[15b]** Millasseau SC, Kelly RP, Ritter JM, Chowienczyk PJ. The vascular impact of aging and vasoactive drugs: comparison of two digital volume pulse measurements. *Am J Hypertens*. 2003;16(6):467-72. PMID 12799095. <https://pubmed.ncbi.nlm.nih.gov/12799095/>

**[16]** Millasseau SC, Guigui FG, Kelly RP, et al. Noninvasive assessment of the digital volume pulse. Comparison with the peripheral pressure pulse. *Hypertension*. 2000;36(6):952-6. PMID 11116106. <https://pubmed.ncbi.nlm.nih.gov/11116106/>

**[17]** Millasseau SC, Ritter JM, Takazawa K, Chowienczyk PJ. Contour analysis of the photoplethysmographic pulse measured at the finger. *J Hypertens*. 2006;24(8):1449-56. PMID 16877944. <https://pubmed.ncbi.nlm.nih.gov/16877944/>

**[18]** Takazawa K, Tanaka N, Fujita M, et al. Assessment of vasoactive agents and vascular aging by the second derivative of photoplethysmogram waveform. *Hypertension*. 1998;32(2):365-70. PMID 9719069. <https://pubmed.ncbi.nlm.nih.gov/9719069/>

**[19]** Iketani T, Iketani Y, Takazawa K, Yamashina A. The influence of the peripheral reflection wave on left ventricular hypertrophy in patients with essential hypertension. *Hypertens Res*. 2000;23(5):451-8. PMID 11016799. <https://pubmed.ncbi.nlm.nih.gov/11016799/>

**[20]** Elgendi M. On the analysis of fingertip photoplethysmogram signals. *Curr Cardiol Rev*. 2012;8(1):14-25. PMID 22845812. <https://pubmed.ncbi.nlm.nih.gov/22845812/>

**[21]** Charlton PH, Paliakaitė B, Pilt K, et al. Assessing hemodynamics from the photoplethysmogram to gain insights into vascular age: a review from VascAgeNet. *Am J Physiol Heart Circ Physiol*. 2022;322(4):H493-H522. PMID 34951543. <https://pubmed.ncbi.nlm.nih.gov/34951543/>

**[22]** Alastruey J, Charlton PH, Bikia V, et al. Arterial pulse wave modeling and analysis for vascular-age studies: a review from VascAgeNet. *Am J Physiol Heart Circ Physiol*. 2023;325(1):H1-H29. PMID 37000606. <https://pubmed.ncbi.nlm.nih.gov/37000606/>

**[23]** Rubins U. Finger and ear photoplethysmogram waveform analysis by fitting with Gaussians. *Med Biol Eng Comput*. 2008;46(12):1271-6. PMID 18855034. <https://pubmed.ncbi.nlm.nih.gov/18855034/>

**[24]** Couceiro R, Carvalho P, Paiva RP, et al. Assessment of cardiovascular function from multi-Gaussian fitting of a finger photoplethysmogram. *Physiol Meas*. 2015;36(9):1801-25. PMID 26235798. <https://pubmed.ncbi.nlm.nih.gov/26235798/>

**[25]** Tigges T, Pielmus A, Klum M, et al. Model selection for the pulse decomposition analysis of photoplethysmographic signals. *Annu Int Conf IEEE Eng Med Biol Soc*. 2017;2017:4014-4017. PMID 29060777. <https://pubmed.ncbi.nlm.nih.gov/29060777/>

**[26]** Baruch MC, Warburton DE, Bredin SS, et al. Pulse decomposition analysis of the digital arterial pulse during hemorrhage simulation. *Nonlinear Biomed Phys*. 2011;5:1. PMID 21226911. <https://pubmed.ncbi.nlm.nih.gov/21226911/>

**[27]** Nagasawa T, et al. *Appl Sci*. 2022;12:1798. doi:10.3390/app12041798（**PubMed 非収載・全文未確認。区分 D**）<https://doi.org/10.3390/app12041798>

**[28]** Zanelli S, Eveilleau K, Charlton PH, et al. Clustered photoplethysmogram pulse wave shapes and their associations with clinical data. *Front Physiol*. 2023;14:1176753. PMID 37954447. <https://pubmed.ncbi.nlm.nih.gov/37954447/>

**[29]** Cunningham JW, Di Achille P, Morrill VN, et al. Machine learning to understand genetic and clinical factors associated with the pulse waveform dicrotic notch. *Circ Genom Precis Med*. 2023;16(1):e003676. PMID 36580284. <https://pubmed.ncbi.nlm.nih.gov/36580284/>

**[30]** Charlton PH, Mariscal Harana J, Vennin S, et al. Modeling arterial pulse waves in healthy aging: a database for in silico evaluation of hemodynamics and pulse wave indexes. *Am J Physiol Heart Circ Physiol*. 2019;317(5):H1062-H1085. PMID 31442381. <https://pubmed.ncbi.nlm.nih.gov/31442381/>

**[31]** Allen J, Murray A. Age-related changes in the characteristics of the photoplethysmographic pulse shape at various body sites. *Physiol Meas*. 2003;24(2):297-307. PMID 12812416. <https://pubmed.ncbi.nlm.nih.gov/12812416/>

**[32]** Allen J, O'Sullivan J, Stansby G, Murray A. Age-related changes in pulse risetime measured by multi-site photoplethysmography. *Physiol Meas*. 2020;41(7):074001. PMID 32784270. <https://pubmed.ncbi.nlm.nih.gov/32784270/>

**[33]** Simonetti GD, Eisenberger U, Bergmann IP, et al. Pulse contour analysis: a valid assessment of central arterial stiffness in children? *Pediatr Nephrol*. 2008;23(3):439-44. PMID 18097689. <https://pubmed.ncbi.nlm.nih.gov/18097689/>

**[34]** Suboh MZ, Jaafar R, Nayan NA, et al. Analysis on four derivative waveforms of photoplethysmogram (PPG) for fiducial point detection. *Front Public Health*. 2022;10:920946. PMID 35844894. <https://pubmed.ncbi.nlm.nih.gov/35844894/>

**[35]** Wilkinson IB, MacCallum H, Flint L, et al. The influence of heart rate on augmentation index and central arterial pressure in humans. *J Physiol*. 2000;525 Pt 1:263-70. PMID 10811742. <https://pubmed.ncbi.nlm.nih.gov/10811742/>

**[36]** Brillante DG, O'Sullivan AJ, Howes LG. Arterial stiffness indices in healthy volunteers using non-invasive digital photoplethysmography. *Blood Press*. 2008;17(2):116-23. PMID 18568701. <https://pubmed.ncbi.nlm.nih.gov/18568701/>

**[37]** Awad AA, Haddadin AS, Tantawy H, et al. The relationship between the photoplethysmographic waveform and systemic vascular resistance. *J Clin Monit Comput*. 2007;21(6):365-72. PMID 17940842. <https://pubmed.ncbi.nlm.nih.gov/17940842/>

**[38]** Tusman G, Acosta CM, Pulletz S, et al. Photoplethysmographic characterization of vascular tone mediated changes in arterial pressure: an observational study. *J Clin Monit Comput*. 2019;33(5):815-24. PMID 30554338. <https://pubmed.ncbi.nlm.nih.gov/30554338/>

**[39]** Joachim J, Coutrot M, Millasseau S, et al. Real-time estimation of mean arterial blood pressure based on photoplethysmography dicrotic notch and perfusion index. A pilot study. *J Clin Monit Comput*. 2021;35(2):395-404. <https://doi.org/10.1007/s10877-020-00486-y>

**[40]** Coutrot M, Joachim J, Dépret F, et al. Noninvasive continuous detection of arterial hypotension during induction of anaesthesia using a photoplethysmographic signal: proof of concept. *Br J Anaesth*. 2019;122(5):605-612. <https://doi.org/10.1016/j.bja.2019.01.037>

**[41]** Cannesson M, Besnard C, Durand PG, et al. Relation between respiratory variations in pulse oximetry plethysmographic waveform amplitude and arterial pulse pressure in ventilated patients. *Crit Care*. 2005;9(5):R562-8. PMID 16277719. <https://pubmed.ncbi.nlm.nih.gov/16277719/>

**[42]** Goda MÁ, Charlton PH, Behar JA. pyPPG: a Python toolbox for comprehensive photoplethysmography signal analysis. *Physiol Meas*. 2024;45(4):045001. PMID 38478997. <https://pubmed.ncbi.nlm.nih.gov/38478997/>

**[43]** Pal R, Rudas A, Kim S, et al. An algorithm to detect dicrotic notch in arterial blood pressure and photoplethysmography waveforms using the iterative envelope mean method. *Comput Methods Programs Biomed*. 2024;254:108283. PMID 38901273. <https://pubmed.ncbi.nlm.nih.gov/38901273/>

**[44]** Liu H, Allen J, Khalid SG, Chen F, Zheng D. Filtering-induced time shifts in photoplethysmography pulse features measured at different body sites: the importance of filter definition and standardization. *Physiol Meas*. 2021;42(7). PMID 34111855. <https://pubmed.ncbi.nlm.nih.gov/34111855/>

**[45]** Alian AA, Shelley KH. Photoplethysmography. *Best Pract Res Clin Anaesthesiol*. 2014;28(4):395-406. PMID 25480769. <https://pubmed.ncbi.nlm.nih.gov/25480769/>

**[46]** Shelley KH. Photoplethysmography: beyond the calculation of arterial oxygen saturation and heart rate. *Anesth Analg*. 2007;105(6 Suppl):S31-S36. PMID 18048895. <https://pubmed.ncbi.nlm.nih.gov/18048895/>

**[47]** Lee HC, Park Y, Yoon SB, et al. VitalDB, a high-fidelity multi-parameter vital signs database in surgical patients. *Sci Data*. 2022;9(1):279. PMID 35676300. <https://pubmed.ncbi.nlm.nih.gov/35676300/>

**[48]** Pilt K, Reiu A. Effect of transmural pressure on the estimation of arterial stiffness index from the photoplethysmographic waveform. *Med Biol Eng Comput*. 2024;62(4):1049-1059. PMID 38123887. <https://pubmed.ncbi.nlm.nih.gov/38123887/>

**[49]** Langewouters GJ, Wesseling KH, Goedhard WJ. The static elastic properties of 45 human thoracic and 20 abdominal aortas in vitro and the parameters of a new model. *J Biomech*. 1984;17(6):425-35. PMID 6480618. <https://pubmed.ncbi.nlm.nih.gov/6480618/>

**[50]** Imura T, Yamamoto K, Satoh T, et al. In vivo viscoelastic behavior in the human aorta. *Circ Res*. 1990;66(5):1413-9. PMID 2185904. <https://pubmed.ncbi.nlm.nih.gov/2185904/>

**[51]** Vermeersch SJ, Rietzschel ER, De Buyzere ML, et al. Determining carotid artery pressure from scaled diameter waveforms: comparison and validation of calibration techniques in 2026 subjects. *Physiol Meas*. 2008;29(11):1267-80. PMID 18843161. <https://pubmed.ncbi.nlm.nih.gov/18843161/>

**[52]** Volkov MV, Margaryants NB, Potemkin AV, et al. Video capillaroscopy clarifies mechanism of the photoplethysmographic waveform appearance. *Sci Rep*. 2017;7(1):13298. PMID 29038533. <https://pubmed.ncbi.nlm.nih.gov/29038533/>

**[53]** Hsiu H, Huang SM, Hsu CL, Hu SF, Lin HW. Effects of cold stimulation on the harmonic structure of the blood pressure and photoplethysmography waveforms. *Photomed Laser Surg*. 2012;30(2):77-84. PMID 22136594. <https://pubmed.ncbi.nlm.nih.gov/22136594/>

**[54]** Herranz Olazabal J, Wieringa F, Hermeling E, Van Hoof C. Comparison between speckle plethysmography and photoplethysmography during cold pressor test referenced to finger arterial pressure. *Bioengineering (Basel)*. 2023;10(1):101. PMID 36671673. <https://pubmed.ncbi.nlm.nih.gov/36671673/>

**[55]** Pilt K, Meigas K, Ferenets R, Temitski K, Viigimaa M. Photoplethysmographic signal waveform index for detection of increased arterial stiffness. *Physiol Meas*. 2014;35(10):2027-36. PMID 25238409. <https://pubmed.ncbi.nlm.nih.gov/25238409/>

**[56]** Clarenbach CF, Stoewhas AC, van Gestel AJ, et al. Comparison of photoplethysmographic and arterial tonometry-derived indices of arterial stiffness. *Hypertens Res*. 2012;35(2):228-33. PMID 21993214. <https://pubmed.ncbi.nlm.nih.gov/21993214/>

**[57]** Heffernan KS, Patvardhan EA, Kapur NK, Karas RH, Kuvin JT. Peripheral augmentation index as a biomarker of vascular aging: an invasive hemodynamics approach. *Eur J Appl Physiol*. 2012;112(8):2871-9. PMID 22138867. <https://pubmed.ncbi.nlm.nih.gov/22138867/>

**[58]** Cox JR, Akeila E, Avolio AP, et al. Validation of noninvasive derivation of the central aortic pressure waveform from fingertip photoplethysmography using a novel selective transfer function method. *Pulse (Basel)*. 2024;12(1):95-105. PMID 39479582. <https://pubmed.ncbi.nlm.nih.gov/39479582/>

---

本資料は研究・教育を目的とした文献的整理および理論的検討であり、個別の臨床判断を指示・保証するものではない。第 3 節の作業理論および第 7 節の指標設計は**提案**であって、検証されたプロトコルではない。第 6 節の波形類型は既知の分類（Dawber 4 クラス）に本稿が P2 の有無を加えた作図上の整理であり、この 5 類型そのものが検証された分類体系であるわけではない。一次文献を必ず参照されたい。

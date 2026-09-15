#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【探索・事後】論文2: 当てはめの型を変えると真の反射波の到達と大きさを追えるか
（節A・節A-2・合成）と、凍結版 ΔT・RI の崩れ方は実データにも出るか（節B・PWDB の既存列）、
候補の当てはめを実データの同じ拍に当てると何が起きるか（節C・PWDB の再当てはめ）。

**これは事後の探索であり、論文2 の事前規準による判定（26番）は動かさない。**
26番（`26_pwdb_compare.py`）で下した判定はそのまま有効で、この台本の出力はすべて
「探索的（事後）」として読む。この台本は成立・不成立の判定を出さない。

なぜ必要か
----------
48番 節4（`48_pwdb_by_waveform_type.py`）で、凍結版 PDA の第2成分のピークは特徴点法の
拡張期側の点より、型1 で +36.9 ms・型3 で +98.5 ms 遅かった（lab_log 2026-09-14 追記140）。
なぜそうなるかを合成脈波で調べたところ、**凍結版の ΔT は真の反射波の到達が約 150 ms を
下回ると下限で詰まり、真値が違っても同じ値を返す。**貯留槽の時定数 0.45 s のとき、
真の ΔT → 凍結版が返した ΔT [ms] は次のとおりであった。

    332→332・300→298・268→264・234→228・158→162・138→142・118→134・98→132・78→174・58→174

最後の 2 拍は真値が 20 ms 違うのに返り値が同じ 174 ms である。長い側（真値 230 ms 以上）の
誤差は 0〜6 ms なので、失敗は精度ではなく**短い側で順位が消えること**である。26番・48番は
年齢層内の順位相関で判定するので、この詰まりはそのまま ρ の低下になる。

同じ拍での順位相関 ρ（時定数 0.45 s ／ 0.30 s）は、凍結版 0.71／0.81、Δμ の下限を 0.01 s に
緩めると 0.89／0.95、貯留槽を前進波の畳み込みで持つと 1.00／1.00、0.65T までで当てはめると
0.95／0.99、参考の特徴点法 1.00／1.00 であった（監督者が合成脈波で実測した値。
lab_log 2026-09-15 追記141。この台本の節A はこの実測を台本の流儀で作り直したものである）。

この台本は 4 つの節を持つ。節A は反射波の**到達**（ΔT）、節A-2 は反射波の**大きさ**（RI）を
同じ合成脈波で振る。節B は実データ（PWDB）の既存列だけで、合成から立てた予測を確かめる。
節C は候補の当てはめを**実データの同じ拍に当て直す**（26番と同じ拍。`--pwdb` が要る）。
**節A-2 のほうが所見は強い**: 反射波が収縮期に重なる条件（型3 相当）では、凍結版の RI は
真の反射が大きいほど小さくなる（ρ −0.89。符号が反転する）。

節A（合成・既定で走る）
-----------------------
当てはめの型を並べ、真の反射波の到達を追えるかを測る（(5)(6) には Δμ の下限だけを凍結版の
ままにした版 (5b)(6b)、(4) には Δμ の下限を 0.01 s に緩めた版 (4b) を足し、先頭に凍結版
そのものを呼ぶ (0) を置いたので、表は 10 行になる）。

  合成脈波   前進波（歪みガウス）＋ 反射波（歪みガウス）＋ 貯留槽（指数減衰）。反射波は
             早く到達するほど幅が広くなり歪みが消える（硬い血管の波形）。雑音は標準偏差
             0.002。**真値は反射波のピーク − 前進波のピーク**（母数の差ではない）
  当てはめ   (0) 凍結版そのもの（`src/pda.py` の `fit_beat` を既定の引数で呼ぶ。起点 8 点・
                 特徴点近傍の解を優先する規則・max_nfev 4000）
             (1) 凍結版 2 カーネル（`src/pda.py` の探索範囲と同じ。Δμ の下限 0.08 s）
             (2) Δμ の下限を 0.01 s に緩める
             (3) 自由な指数減衰を足す（24番 の A1 と同じ形。d·exp(−(t−t0)/τ)）
             (4) 貯留槽を前進波の畳み込みで持つ（res(t) = g·∫g1(s)·e^{−(t−s)/τ}ds/τ。核は
                 単位面積。母数は g と τ の 2 つ）
             (4b) 同じ畳み込みで Δμ の下限を 0.01 s に緩める（(2) と (4) の同時適用）
             (5) 第2成分の形を第1成分に縛る（σ2 = c·σ1・α2 = α1）＋ Δμ の下限 0.01 s
             (5b) 同じ形の拘束で、Δμ の下限は凍結版のまま 0.08 s
             (6) 0.65T までで当てはめる ＋ Δμ の下限 0.01 s
             (6b) 同じ打ち切りで、Δμ の下限は凍結版のまま 0.08 s
             (1) 以降は `scipy.optimize.least_squares`（trf）で当てはめるが、**起点の
             作り方と解の選び方は `fit_beat` と同じ**にしてある（起点 8 点〈特徴点から
             決める初期値 dmu0 ＝ 主ピーク後の −d²y/dt² 最小点 ＋0.02 s の 1 点・Δμ の
             格子 0.12・0.18・0.26・0.36・0.48 s の 5 点・乱数で振った 2 点〉、
             max_nfev 4000、|Δμ − dmu0| ≤ 0.06 s の解が RSS 最小の 1.10 倍以内なら
             それを採る規則）。こうしてあるので、各行は凍結版から**狙った 1 つだけ**が
             違う（2026-09-15 に凍結版とそろえた。lab_log 追記143）。
             **収束検算は採否に課さない**（この節が見たいのは下限で詰まるかどうかで、
             採否ではない）。ただし凍結版と同じ規則を**診断として**当て、拍数を表に
             出す。(0) は `fit_beat` そのものなので、その検算の結果をそのまま使う

             (5)(6) は形の拘束（打ち切り）と Δμ の下限の**2 つ**が凍結版から変わって
             いる。これでは効き目の出どころが読めないので、**一度に 1 つだけ変えた**
             (5b)(6b) を 2026-09-15 に足した。(5)(6) はもともと試作と同じ設定で、試作の
             数値と一致することの記録でもあったが、2026-09-15 に実データを回す前に起点と
             解の選び方を凍結版と同じにしたので（lab_log 追記143）、**設定はもう試作と
             同じではなく、数値が一致することも保証されない**。行を残しているのは
             **2 つ同時に変えた版**としての意味があるからで、試作との一致のためではない。

             (4b) と (0) も 2026-09-15 に足した。(4b) は「Δμ を緩める・貯留槽を畳み込みで
             持つ、の 2 つをそれぞれと同時に適用したときの結果を出すのか」に答えるための行
             である（(2) と (4) の同時適用）。(0) は凍結版そのものを呼ぶ行で、写した複製
             (1) が本体と同じ振る舞いをすることの照合である。
  掃引       貯留槽の時定数 3 通り（0.45・0.35・0.25 s）× 反射波の到達 10 通り（0.30〜0.08 s）。
             時定数を年齢層に見立て、層の中で到達だけを振る（26番の年齢層内 Spearman を模す）
  出す表     型ごとに、時定数の層ごとの 順位相関 ρ・|誤差| の中央値・全拍の最小・
             下限の詰まり（新旧 2 つの規準。下記）、
             診断の表（凍結版と同じ収束検算の規則を当てた 通過・Δμ が探索範囲の下限に
             張り付いた拍数・境界・高さ・別解の拍数。**採否には使わない**）、および
             1 拍ずつの表（真値・型・各当てはめの返り値と誤差・特徴点法）

**下限の詰まりの規準（2026-09-15 に差し替えた）**: 真値の小さいほうから 3 拍で、
**返り値の最小がその 3 拍の真値の最大より 30 ms 以上大きい**とき「あり」と印字する。

最初に置いた規準は「その 3 拍の返り値の範囲が 20 ms 未満なら『あり』」であった。これは
**凍結版を取り逃がす**。凍結版の返り値は真値 98 ms で 132 ms と最小になり、さらに短い
真値（78・58 ms）では逆に 174 ms へ増えるので、下位 3 拍の範囲は 42 ms と広く出る。
範囲は「返り値が下に行けないこと」を測っていない（名前どおりの量になっていない）ので、
規準そのものを差し替えた。**結果を見て閾値を緩めたのではなく、測り方の誤りを直した。**
差し替える前の規準も「（参考）下位 3 拍の範囲」として同じ表に残し、表の下に両方の定義を
書く。あわせて**掃引の全拍を通した返り値の最小**も並べる（真値の最小との差が、追えなく
なった大きさである）。

**この節は探索・記述であり、26番の事前規準による判定には一切関与しない。**下限の詰まりの
規準は、この節の表に印を付けるためだけのもので、成立・不成立の判定には使わない。

参考として `pda2.preprocess` → `find_landmarks` の特徴点法（dia_t − sys_t）も同じ拍で出す。

節A-2（合成・既定で走る）
-------------------------
同じ合成脈波で、振るものを反射波の**大きさ**（母数 a_ref）に変え、当てはめが返す RI
（第2成分／第1成分のピーク高さの比 h2/h1）が順位を追うかを測る。

  掃引       反射波の大きさ 7 通り（0.20・0.28・0.35・0.42・0.50・0.58・0.65）× 条件 2 つ。
             条件は**型1 相当**（反射波の到達 0.28 s。遅く分離する）と**型3 相当**
             （到達 0.10 s。収縮期に重なる）で、貯留槽の時定数は 0.35 s に固定する
  当てはめ   節A と同じ 10 行。参考の特徴点法の RI は `dia_v / sys_v`
  真値       2 つ出す。「真の RI」は振った母数 a_ref、「真の比」は合成した成分のピーク
             高さの比（当てはめの h2/h1 と同じ定義）。条件の中では前進波が変わらないので
             両者は比例し、**順位は同じ**である。ρ は母数に対して、|誤差| は比に対して出す
  出す表     条件ごとに 順位相関 ρ・|誤差| の中央値・返り値の範囲・**符号の反転**、
             診断の表（節A と同じ）、および
             1 拍ずつの表（真の RI・真の比・波形の型・各当てはめの返り値・特徴点法）

**符号の反転の規準（2026-09-15 に、実装の前に決めた）**: ρ が −0.30 より小さいとき
「反転」と印字する。大きさは 20番の `CRIT_RHO`（0.30）と同じで、符号を負にしたものである。
**この印も探索・記述のためだけのもので、26番の事前規準による判定には関与しない。**

監督者が試作で測った値（一致の目安。貯留槽 0.35 s）

    型1 相当  凍結版・Δμ0.01・畳み込み・0.65T・特徴点法のすべてで ρ +1.00。凍結版の
              返り値は真の RI 0.20〜0.65 に対し 0.382・0.442・0.496・0.551・0.614・
              0.679・0.736
    型3 相当  **凍結版 ρ −0.89**（返り値 0.266・0.278・0.268・0.262・0.252・0.239・0.226
              と、真の反射波が大きくなるほど小さくなる）。Δμ0.01 +1.00（0.351〜0.564）、
              畳み込み +1.00（0.151〜0.277。起点を凍結版と同じにし、核を単位面積にした
              後の出力は別の値になる。lab_log 追記143）、0.65T +1.00（0.396〜0.714）、
              特徴点法 +1.00（0.304〜0.441）

機構: 型3 相当では反射波が前進波に融合するので、真の反射が大きいほど**第1成分が高く
なる**。一方、第2成分は貯留槽の下降の上に固定されて高さが変わらない。したがって比
h2/h1 は**下がる**。

節B（実データ・`--csv` があれば走る）
-------------------------------------
既存の `data/pwdb/pwdb_compare.csv`（26番の出力・確認的解析を回した機械では 4,374 行）の
**列だけを読む。新しい当てはめはしない**（数秒で終わる）。読む列は `age`・`klass_own`・
`dt_v1_ms`（凍結版 ΔT）・`dt_lm_ms`（特徴点法 ΔT・Charlton 同梱）・`ok_v1`（26番の A 段）と、
B4 で `ri_v1`（凍結版 RI）・`digital_ri`（特徴点法 RI・Charlton 同梱）。

  B1  型（`klass_own`）ごとに、凍結版 ΔT と特徴点法 ΔT の分布（5・10・25・50・75・90・95
      パーセンタイルと最小・最大）
  B2  下限の検査。特徴点法 ΔT を 20 ms 刻みの区間に分け、区間ごとに凍結版 ΔT の中央値・
      四分位範囲・人数を出す（特徴点法が短い区間でも凍結版が下がらなければ、下限で詰まって
      いる）。あわせて凍結版 ΔT の最小値・下位 5% と、探索範囲の下限（Δμ 0.08 s ＝ 80 ms）
      との差を印字する
  B3  型ごとに ρ(dt_v1_ms, dt_lm_ms)（年齢層内 Spearman の中央値。**符号つき**。同じ量を
      測っているなら正になるはずで、|ρ| では順位が壊れて負に振れたときに見えなくなる）と、
      特徴点法 ΔT が短い側の半数・長い側の半数に分けたときのそれぞれの ρ
  B4  型ごとに ρ(ri_v1, digital_ri) を**年齢層ごとに 1 行ずつ**並べる（節A-2 の所見を
      実データで見るため。規約は B3・48番 と同じ。A 段を主とし C 段を同じ行に並べる）。
      `ri_v1`・`digital_ri` の列が無い CSV では B4 と P4・P5 だけを飛ばす
  B5  予測との照合（下記 P1〜P5）。**判定は付けない**（事後・記述）

凍結版の列は 26番の A 段（`ok_v1 == 1`。その手法が自分で採用した例だけ）で計算し、C 段
（採否を無視した全例）は参考として添える。48番 節4 の +36.9 ms・+98.5 ms が A 段の値だから
である。年齢層内 Spearman の規約は 26番・48番と共有する（`20_pwdb_validity.py` の
`_spearman`・`_judge` をそのまま読み込む。層は `age` の相異なる値、1 層 8 名以上）。
短い側・長い側は**年齢層ごとに**その層の `dt_lm_ms` の中央値で二分する（層をまたいだ
中央値で切ると、年齢と混ざる）。半数それぞれにも 1 層 8 名以上を要求する。

予測（2026-09-15、実データを見る前に固定した）
----------------------------------------------
(P1) 実データでも凍結版 ΔT には下限の詰まりがある: 型3 で、特徴点法 ΔT が最も短い区間
     （下から 2 区間）でも凍結版 ΔT の中央値は 140 ms を下回らない。根拠: 合成では 150 ms を
     下回る真値に対して返り値が下がらなかった。
(P2) 型3 では、特徴点法 ΔT が短い側の半数の ρ(dt_v1_ms, dt_lm_ms) が、長い側の半数より
     0.15 以上小さい。根拠: 下限で詰まるのは短い側だけなので、順位が壊れるのも短い側である。
(P3) 型1 では (P2) の差が 0.15 未満。根拠: 型1 は真の到達が長く、下限で詰まる範囲に入らない。
(P4) 型3 では、年齢層内の ρ(ri_v1, digital_ri) の中央値が 0.30 未満で、かつ高齢の層ほど
     小さい（75 歳層で 0.20 未満）。根拠: 節A-2 で、型3 相当の条件では凍結版の RI が
     真の反射の大きさと逆に動いた（ρ −0.89）。加齢で切痕が消えるほど型3 の波形に近づく。
(P5) 型1 ではその ρ の中央値が 0.60 以上で、年齢層による傾きがない。根拠: 節A-2 の
     型1 相当では凍結版・特徴点法とも ρ +1.00 で、両者は同じ順位を返した。

P4・P5 も 2026-09-15 に、**実データを見る前に**固定した（節A-2 の合成の結果だけを見て
立てた予測である）。P5 の「年齢層による傾きがない」は、**最も若い層と最も高齢の層の ρ の
差が 0.15 未満**と読む（P2・P3 と同じ 0.15 を使う）。P4 の「高齢の層ほど小さい」は括弧の
とおり **75 歳層の ρ が 0.20 未満**で判定し、年齢と層ごとの ρ の順位相関は記述として
添えるだけにする（規準には使わない）。

予測の本文と数値の規準（140 ms・0.15・下から 2 区間・0.30・0.20・0.60）は 2026-09-15 に
固定したものから変えていない。語だけは用語の決まり（`docs/research/terminology.md`）に
従い「下限で詰まる」と書く。

節C（実データ・`--pwdb` が要る）
---------------------------------
節A・節A-2 で候補になった当てはめの型を、**26番と同じ拍**に当て直す。節B が既存列を読む
だけなのに対し、節C は PWDB の指尖 PPG から当てはめをやり直す。

  入力       PWDB の配布物（`--pwdb`）。拍の作り方は 26番と同一である（20番の
             `load_pwdb` で読み、`beat_of` で 1 拍と標本化周波数を復元し、
             `t = np.arange(y.size) / fs`）。真値（`PWV_a`・`pvr`）と同梱の特徴点
             （`dt_lm_ms`・`digital_ri`）は 23番の `load` で読む（26番と同じ扱い）。
             波形の型 `klass_own` は 26番と同じ手順（`pda2.preprocess` →
             `find_landmarks`）で**この台本が自分で付ける**
  当てはめ   `--variants`（既定 `fb,relax,conv,conv01,trunc` ＝ (0)(2)(4)(4b)(6)）。
             節A と同じ `fit_kind` を呼ぶ。(0) は `src/pda.py` の `fit_beat` そのもので、
             26番の `dt_v1_ms`・`ri_v1`・`ok_v1` と一致するはずである（C0 で照合する）
  記録       `data/pwdb/50_refit.csv`（`--refit-csv` で変えられる。`--limit N` のときは
             `50_refit_limitN.csv`。26番の CSV と同じ規約で、限った実行が全例の記録を
             上書きしない）。列は 型ごとに ΔT・RI・採否・Δμ下限・境界・高さ・別解・τ上限・残差と、
             `subj_no`・`fs`・`n_samp`・`klass_own`・`sys_own_ms`・`dia_own_ms`・
             `why`（失敗の理由。no_beat／preprocess_none／EXC:…）・版（python・numpy・scipy）
  再開       既定で再開する。記録にある被験者のうち、頼まれた型がすべて入っているものは
             飛ばし、足りない型だけを当てて記録を書き直す（`--no-resume` で全部やり直す）
  並べ方     `--limit N` は 26番と同じ**等間隔**の取り方（先頭 N 名ではない。年齢層内で
             読むので全層が要る）。`--jobs J` は 26番と同じ ProcessPoolExecutor

  C0  照合。(0) の ΔT・RI・採否・型が 26番の列（`dt_v1_ms`・`ri_v1`・`ok_v1`・
      `klass_own`）と一致するか（`--csv` があるときだけ）
  C1  型（1・3・4・全）ごとの採否と縮退。通過率（凍結版と同じ収束検算の規則）と、
      Δμ が探索範囲の下限に張り付いた割合・境界・高さ・別解の割合（C 段）
  C2  ΔT × 大動脈脈波伝播速度（`PWV_a`・向き 負）。型 × 当てはめ × 段（A・C）の表。
      ます目は |ρ| の中央値（向きの合った層数／評価できた層数）と 20番 `_judge` の規準
  C3  RI × 末梢血管抵抗（`pvr`・向き 正）。同じ表に加え、型3・A 段の年齢層別 ρ
  C4  同梱の特徴点 ΔT との一致（差の中央値と、年齢層で分けない順位相関）
  C5  予測との照合（下記 P6〜P10）。**判定は付けない**（事後・記述）

年齢層内 Spearman の規約は 26番・48番と共有する（20番の `_by_age`・`_judge`。層は `age` の
相異なる値、1 層 8 名以上）。A 段はその当てはめが自分で採用した例だけ（`ok_{型} == 1`）、
C 段は採否を無視した全例である。参考として 26番の凍結版の列と同梱の特徴点を同じ表に並べる。

予測（2026-09-15、実装の前・実データを見る前に固定した。lab_log 追記143）
------------------------------------------------------------------------
(P6) 型3・A 段: (4) conv の ΔT × PWV_a が `_judge` の規準を満たす（|中央値| ≥ 0.30 かつ
     全層で符号が合う）。根拠: 合成の型3 相当で (4) だけが順位を追い、縮退しなかった。
(P7) 型3・C 段: (2) relax の Δμ 下限張り付きの割合が (4) conv より 0.10 以上大きい。
     根拠: 合成の型3 相当で (2) は 7/7 拍が下限に張り付き、(4) は 0/7 であった。
(P8) 型3・A 段: (4) conv の RI × pvr で 75 歳層の ρ > 0 かつ |中央値| ≥ 0.30。
     根拠: 節A-2 で凍結版の RI は型3 相当で符号が反転し、(4) は +1.00 であった。
(P9) 型1・A 段: (4) conv の ΔT × PWV_a が `_judge` の規準を満たす。
     根拠: 合成の型1 相当ではどの型も順位を追えた。
(P10) 検算: (0) fb の ΔT・RI・採否が 26番の列と全例一致、かつ同梱の特徴点の型別
     ρ(dt_lm_ms, PWV_a) が 型1 0.343・型3 0.430（小数 3 桁で一致）を再現
     （26番の列が無ければ「照合できない」）。根拠: (0) は `fit_beat` そのものであり、
     型別 ρ は 48番が同じ入力から出した値である（lab_log 追記137）。

所要（実測して直した。2026-09-15）: **1 名あたり 5 型で約 3.9 秒**（この環境・1 コア・
起点 8 点。畳み込みの 2 型が母数 10 個で重い）。4,374 名では **1 コアで約 4.7 時間、
`--jobs 8` で 35〜40 分**である。最初に書いた「10 分前後」は 1 当てはめ 0.16 秒という
低い見積もりから出した誤りで、実測に置き換えた。

**進み具合を 200 名ごとに印字し、400 名ごとに途中の記録を書く**（`PROGRESS_EVERY`・
`CKPT_EVERY`）。印字が無いと止まっているように見えるため 2026-09-15 に足した。
記録があれば再開するので、途中で止めてもやり直しにはならない。
**節C が書き込むのは自分の記録（50_refit[_limitN].csv）だけである。**

前提と限界
----------
合成脈波は監督者が作ったもので PWDB ではない。反射波の幅と到達の結び付け方は仮定である。
1 層 10 拍なので ρ の差（0.71 対 0.89）は 1〜2 組の入れ替わりに当たる。RI は測っていない。
節B の CSV が抜粋（この環境の複製は 24 行）だと 1 層 8 名に満たず、どの ρ も計算できない。
その場合も落ちずに「—」と人数不足を印字するが、**その数値は読んではいけない。**

版は確認的解析と同じにそろえる（Python 3.9.6・NumPy 2.0.2・SciPy 1.13.1・pandas 2.3.3）。

使い方
------
    python3 scripts/50_reservoir_bench.py --selftest
    python3 scripts/50_reservoir_bench.py
    python3 scripts/50_reservoir_bench.py --csv data/pwdb/pwdb_compare.csv
    python3 scripts/50_reservoir_bench.py --section B --csv data/pwdb/pwdb_compare.csv
    python3 scripts/50_reservoir_bench.py --section ABC --pwdb ~/pwdb --jobs 8 --csv data/pwdb/pwdb_compare.csv

`--section A|B|C|AB|AC|BC|ABC`（既定 AB。CSV が無ければ A だけ。C は `--pwdb` が要る）。
節C の細かい指定は `--limit`・`--jobs`・`--variants`・`--refit-csv`・`--no-resume`。
`--fast` は節A の掃引を 2 層 × 5 拍に
減らす（自己検査と同じ掃引。本番の表ではない）。自己検査は合成だけで走る（CSV もネット
ワークも要らない）。節A（3 層 × 10 拍）＋ 節A-2（2 条件 × 7 拍）の本番は、当てはめ 10 行で
この環境では約 80 秒である（`--section A` を 3 回計った実測は 82・79・77 秒。CSV は要らない）。
2026-09-15 に起点を 8 点・max_nfev を 4000 に上げた（凍結版と同じにした）ので、それまでの
約 40 秒からおよそ倍になっている。
結果は print するので、残すときは tee で `docs/research/results/50_reservoir_bench.txt` に
落とす。

終了コード 0 = 通常、2 = 節B を頼まれたのに CSV が無い・要る列が無い、
または節C を頼まれたのに `--pwdb` が無い・PWDB を読めない。
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import sys
import unicodedata
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import pda                       # noqa: E402  (0) が呼ぶ凍結版本体（fit_beat）
from src import pda2                      # noqa: E402  ROOT を通してから読む
from src.pda import skew_gaussian         # noqa: E402  凍結版と同じ歪みガウス


def _load(stem: str, name: str):
    """数字始まりの台本を名前で読み込む（import 文では書けない）。45番・48番と同じ手口。"""
    p = Path(__file__).resolve().parent / stem
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# 順位相関の規約は 20番のものをそのまま使う（自前で書き直さない。26番・45番・48番と同じ）
M = _load("20_pwdb_validity.py", "m20")

DATA = ROOT / "data"
DEFAULT_CSV = DATA / "pwdb" / "pwdb_compare.csv"

MIN_PER_AGE = 8        # 1 年齢層に要る人数。26番・45番・48番の MIN_PER_AGE と同じ
N_AGES_FULL = 6        # PWDB の年齢層（25・35・45・55・65・75 歳）


# ---------------------------------------------------------------- 表示の部品
def _pad(s, w: int, right: bool = False) -> str:
    """表示幅で揃える（日本語は 2 文字分。f 文字列の桁指定は文字数なのでずれる）。"""
    used = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in str(s))
    fill = " " * max(0, w - used)
    return (fill + str(s)) if right else (str(s) + fill)


def _f(v: float, w: int = 9, prec: int = 3, sign: bool = False) -> str:
    if not np.isfinite(v):
        return _pad("—", w, right=True)
    return f"{v:>+{w}.{prec}f}" if sign else f"{v:>{w}.{prec}f}"


def _n(v: float, prec: int = 3, sign: bool = False) -> str:
    """文中に埋める数値（桁揃えをしない）。"""
    if not np.isfinite(v):
        return "—"
    return f"{v:+.{prec}f}" if sign else f"{v:.{prec}f}"


def _yn(b: bool) -> str:
    return "はい" if b else "いいえ"


def _ari(b: bool) -> str:
    return "あり" if b else "なし"


# ================================================================ 節A（合成）
# 合成脈波の母数。監督者の試作（scratchpad/bench.py）と同じ値で、変えると節A の数値が変わる。
FS = 500.0                 # 標本化周波数 [Hz]
HR_SYN = 70.0              # 心拍数 [1/min]。拍長 T = 60 / HR
TP_F = 0.12                # 前進波のピークの目安 [s]
A_FWD, SIG_FWD, AL_FWD = 1.0, 0.045, 2.5     # 前進波（歪みガウス）の高さ・幅・歪度
A_REF = 0.45               # 反射波の高さ
W_REF_A, W_REF_B = 0.055, 0.16   # 反射波の幅 = W_REF_A + W_REF_B × 到達 [s]
AL_REF = 1.2               # 反射波の歪度（早く到達する拍では 0 にする）
DT_SKEW = 0.18             # 到達がこれ以下なら歪度 0（硬い血管の、幅が広く対称な反射波）
D_RES = 0.45               # 貯留槽の大きさ
RES_PEAK_LAG = 0.05        # 貯留槽が減衰に入る時刻 = 前進波のピーク + 到達 + これ [s]
RES_MAX_FRAC = 0.55        # ただし拍長のこの割合を超えない
NOISE_SD = 0.002           # 雑音の標準偏差

# 当てはめの型。(鍵, 番号, 表の見出し, 説明)
# 番号は波形の型（klass_own）と混ざらないよう括弧付きで書く。(5)(6) は形の拘束・
# 打ち切りに加えて Δμ の下限も 0.01 s に緩めてある（2 つ変わっている）。
# (5b)(6b) は同じ拘束・打ち切りで Δμ の下限を凍結版のまま 0.08 s にした版で、
# **一度に 1 つだけ変えたときの効き**を読むために 2026-09-15 に足した。
# (4b) と (0) も 2026-09-15 に足した。(4b) は「Δμ を緩める・貯留槽を畳み込みで持つ、の
# 2 つをそれぞれと同時に適用したときの結果を出すのか」に答えるための行で、(2) と (4) を
# 同時に適用したものである。(0) は `src/pda.py` の `fit_beat` をそのまま呼ぶ行で、
# 写した複製 (1) が本体と同じ振る舞いをすることの照合である。
# (1) 以降の起点の作り方と解の選び方は `fit_beat` と同じにしてある（2026-09-15 に
# そろえた。lab_log 追記143）。各行が凍結版から**狙った 1 つだけ**違うようにするため。
KINDS = [
    ("fb", "(0)", "凍結版本体",
     "凍結版そのもの（`src/pda.py` の `fit_beat` を既定の引数で呼ぶ。起点 8 点・"
     "特徴点近傍の解を優先する規則・max_nfev 4000）。(1) はこれを写した複製で、"
     "(0) は複製が本体と同じ振る舞いをすることの照合（2026-09-15 に足した）"),
    ("frozen", "(1)", "凍結版", "凍結版 2 カーネル（src/pda.py と同じ探索範囲・Δμ の下限 0.08 s）"),
    ("relax", "(2)", "Δμ0.01", "Δμ の下限を 0.01 s に緩める（ほかは凍結版のまま）"),
    ("decay", "(3)", "減衰項", "自由な指数減衰を足す（24番 A1 と同じ形・d·exp(−(t−t0)/τ)）"),
    ("conv", "(4)", "畳み込み", "貯留槽を前進波の畳み込みで持つ（res = g·∫g1(s)·e^{−(t−s)/τ}ds/τ・核は単位面積）"),
    ("conv01", "(4b)", "畳み込み",
     "同じ畳み込みで Δμ の下限を 0.01 s に緩める（(2) と (4) の同時適用。2026-09-15 に足した）"),
    ("tied", "(5)", "形を縛る", "第2成分の形を第1成分に縛る（σ2 = c·σ1・α2 = α1）＋ Δμ の下限 0.01 s"),
    ("tied08", "(5b)", "形を縛る", "同じ形の拘束で、Δμ の下限は凍結版のまま 0.08 s"),
    ("trunc", "(6)", "0.65T", "0.65T までで当てはめる ＋ Δμ の下限 0.01 s"),
    ("trunc08", "(6b)", "0.65T", "同じ打ち切りで、Δμ の下限は凍結版のまま 0.08 s"),
]
KIND_KEYS = [k for k, _no, _h, _l in KINDS]
KIND_NO = {k: no for k, no, _h, _l in KINDS}
KIND_HEAD = {k: h for k, _no, h, _l in KINDS}
KIND_LABEL = {k: l for k, _no, _h, l in KINDS}

# 模型の形（母数の並び）と、当てはめに使う範囲。(5b) は (5) と、(6b) は (6) と、
# (4b) は (4) と同じ形で、違うのは Δμ の下限だけである。(0) の形「fb」はこの台本の模型を
# 使わないという印で、`_bounds`・`_frozen_starts`・`_model` は (0) では呼ばない。
KIND_SHAPE = {"fb": "fb", "frozen": "plain", "relax": "plain", "decay": "decay",
              "conv": "conv", "conv01": "conv",
              "tied": "tied", "tied08": "tied", "trunc": "plain", "trunc08": "plain"}
KIND_TRUNC = ("trunc", "trunc08")

# 当てはめの設定。凍結版と同じ探索範囲を使う型と、Δμ の下限を緩める型を分ける。
DMU_LO_FROZEN = 0.08       # `src/pda.py` の dmu_bounds の下限 [s]
DMU_LO_RELAX = 0.01
# (0) の Δμ の下限も凍結版と同じ 0.08 s（`fit_beat` の既定）だが、下限は `fit_beat` の側に
# あり、この台本の `_bounds` は (0) では使わない。(4b) は下限だけを DMU_LO_RELAX にする。
KIND_DMU_FROZEN = ("fb", "frozen", "decay", "conv", "tied08", "trunc08")
N_STARTS = 8               # 起点の数（fit_beat と同じ）
MAX_NFEV = 4000            # fit_beat と同じ
SEED_STARTS = 0            # 起点の乱数の種（fit_beat の既定と同じ）
# 解の選択（fit_beat と同じ）: RSS 最小を基本に、特徴点近傍（|Δμ − dmu0| ≤ NEAR_DMU）の
# 解が RSS 最小の NEAR_RSS 倍以内にあればそちらを採る。
NEAR_DMU = 0.06
NEAR_RSS = 1.10
# 収束検算の規準（fit_beat と同じ値）。**この節では採否に使わず、診断として数えるだけ。**
CHK_TOL = 1e-3             # 境界に張り付いたと見なす幅
CHK_AMP = 0.02             # 成分のピーク高さがこれ未満なら「高さ<0.02」（正規化した尺度）
CHK_RSS = 1.15             # 競合解と見なす RSS の比
CHK_DMU = 0.03             # 競合解と見なす Δμ の差 [s]
CHK_RI = 0.08              # 競合解の RI がこれ以上違えば「別解」
TRUNC_FRAC = 0.65          # (6)(6b) が当てはめに使う範囲（拍長に対する割合）
# 貯留槽項（(3)(4)(4b)）の母数の探索範囲と起点。凍結版には無い母数なので、凍結版の閾値では
# ない。2026-09-15 までは τ ∈ [0.05, 1.50]・畳み込みの g ≤ 3.0（面積 τ の核）・減衰の d ≤ 1.0
# だったが、診断で g が 3.0 に、τ が 1.50 に張り付く拍が系統的に出たので、核を単位面積にして
# g の上限を 10、τ の上限を 3.0 s に広げた（実データを見る前の変更。lab_log 追記143）。
# τ が上限に張り付くのは合成脈波の貯留槽が反射波の後で立ち上がる形（synth_beat）に
# 畳み込みが合わないためで、その拍は診断の「境界」に数えられる。
RES_TAU_LO, RES_TAU_HI = 0.05, 3.0
RES_G_HI = 10.0            # 畳み込みの倍率 g の上限（単位面積の核に対して）
RES_D_HI = 1.0             # 減衰項の大きさ d の上限（正規化した拍の尺度）
RES_G0, RES_TAU0 = 1.0, 0.35   # 起点（g は単位面積の核に合わせて 1.0）

# 掃引
TAUS_FULL = (0.45, 0.35, 0.25)
DTS_FULL = (0.30, 0.27, 0.24, 0.21, 0.18, 0.16, 0.14, 0.12, 0.10, 0.08)
TAUS_FAST = (0.45, 0.35)
# 自己検査の掃引。下位 3 拍を本番と同じ到達（0.12・0.10・0.08 s）にそろえてある。
# 下限の詰まりは下位 3 拍で測るので、ここが本番と違うと同じものを検査できない。
DTS_FAST = (0.24, 0.18, 0.12, 0.10, 0.08)
SEED_A = 0                 # 雑音の乱数種。拍ごとに同じ種を使う（試作と同じ）

MIN_BEATS_A = 3            # 節A の ρ を計算するのに要る拍数（節B の 8 名以上とは別）
FLOOR_N = 3                # 下限の詰まりを見る拍数（真値の小さいほうから）
# いま使う規準（2026-09-15 に差し替えた）: その 3 拍の**返り値の最小**が、その 3 拍の
# **真値の最大**より FLOOR_GAP_MS 以上大きいとき「あり」。
FLOOR_GAP_MS = 30.0
# 差し替える前の規準（参考として表に残す）: その 3 拍の返り値の範囲が FLOOR_RANGE_MS
# 未満なら「あり」。凍結版は返り値が下限の手前で折り返すので、範囲では取り逃がす。
FLOOR_RANGE_MS = 20.0


def synth_beat(dt_true: float, tau: float, seed: int = SEED_A, hr: float = HR_SYN,
               a_ref: float = A_REF):
    """前進波（歪みガウス）＋ 反射波（歪みガウス）＋ 貯留槽（指数減衰）の 1 拍を作る。

    反射波は早く到達するほど幅が広くなり歪みが消える（硬い血管の波形）。
    ΔT の真値は**反射波のピーク − 前進波のピーク**で、母数（μ）の差ではない。幅と歪度が
    到達によって変わるので、両者は一致しない。`a_ref` は反射波の大きさの母数で、節A-2 が
    これを振る（既定は A_REF で、節A の掃引はこれまでと同じ波形になる）。RI の真値として
    成分のピーク高さの比 `ri_peak` も返す（当てはめが返す h2/h1 と同じ定義）。
    """
    T = 60.0 / hr
    t = np.arange(0.0, T, 1.0 / FS)
    w_ref = W_REF_A + W_REF_B * dt_true
    al_ref = AL_REF if dt_true > DT_SKEW else 0.0
    fwd = skew_gaussian(t, A_FWD, TP_F - 0.02, SIG_FWD, AL_FWD)
    ref = skew_gaussian(t, a_ref, TP_F + dt_true - 0.02, w_ref, al_ref)
    t_a = min(RES_MAX_FRAC * T, TP_F + dt_true + RES_PEAK_LAG)
    rise = np.clip(t / max(t_a, 1e-6), 0.0, 1.0) ** 2
    res = D_RES * rise * np.exp(-np.maximum(t - t_a, 0.0) / tau)
    y = fwd + ref + res
    y = y + NOISE_SD * np.random.default_rng(seed).standard_normal(y.size)
    i_ref, i_fwd = int(np.argmax(ref)), int(np.argmax(fwd))
    t_ref, t_fwd = float(t[i_ref]), float(t[i_fwd])
    h_ref, h_fwd = float(ref[i_ref]), float(fwd[i_fwd])
    return t, y, {"dt_s": t_ref - t_fwd, "t_ref": t_ref, "t_fwd": t_fwd,
                  "tau": tau, "dt_set": dt_true, "a_ref": a_ref,
                  "h_ref": h_ref, "h_fwd": h_fwd,
                  "ri_peak": h_ref / max(h_fwd, 1e-12)}


def _norm(y: np.ndarray) -> np.ndarray:
    """当てはめの前に 0〜1 に正規化する（凍結版 `fit_beat` と同じ扱い）。"""
    y = np.asarray(y, float)
    y = y - float(np.min(y))
    return y / max(float(np.max(y)), 1e-12)


def _reject_fb(kind: str) -> None:
    """(0) は `src/pda.py` の `fit_beat` をそのまま呼ぶ型なので、この台本の探索範囲・
    起点・模型は使わない。取り違えたときに黙って別の当てはめにならないよう、ここで止める。
    """
    if kind == "fb":
        raise ValueError("型 fb（(0) 凍結版本体）は src/pda.py の fit_beat を直接呼ぶ。"
                         "_bounds・_frozen_starts・_model は使えない")


def _bounds8(t: np.ndarray, ys: np.ndarray, dmu_lo: float):
    """8 母数 (a1, mu1, sigma1, alpha1, a2, Δμ, sigma2, alpha2) の探索範囲。

    式は `src/pda.py` の `fit_beat` と同じで、Δμ の下限だけを型に応じて渡す
    （凍結版のままなら 0.08 s、緩める型は 0.01 s）。
    """
    T = float(t[-1] - t[0])
    t_pk = float(t[int(np.argmax(ys))])
    lo = [0.05, 0.02, 0.015, 0.0, 0.02, dmu_lo, 0.015, 0.0]
    hi = [2.50, max(0.60 * T, t_pk + 0.05), 0.30, 8.0,
          2.00, min(0.60, 0.85 * T), 0.35, 8.0]
    return lo, hi


def _bounds(t: np.ndarray, ys: np.ndarray, kind: str):
    """型ごとの探索範囲。8 母数の並びは `src/pda.py` と同じ

    (a1, mu1, sigma1, alpha1, a2, Δμ, sigma2, alpha2)。型5 は末尾 2 つを σ の比 c に
    置き換え（7 母数）、型3・型4 は減衰の (g, τ) を足す（10 母数）。(0) はこの探索範囲を
    使わないので、呼ばれたら ValueError で止める。
    """
    _reject_fb(kind)
    shape = KIND_SHAPE[kind]
    dmu_lo = DMU_LO_FROZEN if kind in KIND_DMU_FROZEN else DMU_LO_RELAX
    lo, hi = _bounds8(t, ys, dmu_lo)
    if shape == "tied":
        lo, hi = lo[:6] + [0.5], hi[:6] + [4.0]
    elif shape == "decay":
        lo, hi = lo + [0.0, RES_TAU_LO], hi + [RES_D_HI, RES_TAU_HI]
    elif shape == "conv":
        lo, hi = lo + [0.0, RES_TAU_LO], hi + [RES_G_HI, RES_TAU_HI]
    return lo, hi, dmu_lo


def _components(p, kind: str):
    """母数から 2 成分（歪みガウス 4 母数ずつ）を取り出す。"""
    c1 = (p[0], p[1], p[2], p[3])
    if KIND_SHAPE[kind] == "tied":
        c2 = (p[4], p[1] + p[5], p[2] * p[6], p[3])
    else:
        c2 = (p[4], p[1] + p[5], p[6], p[7])
    return c1, c2


def _model(p, tt: np.ndarray, kind: str) -> np.ndarray:
    _reject_fb(kind)
    c1, c2 = _components(p, kind)
    out = skew_gaussian(tt, *c1) + skew_gaussian(tt, *c2)
    shape = KIND_SHAPE[kind]
    if shape == "decay":
        out = out + p[8] * np.exp(-(tt - tt[0]) / max(p[9], 1e-3))
    elif shape == "conv":
        # 核は単位面積（∫e^{−s/τ}ds/τ = 1）にする。g は「前進波を時定数 τ で平滑した
        # 波形」に掛ける倍率で、τ が変わっても g の意味が変わらない。
        # 2026-09-15 までは面積 τ の核で g ≤ 3 としていたが、診断で g が上限に張り付いた
        # ので単位面積に直し、上限も広げた（lab_log 追記143）。
        g1 = skew_gaussian(tt, *c1)
        dt = float(tt[1] - tt[0])
        tau_r = max(p[9], 1e-3)
        kern = np.exp(-(tt - tt[0]) / tau_r) * (dt / tau_r)
        out = out + p[8] * np.convolve(g1, kern)[:tt.size]
    return out


def _frozen_starts(t: np.ndarray, ys: np.ndarray, lo, hi, kind: str,
                   seed: int = SEED_STARTS):
    """起点を `src/pda.py` の `fit_beat` と同じ手順で作る。返り値は (起点の並び, dmu0)。

    `fit_beat` は Δμ の初期値 dmu0 を特徴点から決める（主ピーク後の −d²y/dt² 最小点に
    0.02 s を足した時刻。探索範囲の内側に収める）。そこから

        base0（特徴点から決めた 1 点）
        ＋ Δμ の格子 5 点（0.12・0.18・0.26・0.36・0.48 s）
        ＋ 乱数で振った 2 点（乱数の種は `fit_beat` の既定と同じ）

    の N_STARTS 点を作る。dmu0 は解を選ぶときにも使うので一緒に返す。

    8 母数（a1, mu1, sigma1, alpha1, a2, Δμ, sigma2, alpha2）まではどの型でも同じ手順で
    作り、型ごとの母数（減衰・畳み込みの g と τ、形を縛る型の σ の比 c）は**そのあとで**
    足す。先に足すと乱数の並びが型によってずれ、同じ拍でも起点が変わってしまう。型ごとの
    母数は乱数で振らない。

    (0) は `fit_beat` が自分で起点を作るので、ここには来ない。
    """
    _reject_fb(kind)
    shape = KIND_SHAPE[kind]
    lo8, hi8 = _bounds8(t, ys, float(lo[5]))
    lo8, hi8 = np.asarray(lo8, float), np.asarray(hi8, float)
    i_pk = int(np.argmax(ys))
    t_pk = float(t[i_pk])

    # 反射波の位置の初期値: 主ピーク後の −d²y/dt² 最小点（`fit_beat` と同じ式）
    d2 = np.gradient(np.gradient(ys))
    j0 = i_pk + max(int(0.06 * len(t)), 3)
    j1 = int(0.85 * len(t))
    dmu0 = 0.22
    if j0 < j1:
        j = j0 + int(np.argmin(d2[j0:j1]))
        dmu0 = float(np.clip(t[j] - t_pk + 0.02, lo8[5] + 0.01, hi8[5] - 0.01))

    rng = np.random.default_rng(seed)
    base0 = np.array([1.0, max(t_pk - 0.02, 0.05), 0.06, 2.0, 0.45, dmu0, 0.09, 1.0])
    base0 = np.clip(base0, lo8 + 1e-6, hi8 - 1e-6)
    base = [base0]
    for dg in (0.12, 0.18, 0.26, 0.36, 0.48):
        b = base0.copy()
        b[5] = np.clip(dg, lo8[5] + 1e-6, hi8[5] - 1e-6)
        base.append(b)
    while len(base) < max(N_STARTS, 6):
        base.append(np.clip(
            base0 * rng.uniform(0.7, 1.3, size=8)
            + np.array([0, 0.02, 0, 0.5, 0, 0.05, 0, 0.5]) * rng.standard_normal(8),
            lo8 + 1e-6, hi8 - 1e-6))

    def _inside(v: float, i: int) -> float:
        """型ごとの母数を、その母数の探索範囲の内側に収める。"""
        return float(np.clip(v, lo[i] + 1e-6, hi[i] - 1e-6))

    out = []
    for b in base:
        if shape == "tied":
            x0 = list(b[:6]) + [_inside(1.6, 6)]                    # σ の比 c
        elif shape in ("decay", "conv"):
            x0 = list(b) + [_inside(RES_G0, 8), _inside(RES_TAU0, 9)]   # 貯留槽の g と τ
        else:
            x0 = list(b)
        out.append(x0)
    return out, dmu0


def _ri_of(x, kind: str, t0: float, t1: float) -> float:
    """解 1 つぶんの RI（第2成分／第1成分のピーク高さの比）。

    ピークは凍結版と同じ `pda.component_peak`（4,000 点の格子）で探す。
    """
    c1, c2 = _components(x, kind)
    _tp1, h1 = pda.component_peak(c1, t0, t1)
    _tp2, h2 = pda.component_peak(c2, t0, t1)
    return h2 / max(h1, 1e-9)


def _checks_fail() -> dict:
    """当てはめそのものが成らなかった拍の診断（通過しなかったとだけ記録する）。"""
    return {"dmu_lo": False, "boundary": False, "amp_zero": False,
            "ambiguous": False, "tau_hi": False, "ok": False}


def _diagnose(sols, best, kind: str, lo, hi, h1: float, h2: float,
              t0: float, t1: float) -> dict:
    """凍結版 `fit_beat` の収束検算と同じ規則を解に当てる。**記録するだけで採否に使わない。**

    返す印は次の 5 つ。

        dmu_lo     Δμ が探索範囲の下限に張り付いた（2 成分の縮退の目安。`fit_beat` には
                   無い印で、この台本が下限の詰まりを数えるために足した）
        boundary   母数が探索範囲の端から CHK_TOL 以内にある（`fit_beat` の
                   boundary_stick）。歪度 α の下限（＝ 0・対称ガウス）は正当な解なので
                   除く。減衰・畳み込みの型では貯留槽の大きさ g の下限（＝ 0・貯留槽
                   なし）と時定数 τ の上限（拍の中で減衰しない貯留槽。α = 0 と同じく
                   模型として定義できる極限）も除き、τ の上限は別の印 tau_hi で数える
                   （2026-09-15・実データを見る前に決めた。lab_log 追記143）。
                   τ の下限・σ の比 c の両端・g の上限は見る
        tau_hi     減衰・畳み込みの型で τ が探索範囲の上限に張り付いた（記述のみ）
        amp_zero   成分のピーク高さの小さいほうが CHK_AMP 未満（`fit_beat` の amp_zero）
        ambiguous  RSS が CHK_RSS 倍以内で Δμ が CHK_DMU 以上離れ、RI も CHK_RI 以上
                   違う解がある（`fit_beat` の reproducible の否定）
        ok         boundary・amp_zero・ambiguous のいずれでもない（`fit_beat` の ok）
    """
    p = np.asarray(best.x, float)
    lo_a, hi_a = np.asarray(lo, float), np.asarray(hi, float)
    skip_lo = {3}                            # α1 の下限（対称ガウスは正当な解）
    if KIND_SHAPE[kind] != "tied":
        skip_lo.add(7)                       # α2 の下限（同上。形を縛る型に α2 は無い）
    if KIND_SHAPE[kind] in ("decay", "conv"):
        skip_lo.add(8)                       # g の下限（g = 0 は「貯留槽なし」の解）
    lo_hit = np.abs(p - lo_a) < CHK_TOL
    for i in skip_lo:
        lo_hit[i] = False
    hi_hit = np.abs(p - hi_a) < CHK_TOL
    tau_hi = False
    if KIND_SHAPE[kind] in ("decay", "conv"):
        tau_hi = bool(hi_hit[9])             # τ の上限は境界に数えず、別の印にする
        hi_hit[9] = False
    boundary = bool(np.any(lo_hit) or np.any(hi_hit))
    ri_best = h2 / max(h1, 1e-9)
    ambiguous = any(abs(_ri_of(r.x, kind, t0, t1) - ri_best) > CHK_RI for r in sols
                    if r.cost <= best.cost * CHK_RSS
                    and abs(r.x[5] - p[5]) > CHK_DMU)
    amp_zero = bool(min(h1, h2) < CHK_AMP)
    return {"dmu_lo": bool(p[5] - lo_a[5] < CHK_TOL),
            "boundary": boundary, "amp_zero": amp_zero, "ambiguous": bool(ambiguous),
            "tau_hi": tau_hi,
            "ok": bool((not boundary) and (not amp_zero) and (not ambiguous))}


def fit_kind(t: np.ndarray, y: np.ndarray, kind: str) -> dict:
    """1 拍を型 `kind` で当てはめ、ΔT [s]・RI・残差・診断を返す。

    **収束検算（境界張り付き・別解の有無）は採否に課さない。**この節が見たいのは真値の
    順位を追えるかどうかで、採否ではない（凍結版の採否は 26番の A 段が決めている）。
    ただし凍結版と同じ規則を診断として当て、`checks` に入れて返す（`_diagnose`）。

    起点の作り方（`_frozen_starts`）・解の選び方・max_nfev・成分のピークの求め方
    （`pda.component_peak`）は `fit_beat` と同じにしてある。各行が凍結版から**狙った
    1 つだけ**違うようにするためである。

    型 `fb`（(0) 凍結版本体）だけは `src/pda.py` の `fit_beat` を既定の引数でそのまま
    呼ぶ。正規化は `fit_beat` が中で行うので生の y を渡す（`_norm` と同じ扱いである）。
    `fit_beat` が返す収束検算の結果はそのまま `checks` に写す。
    """
    if kind == "fb":
        try:
            r = pda.fit_beat(t, y)
            c1, c2 = r["components"][0], r["components"][1]
            ck = r["checks"]
            return {"dt_s": float(c2["t_peak"] - c1["t_peak"]),
                    "ri": float(c2["height"]) / max(float(c1["height"]), 1e-9),
                    "ok": bool(r["ok"]), "cost": float(r["rss"]) / 2.0,
                    "checks": {
                        "dmu_lo": bool(float(r["params"][5]) - DMU_LO_FROZEN < CHK_TOL),
                        "tau_hi": False,
                        "boundary": bool(ck["boundary_stick"]),
                        "amp_zero": bool(ck["amp_zero"]),
                        "ambiguous": bool(not ck["reproducible"]),
                        "ok": bool(r["ok"])}}
        except Exception:
            return {"dt_s": float("nan"), "ri": float("nan"), "ok": False,
                    "cost": float("nan"), "checks": _checks_fail()}
    ys = _norm(y)
    lo, hi, _dmu_lo = _bounds(t, ys, kind)
    if kind in KIND_TRUNC:
        keep = t <= t[0] + TRUNC_FRAC * (t[-1] - t[0])
        tfit, yfit = t[keep], ys[keep]
    else:
        tfit, yfit = t, ys
    starts, dmu0 = _frozen_starts(t, ys, lo, hi, kind, SEED_STARTS)
    sols = []
    for x0 in starts:
        try:
            r = least_squares(lambda p: _model(p, tfit, kind) - yfit, x0,
                              bounds=(lo, hi), method="trf", max_nfev=MAX_NFEV)
        except Exception:
            continue
        sols.append(r)
    if not sols:
        return {"dt_s": float("nan"), "ri": float("nan"), "ok": False,
                "cost": float("nan"), "checks": _checks_fail()}
    # 解の選択も `fit_beat` と同じ: RSS 最小を基本に、特徴点近傍（|Δμ − dmu0| ≤ NEAR_DMU）
    # の解が RSS 最小の NEAR_RSS 倍以内にあればそちらを採る。
    gmin = min(sols, key=lambda r: r.cost)
    near = [r for r in sols
            if abs(r.x[5] - dmu0) <= NEAR_DMU and r.cost <= gmin.cost * NEAR_RSS]
    best = min(near, key=lambda r: r.cost) if near else gmin
    t0f, t1f = float(t[0]), float(t[-1])
    c1, c2 = _components(best.x, kind)
    tp1, h1 = pda.component_peak(c1, t0f, t1f)
    tp2, h2 = pda.component_peak(c2, t0f, t1f)
    return {"dt_s": tp2 - tp1, "ri": h2 / max(h1, 1e-9), "ok": True,
            "cost": float(best.cost),
            "checks": _diagnose(sols, best, kind, lo, hi, h1, h2, t0f, t1f)}


def fiducial_dt(t: np.ndarray, y: np.ndarray) -> dict:
    """参考: 特徴点法（`pda2.preprocess` → `find_landmarks`）の ΔT = dia_t − sys_t。"""
    ys, _amp = pda2.preprocess(t, y, FS)
    if ys is None:
        return {"dt_s": float("nan"), "ri": float("nan"), "klass": -1}
    lm = pda2.find_landmarks(t, ys)
    klass = int(lm["klass"])
    if not (np.isfinite(lm["dia_t"]) and np.isfinite(lm["sys_t"])):
        return {"dt_s": float("nan"), "ri": float("nan"), "klass": klass}
    return {"dt_s": float(lm["dia_t"] - lm["sys_t"]),
            "ri": float(lm["dia_v"] / max(lm["sys_v"], 1e-12)), "klass": klass}


def sweep(taus, dts, seed: int = SEED_A, kinds=None) -> dict:
    """時定数 × 到達の掃引。返り値は時定数ごとの真値・返り値・型（すべて ms）。

    `checks` は当てはめの型ごとに、凍結版と同じ収束検算の規則を当てた結果（`fit_kind` の
    `checks`）を拍ごとに並べたものである。**記録するだけで採否には使わない**（(0) は
    `fit_beat` 自身の検算）。
    """
    kinds = list(KIND_KEYS) if kinds is None else list(kinds)
    out = {}
    for tau in taus:
        rec = {"tau": float(tau), "dt_set": [], "truth": [], "klass": [], "fid": [],
               "checks": dict((k, []) for k in kinds),
               "got": dict((k, []) for k in kinds)}
        for dt in dts:
            t, y, tr = synth_beat(dt, tau, seed=seed)
            rec["dt_set"].append(1000.0 * dt)
            rec["truth"].append(1000.0 * tr["dt_s"])
            for k in kinds:
                r = fit_kind(t, y, k)
                rec["checks"][k].append(r["checks"])
                rec["got"][k].append(1000.0 * r["dt_s"] if np.isfinite(r["dt_s"])
                                     else float("nan"))
            f = fiducial_dt(t, y)
            rec["fid"].append(1000.0 * f["dt_s"] if np.isfinite(f["dt_s"])
                              else float("nan"))
            rec["klass"].append(f["klass"])
        out[float(tau)] = rec
    return out


def floor_check(truth_ms, got_ms) -> dict:
    """下限の詰まり。真値の小さいほうから FLOOR_N 拍を取って 2 通りの規準で測る。

    いま使う規準（`flag_gap`。2026-09-15 に差し替えた）
        その 3 拍の**返り値の最小**が、その 3 拍の**真値の最大**より FLOOR_GAP_MS 以上
        大きいとき「あり」。返り値がどれだけ下に行けないかを直接測る。
    差し替える前の規準（`flag_range`。参考として表に残す）
        その 3 拍の返り値の範囲が FLOOR_RANGE_MS 未満なら「あり」。凍結版は返り値が
        下限の手前で折り返すので（真値 98 ms で 132 ms、78・58 ms で 174 ms）、
        範囲は広く出て取り逃がす。

    `got_min` は掃引の全拍を通した返り値の最小で、真値の最小と並べて読む。
    """
    truth = np.asarray(truth_ms, float)
    got = np.asarray(got_ms, float)
    order = np.argsort(truth)[:FLOOR_N]
    v = got[order]
    tv = truth[order]
    fin = v[np.isfinite(v)]
    all_fin = got[np.isfinite(got)]
    out = {"n": int(fin.size), "lo": float("nan"), "hi": float("nan"),
           "rng": float("nan"), "gap": float("nan"),
           "truth_rng": float(np.max(tv) - np.min(tv)),
           "truth_max": float(np.max(tv)), "flag_gap": False, "flag_range": False,
           "got_min": float("nan"),
           "truth_min": float(np.min(truth)) if truth.size else float("nan")}
    if all_fin.size:
        out["got_min"] = float(np.min(all_fin))
    if fin.size >= 2:
        out["lo"], out["hi"] = float(np.min(fin)), float(np.max(fin))
        out["rng"] = out["hi"] - out["lo"]
        out["gap"] = out["lo"] - out["truth_max"]
        out["flag_gap"] = bool(out["gap"] >= FLOOR_GAP_MS)
        out["flag_range"] = bool(out["rng"] < FLOOR_RANGE_MS)
    return out


def summarise_a(res: dict) -> dict:
    """型 × 時定数の (ρ, |誤差| 中央値, 下限の詰まり)。ρ は 20番の `_spearman`。"""
    out = {}
    for tau, rec in res.items():
        truth = np.asarray(rec["truth"], float)
        series = [(k, np.asarray(rec["got"][k], float)) for k in rec["got"]]
        series.append(("fid", np.asarray(rec["fid"], float)))
        for key, got in series:
            rho, n = M._spearman(truth, got, min_n=MIN_BEATS_A)
            err = got - truth
            out[(key, tau)] = {
                "rho": rho, "n": int(n),
                "mae": float(np.nanmedian(np.abs(err))) if np.any(np.isfinite(err))
                else float("nan"),
                "bias": float(np.nanmedian(err)) if np.any(np.isfinite(err))
                else float("nan"),
                "floor": floor_check(truth, got)}
    return out


def _kind_no(key: str) -> str:
    """当てはめの型の番号（波形の型 klass_own と混ざらないよう括弧付きで書く）。"""
    return KIND_NO.get(key, "（参考）")


def print_a_legend(taus, dts, seed: int) -> None:
    print("\n" + "-" * 100)
    print("A0. 合成脈波と当てはめの型")
    print("-" * 100)
    print("  合成脈波 = 前進波（歪みガウス）＋ 反射波（歪みガウス）＋ 貯留槽（指数減衰）。")
    print(f"  反射波は早く到達するほど幅が広くなり歪みが消える（幅 = {W_REF_A} + "
          f"{W_REF_B} × 到達 [s]、到達 {DT_SKEW} s 以下で歪度 0）。")
    print(f"  雑音は標準偏差 {NOISE_SD}（乱数種 {seed}・拍ごとに同じ種）。"
          f"標本化 {FS:.0f} Hz・心拍数 {HR_SYN:.0f}/min。")
    print("  **真値は反射波のピーク − 前進波のピーク**（母数 μ の差ではない。幅と歪度が")
    print("  到達で変わるので両者は一致しない）。")
    print(f"  掃引: 貯留槽の時定数 {list(taus)} s（{len(list(taus))} 層）")
    print(f"        × 反射波の到達 {list(dts)} s（{len(list(dts))} 拍）。")
    print("  時定数を年齢層に見立て、層の中で到達だけを振る（26番の年齢層内 Spearman を模す）。")
    print("  時定数が小さいほど高齢に相当する（PWDB は加齢で末梢血管コンプライアンスを減らす）。")
    print("\n  当てはめの型（**波形の型 klass_own とは別のもの**。番号は括弧付きで書く）:")
    for k in KIND_KEYS:
        print("    " + _pad(_kind_no(k), 8) + _pad(KIND_HEAD[k], 11) + KIND_LABEL[k])
    print("    " + _pad("（参考）", 8) + _pad("特徴点法", 11)
          + "pda2.preprocess → find_landmarks の dia_t − sys_t")
    print("    (5)(6) は形の拘束・打ち切りに加えて Δμ の下限も 0.01 s に緩めた版、"
          "(5b)(6b) は")
    print("    凍結版の 0.08 s のままの版である（一度に 1 つだけ変えたときの効きを読むため）。")
    print("    (4b) は (2) と (4) を同時に適用した版、(0) は複製 (1) の照合で、"
          "いずれも 2026-09-15 に足した。")
    print("  (1) 以降の当てはめも least_squares（trf）だが、**起点の作り方と解の選び方は"
          " `fit_beat` と同じ**にしてある")
    print(f"  （起点 {N_STARTS} 点〈特徴点から決めた 1 点・Δμ の格子 5 点・乱数 2 点〉・"
          f"max_nfev {MAX_NFEV}・|Δμ − dmu0| ≤ {NEAR_DMU} s の解が")
    print(f"  RSS 最小の {NEAR_RSS:.2f} 倍以内ならそれを採る規則）。"
          "こうしてあるので各行は凍結版から**狙った 1 つだけ**が違う。")
    print("  (0) は `src/pda.py` の `fit_beat` そのものである。"
          "**収束検算は採否に課さない**が、凍結版と")
    print("  同じ規則を診断として当て、通過した拍数などを層ごとの表の下に印字する"
          "（(0) は `fit_beat` 自身の検算）。")


def print_a_matrix(summ: dict, taus) -> None:
    """型 × 時定数の順位相関 ρ だけを 1 枚にまとめる。"""
    print("\n" + "-" * 100)
    print("A1. 順位相関 ρ（真の ΔT と、当てはめが返した ΔT。20番の `_spearman`・層ごとに"
          f" {len(list(taus))} 通りの時定数）")
    print("-" * 100)
    head = "  " + _pad("当てはめの型", 32)
    for tau in taus:
        head += _pad(f"時定数 {tau:.2f} s", 15, right=True)
    print(head)
    for k in KIND_KEYS + ["fid"]:
        lab = (f"{_kind_no(k)} {KIND_HEAD[k]}" if k in KIND_HEAD else "（参考）特徴点法")
        line = "  " + _pad(lab, 32)
        for tau in taus:
            line += _f(summ[(k, float(tau))]["rho"], 15, prec=2, sign=True)
        print(line)
    print("  ρ が 1.00 なら真値の順位を完全に追えている。1 層の拍数が少ないので、")
    print("  0.71 と 0.89 の差は 1〜2 組の入れ替わりに当たる。")


def print_checks(rec: dict) -> None:
    """診断の表（凍結版と同じ収束検算の規則を当てた拍数）。**採否には使わない。**

    節A（時定数の層）でも節A-2（条件）でも同じ形で出す。数え方は `_diagnose` を見ること。
    """
    chk = rec.get("checks", {})
    keys = [k for k in KIND_KEYS if chk.get(k)]
    if not keys:
        return

    def _cnt(rows, key):
        return sum(1 for c in rows if c.get(key))

    print("\n    診断: 凍結版の採否規則（境界張り付き・高さ 0.02・競合解の RI 差 0.08）を")
    print("    診断として当てた数。**採否には使わない**（表の値は全拍のもの）。")
    print("    「Δμ下限」は Δμ が探索範囲の下限に張り付いた拍数で、2 成分の縮退の"
          "目安である。")
    print("    「τ上限」は減衰・畳み込みの型で τ が探索範囲の上限に張り付いた拍数（拍の中で"
          "減衰しない貯留槽。")
    print("    境界には数えない）。(0) は fit_beat 自身の検算。")
    print("    " + _pad("当てはめの型", 18) + _pad("通過", 9, right=True)
          + _pad("Δμ下限", 10, right=True) + _pad("境界", 8, right=True)
          + _pad("高さ<0.02", 12, right=True) + _pad("別解", 8, right=True)
          + _pad("τ上限", 8, right=True))
    for k in keys:
        rows = chk[k]
        print("    " + _pad(f"{_kind_no(k)} {KIND_HEAD[k]}", 18)
              + _pad(f"{_cnt(rows, 'ok')}/{len(rows)}", 9, right=True)
              + _pad(_cnt(rows, "dmu_lo"), 10, right=True)
              + _pad(_cnt(rows, "boundary"), 8, right=True)
              + _pad(_cnt(rows, "amp_zero"), 12, right=True)
              + _pad(_cnt(rows, "ambiguous"), 8, right=True)
              + _pad(_cnt(rows, "tau_hi"), 8, right=True))


def print_a_layer(rec: dict, summ: dict, tau: float) -> None:
    """時定数 1 層ぶんの表（まとめ → 1 拍ずつ）。"""
    truth = np.asarray(rec["truth"], float)
    print(f"\n  --- 貯留槽の時定数 {tau:.2f} s（{truth.size} 拍・真値 "
          f"{np.min(truth):.0f}〜{np.max(truth):.0f} ms）---")
    print("    " + _pad("当てはめの型", 18) + _pad("ρ", 8, right=True)
          + _pad("|誤差|中央値", 13, right=True) + _pad("全拍の最小", 13, right=True)
          + _pad("下限の詰まり", 15, right=True)
          + _pad("（参考）下位3拍の範囲", 24, right=True))
    for k in KIND_KEYS + ["fid"]:
        s = summ[(k, tau)]
        fl = s["floor"]
        lab = (f"{_kind_no(k)} {KIND_HEAD[k]}" if k in KIND_HEAD else "（参考）特徴点法")
        rngs = ("—" if not np.isfinite(fl["rng"])
                else f"{fl['lo']:.0f}〜{fl['hi']:.0f}（{fl['rng']:.0f}）"
                     f" {_ari(fl['flag_range'])}")
        gaps = ("—" if not np.isfinite(fl["gap"])
                else f"{_ari(fl['flag_gap'])}（{fl['gap']:+.0f}）")
        print("    " + _pad(lab, 18) + _f(s["rho"], 8, prec=2, sign=True)
              + _pad(f"{s['mae']:.0f} ms" if np.isfinite(s["mae"]) else "—", 13, right=True)
              + _pad(f"{fl['got_min']:.0f} ms" if np.isfinite(fl["got_min"]) else "—",
                     13, right=True)
              + _pad(gaps, 15, right=True)
              + _pad(rngs, 24, right=True))
    f0 = summ[(KIND_KEYS[0], tau)]["floor"]
    print(f"    「下限の詰まり」は、真値の小さいほうから {FLOOR_N} 拍の**返り値の最小**が、"
          f"その {FLOOR_N} 拍の**真値の最大**（{f0['truth_max']:.0f} ms）より")
    print(f"    {FLOOR_GAP_MS:.0f} ms 以上大きいとき「あり」（括弧内はその差）。"
          "2026-09-15 に差し替えた規準である。")
    print(f"    「（参考）下位3拍の範囲」は差し替える前の規準で、その {FLOOR_N} 拍の返り値の"
          f"範囲が {FLOOR_RANGE_MS:.0f} ms 未満のとき「あり」。")
    print("    凍結版は返り値が下限の手前で折り返すので範囲は広く出る。取り逃がすことが")
    print("    分かったので、参考として残してある。")
    print(f"    その {FLOOR_N} 拍の真値の範囲は {f0['truth_rng']:.0f} ms、真値の最小は "
          f"{f0['truth_min']:.0f} ms である。")
    print("    「全拍の最小」は掃引の全拍を通した返り値の最小で、これが真値の最小より"
          "大きいほど")
    print("    短い側を追えていない（下限で詰まっている）。")
    print_checks(rec)

    print("\n    1 拍ずつ（返り値 [ms] と、括弧内は 返り値 − 真値。列の番号は上の表と同じ）")
    head = _pad("真値[ms]", 9, right=True) + _pad("波形の型", 9, right=True)
    for k in KIND_KEYS:
        head += _pad(_kind_no(k), 10, right=True)
    head += _pad("特徴点法", 10, right=True)
    print("  " + head)
    for i, tv in enumerate(rec["truth"]):
        line = _pad(f"{tv:.0f}", 9, right=True) + _pad(str(rec["klass"][i]), 9, right=True)
        for k in KIND_KEYS + ["fid"]:
            v = rec["got"][k][i] if k in rec["got"] else rec["fid"][i]
            line += (_pad("—", 10, right=True) if not np.isfinite(v)
                     else f"{v:>4.0f}({v - tv:+4.0f})")
        print("  " + line)
    print("    「波形の型」は特徴点法（pda2.find_landmarks）が付けた klass_own である"
          "（1 = 極値あり、3 = 変曲点で代用）。")


def section_a(taus=TAUS_FULL, dts=DTS_FULL, seed: int = SEED_A) -> dict:
    """節A: 当てはめの型を並べ、真の反射波の到達を追えるかを測る（合成・表は 10 行）。"""
    print("\n" + "=" * 100)
    print("節A 合成脈波: 当てはめの型を変えると、真の反射波の到達を追えるか")
    print("=" * 100)
    print_a_legend(taus, dts, seed)
    res = sweep(taus, dts, seed=seed)
    summ = summarise_a(res)
    print_a_matrix(summ, taus)
    print("\n" + "-" * 100)
    print("A2. 時定数の層ごとの表")
    print("-" * 100)
    for tau in taus:
        print_a_layer(res[float(tau)], summ, float(tau))
    print("\n  出典: この台本（50番）の節A が合成脈波から計算した値")
    print(f"        （時定数 {len(list(taus))} 通り × 到達 {len(list(dts))} 通り × "
          f"当てはめ {len(KIND_KEYS)} 型・乱数種 {seed}）。")
    return {"res": res, "summ": summ, "taus": tuple(float(v) for v in taus),
            "dts": tuple(dts), "seed": seed}


# ============================================================== 節A-2（合成・RI）
# 反射波の大きさ a_ref を振り、当てはめが返す RI（h2/h1）が順位を追うかを見る。
# 条件は 2 つ。反射波が遅く分離する拍（型1 相当）と、収縮期に重なる拍（型3 相当）。
RIS_FULL = (0.20, 0.28, 0.35, 0.42, 0.50, 0.58, 0.65)
RIS_FAST = (0.20, 0.35, 0.50, 0.65)      # 自己検査の掃引
RI_TAU = 0.35                            # 貯留槽の時定数は固定する
RI_CONDS = ((0.28, "型1 相当", "反射波が遅く分離する（到達 280 ms）"),
            (0.10, "型3 相当", "反射波が収縮期に重なる（到達 100 ms）"))
# 符号の反転の規準（2026-09-15 に、実装の前に決めた）: ρ がこれより小さいとき「反転」。
# 大きさは 20番の CRIT_RHO（0.30）と同じで、符号を負にしたものである。
RHO_FLIP = -0.30


def sweep_ri(conds=RI_CONDS, ris=RIS_FULL, tau: float = RI_TAU, seed: int = SEED_A,
             kinds=None) -> dict:
    """条件 × 反射波の大きさの掃引。返り値は条件ごとの真値・返り値・波形の型。

    真値は 2 つ返す。`truth` は振った母数 a_ref、`ri_peak` は成分のピーク高さの比
    （当てはめが返す h2/h1 と同じ定義）である。条件の中では前進波が変わらないので
    両者は比例し、**順位は同じ**である。ρ は母数（試作と同じ）、|誤差| は比に対して出す。
    `checks` は当てはめの型ごとに、凍結版と同じ収束検算の規則を当てた結果（`fit_kind` の
    `checks`）を拍ごとに並べたものである。**記録するだけで採否には使わない**（(0) は
    `fit_beat` 自身の検算）。
    """
    kinds = list(KIND_KEYS) if kinds is None else list(kinds)
    out = {}
    for dt, lab, note in conds:
        rec = {"dt": float(dt), "label": lab, "note": note, "tau": float(tau),
               "truth": [], "ri_peak": [], "klass": [], "fid": [],
               "checks": dict((k, []) for k in kinds),
               "got": dict((k, []) for k in kinds)}
        for ri in ris:
            t, y, tr = synth_beat(dt, tau, seed=seed, a_ref=ri)
            rec["truth"].append(float(ri))
            rec["ri_peak"].append(tr["ri_peak"])
            for k in kinds:
                r = fit_kind(t, y, k)
                rec["checks"][k].append(r["checks"])
                rec["got"][k].append(r["ri"])
            f = fiducial_dt(t, y)
            rec["fid"].append(f["ri"])
            rec["klass"].append(f["klass"])
        out[lab] = rec
    return out


def summarise_a2(res: dict) -> dict:
    """型 × 条件の (ρ, |誤差| 中央値, 符号の反転)。ρ は 20番の `_spearman`。"""
    out = {}
    for lab, rec in res.items():
        truth = np.asarray(rec["truth"], float)
        peak = np.asarray(rec["ri_peak"], float)
        series = [(k, np.asarray(rec["got"][k], float)) for k in rec["got"]]
        series.append(("fid", np.asarray(rec["fid"], float)))
        for key, got in series:
            rho, n = M._spearman(truth, got, min_n=MIN_BEATS_A)
            err = got - peak
            fin = got[np.isfinite(got)]
            out[(key, lab)] = {
                "rho": rho, "n": int(n),
                "mae": float(np.nanmedian(np.abs(err))) if np.any(np.isfinite(err))
                else float("nan"),
                "lo": float(np.min(fin)) if fin.size else float("nan"),
                "hi": float(np.max(fin)) if fin.size else float("nan"),
                "flip": bool(np.isfinite(rho) and rho < RHO_FLIP)}
    return out


def print_a2_legend(ris, tau: float) -> None:
    print("\n" + "-" * 100)
    print("A2-0. RI の掃引（当てはめの型は節A と同じ 10 行＋参考の特徴点法）")
    print("-" * 100)
    print(f"  反射波の大きさ（母数 a_ref）を {list(ris)} の "
          f"{len(list(ris))} 通りに振る。")
    print(f"  条件は 2 つ。貯留槽の時定数は {tau} s に固定し、反射波の到達だけを変える。")
    for dt, lab, note in RI_CONDS:
        print(f"    {lab}  {note}")
    print("  当てはめが返す RI は第2成分／第1成分の**ピーク高さの比** h2/h1、特徴点法の RI は")
    print("  `dia_v / sys_v` である。真値は 2 つ出す。「真の RI」は振った母数 a_ref、")
    print("  「真の比」は合成した成分のピーク高さの比で、当てはめの h2/h1 と同じ定義である。")
    print("  条件の中では前進波が変わらないので両者は比例し、順位は同じになる。")
    print(f"  **符号の反転**は ρ < {RHO_FLIP:+.2f} のとき「反転」と印字する"
          "（2026-09-15 に実装の前に決めた規準）。")


def print_a2_cond(rec: dict, summ: dict, lab: str) -> None:
    truth = np.asarray(rec["truth"], float)
    print(f"\n  --- {lab}: {rec['note']}・貯留槽の時定数 {rec['tau']:.2f} s"
          f"（{truth.size} 拍・真の RI {np.min(truth):.2f}〜{np.max(truth):.2f}）---")
    print("    " + _pad("当てはめの型", 18) + _pad("ρ", 8, right=True)
          + _pad("|誤差|中央値", 13, right=True) + _pad("返り値の範囲", 18, right=True)
          + _pad("符号の反転", 12, right=True))
    for k in KIND_KEYS + ["fid"]:
        s = summ[(k, lab)]
        name = (f"{_kind_no(k)} {KIND_HEAD[k]}" if k in KIND_HEAD else "（参考）特徴点法")
        rng = ("—" if not np.isfinite(s["lo"])
               else f"{s['lo']:.3f}〜{s['hi']:.3f}")
        print("    " + _pad(name, 18) + _f(s["rho"], 8, prec=2, sign=True)
              + _f(s["mae"], 13, prec=3)
              + _pad(rng, 18, right=True)
              + _pad("反転" if s["flip"] else "—", 12, right=True))
    print(f"    「|誤差|中央値」は**真の比**（成分のピーク高さの比）に対する差の中央値。")
    print(f"    「符号の反転」は ρ < {RHO_FLIP:+.2f} のとき印字する"
          "（2026-09-15 に実装の前に決めた規準）。")
    print_checks(rec)

    print("\n    1 拍ずつ（当てはめが返した RI。列の番号は上の表と同じ）")
    head = (_pad("真のRI", 8, right=True) + _pad("真の比", 8, right=True)
            + _pad("波形の型", 9, right=True))
    for k in KIND_KEYS:
        head += _pad(_kind_no(k), 9, right=True)
    head += _pad("特徴点法", 9, right=True)
    print("  " + head)
    for i, tv in enumerate(rec["truth"]):
        line = (_pad(f"{tv:.2f}", 8, right=True)
                + _pad(f"{rec['ri_peak'][i]:.3f}", 8, right=True)
                + _pad(str(rec["klass"][i]), 9, right=True))
        for k in KIND_KEYS + ["fid"]:
            v = rec["got"][k][i] if k in rec["got"] else rec["fid"][i]
            line += (_pad("—", 9, right=True) if not np.isfinite(v)
                     else f"{v:>9.3f}")
        print("  " + line)
    print("    「波形の型」は特徴点法（pda2.find_landmarks）が付けた klass_own である。")


def section_a2(conds=RI_CONDS, ris=RIS_FULL, tau: float = RI_TAU,
               seed: int = SEED_A) -> dict:
    """節A-2: 反射波の大きさを振り、返り値の RI が順位を追うかを測る（合成）。"""
    print("\n" + "=" * 100)
    print("節A-2 合成脈波: 反射波の大きさを振ると、返り値の RI は順位を追うか")
    print("=" * 100)
    print("  節A と同じ合成脈波で、振るものだけを反射波の大きさに変える。")
    print("  型3 相当で何が起きるか（機構）: 反射波が前進波に融合するので、真の反射が")
    print("  大きいほど**第1成分が高くなる**。一方、第2成分は貯留槽の下降の上に固定されて")
    print("  高さが変わらない。したがって比 h2/h1 は**下がる**。")
    print_a2_legend(ris, tau)
    res = sweep_ri(conds, ris, tau=tau, seed=seed)
    summ = summarise_a2(res)
    print("\n" + "-" * 100)
    print("A2-1. 条件ごとの表")
    print("-" * 100)
    for _dt, lab, _note in conds:
        print_a2_cond(res[lab], summ, lab)
    print("\n  出典: この台本（50番）の節A-2 が合成脈波から計算した値")
    print(f"        （条件 {len(list(conds))} 通り × 反射波の大きさ {len(list(ris))} 通り × "
          f"当てはめ {len(KIND_KEYS)} 型・乱数種 {seed}）。")
    return {"res": res, "summ": summ, "ris": tuple(ris), "tau": float(tau),
            "conds": tuple(lab for _d, lab, _n in conds)}


# ================================================================ 節B（実データ）
KLASS_COL = "klass_own"
KLASSES = (1, 3, 4, 5)
KLASS_LABEL = {
    1: "型1 明瞭な重複切痕と拡張期ピーク（極値）",
    3: "型3 極値は無いが下降の緩む変曲点",
    4: "型4 変曲点が見つからない",
    5: "型5 収縮期ピークが拍の末尾（波形が不正）",
}
KLASS_SHORT = {1: "型1 極値あり", 3: "型3 変曲点で代用", 4: "型4 変曲点なし",
               5: "型5 波形が不正"}
COL_V1 = "dt_v1_ms"        # 凍結版 2 カーネルの ΔT（26番の出力）
COL_LM = "dt_lm_ms"        # 特徴点法の ΔT（Charlton 同梱）
COL_OK = "ok_v1"           # 26番の A 段（その手法が自分で採用した例）
COL_RI_V1 = "ri_v1"        # 凍結版 2 カーネルの RI（26番の出力）
COL_RI_LM = "digital_ri"   # 特徴点法の RI（Charlton 同梱）
NEED_B = ("age", KLASS_COL, COL_V1, COL_LM)
NEED_B4 = (COL_RI_V1, COL_RI_LM)   # B4（RI）に要る列。無ければ B4 だけを飛ばす

BIN_MS = 20.0              # B2 の区間の幅
PCTS = (5, 10, 25, 50, 75, 90, 95)
DMU_LO_MS = 1000.0 * DMU_LO_FROZEN   # 凍結版の探索範囲の下限 Δμ 0.08 s ＝ 80 ms

# 予測の規準（docstring の P1〜P3。2026-09-15 に、実データを見る前に固定した）
PRED_P1_FLOOR_MS = 140.0   # P1 型3: 下から 2 区間でも凍結版 ΔT の中央値がこれを下回らない
PRED_P1_N_BINS = 2         # P1 で見る区間の数（下から）
PRED_RHO_GAP = 0.15        # P2 型3: 短い側の ρ が長い側より これ以上小さい／P3 型1: 未満
# P4・P5（RI。2026-09-15 に、実データを見る前に固定した）
PRED_P4_MED = 0.30         # P4 型3: ρ(ri_v1, digital_ri) の中央値がこれ未満
PRED_P4_OLD = 0.20         # P4 型3: 最も高齢の層（75 歳）の ρ がこれ未満
PRED_P5_MED = 0.60         # P5 型1: ρ の中央値がこれ以上
PRED_P5_SLOPE = 0.15       # P5 型1: 最も若い層と最も高齢の層の ρ の差がこれ未満（傾きがない）
AGE_OLD = 75.0             # PWDB の最も高齢の層


def _colv(d: pd.DataFrame, c: str) -> np.ndarray:
    if c not in d.columns:
        return np.full(len(d), np.nan)
    return pd.to_numeric(d[c], errors="coerce").to_numpy(dtype=float)


def stage_a(d: pd.DataFrame) -> pd.DataFrame:
    """26番の A 段（ok_v1 == 1）。列が無ければそのまま返す（C 段と同じになる）。"""
    if COL_OK not in d.columns:
        return d
    return d[pd.to_numeric(d[COL_OK], errors="coerce") == 1]


def subset(d: pd.DataFrame, k: int) -> pd.DataFrame:
    return d[_colv(d, KLASS_COL) == float(k)]


def missing_cols(d: pd.DataFrame) -> list:
    return [c for c in NEED_B if c not in d.columns]


def dist_of(d: pd.DataFrame, col: str) -> dict:
    """1 列の分布（人数・最小・パーセンタイル・最大）。"""
    v = _colv(d, col)
    v = v[np.isfinite(v)]
    out = {"n": int(v.size), "min": float("nan"), "max": float("nan"),
           "p": dict((q, float("nan")) for q in PCTS)}
    if v.size:
        out["min"], out["max"] = float(np.min(v)), float(np.max(v))
        out["p"] = dict((q, float(np.percentile(v, q))) for q in PCTS)
    return out


def floor_bins(d: pd.DataFrame) -> dict:
    """特徴点法 ΔT を BIN_MS 刻みの区間に分け、区間ごとの凍結版 ΔT を要約する。

    対応のある行（両方が有限）だけを使う。返り値の `bins` は区間の下端をキーにした
    辞書で、下端の小さい順に並べれば「特徴点法が短い区間で凍結版が下がるか」が読める。
    """
    x, y = _colv(d, COL_LM), _colv(d, COL_V1)
    g = np.isfinite(x) & np.isfinite(y)
    x, y = x[g], y[g]
    out = {"n": int(x.size), "bins": [], "v1_min": float("nan"),
           "v1_p5": float("nan"), "lm_min": float("nan")}
    if x.size == 0:
        return out
    out["v1_min"] = float(np.min(y))
    out["v1_p5"] = float(np.percentile(y, 5))
    out["lm_min"] = float(np.min(x))
    idx = np.floor(x / BIN_MS).astype(int)
    for b in np.unique(idx):
        sel = idx == b
        v = y[sel]
        q1, q3 = (float(q) for q in np.percentile(v, [25, 75]))
        out["bins"].append({"lo": float(b) * BIN_MS, "hi": float(b + 1) * BIN_MS,
                            "n": int(sel.sum()), "med": float(np.median(v)),
                            "q1": q1, "q3": q3,
                            "lm_med": float(np.median(x[sel]))})
    return out


def rho_rows(d: pd.DataFrame, half=None, xcol: str = COL_V1, ycol: str = COL_LM) -> list:
    """年齢層ごとの (年齢, ρ(xcol, ycol), n)。既定は ΔT（dt_v1_ms・dt_lm_ms）。

    `half` が "short"／"long" のときは、**その年齢層の** `ycol` の中央値で二分した
    片側だけを使う（層をまたいだ中央値で切ると年齢と混ざる）。ρ は 20番の `_spearman`
    （対応のある行だけ・1 層 MIN_PER_AGE 名以上）。B4 は xcol・ycol に RI の列を渡す。
    """
    out = []
    if "age" not in d.columns or len(d) == 0:
        return out
    for age, g in d.groupby("age", sort=True):
        x, y = _colv(g, xcol), _colv(g, ycol)
        keep = np.isfinite(x) & np.isfinite(y)
        if half is not None and int(keep.sum()) >= 2:
            thr = float(np.median(y[keep]))
            keep = keep & ((y <= thr) if half == "short" else (y > thr))
        r, n = M._spearman(x[keep], y[keep], min_n=MIN_PER_AGE)
        out.append((float(age), r, int(n)))
    return out


def strat(rows: list, sign: int = 1) -> dict:
    """年齢層をまたいだまとめ。中央値・向きの層数は 20番の `_judge` に任せる。"""
    fin = [(a, r, n) for a, r, n in rows if np.isfinite(r)]
    j = M._judge(rows, sign) if rows else None
    return {"rows": rows,
            "med": float(np.median([r for _a, r, _n in fin])) if fin else float("nan"),
            "med_abs": j["med_abs"] if j else float("nan"),
            "n_ok": j["n_ok"] if j else 0,
            "n_ages": j["n_ages"] if j else 0,
            "min_n": min(n for _a, _r, n in fin) if fin else 0,
            "n_tot": int(sum(n for _a, _r, n in fin))}


def print_b1(d: pd.DataFrame, klasses) -> dict:
    """B1 型ごとの ΔT の分布。"""
    print("\n" + "-" * 100)
    print("B1. 型ごとの ΔT の分布（凍結版と特徴点法。単位 ms）")
    print("-" * 100)
    print("  段 A は 26番の A 段（ok_v1 == 1。凍結版が自分で採用した例）、段 C は採否を"
          "無視した全例。")
    out = {}
    for k in klasses:
        g = subset(d, k)
        ga = stage_a(g)
        print(f"\n  {KLASS_LABEL.get(k, f'型{k}')}  n = {len(g)} 名（A 段 {len(ga)} 名）")
        if len(g) == 0:
            print("    該当なし")
            continue
        print("    " + _pad("列", 12) + _pad("段", 4) + _pad("n", 7, right=True)
              + _pad("最小", 8, right=True)
              + "".join(_pad(f"p{q}", 8, right=True) for q in PCTS)
              + _pad("最大", 8, right=True))
        for col in (COL_V1, COL_LM):
            for stg, gg in (("A", ga), ("C", g)):
                s = dist_of(gg, col)
                out[(k, col, stg)] = s
                print("    " + _pad(col, 12) + _pad(stg, 4) + _pad(s["n"], 7, right=True)
                      + _f(s["min"], 8, prec=1)
                      + "".join(_f(s["p"][q], 8, prec=1) for q in PCTS)
                      + _f(s["max"], 8, prec=1))
    print("\n  出典: この台本（50番）の節B が CSV の既存列から計算した値。"
          "**新しい当てはめはしていない。**")
    return out


def print_b2(d: pd.DataFrame, klasses) -> dict:
    """B2 下限の検査（特徴点法 ΔT の区間ごとに凍結版 ΔT を並べる）。"""
    print("\n" + "-" * 100)
    print(f"B2. 下限の検査: 特徴点法 ΔT を {BIN_MS:.0f} ms 刻みの区間に分け、区間ごとの"
          " 凍結版 ΔT（A 段）")
    print("-" * 100)
    print("  特徴点法 ΔT が短い区間でも凍結版 ΔT の中央値が下がらなければ、凍結版は下限で"
          "詰まっている。")
    print("  対応のある行（両方が有限）だけを使う。")
    out = {}
    for k in klasses:
        g = stage_a(subset(d, k))
        res = floor_bins(g)
        out[k] = res
        print(f"\n  {KLASS_LABEL.get(k, f'型{k}')}  対応のある行 {res['n']} 名（A 段）")
        if res["n"] == 0:
            print("    対応のある行が無い")
            continue
        print("    " + _pad("特徴点法 ΔT の区間", 22) + _pad("人数", 7, right=True)
              + _pad("凍結版 ΔT 中央値", 18, right=True)
              + _pad("四分位範囲", 22, right=True)
              + _pad("特徴点法 ΔT 中央値", 20, right=True))
        for b in res["bins"]:
            iqr = f"[{b['q1']:.1f}〜{b['q3']:.1f}]"
            print("    " + _pad(f"[{b['lo']:.0f}, {b['hi']:.0f})", 22)
                  + _pad(b["n"], 7, right=True) + _f(b["med"], 18, prec=1)
                  + _pad(iqr, 22, right=True) + _f(b["lm_med"], 20, prec=1))
        print(f"    凍結版 ΔT の最小 {_n(res['v1_min'], 1)} ms・下位 5% "
              f"{_n(res['v1_p5'], 1)} ms（特徴点法 ΔT の最小は "
              f"{_n(res['lm_min'], 1)} ms）。")
        print(f"    探索範囲の下限 Δμ {DMU_LO_FROZEN} s（＝ {DMU_LO_MS:.0f} ms）との差は "
              f"{_n(res['v1_min'] - DMU_LO_MS, 1, sign=True)} ms・"
              f"{_n(res['v1_p5'] - DMU_LO_MS, 1, sign=True)} ms。")
    print("\n  Δμ は母数（μ2 − μ1）の下限で、ΔT は成分のピーク間隔である。歪みがあると")
    print("  ピークは μ からずれるので、ΔT が 80 ms を下回ることはありうる。80 ms は")
    print("  それでも目安になる（下限より下には母数を動かせない）。")
    print("  出典: この台本（50番）の節B が CSV の既存列から計算した値。")
    return out


def print_b3(d: pd.DataFrame, klasses) -> dict:
    """B3 型ごとの ρ(dt_v1_ms, dt_lm_ms) と、特徴点法 ΔT の短い側・長い側。"""
    print("\n" + "-" * 100)
    print("B3. 型ごとの ρ(dt_v1_ms, dt_lm_ms)（年齢層内 Spearman の中央値。符号つき）")
    print("-" * 100)
    print(f"  層は `age` の相異なる値、1 層 {MIN_PER_AGE} 名以上（20番の `_spearman`）。")
    print("  短い側・長い側は**年齢層ごとに**その層の dt_lm_ms の中央値で二分した半数で、")
    print("  半数それぞれにも 1 層 8 名以上を要求する（足りない層は数えない）。")
    print("  下限で詰まっているなら、短い側で ρ が落ちる。")
    print("    " + _pad("型", 20) + _pad("段", 4) + _pad("ρ 全体", 13, right=True)
          + _pad("ρ 短い側", 13, right=True) + _pad("ρ 長い側", 13, right=True)
          + _pad("差 長−短", 11, right=True) + _pad("層", 5, right=True)
          + _pad("最小n", 8, right=True))
    out = {}
    for k in klasses:
        g = subset(d, k)
        for stg, gg in (("A", stage_a(g)), ("C", g)):
            s_all = strat(rho_rows(gg))
            s_sh = strat(rho_rows(gg, half="short"))
            s_lg = strat(rho_rows(gg, half="long"))
            gap = s_lg["med"] - s_sh["med"]
            out[(k, stg)] = {"all": s_all, "short": s_sh, "long": s_lg, "gap": gap}
            lab = KLASS_SHORT.get(k, f"型{k}")
            print("    " + _pad(lab, 20) + _pad(stg, 4)
                  + _f(s_all["med"], 13, prec=3, sign=True)
                  + _f(s_sh["med"], 13, prec=3, sign=True)
                  + _f(s_lg["med"], 13, prec=3, sign=True)
                  + _f(gap, 11, prec=3, sign=True)
                  + _pad(s_all["n_ages"], 5, right=True)
                  + _pad(s_all["min_n"] or "—", 8, right=True))
    print("  「層」「最小n」は ρ 全体のもの。短い側・長い側は人数が半分になるので、"
          "層が減ることがある。")
    print("  出典: この台本（50番）の節B が CSV の既存列から計算した値。")
    return out


def print_b4_ri(d: pd.DataFrame, klasses) -> dict:
    """B4 型ごとの ρ(ri_v1, digital_ri) を年齢層ごとに 1 行ずつ。

    規約は 48番・B3 と同じ（20番の `_spearman`・1 層 MIN_PER_AGE 名以上・層は `age` の
    相異なる値）。凍結版の RI は A 段（ok_v1 == 1）を主とし、C 段（採否を無視した全例）を
    同じ行に並べる。**新しい当てはめはしない**（既存列を読むだけ）。
    """
    print("\n" + "-" * 100)
    print("B4. 型ごとの ρ(ri_v1, digital_ri)（年齢層ごとに 1 行。符号つき）")
    print("-" * 100)
    miss = [c for c in NEED_B4 if c not in d.columns]
    if miss:
        print(f"  ★ 列が無い: {miss}。B4 と予測 P4・P5 は計算できない。")
        return {}
    print(f"  層は `age` の相異なる値、1 層 {MIN_PER_AGE} 名以上。A 段は ok_v1 == 1、")
    print("  C 段は採否を無視した全例。対応のある行（両方が有限）だけを使う。")
    out = {}
    for k in klasses:
        g = subset(d, k)
        rows_a = rho_rows(stage_a(g), xcol=COL_RI_V1, ycol=COL_RI_LM)
        rows_c = rho_rows(g, xcol=COL_RI_V1, ycol=COL_RI_LM)
        s_a, s_c = strat(rows_a), strat(rows_c)
        out[k] = {"A": s_a, "C": s_c}
        print(f"\n  {KLASS_LABEL.get(k, f'型{k}')}  n = {len(g)} 名（A 段 {len(stage_a(g))} 名）")
        if not rows_c:
            print("    該当なし")
            continue
        print("    " + _pad("年齢層", 10, right=True) + _pad("A段 n", 10, right=True)
              + _pad("A段 ρ", 12, right=True) + _pad("C段 n", 10, right=True)
              + _pad("C段 ρ", 12, right=True))
        d_a = dict((a, (r, n)) for a, r, n in rows_a)
        for age, r_c, n_c in rows_c:
            r_a, n_a = d_a.get(age, (float("nan"), 0))
            print("    " + _pad(f"{age:.0f}", 10, right=True)
                  + _pad(n_a or "—", 10, right=True) + _f(r_a, 12, prec=3, sign=True)
                  + _pad(n_c or "—", 10, right=True) + _f(r_c, 12, prec=3, sign=True))
        print("    " + _pad("中央値", 10, right=True) + _pad("", 10)
              + _f(s_a["med"], 12, prec=3, sign=True) + _pad("", 10)
              + _f(s_c["med"], 12, prec=3, sign=True)
              + f"  （評価できた層 A {s_a['n_ages']}・C {s_c['n_ages']}）")
    print("\n  出典: この台本（50番）の節B が CSV の既存列から計算した値。"
          "**新しい当てはめはしていない。**")
    return out


def print_b5(b2: dict, b3: dict, b4: dict) -> dict:
    """B5 予測との照合（P1〜P5）。**判定は付けない**（事後・記述）。"""
    print("\n" + "-" * 100)
    print("B5. 予測との照合（予測は 2026-09-15 に、実データを見る前に固定した。docstring と同文）")
    print("-" * 100)
    print("  (P1) 型3 で、特徴点法 ΔT が最も短い区間（下から 2 区間）でも凍結版 ΔT の")
    print(f"       中央値は {PRED_P1_FLOOR_MS:.0f} ms を下回らない。")
    print(f"  (P2) 型3 では、特徴点法 ΔT が短い側の半数の ρ が長い側の半数より "
          f"{PRED_RHO_GAP:.2f} 以上小さい。")
    print(f"  (P3) 型1 では (P2) の差が {PRED_RHO_GAP:.2f} 未満。")
    print(f"  (P4) 型3 では、年齢層内の ρ(ri_v1, digital_ri) の中央値が "
          f"{PRED_P4_MED:.2f} 未満で、かつ高齢の層ほど")
    print(f"       小さい（{AGE_OLD:.0f} 歳層で {PRED_P4_OLD:.2f} 未満）。")
    print(f"  (P5) 型1 ではその ρ の中央値が {PRED_P5_MED:.2f} 以上で、年齢層による傾きが")
    print(f"       ない（最も若い層と最も高齢の層の差が {PRED_P5_SLOPE:.2f} 未満）。")

    res3 = b2.get(3, {"bins": [], "n": 0})
    low = res3["bins"][:PRED_P1_N_BINS]
    ev1 = len(low) == PRED_P1_N_BINS
    p1 = ev1 and all(np.isfinite(b["med"]) and b["med"] >= PRED_P1_FLOOR_MS for b in low)
    print(f"\n  P1 型3・特徴点法 ΔT が下から {PRED_P1_N_BINS} 区間の凍結版 ΔT 中央値:")
    for b in low:
        print(f"     [{b['lo']:.0f}, {b['hi']:.0f}) ms  n = {b['n']}  "
              f"凍結版 ΔT の中央値 {_n(b['med'], 1)} ms"
              + ("  ★ この区間は 8 名未満で、中央値は不安定である"
                 if b["n"] < MIN_PER_AGE else ""))
    if ev1:
        print(f"     → {PRED_P1_FLOOR_MS:.0f} ms を下回らない: {_yn(p1)}")
    else:
        print(f"     → 照合できない（対応のある行の区間が {len(low)} しかない）")

    g3 = b3.get((3, "A"), {})
    g1 = b3.get((1, "A"), {})
    gap3 = g3.get("gap", float("nan"))
    gap1 = g1.get("gap", float("nan"))
    p2 = bool(np.isfinite(gap3) and gap3 >= PRED_RHO_GAP)
    p3 = bool(np.isfinite(gap1) and gap1 < PRED_RHO_GAP)
    print(f"\n  P2 型3（A 段）  ρ 短い側 {_n(g3.get('short', {}).get('med', float('nan')), 3, sign=True)}"
          f"・長い側 {_n(g3.get('long', {}).get('med', float('nan')), 3, sign=True)}"
          f"・差 {_n(gap3, 3, sign=True)}")
    print(f"     → 差が {PRED_RHO_GAP:.2f} 以上: "
          + (_yn(p2) if np.isfinite(gap3) else "照合できない（層の人数が足りない）"))
    print(f"\n  P3 型1（A 段）  ρ 短い側 {_n(g1.get('short', {}).get('med', float('nan')), 3, sign=True)}"
          f"・長い側 {_n(g1.get('long', {}).get('med', float('nan')), 3, sign=True)}"
          f"・差 {_n(gap1, 3, sign=True)}")
    print(f"     → 差が {PRED_RHO_GAP:.2f} 未満: "
          + (_yn(p3) if np.isfinite(gap1) else "照合できない（層の人数が足りない）"))

    r4 = _ri_stats(b4, 3)
    r5 = _ri_stats(b4, 1)
    p4 = bool(np.isfinite(r4["med"]) and np.isfinite(r4["old"])
              and r4["med"] < PRED_P4_MED and r4["old"] < PRED_P4_OLD)
    p5 = bool(np.isfinite(r5["med"]) and np.isfinite(r5["span"])
              and r5["med"] >= PRED_P5_MED and r5["span"] < PRED_P5_SLOPE)
    print(f"\n  P4 型3（A 段）  ρ(ri_v1, digital_ri) の中央値 {_n(r4['med'], 3, sign=True)}"
          f"・{AGE_OLD:.0f} 歳層 {_n(r4['old'], 3, sign=True)}"
          f"（評価できた層 {r4['n_ages']}）")
    print(f"     層ごと: {r4['line']}")
    print(f"     → 中央値が {PRED_P4_MED:.2f} 未満、かつ {AGE_OLD:.0f} 歳層が "
          f"{PRED_P4_OLD:.2f} 未満: "
          + (_yn(p4) if np.isfinite(r4["med"]) and np.isfinite(r4["old"])
             else "照合できない（層の人数が足りない）"))
    print(f"     参考: 年齢と層ごとの ρ の順位相関 {_n(r4['trend'], 2, sign=True)}"
          "（負なら高齢の層ほど小さい。記述のみで、規準には使わない）")
    print(f"\n  P5 型1（A 段）  ρ(ri_v1, digital_ri) の中央値 {_n(r5['med'], 3, sign=True)}"
          f"・最も若い層 {_n(r5['young'], 3, sign=True)}"
          f"・最も高齢の層 {_n(r5['old'], 3, sign=True)}"
          f"・差 {_n(r5['span'], 3)}")
    print(f"     層ごと: {r5['line']}")
    print(f"     → 中央値が {PRED_P5_MED:.2f} 以上、かつ層による差が "
          f"{PRED_P5_SLOPE:.2f} 未満: "
          + (_yn(p5) if np.isfinite(r5["med"]) and np.isfinite(r5["span"])
             else "照合できない（層の人数が足りない）"))

    ev4 = bool(np.isfinite(r4["med"]) and np.isfinite(r4["old"]))
    ev5 = bool(np.isfinite(r5["med"]) and np.isfinite(r5["span"]))
    hit = sum(1 for v in (p1, p2, p3, p4, p5) if v)
    ev = sum(1 for v in (ev1, np.isfinite(gap3), np.isfinite(gap1), ev4, ev5) if v)
    print(f"\n  まとめ: 予測 5 条のうち照合できたのは {ev} 条、そのうち「はい」は {hit} 条。")
    if ev < 5:
        print("  照合できなかった条は、人数が足りないか対応のある行・列が無いためである。")
        print("  この CSV が抜粋なら、確認的解析の機械（4,374 行）で走らせ直す。")
    print("  **この節は事後の記述であり、判定（成立・不成立）は付けない。**"
          "26番の事前規準による判定は動かない。")
    return {"P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5, "hit": hit, "n_eval": ev,
            "p1_bins": low, "gap3": gap3, "gap1": gap1, "ri3": r4, "ri1": r5}


def _ri_stats(b4: dict, klass: int) -> dict:
    """B4 の A 段から、P4・P5 に要る値を取り出す（中央値・最若層・最高齢層・傾き）。

    「年齢層による傾き」は記述として年齢と ρ の順位相関も出すが、**規準に使うのは
    最も若い層と最も高齢の層の差**（P5）と、最も高齢の層の値（P4）である。
    """
    s = b4.get(klass, {}).get("A", {})
    rows = [(a, r) for a, r, _n in s.get("rows", []) if np.isfinite(r)]
    out = {"med": s.get("med", float("nan")), "n_ages": s.get("n_ages", 0),
           "young": float("nan"), "old": float("nan"), "span": float("nan"),
           "trend": float("nan"), "line": "—"}
    if not rows:
        return out
    rows.sort()
    out["young"], out["old"] = rows[0][1], rows[-1][1]
    out["span"] = abs(out["old"] - out["young"])
    if len(rows) >= MIN_BEATS_A:
        out["trend"] = M._spearman(np.array([a for a, _r in rows], float),
                                   np.array([r for _a, r in rows], float),
                                   min_n=MIN_BEATS_A)[0]
    out["line"] = "・".join(f"{a:.0f}歳 {r:+.3f}" for a, r in rows)
    # P4 は「75 歳層」を見る。その層が評価できていなければ最も高齢の層で代える
    for a, r in rows:
        if abs(a - AGE_OLD) < 1e-9:
            out["old"] = r
    return out


def section_b(d: pd.DataFrame, src: str) -> dict:
    """節B: 凍結版 ΔT が下限で詰まる性質は実データにも出るか（既存列だけを読む）。"""
    print("\n" + "=" * 100)
    print("節B 実データ（PWDB）: 凍結版 ΔT は下限で詰まっているか")
    print("=" * 100)
    miss = missing_cols(d)
    if miss:
        print(f"  入力 {src}")
        print(f"  ★ 列が無い: {miss}。節B は計算できない（26番 `26_pwdb_compare.py` の"
              "出力が要る）。")
        return {"state": 2, "missing": miss}
    ages = sorted(pd.to_numeric(d["age"], errors="coerce").dropna().unique().tolist())
    kl = _colv(d, KLASS_COL)
    seen = sorted(set(int(v) for v in kl[np.isfinite(kl)]))
    n_ok = int(np.sum(pd.to_numeric(d[COL_OK], errors="coerce") == 1)) \
        if COL_OK in d.columns else -1
    print(f"  入力 {src}")
    print("  （26番の出力。**既存列だけを読み、新しい当てはめはしない**）")
    print(f"  行数 {len(d)} 名（確認的解析を回した機械では 4,374 名）"
          f"・年齢層 {[int(a) for a in ages]}・型の値 {seen}")
    print(f"  A 段（{COL_OK} == 1）{n_ok} 名"
          if n_ok >= 0 else f"  {COL_OK} の列が無いので A 段と C 段は同じになる")
    short = [int(a) for a in ages
             if int((pd.to_numeric(d["age"], errors="coerce") == a).sum()) < MIN_PER_AGE]
    if len(d) < 100:
        print(f"  ★ この CSV は {len(d)} 行の抜粋である（1 層 "
              f"{len(d) // max(len(ages), 1)} 名）。**ここから出る数値は読んではいけない。**")
    elif short:
        print(f"  ★ {MIN_PER_AGE} 名に満たない年齢層がある: {short}")
    klasses = list(KLASSES) + sorted(set(seen) - set(KLASSES))
    out = {"state": 0}
    out["b1"] = print_b1(d, klasses)
    out["b2"] = print_b2(d, klasses)
    out["b3"] = print_b3(d, klasses)
    out["b4"] = print_b4_ri(d, klasses)
    out["b5"] = print_b5(out["b2"], out["b3"], out["b4"])
    return out


# ============================================================ 節C（実データ・再当てはめ）
# 節A・節A-2 で候補になった当てはめの型を、**26番と同じ拍**（PWDB の指尖 PPG）に当て直し、
# 26番の枠組み（波形の型・A 段と C 段・年齢層内 Spearman）でそのまま並べる。
# **探索・事後であり、26番の事前規準による判定は動かさない。**
VARIANTS_DEFAULT = ("fb", "relax", "conv", "conv01", "trunc")
REFIT_NAME = "50_refit.csv"     # 再当てはめの記録（--refit-csv で変えられる）
# 記録に残す診断の列の頭 → `fit_kind` が返す `checks` の鍵
CHK_COLS = (("dmulo", "dmu_lo"), ("bnd", "boundary"), ("amp", "amp_zero"),
            ("amb", "ambiguous"), ("tauhi", "tau_hi"))
CHK_HEAD = {"dmulo": "Δμ下限率", "bnd": "境界率", "amp": "高さ率", "amb": "別解率",
            "tauhi": "τ上限率"}
COL_PWV = "PWV_a"          # 大動脈脈波伝播速度（真値）
COL_PVR = "pvr"            # 末梢血管抵抗（真値）
SIGN_DT = -1               # ΔT × 大動脈PWV の予測の向き（26番・48番と同じ）
SIGN_RI = +1               # RI × 末梢血管抵抗 の予測の向き（同上）
MIN_N_POOL = 20            # C4 の順位相関に要る人数（26番の MIN_N と同じ）
C_KLASSES = (1, 3, 4)      # C1〜C4 で分ける波形の型（これに「全」を足す）
PROGRESS_EVERY = 200       # 節C の進み具合を印字する間隔 [名]
CKPT_EVERY = 400           # 節C が途中の記録を書く間隔 [名]（止めても再開できる）

# 予測の規準（docstring の P6〜P10）。2026-09-15 実装前に固定（lab_log 追記143）
PRED_P7_GAP = 0.10         # P7 型3・C 段: (2) の Δμ 下限の割合が (4) より これ以上大きい
PRED_P8_MED = 0.30         # P8 型3・A 段: (4) の RI × pvr の |中央値| がこれ以上
PRED_C0_DT_MS = 1e-6       # C0・P10: (0) と 26番の ΔT の差の許容 [ms]
PRED_C0_RI = 1e-9          # C0・P10: (0) と 26番の RI の差の許容
PRED_P10_LM = {1: 0.343, 3: 0.430}   # P10: 同梱の特徴点の型別 |ρ|（48番・lab_log 追記137）
PRED_P10_PREC = 3          # P10: 小数 3 桁で一致
# P6・P9 の規準は 20番の `_judge` そのもの（|中央値| ≥ M.CRIT_RHO かつ全層で符号が合う）で、
# この台本では新しい閾値を作らない。

_L = None                  # 23番（真値と同梱の特徴点の読み込み）。節C でだけ読み込む


def _landmarks_module():
    """23番を必要になったときだけ読み込む（節A・節B だけのときは読み込まない）。"""
    global _L
    if _L is None:
        _L = _load("23_pwdb_landmarks.py", "m23")
    return _L


def c_stride(ppg, limit: int):
    """先頭 N 名ではなく等間隔に N 名（26番 `_stride` と同じ式を写したもの）。

    PWDB は被験者が年齢順に並んでいる可能性があり、先頭だけ取ると 1 つの年齢層に偏る。
    年齢層内の順位相関で読むので全層が要る。26番のものと同じ結果になることは自己検査で
    確かめる（26番を読み込んで突き合わせる）。
    """
    if limit >= len(ppg):
        return ppg
    idx = np.unique(np.linspace(0, len(ppg) - 1, limit).round().astype(int))
    return ppg.iloc[idx]


def refit_subject(args_tuple):
    """1 被験者の 1 拍に、頼まれた当てはめの型を当てる（26番 `indices_for_subject` と同じ形）。

    例外は握りつぶさず `why` に残し、値は NaN にする（1 名で落ちても走り続ける）。
    拍の作り方・型の付け方は 26番と同一である（`M.beat_of`・`pda2.preprocess` →
    `find_landmarks`）。採否 `ok_{型}` は `fit_kind` の `checks["ok"]`、すなわち凍結版
    `fit_beat` と同じ収束検算の規則である。
    """
    subj, row, hr, variants = args_tuple
    out = {"subj_no": int(subj)}
    for k in variants:                    # 先に空で埋める（再開の判定が `ok_{型}` を見る）
        out[f"dt_{k}_ms"] = float("nan")
        out[f"ri_{k}"] = float("nan")
        out[f"ok_{k}"] = 0
        for tag, _q in CHK_COLS:
            out[f"{tag}_{k}"] = float("nan")
        out[f"cost_{k}"] = float("nan")
    why = []
    try:
        y, fs = M.beat_of(row, hr)
        if y is None:
            out["why"] = "no_beat"        # 心拍が無い・標本 40 未満で拍を復元できない
            return out
        t = np.arange(y.size) / fs
        out["fs"] = float(fs)
        out["n_samp"] = int(y.size)
        try:                              # --- 波形の型（26番と同じ手順で自分で付ける）
            ys, _amp = pda2.preprocess(t, y, fs)
            if ys is None:
                why.append("preprocess_none")
            else:
                lm = pda2.find_landmarks(t, ys)
                out["klass_own"] = int(lm["klass"])
                out["sys_own_ms"] = float(lm["sys_t"]) * 1000.0
                out["dia_own_ms"] = float(lm["dia_t"]) * 1000.0
        except Exception as e:            # noqa: BLE001
            why.append(("EXC:" + str(e))[:40])
        for k in variants:                # --- 候補の当てはめ（節A と同じ `fit_kind`）
            try:
                r = fit_kind(t, y, k)
                ck = r["checks"]
                out[f"dt_{k}_ms"] = (1000.0 * float(r["dt_s"])
                                     if np.isfinite(r["dt_s"]) else float("nan"))
                out[f"ri_{k}"] = float(r["ri"])
                out[f"ok_{k}"] = int(bool(ck["ok"]))
                for tag, q in CHK_COLS:
                    out[f"{tag}_{k}"] = int(bool(ck[q]))
                out[f"cost_{k}"] = float(r["cost"])
            except Exception as e:        # noqa: BLE001
                why.append((f"EXC:{k}:" + str(e))[:40])
    except Exception as e:                # noqa: BLE001
        why.append(("EXC:" + str(e))[:60])
    if why:
        out["why"] = ";".join(why)[:120]
    return out


def _refit_path(refit_csv, limit: int) -> Path:
    """再当てはめの記録の置き場。--limit のときは別名にする（26番の CSV と同じ規約）。"""
    if refit_csv:
        return Path(refit_csv).expanduser()
    return DATA / "pwdb" / (f"50_refit_limit{limit}.csv" if limit else REFIT_NAME)


def _cached_rows(path: Path) -> dict:
    """記録（CSV）を被験者番号をキーにした辞書で読む。読めなければ空で返す。"""
    if not path.exists():
        return {}
    try:
        # `float_precision="round_trip"` を付ける。既定の速い読み方は最後の 1 ビットが
        # ずれることがあり、再開して書き直すだけで記録の数字が変わってしまう。
        old = pd.read_csv(path, float_precision="round_trip")
    except Exception as e:                # noqa: BLE001
        print(f"  記録 {path} を読めない（{e}）。最初から当てはめる。", flush=True)
        return {}
    if "subj_no" not in old.columns:
        print(f"  記録 {path} に subj_no の列が無い。最初から当てはめる。", flush=True)
        return {}
    out = {}
    for rec in old.to_dict("records"):
        try:
            out[int(rec["subj_no"])] = rec
        except (TypeError, ValueError):
            continue
    return out


def _has_variant(rec: dict, k: str) -> bool:
    """記録にその型の結果が入っているか（`ok_{型}` が書かれているかで見る）。"""
    if not rec:
        return False
    v = rec.get(f"ok_{k}")
    if v is None:
        return False
    try:
        return bool(np.isfinite(float(v)))
    except (TypeError, ValueError):
        return False


def _order_cols(df: pd.DataFrame, variants) -> pd.DataFrame:
    """記録の列を決まった順に並べる（再開して書き直しても同じ CSV になる）。"""
    head = ["subj_no", "fs", "n_samp", "klass_own", "sys_own_ms", "dia_own_ms"]
    per = []
    for k in variants:
        per += ([f"dt_{k}_ms", f"ri_{k}", f"ok_{k}"]
                + [f"{tag}_{k}" for tag, _q in CHK_COLS] + [f"cost_{k}"])
    tail = ["why", "python_version", "numpy_version", "scipy_version"]
    order = [c for c in head + per + tail if c in df.columns]
    rest = [c for c in df.columns if c not in order]
    return df[order + rest]


def build_refit(root: Path, limit: int = 0, jobs: int = 1, variants=VARIANTS_DEFAULT,
                refit_csv=None, resume: bool = True):
    """PWDB の拍に候補の当てはめを当て、記録（CSV）を書き直して表を返す。

    返り値は (この実行で使う表, 記録の場所, 内訳)。表は今回の被験者だけに絞るが、記録には
    前の実行で当てた被験者も残す（再開できるようにするため）。
    """
    root = Path(root).expanduser()
    variants = tuple(variants)
    path = _refit_path(refit_csv, limit)
    hae, _cfg, ppg, _extras = M.load_pwdb(root)
    if limit and limit < len(ppg):
        ppg = c_stride(ppg, limit)
        print(f"  --limit: 等間隔に {len(ppg)} 名を取る（26番と同じ。全年齢層を含めるため）",
              flush=True)
    hr_by = dict(zip(hae["subj_no"].astype(int), hae["HR"].astype(float)))
    have = _cached_rows(path) if resume else {}
    if have:
        print(f"  記録を読んだ: {path}（{len(have)} 名）", flush=True)

    subjects, work, n_cache = [], [], 0
    for i in range(len(ppg)):
        subj = int(ppg.iloc[i, 0])
        subjects.append(subj)
        need = tuple(k for k in variants if not _has_variant(have.get(subj), k))
        if not need:
            n_cache += 1
            continue
        work.append((subj, ppg.iloc[i].to_numpy(float), hr_by.get(subj, np.nan), need))
    print(f"\n  {len(subjects)} 名中 {len(work)} 名に当てはめる"
          f"（記録から {n_cache} 名を再利用）・型 {list(variants)} / jobs={jobs}", flush=True)

    # 版も記録する（26番と同じ。scipy の版が違うと最適化の最終桁が変わりうる）
    import platform
    import time
    import scipy
    meta = {"python_version": platform.python_version(),
            "numpy_version": np.__version__, "scipy_version": scipy.__version__}
    path.parent.mkdir(parents=True, exist_ok=True)

    def _absorb(r: dict) -> None:
        r.update(meta)
        s_ = int(r["subj_no"])
        base = dict(have.get(s_, {}))
        base.update(r)
        have[s_] = base

    def _write() -> pd.DataFrame:
        df_ = _order_cols(pd.DataFrame([have[s_] for s_ in sorted(have)]), variants)
        df_.to_csv(path, index=False)
        return df_

    # 進み具合を PROGRESS_EVERY 名ごとに印字し、CKPT_EVERY 名ごとに記録を書く。
    # 並列でも黙って走らせない（Mac 1 で 4,374 名を --jobs 8 で回すと、印字が無いと
    # 止まっているように見えた。2026-09-15）。途中で止めても記録から再開できる。
    t_start = time.time()
    n_done = 0

    def _tick(r: dict) -> None:
        nonlocal n_done
        _absorb(r)
        n_done += 1
        if n_done % PROGRESS_EVERY == 0 or n_done == len(work):
            el = time.time() - t_start
            eta = el / n_done * (len(work) - n_done)
            print(f"  [{n_done}/{len(work)}] {el:.0f} 秒経過・残り約 {eta:.0f} 秒", flush=True)
        if n_done % CKPT_EVERY == 0 and n_done < len(work):
            _write()
            print(f"  途中の記録を書いた: {path}（{len(have)} 名）", flush=True)

    if work and jobs > 1:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(max_workers=jobs) as ex:
            futs = [ex.submit(refit_subject, w) for w in work]
            for fut in as_completed(futs):
                _tick(fut.result())
    elif work:
        for w in work:
            _tick(refit_subject(w))

    df = _write()
    print(f"  再当てはめの記録: {path}（{len(df)} 名・{len(df.columns)} 列）", flush=True)
    keep = df[df["subj_no"].isin(subjects)].reset_index(drop=True)
    return keep, path, {"n_fit": len(work), "n_cache": n_cache, "n_sub": len(subjects)}


# ---------------------------------------------------------------- 節C の計算の部品
def stage_of(d: pd.DataFrame, ok_col) -> pd.DataFrame:
    """A 段（その型が自分で採用した例だけ）に絞る。`ok_col` が None なら C 段のまま。

    48番の `_stage` と同じ扱いにする（列が無ければ空にする。黙って C 段にしない）。
    """
    if ok_col is None:
        return d
    if ok_col not in d.columns:
        return d.iloc[0:0]
    return d[pd.to_numeric(d[ok_col], errors="coerce") == 1]


def judge_c(d: pd.DataFrame, x: str, y: str, sign: int):
    """年齢層内 Spearman の一式。20番の `_by_age`・`_judge` をそのまま使う（48番と同じ）。"""
    if len(d) == 0 or x not in d.columns or y not in d.columns or "age" not in d.columns:
        return None, []
    rows = M._by_age(d, x, y, min_n=MIN_PER_AGE)
    return M._judge(rows, sign), rows


def _cell(j) -> str:
    """表のます目「|ρ| の中央値（向きの合った層／評価できた層）成立・不成立」。"""
    if not j:
        return "—"
    return (f"{j['med_abs']:.3f}（{j['n_ok']}/{j['n_ages']}）"
            + ("成立" if j["pass"] else "不成立"))


def _age_line_c(rows: list) -> str:
    """年齢層ごとの ρ を 1 行に並べる（48番の `_age_line` と同じ書き方）。"""
    if not rows:
        return "年齢層が取れない"
    return "・".join(f"{int(a)}歳 {_n(r, sign=True)}({n})" for a, r, n in rows)


def _rho_at(rows: list, age: float) -> float:
    """その年齢層の ρ（無ければ NaN）。"""
    for a, r, _n in rows:
        if abs(float(a) - age) < 1e-9:
            return float(r)
    return float("nan")


def _kind_lab(k: str) -> str:
    return f"{_kind_no(k)} {KIND_HEAD[k]}"


def _ktypes():
    """C1〜C4 で分ける型の一覧（型1・型3・型4 と「全」）。"""
    return [(k, f"型{k}") for k in C_KLASSES] + [(None, "全")]


def _sub_k(d: pd.DataFrame, k):
    return d if k is None else subset(d, k)


# ---------------------------------------------------------------- C0
def print_c0(d: pd.DataFrame, variants) -> dict:
    """C0 (0) 凍結版本体の再当てはめが 26番の列と同じ値かを照合する。"""
    print("\n" + "-" * 100)
    print("C0. 照合: (0) 凍結版本体の再当てはめは 26番の列（dt_v1_ms・ri_v1・ok_v1・"
          "klass_own）と同じか")
    print("-" * 100)
    out = {"state": "照合できない", "n": 0, "dt": float("nan"), "ri": float("nan"),
           "n_ok_diff": -1, "n_klass_diff": -1, "n_klass": 0,
           "match": False, "match_p10": False}
    if "fb" not in variants:
        print("  (0) 凍結版本体を当てていないので照合できない（--variants に fb を入れる）。")
        return out
    if COL_V1 not in d.columns:
        print("  26番の列が無いので照合できない（--csv で 26番の出力を渡す）。")
        return out

    def _pair(a_col: str, b_col: str):
        """対応のある行と、その行での差（値の列は |差| の最大、印の列は食い違いの数）。"""
        a, b = _colv(d, a_col), _colv(d, b_col)
        g = np.isfinite(a) & np.isfinite(b)
        if not g.any():
            return 0, float("nan")
        if a_col in ("dt_fb_ms", "ri_fb"):
            return int(g.sum()), float(np.max(np.abs(a[g] - b[g])))
        return int(g.sum()), float(np.sum(a[g] != b[g]))

    n_dt, out["dt"] = _pair("dt_fb_ms", COL_V1)
    n_ri, out["ri"] = _pair("ri_fb", COL_RI_V1)
    n_ok, v_ok = _pair("ok_fb", COL_OK)
    n_kl, v_kl = _pair(KLASS_COL, KLASS_COL + "_26")
    out["n"] = n_dt
    out["n_klass"] = n_kl
    out["n_ok_diff"] = int(v_ok) if np.isfinite(v_ok) else -1
    out["n_klass_diff"] = int(v_kl) if np.isfinite(v_kl) else -1
    print(f"  対応のある行 ΔT {n_dt} 名・RI {n_ri} 名・採否 {n_ok} 名・型 {n_kl} 名")
    print(f"  |dt_fb_ms − dt_v1_ms| の最大   {_n(out['dt'], 9)} ms（許容 {PRED_C0_DT_MS:g}）")
    print(f"  |ri_fb − ri_v1| の最大         {_n(out['ri'], 12)}（許容 {PRED_C0_RI:g}）")
    print("  ok_fb ≠ ok_v1 の人数           "
          + (str(out["n_ok_diff"]) if out["n_ok_diff"] >= 0 else "—（照合できない）"))
    print("  klass_own ≠ klass_own_26 の人数 "
          + (str(out["n_klass_diff"]) if out["n_klass_diff"] >= 0 else "—（照合できない）"))
    ev = bool(n_dt and n_ri and n_ok)
    if not ev:
        out["state"] = "照合できない"
        print("  → 照合できない（対応のある行が無い。26番の CSV がこの被験者を含まない）")
        return out
    out["match_p10"] = bool(out["dt"] <= PRED_C0_DT_MS and out["ri"] <= PRED_C0_RI
                            and out["n_ok_diff"] == 0)
    out["match"] = bool(out["match_p10"] and out["n_klass_diff"] == 0)
    # 型の列が 26番の CSV に無いときは、型の一致は問わない（印字は「—」のまま）
    if out["n_klass_diff"] < 0:
        out["match"] = out["match_p10"]
    out["state"] = "一致" if out["match"] else "食い違いあり"
    print(f"  → {out['state']}")
    if not out["match"]:
        print("  ★ (0) は `src/pda.py` の `fit_beat` をそのまま呼ぶので、26番の列と一致する")
        print("  はずである。食い違うなら入力の拍か版が 26番と違う（この先の表はその前提で読む）。")
    return out


# ---------------------------------------------------------------- C1
def print_c1(d: pd.DataFrame, variants) -> dict:
    """C1 型ごとの採否と縮退の割合（C 段。採否を無視した全例を分母にする）。"""
    print("\n" + "-" * 100)
    print("C1. 採否と縮退: 型ごとに、凍結版の収束検算の規則を当てたときの割合（C 段）")
    print("-" * 100)
    print("  「通過率」は凍結版と同じ規則（境界張り付き・高さ 0.02・競合解の RI 差 0.08）を")
    print("  当てて採用になった割合、すなわち A 段に残る割合である。")
    print("  「Δμ下限率」は Δμ が探索範囲の下限に張り付いた割合で、2 成分の縮退の目安である。")
    print("  n は当てはめを試した拍の数（拍を作れなかった被験者は数えない）。縮退の 4 列は、")
    print("  解が出た拍だけを分母にする。")
    out = {}
    for kt, kname in _ktypes():
        g = _sub_k(d, kt)
        lab = KLASS_LABEL.get(kt, "全例（型を分けない）")
        print(f"\n  {lab}  n = {len(g)} 名")
        print("    " + _pad("当てはめの型", 18) + _pad("n", 8, right=True)
              + _pad("通過率", 10, right=True)
              + "".join(_pad(CHK_HEAD[t], 12, right=True) for t, _q in CHK_COLS))
        for k in variants:
            ok = _colv(g, f"ok_{k}")
            n = int(np.isfinite(ok).sum())
            rec = {"n": n,
                   "ok": float(np.nanmean(ok)) if n else float("nan")}
            for tag, _q in CHK_COLS:
                v = _colv(g, f"{tag}_{k}")
                rec[tag] = float(np.nanmean(v)) if np.isfinite(v).any() else float("nan")
            out[(kt, k)] = rec
            print("    " + _pad(_kind_lab(k), 18) + _pad(n, 8, right=True)
                  + _f(rec["ok"], 10)
                  + "".join(_f(rec[t], 12) for t, _q in CHK_COLS))
    print("\n  出典: この台本（50番）の節C が PWDB の拍に当てはめ直して数えた値。")
    return out


# ---------------------------------------------------------------- C2・C3
def _rows_for(d: pd.DataFrame, variants, pre: str, suf: str, ref_col: str, ref_lab: str,
              lm_col: str, lm_lab: str) -> list:
    """C2・C3 の行（表示名, 列, 採否の列, 段）。参考の 2 行は末尾に置く。"""
    rows = []
    for k in variants:
        col = f"{pre}{k}{suf}"
        rows.append((_kind_lab(k), col, f"ok_{k}", "A"))
        rows.append((_kind_lab(k), col, None, "C"))
    if ref_col in d.columns:
        rows.append((ref_lab, ref_col, COL_OK, "A"))
        rows.append((ref_lab, ref_col, None, "C"))
    if lm_col in d.columns:
        rows.append((lm_lab, lm_col, None, "C"))
    return rows


def print_c_matrix(d: pd.DataFrame, rows: list, tgt: str, sign: int) -> dict:
    """型 × 当てはめの表。ます目は |ρ| の中央値（向きの層／評価層）と規準の成立・不成立。"""
    types = _ktypes()
    print("  " + _pad("当てはめ（段）", 22)
          + "".join(_pad(nm, 19, right=True) for _k, nm in types))
    out = {}
    for lab, col, ok_col, stg in rows:
        line = "  " + _pad(f"{lab} {stg}", 22)
        for kt, _nm in types:
            g = stage_of(_sub_k(d, kt), ok_col)
            j, ages = judge_c(g, col, tgt, sign)
            out[(col, stg, kt)] = {"j": j, "rows": ages, "n": len(g)}
            line += _pad(_cell(j), 19, right=True)
        print(line)
    return out


def print_c2(d: pd.DataFrame, variants) -> dict:
    """C2 ΔT × 大動脈脈波伝播速度（予測の向き 負）。"""
    print("\n" + "-" * 100)
    print(f"C2. ΔT × 大動脈脈波伝播速度 {COL_PWV}（予測の向き 負。年齢層内 Spearman）")
    print("-" * 100)
    print(f"  層は `age` の相異なる値、1 層 {MIN_PER_AGE} 名以上（20番の `_by_age`・`_judge`）。")
    print("  段 A はその当てはめが自分で採用した例だけ（ok_{型} == 1）、段 C は採否を無視した全例。")
    print("  ます目は **|ρ| の中央値（予測の向きに合った層数／評価できた層数）** と、")
    print(f"  20番 `_judge` の規準（|中央値| ≥ {M.CRIT_RHO:.2f} かつ全層で向きが合う）に対する")
    print("  **規準 成立／不成立**。**この印は事後の記述であり、26番の判定は動かない。**")
    rows = _rows_for(d, variants, "dt_", "_ms", COL_V1, "（参考）凍結版 26番",
                     COL_LM, "（参考）同梱の特徴点")
    out = print_c_matrix(d, rows, COL_PWV, SIGN_DT)
    print("  出典: この台本（50番）の節C が PWDB の拍に当てはめ直して計算した値"
          "（参考の 2 行は既存列）。")
    return out


def print_c3(d: pd.DataFrame, variants) -> dict:
    """C3 RI × 末梢血管抵抗（予測の向き 正）。型3・A 段は年齢層別の ρ も並べる。"""
    print("\n" + "-" * 100)
    print(f"C3. RI × 末梢血管抵抗 {COL_PVR}（予測の向き 正。年齢層内 Spearman）")
    print("-" * 100)
    print("  読み方は C2 と同じ。節A-2 で凍結版の RI は型3 相当の条件で符号が反転したので、")
    print("  型3 の列と、その 75 歳層の ρ を見る。")
    rows = _rows_for(d, variants, "ri_", "", COL_RI_V1, "（参考）凍結版 26番",
                     COL_RI_LM, "（参考）同梱の特徴点")
    out = print_c_matrix(d, rows, COL_PVR, SIGN_RI)
    print(f"\n  型3・A 段の年齢層別 ρ（{AGE_OLD:.0f} 歳層を見るため。括弧内は人数）:")
    for lab, col, ok_col, stg in rows:
        if stg != "A":
            continue
        rec = out.get((col, stg, 3), {})
        print("    " + _pad(lab, 22) + _age_line_c(rec.get("rows", [])))
    print("  出典: この台本（50番）の節C が PWDB の拍に当てはめ直して計算した値"
          "（参考の 2 行は既存列）。")
    return out


# ---------------------------------------------------------------- C4
def print_c4(d: pd.DataFrame, variants) -> dict:
    """C4 同梱の特徴点 ΔT との一致（差の中央値と、まとめた順位相関）。"""
    print("\n" + "-" * 100)
    print(f"C4. 一致: 当てはめの ΔT は同梱の特徴点 {COL_LM} と同じ値か（48番 節4 と同じ見方）")
    print("-" * 100)
    print("  差の中央値は（当てはめの ΔT − 同梱の特徴点 ΔT）[ms]、ρ は年齢層で分けずに")
    print(f"  まとめた Spearman（20番の `_spearman`・{MIN_N_POOL} 名以上）。対応のある行だけ。")
    out = {}
    rows = [(_kind_lab(k), f"dt_{k}_ms", f"ok_{k}", "A") for k in variants]
    rows += [(_kind_lab(k), f"dt_{k}_ms", None, "C") for k in variants]
    if COL_V1 in d.columns:
        rows += [("（参考）凍結版 26番", COL_V1, COL_OK, "A"),
                 ("（参考）凍結版 26番", COL_V1, None, "C")]
    for kt, _nm in _ktypes():
        g0 = _sub_k(d, kt)
        lab = KLASS_LABEL.get(kt, "全例（型を分けない）")
        print(f"\n  {lab}  n = {len(g0)} 名")
        print("    " + _pad("当てはめの型", 22) + _pad("段", 4, right=True)
              + _pad("n", 8, right=True) + _pad("差の中央値[ms]", 16, right=True)
              + _pad("|差|の中央値[ms]", 18, right=True) + _pad("ρ", 10, right=True))
        for name, col, ok_col, stg in rows:
            g = stage_of(g0, ok_col)
            a, b = _colv(g, col), _colv(g, COL_LM)
            ok = np.isfinite(a) & np.isfinite(b)
            n = int(ok.sum())
            v = a[ok] - b[ok]
            med = float(np.median(v)) if n else float("nan")
            mad = float(np.median(np.abs(v))) if n else float("nan")
            rho, _nn = M._spearman(a, b, min_n=MIN_N_POOL)
            out[(kt, col, stg)] = {"n": n, "med": med, "med_abs": mad, "rho": rho}
            print("    " + _pad(name, 22) + _pad(stg, 4, right=True)
                  + _pad(n, 8, right=True) + _f(med, 16, prec=1, sign=True)
                  + _f(mad, 18, prec=1) + _f(rho, 10, prec=3, sign=True))
    print("\n  出典: この台本（50番）の節C が PWDB の拍に当てはめ直して計算した値。")
    return out


# ---------------------------------------------------------------- C5
def _pass_of(cells: dict, col: str, stg: str, kt) -> tuple:
    """表のます目から (照合できるか, 規準を満たすか, ます目の文字, 年齢層ごとの ρ) を取る。"""
    rec = cells.get((col, stg, kt), {})
    j = rec.get("j")
    return (j is not None), bool(j and j["pass"]), _cell(j), rec.get("rows", [])


def print_c5(c0: dict, c1: dict, c2: dict, c3: dict, variants) -> dict:
    """C5 予測との照合（P6〜P10）。**判定は付けない**（事後・記述）。"""
    print("\n" + "-" * 100)
    print("C5. 予測との照合（予測は 2026-09-15 に、実データを見る前に固定した。docstring と同文）")
    print("-" * 100)
    print(f"  (P6) 型3・A 段: (4) conv の ΔT × PWV_a が `_judge` の規準を満たす"
          f"（|中央値| ≥ {M.CRIT_RHO:.2f} かつ全層で符号が合う）。")
    print(f"  (P7) 型3・C 段: (2) relax の Δμ 下限張り付きの割合が (4) conv より "
          f"{PRED_P7_GAP:.2f} 以上大きい。")
    print(f"  (P8) 型3・A 段: (4) conv の RI × pvr で {AGE_OLD:.0f} 歳層の ρ > 0 かつ "
          f"|中央値| ≥ {PRED_P8_MED:.2f}。")
    print("  (P9) 型1・A 段: (4) conv の ΔT × PWV_a が `_judge` の規準を満たす。")
    print("  (P10) 検算: (0) fb の ΔT・RI・採否が 26番の列と全例一致、かつ同梱の特徴点の型別")
    print(f"        ρ(dt_lm_ms, PWV_a) が 型1 {PRED_P10_LM[1]:.3f}・型3 {PRED_P10_LM[3]:.3f}"
          f"（小数 {PRED_P10_PREC} 桁で一致）を再現")
    print("        （26番の列が無ければ「照合できない」）。")
    have_conv = "conv" in variants
    have_relax = "relax" in variants
    res = {}

    def _judge_pred(tag: str, kt: int, name: str) -> None:
        """P6・P9（(4) 畳み込みの ΔT × 大動脈PWV。A 段）を同じ書き方で印字する。"""
        if not have_conv:
            print(f"\n  {tag} {name}・A 段  → 照合できない（--variants に conv が無い）")
            res[tag] = {"ev": False, "hit": False}
            return
        ev, hit, cell, _rows = _pass_of(c2, "dt_conv_ms", "A", kt)
        print(f"\n  {tag} {name}・A 段  (4) 畳み込み ΔT × {COL_PWV}: {cell}")
        print("     → `_judge` の規準を満たす: "
              + (f"{_yn(hit)}（規準 {'成立' if hit else '不成立'}）" if ev
                 else "照合できない（8 名以上の年齢層が無い）"))
        res[tag] = {"ev": ev, "hit": hit}

    _judge_pred("P6", 3, "型3")

    # --- P7（Δμ 下限張り付きの割合。型3・C 段）
    r_rx = c1.get((3, "relax"), {}).get("dmulo", float("nan")) if have_relax else float("nan")
    r_cv = c1.get((3, "conv"), {}).get("dmulo", float("nan")) if have_conv else float("nan")
    gap = r_rx - r_cv
    ev7 = bool(np.isfinite(gap))
    hit7 = bool(ev7 and gap >= PRED_P7_GAP)
    print(f"\n  P7 型3・C 段  (2) Δμ0.01 の Δμ 下限 {_n(r_rx)}・(4) 畳み込み {_n(r_cv)}"
          f"・差 {_n(gap, sign=True)}")
    print(f"     → 差が {PRED_P7_GAP:.2f} 以上: "
          + (_yn(hit7) if ev7 else "照合できない（どちらかの割合が出ていない）"))
    res["P7"] = {"ev": ev7, "hit": hit7, "gap": gap}

    # --- P8（RI × 末梢血管抵抗。型3・A 段の 75 歳層）
    if have_conv:
        ev, _hit, cell, rows = _pass_of(c3, "ri_conv", "A", 3)
        rho_old = _rho_at(rows, AGE_OLD)
        med = c3.get(("ri_conv", "A", 3), {}).get("j")
        med_abs = med["med_abs"] if med else float("nan")
        ev8 = bool(np.isfinite(rho_old) and np.isfinite(med_abs))
        hit8 = bool(ev8 and rho_old > 0 and med_abs >= PRED_P8_MED)
        print(f"\n  P8 型3・A 段  (4) 畳み込み RI × {COL_PVR}: {cell}"
              f"・{AGE_OLD:.0f} 歳層 {_n(rho_old, sign=True)}")
        print(f"     層ごと: {_age_line_c(rows)}")
        print(f"     → {AGE_OLD:.0f} 歳層の ρ > 0 かつ |中央値| ≥ {PRED_P8_MED:.2f}: "
              + (_yn(hit8) if ev8 else f"照合できない（{AGE_OLD:.0f} 歳層の ρ が出ていない）"))
    else:
        ev8, hit8 = False, False
        print("\n  P8 型3・A 段  → 照合できない（--variants に conv が無い）")
    res["P8"] = {"ev": ev8, "hit": hit8}

    _judge_pred("P9", 1, "型1")

    # --- P10（検算。(0) と 26番の列、同梱の特徴点の型別 |ρ|）
    lm = {}
    for kt in (1, 3):
        j = c2.get((COL_LM, "C", kt), {}).get("j")
        lm[kt] = j["med_abs"] if j else float("nan")
    ev10 = bool(c0.get("state") != "照合できない"
                and all(np.isfinite(lm[kt]) for kt in (1, 3)))
    hit10 = bool(ev10 and c0.get("match_p10")
                 and all(round(lm[kt], PRED_P10_PREC) == PRED_P10_LM[kt] for kt in (1, 3)))
    if c0.get("state") == "照合できない":
        print("\n  P10 検算  (0) と 26番の列: 照合できない（26番の CSV が無いか、"
              "対応のある行が無い）")
    else:
        print(f"\n  P10 検算  (0) と 26番の列: {c0.get('state')}"
              f"（{c0.get('n')} 名・ΔT の差の最大 {_n(c0.get('dt', float('nan')), 9)} ms・"
              f"RI {_n(c0.get('ri', float('nan')), 12)}・"
              f"採否の食い違い {c0.get('n_ok_diff')} 名）")
    print(f"      同梱の特徴点の型別 |ρ|（C 段）: 型1 {_n(lm[1])}（予測 {PRED_P10_LM[1]:.3f}）"
          f"・型3 {_n(lm[3])}（予測 {PRED_P10_LM[3]:.3f}）")
    print("     → 全例一致かつ型別 |ρ| を再現: "
          + (_yn(hit10) if ev10 else "照合できない（26番の列が無い・層の人数が足りない）"))
    res["P10"] = {"ev": ev10, "hit": hit10, "lm": lm}

    ev = sum(1 for k in ("P6", "P7", "P8", "P9", "P10") if res[k]["ev"])
    hit = sum(1 for k in ("P6", "P7", "P8", "P9", "P10") if res[k]["hit"])
    print(f"\n  まとめ: 予測 5 条のうち照合できたのは {ev} 条、そのうち「はい」は {hit} 条。")
    if ev < 5:
        print("  照合できなかった条は、人数が足りないか列・型が無いためである。")
        print("  この実行が抜粋（--limit）なら、確認的解析の機械で全例を回して読み直す。")
    print("  **この節は事後の記述であり、判定（成立・不成立）は付けない。**"
          "26番の事前規準による判定は動かない。")
    res["n_eval"] = ev
    res["hit"] = hit
    return res


# ---------------------------------------------------------------- 節C の入口
def section_c(root, limit: int = 0, jobs: int = 1, variants=VARIANTS_DEFAULT,
              refit_csv=None, resume: bool = True, d26=None, src26: str = "") -> dict:
    """節C: 候補の当てはめを PWDB の同じ拍に当て、26番の枠組みで並べる（探索・事後）。"""
    print("\n" + "=" * 100)
    print("節C 実データ（PWDB）: 候補の当てはめを同じ拍に当てる"
          "（探索・事後。26番の判定は動かない）")
    print("=" * 100)
    variants = tuple(variants)
    bad = [k for k in variants if k not in KIND_KEYS]
    if bad:
        raise ValueError(f"知らない当てはめの型: {bad}（使えるのは {list(KIND_KEYS)}）")
    root = Path(root).expanduser()
    print(f"  入力 {root}（PWDB の配布物）")
    print("  拍の作り方は 26番と同じ（20番の `load_pwdb`・`beat_of`）。型 klass_own も")
    print("  26番と同じ手順（`pda2.preprocess` → `find_landmarks`）で自分で付ける。")
    print("  当てはめ: " + "・".join(_kind_lab(k) for k in variants))

    ref, path, info = build_refit(root, limit=limit, jobs=jobs, variants=variants,
                                  refit_csv=refit_csv, resume=resume)
    L = _landmarks_module()
    d = L.load(root, pda_dir=root / "__no_pda__")
    d = d.drop(columns=[c for c in ("dt_pda_ms", "ri_pda", "ok2") if c in d.columns])
    n_truth, n_ref = len(d), len(ref)
    d = d.merge(ref, on="subj_no", how="inner")
    print(f"\n  真値・同梱の特徴点 {n_truth} 名・再当てはめ {n_ref} 名 → "
          f"突き合わせ {len(d)} 名（内部結合。26番と同じ扱い）")
    if d26 is not None and "subj_no" in getattr(d26, "columns", []):
        cols = [c for c in ("subj_no", COL_V1, COL_RI_V1, COL_OK, KLASS_COL)
                if c in d26.columns]
        d = d.merge(d26[cols], on="subj_no", how="left", suffixes=("", "_26"))
        n26 = int(np.isfinite(_colv(d, COL_V1)).sum())
        print(f"  26番の列を結合した（{src26}・{n26} 名ぶん）。C0 と C2・C3 の参考行に使う。")
    else:
        print("  26番の CSV が無いので C0 の照合と参考行は飛ばす（--csv で渡せる）。")
    for c in (COL_PWV, COL_PVR, COL_LM, COL_RI_LM, "age", KLASS_COL, KLASS_COL + "_26"):
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    ages = sorted(pd.to_numeric(d["age"], errors="coerce").dropna().unique().tolist()) \
        if "age" in d.columns else []
    kl = _colv(d, KLASS_COL)
    seen = sorted(set(int(v) for v in kl[np.isfinite(kl)]))
    print(f"  年齢層 {[int(a) for a in ages]}・型の値 {seen}"
          + (f"・型の欠測 {int(np.sum(~np.isfinite(kl)))} 名"
             if np.any(~np.isfinite(kl)) else "・型の欠測なし"))
    why = d["why"].dropna().astype(str) if "why" in d.columns else pd.Series(dtype=str)
    why = why[why != ""]
    if len(why):
        top = why.value_counts().head(5).to_dict()
        print(f"  当てはめの失敗 {len(why)} 名: {top}")
    if len(d) < 100:
        print(f"  ★ この実行は {len(d)} 名の抜粋である（1 層 "
              f"{len(d) // max(len(ages), 1)} 名）。**ここから出る数値は読んではいけない。**")

    out = {"state": 0, "n": len(d), "path": str(path), "info": info,
           "variants": variants}
    out["c0"] = print_c0(d, variants)
    out["c1"] = print_c1(d, variants)
    out["c2"] = print_c2(d, variants)
    out["c3"] = print_c3(d, variants)
    out["c4"] = print_c4(d, variants)
    out["c5"] = print_c5(out["c0"], out["c1"], out["c2"], out["c3"], variants)
    return out


# ---------------------------------------------------------------- まとめ
def print_no_pwdb() -> None:
    """節C を頼まれたのに --pwdb が無いときの案内（CSV が無いときと同じ扱いで落とす）。"""
    print("\n  節C は PWDB の配布物が要る（--pwdb で渡す）。")
    print("  例: python3 scripts/50_reservoir_bench.py --section C --pwdb ~/pwdb --jobs 8")
    print("  配布物は Charlton らの PWDB（pwdb_haemod_params.csv・pwdb_model_configs.csv・")
    print("  pwdb_pw_indices.csv・PWs/csv/PWs_Digital_PPG.csv）を置いたフォルダである。")


def report(section: str, d=None, src: str = "", taus=TAUS_FULL, dts=DTS_FULL,
           ris=RIS_FULL, seed: int = SEED_A, pwdb=None, limit: int = 0, jobs: int = 1,
           variants=VARIANTS_DEFAULT, refit_csv=None, resume: bool = True) -> dict:
    """節A（ΔT）・節A-2（RI）・節B・節C を印字する。返り値は計算した値と終了コード。"""
    print("\n" + "=" * 100)
    print("50番 探索的（事後）: 当てはめの型と、凍結版 ΔT が下限で詰まること")
    print("=" * 100)
    print("  論文2・探索的（事後）。**判定（成立・不成立）は付けない。**事前規準による")
    print("  判定は 26番のものが有効で、この台本の出力は事後の記述である。")
    out = {"code": 0}
    if "A" in section:
        out["A"] = section_a(taus, dts, seed=seed)
        out["A2"] = section_a2(RI_CONDS, ris, seed=seed)
    if "B" in section:
        if d is None:
            print("\n  節B は CSV が無いので走らせない（--csv で 26番の出力を渡す）。")
            out["code"] = 2
        else:
            out["B"] = section_b(d, src)
            if out["B"]["state"] != 0:
                out["code"] = 2
    if "C" in section:
        if pwdb is None:
            print_no_pwdb()
            out["code"] = 2
        else:
            try:
                out["C"] = section_c(Path(pwdb), limit=limit, jobs=jobs,
                                     variants=variants, refit_csv=refit_csv,
                                     resume=resume, d26=d, src26=src)
            except (FileNotFoundError, OSError) as e:
                print(f"\n  ★ PWDB を読めない: {e}")
                print_no_pwdb()
                out["code"] = 2
    print("\n" + "-" * 100)
    a_txt = (f"節A 合成脈波（時定数 {len(list(taus))} 通り × 到達 {len(list(dts))} 通り）"
             f"＋ 節A-2（条件 {len(RI_CONDS)} 通り × 大きさ {len(list(ris))} 通り）"
             if "A" in section else "節A・節A-2 なし")
    a_txt2 = (f"当てはめ {len(KIND_KEYS)} 型・雑音 SD {NOISE_SD}・乱数種 {seed}"
              if "A" in section else "")
    b_txt = (f"節B {src}（{len(d)} 名・型の列 {KLASS_COL}・A 段 {COL_OK} == 1）"
             if ("B" in section and d is not None) else "節B なし")
    c = out.get("C")
    c_txt = (f"節C {pwdb}（{c['n']} 名・当てはめ {list(c['variants'])}・"
             f"記録 {c['path']}）" if c else "節C なし")
    print("  出典: analysis/scripts/50_reservoir_bench.py")
    print(f"        / {a_txt}")
    if a_txt2:
        print(f"          （{a_txt2}）")
    print(f"        / {b_txt}")
    print(f"        / {c_txt}")
    print("  年齢層内 Spearman の規約は 20番 `20_pwdb_validity.py` の `_spearman`・`_judge`")
    print(f"  をそのまま使う（1 層 {MIN_PER_AGE} 名以上・層は `age` の相異なる値）。")
    return out


# ---------------------------------------------------------------- 自己検査
# 節B の部品を試す合成データ。型3 だけ凍結版 ΔT を FLOOR_SYN_MS で止め、型1 は特徴点法に
# 載せる。これで P1・P2 が「はい」、P3 も「はい」になるはずである。
AGES_SYN = (25, 35, 45, 55, 65, 75)
N_PER_AGE_SYN = 300
LM_LO_SYN, LM_HI_SYN = 60.0, 260.0     # 特徴点法 ΔT の範囲 [ms]
FLOOR_SYN_MS = 150.0                   # 型3 に仕込む下限 [ms]
JIT_SYN_MS = 4.0                       # 当てはめの雑音 [ms]
P_KLASS1_SYN = 0.35
# RI の仕込み（B4・P4・P5 の部品を試すため）。型1 は特徴点法に載せ、型3 は年齢層ごとに
# 関係の強さを変えて、高齢の層ほど逆向きにする。
RI_LO_SYN, RI_HI_SYN = 0.20, 0.70      # 特徴点法 RI の範囲
RI_JIT_SYN = 0.05                      # 当てはめの雑音
RI_SLOPE_SYN = (0.6, 0.4, 0.2, 0.0, -0.3, -0.6)     # 型3 の傾き（25〜75 歳層）
RI_SLOPE_FLAT = 1.0                    # 型1 の傾き（年齢層によらない）


def synth_b(seed: int = 0) -> pd.DataFrame:
    """節B の部品を試す合成データ。

    ΔT: 型3 は下限（FLOOR_SYN_MS）で詰まり、型1 は詰まらない。
    RI: 型1 は特徴点法に載る（ρ ≈ +1・年齢層による差なし）。型3 は年齢層ごとに傾きを
        変え、高齢の層ほど逆向きにする（P4 の仕込み）。
    """
    rng = np.random.default_rng(seed)
    frames = []
    for k_age, age in enumerate(AGES_SYN):
        n = N_PER_AGE_SYN
        lm = rng.uniform(LM_LO_SYN, LM_HI_SYN, n)
        klass = np.where(rng.random(n) < P_KLASS1_SYN, 1.0, 3.0)
        jit = rng.normal(0.0, JIT_SYN_MS, n)
        v1 = np.where(klass == 1.0, lm + jit, np.maximum(lm, FLOOR_SYN_MS) + jit)
        ri_lm = rng.uniform(RI_LO_SYN, RI_HI_SYN, n)
        ri_jit = rng.normal(0.0, RI_JIT_SYN, n)
        slope = np.where(klass == 1.0, RI_SLOPE_FLAT, RI_SLOPE_SYN[k_age])
        ri_v1 = 0.30 + slope * (ri_lm - 0.45) + ri_jit
        frames.append(pd.DataFrame({"age": age, KLASS_COL: klass, COL_LM: lm,
                                    COL_V1: v1, COL_RI_LM: ri_lm, COL_RI_V1: ri_v1,
                                    COL_OK: 1}))
    return pd.concat(frames, ignore_index=True)


def selftest() -> int:
    n_fail = 0

    def rep(name, cond, detail=""):
        nonlocal n_fail
        cond = bool(cond)
        if not cond:
            n_fail += 1
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))

    print("50番 自己検査（合成だけで走る。CSV もネットワークも要らない）")
    print(f"  節A の掃引は {len(TAUS_FAST)} 層 × {len(DTS_FAST)} 拍に減らす"
          f"（本番は {len(TAUS_FULL)} 層 × {len(DTS_FULL)} 拍）。")
    print(f"  節A-2 は {len(RI_CONDS)} 条件 × {len(RIS_FAST)} 拍に減らす"
          f"（本番は {len(RI_CONDS)} 条件 × {len(RIS_FULL)} 拍）。")

    import inspect
    rep("順位相関の規約を 20番と共有している（_spearman・_judge・層の人数）",
        M.CRIT_RHO == 0.30
        and inspect.signature(M._by_age).parameters["min_n"].default == MIN_PER_AGE,
        f"CRIT_RHO {M.CRIT_RHO} / 層の人数 {MIN_PER_AGE}")

    # --- 合成脈波そのもの
    t, y, tr = synth_beat(0.20, 0.45)
    rep("合成脈波を作れる（真値は成分のピークの差で、母数の差とは違う）",
        t.size == int(round(FS * 60.0 / HR_SYN)) and np.isfinite(tr["dt_s"])
        and abs(tr["dt_s"] - 0.20) > 0.005,
        f"{t.size} 標本・真値 {1000 * tr['dt_s']:.0f} ms（設定 200 ms）")

    # --- (a-1) 下限の詰まりの検出器そのもの（いま使う規準と、差し替える前の規準）
    truth5 = np.array([250.0, 200.0, 150.0, 100.0, 50.0])
    stuck = np.array([250.0, 200.0, 190.0, 187.0, 185.0])   # 下限 185 ms で止めた列
    prop = np.array([255.0, 205.0, 155.0, 105.0, 55.0])     # 真値に比例する列
    f_stuck, f_prop = floor_check(truth5, stuck), floor_check(truth5, prop)
    rep("(a) 検出器: 人工的に下限で止めた列で「あり」（新しい規準・差し替える前の規準とも）",
        f_stuck["flag_gap"] and f_stuck["flag_range"],
        f"返り値の最小 − 真値の最大 {f_stuck['gap']:+.0f} ms"
        f"（要 {FLOOR_GAP_MS:.0f} 以上）・下位 {FLOOR_N} 拍の範囲 {f_stuck['rng']:.0f} ms")
    rep("(a) 検出器: 真値に比例する列では「なし」（同上）",
        (not f_prop["flag_gap"]) and (not f_prop["flag_range"]),
        f"返り値の最小 − 真値の最大 {f_prop['gap']:+.0f} ms・"
        f"下位 {FLOOR_N} 拍の範囲 {f_prop['rng']:.0f} ms")

    # --- 節A を減らした掃引で 1 回走らせる（(a-2)・(b)・(e) で使い回す）
    buf = io.StringIO()
    with redirect_stdout(buf):
        a0 = section_a(TAUS_FAST, DTS_FAST, seed=SEED_A)
    txt_a0 = buf.getvalue()
    summ, res = a0["summ"], a0["res"]
    rep("節A が減らした掃引で最後まで印字される",
        "A2. 時定数の層ごとの表" in txt_a0 and len(txt_a0) > 1000,
        f"{len(txt_a0)} 文字・{len(TAUS_FAST)} 層 × {len(DTS_FAST)} 拍")

    # --- (a-2) 凍結版が短い側で下限に詰まる（本文の所見そのもの）
    det = []
    for tau in TAUS_FAST:
        rec = res[float(tau)]
        truth = np.asarray(rec["truth"], float)
        got = np.asarray(rec["got"]["frozen"], float)
        order = np.argsort(truth)
        d2 = abs(got[order[0]] - got[order[1]])          # 真値が 20 ms 違う 2 拍
        td = abs(truth[order[0]] - truth[order[1]])      # その 2 拍の真値の差
        fl = summ[("frozen", float(tau))]["floor"]
        det.append((tau, d2, fl["got_min"] - float(np.min(truth)), fl, td))
    # 規準は「返り値の差が真値の差の 1/4 未満」（順位の尺度が 4 倍以上に縮んでいる）。
    # 2026-09-15 までは「差 1 ms 未満」だったが、それは汎用の起点 4 点の複製が 2 拍で
    # 同じ値を返していたことに合わせた文言で、凍結版本体は 173・175 ms（差 1.7 ms）を
    # 返す。起点を凍結版と同じにしたときに実態に合わせて直した（lab_log 追記143）。
    rep("(a) 凍結版は短い側で下限に詰まる（真値が 20 ms 違う 2 拍で返り値の差が真値の差の"
        " 1/4 未満）",
        all(dd < 0.25 * td for _t, dd, _g, _fl, td in det),
        "・".join(f"時定数 {t_:.2f}s 返り値の差 {dd:.1f} ms（真値の差 {td:.0f} ms）"
                  for t_, dd, _g, _fl, td in det))
    rep("(a) 凍結版の返り値の最小は真値の最小より 60 ms 以上大きい（短い側を追えない）",
        all(g >= 60.0 for _t, _d, g, _fl, _td in det),
        "・".join(f"時定数 {t_:.2f}s +{g:.0f} ms" for t_, _d, g, _fl, _td in det))

    # 新しい規準（2026-09-15 差し替え）の検算。時定数 0.45 s の層で、凍結版だけが「あり」
    tau0 = float(TAUS_FAST[0])
    fl_fz = summ[("frozen", tau0)]["floor"]
    rep(f"(a) 新しい規準で凍結版が「あり」（時定数 {tau0:.2f} s の層）",
        fl_fz["flag_gap"],
        f"下位 {FLOOR_N} 拍の返り値の最小 {fl_fz['lo']:.0f} ms − 真値の最大 "
        f"{fl_fz['truth_max']:.0f} ms = {fl_fz['gap']:+.0f} ms（要 {FLOOR_GAP_MS:.0f} 以上）")
    none_keys = ("relax", "conv", "conv01", "trunc")
    rep("(a) 新しい規準で Δμ0.01・畳み込み・(4b) 畳み込み＋Δμ0.01・0.65T は「なし」"
        f"（時定数 {tau0:.2f} s の層）",
        all(not summ[(k, tau0)]["floor"]["flag_gap"] for k in none_keys),
        "・".join(f"{_kind_no(k)}{KIND_HEAD[k]} {summ[(k, tau0)]['floor']['gap']:+.0f} ms"
                  for k in none_keys))

    # (0) 凍結版本体も、複製 (1) と同じように短い側で下限に詰まるか。閾値 60 ms は上の
    # (1) の検査と同じものを使う。ここが落ちたら、複製が本体と同じ振る舞いをしていない。
    det_fb = []
    for tau in TAUS_FAST:
        tmin = float(np.min(np.asarray(res[float(tau)]["truth"], float)))
        det_fb.append((float(tau),
                       summ[("fb", float(tau))]["floor"]["got_min"] - tmin,
                       summ[("frozen", float(tau))]["floor"]["got_min"] - tmin))
    rep("(0) 凍結版本体も短い側で下限に詰まる（複製 (1) と同じ印）",
        summ[("fb", tau0)]["floor"]["flag_gap"]
        and all(np.isfinite(g0) and g0 >= 60.0 for _t, g0, _g1 in det_fb),
        "返り値の最小 − 真値の最小: "
        + "・".join(f"時定数 {t_:.2f}s (0) {g0:+.0f} ms / (1) {g1:+.0f} ms"
                    for t_, g0, g1 in det_fb))
    print("    参考: 差し替える前の規準（下位 3 拍の返り値の範囲 < "
          f"{FLOOR_RANGE_MS:.0f} ms）での凍結版の印字は "
          + "・".join(f"時定数 {t_:.2f}s {_ari(fl['flag_range'])}"
                      f"（範囲 {fl['rng']:.0f} ms）" for t_, _d, _g, fl, _td in det)
          + "。これが取り逃がしである。")

    # (0)(4b)(5b)(6b): 凍結版本体が先頭にあり、一度に 1 つだけ変える版が並んでいるか
    rep("当てはめの型が 10 行あり、先頭が (0) 凍結版本体・(4b) は (2) と (4) の同時適用・"
        "(5b)(6b) は Δμ の下限だけが (5)(6) と違う",
        len(KIND_KEYS) == 10 and KIND_KEYS[0] == "fb"
        and KIND_NO["fb"] == "(0)" and KIND_NO["conv01"] == "(4b)"
        and KIND_SHAPE["conv01"] == "conv"
        and ("conv01" not in KIND_DMU_FROZEN) and ("fb" in KIND_DMU_FROZEN)
        and KIND_NO["tied08"] == "(5b)" and KIND_NO["trunc08"] == "(6b)"
        and KIND_SHAPE["tied08"] == KIND_SHAPE["tied"]
        and KIND_SHAPE["trunc08"] == KIND_SHAPE["trunc"]
        and ("tied08" in KIND_DMU_FROZEN) and ("trunc08" in KIND_DMU_FROZEN)
        and ("tied" not in KIND_DMU_FROZEN) and ("trunc" not in KIND_DMU_FROZEN)
        and all(np.isfinite(res[tau0]["got"][k]).all()
                for k in ("fb", "conv01", "tied08", "trunc08")),
        "・".join(f"{_kind_no(k)} ρ {summ[(k, tau0)]['rho']:+.2f}"
                  for k in ("fb", "frozen", "conv", "conv01",
                            "tied", "tied08", "trunc", "trunc08")))

    # --- (b) 畳み込み貯留槽の ρ が凍結版より大きい
    pairs = [(tau, summ[("frozen", float(tau))]["rho"], summ[("conv", float(tau))]["rho"])
             for tau in TAUS_FAST]
    rep("(b) 畳み込み貯留槽の ρ が凍結版より大きい（両層）",
        all(np.isfinite(a) and np.isfinite(b) and b > a for _t, a, b in pairs),
        "・".join(f"時定数 {t_:.2f}s 凍結版 {a:+.2f} → 畳み込み {b:+.2f}"
                  for t_, a, b in pairs))

    # --- 節A-2（RI）を減らした掃引で走らせる
    bufr = io.StringIO()
    with redirect_stdout(bufr):
        a2 = section_a2(RI_CONDS, RIS_FAST, seed=SEED_A)
    txt_a2 = bufr.getvalue()
    s2 = a2["summ"]
    rep("節A-2 が減らした掃引で最後まで印字される",
        "A2-1. 条件ごとの表" in txt_a2 and len(txt_a2) > 1000,
        f"{len(txt_a2)} 文字・条件 {len(RI_CONDS)} 通り × 大きさ {len(RIS_FAST)} 通り")
    rho_fz3 = s2[("frozen", "型3 相当")]["rho"]
    rho_rx3 = s2[("relax", "型3 相当")]["rho"]
    rho_fz1 = s2[("frozen", "型1 相当")]["rho"]
    rep("(a2) 型3 相当で凍結版の RI の ρ が負（符号の反転）",
        s2[("frozen", "型3 相当")]["flip"] and rho_fz3 < RHO_FLIP,
        f"ρ {rho_fz3:+.2f}（規準 {RHO_FLIP:+.2f} より小さいとき反転）")
    rho_fb3 = s2[("fb", "型3 相当")]["rho"]
    rep("(a2) (0) 凍結版本体も型3 相当で反転（複製と同じ）",
        s2[("fb", "型3 相当")]["flip"],
        f"(0) ρ {rho_fb3:+.2f}・(1) ρ {rho_fz3:+.2f}"
        f"（規準 {RHO_FLIP:+.2f} より小さいとき反転）")
    rep("(a2) 同じ条件で Δμ0.01 は正（下限を緩めると反転が消える）",
        np.isfinite(rho_rx3) and rho_rx3 > 0
        and not s2[("relax", "型3 相当")]["flip"],
        f"Δμ0.01 ρ {rho_rx3:+.2f}・凍結版 ρ {rho_fz3:+.2f}")
    rho_cv01_3 = s2[("conv01", "型3 相当")]["rho"]
    rep("(a2) (4b) 畳み込み＋Δμ0.01 は型3 相当で正",
        np.isfinite(rho_cv01_3) and rho_cv01_3 > 0
        and not s2[("conv01", "型3 相当")]["flip"],
        f"(4b) ρ {rho_cv01_3:+.2f}・(1) ρ {rho_fz3:+.2f}")
    rep("(a2) 型1 相当では凍結版も反転しない",
        np.isfinite(rho_fz1) and rho_fz1 > 0 and not s2[("frozen", "型1 相当")]["flip"],
        f"ρ {rho_fz1:+.2f}")
    rep("(a2) RI の真値は 2 通りとも順位が同じ（母数 a_ref と成分のピーク高さの比）",
        all(np.array_equal(np.argsort(np.asarray(r["truth"], float)),
                           np.argsort(np.asarray(r["ri_peak"], float)))
            for r in a2["res"].values()),
        "母数で計算した ρ と比で計算した ρ は同じ順位になる")

    # --- (f) 再実装 (1) と凍結版本体 (0) の照合（2026-09-15 に足した）。
    # 起点の作り方・解の選び方・成分のピークの求め方を凍結版と同じにしたので、(1) は
    # (0) と同じ解に行き着くはずである。節A（2 層 × 5 拍）と節A-2（2 条件 × 4 拍）の
    # 全拍で照合する。ここが落ちたら、写した複製が本体と別の当てはめになっている。
    d_dt = 0.0
    for rc in res.values():
        d_dt = max(d_dt, float(np.max(np.abs(
            np.asarray(rc["got"]["frozen"], float)
            - np.asarray(rc["got"]["fb"], float)))))
    d_ri = 0.0
    for rc in a2["res"].values():
        d_ri = max(d_ri, float(np.max(np.abs(
            np.asarray(rc["got"]["frozen"], float)
            - np.asarray(rc["got"]["fb"], float)))))
    rep("(1) は (0) と同じ値を返す（再実装の照合）",
        d_dt <= 1e-6 and d_ri <= 1e-9,
        f"ΔT の差の最大 {d_dt:.3e} ms（要 1e-06 以下）・"
        f"RI の差の最大 {d_ri:.3e}（要 1e-09 以下）")

    n_chk, n_dif = 0, 0
    for rc in list(res.values()) + list(a2["res"].values()):
        for c_fb, c_fz in zip(rc["checks"]["fb"], rc["checks"]["frozen"]):
            n_chk += 1
            if any(bool(c_fb[q]) != bool(c_fz[q])
                   for q in ("ok", "boundary", "amp_zero", "ambiguous")):
                n_dif += 1
    rep("(1) の診断は (0) の検算と一致する", n_dif == 0,
        f"{n_chk} 拍で 通過・境界・高さ・別解 の 4 つを照合し、食い違い {n_dif} 拍")

    n_bad = 0
    for rc in list(res.values()) + list(a2["res"].values()):
        for k in KIND_KEYS:
            rows = rc["checks"][k]
            n_ok = sum(1 for c in rows if c["ok"])
            if len(rows) != len(rc["truth"]) or not 0 <= n_ok <= len(rows):
                n_bad += 1
    rep("診断の表が印字され、通過数は拍数を超えない",
        n_bad == 0 and "Δμ下限" in txt_a0 and "Δμ下限" in txt_a2,
        f"節A {len(TAUS_FAST)} 層・節A-2 {len(RI_CONDS)} 条件 × 当てはめ "
        f"{len(KIND_KEYS)} 型で数を照合し、食い違い {n_bad} 件")

    # --- (c) 節B の計算部品を、下限で詰まる列を人工的に作った表で確かめる
    db = synth_b(seed=0)
    bufb = io.StringIO()
    with redirect_stdout(bufb):
        sb = section_b(db, "合成データ（自己検査）")
    txt_b = bufb.getvalue()
    rep("(c) 節B が合成の表で最後まで印字される",
        sb["state"] == 0 and "B5. 予測との照合" in txt_b,
        f"{len(db)} 行・{len(txt_b)} 文字")
    b2, bp = sb["b2"], sb["b5"]
    low3 = b2[3]["bins"][:PRED_P1_N_BINS]
    rep("(c) P1: 型3 は下から 2 区間でも凍結版 ΔT の中央値が下がらない",
        bp["P1"] and all(abs(b["med"] - FLOOR_SYN_MS) < 3.0 for b in low3),
        "・".join(f"[{b['lo']:.0f},{b['hi']:.0f}) 中央値 {b['med']:.1f} ms" for b in low3)
        + f"（仕込んだ下限 {FLOOR_SYN_MS:.0f} ms）")
    rep("(c) P2: 型3 は短い側の ρ が長い側より 0.15 以上小さい",
        bp["P2"], f"差 {_n(bp['gap3'], 3, sign=True)}")
    rep("(c) P3: 型1（下限を仕込んでいない）は差が 0.15 未満",
        bp["P3"], f"差 {_n(bp['gap1'], 3, sign=True)}")
    rep("(c) 型1 の凍結版 ΔT の最小は特徴点法に追随する（下限を仕込んでいない）",
        b2[1]["v1_min"] < FLOOR_SYN_MS - 40.0,
        f"型1 の最小 {b2[1]['v1_min']:.1f} ms・型3 の最小 {b2[3]['v1_min']:.1f} ms")
    rep("(c) 下限を仕込まない表では P1 が「いいえ」になる（検査が効いている）",
        not _p1_of(synth_b_nofloor(seed=0)),
        "型3 にも下限を仕込まない合成データで照合した")
    b4 = sb["b4"]
    r3, r1 = bp["ri3"], bp["ri1"]
    rep("(c) P4: 型3 の ρ(ri_v1, digital_ri) は中央値 0.30 未満・75 歳層 0.20 未満",
        bp["P4"],
        f"中央値 {_n(r3['med'], 3, sign=True)}・75 歳層 {_n(r3['old'], 3, sign=True)}"
        f"・年齢との順位相関 {_n(r3['trend'], 2, sign=True)}")
    rep("(c) P5: 型1 は中央値 0.60 以上で年齢層による差が 0.15 未満",
        bp["P5"],
        f"中央値 {_n(r1['med'], 3, sign=True)}・最若層 {_n(r1['young'], 3, sign=True)}"
        f"・最高齢層 {_n(r1['old'], 3, sign=True)}・差 {_n(r1['span'], 3)}")
    rep("(c) B4 の表が型ごと・年齢層ごとに並ぶ（A 段と C 段）",
        set(b4.keys()) >= {1, 3} and b4[3]["A"]["n_ages"] == len(AGES_SYN)
        and b4[1]["C"]["n_ages"] == len(AGES_SYN),
        f"型3 の層 {b4[3]['A']['n_ages']}・型1 の層 {b4[1]['A']['n_ages']}")
    rep("(c) 型3 も特徴点法に追随する表では P4 が「いいえ」になる（検査が効いている）",
        not _p4_of(synth_b_ri_flat(seed=0)),
        "型3 の傾きを型1 と同じにした合成データで照合した")

    # --- (d) 列が無い CSV
    d_miss = db.drop(columns=[COL_V1])
    bufm = io.StringIO()
    with redirect_stdout(bufm):
        out_m = report("B", d_miss, "合成データ（列を抜いた）")
    txt_m = bufm.getvalue()
    rep("(d) 列が無い CSV で落ちずに「列が無い」と印字し、終了コード 2 になる",
        out_m["code"] == 2 and "列が無い" in txt_m and COL_V1 in txt_m,
        f"終了コード {out_m['code']}")

    # --- (e) 同じ乱数種なら出力が同一
    def render(seed):
        b = io.StringIO()
        with redirect_stdout(b):
            section_a(TAUS_FAST, DTS_FAST, seed=seed)
        return b.getvalue()

    t_same, t_other = render(SEED_A), render(SEED_A + 1)
    rep("(e) 同じ乱数種なら出力が同一", t_same == txt_a0, f"{len(t_same)} 文字")
    rep("(e) 乱数種を変えれば値は変わる（比較が効いている）", t_other != txt_a0)

    # --- (g) 節C を模擬 PWDB（26番の自己検証と同じもの）で通す。**ネットワークは要らない。**
    # 実 PWDB は無いので、26番の `_selftest_root` が作る模擬の配布物を使う。ここで検査するのは
    # 処理系（拍の作り方・記録・再開・表が最後まで出ること）であって、当てはめの優劣ではない。
    import tempfile
    import time as _time
    t_c = _time.time()
    with tempfile.TemporaryDirectory() as td:
        refit_p = Path(td) / "50_refit_selftest.csv"
        vars_c = ("fb", "relax")
        bufm = io.StringIO()
        with redirect_stdout(bufm):        # 模擬の作成と読み込みの print は表に出さない
            m26 = _load("26_pwdb_compare.py", "m26")
            root, _kinds = m26._selftest_root(Path(td), n=48)
            hae_, _cfg_, ppg_, _x_ = M.load_pwdb(root)
        rep("(g) --limit の取り方が 26番の `_stride` と同じ",
            list(c_stride(ppg_, 24).iloc[:, 0]) == list(m26._stride(ppg_, 24).iloc[:, 0])
            and len(c_stride(ppg_, len(ppg_) + 5)) == len(ppg_),
            f"{len(ppg_)} 名から 24 名・端から端まで")

        rep("(g) --limit のときの記録は別名になる（全例の記録を上書きしない。26番と同じ規約）",
            _refit_path(None, 0).name == REFIT_NAME
            and _refit_path(None, 300).name == "50_refit_limit300.csv"
            and _refit_path(refit_p, 300) == refit_p,
            f"{_refit_path(None, 0).name} / {_refit_path(None, 300).name}")

        bufc = io.StringIO()
        with redirect_stdout(bufc):
            c1 = section_c(root, limit=24, jobs=1, variants=vars_c, refit_csv=refit_p,
                           resume=True, d26=None)
        txt_c1 = bufc.getvalue()
        need_cols = ["subj_no", "fs", "n_samp", "klass_own", "sys_own_ms", "dia_own_ms"]
        for k in vars_c:
            need_cols += ([f"dt_{k}_ms", f"ri_{k}", f"ok_{k}", f"cost_{k}"]
                          + [f"{tag}_{k}" for tag, _q in CHK_COLS])
        got = pd.read_csv(refit_p)
        rep("(g) 節C が記録（CSV）を書き、要る列が揃う（型 2 つぶん）",
            refit_p.exists() and all(c in got.columns for c in need_cols)
            and len(got) == 24 and got["subj_no"].is_unique,
            f"{len(got)} 名・{len(got.columns)} 列・"
            f"当てはめた {c1['info']['n_fit']} 名")

        txt_first = refit_p.read_text(encoding="utf-8")
        bufc2 = io.StringIO()
        with redirect_stdout(bufc2):
            c2 = section_c(root, limit=24, jobs=1, variants=vars_c, refit_csv=refit_p,
                           resume=True, d26=None)
        rep("(g) 再開すると 1 名も当てはめ直さず、記録も同じ内容になる",
            c2["info"]["n_fit"] == 0 and c2["info"]["n_cache"] == 24
            and refit_p.read_text(encoding="utf-8") == txt_first,
            f"当てはめ直した {c2['info']['n_fit']} 名・再利用 {c2['info']['n_cache']} 名")

        # 3 名だけ、記録の値が `fit_beat` ＋ `si_ri_from_fit` の直接計算と一致するか
        from src.indices import si_ri_from_fit
        hr_by_ = dict(zip(hae_["subj_no"].astype(int), hae_["HR"].astype(float)))
        d_dt, d_ri, n_ok_same, n_chk = 0.0, 0.0, 0, 0
        idx_by = dict((int(ppg_.iloc[i, 0]), i) for i in range(len(ppg_)))
        for subj in [int(v) for v in got["subj_no"].head(3)]:
            row = got[got["subj_no"] == subj]
            i = idx_by[subj]
            y_, fs_ = M.beat_of(ppg_.iloc[i].to_numpy(float), hr_by_.get(subj, np.nan))
            if y_ is None:
                continue
            fit = pda.fit_beat(np.arange(y_.size) / fs_, y_)
            ix = si_ri_from_fit(fit)
            n_chk += 1
            d_dt = max(d_dt, abs(float(row["dt_fb_ms"].iloc[0]) - 1000.0 * ix["dt_s"]))
            d_ri = max(d_ri, abs(float(row["ri_fb"].iloc[0]) - ix["ri"]))
            n_ok_same += int(int(row["ok_fb"].iloc[0]) == int(bool(fit["ok"])))
        rep("(g) 記録の dt_fb_ms・ri_fb・ok_fb が `fit_beat` ＋ `si_ri_from_fit` と一致する",
            n_chk == 3 and d_dt <= 1e-9 and d_ri <= 1e-9 and n_ok_same == 3,
            f"{n_chk} 名で照合・ΔT の差 {d_dt:.3e} ms・RI の差 {d_ri:.3e}・"
            f"採否の一致 {n_ok_same}/{n_chk}")

        kl_ = pd.to_numeric(got["klass_own"], errors="coerce").to_numpy(float)
        rep("(g) 型 klass_own は 1・3・4・5 か欠測のいずれか（26番と同じ付け方）",
            bool(np.all([(not np.isfinite(v)) or int(v) in (1, 3, 4, 5) for v in kl_])),
            f"値 {sorted(set(int(v) for v in kl_[np.isfinite(kl_)]))}")

        rep("(g) C1〜C5 の表が最後まで印字され、予測は照合できないか はい／いいえ になる",
            all(h in txt_c1 for h in ("C1. 採否と縮退", "C2. ΔT ×", "C3. RI ×",
                                      "C4. 一致", "C5. 予測との照合"))
            and "まとめ: 予測 5 条のうち" in txt_c1
            and c1["c5"]["n_eval"] == 0 and c1["c5"]["hit"] == 0,
            f"{len(txt_c1)} 文字・照合できた予測 {c1['c5']['n_eval']} 条"
            "（模擬は 1 層 4 名なのでどの層も評価できない）")
        rep("(g) 26番の列が無いので C0 と P10 は「照合できない」になる",
            c1["c0"]["state"] == "照合できない" and not c1["c5"]["P10"]["ev"]
            and "P10 検算  (0) と 26番の列: 照合できない" in txt_c1)

    # --- (g) --pwdb が無いまま節C を頼まれたら、落ちずに終了コード 2
    bufp = io.StringIO()
    with redirect_stdout(bufp):
        out_p = report("C", None, "")
    txt_p = bufp.getvalue()
    rep("(g) --pwdb が無いまま節C を頼まれたら案内を出して終了コード 2 になる",
        out_p["code"] == 2 and "節C は PWDB の配布物が要る" in txt_p,
        f"終了コード {out_p['code']}")
    print(f"    節C の自己検査に {_time.time() - t_c:.0f} 秒")

    # --- 既定の CSV があれば節B を走らせる（動くことの確認だけ）
    print("\n  --- 既定の CSV で節B を走らせる（動くことの確認だけ）---")
    if DEFAULT_CSV.exists():
        d_real = pd.read_csv(DEFAULT_CSV)
        bufr = io.StringIO()
        with redirect_stdout(bufr):
            out_r = report("B", d_real, str(DEFAULT_CSV))
        txt_r = bufr.getvalue()
        rep("既定の CSV で節B が例外なく最後まで印字される",
            out_r["code"] == 0 and "B5. 予測との照合" in txt_r,
            f"{len(d_real)} 行・終了コード {out_r['code']}・{len(txt_r)} 文字")
        if len(d_real) < 100:
            rows = out_r["B"]["b3"].get((3, "A"), {}).get("all", {})
            rep("抜粋では 8 名以上の年齢層が無く、ρ が計算できないことが表に出る",
                rows.get("n_ages", 0) == 0,
                f"評価できた層 {rows.get('n_ages', 0)}")
            print(f"  ★ この機械の {DEFAULT_CSV.name} は {len(d_real)} 行の抜粋である。")
            print("  ★ **ここから出る数値は読んではいけない。**確認的解析の機械の"
                  " 4,374 行で走らせること。")
    else:
        rep("既定の CSV が無い機械でも自己検査は通る", True, f"{DEFAULT_CSV} が無い")

    print("\n" + ("自己検証: 通過" if n_fail == 0 else f"自己検証: 失敗 {n_fail} 件"))
    return 0 if n_fail == 0 else 1


def synth_b_nofloor(seed: int = 0) -> pd.DataFrame:
    """(c) の対照。型3 にも下限を仕込まない（P1 が「いいえ」になるはず）。"""
    d = synth_b(seed=seed)
    rng = np.random.default_rng(seed + 1)
    d[COL_V1] = _colv(d, COL_LM) + rng.normal(0.0, JIT_SYN_MS, len(d))
    return d


def _p1_of(d: pd.DataFrame) -> bool:
    """P1 だけを静かに計算する（自己検査の対照用）。"""
    b = floor_bins(stage_a(subset(d, 3)))
    low = b["bins"][:PRED_P1_N_BINS]
    return bool(low) and len(low) == PRED_P1_N_BINS and all(
        np.isfinite(x["med"]) and x["med"] >= PRED_P1_FLOOR_MS for x in low)


def synth_b_ri_flat(seed: int = 0) -> pd.DataFrame:
    """(c) の対照。型3 の RI も型1 と同じ傾きにする（P4 が「いいえ」になるはず）。"""
    d = synth_b(seed=seed)
    rng = np.random.default_rng(seed + 2)
    d[COL_RI_V1] = (0.30 + RI_SLOPE_FLAT * (_colv(d, COL_RI_LM) - 0.45)
                    + rng.normal(0.0, RI_JIT_SYN, len(d)))
    return d


def _p4_of(d: pd.DataFrame) -> bool:
    """P4 だけを静かに計算する（自己検査の対照用）。"""
    s = strat(rho_rows(stage_a(subset(d, 3)), xcol=COL_RI_V1, ycol=COL_RI_LM))
    rows = [(a, r) for a, r, _n in s["rows"] if np.isfinite(r)]
    if not rows:
        return False
    old = [r for a, r in rows if abs(a - AGE_OLD) < 1e-9]
    old_v = old[0] if old else sorted(rows)[-1][1]
    return bool(np.isfinite(s["med"]) and s["med"] < PRED_P4_MED
                and old_v < PRED_P4_OLD)


# ---------------------------------------------------------------- 入口
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=str, default=None,
                    help="26番の出力（既定 data/pwdb/pwdb_compare.csv があれば使う）")
    ap.add_argument("--section", type=str, default="AB",
                    choices=("A", "B", "C", "AB", "AC", "BC", "ABC"),
                    help="走らせる節（既定 AB。CSV が無ければ A だけ。C は --pwdb が要る）")
    ap.add_argument("--fast", action="store_true",
                    help="節A・節A-2 の掃引を減らす（自己検査と同じ。本番の表ではない）")
    ap.add_argument("--seed", type=int, default=SEED_A,
                    help="節A・節A-2 の雑音の乱数種")
    ap.add_argument("--pwdb", type=str, default=None,
                    help="PWDB の配布物を置いたフォルダ（節C に要る）")
    ap.add_argument("--limit", type=int, default=0,
                    help="節C で全体から等間隔に N 名だけ当てはめる（先頭 N 名ではない。0=全員）")
    ap.add_argument("--jobs", type=int, default=1, help="節C の並列数（26番と同じ）")
    ap.add_argument("--variants", type=str, default=",".join(VARIANTS_DEFAULT),
                    help="節C で当てる型（KINDS の鍵をコンマで並べる。既定 "
                         + ",".join(VARIANTS_DEFAULT) + "）")
    ap.add_argument("--refit-csv", type=str, default=None,
                    help="節C の記録の場所（既定 data/pwdb/50_refit.csv。--limit なら"
                         " 50_refit_limitN.csv）")
    ap.add_argument("--no-resume", action="store_true",
                    help="節C で記録を使わずに全員当てはめ直す（既定は再開する）")
    ap.add_argument("--selftest", action="store_true",
                    help="合成だけで計算の筋道を検算する（CSV もネットワークも要らない）")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())
    if args.jobs < 1:
        ap.error("--jobs は 1 以上")
    if args.limit < 0:
        ap.error("--limit は 0 以上（0 = 全員）")
    variants = tuple(v.strip() for v in args.variants.split(",") if v.strip())
    bad = [v for v in variants if v not in KIND_KEYS]
    if bad:
        ap.error(f"--variants に知らない型がある: {bad}（使えるのは {list(KIND_KEYS)}）")

    want_b = "B" in args.section
    want_c = "C" in args.section
    if want_c and not args.pwdb:
        print_no_pwdb()
        sys.exit(2)

    d, src = None, ""
    if want_b or want_c:
        p = Path(args.csv) if args.csv else DEFAULT_CSV
        if not p.exists() and not p.is_absolute():
            p = ROOT / str(args.csv)
        if p.exists():
            d, src = pd.read_csv(p), str(p)
        elif args.csv:
            if want_b:
                print(f"\n{args.csv} が無い。26番（26_pwdb_compare.py）の出力が要る。")
                print("確認的解析を回した機械には data/pwdb/pwdb_compare.csv がある"
                      "（4,374 行）。")
                sys.exit(2)
            print(f"\n{args.csv} が無い。節C の C0 の照合と参考行は飛ばす。")
        elif want_b and want_c:
            print(f"\n{DEFAULT_CSV} が無いので節B は走らせない"
                  "（節B は --csv で 26番の出力を渡す）。")
            args.section = args.section.replace("B", "")
        elif want_b:
            print(f"\n{DEFAULT_CSV} が無いので節A だけを走らせる"
                  "（節B は --csv で 26番の出力を渡す）。")
            args.section = args.section.replace("B", "") or "A"

    taus = TAUS_FAST if args.fast else TAUS_FULL
    dts = DTS_FAST if args.fast else DTS_FULL
    ris = RIS_FAST if args.fast else RIS_FULL
    if args.fast:
        print("\n  ★ --fast: 節A・節A-2 の掃引を減らしている。**本番の表ではない。**")
    out = report(args.section, d, src, taus=taus, dts=dts, ris=ris, seed=args.seed,
                 pwdb=args.pwdb, limit=args.limit, jobs=args.jobs, variants=variants,
                 refit_csv=args.refit_csv, resume=not args.no_resume)
    sys.exit(out["code"])


if __name__ == "__main__":
    main()

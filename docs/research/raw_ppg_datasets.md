# 生波形（未加工の PPG）が入手できる公開データベース ― 調査（2026-09-07）

## なぜ探しているか

VitalDB の `SNUADC/PLETH` はモニタの出力である。自動利得調整（AGC）と帯域制限を受けており、
直流成分は復元できない（0〜100 の表示スケール）。我々の機構実験では、拍内のゲイン変動
（時定数 0.25 秒）を入れると **RI が +61% 膨らみ、ΔT は −9 ms しか動かない**。
つまり RI はモニタ出力では歪んでいる可能性が高い。

さらに 32番で、麻酔中のモニタ波形の平均拍の **34% が型4**（切痕も変曲点も無く、拡張期ピークが
定義できない）だった。これが信号鎖（帯域制限・AGC）によるのか、麻酔下の血管拡張（生理）に
よるのかは、モニタ波形だけでは分けられない。

**生波形が手に入れば、前者のいくつかは今日確かめられる。**

---

## 見つかったもの

**注意: いずれも検索で見つけた記述に基づく。雲からは PhysioNet が遮断されているので、
中身（標本化周波数・直流成分の有無・実際のフィルタ）は Mac で必ず自分で確かめること。**

| データベース | 内容 | 生波形として使えるか |
|---|---|---|
| **Pulse Transit Time PPG Dataset**（PhysioNet） | 健常 22 名。2 部位 × 3 波長の PPG、ECG、加速度・ジャイロ、接触圧、温度、血圧、SpO2。安静と 3 種の身体活動 | **最有力。**「タイミング情報を保つため未フィルタである（大半の公開 PPG はフィルタ済み）」と明記されている。高い標本化周波数 |
| **WF-PPG**（Sci Data 2025） | 手首と指の 2 チャネル。接触圧が PPG の形に与える影響を調べるためのデータ | **交流成分と直流成分の両方を含む。**直流が残っているのは VitalDB に無い性質 |
| **同期 生 ＋ 前処理済み 指接触 ECG・二波長 PPG**（Data 2026・MDPI） | 健常 148 名。660 nm と 940 nm を同時記録。安静と運動後の回復期 | **生と前処理済みの両方が入っている。**同じ拍で前処理の影響を直接比べられる |
| **VORTAL**（Charlton・KCL figshare） | 18〜39 歳。ECG・PPG・インピーダンスニューモグラフィ・口鼻圧。安静仰臥位 約 10 分 ＋ 運動後回復期 | 研究用機器での取得。**PWDB と同じ著者**なので方法論の連続性がある |
| BUT PPG（PhysioNet） | スマートフォンで記録した 10 秒 × 3,888 件。ECG・加速度つき | 品質評価用。分解には短い |
| MAUS | 指尖 PPG と手首 PPG を同時記録 | 部位の比較用 |
| 中国の血圧モニタ用データ（Sci Data 2018） | 219 名・657 区間。左示指の指尖 PPG。20〜89 歳 | 年齢幅が広い。前処理の程度は要確認 |

---

## 生波形で**今日**確かめられること（倫理手続き不要）

1. **帯域を広げると特徴点の同定率は上がるか。**モニタ波形で 34% あった型4 が、
   同じ人の生波形でどれだけ減るか。ただし対象は健常成人・安静なので、**麻酔中の値には外挿できない**。
2. **早期振幅比 Am_b/Am_p1 の安定性は上がるか。**この指標は 2 次微分を使うので、原理的に
   帯域制限と雑音に弱い。実機のモニタ波形でのウィンドウ間の再現性 0.36 が、生波形でどこまで上がるか。
   同定率は既に 0.95 なので、伸びしろは再現性の側にある。
3. **AGC の影響を実データで測る。**生波形に人工的に拍内ゲイン変動をかけ、RI がどれだけ膨らむかを見る。
   我々の +61% は合成波での機構実験なので、実データ版の裏づけになる。
4. **直流成分があると RI の値がどう変わるか。**VitalDB では原理的にできない。

## 生波形でも確かめられないこと

- **麻酔中の型4 の由来。**上のデータベースはすべて健常成人の安静または運動後で、
  麻酔中の患者は含まれていない。血管拡張による切痕の消失は、これらのデータには現れない。
  **これは研究2（自施設 10 例）でしか分けられない。**
- **分解法が真値と相関するか。**PWDB は雑音ゼロ・帯域無制限で、生波形よりさらに条件が良い。
  そこで相関しなかった以上、生波形で回復する筋はない（`why_pda_failed_in_silico.md`）。

---

## 次にやること（優先度は低い・研究2 の設計材料として）

1. Mac で PhysioNet の Pulse Transit Time PPG Dataset の説明を読み、標本化周波数・
   フィルタの有無・直流成分の扱いを確かめる（雲からは遮断されている）。
2. 使えるなら、上の 1〜4 を 1 本のスクリプトで測る。**判定に使うのではなく、
   研究2 の設計（何を測れば信号鎖と生理を分けられるか）を決めるための探索**である。
3. 研究2 の計画書に「同じ患者の生波形とモニタ波形で型の分布を比べる」を残す。
   公開データでは代用できない項目であることを、この調査の結論として明記する。

---

## 出典

- [Pulse Transit Time PPG Dataset v1.1.0（PhysioNet）](https://physionet.org/content/pulse-transit-time-ppg/1.1.0/)
- [WF-PPG: A Wrist-finger Dual-Channel Dataset（Sci Data 2025）](https://www.nature.com/articles/s41597-025-04453-7)
- [A Dataset of Synchronized Raw and Preprocessed Finger-Contact ECG and Dual-Wavelength PPG Signals（Data 2026）](https://doi.org/10.3390/data11070155)
- [VORTAL（Charlton, KCL figshare）](https://kcl.figshare.com/articles/dataset/Data_used_in_paper_An_Assessment_of_Algorithms_to_Estimate_Respiratory_Rate_from_the_Electrocardiogram_and_Photoplethysmogram_/16473705)
- [A new, short-recorded photoplethysmogram dataset for blood pressure monitoring in China（Sci Data 2018）](https://www.nature.com/articles/sdata201820)
- [PhysioNet の PPG 関連データベース一覧](https://physionet.org/content/?topic=ppg)

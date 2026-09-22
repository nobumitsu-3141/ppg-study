# 論文2 考察の位置づけ（案・2026-09-21）― 陰性 → 原因 → 修正 → 次の検証

**扱い**: v2 本文（`v2/01_draft_en_v2.md`・`05_draft_ja_v2.md`）には反映していない案である。採るなら差し込む位置を各案に示した。
数値の出典は表6・表6b・表7（`02_tables.md`）と lab_log 追記152・154〜156。**表5 以降は探索・事後で、判定には用いない。**
段の定義: A 段 ＝ その手法が自分で採用した被験者だけ、C 段 ＝ 採否を無視して全員。B 段（比べる手法すべてが採用した共通例）と
雑音を足した実行の結果はまだ無い（Mac 1 で実行待ち）。**それが出るまで案 A の数値は仮置きとする。**

`gate0_rules_v2.md` の「書かないこと」を守る。とくに **「in silico で回復したから実機でも使える」とは書かない。**
「反射波」は慣例上の呼称としてのみ、注記つきで使う。

---

## 案 A　§4.3 機構の末尾に足す ― 下降を外すと ΔT の関連は回復する（探索）

和文:

> 上の機構 1・4 を直接に確かめるため、同じ 4,374 名の同じ拍に、拡張期の下降の扱いだけを変えた 14 通りの当てはめを
> 当て直した（表6）。下降を説明する部品を模型に足す 5 通り（貯留槽の項 2 通り・自由な指数減衰・出力側の畳み込み・逆畳み込み）は
> いずれも失敗した。とくに出力側の畳み込みは、通過率 0.728 と波形にはよく合いながら ΔT × 大動脈脈波伝播速度が 0.042（A 段）で、
> 凍結版（0.220）より低い。下降を説明する自由度を与えると、第2成分をどこに置いても残差が小さくなり、位置が残差から決まらなくなる。
> 一方、下降を当てはめの対象から外す（拍長の 0.55〜0.75 倍、または絶対時間 0.45 s で打ち切る）か、残差を 1 次微分の領域で取る 6 通りは、
> 型3（変曲点のみ・3,378 名）の ΔT × 大動脈脈波伝播速度を C 段で 0.545〜0.724（6/6）に上げ、同梱の特徴点法（0.430）を上回った。
> 打ち切る位置を絶対時間にしても同じ向き・同じ水準なので、この効果は切る位置が心拍数の関数であることの産物ではない。
> ただし RI × 末梢血管抵抗は、打ち切った版では A 段でしか規準を満たさず（C 段 0.107〜0.182）、1 次微分の版で C 段 0.416 に
> とどまり、特徴点法（0.550）に届かない。第2成分が同梱の特徴点の位置に戻ること（差 +98.5 → +25.8 ms）は関連の条件ではなく、
> 1 次微分の版は +88.8 ms のまま 0.687 に達した。これらは 14 通りから事後に選んだ値であり、楽観側にある。
> 当てはめの改良を主解析に用いるには新たな事前登録が要る。

英文（差し込み用）:

> To test mechanisms 1 and 4 directly, the same beats of the same 4,374 subjects were refitted with fourteen variants that
> differ only in how the diastolic decay is handled (table 6). The five variants that add a term to explain the decay (two reservoir
> terms, a free exponential, a convolution applied to the output, and deconvolution followed by the frozen fit) all failed. The
> output-side convolution is instructive: it fitted the waveform well (acceptance 0.728) yet ΔT versus aortic PWV fell to 0.042
> (tier A), below the frozen version (0.220). Given a degree of freedom that explains the decay, the second component can be placed
> almost anywhere at little cost in residual, so its position is no longer determined by the residual. The six variants that remove
> the decay from the objective — truncating the fit at 0.55–0.75 of the beat or at 0.45 s, or fitting in the first-derivative
> domain — raised ΔT versus aortic PWV in type-3 beats (inflection only, n = 3,378) to 0.545–0.724 on tier C (6/6 strata), above the
> supplied fiducial-point value (0.430). Truncating at an absolute time gave the same direction and level, so the effect is not an
> artefact of the cut point being a function of heart rate. RI versus peripheral resistance, however, met the criterion only on
> tier A for the truncated variants (tier C 0.107–0.182) and reached 0.416 on tier C for the derivative-domain variant, still below
> fiducial-point analysis (0.550). Returning the second component to the fiducial position (+98.5 → +25.8 ms) is not a condition
> for the association: the derivative-domain variant stayed at +88.8 ms and reached 0.687. These values were selected post hoc
> from fourteen variants and are optimistic; using a modified fit as a primary analysis would require new preregistration.

---

## 案 B　§4.2 文献との関係に足す ― 「同等」の意味と、特徴点法の側の妥当性

和文:

> 分解法が特徴点法や 2 次微分由来の指標と「同等」とされてきた根拠は、(i) 波形への当てはまりと雑音への頑健さ、
> (ii) 特徴点法で出した同じ量との一致、(iii) 年齢との相関・年齢の分類、の 3 つに限られる。硬さや血管抵抗の独立した参照に対して
> 分解法が特徴点法を上回った報告は見当たらず、真値のある比較は本研究が初めてである。一方、特徴点法の側には in silico の真値と
> in vivo の参照の両方に対する裏づけがある。健常〜混合集団でスティフネス指標は頸大腿脈波伝播速度と r 0.58〜0.66
> [Millasseau 2002; Hellqvist 2024]、本研究の 0.710 と同じ水準にある。ただし治療中の高血圧では 2 次微分由来の指標と
> 頸大腿脈波伝播速度の相関は 0.24 以下と報告されており [Hashimoto 2002]、中枢と末梢は別の情報を持つ。
> 本研究が示したのは、同じ波形から同じ名前の指標を出す 2 つの方法のうち、この集団でこの問いに答えたのは特徴点法だけである、
> ということであって、文献の (i)〜(iii) を否定するものではない。

英文:

> The equivalence claimed for decomposition rests on three kinds of evidence: goodness of fit and robustness to noise, agreement
> with the same quantities read from fiducial points, and correlation with age. We found no report in which a decomposition-derived
> index exceeded a fiducial-point index against an independent reference of stiffness or resistance; the present comparison against
> known truth appears to be the first. Fiducial-point indices, by contrast, are supported both in silico and in vivo: in healthy to
> mixed populations the stiffness index correlates with carotid–femoral PWV at r 0.58–0.66 [Millasseau 2002; Hellqvist 2024],
> the level found here (0.710), although in treated hypertension the correlation of second-derivative indices with carotid–femoral
> PWV is 0.24 or less [Hashimoto 2002], central and peripheral measures carrying different information. Our result is that, of two
> methods that produce indices of the same name from the same waveform, only fiducial-point analysis answered this question in this
> population; it does not contradict the three kinds of evidence above.

---

## 案 C　§4.3 機構 3 を自前のデータで補強する ― 両手法が捉える拡張期の波は線形分離の後進波ではない

和文:

> PWDB は指尖の圧と流速を同じ拍で与えるので、線形の波分離で後進波を作り、その到達時間 ΔT_true と両手法の ΔT を比べた（表7a）。
> 型3 で分解法の ΔT は後進波のピークより +219 ms、特徴点法は +114 ms 遅く、順位相関はいずれもほぼ 0 であった。
> さらに ΔT_true 自体は大動脈脈波伝播速度と正の向きに関連し（型3 |ρ| 0.371、向きの合う層 0/6）、硬いほど遅く到達する。
> すなわち指尖で線形分離した後進波の到達時間は硬さの指標にならず、両手法が「反射波」と呼んできた拡張期の波は
> それとは別の現象で、そちらが硬さと関連する。この結果は機構 3 [Epstein 2014; Hellqvist 2024] を同じ集団で裏づける。
> 本稿では以後「拡張期の波」と呼び、「反射波」は慣例上の呼称としてのみ用いる。

英文:

> Because the database supplies pressure and flow velocity at the digital site for the same beat, the backward wave was obtained by
> linear wave separation and its arrival time compared with ΔT from both methods (table 7a). In type-3 beats, decomposition ΔT
> lagged the backward-wave peak by +219 ms and fiducial-point ΔT by +114 ms, with rank correlations near zero. The arrival time of
> the separated backward wave was itself positively related to aortic PWV (type 3 |ρ| 0.371, predicted sign in 0/6 strata): it
> arrived later, not earlier, in stiffer subjects. The backward wave separated at the finger is therefore not an index of stiffness,
> and the diastolic wave that both methods have called the reflected wave is a different phenomenon, which is the one that tracks
> stiffness. This supports mechanism 3 [Epstein 2014; Hellqvist 2024] in the same population. We refer to it hereafter as the
> diastolic wave and use "reflected wave" only as the conventional name.

---

## 案 D　§4.5 限界に足す ― PPG という量への変換は弱点の一部であって全部ではない

和文:

> 同じ凍結版を指尖の圧波形に当てると、ΔT × 大動脈脈波伝播速度は A 段 0.223 → 0.486、C 段 0.205 → 0.313 と規準を満たしたが、
> RI × 末梢血管抵抗は 0.207 → 0.225 と変わらなかった（表7b）。指尖 PPG が末梢の Windkessel の容積であり圧より長い拡張期の下降を
> 持つことは、分解法が劣った理由の一部である。しかし圧波形でも特徴点法（0.710）には届かないので、本研究の陰性は
> 「PPG という量に 2 成分の和の模型を当てること」に固有であり、圧に当てても解消しない。

英文:

> Applying the frozen fit to the digital pressure waveform instead of the PPG raised ΔT versus aortic PWV from 0.223 to 0.486
> (tier A) and from 0.205 to 0.313 (tier C), both meeting the criterion, whereas RI versus peripheral resistance did not change
> (0.207 to 0.225; table 7b). That the digital PPG is the volume of a peripheral Windkessel, with a longer diastolic decay than the
> pressure, is therefore part of the reason decomposition lost; but even on pressure the fit did not reach fiducial-point analysis
> (0.710), so the negative is specific to fitting a two-component sum to the PPG and is not removed by fitting pressure instead.

---

## 案 E　§4.6 含意を書き換える ― 次に何を検証するか

和文:

> 本研究の帰結は「分解法は使えない」ではなく、関連しなかった原因が特定でき、in silico ではそれを外す改良で ΔT の関連が回復した、
> ということである。次に要るのは、(1) 改良した当てはめがモニタ波形で同定できるか（同定率と再現性。我々の別の検討で事前登録の上で
> 確かめる）、(2) 同定できるなら、独立した参照（頸大腿脈波伝播速度、または熱希釈による全身血管抵抗）に対して前向きに関連するか、
> の 2 段であり、いずれも新しい事前登録を要する。in silico で回復したことは、実機で使えることを意味しない。
> 切痕が無い波形では、拡張期の特徴を要しない早期振幅比が代替となり、この集団では両者を上回った（0.836）。

英文:

> The implication is not that decomposition is unusable but that the cause of its failure can be identified and, in silico,
> removed: excluding the diastolic decay from the objective restored the association of ΔT. What is needed next is, first, to test
> whether the modified fit is identifiable on recorded monitor waveforms (identification rate and repeatability, which we are
> testing under preregistration in separate work), and second, if it is, to test prospectively whether it tracks an independent
> reference — carotid–femoral PWV, or systemic vascular resistance by thermodilution. Both require new preregistration; recovery
> in silico does not imply usability in vivo. Where the dicrotic notch is unavailable, the early amplitude ratio, which requires no
> diastolic feature, is an alternative that outperformed both families in this population (0.836).

---

## 採るときの手順

1. Mac 1 の B 段・雑音の結果で案 A の数値と文（とくに RI の A 段だけの成立が選択によるものかどうか）を確定する。
2. 表6・表6b・表7 を採るなら v2 の図表点数（現在 図3点・表4点）を改め、`00_outline.md` の構成表も直す。
3. 用語検査（`python3 analysis/scripts/check_terminology.py`）を通してから本文に写す。
4. 文献 [Millasseau 2002; Hashimoto 2002] は書誌を照合してから参考文献に足す（Hellqvist 2024・Epstein 2014・Goswami 2010 は照合済み）。

---

## B 段・雑音の結果を受けた修正（2026-09-22。表6c・lab_log 追記158）

案 A の数値は確定した。修正するのは次の 3 点。

1. **RI の文を弱める。**「RI × 末梢血管抵抗は、打ち切った版では A 段でしか規準を満たさず」の後に足す:
   > 同じ被験者の上で比べる B 段でも 0.381 にとどまり、拍の振幅の 1%・2% の白色雑音を足すと 0.266・0.168 に落ちる。
   > 1 次微分の版の RI（C 段 0.416）も雑音で 0.196・0.173 に落ちる。分解由来の RI は、どの版も特徴点法（0.550）に届かず、雑音に残らない。
   （英文）The truncated variants met the RI criterion only on tier A; on tier B (the same subjects for all methods) the value was 0.381,
   and white noise of 1% and 2% of the pulse amplitude reduced it to 0.266 and 0.168. The derivative-domain RI (tier C 0.416) fell to
   0.196 and 0.173 with the same noise. No decomposition-derived RI reached fiducial-point analysis (0.550) or survived noise.
2. **ΔT の候補を打ち切りに絞る。**「1 次微分の版は +88.8 ms のまま 0.687 に達した」の後に足す:
   > ただし 1 次微分の版は雑音に弱く、1%・2% の雑音で 0.337・0.347 に落ち、通過率は 0.290 まで下がる。打ち切った版は 0.486・0.454 を保つ。
   > 打ち切った版の採否は硬さに偏らない（採否 × 大動脈脈波伝播速度の層内 ρ +0.03）が、1 次微分の版は硬い被験者ほど不採用になる（−0.54）。
   （英文）The derivative-domain variant, however, is fragile: with 1% and 2% noise its tier-C value fell to 0.337 and 0.347 and its
   acceptance to 0.290, whereas the truncated variant kept 0.486 and 0.454. Acceptance of the truncated variant was not related to
   stiffness (within-stratum ρ +0.03), while the derivative-domain variant rejected stiffer subjects (−0.54).
3. **第1成分の位置の但し書きを足す**（§4.3 機構 3 か限界に）:
   > どの版でも第1成分のピークは線形分離の前進波のピークより 34〜50 ms 遅く、PPG の収縮期ピークに座る。打ち切った版と 1 次微分の版では
   > 第1成分の位置が硬さとともに動き（層内 ρ −0.49・−0.73）、ΔT の関連は第2成分だけでなく第1成分の移動を含む。
   （英文）In every variant the first component peaked 34–50 ms after the peak of the linearly separated forward wave, at the systolic
   peak of the PPG. In the truncated and derivative-domain variants its position moved with stiffness (within-stratum ρ −0.49 and −0.73),
   so the association of ΔT involves the first component as well as the second.

**残る不備**: 雑音の列で比べている特徴点法は雑音を足していない同梱の値である。同じ条件の比較には、雑音を足した拍に自前の特徴点法を当てた行が要る（W6b）。

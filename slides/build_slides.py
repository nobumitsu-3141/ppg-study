# -*- coding: utf-8 -*-
"""PPG 波形の SI・RI を麻酔中の循環動態モニターにする ― 講演スライド生成.

出力: PPG_SI_RI_reflected_wave_slides.pptx（川副式書式・16:9）

内容の出典はすべて本リポジトリの既存レビュー（`SpO2_PPG_waveform_analysis_flow.md`、
`perioperative_stiffness_outcomes.md`、`SDPPG_prognostic_evidence_and_diastolic_gap.md`、
`PWTT_esCCO_structure_and_limits.md`、`PPG_code_development_context.md`）と、
そこに収載された一次文献（PMID 検証済み）に限る。第 5 章の推定手法は提案であり未検証。
波形図はすべて模式図（本文で提示するガウス和モデルから生成したもの）。
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.dml import MSO_LINE_DASH_STYLE as DASH

from deck_kawazoe import (Deck, panel, textbox, line, curve, text_w_in, WARNINGS,
                          GOLD, TEAL, BLUE, VERM, RED, INK, SUB, WAVE)

DASHED = DASH.DASH
FAINT = "EFEFEF"
BLUE_BG = "E4F0F8"
VERM_BG = "FBEAE0"
TEAL_BG = "E0F3F3"
RED_BG = "FBE7E7"
GOLD_BG = "F7EFD9"

# ---------------------------------------------------------------- 模式波形（ガウス和）
ELASTIC = [(1.00, 0.20, 0.070), (0.46, 0.42, 0.090), (0.20, 0.63, 0.150)]
STIFF = [(1.00, 0.21, 0.082), (0.60, 0.31, 0.100), (0.22, 0.56, 0.175)]


def gsum(t, comps):
    return sum(a * math.exp(-((t - m) ** 2) / (2 * s * s)) for a, m, s in comps)


def gnorm(comps):
    return max(gsum(i / 400.0, comps) for i in range(401))


def wave(slide, comps, x, y, w, h, color=WAVE, pt=2.6, dash=None, norm=None, n=170,
         t0=0.0, t1=1.0):
    nm = norm or gnorm(comps)
    pts = []
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        pts.append((x + (t - t0) / (t1 - t0) * w, y + h - gsum(t, comps) / nm * h))
    return curve(slide, pts, color, pt, dash)


def axis(slide, x, y, w, h, color="9A9A9A"):
    line(slide, x, y + h, x + w, y + h, color, 1.25)


def at(comps, t, x, y, w, h, norm=None):
    """時刻 t（0-1）の描画座標を返す。"""
    nm = norm or gnorm(comps)
    return (x + t * w, y + h - gsum(t, comps) / nm * h)


CH = ["背景", "指標", "根拠", "課題", "数学", "活用"]
d = Deck(CH)

# ================================================================ 表紙
cv = d.cover(
    "PPG波形で血管を診る",
    [("麻酔中の循環動態モニターとしての SI・RI", 30, INK, True),
     ("― 反射波の同定という壁を、数学で越える ―", 26, SUB, False),
     ("", 12, SUB, False),
     ("SpO₂ モニタの脈波だけで、血管の状態を追えるか", 24, BLUE, False)],
    notes="本講演の主張は一つ。SpO₂ モニタが表示している脈波（PPG）は、"
          "血管の状態を映す情報を持っているが、その情報を取り出す SI・RI という指標は "
          "「反射波（拡張期ピーク）を同定できる」ことを暗黙の前提にしている。"
          "そして周術期でいちばん評価したい患者ほど、その前提が壊れる。"
          "本講演では、ランドマークを『探す』のをやめ、波形を『前進波＋反射波の重ね合わせ』"
          "としてモデル化して当てはめる（多ガウス分解）という数学的推定を提案し、"
          "それが循環動態把握に何をもたらすかを述べる。"
          "本資料は研究・教育目的の整理であり、臨床判断を指示するものではない。")
CVX, CVY, CVW, CVH = 0.9, 4.35, 6.6, 2.0
_ne = gnorm(ELASTIC)
wave(cv, ELASTIC, CVX, CVY, CVW, CVH, WAVE, 3.0, norm=_ne)
wave(cv, [ELASTIC[0]], CVX, CVY, CVW, CVH, BLUE, 2.0, dash=DASHED, norm=_ne)
wave(cv, ELASTIC[1:], CVX, CVY, CVW, CVH, VERM, 2.0, dash=DASHED, norm=_ne)
axis(cv, CVX, CVY, CVW, CVH)
textbox(cv, CVX, CVY + CVH + 0.06, 6.6, 0.40,
        [("前進波（青）＋反射波（朱）の模式図", 22, SUB)], space_after=0)
panel(cv, 8.1, 4.55, 4.5, 1.6, fill=TEAL_BG, line=TEAL,
      paras=[("反射波を", 26, TEAL, True), ("数学で取り出す", 26, TEAL, True)])

# ================================================================ 第1章 背景
s = d.add("術中に見えないもの", 0,
          source="出典: 本リポジトリ中核レビュー §1・§3（SpO₂/PPG 波形解析の流れ）",
          notes="麻酔中に我々が数字で見ているのは血圧・心拍数・SpO₂ という『結果』であり、"
                "その結果を作っている三つの入力（前負荷・心収縮力・血管トーヌス）は直接には見えない。"
                "前負荷は呼吸性変動（ΔPOP/PPV）で、心収縮力は心エコーで、ある程度は覗ける。"
                "しかし血管トーヌスだけは、観血的動脈圧ラインや肺動脈カテーテルを入れない限り"
                "連続的に見る手段がない。低血圧に対して昇圧薬を使うか輸液を足すかという判断は、"
                "まさにこの見えない軸の上で行われている。"
                "本講演は、この見えない軸を SpO₂ センサだけで推定できないかという問いから始まる。")
panel(s, 0.6, 2.05, 3.4, 1.15, fill=BLUE_BG, line=BLUE, paras=[("前負荷", 26, INK, True)])
panel(s, 4.35, 2.05, 3.4, 1.15, fill=BLUE_BG, line=BLUE, paras=[("心収縮力", 26, INK, True)])
panel(s, 8.10, 2.05, 3.4, 1.15, fill=VERM_BG, line=VERM, paras=[("血管トーヌス", 26, INK, True)])
for cx in (2.3, 6.05, 9.8):
    line(s, cx, 3.30, cx, 3.95, "8A8A8A", 2.0, arrow=True)
panel(s, 2.6, 4.05, 6.9, 1.0, fill=FAINT, line="8A8A8A",
      paras=[("見えるのは合計 ―― 血圧・心拍数", 26, INK, True)])
textbox(s, 0.6, 5.35, 11.0, 1.1,
        [("前負荷は呼吸性変動で、収縮力は心エコーで、ある程度は覗ける", 24, INK),
         ("血管トーヌスだけが、連続的に見る手段を持たない", 26, VERM, True)],
        space_after=8)

s = d.add("PPGは容積の信号", 0,
          source="出典: Allen J. Physiol Meas 2007;28:R1-39（PMID 17322588）",
          notes="PPG は指先に光を当て、拍動に伴う血液量（容積）の変化を光の強さの変化として"
                "とらえた信号である。拍動しない成分が DC、拍動する成分が AC で、灌流指数 PI は AC/DC。"
                "決定的に重要なのは、PPG が『圧』ではなく『容積』の信号だという点である。"
                "局所の容積変化はおおむね〈局所コンプライアンス × 局所脈圧〉で決まるため、"
                "PPG 振幅は中心大動脈圧の絶対値ではなく測定部位の性質に強く依存する。"
                "さらに臨床モニタは AGC（自動ゲイン制御）で波形の高さを勝手に正規化するので、"
                "振幅の絶対値と拍間の振幅変化は壊れている。一方、同一波形内の振幅比と"
                "タイミング（時間）の情報は AGC の後も保たれる。"
                "だから指標設計では、振幅よりタイミング／形状を優先するのが安全である。"
                "なお加速度脈波の形態に対する主要な脅威は AGC ではなく帯域制限である。")
panel(s, 0.6, 2.0, 5.5, 1.0, fill=TEAL_BG, line=TEAL,
      paras=[("PI ＝ AC ÷ DC", 28, INK, True)])
textbox(s, 0.6, 3.25, 5.6, 1.35,
        [("AC：拍動する成分（＝脈波）", 24, INK),
         ("DC：拍動しない土台の成分", 24, INK)], space_after=10)
wave(s, ELASTIC, 6.6, 2.05, 5.2, 1.35, color=WAVE, pt=2.6)
axis(s, 6.6, 2.05, 5.2, 1.35)
panel(s, 6.6, 3.55, 5.2, 0.55, fill=FAINT, line=None,
      paras=[("DC 成分（拍動しない土台）", 22, SUB, False)])
textbox(s, 0.6, 4.90, 11.9, 1.7,
        [("圧ではなく容積の信号 ―― 中心大動脈圧は映らない", 24, INK),
         ("AGC が壊すのは振幅の絶対値、残るのは時間と比", 24, VERM, True),
         ("だから指標は、振幅よりタイミングを優先する", 24, BLUE, True)],
        space_after=8)

s = d.add("前進波と反射波", 0,
          source="出典: 本リポジトリ中核レビュー §2 ／ Charlton PH, et al. Am J Physiol 2022;322:H493",
          notes="動脈波形は、左室駆出で生じて末梢へ進む前進波と、血管分岐・末梢抵抗・"
                "インピーダンス不整合の点で反射して中枢へ戻る反射波の合成として理解される。"
                "指先で記録される波形では、収縮期ピーク P1 が主に前進波を、"
                "その後に続く拡張期側のピーク P2（および重複切痕）が主に反射波の帰還を映す。"
                "古典的教科書は重複切痕を大動脈弁閉鎖に帰属させるが、"
                "大動脈で直接記録される鋭い incisura は末梢へ向かうほど鋭さを失い、"
                "複数の反射波の合成である dicrotic notch へと変質する。"
                "数値モデル研究では、フェニレフリンで末梢血管抵抗のみを変えると"
                "重複切痕が変化することが実測されている（Politi 2016）。"
                "要するに『波形から血管を読む』試みの核心は、"
                "反射波の大きさ（高さ）とタイミング（時相）を読むことに帰着する。"
                "SI・RI・重複切痕は、いずれもこの反射波の別々の側面を数値化したものである。")
PX, PY, PW, PH = 0.75, 2.62, 6.3, 2.35
NE = gnorm(ELASTIC)
wave(s, ELASTIC, PX, PY, PW, PH, WAVE, 3.0, norm=NE)
wave(s, [ELASTIC[0]], PX, PY, PW, PH, BLUE, 2.0, dash=DASHED, norm=NE)
wave(s, ELASTIC[1:], PX, PY, PW, PH, VERM, 2.0, dash=DASHED, norm=NE)
axis(s, PX, PY, PW, PH)
p1x, p1y = at(ELASTIC, 0.203, PX, PY, PW, PH, NE)
p2x, p2y = at(ELASTIC, 0.430, PX, PY, PW, PH, NE)
line(s, p1x, p1y - 0.12, p1x, PY - 0.28, BLUE, 1.25, dash=DASHED)
line(s, p2x, p2y - 0.12, p2x, PY - 0.28, VERM, 1.25, dash=DASHED)
line(s, p1x, PY - 0.22, p2x, PY - 0.22, BLUE, 2.0, arrow=True, head=True)
textbox(s, p1x - 0.55, PY - 0.72, 1.1, 0.4, [("P₁", 22, BLUE, True)], align=PP_ALIGN.CENTER,
        space_after=0)
textbox(s, p2x + 0.05, PY - 0.72, 1.1, 0.4, [("P₂", 22, VERM, True)], space_after=0)
textbox(s, (p1x + p2x) / 2 - 0.5, PY - 0.05, 1.2, 0.4, [("ΔT", 22, BLUE, True)],
        align=PP_ALIGN.CENTER, space_after=0)
textbox(s, 7.5, 2.30, 5.2, 2.7,
        [("前進波（青）", 26, BLUE, True),
         ("左室駆出で末梢へ進む波", 24, INK),
         ("", 12, INK),
         ("反射波（朱）", 26, VERM, True),
         ("末梢で跳ね返って戻る波", 24, INK)], space_after=8)
panel(s, 0.75, 5.25, 11.8, 1.05, fill=GOLD_BG, line=GOLD,
      paras=[("血管を読むとは、反射波の「高さ」と「時刻」を読むこと", 26, INK, True)])

s = d.add("反射波が語る二軸", 0,
          source="出典: 本リポジトリ中核レビュー §3（因子ごとの波形変化と検証強度）",
          notes="時相（早い／遅い）を最も強く動かすのは血管壁スティフネスである。"
                "壁が硬いと伝播が速まり反射波が早く帰るので、ΔT が短くなる。"
                "この伝播の速さを定量化した指標が PWV だが、PWV はスティフネスという因子そのものではなく"
                "その結果を測る指標であることに注意する。"
                "高さ（反射波・切痕の上下）を主に動かすのは全身血管抵抗・血管トーヌスである。"
                "Awad 2007 では、指 PPG の振幅と熱希釈 SVR の相関は弱く（r = −0.15）、"
                "切痕を含む『幅』の相関の方が良好であった（r = 0.56、14 例）。"
                "つまり振幅単独では鈍感で、切痕の位置・幅と組み合わせて初めて意味を持つ。"
                "この二軸の対応づけが、次章で SI と RI を読み分ける見取り図になる。")
panel(s, 0.7, 2.05, 5.7, 2.05, fill=BLUE_BG, line=BLUE, anchor=MSO_ANCHOR.TOP,
      paras=[("時間の軸 ―― いつ戻るか", 26, BLUE, True), ("", 12, INK),
             ("早く戻る ＝ 血管壁が硬い", 24, INK),
             ("PWV はその結果を測る指標", 22, SUB)], align=PP_ALIGN.LEFT, space_after=8)
panel(s, 6.9, 2.05, 5.7, 2.05, fill=VERM_BG, line=VERM, anchor=MSO_ANCHOR.TOP,
      paras=[("高さの軸 ―― どれだけ戻るか", 26, VERM, True), ("", 12, INK),
             ("高く戻る ＝ 末梢が締まっている", 24, INK),
             ("振幅単独では鈍感（r = −0.15）", 22, SUB)], align=PP_ALIGN.LEFT, space_after=8)
textbox(s, 0.7, 4.45, 11.9, 1.9,
        [("この二軸を測る指標が、次章の SI と RI である", 26, INK, True),
         ("", 12, INK),
         ("Awad 2007：指 PPG 振幅と熱希釈 SVR は弱相関 r = −0.15", 24, SUB),
         ("一方、切痕を含む「幅」は r = 0.56 と良好（14 例）", 24, SUB)], space_after=6)

# ================================================================ 第2章 指標
s = d.add("SI ― 時間の指標", 1,
          source="出典: Millasseau SC, et al. Clin Sci 2002;103:371-7（PMID 12241535）",
          notes="SI（stiffness index：スティフネス指数）は、指尖容積脈波（DVP）の"
                "収縮期ピーク P1 と拡張期側ピーク P2 の時間差 ΔT を用い、"
                "SI ＝ 被験者身長 ÷ ΔT で定義される。単位は m/s。"
                "考え方は単純で、反射波は体幹をいったん下って戻ってくるので、"
                "その往復距離はおおむね身長に比例する。往復距離を往復時間で割れば速さになる。"
                "つまり SI は『反射波の平均的な伝播速度』の代理量であり、"
                "頸動脈-大腿動脈脈波伝播速度（cf-PWV）と相関し、加齢に伴う大動脈スティフネス増加を反映する。"
                "身長を使うのは、身長が体幹の長さの代理になるからであって、"
                "身長そのものに生理学的意味があるわけではない。")
panel(s, 0.7, 1.95, 11.9, 1.0, fill=BLUE_BG, line=BLUE,
      paras=[("SI ＝ 身長 ÷ ΔT　［m/s］", 32, INK, True)])
QX, QY, QW, QH = 0.75, 3.35, 6.0, 2.0
wave(s, ELASTIC, QX, QY, QW, QH, WAVE, 2.6, norm=NE)
axis(s, QX, QY, QW, QH)
q1x, q1y = at(ELASTIC, 0.203, QX, QY, QW, QH, NE)
q2x, q2y = at(ELASTIC, 0.430, QX, QY, QW, QH, NE)
line(s, q1x, q1y - 0.10, q1x, QY - 0.30, BLUE, 1.25, dash=DASHED)
line(s, q2x, q2y - 0.10, q2x, QY - 0.30, BLUE, 1.25, dash=DASHED)
line(s, q1x, QY - 0.24, q2x, QY - 0.24, BLUE, 2.25, arrow=True, head=True)
textbox(s, (q1x + q2x) / 2 - 0.7, QY - 0.05, 1.4, 0.4, [("ΔT", 24, BLUE, True)],
        align=PP_ALIGN.CENTER, space_after=0)
textbox(s, 7.15, 3.35, 5.4, 2.3,
        [("ΔT ＝ 反射波の往復時間", 26, BLUE, True),
         ("往復距離 ≒ 身長に比例", 24, INK),
         ("距離 ÷ 時間 ＝ 速さ", 24, INK),
         ("硬いほど速く戻る → SI 高値", 24, INK)], space_after=10)

s = d.add("RI ― 高さの指標", 1,
          source="出典: Chowienczyk PJ, et al. J Am Coll Cardiol 1999;34:2007-14（PMID 10588217）",
          notes="RI（reflection index：反射指数）は、DVP の反射（拡張期）ピーク高 P2 を"
                "収縮期ピーク高 P1 で除した比である。圧反射波の指標であると同時に"
                "小血管トーヌス（small vessel tone）を反映する。"
                "Chowienczyk らの原典では、内皮依存性の β₂ 刺激（アルブテロール）による血管拡張で"
                "反射波が減弱し、その反応が 2 型糖尿病では鈍化することが示された。"
                "硝酸薬でも反射波が減じ、変曲点の位置が下がる。"
                "『変曲点の位置＝末梢トーヌス』という発想の直接の起点がこの研究である。"
                "なお RI は同一波形内の振幅比なので、AGC で全体が拡大縮小されても値は保たれる。"
                "ただし後述のとおり心拍数の交絡は受ける。")
panel(s, 0.7, 1.95, 11.9, 1.0, fill=VERM_BG, line=VERM,
      paras=[("RI ＝ P₂ ÷ P₁ × 100　［%］", 32, INK, True)])
wave(s, ELASTIC, QX, QY, QW, QH, WAVE, 2.6, norm=NE)
axis(s, QX, QY, QW, QH)
line(s, q1x, q1y, q1x, QY + QH, VERM, 2.25)
line(s, q2x, q2y, q2x, QY + QH, VERM, 2.25)
textbox(s, q1x - 0.62, QY + QH + 0.04, 1.2, 0.4, [("P₁", 22, VERM, True)],
        align=PP_ALIGN.CENTER, space_after=0)
textbox(s, q2x - 0.05, QY + QH + 0.04, 1.2, 0.4, [("P₂", 22, VERM, True)], space_after=0)
textbox(s, 7.15, 3.35, 5.4, 2.3,
        [("反射がどれだけ大きいか", 26, VERM, True),
         ("末梢の小血管トーヌスを反映", 24, INK),
         ("血管拡張薬で RI は低下する", 24, INK),
         ("同一波形内の比 → AGC に強い", 24, INK)], space_after=10)

s = d.add("SIとRIの分担", 1,
          source="出典: 本リポジトリ中核レビュー §5 ／ Millasseau 2002・Chowienczyk 1999",
          notes="SI と RI は同じ拡張期ピーク P2 から作られるが、測っている軸が違う。"
                "SI は P1 から P2 までの時間を使うので大動脈側の硬さを、"
                "RI は P2 の高さを使うので末梢小血管のトーヌスを反映する。"
                "実務上は『時間指標の SI』と『振幅比の RI』という区別が重要で、"
                "臨床モニタの AGC・心拍数変動に対する頑健性が両者で異なる（第3章）。"
                "そして本講演の主題は最下段にある。どちらの指標も、"
                "拡張期ピーク P2 ＝ 反射波を同定できることを暗黙の前提にしている。"
                "この前提が崩れると、二つの指標は同時に、そして静かに壊れる。")
panel(s, 0.7, 1.95, 5.8, 2.75, fill=BLUE_BG, line=BLUE, anchor=MSO_ANCHOR.TOP,
      paras=[("SI（時間の軸）", 28, BLUE, True), ("", 10, INK),
             ("身長 ÷ ΔT", 24, INK),
             ("大動脈のスティフネス", 24, INK),
             ("心拍数の交絡を受けにくい", 24, INK)], align=PP_ALIGN.LEFT, space_after=8)
panel(s, 6.8, 1.95, 5.8, 2.75, fill=VERM_BG, line=VERM, anchor=MSO_ANCHOR.TOP,
      paras=[("RI（高さの軸）", 28, VERM, True), ("", 10, INK),
             ("P₂ ÷ P₁", 24, INK),
             ("末梢小血管のトーヌス", 24, INK),
             ("心拍数の交絡を受けやすい", 24, INK)], align=PP_ALIGN.LEFT, space_after=8)
panel(s, 0.7, 5.05, 11.9, 1.25, fill=RED_BG, line=RED,
      paras=[("共通の前提 ―― 拡張期ピーク P₂ が同定できること", 28, RED, True)])

# ================================================================ 第3章 根拠
s = d.add("SIはPWVと合うか", 2,
          source="出典: Millasseau SC, et al. Clin Sci 2002;103:371-7（PMID 12241535）",
          notes="Millasseau らは、指尖容積脈波から得た SI が cf-PWV と r = 0.65 で相関し、"
                "被験者内の変動係数が 9.6% であることを報告している。"
                "この二つの数値は意味を分けて読む必要がある。"
                "r = 0.65 という相関は、集団のなかで個人を序列づけるには不十分である。"
                "一方、被験者内変動係数 9.6% は、同一人物の変化を追跡するには十分に小さい。"
                "したがって『術前値でリスク層別化する』使い方は r = 0.65 の壁に当たるが、"
                "『同一患者の術中変化 Δ を追う』使い方であれば変動係数 9.6% で足りる。"
                "これは本プロジェクト全体の設計原則である Δ 追跡を、周術期の文脈で独立に支持する数値である。")
panel(s, 0.7, 2.0, 5.8, 1.9, fill=FAINT, line="8A8A8A", anchor=MSO_ANCHOR.TOP,
      paras=[("cf-PWV との相関", 26, INK, True), ("", 10, INK),
             ("r ＝ 0.65", 34, VERM, True)], space_after=6)
panel(s, 6.8, 2.0, 5.8, 1.9, fill=FAINT, line="8A8A8A", anchor=MSO_ANCHOR.TOP,
      paras=[("被験者内 変動係数", 26, INK, True), ("", 10, INK),
             ("CV ＝ 9.6 %", 34, BLUE, True)], space_after=6)
textbox(s, 0.7, 4.15, 11.9, 2.2,
        [("集団のなかで個人を序列づけるには足りない", 26, VERM, True),
         ("同一人物の変化を追うには十分に小さい", 26, BLUE, True),
         ("", 12, INK),
         ("→ 絶対値の校正ではなく、ベースラインからの Δ 追跡へ", 26, INK, True)],
        space_after=10)

s = d.add("RIは薬に反応する", 2,
          source="出典: Chowienczyk 1999（PMID 10588217）／ Takazawa K, et al. Hypertension 1998;32:365-70（PMID 9719069）",
          notes="Chowienczyk らは、内皮依存性の β₂ 刺激による血管拡張で反射波が減弱すること、"
                "そしてその反応が 2 型糖尿病患者では鈍化することを示した。"
                "硝酸薬投与でも反射波が減じて変曲点の位置が下がる。"
                "Takazawa らは加速度脈波（SDPPG）の d/a 比が血管作動薬に鋭敏に反応することを示した。"
                "アンジオテンシン投与で d/a が低下し、ニトログリセリンで上昇する。"
                "つまり反射波由来の指標は、血管作動薬に対する感度そのものは持っている。"
                "問題は感度ではなく、後述する『そもそも反射波を同定できるか』の方にある。")
panel(s, 0.7, 2.0, 5.8, 2.5, fill=VERM_BG, line=VERM, anchor=MSO_ANCHOR.TOP,
      paras=[("RI（原波形）", 26, VERM, True), ("", 10, INK),
             ("β₂ 刺激で反射波が減弱", 24, INK),
             ("硝酸薬で変曲点が下がる", 24, INK),
             ("2 型糖尿病では反応が鈍化", 24, INK)], align=PP_ALIGN.LEFT, space_after=8)
panel(s, 6.8, 2.0, 5.8, 2.5, fill=TEAL_BG, line=TEAL, anchor=MSO_ANCHOR.TOP,
      paras=[("d/a 比（加速度脈波）", 26, TEAL, True), ("", 10, INK),
             ("アンジオテンシンで低下", 24, INK),
             ("ニトログリセリンで上昇", 24, INK),
             ("切痕が乏しい波形でも取れる", 24, INK)], align=PP_ALIGN.LEFT, space_after=8)
panel(s, 0.7, 4.85, 11.9, 1.15, fill=GOLD_BG, line=GOLD,
      paras=[("血管作動薬への感度はある ―― 問題は感度ではない", 26, INK, True)])

s = d.add("12.7万人の成績", 2,
          source="出典: Chen H, et al. J Clin Hypertens 2025;27:e70058（PMID 40346852）",
          notes="Chen らは UK Biobank の参加者 127,045 名（40〜69 歳）を追跡中央値 11.7 年で観察し、"
                "PPG 由来の動脈スティフネス指数 ASI と主要心血管イベント MACE の関連を検討した。"
                "非高齢者（40〜64 歳、102,687 名）では未調整ハザード比 1.314（95%CI 1.280-1.350）、"
                "共変量調整後は 1.06〜1.13 に減衰するが有意性は保持された。"
                "高齢者（65〜69 歳、24,358 名）では未調整 1.066（95%CI 1.026-1.107）で、"
                "調整後は有意性が消失した。原著の結論は『ASI は 65 歳未満における一次予防に用いるべき』である。"
                "しばしば引用される『ハザード比 1.31』は非高齢者群における未調整（粗）モデルの値であり、"
                "集団全体の値でも調整後の値でもない。この限定を必ず付して引用すること。"
                "この研究の意味は二重である。SpO₂ センサだけで取れる指標が 10 万人規模で"
                "心血管イベントを予測しうること。そして、その予測力が最も血管の硬い集団で消えること。")
panel(s, 0.7, 2.0, 5.8, 2.15, fill=BLUE_BG, line=BLUE, anchor=MSO_ANCHOR.TOP,
      paras=[("非高齢者 40〜64 歳", 26, BLUE, True), ("", 10, INK),
             ("未調整 HR 1.314", 26, INK, True),
             ("調整後 1.06〜1.13（有意）", 24, INK)], align=PP_ALIGN.LEFT, space_after=8)
panel(s, 6.8, 2.0, 5.8, 2.15, fill=RED_BG, line=RED, anchor=MSO_ANCHOR.TOP,
      paras=[("高齢者 65〜69 歳", 26, RED, True), ("", 10, INK),
             ("未調整 HR 1.066", 26, INK, True),
             ("調整後は有意性が消失", 24, INK)], align=PP_ALIGN.LEFT, space_after=8)
textbox(s, 0.7, 4.45, 11.9, 1.9,
        [("SpO₂ センサだけの指標が 12.7 万人で心血管イベントを予測", 26, INK, True),
         ("しかし最も血管が硬い集団では、その力が消える", 26, RED, True),
         ("引用注意：「1.31」は非高齢・未調整の値である", 24, SUB)], space_after=10)

s = d.add("取れる指標ほど根拠薄", 2,
          source="出典: 本リポジトリ「周術期アウトカムと血管スティフネス」§1",
          notes="血管スティフネスを評価する手段は取得の容易さで並べられるが、"
                "エビデンスの強さで並べると順序がほぼ逆になる。"
                "SDPPG 指標と PPG 由来 SI/ASI は SpO₂ センサだけで取れるが周術期の前向き検証がほぼない。"
                "baPWV は専用機が要るが術後アウトカムの予測研究がある。"
                "cfPWV は手技を要し術中は不可能だが、導入時低血圧の予測研究がある（ただし反証もある）。"
                "この非対称が意味することは明快である。離島の一人麻酔科でも取れる指標ほど検証が乏しく、"
                "確かなエビデンスがある指標ほどその現場では取れない。"
                "本プロジェクトはこの空隙を埋めようとするものであり、"
                "同時に、現時点でその空隙が埋まっていないことを正直に認識しておく必要がある。")
rows = [("SDPPG・PPG-SI", "SpO₂ センサのみ", "◎ 取得容易", "× 周術期検証なし", VERM),
        ("baPWV", "専用機", "△ 術前外来のみ", "○ 術後予測研究あり", SUB),
        ("cfPWV", "専用機・手技", "× 術中は不可", "○ 導入時低血圧の研究", SUB)]
ry = 2.05
panel(s, 0.7, ry, 3.3, 0.62, fill=FAINT, line=None, paras=[("指標", 22, INK, True)])
panel(s, 4.15, ry, 3.5, 0.62, fill=FAINT, line=None, paras=[("周術期の取得", 22, INK, True)])
panel(s, 7.80, ry, 4.8, 0.62, fill=FAINT, line=None, paras=[("アウトカム根拠", 22, INK, True)])
for i, (nm, dev, easy, ev, col) in enumerate(rows):
    yy = ry + 0.75 + i * 0.86
    panel(s, 0.7, yy, 3.3, 0.72, fill=None, line=col, line_pt=1.5,
          paras=[(nm, 22, col, True)])
    panel(s, 4.15, yy, 3.5, 0.72, fill=None, line=col, line_pt=1.5,
          paras=[(easy, 22, INK, False)])
    panel(s, 7.80, yy, 4.8, 0.72, fill=None, line=col, line_pt=1.5,
          paras=[(ev, 22, INK, False)])
panel(s, 0.7, 5.45, 11.9, 0.95, fill=GOLD_BG, line=GOLD,
      paras=[("手元で取れる指標ほど、周術期の裏づけがない", 26, INK, True)])

s = d.add("時間スケールの不一致", 2,
          source="出典: 本リポジトリ中核レビュー §5 ／ Md Lazin Md Lazim MR, et al. IJERPH 2020;17:2591（PMID 32290168）",
          notes="SI・RI は本来、安静時の被験者で大動脈スティフネスや反射（小血管トーヌス）という"
                "半ば慢性的な血管特性を評価する指標として検証された。"
                "1 拍ごとの急性の全身血管抵抗変動・前負荷変動をリアルタイムに追う指標としては未検証である。"
                "術中の急性トーヌス変化には、切痕の位置・幅や加速度脈波の d/a のほうが対応しやすい。"
                "定量化を『反射・スティフネス軸』と『急性トーヌス軸』に分けておくと、"
                "この時間スケールの取り違えを避けられる。"
                "また心拍数の交絡は指標依存である。系統的レビューによれば、"
                "反射指数 RI は心拍数と相当程度に関連するが、スティフネス指数 SI の関連は乏しく、"
                "加速度脈波指標については結論が出ていない。"
                "周術期のように心拍数が大きく動く状況では、振幅比の RI よりも時間指標の SI のほうが"
                "交絡を受けにくいと考えられる。"
                "なお『心拍数が上がると反射波が高くなる』という記述はヒト実測では支持されていない。")
panel(s, 0.7, 2.0, 11.9, 1.15, fill=RED_BG, line=RED,
      paras=[("SI・RI は「安静時の血管特性」の指標として検証された", 26, RED, True)])
textbox(s, 0.7, 3.35, 11.9, 1.35,
        [("1 拍ごとの急性変動を追う指標としては未検証", 26, INK, True),
         ("術中の急性トーヌスには切痕の位置・幅や d/a が対応しやすい", 24, INK)],
        space_after=10)
panel(s, 0.7, 4.85, 5.8, 1.45, fill=VERM_BG, line=VERM, anchor=MSO_ANCHOR.TOP,
      paras=[("RI は心拍数と関連する", 24, VERM, True),
             ("頻脈の術中は不利", 24, INK)], align=PP_ALIGN.LEFT, space_after=8)
panel(s, 6.8, 4.85, 5.8, 1.45, fill=BLUE_BG, line=BLUE, anchor=MSO_ANCHOR.TOP,
      paras=[("SI の関連は乏しい", 24, BLUE, True),
             ("時間指標のほうが頑健", 24, INK)], align=PP_ALIGN.LEFT, space_after=8)

# ================================================================ 第4章 課題
s = d.add("壁は反射波の同定", 3,
          source="出典: 本リポジトリ中核レビュー §6・§7",
          notes="ここからが本講演の中心である。"
                "SI も RI も、拡張期ピーク P2 という一点を波形上で決めることから始まる。"
                "P2 が決まらなければ ΔT も P2/P1 も計算できない。"
                "つまり SI・RI の信頼性の問題は、統計や校正の問題である前に、"
                "『波形上のどこを P2 と呼ぶか』という同定の問題である。"
                "そしてこの同定は、周術期でいちばん評価したい患者ほど難しくなる。")
panel(s, 0.7, 2.0, 11.9, 1.15, fill=RED_BG, line=RED,
      paras=[("P₂ が取れなければ、SI も RI も存在しない", 30, RED, True)])
WX, WY, WW, WH = 1.6, 3.90, 5.4, 1.85
NS = gnorm(STIFF)
wave(s, STIFF, WX, WY, WW, WH, WAVE, 2.6, norm=NS)
axis(s, WX, WY, WW, WH)
sx, sy = at(STIFF, 0.48, WX, WY, WW, WH, NS)
line(s, sx, WY + 0.08, sx, sy - 0.12, RED, 2.25, dash=DASHED, arrow=True)
textbox(s, sx - 0.45, WY - 0.44, 0.9, 0.44, [("？", 28, RED, True)], align=PP_ALIGN.CENTER,
        space_after=0)
textbox(s, 7.6, 4.00, 5.0, 2.2,
        [("拡張期ピークはどこか", 26, RED, True),
         ("局所最大が無い波形では", 24, INK),
         ("探すこと自体が成立しない", 24, INK)], space_after=10)

s = d.add("硬いほど消える", 3,
          source="出典: 本リポジトリ中核レビュー §6 ／ Millasseau 2002・Dawber 1973（PMID 4699520）",
          notes="ここに、この研究領域が抱える中心的なパラドクスがある。"
                "生理学的には次の連鎖が働く。スティフネス上昇 → 反射波の早期帰還（PWV 上昇として測定される）"
                "→ 収縮期への融合 → 一峰性化 → 重複切痕・拡張期ピークの減弱・消失。"
                "つまり、切痕や P2 を評価したい当の集団（高齢・高スティフネス）で、それらは最も見えにくくなる。"
                "Dawber らは 1973 年の Framingham で、動脈脈波を切痕の見え方で 4 クラスに分類している。"
                "Class 1 が明瞭な切痕、Class 4 が切痕の痕跡なしで、"
                "健常若年は Class 1、加齢・スティフネス上昇に伴い Class 4 へ移行する。"
                "この構造は UK Biobank の ASI が高齢者で予測力を失うことと同型であり、"
                "加速度脈波の f 点（拡張期ピークに対応する点）が高スティフネス例で検出できないことともつながる。"
                "指標が最も必要な集団で、指標が働かなくなる。")
chain = [["壁が硬い"], ["PWV 上昇"], ["反射波が", "早く戻る"],
         ["収縮期に", "融合する"], ["一峰性化"], ["P₂ 消失"]]
cw, gap = 1.82, 0.20
cx0 = 0.72
for i, tt_ in enumerate(chain):
    col = RED if i >= 4 else VERM
    bg = RED_BG if i >= 4 else VERM_BG
    panel(s, cx0 + i * (cw + gap), 2.05, cw, 1.35, fill=bg, line=col,
          paras=[(u, 22, INK, True) for u in tt_], space_after=2)
    if i < len(chain) - 1:
        line(s, cx0 + i * (cw + gap) + cw + 0.02, 2.72,
             cx0 + (i + 1) * (cw + gap) - 0.02, 2.72, "8A8A8A", 2.0, arrow=True)
GX, GY, GW, GH = 1.2, 3.85, 4.7, 1.75
wave(s, ELASTIC, GX, GY, GW, GH, WAVE, 2.6, norm=NE)
axis(s, GX, GY, GW, GH)
textbox(s, GX, GY + GH + 0.06, 4.7, 0.42, [("しなやかな血管：P₂ が見える", 22, INK, True)],
        space_after=0)
wave(s, STIFF, 7.3, GY, GW, GH, RED, 2.6, norm=NS)
axis(s, 7.3, GY, GW, GH)
textbox(s, 7.3, GY + GH + 0.06, 4.9, 0.42, [("硬い血管：山がひとつに融合", 22, RED, True)],
        space_after=0)

s = d.add("第2ピークの正体", 3,
          source="出典: Epstein S, et al. Annu Int Conf IEEE EMBC 2014;2014:1969-72（PMID 25570367）",
          notes="ここで、より根本的な問題を一つ挟んでおく。"
                "我々は「第2ピーク＝末梢からの反射波」と当然のように呼んでいるが、"
                "この物理的な帰属自体が数値モデルからは支持されていない。"
                "Epstein らは、手の主要動脈を含む 75 本の動脈網を表現した非線形 1 次元の脈波伝播モデルで、"
                "動脈壁スティフネス・末梢抵抗・末梢コンプライアンス・末梢反射を個別に変化させ、"
                "模擬した指尖の面積波形からスティフネス指数 SI を算出した。"
                "結論は二つある。第一に、大動脈脈波伝播速度は大動脈スティフネスに支配されるが、"
                "SI は全ての導管血管のスティフネスに支配される。したがって SI は大動脈 PWV の直接の代用ではない。"
                "第二に、そしてこちらが重要だが、"
                "指尖容積脈波の第 2 ピークは末梢反射ではなく、"
                "75 本の動脈区間の内部で生じるインピーダンス不整合が主因である。"
                "上肢の末梢反射はむしろ第 1 ピークの到達時刻を遅らせる方向に働く。"
                "この指摘は本講演の手法にそのまま効く。"
                "波形をどれだけ上手く分解できても、二番目の山に「末梢反射波」というラベルを貼ってよいかは"
                "数学の外側の問題であり、この帰属が誤っていれば、そこから作った SI・RI の生理学的意味は変わってしまう。"
                "だからこそ、生成条件が既知の仮想被験者による検証を先に置く必要がある。")
panel(s, 0.7, 2.0, 11.9, 1.1, fill=FAINT, line="8A8A8A",
      paras=[("75 本の動脈網の数値モデルで検証（Epstein 2014）", 26, INK, True)])
panel(s, 0.7, 3.3, 5.8, 1.9, fill=BLUE_BG, line=BLUE, anchor=MSO_ANCHOR.TOP,
      paras=[("SI は PWV の代用ではない", 24, BLUE, True), ("", 8, INK),
             ("PWV は大動脈の硬さ", 22, INK),
             ("SI は導管血管全体の硬さ", 22, INK)], align=PP_ALIGN.LEFT, space_after=6)
panel(s, 6.8, 3.3, 5.8, 1.9, fill=VERM_BG, line=VERM, anchor=MSO_ANCHOR.TOP,
      paras=[("第2ピークの主因", 24, VERM, True), ("", 8, INK),
             ("末梢反射ではなく", 22, INK),
             ("動脈網内部のインピーダンス不整合", 22, INK)], align=PP_ALIGN.LEFT, space_after=6)
panel(s, 0.7, 5.4, 11.9, 0.95, fill=RED_BG, line=RED,
      paras=[("「2番目の山＝末梢反射波」は自明ではない", 26, RED, True)])

s = d.add("同定が壊れる四条件", 3,
          source="出典: 本リポジトリ中核レビュー §7 ／ Suboh MZ, et al. Front Public Health 2022;10:920946（PMID 35844894）",
          notes="拡張期ピークの同定が破綻する条件は四つに整理できる。"
                "第一に一峰性化。高齢・高スティフネス例で反射波が収縮期に融合し、山がひとつになる。"
                "第二に shoulder 化。ピークが肩（変曲点）になり、局所最大そのものが消失する。"
                "Suboh らは四次微分までを用いた特徴点検出を検討したうえで、"
                "加齢に伴い拡張期ピークが shoulder 化して同定が困難になることを明記している。"
                "局所最大が存在しなければ、微分の極値も定義できない。"
                "第三に頻脈。心拍数が上がると拡張期が短縮し、切痕・拡張期ピークを含む拡張期部分が"
                "圧縮・切り詰められる。"
                "第四に信号側の劣化。臨床モニタの帯域制限、AGC、体動・末梢冷感・プローブ装着条件。"
                "とくに加速度脈波の形態に対する主要な脅威は AGC ではなく帯域制限である点は"
                "実装上きわめて重要である。")
items = [("① 一峰性化", "高齢・高スティフネスで山が融合", VERM, VERM_BG),
         ("② shoulder 化", "肩になり局所最大が消える", VERM, VERM_BG),
         ("③ 頻脈", "拡張期が短縮し切り詰められる", BLUE, BLUE_BG),
         ("④ 信号の劣化", "帯域制限・AGC・体動・末梢冷感", RED, RED_BG)]
for i, (h, t, col, bg) in enumerate(items):
    xx = 0.7 + (i % 2) * 6.1
    yy = 2.02 + (i // 2) * 1.72
    panel(s, xx, yy, 5.8, 1.5, fill=bg, line=col, anchor=MSO_ANCHOR.TOP,
          paras=[(h, 26, col, True), ("", 8, INK), (t, 24, INK, False)],
          align=PP_ALIGN.LEFT, space_after=6)
panel(s, 0.7, 5.50, 11.9, 0.85, fill=GOLD_BG, line=GOLD,
      paras=[("評価したい患者ほど、これらが重なって起きる", 26, INK, True)])

s = d.add("点を探す方法の限界", 3,
          source="出典: 本リポジトリ中核レビュー §4・§6 ／ Murray & Foster 1996（PMID 8934343）・Takazawa 1998",
          notes="これまでの方法は、いずれも波形上の『点』を探すという発想に立っている。"
                "目視は Murray と Foster（1996）以来の伝統があり、"
                "振幅と重複切痕の位置がカテコラミン刺激の鋭敏な指標になりうると指摘された。"
                "しかし重複切痕はしばしば独立した切痕ではなく単なる変曲点としてしか現れず、"
                "末梢ほど不明瞭で、過減衰でも消える。トレンド（経時変化の向き）の読み取りには妥当だが、"
                "絶対的な定量評価には向かない。"
                "二次微分（加速度脈波）は、生波形で見えない変曲点を顕在化させる強力な手段である。"
                "しかしこれも原理的な限界を共有する。局所最大が存在しなければ二次微分の谷も定義できない。"
                "四次微分まで用いても、shoulder 化した拡張期ピークは同定できない。"
                "つまり『点を探す』という発想そのものが、高スティフネス例で行き止まりになる。"
                "だから発想を変える必要がある。")
panel(s, 0.7, 2.0, 5.8, 2.35, fill=FAINT, line="8A8A8A", anchor=MSO_ANCHOR.TOP,
      paras=[("目視で探す", 26, INK, True), ("", 10, INK),
             ("トレンドの向きは読める", 24, INK),
             ("絶対評価には向かない", 24, INK),
             ("過減衰でも切痕は消える", 24, INK)], align=PP_ALIGN.LEFT, space_after=8)
panel(s, 6.8, 2.0, 5.8, 2.35, fill=TEAL_BG, line=TEAL, anchor=MSO_ANCHOR.TOP,
      paras=[("微分で探す", 26, TEAL, True), ("", 10, INK),
             ("隠れた変曲点を顕在化できる", 24, INK),
             ("四次微分まで検討されている", 24, INK),
             ("しかし極大が消えれば谷も消える", 24, INK)], align=PP_ALIGN.LEFT, space_after=8)
panel(s, 0.7, 4.7, 11.9, 1.55, fill=RED_BG, line=RED,
      paras=[("「点を探す」方法は、同じ壁で同時に止まる", 28, RED, True),
             ("→ 探すのではなく、波を当てはめる", 26, INK, True)])

# ================================================================ 第5章 数学的推定
s = d.add("点から波へ", 4,
          source="手法自体は既報（Rubins 2008・Goswami 2010・Couceiro 2015）。未検証なのは周術期での成立性",
          notes="発想の転換はここにある。"
                "これまでは、観測された波形の上で『拡張期ピークという点はどこか』を探していた。"
                "これからは、『前進波と反射波を足すとこの波形になるはずだ』というモデルを立て、"
                "そのモデルが観測波形にいちばんよく合うようにパラメータを調整する。"
                "この違いは決定的である。点を探す方法は、点が見えなくなった瞬間に答えを返せない。"
                "モデルを当てはめる方法は、山が融合して見えなくなっても、"
                "『二つの山の重ね合わせとして最もよく説明できる組み合わせ』を返すことができる。"
                "もちろんそれが正しい保証はない。だからこそ後半で制約と検証を扱う。")
panel(s, 0.7, 2.02, 5.8, 1.55, fill=FAINT, line="8A8A8A", anchor=MSO_ANCHOR.TOP,
      paras=[("これまで：点を探す", 26, INK, True),
             ("波形の上で P₂ の位置を決める", 24, INK)],
      align=PP_ALIGN.LEFT, space_after=8)
panel(s, 6.8, 2.02, 5.8, 1.55, fill=TEAL_BG, line=TEAL, anchor=MSO_ANCHOR.TOP,
      paras=[("これから：波を当てはめる", 26, TEAL, True),
             ("前進波＋反射波のモデルを当てる", 24, INK)],
      align=PP_ALIGN.LEFT, space_after=8)
FGY, FGH, FGW = 3.72, 1.38, 4.6
NS0 = gnorm(STIFF)
wave(s, STIFF, 1.30, FGY, FGW, FGH, WAVE, 2.6, norm=NS0)
axis(s, 1.30, FGY, FGW, FGH)
wave(s, STIFF, 7.40, FGY, FGW, FGH, WAVE, 2.6, norm=NS0)
wave(s, [STIFF[0]], 7.40, FGY, FGW, FGH, BLUE, 2.0, dash=DASHED, norm=NS0)
wave(s, [STIFF[1]], 7.40, FGY, FGW, FGH, VERM, 2.0, dash=DASHED, norm=NS0)
axis(s, 7.40, FGY, FGW, FGH)
textbox(s, 0.7, 5.18, 5.8, 0.36, [("点が見つからない", 22, RED, True)],
        align=PP_ALIGN.CENTER, space_after=0)
textbox(s, 6.8, 5.18, 5.8, 0.36, [("山として推定できる", 22, TEAL, True)],
        align=PP_ALIGN.CENTER, space_after=0)
panel(s, 0.7, 5.70, 11.9, 0.82, fill=GOLD_BG, line=GOLD,
      paras=[("見えない波を、見える波形から逆算する", 28, INK, True)])

s = d.add("順問題と逆問題", 4,
          source="提案手法（数学的な位置づけの説明）",
          notes="数学では、原因から結果を計算することを順問題、結果から原因を割り出すことを逆問題という。"
                "今回の順問題はやさしい。前進波と反射波の形が分かっていれば、足すだけで観測波形が得られる。"
                "難しいのは逆問題である。観測波形という『合計』だけを見て、"
                "その内訳である前進波と反射波を割り出さなければならない。"
                "料理にたとえれば、出来上がったスープを味わって材料と分量を当てるようなものである。"
                "合計が同じになる内訳は原理的に複数ありうるので、逆問題は一般に一意に解けない。"
                "この『一意に解けない』という性質を不良設定（ill-posed）といい、"
                "後のスライドで扱う中心的な難所になる。")
panel(s, 0.7, 2.05, 11.9, 1.5, fill=BLUE_BG, line=BLUE, anchor=MSO_ANCHOR.TOP,
      paras=[("順問題（やさしい）", 26, BLUE, True),
             ("前進波 ＋ 反射波 → 観測波形　　足すだけ", 26, INK, True)],
      align=PP_ALIGN.LEFT, space_after=8)
panel(s, 0.7, 3.75, 11.9, 1.5, fill=VERM_BG, line=VERM, anchor=MSO_ANCHOR.TOP,
      paras=[("逆問題（むずかしい）", 26, VERM, True),
             ("観測波形 → 前進波 ＋ 反射波　　内訳を当てる", 26, INK, True)],
      align=PP_ALIGN.LEFT, space_after=8)
textbox(s, 0.7, 5.45, 11.9, 0.9,
        [("スープを味わって材料と分量を当てるのに似ている", 26, INK, True)], space_after=0)

s = d.add("山ひとつの式", 4,
          source="Gaussian（ガウス関数）。PPG 分解に用いた最初期の報告は Rubins U. Med Biol Eng Comput 2008;46:1271-6（PMID 18855034）",
          notes="部品として使うのはガウス関数、いわゆる『釣鐘型の山』である。"
                "式は g(t) ＝ a × exp( −(t − μ)² ÷ (2σ²) ) と書く。"
                "難しく見えるが、つまみは三つしかない。"
                "a は山の高さ。大きくすると山が高くなる。"
                "μ（ミュー）は山の位置。大きくすると山が右へずれる。"
                "σ（シグマ）は山の幅。大きくすると山がなだらかに広がる。"
                "exp は指数関数で、(t − μ)² すなわち中心からの距離の二乗が大きいほど"
                "急速にゼロへ近づくことを表す。これが『中心が高く、離れるほど低い』釣鐘の形を作る。"
                "なぜ山の形を使うのか。前進波も反射波も、"
                "『ある時刻に立ち上がってピークを作り、また下がる』一つの塊だからである。"
                "PPG をガウス関数の和で表す発想は Rubins（2008）に遡る。")
panel(s, 0.7, 1.95, 11.9, 1.05, fill=TEAL_BG, line=TEAL,
      paras=[("g(t) ＝ a × exp( −(t − μ)² ÷ 2σ² )", 30, INK, True)])
knobs = [("a：高さ", "山の高さを決める", VERM),
         ("μ：位置", "山の時刻を決める", BLUE),
         ("σ：幅", "山の広がりを決める", TEAL)]
for i, (h, t, col) in enumerate(knobs):
    panel(s, 0.7 + i * 4.05, 3.2, 3.75, 1.35, fill=None, line=col, line_pt=2.0,
          anchor=MSO_ANCHOR.TOP,
          paras=[(h, 26, col, True), (t, 22, INK, False)], space_after=6)
KX, KY, KW, KH = 1.3, 4.85, 10.6, 1.35
NK = 0.85
wave(s, [(0.55, 0.28, 0.055)], KX, KY, KW, KH, "6E6E6E", 2.6, norm=NK)
wave(s, [(0.85, 0.28, 0.055)], KX, KY, KW, KH, VERM, 2.2, dash=DASHED, norm=NK)
wave(s, [(0.55, 0.62, 0.055)], KX, KY, KW, KH, BLUE, 2.2, dash=DASHED, norm=NK)
wave(s, [(0.55, 0.28, 0.125)], KX, KY, KW, KH, TEAL, 2.2, dash=DASHED, norm=NK)
axis(s, KX, KY, KW, KH)

s = d.add("山を足すと波になる", 4,
          source="出典: Rubins 2008（PMID 18855034）／ Couceiro R, et al. Physiol Meas 2015;36:1801-25（PMID 26235798）",
          notes="山を複数足し合わせると PPG の一拍分の形になる。"
                "y(t) ＝ g₁(t) ＋ g₂(t) ＋ g₃(t) …。"
                "生理学的な読み替えは次のとおり。"
                "g₁ が前進波、すなわち左室駆出そのものに対応する最初の山。"
                "g₂ が第一の反射波、すなわち拡張期ピークを作る山。"
                "g₃ 以降が後続の反射・拡張期の緩やかな成分である。"
                "何個の山を使うかは研究によって異なる。"
                "Rubins（2008）は収縮期波と拡張期波をそれぞれ二つのガウス関数の和で表した。"
                "Couceiro ら（2015）は五つのガウス関数で PPG 一拍を分解している。"
                "重要なのは個数そのものではなく、"
                "『第一の山＝前進波、第二の山＝第一反射波』という対応を固定して運用することである。"
                "この対応が固定されて初めて、モデルのパラメータから SI・RI を再定義できる。")
MX, MY, MW, MH = 0.9, 2.1, 7.2, 2.6
wave(s, ELASTIC, MX, MY, MW, MH, WAVE, 3.0, norm=NE)
wave(s, [ELASTIC[0]], MX, MY, MW, MH, BLUE, 2.0, dash=DASHED, norm=NE)
wave(s, [ELASTIC[1]], MX, MY, MW, MH, VERM, 2.0, dash=DASHED, norm=NE)
wave(s, [ELASTIC[2]], MX, MY, MW, MH, "9A9A9A", 2.0, dash=DASHED, norm=NE)
axis(s, MX, MY, MW, MH)
textbox(s, 8.5, 2.15, 4.1, 2.6,
        [("g₁ ＝ 前進波", 26, BLUE, True),
         ("g₂ ＝ 第一反射波", 26, VERM, True),
         ("g₃ ＝ 後続成分", 26, "9A9A9A", True)], space_after=14)
panel(s, 0.9, 5.05, 11.7, 1.2, fill=TEAL_BG, line=TEAL,
      paras=[("y(t) ＝ g₁(t) ＋ g₂(t) ＋ g₃(t)", 30, INK, True)])

s = d.add("良し悪しの測り方", 4,
          source="最小二乗法（least squares）。PPG 分解での実装例は Couceiro 2015（PMID 26235798）",
          notes="では、当てはめの良し悪しをどう測るか。"
                "各時刻で『実測値 − モデル値』の差（残差）を計算し、それを二乗して全時刻で足し合わせる。"
                "これを残差二乗和 SSE（sum of squared errors）という。"
                "二乗するのは二つの理由がある。プラスの誤差とマイナスの誤差が打ち消し合わないようにするため、"
                "そして大きな外れをより強く罰するためである。"
                "SSE が小さいほど、モデルは観測波形をよく説明している。"
                "したがって我々の仕事は『SSE を最小にするパラメータの組を探す』という一つの問題に還元される。"
                "これが最小二乗法である。"
                "パラメータは一つの山につき三つ（a, μ, σ）なので、山が三つなら九つ、五つなら十五個になる。"
                "この十五次元の空間から、SSE を最小にする一点を探すことになる。")
EX, EY, EW, EH = 0.9, 2.15, 7.2, 2.5
wave(s, ELASTIC, EX, EY, EW, EH, WAVE, 2.8, norm=NE)
MOD = [(1.00, 0.20, 0.070), (0.40, 0.45, 0.105), (0.20, 0.63, 0.150)]
wave(s, MOD, EX, EY, EW, EH, TEAL, 2.4, dash=DASHED, norm=NE)
axis(s, EX, EY, EW, EH)
for tt in (0.30, 0.38, 0.46, 0.54, 0.62):
    ax_, ay_ = at(ELASTIC, tt, EX, EY, EW, EH, NE)
    bx_, by_ = at(MOD, tt, EX, EY, EW, EH, NE)
    line(s, ax_, ay_, bx_, by_, RED, 2.0)
textbox(s, 8.5, 2.2, 4.1, 2.4,
        [("実測（黒）", 24, WAVE, True),
         ("モデル（緑）", 24, TEAL, True),
         ("差（赤）を小さくしたい", 24, RED, True)], space_after=14)
panel(s, 0.9, 5.0, 11.7, 1.25, fill=BLUE_BG, line=BLUE,
      paras=[("SSE ＝ Σ（実測 − モデル）²　を最小にする", 28, INK, True)])

s = d.add("谷を下って探す", 4,
          source="反復最適化（Levenberg–Marquardt 等）。初期値依存性の定量的検討は Basso G, et al. Physiol Meas 2024;45(11)（PMID 39577084）",
          notes="SSE を最小にするパラメータは、式を解いて一発で求まるものではない。"
                "パラメータを少しずつ動かしながら SSE が小さくなる方向へ進む、という反復計算で探す。"
                "イメージは、霧の中で山を下るのに似ている。足元の傾きだけを頼りに、下り坂の方向へ一歩進む。"
                "これを繰り返すと谷底に着く。この考え方を勾配降下といい、"
                "曲線当てはめでは Levenberg–Marquardt 法という改良版がよく使われる。"
                "問題は、着いた谷底が本当にいちばん深い谷とは限らないことである。"
                "手前の浅いくぼみに落ちて止まってしまうことがあり、これを局所解という。"
                "どの谷に落ちるかは、どこから歩き始めたか（初期値）で決まる。"
                "Basso ら（2024）は MIMIC-III の 8,000 拍を用い、初期値をランダムに与えたときの"
                "モデルの感度と頑健性を定量的に比較している。"
                "初期値依存性は理論上の心配ではなく、実測データで確認された実務上の問題である。")
LX, LY, LW, LH = 1.1, 2.10, 6.5, 2.35


def sse_land(u):
    return (0.95 - 0.42 * math.exp(-((u - 0.25) ** 2) / (2 * 0.10 ** 2))
            - 0.80 * math.exp(-((u - 0.72) ** 2) / (2 * 0.11 ** 2)))


land = [(LX + (i / 200.0) * LW, LY + LH - sse_land(i / 200.0) * LH) for i in range(201)]
curve(s, land, "8A8A8A", 2.4)
axis(s, LX, LY, LW, LH)
for u_, colr in ((0.25, RED), (0.72, TEAL)):
    bx = LX + u_ * LW - 0.21
    by = LY + LH - sse_land(u_) * LH - 0.40
    panel(s, bx, by, 0.40, 0.40, fill=colr, line=None, radius=0.5)
textbox(s, LX + 0.25 * LW - 1.0, LY + LH + 0.06, 2.0, 0.40, [("局所解", 22, RED, True)],
        align=PP_ALIGN.CENTER, space_after=0)
textbox(s, LX + 0.72 * LW - 1.1, LY + LH + 0.06, 2.2, 0.40, [("真の最小", 22, TEAL, True)],
        align=PP_ALIGN.CENTER, space_after=0)
textbox(s, LX, LY + LH + 0.49, 6.6, 0.35,
        [("縦軸 SSE ・ 横軸 パラメータ（模式図）", 22, SUB)], space_after=0)
textbox(s, 8.1, 2.15, 4.6, 2.6,
        [("傾きを頼りに下る", 26, INK, True),
         ("Levenberg–Marquardt 法", 22, INK),
         ("", 10, INK),
         ("浅い谷で止まる危険", 24, RED, True)], space_after=10)
panel(s, 1.1, 5.55, 11.5, 0.90, fill=RED_BG, line=RED,
      paras=[("どこから歩き始めるか（初期値）で答えが変わる", 26, RED, True)])

s = d.add("答えが一意でない", 4,
          source="不良設定（ill-posed）問題。PPG 分解での実証は Basso G, et al. Physiol Meas 2024（PMID 39577084）",
          notes="逆問題の本質的な難所がこれである。"
                "違う山の組み合わせでも、足し合わせた結果がほとんど同じ形になることがある。"
                "たとえば『高くて細い反射波』と『やや低くて広い反射波を少し早めに置いたもの』は、"
                "合計するとほぼ見分けがつかない。"
                "このとき SSE はどちらもほぼ同じ値を取るので、数学的にはどちらも『正解』である。"
                "しかし臨床的な意味はまったく違う。RI は前者で高く、後者で低く出る。"
                "この状態を不良設定（ill-posed）といい、"
                "『解が存在する』『解が一意である』『解がデータの微小な変化に対して安定である』"
                "という三条件のうち、後の二つが満たされない。"
                "Basso ら（2024）は、初期値をランダムに変えたときに従来モデルの推定値がどれだけ揺れるかを示し、"
                "非対称な skewed-Gaussian モデルのほうが揺れが小さいことを報告している。"
                "モデルの選択そのものが、一意性の問題への対処になりうるということである。")
AX_, AY_, AW_, AH_ = 0.9, 2.1, 5.3, 2.2
ALT = [(1.00, 0.20, 0.070), (0.36, 0.395, 0.115), (0.24, 0.64, 0.150)]
nalt = gnorm(ALT)
wave(s, ELASTIC, AX_, AY_, AW_, AH_, WAVE, 2.6, norm=NE)
wave(s, [ELASTIC[1]], AX_, AY_, AW_, AH_, VERM, 2.0, dash=DASHED, norm=NE)
axis(s, AX_, AY_, AW_, AH_)
textbox(s, AX_, AY_ + AH_ + 0.06, 5.3, 0.42, [("分解 A：高くて細い反射波", 22, VERM, True)],
        space_after=0)
wave(s, ALT, 7.1, AY_, AW_, AH_, WAVE, 2.6, norm=nalt)
wave(s, [ALT[1]], 7.1, AY_, AW_, AH_, TEAL, 2.0, dash=DASHED, norm=nalt)
axis(s, 7.1, AY_, AW_, AH_)
textbox(s, 7.1, AY_ + AH_ + 0.06, 5.4, 0.42, [("分解 B：低くて広い反射波", 22, TEAL, True)],
        space_after=0)
panel(s, 0.9, 5.0, 11.6, 1.25, fill=RED_BG, line=RED,
      paras=[("合計は同じでも、RI の値は変わる", 28, RED, True),
             ("＝ 数学だけでは答えが決まらない（不良設定）", 24, INK, True)])

s = d.add("生理学で縛る", 4,
          source="提案手法。初期値は加速度脈波（SDPPG）のランドマークから与える",
          notes="一意でない問題を解けるようにするには、探索の範囲を狭めるしかない。"
                "狭める根拠は数学ではなく生理学から取る。これが本手法の中心的な設計である。"
                "第一に順序の制約。前進波は反射波より必ず先に来るので μ₁ < μ₂ < μ₃ を課す。"
                "第二に時間窓の制約。反射波の往復時間 ΔT ＝ μ₂ − μ₁ は生理的にありうる範囲に限る。"
                "この範囲は身長と、想定される脈波伝播速度の範囲から決まる。"
                "第三に符号の制約。振幅 a と幅 σ は必ず正である。"
                "第四に初期値の制約。ランダムな初期値ではなく、"
                "加速度脈波（SDPPG）の a〜e 波の時刻を初期値として与える。"
                "加速度脈波の横軸（ランドマークの時刻）は、AGC で振幅が壊れていても保存される。"
                "微分は時間軸を変えないからである。"
                "つまり、従来法である微分は捨てるのではなく、当てはめの出発点として使う。"
                "『微分で当たりをつけ、当てはめで仕上げる』という二段構えになる。")
cons = [("順序", "μ₁ < μ₂ < μ₃", "前進波が先、反射波が後", BLUE),
        ("時間窓", "ΔT は生理的範囲", "身長と伝播速度から決まる", BLUE),
        ("符号", "a > 0、σ > 0", "高さも幅も負にならない", TEAL),
        ("初期値", "SDPPG の a〜e 波", "微分で当たりをつける", TEAL)]
for i, (h, f, t, col) in enumerate(cons):
    yy = 1.95 + i * 1.02
    panel(s, 0.7, yy, 2.35, 0.88, fill=None, line=col, line_pt=2.0,
          paras=[(h, 24, col, True)])
    panel(s, 3.2, yy, 3.7, 0.88, fill=None, line=col, line_pt=1.5,
          paras=[(f, 24, INK, True)])
    panel(s, 7.05, yy, 5.55, 0.88, fill=None, line=col, line_pt=1.5,
          paras=[(t, 22, INK, False)])
textbox(s, 0.7, 6.10, 11.9, 0.45,
        [("微分で当たりをつけ、当てはめで仕上げる", 24, TEAL, True)], space_after=0)

s = d.add("正解つきで検証", 4,
          source="出典: Charlton PH, et al. Am J Physiol Heart Circ Physiol 2019;317:H1062-85（PMID 31442381）／ Lee HC, et al. Sci Data 2022（PMID 35676300）",
          notes="当てはめができたとして、その分解が正しいかをどう確かめるか。"
                "実測の PPG には『正解』が付いていないので、三段構えで詰める。"
                "第一段は in silico、すなわち計算機シミュレーションである。"
                "Charlton ら（2019）の公開データベースは、25〜75 歳の心血管特性を文献レビューで同定し、"
                "それを入力として 4,374 名の仮想被験者の脈波を生成したものである。"
                "圧・流速・内腔断面積・光電容積脈波が主要な測定部位で同時に出力され、"
                "各波形を生成した心血管特性が既知である。"
                "圧と流量が両方あるので、古典的な波分離によって前進波・反射波の参照値を計算できる。"
                "つまり『答え合わせのできる波形』が数千例分ある。"
                "第二段は VitalDB などの公開周術期データセットで、実患者の高分解能波形に対して"
                "検出成功率と再現性を評価する。"
                "第三段が実機で、Vital Recorder 経由で AGC と帯域制限を受けた臨床モニタ波形に適用する。"
                "重要なのは、年齢層別の検出成功率を事前登録し、検出できなかった症例の扱いを"
                "先に決めておくことである。これを怠ると、検出できた症例だけを解析する選択バイアスが必ず入る。")
stages = [("① 計算機", "仮想被験者 4,374 名", "圧・流量・PPG が既知", TEAL, TEAL_BG),
          ("② 公開データ", "VitalDB の周術期波形", "検出成功率と再現性", BLUE, BLUE_BG),
          ("③ 実機", "Vital Recorder", "AGC・帯域制限の下で", VERM, VERM_BG)]
for i, (h, a_, b_, col, bg) in enumerate(stages):
    panel(s, 0.7 + i * 4.05, 2.05, 3.75, 2.5, fill=bg, line=col, anchor=MSO_ANCHOR.TOP,
          paras=[(h, 26, col, True), ("", 10, INK), (a_, 22, INK, False),
                 (b_, 22, INK, False)], space_after=8)
panel(s, 0.7, 4.85, 11.9, 1.4, fill=RED_BG, line=RED,
      paras=[("年齢層別の検出成功率を事前登録する", 26, RED, True),
             ("検出できなかった症例を除くと選択バイアスが必ず入る", 24, INK, True)])

s = d.add("SI・RIを再定義", 4,
          source="この再定義は既報。Rubins 2008 が RI を、Goswami 2010 が SI・RI を分解から導出している",
          notes="モデルが当てはまれば、SI と RI は波形上の点ではなくモデルのパラメータから定義できる。"
                "SI は身長を μ₂ − μ₁ で割ったもの、RI は a₂ を a₁ で割ったものになる。"
                "この再定義の意味は大きい。"
                "従来の SI・RI は、拡張期ピークという局所最大が波形上に存在することを要求していた。"
                "モデルのパラメータは、山が融合して局所最大が消えていても存在する。"
                "つまり、一峰性化した高スティフネス例でも値が出る。"
                "これが第 4 章で述べたパラドクス（評価したい集団で指標が壊れる）への直接の回答である。"
                "ただし『値が出る』ことと『値が正しい』ことは別である。"
                "融合が進むほど分解の不確実性は大きくなるので、"
                "推定値と同時に信頼区間あるいは当てはまりの良さを必ず併記して運用する必要がある。"
                "なお Couceiro ら（2015）は同じ趣旨の時間パラメータを T1_2、振幅パラメータを R1_2 と呼んでいる。")
panel(s, 0.7, 2.05, 5.8, 1.5, fill=BLUE_BG, line=BLUE,
      paras=[("SI ＝ 身長 ÷ (μ₂ − μ₁)", 28, INK, True)])
panel(s, 6.8, 2.05, 5.8, 1.5, fill=VERM_BG, line=VERM,
      paras=[("RI ＝ a₂ ÷ a₁", 28, INK, True)])
textbox(s, 0.7, 3.85, 11.9, 1.5,
        [("波形に山が見えなくても、モデルの山は存在する", 26, TEAL, True),
         ("→ 一峰性化した高スティフネス例でも値が出る", 26, INK, True)], space_after=12)
panel(s, 0.7, 5.4, 11.9, 0.9, fill=RED_BG, line=RED,
      paras=[("この再定義自体は、既に提案されている", 26, RED, True)])

s = d.add("既に試されている", 4,
          source="出典: 本リポジトリ「反射波の数学的分離から SI・RI を再計算する ― 先行技術調査」",
          notes="ここは本講演でいちばん正直に述べるべきところである。"
                "「点を探すのをやめ、波を当てはめる」という発想の転換も、"
                "そこから SI・RI を作り直すことも、血圧・血管抵抗と対比することも、すべて既に行われている。"
                "Rubins（2008）は指と耳の PPG を収縮期波・拡張期波に分け、"
                "それぞれを 2 つのガウス関数の和で当てはめ、"
                "直達波と 3 つの反射波の時刻から反射指数 RI とオーグメンテーション指数 AI を算出し、微分法と比較した。"
                "健常者 40 名。分解由来の RI はここが最初期である。"
                "Goswami ら（2010）は Rayleigh 関数による 2 波合成モデルから、"
                "反射指数 RI・スティフネス指数 SI・脈波伝播速度を明示的に導出し、"
                "健常者と治療中高血圧者の 113 信号で従来法と比較した。分解由来の SI もここで揃っている。"
                "Couceiro ら（2015）は 5 ガウス分解から SI・RI に加えて時間差 T1_2 と振幅比 R1_2 を算出し、"
                "循環動態が不安定な 43 名で血圧と総末梢血管抵抗係数に対比した。"
                "さらに Grabovskis ら（2015）はカフ圧で局所血管抵抗を段階的に上げ、"
                "分解由来の遅延と振幅比が応答することを示し、"
                "Wang ら（2018）は運動負荷で、Park ら（2022）は血管年齢で同様の解析を行い、"
                "Baruch らの Pulse Decomposition Analysis は中心動脈圧との対比を経て製品化されている。"
                "つまり、本講演の第 5 章で述べた手法は新しい提案ではない。"
                "この事実を伏せて話を進めるのは誠実ではないので、ここで明示する。"
                "詳細は本リポジトリの先行技術調査文書に PICO 形式で一覧化してある。")
rows_pa = [("2008", "Rubins", "ガウス当てはめから RI を算出", VERM),
           ("2010", "Goswami", "2 波合成から SI と RI を導出", VERM),
           ("2015", "Couceiro", "血圧・総末梢血管抵抗と対比", RED),
           ("2015〜", "Grabovskis ほか", "血管抵抗・運動負荷・血管年齢へ展開", SUB)]
for i, (yr_, au_, wt_, col_) in enumerate(rows_pa):
    yy = 2.02 + i * 0.92
    panel(s, 0.7, yy, 1.75, 0.78, fill=None, line=col_, line_pt=1.5,
          paras=[(yr_, 22, col_, True)])
    panel(s, 2.60, yy, 3.5, 0.78, fill=None, line=col_, line_pt=1.5,
          paras=[(au_, 22, INK, True)])
    panel(s, 6.25, yy, 6.35, 0.78, fill=None, line=col_, line_pt=1.5,
          paras=[(wt_, 22, INK, False)])
panel(s, 0.7, 5.78, 11.9, 0.85, fill=RED_BG, line=RED,
      paras=[("分解して SI・RI を作り直すことは、既出である", 26, RED, True)])

s = d.add("先行研究の成績", 4,
          source="出典: Couceiro R, et al. Physiol Meas 2015;36:1801-25（PMID 26235798）",
          notes="この方向にはすでに先行研究がある。"
                "Couceiro ら（2015）は五つのガウス関数で指尖 PPG を分解し、"
                "健常者と心血管疾患患者 68 名で、心エコーによる左室駆出時間 LVET と比較した。"
                "最良の推定値は絶対誤差 15.41 ± 13.66 ms、相関 ρ = 0.78 であった。"
                "さらに循環動態が不安定な 43 名で、分解から得たパラメータと"
                "血圧・総末梢血管抵抗係数 TPRI との関連を検討している。"
                "ここが本講演にとって決定的に重要である。"
                "最も高い相関を示したのは T1_2、すなわち前進波と第一反射波の時間差であり、"
                "TPRI との相関は ρ = 0.45 であった。"
                "一方、振幅比である R1_2（前進波と第一反射波の振幅の比）は、"
                "すべての参照値に対して低い相関しか示さなかった。"
                "つまり、分解で得られる時間パラメータのほうが振幅パラメータより有望である。"
                "これは本プロジェクトの設計原則『タイミング／形状の情報を振幅より優先する』と一致する。"
                "AGC の議論から導かれた原則と、独立した実測研究の結果が同じ方向を指している。")
panel(s, 0.7, 2.0, 11.9, 1.15, fill=FAINT, line="8A8A8A",
      paras=[("五ガウス分解：68 例で LVET 誤差 15.41 ± 13.66 ms（ρ = 0.78）", 24, INK, True)])
panel(s, 0.7, 3.35, 5.8, 1.85, fill=BLUE_BG, line=BLUE, anchor=MSO_ANCHOR.TOP,
      paras=[("時間パラメータ", 26, BLUE, True), ("", 8, INK),
             ("前進波と反射波の時間差", 22, INK),
             ("TPRI と ρ = 0.45（最高）", 24, INK, True)], align=PP_ALIGN.LEFT, space_after=6)
panel(s, 6.8, 3.35, 5.8, 1.85, fill=VERM_BG, line=VERM, anchor=MSO_ANCHOR.TOP,
      paras=[("振幅パラメータ", 26, VERM, True), ("", 8, INK),
             ("前進波と反射波の振幅比", 22, INK),
             ("参照値すべてと低相関", 24, INK, True)], align=PP_ALIGN.LEFT, space_after=6)
panel(s, 0.7, 5.4, 11.9, 0.9, fill=GOLD_BG, line=GOLD,
      paras=[("時間の軸のほうが有望 ―― ただし ρ = 0.45", 26, INK, True)])

s = d.add("圧だけで分ける法", 4,
          source="出典: Westerhof BE, et al. Hypertension 2006;48:595-601（PMID 16940207）／ Kips JG, et al. Hypertension 2009;53:142-9（PMID 19075098）",
          notes="ガウス分解とは別の、より古典的な道も押さえておく。"
                "波分離（wave separation）は、圧と流量の両方を測れば前進波と反射波を厳密に分けられる、"
                "という循環生理学の標準的手法である。"
                "しかし流量の測定は臨床では容易でない。"
                "Westerhof ら（2006）は、大動脈流量波形は個人差が比較的小さいことに着目し、"
                "実測流量の代わりに三角形で近似した流量波形を使うことを提案した。"
                "三角形の底辺は圧の立ち上がりから重複切痕まで、頂点は駆出時間の 30% あるいは圧の変曲点に置く。"
                "Kips ら（2009）は Asklepios 研究の 2,500 名超でこの近似を検証した。"
                "三角近似による反射量の一致は R² ＝ 0.55 にとどまり、"
                "より生理的な流量波形を用いると R² ＝ 0.74 に改善した。"
                "大動脈伝播時間の推定は R² < 0.29 と不良であった。"
                "しかも我々が扱うのは圧ではなく容積信号の PPG なので、仮定はさらに一段増える。"
                "したがってこの道は、主軸ではなく、"
                "ガウス分解の結果を突き合わせるための独立した参照として位置づけるのが妥当である。")
panel(s, 0.7, 2.0, 11.9, 1.05, fill=FAINT, line="8A8A8A",
      paras=[("本来は 圧 ＋ 流量 の両方が必要 → 流量を三角形で代用", 26, INK, True)])
kr = [("三角形で近似した流量", "R² ＝ 0.55", VERM),
      ("より生理的な流量波形", "R² ＝ 0.74", BLUE),
      ("大動脈の伝播時間", "R² < 0.29", RED)]
for i, (h, v, col) in enumerate(kr):
    yy = 3.25 + i * 1.0
    panel(s, 0.7, yy, 7.4, 0.85, fill=None, line=col, line_pt=1.5,
          paras=[(h, 24, INK, False)])
    panel(s, 8.3, yy, 4.3, 0.85, fill=None, line=col, line_pt=1.5,
          paras=[(v, 24, col, True)])
textbox(s, 0.7, 6.28, 11.9, 0.4,
        [("PPG は容積信号なので仮定が増える → 参照として使う", 22, SUB)], space_after=0)

s = d.add("数学が保証しないこと", 4,
          source="本章の内容は本プロジェクトの作業仮説であり、臨床での検証は未了である",
          notes="第 5 章を閉じるにあたって、限界を率直に述べておく。"
                "当てはまりが良いことは、正しいことの証明ではない。"
                "十分な数のガウス関数を使えば、どんな滑らかな曲線でもほぼ完全に再現できる。"
                "しかし『よく再現できた』ことと『二番目の山が本当に末梢からの反射波である』ことは別問題である。"
                "この対応づけは数学の外側にあり、生理学的な検証でしか埋められない。"
                "検証の道具は三つある。"
                "第一に薬理学的介入。血管拡張薬・昇圧薬を投与したときに、"
                "推定された反射波が既知の方向へ動くかを見る。"
                "第二に in silico の正解との照合。生成条件が既知の仮想被験者で真値と比較する。"
                "第三に独立指標との突き合わせ。cf-PWV や観血的動脈圧由来の指標と収束的妥当性を確認する。"
                "これらを通らないかぎり、この手法は仮説にとどまる。"
                "本講演はその仮説を、反証可能な形で提示するところまでを目的としている。")
panel(s, 0.7, 2.0, 11.9, 1.25, fill=RED_BG, line=RED,
      paras=[("当てはまりの良さは、正しさの証明ではない", 28, RED, True)])
textbox(s, 0.7, 3.45, 11.9, 1.0,
        [("山の数を増やせば、どんな曲線でも再現できてしまう", 24, INK),
         ("「二番目の山＝反射波」の対応は、数学の外側にある", 24, INK)], space_after=10)
vs = [("薬理学的介入", "既知の方向に動くか", TEAL),
      ("in silico の真値", "生成条件と照合する", BLUE),
      ("独立指標", "cf-PWV と突き合わせる", VERM)]
for i, (h, t, col) in enumerate(vs):
    panel(s, 0.7 + i * 4.05, 4.75, 3.75, 1.5, fill=None, line=col, line_pt=2.0,
          anchor=MSO_ANCHOR.TOP,
          paras=[(h, 24, col, True), (t, 22, INK, False)], space_after=6)

s = d.add("新規性はどこか", 4,
          source="出典: 本リポジトリ「反射波の数学的分離から SI・RI を再計算する ― 先行技術調査」§9",
          notes="では、この研究に何が残っているのか。新規性は指標の定義ではなく、検証の条件の側にしかない。"
                "第一に、周術期・全身麻酔下という設定である。"
                "先行研究の対象は健常者・傾斜台・カフ圧迫・運動負荷・高血圧外来・血管年齢コホートであり、"
                "麻酔導入時や昇圧薬投与時に分解由来指標が観血血圧と較正済み全身血管抵抗の変化を追随するかは未検証である。"
                "PubMed で分解手法と麻酔・周術期を掛け合わせて検索しても該当は 3 件のみで、"
                "分解由来の SI・RI を全身血管抵抗と対比した研究は 1 件も無かった。"
                "第二に、退化した波形における救済という仮説そのものである。"
                "一峰性化・shoulder 化してランドマーク法が破綻する拍において、"
                "モデル法が値を返し、かつその値が血管抵抗と関連するかを"
                "主要評価項目として事前規定した研究は見当たらない。"
                "年齢層・スティフネス層別の検出成功率を主要アウトカムに置き、"
                "pyPPG などのランドマーク法と同一の拍で直接対決させる設計にすれば、"
                "第 4 章で述べた第 2 ピークの帰属問題にも同時に答えられる。"
                "第三に、AGC と帯域制限のある実機モニタ波形での成立性。"
                "先行研究はすべて研究用 PPG か観血動脈圧を使っており、"
                "臨床パルスオキシメータの表示波形で分解が安定に解けるかは誰も確認していない。"
                "これは構想全体の必要条件であり、否定されれば構想は成立しない。"
                "第四に、絶対値の相関ではなく変化の追随性としての評価。"
                "先行研究はプールした相関係数を報告しているが、"
                "昇圧薬で血管抵抗を動かしたときの変化方向の一致率という評価軸は未実施である。"
                "第五に、拍ごとの識別可能性を出力として報告すること。"
                "推定値と一緒に不確かさを出し、識別不能な拍を事前規定で除外する運用は標準になっていない。"
                "そして重要な但し書きとして、Couceiro の成績を踏まえれば事前確率は低めに見積もるべきであり、"
                "陰性結果でも情報価値が出るように設計しておく必要がある。")
gaps = [("① 周術期・全身麻酔下での検証", TEAL),
        ("② 退化波形での救済という仮説", TEAL),
        ("③ AGC・帯域制限のある実機波形", BLUE),
        ("④ 相関ではなく、変化の追随性", BLUE),
        ("⑤ 拍ごとの識別可能性の報告", BLUE)]
for i, (t_, col_) in enumerate(gaps):
    panel(s, 0.7, 1.95 + i * 0.76, 11.9, 0.66, fill=None, line=col_, line_pt=1.75,
          paras=[(t_, 24, INK, True)], align=PP_ALIGN.LEFT)
panel(s, 0.7, 5.80, 11.9, 0.82, fill=GOLD_BG, line=GOLD,
      paras=[("新規性は定義ではなく、検証の条件の側にある", 26, INK, True)])

# ================================================================ 第6章 活用
s = d.add("Δとして使う", 5,
          source="出典: 本リポジトリ設計原則 §4.1 ／ Millasseau 2002（被験者内 CV 9.6%）",
          notes="臨床運用の第一原則は、絶対値を信じないことである。"
                "多くの既存指標は、波形の特徴量を血圧や全身血管抵抗の絶対値に対応づけようとして、"
                "機器ごと・個人ごとのばらつきに阻まれてきた。"
                "本アプローチは方針を変え、麻酔導入前のベースラインからの相対変化 Δ を追跡することを核心に置く。"
                "利点は三つある。"
                "個人内の変化だけを見るため絶対値の校正が要らない。"
                "平均動脈圧の推定式のような機器固有の変換式に縛られない。"
                "そして、手術中に問題になるのは『導入前と比べて今どう変わったか』であり、"
                "臨床的関心と一致する。"
                "数値的な根拠は Millasseau の被験者内変動係数 9.6% である。"
                "個人間の序列づけには足りない精度でも、個人内の変化追跡には十分に小さい。")
panel(s, 0.7, 2.0, 11.9, 1.2, fill=GOLD_BG, line=GOLD,
      paras=[("絶対値ではなく、導入前からの変化を追う", 28, INK, True)])
TX, TY, TW, TH = 1.0, 3.5, 7.0, 2.0
def _sig(z):
    return 1.0 / (1.0 + math.exp(-z))


trend = []
for i in range(181):
    u = i / 180.0
    v = (0.78 - 0.46 * _sig((u - 0.33) / 0.045) + 0.26 * _sig((u - 0.70) / 0.040)
         + 0.015 * math.sin(34 * u))
    trend.append((TX + u * TW, TY + TH - min(max(v, 0.04), 0.98) * TH))
curve(s, trend, BLUE, 2.8)
axis(s, TX, TY, TW, TH)
line(s, TX + 0.30 * TW, TY - 0.05, TX + 0.30 * TW, TY + TH, "9A9A9A", 1.5, dash=DASHED)
line(s, TX + 0.68 * TW, TY - 0.05, TX + 0.68 * TW, TY + TH, "9A9A9A", 1.5, dash=DASHED)
textbox(s, TX, TY + TH + 0.06, 7.0, 0.42, [("導入前 → 麻酔導入 → 昇圧薬（模式図）", 22, SUB)],
        space_after=0)
textbox(s, 8.4, 3.55, 4.2, 2.0,
        [("校正が要らない", 24, INK),
         ("推定式に縛られない", 24, INK),
         ("CV 9.6% で足りる", 24, BLUE, True)], space_after=12)

s = d.add("二軸で読む", 5,
          source="解釈の枠組み（仮説）。方向は Millasseau 2002・Chowienczyk 1999 の既知の所見に基づく",
          notes="推定された二つのパラメータを、二軸のマップとして読む。"
                "横軸は時間の軸で、前進波と反射波の時間差 ΔT。"
                "ΔT が短くなるのは反射波が早く戻ってくること、すなわち大動脈側が硬くなる方向である。"
                "縦軸は高さの軸で、反射波と前進波の振幅比 RI。"
                "RI が下がるのは反射が小さくなること、すなわち末梢が拡張する方向である。"
                "血管拡張薬で RI が低下することは Chowienczyk らの原典で示されている。"
                "この二軸を分けて見ることの臨床的な意味は、"
                "『いま起きているのは末梢の拡張か、それとも血管が硬いこと自体か』を分離できる点にある。"
                "麻酔導入時の低血圧に対して、末梢が開いているなら昇圧薬、"
                "もともと硬い血管に前負荷低下が重なっているなら輸液、"
                "という判断の材料になりうる。"
                "ただしこれは解釈の枠組みであって、検証された臨床アルゴリズムではない。"
                "とくに『局所の指トーヌスを見ているのか全身の血管抵抗を見ているのか』は未解決であり、"
                "上肢神経ブロック下で麻酔側と対照側を比較する観察研究が進行中である。")
CX_, CY_ = 6.85, 3.72
line(s, CX_, 4.78, CX_, 2.66, VERM, 2.0, arrow=True, head=True)
line(s, 5.30, CY_, 8.40, CY_, BLUE, 2.0, arrow=True, head=True)
panel(s, CX_ - 0.11, CY_ - 0.11, 0.22, 0.22, fill=TEAL, line=None, radius=0.5)
textbox(s, 5.55, 2.06, 2.6, 0.42, [("RI 高い ＝ 収縮", 22, VERM, True)],
        align=PP_ALIGN.CENTER, space_after=0)
textbox(s, 5.55, 4.94, 2.6, 0.42, [("RI 低い ＝ 拡張", 22, VERM, True)],
        align=PP_ALIGN.CENTER, space_after=0)
textbox(s, 1.75, 3.52, 3.3, 0.42, [("ΔT 短い ＝ 硬い", 22, BLUE, True)],
        align=PP_ALIGN.RIGHT, space_after=0)
textbox(s, 8.60, 3.52, 3.7, 0.42, [("ΔT 長い ＝ しなやか", 22, BLUE, True)], space_after=0)
textbox(s, 7.08, 3.92, 3.2, 0.42, [("● 導入前の基準点", 22, TEAL, True)], space_after=0)
panel(s, 0.7, 5.42, 11.9, 1.1, fill=TEAL_BG, line=TEAL,
      paras=[("「末梢が開いたのか、血管が硬いのか」を分けて見る", 26, INK, True),
             ("※ 局所トーヌスか全身血管抵抗かは未解決", 22, RED, True)])

s = d.add("使いどころ", 5,
          source="出典: Coutrot M, et al. Br J Anaesth 2019;122:605-12 ／ Tusman G, et al. J Clin Monit Comput 2019;33:815-24",
          notes="想定する使いどころを三つ挙げる。いずれも現時点では仮説である。"
                "第一に麻酔導入時低血圧。導入前のベースラインからの Δ を見ることで、"
                "血圧が下がる前に血管側の変化を捉えられる可能性がある。"
                "Tusman ら（2019）は心臓外科 15 例で、PPG 振幅と重複切痕の位置から血管トーヌスを"
                "6 クラスに分類し、収縮期血圧・全身血管抵抗・血管コンプライアンスとよく相関し、"
                "低血圧・高血圧エピソードを高い精度で検出したと報告している。"
                "第二に昇圧薬への血管反応。Coutrot ら（2019）は麻酔導入時 61 例で、"
                "相対的重複切痕高比 Dicpleth と灌流指数 PI の変動が、"
                "術中低血圧の検出および昇圧薬ボーラスへの血管反応の追跡に有用であることを示した"
                "（proof-of-concept 研究）。"
                "第三に脊椎麻酔後の低血圧。ただしこの領域の予測研究は帝王切開という単一設定に集中しており、"
                "一般化は未確立である。"
                "重要なのは、これらがいずれも『反射波に由来する形態指標が臨床事象と結びつく』ことを"
                "示唆する段階にとどまり、SI・RI そのものの周術期検証ではないという点である。")
uses = [("導入時低血圧", "血圧が下がる前に血管側の変化を見る", BLUE, BLUE_BG),
        ("昇圧薬への反応", "投与後に血管側がどう動いたかを見る", VERM, VERM_BG),
        ("脊椎麻酔後低血圧", "報告は帝王切開に集中し一般化は未確立", TEAL, TEAL_BG)]
for i, (h, t, col, bg) in enumerate(uses):
    yy = 2.0 + i * 1.42
    panel(s, 0.7, yy, 4.35, 1.2, fill=bg, line=col, paras=[(h, 26, col, True)])
    panel(s, 5.25, yy, 7.35, 1.2, fill=None, line=col, line_pt=1.5,
          paras=[(t, 22, INK, False)])
textbox(s, 0.7, 6.24, 11.9, 0.42,
        [("いずれも仮説段階 ―― 臨床判断の根拠にはしない", 24, RED, True)], space_after=0)

s = d.add("esCCOとの接続", 5,
          source="出典: Yamada T, et al. Anesth Analg 2012;115:82-7（PMID 22467885）／ 本リポジトリ「PWTT と esCCO」",
          notes="反射波の情報が取れると、既存モニタの弱点にも接続する。"
                "モニタが表示する PWTT の正体は脈波到達時間 PAT であり、"
                "心臓側の前駆出期 PEP と血管側の血管内伝播時間 VTT の和である。"
                "esCCO の較正係数 K には血管の情報が入っていないため、"
                "後負荷が上昇した場面で一回拍出量を系統的に過大評価する。"
                "Yamada ら（2012）の多施設検証では、esCCO の誤差が全身血管抵抗と"
                "r = 0.37（P < 0.0001）で相関することが示されている。"
                "一般に報告される一致性の水準は、安定期の全身麻酔下で熱希釈法との相関 r ≈ 0.84、"
                "バイアス約 1.6 L/min、誤差率およそ 47% であり、"
                "Critchley 基準の ±30% を大きく超える。絶対値の心拍出量計としては使えない。"
                "本プロジェクトの別稿は、この較正係数 K を加速度脈波の形態指標で動的に補正するという"
                "作業仮説を提示している。反射波を安定に推定できることは、その入力になりうる。"
                "ただしこの補正提案自体が未検証の仮説であることを繰り返し強調しておく。")
panel(s, 0.7, 2.0, 11.9, 1.05, fill=FAINT, line="8A8A8A",
      paras=[("PWTT ＝ PEP ＋ VTT　―― 血管の情報が分離できていない", 26, INK, True)])
panel(s, 0.7, 3.25, 5.8, 1.85, fill=RED_BG, line=RED, anchor=MSO_ANCHOR.TOP,
      paras=[("esCCO の誤差", 26, RED, True), ("", 8, INK),
             ("全身血管抵抗と r = 0.37", 24, INK),
             ("誤差率およそ 47%", 24, INK)], align=PP_ALIGN.LEFT, space_after=6)
panel(s, 6.8, 3.25, 5.8, 1.85, fill=TEAL_BG, line=TEAL, anchor=MSO_ANCHOR.TOP,
      paras=[("反射波が取れれば", 26, TEAL, True), ("", 8, INK),
             ("較正係数 K を動的に補正", 24, INK),
             ("※ 未検証の作業仮説", 24, RED, True)], align=PP_ALIGN.LEFT, space_after=6)
textbox(s, 0.7, 5.35, 11.9, 0.95,
        [("同じ血管の硬さが、術前はリスク指標に、術中は誤差源になる", 24, INK, True)],
        space_after=0)

s = d.add("限界", 5,
          source="出典: 本リポジトリ中核レビュー §7 ／ 各成果物の限界の記述",
          notes="限界を率直に列挙する。"
                "第一に、PPG は容積信号であり圧ではない。振幅・PI は中心インピーダンスよりも"
                "局所のコンプライアンス・血管運動トーヌス・灌流圧に支配される。"
                "第二に、指で記録される切痕位置が測定部位の局所トーヌスを映すのか"
                "全身血管抵抗を映すのかは未解決であり、上肢神経ブロック下で麻酔側と対照側を比較する"
                "観察研究が進行中である。"
                "第三に、臨床モニタの AGC と帯域制限。AGC は振幅の絶対値と拍間の振幅変化を壊し、"
                "加速度脈波の形態には帯域制限が効く。この区別は実装上きわめて重要である。"
                "第四に、加齢交絡。スティフネス上昇は急性の血行動態変化とは独立に切痕を減弱させるため、"
                "『いまの血管収縮』か『もとの硬い血管』かの切り分けを要する。"
                "第五に、SI・RI は 1 拍ごとの急性変動では未検証である。"
                "第六に、第 5 章の推定手法そのものが未検証の提案である。"
                "したがって現時点で臨床判断の根拠にしてはならない。")
lims = ["容積信号であり、圧ではない",
        "指の局所トーヌスか全身 SVR か未解決",
        "AGC は振幅を壊し、帯域制限は形態を壊す",
        "加齢交絡：いまの収縮か、もとの硬さか",
        "急性変動での SI・RI は未検証"]
for i, t in enumerate(lims):
    panel(s, 0.7, 2.0 + i * 0.85, 11.9, 0.72, fill=None, line="9A9A9A", line_pt=1.25,
          paras=[(t, 24, INK, False)], align=PP_ALIGN.LEFT)
textbox(s, 0.7, 6.26, 11.9, 0.42,
        [("本手法は未検証の提案であり、臨床判断の根拠にはしない", 24, RED, True)],
        space_after=0)

s = d.add("まとめ", 5,
          source="本資料は研究・教育目的の整理であり、個別の臨床判断を指示・保証するものではない",
          notes="まとめ。"
                "第一に、SI は反射波の時間、RI は反射波の高さを測る指標であり、"
                "それぞれ大動脈のスティフネスと末梢の小血管トーヌスに対応する。"
                "第二に、どちらも拡張期ピーク（反射波）を同定できることを前提にしており、"
                "高スティフネス例ではその前提が崩れる。周術期でいちばん評価したい集団で指標が壊れる。"
                "第三に、そこで発想を『点を探す』から『波を当てはめる』へ変える。"
                "PPG 一拍を複数のガウス関数の和としてモデル化し、"
                "残差二乗和を最小にするパラメータを反復計算で求める。"
                "第四に、逆問題は一意に解けないので、順序・時間窓・符号の制約と、"
                "加速度脈波から与える初期値で探索空間を狭める。"
                "検証は仮想被験者・公開データ・実機の三段で行い、検出成功率を事前登録する。"
                "第五に、得られた時間パラメータと振幅パラメータを二軸で読むことで、"
                "『末梢が開いたのか、血管が硬いのか』を分けて見られる可能性がある。"
                "ただし全体が仮説段階であることを最後にもう一度強調しておく。")
summary = [("SI は反射波の時間、RI は反射波の高さ", BLUE),
           ("どちらも反射波の同定を前提にしている", VERM),
           ("硬い血管ほど、その前提が壊れる", RED),
           ("点を探すのをやめ、波を当てはめる（既報）", TEAL),
           ("新規性は定義でなく、検証の条件の側にある", RED),
           ("読むのは絶対値ではなく、導入前からの Δ", GOLD)]
for i, (t, col) in enumerate(summary):
    panel(s, 0.7, 1.98 + i * 0.75, 11.9, 0.64, fill=None, line=col, line_pt=1.75,
          paras=[(t, 24, INK, True)], align=PP_ALIGN.LEFT)

# ================================================================ 参考文献
REFS1 = [
    "Allen J. Photoplethysmography and its application in clinical physiological measurement. Physiol Meas. 2007;28(3):R1-39. PMID 17322588",
    "Murray WB, Foster PA. The peripheral pulse wave: information overlooked. J Clin Monit. 1996;12(5):365-77. PMID 8934343",
    "Takazawa K, et al. Vasoactive agents and vascular aging by the second derivative of photoplethysmogram. Hypertension. 1998;32(2):365-70. PMID 9719069",
    "Chowienczyk PJ, et al. Photoplethysmographic assessment of pulse wave reflection. J Am Coll Cardiol. 1999;34(7):2007-14. PMID 10588217",
    "Millasseau SC, et al. Age-related increases in large artery stiffness by digital pulse contour analysis. Clin Sci. 2002;103(4):371-7. PMID 12241535",
    "Dawber TR, et al. Characteristics of the dicrotic notch of the arterial pulse wave in coronary heart disease. Angiology. 1973;24(4):244-55. PMID 4699520",
    "Awad AA, et al. The photoplethysmographic waveform and systemic vascular resistance. J Clin Monit Comput. 2007;21(6):365-72. PMID 17940842",
    "Rubins U. Finger and ear photoplethysmogram waveform analysis by fitting with Gaussians. Med Biol Eng Comput. 2008;46(12):1271-6. PMID 18855034",
    "Westerhof BE, et al. Quantification of wave reflection in the human aorta from pressure alone. Hypertension. 2006;48(4):595-601. PMID 16940207",
    "Kips JG, et al. Wave reflection and pulse transit time from the pressure waveform alone. Hypertension. 2009;53(2):142-9. PMID 19075098",
]
REFS2 = [
    "Yamada T, et al. Noninvasive continuous cardiac output using pulse wave transit time. Anesth Analg. 2012;115(1):82-7. PMID 22467885",
    "Goswami D, et al. A new two-pulse synthesis model for digital volume pulse signal analysis. Cardiovasc Eng. 2010;10(3):109-17. PMID 20734136",
    "Epstein S, et al. Numerical assessment of the stiffness index. Annu Int Conf IEEE EMBC. 2014;2014:1969-72. PMID 25570367",
    "Couceiro R, et al. Cardiovascular function from multi-Gaussian fitting of a finger photoplethysmogram. Physiol Meas. 2015;36(9):1801-25. PMID 26235798",
    "Grabovskis A, et al. Two-stage multi-Gaussian fitting of conduit artery photoplethysmography waveform. J Biomed Opt. 2015;20(3):035004. PMID 25751027",
    "Baruch MC, et al. Validation of the pulse decomposition analysis algorithm using central arterial blood pressure. Biomed Eng Online. 2014;13:96. PMID 25005686",
    "Wang A, et al. Gaussian modelling characteristics changes derived from finger photoplethysmographic pulses. Microvasc Res. 2018;117:15-21. PMID 28347756",
    "Park J, et al. Vascular aging estimation using photoplethysmogram waveform decomposition. JMIR Med Inform. 2022;10(3):e33439. PMID 35297776",
    "Tusman G, et al. Photoplethysmographic characterization of vascular tone mediated changes in arterial pressure. J Clin Monit Comput. 2019;33(5):815-24",
    "Coutrot M, et al. Noninvasive continuous detection of arterial hypotension during induction of anaesthesia. Br J Anaesth. 2019;122(5):605-12. PMID 30916032",
    "Aguet C, et al. Blood pressure monitoring during anesthesia induction using PPG morphology features. PLoS One. 2023;18(2):e0279252. PMID 36735652",
    "Lee QY, et al. Multivariate classification of systemic vascular resistance using photoplethysmography. Physiol Meas. 2011;32(8):1117-32. PMID 21693795",
    "Manoj R, et al. Arterial pressure pulse wave separation analysis using a multi-Gaussian decomposition model. Physiol Meas. 2022;43(5). PMID 35537402",
    "Charlton PH, et al. Modeling arterial pulse waves in healthy aging: a database for in silico evaluation. Am J Physiol. 2019;317(5):H1062-85. PMID 31442381",
    "Md Lazin Md Lazim MR, et al. Is Heart Rate a Confounding Factor for Photoplethysmography Markers? IJERPH. 2020;17(7):2591. PMID 32290168",
    "Suboh MZ, et al. Four derivative waveforms of photoplethysmogram for fiducial point detection. Front Public Health. 2022;10:920946. PMID 35844894",
    "Lee HC, et al. VitalDB, a high-fidelity multi-parameter vital signs database in surgical patients. Sci Data. 2022;9(1):279. PMID 35676300",
    "Goda MA, Charlton PH, Behar JA. pyPPG: a Python toolbox for photoplethysmography signal analysis. Physiol Meas. 2024;45(4). PMID 38478997",
    "Basso G, et al. A skewed-Gaussian model for pulse decomposition analysis of photoplethysmography. Physiol Meas. 2024;45(11). PMID 39577084",
    "Chen H, et al. PPG-derived arterial stiffness index and cardiovascular prevention (UK Biobank). J Clin Hypertens. 2025;27(5):e70058. PMID 40346852",
    "先行技術調査の全一覧（PICO・PMID・URL）は本リポジトリ PPG_wave_decomposition_prior_art.html を参照",
]
from deck_kawazoe import text_w_in as _tw, line_h_in as _lh

REF_BOX_W, REF_BOX_H, REF_SA = 12.15, 4.60, 6
ALL_REFS = REFS1 + REFS2
pages, cur, used = [], [], 0.0
for i, r in enumerate(ALL_REFS):
    txt = f"[{i + 1}] {r}"
    n = max(1, math.ceil(_tw(txt, 16) / REF_BOX_W))
    need = n * _lh(16) + REF_SA / 72.0
    if used + need > REF_BOX_H - 0.10 and cur:
        pages.append(cur)
        cur, used = [], 0.0
    cur.append(txt)
    used += need
if cur:
    pages.append(cur)

MARU = "①②③④⑤"
for idx, chunk in enumerate(pages):
    s = d.add(f"参考文献 {MARU[idx]}", None,
              source="PMID・URL は本リポジトリ各成果物の参考文献欄に収載（検証済み）",
              notes="本スライドの主張はすべてこれらの一次文献、または本リポジトリの既存レビューに由来する。"
                    "第 5 章の推定手法は、これら先行研究の手法を組み合わせた提案であり、"
                    "本プロジェクトとしての臨床検証は未了である。")
    textbox(s, 0.6, 1.9, REF_BOX_W, REF_BOX_H, [(t, 16, INK) for t in chunk],
            space_after=REF_SA, where="refs")

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "PPG_SI_RI_reflected_wave_slides.pptx")
d.save(OUT)
print(f"saved: {OUT}  ({len(d.prs.slides.__iter__.__self__._sldIdLst)} slides)")
if WARNINGS:
    print(f"\n--- build warnings ({len(WARNINGS)}) ---")
    for w in WARNINGS:
        print(" ", w)
else:
    print("build warnings: none")

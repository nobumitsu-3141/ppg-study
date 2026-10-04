#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""研究全体の流れのスライドを川副式書式で生成する（表紙・目標・結果の当てはめ・検証①の型別の表の 4 枚）。

位置づけ:
  スライド 2「目標」は研究前の設計（結果を入れない）。太字の仮説を、前提 2 つと検証 3 つで下から示す。
  スライド 3「結果の当てはめ」は同じ下から上の順に、各段へ**いまの結果**を載せたもの。
  スライド 4 は検証①（模型）の型別の表。

書式ルール（slide-format スキル）:
  - タイトル 44pt 太字・金 BF9000・黒縁取り 2.25pt・全スライド同位置・1 行。直下に金の下線（y=1.52in・8pt・全幅）
  - 本文は 22pt 以上（出典 16pt のみ例外）。1 行 1 論点。説明は**ノート**へ
  - 対比色はブルー 0072B2 × バーミリオン D55E00（＋ティール 00A8AA）。金は構造色として予約
  - 色だけで区別しない（判定札は文字と色の両方。未実行は破線）

判定札の定義（スライド 3）:
  支持＝事前に決めた規準を満たした／一部（弱い）＝一部の指標・型だけが満たした、または関連が弱い／未実行
接頭語: 文献＝文献の値／確定＝事前登録した方法・規準での結果／探索＝結果を見たあとに選んだ解析（判定には用いない）

段（CLAUDE.md §3）: A 段＝その手法が自分で採用した被験者だけ、B 段＝比べる全手法が採用した共通例、
  C 段＝採否を無視して全員。**スライド 3・4 の模型の数値は C 段**で、スライド上に毎回 1 行で注釈する。

使い方:
    python3 build_slides_flow.py --out flow_ja.pptx
    python3 build_slides_flow.py --selftest

数値の出どころ:
    検証①（模型）: docs/research/results/50_reservoir_bench_C14.txt の C2・C3 の C 段の行
        （Mac 1・4,374 名・2026-09-17。**このファイルは Mac 1 で未 commit のとき、この環境では読めない**。
        --selftest は無ければ照合を飛ばし、docs/manuscript/paper2/02_tables.md の表5・表6 と照合する）
    前提②: 50番 節C の C1（凍結版の採用率）、lab_log 追記32・34番の実機 20 例（SAP-3 §5 の表）
    検証②: docs/research/roadmap_v1.md §8（Gate 1）・§13.1（判別試験）、論文1（ΔPE +0.2%）
    前提①: docs/research/pda_literature_review.md 追補4〜6（要旨・検索の要約による確認が中心）
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

GOLD, BLACK, WHITE = "BF9000", "000000", "FFFFFF"
BLUE, VERM, TEAL = "0072B2", "D55E00", "00A8AA"
LGREY, DGREY, PALE, LINE, GREYTXT = "D9D9D9", "595959", "F2F2F2", "7F7F7F", "595959"
BLUE_PALE = "DCEBF5"
FONT = "メイリオ"
SW, SH = 13.333, 7.5
MIN_PT = 22.0
SRC_PT = 16.0

DATE = "2026-10-04"

# --------------------------------------------------------------- 数値（C 段・型3 など）
# 検証①の表（C 段）。(|ρ| の中央値, 規準を満たすか)。型 1・3・4・全例の順。
# 出どころ: 50_reservoir_bench_C14.txt の C2（ΔT × 大動脈PWV）・C3（RI × 末梢血管抵抗）の C 段の行。
TABLE = {
    "ΔT": {
        "凍結版": [(0.224, False), (0.207, False), (0.472, True), (0.205, False)],
        "改良版": [(0.221, False), (0.596, True), (0.530, True), (0.558, True)],
        "特徴点法": [(0.343, False), (0.430, True), (0.796, True), (0.710, True)],
    },
    "RI": {
        "凍結版": [(0.554, True), (0.184, False), (0.637, True), (0.171, False)],
        "改良版": [(0.514, True), (0.107, False), (0.926, True), (0.143, False)],
        "特徴点法": [(0.481, True), (0.550, True), (0.888, True), (0.504, True)],
    },
}
TYPE_HEAD = ["型1 切痕あり", "型3 変曲点のみ", "型4 無し", "全例"]

# スライド 3 の行（下から順。前提① が最下段）
CHIP = {"yes": ("支持", BLUE, WHITE), "part": ("一部", TEAL, BLACK),
        "weak": ("弱い", TEAL, BLACK), "no": ("不支持", VERM, WHITE),
        "todo": ("未実行", WHITE, GREYTXT)}

ROWS = [
    dict(tag="前提①", kind="前提", chip="part",
         design=("特徴点法の指標は", "参照基準と相関する"),
         result=("文献 SI×頸大腿PWV r 0.65", "文献 RI×SVR の単独報告は未確認")),
    dict(tag="前提②", kind="前提", chip="yes",
         design=("分解は切痕が無い", "波形でも指標を出せる"),
         result=("探索 採用率 型3 0.901・型4 0.952", "探索 実機 20 例で値が出る率 1.00")),
    dict(tag="検証①", kind="検証", chip="part",
         design=("模型で分解の指標は", "型別に真値と相関"),
         result=("確定 凍結版 ΔT 0.207・RI 0.184", "探索 改良版 ΔT 0.596・RI 0.107")),
    dict(tag="検証②", kind="検証", chip="weak",
         design=("麻酔データベースで", "参照値と相関する"),
         result=("確定 補正は精度を上げず ΔPE +0.2%", "探索 RI×SVR +0.098・血圧を追う")),
    dict(tag="検証③", kind="検証", chip="todo",
         design=("麻酔患者で前向きに", "参照基準と相関する"),
         result=("論文3 で実機の同定を確認してから", "頸大腿PWV を参照に事前登録する")),
]

# --------------------------------------------------------------- ノート
NOTES_AIM = (
    "研究の目標（研究前の設計として書く。結果はこの後のスライドで当てはめる）。\n"
    "仮説（太字）: 分解法（PDA）由来の指標は真値と関連する。具体には RI が末梢血管抵抗（SVR）と、SI（＝身長／ΔT）が脈波伝播速度（PWV）と相関する。"
    "しかも特徴点法が指標を出せない波形（拡張期ピークや切痕が無い型）でも成り立つ。\n"
    "前提①（文献）: 特徴点法（輪郭・2 次微分）で出した SI・RI は参照基準と相関する。SI × 頸大腿PWV は r 0.6〜0.7（Millasseau 2002）。"
    "RI は血管作動薬への応答（Millasseau 2003・Chowienczyk 1999）で、独立に測った SVR との相関の報告は無い。"
    "→ 前提としては SI 側が強く、RI × SVR は仮説の弱い側であることを先に書いておく。\n"
    "前提②（文献）: 分解は実測波形をよく再現し（Tigges 2017・Fleischhauer 2020・Basso 2024）、切痕や拡張期ピークが無い波形からも成分波を取り出して指標を出せる。"
    "分解由来の指標と特徴点法の指標は測る場所が違う別の量であり（Goswami 2010）、一致する必要は無い。"
    "だから妥当性は特徴点法との一致ではなく、真値に対して直接に確かめる（検証①）。特徴点法は参照ではなく比較の基準（同じ規準でどこまで届くか）。\n"
    "検証①（模型・in silico）: 真値既知の 1 次元血行動態モデル（Charlton 2019 の PWDB 4,374 名）。年齢を固定した層内の Spearman 順位相関で、"
    "|ρ| の中央値 ≥ 0.30 かつ全層で予測の向き（ΔT × 大動脈PWV は負、RI × 末梢血管抵抗は正）を規準とする。"
    "波形の型（切痕あり／変曲点のみ／いずれも無し）で層別し、特徴点法が使えない型で分解が真値を追うかを見る。指標が出る割合（同定率）も仮説の価値の一部。"
    "陽性対照はモデルの脈波到達時間 × 大動脈PWV。規準は結果を見る前に凍結する。\n"
    "検証②（臨床データベース）: 麻酔中の公開データベース（VitalDB）。参照値は心拍出量モニタ由来の SVR と血圧。"
    "参照が圧波形に依存する（独立でない）ことを先に認め、前提検証（指標が血圧を超えて説明するか）を解釈の規準に置く。同定率と再現性も報告する。\n"
    "検証③（前向き）: 麻酔患者で、参照基準（導入前の頸大腿PWV。心臓外科なら熱希釈の SVR）に対する相関を事前登録して確かめる。"
    "被験者内の解析では血圧の調整を事前指定する。\n"
    "用語: 真値＝模型の入力値（in silico でのみ使う）。参照基準＝in vivo の測定値（頸大腿PWV・熱希釈 SVR）。"
    "関連＝年齢層内の順位相関（Spearman）。妥当性＝基準関連妥当性（前提①・検証①〜③）。分解と特徴点法の一致（併存的妥当性）は求めない。"
    "『再現する』は当てはまりの良さであって妥当性ではない。"
)

NOTES_RESULT = (
    f"結果の当てはめ（{DATE} 時点）。スライド 2（目標）と同じ下から上の順に、各段の結果を載せた。\n"
    "判定札: 支持＝事前に決めた規準を満たした／一部・弱い（ティール）＝一部の指標・型だけが満たした、または関連が弱い／未実行（破線）。\n"
    "接頭語: 文献＝文献の値／確定＝事前登録した方法・規準での結果／探索＝結果を見たあとに選んだ解析（判定には用いない）。\n"
    "段: 検証①の数値は型3の C 段（C 段＝採否を無視した全員）。A 段＝その手法が自分で採用した被験者だけ、B 段＝比べる全手法が採用した共通例。\n"
    "答え: 仮説（分解法の RI×SVR・SI×PWV）は一部だけ。強い部分は SI（ΔT）の型3・改良版（探索）で、RI×SVR は模型でも麻酔データベースでも示せていない。\n"
    "\n"
    "前提①（文献。一部）: SI×頸大腿PWV は r 0.65（Millasseau 2002・健常〜混合 87 名。Hellqvist 2024 が引く既報は 0.58〜0.66）。"
    "この r は年齢をまたいだ相関で、我々の規準（年齢層内の順位相関）とは別の量。治療中の高血圧では 2 次微分由来の指標と頸大腿PWV の相関は 0.24 以下"
    "（Hashimoto 2002・294 名）。RI は血管作動薬への応答（Millasseau 2003・Chowienczyk 1999・Coutrot 2019 の対 MAP r 0.73）で、独立に測った SVR との"
    "単変量の相関を主結果にした報告は見つかっていない（追補6。要旨と検索の要約による確認で、全文は未確認）。"
    "→ SI は支持、RI×SVR は文献の裏づけが無い。\n"
    "前提②（探索。支持）: 凍結版の採用率（収束検算を通った割合。分母は全員）は 型3 0.901・型4 0.952・全例 0.923（50番 C1）。"
    "実機（VitalDB 20 例・360 ウィンドウ・34番）で分解由来の値が有限になった割合は ≈1.00、特徴点法は 0.64、凍結版の採択率は 0.778。"
    "ただし「値が出る」ことと「値が真値を追う」ことは別で、後者は検証①で測る。第2版（採否を型1 だけに当てる版）の採用は 2/4,374（歪みガウス）・103（ガンマ）と少ない。\n"
    "検証①（模型。一部）: PWDB 4,374 名・年齢層内 Spearman・規準は |ρ| の中央値 ≥ 0.30 かつ全層で予測の向き。型3（変曲点のみ・3,378 名）の C 段:"
    " 凍結版 ΔT 0.207（6/6・不成立）・RI 0.184（4/6・不成立）、改良版（拍長の 0.65 倍で打ち切り）ΔT 0.596（6/6・成立）・RI 0.107（6/6・不成立）、"
    "同梱の特徴点法 ΔT 0.430・RI 0.550（比較の基準）。事前登録の判定（全例）は凍結版 ΔT 0.223・RI 0.207（A 段）でいずれも不成立。"
    "型別の層別と改良版は事後（表5・表6）。改良版は 14 通りから選んだので楽観側で、A 段 0.828 は採用率 0.413 の拍だけの値、C 段 0.596 が妥当。"
    "雑音（拍の振幅の 1%・2%）を足しても ΔT 0.486・0.454（6/6）を保つが、RI は B 段（3 型の共通例）でも 0.266・0.168 に落ちる。"
    "型1 の ΔT は特徴点法でも不成立（型1 の層内の PWV の幅が型3 の 0.08 倍。範囲の制限）。\n"
    "検証②（VitalDB・論文1。弱い）: 確定＝論文1（862 例・SAP v0.3 凍結・事前登録）の主要評価で、分解由来の SI・RI による PWTT 較正定数の補正は"
    "精度を改善しなかった（ΔPE +0.2% [+0.1, +0.4]・事前の無益性基準に該当）。前提検証で指標が ΔPWTT の変動を説明する割合は r² 0.044（ΔMAP% 単独 0.139）。"
    "探索＝研究1c C-2（副次・主解析にしない）で RI×SVR の症例内順位相関の中央値 +0.098（204 例・符号検定 p=1.7e-05・SI×SVR は無関連）。"
    "判別試験（37・38番・203 例・43,217 ウィンドウ）で凍結版 RI は ρ(ΔSVR%) +0.031 [−0.023, +0.094]・ρ(ΔMAP%) +0.075 [+0.008, +0.131] で血圧側。"
    "参照の SVR（EV1000）は圧波形由来で独立でないので、陽性でも証明にならない設計。→ 弱い関連はあるが、血圧と区別できない。"
    "札を「不支持」でなく「弱い」にしたのは、Gate 1 の事前の判定が「関連あり（RI のみ・弱い）」だったことによる。\n"
    "検証③（未実行）: 論文3（SAP-3 を凍結してから VitalDB 840 例。規準は同定率の症例中央値 ≥ 0.70 かつ lag-1 自己相関 ≥ 0.30）で改良版が実機の波形で"
    "同定できると分かってから、新しい事前登録で着手する。参照基準は導入前の頸大腿PWV（被験者間）を主、心臓外科なら熱希釈 SVR（被験者内。血圧の調整を事前指定）を副とする。"
    "20 例のパイロットでは特徴点法 ΔT の同定率が 0.67 で規準 0.70 に届かず、平均拍の 34.9% が型4（32番）。\n"
    "数値の出どころ: 50_reservoir_bench_C14.txt（Mac 1・2026-09-17。リポジトリへは未 commit）・論文2 表1・表5・表6・表6c・roadmap_v1.md §8・§13.1・32・34番。"
)

NOTES_TABLE = (
    f"検証①（模型）の型別の表（{DATE} 時点）。PWDB 4,374 名（型1 891・型3 3,378・型4 105）。年齢層内 Spearman 順位相関の |ρ| の中央値。\n"
    "段: すべて C 段（採否を無視した全員）。A 段（その手法が自分で採用した被験者だけ）は凍結版 ΔT 全例 0.223・RI 0.207（事前登録の判定。いずれも不成立）、"
    "改良版は型3 の ΔT 0.828・RI 0.530（採用率 0.413 の拍だけ）。B 段（凍結版・改良版・微分領域の 3 型が採用した共通例・型3 732 名）では改良版 ΔT 0.630・RI 0.381。\n"
    "成立＝|ρ| の中央値 ≥ 0.30 かつ評価できた全層で予測の向き（括弧の層の数は省略）。型4 は 105 名で 3 層しか評価できない。\n"
    "読み方: ① 凍結版は型3 で ΔT・RI とも不成立（事前登録の全例の判定と同じ向き）。② 改良版（拍長の 0.65 倍で打ち切り）は型3 の ΔT を 0.207 → 0.596 に上げ、"
    "同梱の特徴点法（0.430）を上回る。RI は 0.107 で届かない。③ 型1 の ΔT は特徴点法でも不成立（0.343・4/6）で、型1 の層内の PWV の幅が型3 の 0.08 倍と狭い"
    "（表5b。範囲の制限）。④ 凍結版 RI は型1 で成立（0.554）。切痕が極値として残る型では第2成分の振幅が反射係数を追う。"
    "⑤ 型4 は 3 層だけの評価で、凍結版・改良版とも成立しているが、特徴点法は同梱の検出器による値で、我々の検出器は型4 を見つけられない。\n"
    "留保: 改良版は 14 通りの当てはめから事後に選んだので楽観側。雑音（拍の振幅の 1%・2%）を足した型3 の ΔT は 0.486・0.454（6/6）、"
    "RI は B 段でも 0.266・0.168。1 次微分の領域で当てた版は雑音で 0.337 に落ち、通過率 0.290 まで下がる。改良した当てはめを主解析に用いるには新たな事前登録が要る。\n"
    "数値の出どころ: 50_reservoir_bench_C14.txt の C2・C3（Mac 1・2026-09-17。未 commit）。型別の凍結版と特徴点法は論文2 表5、型3 の三者は表6 と一致。"
)


# --------------------------------------------------------------- 部品
def _set_font(run, pt, bold=False, color=BLACK, outline=False):
    run.font.size = Pt(pt)
    run.font.bold = bold
    run.font.name = FONT
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ln", "a:solidFill", "a:latin", "a:ea"):
        for el in rPr.findall(qn(tag)):
            rPr.remove(el)
    idx = 0
    if outline:
        ln = etree.SubElement(rPr, qn("a:ln"), w=str(int(2.25 * 12700)))
        sf = etree.SubElement(ln, qn("a:solidFill"))
        etree.SubElement(sf, qn("a:srgbClr"), val=BLACK)
        rPr.remove(ln)
        rPr.insert(idx, ln)
        idx += 1
    sf = etree.SubElement(rPr, qn("a:solidFill"))
    etree.SubElement(sf, qn("a:srgbClr"), val=color)
    rPr.remove(sf)
    rPr.insert(idx, sf)
    lat = etree.SubElement(rPr, qn("a:latin"), typeface=FONT)
    rPr.remove(lat)
    rPr.append(lat)
    ea = etree.SubElement(rPr, qn("a:ea"), typeface=FONT)
    rPr.remove(ea)
    rPr.append(ea)


def title_and_rule(slide, text):
    t = slide.shapes.title
    t.left, t.top, t.width, t.height = Inches(0.55), Inches(0.35), Inches(9.3), Inches(0.95)
    tf = t.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = text
    _set_font(r, 44, bold=True, color=GOLD, outline=True)
    line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(0), Inches(1.52),
                                      Inches(SW), Inches(1.52))
    line.line.color.rgb = RGBColor.from_string(GOLD)
    line.line.width = Pt(8)


def text_box(slide, x, y, w, h, lines, pt=22, bold=False, color=BLACK, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.MIDDLE, space_after=4):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True      # 折り返し無効だと LibreOffice が中央寄せに描く。幅は lint の推定で余裕を見てある
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    for i, (txt, b, c) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        r = p.add_run()
        r.text = txt
        _set_font(r, pt, bold=bold if b is None else b, color=c or color)
    return tb


def box(slide, x, y, w, h, lines, fill, line, pt=22, bold=False, color=BLACK,
        align=PP_ALIGN.LEFT, dashed=False, line_w=1.25, line_spacing=None):
    """角丸の箱。lines は文字列か文字列のリスト（段落ごと・段落の後ろの空きは 0）。"""
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = RGBColor.from_string(fill)
    s.line.color.rgb = RGBColor.from_string(line)
    s.line.width = Pt(line_w)
    if dashed:
        s.line.dash_style = MSO_LINE.DASH
    s.shadow.inherit = False
    tf = s.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.1)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    if isinstance(lines, str):
        lines = [lines]
    for i, txt in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(0)
        if line_spacing:
            p.line_spacing = line_spacing
        r = p.add_run()
        r.text = txt
        _set_font(r, pt, bold=bold, color=color)
    return s


def arrow_up(slide, x, y_from, y_to, color=BLACK, width=2.25):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y_from),
                                   Inches(x), Inches(y_to))
    c.line.color.rgb = RGBColor.from_string(color)
    c.line.width = Pt(width)
    ln = c.line._get_or_add_ln()
    etree.SubElement(ln, qn("a:tailEnd"), type="triangle", w="med", len="med")
    return c


def set_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def source_line(slide, text, y=7.08):
    text_box(slide, 0.5, y, 12.4, 0.36, [(text, False, BLACK)], pt=SRC_PT, anchor=MSO_ANCHOR.TOP)


# --------------------------------------------------------------- スライド
def slide_cover(prs):
    s = prs.slides.add_slide(prs.slide_layouts[5])
    title_and_rule(s, "研究の目標と結果")
    text_box(s, 0.55, 2.2, 12.2, 1.3,
             [("分解法（PDA）の指標は真値と関連するか", True, BLACK),
              ("研究前の設計と、いまの結果", True, BLACK)], pt=28, space_after=2)
    text_box(s, 0.55, 3.7, 12.2, 0.6, [(f"{DATE}　川副靖晃", False, BLACK)], pt=22)
    return s


def tag_style(kind):
    return (LGREY, BLACK) if kind == "前提" else (DGREY, WHITE)


def slide_aim(prs):
    s = prs.slides.add_slide(prs.slide_layouts[5])
    title_and_rule(s, "PDA指標は真値と関連する")
    text_box(s, 0.55, 1.62, 12.2, 0.42,
             [("仮説（RI × SVR・SI × PWV）。切痕の無い波形でも ― 下から示す", True, BLACK)], pt=24)
    aim_steps = [
        ("前提①", "前提", "特徴点法の指標は参照基準と相関する"),
        ("前提②", "前提", "分解は切痕が無い波形でも指標を出せる"),
        ("検証①", "検証", "模型で分解の指標は型別に真値と相関"),
        ("検証②", "検証", "麻酔データベースで参照値と相関する"),
        ("検証③", "検証", "麻酔患者で前向きに参照基準と相関する"),
    ]
    n = len(aim_steps)
    box_h, gap, y_top = 0.70, 0.18, 2.2
    tag_x, tag_w, step_x, step_w = 0.55, 1.4, 2.1, 6.45
    ys = []
    for i, (tag, kind, txt) in enumerate(aim_steps):
        y = y_top + (n - 1 - i) * (box_h + gap)
        ys.append(y)
        fill, col = tag_style(kind)
        box(s, tag_x, y, tag_w, box_h, tag, fill, fill, bold=True, color=col, align=PP_ALIGN.CENTER)
        box(s, step_x, y, step_w, box_h, txt, PALE, LINE)
    xc = step_x + step_w / 2
    for i in range(n - 1):
        arrow_up(s, xc, ys[i], ys[i + 1] + box_h)
    rx, rw = 8.75, 4.1
    box(s, rx, y_top, rw, 0.62, "用語と規準", GOLD, GOLD, bold=True, align=PP_ALIGN.CENTER)
    text_box(s, rx, y_top + 0.72, rw, 3.2,
             [("真値＝模型の入力値", False, BLACK), ("参照基準＝頸大腿PWV", False, BLACK),
              ("参照基準＝熱希釈の SVR", False, BLACK), ("関連＝層内の順位相関", False, BLACK),
              ("規準 |ρ| ≥ 0.30", False, BLACK), ("全層で予測の向き", False, BLACK)],
             anchor=MSO_ANCHOR.TOP)
    box(s, rx, y_top + 4.05, rw, 0.7, "前提 → 仮説 → 検証", WHITE, LINE, bold=True,
        align=PP_ALIGN.CENTER)
    source_line(s, "用語: 特徴点法＝輪郭・2 次微分の特徴点から指標を出す方法。分解法（PDA）＝成分波の和を当てて指標を出す方法。",
                y=7.0)
    set_notes(s, NOTES_AIM)
    return s


# スライド 3 の座標（Meiryo の行高が大きいので、2 行の箱は 0.88in とする）
R_H, R_GAP, R_Y0 = 0.84, 0.05, 2.5
R_LS = 0.9      # 2 行の箱の行間（メイリオの行高が大きく、1.0 だと 2 行が 0.92in になるため）
X_ARROW, X_TAG, W_TAG = 0.27, 0.45, 1.3
X_DES, W_DES = 1.85, 3.55
X_CHIP, W_CHIP = 5.5, 1.2
X_RES, W_RES = 6.8, 6.1


def slide_result(prs):
    s = prs.slides.add_slide(prs.slide_layouts[5])
    title_and_rule(s, "PDA指標は真値と関連するか")
    text_box(s, 0.45, 1.58, 12.4, 0.46,
             [("答え：一部のみ。強いのは SI（ΔT）の型3・改良版（探索）", True, BLACK)], pt=22)
    text_box(s, 0.45, 2.02, 12.4, 0.46,
             [("確定＝事前登録　探索＝事後　検証①は型3・C 段（採否を無視した全員）", False, BLACK)], pt=22)
    n = len(ROWS)
    for i, row in enumerate(ROWS):
        y = R_Y0 + (n - 1 - i) * (R_H + R_GAP)
        fill, col = tag_style(row["kind"])
        box(s, X_TAG, y, W_TAG, R_H, row["tag"], fill, fill, bold=True, color=col, align=PP_ALIGN.CENTER)
        box(s, X_DES, y, W_DES, R_H, list(row["design"]), PALE, LINE, line_spacing=R_LS)
        word, cfill, ccol = CHIP[row["chip"]]
        todo = row["chip"] == "todo"
        box(s, X_CHIP, y, W_CHIP, R_H, word, cfill, LINE if todo else cfill, bold=True, color=ccol,
            align=PP_ALIGN.CENTER, dashed=todo)
        box(s, X_RES, y, W_RES, R_H, list(row["result"]), WHITE, "BFBFBF", line_spacing=R_LS)
    y_bottom = R_Y0 + n * R_H + (n - 1) * R_GAP
    arrow_up(s, X_ARROW, y_bottom - 0.05, R_Y0 + 0.05)
    source_line(s, "出典: 論文2 表1・表5・表6・表6c、論文1、32・34・37・38番、文献 追補4〜6", y=7.04)
    set_notes(s, NOTES_RESULT)
    return s


def cell_text(cell, lines, pt=22, bold=False, color=BLACK, align=PP_ALIGN.CENTER, fill=None):
    cell.margin_left = cell.margin_right = Inches(0.05)
    cell.margin_top = cell.margin_bottom = Inches(0.02)
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    if fill:
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor.from_string(fill)
    tf = cell.text_frame
    tf.word_wrap = False
    if isinstance(lines, str):
        lines = [lines]
    for i, txt in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(0)
        r = p.add_run()
        r.text = txt
        _set_font(r, pt, bold=bold, color=color)


def slide_table(prs):
    s = prs.slides.add_slide(prs.slide_layouts[5])
    title_and_rule(s, "検証①：型別の結果")
    rows_def = [(idx, m) for idx in ("ΔT", "RI") for m in ("凍結版", "改良版", "特徴点法")]
    n_rows, n_cols = 1 + len(rows_def), 5
    x0, y0, w_lab, w_num, row_h = 0.5, 1.72, 2.3, 2.5, 0.52
    gf = s.shapes.add_table(n_rows, n_cols, Inches(x0), Inches(y0),
                            Inches(w_lab + 4 * w_num), Inches(row_h * n_rows))
    tbl = gf.table
    tbl.first_row = False
    tbl.horz_banding = False
    tbl.columns[0].width = Inches(w_lab)
    for c in range(1, n_cols):
        tbl.columns[c].width = Inches(w_num)
    for r in range(n_rows):
        tbl.rows[r].height = Inches(row_h)
    cell_text(tbl.cell(0, 0), "指標・方法", bold=True, fill=DGREY, color=WHITE)
    for c, head in enumerate(TYPE_HEAD, start=1):
        cell_text(tbl.cell(0, c), head, bold=True, fill=DGREY, color=WHITE)
    for r, (idx, m) in enumerate(rows_def, start=1):
        label = f"{idx} {m}"
        cell_text(tbl.cell(r, 0), label, bold=True, fill=LGREY if idx == "ΔT" else "E8E8E8",
                  align=PP_ALIGN.LEFT)
        for c, (val, ok) in enumerate(TABLE[idx][m], start=1):
            word = "成立" if ok else "不成立"
            cell_text(tbl.cell(r, c), f"{val:.3f} {word}", bold=ok, fill=BLUE_PALE if ok else WHITE)
    y_after = y0 + row_h * n_rows
    text_box(s, 0.5, y_after + 0.12, 12.4, 0.5,
             [("型3 では ΔT だけが 不成立 → 成立（改良版）。RI は届かない", True, BLACK)], pt=24)
    text_box(s, 0.5, y_after + 0.68, 12.4, 0.46,
             [("C 段＝採否を無視した全員　成立＝|ρ| ≥ 0.30 かつ全層で予測の向き", False, BLACK)], pt=22)
    text_box(s, 0.5, y_after + 1.12, 12.4, 0.46,
             [("型4＝いずれも無し（105 名・3 層）　改良版＝0.65T 打ち切り（探索）", False, BLACK)], pt=22)
    source_line(s, "出典: 論文2 表5・表6、50番 節C（PWDB 4,374 名）")
    set_notes(s, NOTES_TABLE)
    return s


def build(out):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(SW), Inches(SH)
    slide_cover(prs)
    slide_aim(prs)
    slide_result(prs)
    slide_table(prs)
    prs.save(out)
    return out


# --------------------------------------------------------------- 検査


def _banned_terms():
    """用語検査器（analysis/scripts/check_terminology.py）の禁止語の表を読む。

    禁止語の一覧をこの台本に写さない（写すと検査器がこの行を禁止語の使用と数える）。
    検査器が無い機械では None を返し、自己検査はこの項目を飛ばす。
    """
    import importlib.util
    path = os.path.join(REPO, "analysis", "scripts", "check_terminology.py")
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location("check_terminology", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.BANNED


def _all_runs(prs):
    """(スライド番号, 図形の最初の文字, 文字の大きさ pt, 文字) を返す。表のセルも含む。"""
    out = []
    for si, sl in enumerate(prs.slides, start=1):
        for sp in sl.shapes:
            tfs = []
            if sp.has_text_frame:
                tfs.append(sp.text_frame)
            if getattr(sp, "has_table", False) and sp.has_table:
                for row in sp.table.rows:
                    for cell in row.cells:
                        tfs.append(cell.text_frame)
            for tf in tfs:
                head = tf.text.strip()[:12]
                for p in tf.paragraphs:
                    for r in p.runs:
                        out.append((si, head, r.font.size.pt if r.font.size else None, r.text))
    return out


def _units(text):
    u = 0.0
    for ch in text:
        o = ord(ch)
        if ch == " ":
            u += 0.30
        elif o <= 0x24F or 0x2080 <= o <= 0x208E:
            u += 0.56
        else:
            u += 1.0
    return u


def selftest():
    fails = []

    def rep(name, cond, detail=""):
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}  {detail}")
        if not cond:
            fails.append(name)

    print("build_slides_flow 自己検査")
    with tempfile.TemporaryDirectory() as td:
        out = build(os.path.join(td, "flow.pptx"))
        prs = Presentation(out)
        runs = _all_runs(prs)
        rep("4 枚（表紙・目標・結果の当てはめ・検証①の表）", len(prs.slides) == 4, f"{len(prs.slides)} 枚")
        small = [(si, h, pt) for si, h, pt, _t in runs if pt is not None and pt < MIN_PT]
        bad = [x for x in small if not (abs(x[2] - SRC_PT) < 0.01 and x[1].startswith(("出典", "用語")))]
        rep("22pt 未満の文字は出典・用語の 16pt だけ", not bad, f"22pt 未満 {len(small)} 件・規則外 {bad[:3]}")
        nosize = [x for x in runs if x[2] is None and x[3].strip()]
        rep("文字の大きさが未指定の文字が無い", not nosize, f"{len(nosize)} 件")
        # タイトルは 44pt で 1 行（メイリオの推定幅 ×1.12 が箱の幅 9.3in に収まる）
        wide = []
        for si, sl in enumerate(prs.slides, start=1):
            t = sl.shapes.title.text_frame.text
            w_in = _units(t) * 44 / 72 * 1.12
            if w_in > 9.3 - 0.1:
                wide.append((si, t, round(w_in, 2)))
        rep("タイトルが 1 行に収まる（推定幅 9.2in 以内）", not wide, f"超過 {wide}")
        rep("目標・結果・表のスライドにノートがある", all(
            len(prs.slides[i].notes_slide.notes_text_frame.text) > 300 for i in (1, 2, 3)),
            "ノートの長さ " + "・".join(str(len(prs.slides[i].notes_slide.notes_text_frame.text)) for i in (1, 2, 3)))
        alltext = "\n".join(t for _si, _h, _pt, t in runs) + NOTES_AIM + NOTES_RESULT + NOTES_TABLE
        banned = _banned_terms()
        if banned is None:
            print("  （用語検査器が無いので禁止語の確認は飛ばした）")
        else:
            hit = [t for t, _alt, allow in banned
                   if t in alltext and not (allow and re.sub(allow, "", alltext).find(t) < 0)]
            rep("禁止語（造語・比喩。検査器の表）が無い", not hit, f"検出 {hit}（表 {len(banned)} 語）")
        # 結果スライドの数値が TABLE・ROWS と食い違わない
        res_text = "\n".join(t for si, _h, _pt, t in runs if si == 3)
        t3 = TABLE["ΔT"]["凍結版"][1][0], TABLE["RI"]["凍結版"][1][0], TABLE["ΔT"]["改良版"][1][0], TABLE["RI"]["改良版"][1][0]
        rep("スライド 3 の検証①の数値が表（スライド 4）の型3 の列と一致する",
            all(f"{v:.3f}" in res_text for v in t3), f"型3 の 4 値 {t3}")
        rep("判定札の 4 種がそろい、未実行は破線で描く",
            {CHIP[r['chip']][0] for r in ROWS} == {"一部", "支持", "弱い", "未実行"}
            and any(r["chip"] == "todo" for r in ROWS), "支持・一部・弱い・未実行")
        # 表の成立の印が規則どおり（|ρ| ≥ 0.30）。層の向きは数えられないので、0.30 未満が成立でないことだけ
        viol = [(i, m, v) for i in TABLE for m in TABLE[i] for v, ok in TABLE[i][m] if ok and v < 0.30]
        rep("表で成立の印が付いた値はすべて |ρ| ≥ 0.30", not viol, f"違反 {viol}")
        # 論文2 の表5・表6 と照合（原稿が無い機械では飛ばす）
        md = os.path.join(REPO, "docs", "manuscript", "paper2", "02_tables.md")
        if os.path.exists(md):
            txt = open(md, encoding="utf-8").read()
            t6 = txt[txt.index("## 表6　"):txt.index("## 表6b")]
            need6 = ["0.207（6/6）", "0.184（4/6）", "0.596（6/6）", "0.107（6/6）", "0.430（6/6）", "0.550（6/6）"]
            miss6 = [k for k in need6 if k not in t6]
            rep("型3 の 6 値が論文2 表6 にある", not miss6, f"欠け {miss6}")
            t5 = txt[txt.index("## 表5　"):txt.index("## 表5b")]
            need5 = ["0.343（4/6）", "0.224（4/6）", "0.554（6/6）", "0.796（3/3）", "0.472（3/3）", "0.637（3/3）",
                     "0.481（6/6）", "0.888（3/3）"]
            miss5 = [k for k in need5 if k not in t5]
            rep("型1・型4 の凍結版と特徴点法の 8 値が論文2 表5 にある", not miss5, f"欠け {miss5}")
        else:
            print("  （論文2 の表が無いので表5・表6 との照合は飛ばした）")
        # Mac 1 の結果ファイルがあれば C2・C3 の C 段の行と照合する
        res = os.path.join(REPO, "docs", "research", "results", "50_reservoir_bench_C14.txt")
        if os.path.exists(res):
            body = open(res, encoding="utf-8").read()
            miss = []
            for idx, sect in (("ΔT", "C2."), ("RI", "C3.")):
                blk = body[body.index(sect):]
                blk = blk[:blk.index("出典:")]
                for m, key in (("凍結版", "(0) 凍結版本体 C"), ("改良版", "(6b) 0.65T C"),
                               ("特徴点法", "（参考）同梱の特徴点 C")):
                    line = next(ln for ln in blk.splitlines() if ln.strip().startswith(key))
                    vals = re.findall(r"(\d\.\d{3})（", line)
                    exp = [f"{v:.3f}" for v, _ok in TABLE[idx][m]]
                    if vals[:4] != exp:
                        miss.append((idx, m, vals[:4], exp))
            rep("表の 24 値が 50_reservoir_bench_C14.txt の C2・C3（C 段）と一致する", not miss, f"不一致 {miss}")
        else:
            print("  （50_reservoir_bench_C14.txt が無い［Mac 1 で未 commit］ので結果ファイルとの照合は飛ばした）")
    print("\n自己検査: " + ("通過" if not fails else f"失敗 {len(fails)} 件"))
    return 0 if not fails else 1


def main():
    ap = argparse.ArgumentParser(description="研究全体の流れのスライドを作る（目標・結果の当てはめ・検証①の表）")
    ap.add_argument("--out", default=os.path.join(HERE, "flow_ja.pptx"), help="出力する pptx（既定は追跡外）")
    ap.add_argument("--selftest", action="store_true", help="組んでから自分で確かめる")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())
    print("saved", build(args.out))


if __name__ == "__main__":
    main()

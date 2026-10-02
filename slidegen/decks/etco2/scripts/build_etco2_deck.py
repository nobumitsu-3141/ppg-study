#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EtCO2 deck builder. Assembles the full ~60-slide 川副式 deck from content/*.md
(transcribed below as Python data — the .md files are the source of truth; this
script mirrors them exactly) using decklib factories and figlib-generated PNGs.
NOTE: keep figlib (hex colors) and decklib (RGBColor) in separate namespaces —
see scripts/test_smoke.py."""
import figlib as F
from decklib import *

FIG = F.OUTDIR
def fp(code):
    return f"{FIG}/{code}.png"

TEMPLATE = "_template_kawazoe.pptx"
OUT = "../out/EtCO2モニタリング.pptx"

# ---------------------------------------------------------------- refs -----
U = {
    "jaffe08": "https://pubmed.ncbi.nlm.nih.gov/18713900/",
    "smalhout": None,
    "tinker": "https://pubmed.ncbi.nlm.nih.gov/2802207/",
    "kodali13": "https://pubmed.ncbi.nlm.nih.gov/23221862/",
    "kodali13b": "https://doi.org/10.1097/ALN.0b013e318278c8b6",
    "kodali13c": "https://pubmed.ncbi.nlm.nih.gov/23221867/",
    "sandberg24": "https://www.nature.com/articles/s41598-024-75808-0",
    "severinghaus61": "https://pubmed.ncbi.nlm.nih.gov/13698064/",
    "verscheure16": "https://pubmed.ncbi.nlm.nih.gov/27334879/",
    "verscheure16b": "https://doi.org/10.1186/s13054-016-1377-3",
    "geers00": "https://pubmed.ncbi.nlm.nih.gov/10747205/",
    "nunn60": "https://pubmed.ncbi.nlm.nih.gov/14427915/",
    "west64": "https://pubmed.ncbi.nlm.nih.gov/14195584/",
    "bs92": "https://pubmed.ncbi.nlm.nih.gov/1643689/",
    "bs92b": "https://doi.org/10.1007/BF03008330",
    "bsphilip00": "https://doi.org/10.1097/00000539-200010000-00038",
    "fowler48": "https://doi.org/10.1152/ajplegacy.1948.154.3.405",
    "grmec02": "https://doi.org/10.1007/s00134-002-1290-x",
    "deitch10": "https://doi.org/10.1016/j.annemergmed.2009.07.030",
    "gudipati88": "https://doi.org/10.1161/01.cir.77.1.234",
    "larach10": "https://doi.org/10.1213/ANE.0b013e3181c6b9b2",
    "fletcher84": "https://doi.org/10.1093/bja/56.2.109",
    "jaffe17": "https://doi.org/10.1007/s10877-016-9830-z",
    "mirski07": "https://doi.org/10.1097/00000542-200701000-00026",
    "glahn10": "https://doi.org/10.1093/bja/aeq243",
    "cantineau96": "https://doi.org/10.1097/00003246-199605000-00011",
    "merchant20": "https://doi.org/10.1161/CIR.0000000000000918",
    "waugh11": "https://doi.org/10.1016/j.jclinane.2010.08.012",
    "verschuren10": "https://doi.org/10.1111/j.1538-7836.2009.03667.x",
    "klopfenstein08": "https://doi.org/10.1111/j.1399-6576.2007.01568.x",
    "frerk15": "https://doi.org/10.1093/bja/aev371",
    "bhende95": "https://pubmed.ncbi.nlm.nih.gov/7862479/",
}

# ---------------------------------------------------- front-matter data ----
# concise one-line chapter labels for menu/divider (long forms wrapped & overlapped)
FULL = ["歴史 ― CO₂ 計測の歩み",
        "成り立ち ― 測定原理",
        "基礎 ― CO₂ の生理",
        "正常カプノグラム",
        "麻酔中の見どころ",
        "異常所見 ― 波形アトラス",
        "対応 ― 異常への初動",
        "特殊な使用例"]
SHORT = ["歴史", "原理", "生理", "正常", "術中", "異常", "対応", "特殊"]
MENUSUB = ["赤外CO₂計測の誕生と、標準モニタ化の歴史",
           "赤外吸収の原理・メイン/サイドストリーム・誤差",
           "VCO₂ と VA・a–ET 較差・死腔と V/Q・“3軸”",
           "時間軸の4相と α/β 角、容量軸カプノグラフィ",
           "挿管確認・換気/回路・循環の窓・トレンド",
           "ベースライン/高さ/形/リズムで読む波形アトラス",
           "消失・急低下・上昇への初動と総覧表",
           "CPR・鎮静・肺塞栓・腹腔鏡・小児 ほか"]
SUBS = {
    0: [("1.1", "発見→赤外→NDIR分析計"), ("1.2", "臨床導入とアトラス"),
        ("1.3", "標準モニタ化・食道挿管検出"), ("1.4", "なぜ主役か")],
    1: [("2.1", "赤外吸収の原理"), ("2.2", "メイン vs サイド"), ("2.3", "応答時間・遅延"),
        ("2.4", "誤差要因"), ("2.5", "数値 vs 波形・2系統")],
    2: [("3.1", "産生・運搬・排出"), ("3.2", "PaCO₂ と PetCO₂"), ("3.3", "a–ET 較差"),
        ("3.4", "死腔と V/Q"), ("3.5", "EtCO₂ の3軸")],
    3: [("4.1", "時間軸の4相"), ("4.2", "α角・β角"), ("4.3", "相III の傾き"),
        ("4.4", "容量軸カプノグラフィ"), ("4.5", "正常波形チェック")],
    4: [("5.1", "挿管確認"), ("5.2", "換気・回路"), ("5.3", "循環の窓"),
        ("5.4", "上昇と MH"), ("5.5", "トレンド"), ("5.6", "a–ET 較差")],
    5: [("6.1", "系統的読影"), ("6.2", "リブリージング"), ("6.3", "シャークフィン"),
        ("6.4", "curare cleft"), ("6.5", "急低下・消失"), ("6.6", "漸増 vs 漸減"), ("6.7", "パターン集")],
    6: [("7.1", "消失アルゴリズム"), ("7.2", "急低下の鑑別"), ("7.3", "上昇・MH 初動"),
        ("7.4", "閉塞への対応"), ("7.5", "回路異常"), ("7.6", "総覧表")],
    7: [("8.1", "CPR"), ("8.2", "挿管確認"), ("8.3", "鎮静・非挿管"), ("8.4", "肺塞栓・循環評価"),
        ("8.5", "腹腔鏡・体位"), ("8.6", "挿管困難・搬送"), ("8.7", "小児")],
}

# ============================ BUILD ============================
prs = new_deck(TEMPLATE)

# ---- T. title ----
title_slide(prs, "EtCO₂ モニタリング",
            [("― カプノグラフィを読み解く ―", dict(size=22, bold=True, color=INK)),
             ("歴史・原理から術中の見どころ・特殊使用まで（麻酔科専門医向け）", dict(size=20, color=GRAY)),
             ("", dict(size=10, color=INK)),
             ("川副 靖晃", dict(size=22, color=INK))],
            hero=fp("f00_hero"))

# ---- CQ ----
sCQ = bullets(prs, "その“四角い波形”、読めますか？", [
    ("全身麻酔中、いちばん長く見ているグラフは EtCO₂ かもしれない。", dict(color=INK, sa=16)),
    ("だが「40 mmHg」の数字だけ見て、“形”を読み飛ばしていないか。", dict(color=INK, sa=16)),
    ("傾き・ベースライン・高さ・リズム ― 波形は換気・循環・代謝を語る。", dict(color=INK, sa=20)),
    ("→ 歴史→原理→生理→正常→術中→異常→対応→特殊 で体系化する。", dict(color=RED, sa=0)),
], size=22)
set_notes(sCQ,
    "全身麻酔中、いちばん長く見ているグラフは EtCO₂ かもしれない。\n"
    "だが「40 mmHg」の数字だけ見て、“形”を読み飛ばしていないか。\n"
    "相III の傾き・ベースライン・高さ・リズム ― 波形は換気・循環・代謝を同時に語る。\n"
    "→ 歴史 → 原理 → 生理 → 正常 → 術中 → 異常 → 対応 → 特殊 で体系化する。")

# ---- G. goals ----
bullets(prs, "この講義の到達目標", [
    ("1. 測定原理（赤外吸収・メイン/サイド）と誤差要因を説明できる", dict(color=INK, sa=16)),
    ("2. 正常カプノグラム（4相・α/β角・a–ET 較差）を読める", dict(color=INK, sa=16)),
    ("3. 異常波形を ベースライン・高さ・形・リズム で系統的に鑑別できる", dict(color=INK, sa=16)),
    ("4. EtCO₂ の変化（消失・急低下・上昇）への初動を選べる", dict(color=INK, sa=16)),
    ("5. 特殊使用（CPR・鎮静・肺塞栓・腹腔鏡・小児）で活用できる", dict(color=INK, sa=0)),
], size=22)

# ---- M. menu ----
menu_slide(prs, "メニュー", FULL, MENUSUB)

# ================================================================ CH 1 ====
divider(prs, 0, FULL, SHORT, SUBS)

figure_slide(prs, "1.1 発見→NDIRへ", fp("f0101"), active=0,
             caption="気体化学・赤外物理・計測工学の3つの源流が1本の時系列でNDIRに合流する",
             cite="Jaffe MB. Anesth Analg 2008; 107:890-904.", cite_url=U["jaffe08"])
figure_slide(prs, "1.2 波形読影の誕生", fp("f0102"), active=0,
             caption="多ガス質量分析の時代から、赤外・専用機による「カプノグラム（波形）」の読影へ",
             cite="Smalhout B, Kalenda Z. An Atlas of Capnography. Utrecht: Kerckebosch; 1975.", cite_url=U["smalhout"])
figure_slide(prs, "1.3 標準モニタ化", fp("f0103"), active=0,
             caption="Harvard基準→ASA基準→JSA指針、そして「食道挿管を見逃さない」ことが死亡を減らした",
             cite="Tinker JH, Dull DL, Caplan RA, et al. Anesthesiology 1989; 71:541-546.", cite_url=U["tinker"])
s14 = column(prs, "1.4 なぜ主役か",
       "SpO₂より早く・1波形で3つを・確認の金字塔",
       ["【SpO₂より早い】換気停止・回路外れ・食道挿管を早期に捉える。",
        "【1波形で3つ】産生×運搬×排出の積として決まる。",
        "【確認の金字塔】カプノグラフィ＝挿管確認のゴールドスタンダード。"],
       active=0, cite="Tinker JH, Dull DL, Caplan RA, et al. Anesthesiology 1989; 71:541-546.",
       cite_url=U["tinker"], accent=GOLD)
set_notes(s14,
    "【SpO₂より早い】換気停止・回路外れ・食道挿管を、酸素飽和度が下がるより前に捉える。"
    "特に十分な前酸素化のあとは酸素の予備で SpO₂ 低下が遅れるため、無呼吸や誤挿管の“最初の警報”は EtCO₂ 側で鳴る。\n\n"
    "【1波形で3つを読む】EtCO₂ は 産生(代謝)×運搬(循環・肺血流)×排出(換気) の積として決まる。"
    "非侵襲・呼吸ごとに連続表示され、1本の波形で代謝・循環・換気の異常を同時に映す（＝第3章で定式化する“3軸”の窓）。\n\n"
    "【確認の金字塔】気管挿管が食道でないことの確認は、視認や聴診ではなくカプノグラフィが最終判定＝ゴールドスタンダード。"
    "“形が出続けるか”が気道の生命線。以後の章はすべてこの4相波形を読む話に帰着する。")

# ================================================================ CH 2 ====
divider(prs, 1, FULL, SHORT, SUBS)

figure_slide(prs, "2.1 赤外吸収の原理", fp("f0201"), active=1,
             caption="「二原子でない分子は固有波長の赤外を吸う」。吸われ残った光の量で濃度を測る。",
             cite="Jaffe MB. Anesth Analg 2008; 107:890–904.", cite_url=U["jaffe08"])
figure_slide(prs, "2.2 メイン/サイド", fp("f0202"), active=1,
             caption="センサを「気道に置く」か「ガスを吸い込んで測る」か。速さ・重さ・水対策で棲み分け。",
             cite="Kodali BS. Anesthesiology 2013; 118:192–201.", cite_url=U["kodali13"])
figure_slide(prs, "2.3 応答時間・遅延", fp("f0203"), active=1,
             caption="サイドストリームは「遅れて・なまって」届く。速い呼吸・浅い一回換気では過小評価に。",
             cite="Sandberg WS ほか. Sci Rep 2024; 14:26385.", cite_url=U["sandberg24"])
s24a = column_row(prs, "2.4 誤差要因 ①", [
    ("水滴・分泌物・結露", [
        "セルを汚し波形がなまる。",
        "水トラップ・親水膜で除去する。"], BLUE),
    ("衝突広がり", [
        "N₂O・O₂で偽高値になる。",
        "現行機は自動補正する。"], GOLD),
], active=1, cite="Severinghaus JW, Larson CP, Eger EI. Anesthesiology 1961; 22:429–432.",
   cite_url=U["severinghaus61"])
set_notes(s24a,
    "【水滴・分泌物・結露】サイドラインの水滴や気道分泌物はサンプルセルを汚し、部分閉塞で波形をなまらせ、"
    "完全閉塞では波形消失に至る。水トラップと親水膜で除去し、詰まれば交換する。メインストリームはキュベット"
    "加温で結露を防ぐ。\n\n"
    "【衝突広がり（collision broadening）】高濃度N₂O・O₂はCO₂の吸収線を圧力広がりで太らせ、CO₂を偽高値に"
    "読ませる（古典的にN₂O 70%で相対約+10%）。現行機はN₂O・O₂濃度を測り自動補正するので、較正時のガス設定を"
    "正しく合わせる。")

s24b = column_row(prs, "2.4 誤差要因 ②", [
    ("リーク・希釈", [
        "外気混入で希釈される。",
        "接続部・吸引量に注意。"], RED),
    ("ゼロ点・較正", [
        "較正ずれで絶対値が狂う。",
        "定期較正と気圧補正を保つ。"], TEAL),
], active=1)
set_notes(s24b,
    "【リーク・希釈】サンプリングラインやコネクタの漏れ、カフ漏れ、非挿管での外気混入はサンプルを希釈し"
    "PetCO₂を過小評価させる。接続部の緩み・亀裂・過大な吸引流量に注意。\n\n"
    "【ゼロ点・較正】ゼロドリフトや較正ずれは絶対値を狂わせる。定期較正と大気圧補正を保つ。NDIRは濃度(分率)"
    "を測るため、気圧が変われば分圧(mmHg)換算がずれる点に留意する。")
figure_slide(prs, "2.5 数値 vs 波形", fp("f0205"), active=1,
             caption="「数値だけ」か「波形も」か。さらに横軸を時間にとるか呼気量にとるかで2系統に分かれる。",
             cite="Verscheure S ほか. Crit Care 2016; 20:184.", cite_url=U["verscheure16"])

# ================================================================ CH 3 ====
divider(prs, 2, FULL, SHORT, SUBS)

s31 = figure_slide(prs, "3.1 産生・排泄", fp("f0301"), active=2,
             caption="組織で作られた CO₂ は静脈血で運ばれ、肺胞換気で吐き出される。",
             cite="Geers C, Gros G. Physiol Rev 2000; 80:681-715", cite_url=U["geers00"])
set_notes(s31, "組織で作られた CO₂ は静脈血で運ばれ、肺胞換気で吐き出される。定常状態では PaCO₂ ∝ 産生量 ÷ 肺胞換気量。")
figure_slide(prs, "3.2 PaCO₂/PetCO₂", fp("f0302"), active=2,
             caption="呼気終末ガスは肺胞気を代表する。理想肺なら PACO₂ = PaCO₂ = PetCO₂。現実がズレる理由が次節。",
             cite="Nunn JF, Hill DW. J Appl Physiol 1960; 15:383-389", cite_url=U["nunn60"])
figure_slide(prs, "3.3 a–ET 較差", fp("f0303"), active=2,
             caption="正常 2–5 mmHg。PaCO₂ > 平均肺胞気 PACO₂ > PetCO₂ の階段。決めるのは死腔・V/Q 不均等・拡散。",
             cite="Nunn JF, Hill DW. J Appl Physiol 1960; 15:383-389", cite_url=U["nunn60"])
figure_slide(prs, "3.4　死腔と V/Q", fp("f0304"), active=2,
             caption="換気されるが灌流されない肺胞＝死腔。死腔↑で PetCO₂↓・a–ET 較差↑。Bohr–Enghoff で定量。",
             cite="West JB, Dollery CT, Naimark A. J Appl Physiol 1964; 19:713-724", cite_url=U["west64"])
s35 = figure_slide(prs, "3.5 EtCO₂の3軸", fp("f0305"), active=2,
             caption="産生（代謝）・運搬（循環／肺血流）・排出（換気）。",
             cite="Bhavani-Shankar K, et al. Can J Anaesth 1992; 39:617-632", cite_url=U["bs92"])
set_notes(s35, "産生（代謝）・運搬（循環／肺血流）・排出（換気）。以後すべての EtCO₂ 異常は、この3軸のどれが動いたかで読む。")

# ================================================================ CH 4 ====
divider(prs, 3, FULL, SHORT, SUBS)

figure_slide(prs, "4.1 時間軸の4相", fp("f0401"), active=3,
             caption="1呼吸を4相で読む：相I（死腔）→相II（急上昇）→相III（肺胞プラトー）→相0（吸気下降）",
             cite="Bhavani-Shankar K, Philip JH. Anesth Analg 2000; 91:973-7", cite_url=U["bsphilip00"])
figure_slide(prs, "4.2　α角とβ角", fp("f0402"), active=3,
             caption="相の“折れ角”が病態を映す：α角＝相II–III、β角＝相III–吸気",
             cite="Bhavani-Shankar K, Philip JH. Anesth Analg 2000; 91:973-7", cite_url=U["bsphilip00"])
figure_slide(prs, "4.3 相IIIの傾き", fp("f0403"), active=3,
             caption="プラトーはわずかに上る—勾配の増大は不均等換気のサイン",
             cite="Verscheure S, et al. Crit Care 2016; 20:184", cite_url=U["verscheure16b"])
figure_slide(prs, "4.4 容量軸 SBT-CO₂", fp("f0404"), active=3,
             caption="横軸を“時間”から“呼気量”へ—死腔とVCO₂が測れる専門波形",
             cite="Fowler WS. Am J Physiol 1948; 154:405-16 ／ Verscheure S, et al. Crit Care 2016; 20:184",
             cite_url=U["fowler48"])
s45 = bullets_figure(prs, "4.5 正常波形の確認", [
    ("① ベースライン＝0", dict(color=INK, sa=16)),
    ("② 矩形：急峻な立上り・平坦", dict(color=INK, sa=16)),
    ("③ 高さ＝PetCO₂ 35–45 mmHg", dict(color=INK, sa=16)),
    ("④ α角が正常：約100–110°", dict(color=INK, sa=16)),
    ("→ 毎呼吸ひと目で確認、逸脱は第6章へ", dict(color=GOLD, sa=0)),
], fp("f0405"), active=3, fig_w=Cm(9.5),
   cite="Kodali BS. Anesthesiology 2013; 118:192-201", cite_url=U["kodali13b"])
set_notes(s45,
    "① ベースライン＝0：吸気相でCO₂が0に戻る（リブリージングなし）\n"
    "② 矩形：相IIが急峻に立ち上がり、相IIIが平坦（ごく軽い上り）\n"
    "③ 高さ＝PetCO₂ 35–45 mmHg（正常換気の目安）\n"
    "④ α角が正常：約100–110°、開大していない\n"
    "→ この4点を毎呼吸ひと目で確認。逸脱は第6章の系統的鑑別へ")

# ================================================================ CH 5 ====
divider(prs, 4, FULL, SHORT, SUBS)

figure_slide(prs, "5.1 挿管確認", fp("f0501"), active=4,
             caption="持続する矩形波（6呼吸）＝気管。数呼吸で消えて平坦＝食道。",
             cite="Grmec S. Intensive Care Med 2002; 28:701-4.", cite_url=U["grmec02"])
figure_slide(prs, "5.2 換気・回路監視", fp("f0502"), active=4,
             caption="低換気↑・過換気↓・回路外れは波形消失で即座に。SpO₂低下より早い。",
             cite="Deitch K, et al. Ann Emerg Med 2010; 55:258-64.", cite_url=U["deitch10"])
figure_slide(prs, "5.3 循環の窓", fp("f0503"), active=4,
             caption="換気一定なら EtCO₂ は肺血流（＝心拍出量）を映す。突然の低下は塞栓・低心拍出・心停止。",
             cite="Gudipati CV, Weil MH, et al. Circulation 1988; 77:234-9.", cite_url=U["gudipati88"])
s54 = figure_slide(prs, "5.4 上昇と MH", fp("f0504"), active=4,
             caption="分時換気量を上げても是正されない進行性のEtCO₂上昇はMHの早期・鋭敏な所見。",
             cite="Larach MG, et al. Anesth Analg 2010; 110:498-507.", cite_url=U["larach10"])
set_notes(s54, "分時換気量を上げても是正されない進行性のEtCO₂上昇はMHの早期・鋭敏な所見。ただし単独では診断しない。")
figure_slide(prs, "5.5 トレンドで読む", fp("f0505"), active=4,
             caption="波形の“くぼみ”は自発呼吸の再開、トレンドは麻酔深度と換気設定の最適化に使う。")
s56 = column(prs, "5.6 a–ET 較差",
       "PetCO₂ ＝ PaCO₂ ではない ― 較差は動く",
       ["正常の a–ET(CO₂) 較差は概ね 2–5 mmHg。これは固定値ではない。",
        "較差を広げるのは換気血流ミスマッチ。",
        "低心拍出・肺塞栓・体位・片肺換気で拡大する。",
        "実務: PetCO₂だけでPaCO₂を過信しない。",
        "絶対値が要る局面は血ガスで実測する。"],
       active=4, cite="Fletcher R, Jonson B. Br J Anaesth 1984; 56:109-19.", cite_url=U["fletcher84"], accent=TEAL)
set_notes(s56,
    "正常の a–ET(CO₂) 較差は概ね 2–5 mmHg。仰臥位・全身麻酔・調節換気の“素直な肺”での話で、これは固定値ではない。\n\n"
    "較差を広げるのは肺胞死腔の増加＝換気血流ミスマッチ。低心拍出・肺塞栓（肺血流↓）、PEEPやhigh TVでのWest zone 1化、"
    "側臥位/腹臥位/頭低位などの体位、片肺換気で較差は拡大し、PetCO₂はPaCO₂を過小評価する。\n\n"
    "実務: PetCO₂だけでPaCO₂を過信しない。トレンドは有用だが、絶対値が要る局面（脳外科の厳密なCO₂管理、重症肺疾患、"
    "塞栓を疑うとき）は動脈血ガスで実測し、その時点の較差を“較正”して以後のトレンド解釈に使う。")

# ================================================================ CH 6 ====
divider(prs, 5, FULL, SHORT, SUBS)

figure_slide(prs, "6.1 異常の読み方", fp("f0601"), active=5,
             caption="ベースライン・高さ・形・リズムの順に見れば、どの異常も取りこぼさない",
             cite="Bhavani-Shankar K, et al. Can J Anaesth 1992; 39:617-32", cite_url=U["bs92b"])
figure_slide(prs, "6.2 リブリージング", fp("f0602"), active=5,
             caption="吸気CO₂＞0（相Iが0に戻らない）＝呼出したCO₂の再吸入",
             cite="Bhavani-Shankar K, Philip JH. Anesth Analg 2000; 91:973-7", cite_url=U["bsphilip00"])
figure_slide(prs, "6.3 シャークフィン", fp("f0603"), active=5,
             caption="相IIとIIIが融合し立ち上がりが鈍る＝気管支攣縮・COPD・呼出遅延",
             cite="Jaffe MB. J Clin Monit Comput 2017; 31:19-41", cite_url=U["jaffe17"])
figure_slide(prs, "6.4 curare cleft", fp("f0604"), active=5,
             caption="調節換気中のプラトーのくぼみ＝自発呼吸の再出現（筋弛緩の醒め）",
             cite="Bhavani-Shankar K, et al. Can J Anaesth 1992; 39:617-32", cite_url=U["bs92b"])
figure_slide(prs, "6.5 急低下・消失", fp("f0605"), active=5,
             caption="「波形が消えてゼロ」か「小さく残る」かで、換気系の事故か循環の破綻かを切り分ける",
             cite="Kodali BS. Anesthesiology 2013; 118:192-201", cite_url=U["kodali13c"])
figure_slide(prs, "6.6 漸増 vs 漸減", fp("f0606"), active=5,
             caption="分単位のトレンドは「産生・排出・循環」のどれが動いたかを語る",
             cite="Bhavani-Shankar K, et al. Can J Anaesth 1992; 39:617-32", cite_url=U["bs92b"])
figure_slide(prs, "6.7 パターン集", fp("f0607"), active=5,
             caption="覚えておくと一目で当たる4つの形",
             cite="Jaffe MB. J Clin Monit Comput 2017; 31:19-41", cite_url=U["jaffe17"])

# ================================================================ CH 7 ====
divider(prs, 6, FULL, SHORT, SUBS)

figure_slide(prs, "7.1 波形消失対応", fp("f0701"), active=6,
             caption="波形が突然ゼロ。落ち着いて「循環の確認」と「4系統の系統点検」を並行する。")
figure_slide(prs, "7.2 急低下の鑑別", fp("f0702"), active=6,
             caption="波形の“形”は保たれたまま高さが急落＝肺血流（心拍出）の急減。まず循環を診る。",
             cite="Mirski MA, et al. Anesthesiology 2007; 106:164-77", cite_url=U["mirski07"])
figure_slide(prs, "7.3 上昇・MH 初動", fp("f0703"), active=6,
             caption="分時換気量を上げても下がらない急上昇＋頻脈/硬直＝MH を疑い、直ちにトリガー中止。",
             cite="Glahn KPE, et al. Br J Anaesth 2010; 105:417-20", cite_url=U["glahn10"])
figure_slide(prs, "7.4 閉塞性への対応", fp("f0704"), active=6,
             caption="相II延長・相III上り勾配・α角増大の「正常化」を治療効果の指標にする。")
s75 = column_row(prs, "7.5 回路異常対応", [
    ("見きわめ", [
        "吸気CO₂>0=再呼吸。",
        "真の再呼吸かを鑑別。"], BLUE),
    ("主な原因", [
        "①吸収剤消耗",
        "②弁の閉鎖不全",
        "③新鮮ガス不足",
        "低流量麻酔で頻発。"], ORANGE),
    ("初動（早い順）", [
        "流量増量（即効）。",
        "吸収剤交換・弁点検。",
        "0復帰で確認。"], RGBColor(0x70, 0xAD, 0x47)),
], active=6)
set_notes(s75,
    "【何が起きているか（見きわめ）】吸気時の CO₂ が 0 を超え、ベースラインが基線（0）に戻らない＝再呼吸。"
    "EtCO₂ は上昇方向に動く。まず“真の再呼吸”か、水滴・分泌物やゼロ点ずれによるアーチファクトかを分ける。\n\n"
    "【主な原因（回路の3点）】①CO₂ 吸収剤の消耗、②一方向弁の閉鎖不全/固着、③新鮮ガス流量の不足。"
    "低流量麻酔や Mapleson 系では新鮮ガス不足がそのまま再呼吸に直結する。\n\n"
    "【初動（早い順）】まず新鮮ガス流量を上げる（即効の一時対応）。並行して吸収剤を交換し、吸気/呼気弁を"
    "点検・交換する。改善はベースラインが 0 へ戻ることで確認する。")
table_figure_slide(prs, "7.6 対応の総覧表", fp("f0706"), active=6,
                    cite="Glahn KPE, et al. Br J Anaesth 2010; 105:417-20（MH行）／Mirski MA, et al. Anesthesiology 2007; 106:164-77（塞栓行）",
                    cite_url=U["glahn10"])

# ================================================================ CH 8 ====
divider(prs, 7, FULL, SHORT, SUBS)

figure_slide(prs, "8.1 心肺蘇生 CPR", fp("f0801"), active=7,
             caption="換気を一定に保てば EtCO₂ ≒ 肺血流（＝圧迫が生む心拍出）の窓",
             cite="Cantineau JP, et al. Crit Care Med 1996; 24:791", cite_url=U["cantineau96"])
figure_slide(prs, "8.2 挿管・位置確認", fp("f0802"), active=7,
             caption="持続する矩形波＝気管。手術室・救急・病院前・搬送で共通の合言葉「波形なし＝位置が違う」",
             cite="Merchant RM, et al. Circulation 2020; 142:S337", cite_url=U["merchant20"])
figure_slide(prs, "8.3 鎮静・非挿管", fp("f0803"), active=7,
             caption="手技鎮静（PSA）＋酸素投与下では SpO₂ が遅れる。カプノで換気そのものを見る",
             cite="Waugh JB, et al. J Clin Anesth 2011; 23:189", cite_url=U["waugh11"])
figure_slide(prs, "8.4 肺塞栓と循環", fp("f0804"), active=7,
             caption="肺血流が途絶えると換気されるのに灌流されない肺胞（＝死腔）が増え、EtCO₂↓・a–ET較差↑",
             cite="Verschuren F, et al. J Thromb Haemost 2010; 8:60", cite_url=U["verschuren10"])
figure_slide(prs, "8.5 腹腔鏡・体位", fp("f0805"), active=7,
             caption="腹腔内 CO₂ が吸収されて EtCO₂↑。長時間・頭低位・皮下気腫では PetCO₂ が PaCO₂ を過小評価",
             cite="Klopfenstein CE, et al. Acta Anaesthesiol Scand 2008; 52:700", cite_url=U["klopfenstein08"])
s86 = column_row(prs, "8.6 挿管困難・搬送", [
    ("挿管困難", [
        "気管内留置の確認。",
        "心停止でも平坦化。"], GOLD),
    ("NIV・非挿管換気", [
        "NIVでも追える。",
        "リークで値は薄まる。"], TEAL),
    ("搬送・院内移動", [
        "搬送は必須級。",
        "波形消失で即検知。"], BLUE),
], active=7, cite="Frerk C, et al. Br J Anaesth 2015; 115:827", cite_url=U["frerk15"])
set_notes(s86,
    "【挿管困難（DAS の位置づけ）】持続波形カプノグラフィは気管内留置の確認と、食道挿管・換気不良の早期発見の要。"
    "心停止では気管内でも波形が平坦化しうるため、他の所見と併せて判断する。\n\n"
    "【NIV・非挿管換気】マスク/NIV でも呼気 CO₂ の有無・トレンドで換気とリーク、無呼吸を追える。回路リークや"
    "開口呼吸で値は薄まるため、絶対値よりトレンドと波形の質で読む。\n\n"
    "【搬送・院内移動】挿管患者の搬送では波形カプノグラフィは必須級モニタ。移動中の計画外抜管・回路外れ・"
    "チューブ屈曲を“波形消失”で即座に検知でき、SpO₂ 低下より早い。")
figure_slide(prs, "8.7 小児・新生児", fp("f0807"), active=7,
             caption="小さい一回換気量×死腔・希釈の影響を受けやすい。低流量サンプリングとトレンド重視で読む",
             cite="Bhende MS, et al. Pediatrics 1995; 95:395", cite_url=U["bhende95"])

# ================================================================ CLOSE ====
sC = bullets(prs, "まとめ ― 3・2・1 で持ち帰る", [
    ("3つの本質", dict(color=GOLD, sa=8)),
    ("EtCO₂＝産生×運搬×排出を映す窓", dict(color=INK, sa=4, lv=1)),
    ("波形の“形”は換気の質と気道抵抗を語る", dict(color=INK, sa=4, lv=1)),
    ("a–ET較差＝死腔・V/Q・肺血流を映す", dict(color=INK, sa=18, lv=1)),
    ("2つの型", dict(color=GOLD, sa=8)),
    ("時間軸＝換気の質とトレンドを読む", dict(color=INK, sa=4, lv=1)),
    ("容量軸＝死腔・V̇CO₂を定量する", dict(color=INK, sa=18, lv=1)),
    ("1つの鉄則", dict(color=GOLD, sa=8)),
    ("挿管確認の鉄則＝“No trace = wrong place”", dict(color=RED, sa=0, lv=1)),
])
set_notes(sC,
    "3つの本質\n"
    "・EtCO₂ は 産生(代謝)×運搬(循環・肺血流)×排出(換気) を映す1つの窓\n"
    "・波形の“形”（相III勾配・α角）は換気の質と気道抵抗を語る\n"
    "・a–ET(CO₂)較差は 死腔・V/Q・肺血流 を映す ― PetCO₂ で PaCO₂ を過信しない\n\n"
    "2つの型\n"
    "・時間軸カプノグラム＝換気の質・トレンドを読む（日常）\n"
    "・容量軸カプノグラフィ＝死腔・V̇CO₂ を定量する（深掘り）\n\n"
    "1つの鉄則\n"
    "・挿管確認は EtCO₂ がゴールドスタンダード ― “No trace = wrong place”（持続する矩形波＝気管）")

REFS = [
    ("Bhavani-Shankar K, Philip JH. Anesth Analg 2000; 91:973-7.", U["bsphilip00"]),
    ("Bhavani-Shankar K, et al. Can J Anaesth 1992; 39:617-32.", U["bs92b"]),
    ("Bhende MS, et al. Pediatrics 1995; 95:395.", U["bhende95"]),
    ("Cantineau JP, et al. Crit Care Med 1996; 24:791.", U["cantineau96"]),
    ("Deitch K, et al. Ann Emerg Med 2010; 55:258-64.", U["deitch10"]),
    ("Fletcher R, Jonson B. Br J Anaesth 1984; 56:109-19.", U["fletcher84"]),
    ("Fowler WS. Am J Physiol 1948; 154:405-16.", U["fowler48"]),
    ("Frerk C, et al. Br J Anaesth 2015; 115:827.", U["frerk15"]),
    ("Geers C, Gros G. Physiol Rev 2000; 80:681-715.", U["geers00"]),
    ("Glahn KPE, et al. Br J Anaesth 2010; 105:417-20.", U["glahn10"]),
    ("Grmec S. Intensive Care Med 2002; 28:701-4.", U["grmec02"]),
    ("Gudipati CV, Weil MH, et al. Circulation 1988; 77:234-9.", U["gudipati88"]),
    ("Jaffe MB. Anesth Analg 2008; 107:890-904.", U["jaffe08"]),
    ("Jaffe MB. J Clin Monit Comput 2017; 31:19-41.", U["jaffe17"]),
    ("Klopfenstein CE, et al. Acta Anaesthesiol Scand 2008; 52:700.", U["klopfenstein08"]),
    ("Kodali BS. Anesthesiology 2013; 118:192-201.", U["kodali13"]),
    ("Larach MG, et al. Anesth Analg 2010; 110:498-507.", U["larach10"]),
    ("Merchant RM, et al. Circulation 2020; 142:S337.", U["merchant20"]),
    ("Mirski MA, et al. Anesthesiology 2007; 106:164-77.", U["mirski07"]),
    ("Nunn JF, Hill DW. J Appl Physiol 1960; 15:383-389.", U["nunn60"]),
    ("Sandberg WS, et al. Sci Rep 2024; 14:26385.", U["sandberg24"]),
    ("Severinghaus JW, Larson CP, Eger EI. Anesthesiology 1961; 22:429-432. ［要確認：巻頁］", U["severinghaus61"]),
    ("Smalhout B, Kalenda Z. An Atlas of Capnography. Utrecht: Kerckebosch; 1975.", U["smalhout"]),
    ("Tinker JH, Dull DL, Caplan RA, et al. Anesthesiology 1989; 71:541-546.", U["tinker"]),
    ("Verschuren F, et al. J Thromb Haemost 2010; 8:60.", U["verschuren10"]),
    ("Verscheure S, et al. Crit Care 2016; 20:184.", U["verscheure16"]),
    ("Waugh JB, et al. J Clin Anesth 2011; 23:189.", U["waugh11"]),
    ("West JB, Dollery CT, Naimark A. J Appl Physiol 1964; 19:713-724.", U["west64"]),
]
references(prs, REFS)

add_pagenumbers(prs)
prs.save(OUT)
print("saved", OUT, "slides:", len(prs.slides._sldIdLst))

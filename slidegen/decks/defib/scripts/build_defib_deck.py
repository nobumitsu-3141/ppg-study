#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""除細動器デック ビルダー。content/*.md（各スライドをYAMLの1ドキュメントとして記述した章データ）と
content/front_back.md（前付け・結語・章見出し定義）を実行時に読み込み、decklib の工場でスライドを
組み立てる。content が正——title/caption/heading/paras/bullets/citation/cite_url は一切創作せず、
ソースの値をそのまま転記する（レイアウトの割付・配色・spacing などの組版パラメータのみ本スクリプトが担当）。
ch*.md は妥当な YAML（各スライド = 1ドキュメント、先頭がリストでその要素が dict）なので PyYAML で読む。
front_back.md は構造化 markdown なので、バッククォート文字列・章見出しリストを正規表現で抽出する。
figs/*.png は make_figs*.py で生成済み（40枚）。

NOTE: YAML の '>' 折り畳みブロック（body.paras）は改行が半角スペースに変換される仕様上、日本語の行送り
箇所に本来存在しない半角スペースが混入する。この corpus を実地に調べた結果（英数字直前の半角スペースは
"は SYNC"「vs 非適応」のように意図的な自作ルールで多用される一方、和文の閉じ約物「。、）】」』・」の直後に
半角スペースが来る例は原文中に一つも無い）に基づき、(1) 非ASCII文字同士に挟まれた単一スペース、
(2) 和文閉じ約物の直後の単一スペース、の2パターンだけを折り畳みアーティファクトとして除去する。
英単語の前後の意図的なスペースは温存する。"""
import os, re
import yaml
import figlib as F
from decklib import *

FIG = F.OUTDIR
def fp(code):
    return f"{FIG}/{code}.png"

TEMPLATE = "_template_kawazoe.pptx"
OUT = "../out/除細動器を使いこなす.pptx"
CONTENT = "../content"

# ---------------------------------------------------------------- helpers --
_CLOSERS = "。、）】」』・"
_BOTH_NONASCII_RE = re.compile(r'(?<=[^\x00-\x7F]) (?=[^\x00-\x7F])')
_AFTER_CLOSER_RE = re.compile('([' + _CLOSERS + ']) ')

def clean_fold(text):
    """Undo YAML folded-scalar line-join artifacts inside Japanese paragraphs (see NOTE)."""
    t = text.strip().replace("**", "")
    t = _BOTH_NONASCII_RE.sub('', t)
    t = _AFTER_CLOSER_RE.sub(r'\1', t)
    return t

def clean_step(x):
    """A steps_photo step is either a plain string (auto-numbered 1,2,3...) or a
    YAML 2-item sequence [num, text] (parsed as a Python list) used to keep a
    continuous number across a split pair of slides (e.g. 7.1①=1-4, 7.1②=5-8).
    decklib.steps_photo() expects the explicit-number form as a *tuple*."""
    if isinstance(x, (list, tuple)) and len(x) == 2:
        return (str(x[0]), clean_fold(x[1]))
    return clean_fold(x)

def load_chapter(n):
    path = os.path.join(CONTENT, f"ch{n}.md")
    with open(path, encoding="utf-8") as f:
        docs = list(yaml.safe_load_all(f))
    slides = {}
    for d in docs:
        if isinstance(d, list) and d and isinstance(d[0], dict):
            s = d[0]
            slides[s["id"]] = s
    return slides

def section_of(sid, n):
    return int(round((sid - n) * 10))

def body_slides(slides, n):
    ids = sorted(k for k in slides if abs(k - n) > 1e-6)  # exclude the n.0 divider doc
    return [slides[i] for i in ids]

CH = {n: load_chapter(n) for n in range(1, 9)}

# ---------------------------------------------------- front_back.md parse --
with open(os.path.join(CONTENT, "front_back.md"), encoding="utf-8") as f:
    FB = f.read()

def fb_section(start, end):
    i = FB.index(start)
    j = FB.index(end, i) if end else len(FB)
    return FB[i:j]

def backticks(text):
    return re.findall(r'`([^`]*)`', text)

sec_full  = fb_section("FULL（", "SHORT（")
sec_short = fb_section("SHORT（", "breadcrumb")
sec_menu  = fb_section("MENUSUB（", "SUBS（")
sec_subs  = fb_section("SUBS（", "\n---")
sec_T  = fb_section("## T.", "## CQ.")
sec_CQ = fb_section("## CQ.", "## G.")
sec_G  = fb_section("## G.", "## M.")
sec_M  = fb_section("## M.", "\n---")
sec_C  = fb_section("## C.", "## R.")

FULL = [re.match(r'\d+\.\s*(.*)', l.strip()).group(1)
        for l in sec_full.splitlines() if re.match(r'\d+\.', l.strip())]

_short_line = [l for l in sec_short.splitlines() if l.strip().startswith("1.")][0]
SHORT = [p.strip("　") for p in re.split(r'\d+\.', _short_line) if p.strip("　")]

MENUSUB = [re.match(r'\d+\.\s*(.*)', l.strip()).group(1)
           for l in sec_menu.splitlines() if re.match(r'\d+\.', l.strip())]

SUBS = {}
for l in sec_subs.splitlines():
    m = re.match(r'-\s*(\d+):\s*(.+)', l.strip())
    if not m:
        continue
    idx = int(m.group(1)) - 1
    pairs = re.findall(r'\(([\d.]+)\s+([^)]+)\)', m.group(2))
    SUBS[idx] = [(code, label) for code, label in pairs]

t_bt = backticks(sec_T)
# main = first, name = last, everything between = subtitle lines (1本目=bold, 残り=gray)
TITLE_MAIN, TITLE_NAME, TITLE_SUBS = t_bt[0], t_bt[-1], t_bt[1:-1]

cq_bt = backticks(sec_CQ)
CQ_TITLE, CQ_ITEMS = cq_bt[0], cq_bt[1:]

g_bt = backticks(sec_G)
G_TITLE, G_ITEMS = g_bt[0], g_bt[1:]

MENU_TITLE = backticks(sec_M)[0]

c_bt = backticks(sec_C)
C_TITLE = c_bt[0]
C_ESSENCE, C_TYPES, C_RULE = c_bt[1:4], c_bt[4:5], c_bt[5:6]

assert len(FULL) == 8 and len(SHORT) == 8 and len(MENUSUB) == 8 and len(SUBS) == 8
assert len(CQ_ITEMS) == 6 and len(G_ITEMS) == 5
assert len(C_ESSENCE) == 3 and len(C_TYPES) == 1 and len(C_RULE) == 1

# ============================ BUILD ============================
prs = new_deck(TEMPLATE)

# ---- T. title ----
title_slide(prs, TITLE_MAIN,
            [(TITLE_SUBS[0], dict(size=22, bold=True, color=INK))]
            + [(s, dict(size=20, color=GRAY)) for s in TITLE_SUBS[1:]]
            + [(TITLE_NAME, dict(size=22, color=INK))],   # spacer 行は入れない（サブ枠に収める）
            hero=fp("f00_hero"))

# ---- CQ ----
# 本文折返し=0対応：元は4行（うち2行目が長文3連結）だったのを6行に再構成。文言は短縮のみ
# （創作なし）。元の4行は speaker notes に全文保持。
s_cq = bullets(prs, CQ_TITLE, [
    (CQ_ITEMS[0], dict(color=INK, sa=10)),
    (CQ_ITEMS[1], dict(color=INK, sa=6)),
    (CQ_ITEMS[2], dict(color=INK, sa=6)),
    (CQ_ITEMS[3], dict(color=INK, sa=16)),
    (CQ_ITEMS[4], dict(color=INK, sa=20)),
    (CQ_ITEMS[5], dict(color=RED, sa=0)),
], size=22)
set_notes(s_cq,
    "本文折返し対応のため6行に再構成。元の4行（原文）：\n"
    "・同じ一台のボタンの押し方ひとつで、救命にも、無効にも、危険にもなる。\n"
    "・VF に「同期」をかけて放電されない。AF に「非同期」で T 波に当てる。ペーシングで\"脈\"を確かめない。\n"
    "・除細動・カルディオバージョン・ペーシング ― 3つの使い分けと、その安全確認が要。\n"
    "・→ 歴史 → 機器 → 作用 → 除細動 → 同期 → ペーシング → 手技 → 周術期 で体系化する。")

# ---- G. goals ----
s_g = bullets(prs, G_TITLE, [
    (G_ITEMS[0], dict(color=INK, sa=16)),
    (G_ITEMS[1], dict(color=INK, sa=16)),
    (G_ITEMS[2], dict(color=INK, sa=16)),
    (G_ITEMS[3], dict(color=INK, sa=16)),
    (G_ITEMS[4], dict(color=INK, sa=0)),
], size=22)
# ①②⑤ was shortened to fit one line without wrapping (①②: 本文折返し対応で "vs"の前後スペース除去・
# エネルギーvs電流→E vs I・カルディオバージョン→CV; ⑤: 既存の短縮); original full wording
# (front_back.md, pre-edit) preserved verbatim in the speaker notes.
set_notes(s_g,
    "① 機器を説明できる：コンデンサ・エネルギー vs 電流・単相/二相・4つのモード。\n"
    "② 除細動と同期カルディオバージョンの適応・エネルギー・\"同期の要否\"を選べる。\n"
    "⑤ 周術期の特殊状況（CIED・小児・妊娠・開胸）と代表的な落とし穴に対応できる。")

# ---- M. menu ----
# 本文折返し=0対応：FULL（長い章見出し）ではなくSHORT（短い章名）を使う。元のFULL見出しは
# speaker notes に全文保持。
s_menu = menu_slide(prs, MENU_TITLE, SHORT, MENUSUB)
set_notes(s_menu, "元はFULL（長い章見出し）表示。本文折返し対応でSHORT（章名のみ）に変更。原文：\n" +
          "\n".join(f"{i+1}. {t}" for i, t in enumerate(FULL)))

# ============================ chapters ============================
chapter_counts = []
for n in range(1, 9):
    idx = n - 1
    slides = CH[n]
    s_div = divider(prs, idx, FULL, SHORT, SUBS)
    if idx == 0:
        # 1.3 の右列ラベルを本文折返し対応で短縮（元「1.3 同期＝カルディオバージョンの発明」）。
        set_notes(s_div, "節見出し1.3の原文（本文折返し対応で短縮）：1.3 同期＝カルディオバージョンの発明")
    count = 1  # the divider itself
    for s in body_slides(slides, n):
        layout = s["layout"]
        title = s["title"]
        citation = s.get("citation")
        cite_url = s.get("cite_url")
        # figure code: explicit `fig:` wins (lets a slide keep its figure after being
        # renumbered); otherwise derive fXXYY from the id.
        fig_path = fp(s["fig"] if s.get("fig") else f"f{n:02d}{section_of(s['id'], n):02d}")

        # notes: full/original wording moved off-slide when the on-slide text was
        # shortened per the simplification rule (kept verbatim, nothing invented).
        notes_text = clean_fold(s["notes"]) if s.get("notes") else None

        if layout == "figure":
            caption = (s.get("body") or {}).get("caption")
            sl = figure_slide(prs, title, fig_path, active=idx,
                         cite=citation, cite_url=cite_url, caption=caption)
        elif layout == "steps_photo":
            b = s.get("body") or {}
            steps = [clean_step(x) for x in b.get("steps", [])]
            sl = steps_photo(prs, title, steps, b.get("photo_label", ""),
                        photo_sub=b.get("photo_sub"), lead=b.get("lead"),
                        active=idx, cite=citation, cite_url=cite_url)
        elif layout == "table":
            sl = table_figure_slide(prs, title, fig_path, active=idx,
                                cite=citation, cite_url=cite_url)
        elif layout == "bullets_figure":
            body_list = s.get("body") or []
            items = [(t, dict(color=INK, sa=16)) for t in body_list]
            if items:
                items[-1] = (items[-1][0], dict(color=INK, sa=0))
            sl = bullets_figure(prs, title, items, fig_path, active=idx,
                            cite=citation, cite_url=cite_url)
        elif layout == "column":
            b = s.get("body") or {}
            heading = b.get("heading")
            paras = [clean_fold(p) for p in b.get("paras", [])]
            sl = column(prs, title, heading, paras, active=idx,
                   cite=citation, cite_url=cite_url)
        else:
            raise ValueError(f"unknown layout {layout!r} at id {s['id']}")
        set_notes(sl, notes_text)
        count += 1
    chapter_counts.append((n, count))

# ============================ CLOSE ============================
close_items = [("3つの本質", dict(color=GOLD, sa=8))]
for i, t in enumerate(C_ESSENCE):
    sa = 18 if i == len(C_ESSENCE) - 1 else 4
    close_items.append((t, dict(color=INK, sa=sa, lv=1)))
close_items.append(("2つの型", dict(color=GOLD, sa=8)))
for t in C_TYPES:
    close_items.append((t, dict(color=INK, sa=18, lv=1)))
close_items.append(("1つの鉄則", dict(color=GOLD, sa=8)))
for t in C_RULE:
    close_items.append((t, dict(color=RED, sa=0, lv=1)))

bullets(prs, C_TITLE, close_items, size=22)

# ============================ 巻末: AED vs DC ＋ よくある Q&A ============================
sl = column(prs, "AED と 手動除細動（DC）の違い",
            "自動のAED と 全モードの手動DC",
            ["【判断】AED＝機械が自動解析・音声誘導／手動DC＝術者が判断",
             "【機能】AED＝ショックのみ／手動DC＝同期CV・ペーシングも",
             "【場面】AED＝院外・BLS／手動DC＝院内・麻酔科"],
            cite="Panchal AR, et al. Circulation 2020; 142(suppl 2):S366-S468.",
            cite_url="https://pubmed.ncbi.nlm.nih.gov/33081529/")
set_notes(sl, "AEDと手動除細動器（DC）の本質差＝『機械が判断しショックだけするか（AED）』か『術者が全モードを操るか（手動）』。AEDはVF/無脈性VTを自動解析し半自動で放電、非医療者でも使える院外/BLSの一次救命ツール。手動DCは医療者が波形を判断し、エネルギー選択・同期下カルディオバージョン・経皮ペーシングまで行える（麻酔科・院内向け）。本デックの想定機 TEC-5631 は手動DC。詳細は第2章2.5/2.6・第4章4.4。")

sl = bullets(prs, "よくある質問 Q&A ①", [
    ("Q. 同期（SYNC）はいつ入れる？", dict(color=GOLD, bold=True, sa=4)),
    ("A. 脈あり不安定頻拍（AF/粗動/SVT/VT）。VFは非同期。", dict(color=INK, sa=18)),
    ("Q. パッドは前側方？前後？", dict(color=GOLD, bold=True, sa=4)),
    ("A. 緊急は前側方。AF待機CV・ペーシング・CIEDは前後。", dict(color=INK, sa=18)),
    ("Q. 単相性と二相性でJは同じ？", dict(color=GOLD, bold=True, sa=4)),
    ("A. 違う。二相性120–200J／単相360J（本機は最大270J）。", dict(color=INK, sa=0)),
], size=22)
set_notes(sl, "Q1同期：脈のある不安定頻拍（意識障害/胸痛/低血圧/心不全を伴うAF・粗動・SVT・脈ありVT）に同期下カルディオバージョン。VF・無脈性VT・不安定な多形性VTは非同期（除細動）。→第5章。 Q2パッド：緊急は貼りやすい前側方が標準。AFの待機的カルディオバージョン・経皮ペーシング・CIED回避では前後配置が有利（AF待機CVで前後96% vs 前側方78%）。→7.5/第8章。 Q3波形：単相性は高エネ（360J）、二相性は低エネで高い初回成功率（120–200J）。TEC-5631は二相性・最大270J。→2.4/4.2。")

sl = bullets(prs, "よくある質問 Q&A ②", [
    ("Q. 妊婦への除細動は？", dict(color=GOLD, bold=True, sa=4)),
    ("A. 通常エネルギーでよい。子宮左方転位＋母体/胎児モニタ。", dict(color=INK, sa=18)),
    ("Q. CIED（PM/ICD）患者では？", dict(color=GOLD, bold=True, sa=4)),
    ("A. パッドをジェネレータから≥8cm・前後。放電後に点検。", dict(color=INK, sa=18)),
    ("Q. ペーシングの捕捉、どう確認？", dict(color=GOLD, bold=True, sa=4)),
    ("A. 電気的（スパイク後QRS）＋機械的（脈・SpO2）の両方で。", dict(color=INK, sa=0)),
], size=22)
set_notes(sl, "Q4妊婦：除細動エネルギーは通常量でよい。子宮左方転位（LUD）で大動脈圧迫を避け、母体・胎児をモニタ。→8.5。 Q5 CIED：救命ショックは遅らせない。パッドはジェネレータから≥8cm離し前後配置、放電後に必ずデバイス点検。磁石の作用は真逆＝ICDは頻拍治療を一時停止／PMは非同期ペーシングに切替（ペーシング機能自体は磁石で止まらない）。→8.1/8.2。 Q6捕捉：電気的捕捉（各スパイク後にQRS）と機械的捕捉（触知脈・SpO2脈波・A-line）の両方を確認。ECGだけだと偽捕捉に騙される。→6.4/6.5。")

# ---- R. references (collected from every slide's citation/cite_url, deduped by url) ----
seen_urls = set()
refs = []
for n in range(1, 9):
    for s in body_slides(CH[n], n):
        c, u = s.get("citation"), s.get("cite_url")
        if not c or u in seen_urls:
            continue
        seen_urls.add(u)
        refs.append((c, u))
REFS = sorted(refs, key=lambda r: r[0])
references(prs, REFS)

add_pagenumbers(prs)
prs.save(OUT)

total = len(prs.slides._sldIdLst)
print("saved", OUT, "slides:", total)
print("front-matter (title+CQ+G+menu):", 4)
for n, count in chapter_counts:
    print(f"  第{n}章: {count} slides (divider 1 + body {count-1})")
print("close+references:", 2)
print("unique references:", len(REFS))

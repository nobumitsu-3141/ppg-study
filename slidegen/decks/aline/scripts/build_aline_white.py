#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""観血的動脈圧測定 デック ビルダー（川副式・白背景・decklibヘルパー版）。
aline_content.json（本文）＋ figs/（白背景版, dz.py で再生成済み）から .pptx を組み立てる。

content の title/headline/bullets/diagram/citations/notes は一切創作しない — JSON の値を
そのまま転記する（本ファイルはレイアウトの割付・配色・章構成の組版パラメータのみを担当）。

25件の content スライドすべてに事前生成PNG figs/<id>_*.png が揃っている（dz.py の ALL 辞書）。
波形18件に加え、タイムライン/比較表/連結図/カード/フローチャート系の新規7件（s1_1, s1_2, s2_1,
s7_1, s7_2, s8_2, s8_3）を追加した。各スライドの diagram.spec/labels/values に厳密に従って
描いたもので、新しい臨床数値・主張は追加していない。fig_for() が figs/<id>_*.png を自動検出する
ため、下の分岐ロジックは維持したまま（現状は全件が bullets_figure 経路を通る）。
"""
import json, os, glob
from decklib import *

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "figs")
TEMPLATE = "_template_kawazoe.pptx"
OUT = "../out/観血的動脈圧測定.pptx"
CONTENT_JSON = os.path.join(HERE, "..", "aline_content.json")

with open(CONTENT_JSON, encoding="utf-8") as f:
    DATA = json.load(f)
CONTENT = {s["id"]: s for s in DATA["slides"]}
REFS_RAW = DATA.get("references", [])

def fig_for(sid):
    matches = sorted(glob.glob(os.path.join(FIG, f"{sid}_*.png")))
    return matches[0] if matches else None

# ---------------------------------------------------------- chapter structure --
# 章名・章サブタイトルは aline_structure_brief.md（Fable確定の構成設計書）と同一（本文ではなく
# ナビゲーション用のラベル）。CHAPTERS（decklib.py のパンくずラベル）と一致させる。
SECTIONS = [
    ("歴史",     "直接測定はどう生まれ、臨床に来たか"),
    ("成り立ち", "測定系の構成と動特性（自然周波数・減衰）"),
    ("基礎",     "動脈圧波形の解剖と前進波＋反射波"),
    ("正常",     "正常値・正常波形と正しい校正"),
    ("見どころ", "麻酔中の拍動ごとの情報をどう使うか"),
    ("異常",     "系のアーチファクトと病態を映す波形"),
    ("対応",     "トラブルシューティングと合併症・安全"),
    ("特殊",     "パルスコンター・GDT・特殊状況"),
]
FULL = [f"{name}：{sub}" for name, sub in SECTIONS]
MENU_NAMES = [name for name, sub in SECTIONS]  # 目次スライド専用: 副題なしの章名のみ(1行厳守)
SHORT = CHAPTERS  # decklib.py 側で aline 用8ラベルに設定済み
assert len(FULL) == 8 and len(SHORT) == 8 and len(MENU_NAMES) == 8

def chapter_ids(n):
    prefix = f"s{n}_"
    ids = [k for k in CONTENT if k.startswith(prefix)]
    ids.sort(key=lambda k: int(k.split("_")[1]))
    return ids

# 各章の右カラム（サブ項目コード＋ラベル）は content の "title" フィールド（例 "1.1 直接測定の夜明け"）
# をそのまま分割して使う（新規に文言を作らない）。
SUBS = {}
for n in range(1, 9):
    subs = []
    for sid in chapter_ids(n):
        title = CONTENT[sid]["title"]
        code, label = title.split(" ", 1)
        subs.append((code, label))
    SUBS[n - 1] = subs
assert len(SUBS) == 8

NO_FIG_IDS = []  # 事前生成PNGが無く bullets のみになったスライド（報告用）

# ============================ BUILD ============================
prs = new_deck(TEMPLATE)

# ---- cover ----
title_slide(prs, "観血的動脈圧測定",
            [("― 歴史・成り立ちから、波形の読みと応用まで ―", dict(size=22, bold=True, color=INK)),
             ("", dict(size=10, color=INK)),
             ("川副 靖晃", dict(size=22, color=INK))],
            hero=os.path.join(FIG, "hero.png"))

# ---- contents ----
# 章名のみ(副題なし)を渡す — menu_slide は「章名のみ、各行1行厳守」設計(docstring参照)。
# 副題付きFULLを渡すと2行折返しを起こすため目次専用にMENU_NAMESへ差し替え。
menu_slide(prs, "目次 ― 全8章", MENU_NAMES)

# ============================ chapters ============================
chapter_counts = []
for n in range(1, 9):
    idx = n - 1
    # divider左カラムはFULL(副題付き・2行折返しの原因)ではなくMENU_NAMES(目次と同じ短い章名)を渡す
    divider(prs, idx, MENU_NAMES, SHORT, SUBS)
    count = 1  # divider自身
    for sid in chapter_ids(n):
        s = CONTENT[sid]
        title = s["headline"]
        bullets_list = s.get("bullets", [])
        items = [(b, dict(color=INK, sa=16)) for b in bullets_list]
        if items:
            items[-1] = (items[-1][0], dict(color=INK, sa=0))
        cites = s.get("citations", [])
        cite = " ／ ".join(cites) if cites else None
        fig_path = fig_for(sid)
        if fig_path:
            slide = bullets_figure(prs, title, items, fig_path, active=idx, cite=cite)
        else:
            NO_FIG_IDS.append(sid)
            slide = bullets(prs, title, items, active=idx, cite=cite, size=22)
        set_notes(slide, s.get("notes"))
        count += 1
    chapter_counts.append((n, count))

# ---- summary (Take-home) ----
sm = CONTENT["summary"]
sm_items = [(b, dict(color=INK, sa=14)) for b in sm["bullets"]]
if sm_items:
    sm_items[-1] = (sm_items[-1][0], dict(color=INK, sa=0))
sm_cites = sm.get("citations", [])
sm_slide = bullets(prs, sm["headline"], sm_items, size=22,
                    cite=" ／ ".join(sm_cites) if sm_cites else None)
set_notes(sm_slide, sm.get("notes"))

# ---- references (aline_content.json の references をそのまま転記; URL情報は無いためリンク無し) ----
# 24件を1枚(2列×12)で組んだところ 10.5pt でも下端を超えて数件が枠外に消えることをQCで確認したため、
# 1枚あたり12件(2列×6)に分割する（文言は一切変更せず、ページ割りのみ）。
REF_CHUNK = 12
ref_chunks = [REFS_RAW[i:i + REF_CHUNK] for i in range(0, len(REFS_RAW), REF_CHUNK)]
for gi, chunk in enumerate(ref_chunks, start=1):
    ttl = "参考文献" if len(ref_chunks) == 1 else f"参考文献 ({gi}/{len(ref_chunks)})"
    references(prs, [(r, None) for r in chunk], title=ttl)

add_pagenumbers(prs)
prs.save(OUT)

total = len(prs.slides._sldIdLst)
print("saved", OUT, "slides:", total)
print("front-matter (cover+contents):", 2)
for n, count in chapter_counts:
    print(f"  第{n}章: {count} slides (divider 1 + body {count - 1})")
print("summary+references:", 1 + len(ref_chunks), f"(references split into {len(ref_chunks)} slide(s))")
print("no-fig (bullets-only, PNG未生成) slides:", NO_FIG_IDS, "count:", len(NO_FIG_IDS))

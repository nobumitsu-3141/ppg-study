# -*- coding: utf-8 -*-
"""解析の一覧を A4 横 1 ページに収めて印刷用 PDF にする。

データは ../build_catalog.py の TITLE・TREE・PAPERS をそのまま読む（本文は書き写さない）。

    python3 make_a4.py
    python3 make_a4.py --selftest

出力（すべてこのディレクトリ）:
    catalog_a4.html  組版した HTML
    catalog_a4.pdf   Chromium の --print-to-pdf で出した A4 横 1 ページ
    catalog_a4.png   同じ HTML を 1123x794 px で撮った確認用画像
"""
from __future__ import annotations

import argparse
import glob
import html as htmllib
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_DIR = HERE
REPO = HERE.parents[1]
import tempfile
TMP = Path(tempfile.gettempdir())
HTML_OUT = REPO / "docs" / "research" / "analysis_catalog_a4.html"
PROBE_OUT = TMP / "catalog_a4_probe.html"
PDF_OUT = REPO / "docs" / "research" / "analysis_catalog_a4.pdf"
PNG_OUT = TMP / "catalog_a4.png"

IDEO_SPACE = "　"
DASH = " ― "  # 全角のホリゾンタルバー（葉の「識別子 ― 本文」の区切り）

# 画面（スクリーンショット・プローブ）で見込む A4 横の画素数（96 dpi）
PAGE_W_PX = 1123
PAGE_H_PX = 794

# 種別の色。本研究の作図と同じ Okabe-Ito 系。
KIND_COLOR = {
    "conf": "#0072B2",
    "expl": "#D55E00",
    "meth": "#009E73",
    "sens": "#56B4E9",
    "tool": "#777777",
    "none": "#8A8782",
}

LEGEND = [
    ("確認的（事前登録）", "conf"),
    ("探索的", "expl"),
    ("方法の検証", "meth"),
    ("感度解析", "sens"),
    ("道具・その他", "tool"),
]

SOURCE_LINE = ("docs/research/analysis_catalog.md ／ "
               "数値は結果ファイル・原稿の表・lab_log の追記から引用")
FOOT_NOTE = "全表（45 行）と出典は analysis_catalog.md と閲覧ページにある"

# 列の幅（論文1 は葉が多いので広くとる）
COL_WIDTH = ("41.5%", "31.0%", "27.5%")

# 文字の大きさ（pt）
FS = dict(
    title=16.5,
    date=8.0,
    question=8.6,
    source=6.3,
    paper=10.0,
    paper_sub=6.8,
    branch=7.0,
    leaf=7.6,
    chip=7.0,
    ans_name=7.4,
    ans_head=7.8,
    ans_body=6.8,
    legend=6.6,
    note=6.3,
)


# ---------------------------------------------------------------- データの読み込み
def load_source():
    """../build_catalog.py を module として読む。"""
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
    import build_catalog as bc  # noqa: E402
    return bc


def branch_kind(label: str) -> str:
    """枝の名前から色の区分を決める。"""
    if label.startswith("確認的"):
        return "conf"
    if label.startswith("探索"):
        return "expl"
    if label.startswith("方法の検証"):
        return "meth"
    if label.startswith("感度解析"):
        return "sens"
    if label.startswith("道具"):
        return "tool"
    return "none"


def split_leaf(text: str):
    """葉の本文を「先頭の識別子」と「結果の本文」に分ける。"""
    if IDEO_SPACE in text:
        chip, rest = text.split(IDEO_SPACE, 1)
        return chip, rest
    if DASH in text:
        chip, rest = text.split(DASH, 1)
        return chip, "― " + rest  # 区切りの ― も本文に残す（1 字も落とさない）
    return text, ""


def split_head(text: str):
    """論文の見出しを「名前」と「説明」に分ける。"""
    if IDEO_SPACE in text:
        name, sub = text.split(IDEO_SPACE, 1)
        return name, sub
    return text, ""


def build_groups(tree):
    """TREE を 論文ごと（深さ1）にまとめる。枝が無い論文は枝 None の 1 束にする。"""
    groups = []
    for depth, kind, text in tree:
        if depth == 0:
            continue
        if depth == 1 and kind == "p":
            name, sub = split_head(text)
            groups.append(dict(name=name, sub=sub, branches=[]))
        elif depth == 2 and kind == "b":
            groups[-1]["branches"].append(dict(label=text, kind=branch_kind(text), leaves=[]))
        elif kind == "l":
            g = groups[-1]
            if not g["branches"]:
                g["branches"].append(dict(label=None, kind="none", leaves=[]))
            g["branches"][-1]["leaves"].append(split_leaf(text))
    return groups


def first_sentence(text: str) -> str:
    i = text.find("。")
    return text[: i + 1] if i >= 0 else text


def second_sentence(text: str) -> str:
    parts = [p for p in text.split("。") if p]
    return parts[1] + "。" if len(parts) > 1 else ""


# ---------------------------------------------------------------- HTML の組み立て
def e(s: str) -> str:
    return htmllib.escape(s, quote=False)


def source_html() -> str:
    """出典の行。長いので ／ のところで 2 行に分ける（文字は 1 字も変えない）。"""
    return e(SOURCE_LINE).replace("／ ", "／<br>")


def render_leaf(chip: str, rest: str) -> str:
    cls = "chip" if rest else "chip bare"
    body = ('<span class="ltxt">' + e(rest) + "</span>") if rest else ""
    return f'<div class="leaf"><span class="{cls}">{e(chip)}</span>{body}</div>'


def render_branch(br) -> str:
    out = []
    if br["label"] is not None:
        c = KIND_COLOR[br["kind"]]
        out.append(
            f'<div class="brh" style="color:{c}"><span class="brl">{e(br["label"])}</span>'
            f'<span class="brr" style="background:{c}"></span></div>'
        )
    for chip, rest in br["leaves"]:
        out.append(render_leaf(chip, rest))
    return "\n".join(out)


def render_group(g, with_divider: bool = False) -> str:
    out = []
    if with_divider:
        out.append('<div class="gdiv"></div>')
    sub = f'<div class="psub">{e(g["sub"])}</div>' if g["sub"] else ""
    out.append(f'<div class="phead"><div class="pname">{e(g["name"])}</div>{sub}</div>')
    for br in g["branches"]:
        out.append(render_branch(br))
    return "\n".join(out)


def build_html(bc, probe: bool = False) -> str:
    groups = build_groups(bc.TREE)
    question = [t for d, k, t in bc.TREE if d == 0][0]
    m = re.search(r"（(\d{4}-\d{2}-\d{2})）", bc.TITLE)
    date = m.group(1) if m else ""

    cols = [render_group(groups[0]), render_group(groups[1])]
    third = [render_group(groups[2])]
    for extra in groups[3:]:
        third.append('<div class="gextra">' + render_group(extra, with_divider=True) + "</div>")
    cols.append("\n".join(third))

    paper_color = {p["name"]: KIND_COLOR.get(p["color"], KIND_COLOR["none"]) for p in bc.PAPERS}
    boxes = []
    for p in bc.PAPERS:
        ans = dict(p["lines"]).get("答え", "")
        head = first_sentence(ans)
        body = second_sentence(ans)
        c = paper_color[p["name"]]
        boxes.append(
            f'<div class="abox" style="border-left-color:{c}">'
            f'<div class="aline"><span class="aname" style="color:{c}">{e(p["name"])}</span>'
            f'<span class="ahead">{e(head)}</span></div>'
            f'<div class="abody">{e(body)}</div></div>'
        )

    chips = "".join(
        f'<span class="lg"><span class="lgd" style="background:{KIND_COLOR[k]}"></span>{e(n)}</span>'
        for n, k in LEGEND
    )

    probe_js = ""
    if probe:
        probe_js = """
<script>
(function () {
  var d = document.documentElement, page = document.querySelector('.page');
  var cols = [].map.call(document.querySelectorAll('.col'), function (c, i) {
    var top = c.getBoundingClientRect().top, bot = top;
    [].forEach.call(c.children, function (ch) {
      var b = ch.getBoundingClientRect().bottom;
      if (b > bot) bot = b;
    });
    return {i: i, scrollH: c.scrollHeight, clientH: c.clientHeight,
            scrollW: c.scrollWidth, clientW: c.clientWidth,
            contentH: Math.round(bot - top), boxH: Math.round(c.getBoundingClientRect().height),
            boxW: Math.round(c.getBoundingClientRect().width)};
  });
  var last = document.querySelector('.foot');
  var out = {
    docScrollW: d.scrollWidth, docScrollH: d.scrollHeight,
    pageScrollW: page.scrollWidth, pageScrollH: page.scrollHeight,
    pageClientW: page.clientWidth, pageClientH: page.clientHeight,
    pageTop: Math.round(page.getBoundingClientRect().top),
    pageBottom: Math.round(page.getBoundingClientRect().bottom),
    footTop: Math.round(last.getBoundingClientRect().top),
    footBottom: Math.round(last.getBoundingClientRect().bottom),
    innerW: window.innerWidth, innerH: window.innerHeight,
    cols: cols,
    leaves: document.querySelectorAll('.leaf').length,
    font: getComputedStyle(document.querySelector('.leaf .ltxt') ||
                           document.querySelector('.leaf')).fontSize
  };
  var p = document.createElement('pre');
  p.id = 'probe-json';
  p.textContent = 'PROBE' + JSON.stringify(out) + 'ENDPROBE';
  document.body.appendChild(p);
})();
</script>
"""

    css = f"""
@page {{ size: A4 landscape; margin: 9mm; }}
* {{ box-sizing: border-box; }}
html {{
  padding: 9mm; margin: 0; background: #E7E4DE;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; color-adjust: exact;
}}
body {{
  margin: 0; padding: 0; background: #FCFBF8; color: #17181A;
  font-family: "Noto Sans JP", "WenQuanYi Zen Hei", sans-serif;
  font-variant-numeric: tabular-nums; font-feature-settings: "palt" 1;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; color-adjust: exact;
}}
@media print {{
  html {{ padding: 0; background: #FCFBF8; }}
}}
.page {{
  width: 279mm; height: 192mm; overflow: hidden;
  display: flex; flex-direction: column;
}}

/* 見出し帯 */
.head {{ display: flex; align-items: flex-end; gap: 6mm; padding-bottom: 1.5mm; }}
.head-l {{ flex: 1 1 auto; min-width: 0; }}
.h1row {{ display: flex; align-items: baseline; gap: 3.2mm; }}
h1 {{ margin: 0; font-size: {FS['title']}pt; font-weight: 700; letter-spacing: .06em; }}
.date {{ font-size: {FS['date']}pt; color: #5E5C57; font-variant-numeric: tabular-nums; }}
.q {{ margin-top: 1.1mm; font-size: {FS['question']}pt; line-height: 1.3; color: #2C2E31; }}
.head-r {{ flex: 0 0 auto; text-align: right; font-size: {FS['source']}pt;
  line-height: 1.45; color: #6B6862; max-width: 72mm; }}
.rule {{ height: 0; border-top: .5pt solid #2C2E31; }}

/* 本体 3 列 */
.body {{ flex: 1 1 auto; min-height: 0; display: flex; padding-top: 3.0mm; }}
.col {{ min-width: 0; padding: 0 3.4mm; }}
.col:first-child {{ padding-left: 0; }}
.col:last-child {{ padding-right: 0; }}
.col + .col {{ border-left: .4pt solid #D9D6D0; }}
.col.c1 {{ flex: 0 0 {COL_WIDTH[0]}; }}
.col.c2 {{ flex: 0 0 {COL_WIDTH[1]}; }}
.col.c3 {{ flex: 0 0 {COL_WIDTH[2]}; display: flex; flex-direction: column; }}
.gextra {{ margin-top: auto; }}

.phead {{ margin-bottom: 2.0mm; }}
.pname {{ font-size: {FS['paper']}pt; font-weight: 700; letter-spacing: .03em; }}
.psub {{ font-size: {FS['paper_sub']}pt; line-height: 1.34; color: #6B6862; margin-top: .5mm; }}

.brh {{ display: flex; align-items: center; gap: 1.6mm; margin: 2.8mm 0 1.3mm; }}
.brh:first-of-type {{ margin-top: 1.4mm; }}
.brl {{ font-size: {FS['branch']}pt; letter-spacing: .12em; white-space: nowrap; }}
.brr {{ flex: 1 1 auto; height: .9pt; opacity: .55; }}

.leaf {{
  font-size: {FS['leaf']}pt; line-height: 1.32; margin-bottom: 1.95mm;
  padding-left: 3.4mm; text-indent: -3.4mm; color: #17181A;
}}
.chip {{
  font-family: "DejaVu Sans Mono", "Noto Sans JP", monospace;
  font-size: {FS['chip']}pt; color: #24262A;
  background: #ECE9E2; border-radius: 1pt; padding: .15mm .7mm;
  margin-right: 1.1mm; white-space: nowrap;
}}
.chip.bare {{ background: none; padding: 0; margin-right: 0; white-space: normal; }}
.ltxt {{ }}

.gdiv {{ border-top: .4pt solid #D9D6D0; margin: 0 0 2.6mm; }}

/* 脚 */
.foot {{ flex: 0 0 auto; padding-top: 3.0mm; }}
.foot-rule {{ height: 0; border-top: .5pt solid #C9C6C0; margin-bottom: 1.8mm; }}
.answers {{ display: flex; gap: 3.4mm; }}
.abox {{ flex: 1 1 0; min-width: 0; border-left: 1.4pt solid #888; padding-left: 2.0mm; }}
.aline {{ display: flex; align-items: baseline; gap: 1.6mm; }}
.aname {{ font-size: {FS['ans_name']}pt; font-weight: 700; white-space: nowrap;
  letter-spacing: .04em; }}
.ahead {{ font-size: {FS['ans_head']}pt; font-weight: 700; }}
.abody {{ font-size: {FS['ans_body']}pt; line-height: 1.32; color: #4A4843; margin-top: .8mm; }}
.legend {{ display: flex; align-items: baseline; justify-content: space-between;
  gap: 4mm; margin-top: 2.4mm; }}
.lgs {{ display: flex; gap: 3.4mm; flex-wrap: wrap; font-size: {FS['legend']}pt; color: #4A4843; }}
.lg {{ display: inline-flex; align-items: center; gap: 1.1mm; white-space: nowrap; }}
.lgd {{ width: 4.6mm; height: 1.1pt; display: inline-block; }}
.note {{ font-size: {FS['note']}pt; color: #6B6862; white-space: nowrap; }}
#probe-json {{ display: none; }}
"""

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>解析の一覧（A4 横 1 ページ）</title>
<style>{css}</style>
</head>
<body>
<div class="page">

  <div class="head">
    <div class="head-l">
      <div class="h1row"><h1>解析の一覧</h1><span class="date">{e(date)}</span></div>
      <div class="q">{e(question)}</div>
    </div>
    <div class="head-r">{source_html()}</div>
  </div>
  <div class="rule"></div>

  <div class="body">
    <div class="col c1">{cols[0]}</div>
    <div class="col c2">{cols[1]}</div>
    <div class="col c3">{cols[2]}</div>
  </div>

  <div class="foot">
    <div class="foot-rule"></div>
    <div class="answers">{''.join(boxes)}</div>
    <div class="legend">
      <div class="lgs">{chips}</div>
      <div class="note">{e(FOOT_NOTE)}</div>
    </div>
  </div>

</div>{probe_js}
</body>
</html>
"""


# ---------------------------------------------------------------- Chromium の呼び出し
def chromium() -> str:
    hits = sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))
    if not hits:
        raise SystemExit("chromium が見つからない")
    return hits[0]


def run_chrome(extra, timeout=180):
    cmd = [chromium(), "--headless", "--no-sandbox", "--disable-gpu",
           "--hide-scrollbars", "--force-device-scale-factor=1"] + extra
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def make_pdf() -> str:
    """PDF を出す。--no-pdf-header-footer が使えなければ --print-to-pdf-no-header を試す。"""
    url = "file://" + str(HTML_OUT)
    for flag in ("--no-pdf-header-footer", "--print-to-pdf-no-header"):
        if PDF_OUT.exists():
            PDF_OUT.unlink()
        r = run_chrome([flag, f"--print-to-pdf={PDF_OUT}", url])
        if PDF_OUT.exists() and PDF_OUT.stat().st_size > 0:
            return flag
        sys.stderr.write(f"[{flag}] 失敗\n{r.stdout}\n{r.stderr}\n")
    raise SystemExit("PDF を作れなかった")


def make_png(inner_h: int):
    """1123x794 px の確認用画像。

    この Chromium は --window-size より表示領域が {PAGE_H_PX}-inner_h だけ低いので、
    その分だけ高いウィンドウで撮ってから 1123x794 に切り取る。
    """
    from PIL import Image
    if PNG_OUT.exists():
        PNG_OUT.unlink()
    pad = max(0, PAGE_H_PX - int(inner_h))
    raw = HERE / "_shot_raw.png"
    if raw.exists():
        raw.unlink()
    run_chrome([f"--window-size={PAGE_W_PX},{PAGE_H_PX + pad}",
                f"--screenshot={raw}", "file://" + str(HTML_OUT)])
    if not raw.exists():
        raise SystemExit("PNG を作れなかった")
    im = Image.open(raw).convert("RGB").crop((0, 0, PAGE_W_PX, PAGE_H_PX))
    im.save(PNG_OUT)
    raw.unlink()
    return im.size


def run_probe(bc) -> dict:
    PROBE_OUT.write_text(build_html(bc, probe=True), encoding="utf-8")
    r = run_chrome([f"--window-size={PAGE_W_PX},{PAGE_H_PX}", "--dump-dom",
                    "file://" + str(PROBE_OUT)])
    m = re.search(r"PROBE(\{.*?\})ENDPROBE", r.stdout, re.S)
    if not m:
        raise SystemExit("プローブの出力を読めなかった:\n" + r.stdout[-2000:] + r.stderr[-2000:])
    return json.loads(htmllib.unescape(m.group(1)))


PDF_TR = {ord("‧"): "・", ord("∕"): "/", ord("⁄"): "/"}


def _norm(s: str) -> str:
    """PDF から取り出した文字列と元の文字列を比べるための正規化。

    Noto Sans JP の ToUnicode は一部の字を康熙部首に写すので NFKC で戻し、
    中黒・斜線の異体と空白を揃えてから比べる。
    """
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", s).translate(PDF_TR))


def verify_pdf(bc) -> dict:
    from pypdf import PdfReader
    rd = PdfReader(str(PDF_OUT))
    box = rd.pages[0].mediabox
    text = _norm(rd.pages[0].extract_text())
    leaves = [t for d, k, t in bc.TREE if k == "l"]
    missing = [t for t in leaves if _norm(t) not in text]
    for p in bc.PAPERS:
        if _norm(first_sentence(dict(p["lines"])["答え"])) not in text:
            missing.append(p["name"] + " の答え")
    return dict(pages=len(rd.pages), w=float(box.width), h=float(box.height),
                leaves=len(leaves), missing=missing)


# ---------------------------------------------------------------- 自己検査
def selftest() -> int:
    bc = load_source()
    ok = True

    def chk(name, cond, detail=""):
        nonlocal ok
        print(("PASS  " if cond else "FAIL  ") + name + (("  " + detail) if detail else ""))
        if not cond:
            ok = False

    groups = build_groups(bc.TREE)
    chk("論文（深さ1）は 4 束", len(groups) == 4, str([g["name"] for g in groups]))
    n_leaf_tree = sum(1 for d, k, t in bc.TREE if k == "l")
    n_leaf_grp = sum(len(b["leaves"]) for g in groups for b in g["branches"])
    chk("葉の数が一致", n_leaf_tree == n_leaf_grp, f"{n_leaf_tree} / {n_leaf_grp}")

    chip, rest = split_leaf("03番" + IDEO_SPACE + "前提検証 r² 0.000")
    chk("識別子の切り出し（全角空白）", chip == "03番" and rest == "前提検証 r² 0.000")
    chip, rest = split_leaf("11番＋12番" + IDEO_SPACE + "定義を変えた 9 通り")
    chk("識別子の切り出し（＋つき）", chip == "11番＋12番")
    chip, rest = split_leaf("00番・01番")
    chk("区切りが無いときは全体が識別子", chip == "00番・01番" and rest == "")
    chip, rest = split_leaf("研究2・研究3 ― 行わない")
    chk("― で切っても 1 字も落とさない",
        chip == "研究2・研究3" and rest == "― 行わない")
    chk("色の区分", [branch_kind(x) for x in
                     ("確認的（事前登録）", "探索（事後）", "方法の検証", "感度解析", "道具",
                      "研究1b ― 脈波伝播時間の分解")]
        == ["conf", "expl", "meth", "sens", "tool", "none"])
    chk("答えの 1 文目", first_sentence("説明しない。r² 0.000。") == "説明しない。")

    doc = build_html(bc)
    miss = [t for d, k, t in bc.TREE if k == "l" and e(split_leaf(t)[1] or split_leaf(t)[0]) not in doc]
    chk("葉の本文がすべて HTML に入っている", not miss, str(miss[:2]))
    chk("問いが入っている", e([t for d, k, t in bc.TREE if d == 0][0]) in doc)
    chk("出典の行が入っている", source_html() in doc)
    chk("出典の行は文字を落としていない",
        source_html().replace("<br>", " ") == e(SOURCE_LINE))
    for p in bc.PAPERS:
        chk(f"{p['name']} の答えの 1 文目が脚に入っている",
            e(first_sentence(dict(p["lines"])["答え"])) in doc)
    chk("A4 横の指定", "size: A4 landscape" in doc)
    chk("印刷時に色を出す指定", "print-color-adjust: exact" in doc)

    banned = ("錨", "窓", "天井", "帯域", "化ける", "足切り", "予行", "配管", "土俵",  # 用語の引用
              "鍵点", "肩", "ふらつき", "売り文句", "正本")  # 用語の引用
    mine = [SOURCE_LINE, FOOT_NOTE, "解析の一覧", "答え"] + [n for n, _ in LEGEND]
    bad = [(s, w) for s in mine for w in banned if w in s]
    chk("自分で書いた文に禁止語が無い", not bad, str(bad))

    print("ALL PASS" if ok else "FAILED")
    return 0 if ok else 1


# ---------------------------------------------------------------- 本体
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--no-pdf", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    bc = load_source()
    HTML_OUT.write_text(build_html(bc), encoding="utf-8")
    print(f"HTML  {HTML_OUT}")

    probe = run_probe(bc)
    print("PROBE " + json.dumps(probe, ensure_ascii=False))
    tol = 1  # mm を px にしたときの丸め（279mm = 1054.49px）で 1 px ずれる
    fits = (probe["docScrollW"] <= PAGE_W_PX and probe["docScrollH"] <= PAGE_H_PX
            and probe["pageScrollH"] <= probe["pageClientH"] + tol
            and probe["pageScrollW"] <= probe["pageClientW"] + tol
            and probe["footBottom"] <= probe["pageBottom"]
            and all(c["contentH"] <= c["boxH"] for c in probe["cols"])
            and all(c["scrollW"] <= c["clientW"] + tol for c in probe["cols"]))
    print("FIT   " + ("OK" if fits else "OVERFLOW")
          + "  列の中身の高さ/入れ物 " + " ".join(f"{c['contentH']}/{c['boxH']}"
                                                  for c in probe["cols"]))

    if not a.no_pdf:
        flag = make_pdf()
        info = verify_pdf(bc)
        a4 = (abs(info["w"] - 842) <= 1 and abs(info["h"] - 595) <= 1)
        print(f"PDF   {PDF_OUT}  flag={flag}  pages={info['pages']}  "
              f"{info['w']:.2f}x{info['h']:.2f}pt  A4横={'OK' if a4 else 'NG'}  "
              f"1ページ={'OK' if info['pages'] == 1 else 'NG'}")
        print(f"TEXT  PDF の中に葉 {info['leaves']} 件と答え 3 件: "
              + ("すべてある" if not info["missing"] else "欠け " + str(info["missing"])))
        fits = fits and info["pages"] == 1 and a4 and not info["missing"]
    size = make_png(probe["innerH"])
    print(f"PNG   {PNG_OUT}  {size[0]}x{size[1]} px")
    print("FONT  " + subprocess.run(["fc-match", "Noto Sans JP"],
                                    capture_output=True, text=True).stdout.strip())
    return 0 if fits else 1


if __name__ == "__main__":
    raise SystemExit(main())

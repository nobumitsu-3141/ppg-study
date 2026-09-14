# -*- coding: utf-8 -*-
"""解析の一覧の「B. 一覧表」（45 行・9 列）を A4 横の複数ページに組んで印刷用 PDF にする。

行のデータは build_catalog.py の ROWS をそのまま読む（本文は書き写さない）。
列の見出しも build_catalog.build_md() が出す markdown の表から取り出して使う。

    python3 make_table_pdf.py
    python3 make_table_pdf.py --no-pdf
    python3 make_table_pdf.py --selftest

出力:
    docs/research/analysis_catalog_table.html  組版した HTML
    docs/research/analysis_catalog_table.pdf   Chromium の --print-to-pdf で出した A4 横（複数ページ）
    /tmp/table_p1.png ／ /tmp/table_last.png   確認用のラスタ画像（PyMuPDF があるとき）

組み方:
    9 列はどのページでも 9 列のまま。table-layout: fixed で列幅を mm で決め打ちし、
    thead を table-header-group にして見出しを各ページで繰り返す。
    tr は break-inside: avoid なので、1 行がページをまたいで割れることはない。
    ページの見出しと番号は CSS の @page 余白領域（@top-left・@bottom-right）で出す。
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
HTML_OUT = REPO / "docs" / "research" / "analysis_catalog_table.html"
PDF_OUT = REPO / "docs" / "research" / "analysis_catalog_table.pdf"
PROBE_OUT = Path("/tmp/catalog_table_probe.html")
PNG_FIRST = Path("/tmp/table_p1.png")
PNG_LAST = Path("/tmp/table_last.png")

# A4 横（96 dpi の画素数と、印刷できる範囲）
PAGE_W_PX = 1123
PRINT_W_MM = 277.0          # 列幅の合計。297mm − 左右の余白 8mm − 余裕
PRINT_H_MM = 210.0 - 10.0 - 13.0   # 上 10mm・下 13mm の余白を引いた高さ
PX_PER_MM = 96.0 / 25.4

# 列の幅（mm）。合計は PRINT_W_MM。
COL_MM = [12.0, 15.0, 15.0, 37.0, 34.0, 30.0, 34.0, 55.0, 45.0]

# 種別の色。本研究の作図と同じ Okabe-Ito 系（build_catalog.KIND_CLASS の区分名で引く）。
KIND_COLOR = {
    "conf": "#0072B2",
    "expl": "#D55E00",
    "meth": "#009E73",
    "sens": "#56B4E9",
    "tool": "#777777",
}

# 論文ごとのまとまり。(paper の文字列に含まれるか調べる語, 見出しの名前)
# 上から順に調べ、どれにも当たらない行は最後のまとまりに入れる。
GROUPS = [
    ("論文1", "論文1（研究1・1b・1c・1d を含む）"),
    ("論文2", "論文2"),
    ("論文3", "論文3"),
    (None, "共通・道具（どの論文にも属さないもの）"),
]

NOTE = ("数値はすべて結果ファイル・原稿の表・lab_log の追記から引き、出典を各行に併記した。"
        "全体像（A4 1 枚）は analysis_catalog_a4.pdf。")
HEAD_FMT = "解析の一覧 ― B. 一覧表（{date}）"

# 文字の大きさ（pt）
FS_CELL = 6.8
FS_HEAD = 7.0
FS_NO = 6.2
FS_CHIP = 6.0
FS_GROUP = 7.4
FS_NOTE = 7.0
FS_MARGIN = 6.5
LH_CELL = 1.32


# ---------------------------------------------------------------- データの読み込み
def load_source():
    """build_catalog.py を module として読む。"""
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
    import build_catalog as bc  # noqa: E402
    return bc


def header_labels(bc) -> list[str]:
    """build_md() が書く markdown の表から、列の見出しを 9 つ取り出す。

    見出しを手で書き写すと本体とずれるので、出力そのものから読む。
    """
    for ln in bc.build_md().splitlines():
        if ln.startswith("| 番号 |"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cells) == 9:
                return cells
    raise SystemExit("build_md() の中に 9 列の見出し行が見つからない")


def catalog_date(bc) -> str:
    m = re.search(r"（(\d{4}-\d{2}-\d{2})）", bc.TITLE)
    return m.group(1) if m else ""


def group_index(paper: str) -> int:
    """論文の欄の文字列から、どのまとまりに入れるかを決める。"""
    for i, (key, _) in enumerate(GROUPS):
        if key is not None and key in paper:
            return i
    return len(GROUPS) - 1


def group_rows(rows) -> list[tuple[str, list]]:
    """行を論文ごとのまとまりに分ける。まとまりの中は元の順（番号の順）のまま。"""
    buckets: list[list] = [[] for _ in GROUPS]
    for r in rows:
        buckets[group_index(r["paper"])].append(r)
    return [(label, buckets[i]) for i, (_, label) in enumerate(GROUPS)]


def group_title(label: str, n: int) -> str:
    return f"{label} ― {n} 行"


# ---------------------------------------------------------------- 文字の変換
def e(s: str) -> str:
    return htmllib.escape(s, quote=False)


def cell_html(bc, s: str) -> str:
    """セルの markdown を HTML にする。**強調** は <strong>、逆引用符は落とす。"""
    return bc.md_strong_to_html(s.replace("`", ""))


def cell_text(s: str) -> str:
    """PDF に出るはずの素の文字列（強調の印と逆引用符を落としたもの）。"""
    return s.replace("`", "").replace("**", "")


def tint(hexcolor: str, frac: float = 0.16) -> str:
    """種別の印の下地。白に混ぜてうすくする（文字は黒のまま読める）。"""
    h = hexcolor.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    mixed = [round(255 - (255 - v) * frac) for v in rgb]
    return "#%02X%02X%02X" % tuple(mixed)


# ---------------------------------------------------------------- HTML の組み立て
def build_css(bc, date: str, caption: bool) -> str:
    cols = "\n".join(
        f".ct col:nth-child({i + 1}) {{ width: {w}mm; }}" for i, w in enumerate(COL_MM))
    chips = "\n".join(
        f'.k-{k} {{ border-color: {c}; background: {tint(c)}; }}'
        for k, c in KIND_COLOR.items())
    margin_boxes = "" if caption else f"""
  @top-left {{
    content: "{HEAD_FMT.format(date=date)}";
    font-family: "Noto Sans JP", "WenQuanYi Zen Hei", sans-serif;
    font-size: {FS_MARGIN}pt; color: #5E5C57; vertical-align: bottom;
  }}
  @bottom-right {{
    content: "p " counter(page) " / " counter(pages);
    font-family: "Noto Sans JP", "WenQuanYi Zen Hei", sans-serif;
    font-size: {FS_MARGIN}pt; color: #5E5C57; vertical-align: top;
  }}"""
    return f"""
@page {{
  size: A4 landscape;
  margin: 10mm 8mm 13mm 8mm;{margin_boxes}
}}
* {{ box-sizing: border-box; }}
html, body {{
  margin: 0; padding: 0; background: #FFFFFF; color: #17181A;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; color-adjust: exact;
}}
body {{
  font-family: "Noto Sans JP", "WenQuanYi Zen Hei", sans-serif;
  font-variant-numeric: tabular-nums;
}}
@media screen {{
  body {{ padding: 10mm 8mm 13mm; background: #F4F2EE; }}
  .ct {{ background: #FFFFFF; }}
}}

.note {{
  font-size: {FS_NOTE}pt; line-height: 1.45; color: #4A4843;
  margin: 0 0 2.4mm; max-width: {PRINT_W_MM}mm;
}}

.ct {{
  width: {PRINT_W_MM}mm; table-layout: fixed; border-collapse: collapse;
}}
{cols}
.ct caption {{
  caption-side: top; text-align: left; font-size: 9pt; font-weight: 700;
  padding: 0 0 2.0mm; letter-spacing: .04em;
}}
thead {{ display: table-header-group; }}
tfoot {{ display: table-footer-group; }}
tr {{ break-inside: avoid; page-break-inside: avoid; }}

.ct th, .ct td {{
  vertical-align: top; text-align: left; padding: 1.05mm 1.15mm;
  border-bottom: .3pt solid #DCD9D3;
  font-size: {FS_CELL}pt; line-height: {LH_CELL}; font-weight: 400;
  overflow-wrap: anywhere; word-break: normal;
}}
.ct thead th {{
  font-size: {FS_HEAD}pt; font-weight: 700; background: #EDEAE4; color: #17181A;
  border-top: .6pt solid #8E8A82; border-bottom: .6pt solid #8E8A82;
  padding: 1.2mm 1.15mm; letter-spacing: .02em;
}}
.ct tbody tr.alt td, .ct tbody tr.alt th {{ background: #FAF9F6; }}
.ct tbody tr.grp td {{
  background: #E6E3DD; font-size: {FS_GROUP}pt; font-weight: 700;
  padding: 1.5mm 1.15mm; letter-spacing: .04em;
  border-top: .6pt solid #8E8A82; border-bottom: .4pt solid #B4B0A8;
  break-after: avoid; page-break-after: avoid;
}}
.c-no {{
  font-family: "DejaVu Sans Mono", "Noto Sans JP", monospace;
  font-size: {FS_NO}pt; color: #24262A;
}}
.chip {{
  display: inline-block; font-size: {FS_CHIP}pt; line-height: 1.25;
  padding: .25mm .7mm; border-radius: 1.2pt; border: .4pt solid #999;
  color: #17181A; background: #EEEEEE;
}}
{chips}
.ct strong {{ font-weight: 700; }}
#probe-json {{ display: none; }}
"""


PROBE_JS = """
<script>
(function () {
  var t = document.querySelector('.ct');
  var over = [];
  [].forEach.call(document.querySelectorAll('.ct td, .ct th'), function (c) {
    if (c.scrollWidth > c.clientWidth + 1) {
      over.push({txt: (c.textContent || '').slice(0, 18),
                 s: c.scrollWidth, c: c.clientWidth});
    }
  });
  var rows = [].map.call(document.querySelectorAll('.ct tbody tr'), function (r) {
    return {no: (r.cells[0].textContent || '').trim().slice(0, 26),
            h: Math.round(r.getBoundingClientRect().height)};
  });
  var hi = rows.slice().sort(function (a, b) { return b.h - a.h; }).slice(0, 3);
  var out = {
    docScrollW: document.documentElement.scrollWidth,
    tableW: Math.round(t.getBoundingClientRect().width),
    tableScrollW: t.scrollWidth, tableClientW: t.clientWidth,
    headW: [].map.call(document.querySelectorAll('.ct thead th'), function (h) {
      return Math.round(h.getBoundingClientRect().width); }),
    rows: rows.length, overflow: over, tallest: hi,
    sumH: rows.reduce(function (a, r) { return a + r.h; }, 0),
    font: getComputedStyle(document.querySelector('.ct tbody td')).fontSize
  };
  var p = document.createElement('pre');
  p.id = 'probe-json';
  p.textContent = 'PROBE' + JSON.stringify(out) + 'ENDPROBE';
  document.body.appendChild(p);
})();
</script>
"""


def build_html(bc, rows, heads, date: str, caption: bool = False, probe: bool = False) -> str:
    """1 つの表（9 列）を組む。caption=True のときは見出しを表の caption に置く。"""
    o: list[str] = []
    a = o.append
    a('<table class="ct">')
    if caption:
        a(f"  <caption>{e(HEAD_FMT.format(date=date))}</caption>")
    a("  <colgroup>" + "".join("<col>" for _ in COL_MM) + "</colgroup>")
    a("  <thead><tr>")
    for h in heads:
        a(f'    <th scope="col">{e(h)}</th>')
    a("  </tr></thead>")
    a("  <tbody>")
    for label, group in group_rows(rows):
        a(f'    <tr class="grp"><td colspan="{len(heads)}">'
          f"{e(group_title(label, len(group)))}</td></tr>")
        for i, r in enumerate(group):
            cls = bc.KIND_CLASS[r["kind"]]
            a(f'    <tr class="{"alt" if i % 2 else "row"}">')
            a(f'      <th scope="row" class="c-no">{e(r["no"])}</th>')
            a(f'      <td>{e(r["paper"])}</td>')
            a(f'      <td><span class="chip k-{cls}">{e(r["kind"])}</span></td>')
            for key in ("aim", "idx", "data", "cmp", "res", "found"):
                a(f'      <td>{cell_html(bc, r[key])}</td>')
            a("    </tr>")
    a("  </tbody>")
    a("</table>")
    table = "\n".join(o)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>解析の一覧 ― B. 一覧表</title>
<style>{build_css(bc, date, caption)}</style>
</head>
<body>
<p class="note">{e(NOTE)}</p>
{table}
</body>{PROBE_JS if probe else ""}
</html>
"""


# ---------------------------------------------------------------- Chromium の呼び出し
def chromium() -> str:
    hits = sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))
    if not hits:
        raise SystemExit("chromium が見つからない")
    return hits[0]


def run_chrome(extra, timeout=240):
    cmd = [chromium(), "--headless", "--no-sandbox", "--disable-gpu",
           "--hide-scrollbars", "--force-device-scale-factor=1"] + extra
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def make_pdf() -> str:
    url = "file://" + str(HTML_OUT)
    for flag in ("--no-pdf-header-footer", "--print-to-pdf-no-header"):
        if PDF_OUT.exists():
            PDF_OUT.unlink()
        r = run_chrome([flag, f"--print-to-pdf={PDF_OUT}", url])
        if PDF_OUT.exists() and PDF_OUT.stat().st_size > 0:
            return flag
        sys.stderr.write(f"[{flag}] 失敗\n{r.stdout}\n{r.stderr}\n")
    raise SystemExit("PDF を作れなかった")


def run_probe(bc, rows, heads, date) -> dict:
    PROBE_OUT.write_text(build_html(bc, rows, heads, date, probe=True), encoding="utf-8")
    r = run_chrome([f"--window-size={PAGE_W_PX},900", "--dump-dom", "file://" + str(PROBE_OUT)])
    m = re.search(r"PROBE(\{.*?\})ENDPROBE", r.stdout, re.S)
    if not m:
        raise SystemExit("プローブの出力を読めなかった:\n" + r.stdout[-2000:] + r.stderr[-2000:])
    return json.loads(htmllib.unescape(m.group(1)))


# ---------------------------------------------------------------- PDF の検査
# NFKC は康熙部首（U+2F00–U+2FD5）を漢字に戻すが、CJK 部首補助（U+2E80–U+2EF3）には
# 対応表が無いので手で書く。⻑（U+2ED1）は「ウィンドウ長」の長で実際に出た。
PDF_TR = {ord("‧"): "・", ord("∕"): "/", ord("⁄"): "/", ord("⻑"): "長"}


def _norm(s: str) -> str:
    """PDF から取り出した文字列と元の文字列を比べるための正規化。

    Noto Sans JP の ToUnicode は一部の字を部首の符号位置に写すので漢字に戻し、
    中黒・斜線の異体と空白を揃えてから比べる。
    """
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", s).translate(PDF_TR))


def verify_pdf(rows, heads, date: str) -> dict:
    from pypdf import PdfReader
    rd = PdfReader(str(PDF_OUT))
    pages = [_norm(p.extract_text()) for p in rd.pages]
    sizes = [(float(p.mediabox.width), float(p.mediabox.height)) for p in rd.pages]
    n = len(pages)

    head_key = _norm(heads[3])          # 「示したかったこと」
    run_head = _norm(HEAD_FMT.format(date=date))
    miss_head = [i + 1 for i, t in enumerate(pages) if head_key not in t]
    miss_run = [i + 1 for i, t in enumerate(pages) if run_head not in t]
    miss_pageno = [i + 1 for i, t in enumerate(pages)
                   if _norm(f"p {i + 1} / {n}") not in t]

    groups = [(group_title(label, len(g)), g) for label, g in group_rows(rows)]
    miss_group = [g for g, _ in groups if not any(_norm(g) in t for t in pages)]

    # 行がページをまたいで割れていないこと。番号と「分かったこと」の先頭 12 字が
    # 同じページに出れば、その行はそのページに収まっている。
    where: dict[str, list[int]] = {}
    split: list[str] = []
    missing: list[str] = []
    for r in rows:
        no = _norm(r["no"])
        tail = _norm(cell_text(r["found"]))[:12]
        both = [i + 1 for i, t in enumerate(pages) if no in t and tail in t]
        anyno = [i + 1 for i, t in enumerate(pages) if no in t]
        if not anyno:
            missing.append(r["no"])
        elif not both:
            split.append(r["no"])
        where[r["no"]] = both
    per_page = {i + 1: 0 for i in range(n)}
    for r in rows:
        if where[r["no"]]:
            per_page[where[r["no"]][0]] += 1

    dup = [no for no, ps in where.items() if len(ps) > 1]

    return dict(pages=n, sizes=sizes, per_page=per_page, where=where, dup=dup,
                miss_head=miss_head, miss_run=miss_run, miss_pageno=miss_pageno,
                miss_group=miss_group, split=split, missing=missing,
                groups=[(g, len(x)) for g, x in groups])


def make_previews() -> str:
    """1 ページ目と最後のページを 110 dpi の PNG にする。"""
    try:
        import pymupdf
    except ImportError:
        return "PyMuPDF が無いので画像は作らなかった（pip install pymupdf）"
    doc = pymupdf.open(str(PDF_OUT))
    out = []
    for path, idx in ((PNG_FIRST, 0), (PNG_LAST, doc.page_count - 1)):
        pm = doc[idx].get_pixmap(dpi=110)
        pm.save(str(path))
        out.append(f"{path}（p{idx + 1}, {pm.width}x{pm.height}）")
    doc.close()
    return "  ".join(out)


# ---------------------------------------------------------------- 自己検査
def fake_rows() -> list[dict]:
    """自己検査用の作り物の行（本物の ROWS は使わない）。"""
    def row(no, paper, kind, tag):
        return dict(no=no, paper=paper, kind=kind,
                    aim=f"{tag} のねらい", idx=f"{tag} の指標",
                    data=f"{tag} のデータ", cmp=f"{tag} の比較",
                    res=f"**{tag} の結果** `code_{tag}.py` <&>",
                    found=f"{tag} で分かったこと 0123456789")
    return [
        row("A1番", "論文1", "確認的（事前登録）", "あ"),
        row("A2番", "共通（論文1）", "道具", "い"),
        row("A3番", "論文1b B-1", "感度解析", "う"),
        row("A4番", "論文1（探索）", "探索的（凍結後）", "え"),
        row("B1番", "論文2", "方法の検証", "お"),
        row("B2番", "論文3／論文2", "探索的（事後）", "か"),
        row("C1番", "論文3", "確認的（事前登録）", "き"),
        row("D1番", "共通", "道具", "く"),
        row("D2番", "―", "道具", "け"),
    ]


def selftest() -> int:
    bc = load_source()
    ok = True

    def chk(name, cond, detail=""):
        nonlocal ok
        print(("PASS  " if cond else "FAIL  ") + name + (("  " + detail) if detail else ""))
        if not cond:
            ok = False

    rows = fake_rows()
    heads = header_labels(bc)
    date = catalog_date(bc)

    chk("列の見出しは 9 つ", len(heads) == 9, " | ".join(heads))
    chk("見出しに「示したかったこと」がある", heads[3] == "示したかったこと", heads[3])
    chk("見出しは build_md() の表と同じ",
        "| " + " | ".join(heads) + " |" in bc.build_md())
    chk("日付を取り出せる", bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", date)), date)

    chk("列幅は 9 つ", len(COL_MM) == 9, str(COL_MM))
    chk("列幅の合計が印刷できる幅と同じ", abs(sum(COL_MM) - PRINT_W_MM) < 1e-9,
        f"{sum(COL_MM)} / {PRINT_W_MM}")

    chk("論文1 に入る", [group_index(p) for p in
                         ("論文1", "共通（論文1）", "論文1b B-1", "論文1c C-2", "論文1（探索）")]
        == [0] * 5)
    chk("論文2・論文3 に入る", group_index("論文2") == 1 and group_index("論文3") == 2)
    chk("論文3／論文2 は先に当たる論文2 に入る", group_index("論文3／論文2") == 1)
    chk("どれにも当たらない行は共通・道具",
        group_index("共通") == 3 and group_index("―") == 3)

    gr = group_rows(rows)
    chk("まとまりは 4 つ", len(gr) == 4, str([g[0] for g in gr]))
    chk("行の数はまとまりに分けても変わらない", sum(len(g[1]) for g in gr) == len(rows))
    chk("まとまりの中は元の順のまま",
        [r["no"] for r in gr[0][1]] == ["A1番", "A2番", "A3番", "A4番"])
    chk("まとまりの見出しに行数が入る",
        group_title(gr[0][0], len(gr[0][1])) == "論文1（研究1・1b・1c・1d を含む） ― 4 行")

    chk("強調は <strong>、逆引用符は落ちる",
        cell_html(bc, "**あ**い`x`") == "<strong>あ</strong>いx",
        cell_html(bc, "**あ**い`x`"))
    chk("HTML の特殊文字を逃がす", cell_html(bc, "<&>") == "&lt;&amp;&gt;")
    chk("素の文字列から印を落とす", cell_text("**あ**`x`") == "あx")
    chk("印の下地は白寄りでうすい", tint("#0072B2") == "#D6E8F3", tint("#0072B2"))
    chk("PDF の文字を比べる前の正規化",
        _norm("ウィンドウ⻑ ‧ ＋１") == _norm("ウィンドウ長・+1"),
        _norm("ウィンドウ⻑ ‧ ＋１"))

    doc = build_html(bc, rows, heads, date)
    chk("A4 横の指定", "size: A4 landscape" in doc)
    chk("余白の指定", "margin: 10mm 8mm 13mm 8mm" in doc)
    chk("印刷時に色を出す指定", "print-color-adjust: exact" in doc)
    chk("見出しを各ページで繰り返す", "display: table-header-group" in doc)
    chk("行を割らない", "break-inside: avoid" in doc and "page-break-inside: avoid" in doc)
    chk("列幅を決め打ちする", "table-layout: fixed" in doc)
    chk("長い文字列を折り返す", "overflow-wrap: anywhere" in doc)
    chk("ページの見出しと番号は @page の余白領域",
        "@top-left" in doc and 'counter(page) " / " counter(pages)' in doc)
    chk("caption は既定では出さない", "<caption>" not in doc)
    chk("caption に切り替えられる",
        "<caption>" in build_html(bc, rows, heads, date, caption=True)
        and "@top-left" not in build_html(bc, rows, heads, date, caption=True))
    chk("前書きの 1 行が入っている", e(NOTE) in doc)
    chk("表は 1 つだけ", doc.count("<table") == 1)
    chk("行の数（見出し 1 ＋ まとまり 4 ＋ 本体 9）",
        doc.count("<tr") == 1 + len(GROUPS) + len(rows), str(doc.count("<tr")))
    chk("列の数はどの行も 9",
        all(doc.count(f'<th scope="row"') == len(rows) for _ in (0,))
        and doc.count("<td") == len(rows) * 8 + len(GROUPS))
    for r in rows:
        body = [e(r["no"]), e(r["paper"]), e(r["kind"]),
                cell_html(bc, r["aim"]), cell_html(bc, r["res"]), cell_html(bc, r["found"])]
        chk(f'{r["no"]} の中身が入っている', all(x in doc for x in body))
    for label, g in gr:
        chk(f"{label} の見出しが入っている", e(group_title(label, len(g))) in doc)
    for kind, cls in bc.KIND_CLASS.items():
        chk(f"種別「{kind}」に色がある", cls in KIND_COLOR and f".k-{cls}" in doc)
    chk("種別の印は黒い文字", "color: #17181A;" in doc)

    chk("行の高さの見込みが 1 ページに収まる",
        PRINT_H_MM * PX_PER_MM > 700, f"{PRINT_H_MM}mm")

    banned = ("錨", "窓", "天井", "帯域", "化ける", "足切り", "予行", "配管", "土俵",  # 用語の引用
              "鍵点", "肩", "ふらつき", "売り文句", "正本", "ランドマーク")  # 用語の引用
    mine = [NOTE, HEAD_FMT, "解析の一覧 ― B. 一覧表"] + [g[1] for g in GROUPS]
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
    rows, heads, date = bc.ROWS, header_labels(bc), catalog_date(bc)
    HTML_OUT.write_text(build_html(bc, rows, heads, date), encoding="utf-8")
    print(f"HTML  {HTML_OUT}  {HTML_OUT.stat().st_size:,} bytes  行 {len(rows)}・列 {len(heads)}")
    for label, g in group_rows(rows):
        print(f"      {group_title(label, len(g))}")

    probe = run_probe(bc, rows, heads, date)
    limit = PRINT_H_MM * PX_PER_MM
    tall = [r for r in probe["tallest"] if r["h"] > limit]
    print("PROBE " + json.dumps({k: probe[k] for k in
                                 ("tableW", "headW", "rows", "tallest", "font")},
                                ensure_ascii=False))
    fits = not probe["overflow"] and not tall
    print(f"FIT   {'OK' if fits else 'NG'}  列からはみ出したセル {len(probe['overflow'])} 件・"
          f"1 ページより高い行 {len(tall)} 件（上限 {limit:.0f}px）")
    if probe["overflow"]:
        print("      " + json.dumps(probe["overflow"][:4], ensure_ascii=False))

    if a.no_pdf:
        return 0 if fits else 1

    flag = make_pdf()
    info = verify_pdf(rows, heads, date)
    a4 = all(abs(w - 841.9) <= 1 and abs(h - 595) <= 1 for w, h in info["sizes"])
    margin_ok = not info["miss_pageno"] and not info["miss_run"]
    if not margin_ok:
        # @page の余白領域が出なかったときは、見出しを表の caption に置きなおす。
        print("WARN  @page の余白領域が出ない。見出しを caption に移して作りなおす")
        HTML_OUT.write_text(build_html(bc, rows, heads, date, caption=True), encoding="utf-8")
        flag = make_pdf()
        info = verify_pdf(rows, heads, date)
        a4 = all(abs(w - 841.9) <= 1 and abs(h - 595) <= 1 for w, h in info["sizes"])

    print(f"PDF   {PDF_OUT}  flag={flag}  ページ {info['pages']}  "
          f"{info['sizes'][0][0]:.1f}x{info['sizes'][0][1]:.1f}pt  A4横={'OK' if a4 else 'NG'}")
    print("ROWS  ページごとの行数 " +
          " ".join(f"p{p}:{n}" for p, n in info["per_page"].items()) +
          f"  合計 {sum(info['per_page'].values())} / {len(rows)}")
    print(f"TEXT  番号の欠け {info['missing'] or 'なし'}／"
          f"ページをまたいだ行 {info['split'] or 'なし'}／"
          f"2 ページに出た行 {info['dup'] or 'なし'}")
    print(f"HEAD  「{heads[3]}」が無いページ {info['miss_head'] or 'なし'}／"
          f"走りの見出しが無いページ {info['miss_run'] or 'なし'}／"
          f"ページ番号が無いページ {info['miss_pageno'] or 'なし'}")
    print(f"GROUP {info['miss_group'] and ('欠け ' + str(info['miss_group'])) or 'まとまりの見出し 4 件すべてある'}")
    print("PNG   " + make_previews())
    print("FONT  " + subprocess.run(["fc-match", "Noto Sans JP"],
                                    capture_output=True, text=True).stdout.strip())

    good = (fits and a4 and not info["missing"] and not info["split"]
            and not info["miss_head"] and not info["miss_group"]
            and sum(info["per_page"].values()) == len(rows))
    print("RESULT " + ("OK" if good else "NG"))
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())

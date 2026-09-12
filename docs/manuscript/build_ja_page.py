#!/usr/bin/env python3
"""2 本の和文原稿（.md）を機械的に 1 枚の HTML に組む。転記は一切しない。

使い方（引数は 2 つ。出力先、次に雛形）:

    python3 docs/manuscript/build_ja_page.py 出力先.html docs/manuscript/ja_shell.html

雛形の <!--NAV--> と <!--DOCS--> を置き換える。頁の日付は雛形の側にある。
"""
import html, re, sys
from pathlib import Path

ROOT = Path('/home/user/ppg-study')
DOCS = [
    ("p1", "論文1", "研究1・VitalDB 862例", ROOT / 'docs/manuscript/05_draft_ja.md'),
    ("p2", "論文2", "研究0・PWDB 4,374名", ROOT / 'docs/manuscript/paper2/05_draft_ja.md'),
]

def inline(t):
    t = html.escape(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'`(.+?)`', r'<code>\1</code>', t)
    return t

def convert(md, pid):
    out, i, lines = [], 0, md.split('\n')
    n = 0
    while i < len(lines):
        s = lines[i].rstrip()
        t = s.strip()
        if not t:
            i += 1; continue
        if t.startswith('# '):                      # ファイル見出しは落とす（ページ側で出す）
            i += 1; continue
        if t.startswith('---'):
            out.append('<hr>'); i += 1; continue
        if t.startswith('> '):                      # 引用（作業メモ）
            buf = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                buf.append(lines[i].strip().lstrip('>').strip()); i += 1
            out.append('<aside class="memo">' + inline(' '.join(buf)) + '</aside>'); continue
        if t.startswith('|'):                       # 表
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
            body = [r for r in rows if not all(set(c) <= set('-: ') for c in r)]
            if not body: continue
            head, rest = body[0], body[1:]
            th = ''.join(f'<th>{inline(c)}</th>' for c in head)
            tr = ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in rest)
            out.append(f'<div class="scroll"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>')
            continue
        m = re.match(r'^【(.+?)】$', t)              # 書誌事項の見出し
        if m:
            n += 1
            out.append(f'<h3 class="bib" id="{pid}-b{n}"><span>【</span>{inline(m.group(1))}<span>】</span></h3>')
            i += 1; continue
        m = re.match(r'^〈(.+?)〉$', t)              # 本文の節
        if m:
            n += 1
            out.append(f'<h3 class="sec" id="{pid}-s{n}">{inline(m.group(1))}</h3>')
            i += 1; continue
        if s.startswith('　'):                    # 数式行・字下げ行
            out.append(f'<p class="ind">{inline(t)}</p>'); i += 1; continue
        if t.startswith('〔') and t.endswith('〕'):   # 未記入の枠
            out.append(f'<p class="todo">{inline(t)}</p>'); i += 1; continue
        # 段落: 「見出し語　本文」の形（全角空白区切り）は見出し語を立てる
        m = re.match(r'^([^\s　]{2,14})　(.+)$', t)
        if m and not t.startswith(('図', '表')):
            out.append(f'<p><span class="run">{inline(m.group(1))}</span>{inline(m.group(2))}</p>')
        else:
            cls = ' class="cap"' if re.match(r'^(図|表)\d', t) else ''
            out.append(f'<p{cls}>{inline(t)}</p>')
        i += 1
    return '\n'.join(out)

parts, nav = [], []
for pid, label, sub, path in DOCS:
    md = path.read_text(encoding='utf-8')
    title = ''
    m = re.search(r'【表題】\s*\n\s*\n(.+)', md)
    if m: title = m.group(1).strip()
    nav.append(f'<a href="#{pid}">{label}<span>{sub}</span></a>')
    parts.append(
        f'<article id="{pid}" class="doc">\n'
        f'<header class="dhead"><p class="eyebrow">{label}　和文原稿</p>'
        f'<h2>{html.escape(title)}</h2>'
        f'<p class="src">{html.escape(str(path.relative_to(ROOT)))}</p></header>\n'
        + convert(md, pid) + '\n</article>')

print(f"docs: {len(parts)}", file=sys.stderr)
Path(sys.argv[1]).write_text(
    Path(sys.argv[2]).read_text(encoding='utf-8')
        .replace('<!--NAV-->', '\n'.join(nav))
        .replace('<!--DOCS-->', '\n'.join(parts)),
    encoding='utf-8')

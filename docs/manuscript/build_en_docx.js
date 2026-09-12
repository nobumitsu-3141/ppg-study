// 英文原稿（markdown）を Word ファイルにする。
// 原稿 md を機械的に読むだけで、本文の書き写しや言い換えは一切行わない。
//   実行例:
//     NODE_PATH=<docx のある node_modules> node docs/manuscript/build_en_docx.js \
//       --src docs/manuscript/v2/01_draft_en_v2.md \
//       --out docs/manuscript/v2/paper1_draft_en_v2.docx
//
// 対応する記法
//   #・##・### ............ 見出し 1・2・3
//   段落 .................. 連続する行を 1 段落に連結する（md は 90 桁で折り返してある）
//   **太字**・*斜体* ...... 文字の装飾
//   | で区切られた表 ...... Word の表。先頭行を見出し、|---| の行は読み飛ばす
//   - ..................... 箇条書き（2 字下げの続き行は同じ項目に連結する）
//   1. ................... 番号付き文献リスト。通常段落として出す（3 字下げの続き行を連結）
//   > ..................... 引用符を外して通常段落として出す
//   ![alt](path) .......... 図は埋め込まず、代替テキストだけの段落にする
//   --- ................... 読み飛ばす
//   `[[ ]]` の注記は原文のまま残す。
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Footer, PageNumber, AlignmentType,
  HeadingLevel, Table, TableRow, TableCell, WidthType, BorderStyle,
} = require('docx');

const FONT = 'Times New Roman';
const BLACK = '000000';
const SIZE = 22;          // 11 pt（half-point 単位）
const LINE = 276;         // 行間 1.15（240 × 1.15）
const MARGIN = 1417;      // 25 mm（25 / 25.4 × 1440 twips）

const argOf = name => {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 ? process.argv[i + 1] : undefined;
};

// ---- 行内の装飾 ----------------------------------------------------------
// **太字** と *斜体* だけを見る。対になっていない * はそのままの文字として残す。
function inline(text, base = {}) {
  const runs = [];
  const re = /\*\*([^*]+?)\*\*|\*([^*\n]+?)\*/g;
  let last = 0;
  let m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) runs.push(mk(text.slice(last, m.index), base));
    if (m[1] !== undefined) runs.push(mk(m[1], { ...base, bold: true }));
    else runs.push(mk(m[2], { ...base, italics: true }));
    last = m.index + m[0].length;
  }
  if (last < text.length) runs.push(mk(text.slice(last), base));
  return runs.length ? runs : [mk('', base)];
}

const mk = (text, o = {}) =>
  new TextRun({ text, font: FONT, color: BLACK, size: SIZE, ...o });

const para = (text, o = {}) => new Paragraph({
  children: inline(text),
  spacing: { after: 120, line: LINE },
  ...o,
});

const heading = (text, level) => new Paragraph({
  heading: level,
  children: inline(text, { bold: true, size: level === HeadingLevel.HEADING_1 ? 28
    : level === HeadingLevel.HEADING_2 ? 26 : 24 }),
  spacing: { before: 280, after: 140, line: LINE },
});

const bullet = text => new Paragraph({
  children: inline(text),
  bullet: { level: 0 },
  spacing: { after: 80, line: LINE },
});

// ---- 表 ------------------------------------------------------------------
const cells = row => row.replace(/^\|/, '').replace(/\|$/, '').split('|').map(s => s.trim());
const isSep = row => /^\|[\s:\-|]+\|$/.test(row.trim());

function table(rows) {
  const grid = rows.filter(r => !isSep(r)).map(cells);
  const width = Math.max(...grid.map(r => r.length));
  const border = { style: BorderStyle.SINGLE, size: 1, color: '999999' };
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: grid.map((r, i) => new TableRow({
      tableHeader: i === 0,
      children: Array.from({ length: width }, (_, j) => new TableCell({
        borders: { top: border, bottom: border, left: border, right: border },
        margins: { top: 40, bottom: 40, left: 80, right: 80 },
        children: [new Paragraph({
          children: inline(r[j] || '', i === 0 ? { bold: true } : {}),
          spacing: { after: 0, line: LINE },
        })],
      })),
    })),
  });
}

// ---- md を読んで Word の要素の並びにする ---------------------------------
function convert(md) {
  const lines = md.split('\n');
  const out = [];
  let buf = [];                      // 連結中の段落の行

  const flush = () => {
    if (!buf.length) return;
    const text = buf.join(' ').replace(/\s+/g, ' ').trim();
    buf = [];
    if (!text) return;
    const img = text.match(/^!\[([^\]]*)\]\([^)]*\)$/);
    out.push(para(img ? img[1] : text));
  };

  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];
    const line = raw.replace(/\s+$/, '');

    if (!line.trim()) { flush(); continue; }
    if (/^---+$/.test(line.trim())) { flush(); continue; }

    const h = line.match(/^(#{1,3})\s+(.*)$/);
    if (h) {
      flush();
      out.push(heading(h[2].trim(),
        h[1].length === 1 ? HeadingLevel.HEADING_1
        : h[1].length === 2 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3));
      continue;
    }

    if (line.trimStart().startsWith('|')) {
      flush();
      const rows = [];
      while (i < lines.length && lines[i].trimStart().startsWith('|')) rows.push(lines[i++]);
      i--;
      out.push(table(rows));
      out.push(new Paragraph({ children: [mk('')], spacing: { after: 80, line: LINE } }));
      continue;
    }

    if (/^-\s+/.test(line)) {
      flush();
      const item = [line.replace(/^-\s+/, '')];
      while (i + 1 < lines.length && /^\s{2,}\S/.test(lines[i + 1]) && lines[i + 1].trim()) {
        item.push(lines[++i].trim());
      }
      out.push(bullet(item.join(' ')));
      continue;
    }

    if (/^\d+\.\s+/.test(line)) {
      flush();
      const item = [line];
      while (i + 1 < lines.length && /^\s{2,}\S/.test(lines[i + 1]) && lines[i + 1].trim()) {
        item.push(lines[++i].trim());
      }
      out.push(para(item.join(' ').replace(/\s+/g, ' ')));
      continue;
    }

    if (/^>\s?/.test(line)) {
      flush();
      const item = [line.replace(/^>\s?/, '')];
      while (i + 1 < lines.length && /^>\s?/.test(lines[i + 1])) {
        item.push(lines[++i].replace(/^>\s?/, ''));
      }
      out.push(para(item.join(' ').replace(/\s+/g, ' ').trim()));
      continue;
    }

    buf.push(line.trim());
  }
  flush();
  return out;
}

function build({ src, out }) {
  const children = convert(fs.readFileSync(src, 'utf8'));
  const doc = new Document({
    styles: { default: { document: { run: { font: FONT, size: SIZE, color: BLACK } } } },
    sections: [{
      properties: { page: {
        size: { width: 11906, height: 16838 },
        margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN },
      } },
      footers: { default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: BLACK })],
      })] }) },
      children,
    }],
  });
  return Packer.toBuffer(doc).then(b => {
    fs.mkdirSync(path.dirname(out), { recursive: true });
    fs.writeFileSync(out, b);
    console.log(`wrote ${out}  ${b.length} bytes  要素${children.length}`);
  });
}

const src = argOf('src');
const out = argOf('out');
if (!src || !out) {
  console.error('使い方: node docs/manuscript/build_en_docx.js --src <md> --out <docx>');
  process.exit(1);
}
build({ src, out }).catch(e => { console.error(e.message); process.exit(1); });

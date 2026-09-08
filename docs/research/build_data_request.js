// 取得依頼の md を Word にする。教授報告と同じ体裁（游明朝・A4・色なし）。
//   NODE_PATH=<docx のある node_modules> node docs/research/build_data_request.js
const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, AlignmentType, BorderStyle, VerticalAlign, Footer, PageNumber,
} = require('docx');

const [SRC, OUT] = process.argv.slice(2);
if (!SRC || !OUT) { console.error('usage: node build_data_request.js <src.md> <out.docx>'); process.exit(1); }
const FONT = '游明朝';
const BK = '000000';
const W = 9638;
const LINE = { style: BorderStyle.SINGLE, size: 4, color: BK };
const THIN = { style: BorderStyle.SINGLE, size: 2, color: BK };

const runs = (text, o = {}) => text.split(/(\*\*[^*]+\*\*)/).filter(Boolean).map(seg => {
  const b = seg.startsWith('**') && seg.endsWith('**');
  return new TextRun({ text: b ? seg.slice(2, -2) : seg, bold: b, font: FONT, color: BK, ...o });
});
const p = (t, o = {}) => new Paragraph({
  children: runs(t, o.run || {}),
  spacing: { before: o.before ?? 0, after: o.after ?? 120, line: 300 },
  indent: o.indent,
});
const h1 = t => new Paragraph({
  children: [new TextRun({ text: t, bold: true, size: 26, font: FONT, color: BK })],
  spacing: { before: 380, after: 160, line: 300 },
});
const h2 = t => new Paragraph({
  children: [new TextRun({ text: t, bold: true, size: 22, font: FONT, color: BK })],
  spacing: { before: 260, after: 110, line: 300 },
});

const cell = (text, width, head) => new TableCell({
  width: { size: width, type: WidthType.DXA },
  margins: { top: 55, bottom: 55, left: 95, right: 95 },
  verticalAlign: VerticalAlign.TOP,
  borders: head ? { bottom: LINE } : undefined,
  children: [new Paragraph({
    children: runs(text, { size: 18, bold: head || undefined }),
    spacing: { after: 0, line: 250 },
  })],
});
function tbl(rows) {
  const n = rows[0].length;
  const len = Array.from({ length: n }, (_, j) =>
    Math.max(...rows.map(r => (r[j] || '').replace(/\*\*/g, '').length), 4));
  const tot = len.reduce((a, b) => a + b, 0);
  const widths = len.map(l => Math.max(700, Math.round(W * l / tot)));
  const scale = W / widths.reduce((a, b) => a + b, 0);
  const wf = widths.map(w => Math.round(w * scale));
  return new Table({
    columnWidths: wf,
    width: { size: W, type: WidthType.DXA },
    borders: {
      top: LINE, bottom: LINE,
      left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
      insideHorizontal: THIN, insideVertical: { style: BorderStyle.NONE },
    },
    rows: rows.map((r, i) => new TableRow({
      tableHeader: i === 0,
      children: r.map((c, j) => cell(c, wf[j], i === 0)),
    })),
  });
}

const lines = fs.readFileSync(SRC, 'utf8').split('\n');
const out = [];
for (let i = 0; i < lines.length; i++) {
  const t = lines[i].trim();
  if (!t || t === '---') continue;
  if (t.startsWith('| ')) {                                   // 表
    const rows = [];
    while (i < lines.length && lines[i].trim().startsWith('|')) {
      rows.push(lines[i].trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim()));
      i++;
    }
    i--;
    out.push(tbl(rows.filter(r => !r.every(c => /^[-: ]*$/.test(c)))));
    out.push(new Paragraph({ children: [], spacing: { after: 140 } }));
    continue;
  }
  if (t.startsWith('> ')) {                                   // 引用
    const buf = [];
    while (i < lines.length && lines[i].trim().startsWith('>')) {
      buf.push(lines[i].trim().replace(/^>\s?/, '')); i++;
    }
    i--;
    out.push(p(buf.join(''), { indent: { left: 420 }, after: 150 }));
    continue;
  }
  if (t.startsWith('# ')) { out.push(h1(t.slice(2))); continue; }
  if (t.startsWith('## ')) { out.push(h1(t.slice(3))); continue; }
  if (t.startsWith('### ')) { out.push(h2(t.slice(4))); continue; }
  if (/^[-*] /.test(t)) { out.push(p('・' + t.slice(2), { indent: { left: 210 }, after: 70 })); continue; }
  const num = t.match(/^(\d+)\. (.*)$/);
  if (num) { out.push(p(num[1] + '．' + num[2], { indent: { left: 210 }, after: 70 })); continue; }
  out.push(p(t));
}

const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: 21, color: BK } } } },
  sections: [{
    properties: { page: {
      size: { width: 11906, height: 16838 },
      margin: { top: 1134, right: 1134, bottom: 1134, left: 1134 },
    } },
    footers: { default: new Footer({ children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: BK })],
    })] }) },
    children: out,
  }],
});
Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(OUT, b);
  console.log(`wrote ${OUT}  ${b.length} bytes  要素${out.length}`);
});

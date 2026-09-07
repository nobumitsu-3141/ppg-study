const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, AlignmentType, BorderStyle, HeadingLevel, VerticalAlign,
  Footer, PageNumber,
} = require('docx');

const FONT = '游明朝';
const W = 9638;                       // A4(11906) − 余白(1134×2)
const LINE = { style: BorderStyle.SINGLE, size: 4, color: '000000' };
const THIN = { style: BorderStyle.SINGLE, size: 2, color: '000000' };

function runs(text, opts = {}) {
  const out = [];
  text.split(/(\*\*[^*]+\*\*)/).forEach(seg => {
    if (!seg) return;
    const b = seg.startsWith('**') && seg.endsWith('**');
    out.push(new TextRun({ text: b ? seg.slice(2, -2) : seg, bold: b, font: FONT, color: '000000', ...opts }));
  });
  return out;
}
const p = (text, o = {}) => new Paragraph({
  children: runs(text, o.run || {}),
  spacing: { after: o.after ?? 120, line: o.line ?? 300 },
  indent: o.indent,
  alignment: o.align,
});
const h1 = (text) => new Paragraph({
  children: [new TextRun({ text, bold: true, size: 26, font: FONT, color: '000000' })],
  spacing: { before: 340, after: 150 },
  heading: HeadingLevel.HEADING_1,
});
const h2 = (text) => new Paragraph({
  children: [new TextRun({ text, bold: true, size: 22, font: FONT, color: '000000' })],
  spacing: { before: 240, after: 100 },
  heading: HeadingLevel.HEADING_2,
});
const cap = (text) => new Paragraph({
  children: [new TextRun({ text, bold: true, size: 19, font: FONT, color: '000000' })],
  spacing: { before: 170, after: 70 },
});
const gap = (n = 130) => new Paragraph({ children: [], spacing: { after: n } });

const cell = (text, width, head, align) => new TableCell({
  width: { size: width, type: WidthType.DXA },
  margins: { top: 55, bottom: 55, left: 95, right: 95 },
  verticalAlign: VerticalAlign.TOP,
  borders: head ? { bottom: LINE } : undefined,
  children: [new Paragraph({
    children: runs(text, { size: 19, bold: head || undefined }),
    spacing: { after: 0, line: 255 },
    alignment: align,
  })],
});

function tbl(widths, rows) {
  return new Table({
    columnWidths: widths,
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    borders: {
      top: LINE, bottom: LINE,
      left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
      insideHorizontal: THIN,
      insideVertical: { style: BorderStyle.NONE },
    },
    rows: rows.map((r, i) => new TableRow({
      tableHeader: i === 0,
      children: r.map((c, j) => cell(
        c, widths[j], i === 0,
        i > 0 && j > 0 && /^[-−+0-9.,%〜 ―—]+$/.test(c.replace(/\*\*/g, '')) ? AlignmentType.RIGHT : undefined,
      )),
    })),
  });
}

module.exports = { Document, Packer, Paragraph, TextRun, Footer, PageNumber, AlignmentType, FONT, W, p, h1, h2, cap, tbl, gap, runs };

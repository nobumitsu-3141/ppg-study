const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, BorderStyle, HeadingLevel,
  Footer, PageNumber, VerticalAlign,
} = require('docx');

const FONT = '游明朝';
const W = 9638;                 // A4 (11906) - margins (1134*2)

// ---- inline rich text: **bold** ----
function runs(text, opts = {}) {
  const out = [];
  text.split(/(\*\*[^*]+\*\*)/).forEach(seg => {
    if (!seg) return;
    const b = seg.startsWith('**') && seg.endsWith('**');
    out.push(new TextRun({ text: b ? seg.slice(2, -2) : seg, bold: b, font: FONT, ...opts }));
  });
  return out;
}
const p = (text, o = {}) => new Paragraph({
  children: runs(text, o.run || {}),
  spacing: { after: o.after ?? 120, line: o.line ?? 300 },
  alignment: o.align,
  indent: o.indent,
});
const h1 = (text) => new Paragraph({
  children: [new TextRun({ text, bold: true, size: 26, color: '2E74B5', font: FONT })],
  spacing: { before: 320, after: 160 },
  heading: HeadingLevel.HEADING_1,
});
const h2 = (text) => new Paragraph({
  children: [new TextRun({ text, bold: true, size: 22, font: FONT })],
  spacing: { before: 220, after: 110 },
  heading: HeadingLevel.HEADING_2,
});
const cap = (text) => new Paragraph({
  children: [new TextRun({ text, bold: true, size: 19, font: FONT })],
  spacing: { before: 180, after: 80 },
});

const cell = (text, width, { head = false, align } = {}) => new TableCell({
  width: { size: width, type: WidthType.DXA },
  shading: head ? { type: ShadingType.CLEAR, fill: 'EDF2F7' } : undefined,
  margins: { top: 60, bottom: 60, left: 90, right: 90 },
  verticalAlign: VerticalAlign.TOP,
  children: [new Paragraph({
    children: runs(text, { size: 19, bold: head || undefined }),
    spacing: { after: 0, line: 260 },
    alignment: align,
  })],
});

function tbl(widths, rows) {
  return new Table({
    columnWidths: widths,
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    borders: {
      top:    { style: BorderStyle.SINGLE, size: 4, color: 'B7C3CE' },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: 'B7C3CE' },
      left:   { style: BorderStyle.SINGLE, size: 4, color: 'B7C3CE' },
      right:  { style: BorderStyle.SINGLE, size: 4, color: 'B7C3CE' },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: 'D6DEE6' },
      insideVertical:   { style: BorderStyle.SINGLE, size: 2, color: 'D6DEE6' },
    },
    rows: rows.map((r, i) => new TableRow({
      tableHeader: i === 0,
      children: r.map((c, j) => cell(c, widths[j], { head: i === 0, align: i > 0 && j > 0 && /^[-−+0-9.—]+$/.test(c) ? AlignmentType.RIGHT : undefined })),
    })),
  });
}
const gap = (n = 120) => new Paragraph({ children: [], spacing: { after: n } });

module.exports = { Document, Packer, Paragraph, TextRun, Footer, PageNumber, AlignmentType, FONT, W, p, h1, h2, cap, tbl, gap, runs };

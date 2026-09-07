const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, Footer, PageNumber, AlignmentType } = require('docx');
const FONT = '游明朝';
const main = require('./build_report.js').body;
const app  = require('./build_appendix.js').body;

const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: 21 } } } },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1134, right: 1134, bottom: 1134, left: 1134 },
      },
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18 })],
        })],
      }),
    },
    children: [...main, ...app],
  }],
});

Packer.toBuffer(doc).then(b => {
  fs.writeFileSync('研究報告_2026-09-07.docx', b);
  console.log('wrote', b.length, 'bytes');
});

// 和文原稿の【和文要旨】【本文】だけを Word ファイルにする。
// 原稿 md を機械的に読むだけで、本文の書き写しは一切行わない。
//   実行例: NODE_PATH=<docx のある node_modules> node docs/manuscript/build_ja_docx.js
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Footer, PageNumber, AlignmentType,
} = require('docx');

const FONT = '游明朝';
const BLACK = '000000';
const EM = 210;                       // 全角1字 = 10.5 pt = 210 twips

const TARGETS = [
  { src: 'docs/manuscript/05_draft_ja.md',        out: 'docs/manuscript/論文1_和文要旨_本文.docx' },
  { src: 'docs/manuscript/paper2/05_draft_ja.md', out: 'docs/manuscript/paper2/論文2_和文要旨_本文.docx' },
];

const block = (text, name) => {
  const m = text.match(new RegExp(`^【${name}】$([\\s\\S]*?)(?=^【)`, 'm'));
  if (!m) throw new Error(`【${name}】が見つからない`);
  // 行頭の全角空白は数式行の目印なので落とさない
  return m[1].split('\n').map(s => s.replace(/\s+$/, '')).filter(Boolean);
};

const run = (text, o = {}) => new TextRun({ text, font: FONT, color: BLACK, ...o });

const title = t => new Paragraph({
  children: [run(t, { bold: true, size: 22 })],
  spacing: { after: 300, line: 320 },
});
const head = t => new Paragraph({
  children: [run(t, { bold: true, size: 22 })],
  spacing: { before: 340, after: 160, line: 300 },
});
const sect = t => new Paragraph({
  children: [run(t, { bold: true })],
  spacing: { before: 260, after: 120, line: 300 },
});
// 数式行（行頭が全角空白）。字下げせず、太字化もしない。
const eq = line => new Paragraph({
  children: [new TextRun({ text: line, font: FONT, color: BLACK })],
  spacing: { before: 90, after: 90, line: 300 },
});
// 段落。行頭の「見出し語　」および要旨の「目的：」等のラベルだけを太字にする。
const para = (line, { label = false } = {}) => {
  const kids = [];
  let rest = line;
  const lead = label
    ? line.match(/^(目的|方法|結果|結論)：/)
    : line.match(/^(.{2,30}?)　(?=.{20})/);
  if (lead) { kids.push(run(lead[0], { bold: true })); rest = line.slice(lead[0].length); }
  kids.push(run(rest));
  return new Paragraph({
    children: kids,
    spacing: { after: 120, line: 300 },
    indent: { firstLine: EM },
  });
};

function build({ src, out }) {
  const md = fs.readFileSync(src, 'utf8');
  const children = [title(block(md, '表題')[0])];
  children.push(head('【和文要旨】'));
  block(md, '和文要旨').forEach(l => children.push(para(l, { label: true })));
  children.push(head('【本文】'));
  block(md, '本文').forEach(l => children.push(
    /^　/.test(l) ? eq(l) : /^〈.+〉$/.test(l) ? sect(l) : para(l)));

  const doc = new Document({
    styles: { default: { document: { run: { font: FONT, size: 21, color: BLACK } } } },
    sections: [{
      properties: { page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1134, right: 1134, bottom: 1134, left: 1134 },
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
    console.log(`wrote ${out}  ${b.length} bytes  段落${children.length}`);
  });
}

TARGETS.reduce((p, t) => p.then(() => build(t)), Promise.resolve())
  .catch(e => { console.error(e.message); process.exit(1); });

# 論文和訳（日本語全訳）

PPG／血管老化に関する5本の論文の日本語全訳。本文・図キャプション・表・数式・引用文献を、
要約や意訳・短縮なしに原文へ忠実に訳出している。原文の節番号・見出し構成・段落構成を保持。

| ファイル | 原著 | 頁数 |
|---|---|---|
| `01_Rubins_2008_ja.pdf` | Rubins U. *Finger and ear photoplethysmogram waveform analysis by fitting with Gaussians.* Med Biol Eng Comput 2008;46:1271–1276 | 7 |
| `02_Westerhof_2008_ja.pdf` | Westerhof BE, van den Wijngaard JP, Murgo JP, Westerhof N. *Location of a Reflection Site Is Elusive.* Hypertension 2008;52:478–483 | 10 |
| `03_Volkov_2017_ja.pdf` | Volkov MV, et al. *Video capillaroscopy clarifies mechanism of the photoplethysmographic waveform appearance.* Sci Rep 2017;7:13298 | 10 |
| `04_Aminuddin_2018_ja.pdf` | Aminuddin A, et al. *Effect of increasing heart rate on finger photoplethysmography fitness index (PPGF)…* PLoS ONE 2018;13:e0207301 | 11 |
| `05_Zanelli_2024_VascAgeNet_ja.pdf` | Zanelli S, et al. *Developing technologies to assess vascular ageing: a roadmap from VascAgeNet.* Physiol Meas 2024;45:121001 | 98 |

## 訳出方針

- **本文**は逐文訳。要約・省略・意訳を行っていない。
- **図キャプション**は全訳。図中の英語ラベルが理解に必要な場合のみ「［図中の表記］」として訳語を補記した（Rubins 2008 図2、Westerhof 2008 図1・図2）。
- **表**は表題・全セル・脚注を訳出（Aminuddin 2018 表1–4、Zanelli 2024 表1–2）。
- **数式**は原著の記号・添字のまま再現。
- **引用文献リスト**は書誌情報のため原文のまま収録。
- 略号は初出時に日本語訳を併記し、以降は原著どおり略号を使用。
- 原著の文献引用形式（`[1]`、`文献 n`、`Roth et al 2017`）はそのまま残した。

## 生成方法

HTML（`*_ja.html`）＋ `style.css` を WeasyPrint で A4 PDF 化。和文フォントは Noto Serif CJK JP。

```bash
pip install weasyprint pymupdf
apt-get install -y fonts-noto-cjk
python3 -c "
from weasyprint import HTML
import glob
for f in sorted(glob.glob('*_ja.html')):
    HTML(f).write_pdf(f.replace('.html','.pdf'))
"
```

# 論文和訳（日本語全訳）

PPG／パルスオキシメトリ／血管老化に関する10本の論文の日本語全訳。本文・図キャプション・表・数式・
引用文献を、要約や意訳・短縮なしに原文へ忠実に訳出している。原文の節番号・見出し構成・段落構成を保持。

## 血管老化・脈波解析

| ファイル | 原著 | 頁数 |
|---|---|---|
| `01_Rubins_2008_ja.pdf` | Rubins U. *Finger and ear photoplethysmogram waveform analysis by fitting with Gaussians.* Med Biol Eng Comput 2008;46:1271–1276 | 7 |
| `02_Westerhof_2008_ja.pdf` | Westerhof BE, van den Wijngaard JP, Murgo JP, Westerhof N. *Location of a Reflection Site Is Elusive.* Hypertension 2008;52:478–483 | 10 |
| `03_Volkov_2017_ja.pdf` | Volkov MV, et al. *Video capillaroscopy clarifies mechanism of the photoplethysmographic waveform appearance.* Sci Rep 2017;7:13298 | 10 |
| `04_Aminuddin_2018_ja.pdf` | Aminuddin A, et al. *Effect of increasing heart rate on finger photoplethysmography fitness index (PPGF)…* PLoS ONE 2018;13:e0207301 | 11 |
| `05_Zanelli_2024_VascAgeNet_ja.pdf` | Zanelli S, et al. *Developing technologies to assess vascular ageing: a roadmap from VascAgeNet.* Physiol Meas 2024;45:121001 | 96 |

## 周術期モニタリング・パルスオキシメトリ

| ファイル | 原著 | 頁数 |
|---|---|---|
| `06_Coutrot_2019_ja.pdf` | Coutrot M, et al. *Noninvasive continuous detection of arterial hypotension during induction of anaesthesia using a photoplethysmographic signal: proof of concept.* Br J Anaesth 2019;122:605–612 | 12 |
| `07_Aoyagi_2003_ja.pdf` | Aoyagi T（青柳卓雄）. *Pulse oximetry: its invention, theory, and future.* J Anesth 2003;17:259–266 | 12 |
| `08_Chan_2013_ja.pdf` | Chan ED, Chan MM, Chan MM. *Pulse oximetry: Understanding its basic principles facilitates appreciation of its limitations.* Respir Med 2013;107:789–799 | 18 |
| `09_Thiele_2011_ja.pdf` | Thiele RH, et al. *Relationship Between Plethysmographic Waveform Changes and Hemodynamic Variables…* J Cardiothorac Vasc Anesth 2011;25:1044–1050 | 10 |
| `10_Colquhoun_2013_ja.pdf` | Colquhoun D, Dunn LK, McMurry T, Thiele RH. *The relationship between the area of peripherally-derived pressure volume loops and systemic vascular resistance.* J Clin Monit Comput 2013 | 7 |

## 訳出方針

- **本文**は逐文訳。要約・省略・意訳を行っていない。
- **図キャプション**は全訳。図中の英語ラベルが理解に必要な場合のみ「［図中の表記］」として訳語を補記した（Rubins 2008 図2、Westerhof 2008 図1・図2、Coutrot 2019 図3、Chan 2013 図1・2・5、Thiele 2011 図2・5）。
- **表**は表題・全セル・脚注を訳出（Aminuddin 2018 表1–4、Zanelli 2024 表1–2、Coutrot 2019 表1–2、Chan 2013 表1、Thiele 2011 表1–2、Colquhoun 2013 表1）。**Box**（Chan 2013 Box 1–2）、**編集者の要点欄**（Coutrot 2019）も全訳。
- **数式**は原著の記号・添字のまま再現。テキスト抽出で壊れた数式は原著ページ画像から復元した（Rubins 2008 式1–4、Aminuddin 2018 PPGF 式、Aoyagi 2003 全数式、Colquhoun 2013 PVA 式）。
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

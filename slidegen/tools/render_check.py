#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pptx を 1 枚ずつ PNG に落として目視確認できるようにする（read-only）。

lint(slide_lint.py) は座標とフォントサイズしか見ない。文字の重なり方や図の収まりは
実際に描画しないと分からないため、LibreOffice で PDF 化し pdftoppm で分割する。

  python3 tools/render_check.py <deck.pptx> [--out DIR] [--dpi N] [--slides 1,3,5]

【重要】Linux での描画はメイリオではなく代替フォントによるものである。
fontconfig/meiryo-alias.conf を入れていれば Noto Sans CJK JP で描かれる。
本番の PowerPoint(メイリオ)より字面がやや小さくなるため、
ここで「ちょうど収まっている」ものは本番で溢れうる。最終判断は Mac の PowerPoint で行う。
"""
import argparse, os, shutil, subprocess, sys, glob


def need(cmd):
    if shutil.which(cmd) is None:
        sys.exit(f"エラー: {cmd} が見つからない。setup-linux.sh を実行するか {cmd} を導入すること。")
    return cmd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx")
    ap.add_argument("--out", default=None, help="出力先（既定: <pptx と同じ場所>/_render）")
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--slides", default=None, help="例 1,3,5 / 省略で全枚")
    a = ap.parse_args()

    src = os.path.abspath(a.pptx)
    if not os.path.isfile(src):
        sys.exit(f"エラー: 見つからない: {src}")
    out = os.path.abspath(a.out or os.path.join(os.path.dirname(src), "_render"))
    os.makedirs(out, exist_ok=True)

    need("soffice"); need("pdftoppm")

    # fontconfig の対応づけが効いているか警告
    try:
        m = subprocess.run(["fc-match", "Meiryo"], capture_output=True, text=True).stdout.strip()
        if "CJK JP" not in m:
            print(f"⚠ Meiryo が日本語フォントに解決されていない: {m}", file=sys.stderr)
            print("  漢字が中国語字体で描かれる。fontconfig/meiryo-alias.conf を導入すること。", file=sys.stderr)
    except FileNotFoundError:
        pass

    print(f"PDF 変換中: {os.path.basename(src)}")
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", out, src],
                   check=True, capture_output=True, timeout=600)
    pdf = os.path.join(out, os.path.splitext(os.path.basename(src))[0] + ".pdf")
    if not os.path.isfile(pdf):
        sys.exit("エラー: PDF 変換に失敗した。")

    cmd = ["pdftoppm", "-png", "-r", str(a.dpi)]
    if a.slides:
        nums = [int(x) for x in a.slides.split(",") if x.strip()]
        for n in nums:
            subprocess.run(cmd + ["-f", str(n), "-l", str(n), pdf, os.path.join(out, "slide")],
                           check=True, capture_output=True)
    else:
        subprocess.run(cmd + [pdf, os.path.join(out, "slide")], check=True, capture_output=True)

    pngs = sorted(glob.glob(os.path.join(out, "slide*.png")))
    total = sum(os.path.getsize(p) for p in pngs)
    print(f"完了: {len(pngs)} 枚 / {total/1e6:.1f} MB -> {out}")
    print("注意: 本番の PowerPoint(メイリオ)とは字面が異なる。最終確認は Mac で行うこと。")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tile out/s-*.png slide renders into QC contact sheets (4/sheet, 2 cols, high-res)."""
import glob, os, math
from PIL import Image

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "out"))
pngs = sorted(glob.glob(os.path.join(OUT, "s-*.png")))
PER, COLS, TW, PAD = 4, 2, 760, 10
thumbs = []
for p in pngs:
    im = Image.open(p).convert("RGB")
    r = TW / im.width
    thumbs.append(im.resize((TW, int(im.height * r))))
if thumbs:
    th = thumbs[0].height
    for si in range(0, len(thumbs), PER):
        chunk = thumbs[si:si + PER]
        rows = math.ceil(len(chunk) / COLS)
        sheet = Image.new("RGB", (COLS * TW + (COLS + 1) * PAD, rows * th + (rows + 1) * PAD), "white")
        for i, im in enumerate(chunk):
            r, c = divmod(i, COLS)
            sheet.paste(im, (PAD + c * (TW + PAD), PAD + r * (th + PAD)))
        sheet.save(os.path.join(OUT, f"qc_{si // PER + 1}.png"))
    print("slides:", len(thumbs), "sheets:", math.ceil(len(thumbs) / PER))

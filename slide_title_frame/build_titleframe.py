#!/usr/bin/env python3
# Build framed-title versions of SpO2PPG deck in three Japanese fonts.
import os, re, shutil, subprocess, unicodedata, glob

WORK = os.path.dirname(os.path.abspath(__file__))
SRC_UNPACKED = os.path.join(WORK, "unpacked")
EMU = 914400

# advance estimate (inches) per glyph at 44pt -- deliberately generous (over-estimate)
FULL, HALF = 0.66, 0.38
PAD = 0.30          # inner padding text<->frame (each side)
LEFT_OUTSET = 0.20  # frame left sits this far left of the title box left edge
CHIP_GAP = 0.14     # frame right must clear the chapter chips by this margin
TOP, HGT = 0.66, 0.88          # content-slide frame band, hugs the (low-centered) title line
FRAME_FILL = None              # None => noFill (pure frame); or "F7F8FA"
FRAME_LINE = "44546A"          # slate (theme dk2)
FRAME_W = 28575                # 2.25pt
ROUND_ADJ = 8000               # ~8% corner radius

def is_full(ch):
    return unicodedata.east_asian_width(ch) in ("W", "F", "A")

def advance_in(text):
    return sum(FULL if is_full(c) else HALF for c in text)

def title_text(xml, sp):
    # concatenate <a:t> inside the title sp
    return "".join(re.findall(r"<a:t>(.*?)</a:t>", sp, re.S))

def plate_xml(sp_id, x, y, cx, cy):
    fill = "<a:noFill/>" if FRAME_FILL is None else f'<a:solidFill><a:srgbClr val="{FRAME_FILL}"/></a:solidFill>'
    return (
        "<p:sp>"
        "<p:nvSpPr>"
        f'<p:cNvPr id="{sp_id}" name="TitleFrame"/>'
        "<p:cNvSpPr/>"
        "<p:nvPr/>"
        "</p:nvSpPr>"
        "<p:spPr>"
        f'<a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        f'<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val {ROUND_ADJ}"/></a:avLst></a:prstGeom>'
        f"{fill}"
        f'<a:ln w="{FRAME_W}" cap="flat"><a:solidFill><a:srgbClr val="{FRAME_LINE}"/></a:solidFill><a:round/></a:ln>'
        "</p:spPr>"
        "<p:txBody>"
        '<a:bodyPr rtlCol="0" anchor="ctr"/><a:lstStyle/><a:p><a:endParaRPr lang="ja-JP"/></a:p>'
        "</p:txBody>"
        "</p:sp>"
    )

def chip_min_left(xml):
    # min a:off x among shapes whose top<0.9in and left>7.0in
    lefts = []
    for m in re.finditer(r'<a:off x="(-?\d+)" y="(-?\d+)"/>', xml):
        x = int(m.group(1)); y = int(m.group(2))
        if y < int(0.9 * EMU) and x > int(7.0 * EMU):
            lefts.append(x)
    return min(lefts) if lefts else None

def process_slide(path):
    xml = open(path, encoding="utf-8").read()
    # locate title placeholder sp
    ph = xml.find('<p:ph type="title"')
    if ph == -1:
        return xml, False
    sp_start = xml.rfind("<p:sp>", 0, ph)
    sp_end = xml.find("</p:sp>", ph) + len("</p:sp>")
    sp = xml[sp_start:sp_end]
    # placeholder left/top from its xfrm
    off = re.search(r'<a:off x="(-?\d+)" y="(-?\d+)"/>', sp)
    ph_left = int(off.group(1)) / EMU
    text = title_text(xml, sp)
    ids = [int(i) for i in re.findall(r'id="(\d+)"', xml)]
    new_id = (max(ids) + 1) if ids else 900

    slide_no = int(re.search(r"slide(\d+)\.xml", path).group(1))
    if slide_no == 1:
        # title slide: centered plate around the (bottom-anchored, centered) title line
        x, y, cx, cy = 2.00, 2.96, 9.33, 0.90
    else:
        text_start = ph_left + 0.10
        adv = advance_in(text)
        right_hug = text_start + adv + PAD
        chip = chip_min_left(xml)
        cap = (chip / EMU - CHIP_GAP) if chip else 12.30
        right = min(cap, right_hug)
        left = ph_left - LEFT_OUTSET
        x, y, cx, cy = left, TOP, right - left, HGT

    plate = plate_xml(new_id, round(x * EMU), round(y * EMU), round(cx * EMU), round(cy * EMU))
    new_xml = xml[:sp_start] + plate + xml[sp_start:]
    return new_xml, True

# 1) build framed slide XMLs (font-neutral: still Meiryo)
framed = {}
for path in sorted(glob.glob(os.path.join(SRC_UNPACKED, "ppt/slides/slide*.xml")),
                   key=lambda p: int(re.search(r"slide(\d+)", p).group(1))):
    new_xml, ok = process_slide(path)
    framed[os.path.basename(path)] = new_xml
    if not ok:
        print("WARN no title:", path)

print(f"framed {len(framed)} slides")

# 2) emit three font versions
FONTS = {
    "Meiryo": "Meiryo",
    "NotoSansJP": "Noto Sans JP",
    "BIZ-UDPGothic": "BIZ UDPGothic",
}
OUT = os.path.join(WORK, "out")
os.makedirs(OUT, exist_ok=True)
for tag, fontname in FONTS.items():
    build = os.path.join(WORK, f"build_{tag}")
    if os.path.exists(build):
        shutil.rmtree(build)
    shutil.copytree(SRC_UNPACKED, build)
    for name, xml in framed.items():
        swapped = xml.replace('typeface="Meiryo"', f'typeface="{fontname}"')
        with open(os.path.join(build, "ppt/slides", name), "w", encoding="utf-8") as f:
            f.write(swapped)
    out_pptx = os.path.join(OUT, f"SpO2PPG_frame_{tag}.pptx")
    if os.path.exists(out_pptx):
        os.remove(out_pptx)
    subprocess.run(["zip", "-Xrq", out_pptx, "."], cwd=build, check=True)
    n = len(re.findall("Meiryo", "".join(framed.values())))
    print(f"built {out_pptx}  (font={fontname}, swapped {n} Meiryo refs/deck)")
print("done")

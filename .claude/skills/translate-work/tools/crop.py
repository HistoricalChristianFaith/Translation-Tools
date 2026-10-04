#!/usr/bin/env python3
"""Crop and enlarge part of a page image, so a doubtful glyph can be read reliably.

    crop.py PAGE.jpg --box 0.12 0.30 0.88 0.40 --out /path/crop.png [--scale 3]
        box = x0 y0 x1 y1 as FRACTIONS of width/height (a horizontal band = one or two lines)
    crop.py PAGE.jpg --band 5 --of 12 --out /path/crop.png
        the 5th of 12 equal horizontal bands (quick scan of a page, top to bottom)
    crop.py PAGE.jpg --downscale 1900 --out /path/page_small.jpg
        a reduced full-page copy (very large scans can be read unreliably at full size)

Then open the output with the Read tool. Use a unique --out name for every crop, in the run's
crops folder (`_source/run/crops/`).
"""

import argparse
import os

from PIL import Image


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    ap.add_argument("--out", required=True)
    ap.add_argument("--box", nargs=4, type=float)
    ap.add_argument("--band", type=int)
    ap.add_argument("--of", type=int, default=10)
    ap.add_argument("--overlap", type=float, default=0.02)
    ap.add_argument("--scale", type=float, default=3.0)
    ap.add_argument("--downscale", type=int, help="longest side in px for a reduced full-page copy")
    a = ap.parse_args()
    im = Image.open(a.image).convert("RGB")
    W, H = im.size
    if a.downscale:
        r = a.downscale / max(W, H)
        out = im.resize((int(W * r), int(H * r)), Image.LANCZOS) if r < 1 else im
    else:
        if a.band:
            h = 1.0 / a.of
            y0 = max(0.0, (a.band - 1) * h - a.overlap)
            y1 = min(1.0, a.band * h + a.overlap)
            box = (0.0, y0, 1.0, y1)
        elif a.box:
            box = a.box
        else:
            ap.error("give --box, --band, or --downscale")
        c = im.crop((int(box[0] * W), int(box[1] * H), int(box[2] * W), int(box[3] * H)))
        out = c.resize((int(c.width * a.scale), int(c.height * a.scale)), Image.LANCZOS)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    out.save(a.out)
    print(f"{a.out} ({out.width}x{out.height})")


if __name__ == "__main__":
    main()

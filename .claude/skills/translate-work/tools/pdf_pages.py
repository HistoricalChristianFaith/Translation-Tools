#!/usr/bin/env python3
"""PDF helper for staging a base edition, a witness, or an oracle supplied as a PDF.

    pdf_pages.py info   FILE.pdf                                  # page count, text layer?, sample text
    pdf_pages.py render FILE.pdf --pages 110-233 --out DIR --prefix cramer [--offset 9] [--dpi 300]
                         # pdf page P -> DIR/<prefix>_p<P-offset>_pdf<PPPP>.jpg ; DIR/index.json updated
    pdf_pages.py text   FILE.pdf --out FILE.txt [--pages a-b]     # pdftotext -layout (whole book or a range)
    pdf_pages.py find   FILE.pdf "phrase" [--max 20]              # which PDF pages contain a phrase (text layer)

--offset is "PDF page = printed page + offset". Check it at BOTH ends of the range on the rendered
images: scans can be duplicated or jumbled, so the offset may change partway through. Render such
ranges in pieces, with a different --offset for each.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"{cmd[0]} failed: {r.stderr.strip()[:300]}")
    return r.stdout


def npages(pdf):
    m = re.search(r"Pages:\s+(\d+)", run(["pdfinfo", pdf]))
    return int(m.group(1)) if m else 0


def rng(spec, total):
    if not spec:
        return 1, total
    lo, _, hi = spec.partition("-")
    return int(lo), int(hi or lo)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("info"); s.add_argument("pdf")
    s = sub.add_parser("render"); s.add_argument("pdf"); s.add_argument("--pages", required=True)
    s.add_argument("--out", required=True); s.add_argument("--prefix", default="base")
    s.add_argument("--offset", type=int, default=0); s.add_argument("--dpi", type=int, default=300)
    s.add_argument("--index-depth", type=int, default=2)
    s = sub.add_parser("text"); s.add_argument("pdf"); s.add_argument("--out", required=True); s.add_argument("--pages")
    s = sub.add_parser("find"); s.add_argument("pdf"); s.add_argument("phrase"); s.add_argument("--max", type=int, default=20)
    a = ap.parse_args()

    if a.cmd == "info":
        n = npages(a.pdf)
        sample = run(["pdftotext", "-f", str(min(20, n)), "-l", str(min(22, n)), "-layout", a.pdf, "-"])
        words = len(sample.split())
        print(f"pages: {n}\ntext layer: {'yes' if words > 50 else 'NO (scanned images only -- OCR needed)'} "
              f"({words} words on sample pages)\nsample: {' '.join(sample.split()[:40])}")
    elif a.cmd == "text":
        cmd = ["pdftotext", "-layout"]
        if a.pages:
            lo, hi = rng(a.pages, 0)
            cmd += ["-f", str(lo), "-l", str(hi)]
        run(cmd + [a.pdf, a.out])
        print(f"{a.out}: {os.path.getsize(a.out) // 1024} KB")
    elif a.cmd == "find":
        n = npages(a.pdf)
        hits = []
        needle = re.sub(r"\s+", " ", a.phrase.lower())
        for p in range(1, n + 1):
            t = re.sub(r"\s+", " ", run(["pdftotext", "-f", str(p), "-l", str(p), a.pdf, "-"]).lower())
            if needle in t:
                hits.append(p)
                if len(hits) >= a.max:
                    break
        print("pdf pages: " + (", ".join(map(str, hits)) if hits else "(not found)"))
    elif a.cmd == "render":
        from PIL import Image  # noqa: PLC0415
        lo, hi = rng(a.pages, npages(a.pdf))
        os.makedirs(a.out, exist_ok=True)
        idx_path = os.path.join(a.out, "index.json")
        index = json.load(open(idx_path, encoding="utf-8"))["pages"] if os.path.exists(idx_path) else []
        have = {p.get("pdf") for p in index}
        src_root = os.path.abspath(os.path.join(a.out, *[".."] * a.index_depth))
        done = 0
        for p in range(lo, hi + 1):
            if p in have:
                continue
            label = str(p - a.offset)
            while label in {x["label"] for x in index}:
                label += "b"
            dest = os.path.join(a.out, f"{a.prefix}_p{label}_pdf{p:04d}.jpg")
            with tempfile.TemporaryDirectory() as td:
                run(["pdftoppm", "-f", str(p), "-l", str(p), "-r", str(a.dpi), "-png", a.pdf, os.path.join(td, "pg")])
                png = [f for f in os.listdir(td) if f.endswith(".png")][0]
                Image.open(os.path.join(td, png)).convert("RGB").save(dest, "JPEG", quality=90)
            index.append({"label": label, "file": os.path.relpath(dest, src_root), "pdf": p})
            done += 1
        index.sort(key=lambda x: x.get("pdf", 0))
        json.dump({"pages": index}, open(idx_path, "w", encoding="utf-8"), indent=1)
        print(f"rendered {done} page(s); index has {len(index)}: {idx_path}")


if __name__ == "__main__":
    main()

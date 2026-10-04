#!/usr/bin/env python3
"""archive.org helper for finding and staging a scanned edition.

    archive_item.py search "origenes werke 1920" [--rows 15]      # advancedsearch: id | year | title
    archive_item.py files  ITEM                                    # the useful files + sizes
    archive_item.py test   ITEM                                    # can the key files actually be downloaded?
    archive_item.py pagemap ITEM --out page_map.json               # leaf -> printed page (page_numbers.json / scandata)
    archive_item.py ocr    ITEM --out FILE                         # download the full-text _djvu.txt
    archive_item.py render ITEM --leaves 339-579 --out DIR --prefix base [--pagemap page_map.json]
                                                                   # leaf images -> DIR/<prefix>_p<PAGE>_leaf<NNNN>.jpg + DIR/index.json
    archive_item.py pdf    ITEM --out FILE.pdf                     # download the item's PDF (for pdf_pages.py)

Rendering fetches single members of the `_jp2.zip` (so the whole zip is never downloaded), decodes
them with `opj_decompress` (OpenJPEG), and saves an RGB JPEG at native resolution. Existing images
are skipped, so a render can be resumed. The printed page comes from the page map, which is
authoritative: page->leaf offsets DRIFT and scans duplicate leaves, so never assume a constant
offset without checking both ends on the images. Leaves with no printed number are labelled
`L<leaf>`. When one printed number has two leaves, the second is labelled `<page>b`.
Known quirks: some multi-volume items 404 on every file. If `test` fails, look for a standalone
item of the same edition (e.g. a single-volume upload), and record the substitute in the report.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "translate-work/1.0 (scholarly staging)"}


def get(url, binary=False, tries=3, timeout=120):
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                data = r.read()
                return data if binary else data.decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001 - network errors of every kind get retried
            last = e
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"GET failed: {url}: {last}")


def metadata(item):
    return json.loads(get(f"https://archive.org/metadata/{urllib.parse.quote(item)}"))


def dl_url(item, name):
    return f"https://archive.org/download/{urllib.parse.quote(item)}/{urllib.parse.quote(name)}"


def pick(files, suffix):
    c = [f["name"] for f in files if f["name"].endswith(suffix)]
    return sorted(c, key=len)[0] if c else None


def cmd_search(a):
    q = urllib.parse.urlencode({"q": a.query, "fl[]": ["identifier", "title", "year", "creator"],
                                "rows": a.rows, "output": "json"}, doseq=True)
    docs = json.loads(get(f"https://archive.org/advancedsearch.php?{q}"))["response"]["docs"]
    for d in docs:
        print(f"{d.get('identifier')} | {d.get('year', '?')} | {str(d.get('title', ''))[:110]}")
    if not docs:
        print("(no results)")


def cmd_files(a):
    md = metadata(a.item)
    print(f"title: {md.get('metadata', {}).get('title')}")
    for f in md.get("files", []):
        if re.search(r"(_jp2\.zip|\.pdf|_djvu\.txt|_page_numbers\.json|_scandata\.xml)$", f["name"]):
            print(f"  {f['name']}  {int(f.get('size', 0)) // 1024} KB  {f.get('format', '')}")


def probe(url):
    req = urllib.request.Request(url, headers=dict(UA, Range="bytes=0-1023"))
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:  # noqa: BLE001
        return f"error: {e.__class__.__name__}"


def cmd_test(a):
    md = metadata(a.item)
    files = md.get("files", [])
    res = {"item": a.item, "title": md.get("metadata", {}).get("title")}
    for suf in ("_jp2.zip", ".pdf", "_djvu.txt", "_page_numbers.json", "_scandata.xml"):
        n = pick(files, suf)
        res[suf] = {"name": n, "status": probe(dl_url(a.item, n)) if n else "absent"}
    z = res["_jp2.zip"]["name"]
    if z:
        stem = z[: -len("_jp2.zip")]
        member = f"{z}/{stem}_jp2/{stem}_0001.jp2"
        res["jp2_member_0001"] = probe(f"https://archive.org/download/{urllib.parse.quote(a.item)}/{urllib.parse.quote(member)}")
    print(json.dumps(res, ensure_ascii=False, indent=1))
    ok = any(isinstance(v, dict) and v.get("status") in (200, 206) for v in res.values())
    sys.exit(0 if ok else 1)


def build_pagemap(item):
    files = metadata(item).get("files", [])
    pn = pick(files, "_page_numbers.json")
    leaf2 = {}
    if pn:
        data = json.loads(get(dl_url(item, pn)))
        for p in data.get("pages", []):
            if p.get("pageNumber"):
                leaf2[int(p["leafNum"])] = str(p["pageNumber"])
    if not leaf2:
        sd = pick(files, "_scandata.xml")
        if sd:
            xml = get(dl_url(item, sd))
            for m in re.finditer(r'<page leafNum="(\d+)">(.*?)</page>', xml, re.S):
                num = re.search(r"<pageNumber>([^<]+)</pageNumber>", m.group(2))
                if num:
                    leaf2[int(m.group(1))] = num.group(1).strip()
    return leaf2


def cmd_pagemap(a):
    leaf2 = build_pagemap(a.item)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({"item": a.item, "leaf_to_page": {str(k): v for k, v in sorted(leaf2.items())}}, f, indent=1)
    if leaf2:
        ks = sorted(leaf2)
        print(f"{len(leaf2)} numbered leaves; first leaf {ks[0]}=p.{leaf2[ks[0]]}, last leaf {ks[-1]}=p.{leaf2[ks[-1]]}")
    else:
        print("no printed page numbers found (map pages by reading running heads on the images)")


def cmd_ocr(a):
    n = pick(metadata(a.item).get("files", []), "_djvu.txt")
    if not n:
        sys.exit("no _djvu.txt in this item")
    txt = get(dl_url(a.item, n))
    open(a.out, "w", encoding="utf-8").write(txt)
    print(f"{a.out}: {txt.count(chr(10))} lines")


def cmd_pdf(a):
    n = pick(metadata(a.item).get("files", []), ".pdf")
    if not n:
        sys.exit("no PDF in this item")
    with open(a.out, "wb") as f:
        f.write(get(dl_url(a.item, n), binary=True, timeout=600))
    print(f"{a.out}: {os.path.getsize(a.out) // 1024} KB")


def leaf_range(spec):
    out = []
    for part in spec.split(","):
        lo, _, hi = part.partition("-")
        out += list(range(int(lo), int(hi or lo) + 1))
    return out


def cmd_render(a):
    from PIL import Image  # noqa: PLC0415 - only needed here
    if not shutil.which("opj_decompress"):
        sys.exit("opj_decompress (OpenJPEG) not found on PATH")
    files = metadata(a.item).get("files", [])
    z = pick(files, "_jp2.zip")
    if not z:
        sys.exit("no _jp2.zip in this item -- use `pdf` + pdf_pages.py instead")
    stem = z[: -len("_jp2.zip")]
    pm = {}
    if a.pagemap:
        pm = {int(k): v for k, v in json.load(open(a.pagemap, encoding="utf-8"))["leaf_to_page"].items()}
    os.makedirs(a.out, exist_ok=True)
    idx_path = os.path.join(a.out, "index.json")
    index = json.load(open(idx_path, encoding="utf-8"))["pages"] if os.path.exists(idx_path) else []
    have = {p["leaf"] for p in index if "leaf" in p}
    labels = {p["label"] for p in index}
    src_root = os.path.abspath(os.path.join(a.out, *[".."] * a.index_depth))
    done = fail = 0
    for leaf in leaf_range(a.leaves):
        if leaf in have:
            continue
        page = pm.get(leaf, f"L{leaf}")
        label = page
        while label in labels:
            label += "b"
        name = f"{a.prefix}_p{label}_leaf{leaf:04d}.jpg"
        dest = os.path.join(a.out, name)
        member = f"{z}/{stem}_jp2/{stem}_{leaf:04d}.jp2"
        url = f"https://archive.org/download/{urllib.parse.quote(a.item)}/{urllib.parse.quote(member)}"
        try:
            with tempfile.TemporaryDirectory() as td:
                jp2, png = os.path.join(td, "l.jp2"), os.path.join(td, "l.png")
                open(jp2, "wb").write(get(url, binary=True))
                subprocess.run(["opj_decompress", "-i", jp2, "-o", png], check=True, capture_output=True)
                im = Image.open(png).convert("RGB")
                if a.scale != 1.0:
                    im = im.resize((int(im.width * a.scale), int(im.height * a.scale)), Image.LANCZOS)
                im.save(dest, "JPEG", quality=90)
        except Exception as e:  # noqa: BLE001
            print(f"  leaf {leaf}: FAILED {e}")
            fail += 1
            continue
        index.append({"label": label, "file": os.path.relpath(dest, src_root), "leaf": leaf})
        labels.add(label)
        done += 1
        if done % 10 == 0:
            json.dump({"pages": sorted(index, key=lambda p: p["leaf"])}, open(idx_path, "w"), indent=1)
            print(f"  ... {done} rendered")
    index.sort(key=lambda p: p.get("leaf", 0))
    json.dump({"pages": index}, open(idx_path, "w", encoding="utf-8"), indent=1)
    print(f"rendered {done}, failed {fail}, index has {len(index)} page(s): {idx_path}")
    sys.exit(1 if fail else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("--rows", type=int, default=15)
    for n in ("files", "test"):
        sub.add_parser(n).add_argument("item")
    s = sub.add_parser("pagemap"); s.add_argument("item"); s.add_argument("--out", required=True)
    s = sub.add_parser("ocr"); s.add_argument("item"); s.add_argument("--out", required=True)
    s = sub.add_parser("pdf"); s.add_argument("item"); s.add_argument("--out", required=True)
    s = sub.add_parser("render"); s.add_argument("item"); s.add_argument("--leaves", required=True)
    s.add_argument("--out", required=True); s.add_argument("--prefix", default="base")
    s.add_argument("--pagemap"); s.add_argument("--scale", type=float, default=1.0)
    s.add_argument("--index-depth", type=int, default=2,
                   help="index paths are relative to this many levels above --out (2 = _source/ for _source/pages/base)")
    a = ap.parse_args()
    {"search": cmd_search, "files": cmd_files, "test": cmd_test, "pagemap": cmd_pagemap,
     "ocr": cmd_ocr, "pdf": cmd_pdf, "render": cmd_render}[a.cmd](a)


if __name__ == "__main__":
    main()

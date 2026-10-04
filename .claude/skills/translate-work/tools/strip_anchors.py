#!/usr/bin/env python3
"""Pass R7: remove inline page/column anchors (e.g. `[GCS p.259]`, `[PG 1320]`, `[JTS 9 p.231]`)
from a base text, touching nothing else.

Anchors are carried through every refinement pass for traceability, then stripped as the LAST
base-text step. The strip must be deletion-only and must never touch genuine editorial brackets,
so the pattern should match ONLY the anchor form (never a bare `\\[.*?\\]`).

Rules, applied identically to every file (and to every mirrored tree, so byte-identity between
trees is preserved by construction):
  1. a line that is nothing but an anchor            -> the whole line is removed
  2. an anchor at line start followed by one space   -> anchor + that space removed
  3. an anchor between two spaces                    -> anchor + one space removed
  4. an anchor at line end preceded by a space       -> anchor + that space removed
  5. any other anchor (mid-word, glued to a word)    -> anchor removed (split words rejoin)

Self-checks per file: no anchor left; no new double / leading / trailing spaces compared with the
pre-strip file; removing every anchor match from the original and deleting all whitespace gives
the same character stream as the result with all whitespace deleted. A file failing any check is
reported as ANOMALY and not written.

    python3 strip_anchors.py --pattern '\\[GCS p\\.\\d+\\]' LATIN/ _source/passB_final/ --dry-run
    python3 strip_anchors.py --pattern '\\[GCS p\\.\\d+\\]' LATIN/ _source/passB_final/ --backup _source/prestrip

Always back up first (--backup copies each file before writing) and log the result to
`_source/anchor_strip.md`. The last line is `GATE strip_anchors: PASS` or
`GATE strip_anchors: FAIL (<n> problem(s))` (n = anomalous files; gate.py).
"""

import argparse
import glob
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate  # noqa: E402


def strip(text, anchor):
    a = anchor.pattern
    text = re.sub(rf"(?m)^[ \t]*(?:{a}[ \t]*)+\n", "", text)   # 1. anchor-only line
    text = re.sub(rf"(?m)^{a} ", "", text)                      # 2. line start + space
    text = re.sub(rf" {a}(?= )", "", text)                      # 3. between spaces
    text = re.sub(rf"(?m) {a}$", "", text)                      # 4. line end
    return anchor.sub("", text)                                 # 5. everything else


def ws_stats(text):
    return (text.count("  "), len(re.findall(r"(?m)^[ \t]+\S", text)), len(re.findall(r"(?m)\S[ \t]+$", text)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pattern", required=True, help="regex matching ONE anchor, e.g. '\\[PG \\d+\\]'")
    ap.add_argument("dirs", nargs="+", help="directories (or files) to strip")
    ap.add_argument("--glob", default="*.txt")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--backup", help="copy every file here (per-tree subfolder) before writing")
    a = ap.parse_args()
    gate.arm("strip_anchors")
    anchor = re.compile(a.pattern)

    files = []
    for d in a.dirs:
        files += sorted(glob.glob(os.path.join(d, a.glob))) if os.path.isdir(d) else [d]
    if not files:
        sys.exit("No files matched.")

    rc, total, bad = 0, 0, 0
    for fp in files:
        orig = open(fp, encoding="utf-8").read()
        n = len(anchor.findall(orig))
        new = strip(orig, anchor)
        left = anchor.findall(new)
        same_stream = re.sub(r"\s", "", anchor.sub("", orig)) == re.sub(r"\s", "", new)
        no_new_ws = all(after <= before for after, before in zip(ws_stats(new), ws_stats(orig)))
        ok = not left and same_stream and no_new_ws
        print(f"{fp}: {n} anchor(s) -> {len(left)} left; char-stream {'identical' if same_stream else 'CHANGED'}; "
              f"ws(dbl,lead,trail) {ws_stats(orig)} -> {ws_stats(new)}  [{'OK' if ok else 'ANOMALY'}]")
        if not ok:
            rc, bad = 1, bad + 1
            continue
        total += n
        if not a.dry_run and new != orig:
            if a.backup:
                dest = os.path.join(a.backup, os.path.basename(os.path.dirname(os.path.abspath(fp))))
                os.makedirs(dest, exist_ok=True)
                shutil.copy2(fp, dest)
            with open(fp, "w", encoding="utf-8") as f:
                f.write(new)
    print(f"\nTOTAL anchors {'that would be ' if a.dry_run else ''}removed: {total}"
          + ("" if rc == 0 else "  (anomalous files were NOT written)"))
    gate.finish(bad)


if __name__ == "__main__":
    gate.guard(main)

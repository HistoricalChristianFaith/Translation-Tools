#!/usr/bin/env python3
"""Evidence for drafting html_config.py: what the English units actually contain.

    mark_census.py --work-dir W [--glob 'english/*_english.txt']

Prints per unit: the first block (the printed heading the HTML replaces), the manifest/header
passage, block openers that look like verse numbers, and blocks that look like in-body labels;
then the mark characters with counts (MARKS must declare each), apostrophes, and other non-ASCII
characters (reported only: Greek, Hebrew, accented letters, dashes, signs).
"""
import argparse
import collections
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import htmlkit as K  # noqa: E402

PREFIX_RE = re.compile(r"^\d+(?:[./]\d+)*\.\s")
LABEL_RE = re.compile(r"^\((?:Chapter|Verses?|Book|Homily|Section)\b[^)]{0,60}\)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--glob", default="english/*_english.txt")
    a = ap.parse_args()
    try:
        units = K.load_units(os.path.abspath(os.path.expanduser(a.work_dir)), a.glob)
    except K.BuildError as e:
        sys.exit(f"ERROR: {e}")
    marks, apos, other = collections.Counter(), 0, collections.Counter()
    print(f"{len(units)} units\n")
    for u in units:
        prefixes = [PREFIX_RE.match(b).group(0).strip() for b in u.blocks[1:] if PREFIX_RE.match(b)]
        labels = [LABEL_RE.match(b).group(0) for b in u.blocks[1:] if LABEL_RE.match(b)]
        runon = [m.group(0) for b in u.blocks[1:] for m in re.finditer(r"\((?:Chapter \d+ — )?Verses? [^)]{1,30}\)", b)
                 if m.start() > 0]
        print(f"{u.where}  passage={u.passage!r}  blocks={len(u.blocks)}")
        print(f"   first block: {u.first_block[:70]!r}")
        if prefixes:
            print(f"   verse-number openers: {prefixes}")
        if labels:
            print(f"   in-body labels: {labels[:6]}{' …' if len(labels) > 6 else ''}")
        if runon:
            print(f"   labels inside running text (references or run-on labels): {runon[:4]}")
        for b in u.blocks:
            c, ap_ = K.census(b)
            marks.update(c)
            apos += ap_
            for ch in b:
                if ord(ch) > 127 and ch not in K.MARK_CHARS:
                    other[ch] += 1
    print("\nmark characters (each key must be in MARKS):")
    for k, v in sorted(marks.items(), key=lambda kv: -kv[1]):
        print(f"   {k!r}: {v}")
    if not marks:
        print("   none")
    print(f"apostrophes (’ inside or closing a word, rendered as APOSTROPHE): {apos}")
    groups = collections.defaultdict(int)
    for ch, n in other.items():
        name = unicodedata.name(ch, "?")
        groups["GREEK" if "GREEK" in name else "HEBREW" if "HEBREW" in name else name] += n
    print("other non-ASCII (reported only):")
    for g, n in sorted(groups.items(), key=lambda kv: -kv[1])[:20]:
        print(f"   {g}: {n}")


if __name__ == "__main__":
    main()

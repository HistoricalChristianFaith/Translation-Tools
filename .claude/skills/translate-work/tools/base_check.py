#!/usr/bin/env python3
"""Deterministic structural checks for a source-language BASE TEXT (run after every pass).

Each base-text project in this workflow grew its own `_source/scratchpad/validate.py`; this is a
generic version of the checks they all share. It never edits anything. Checks, per file (body =
everything after the `====` header separator):

  --pair »«        paired marks balanced, never closed before opened, never nested (repeatable)
  --even '*'       marks that must occur an even number of times (repeatable)
  --forbid RE      a regex that must not occur in the body (e.g. '[Jj]' for "no consonantal J")
  --anchor RE      page/column anchors with ONE numeric group: must be non-decreasing and
                   contiguous (no page skipped) inside each file; first/last are reported
  --section RE     numbered sections with ONE numeric group (default '^(\\d+)\\.\\s'): must run
                   1, 2, 3 ... with no gap (--section-start-for 12=2 for a unit that starts later)
  --body-start RE  start the checked body at the first line matching RE instead of right after
                   the `====` separator (skips heading / lemma lines with their own conventions)
  --ending RE      a regex the end of the body must match (e.g. 'Amen[.!]?«?\\.?$')
  --mirror DIR     a second tree holding the same running text (e.g. `_source/passB_final/`):
                   the body from the first line matching --mirror-start must be byte-identical
                   to the mirror file with the same unit number

    python3 base_check.py LATIN/ --pair »« --forbid '[Jj]' --anchor '\\[GCS p\\.(\\d+)\\]' \\
        --ending 'Amen' --mirror _source/passB_final --mirror-start '^\\d+\\.\\s'
    python3 base_check.py GREEK/ --pair »« --pair ⟨⟩ --pair '[[' ']]' --even '*' --even '†' \\
        --even-exempt '(?m)^§\\s+[IVXLCDM]+\\*' --section none

Exit status 0 = ALL CLEAN. Keep it clean after every pass; adapt the flags (never the text) when
a pass legitimately changes the shape (e.g. anchors vanish after R7 -> the anchor check simply
finds none and is skipped).
"""

import argparse
import glob
import os
import re
import sys


def body_of(text):
    lines = text.split("\n")
    for i, l in enumerate(lines):
        if re.match(r"^={5,}\s*$", l):
            return "\n".join(lines[i + 1:])
    return text


def unit_no(path):
    m = re.search(r"(\d+)", os.path.basename(path))
    return int(m.group(1)) if m else None


def check_pair(body, o, c):
    errs, depth, maxd = [], 0, 0
    if len(o) == 1 and len(c) == 1:
        for ch in body:
            if ch == o:
                depth += 1
                maxd = max(maxd, depth)
            elif ch == c:
                depth -= 1
                if depth < 0:
                    errs.append(f"{c} before {o}")
                    depth = 0
        if maxd > 1:
            errs.append(f"{o}{c} nested (depth {maxd})")
    if body.count(o) != body.count(c):
        errs.append(f"{o}{c} unbalanced {body.count(o)}/{body.count(c)}")
    return errs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="directory of base-text files (or one file)")
    ap.add_argument("--glob", default="*.txt")
    ap.add_argument("--pair", nargs="+", action="append", default=[],
                    help="two chars as one arg ('»«') or opener and closer as two args ('[[' ']]')")
    ap.add_argument("--even", action="append", default=[])
    ap.add_argument("--even-exempt", help="regex removed before counting --even marks")
    ap.add_argument("--forbid", action="append", default=[])
    ap.add_argument("--anchor")
    ap.add_argument("--section", default=r"(?m)^(\d+)\.\s", help="regex, or 'none'")
    ap.add_argument("--section-start-for", action="append", default=[], metavar="UNIT=N")
    ap.add_argument("--body-start")
    ap.add_argument("--ending")
    ap.add_argument("--mirror")
    ap.add_argument("--mirror-start", default=r"^\d+\.\s")
    a = ap.parse_args()

    pairs = []
    for p in a.pair:
        if len(p) == 1 and len(p[0]) == 2:
            pairs.append((p[0][0], p[0][1]))
        elif len(p) == 2:
            pairs.append((p[0], p[1]))
        else:
            sys.exit(f"--pair needs '»«' or two args, got {p}")

    files = sorted(glob.glob(os.path.join(a.target, a.glob))) if os.path.isdir(a.target) else [a.target]
    if not files:
        sys.exit("No files matched.")
    dirty = 0
    for fp in files:
        text = open(fp, encoding="utf-8").read()
        body = body_of(text)
        if a.body_start:
            blines = body.split("\n")
            first = next((i for i, l in enumerate(blines) if re.match(a.body_start, l)), len(blines))
            body = "\n".join(blines[first:])
        errs, info = [], []
        for o, c in pairs:
            errs += check_pair(body, o, c)
        counted = re.sub(a.even_exempt, "", body) if a.even_exempt else body
        for m in a.even:
            if counted.count(m) % 2:
                errs.append(f"'{m}' count odd ({counted.count(m)})")
        for rx in a.forbid:
            hits = re.findall(rx, body)
            if hits:
                errs.append(f"forbidden /{rx}/ x{len(hits)}")
        if a.anchor:
            nums = [int(x) for x in re.findall(a.anchor, body)]
            if nums:
                info.append(f"anchors {nums[0]}..{nums[-1]} ({len(nums)})")
                for x, y in zip(nums, nums[1:]):
                    if y < x:
                        errs.append(f"anchor goes backwards {x}->{y}")
                    elif y > x + 1:
                        errs.append(f"anchor gap {x}->{y}")
        if a.section != "none":
            secs = [int(x) for x in re.findall(a.section, body)]
            if secs:
                starts = dict(tuple(map(int, x.split("="))) for x in a.section_start_for)
                first_no = starts.get(unit_no(fp), 1)
                expect = list(range(first_no, first_no + len(secs)))
                info.append(f"sections {secs[0]}..{secs[-1]}")
                if secs != expect:
                    bad = next(i for i, (s, e) in enumerate(zip(secs, expect)) if s != e)
                    errs.append(f"section sequence breaks at #{bad}: got {secs[bad]}, expected {expect[bad]}")
        if a.ending and not re.search(a.ending + r"\s*$", body.strip()):
            errs.append(f"ending /{a.ending}/ not found; ends …{body.strip()[-50:]!r}")
        if a.mirror:
            n = unit_no(fp)
            cands = [m for m in glob.glob(os.path.join(a.mirror, "*")) if unit_no(m) == n]
            if len(cands) != 1:
                errs.append(f"mirror file for unit {n}: {len(cands)} candidates")
            else:
                lines = body.split("\n")
                start = next((i for i, l in enumerate(lines) if re.match(a.mirror_start, l)), None)
                running = "\n".join(lines[start:]).strip() if start is not None else ""
                if running != open(cands[0], encoding="utf-8").read().strip():
                    errs.append(f"running text != mirror {os.path.basename(cands[0])}")
        dirty += bool(errs)
        print(f"  {os.path.basename(fp)}: {'CLEAN' if not errs else 'ERRORS'}"
              f"{'  (' + ', '.join(info) + ')' if info else ''}")
        for e in errs:
            print(f"      - {e}")
    print(f"\n{'ALL CLEAN' if not dirty else f'{dirty} file(s) with errors'} ({len(files)} checked)")
    sys.exit(1 if dirty else 0)


if __name__ == "__main__":
    main()

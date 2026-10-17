#!/usr/bin/env python3
"""Check an HTML fragment against the Writings-Database house format, read-only.

    check_html.py FILE                       house format + footnote links
    check_html.py FILE --work-dir W          ... + fidelity of FILE to W's English (via W/html_config.py)

Works on any file in the repo (also ones this skill did not write). Writes nothing.
Last line: `GATE check_html: PASS` / `FAIL (n problem(s))`.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import htmlkit as K  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("file")
    ap.add_argument("--work-dir")
    ap.add_argument("--config")
    ap.add_argument("--author", help="author name, for the <h1> advisory (default: the parent folder)")
    a = ap.parse_args()
    doc = K.read_text(a.file)
    author = a.author
    if not author:                       # the folder just below the repo root (the one with CLAUDE.md)
        d = os.path.dirname(os.path.abspath(a.file))
        while os.path.dirname(d) != d and not any(
                os.path.exists(os.path.join(os.path.dirname(d), n)) for n in ("CLAUDE.md", "AGENTS.md")):
            d = os.path.dirname(d)
        author = os.path.basename(d)
    errs, adv = K.gate_house(doc, author)
    errs += K.gate_notes(doc)
    if a.work_dir:
        work = os.path.abspath(os.path.expanduser(a.work_dir))
        try:
            cfg = K.load_config(a.config or os.path.join(work, "html_config.py"))
            units = K.load_units(work, cfg.SRC_GLOB)
            items, serr = K.build_items(cfg, units, [])
            errs += serr
            errs += [f"fidelity: {e}" for e in K.gate_fidelity(K.expected_stream(cfg, items), K.output_stream(doc))]
        except K.BuildError as e:
            errs.append(str(e))
    for e in errs[:40]:
        print(f"  {e}")
    for x in adv:
        print(f"  advisory: {x}")
    print(f"GATE check_html: {'PASS' if not errs else f'FAIL ({len(errs)} problem(s))'}")
    sys.exit(0 if not errs else 1)


if __name__ == "__main__":
    main()

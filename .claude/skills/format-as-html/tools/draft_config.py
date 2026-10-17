#!/usr/bin/env python3
"""Draft WORK_DIR/html_config.py from the run artifacts, the English files and a mark census.

    draft_config.py --work-dir W --root R --relpath 'Author/Work.html' [--force]
    draft_config.py --work-dir W --root R --reldir 'Author/Work' [--force]      (folder mode)

--root/--relpath come from the location interview (locate.py). Guesses are marked `# GUESS`;
MARKS values are left None and SOURCE_NOTE keeps a TODO, so the build refuses to run until the
model has filled them from the run's rules and the user has approved the note.
"""
import argparse
import datetime
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import htmlkit as K  # noqa: E402
from locate import work_names  # noqa: E402

RUBRIC_RE = re.compile(r"^(?:[A-Z][A-Z .,]+\.|\((?:Verses?|Chapter|Book|Homily)\b[^)]*\))$")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--root", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--relpath")
    g.add_argument("--reldir")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    work_dir = os.path.abspath(os.path.expanduser(a.work_dir))
    dest = os.path.join(work_dir, "html_config.py")
    if os.path.exists(dest) and not a.force:
        sys.exit(f"{dest} exists; re-run with --force to replace it")
    units = K.load_units(work_dir, "english/*_english.txt")
    author, work = work_names(work_dir)
    state = K.load_json(os.path.join(work_dir, "_source", "run", "state.json")) or {}

    if a.relpath:
        output = f'{{"mode": "single", "root": {a.root!r}, "relpath": {a.relpath!r}}}'
        h1 = repr(work)
    else:
        output = (f'{{"mode": "folder", "root": {a.root!r}, "reldir": {a.reldir!r},\n'
                  f'          "filename": lambda u: f"{{u.where}}.html"}}   # GUESS: file names')
        h1 = "lambda u: label_heading()(u)[0][1]   # GUESS: one <h1> per file"

    firsts = [u.first_block for u in units]
    rubric = all(RUBRIC_RE.match(f) for f in firsts)
    drop = (r'r"^(?:[A-Z][A-Z .,]+\.|\((?:Verses?|Chapter|Book|Homily)\b[^)]*\))$"' if rubric
            else "None   # GUESS: first blocks are not all printed headings; check the census")
    check_label = '"passage"' if any(K.LABEL_SPAN_RE.match(f) for f in firsts) else "None"

    spans = [K.parse_span(u.passage) for u in units if u.passage and ":" not in u.passage]
    spans = [s for s in spans if s]
    if spans and len(spans) >= len(units) - 2:
        headings = "verse_heading(chapter=1)   # GUESS: '1:a-b' (single-chapter book); special passages keep their name"
        verses = [s for s in spans if s]
        coverage = f"verse_coverage({verses[0][0][0]}, {verses[-1][1][0]})"
    elif all(re.match(r"^(?:BOOK [IVXLC]+\.|PROLOGUE\.)$", f) for f in firsts):
        headings, coverage = "book_heading()   # GUESS", "None"
    else:
        headings, coverage = "label_heading()   # GUESS: the label from each English header", "None"

    prefix_units = sum(1 for u in units if any(re.match(r"^\d+(?:[./]\d+)*\.\s", b) for b in u.blocks[1:]))
    strip = ('[r"^\\d+(?:[./]\\d+)*\\.\\s+(?=\\S)"]   # GUESS: leading verse numbers in '
             f'{prefix_units} unit(s); the heading carries the verse') if prefix_units else "[]"

    counts = {}
    for u in units:
        for b in u.blocks:
            for k, v in K.census(b)[0].items():
                counts[k] = counts.get(k, 0) + v
    marks = "\n".join(f"    {k!r}: None,   # {v}x: set from the run's TRANSLATION_RULES"
                      for k, v in sorted(counts.items(), key=lambda kv: -kv[1])) or "    # no marks found"

    lo, hi = K.page_range(units)
    facts = ["# Facts for the note (from state.json / manifest):"]
    for key in ("base", "base_license", "oracle", "language"):
        if state.get(key):
            facts.append(f"#   {key}: {state[key]}")
    facts.append(f"#   pages: {lo}–{hi}" if lo else "#   pages: unknown")
    lang = state.get("language", "Source")
    note = (f'"{lang} source: TODO the work and its date, the edition ({state.get("base", "edition")}), '
            '{pages}, verified against the page images. TODO the conventions: lemmata, Scripture, '
            'Greek, what was left untranslated."')

    tmpl = K.read_text(os.path.join(HERE, "..", "templates", "html_config_template.py"))
    for k, v in {"AUTHOR": author, "WORK": work, "DATE": datetime.date.today().isoformat(),
                 "OUTPUT": output, "H1": h1, "NOTE_FACTS": "\n".join(facts), "SOURCE_NOTE": note,
                 "LICENSE": state.get("base_license", "unknown"), "DROP_FIRST_BLOCK": drop,
                 "CHECK_LABEL": check_label, "UNIT_HEADINGS": headings, "STRIP_PREFIX": strip,
                 "MARKS": marks, "COVERAGE": coverage}.items():
        tmpl = tmpl.replace(f"%%{k}%%", v)
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(tmpl)
    print(f"drafted {dest}")
    print(f"  units {len(units)}, marks {counts or 'none'}, first blocks {'all headings' if rubric else 'MIXED'}")
    print("  next: set every MARKS value, write SOURCE_NOTE (no TODO), confirm each # GUESS")


if __name__ == "__main__":
    main()

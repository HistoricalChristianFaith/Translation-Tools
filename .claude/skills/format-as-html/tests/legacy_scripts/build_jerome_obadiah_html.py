#!/usr/bin/env python3
"""Build the HTML deliverable for Jerome, *Commentary on Obadiah* (fresh English translation from
the Translation-Tools run on Adriaen's CCSL 76) into the main Writings-Database repo, in the house
"bare fragment" format (Writings-Database/CLAUDE.md).

Source:  Writings-Database-Non-English/Jerome/Commentary on Obadiah/english/sectionNN_english.txt
Output:  Writings-Database/Jerome/Commentary on Obadiah.html   (replaces the ChatGPT version)

    python3 build_jerome_obadiah_html.py              # write the file
    python3 build_jerome_obadiah_html.py --dry-run    # parse, render and check; write nothing
    python3 build_jerome_obadiah_html.py --out /tmp/x.html   # write somewhere else (preview)

ONE consolidated file, like the old file at this path (the filename must not change: other repos
cite it by URL). Headings keep the old file's form: `<h2>Prologue</h2>`, then one `<h2>` per verse
section in chapter:verse form (Obadiah has one chapter): `<h2>1:1</h2>`, `<h2>1:2-4</h2>`,
`<h2>1:12-13a</h2>`, `<h2>1:13b-14</h2>`. The sections are the run's 13 units (the PL "Vers."
sections mapped onto CCSL's lemmata), so they differ slightly from the old file's.

House format:

    <article class="writing">
    <h1>Commentary on Obadiah</h1>
    <i>Latin source: … This English translation is released into the public domain.</i><br><br>
    <h2>Prologue</h2>
    paragraph<br><br>
    <h2>1:1</h2>
    <i>lemma (Jerome's version from the Hebrew)</i> LXX: <i>lemma (Septuagint)</i> exposition…<br><br>
    …
    <h2>1:20-21</h2>
    …<br><br>
    epilogue to Pammachius<br><br>     (the last paragraph of unit 12, kept under 1:20-21)
    </article>

Source file layout: three `#` header lines (line 1: `… — Prologue (…)` or `… — Verse(s) X: Obad.
X (…)`; line 2: `… CCSL 76 (…), pp. A–B` or `p. A`), a `====` rule, then blank-line-separated
blocks:
  - unit 0 opens with `PROLOGUE.`, unit 1 with CCSL's rubric `HERE BEGINS THE BOOK.`: both dropped
    (the <h2> replaces them);
  - units 2-12 open with a label block, `(Verse 7.)` / `(Verses 12–13a.)`: dropped, and it must
    agree with the header's verse span (unit 1 has no label; its span comes from the header);
  - a lemma paragraph opens with CCSL's bold verse number(s), `1.`, `2/4.`, `5.6.`, `12.13.`,
    `14.`: dropped, as the <h2> carries the verse (a block opening with a lemma and no number,
    e.g. unit 8's `*Nor shall you…*`, is left as is);
  - every other paragraph stays under its unit's heading.

Marks (the translation's conventions -> house style):
  - `*…*` = the lemmata (Jerome's version from the Hebrew, and after `LXX:` the Septuagint) and
    the lemma words repeated in the exposition -> <i>…</i>;
  - `»…«` = the other Scripture Jerome quotes -> <i>…</i>;
  - `“…”` -> straight "…" (none at present);
  - `LXX:`, Greek with its English gloss in parentheses (`φερωνύμως (true to his name)`), dashes
    -> pass through.
There are no footnotes and no Scripture references: CCSL gives its references in the apparatus,
which the run left out by decision.
Safety checks: the units must be 0..12, with unit 0 the Prologue and units 1..12 verse sections
that run on without gap or overlap from verse 1 to verse 21 (12-13a then 13b-14); each label block
must match its header; every heading needs reading text; * and » « must pair up in every block; no
unconverted mark may survive.
"""
import argparse
import glob
import html
import os
import re
import sys

SRC_DIR = "english"                      # sanitized for the test copy
OUT_FILE = "Commentary on Obadiah.html"   # sanitized for the test copy
H1 = "Commentary on Obadiah"
UNITS = 13                    # Prologue + 12 verse sections
LAST_VERSE = 21

SOURCE_TMPL = (
    "<i>Latin source: Jerome's commentary on Obadiah, with a prologue to Pammachius (written at "
    "Bethlehem in 396, replacing the allegorical commentary of his youth), from the critical text "
    "of M. Adriaen, <i>Corpus Christianorum, Series Latina</i> 76 (Turnhout, 1969), {pages}, "
    "verified against the page images, with the edition's few evident misprints corrected. Each "
    "lemma gives Obadiah in Jerome's own version from the Hebrew and then, after \"LXX:\", in his "
    "Latin of the Septuagint; all Scripture is translated as Jerome quotes it, from his own Latin. "
    "Italics mark the lemmata and the other Scripture he quotes. Greek words are kept as printed, "
    "with an English gloss in parentheses. The edition's apparatus (Scripture references and "
    "variant readings) is not translated. This English translation is released into the public "
    "domain.</i><br><br>")

RULE_RE = re.compile(r"^={5,}\s*$", re.M)
HEADER_RE = re.compile(r"—\s*(?:(Prologue)\b|Verses? ([\d–\-ab]+): Obad\. ([\d\-ab]+)\b)")
PAGES_RE = re.compile(r"CCSL 76 \([^)]*\), pp?\. (\d+)(?:[–\-](\d+))?")
LABEL_RE = re.compile(r"^\((Verses?) ([\d–\-ab]+)\.\)$")
SPAN_RE = re.compile(r"^(\d+)([ab]?)(?:-(\d+)([ab]?))?$")
VERSE_NUM_RE = re.compile(r"^\d+(?:[./]\d+)*\.\s+(?=\S)")
QUOTE_MAP = {"“": '"', "”": '"', "‘": "'", "’": "'"}


def parse_span(text, where):
    """`12-13a` / `12–13a` / `7` -> ((12, ''), (13, 'a')): first and last verse, with part."""
    m = SPAN_RE.match(text.replace("–", "-"))
    if not m:
        raise ValueError(f"{where}: cannot read verse span {text!r}")
    first = (int(m.group(1)), m.group(2))
    last = (int(m.group(3)), m.group(4)) if m.group(3) else first
    if last < first:
        raise ValueError(f"{where}: verse span {text!r} runs backwards")
    return first, last


def heading(first, last):
    """((2, ''), (4, '')) -> `1:2-4`; ((7, ''), (7, '')) -> `1:7`; ((13, 'b'), (14, '')) -> `1:13b-14`."""
    a = f"{first[0]}{first[1]}"
    return f"1:{a}" if first == last else f"1:{a}-{last[0]}{last[1]}"


def follows(prev_last, first):
    """Does a section starting at `first` continue straight on from one ending at `prev_last`?"""
    if prev_last[1] == "a":
        return first == (prev_last[0], "b")
    return first == (prev_last[0] + 1, "") or (first == (prev_last[0] + 1, "a"))


def render_block(text, where):
    """Escape, *…* and »…« -> <i>…</i>, “…” -> straight quotes."""
    text = html.escape(" ".join(text.split()), quote=False)
    out, star, guil = [], False, False
    for ch in text:
        if ch == "*":
            if guil:
                raise ValueError(f"{where}: * inside »…« in: {text[:80]!r}")
            out.append("</i>" if star else "<i>")
            star = not star
        elif ch == "»":
            if guil or star:
                raise ValueError(f"{where}: nested » in: {text[:80]!r}")
            guil = True
            out.append("<i>")
        elif ch == "«":
            if not guil:
                raise ValueError(f"{where}: « without » in: {text[:80]!r}")
            guil = False
            out.append("</i>")
        else:
            out.append(QUOTE_MAP.get(ch, ch))
    if star or guil:
        raise ValueError(f"{where}: unclosed * or » in: {text[:80]!r}")
    return "".join(out)


def parse_unit(path):
    """Return (n, heading, (first, last) or None, (page_from, page_to), paragraphs)."""
    fname = os.path.basename(path)
    where = fname.split("_")[0]
    parts = RULE_RE.split(open(path, encoding="utf-8").read(), maxsplit=1)
    if len(parts) != 2:
        raise ValueError(f"{fname}: no ==== rule between header and body")
    header, body = parts
    m = HEADER_RE.search(header.strip().splitlines()[0])
    if not m:
        raise ValueError(f"{fname}: header line 1 has no 'Prologue' / 'Verse(s) X: Obad. X' label")
    n = int(re.search(r"section(\d+)_", fname).group(1))
    p = PAGES_RE.search(header)
    if not p:
        raise ValueError(f"{fname}: header has no 'CCSL 76 (…), pp. A–B'")
    pages = (int(p.group(1)), int(p.group(2) or p.group(1)))

    blocks = [b.strip() for b in re.split(r"\n\s*\n", body) if b.strip()]
    if m.group(1):                                       # the Prologue
        if n != 0:
            raise ValueError(f"{fname}: only unit 0 may be the Prologue")
        if blocks[0] != "PROLOGUE.":
            raise ValueError(f"{fname}: the Prologue does not open with 'PROLOGUE.'")
        return n, "Prologue", None, pages, blocks[1:]

    if n == 0:
        raise ValueError(f"{fname}: unit 0 must be the Prologue")
    span = parse_span(m.group(3), fname)
    if parse_span(m.group(2), fname) != span:
        raise ValueError(f"{fname}: header verse label {m.group(2)!r} disagrees with Obad. "
                         f"{m.group(3)!r}")
    opener = blocks[0]
    if n == 1:
        if opener != "HERE BEGINS THE BOOK.":
            raise ValueError(f"{fname}: unit 1 does not open with 'HERE BEGINS THE BOOK.'")
    else:
        lm = LABEL_RE.match(opener)
        if not lm:
            raise ValueError(f"{fname}: no '(Verse(s) X.)' label block: {opener[:40]!r}")
        if parse_span(lm.group(2), fname) != span:
            raise ValueError(f"{fname}: label {opener!r} disagrees with the header's Obad. "
                             f"{m.group(3)}")
    paras = []
    for b in blocks[1:]:
        if LABEL_RE.match(b) or b in ("PROLOGUE.", "HERE BEGINS THE BOOK."):
            raise ValueError(f"{fname}: stray heading block {b[:40]!r}")
        paras.append(VERSE_NUM_RE.sub("", b, count=1))
    if not paras:
        raise ValueError(f"{fname}: section {heading(*span)} has no reading text")
    return n, heading(*span), span, pages, paras


def build(src):
    files = sorted(glob.glob(os.path.join(src, "section*_english.txt")))
    if not files:
        sys.exit(f"no source files under {src}")
    units = [parse_unit(p) for p in files]
    if [u[0] for u in units] != list(range(UNITS)):
        sys.exit(f"units are not 0..{UNITS - 1}: {[u[0] for u in units]}")
    prev = (0, "")                                       # sections run on 1 .. 21, no gap/overlap
    for n, head, span, _, _ in units[1:]:
        if not follows(prev, span[0]):
            sys.exit(f"section{n:02d} ({head}) does not follow on from verse {prev[0]}{prev[1]}")
        prev = span[1]
    if prev != (LAST_VERSE, ""):
        sys.exit(f"the last section ends at verse {prev[0]}{prev[1]}, not {LAST_VERSE}")

    page_from, page_to = units[0][3][0], max(u[3][1] for u in units)
    out = ['<article class="writing">', f"<h1>{H1}</h1>",
           SOURCE_TMPL.format(pages=f"pp. {page_from}–{page_to}")]
    summary = []
    for n, head, _, _, paras in units:
        where = f"section{n:02d}"
        out.append(f"<h2>{head}</h2>")
        out += [f"{render_block(b, where)}<br><br>" for b in paras]
        summary.append((where, head, len(paras)))
    out += ["</article>", ""]
    doc = "\n".join(out)

    left = sorted({ch for ch in "*»«“”‘’" if ch in doc})
    if left:
        raise AssertionError(f"unconverted marks survived: {left!r}")
    if doc.count("<i>") != doc.count("</i>"):
        raise AssertionError("unbalanced <i>")
    if doc.count("<h2>") != len(units):
        raise AssertionError("heading count mismatch")
    return doc, summary


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--src", default=SRC_DIR)
    ap.add_argument("--out", default=OUT_FILE)
    ap.add_argument("--dry-run", action="store_true", help="parse and check only; write nothing")
    a = ap.parse_args()

    doc, summary = build(a.src)                  # build and check everything before writing
    for where, head, npara in summary:
        print(f"{where}  <h2>{head}</h2>  {npara:>2} paras")
    if not a.dry_run:
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(doc)
    print(f"\n{len(summary)} sections, {len(doc):,} chars "
          f"{'checked (dry run)' if a.dry_run else 'written to ' + a.out}")


if __name__ == "__main__":
    main()

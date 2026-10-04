# Phase 08: Oracle back-check (Pass R3; subagent, one packet)

Read your packet's text **sentence by sentence against the oracle**, the modern English
translation the user supplied. Use it purely as a **detector** of meaning-level defects in our
text. Settle every candidate on the **base page image**. **The oracle is never the authority**
(`copyright.md`).

This pass also produces two things the translation phases need:
1. per-unit **oracle extracts** (used to grade the English later);
2. the list of **known oracle divergences** (so the grader doesn't penalize our correct
   readings).

Inputs:
- your units;
- the base images;
- `${SRC_DIR}/oracle/oracle_full.txt` (or `oracle.pdf` with `pdf_pages.py find`/`render` if
  it has no text layer);
- `${SRC_DIR}/pass0_report.md` (where the oracle's units start);
- `[R3]` items in `carry_forward.md`.

## 1. Extract the oracle text per unit

For each of your units, find its translation in the oracle: its heading (e.g. "Homily 5"), or
for anthologies, the sections that render this unit's text. Write it **verbatim** to
`${SRC_DIR}/oracle/extracts/unit<NN>.txt` (NN = the unit's `n`, zero-padded to 2 digits), with
footnotes left in. This file is a private local cache: never quote it anywhere beyond a few
words.
- If the oracle is an **anthology** that covers only part of a unit, extract what exists, and
  start the file with one line: `# COVERAGE: partial — <which part>`.
- If it doesn't cover the unit at all, don't write a file. Say so in your notes (this unit will
  be ungraded).

## 2. Back-check

Go through the unit sentence by sentence. A **candidate** is a place where the English implies a
real **meaning** difference:
- a dropped or added clause;
- a different word sense, subject or object;
- a flipped negation;
- a different referent;
- a mis-scoped quotation;
- a different proper name or numeral;
- a doxology anomaly.

**Ignore** translation freedom: word order, idiom, expansion or compression, paraphrase, and the
oracle quoting Scripture in a modern Bible version.

Settle each candidate on the base image (crop):
- **our slip:** fix it in place;
- **oracle follows a different edition or apparatus reading, or paraphrases, or errs:** keep
  our text, and log it under `## Oracle divergences` (unit, section, our reading in a few words,
  the oracle's in a few words, the reason: variant / smoothing / abridgment / oracle error);
- **the base edition itself seems wrong** (the oracle's reading makes better sense and the print
  looks like a misprint): keep it, and add a `[R6]` Carry-forward item.

Expect loose tracking where the ancient translator or the modern one took liberties. Most
candidates end as "keep".

## Output

Notes `${RUN_DIR}/notes/R3/<packet>.md`: the standard sections plus `## Oracle divergences`, and
a line per unit in the Summary saying `extract: full | partial | none`. Status
`${RUN_DIR}/status/R3/<packet>.json`. Edit only your packet's units (and write only your units'
extract files).

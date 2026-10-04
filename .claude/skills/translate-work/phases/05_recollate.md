# Phase 05: Lensless re-collation (Pass R2; subagent, one packet)

You are a **fresh, independent reader**. Re-read your packet's text **word for word against the
page images**, with **no other witness open**: no OCR, no second edition, no translation. The
image is the only reference.

This pass runs right after Pass B, **before** any editorial pass. So the text is still meant to
be a pure transcription of the edition, and **every** difference between the text and the image
is a real slip. Fix it.

Inputs:
- your units' files in `${LANG_DIR}/`;
- `${SRC_DIR}/pages/base/index.json`;
- `manifest.json`;
- `[R2]` items in `carry_forward.md`.

**Don't open** `ocr/`, `pages/witness/`, `oracle/`, or any report except `carry_forward.md`.

## Method

For each unit, page by page, band by band (`image_reading.md`):

1. Read the printed band, then compare the text's corresponding stretch **word by word**. Don't
   read the text first; that primes you to see what's written.
2. Weakest spots first, since they are where Pass B errs most:
   - word forms and endings;
   - dropped or duplicated words and short lines;
   - wrong word division at line ends;
   - accents, breathings, iota subscript and final sigma (Greek);
   - the **type boundary**: exactly which words are italic, spaced, uncial or bold, i.e. the
     extent of each `» «` / `* *`;
   - punctuation that carries sense;
   - section numerals;
   - anchors placed at the true page turn (the first word printed on each page).
3. **Crop and enlarge (3×) before every change and every doubt.**
4. Fix slips in place with small edits. Anything you can't settle on the image goes under
   Doubts. Don't "improve" what the edition prints; misprints in the edition itself are for R6
   (note them as Carry-forward `[R6]`).

## Output

- Notes `${RUN_DIR}/notes/R2/<packet>.md`: `## Fixes` lists **every** change (unit, page,
  before → after, class). Also give counts by class in the Summary.
- Status `${RUN_DIR}/status/R2/<packet>.json`.

Edit only your packet's units. A clean pass (0 fixes) is a good result, not a failure. Don't
invent changes.

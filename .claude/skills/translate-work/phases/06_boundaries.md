# Phase 06: Boundaries & completeness (Pass R4; subagent, one packet or role `seams`)

Verify on the images that each unit starts and ends at exactly the printed point, and that
**nothing inside it is missing, duplicated or misplaced**. This is a completeness audit, not a
word-by-word collation (R2 did that).

You may consult the oracle (`${SRC_DIR}/oracle/oracle_full.txt`), if present, **only as a
completeness tripwire**. A paragraph in the English with no counterpart in our text suggests a
dropped passage. Settle it on the image, and never rewrite the text to match the English.

## Packet role: per unit

1. **Start:** heading, lemma or title line and incipit match the print. No tail of the previous
   unit leaked in; no opening words dropped.
2. **End:** the body stops at the exact printed explicit (closing formula or doxology, with its
   punctuation). Nothing of the next unit leaked in; nothing before the explicit dropped.
3. **Internal completeness:** for **every** page in the unit's span:
   - its anchor appears exactly once, at the first word printed on that page;
   - every printed paragraph is present. Check the first and last words of each printed
     paragraph and the line count against the image;
   - no line was lost at a page or column turn, around a heading, around an excluded apparatus
     or foreign block, or in a band spanning both columns;
   - no line appears twice.
4. **Section numerals:** all present, in sequence, at the printed spot. None invented.
5. **Layout traps:** a conclusion printed in a full-width band above interleaved material;
   running heads that lag; a unit that continues past a plate or blank leaf.

Fix defects in place (tiny edits; restore a dropped chunk by seeding it disk→disk from OCR or
tesseract, then correcting on the image). Report every page as verified or fixed.

The manifest's `incipit` and `explicit` are locators, not evidence. Judge the boundary on the image; if the text is right and the field differs, sync the field with `manifest_edit.py` (`conventions.md` → *Editing discipline*). Never edit text toward a field. (This applies to the `seams` role too.)

Notes: `${RUN_DIR}/notes/R4/<packet>.md`. Status: `${RUN_DIR}/status/R4/<packet>.json`. Edit
only your packet's units.

## Role `seams` (runs alone, after all packet agents)

Check every boundary between **consecutive units**, especially those that fall between two
packets, and any volume, issue or part seam in the base:
- On each shared page, the split point is exactly the printed heading. Text above it belongs to
  the earlier unit, text from the incipit down to the later one. Both units anchor the page.
- No text is lost or duplicated at the seam.
- The unit count and numbering match the edition (no unit dropped between parts or volumes).

You may edit **both** units at a seam, with minimal edits. Notes:
`${RUN_DIR}/notes/R4/seams.md`. Status: `${RUN_DIR}/status/R4/seams.json`.

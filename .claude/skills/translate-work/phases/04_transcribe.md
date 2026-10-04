# Phase 04: Transcribe (Pass B; subagent, one packet)

Produce the text of your packet's units **directly from the page images**: a diplomatic
transcription of the edition's main text, following `shared/conventions.md`. This is where the
source text is created. Every later pass checks it, but nothing later can recover a sentence you
never looked at, so be complete and exact.

Inputs:
- `${RUN_DIR}/manifest.json` (your units: `file`, `heading`, `pages`, `incipit`, `explicit`);
- `${SRC_DIR}/pages/base/index.json`;
- `${SRC_DIR}/boundary_audit.md` (the rows for your units);
- `${RUN_DIR}/stage_base.json` (`ocr`, `ocr_slice`, `two_column`);
- if the normalize phase ran: `${RUN_DIR}/normalize/summary.md` and the flags on your pages in
  `${RUN_DIR}/normalize/flags.jsonl`;
- `[B]` items in `carry_forward.md`.

**Seeded units and B mode.** If the normalize phase seeded your units (no placeholder line in the
body), don't re-seed: correct the body **in place** against the images, page by page (sub-packets:
small in-place edits on your pages only; no `[[JOIN]]`). The script already settled its
categories (code points, combining marks, look-alikes, whitespace, the mark conversions in
`summary.md`); don't redo them by hand. Your B mode is `state.json` → `b_mode` (`boot.md` §3;
`null` = `full`):
- `B-MODE: full` (default): collate every word, as below;
- `B-MODE: light` (clean born-digital text layer): read every page for structure (paragraphs,
  section numbers, anchors, headings), mark scope (`» «` vs book titles, `* *`, brackets) and
  exclusions; check letters at every flagged spot and wherever the print visibly differs.
  Every page is still a checklist item.

**A clean text layer reproduces the print, misprints included.** Where its letters (or accents,
breathings) disagree with what you expect, log a **doubt** (`status_contract.md` §2a); change a
letter only if the image unambiguously shows a different one.

## Method (per unit, in order)

1. **Confirm the start and end on the images before transcribing.** Find the heading, the lemma
   line (already in the scaffold; verify it) and the incipit on the first page, and the explicit
   on the last page. A shared page belongs to two units: take only your unit's part of it.
   The manifest's `incipit` and `explicit` are locators, not evidence. Judge the boundary on the image; if the text is right and the field differs, sync the field with `manifest_edit.py` (`conventions.md` → *Editing discipline*). Never edit text toward a field.
2. **Build the body page by page**, replacing the `[[TO BE TRANSCRIBED IN PASS B]]` line.
   **Sub-packet:** replace only *your* line `[[TO BE TRANSCRIBED IN PASS B: <id> pp.<range>]]`
   (grow it page by page: insert each page's text just above the placeholder, then remove the
   placeholder when your last page is done). If your first page continues the previous
   sub-packet's paragraph, begin your text with `[[JOIN]]` followed by exactly what follows the
   page turn (`[[JOIN]][GCS p.187]rest-of-word…`, or `[[JOIN]] [GCS p.187]next…` after a word
   break). The orchestrator's `packets.py join` then merges the two lines. Skip step 1's start
   or end check unless your range holds that page.
   (Seeded units: skip the seeding below; correct in place.)
   **Resuming:** if your checklist already has checked pages (an earlier agent died), their text
   is already in the file: verify it briefly and continue from the first unchecked page.
   - **OCR `usable-draft`:** seed each page from the OCR slice **with a Python snippet**
     (disk→disk; find the page's lines in the slice). Then correct it against the image **band by
     band**. Expect systematic OCR noise (c/e, ligatures, u/n, broken words at line ends,
     apparatus lines mixed in, hyphenation), so every word must be checked, not skimmed.
   - **OCR `structure-only` or `none`:** transcribe from the image band by band. Where
     generating text is blocked, follow `content_filter.md` (tesseract seed, then tiny edits).
3. **As you go:**
   - One paragraph per physical line, with section numbers as printed.
   - Rejoin words hyphenated across line or page breaks.
   - Insert the page anchor (manifest `anchor.format`) **exactly** where each new page begins.
     The first body line starts with the anchor of the page where the unit starts. On a
     two-column base, add an anchor at each column turn.
   - Apply the marks (» « for Scripture as the edition marks it; * * for lemma words if marked;
     ⟨ ⟩ [ ] [[ ]] † † and lacunae as printed).
   - Leave out the apparatus, running heads, page numbers, marginal numbers, and foreign or
     interleaved material. Log each exclusion that isn't obvious as a Doubt.
   - Orthography exactly as printed.
4. **Adversarial self-check.** When the unit is complete, re-read it against every page once
   more, band by band, as if checking someone else's work. Check:
   - no line skipped (compare the first and last words of each printed paragraph);
   - no apparatus words taken in;
   - every page anchored once, in order;
   - sections in sequence;
   - the explicit exactly as printed.
   Fix what you find.
5. Make sure the header's 4 `#` lines are accurate (the source pages), and the heading and lemma
   match the image.

## Before you finish

- Run `python3 ${TOOLS_DIR}/base_check.py ${LANG_DIR} --glob '<your files>'` with the manifest's
  pair and anchor flags (see `check_base.py` for how flags are built). Or simply run
  `python3 ${TOOLS_DIR}/check_base.py --work-dir ${WORK_DIR} --quiet` and read **only the lines
  about your files**. Other packets (and sibling sub-packets) may still be in progress, so their
  errors are not yours.
  Fix your files until they are clean.
- Notes (`${RUN_DIR}/notes/B/<packet>.md`):
  - `## Fixes` = notable corrections to the OCR seed (classes and counts are enough; list
    only the non-obvious ones);
  - `## Doubts` = every uncertain reading, damaged word, restored numeral, or excluded
    passage, with page (each also added to the ledger);
  - `## Carry-forward` = anything R2/R4/R1/R5/R6 should look at.
- Status `${RUN_DIR}/status/B/<packet>.json`. `fixes` = number of notable corrections.

Edit **only your packet's unit files.**

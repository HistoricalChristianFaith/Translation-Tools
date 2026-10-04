# Phase 07: Secondary-witness cross-check (Pass R1; subagent, one packet)

Collate your packet's text against an **independent printing** of the same work (the witness:
e.g. Migne against a GCS base, Lommatzsch against Migne, Cramer's *Catenae* against a JTS catena
edition). Every divergence is a **signal**. **Every decision is made on the BASE page image.**
The witness is never the authority.

Inputs:
- your units;
- the base images;
- `${SRC_DIR}/pages/witness/index.json`, `${RUN_DIR}/stage_witness.json` (`unit_map_hint`),
  `${SRC_DIR}/pass0_witness.md`;
- the witness OCR, if any (only for locating passages).

## Method

1. **Locate** each unit in the witness: headings and incipit, via the hint, the OCR, or scanning
   the witness images. Record the witness pages or columns in your notes.
2. **Collate** sentence by sentence. For every divergence, classify it:
   - **base transcription slip:** our text differs from the **base image** (the witness only
     drew your attention to it). Fix it, after cropping the base image;
   - **editorial variant:** the base edition prints X, the witness prints Y, and our text
     faithfully has X. **Don't change the text.** Log it under `## Variants` (unit, base
     page, base reading, witness reading, a note on which looks right and why). R6 decides;
   - **witness error:** the witness is plainly wrong. Log it briefly.
3. Look hardest at **cut, faded or curved margins** of the base images. In past projects, that
   is where base errors hid and the witness caught them.

## Output

Notes `${RUN_DIR}/notes/R1/<packet>.md` with the standard sections **plus** `## Variants` (a
bulleted list; can be long). Put probable misprints of the base edition under `## Carry-forward`
tagged `[R6]` as well. Status `${RUN_DIR}/status/R1/<packet>.json` (`fixes` = base slips fixed).
Edit only your packet's units.

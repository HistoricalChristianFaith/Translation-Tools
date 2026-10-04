# {Author}, *{Work}*: {Language} base-text project (issue #{N})

<!--
Workspace README for `<Author>/<Work>/_source/` (git-ignored). Write it in Phase 0, before any
pass runs. Every later session and subagent reads it first, and its conventions override any
default. Keep the Status line current as passes finish. Worked examples:
examples/source-workspace/README__leviticus.md (Latin, OCR + page images) and
README__1corinthians.md (Greek catena fragments, image-first).
-->

{2–4 sentences: what the work is, how it survives (original / ancient translation / catena
fragments), what is complete or lost, and what the units are (homilies, fragments, chapters).}

> **Caveats that affect the whole method.** {E.g. the translator took liberties, so the oracle will
> track loosely; the base is Migne, not a critical edition; the OCR is unusable for polytonic Greek;
> the fragments are spread across several journal issues, so seams are the main completeness risk.}

This folder is the **source-language workspace**. The English translation (one file per unit
in `../english/`) is a later project. Method and layout mirror
{nearest completed sibling project}.

---

## ⇒ Project 1 (the current concern): a stable, clean {Language} base text

**Goal:** through repeated correction passes against multiple witnesses, produce a *stable, clean,
verified {Language} reading text* of all {K} units, good enough to translate from. "Stable" means a
further full pass yields no substantive change. **Translation is a later project.**

**Status:** {🟡/🟢} {which passes are done; what the next step is}

### Pass 0: staging ({✅/⬜})
- **Base edition item:** {archive.org identifier / URL}, {edition, year, pages}.
- **OCR:** `{file}_djvu.txt` ({lines}), with the slice for this work at lines {a–b}. {How usable is it?
  For polytonic Greek or Migne Latin, usually structure only.}
- **Page images:** `{prefix}_p{PAGE}_leaf{LEAF}.jpg`, {count} leaves at native resolution
  ({W×H}). Render recipe: `_jp2.zip` member, then `opj_decompress`, then PIL `convert('RGB')`, then
  JPEG (or `pdftoppm -r 300..400 -jpeg` for PDF items).
- **Printed page → leaf map:** `page_numbers.json` / `scandata.xml`. {Constant offset? Drifting?
  Duplicated leaves? Always glob by printed page and never compute leaves unless verified.}
- **Boundaries verified on the images:** {first unit incipit at p./leaf; last unit explicit at p./leaf;
  every seam between volumes / issues / parts.}

### Witnesses, in priority order
1. **{Base edition}** ({year}, public domain): the primary text.
2. **{Base} page images**: the ground truth for every correction.
3. **{Secondary witness}** ({Migne / Lommatzsch / Cramer / …}, PD): independent editorial line, used at R1.
4. **English oracle**: {Translator, *Title* (Series, Year)}, **copyright: consult, never copy.**
   Staged as `oracle_{name}_en.pdf` (git-ignored). Used at R3 (and for grading the English later).
5. {Extra apparatus / notes (PD) for R6, if any.}

### Passes to execute
- **A — Extract & structure:** {how units are delimited; OCR used for structure only?}
- **Normalize — seed clean-up** {run | skipped: no text layer}: a custom script makes the invisible
  and mechanical fixes (code points, combining marks, look-alikes, settled mark conversions) and
  seeds the unit files; visible letters are never changed by script. B mode: {full | light}.
- **B — Image collation:** transcribe every unit directly from the page images. Per-unit transcribe
  plus adversarial self-verify subagents, fanned out on disjoint files.
- **R2 — Lensless re-collation:** re-read everything word for word against the images with no other
  witness. Run right after B, while every divergence is still a real slip.
- **R4 — Boundary & completeness audit:** every unit's start and end, every shared page and seam,
  every page anchored once, the section sequence.
- **R1 — {Secondary witness} cross-check:** every divergence is a signal, adjudicated on the base image.
- **R3 — Oracle back-check:** sentence by sentence against the English oracle, used as a detector,
  never as an authority. Adjudicate on the image.
- **R5 — Consistency & conventions:** single-editor uniformity (orthography as printed, marks,
  anchors, lemma per unit, embedded Greek); build the unit → passage table.
- **R6 — Apparatus / variant pass:** narrow pass over the residual cruxes; emend only on convergent
  evidence and record the rest as record-don't-adopt.
- **R8 — Doubt resolution:** every doubt left after R6 checked against the other sources
  ({manuscript / other editions / none}) and the oracle as detector; the critical editor's
  choices are kept, only demonstrable transcription errors change.
- **R7 — Anchor strip:** remove every `{[ANCHOR p.N]}` (match only that form) from all trees, touch
  nothing else, and keep the trees byte-identical.

Each pass **fixes in place** and **logs to a named `_source/*.md` report**. Keep a running
`uncertain_readings.md` and drive it to zero-or-documented.

### Editorial conventions
- `» … «`: Scripture the author quotes.
- `* … *`: the lemma under comment.
- `⟨ … ⟩`: editor's supplements. `[ … ]`: editor's seclusions. `…` / `* * * *`: printed lacuna (do not fill).
- `{[ANCHOR p.N]}`: printed page / column, kept through R6 and stripped at R7.
- Orthography **as the edition prints it** (record any uniform normalization, e.g. J→I, in the pass report).
- {Language} reading text only; other-language material goes in notes, not interleaved.

### Project-1 deliverable
`{LATIN|GREEK}/{unit}NN_{lang}.txt`: `#` header lines, a `====` rule, then the body with **one
paragraph per physical line**. Plus the final `uncertain_readings.md`.

---

## Source survey (why these witnesses)

| Edition | Year | PD? | Role |
|---------|------|-----|------|
| {Base} | | ✅ | **Base** |
| {Secondary} | | ✅ | R1 witness |
| {Oracle} | | ❌ | **Oracle** (consult, never copy) |
| {Modern critical ed.} | | ❌ | Not staged (copyright); usable as base if the user supplies it |

## Provenance links
- Base: {url}
- Issue: {url}

## `_source/` contents (git-ignored)
| File | What | Present? |
|------|------|----------|
| | | |

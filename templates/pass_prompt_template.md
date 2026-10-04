# TASK: Execute Pass {ID} ({name}) on {Author}, *{Work}*

<!--
Prompt skeleton for one base-text refinement pass, run as ONE interactive Claude Code session.
Save the filled-in prompt as `_source/pass{ID}_prompt.md` so the method is reproducible.
Real examples: examples/pass-prompts/. Keep every section; delete the guidance comments.
-->

You are running **Pass {ID}** of a {Language} base-text project: {Author}, *{Work}* ({K} units,
{edition}). **Passes {list} are complete** and `{validator}` reports ALL CLEAN. Your job now is
**{one-sentence purpose}**.

REPO ROOT: `{path}`
PROJECT DIR: `{Author}/{Work}` (cd here; all paths below are relative to it)

## What {ID} is (and is NOT)
- **IS:** {the specific check}. **The {base} page image is the sole arbiter.**
- **IS NOT:** {the neighbouring passes' jobs}. Do not do those here.
- {If a witness or oracle is involved:} it is a **detector, never an authority**. Flag candidates
  with it, adjudicate every one on the image, and never rewrite the text toward it.

## Read first (in full)
1. `_source/README.md`: the project spec. **Its editorial conventions override any default.**
2. `_source/{previous pass report}.md`: what the last pass did and its carry-forward items.
3. `_source/uncertain_readings.md`: open items, especially any flagged "for {ID}".

## Inputs
- **Text under check (edit these):** `{LATIN|GREEK}/…` {and the mirror `_source/passB_final/…`}.
  Never alter the header lines or the `====` rule unless the image proves them wrong (log it).
- **Ground truth (read-only):** `_source/{pages}/…`. **Glob by printed page and never compute leaves**
  (offsets drift, and some leaves are double-scanned). Open with the Read tool.
- **Witness / oracle (if any):** `_source/{…}`.
- **Tooling:** `{validator}` (must stay ALL CLEAN), `{assemble}` (orchestrator runs it once, at the end).

## Technique
- Read the whole page first; for any doubtful glyph, **crop and enlarge ~3×** with PIL and read
  the crop (accents, breathings, final sigma, italic vs roman, bold vs regular, section numerals).
- **Fan out** one subagent per unit, or per contiguous page range, on **disjoint files**, so they can
  run in parallel without write conflicts. De-risk by launching one or two first. Subagents report
  back by page number with PASS/FAIL and fix locations. They do **not** run the assembler.
- {Content-filter constraint, if it has bitten this corpus:} keep each model generation to ~1–2 words
  of source text. Fix with **tiny edits**. Restore any dropped chunk by copying OCR **disk→disk with
  Python**, then correcting it word by word against the image. Never author flowing source text.

## Carry-forward items (verify on the image; do not restructure)
1. {…}

## Discipline
- Fix **in place** only what the image proves. Log everything else as a doubt.
- Do not renumber or re-scope units. If the image contradicts the manifest, **log it** and do not
  silently change structure.
- Do not start any other pass. Do not modify files outside `{dirs}` and the reports below.

## Output / definition of done
1. Corrections applied in place, with `{validator}` → **ALL CLEAN** and the trees byte-identical.
2. `_source/{report}.md`: what was checked, correction counts by class, per-unit tally, and items
   handed to later passes.
3. `_source/uncertain_readings.md` updated (mark items RESOLVED; add new ones under `## Pass {ID}`).
4. Commit the tracked text so the pass is a visible diff:
   `git commit -m "{author} {work}: {lang} base text, {ID} ({name})"`
5. Finish with a short summary and **stop**. The next pass is {next ID}.

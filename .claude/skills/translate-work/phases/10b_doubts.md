# Phase 10b: Doubt resolution against other sources (Pass R8; subagent, one packet or role `doubts`)

Every doubt still unsettled after R6 is checked against **every other source the run has**, and
gets a final disposition in the ledger. Convergence runs after you and re-reads what you change.

Your assignment is a packet (its doubts) or the role `doubts` (all of them). Your checklist
(`checklists/R8/<id>.json`, `status_contract.md` §0) lists them as `d:<doubt id>` items: the open
**and deferred** doubts. Show one with `doubts.py list --work-dir ${WORK_DIR} --json` (filter by
`--unit`/`--pages`).

**Runs without a ledger** (no `run/doubts.jsonl`, or `MODE: legacy`): the doubts are free text in
`${SRC_DIR}/uncertain_readings.md` (merged `## Doubts` of every pass; per pass in
`${RUN_DIR}/notes/<PHASE>/*.md`). Skip those already settled in `apparatus_pass.md` (R6's docket)
or later notes. Enter each remaining one first with `doubts.py add --phase R8 --packet <id>`,
then settle it like the rest.

## Sources (use each that exists; `survey.json` → `other_sources`, `witness_candidates`, `copyright_bases`)

1. **The base page image** again, cropped and enlarged: what exactly is printed.
2. **R6's decisions**: the docket and `## Settled cruxes` in `apparatus_pass.md`, and the
   edition's own apparatus and errata on that page.
3. **The manuscript(s)** or other witnesses, if the survey lists a digitized copy (e.g. a IIIF
   manifest): fetch only the folios you need (IIIF Image API region/size, a few hundred KB
   each) into `${RUN_DIR}/crops/R8/`; find the folio from the edition's folio markers or
   apparatus. Record shelfmark + folio for every reading you cite.
4. **Other editions and digital texts** (the staged witness in `pages/witness/`, Migne,
   TLG/First1KGreek/Corpus Corporum texts): fetch the passage only.
   A copyright critical edition counts only if the user supplied a copy (in `_source/incoming/`);
   cite it like the oracle (`copyright.md`).
5. **The oracle translation**, only as a detector of sense (which reading it translates);
   never proof, never quoted beyond a few words (`copyright.md`).
If a source you need is unreachable, say so in the reason.

## Policy: the critical editor is trusted

- **Change** the text only for a demonstrable **transcription error**: (a) our text differs from
  the printed page (image-proved), or (b) the edition misprinted what it meant to print: an
  impossible form or single-letter slip, where the manuscript or the editor's own apparatus
  shows the intended letter and the apparatus records **no** deliberate choice (R6's bright line,
  `10_variants.md`).
- **Never** change an editorial choice (an adopted variant, a conjecture, the editor's
  orthography or accentuation, a supplement or seclusion), even if the manuscript or another
  edition reads otherwise. At most note it (`## Settled cruxes`).
- The README or a resolved decision may state a stricter house policy; it wins.

## Disposition (one `doubts.py update --phase R8 --by <id>` per doubt, `status_contract.md` §2a)

- `confirmed-as-printed`: the text stands; reason names the sources checked;
- `changed`: minimal edit, image re-checked, `check_base.py` clean; count it as a fix. If your edit changes words inside a unit's incipit or explicit, sync the field with `manifest_edit.py` in the same step (`conventions.md` → *Editing discipline*): the field follows the text;
- `escalated`: a real editorial choice (`decisions.py add` first, `--decision <id>`);
- `deferred`: still unsettleable, with the reason and what would settle it.
A packet agent edits only its packet's units; the `doubts` role may edit any unit.

## Output

Notes `${RUN_DIR}/notes/R8/<id>.md` (status_contract §1) with, before `## Fixes`, a table:
doubt id | unit/page | printed | sources checked (with folio) | disposition | why. Add a
`## Settled cruxes` section (one line per reading the translator or validator must not "fix"
back). Status `${RUN_DIR}/status/R8/<id>.json` (`fixes` = changed, `doubts` = entries you added).

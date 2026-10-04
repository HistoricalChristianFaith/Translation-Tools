# Phase 10: Apparatus & variant pass (Pass R6; subagent, role `docket`)

A narrow, evidence-driven pass over the **residual cruxes**. This is the one pass that may make
the text **depart from what the edition prints**, and only when the evidence converges. You are
the only agent running; you may edit any unit.

## Build the docket

Collect every open item that asks "is the printed text right?":
- `[R6]` items in `carry_forward.md`;
- probable misprints and doubtful readings in `uncertain_readings.md`;
- the `## Variants` lists in `variants_witness.md` (R1) that point to a likely base misprint;
- the base-edition doubts raised in `oracle_discrepancies.md` (R3);
- every **open doubt in the ledger** (`d:` items on your checklist, `checklists/R6/docket.json`).

Number the items. Every item gets a verdict. Record each ledger doubt's verdict with
`doubts.py update` (`status_contract.md` §2a): EMEND → `changed`, KEEP → `confirmed-as-printed`,
a real editorial choice → `escalated`; `deferred` only with a reason (e.g. it needs a source you
don't have, such as the manuscript: R8 checks the run's other sources next; say what to check).

## Evidence (in this order)

1. **The base page image**, cropped: confirm what is actually printed.
2. **The edition's own apparatus and errata**, at the foot of the page or in the volume's
   addenda (crop them). An editor's own correction, "scripsi", or a listed erratum is strong
   evidence.
3. **The secondary witness** (`pages/witness/`), where it exists.
4. **The corpus itself.** How the work spells or phrases the same word elsewhere (grep the unit
   files).
5. The oracle only as a hint of sense, never as proof (`copyright.md`).

## Policy (the bright line)

- **EMEND** only an unambiguous **single-letter slip or impossible non-word**, and only when at
  least one other piece of evidence converges: the apparatus or errata, the witness, or the
  corpus's correct form elsewhere. Also emend where the editor himself marks a correction.
- **KEEP** (record, don't adopt) everything else:
  - a real word at multi-letter distance from the alternative;
  - a genuine variant between editions;
  - anything that is only "more sensible";
  - a crux (keep the edition's obelus or supplement).
- Never import a reading from a copyright modern edition.

For each emendation: a minimal edit, and the image re-checked afterwards. If your edit changes words inside a unit's incipit or explicit, sync the field with `manifest_edit.py` in the same step (`conventions.md` → *Editing discipline*): the field follows the text. Then run
`python3 ${TOOLS_DIR}/check_base.py --work-dir ${WORK_DIR} --quiet` until it is ALL CLEAN.

## Output

- Notes `${RUN_DIR}/notes/R6/docket.md`:
  - the docket as a table (item | unit/page | printed | alternative | evidence | verdict
    EMEND/KEEP | why);
  - `## Fixes` = the emendations;
  - a section **`## Settled cruxes`**: one short line per item a translator or validator must
    not "fix" back (e.g. "Hom XI §3: *Iacobus* (James), not Paulus: keep"). The configure
    phase copies these into the validator's house rules.
- Status `${RUN_DIR}/status/R6/docket.json` (`fixes` = emendations).

# Gate repair (subagent, one packet; PHASE = `<P>-repair`)

The deterministic gate (`check_base.py`) failed on your packet's units after phase `<P>`.
Your assignment file (`${RUN_DIR}/assignments/<P>-repair/<packet>.md`) lists the exact error
lines. Examples:
- unbalanced `» «`;
- an anchor gap (a page with no anchor, or anchors out of order);
- the section sequence broken;
- a missing heading or separator;
- a forbidden character;
- `unit <n>: incipit not found at the start of the body: '…'` (or `explicit … at the end`): the
  manifest field and the unit file disagree.

For each error:
1. Find the spot in the unit file (for an anchor gap, the pages named; for unbalanced marks,
   scan the unit for the open or close without a partner).
2. **Settle it on the page image** (crop). The fix is whatever the print shows: a missing
   anchor at the true page turn, a guillemet at the true end of the quotation, a section numeral
   as printed. Never "fix" the gate by deleting real text or marks. If the print itself is
   irregular (e.g. the edition really skips a section number), don't change the text; report it
   under Carry-forward `[orchestrator]` with the exact check setting to change (e.g.
   `section_start_for`).
   **An incipit/explicit error:** check the text at that spot on the image. If the text matches
   the image, or carries a recorded emendation (R6 docket, R8 `changed`, a resolved decision),
   sync the field to the text with `manifest_edit.py` (`conventions.md` → *Editing discipline*).
   If the text is wrong, fix it on the image, then sync the field if it still differs. Never edit
   text toward the field.
3. Re-run `python3 ${TOOLS_DIR}/check_base.py --work-dir ${WORK_DIR} --quiet` until your units
   are clean.

Notes `${RUN_DIR}/notes/<P>-repair/<packet>.md`. Status
`${RUN_DIR}/status/<P>-repair/<packet>.json`. Edit only your packet's units.

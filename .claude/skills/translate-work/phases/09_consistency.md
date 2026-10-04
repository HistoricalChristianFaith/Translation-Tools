# Phase 09: Whole-corpus consistency & conventions (Pass R5; subagent, role `corpus`)

You are the **single editor** of the whole text. This is the only agent in the run, so you may
edit **every** unit file. Make the corpus uniform in its conventions **without** moving away from
what the edition prints. Every text change must be justified by the image or by a resolved
decision.

Inputs:
- all unit files;
- `manifest.json`, `README.md`;
- the reports so far (`passB_report.md`, `recollation_pass.md`, `r4_boundary_audit.md`,
  `variants_witness.md`, `oracle_discrepancies.md`), `uncertain_readings.md`;
- `[R5]` items in `carry_forward.md`;
- resolved decisions.

`MODE: apply-decision <id>` (prompt `MODE=apply-decision <id>`) means: do **only** step 4 for that decision, then
report.

## Checks

0. **Code points.** If `${RUN_DIR}/normalize/normalize.py` exists, run it on `${LANG_DIR}`
   (dry run). Later agents' typing reintroduces variants (e.g. tonos for oxia): apply its
   invisible categories with `--write` and report the counts. Don't hunt code points by hand.
1. **Orthography as printed.** Scan the whole corpus for variant spellings of the same word
   (e.g. *cael-/coel-*, *-tio/-cio*, *Hierusalem/Ierusalem*, accent patterns in Greek). For
   each outlier, check its page image. It's a **slip** if the edition prints the majority form
   there, so fix it. It's **kept** if the edition really varies; log it as a NOTE.
2. **Marks.** Guillemets and asterisks are used the same way in every unit (heading lemma line vs
   body). Check lemma-line glyphs **by eye against the image**: `check_base.py` scans them but
   can't know what the edition prints. Check supplements and seclusions, lacunae, rubrics and
   double brackets.
3. **Headings and header lines.** Heading lines are in one uniform format matching the manifest.
   The 4 `#` header lines are accurate and uniformly phrased (source pages correct).
4. **Resolved decisions** (`decisions.py list --resolved`). Apply each one that changes text,
   corpus-wide (e.g. J→I everywhere; reinsert or drop a class of inline Greek). If your edit changes words inside a unit's incipit or explicit, sync the field with `manifest_edit.py` in the same step (`conventions.md` → *Editing discipline*): the field follows the text. Where the
   decision changes what `check_base.py` should enforce, update **only** the `checks` block of
   `${RUN_DIR}/manifest.json` (e.g. add `"[Jj]"` to `forbid`). Never touch the rest of the
   manifest.
5. **Inline other-language material.** One policy for the whole corpus (see `conventions.md`
   and the decisions). Words the author himself cites or glosses stay, in their own script,
   image-verified. Queue a decision if the README doesn't settle it.
6. **The unit → passage table.** For every unit, the biblical passage or topic it expounds, as
   the text itself shows (lemma, quoted verses). Write `${RUN_DIR}/unit_meta.json` as
   `{"1": "Lev. 1 (the whole burnt offering)", …}`, with short labels. The configure phase uses
   it.

## Output

After your edits, run `python3 ${TOOLS_DIR}/check_base.py --work-dir ${WORK_DIR} --quiet` and make
it ALL CLEAN. Notes `${RUN_DIR}/notes/R5/corpus.md`: each class of check, what changed (counts
plus examples), and what was kept and why. Status `${RUN_DIR}/status/R5/corpus.json`.

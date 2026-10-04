# Phase 14: Validation review (subagent, one packet)

For each unit of this round, the orchestrator had:
- a **scan agent** (one per unit, `14a_validate_scan.md`) judge whether the English faithfully
  and completely renders **our source text** (the sole arbiter), and write its findings;
- `validate.py apply` **auto-apply** every fix that was safe to apply (unique match, marks
  balanced, block count unchanged). In a confirm round (`MODE: confirm`) nothing was applied.

You stand in for the human reviewer, for your packet's units only.

**Rounds.** Validation runs in rounds, each with its own PHASE key: `validate` (round 1),
`validate-r2` … `validate-r5` (repeated until a round finds nothing substantive), `validate-g<j>`
(a recheck against our source of the units grading round `j` changed), then `validate-g<j>-r2`
and `validate-g<j>-r3` (rechecks of the recheck's own changes), and `<K>-confirm` (one last
check of a loop that ended with changes left, e.g. `validate-r5-confirm`). Your PHASE is your
round; every path below uses it. You are a fresh pair of eyes: judge the English as it stands
now, even where an earlier round settled something differently.

Inputs (per unit `n` of your packet, where `<stem>` = the English file name without `.txt`):
- the English: `${EN_DIR}/<stem>.txt`;
- the source: `${LANG_DIR}/<unit file>`;
- the English before this round's auto-fixes: `${RUN_DIR}/snapshots/pre-<PHASE>/<stem>.txt`;
- the scan's findings: `${RUN_DIR}/findings/<PHASE>/<stem>.json`, and what `apply` did with them:
  `${RUN_DIR}/findings/<PHASE>/<stem>.apply.json` (`applied`, and `skipped` with a reason each).
  No findings file: the unit was `unvalidated` (English or source missing): list it and move on.
  Rounds run before the subagent migration: `${RUN_DIR}/logs/<PHASE>/<stem>.1.txt` (and
  `.2.txt` if it had to retry); older runs' round 1: `${RUN_DIR}/logs/<SLUG>/validation/<stem>.1.txt`,
  where `<SLUG>` is the one folder under `${RUN_DIR}/logs/` that has a `validation/` subfolder;
- the house rules: `VALIDATION_HOUSE_RULES` in `${RUN_DIR}/work_config.py`;
- `apparatus_pass.md` (`## Settled cruxes`);
- earlier rounds' notes on your packet, for context: `${RUN_DIR}/notes/validate*/<packet>.md`
  and `${RUN_DIR}/notes/grade*/<packet>.md` (those that exist).

## For each unit

1. **Review the auto-applied fixes:**
   `diff "${RUN_DIR}/snapshots/pre-<PHASE>/<stem>.txt" "${EN_DIR}/<stem>.txt"`.
   For each change, check the source. **Revert** any fix that is wrong, that "normalizes"
   Scripture toward a modern Bible, that undoes a settled crux or house rendering, or that makes
   the English worse. Keep the good ones.
2. **Handle the findings the scan couldn't fix** (findings without a `fix`, and the `skipped`
   ones in the journal). For each significant or moderate finding: check the source. If it's a
   real defect, fix the English with a minimal edit, keeping every mark and the block structure
   (one paragraph per block, blank line between blocks). If it's a false positive (house rule,
   settled crux), note it as such.
3. **Structure.** `python3 "${TOOLS_DIR}/validate.py" --config "${RUN_DIR}/work_config.py" --structure-only --units <your units>`
   must show **no `ERROR`** when you finish. Settle every open `WARN` on a unit you edited, and
   any carried from translate, the way `13_translate.md` step 4 does: re-read the block against
   the source; a real slip is fixed, anything else is recorded with
   `validate.py … settle <uid> --check <check> [--block n] --by <PHASE>/<packet> --reason "…"`.
   **Never add words, repeat content or expand a rendering to clear a warning.**

There is no in-round re-check: a fresh scan agent checks your substantive edits in the next round
(or, at the end of a loop, in a confirm round). So keep each edit minimal and exact.

Judge only **English against our source**. Never use an outside translation. Keep the English
the model wrote unless it's actually wrong; don't rewrite for taste.

## MODE: confirm

Your PHASE ends in `-confirm`. Nothing was auto-applied: the diff in step 1 is empty, and the
scan's `fix` objects are suggestions only. Settle **every** finding by hand: check it against the
source, apply the good fixes yourself (minimal edits, marks and blocks intact), dismiss the
rest with a reason. A confirm round never triggers another round: any substantive fix you make is
listed in the report as `not settled after confirm`, for a human look.

## Substantive or trivial

Every fix that stands at the end (a kept auto-fix, or your own edit) is one or the other. **Your
judgment of what the change does decides, not the scan's severity label.**
- **Substantive:** it changes what the English says: a mistranslation or shifted sense, a wrong
  referent, subject, tense, mood or construction that alters the meaning, an omission or
  addition, a Scripture quotation, a name.
- **Trivial:** the meaning is the same before and after: wording, style, punctuation, spelling,
  typography, a term aligned with the house vocabulary without changing the sense.

The substantive count decides whether your packet gets another validation round, so count
honestly: a reworded sentence that says the same thing is trivial. If a fix undoes a fix from an
earlier round, it still counts; add `(reverses <that round's PHASE>)` to its line in the notes.

## Output

Notes `${RUN_DIR}/notes/<PHASE>/<packet>.md`:
- `## Fixes`: reverted auto-fixes and every fix that stands, each with unit, block, reason, and
  `[substantive]` or `[trivial]`;
- `## Doubts`: open questions;
- `## Carry-forward`: false-positive *patterns* worth adding to the house rules, tagged
  `[orchestrator]`;
- a Summary line per unit: scan score, auto-fixes kept/reverted, findings fixed/dismissed,
  substantive fixes, warnings settled.

Status `${RUN_DIR}/status/<PHASE>/<packet>.json`, with `"fixes"` (every fix that stands) and
`"substantive"` (those of them that are substantive). Edit only your packet's English files.

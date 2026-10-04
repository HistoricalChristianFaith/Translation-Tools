# Phase 15: Grading review (subagent, one packet)

For each unit of this round that has an oracle extract, the orchestrator had a **scan agent**
(one per unit, `15a_grade_scan.md`) judge how closely our English matches the **sense** of the
oracle translation. The grader wrote nothing to our files. You settle its divergences, for your
packet's units.

**Rounds.** Grading runs in rounds, each with its own PHASE key: `grade` (round 1), then
`grade-r2`, `grade-r3` while a round still makes substantive fixes. After every round that
changed something, validation rounds (`validate-g<k>`, then `validate-g<k>-r2`, `-r3` while they
still change something) recheck those units against our source.
Your PHASE is your round; every path below uses it. The grader flags the oracle's own
differences again every round: judge each afresh on the source.

Inputs (per unit; `<stem>` = English file name without `.txt`):
- the English: `${EN_DIR}/<stem>.txt`;
- the source: `${LANG_DIR}/<unit file>`;
- the grade: `${RUN_DIR}/findings/<PHASE>/<stem>.json` (JSON: score, divergences). Rounds run
  before the subagent migration: `${RUN_DIR}/logs/<PHASE>/<stem>.1.txt`; older runs' round 1:
  `${RUN_DIR}/logs/<SLUG>/grading/<stem>.1.txt`;
- `GRADING_CAVEATS` and `ORACLE_NOTES` in `work_config.py`;
- the oracle extract: `${SRC_DIR}/oracle/extracts/unit<NN>.txt`. Copyright: consult only, never
  copy;
- earlier rounds' notes on your packet, for context: `${RUN_DIR}/notes/grade*/<packet>.md` and
  `${RUN_DIR}/notes/validate*/<packet>.md` (those that exist).

Units with no grade file were ungraded (no oracle coverage). List them and move on.

## For each graded divergence (significant and moderate first)

**Settle it against our source, not the oracle** (`copyright.md`):
- **The source supports the oracle's sense** → our English is wrong. Fix it with a minimal edit
  in our own words (never the oracle's), keeping the marks and block structure.
- **The source supports our English** (the oracle follows a different reading, paraphrases,
  abridges, or errs) → keep ours. Record it as a known oracle divergence.
- **Genuinely ambiguous** → keep ours, and add a Doubt.

When you finish, `python3 "${TOOLS_DIR}/validate.py" --config "${RUN_DIR}/work_config.py" --structure-only --units <the units you edited>`
must show **no `ERROR`**. Settle every open `WARN` on a unit you edited as `14_validate_review.md`
step 3 says (`--by <PHASE>/<packet>`). **Never add words, repeat content or expand a rendering to
clear a warning.**

## Substantive or trivial

Classify every fix you make as in `14_validate_review.md` → *Substantive or trivial*: it is
**substantive** when it changes what the English says (sense, referent, construction that alters
the meaning, omission or addition, Scripture, name), **trivial** when the meaning is unchanged.
Your judgment decides, not the grader's severity label. Kept divergences are not fixes and never
count. The substantive count decides whether your packet gets another grading round and a
recheck against the source. If a fix undoes a fix from an earlier round, add
`(reverses <that round's PHASE>)` to its line in the notes.

## Output

Notes `${RUN_DIR}/notes/<PHASE>/<packet>.md`:
- a Summary line per unit: score, divergences fixed / kept (with reason class), substantive
  fixes;
- `## Fixes`: each with unit, block, reason, and `[substantive]` or `[trivial]`;
- `## Doubts`;
- `## Carry-forward`: new oracle divergences worth adding to `GRADING_CAVEATS`, tagged
  `[orchestrator]`.

Status `${RUN_DIR}/status/<PHASE>/<packet>.json`, with `"fixes"` and `"substantive"`. Edit only
your packet's English files.

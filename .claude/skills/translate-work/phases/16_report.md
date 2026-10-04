# Phase 16: Final report (subagent, role `report`)

Write `${RUN_DIR}/FINAL_REPORT.md`, the record of the run for the user and for anyone reviewing
the translation later. Base it only on files, never on guesses. Collect numbers with the tools:
- `python3 ${TOOLS_DIR}/status_check.py --work-dir ${WORK_DIR} --phase <P>` for each per-packet
  phase;
- `--expect corpus` / `--expect docket` / `--expect seams` for the single-agent ones;
- `python3 ${TOOLS_DIR}/state.py show --work-dir ${WORK_DIR}`;
- `python3 ${TOOLS_DIR}/decisions.py list --work-dir ${WORK_DIR} --resolved`;
- `python3 ${TOOLS_DIR}/doubts.py count --work-dir ${WORK_DIR}` (also `--group phase`, and
  `list --status open|deferred|escalated`, `list --phase R8`), if the run has a doubt ledger
  (`run/doubts.jsonl`); `doubt_resolution.md` (R8);
- `${RUN_DIR}/normalize/normalize.json`, if the normalize phase ran;
- `${RUN_DIR}/manifest_edits.jsonl` (incipit / explicit synced to the text: unit, field, old → new,
  by whom, why), if it exists;
- `python3 ${TOOLS_DIR}/merge_notes.py --work-dir ${WORK_DIR} --pending` (`[orchestrator]` items
  never settled) and `${RUN_DIR}/orchestrator_acks.jsonl` (how the others were settled);
- translation: `status_check.py --work-dir ${WORK_DIR} --phase translate --by-unit --sum warns`
  (units, warnings settled), and `${SRC_DIR}/run/translate_notes.md` (`## Checks`, `## Doubts`);
- the review rounds: every `${RUN_DIR}/logs/validate*.log` and `grade*.log` (each is its round's
  summary table, written by `validate.py summary` / `grade.py summary`; the first and last round
  of each give the before/after scores; what `apply` did is in `${RUN_DIR}/logs/apply/<K>.log`),
  and for each round key `<K>` (`validate`, `validate-r2`, …, `grade`, `grade-r2`, …,
  `validate-g1`, `validate-g1-r2`, …, `validate-r5-confirm`, `validate-g<j>-r3-confirm`):
  `status_check.py --work-dir ${WORK_DIR} --phase <K> --whole --packets <its packets> --sum substantive`
  (its packets: the ids with a status file in `${RUN_DIR}/status/<K>/`); the state notes on the
  `validate` and `grade` phases (rounds run, anything not settled, every `not settled after
  confirm` passage);
- structure: `python3 ${TOOLS_DIR}/validate.py --config ${RUN_DIR}/work_config.py --structure-only`
  (open warnings, and the settled ones with their reasons);
- `grep -h "(reverses " "${RUN_DIR}"/notes/validate*/*.md "${RUN_DIR}"/notes/grade*/*.md`: passages
  where a later round undid an earlier round's fix (back-and-forth); list each for a human look.

## Structure (keep the Summary first and short; the orchestrator shows only it to the user)

```markdown
# <Author>, <Work>: translation report

## Summary
- Result: <N> units translated → `<WORK_DIR>/english/` (one file per unit)
- Base text: <edition>, <pages>; <K> source-text passes; converged: yes | no (<packets>)
- Fidelity (validator, vs our source): mean <first-round score> → <last-round score>/100 over <r> rounds; <n> significant findings open
- Sense vs oracle (<oracle>): mean <first> → <last>/100 over <m> graded units, <r> rounds | no oracle
- Review rounds: <per round: key, packets, fixes, substantive>; not settled: <packets> | none
- Open items: <x> uncertain readings (ledger: <o> open / <d> deferred of <t>), <y> doubts from review, decisions auto-resolved: <z>
- Review first: <3-6 specific units or items that most deserve a human look, and why>

---

## Sources
## Source-text passes   (table: pass | agents | fixes | doubts | report file)
## Editorial decisions  (resolved decisions: question → choice, by user or auto)
## Normalization        (script changes by category, B mode; pointer to run/normalize/summary.md)
## Emendations (R6)     (count + pointer to apparatus_pass.md)
## Doubt outcomes       (ledger counts by status and by phase; every R8 disposition other than
                         confirmed-as-printed: id | unit/page | outcome | source; deferred ones with reason)
## Translation          (per-unit table: unit | validator score (last round) | fixes (substantive) summed over rounds | grade | notes)
## Review rounds        (table: round key | packets | fixes | substantive | mean score; then the back-and-forth passages)
## Structure warnings   (open ones by unit; settled ones: unit | block | check | by | reason)
## Open items           (pointers: uncertain_readings.md, review notes; every `not settled after
                         confirm` passage, for a human look; every `[orchestrator]` item still
                         pending, with its id)
## Manifest edits       (manifest_edits.jsonl as a table; "none" if absent)
## Files                (where everything is; how to review: diffs in run/snapshots/)
```

Copyright: no oracle text in the report beyond a few words per item.

Status `${RUN_DIR}/status/report/report.json`, with notes `${RUN_DIR}/notes/report/report.md` (a
one-line Summary is enough). Return under 20 words.

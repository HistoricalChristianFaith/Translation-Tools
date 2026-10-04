# Phase 12: Configure the translation (subagent, role `configure`)

Write `${RUN_DIR}/work_config.py`, the per-work configuration used by
`${TOOLS_DIR}/translate.py`, `validate.py` and `grade.py`. Those tools build the bundles the
translate, validate and grade subagents work from, and the three rule blocks you write here go
into every bundle. The quality of the translation depends mostly on them: they carry everything
the source-text passes learned to agents that read nothing else (they don't read the README, the
reports or the decisions).

## Read first

- `${TOOLS_DIR}/work_config_template.py`: what every setting means;
- `${TOOLS_DIR}/skill_config_base.py`: which settings are derived for you;
- `${SRC_DIR}/README.md`, `manifest.json`, `${RUN_DIR}/unit_meta.json`;
- the reports: `consistency_pass.md`, `apparatus_pass.md` and `doubt_resolution.md` (R8; both
  **`## Settled cruxes`**),
  `oracle_discrepancies.md` (**`## Oracle divergences`**), `uncertain_readings.md`;
- resolved decisions (those from phase `plan` were answered by the user at plan approval: apply
  them, don't queue them again);
- 2–3 unit files (to see the real markup).

## Write the file

```python
import os, sys
sys.path.insert(0, "<absolute TOOLS_DIR>")
import skill_config_base as B
globals().update(B.defaults("<absolute WORK_DIR>"))

WORK_CONTEXT = "..."            # 2-5 sentences: what the work is, how it survives, the base edition, what it expounds
HELD_LINES = [...]              # body lines that are editorial notes, not the author's text -> fixed English
TRANSLATION_RULES = (...)       # see below
VALIDATION_HOUSE_RULES = (...)  # see below
ENDING_CHECKS = [...]           # e.g. [(r"Amen", r"Amen", "closing doxology")] if units end with one
ORACLE_LABEL = "..."; ORACLE_SHORT = "..."   # only if an oracle exists
GRADING_CAVEATS = (...)         # see below
ORACLE_NOTES = {n: "..."}       # per-unit notes (partial coverage, shared excerpts), optional
# Optional overrides: heading_en(n), english_header(n)
```

Override `heading_en` if the unit labels don't make a natural English heading (e.g.
`§ XI — 1 Corinthians ii 12–15`). It must depend only on `n` and fixed data.

### `TRANSLATION_RULES`

Bullets, `"- TOPIC. instruction\n"`. The generic rules (`13_translate.md`) already cover: output
only the translation, keep the block structure, keep `» «` and `* *`, and translate Scripture as
it stands.
**Add, specifically for this corpus:**
- **Scripture:** which text the author quotes (Old Latin / LXX / NT Greek) and its numbering
  system (LXX Psalms, "Kingdoms", any book offset the reports found). Name concrete examples.
- **Names:** the edition's spellings and their standard English forms (take them from the
  text). Say that names the author etymologizes keep his form, with a gloss.
- **Fixed vocabulary:** the 10–25 recurring technical terms and one English rendering each.
- **Every mark the base still carries** and exactly what to do with it, listing the actual
  instances (e.g. "only four square-bracket interventions exist: …"). This covers supplements,
  seclusions, rubrics, verse labels, double brackets, cruxes and lacunae.
- **House policy: trust the critical editor.** When the base is a critical edition, its
  supplements `⟨ ⟩` and seclusions `[ ]` are handled **silently** in the English: read every
  supplement into the sense, omit every secluded word, and print **no** brackets for either in
  the English (the source-language text keeps them as printed). This is settled; **do not queue a
  decision about it.** State it in `TRANSLATION_RULES` with the actual instances, and list the
  omitted seclusions in `VALIDATION_HOUSE_RULES` so the validator doesn't flag them as dropped
  text. (It doesn't cover `[ ]` used for rubrics or verse labels, or cruxes and lacunae; handle
  those per work as above.)
- **Deliberate irregularities to render as printed:** non-uniform doxologies, odd forms kept at
  R6. List them unit by unit.
- **Kept foreign words** (e.g. a Greek word the author glosses): keep them in their script, with
  a gloss.
- **Register:** keep the argumentative connectives; long periods may be broken up but no clause
  dropped; fragments may begin or end abruptly.

### `VALIDATION_HOUSE_RULES`

Lines starting `"  - "`. Everything the validator must **not** flag: every settled crux from
`apparatus_pass.md` and `doubt_resolution.md`, every deliberate irregularity, the house renderings of the fixed vocabulary,
kept foreign words, marks that are kept or dropped by design, and the numbering conventions.
Each stated precisely enough to recognize (unit + the words). Without this list the validator
re-flags settled decisions forever.

### `GRADING_CAVEATS` (only with an oracle)

The ways the oracle is not a tight yardstick, from `oracle_discrepancies.md`:
- which edition it translates;
- whether it abridges or paraphrases (for an anthology: "content in ours but absent from the
  oracle is its cut, not our addition");
- its known divergences, each in a few words (e.g. "Hom III: 'Elisha' (oracle 'Elijah': oracle
  slip)").

Copyright: at most a few words from the oracle per item.

## Test

1. `python3 "${TOOLS_DIR}/translate.py" --config "${RUN_DIR}/work_config.py" --check` must end in
   `Round-trip OK`. Fix parsing settings (`HELD_LINES`, `BODY_HEADING_RE` override) until it does.
2. **Pick the trial unit**: the **shortest** unit (fewest characters of source text). Don't
   translate it yourself: the orchestrator has a translate agent do it from your rules alone,
   then sends you back to review it (`MODE: trial-review`, below).

## Output

Notes `${RUN_DIR}/notes/configure/configure.md`:
- the rule blocks summarized;
- the trial unit;
- anything the orchestrator should know (e.g. `--images` recommended because a unit has many
  doubts).

Status `${RUN_DIR}/status/configure/configure.json`, with `"trial_unit": <n>`.

## MODE: trial-review

A translate agent has translated the trial unit from your rules alone (its bundle,
`${RUN_DIR}/bundles/translate/u<NN>.md`, is exactly what it saw). Read its English
(`${EN_DIR}/<stem>.txt`) against the source. Check the marks, names, Scripture wording, held lines
and heading, and read its notes (`${RUN_DIR}/notes/translate/u<NN>.md`).
- Something **systematic** is wrong (a name form, a Scripture convention, a mark, a fixed term):
  adjust the rules in `work_config.py`. `translate.py --check` must still pass.
- A one-off slip is not a rule problem: leave it to the review rounds.
- Don't edit the English yourself. If the rules changed, the orchestrator has the unit translated
  again.
- `python3 "${TOOLS_DIR}/validate.py" --config "${RUN_DIR}/work_config.py" --structure-only <stem>`
  must show no `ERROR`. Settle any open `WARN` as `13_translate.md` step 4 says (`--by
  configure/trial`); never pad.

Add a `## Trial review` section to the notes (what you checked, what you changed). Leave
`configure.json` as it is: your status is `${RUN_DIR}/status/configure/trial-review.json`, with
`"trial_unit": <n>`, `"rules_changed": true|false` and `"notes": "run/notes/configure/configure.md"`.

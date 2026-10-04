# Phase 14a: Validation scan of one unit (subagent, unit `u<NN>` or a batch of units)

You VALIDATE one unit's English translation against its SOURCE for fidelity, and write your
findings as JSON. You never edit anything else. Your PHASE is `<K>-scan`, where `<K>` is the
review round (`validate`, `validate-r2`, `validate-g1-r2`, `validate-r5-confirm`, …); your
ASSIGNMENT is a unit id (`u07`) or a batch of consecutive units (`u12-u17`, `boot.md` §3: then
everything below is done for each unit in turn). `<uid>` below is the unit you are working on.

- Bundle: `${RUN_DIR}/bundles/<K>/<uid>.md`. It holds the work context, the house rules, any open
  structure notes, the source file (the arbiter) and the English body.
- Output: the `output:` path in the bundle, `${RUN_DIR}/findings/<K>/<stem>.json`.

## Sources rule

Work from the bundle. **Don't consult** earlier findings, notes, reports, other units, or the
oracle (`_source/oracle/`): this judgment must not depend on the work it checks, or on the
yardstick grading uses later. Tools for reference are fine (e.g. a web search to identify a person
or a rare term), but **never use an outside Bible or translation** to judge a rendering. **Never
edit the English or the source**: `apply` refuses a unit whose English changed after its bundle
was made. You aren't told about earlier rounds; judge the English as it stands. **In a batch,
judge each unit on its own bundle only**: a finding for one unit never cites or relies on another
unit's source or English.

## What you judge

THE SOURCE IS THE SOLE ARBITER. Does the ENGLISH faithfully and COMPLETELY render what the source
says, in the sense the author's own argument requires? Read the whole unit so you can catch
internal inconsistencies.

WHAT COUNTS AS A FINDING:
- OMISSION: a source clause/word whose sense is absent from the English.
- ADDITION: English content whose sense is not in the source.
- MISTRANSLATION / SENSE-SHIFT: wrong sense, flipped negation, altered subject/object or referent,
  an allegorical identification the source does not support.
- SCRIPTURE: a quoted verse misrendered against the source quotation as printed.
- NAME/REFERENT: a name rendered so the person/place referred to differs.
- INCONSISTENCY: the same source word/phrase rendered incompatibly, or the English contradicting
  itself where the source is coherent.
- UNTRANSLATED / GARBLED: source left untranslated, or incoherent English.

WHAT DOES NOT COUNT (never flag):
- Independent wording/style (synonyms, clause order, sentence length, register) when the MEANING
  matches.
- Our editorial marks (» « around Scripture, * * around the lemma, and any others the house rules
  list). Marks are not meaning.
- Standard-English normalization of biblical names (same referent = not a defect).
- Everything the bundle's **House rules** list.

**Structure notes** (if the bundle has any): deterministic flags, e.g. a block much shorter than
its source. Check each against the source. A real omission there is a finding like any other; a
flag that the source explains is not.

**Fixes.** For each genuine finding, when (and ONLY when) a precise, minimal, SAFE correction
exists, include a `fix` object: `old` = a VERBATIM substring of OUR ENGLISH that occurs EXACTLY
ONCE (marks intact), `new` = the corrected English (same marks; change only what the defect
requires). Otherwise omit `fix`.

If the English is faithful throughout, return an empty findings array and a high score: do NOT
invent defects.

## Output: the findings file

One JSON object, nothing else in the file:
```json
{
  "score": 0-100, "grade": "A+..F", "fidelity": "high|moderate|low",
  "findings": [ { "locus": "<anchor phrase from OUR English>",
                  "severity": "minor|moderate|significant",
                  "category": "omission|addition|mistranslation|sense-shift|scripture|name|inconsistency|untranslated",
                  "source": "<the source words at issue>", "ours": "<our rendering>", "issue": "<one line>",
                  "fix": {"old": "...", "new": "..."} } ],
  "summary": "<1-3 sentences>"
}
```
Most severe first. Keep `source` and `ours` to a few words (`content_filter.md`).

Then check it, and repeat until it exits 0:
```
python3 "${TOOLS_DIR}/validate.py" --config "${RUN_DIR}/work_config.py" check-findings --phase <K> --unit <uid>
```
It checks the schema and tries every `fix` in order against the English, exactly as `apply` will.
A fix it rejects (`old` not found or not unique, marks unbalanced, block count changed): repair
the fix, or drop the `fix` object. **Keep the finding.** "Make it pass" never means deleting a
finding.

## Notes and status

Notes `${RUN_DIR}/notes/<K>-scan/<uid>.md`: a `## Summary` line (score, findings, significant)
and `## Doubts` (`- none` if empty).

Status `${RUN_DIR}/status/<K>-scan/<uid>.json`, written last:
```json
{"phase": "<K>-scan", "packet": "u07", "units": [7], "status": "done",
 "model": "<the exact model id you run as>", "score": 91, "findings": 4, "significant": 1,
 "notes": "run/notes/<K>-scan/u07.md"}
```
`model`: your model id as your environment states it (`unknown` if it doesn't). Final message
under 20 words, after your last unit, e.g. `validate-r2-scan u07 done: 91, 4 findings, 1 significant.`
or `validate-r2-scan u12-u17 done: 6 units, 9 findings, 1 significant.`

**MODE `retry`:** a previous agent died; start over from the bundle and overwrite its findings
file if one exists.

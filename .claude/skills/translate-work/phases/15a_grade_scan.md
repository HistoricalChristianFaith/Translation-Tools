# Phase 15a: Grading scan of one unit (subagent, unit `u<NN>` or a batch of units)

You GRADE one unit's English translation against a published reference translation (the
oracle), for SENSE fidelity, and write your divergences as JSON. You never edit anything. Your
PHASE is `<K>-scan`, where `<K>` is the grading round (`grade`, `grade-r2`, `grade-r3`); your
ASSIGNMENT is a unit id (`u07`) or a batch of consecutive units (`u12-u17`, `boot.md` §3: then
everything below is done for each unit in turn). `<uid>` below is the unit you are working on.

- Bundle: `${RUN_DIR}/bundles/<K>/<uid>.md`. It holds the grading caveats, the unit note, the
  source (context), our English and the reference.
- Output: the `output:` path in the bundle, `${RUN_DIR}/findings/<K>/<stem>.json`.

## Sources rule and copyright

Work from the bundle. **Don't consult** earlier findings, notes, reports or other units. Tools for
reference are fine. **Never edit** the English, the source or the oracle. The reference is a
copyright translation (`copyright.md`): consult it, never copy it. Your findings quote it only in
a few words per item. **In a batch, grade each unit on its own bundle only**: a divergence for one
unit never cites or relies on another unit's English, source or reference.

## What you judge

THE YARDSTICK IS THE REFERENCE named in the bundle. The source is supplied as context: use it to
tell a genuine sense-divergence apart from a wording difference, from the reference's own
interpretive freedom, or from a place where the reference follows a different reading than our
base. Read the bundle's **Grading caveats** and **Unit note** before grading.

WHAT COUNTS AS A DIVERGENCE (a difference in MEANING in OUR English):
- OMISSION: a clause whose sense is in the reference (and the source) but absent from ours.
- ADDITION: content in ours not in the source and not supportable from it.
- SHIFTED SENSE: altered subject/object, flipped negation, different referent or allegorical
  identification, wrong sense of an ambiguous word.
- SCRIPTURE: a quoted verse whose reference/wording points to a different passage/sense.
- NAME/REFERENT: a name rendered so the referent differs.
- TRUNCATION: ours stops materially earlier than the source runs.

WHAT DOES NOT COUNT: word choice, synonyms, sentence length, clause order, register, punctuation
when the meaning matches; our editorial marks (» « * * etc.); standard-English name
normalization; the reference's page numbers, running heads, footnote numbers and footnotes (PDF
noise); places where ours follows the source more closely than the reference.

Do NOT invent differences.

## Output: the findings file

One JSON object, nothing else in the file:
```json
{
  "score": "<0-100: how fully ours conveys the reference's sense across the overlap>",
  "grade": "A+..F", "sense_alignment": "high|moderate|low", "coverage": "full|partial|minimal",
  "divergences": [ { "locus": "<anchor phrase from OUR text>",
                     "severity": "minor|moderate|significant",
                     "category": "omission|addition|shifted-sense|scripture|name|truncation",
                     "oracle": "<brief: the reference sense>", "ours": "<brief: how ours differs>",
                     "note": "<one line; cite the source if it decides it>" } ],
  "summary": "<1-3 sentences>"
}
```
(`score` is a number.) Most severe first. Keep quoted snippets to a few words. Then check it, and
repeat until it exits 0:
```
python3 "${TOOLS_DIR}/grade.py" --config "${RUN_DIR}/work_config.py" check-findings --phase <K> --unit <uid>
```

## Notes and status

Notes `${RUN_DIR}/notes/<K>-scan/<uid>.md`: a `## Summary` line (score, divergences, significant)
and `## Doubts` (`- none` if empty). No oracle text beyond a few words.

Status `${RUN_DIR}/status/<K>-scan/<uid>.json`, written last:
```json
{"phase": "<K>-scan", "packet": "u07", "units": [7], "status": "done",
 "model": "<the exact model id you run as>", "score": 88, "findings": 3, "significant": 0,
 "notes": "run/notes/<K>-scan/u07.md"}
```
`findings` = the number of divergences. `model`: your model id as your environment states it
(`unknown` if it doesn't). Final message under 20 words, after your last unit, e.g.
`grade-scan u07 done: 88, 3 divergences.` or `grade-scan u12-u17 done: 6 units, 11 divergences.`

**MODE `retry`:** a previous agent died; start over from the bundle and overwrite its findings
file if one exists.

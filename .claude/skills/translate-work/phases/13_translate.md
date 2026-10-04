# Phase 13: Translate one unit (subagent, unit `u<NN>` or a batch of units)

You translate **one unit** from its bundle. Your ASSIGNMENT is a unit id (`u07`) or a batch of
consecutive units (`u12-u17`, `boot.md` §3: then everything below is done for each unit in turn).
`<uid>` below means the unit you are working on, and `<n>` its number.

- Bundle (your text and your rules): `${RUN_DIR}/bundles/translate/<uid>.md`
- Output (you write it): the `output:` path in the bundle, `${RUN_DIR}/translate/<uid>.out.txt`
- The English file it becomes: the `english:` path in the bundle (`assemble` writes it, never you)

## Sources rule

Your bundle is your text and your rules. **Don't consult** other units' English, the reports,
notes, earlier findings or the oracle extracts (`_source/oracle/`): the translation must not
depend on them. Later phases check your work against our source and grade it against the oracle,
so reading either would make those checks meaningless. **In a batch** you remember your own
earlier units: staying consistent with your own renderings there is allowed, and good. Still
don't open any English outside your batch. You may use any tool for reference, for
example a web search to identify a person, a place or a rare term. **Never take a rendering from
an existing English translation of this work, or from a modern Bible.** Edit only your own output
file: never the source, never an English file.

## Rules (every work; the bundle's *Rules for this work* add to them)

1. The output holds **only the translation**: the markers and the English. No preamble, notes,
   meta-commentary or quotation of the source. Never write "Here is the translation" or "Let me
   translate".
2. **Keep the block structure exactly.** Every `@@ n @@` marker of the bundle appears once in the
   output, in order, on its own line, followed by **one paragraph** of English: the translation
   of that block and nothing else. Never merge, split, add or drop a block. Keep any section
   number (`1.`, `2.`, …) at the head of its block.
3. Text between guillemets `» «` is Scripture the author **quotes**. Keep the guillemets around the
   quoted words and translate them in the source wording **as it stands**: never substitute a
   modern Bible or call a verse-lookup tool. Don't add or remove guillemets.
4. Text between asterisks `* *` is the lemma under comment. Keep the `* *` marks and translate the
   words.

**Page images** (only if the bundle lists `images:`; read `${PHASES_DIR}/shared/image_reading.md`
first). The scans of the printed pages this unit spans are listed in order. The source text is
transcribed and already page-verified through several passes, but a rare valid-but-wrong-word slip
can still hide. Whenever a word or phrase is grammatically impossible, breaks the sense, or looks
like a plausible mis-transcription, OPEN the matching page image and translate the reading the
printed page actually shows. Read the MAIN text and IGNORE the critical apparatus, margins, running
heads and page numbers. Don't otherwise emend, and add nothing to the output about what you
checked: a reading you doubt goes in your notes (`## Doubts`). If the bundle has a
`## Page images for this work` section, it refines this rule for this edition's pages.

## Procedure

1. Read the bundle.
2. Translate every block into the output file:
   ```
   @@ 1 @@
   <English of block 1, one paragraph>

   @@ 2 @@
   <English of block 2>
   ```
   You may write it in parts (Write the first blocks, then extend the file with Edit, appending
   after the last block). For a long unit, do: 10–15 blocks per write.
3. `python3 "${TOOLS_DIR}/translate.py" --config "${RUN_DIR}/work_config.py" assemble <uid>`. Fix every block named in an
   `ERROR` line in the output file and re-run until it exits 0 (it then writes the English file).
   Exit 2 (`REFUSED`) means the English was edited after an earlier assemble: stop this unit,
   write status `failed` with that reason (in a batch, go on with the next unit).
4. **Warnings.** Look at every `WARN` line from `assemble`, then run
   `python3 "${TOOLS_DIR}/validate.py" --config "${RUN_DIR}/work_config.py" --structure-only <uid>` and look at every
   `WARN` it prints. They are heuristics (`short-ratio`, `mid-sentence`, `ending:<label>`,
   `scaffold`, `marks`, `internal blank lines`): they point at places where something *may* have
   been dropped. For each one, re-read the block against the source:
   - **a real slip** (a clause dropped, the block stopped early, a mark lost, preamble leaked):
     fix the output file and re-run `assemble`;
   - **not a slip** (the source is wordy, Greek compresses, the sentence really ends there):
     - a `--structure-only` warning: record it, e.g.
       `python3 "${TOOLS_DIR}/validate.py" --config "${RUN_DIR}/work_config.py" settle <uid> --check short-ratio --block 7 --by translate/<uid> --reason "source repeats a lemma; nothing omitted"`
       (`ending:<label>` checks take no `--block`);
     - an `assemble`-only warning (`scaffold`, `marks`, `internal blank lines`): nothing to
       record with a tool.

     Either way, add a line to `## Checks` in your notes: `block 7: short-ratio 0.62: source
     has a repeated lemma; nothing omitted`.

   `--structure-only` must end with **no `ERROR` and no open `WARN`** for your unit.
   **Never add words, repeat content or expand a rendering to satisfy a length check. A faithful
   block shorter than the ratio is correct.** The ratio finds dropped clauses; it doesn't define a
   good length.
5. Notes, then status (below).

## MODEs

- `retry`: a previous agent on this unit died. Keep the blocks already in the output file;
  `assemble` reports the missing ones: finish those. **First** re-read the **last** block already
  in the file against its source: the previous agent may have died while writing it, and a
  cut-off block only raises a warning. A fresh dispatch that finds an output file already there
  does the same. If the English file already exists and `assemble` accepts the output, go on to
  step 4. In a batch, `retry` covers every unit: one already finished is skipped (`boot.md` §3),
  one with no output file yet is simply translated.
- `tiny-edit`: the content filter blocked an earlier attempt. Write **2–3 blocks per write**, and
  keep your own messages free of source text (`content_filter.md`). If even that is blocked, write
  status `filter_blocked` with the last block written. (Without this MODE, in a batch: a unit
  blocked even after `content_filter.md`'s steps gets `filter_blocked`, and you go on with the
  next unit.)

## Output

Notes `${RUN_DIR}/notes/translate/<uid>.md`:
```markdown
# translate — <uid> (<unit label>)
## Summary
One or two sentences: blocks translated, anything notable.
## Checks
- block 7: short-ratio 0.62: source repeats the lemma; nothing omitted
## Doubts
- block 12: <the reading you doubt, in a few words, and what you translated>
```
Doubts are in words only: never edit the source, and don't add them to the doubt ledger. Write
`- none` under an empty heading.

Status `${RUN_DIR}/status/translate/<uid>.json`, written last:
```json
{"phase": "translate", "packet": "u07", "units": [7], "status": "done",
 "model": "<the exact model id you run as, e.g. claude-opus-5-5>", "blocks": 23, "fixes": 0,
 "doubts": 0, "warns": 2, "notes": "run/notes/translate/u07.md"}
```
`fixes` = blocks you corrected after a check; `doubts` = items under `## Doubts`; `warns` = the
warnings you settled. `model`: your model id as your environment states it (`unknown` if it
doesn't). Then, after your last unit, a final message under 20 words, e.g.
`translate u07 done: 23 blocks, 2 warnings settled.` or
`translate u12-u17 done: 6 units, 3 warnings settled, 2 doubts.`

# Shared: how every subagent reports

Every subagent finishes by writing exactly two files, then returning **a message under 20
words**. The orchestrator never reads your reasoning. It reads your status file, and a tool reads
your notes. On the way, you keep your **checklist** (§0) and the **doubt ledger** (§2a) current.

`<id>` below is your ASSIGNMENT (`boot.md`): a packet (`p05`), a sub-packet (`p07a`), or a role
(`corpus`); `<PHASE>` is your PHASE.

## 0. Checklist first, mark as you go (per-packet phases)

The orchestrator has enumerated every item you must check in
`${RUN_DIR}/checklists/<PHASE>/<id>.json`: every page of your range (review phases: every unit,
`u<n>`), plus (`d:<doubt id>` items) every open doubt the ledger holds on those pages. Start with
`python3 "${TOOLS_DIR}/checklist.py" show --work-dir "${WORK_DIR}" --phase <PHASE> --id <id>`.
When you **finish** an item (never before), mark it, one command per item:
```
python3 "${TOOLS_DIR}/checklist.py" mark --work-dir "${WORK_DIR}" --phase <PHASE> --id <id> --item 175 --result "ok | 2 fixes | 1 doubt"
```
A `d:` item is checked by settling that doubt with `doubts.py update` (§2a). Before writing
status `done`, `checklist.py verify ... --id <id>` must print `COMPLETE`. If you can't finish,
write status `failed` with a reason naming the unchecked items. `status_check.py` sends back
(REDISPATCH) any `done` packet whose checklist is missing or has an unchecked item: **a missing
checklist is unknown coverage**. (No checklist file and none required, e.g. a role phase the
orchestrator didn't enumerate: skip this section.)

## Sub-packets

If your assignment says `sub-packet p07a … pages 173–186 ONLY`, a sibling agent is working on the
**same unit file** at the same time on other pages. Use `p07a` as `<id>` everywhere (notes,
status, checklist, ledger). Check and edit **only your pages**; unit start or end checks belong to
the sub-packet holding that page. Make only **small in-place edits** (Edit with a short, unique
old string; never rewrite or re-save the whole file); re-read before each edit, and if the
file changed under you, re-read and retry. Report anything outside your range as Carry-forward.
Add `"parent": "p07", "pages": "173-186"` to your status.

## 1. Notes: `${RUN_DIR}/notes/<PHASE>/<packet>.md`

```markdown
# <PHASE> — <packet> (<units, e.g. "Homily V" or "§§ XLV–LIII">)
## Summary
Two or three sentences: what you checked (pages), what you found.
## Fixes
- <unit> p.<page> §<n>: `<before>` → `<after>`: <class: accent | breathing | sigma | word | omission |
  addition | mark | anchor | section | boundary | punctuation> (image-verified; crop <file> if used)
## Doubts
- [<doubt id>] <unit> p.<page>: <what is doubtful, what you kept, why>
- settled: [<doubt id>] -> <new status>: <reason>   (earlier doubts you settled)
## Carry-forward
- [R4] <item for a later pass, tagged with its target: normalize B R2 R4 R1 R3 R5 R6 R8 convergence orchestrator>
```

- Write `- none` under a heading that has nothing.
- Keep source-language quotation to a few words per item (see `content_filter.md`).
- The `## Doubts` and `## Carry-forward` sections are merged automatically into
  `_source/uncertain_readings.md` and `run/carry_forward.md`, so write them as standalone
  bullets.

## 2. Status: `${RUN_DIR}/status/<PHASE>/<packet>.json`  (`<packet>` = your `<id>`)

```json
{"phase": "R2", "packet": "p05", "units": [5], "status": "done",
 "fixes": 4, "doubts": 1, "decisions": 0, "notes": "run/notes/R2/p05.md"}
```

- `status`:
  - `done`: finished everything;
  - `skipped`: nothing to do, with a `reason`;
  - `failed`: could not finish, with a `reason`;
  - `filter_blocked`: see `content_filter.md`.
- `notes` is relative to `_source/`.
- Single-agent phases use their fixed name in place of `<packet>` (e.g. `corpus`, `seams`,
  `survey`, `structure`, `configure`).
- `doubts` = the number of ledger entries you **added** (§2a); `status_check.py` warns if they
  differ.
- Phases that decide on another round add `"substantive"`: the convergence pass and the review
  rounds (`validate*`, `grade*`) count the fixes that change the meaning (their phase file
  defines it).
- Write the status file **last**. Its existence means "finished".

## 2a. Doubt ledger (every doubt, every phase)

Every reading you leave unchanged because you're unsure is a **doubt**: record it in the ledger
(`run/doubts.jsonl`) as well as in your notes, one command each; it prints the doubt id:
```
python3 "${TOOLS_DIR}/doubts.py" add --work-dir "${WORK_DIR}" --phase <PHASE> --packet <id> \
  --unit <n> --page <label> --reading "<few words as printed>" --question "<what is doubtful>"
```
Open doubts from earlier phases on your pages are `d:` items on your checklist. Look at each on
the image and settle it (one command), `--status` one of:
`confirmed-as-printed` (the text is right), `changed` (you fixed it; count it as a fix),
`escalated` (needs an editorial choice: `decisions.py add` first, pass `--decision <its id>`),
`deferred` (can't be settled on the image; say which pass should look, or what R8 should
consult: the manuscript, another edition):
```
python3 "${TOOLS_DIR}/doubts.py" update --work-dir "${WORK_DIR}" --id <doubt id> --status <status> \
  --phase <PHASE> --by <id> --reason "<one line>"
```
`doubts.py list --work-dir "${WORK_DIR}" --status open --pages 173-186` shows the open doubts on a
page range.

## 3. Decisions (only for genuine editorial choices)

If you meet a real choice the README and resolved decisions don't settle, one where reasonable
editors could differ and that affects many places:

```
python3 "${TOOLS_DIR}/decisions.py" add --work-dir "${WORK_DIR}" --phase <PHASE> --packet <packet> \
  --question "..." --option "Label::what it means" --option "Label::..." \
  --recommended "Label" --evidence "pages, counts" --affects "which units"
```

Then **continue under your recommended option**, and count it in `"decisions"`. Don't raise
decisions for things the image settles.

## 4. The return message

A single line under 20 words, e.g. `R2 p05 done: 4 fixes, 1 doubt.` Nothing else.

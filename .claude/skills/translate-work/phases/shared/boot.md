# Shared: boot (every subagent starts here)

You are a subagent of a /translate-work run. Your prompt is one line:

```
WORK_DIR="<abs path>". Follow <abs path>/phases/shared/boot.md with PHASE=<key> ASSIGNMENT=<id> [MODE=<mode>]. Final message ≤20 words.
```

Everything else you need is derived below or sits in files. You don't dispatch agents and you
don't ask the user anything (genuine editorial choices go to `decisions.py`, `status_contract.md` §3).

## 1. Variables (all absolute paths)

- `SKILL_DIR` = the path you were told to follow, minus `/phases/shared/boot.md`.
  `PHASES_DIR` = `${SKILL_DIR}/phases`, `TOOLS_DIR` = `${SKILL_DIR}/tools`,
  `TEMPLATES_DIR` = `${SKILL_DIR}/templates`.
- `WORK_DIR` = from the prompt. `SRC_DIR` = `${WORK_DIR}/_source`, `RUN_DIR` = `${SRC_DIR}/run`,
  `EN_DIR` = `${WORK_DIR}/english`.
- `LANG_DIR` = `${WORK_DIR}/<lang_dir>`, where `<lang_dir>` is the output of
  `python3 "${TOOLS_DIR}/state.py" get --work-dir "${WORK_DIR}" lang_dir` without its JSON quotes
  (e.g. `"GREEK"` → `${WORK_DIR}/GREEK`). It prints `null` before structure has run: then there is
  no `LANG_DIR` yet (survey, stage, structure).

**Path rule.** Every path is absolute. Shell variables don't survive between your Bash calls, so
write each path out in full in every command, and **always double-quote it** (work folders
contain spaces, e.g. `".../Origen of Alexandria/Homilies on the Psalms"`). Wherever a phase file
writes `${WORK_DIR}`, `${RUN_DIR}`, `${TOOLS_DIR}`, … it means these values.

**Shell rule.** Your Bash tool runs the user's login shell: zsh on macOS, bash elsewhere. Write
commands that work in both:
- never keep a command or a path in a variable and expand it unquoted (`$T/state.py`): zsh
  doesn't split it; write the command out in full;
- quote every glob or pattern you pass to a program (`--include='*.md'`, `grep -n '\[PL 375\]'`,
  `grep -c '^====='`): zsh aborts a command whose unquoted glob matches nothing, and expands an
  unquoted word starting with `=` as a command path;
- don't name a shell variable `path` or `status` (special in zsh);
- never pipe a command whose exit code you judge (`check_base`, `assemble`, `check-findings`,
  `manifest_check`, …): a pipeline's exit status is its last command's. The skill's gate tools end
  with `GATE <tool>: PASS` or `GATE <tool>: FAIL (…)`; to see any other exit code, end the
  command with `; echo "exit=$?"`.

## 2. PHASE → phase file

| PHASE | Phase file (`${PHASES_DIR}/…`) | ASSIGNMENT | Phase MODEs |
|---|---|---|---|
| `survey` | `01_survey.md` | `survey` | `user-files`, `re-search` (hint in the assignment file) |
| `stage` | `02_stage.md` | `base` or `witness` | |
| `structure` | `03_structure.md` | `assemble`, or `scout-<from>-<to>` (the page-label range) | `adopt` (with `assemble`) |
| `normalize` | `03b_normalize.md` | `normalize` | `apply-decision <id>` |
| `B` | `04_transcribe.md` | packet / sub-packet | |
| `R2` | `05_recollate.md` | packet / sub-packet | |
| `R4` | `06_boundaries.md` | packet / sub-packet, or `seams` | |
| `R1` | `07_witness.md` | packet / sub-packet | |
| `R3` | `08_oracle.md` | packet / sub-packet | |
| `R5` | `09_consistency.md` | `corpus` | `apply-decision <id>` |
| `R6` | `10_variants.md` | `docket` | |
| `R8` | `10b_doubts.md` | `doubts`, or a packet | `legacy` |
| `convergence` | `11_convergence.md` (it builds on `05_recollate.md`) | packet / sub-packet | |
| `configure` | `12_configure.md` | `configure` | `trial-review` |
| `translate` | `13_translate.md` | unit `u<NN>` or batch `u<NN>-u<MM>` | `retry`, `tiny-edit` |
| `validate`, `validate-r<k>`, `validate-g<j>`, `validate-g<j>-r<k>`, `<K>-confirm` (review rounds) | `14_validate_review.md` | packet (whole) | `confirm` (every `-confirm` key) |
| `<K>-scan` for every validate round key `<K>` (`validate-scan`, `validate-r<k>-scan`, `validate-g<j>[-r<k>]-scan`, `<K>-confirm-scan`) | `14a_validate_scan.md` | unit `u<NN>` or batch `u<NN>-u<MM>` | `retry` |
| `grade`, `grade-r<k>` (review rounds) | `15_grade_review.md` | packet (whole) | |
| `grade-scan`, `grade-r<k>-scan` | `15a_grade_scan.md` | unit `u<NN>` or batch `u<NN>-u<MM>` | `retry` |
| `report` | `16_report.md` | `report` | |
| `<P>-repair` (e.g. `R2-repair`) | `gate_repair.md` | packet (whole) | error lines in the assignment file |

An unknown PHASE, or a missing phase file: write nothing, return `boot failed: <reason>`.

## 3. Your assignment

- **Packet or sub-packet id** (`p05`, `p07a`: `p` + digits, optional letter). Resolve it:
  `python3 "${TOOLS_DIR}/packets.py" list --work-dir "${WORK_DIR}" --ids <ASSIGNMENT> --whole`
  prints exactly one line, e.g. `packet p05 = units [5] (Homily V), pages 332-358` or
  `sub-packet p07a = units [7] (Ps67 I), pages 173-186 ONLY (of packet p07; …)`. That line is your
  assignment: your units, their labels and your pages. A sub-packet line: follow
  `status_contract.md` → *Sub-packets*.
- **Unit id** (`u07`: `u` + digits; translate and every `*-scan` phase). Resolve it:
  `python3 "${TOOLS_DIR}/packets.py" list --work-dir "${WORK_DIR}" --ids <ASSIGNMENT>` prints one
  line, e.g. `unit u07 = unit 7 (Homily VII), pages 173-199, packet p03`. Your `<id>` in notes and
  status is the unit id. There is no checklist: your output file is checked instead.
- **Batch id** (`u12-u17`: two unit ids joined by `-`; translate and every `*-scan` phase): a
  short run of consecutive units, all yours. The same `packets.py list --ids <ASSIGNMENT>`
  prints a batch line, then one unit line per unit, in order. Do the lean boot (§4) **once**,
  then run your phase file's procedure for **each unit in turn**, exactly as for a single unit
  id: in the phase file, `<uid>` is the unit you are working on now. Per unit:
  1. **Skip it if it is already finished** (a batch may be a re-dispatch):
     `python3 "${TOOLS_DIR}/status_check.py" --work-dir "${WORK_DIR}" --phase <PHASE> --by-unit --units <uid>`
     printing `GATE status_check: PASS` means its status is done and its output newer than its
     bundle: go on to the next unit.
  2. Read its bundle. Bundles start with a **shared part** (work context, rules) that is the same
     for every unit of the phase; line 1 names its `sha` and the line where the unit's own part
     starts. Read your first unit's bundle whole. For each later unit, Read its bundle from that
     line (`offset`): its first lines must be `# Unit part: …` and `shared: <the same sha>`. If
     they aren't, read that bundle whole.
  3. Do the work, then its notes, then **its status, as soon as that unit is finished**, before
     you start the next one. A unit that ends `failed` or `filter_blocked`: write that status and
     **go on with the next unit**. Never stop a batch for one unit.

  Your final message covers the whole batch in one line, e.g.
  `translate u12-u17 done: 6 units, 1 warning settled, 2 doubts` or
  `validate-scan u12-u17: 5 done, 1 failed (u15)`.
- **Anything else** is a role name (see the table): no packet lookup. Your `<id>` in notes,
  status and checklist is the role name.
- **Assignment file** (optional): `${RUN_DIR}/assignments/<PHASE>/<ASSIGNMENT>.md`. If it exists,
  read it: the orchestrator's notes for this dispatch (retry reason, split note, survey hint, gate
  error lines, special instructions). It overrides the phase file where they conflict.
- **MODE** (optional): the text after `MODE=` in the prompt, up to the period, e.g. `tiny-edit` or
  `apply-decision R5-corpus-1`. It is what the phase files call `MODE: <mode>`. General meanings:
  - `tiny-edit` (any phase): the content filter blocked the previous attempt; from the start,
    work as `content_filter.md` → *If you are blocked* prescribes (seed disk→disk, tiny edits);
  - `retry` (any phase): a previous agent on this id died without a status. **In B** its checklist
    was kept: resume after the last checked page. **In other phases** the checklist was
    re-initialized: do the whole assignment, and first diff your unit(s) against
    `${RUN_DIR}/snapshots/pre-<PHASE>/` so any edit the dead agent left is verified on the image
    (count it as your fix, or revert it);
  - the phase MODEs in §2 are defined in the phase file;
  - for `translate` and `*-scan`, the phase file's own `retry` / `tiny-edit` replaces the general
    meaning above (no checklist, no snapshot diff).
- **MODE `confirm`:** inferred from a PHASE ending in `-confirm`; the prompt states it too.
- **B only:** your B-MODE is `python3 "${TOOLS_DIR}/state.py" get --work-dir "${WORK_DIR}" b_mode`
  (`null` means `full`).

## 4. Read, in this order, then do the work

**Lean boot (`translate` and every `*-scan` phase).** Read only `status_contract.md` (§2 Status,
§4 Return), `content_filter.md`, your phase file and your bundle (in a batch: your bundles, one
unit at a time, §3); add `image_reading.md` if the
bundle lists images, and `copyright.md` for a grade scan (its bundle holds the oracle). Skip
everything else below: README, carry-forward and decisions. Configure compiled them into the
rules inside your bundle, and consulting the run's other files (reports, notes, the oracle, other
units, earlier findings) would break the independence this phase exists for. Every tool stays
available, web search included; your phase file says what not to consult.

Every other phase:

1. `${PHASES_DIR}/shared/`: `conventions.md`, `image_reading.md`, `content_filter.md`,
   `copyright.md`, `status_contract.md`.
2. Your phase file (§2).
3. `${SRC_DIR}/README.md` (the project spec; it overrides defaults), if it exists.
4. The items tagged `[<PHASE>]` in `${RUN_DIR}/carry_forward.md`, if it exists:
   `grep -F "[<PHASE>]" "${RUN_DIR}/carry_forward.md"` (not the whole file).
5. Resolved decisions:
   `python3 "${TOOLS_DIR}/decisions.py" list --work-dir "${WORK_DIR}" --resolved`.

## 5. Output

Exactly as `status_contract.md` says: checklist marked as you go, notes
`${RUN_DIR}/notes/<PHASE>/<id>.md`, status `${RUN_DIR}/status/<PHASE>/<id>.json` written last,
doubts in the ledger, decisions via `decisions.py`. Then a **final message under 20 words**, e.g.
`R2 p05 done: 4 fixes, 1 doubt.` Nothing else.

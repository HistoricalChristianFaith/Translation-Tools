---
name: translate-work
description: >
  Produce a fresh, verified English translation of a patristic or medieval work (Latin, Greek,
  ...) from the page images of a public-domain edition. Interviews the user (target work, base
  text, oracle), surveys online sources, then orchestrates subagents through staging,
  seed normalization, multi-pass source-text verification (B, R2, R4, R1, R3, R5, R6, R8
  doubt resolution, convergence, R7), and
  translate / validate / grade. Resumable across sessions.
argument-hint: "[author and work, e.g. 'Origen, Homilies on Numbers'] | [path to a work folder to resume]"
---

# /translate-work: translation orchestrator

## MANDATORY FIRST ACTIONS

**Step 0: Model check.** The run is pinned to Opus 5.5: you (the orchestrator) on
`claude-opus-5-5[1m]` (the 1M context window: your context budget below assumes it), every
subagent on `claude-opus-5-5`. Check which model you're running as, and that the pin is in the
settings of the project you run in (`.claude/settings.json` next to the skill's `skills/` folder,
i.e. `${CLAUDE_SKILL_DIR}/../../settings.json`):
```json
{"model": "claude-opus-5-5[1m]",
 "env": {"ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-5-5", "CLAUDE_CODE_SUBAGENT_MODEL": "claude-opus-5-5"}}
```
If you aren't exactly `claude-opus-5-5[1m]` (plain `claude-opus-5-5` fails too: right model, too
small a context budget), or the settings are missing, stop before running any tool and tell the
user:

> ⚠️ /translate-work is pinned to Claude Opus 5.5 with the 1M context window
> (`claude-opus-5-5[1m]`), and every subagent to `claude-opus-5-5`, so a run that lasts days
> never changes model midway. [The pin settings are missing: I can add them to
> `<settings path>`.] Settings take effect in a new session: then re-run `/translate-work`. Or
> reply "continue" to proceed as is.

Wait for their reply. If they want the settings, add (merge) them, and stop.

**Step 1: Bind the skill paths.**
- `SKILL_DIR` = `${CLAUDE_SKILL_DIR}`. If that placeholder was not substituted, Glob for
  `**/translate-work/SKILL.md` and use its folder.
- `PHASES_DIR` = `${SKILL_DIR}/phases`, `TOOLS_DIR` = `${SKILL_DIR}/tools`,
  `TEMPLATES_DIR` = `${SKILL_DIR}/templates`.
- Glob `${PHASES_DIR}/*.md` and `${PHASES_DIR}/shared/*.md` (including `shared/boot.md`, every
  subagent's entry point). If any phase file referenced below is missing, **stop** and tell the user: "Phase file not found at [path]. The skill is not
  installed correctly." **Never improvise the method.**

**Step 2: Prerequisites.** Run one Bash command that checks: `python3 -c "import PIL"`,
`pdftotext -v`, `pdftoppm -v`, `pdfinfo -v`, `opj_decompress -h`, and
(optional) `tesseract --list-langs`. If something required is missing, give the exact install
command (macOS: `brew install poppler openjpeg tesseract tesseract-lang`;
`python3 -m pip install pillow`) and stop until the user confirms it's installed.

**Step 3: Interview.** Read `${PHASES_DIR}/00_interview.md` and follow it exactly. It resolves the
target work, the work folder (and whether to resume), the base text, the oracle and the plan,
and it initializes the run state. **Don't start any other phase until the interview reaches
"Plan approved".**

---

## Your role: ORCHESTRATOR

You dispatch subagents, run the deterministic tools, check gates, and talk to the user.
**You don't do the scholarly work yourself.** No reading page images, source text, translations
or reports into your own context.

**Context rules (a run takes days and many sessions; keep your context lean):**
- Learn where things stand only from `state.py show`, `status_check.py`, `check_base.py --quiet`,
  `GATE` lines,
  `decisions.py list`, `doubts.py count`, `packets.py list`, tool exit codes, and the small JSON
  files named below
  (`survey.json`, `stage_*.json`, `normalize/normalize.json`). Never `cat` a report, a notes file, or a unit file.
  The one exception: the `[orchestrator]` items `merge_notes.py` prints (`ORCHESTRATOR: n`, one
  line each, ≤200 characters). They are addressed to you; settle each (see *Orchestrator items*).
- Subagent return messages must be under 20 words. If a subagent returns more, ignore the
  extra.
- If a subagent fails, **re-dispatch it**. Don't diagnose the failure by reading its work.
- After every phase, send the user **one line** of progress, e.g.
  `✓ R2 done: 16/16 packets, 23 fixes, 4 doubts (ledger: 37 open). Next: R4.` The open count
  is `T/doubts.py count W` → `open=` (omit it if the run has no ledger).

**Context budget.** Run `T/context_check.py W` after each phase's progress line and after each
dispatch wave. It measures your own context from this session's transcript, found by the
`CLAUDE_CODE_SESSION_ID` Claude Code exports (threshold: `context_threshold_k`, default 400k;
exit 1 = can't tell, continue, and add "context check unavailable" to the progress line).
On **PAUSE** (exit 2): start nothing new. Reach the next safe stopping point: every dispatched agent returned,
status_check / merge / gate done, state updated, auto-commit done. Then send the user
one message: the estimate, where the run stands (`T/state.py show W` → next phase), and exactly:
run `/clear`, then `/translate-work "<WORK_DIR>"`. **Stop.** The new session resumes from
`state.json` (*Resuming*), open decisions first.

## Variables (yours; subagents derive the same ones from `WORK_DIR` via `shared/boot.md`)

| Name | Value |
|---|---|
| `WORK_DIR` | the work folder, e.g. `.../Writings-Database-Non-English/Origen of Alexandria/Homilies on Numbers` |
| `SRC_DIR` | `${WORK_DIR}/_source` (git-ignored workspace) |
| `RUN_DIR` | `${SRC_DIR}/run` (state, manifest, packets, status, notes, decisions, logs, crops) |
| `LANG_DIR` | `${WORK_DIR}/<LATIN|GREEK|…>` (from `state.json` `lang_dir`, set at structure) |
| `EN_DIR` | `${WORK_DIR}/english` |
| `PHASES_DIR`, `TOOLS_DIR`, `TEMPLATES_DIR` | from Step 1 |

In the commands below, `T/x.py` = `python3 "<TOOLS_DIR>/x.py"` and `W` = `--work-dir "<WORK_DIR>"`,
written out in full in every command (see *Shell*); `…` right after `translate.py`, `validate.py`
or `grade.py` stands for `--config "<RUN_DIR>/work_config.py"`.

## Shell

Your Bash tool runs the user's login shell: **zsh** on macOS, bash elsewhere. Write every command
so it works in both:
- **Never put a command or a path in a variable and expand it unquoted** (`T="python3 …/tools";
  $T/state.py`): zsh doesn't word-split it, so the command is "not found". Write
  `python3 "<TOOLS_DIR>/state.py" … --work-dir "<WORK_DIR>"` in full, double-quoted, in every
  command. `T/` and `W` in this file are notation for exactly that.
- **Quote every glob or pattern you pass to a program**: `--include='*.py'`,
  `grep -n '\[PL 375\]'`, `grep -c '^====='`. zsh aborts a command whose unquoted glob matches
  nothing, and expands an unquoted word starting with `=` (`=====`) as a command path.
- Don't name a shell variable `path`, `status` or `pipestatus`: in zsh `path` rewrites `PATH` and
  `status` is read-only.
- **Never pipe a gate command** (no `| tail`, `| head`, `| grep`; no `PIPESTATUS`, which zsh
  doesn't have): a pipeline's exit status is its last command's, so the gate can't fail. Every
  gate tool (`status_check`, `check_base`, `manifest_check`, `normalize_check`, `packets.py join`,
  `strip_anchors`, `translate.py --check`, `validate.py --structure-only`) ends with **one line**,
  `GATE <tool>: PASS` or `GATE <tool>: FAIL (<n> problem(s))`, and exits 0 or 1 to match; where
  its output is long, use its `--quiet` / `--summary` flag. **A gate passes only if its last line
  is `GATE <tool>: PASS`.** No GATE line (a crash, a usage error) is a failure. To see another
  command's exit code, end it with `; echo "exit=$?"`.

## Subagent prompt template

Launch every subagent with the Agent tool, `subagent_type: general-purpose`, `model: "opus"`
(always explicit: never let an agent inherit a non-Opus default; the pin in Step 0 makes `opus`
resolve to `claude-opus-5-5`), and **exactly this one line** (the agent reads everything else from files):

```
WORK_DIR="<abs WORK_DIR>". Follow <abs SKILL_DIR>/phases/shared/boot.md with PHASE=<key> ASSIGNMENT=<id> [MODE=<mode>]. Final message ≤20 words.
```

- `<key>` = the phase's state key (`survey`, `stage`, `structure`, `normalize`, `B`, `R2`, …,
  `configure`, `translate`, `report`), a review round key (`validate`, `validate-r2`, `grade`, …),
  a round's scan key `<K>-scan`, or `<P>-repair` for gate repair.
- `<id>` = a dispatch id (packet `p05`, sub-packet `p07a`, or, for `translate` and `<K>-scan`,
  a unit batch `u12-u17` or a single unit `u07`: `T/packets.py batches W --units <list>`) or a
  role name (`survey`, `base`,
  `witness`, `assemble`, `scout-<from>-<to>`, `normalize`, `seams`, `corpus`, `docket`, `doubts`,
  `configure`, `report`). `boot.md` derives every path, the phase file, the units/pages (via
  `packets.py list`), the reading order and the output rules.
- `MODE` only when the procedure below names one (`tiny-edit`, `retry`, `adopt`, `user-files`,
  `re-search`, `legacy`, `apply-decision <id>`, `trial-review`, `confirm`).
- **Never paste instructions, paths, pages, titles or reading lists into a prompt.** Anything
  extra for one dispatch (retry reason, split note, survey hint, gate error lines, special
  instructions) goes into `${RUN_DIR}/assignments/<PHASE>/<id>.md`, a few lines written with a
  heredoc (`mkdir -p` first); `boot.md` tells the agent to read it. At the start of each phase,
  `rm -rf "${RUN_DIR}/assignments/<PHASE>"` so no stale note reaches a fresh agent.

**Sub-packets.** A unit is never split across packets, so long units make long packets, and
agents reading 20+ pages die on rate limits or the stall watchdog. `packets.py split` (run at
structure) gives every packet over 12 pages page-range sub-packets (`p07a`, `p07b`, …) in
`packets.json`. In the page-reading phases (B, R2, R4, R1, R3, convergence) dispatch one agent
per sub-packet: `T/packets.py ids W` lists the dispatch ids (subs replace their packet). Siblings
edit the same unit file with small in-place edits, each only on its own pages. `status_check.py`
counts a packet complete only when all its subs are, sums their counts, and lists sub ids to
redispatch; `merge_notes.py` merges sub notes under their packet. Review phases (validate, grade)
work per unit: pass `--whole` to `packets.py`, `checklist.py init` and `status_check.py`.
**Per-unit phases** (`translate` and every `<K>-scan`) work per unit (bundle, output, notes and
status per unit; `status_check.py --by-unit`; no checklists: a `done` unit needs its output file
instead) but dispatch **batches**: one agent per short run of consecutive units, worked one at a
time. `T/packets.py batches W --units <unit ids>` turns a unit list into batch ids (`u012-u017`;
a lone unit stays `u007`), capped by `state.json` `batch_units` (default 6) and `batch_chars`
(source bytes, default 30000); `T/state.py set W batch_units=1` restores one agent per unit.
Each agent counts as one in the waves of 6 and in `state.py agents`.

**Per-unit retry rules** (instead of the packet rules in step 3 below):
- `status_check --by-unit` lists unit ids after `REDISPATCH:`. Re-batch them with
  `T/packets.py batches W --units <those ids> --isolate-first` and dispatch the result with
  `MODE=retry` (a batch agent skips any unit already finished, so the mode is harmless for the
  others). `--isolate-first` sends the first unit of every run alone: when a batch agent dies,
  that unit is the likeliest cause, and alone it can't take the rest of a batch down with it.
- A `filter_blocked` unit: alone (its unit id) with `MODE=tiny-edit`.
- At most 2 retries per unit, the second always alone. Then stop and ask the user (show the
  one-line reasons). Count a unit's retries yourself, as for packets.

## Standard per-packet phase procedure (B, R2, R4, R1, R3, R8, convergence, reviews)

1. `T/state.py phase W <PHASE> in_progress`, and for source-text phases
   `T/state.py snapshot W pre-<PHASE>`. Clear `${RUN_DIR}/assignments/<PHASE>/`.
   **Checklists:** `T/checklist.py init W --phase <PHASE> [--doubts]`: one checklist per
   dispatch id listing every page (an enumerated inventory). Add `--doubts` in every
   phase that reads the images (B, R2, R4, R1, R3, convergence), so each open ledger doubt
   on those pages gets settled; validate/grade use `--whole --by unit`. For B:
   `T/packets.py placeholders W` first (one placeholder line per sub-packet in split units; a
   no-op on units the normalize phase seeded). (B agents read their B mode from `state.json`
   `b_mode` via `boot.md`; don't put it in the prompt.)
2. **Dispatch in true waves of at most 6 agents**, one per dispatch id, each with the one-line
   prompt (`PHASE=<PHASE> ASSIGNMENT=<id>`). Send up to 6 Agent calls in one message, wait for
   all of them, then send the next wave. (More concurrent agents caused
   rate-limit failures in practice.) Record each wave with `T/state.py agents W --add <n>`.
3. `T/status_check.py W --phase <PHASE>` must print `GATE status_check: PASS`. It also fails a
   `done` packet whose checklist is missing or has unchecked items. For each id listed in `REDISPATCH:`, re-init its checklist
   (`T/checklist.py init W --phase <PHASE> --ids <ids> [--doubts]`) and send a new agent
   (maximum 2 retries per packet), with `MODE=retry` and, if useful, the one-line reason in its
   assignment file. A `filter_blocked` packet is re-dispatched with `MODE=tiny-edit`.
   **Retry rule for long work:** if an agent died (rate limit, stall, error return, no status)
   on a packet, re-dispatch it as sub-packets:
   `T/packets.py split W --packet <pid> --parts 2` (a failing sub-packet: re-split its parent with
   more parts, e.g. `--parts 4`, and re-dispatch **all** its subs), then `checklist.py init --ids
   <pid>` and dispatch the ids from `T/packets.py ids W --ids <pid>` (their pages come from
   `packets.json`; no prompt change). **In B**, never re-split
   once a packet's agents have started and don't re-init its checklists: re-dispatch the same id;
   the new agent resumes after the last checked page. After 2 failed retries, stop and ask the
   user (show the one-line reasons). **A missing status or checklist is unknown coverage, never
   "no findings".**
4. `T/merge_notes.py W --phase <PHASE> --report <REPORT> --title "<title>"`. After B, also
   `T/packets.py join W` (must print `GATE join: PASS`: it joins the `[[JOIN]]` seams between
   sub-packets). If `merge_notes` prints `ORCHESTRATOR: n` with n > 0, settle every item before
   marking the phase done (*Orchestrator items*).
5. **Gate:** `T/check_base.py W --quiet` must print `GATE check_base: PASS` (source-text phases).
   If it fails, dispatch **gate repair** (whole packets): one agent per affected packet with
   `PHASE=<PHASE>-repair ASSIGNMENT=<pid>`, after writing that packet's exact error lines to
   `${RUN_DIR}/assignments/<PHASE>-repair/<pid>.md`. After each repair round, wait for its agents,
   then `T/status_check.py W --phase <PHASE>-repair --whole --packets <them>`, and
   `T/merge_notes.py W --phase <PHASE>-repair --report run/<PHASE>_repair_notes.md --title "<PHASE> gate repair"`
   (settle its `ORCHESTRATOR` items too), and re-run the gate. Maximum 2 rounds, then ask the
   user. An `incipit/explicit not found` line goes to gate repair like any other: the agent
   settles it on the image (the field mirrors the unit file; `manifest_edit.py` syncs it).
6. `T/state.py phase W <PHASE> done`. Handle decisions (see *Decisions & checkpoints*). Send the
   progress line.

**Dispatch checklist (mandatory before marking a phase done):**
- [ ] every checklist initialized before its agent was dispatched (per-packet phases; per-unit
  phases have none);
- [ ] every packet, sub-packet (or role) dispatched;
- [ ] `status_check.py` prints `GATE status_check: PASS`;
- [ ] notes merged, and every `ORCHESTRATOR` item they printed settled and acked;
- [ ] gate clean.

Any unchecked box means the phase is not done.

## The phases

| # | Phase (state key) | Phase file | Dispatch | Report (`_source/…`) | Gate |
|---|---|---|---|---|---|
| 0 | `survey` | `00_interview.md` → `01_survey.md` | interview + 1 survey agent (`--expect survey`) | `run/survey_notes.md` | `survey.json` exists; plan approved |
| 1 | `stage` | `02_stage.md` | role `base` (+ role `witness` in parallel, if a witness was chosen) (`--expect base [--expect witness]`) | `run/stage_notes.md` (the agent writes `pass0_report.md` itself) | statuses done; `run/stage_base.json` exists |
| 2 | `structure` | `03_structure.md` | role `assemble` alone (`--expect assemble`), or first `scout-<from>-<to>` agents on ~40-page ranges (`--expect scout-<from>-<to>` each), then `assemble` | `run/structure_notes.md` (the agent writes `boundary_audit.md` itself) | `T/manifest_check.py W` → `GATE manifest_check: PASS` |
| 2b | `normalize` | `03b_normalize.md` | one agent, role `normalize` (skip if `stage_base.json` → `ocr` isn't `usable-draft`) | `run/normalize_notes.md` | see below |
| 3 | `B` | `04_transcribe.md` | per packet | `passB_report.md` | standard |
| 4 | `R2` | `05_recollate.md` | per packet, **fresh agents** | `recollation_pass.md` | standard |
| 5 | `R4` | `06_boundaries.md` | per packet, then **one** `seams` agent in a final wave | `r4_boundary_audit.md` | standard, with `--with-packets --expect seams` (one call checks every packet **and** the seams role; `--expect` alone checks only the role) |
| 6 | `R1` | `07_witness.md` | per packet (skip the phase if no witness) | `variants_witness.md` | standard |
| 7 | `R3` | `08_oracle.md` | per packet (skip the phase if no oracle) | `oracle_discrepancies.md` | standard |
| 8 | `R5` | `09_consistency.md` | one agent, role `corpus` | `consistency_pass.md` | standard (`--expect corpus`) |
| 9 | `R6` | `10_variants.md` | one agent, role `docket`, after `T/checklist.py init W --phase R6 --role docket --by none --all-open-doubts` | `apparatus_pass.md` | standard (`--expect docket --require-checklist`) |
| 9b | `R8` | `10b_doubts.md` | role `doubts` or per packet (see below) | `doubt_resolution.md` | standard (`--require-checklist`) |
| 10 | `convergence` | `11_convergence.md` | per packet (see the convergence rule) | `convergence_pass.md` | `--sum substantive` == 0 |
| 11 | `R7` | *(orchestrator)* | none | `anchor_strip.md` | see below |
| 12 | `configure` | `12_configure.md` | one agent, role `configure` (`--expect configure`), then the trial (see *Configure*) | `run/configure_notes.md` | status done; trial done; `translate.py --check` OK |
| 13 | `translate` | `13_translate.md` | per unit, dispatched in batches (`u012-u017`, `--by-unit`) | `run/translate_notes.md` | one English file per unit; structure: no `ERROR` |
| 14 | `validate` | `14a_validate_scan.md`, `14_validate_review.md` | 2–5 review rounds: per-unit scans (in batches), `apply`, per-packet reviewers (+ a confirm round) | `validation_review*.md` | every round's reviewers done; structure: no `ERROR` |
| 15 | `grade` | `15a_grade_scan.md`, `15_grade_review.md` | 1–3 review rounds (per-unit scans in batches, per-packet reviewers), each followed by a `validate-g` recheck loop (skip if no oracle) | `grading_review*.md`, `validation_review_g*.md` | every round's reviewers done; structure: no `ERROR` |
| 16 | `report` | `16_report.md` | one agent, role `report` (`--expect report`) | `run/report_notes.md` (the agent writes `run/FINAL_REPORT.md`) | file exists |

The **Report** column is the `--report` argument for `merge_notes.py`, relative to `_source/`.
Every merge, in every phase and review round, may print `ORCHESTRATOR: n item(s)`: settle and ack
them before the phase or round is done (*Orchestrator items*).
Single-agent phases pass their role names to `status_check.py` with `--expect`, as shown.
**Older runs** (no `checklists_from` in `state.json`) keep passing without checklists; checklists
present are still verified. To adopt them mid-run: `T/state.py set W checklists_from=<next phase>`.
Phases added to the skill later (`normalize`, `R8`) count as `skipped` in a run that had already
reached a later phase (`state.py` notes it), else as pending.
Skipping a phase: `T/state.py phase W R1 skipped --note "no witness chosen"`.

**Why this order:** normalize comes before B so B starts from mechanically clean text and its own
changes stay auditable (pre-B snapshot = the normalized seed). R2 comes right after B, while the
text is still a pure transcription, so every difference from the image is a real slip. R4 then
settles boundaries before any witness is brought in. The witness (R1) and the oracle (R3) are
detectors adjudicated on the image. R5 and R6 make editorial passes over the whole corpus. R8
settles the doubts left over against every other source, before convergence so that its edits
are re-read. Convergence proves stability. R7 strips anchors last.

### Normalize (phase 2b)

1. `T/state.py phase W normalize in_progress`. Skip it (`skipped --note "no text layer"`) if
   `stage_base.json` → `ocr` isn't `usable-draft`, and set `T/state.py set W b_mode=full`.
2. Dispatch one agent (`PHASE=normalize ASSIGNMENT=normalize`); `T/status_check.py W --phase normalize --expect normalize`.
3. `T/merge_notes.py W --phase normalize --report run/normalize_notes.md --title "Normalize"`.
   **Gate:** `T/normalize_check.py W` must print `GATE normalize_check: PASS` (it runs the run's
   `normalize.py` dry run, which must report `changes: 0`, and `manifest_check`). (No
   `check_base` gate yet: B completes the text.)
4. Decisions as usual. If a resolution changes a scripted category, re-dispatch the agent with
   `MODE=apply-decision <id>` (it edits the script and re-runs it) before B.
5. `T/state.py set W b_mode=<normalize.json b_mode>` (tell the user in the progress line if it
   differs from the plan), `T/state.py phase W normalize done`. B's `pre-B` snapshot now holds
   the normalized seed, so `diff -r snapshots/pre-B snapshots/pre-R2` is exactly B's work.

### R8: doubt resolution (phase 9b)

`T/state.py snapshot W pre-R8`. Count what's left: `T/doubts.py count W` → `open` + `deferred`.
- **≤ 25 (or no ledger):** one agent, role `doubts`:
  `T/checklist.py init W --phase R8 --role doubts --by none --all-open-doubts --include-deferred`;
  gate `T/status_check.py W --phase R8 --expect doubts --require-checklist`. With no ledger
  (older run) add `MODE=legacy` (the agent enters `uncertain_readings.md` into the ledger).
- **More:** per packet: `T/checklist.py init W --phase R8 --whole --by none --doubts --include-deferred`;
  dispatch only the ids after `nonempty:` (`PHASE=R8 ASSIGNMENT=<pid>`); gate
  `T/status_check.py W --phase R8 --whole --packets <them> --require-checklist`.
- **Zero:** `T/state.py phase W R8 skipped --note "no open doubts"`.
Then merge notes (report `doubt_resolution.md`), `check_base` gate, decisions, done.

### Convergence rule (phase 10)

- **Round 1:** dispatch all packets if there are ≤ 20. Otherwise dispatch every packet touched by
  R5, R6 or R8 (`T/state.py changed W --since pre-R5`, which includes R8's edits; if R5 was
  skipped, add `--since pre-R8`), plus a random third of the others (pick them
  with a one-line Python snippet). Record the chosen list with
  `T/state.py set W convergence_packets=<comma list>` (packet ids; `status_check.py` defaults
  to it). Dispatch `T/packets.py ids W --ids <the list>` (split packets expand to their subs).
- **Gate:** `T/status_check.py W --phase convergence --packets <the list> --sum substantive --nonzero substantive`.
  `substantive=0` → converged.
- **Otherwise:** re-dispatch only the ids printed after `NONZERO substantive:` (packet or
  sub-packet ids; re-init their checklists), under the same phase key with fresh agents (their
  status files are overwritten). Check again with `--packets`
  set to those ids. Maximum 2 extra rounds. If still not converged, tell the user and mark
  `convergence` done with `--note "not converged: <packets>"`. The final report lists them.

### R7: anchor strip (orchestrator)

```
T/state.py snapshot W pre-R7
T/strip_anchors.py --pattern "$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["anchor"]["regex"])' "${RUN_DIR}/manifest.json")" "${LANG_DIR}" > "${SRC_DIR}/anchor_strip.md"; echo "exit=$?"
T/check_base.py W --quiet
```
The manifest's `anchor.regex` matches **only** the anchor form, never other brackets. The tool
refuses to write any file that fails its deletion-only checks. The strip must print `exit=0`
(its `GATE strip_anchors` line is the last line of `anchor_strip.md`), and `check_base` must
print `GATE check_base: PASS`. If either fails, stop and ask the user. Then mark `R7` done.

### Configure (phase 12)

`T/state.py phase W configure in_progress`, then dispatch `PHASE=configure ASSIGNMENT=configure`
(`--expect configure`). The agent writes `work_config.py` and picks the trial unit; it doesn't
translate. **The trial** is yours: a translate agent translates the trial unit from the rules
alone, and the configure agent reviews the result.
1. `n` = `trial_unit` from `${RUN_DIR}/status/configure/configure.json`
   (`python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["trial_unit"])' "${RUN_DIR}/status/configure/configure.json"`),
   `uid` = `T/packets.py uids W --units <n>`. `T/state.py set W trial_unit=<n> configure_trial=1`.
2. Translate it: `T/translate.py --config "${RUN_DIR}/work_config.py" prep --units <n> [--images]`
   (`--force` from the second iteration on; `--images` if `state.json` `translate_images` is
   true), dispatch `PHASE=translate ASSIGNMENT=<uid>` (a single unit, not a batch), then
   `T/status_check.py W --phase translate --by-unit --units <n>` must print
   `GATE status_check: PASS` (per-unit retry rules).
3. Review it: `T/state.py set W configure_trial=<i>-review`,
   `rm -f "${RUN_DIR}/status/configure/trial-review.json"`, dispatch
   `PHASE=configure ASSIGNMENT=configure MODE=trial-review`, then
   `T/status_check.py W --phase configure --expect trial-review`.
4. `rules_changed` in `trial-review.json` true: at iteration 1, `T/state.py set W configure_trial=2`
   and repeat steps 2–3 with `--force`. At iteration 2 (the last), the trial English predates the
   final rules: `T/translate.py --config … prep --force --units <n>` once more, so the translate
   phase translates that unit afresh, and note it. `rules_changed` false: the trial English stays,
   and the translate phase skips that unit.
5. Gate: `T/translate.py --config "${RUN_DIR}/work_config.py" --check --summary` must print
   `GATE translate: PASS`.
   `T/state.py set W configure_trial=done`, `T/merge_notes.py W --phase configure --report run/configure_notes.md --title "Configure"`,
   mark `configure` done.

### Translate (phase 13)

Per-unit work in batches (*Per-unit phases* above): each unit has its own bundle, and the tools
stand on both sides (`translate.py prep` writes the bundles, the agent runs `translate.py
assemble`, which checks its output and writes the English file).
1. `T/state.py phase W translate in_progress`. Clear `${RUN_DIR}/assignments/translate/`.
2. `T/translate.py --config "${RUN_DIR}/work_config.py" prep [--images]` (`--images` if
   `state.json` `translate_images` is true). It prints `bundled:` (dispatch these), `existing:`
   (already translated: they get a `skipped` status, or keep their `done` one) and, on a resumed
   run, `unfinished:` (English assembled but no status).
3. `T/packets.py batches W --units <the bundled ids>`, then dispatch
   `PHASE=translate ASSIGNMENT=<batch id>` for every id it prints, in waves of 6. On a resumed
   run, batch the bundled, `unfinished:` and `REDISPATCH:` ids together (`--isolate-first`) and
   dispatch them all with `MODE=retry`.
4. `T/status_check.py W --phase translate --by-unit` must print `GATE status_check: PASS`; if
   not, the per-unit retry rules. It needs no checklist: a `done` unit needs its English file,
   newer than its bundle. A `MODEL WARN` line: stop and tell the user (a re-dispatch would run on
   the same wrong model).
5. `T/merge_notes.py W --phase translate --report run/translate_notes.md --title "Translate"`.
6. **Gate.** `T/validate.py --config "${RUN_DIR}/work_config.py" --structure-only --summary` must
   print `GATE validate: PASS` (no `ERROR` line; a unit without English is an `ERROR`, so this
   also proves one English file per unit):
     - a missing English file is a failed agent: back to step 4 for it;
     - any other `ERROR` (`BLOCK COUNT`) can't happen after a clean `assemble`. If one appears,
       re-translate that unit once (`prep --force --units <n>`, allowed because `translate` isn't
       done yet, then dispatch it alone). If it's still flagged, record it and continue;
     - `WARN` lines never block the gate and are **not** re-dispatched: the agent checked each
       against the source and settled it (`SETTLED`), and the validate scan and reviewers see any
       left open. Name the units in the progress line (`structure: 0 errors; 3 settled, 1 open (u12)`,
       from the `open warnings in:` line).
7. `T/state.py phase W translate done`, progress line, auto-commit, context check.

### Review rounds (validate and grade)

The English is checked in **rounds**, repeated until a round stops finding substantive fixes: a
fix that changes what the English says (the phase files define it; wording, punctuation and
style are trivial). Each round has its own key `<K>`, used as the PHASE for its reviewers'
statuses, notes, checklists and snapshot, and as `<K>-scan` for its per-unit scans:
`validate`, `validate-r2` … `validate-r5`; `grade`, `grade-r2`, `grade-r3`; `validate-g<j>`,
`validate-g<j>-r2`, `validate-g<j>-r3` (the recheck loop after grading round `j`); and
`<K>-confirm` (a confirm round, below). Back-and-forth between rounds is allowed: a later round
may undo an earlier round's fix; the report lists those passages.

**One round** `<K>` over packets `<P>` (a comma list of packet ids, or `all`; drop `--ids <P>`
and `--packets <P>` when it is `all`). `T/<tool>` is `T/validate.py` for `validate*` keys and
`T/grade.py` for `grade*` keys, always with `--config "${RUN_DIR}/work_config.py"`:
1. `T/state.py snapshot W pre-<K> --dir english --keep` (`--keep`: a snapshot taken earlier in
   this round stays, so the baseline never moves past fixes the reviewers haven't seen).
2. `T/state.py set W review_round=<K> review_packets=<P> review_step=scan`. Clear
   `${RUN_DIR}/assignments/<K>/` and `${RUN_DIR}/assignments/<K>-scan/`.
3. `T/<tool> bundle --phase <K> --units "$(T/packets.py units W --ids <P>)"`. It prints `bundled:`
   (unit ids) and `unvalidated:` (validate: English or source missing) or `ungraded:` (grade: no
   oracle extract). **Never re-translate inside a review round.** An `unvalidated` unit is a
   broken run (the translate gate guarantees one English file per unit), not something a round
   fixes: record it (`T/state.py set W review_unvalidated.<K>=<ids>`), name it in the progress
   line, continue with the rest and tell the user. The repair is a deliberate, separate step
   the user agrees to: `T/translate.py … prep --force --after-review --units <n>` (it moves the
   old English to `run/translate/replaced/`), a translate dispatch, then a fresh round for that
   unit.
4. `T/packets.py batches W --units <bundled ids>`, then dispatch `PHASE=<K>-scan
   ASSIGNMENT=<batch id>` for every id it prints, in waves of 6. Then
   `T/status_check.py W --phase <K>-scan --by-unit --units <bundled ids>` must print
   `GATE status_check: PASS`; if not, the per-unit retry rules. A `MODEL WARN` line: stop and
   tell the user. (A changed-set round has few, scattered units, so its batches are small.)
5. `T/state.py set W review_step=apply`. Validate rounds only, and never a confirm round:
   `mkdir -p "${RUN_DIR}/logs/apply"`, then
   `T/validate.py … apply --phase <K> > "${RUN_DIR}/logs/apply/<K>.log"` must exit 0 (it applies
   to the bundled units, with a journal: re-running it never applies twice). A unit line `no
   findings file` = its scan never finished: back to step 4 for it. `REFUSED` = its English
   changed after its scan: `T/validate.py … bundle --phase <K> --units <n>`, re-scan it (step 4),
   re-run apply. Then, for every round:
   `T/<tool> summary --phase <K> > "${RUN_DIR}/logs/<K>.log"`.
6. `T/state.py set W review_step=review`. `T/checklist.py init W --phase <K> --whole --by unit --ids <P>`,
   then one reviewer per packet (`PHASE=<K> ASSIGNMENT=<pid>`; add `MODE=confirm` for a
   `-confirm` key) in waves of 6, with the standard retry rules (`--whole`, no `check_base` gate).
7. `T/status_check.py W --phase <K> --whole --packets <P> --sum substantive --nonzero substantive`
   must exit 0. The ids after `NONZERO substantive:` are the round's **changed set** (empty if
   the line is absent or `substantive=0`).
8. `T/merge_notes.py W --phase <K> --report <report> --title "<title>"`. Report names:
   `validation_review.md` for `validate`, `validation_review_<rest>.md` for `validate-<rest>`
   with `-` → `_` (`validation_review_r2.md`, `validation_review_g1_r2.md`,
   `validation_review_r5_confirm.md`); `grading_review.md`, `grading_review_<r2|r3>.md`.
   `T/validate.py … --structure-only --summary` must print `GATE validate: PASS` (no `ERROR`);
   the progress line names
   the units with open warnings.
9. `T/state.py set W review_step=done`. Decisions (as at the end of a phase), auto-commit (message
   `<work>: <K>`), the context check, and one progress line, e.g.
   `✓ validate-r2: 29 packets, 12 fixes, 4 substantive (p03,p08,p11). Next: validate-r3 on those.`

**Re-running and resuming a round.** Re-running a round key from step 1 is safe: `--keep` keeps
the snapshot taken before anything was applied, and `bundle` deletes every earlier file of the
units it bundles. Resuming continues where `review_step` says:
- `scan`: run step 1 again (harmless), then step 4's `status_check` and dispatch only the
  `REDISPATCH:` ids, re-batched with `--isolate-first` and `MODE=retry`. Don't re-run `bundle` for the whole round (it would discard finished scans);
  a unit with no bundle file gets `bundle --phase <K> --units <n>` alone.
- `apply`: re-run step 5; the journal makes it safe.
- `review`: step 6's `status_check`, dispatch only the `REDISPATCH:` ids, then steps 7–9.
- `done`: the round is finished; go on to the next one.

**Confirm round** `<K>-confirm`: a normal round on the changed set of `<K>`, except that step 5
runs only `summary` (no `apply`: the scans' fixes are suggestions), its reviewers run with
`MODE=confirm` (they settle every finding by hand and apply the good fixes themselves), and it
**never triggers another round**: its changed set is recorded as `not settled after confirm:
<ids>` in the phase note, and the report lists those passages for a human look.

### Validate (phase 14): 2 to 5 rounds against our source

`T/state.py phase W validate in_progress`, then:
- round 1 `validate` on `all`, then round 2 `validate-r2` on `all` (always: at least two full
  rounds);
- round `k` = 3, 4, 5: `validate-r<k>` on the changed set of round `k-1`. Stop as soon as a
  round's changed set is empty.

If round 5 still has a changed set, run the confirm round `validate-r5-confirm` on it, and mark
the phase done with `--note "not settled after confirm: <its changed set, or none>"`. Otherwise
`T/state.py phase W validate done --note "<n> rounds"`.

### Grade (phase 15): 1 to 3 rounds against the oracle (skip if no oracle)

`T/state.py phase W grade in_progress`, then for `j` = 1, 2, 3:
- grading round `grade` (`j` = 1, on `all`) or `grade-r<j>` (on the changed set of `grade-r<j-1>`
  / `grade`);
- if its changed set `S` is empty: stop;
- otherwise the **recheck loop**: `validate-g<j>` on `S`, then `validate-g<j>-r2` and
  `validate-g<j>-r3`, each on the changed set of the round before it; stop the loop as soon as a
  round's changed set is empty. If `validate-g<j>-r3` still has a changed set, run its confirm
  round `validate-g<j>-r3-confirm` and record what it leaves. Our source has the last word on
  every fix grading made.
- Then continue with `j+1` (on grading round `j`'s changed set, as above).

If `grade-r3` still has a changed set (after its recheck loop), mark the phase done with
`--note "not settled after 3 rounds: <ids>"`; otherwise `--note "<n> rounds"`. Add every
`not settled after confirm: <ids>` from the loops to the note.

### Report

First `T/merge_notes.py W --pending`, and settle what it lists (the report lists whatever stays
un-acked). Then dispatch `PHASE=report ASSIGNMENT=report`. Then read **only** the `## Summary` section at the top
of `${RUN_DIR}/FINAL_REPORT.md` (up to its first `---`), show it to the user with the path of
the English files, and mark `report` done.

## Decisions & checkpoints

Subagents queue editorial choices with `decisions.py`. At the **end of every phase**:

1. `T/decisions.py count W`. If `open=0`, continue.
2. **Autonomy `autonomous`:** `T/decisions.py resolve-recommended W`, and mention the count in the
   progress line.
3. **`checkpoints` or `guided`:** `T/decisions.py list W --open --json --limit 4` → one
   `AskUserQuestion` call with up to 4 questions:
   - header = a short tag;
   - option labels = the decision's options, recommended first, with " (Recommended)" appended;
   - description = the option description, plus the evidence on the recommended option.

   Resolve each answer with `T/decisions.py resolve W --id <id> --choice "<label>"`. Repeat
   until `open=0`.
4. Doubts escalated to a decision (`doubts.py`, status `escalated`) arrive here as ordinary
   decisions; nothing extra to do.
5. If a resolution changes text already written (e.g. "normalize J→I" decided after B), **R5
   applies it corpus-wide** (before B: the normalize script, see *Normalize*). If R5 has already
   run, dispatch one extra agent: `PHASE=R5 ASSIGNMENT=corpus MODE=apply-decision <id>`.

**Extra pauses in `guided` mode** (one `AskUserQuestion` each, [Continue (Recommended) / Pause
here]; tell the user which file to look at):
- after `stage` (boundary pages: `pass0_report.md`);
- after `R6` (the emendation list in `apparatus_pass.md`);
- after `configure` (trial translation `english/…` + `run/work_config.py`);
- before `report` (the English diff against `run/snapshots/pre-validate/`).

### Orchestrator items

Agents report what only you can act on as Carry-forward bullets tagged `[orchestrator]` (a manifest
`label` / `passage` / `pages` to correct, a check setting to change, a caveat to add to the rules,
a note for the user). `merge_notes.py` prints the un-acked ones of the phase it merges
(`ORCHESTRATOR: n item(s)`, then `<id>: <first line>`); `T/merge_notes.py W --pending` lists them
for every phase. Settle each item one of these ways:
- **routed:** an assignment note (`${RUN_DIR}/assignments/<PHASE>/<id>.md`) for the agent of a
  later phase, or a re-dispatch;
- **decision:** `T/decisions.py add W …`, handled with the other decisions;
- **user:** tell or ask the user (in `autonomous` mode, mention it in the progress line);
- **none:** no action needed, with the reason (e.g. already synced by `manifest_edit.py`; a
  plain FYI).

Then record it: `T/merge_notes.py W --ack <id>[,<id>…] --how routed|decision|user|none --ref "<one line>"`.
A fresh agent that rewrites its note and reports the same item again re-opens it (the problem
is still there). `incipit` / `explicit` are never orchestrator items: agents sync them themselves
with `manifest_edit.py`, and the `check_base` gate catches a forgotten one.

## Resuming

The interview detects `${RUN_DIR}/state.json` and offers to resume. On resume:
1. `T/state.py show W`, then `T/state.py next W` gives the phase to run.
2. Handle any open decisions first, then `T/merge_notes.py W --pending` and settle what it lists
   (*Orchestrator items*).
3. For a per-packet phase that was `in_progress`, run `status_check.py` first and dispatch only
   the `REDISPATCH:` ids (re-init only their checklists, except in B).
4. `configure` `in_progress`: `T/state.py get W configure_trial` says where the trial stands
   (`null`: the configure agent's own step; `<i>`: step 2 of iteration `i`; `<i>-review`: step 3;
   `done`: the gate). `translate` `in_progress`: run *Translate* again from step 2 (`prep` skips
   translated units and lists `unfinished:` ones), dispatching only the bundled, unfinished and
   `REDISPATCH:` ids, batched together with `MODE=retry` (*Translate* step 3).
5. `validate` / `grade` `in_progress`: `T/state.py get W review_round`, `review_packets` and
   `review_step` give the round in progress and where it stands; continue it as *Review rounds*
   → *Re-running and resuming a round* says. The earlier rounds' changed sets can be re-derived
   with `status_check.py … --nonzero substantive` on their keys.
6. **Runs started before the subagent migration.** A background `translate.py` / `validate.py`
   / `grade.py` script of the old kind may still be running: `pgrep -f "translate.py|validate.py|grade.py"`.
   If one is, wait for it once. Then: translate continues as in 4 (old English counts as
   translated); a review round with no `review_step` whose `${RUN_DIR}/logs/<K>/` holds old
   transcripts is **restarted** from step 1 with the new flow (`--keep` keeps its old `pre-<K>`
   snapshot, so its reviewers still see the old script's auto-fixes in their diff).

Every phase is idempotent: re-running a phase overwrites its own statuses, notes and report.

## Git (only if `WORK_DIR` is inside a git repository)

- `_source/` must be git-ignored. It holds copyright oracles and large scans. The interview
  arranges this.
- If the user opted into `auto_commit` (`T/state.py get W auto_commit` → `true`), after each
  gated phase run:
  `git -C "${WORK_DIR}" add "<LANG_DIR>" english && git -C "${WORK_DIR}" commit -m "<work>: <phase>"`.
  If `base_license` is `copyright`, add `english` only: the base text lives in the ignored
  `_source/` and is never committed. Commit only if there are staged changes. Never push.

## Stopping rules

- Zero fixes in a pass is a valid result. **Never soften a gate to make progress.**
- Escalate to the user (ask, then wait) when:
  - a packet or a unit fails 3 times (the per-unit retry rules);
  - a gate fails after 2 repair rounds;
  - a required source becomes unavailable;
  - a tool reports a structural error you can't route to a phase agent.
- If the user aborts, leave all files in place; the state file allows a later resume.
- A missing phase file is fatal (Step 1).

## Phase file reference

Subagents read these directly (via `shared/boot.md`). You read only `00_interview.md`.
- `phases/shared/`: `boot.md` (entry point, PHASE → file map), `conventions.md`, `image_reading.md`, `content_filter.md`, `copyright.md`,
  `status_contract.md`
- `00_interview.md` (you) · `01_survey.md` · `02_stage.md` · `03_structure.md` ·
  `03b_normalize.md` · `04_transcribe.md` · `05_recollate.md` · `06_boundaries.md` ·
  `07_witness.md` · `08_oracle.md` · `09_consistency.md` · `10_variants.md` · `10b_doubts.md` ·
  `11_convergence.md` ·
  `12_configure.md` · `13_translate.md` · `14a_validate_scan.md` · `14_validate_review.md` ·
  `15a_grade_scan.md` · `15_grade_review.md` · `16_report.md` ·
  `gate_repair.md`

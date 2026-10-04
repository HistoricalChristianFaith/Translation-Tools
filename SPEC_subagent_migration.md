# Spec: replace headless `claude -p` with orchestrated subagents

Status: implemented (rollout steps 1, 3 tool side, 4; the step 2–3 A/B runs are not done yet) ·
Scope: `.claude/skills/translate-work/` · Date: 2026-10-02

**Implementation notes: where the code departs from the text below.**
- Settled structure warnings live in one file per unit, `run/structure_settled/u<NN>.json`, not
  in a shared `run/structure_settled.json`: parallel agents settle at the same time.
- `state.py snapshot … --keep` keeps an existing snapshot. Review rounds take `pre-<K>` with it
  (step 1 now comes before `review_step=scan`), so re-running a round after `apply` never moves
  the reviewers' baseline past fixes they haven't seen. This also covers the §10 restart of an
  old-layout round. Snapshots are copied to `.tmp` and swapped in.
- Every tool write is atomic (tmp + `os.replace`), including the English that `apply` writes.
- `check-findings` tries the fixes **in order**, exactly as `apply` does, not each on its own.
- `bundle` records the units it bundled in `run/bundles/<K>/units.json`; `apply` and `summary`
  default to them, so `unvalidated` units never make `apply` fail.
- `apply` logs go to `logs/apply/<K>.log`, outside the `logs/validate*.log` glob of the report.
- Unit ids are padded to 2 digits or to the width of the highest unit **number** (not count).
- `assemble` output format: a marker line, then the block (blank lines around it are fine).
  `assemble` refuses (exit 2) to overwrite English that wasn't written by this unit's last
  assemble (`run/translate/u<NN>.assembled.json`), so it can never undo review fixes.
- `prep` writes a `skipped` status only for an English file that was never bundled (old runs);
  a bundled unit with English but no status is listed as `unfinished:` and re-dispatched.
- `assemble`-only warnings (`scaffold`, `marks`, internal blank lines) are recorded in the notes;
  `settle` covers the `--structure-only` checks.
- The configure trial keeps its state in `state.json` (`trial_unit`, `configure_trial`); the
  trial review writes `status/configure/trial-review.json`. If the last allowed review still
  changes the rules, the trial unit is re-bundled for the translate phase instead of keeping
  English made under the old rules.
- `IMAGE_RULE` stays as an optional work-specific setting (the Origen run has one); with
  `--images` it goes into the bundle after the generic rule in `13_translate.md`.
- `LOG_ROOT` is gone from `skill_config_base.defaults()`.

## 1. Summary

`/translate-work` already runs as an orchestrator with subagents for every source-text phase,
much like VulnHunter's `/vulnhunt`: one-line `boot.md` prompts, file-based status, waves of 6,
checklists, re-dispatch. The exception is the English half. Translate, validate and grade still
go through `common.call_claude`, which shells out to
`claude -p --dangerously-skip-permissions --tools Read` once per unit. Two of those call sites run
**inside subagents**: the configure trial translation, and the validate reviewer's re-check.

This spec moves those model calls into Agent-tool subagents. It keeps every deterministic guard
the scripts provide today by putting each subagent between two tools:

```
tool: prepare a self-contained bundle  →  subagent: does the model work, writes a file
                                       →  tool: checks the file (the agent loops until it passes)
```

After the migration, no file in the skill invokes `claude`, and `--dangerously-skip-permissions`
is gone.

### Decisions already made

| Question | Decision |
|---|---|
| Translate granularity | **One agent per unit** (dispatch id `u<NN>`) |
| Validate / grade: finder and verifier | **Separate agents.** A *scan* agent finds problems; the existing *review* agent settles them |
| Reviewer's in-round re-check (14 step 3) | **Replaced by rounds.** Each grading recheck `validate-g<j>` becomes a loop of up to 3 validate rounds; a loop that ends with changes left gets a *confirm round* (§6.3a) |
| Length / scaffold heuristics | **Warnings, never loop gates.** The agent must look at each and record what it decided; it must never pad to pass (§6.1) |
| Re-translating inside a review round | **Never.** A unit with no English is recorded, not re-translated; `prep --force` keeps the replaced English (§6.1, §6.3) |
| Structure heuristics after translate | **Warnings everywhere, not only in `assemble`.** `--structure-only` labels each issue `ERROR` or `WARN` and fails only on `ERROR`; a warning settled against the source is recorded and stays settled while its block is unchanged (§6.0) |
| Re-running a round or a bundle | **Always safe.** `prep` / `bundle` delete every earlier file of the units they bundle; `apply` keeps a journal and never applies twice (§6.1, §6.3) |
| Tools | **Every agent keeps every tool**, web search included, the orchestrator as well. What `--tools Read` used to enforce becomes prose in the phase files (§8.2) |
| Model | **Pinned to Opus 5.5** for the orchestrator (`claude-opus-5-5[1m]`, 1M context) and every subagent (`claude-opus-5-5`) (§8.4) |

## 2. Goals and non-goals

**Goals**
1. No headless `claude` call, and no `--dangerously-skip-permissions`, anywhere in the skill.
2. Every model call becomes a subagent that the orchestrator dispatches, tracks with a status
   file, and re-dispatches on failure (VulnHunter's "a failed agent is unknown coverage").
3. Keep the guarantees the scripts provide today (§3.2) exactly, except the two dropped by
   decision (tool restriction, no transcripts). Where cheap, make them stronger.
4. Keep the independence of today's per-unit calls: the translator and the scanners work from
   what the old prompt contained, and the phase files tell them what not to consult. This is a
   rule in prose, not a tool restriction (§8.2).
5. Resume the English phases with `status_check.py`, the same way as every other phase, instead
   of `pgrep` and log tails.

**Non-goals**
- Changing the source-text phases (survey through R7). They are already subagent-based.
- Changing what the prompts ask for. The generic rules move into phase files nearly word for
  word; `work_config.py` still holds the work-specific rules.
- An unattended / batch runner. If one is wanted later, it wraps the *whole* skill headlessly at
  the outermost layer, the way VulnHunter's `vulnhunter-agent/` does (§9).
- Restricting what tools an agent may use (§8.2).

## 3. Background: what exists today

### 3.1 Call sites of `common.call_claude` (`tools/common.py:308`)

| # | Caller | Context | Script |
|---|---|---|---|
| 1 | SKILL.md *Translate* | orchestrator, background Bash, hours | `translate.py` (all units, sequential) |
| 2 | SKILL.md *Review rounds* step 3 | orchestrator, background Bash | `validate.py` / `grade.py` (fidelity / grading call + auto-fix) |
| 3 | `12_configure.md` *Test* step 2 | **subagent** | `translate.py <shortest unit>` |
| 4 | `14_validate_review.md` step 3 | **subagent** | `validate.py --report-only <unit>` |

### 3.2 What the script layer guarantees (all preserved)

| Guarantee | Where today | Where after |
|---|---|---|
| Model never sees headers or held lines; heading rebuilt from the unit number | `parse_source`, `render` | `translate.py prep` / `assemble` (same functions) |
| Block count matches the source | `translate_blocks` (count blank-line paragraphs, retry, block-by-block fallback) | `assemble`: explicit numbered block markers, so the error names the missing block |
| Truncation detection | `looks_truncated` (whole unit) | `assemble`: whole unit (error, as today); per block, the `SHORT_BLOCK_RATIO` rule from `structure_report` (*warn*, as it is in `structure_report` today) |
| Preamble / scaffold leakage | `clean_reply` + `SCAFFOLD_KEYWORDS` | `assemble`: text before the first marker is an error; a block opening with a scaffold phrase is a *warn* |
| Reviewer re-checks its own substantive edits | `14_validate_review.md` step 3 (`validate.py --report-only`) | the next round re-scans with fresh agents; grading rechecks loop, and the last round of a loop gets a confirm round (§6.3a) |
| Units never deleted mid-review | `validate.py` only reports a missing English (`unvalidated`) | the same; `prep --force` moves replaced English aside and refuses after `translate` is done (§6.1) |
| Structure gates (translate gate, every review round, reviewers) | `--structure-only` must report no issue at all | must report no `ERROR`; heuristic issues are `WARN`, settled once against the source and recorded (§6.0) |
| Paired-mark drift | warning per unit | warning per block |
| Guarded auto-fix (unique `old`, marks balanced, block count unchanged) | `validate.apply_fixes` | `validate.py apply`, unchanged |
| JSON shape of findings | `extract_json` + one retry | `check-findings` (schema + enums), looped by the agent |
| Fresh context per unit | one process per call | one agent per unit, working from a single bundle file (§5) |
| Model pinned | `MODEL` in `common.py` (`claude-opus-5-5`) | the same model, pinned in the project settings: `claude-opus-5-5[1m]` for the orchestrator (1M context for its `context_check` budget), `claude-opus-5-5` for every Agent dispatch; checked in each status, ignoring the `[1m]` suffix (§8.4) |
| Model can only read (`--tools Read`) | process flag | **Dropped by decision.** Every agent keeps every tool, web search included; the phase files say in prose what not to consult and what not to edit (§8.2) |
| No transcript of oracle text | `--no-session-persistence` | Dropped. R3 and grade-review subagents already read oracle extracts, so subagent transcripts already contain oracle text (§8.3) |

## 4. Design principles

1. **The tool prepares, the agent works, the tool checks.** Deterministic Python stays the
   gatekeeper. An agent may not write `status: done` until the checking tool exits 0.
   **Only exact checks may gate a loop**: marker integrity, schema, uniqueness, mark balance.
   Heuristics (length ratios, phrase lists, "ends mid-sentence") are warnings. An agent that
   loops until a heuristic passes learns to game it, for example by padding the English to
   meet a length ratio. For each warning, the agent looks again, fixes a real slip, and
   otherwise records the warning and its reason in its notes.
2. **One bundle per dispatch.** For isolated phases, the prepare step writes a single
   self-contained file that holds everything the agent needs. The phase file tells the agent
   what it must not consult (§8.2). This is how we keep the old per-call independence without a
   separate process. Tools are not restricted.
3. **Lean boot for high-fan-out phases.** Isolated phases skip `boot.md` §4's reading list
   (README, carry-forward, decisions). Configure has already compiled all of that into the rules
   inside the bundle.
4. **The orchestrator stays lean.** It runs tools, dispatches one-line prompts and reads status
   lines. It never reads bundles, findings or English.
5. **Old runs keep working.** Every change in path or layout gets a fallback (§10).

## 5. Per-unit dispatch ids

Per-unit agents need an id space alongside packets.

- **Format:** `u<NN>`, the unit number zero-padded to 2 digits (3 if the work has ≥ 100 units),
  matching `oracle/extracts/unitNN.txt`.
- **`packets.py`:**
  - `packets.py uids W [--units 3,8] [--ids p03,p08]` prints the comma list of unit ids (all
    units, the given units, or the units of the given packets).
  - `packets.py list W --ids u07` prints one assignment line, e.g.
    `unit u07 = unit 7 (Homily VII), pages 173-199, packet p03`.
- **`status_check.py --by-unit [--units 3,8]`:** expects `status/<PHASE>/u<NN>.json` for every
  manifest unit (or the given ones). A `done` status also needs its **artifact**:
  - for `translate`, the English file;
  - for `*-scan`, `findings/<K>/<stem>.json`;
  - the artifact must be newer than the unit's bundle.

  A `skipped` translate status also needs the English file to exist ("already translated" with
  no English is stale). The artifact check replaces checklists for per-unit phases (a one-item
  checklist adds nothing). `REDISPATCH:` lists `u<NN>` ids; `--sum` and `--nonzero` work as now.
  Stale statuses are also removed at the source: `prep` and `bundle` delete them for every unit
  they bundle (§6.1, §6.3).

  **`--by-unit` never requires or verifies a checklist.** Leaving this out would break every
  unit: `checklists_required()` (`status_check.py:50-57`) returns True for `translate`, because
  it is in `PHASES` after `checklists_from=B`. Each `done` unit would then fail with "checklist
  missing" and be re-dispatched indefinitely. Concretely:
  - with `--by-unit`, `need_cl` is False and the `CL.verify` branch is skipped, even if a
    checklist file happens to exist; `--require-checklist` together with `--by-unit` is a
    usage error;
  - groups come from the manifest's units (or `--units`), never from `packets.json` and
    `P.governing`, so sub-packets play no part;
  - the ledger-count WARN stays. It only fires if the phase has ledger entries, and
    translate and scan agents add none (§12.4).

  The §11 step 1 test covers this: on a run with `checklists_from=B`, `--by-unit` must exit 0
  once every unit has a `done` status and a fresh artifact.
- **`boot.md` §3:** an ASSIGNMENT matching `u\d+` is a unit id; resolve it with
  `packets.py list --ids <id>`.

## 6. Component designs

### 6.0 Structure check: errors and warnings

Today `validate.py --structure-only` exits 1 on any issue, and four places require it to be
clean: the translate gate, every review round (*Review rounds* step 6), the validate reviewer
(`14_validate_review.md` step 4) and the grade reviewer (`15_grade_review.md`). Once the
translator may leave a heuristic flag in place because nothing was dropped (§6.1), those gates
would either fail forever or push a reviewer to pad the English until the flag clears. Both
are wrong, so the heuristic-is-a-warning rule (§4.1) applies to the structure check everywhere.

**Levels.** `structure_report` labels each issue:

| Issue | Level |
|---|---|
| `missing-english`, `missing-source` | `ERROR` |
| `BLOCK COUNT` | `ERROR` |
| block shorter than `SHORT_BLOCK_RATIO × source` (`short-ratio`) | `WARN` |
| block ends mid-sentence where the source completes (`mid-sentence`) | `WARN` |
| an `ENDING_CHECKS` pattern missing (`ending:<label>`) | `WARN` |

**Block numbers.** Issues name the translatable block by the number of its `@@ n @@` marker
(1..N, held lines not counted). Today `block #i` counts every slot, held lines included, so
it can differ from the marker number. One numbering means the translator's note, a settle
record and a reviewer's line all point at the same block.

**Settled warnings.** A warning that was checked against the source and found not to be a slip
is recorded once:

```
validate.py --config C settle <unit> --check short-ratio --block 7 --by translate/u07 \
    --reason "source repeats a lemma; nothing omitted"
    Appends {unit, block, check, english_sha256, by, reason, at} to run/structure_settled.json.
    english_sha256 is the hash of that English block (of the whole body for unit-level checks
    such as ending:<label>, which take no --block). Refuses a check that isn't currently raised.
```

`structure_report` prints a warning that has a matching record as
`SETTLED block 7: short-ratio (translate/u07: source repeats a lemma; nothing omitted)`. A
record only applies while the block's English is unchanged: when a later round edits the block,
the hash no longer matches and the warning is open again.

**Exit code and output.** `--structure-only` exits 1 only if it printed an `ERROR` line. The
summary line becomes `<a>/<b> file(s) without errors; <w> open warning(s), <s> settled`.

**Who settles.** The rule is the same everywhere: re-read the block against the source; a real
slip is fixed, anything else is settled with a reason. **Never add words, repeat content or
expand a rendering to clear a warning.**
- the translator, for every warning on its unit (§6.1 step 4);
- the validate and grade reviewers, for every open warning on a unit they edited
  (`14_validate_review.md`, `15_grade_review.md`).

**Gates.** Wherever SKILL.md or a phase file says `--structure-only` "must be clean", it now
means "exit 0: no `ERROR` line". Open warnings never block a gate; the progress line names the
units that still have them. The final report lists open warnings and the settled ones with
their reasons.

### 6.1 Translate (phase 13, new phase file `13_translate.md`)

**Tools (`translate.py`):**

```
translate.py --config C prep [--units 3,8] [--images] [--force [--after-review]]
    For each unit: parse_source, then write run/bundles/translate/u<NN>.md.
    Skips units whose English already exists (unless --force). Such a unit gets a `skipped`
    status ("already translated") only if it has no status yet; a `done` status is never
    overwritten, so its counts survive a second `prep`.
    For every unit it bundles, it first deletes that unit's status/translate/u<NN>.json and
    notes/translate/u<NN>.md, and any structure_settled.json records for that unit, so nothing
    from an earlier attempt can pass for this one. Without --force it keeps an existing
    run/translate/u<NN>.out.txt, so the next agent continues it (MODE=retry). With --force it
    also deletes that file and MOVES the English file to
    run/translate/replaced/<stem>.<timestamp>.txt (never deletes it). Once state.json says
    `translate` is done, --force refuses (exit 2) unless --after-review is also given, because
    the English now holds review-round fixes.
    Prints `bundled: u01,u02,…`, `existing: …` and `replaced: …`.

translate.py --config C assemble <unit>
    Parse run/translate/u<NN>.out.txt, check it, render the English file. Exit codes:
    0 = English written (warnings may be printed); 1 = errors (nothing written).
    Prints one line per problem: `ERROR block 12: …` / `WARN block 7: …`.

translate.py --config C --check
    Parse-only self test (unchanged), plus a round trip IN MEMORY: for each unit, build the
    bundle text, use its own source blocks as the "output", run the assemble parser and checks
    on that string, and render to a string. The block count and held-line positions must match
    the source. --check writes NOTHING: no bundle, no status, no English. Configure runs it on
    live runs, and the §11 tests run it on finished ones.
```

**Bundle `run/bundles/translate/u<NN>.md`:**

```markdown
# Translate bundle: <unit label> (unit 7)
source_language: Latin
blocks: 23
output: <abs path>/run/translate/u07.out.txt
images: none | <abs paths, one per line>

## Work context
<WORK_CONTEXT>

## Rules for this work
<TRANSLATION_RULES>

## Text
@@ 1 @@
<block 1 source text>

@@ 2 @@
<block 2 source text>
…
```

The generic rules now in `translate.build_prompt` (keep the block structure, keep `» «` and
`* *`, translate Scripture as it stands, never use a modern Bible) and `IMAGE_RULE` move into
`13_translate.md` with the wording intact. The bundle carries only work-specific data.

**Output format (`run/translate/u<NN>.out.txt`):** the same `@@ n @@` markers, each followed by
one paragraph of English. The agent may write it in several appends. That's useful for very
long units and is the `tiny-edit` content-filter mode: write a few blocks at a time.

**`assemble` checks.** Errors are exact checks only (§4.1). Heuristics are warnings.

| Check | Level | Why |
|---|---|---|
| markers `1..N` each present exactly once, in order | error | exact |
| any non-blank text before the first marker or between a marker line and its block | error | exact; this is where a leaked preamble would sit, so it is caught without a phrase list |
| an empty block | error | exact |
| whole unit `len(out) < 0.5 × len(src)` | error | today's `looks_truncated` threshold, which already forced a retry. It is far below any real translation ratio (Latin ~0.70, Greek ~0.55 per *block* are the *warning* floors), so meeting it never takes padding |
| internal blank lines in a block (collapsed) | warn | as the old fallback did silently |
| block shorter than `SHORT_BLOCK_RATIO × source` (source block ≥ `SHORT_MIN_SOURCE`) | warn | heuristic; same rule as `structure_report`, where it is also only an issue line |
| block opens with a `SCAFFOLD_KEYWORDS` phrase | warn | heuristic; the list includes phrases a real sentence can start with ("consulting the …") |
| paired-mark opener count differs from the source block | warn | today's per-unit NOTE, per block |

**Agent procedure (`13_translate.md`):**
1. Read the bundle. With images listed, also read `shared/image_reading.md`.
2. Translate every block into the output file.
3. Run `assemble`. Fix every block named in an `ERROR` line and re-run until it exits 0.
4. Settle each `WARN` line from `assemble`, then run `validate.py --structure-only <stem>` and
   settle each `WARN` it prints (§6.0). Its `short-ratio`, `mid-sentence` and `ending:` lines
   are heuristics too. For each one, re-read the block against the source:
   - **a real slip** (a clause dropped, the block stopped early, a mark lost): fix the output
     file and re-run `assemble`;
   - **not a slip** (the source is wordy, Greek compresses, the sentence really ends there):
     record it with `validate.py settle <unit> --check short-ratio --block 7 --by translate/u07
     --reason "…"` and add the same line to `## Checks` in the notes: `block 7: short-ratio
     0.62: source has a repeated lemma; nothing omitted`.

   `--structure-only` must end with no open `WARN` and no `ERROR` for your unit. The phase file
   says it outright: **never add words, repeat content or expand a rendering to satisfy a
   length check. A faithful block shorter than the ratio is correct.** The ratio finds dropped
   clauses; it doesn't define a good length.
5. Write notes (`## Checks` as above, `## Doubts`: readings you found doubtful, in words; never
   edit the source), then the status: `{"phase": "translate", "packet": "u07", "units": [7],
   "status": "done", "model": "claude-opus-5-5", "blocks": 23, "fixes": 0, "doubts": 0,
   "warns": 2, …}`. `warns` counts the warnings you settled.

Sources rule in the phase file (prose; tools are not restricted, §8.2): your bundle is your
text and your rules. Don't consult other units' English, reports, notes, earlier findings or
the oracle extracts. The translation must not depend on them. You may use any tool for
reference, for example a web search to identify a person, place or rare term. Never take a
rendering from an existing English translation of this work or from a modern Bible. Edit only
your own output file; never the source.

**`MODE=retry`:** keep the blocks already in the output file. `assemble` reports which are
missing; finish those. Before that, re-read the **last** block already in the file against
its source: the previous agent may have died while writing it, and a cut-off block only
raises a warning. A fresh dispatch that finds an output file already there does the same.
This lets a unit resume partway through, which today's script can't do.

**Orchestrator (SKILL.md *Translate*, replaces the background script):**
1. `T/state.py phase W translate in_progress`.
2. `T/translate.py --config CFG prep [--images]` (`--images` if `state.json`
   `translate_images` is true).
3. Dispatch `PHASE=translate ASSIGNMENT=u<NN>` for every bundled id, in waves of 6.
4. `T/status_check.py W --phase translate --by-unit`; standard retry rules (2 retries, then ask
   the user). A `filter_blocked` unit is re-dispatched with `MODE=tiny-edit`.
5. `T/merge_notes.py W --phase translate --report run/translate_notes.md --title "Translate"`.
6. **Gate.**
   - `ls english | wc -l` equals the unit count. A missing unit is a failed agent: follow the
     retry rules in step 4.
   - `T/validate.py --config CFG --structure-only` must exit 0 (no `ERROR` line, §6.0):
     - An `ERROR` (`BLOCK COUNT`, `MISSING`) can't happen after a clean `assemble`. If one
       appears, re-translate that unit once (`prep --force --units <n>`, which is allowed
       because `translate` isn't done yet, then dispatch). If it's still flagged, record it
       and continue.
     - `WARN` lines never block the gate and are **not** re-dispatched. `SETTLED` ones were
       checked against the source by the agent. An open `WARN` means the agent didn't settle
       it: the validate scan sees it in its bundle (§6.3), and the validate reviewer settles
       it. A fresh translation would be a coin toss, and the validate scan judges omissions
       better than a ratio does. Name the units in the progress line
       (`structure: 0 errors; 3 settled, 1 open (u12)`).

   Today the old flow re-ran every flagged unit once with `--force`. That's replaced because
   the per-block check now runs, and gets settled, inside the agent.
7. Done, progress line, auto-commit, context check.

### 6.2 Configure trial (phase 12)

A subagent can't dispatch a subagent, so the orchestrator now runs the trial.

1. Configure agent (unchanged up to *Test* step 1): writes `work_config.py`; `translate.py
   --check` must pass. *Test* steps 2–3 are removed. The agent picks the trial unit (the
   shortest) and puts `"trial_unit": <n>` in its status.
2. Orchestrator: `T/translate.py --config CFG prep --units <n> [--images]`, then dispatch
   `PHASE=translate ASSIGNMENT=u<NN>` and run `status_check --by-unit --units <n>`.
3. Orchestrator: dispatch `PHASE=configure ASSIGNMENT=configure MODE=trial-review`. The agent
   reads the trial English against the source, checks marks, names, Scripture, held lines and
   heading, adjusts the rules, and adds `"rules_changed": true|false` to its status.
4. If `rules_changed`: repeat steps 2–3 with `prep --force` (at most 2 iterations, then go on
   and note it). The final trial output stays, and the translate phase skips that unit
   (`prep` writes its `skipped` status). `prep --force` is allowed here because `translate`
   isn't done yet; the replaced trial English goes to `run/translate/replaced/`.

Side benefit: the trial now tests whether the **rules alone** produce a good translation. Today
the same agent that wrote the rules also produces the translation, so it knows more than the
rules say.

### 6.3 Validate round `<K>` (scan → apply → review)

**New tool subcommands (`validate.py`):**

```
validate.py --config C bundle --phase K --units 3,8
    structure_report each unit. A unit is `unvalidated` ONLY when structure_report returns a
    status other than "ok", which today means `missing-english` or `missing-source`
    (validate.py:44-47; the same test validate_file uses at :224). A unit with structure
    *issues* (block count, short block, mid-sentence, ENDING_CHECKS) is "ok" and IS bundled,
    as today; its open ERROR and WARN lines go into the bundle under `## Structure notes`, so
    the scanner can check them against the source. SETTLED warnings are left out, so the
    scanner judges those blocks without the translator's reasoning. `unvalidated:` units get
    no bundle.
    Clean slate: for every unit it bundles, it first deletes that unit's
    findings/<K>/<stem>.json, findings/<K>/<stem>.apply.json, status/<K>-scan/u<NN>.json and
    notes/<K>-scan/u<NN>.md. A round key that runs again (a deliberate re-run, the §10 restart)
    can then never read an earlier attempt's files as its own.
    Writes run/bundles/<K>/u<NN>.md: unit label, WORK_CONTEXT, VALIDATION_HOUSE_RULES, the
    source file (as today's prompt: whole file), the English body, the output path, and
    `english_sha256:`, the hash of the whole English file as the scanner sees it.
    Prints `bundled: …` and `unvalidated: …`.

validate.py --config C check-findings --phase K --unit 7
    run/findings/<K>/<stem>.json against the schema below. Each `fix` is tested on its own
    against the current English file with the same predicate `apply_fixes` uses (one shared
    function): `old` occurs exactly once in the raw file, header included, as `apply_fixes`
    counts it; `old != new`; the result keeps the marks balanced and the block count
    unchanged. (This is new: the scanner sees bad fixes before `apply` skips them.) A finding
    whose fix fails keeps the finding and drops or repairs the `fix`; the phase file says so,
    so that "make it pass" never turns into "delete the finding". Exit 0 = valid.

validate.py --config C apply --phase K --units 3,8
    apply_fixes, unchanged, from each findings file, with a journal in
    run/findings/<K>/<stem>.apply.json so that a re-run never applies a fix twice:
    - no findings file: error for that unit (its scan didn't finish).
    - no journal: if the English no longer matches the bundle's english_sha256, REFUSE the
      unit (the English changed after the scanner saw it; re-bundle). Otherwise compute the
      result in memory, write the journal {state: "pending", findings_sha256, english_before,
      english_after (hashes), applied[], skipped[] with reasons}, then write the English, then
      set state "done".
    - journal present: its findings_sha256 must match the findings file, else error (findings
      rewritten after apply: re-run `bundle` for that unit). State "done": skip. State
      "pending": English == english_after → set "done"; == english_before → write it, set
      "done"; anything else → error.
    Prints one line per unit (`applied 3, skipped 1` / `already applied` / `REFUSED …`).
    Exit 0 only if every unit ends "done".

validate.py --config C summary --phase K --units 3,8
    The score table today's run prints at the end (same format), for logs/<K>.log; the report
    phase reads it.

validate.py --config C --structure-only [unit]     (ERROR / WARN / SETTLED lines, §6.0)
validate.py --config C settle <unit> --check … [--block n] --by … --reason …   (§6.0)
```

**Findings schema:** today's JSON exactly (`score`, `grade`, `fidelity`, `findings[]` with
`locus`, `severity`, `category`, `source`, `ours`, `issue`, optional `fix{old,new}`,
`summary`). `normalize()` stays as the reader.

**Scan agent (new `14a_validate_scan.md`, PHASE `<K>-scan`, ASSIGNMENT `u<NN>`):**
- The fidelity instructions from `validate.build_prompt` move here nearly word for word
  ("the source is the sole arbiter", what counts, what doesn't, the fix rules, "do not invent
  defects").
- Sources rule (prose, §8.2): work from the bundle; don't consult earlier findings, notes,
  reports, other units or the oracle. Tools for reference are fine. **Never edit the English
  or the source.**
- Write the findings JSON, loop `check-findings` to exit 0, then write a status with
  `"model"`, `"findings"`, `"significant"` and `"score"`.
- Each unit gets a fresh agent. The scanner is not told about earlier rounds, the same as
  today's per-call validator.

**Review agent (`14_validate_review.md`, per packet, unchanged role):**
- Inputs change from `logs/<K>/<stem>.1.txt` to `findings/<K>/<stem>.json` plus
  `<stem>.apply.json`. The old path stays as a fallback for older runs.
- Step 3 (re-validate through the script) is **removed**, and the round structure takes over
  its job (§6.3a). The original justification, "substantive fixes already trigger another
  round", was only half true. A round with substantive fixes triggers another round *except*
  in two cases:
  - `validate-r5`, the last validate round;
  - every `validate-g<j>`, which is followed by a grade round on the *grade* round's changed
    set, not by another source check (`SKILL.md:329-337`).

  Without §6.3a, substantive reviewer edits in those rounds would never be checked by a fresh
  model.
- Structure (step 4): `--structure-only` must show no `ERROR` for the packet's units (§6.0).
  Every open `WARN` on a unit the reviewer edited, or one carried from translate, is settled
  like a translator's: fix a real slip, otherwise `validate.py settle … --by <K>/<packet>`.
  Never pad to clear it. `15_grade_review.md` gets the same rule.
- Everything else is unchanged: review the auto-fixes by diff, settle the unfixed findings,
  count fixes as substantive or trivial.

**Orchestrator, one round `<K>` over packets `<P>`** (replaces SKILL.md *Review rounds*
steps 1–3; steps 4–7 stay):
1. `T/state.py set W review_round=<K> review_packets=<P> review_step=scan`. Clear
   `assignments/<K>/` and `assignments/<K>-scan/`.
2. `T/state.py snapshot W pre-<K> --dir english`.
3. `T/validate.py --config CFG bundle --phase <K> --units "$(T/packets.py units W --ids <P>)"`.
   **Never re-translate inside a review round.** An `unvalidated:` unit means the English or
   the source file is missing. That's a broken run (the translate gate guarantees one English
   file per unit), not something a review round should fix. Record it as today
   (`T/state.py set W review_unvalidated.<K>=<units>`, and in the progress line), continue
   with the rest, and tell the user. The repair is a deliberate, separate step:
   `prep --force --after-review --units <n>` plus a translate dispatch, then a fresh round
   for that unit. `--after-review` exists only so this can't happen by accident, and even then
   `prep` moves the old English aside instead of deleting it.
   (Why this matters: if "fail" were read as "has structure issues", re-translating would
   silently throw away every fix earlier rounds made to that unit.)
4. Dispatch `PHASE=<K>-scan ASSIGNMENT=u<NN>` per bundled unit, in waves of 6.
   `T/status_check.py W --phase <K>-scan --by-unit --units <them>`, standard retries.
5. `T/state.py set W review_step=apply`.
   `T/validate.py --config CFG apply --phase <K> --units … > logs/<K>-apply.log`, then
   `T/validate.py --config CFG summary --phase <K> --units … > logs/<K>.log`.
6. `T/state.py set W review_step=review`. Reviewers per packet, as today (checklist
   `--whole --by unit`, status_check `--sum substantive --nonzero substantive`, merge notes,
   structure check, decisions, auto-commit, context check, progress line). The structure check
   passes on exit 0, meaning no `ERROR` (§6.0); the progress line names units with open
   warnings.

**Re-running and resuming a round.** Starting a round key again from step 1 is safe: step 3
clears every earlier file of the bundled units, and the snapshot is retaken before anything is
applied. Resuming is different, because the snapshot must stay the one taken before `apply`:
- `review_step=scan`: re-run step 4's status_check and dispatch only `REDISPATCH:` ids. Don't
  re-run `bundle`: it would discard the finished scans. (Exception: a unit with no bundle file
  gets `bundle --units <n>` alone.)
- `review_step=apply`: re-run step 5; the journal makes it safe.
- `review_step=review`: as today.
- With `review_step` at `apply` or `review`, **never** re-run steps 1–3. A new `pre-<K>`
  snapshot taken after `apply` would hide the auto-fixes from the reviewers' diff.

### 6.3a Round sequencing: recheck loops and confirm rounds

Validate rounds 1–5 and grade rounds 1–3 keep today's rules. Two changes close the gap left by
removing the reviewer's re-check:

**1. Each grading recheck becomes a loop.** After grade round `j` (`grade`, `grade-r2`,
`grade-r3`) with a non-empty changed set `S`:
- `validate-g<j>` on `S` (as today);
- then `validate-g<j>-r2` and `validate-g<j>-r3`, each on the changed set of the round before
  it. Stop as soon as a round's changed set is empty.
- Then continue with grade round `j+1` on grade round `j`'s changed set (unchanged rule).

**2. A loop that ends with changes left gets one confirm round.** This applies to
`validate-r5` and `validate-g<j>-r3`. Run `<K>-confirm` on its changed set (e.g.
`validate-r5-confirm`, `validate-g2-r3-confirm`). A confirm round is a normal validate round
(§6.3 steps 1–6) with two differences:
- **No `apply` step** (`summary` still writes `logs/<K>.log`). The scanners' `fix` objects
  are suggestions only. Reviewers run
  `14_validate_review.md` with `MODE=confirm`: there are no auto-fixes to review, they settle
  every finding by hand and apply the good fixes themselves. This is exactly what today's
  step 3 did ("you may apply its good suggestions by hand").
- **It never triggers another round.** Its substantive count is recorded. If it's nonzero,
  the phase note says `not settled after confirm: <ids>`, and the report lists those passages
  for human review.

The confirm reviewers' own edits are the only ones no fresh model ever re-checks. That matches
today, where edits applied by hand after the step 3 re-check weren't re-checked either. So
the guarantee is kept exactly, and only at the last round of each loop.

**Cost.** For each grade round there are at most 3 recheck rounds and 1 confirm round, and
each covers only the previous round's changed set, usually a few packets. In the §9 example,
a typical grade round adds 1–2 small recheck rounds; a confirm round runs only when a loop
hits its cap.

**Key and tool changes:**
- `status_check.checklists_required()` maps round keys to their base phase with
  `^(validate|grade)-[rg]\d+$` (`status_check.py:56`). Extend it to match every review-round
  key: `^(validate|grade)(-[rg]\d+)*(-confirm)?$`. Scan keys (`…-scan`) never match; they use
  `--by-unit` (§5).
- `boot.md` §2: the `14_validate_review.md` row adds `validate-g<j>-r<k>` and `<K>-confirm`,
  and MODE `confirm` (inferred from the `-confirm` suffix; the prompt states it too).
  Scan rows add `validate-g<j>-r<k>-scan` and `<K>-confirm-scan`.
- Report names for `merge_notes.py`: `validation_review_g<j>_r<k>.md`,
  `validation_review_<round>_confirm.md`.
- `16_report.md` lists the new round keys and every `not settled after confirm` passage.
- SKILL.md *Grade*: replace "the recheck `validate-g<j>` on that changed set" with the loop
  above. SKILL.md *Validate*: replace "If round 5 still has a changed set, record it" with the
  confirm round, then record what it leaves.

### 6.4 Grade round `<K>` (scan → review)

The same as §6.3 without `apply` (grading has never written to the English).
- `grade.py --config C bundle --phase K --units …`: bundles include `GRADING_CAVEATS`,
  `ORACLE_NOTES[n]`, the source as context, the English, and the oracle extract. It prints
  `bundled:` and `ungraded:` (no oracle coverage). Only bundled units are dispatched. Same
  clean slate as `validate.py bundle`: it first deletes each bundled unit's earlier findings,
  scan status and scan notes for `<K>`.
- `grade.py check-findings` (divergences schema) and `grade.py summary --phase K`.
- New `15a_grade_scan.md` (PHASE `<K>-scan`): the grading instructions from
  `grade.build_prompt`. Work from the bundle (sources rule, §8.2); write
  `findings/<K>/<stem>.json`; never edit.
- `15_grade_review.md`: input path → `findings/<K>/<stem>.json` (old `logs/` path as
  fallback).

### 6.5 `boot.md` changes

**§2 map, new rows:**

| PHASE | Phase file | ASSIGNMENT | MODEs |
|---|---|---|---|
| `translate` | `13_translate.md` | unit `u<NN>` | `retry`, `tiny-edit` |
| `validate-scan`, `validate-r<k>-scan`, `validate-g<j>[-r<k>]-scan`, `<K>-confirm-scan` | `14a_validate_scan.md` | unit `u<NN>` | `retry` |
| `validate-g<j>-r<k>`, `<K>-confirm` (review rounds, §6.3a) | `14_validate_review.md` | packet (whole) | `confirm` (for `-confirm` keys) |
| `grade-scan`, `grade-r<k>-scan` | `15a_grade_scan.md` | unit `u<NN>` | `retry` |
| `configure` | `12_configure.md` | `configure` | + `trial-review` |

**§4, lean boot:** for `translate` and every `*-scan` phase, read only `status_contract.md`
(§2 Status, §4 Return), `content_filter.md`, your phase file and your bundle (plus
`image_reading.md` if the bundle lists images). Skip README, carry-forward and decisions;
configure compiled them into the bundle's rules. State plainly why: consulting the run's other
files (reports, notes, the oracle, other units, earlier findings) breaks the independence this
phase exists for. Every tool stays available, web search included (§8.2).

## 7. Removals and cleanup

| File | Change |
|---|---|
| `tools/common.py` | Delete `call_claude`, `call_for_json`, `extract_json`, `is_rate_limit_error`, `RETRY_DELAYS`, `RATE_LIMIT_DELAYS`, and the `CLAUDE_CMD` / `CLAUDE_TIMEOUT` / `MODEL` defaults. Update the module docstring. `load_config` prints a one-line notice if a config still sets them (ignored) |
| `tools/translate.py`, `validate.py`, `grade.py` | Drop `--model`, `--no-log`, `--log-dir`, the per-file model-calling paths, and `build_prompt` (its text moves to phase files). Add the subcommands above. Keep `--structure-only` and `--check`. `validate.py`: `structure_report` levels, marker block numbers, `settle` and `run/structure_settled.json` (§6.0); one shared fix predicate for `check-findings` and `apply_fixes`; `bundle` clean slate; `apply` journal (§6.3) |
| `tools/work_config_template.py` | Delete the *Model invocation* section (lines 138–146) and the usage lines that imply model calls |
| `tools/skill_config_base.py` | `LOG_ROOT` is no longer needed for transcripts (keep it only if `summary` uses it) |
| `tools/context_check.py:7` | Update the comment (headless calls no longer write transcripts) |
| `tools/status_check.py` | `--by-unit` (§5: no checklists, manifest groups; a `skipped` translate status needs the English); `checklists_required()` regex covers the §6.3a round keys; WARN when a status's `model` isn't `PINNED_MODEL`, comparing with any `[1m]` suffix dropped (§8.4) |
| `tools/state.py` | `PINNED_MODEL = "claude-opus-5-5"` (no context suffix), next to `PHASES` (read by `status_check.py`) |
| `tools/scratch_copy.py` | New: test copies of a run (§11.0) |
| `SKILL.md` | Step 0: the orchestrator must be Opus 5.5 with 1M context (`claude-opus-5-5[1m]`), and the pin settings must be in place (§8.4). Step 2: drop `claude --version`. Phases table: rows 12–15. Rewrite *Translate* and *Review rounds*. Every structure gate means "no `ERROR`" (§6.0). *Resuming* steps 4–5 become: per-unit `status_check` for translate; for rounds, `review_step` says where to resume, as in §6.3 *Re-running and resuming a round*. Dispatch template: `<id>` may be `u<NN>`; `model: "opus"` resolves to the pinned model. Phase file reference: add `13`, `14a`, `15a` |
| `phases/12_configure.md` | *Test* steps 2–3 → `trial_unit` in status; add `MODE: trial-review` section (its structure check: no `ERROR`, warnings settled as in §6.0) |
| `phases/14_validate_review.md`, `15_grade_review.md` | Input paths; remove step 3 (14); 14 gains the §6.3a round keys and `MODE: confirm` (no auto-fixes; settle and apply every finding by hand). Structure: "must be clean" → no `ERROR`; settle open warnings, never pad (§6.0) |
| `phases/16_report.md` | `logs/<K>.log` is now written by `summary`, same format; mention `logs/<K>-apply.log`; list the §6.3a round keys and every `not settled after confirm` passage; list open structure warnings and the settled ones with reasons (§6.0); translate counts come from `status_check --by-unit` |
| `phases/shared/boot.md` | §2 rows, §3 unit ids (and: for `translate` and `*-scan`, the phase file's `retry` / `tiny-edit` meaning replaces §3's general one), §4 lean boot |
| `phases/13_translate.md`, `14a`, `15a` | New. Each states the sources rule in its own words (§8.2) |
| `.claude/settings.json` (project) | New or extended: the model pin (§8.4) |
| `TRANSLATION_PROCESS.md` §3 | Replace the headless paragraph: everything runs in one interactive session with subagents |
| `README.md` (skill) | Tools listing; `run/` layout gains `bundles/`, `translate/`, `findings/` |
| `examples/original-scripts/` (repo root, outside the skill) | **Unchanged** (historical record; they're not called) |

New `run/` subfolders: `bundles/<PHASE>/`, `translate/`, `findings/<K>/`. All live under the
git-ignored `_source/`.

## 8. Permissions, tools, copyright, model

### 8.1 Permissions

Subagents inherit the session's permission mode. Permissions are separate from tools (§8.2):
every tool is available, and the allowlist only saves approval prompts. The skill should run
without bypass:
- The interview (or README) recommends a project allowlist covering `python3` calls to
  `TOOLS_DIR/*.py`, Bash `ls`/`diff`/`git -C <WORK_DIR>`, and Read/Edit/Write under the
  works root. Absolute paths in Read/Edit rules use the `//` prefix.
- Draft the exact rules from a real run's transcript with the `fewer-permission-prompts`
  skill, rather than guessing them up front.
- The page images live under `WORK_DIR/_source`, inside the allowlisted tree, so `--images`
  needs nothing special. That was the original reason for the bypass flag.

### 8.2 Tools and independence (decision)

Today the headless calls can only read (`--tools Read`). **After the migration no agent's tools
are restricted.** The orchestrator, the per-packet agents and the per-unit subagents all run
with the full `general-purpose` tool set, web search and web fetch included, so an agent that
needs a lookup can do one. There is no custom agent type and no tool list.

What the process flag used to enforce becomes prose, stated in each phase file in its own words:
- **Independence** (translate, `*-scan`): work from your bundle. Don't consult other units'
  English, reports, notes, earlier findings or the oracle extracts. They would make this
  judgment depend on work it is meant to check, or on the yardstick grading uses later.
- **Sources for a rendering** (translate, reviewers): reference lookups are fine, for example a
  web search to identify a person, place, rare term or the edition. Never take a rendering from
  an existing English translation of this work or from a modern Bible; Scripture is translated
  as the author quotes it. (These are today's prompt rules, unchanged.)
- **Write scope:** edit only your own output files. Scanners never edit; nobody but the
  source-text phases edits the source.

The source-text phases already run this way, with full tools and rules in prose, so this
brings the English half in line with them. The trade-off is accepted: no tool catches a
breach. The review rounds, grading and auto-commit diffs are the backstop. The orchestrator's
context rules in SKILL.md (don't read reports, notes or text into your own context) are about
its context budget, not about tools, and are unchanged.

### 8.3 Copyright

Grade bundles contain oracle text. They live in `_source/` (git-ignored), next to the existing
`oracle/extracts/`. Subagent transcripts also contain oracle text, but R3 (`08_oracle.md`) and
grade review already put it there, so this adds no new exposure. If that matters, the fix applies
to the whole skill, not just to grade.

### 8.4 Model: pinned to Opus 5.5

Today `MODEL = "claude-opus-5-5"` pins every headless call. The Agent tool's `model` parameter
takes only aliases (`"opus"`), and an alias moves when a new Opus ships, which could happen
partway through a run that lasts several days. Pin the alias itself in the project's
`.claude/settings.json`, the project the `/translate-work` session runs in:

```json
{
  "model": "claude-opus-5-5[1m]",
  "env": {
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-5-5",
    "CLAUDE_CODE_SUBAGENT_MODEL": "claude-opus-5-5"
  }
}
```

- `model` pins the orchestrator's own session, **with the 1M context window**. A plain model ID
  doesn't opt into 1M; only the `[1m]` suffix does. The orchestrator needs it: `context_check.py`
  pauses at `context_threshold_k` (default 400k), and on a standard window the session would
  compact before that pause could fire.
- Subagents stay on the plain ID. A per-unit or per-packet agent works from one bundle or one
  packet and doesn't need 1M; it would only cost more.
- `ANTHROPIC_DEFAULT_OPUS_MODEL` makes the `opus` alias resolve to Opus 5.5, for `/model opus`
  and for every Agent dispatch with `model: "opus"`. The dispatch template keeps
  `model: "opus"`.
- `CLAUDE_CODE_SUBAGENT_MODEL` covers any dispatch without an explicit model.
  `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` would also override per-dispatch models. The docs don't
  say for certain how it ranks against the Agent tool's `model` parameter, and with the alias
  pinned it isn't needed, so leave it out.

**Checks.**
- SKILL.md Step 0: the orchestrator must be running `claude-opus-5-5[1m]`, not just "an
  Opus-class model". Plain `claude-opus-5-5` fails this check too: the model is right, but the
  context budget isn't. If the check fails, or the settings above are missing, say so and offer
  to add them. Changing settings takes a new session. (`/model opus` mid-run switches to the
  plain ID, which this check also catches on the next resume.)
- Every translate and scan status records `"model"`, the model the agent reports it is running.
  `status_check.py` prints a WARN for any status whose `model` isn't `PINNED_MODEL`
  (`state.py`). The comparison drops a trailing context suffix (`[1m]`) from both sides first,
  so `claude-opus-5-5[1m]` matches `claude-opus-5-5`. The pin is on the model, not the window.
  On a WARN the orchestrator stops and tells the user. It's a WARN, not a re-dispatch, because a
  re-dispatch would run on the same wrong model.
- The §11 A/B test only counts if A (headless, `MODEL`) and B (agents) ran on the same model.
  Check B's statuses.

## 9. Cost and throughput

Example: 40 units in 8 packets, oracle present, typical 3 validate + 2 grade rounds.

| Step | Today | After |
|---|---|---|
| Translate | 40 headless calls, **one at a time** | 40 agents in 7 waves of 6 (faster wall-clock) |
| Validate round (full) | 40 calls + 8 reviewers | 40 scan agents + 8 reviewers |
| Later rounds | changed set only | changed set only (scan per unit in the set); each grade round adds up to 3 recheck rounds plus 1 confirm round on shrinking changed sets (§6.3a) |
| Orchestrator context | ~1 line per round | ~1 dispatch line per agent; `context_check.py` PAUSE covers it |

Per unit, an agent costs more than a bare `-p` call (boot reading, tool round-trips, the
`assemble`/`check-findings` loop). The lean boot keeps the extra small. Rate limits are now
handled by the harness plus the existing retry and re-split rules, instead of the script's
backoff.

Batch / unattended runs, if needed later: one headless invocation of the **whole** skill
(`claude -p "/translate-work <dir>"` with the §8.1 allowlist), never headless calls inside it.

## 10. Migration and compatibility

- **Runs that already have English** from the old script: `prep` writes `skipped`
  ("already translated") statuses, so `status_check --by-unit` passes.
- **A run paused mid-translate** with the background script: on resume, if `pgrep` still finds
  the script, wait for it once. Otherwise switch to the new flow; `prep` skips the units already
  done.
- **A run paused mid-review-round** under the old layout: if `review_step` is absent and
  `logs/<K>/` holds transcripts, finish that round the old way, with reviewers reading the old
  paths (fallbacks kept in 14/15). The next round uses the new flow. (Running the old scripts
  needs the headless path, so if we delete it in the same commit, such a round instead restarts
  its scan with the new flow. **Pick one when implementing;** restarting the round is simpler.)
- Configs that set `CLAUDE_CMD` / `MODEL` keep loading (ignored, with a notice).

## 11. Rollout plan

Each step leaves the skill working.

### 11.0 Test harness: never test on a real run

Every test below runs on a **scratch copy** of a finished run, never on the run itself. Three
things make testing in place destructive:
- `TARGET_DIR` is hard-wired to `<WORK_DIR>/english` (`skill_config_base.py:99`), so there is
  no "scratch `english/`" inside a run;
- `prep --force` replaces the English;
- bundles, statuses and findings would land in the finished run's `run/`.

A plain `cp -R` isn't enough either. The configure agent bakes the absolute `WORK_DIR` into
`run/work_config.py` (`B.defaults("<abs WORK_DIR>")`, `12_configure.md:22-26`), and
`state.json` holds `work_dir`. A copied config would still read and write the original
folder.

New tool, `tools/scratch_copy.py`:

```
scratch_copy.py --work-dir SRC --to DST [--english-from <snapshot label>]
    Refuses if DST exists, or if either path is inside the other.
    Copies SRC to DST. On APFS it uses `cp -cR` (clonefile: instant, and the page images
    take no extra space); otherwise it falls back to shutil.copytree.
    Rewrites the absolute SRC path to DST in run/work_config.py and state.json.
    Sets auto_commit=false in the copy.
    Then VERIFIES: loads the copy's config and asserts that SOURCE_DIR, TARGET_DIR,
    IMAGE_DIR, LOG_ROOT and every image_paths(n) / oracle extract path lies under DST,
    and greps the copy's run/*.py and run/*.json for any remaining SRC path. Any hit: exit 1.
    --english-from pre-validate: replaces DST/english with run/snapshots/pre-validate/,
    i.e. the English exactly as validate round 1 saw it.
```

Put `DST` outside any git repository (e.g. the session scratchpad). Each test starts from a
fresh copy, so earlier tests can't leave state behind.

### 11.1 Steps

1. **Tools, additive.** `packets.py uids` and unit-id `list`; `status_check.py --by-unit` with
   artifact checks; `validate.py` / `grade.py` subcommands `bundle`, `check-findings`, `apply`,
   `summary`; `translate.py prep` / `assemble` and the extended `--check`; `scratch_copy.py`.
   The old paths still exist.
   *Tests (scratch copy):*
   - **`--check` writes nothing.** Take a recursive listing with hashes of `english/` and
     `_source/run/` before and after `translate.py --check`; they must be identical.
   - **`apply` matches `apply_fixes`.** Write findings by hand, including a non-unique `old`,
     a mark-unbalancing `new` and a block-merging `new`. On copy A run `bundle` →
     `check-findings` → `apply`. On copy B run `validate.apply_fixes` directly with the same
     findings. `diff -r` the two `english/` folders: they must be identical. `check-findings`
     must reject the three bad fixes that `apply_fixes` skips.
   - **`--by-unit` on a run with `checklists_from=B`:** with no checklists, all `done`
     statuses and fresh artifacts, it exits 0. A stale artifact (older than the bundle)
     produces `REDISPATCH`. (§5)
   - **`checklists_required()`:** a table test over `validate`, `validate-r5`,
     `validate-g2-r3`, `validate-r5-confirm` (all map to their base phase) and
     `validate-r2-scan`, `translate` used with `--by-unit` (no checklist). (§6.3a)
   - **`prep --force` guard:** with `translate` done, `prep --force --units n` exits 2 and
     leaves the English untouched; with `--after-review` it moves the English to
     `run/translate/replaced/`.
   - **`summary`** prints the same table format as today's validate/grade run.
   - **Structure levels (§6.0).** On units built to trip each check: `--structure-only` exits
     0 when it prints only `WARN` lines and 1 when it prints an `ERROR`. On a unit with held
     lines and a header lemma, the block numbers in its lines equal the `@@ n @@` markers.
   - **`settle` (§6.0).** Settle a warning: it prints as `SETTLED` and no longer counts as
     open. Edit that block: the warning is open again. `settle` refuses a check that isn't
     raised.
   - **Round re-run (§6.3).** Run `bundle` → hand-written findings → `apply` for a key `K`.
     Run `bundle` again for `K`: the old findings, `.apply.json`, scan statuses and notes of
     those units are gone, and a second `apply` with new findings applies them.
   - **`apply` journal.** Use a fix whose `new` contains its `old`. Leave a journal in state
     `pending` with the English already written (as if `apply` died mid-unit), then re-run
     `apply`: the fix is applied exactly once. Edit the English after `bundle`: `apply`
     refuses the unit.
   - **Stale statuses (§5, §6.1).** A `skipped` translate status with no English produces
     `REDISPATCH`. `prep` on a unit that has an old `done` status for a missing English
     deletes it; `prep` on a translated unit with a `done` status leaves that status alone.
   - **Model pin (§8.4).** Statuses with `"model"` set to `claude-opus-5-5` and to
     `claude-opus-5-5[1m]` produce no WARN; any other model produces one.
2. **Validate and grade rounds.** `14a`, `15a`, edits to `14`, `15`, `boot.md`, SKILL.md
   *Review rounds* (with §6.3a) and *Resuming*. This removes call site #4 (the subagent
   re-check).
   *Test: an A/B run on identical input.* The old transcripts in a finished run don't work as
   a baseline: they judged round-1 English, and the run's English has since taken every later
   fix. Instead:
   - Make a copy with `--english-from pre-validate`.
   - Pick 5–6 units: the shortest, the longest, the one with the most round-1 significant
     findings, and a Greek unit if a Greek run exists.
   - **Old path (A):** `validate.py --report-only --units … --log-dir run/logs/ab-old` in the
     copy. The headless path still exists at this step, so A and B see the same English,
     config and model.
   - **New path (B):** `bundle --phase ab-new` plus scan agents for the same units.
   - The finished run's own `logs/validate/` round-1 transcripts are a second A sample. They
     show how much the old path varies from one run to the next.
   - Compare per unit: score, the number of findings and significant findings, the overlap of
     significant loci, and the `check-findings` rejections B needed. **Pass:** B's score and
     significant count fall within the A–A spread, and every significant finding *both* A
     runs found is in B, or a review of the miss shows it's a false positive. Repeat for
     grade with `grade --phase ab-new`.
   - Then run one full round, scan → apply → review, on 2 packets of the copy to exercise
     statuses, merge and resume (kill an agent mid-wave, then resume). Resume once at
     `review_step=apply` and check that `pre-<K>` was not retaken: the reviewers' diff still
     shows the auto-fixes. Then run the same round key again from step 1.
   - Every B status records `"model": "claude-opus-5-5"` (§8.4).
3. **Translate and the configure trial.** `13_translate.md`, configure edits, SKILL.md
   *Translate*. This removes call sites #1 and #3.
   *Test (scratch copy):*
   - Pick 3 units: the shortest, the longest (to exercise appends and `MODE=retry`; kill
     its agent once mid-unit), and one with held lines or a header lemma.
   - Run `prep --force --after-review --units …`. The moved files in
     `run/translate/replaced/` are the old path's translations and become the baseline.
   - Dispatch the translate agents, then compare each unit with its baseline: identical
     header, heading and held lines; the same block count; mark counts per block; the per-block
     length ratio (a systematic rise means padding, see §6.1); and `--structure-only`.
   - Read 2–3 blocks per unit side by side to judge quality.
   - Separately, on a fresh copy with `configure` and `translate` reset to pending
     (`state.py phase`), run the §6.2 trial loop end to end.
4. **Remove the headless path** (§7) and update the docs. Run
   `grep -rn "claude -p\|dangerously\|call_claude"` over the skill; it must return nothing.
5. **Optional, VulnHunter-style:** move the long orchestrator procedures (review rounds,
   convergence, R8, translate) out of SKILL.md into `orchestrator/*.md`, read only when that
   phase is reached. This keeps the orchestrator's starting context smaller.

## 12. Open questions

1. **Scan granularity.** This spec scans **per unit** to match today's per-call validator
   exactly. Per-packet scans would cut agents roughly 5×, at the cost of a scanner seeing several
   units. Easy to change later: `bundle` and `check-findings` are per unit either way.
2. **Old-round compatibility** (§10): finish the round the old way, or restart its scan? I
   recommend restarting.
3. **Translator doubts:** this spec keeps them in notes only (merged into
   `uncertain_readings.md`, shown in the report), not in the ledger, since no later phase settles
   ledger doubts. Confirm.

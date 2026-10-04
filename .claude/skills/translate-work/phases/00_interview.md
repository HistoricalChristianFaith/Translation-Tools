# Phase 00: Interview (read by the ORCHESTRATOR)

Goal: know **what** to translate, **where** its workspace lives, **which** base text, witness and
oracle to use, and get the user's **approval of a plan**. The interview ends with the line
"Plan approved", after which the autonomous run begins.

Use `AskUserQuestion` for every discrete choice. It pauses until the user answers. Put the
recommended option first, with " (Recommended)" appended to its label. The user can always type
a free answer through "Other". For open-ended input (the name of the work), ask in plain text
and **end your turn**; continue when the user replies.

Keep your own messages short: one screen at most.

---

## Step 1: Target work

- If the invocation argument names a work (e.g. `/translate-work Origen, Homilies on Numbers`),
  use it.
- If it is a path to an existing folder (typically quoted, e.g. `/translate-work "/Users/…/Origen
  of Alexandria/Homilies on Numbers"`, as the context-budget pause prints it), strip the
  surrounding quotes, keep the spaces, and use it as `WORK_DIR`: skip Step 2.1–2.2 and go
  straight to Step 2.3 (resume detection). Always quote it in commands (`W` already does).
- Otherwise ask in plain text:

  > Which work should I translate? Give the author and title (e.g. *Origen, Homilies on
  > Numbers*; *Jerome, Commentary on Ecclesiastes*). Mention anything you already know: a
  > particular edition, a GitHub issue, a partial workspace.

  End your turn.

Normalize the answer to `<Author>` and `<Work>` folder names in the style of the
repository you'll use (e.g. `Origen of Alexandria` / `Homilies on Numbers`). If an author folder
already exists, reuse its exact spelling.

## Step 2: Workspace location, and resume detection

1. Look for a works root. Check, in order:
   - a folder named `Writings-Database-Non-English` in the current directory, its parents, or
     `~/Desktop`;
   - otherwise `<cwd>/works`.
2. Ask (`AskUserQuestion`, header "Workspace"):
   "Where should the workspace for <Work> live?"
   - `<root>/<Author>/<Work>` (Recommended)
   - `<cwd>/works/<Author>/<Work>` (if different)

   Set `WORK_DIR`.
3. **If `${WORK_DIR}/_source/run/state.json` exists:** run `T/state.py show W`, then ask (header
   "Resume"):
   - Resume from `<next phase>` (Recommended)
   - Show status only (then stop)
   - Start over (moves `_source/run` to `_source/run.old-<timestamp>`; page images and staged
     sources are kept)

   On **Resume**, jump to *Resuming* in `SKILL.md`. The interview is over.
4. **If `WORK_DIR` already contains a filled `LATIN/` or `GREEK/` folder but no state:** tell the
   user, and ask (header "Existing text"):
   - Adopt it as the verified base and start at translation (Recommended if the project's reports
     say the base is final)
   - Rebuild the base from scratch (moves the existing folder to `_source/previous-<LANG>/`)
   - Abort

   **Adopt** needs a manifest. Initialize state (Step 3), then dispatch `PHASE=structure
   ASSIGNMENT=assemble MODE=adopt`. It builds the manifest from the existing files, with no scouting and no
   scaffolds. Then mark `stage`, `normalize`, `B`, `R2`, `R4`, `R1`, `R3`, `R5`, `R6`, `R8`,
   `convergence` and `R7` as `skipped` with `--note "adopted existing base"`, and continue at `configure`. (If page
   images are also missing, `structure` in adopt mode still works: it indexes no images and sets
   `base_images` to an empty index. Mention that `--images` won't be available.)

## Step 3: Initialize state and run the survey

```
T/state.py init W --work "<Author>, <Work>"
T/state.py phase W survey in_progress
```
Create `${SRC_DIR}/incoming/base/`, `${SRC_DIR}/incoming/oracle/` and
`${SRC_DIR}/incoming/witness/`.

Ask first (header "Your files"): "Do you already have files for this work: a base edition, an
oracle translation, a witness?" [No: find sources for me (Recommended) / Yes: I'll drop them in
now]. On Yes, give the three folders (base/ = the text to translate from, oracle/ = a modern
translation, witness/ = another edition), pause [I've added them / Never mind], and `ls` them.

Dispatch **one** survey agent (prompt template in `SKILL.md`: `PHASE=survey ASSIGNMENT=survey`,
plus `MODE=user-files` if the user dropped files in). While it works, tell the user in one line that you're surveying editions and
translations online.

When it returns, check `${RUN_DIR}/status/survey/survey.json` (status done) and read
**`${RUN_DIR}/survey.json`**. It is compact by design; you may read it.

## Step 4: Present the survey

Show the user a summary of at most 12 lines: how the work survives, the unit count, existing
English translations (mention public-domain excerpt collections briefly), the best base
candidate with its public-domain status and download test, the witness candidate, the oracle
candidates, and any hazards. Then, **if `copyright_bases` is non-empty**, list each one on its own
line with its exact `citation` (and its `volumes`, for a multi-volume edition), marked "(the
oracle's text)" if `oracle_tracks`, plus its `advantage`: these are editions we can translate from
if the user obtains a copy. They don't count toward the 12 lines. Mention that the full survey,
with search strings for each copyright edition, is in `_source/run/survey.md`.

**If `existing_english` contains a public-domain translation with `coverage` `complete` or
`most`:** ask first (header "Existing
English"): "A public-domain English translation already exists (<citation>). Continue with a
fresh translation anyway?" [Continue / Abort]. On Abort, mark `survey` done and stop.

**If `base_candidates` is empty because no public-domain edition can exist** (e.g. a work
discovered after ~1930 whose only editions are in copyright): explain this, and offer (header
"No PD base") [Supply a modern edition myself (I'll drop it in) / Abort]. A user-supplied modern
edition is staged exactly like a user-supplied base, below (give the exact names from
`copyright_bases`, as for a chosen copyright base). Record
`T/state.py set W base_license=copyright` and warn that the result is a translation of a
copyright edition, which the user must clear themselves.

## Step 5: Base text

Ask (header "Base text"): "Which base text should I build the <language> text from?". Options
(4 at most):
- the recommended candidate: `<citation> — <source>, download OK` (Recommended);
- if `copyright_bases` is non-empty, the best one (prefer `oracle_tracks: true`):
  `<short citation> (copyright): I'll obtain it`, its `advantage` as the description; the
  others stay reachable through "Other";
- 1 other public-domain candidate (2 if there's no copyright base);
- "I'll supply the base myself".

**If the user chooses a copyright base** (from the list, or by naming one through "Other"):
1. Give them the entry from `copyright_bases` in full: the exact `citation`, the `volumes` with
   the units each one holds, the `pages`, its `search` strings and `where` to look. Add what makes a
   copy usable: page images (a scanned PDF; with a text layer if possible), every volume, the work's
   whole page range.
2. Tell them this run then translates a copyright edition: the Latin/Greek stays in the
   git-ignored `_source/` and is never committed, and clearing the rights to publish the
   translation is up to them.
3. Continue with the drop-in steps below (folder `_source/incoming/base/`). Once the files are
   there, record `T/state.py set W base_license=copyright` along with the rest of the base.

**If the chosen candidate failed the download test, or the user supplies it (copyright bases
included):**
1. Tell the user exactly what to look for, using the survey's `user_sourcing_hints` (or the
   chosen `copyright_bases` entry): title,
   editor, year, series/volume, pages, likely sites and search terms. Tell them to put the
   PDF / images / zip into **`<WORK_DIR>/_source/incoming/base/`**.
2. Pause (header "Base drop-in"): [I've added it / Skip: search again with my hint (use Other
   to give the hint) / Abort].
3. On "added": `ls` the folder. For a PDF, run `T/pdf_pages.py info <file>`. If nothing usable
   is there, say so and ask again.
4. On a new hint: write it to `${RUN_DIR}/assignments/survey/survey.md` (heredoc) and
   re-dispatch the survey agent with `MODE=re-search`, then return to Step 4.

Record: `T/state.py set W base=<short citation> base_id=<id> base_source=archive|incoming language=<Latin|Greek|…>`.

## Step 6: Secondary witness

If the survey recommends a downloadable public-domain witness (another edition of the same text:
Migne, Lommatzsch, Cramer, …), include it in the plan by default and let the user remove it at
Step 8. If none exists, `R1` will be skipped. The user can also drop one into
`_source/incoming/witness/`.

## Step 7: Oracle

Explain in one or two lines: an *oracle* is a published modern translation, used only to detect
problems (source-text pass R3) and to grade our English. It's usually in copyright, so you can't
download it and the user has to supply it.

Ask (header "Oracle"): "Can you supply a copy of an oracle translation?" Options:
- `<best oracle citation>`: I'll drop it in (Recommended);
- `<second oracle>`: I'll drop it in (if any);
- No oracle: skip R3 and grading (weaker quality control).

If the user will drop it in, tell them the folder **`<WORK_DIR>/_source/incoming/oracle/`**
(a PDF with a text layer is best). Pause (header "Oracle drop-in"): [I've added it / Skip the
oracle after all].

Check it with `T/pdf_pages.py info <file>`. If there's no text layer, tell the user and ask
[Use it anyway: R3 will read page images; grading will be skipped / Skip the oracle].

Record: `T/state.py set W oracle=<short citation>` (or `oracle=null`).

## Step 8: Plan approval

Estimate the agent count:

```
packets ≈ max(1, units)   when units ≤ 25, else ≈ pages / 10
agents  ≈ 1 (survey) + 2 (stage) + 1-5 (structure)
        + packets × (B + R2 + R4 + R1? + R3? + convergence ≈ 1.5 rounds)
        + 1 (normalize, if a text layer) + 1 (seams) + 1 (R5) + 1 (R6) + 1-3 (R8) + 1 (configure)
        + batches × (1 translate + 2 validate scans + 1 if oracle) (full per-unit phases)
        + ≈ batches × 1.5 (later rounds' scans, on changed sets)
        + packets × (2 + 1 if oracle) (first review rounds) + ≈ packets × 1.5 (later rounds, rechecks)
        + 1 (report)
batches ≈ ceil(units / 6)   (per-unit phases dispatch runs of up to 6 consecutive units per agent)
```
Use the unit and page counts from the survey.

Show a plan of at most 15 lines:
- the work;
- the base (and how it is obtained);
- the witness;
- the oracle;
- the expected language directory;
- the passes that will run and which are skipped: `normalize` runs if the base has a text layer
  (a clean born-digital one → a light Pass B; confirmed by the normalize phase); `R8` checks the
  doubts left after R6 against the other sources the survey found (name them, e.g. the
  digitized manuscript, or "none: page image and oracle only"); the English is then checked in
  2–5 validation rounds against our source and 1–3 grading rounds against the oracle, repeated
  while a round still makes substantive fixes;
- the estimated agents;
- where the result will be (`<WORK_DIR>/english/`);
- that the run spans sessions: at ~400k tokens of my context I stop at a safe point and ask you
  to `/clear` and re-run `/translate-work "<WORK_DIR>"` (change it with
  `T/state.py set W context_threshold_k=<n>`);
- that `_source/` holds the workspace (and will be git-ignored).

Then **one** `AskUserQuestion` call with these questions:
1. (header "Plan") "Approve this plan?" [Approve (Recommended) / Remove the secondary witness /
   Abort]
2. (header "Autonomy") "How often should I stop for you?"
   - Checkpoints: decisions batched between phases (Recommended)
   - Guided: also after staging, variants, configure and before the report
   - Autonomous: only when blocked; decisions take my recommendation
3. (header "Page images") "During translation, let the model open page scans when a reading
   looks doubtful?" [No: text only (Recommended) / Yes: slower]
4. **Only if WORK_DIR is inside a git repo** (`git -C <dir> rev-parse` succeeds): (header
   "Commits") "Commit the text after each phase?" [No (Recommended) / Yes]

Then, if `survey.json` → `anticipated_decisions` is non-empty, a second `AskUserQuestion` call
(header "Conventions") with up to 4 of them (recommended option first); more → another call.
Asking now saves a stop at stage, structure or configure. Record each answer as a resolved
decision: `T/decisions.py add W --phase plan --packet interview --question … --option … --recommended …`,
then `T/decisions.py resolve W --id <printed id> --choice "<label>"`.

Record everything:
```
T/state.py set W autonomy=<checkpoints|guided|autonomous> translate_images=<true|false> auto_commit=<true|false> witness=<citation|null>
```
If the user asked to change something (via "Other"), adjust and show the plan again.

**Git ignore:** if `WORK_DIR` is in a git repo and `git check-ignore -q "<WORK_DIR>/_source/x"`
fails, append the relative path `<.../_source/>` to that repo's root `.gitignore` and tell the
user in one line.

Mark `T/state.py phase W survey done`, and say **"Plan approved"**, followed by one line saying
the run is starting with staging. Then continue with phase 1 (`stage`) in `SKILL.md`.

# Spec: `/format-as-html` — publish a translated work as a Writings-Database HTML fragment

Status: **implemented (v1, 2026-10-07)**: `SKILL.md`, `tools/`, `templates/`, `tests/` (16 tests
passing). This spec stays as the design record; §14 lists where the implementation departs from it.
The review's findings are in §13; the decisions on the open questions are in §11.

## 1. Why

Every finished translation so far has been published by a one-off script in
`~/Desktop/Scripts/` (17 of them, e.g. `build_jerome_obadiah_html.py`). A survey of all 17 found:

- **Three generations that drift apart.** Gen 1 (Jul–Sep: homilies, fragments, Peri Pascha) puts a
  highlight.js `<script>` on line 1, uses "Origen, …" in `<h1>` and has no `<article>`. Gen 2
  (Origen Psalms) uses `<br/><br/>`. Only Gen 3 (the Jerome scripts, Oct) matches the current
  house format.
- **Heavy copy-paste.** Header/body splitting, `html.escape`, quote nesting (4 copies), the
  footnote engine (3 copies), leftover-mark checks, the CLI. Fixes landed in one copy only: a
  greedy header regex, the `[[…]]` lemma guard, a dead `⟨⟩` check, unescaped `<h1>`.
- **Mark meanings conflict between works.** `»«` became `"` in the Origen scripts but `<i>` in
  Isaiah and Obadiah.
- **The work-specific part is small.** It's heading forms, mark meanings, what to drop, the
  source-note text, coverage rules and a few named exceptions.

The skill replaces the scripts with **one tested renderer, driven by a small per-work config**.
The config is drafted from what the work folder reliably contains, and the model's judgment goes
only into the choices that need it.

### 1.1 What the work folder reliably contains (verified 2026-10-06)

| Need | Reliable source | Not reliable |
|---|---|---|
| unit list, order, passage, pages | `_source/run/manifest.json` → `units[]` (`n`, `file`, `label`, `passage`, `pages`) | — |
| English text | `english/*_english.txt`: `#` header lines, a `====` rule, blank-line blocks (written by `translate.py assemble`) | the header's wording comes from each run's `english_header()` and varies between works |
| printed heading block to drop | the **first block** of each English file (an all-caps rubric or a parenthesized label) | `HEADING_EN` / `LABEL_EN` in `work_config.py`: per-work extras, not in the template and not read by any tool; present in 3 of the 6 runs |
| work title, author | `work_config.py` → `AUTHOR`, `WORK` (template fields, present in all 6 runs) | — |
| base, license, oracle | `_source/run/state.json` → `base`, `base_license`, `oracle` | — |
| mark meanings | the run's `TRANSLATION_RULES` (prose), read by the model | there is no machine-readable mark table |
| editorial decisions | `_source/run/decisions.jsonl` | — |

## 2. Scope

**In:**
- Works translated by `/translate-work` (`english/` + `_source/run/`), the primary case.
- Works with the same English layout but no run state (older runs): drafted from the English files
  alone (§5.2).
- Output to the Writings-Database repo: one consolidated file (default) or a folder of files
  (§5.3).
- Replacing an existing HTML file at the same path, after a diff and a drift check (§6, steps 6–7).

**Out:**
- Regenerating already published Gen 1/Gen 2 HTML. **Decided: no** (§11). `check_html.py` may
  still *audit* any file read-only.
- Editorial Markdown sources (Peri Pascha) and the old chunk formats (`== §N ==`).
- Any change to the translation itself. The skill renders and never edits wording.
- Committing, or offering to commit. **Decided** (§11).

## 3. Design principles

1. **Deterministic renderer, judgment only in the config.** Python does all parsing, rendering and
   checking. The model drafts the config, explains it and asks the user; it never hand-writes HTML.
2. **Prove fidelity with a transform log** (§8 `fidelity`). Every change the renderer makes to the
   text is logged (a dropped block, a stripped prefix, a mark converted, a quote straightened, a
   note moved). Replaying the log on the source must give exactly the output text, and any change
   that isn't logged fails.
3. **Build and check everything before writing anything.** Writing is a separate, explicit step.
4. **Never overwrite blind.** Diff against the existing file, and refuse to overwrite hand edits
   silently (§6 step 6, drift check). Keep the filename, since other repos cite it by URL.
5. **The config is the record, if it's kept.** It lives at `WORK_DIR/html_config.py`, next to
   `english/`. If either is untracked in git, the report says so (§6 step 8).
6. **Portable.** This repo is public (GitHub `HistoricalChristianFaith/Translation-Tools`): no
   user paths in the skill. The output location comes from an interview (§5.4).
7. **Same conventions as translate-work:** `GATE <tool>: PASS|FAIL (n)` last lines, exit codes,
   zsh-safe commands.

## 4. Layout

```
.claude/skills/format-as-html/
├── SKILL.md                 entry point: the procedure in §6 (written at implementation)
├── SPEC.md                  this file
├── tools/
│   ├── htmlkit.py           shared library (§7)
│   ├── build_html.py        CLI: --work-dir W [--out P] (check + preview)  |  --write  |  --diff
│   ├── draft_config.py      first html_config.py from manifest, English files, state + census
│   ├── check_html.py        house-format + fidelity checker; read-only audit of any file
│   └── mark_census.py       mark characters (§8 census), block openers, header labels per unit
├── templates/
│   └── html_config_template.py
└── tests/
    ├── fixtures/            SYNTHETIC English units only (no real translations: §13 F14)
    ├── legacy_scripts/      frozen copies of the Gen 3 scripts, for differential tests
    └── test_build.py
```

`build_html.py` with no action flag only builds, checks and prints the summary and gates. `--diff`
adds the comparison with the existing file. `--write` writes, and only after every gate passes.

## 5. The per-work config (`WORK_DIR/html_config.py`)

A plain Python module (like `work_config.py`), so it can hold a small function where a dict won't
do. It holds no absolute paths. Unset fields have the defaults shown.

```python
# --- where ---
SRC_GLOB      = "english/*_english.txt"         # relative to WORK_DIR; numeric sort on the unit number
OUTPUT        = {"mode": "single", "relpath": "Jerome/Commentary on Obadiah.html"}   # under OUTPUT_ROOT (§5.4)

# --- title, note, rights ---
H1            = "Commentary on Obadiah"         # escaped on render
SOURCE_NOTE   = "Latin source: … {pages} …"     # plain text with {pages} {cols} {base}; rendered as <i>…</i><br><br>
RELEASE       = None                            # "public-domain" appends the release sentence; see §8 rights
RIGHTS_CONFIRMED = False                        # must be True for RELEASE with a copyright base

# --- structure ---
DROP_FIRST_BLOCK = r"^(?:[A-Z][A-Z .,]+\.|\((?:Verses?|Chapter|Book) [^)]*\))$"   # must match, or the unit fails
CHECK_LABEL   = "passage"                        # the dropped label must agree with manifest passage
UNIT_HEADINGS = verse_heading(chapter=1)        # unit -> [(level, text)]; helpers in §7
BLOCK_LABELS  = None                            # in-body labels that open new headings (Isaiah), §5.1
STRIP_PREFIX  = [r"^\d+(?:[./]\d+)*\.\s+(?=\S)"] # applied to each block's start
KEEP_PREFIX   = []                              # exact (unit, block_index) pairs where a prefix is kept

# --- marks: every mark character found by the census must appear here ---
MARKS = {
    "*":  "italic",     # lemmata
    "»«": "italic",     # Scripture -> italic; were »« something else in this run: "quote"
    "“”": "quote",      # straight "…", nested quotes become '…'
}

# --- notes, coverage, exceptions ---
FOOTNOTES     = None    # or {"patterns": [...], "style": fn}: bracket notes -> two-way numbered notes
COVERAGE      = verse_coverage(first=1, last=21, parts="ab")   # or chapter tables, or None
EXCEPTIONS    = {}      # named and commented, e.g. {"order_exempt_units": [5]}

# --- written by the tool, not by hand ---
LAST_BUILD    = {"sha256": "…", "date": "2026-10-06"}   # hash of the last output written (§6 drift check)
```

**Marks rule (decided, §11 Q2):** `»«` is `italic` when the run's rules say `»«` marks Scripture,
and `quote` otherwise. The same applies to any other pair the rules call Scripture. A mark the model
can't place stays `None`, and the build stops until it's set.

### 5.1 Drafting from a translate-work run

| Field | Drafted from |
|---|---|
| `OUTPUT.relpath` | `<AUTHOR>/<WORK>.html`. If a file exists there, it's kept. If not, the user confirms the new name. |
| `H1` | `WORK` |
| `DROP_FIRST_BLOCK` | the first blocks of all units (census); the regex is tightened to what is actually there |
| `UNIT_HEADINGS` | manifest `passage` (`Obad 12-13a` → `1:12-13a`, `Isa 1:1-2:3` → no unit heading) plus the unit's first block; the *form* of an existing file's headings is matched, not its divisions |
| `BLOCK_LABELS` | proposed when the census finds labels inside units (`(Chapter 14 — Verses 1, 2.)`), with chapter inheritance and splitting of labels run into a paragraph, as in Isaiah |
| `STRIP_PREFIX` | block openers that repeat the unit's verse numbers |
| `MARKS` | **left `None` by the drafter.** The model fills them from `TRANSLATION_RULES` and the census, and quotes the rule next to each entry as a comment. Inferring mark meanings from prose isn't done in Python. |
| `SOURCE_NOTE`, `RELEASE` | a draft from `state.json` (base, license, oracle), decisions (names, Greek, apparatus) and the manifest page range. `RELEASE` stays `None` for a copyright base. |
| `COVERAGE` | the manifest passages |

### 5.2 Without run state

The inputs are only the census and the English headers. The drafter proposes the same fields and
marks every guess `# GUESS:` for the model to confirm with the user.

### 5.3 Folder mode

`OUTPUT = {"mode": "folder", "reldir": "...", "filename": fn}` writes one file per unit. Each file
gets its own `<h1>` (`H1` becomes a function of the unit) and the same `SOURCE_NOTE`. Gates run per
file and across files (unit numbering, no file left over from an earlier build in that folder
unless it's listed in `EXCEPTIONS`).

### 5.4 Output location: an interview

The output root is the folder of the Writings-Database repo. It is **not** the root translate-work's
interview finds (that one is `Writings-Database-Non-English`). `locate.py` lists candidate roots
(`$FORMAT_AS_HTML_ROOT`, the sibling of a `<X>-Non-English` ancestor, `Writings-Database*` folders
nearby or on the Desktop), keeps only those whose `CLAUDE.md`/`AGENTS.md` describes the fragment
format, and offers numbered options: replace the existing page, a new file, a new folder, or close
name matches. The model asks the user once, with those options as quick selects (`AskUserQuestion`,
"Other" for any path). The answer is stored in the work's own `html_config.py` (`OUTPUT.root`,
`relpath`). That file lives in the user's work folder, not in this public repo, so an absolute root
there is fine. The skill itself holds no user paths.

## 6. Procedure (what `SKILL.md` will say)

`/format-as-html <work>`, where `<work>` is a work folder path or "Author, Work".

1. **Locate.** Resolve `WORK_DIR` and `OUTPUT_ROOT`, and check that `english/` has one file per
   manifest unit. If `state.json` exists, `report` must be `done`; otherwise warn and ask whether to
   continue.
2. **Census.** `mark_census.py W` lists the mark characters with counts, the first block of each
   unit, any in-body labels, and the header labels.
3. **Config.** If `WORK_DIR/html_config.py` exists, use it (a re-run). Otherwise
   `draft_config.py W` writes it, and the model fills `MARKS` and the `GUESS` items.
4. **Ask the user once** (one `AskUserQuestion`, up to 4 questions), and only on a first build or
   where something changed:
   - the title, if an existing file's `<h1>` differs;
   - heading divisions, if they differ from the existing file's;
   - dropping anything that carries information (an incipit rubric, a mid-unit verse number);
   - **rights**: with a copyright base, whether to add the public-domain release sentence
     (`RELEASE`, `RIGHTS_CONFIRMED`).
   The full source note is shown for approval.
5. **Build and check.** `build_html.py W` prints the per-unit summary, advisories and every gate
   (§8).
6. **Diff and drift check.** `build_html.py W --diff` against the existing file:
   - **Drift:** if the existing file's hash ≠ `LAST_BUILD.sha256`, it was edited by hand after the
     last build, or was never built by this skill. Show those edits. This has already happened:
     the published Obadiah file differs from its script's output, because a sentence was removed
     from the note by hand and committed in `5297f22d`. Fold the edits into the config, or ask the
     user before overwriting them.
   - **Replacement vs re-render:** when the old file is a different translation (e.g. ChatGPT),
     show the heading list old → new and the word counts, not a paragraph diff.
7. **Write.** `build_html.py W --write`, only after the user approves (or immediately if the request
   already said to write). It runs `check_html.py` on the written file and updates `LAST_BUILD`.
8. **Report** in a few lines: the path, units, words, gates, what was dropped, open advisories,
   any rights note, and whether `english/` or `html_config.py` is untracked in git. Nothing is
   committed, and the skill doesn't offer to commit.

Re-running after a translation fix is steps 5–8 with the saved config.

## 7. `htmlkit.py`, the shared library

From the Gen 3 scripts, with the known bugs fixed:
- `read_unit(path)` → header, blocks (split on `^={5,}$` and blank lines, whitespace collapsed);
  errors name the file and quote a snippet.
- `render_inline(text, marks, log)` → escape first (`quote=False`), then convert marks with a
  stack that rejects nesting it wasn't told to allow; logs each change.
- `convert_quotes(text, log)` → depth nesting (`"` outer, `'` inner). An apostrophe (`’` between
  letters, or after `s` before a space or punctuation) is never treated as a quote.
- `footnotes` → the private-use placeholder engine: numbers 1..k in document order, two-way
  links, a trailing `<section class="notes"><hr>…</section>`; logs each moved note.
- Heading helpers: `verse_heading`, `book_heading` (Roman numerals → words), `homily_heading`.
  Block-label parsing with chapter inheritance and splitting of labels run into a paragraph.
- Coverage helpers: contiguous verses with `a/b` parts, chapter/verse tables, named exemptions.
- Greedy header regexes where titles nest brackets; `<h1>`/`<h2>` text is always escaped.

## 8. Gates (each ends `GATE <name>: PASS|FAIL (n)`)

| Gate | Fails when |
|---|---|
| `census` | a **mark character** in the source isn't in `MARKS` (marks: `* » « ‹ › “ ” ‘ ’ ⟨ ⟩ [ ] † ‖`, with `’` apostrophes excluded). Letters of any script (Greek, Hebrew, accented Latin), digits, dashes and the Origenian signs `÷ ※ ⁚` are reported as counts, never failures. |
| `structure` | units aren't contiguous; a first block doesn't match `DROP_FIRST_BLOCK`; a dropped label disagrees with its passage; a heading has no text under it; `COVERAGE` is broken |
| `marks` | an unpaired or unexpectedly nested mark; any source mark survives in the output; converted span count ≠ source span count |
| `house` | a tag outside the whitelist (`article h1 h2 h3 i b br sup a section hr span`); any `<p>`, `<html>`, `<head>`, `<body>`, `<title>` or `<script>`; more than one `<h1>`; unbalanced tags; paragraphs not `<br><br>`. The author's name in `<h1>` is only an **advisory**, since a title may contain a name legitimately. |
| `fidelity` | replaying the transform log on the source text doesn't give exactly the output text, or the output has a change that isn't in the log. The text is compared as one stream, so paragraphs split by `BLOCK_LABELS` or notes moved by `FOOTNOTES` are covered. |
| `notes` | footnotes aren't numbered 1..k in order, or a link isn't two-way |
| `rights` | `RELEASE` is set with `base_license=copyright` and `RIGHTS_CONFIRMED` is not `True` |

**Which house rules apply:** `Writings-Database/CLAUDE.md` (bare fragment, no `<script>`).
`Writings-Database/AGENTS.md` still says the opposite: put the highlight.js `<script>` in `<head>`.
That's where Gen 1 came from. The skill follows `CLAUDE.md`, and on its first run tells the user
that `AGENTS.md` is out of date (§13 F6).

## 9. Acceptance tests

The English for Isaiah, Philemon, Titus and Galatians no longer exists. Their `english/` folders
are empty and were never in git. So byte-for-byte reproduction of those published files can't be
tested. Instead:

1. **Differential tests (main proof).** Synthetic English units in each Gen 3 script's input format
   (verse sections with split `a/b` verses, books with in-body labels and a label run into a
   paragraph, footnote brackets, nested quotes) are run through the frozen legacy script
   (`tests/legacy_scripts/`) **and** through the new renderer with an equivalent config. The outputs
   must be byte-identical.
2. **Obadiah, real data (run locally, not in the public repo).** A config reproduces the output of
   `build_jerome_obadiah_html.py` byte for byte. It's compared with the script's output, not the
   published file, which carries a hand edit (step 6). The drift check must flag that edit.
3. **Negative fixtures.** An undeclared mark, an unpaired `»`, a missing unit, a label/passage
   mismatch, a dropped word, an unlogged change, and `RELEASE` with a copyright base and no
   confirmation must each fail the right gate.
4. **Read-only audit.** `check_html.py` on a Gen 1 file reports its violations (`<script>`, author
   in `<h1>`, no `<article>`) and writes nothing.

## 10. Integration with translate-work

- Standalone: `/format-as-html "<WORK_DIR>"` after a run reports `done`.
- Later, optionally, translate-work's report step suggests the command. No new phase is needed.
- The skill reads `_source/run/` and never writes there. Its config lives at `WORK_DIR/html_config.py`.
- Copyright hygiene carries over: the Latin/Greek never goes into Writings-Database, and the
  `rights` gate guards the release sentence.
- Writings-Database needs no registration for a new work: `<Author>/metadata.toml` is per author
  only (checked for Jerome).

## 11. Decisions (2026-10-06)

1. **Config location:** `WORK_DIR/html_config.py`, next to the English.
2. **`»«`:** italic when the run's rules say it marks Scripture, straight quotes otherwise (§5).
3. **Regenerate Gen 1/Gen 2 HTML:** no.
4. **Commits:** the skill never commits and never offers to.
5. **Interface:** just `/format-as-html <work>`.

## 12. Build plan

1. `htmlkit.py` with the transform log, plus `check_html.py`, with synthetic fixtures and the
   negative tests.
2. Differential tests against frozen copies of the Obadiah, Isaiah and Philemon/Titus scripts.
3. `mark_census.py` + `draft_config.py`, tested by drafting Obadiah's config and comparing it with
   the hand-written one; the Obadiah real-data check (§9.2) locally.
4. `SKILL.md` + template; first real run on the next finished translation.
5. Optional: the translate-work report hook.

## 13. Adversarial review: findings and how this revision answers them

| # | Finding (evidence) | Fix in this revision |
|---|---|---|
| F1 | The byte-for-byte targets can't be tested: the English for Isaiah, Philemon, Titus and Galatians is gone (empty `english/`, never tracked; their scripts exit "no source files") | §9: differential tests on synthetic fixtures through frozen legacy scripts |
| F2 | The published Obadiah file already differs from its generator (the note was edited by hand, commit `5297f22d`); a re-run would silently revert that edit | §6 step 6: drift check with `LAST_BUILD.sha256` |
| F3 | "The config is the record" assumed the English is tracked; Obadiah's `english/` is untracked and the others are lost | §3.5 + §6 step 8: report untracked `english/` / config |
| F4 | `HEADING_EN` / `LABEL_EN` were treated as pipeline outputs; they aren't in the template, no tool reads them, and only 3 of 6 runs have them | §1.1: draft from manifest `passage` and the English first block instead |
| F5 | "Find the root the way the interview does" finds `Writings-Database-Non-English`, the wrong repo; the spec also hardcoded `~/Desktop` paths in a public repo | §5.4: a location interview over the detected options; the root is stored only in the work's own config |
| F6 | The house rules contradict each other: `AGENTS.md` requires the highlight.js `<script>`, `CLAUDE.md` forbids it | §8: `CLAUDE.md` is the authority; tell the user `AGENTS.md` is stale |
| F7 | In-body sub-headings weren't modelled: Isaiah's units are books, and its lemma headings come from labels inside them | §5 `BLOCK_LABELS`, §7 helpers |
| F8 | Per-paragraph fidelity breaks with split blocks, moved footnotes, straightened quotes, stripped prefixes | §3.2/§8: one-stream fidelity via a transform log |
| F9 | `KEEP_PREFIX_IN` keyed by unit is too coarse (Obadiah's "14." is block 2 of unit 8) | `KEEP_PREFIX` keyed by (unit, block) |
| F10 | "Every non-ASCII character must be declared" would fail on Greek, Hebrew, accented names; `’` is both apostrophe and quote | §8 `census`: a fixed set of mark characters; apostrophe rule in §7 |
| F11 | Inferring mark meanings from `TRANSLATION_RULES` prose in Python is unrealistic | §5.1: the drafter leaves `MARKS` `None`; the model fills it and cites the rule |
| F12 | A rights gate that string-matches "public domain" in the note is fragile | `RELEASE` / `RIGHTS_CONFIRMED` fields; the sentence is rendered, not typed |
| F13 | Folder mode was named but undefined (per-file `<h1>`, stale files) | §5.3 |
| F14 | Test fixtures copied from real translations would put a translation of a copyright edition (CCSL) into a public repo | §4/§9: synthetic fixtures only; real-data check runs locally |
| F15 | "Author in `<h1>`" as a hard failure has false positives | advisory only |
| F16 | Paragraph diffs are useless when the old file is a different translation (the ChatGPT files) | §6 step 6: replacement mode shows headings and counts |
| F17 | Checked and fine: no per-work registration in Writings-Database; the old Obadiah file's Latin link was already dangling (`Jerome/Latin/` doesn't exist) | §10 note; no Latin link generated |

## 14. Implementation notes (v1, 2026-10-07)

- **Fidelity is an independent re-derivation, not a replayed log.** `render_inline` builds the HTML;
  `plain_expected` (separate code) computes the text the HTML must show from the same source
  paragraphs; `gate_fidelity` compares the two word streams, footnotes appended at the end. The
  structural drops (first blocks, stripped prefixes, labels turned into headings) are printed as the
  "dropped/stripped" list for review. A prefix that would remove a word fails `structure`. Quotes are
  compared normalized to `"`, so a wrong nesting depth is not caught by `fidelity` (the
  `test_quote_nesting` unit test covers the renderer).
- **Location:** the interview in §5.4 replaces the environment-variable chain.
- **Folder mode** renders and checks per file, but `LAST_BUILD` (drift detection) is recorded for
  single-file outputs only.
- **Mark modes** are `italic`, `quote`, `straight`, `strip`, `pass`. The `census` gate checks a fixed
  set of mark characters (`* † ‖ » « “ ” ‘ ’ ‹ › ⟨ ⟩ [ ]`); `’` apostrophes are told apart by
  position (inside a word, or a plural possessive with no `‘` open).
- **Verified on Obadiah:**
  - The skill's output with the old note is byte-identical to `build_jerome_obadiah_html.py`'s output.
  - With your hand-edited note folded into the config, it is byte-identical to the published page.
  - The drift check refused to overwrite the hand edit until the edit was folded in.
  - `<W>/html_config.py` holds the settled config and `LAST_BUILD`.


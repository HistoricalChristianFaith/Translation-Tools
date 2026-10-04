# Translating patristic texts with an LLM: the process

This document describes the workflow used to produce fresh, public-domain English translations of
five works of Origen of Alexandria (August–September 2026). Earlier works (Judges, Isaiah, Luke)
used earlier, less developed versions of the same workflow; these five are where it settled.

| Work | Survives as | Base text | Units |
|---|---|---|---|
| *Homilies on Exodus* | Rufinus's Latin | GCS 29 (Baehrens 1920) | 13 homilies |
| *Homilies on Leviticus* | Rufinus's Latin | GCS 29 (Baehrens 1920) | 16 homilies |
| *Homilies on Psalms 36–38* | Rufinus's Latin | Migne PG 12 (no PD critical edition) | 9 homilies + preface |
| *Commentary on Ephesians* | Greek catena fragments | Gregg, *JTS* 3 (1902) | 37 fragments |
| *Commentary on 1 Corinthians* | Greek catena fragments | Jenkins, *JTS* 9–10 (1908–09) | 90 fragments |

The goal is for someone else to be able to repeat it on a new work. The short version:

> **First build a verified source-language text from the printed page images, in many small,
> logged, independently checked passes. Then translate it one unit per LLM call inside
> deterministic scaffolding. Validate the English against that source. Grade it against a published
> translation.** The end product is one plain-text English file per unit.

Most of the effort, and most of the quality, is in the first half. The translation step is almost
the easy part.

> **Automated version:** the `/translate-work` Claude Code skill
> ([`.claude/skills/translate-work/`](.claude/skills/translate-work/README.md)) runs this whole
> process. It interviews you (work, base text, oracle), surveys sources online, then orchestrates
> subagents through every phase below and pauses only for editorial decisions. This document
> describes the method the skill encodes; read it to understand or audit what the skill does.

**What's in this repo**

| Path | What |
|---|---|
| `TRANSLATION_PROCESS.md` | This document |
| `.claude/skills/translate-work/` | The `/translate-work` skill: orchestrator, phase files, tools |
| `tools/` | (symlink into the skill) Generic, config-driven tools: `translate.py`, `validate.py`, `grade.py` (they prepare the bundles the skill's translate / validate / grade subagents work from, and check what those agents write; they never call a model), plus base-text helpers `base_check.py` and `strip_anchors.py` |
| `tools/work_config_template.py` | Commented template for a new work's config |
| `examples/configs/` | Configs of the Leviticus and 1 Corinthians runs (settings reference for `tools/`) |
| `examples/original-scripts/` | Verbatim snapshots of the per-work scripts actually used (Leviticus, 1 Corinthians), plus some per-project base-text helpers |
| `examples/pass-prompts/` | Real prompts and subagent briefs used for base-text passes B, R1, R2, R3 and R4 |
| `examples/source-workspace/` | Two real `_source/README.md` planning docs and two pass reports |
| `templates/` | Skeletons for a new work's `_source/README.md` and for a pass prompt |

---

## 1. Principles (the rules everything else follows)

1. **Never translate from OCR.** First establish a *base text*: a transcription from the page
   images of a public-domain edition, verified until another full pass changes nothing substantive.
2. **The printed page image is the ground truth.** OCR, a second edition, and a modern
   translation are all *detectors*. They point at places to look. Every decision is made by
   looking at the image.
3. **Each question has exactly one arbiter.**
   - Is the base text right? → the page image.
   - Is the English faithful? → *our* base text (the validator).
   - How close is the English to the published scholarly sense? → the oracle translation (the
     grader, which is read-only and advisory).
4. **Copyright oracles are consulted, never copied.** Modern translations (FOTC, OECS, and so on)
   are staged locally in a git-ignored folder. Prompts may quote a few words to name a
   discrepancy, and nothing more.
5. **The model never touches structure.** Scripts parse headers, unit numbers, headings and
   editorial notes deterministically and hold them aside. The model sees only translatable blocks.
   Every reply is checked against a structural fingerprint (the block count).
6. **Every pass fixes in place, logs to a named report, and leaves the checker clean.** The base
   text and the English are under git, so each pass is a reviewable diff.
7. **Translate what the source says, as it says it.** That means the author's own Scripture
   wording and numbering (LXX Psalms, "Kingdoms"). No harmonising to a modern Bible, no
   "improving" the exegesis, no filling of printed lacunae.
8. **Settled decisions are written down and fed forward.** Every crux resolved in a pass report
   becomes a "do not re-flag" line in the translator, validator and grader prompts. Nothing gets
   relitigated.

---

## 2. Layout: repositories and folders

```
Writings-Database-Non-English/<Author>/<Work>/     source-language repo (GitHub: HistoricalChristianFaith)
├── LATIN/ or GREEK/        the verified base text, one file per unit    (git-tracked)
├── english/                the English translation, one file per unit   (git-tracked)
└── _source/                the workspace                                (git-ignored)
    ├── README.md           project plan: witnesses, passes, conventions, status
    ├── <edition>_pages/    rendered page images (the ground truth)
    ├── *_djvu.txt, page_numbers.json, scandata.xml   OCR + page→leaf maps
    ├── oracle_<name>.pdf   copyright English translation (local only)
    ├── passB_final/        mirror of the running text (Latin projects)
    ├── pass*_prompt.md     the prompt used for each pass
    ├── <pass>_report.md    one report per pass (boundary_audit, recollation_pass, variants_*,
    │                       oracle_discrepancies, consistency_pass, apparatus_pass, anchor_strip)
    ├── uncertain_readings.md   running convergence log (OPEN / RESOLVED / NOTE)
    └── scratchpad/         per-project helpers (validate.py, assemble.py, r7_strip.py, OCR seeds, crops)

Scripts/                    per-work pipeline scripts (translate_*, validate_*, grade_*)
                            and their logs (validation_logs_<work>/, grading_logs_<work>/)
```

**Base-text file format** (all five works). `#` provenance lines, then a `====` rule, then the body.
**Every paragraph is exactly one physical line.** The scripts depend on this.

```
# Origen, Homilies on Leviticus — Homily 2 (Lev. 4 ...).
# ... (source, edition, pages, scripture note)
============================================================
HOMILIA II.
*De sacrificiorum ritu, ...*
1. Superior quidem de principiis Levitici disputatio ...
2. Et primo velim videre, quae sit ista differentia ...
```

A catena fragment keeps its metadata in the header instead:

```
§ XI  |  1 Cor. ii 12–15
[Cramer 46–48]
LEMMA: [Ἡμεῖς δὲ οὐ τὸ πνεῦμα τοῦ κόσμου ἐλάβομεν ...]
====================================================================
[Ὠριγένους]
Κατανοήσωμεν *τὰ ὑπὸ τοῦ θεοῦ χαρισθέντα ἡμῖν*· ...
```

---

## 3. Tooling prerequisites

- **Claude Code** (`claude`). Everything runs in one interactive session with subagents: the
  base-text passes, and translate, validate and grade too, one subagent per unit between two
  deterministic tool steps (prepare a self-contained bundle; check the file the agent wrote).
  No headless `claude -p` call and no `--dangerously-skip-permissions`. The model is pinned to
  Opus 5.5 in the project settings (the orchestrator on `claude-opus-5-5[1m]`, every subagent on
  `claude-opus-5-5`). The per-work scripts in `examples/original-scripts/` ran these phases
  headlessly, one `claude -p` call per unit; that is the method described in §§6–8, which the
  skill keeps.
- Python 3 with Pillow (crops, image conversion). PyMuPDF helps with oracle extraction.
- poppler (`pdftotext`, `pdftoppm`), OpenJPEG (`opj_decompress`), tesseract (optional, rough OCR
  seeds only).
- git for every tracked tree.

---

## 4. Phase 0: choose the base and stage the sources

Start by writing `_source/README.md`. Template: `templates/source_README_template.md`; real
examples: `examples/source-workspace/`. It records:

- **The source survey.** How the work survives, which editions exist, and which are public
  domain. A table of *Edition / Year / PD? / Role*. The base must be public domain. A modern
  critical edition that is still in copyright is "reference only".
- **Witnesses in priority order:**
  1. The base edition.
  2. Its page images.
  3. An independent secondary witness (Migne, Lommatzsch, Cramer's *Catenae*).
  4. The English oracle (copyright).
  5. Any extra public-domain apparatus (e.g. Turner's notes on 1 Corinthians).
- **The pass list, editorial conventions, deliverable filenames, and a Status line.** Keep the
  Status line current as passes finish.

Then stage (Pass 0):

- **Page images.** For archive.org items, fetch the `_jp2.zip` (or a single member via the
  zip-member URL `.../<item>_jp2.zip/<item>_jp2%2F<item>_<NNNN>.jp2`). Decode with
  `opj_decompress`, convert with PIL `convert('RGB')`, and save JPEG at **native resolution**.
  For PDF items use `pdftoppm -r 300..400 -jpeg`. The old `BookReaderImages.php` endpoint 404s and
  IIIF `full/full` 504s under load, so render locally.
  Name the files by printed page, e.g. `gcs29_p<PAGE>_leaf<LEAF>.jpg`,
  `pg12_col<ODD>-<EVEN>_leaf<L>.jpg`, `jenkins_pt<PART>_p<PAGE>_leaf<NNNN>.jpg`.
- **Printed page → leaf map** from `page_numbers.json` / `scandata.xml`. **Offsets drift.** GCS 29
  goes +49 → +72 across the volume. Scans duplicate pages. Cramer vol. V jumbles pp. 150–163.
  So **always glob by printed page and never compute a leaf** unless the offset has been verified
  at both ends.
- **OCR.** Keep the full `_djvu.txt` and a slice for the work. Latin GCS OCR is a usable
  first draft. Migne Latin OCR and 1900s polytonic Greek OCR are **structure only** (finding
  boundaries and section numbers), never text.
- **Boundaries verified on the images.** First incipit, last explicit, every seam between
  volumes, issues or parts.
- **The oracle PDF**, dropped in manually as `oracle_<translator>_<series>.pdf`. It is copyright
  and stays git-ignored.

Record source quirks durably (wrong archive items, offset glitches). Several items listed in
project notes turned out to be undownloadable; a working substitute had to be found and written
down.

---

## 5. Phase 1: establish the base text (the refinement passes)

### 5.1 The passes

Order as settled: **A → B → R2 → R4 → R1 → R3 → R5 → R6 → R7**.

| Pass | Purpose | Lens (detector) | Arbiter | Report |
|---|---|---|---|---|
| **A** Extract & structure | Split the OCR into units; build the manifest (unit → passage → pages → anchors); scaffold headers | OCR | image | `passA_report.md`, `boundary_audit.md`, manifest |
| **B** Image transcription | Transcribe every unit directly from the page images, with `[p.N]` anchors at every page or column turn | — | image | `passB_report.md` |
| **R2** Lensless re-collation | A fresh reader re-reads *everything* word for word against the images, with no other witness open | none | image | `recollation_pass.md` |
| **R4** Boundary & completeness | Every unit's start and end, shared pages, seams, every page anchored once, section numerals | (oracle as tripwire only) | image | `r4_boundary_audit.md` |
| **R1** Secondary-witness cross-check | Collate against an independent edition; every divergence is a signal | Migne / Lommatzsch / Cramer | image | `variants_<witness>.md` |
| **R3** Oracle back-check | Sentence by sentence against the English oracle, looking for meaning-level slips | oracle translation | image | `oracle_discrepancies.md` |
| **R5** Consistency & conventions | Single-editor uniformity: orthography as printed, marks, anchors, lemma per unit, embedded Greek; build the unit → passage table | — | image | `consistency_pass.md` |
| **R6** Apparatus / variant pass | A narrow pass over the residual cruxes: emend or record | apparatus, witness, corpus | image + evidence | `apparatus_pass.md` |
| **R7** Anchor strip | Remove every page anchor, touching nothing else: the clean reading text | — | byte checks | `anchor_strip.md` |

A single file, `uncertain_readings.md`, runs across all passes. Every doubt is logged there as
OPEN, and later resolved or documented. **The base is "final" when a complete pass produces no
substantive diff.** Then it graduates to translation.

Variants of the pipeline:

- **No usable OCR** (Migne Latin, polytonic Greek): skip Pass A's text extraction. Pass B *is*
  the origin of the text. Lean harder on R2.
- **Fragment collections** (catenae): the spine is the editor's numbering (§ I–XC) plus each
  fragment's lemma. The main completeness risk is a fragment dropped at a seam between journal
  parts, which is what R4 is for.
- **Different lenses per work:**
  - R1: Migne for GCS-based works; Lommatzsch when Migne is the base; Cramer for the catenae.
  - R6: Baehrens's apparatus, Gregg's or Jenkins's apparatus, Turner's notes; with no apparatus,
    a "corroboration test".

### 5.2 How a pass is actually run

Each pass is **one interactive Claude Code session**, started from a written prompt saved as
`_source/pass<ID>_prompt.md`. Template: `templates/pass_prompt_template.md`. Real ones:
`examples/pass-prompts/`. The prompt always spells out:

- what the pass **is and is not**, with neighbouring passes' jobs explicitly excluded;
- **what to read first**: the README (its conventions override defaults), the previous pass's
  report, `uncertain_readings.md`;
- **the arbiter**: the image, globbed by printed page;
- **inputs and tooling**: which files to edit, which validator must stay clean, which scripts
  *not* to run;
- **carry-forward items** from the previous report;
- **discipline**: fix only what the image proves; never restructure silently; don't start the
  next pass;
- **definition of done**: validator clean, report written, `uncertain_readings.md` updated,
  commit made, then stop.

Inside the session the main loop acts as **orchestrator**. It fans out **one subagent per unit,
or per contiguous page range**, each writing only its own disjoint files, so they run in parallel
without conflicts. It de-risks by launching one or two subagents first. Subagents report back by
page number with PASS/FAIL. After they finish, the orchestrator runs the assembler and validator
**once, centrally**, and spot-checks independently. Collator briefs for the witness passes are in
`examples/pass-prompts/R1_*` and `R3_*`.

Techniques that mattered:

- **Crop and enlarge.** For any doubtful glyph (accents, breathings, final sigma, iota subscript,
  italic vs roman, bold clarendon vs regular, section numerals), crop the line from the original
  JPEG, enlarge ~3× with PIL, and read the crop. Very large originals (e.g. 2252×3248) were
  unreliable to read directly; downscaled ~1900px copies in a scratch folder worked better.
- **Content-filter false positives.** Penitential or sacrificial themes (blood, leprosy,
  punishment) tripped an API filter when the model *emitted* more than a few words of the Latin
  at once. This happened in subagents too. The workaround, used for Leviticus and one Psalms
  homily:
  - Seed text **disk→disk with Python**: rough tesseract OCR of the page as a scaffold, never
    retyped by the model.
  - Correct it with **tiny 1–2-word edits** against the image.
  - Assemble files with a script.
  - Keep replies near source-text-free.

  Reading and comparing images never trips the filter; generating the text does.
  See `examples/pass-prompts/B_finish_under_content_filter__leviticus.md`.
- **A per-project validator, kept ALL CLEAN after every pass.** It checks:
  - guillemets balanced and never nested;
  - no consonantal J (when normalized);
  - anchors monotonic and contiguous, with shared pages double-anchored;
  - sections 1…n;
  - the exact per-unit closing doxology;
  - `LATIN/` byte-identical to `passB_final/`.

  `tools/base_check.py` is a generic version of it. When a pass legitimately changes the shape
  (anchors vanish at R7), **adapt the validator, never the text**.
- **Two trees, byte-identical.** Latin projects keep the running text in `_source/passB_final/`
  and assemble `LATIN/` (header + body) from it. Every edit is made to one side. `assemble.py`
  re-mirrors it. The validator proves byte identity.
- **Commit the tracked text after each pass**, so every pass is its own diff.

### 5.3 Pass-by-pass lessons

- **B.** Transcribe from images, not OCR, so systematic OCR errors (c/e, ligatures, Greek
  accents) never enter. Confirm each unit's start and end on the image *before* transcribing.
  **Trust centered headings and doxologies for boundaries, not running heads**: running heads lag
  the text. Skip interleaved material that is not the work (Migne interleaves *Selecta* catena
  scholia between homily sets).
- **R2 goes right after B.** While the base is still a pure diplomatic transcript, every
  base↔image divergence is a real slip, so there is nothing to filter. Leviticus ran this check
  late (as "R6B", after the editorial passes) and had to filter out R5/R6's intentional changes.
  Every later project moved it up. A typical yield is a few dozen accent, breathing or word-level
  fixes (1 Corinthians: 54 fixes in 27 files).
- **R4** found real losses. In Psalms 36–38, a homily's conclusion sat in a band spanning both
  Migne columns above catena material. Pass B had stopped at the bottom of the left column and
  wrongly concluded the homily was truncated.
- **R1** mostly confirms, and has zero edits on a clean base. Base errors hide at **cut or faded
  margins**, and that is where the second witness earns its keep. Log every variant for R6.
- **R3.** The oracle is a detector, never an authority: correct the base toward *its own
  witness*, never toward the English. Expect loose tracking where the ancient translator took
  liberties (Rufinus on Leviticus). An oracle's "extras" are often **a different critical
  edition's readings** (Heintz translates SC 411, not Migne), not dropped text. Typical yield is
  near zero base changes, but R3 produces the list of known oracle divergences that the grader
  needs later.
- **R5.** Some glyph conventions sit outside what the validator scans (Psalms lemma lines use
  forward «…», unlike the body's »…«), so check those by eye. Decide once how to handle inline
  Greek (Leviticus: keep Greek words that Origen himself glosses) and apply it everywhere.
- **R6.** Emend **only on convergent evidence**, and record everything else as "record,
  don't adopt". With no apparatus, the bright line is:
  - a **single-letter slip or impossible non-word** → emend, when the witness agrees or the
    corpus supports the correct form;
  - a **real word at multi-letter distance** → keep, as an edition variant.

  Typical yield: 4–7 emendations per work.
- **R7.** Remove anchors with one anchor-only regex applied identically to every tree, so byte
  identity holds by construction. Match only the anchor form (`\[GCS p\.\d+\]`, `\[PG \d+\]`,
  `\[JTS[^\]]*\]`), never all `[...]`, because genuine editorial brackets must survive. Anchors
  can sit mid-word (`pres[GCS p.259]byteri`). Back up first, then verify the change is
  deletion-only. `tools/strip_anchors.py` does all of this; it reproduces the real Leviticus and
  Psalms R7 output byte for byte.

### 5.4 Editorial conventions (shared by every base text)

| Mark | Meaning | Carried into English as |
|---|---|---|
| `» … «` | Scripture the author quotes | kept, translated in the author's wording |
| `* … *` | the lemma under comment | kept |
| `⟨ … ⟩` | editor's supplement | read in sense, brackets dropped |
| `[ … ]` | editor's seclusion | read in sense, brackets dropped, **except** rubrics like `[Ὠριγένους]` → `[Of Origen]` and verse labels `[iv 16]`, which are kept |
| `[[ … ]]`, `† … †` | double-bracketed scholia; obelized cruxes | kept as printed |
| `…`, `. . .`, `* * * *` | printed lacuna | kept, never filled |
| `[GCS p.N]`, `[PG n]`, `[JTS 9 p.N]` | page/column anchor | used through R6, stripped at R7 |

Orthography stays as the edition prints it (*Istrahel*, *Moyses*, *coelum*). Any uniform
normalization (J→I) is decided once and recorded.

---

## 6. Phase 2: translate

**Script:** `translate_<author>_<work>.py` (originals in `examples/original-scripts/`), or
generically `tools/translate.py --config <config>`.

What it does, per unit (one homily or one fragment):

1. **Deterministic parse.**
   - The `#` header and `====` rule are discarded.
   - The heading (`HOMILIA II.`, `§ XI | …`) is held aside and later re-emitted in English, with
     the numeral taken **from the filename** so it can never be corrupted.
   - Editorial notes that are not the author's text (Homily I's `[Titulus deest …]`) are held
     aside and replaced by fixed English.
   - A header `LEMMA:` is sent as block 0.
   - Every other body line is one block.
2. **One call per unit** with all blocks separated by blank lines. The reply must contain
   **exactly as many blocks** and must not be much shorter than the source (a sign of
   truncation).
3. **On failure:** retry once with an explicit block-count reminder. If that also fails, translate
   **block by block**, which preserves the count by construction.
4. Strip any leaked preamble ("Here is the translation…"). Soft-check that the `»` count survived.
5. Write `english/<unit>_english.txt`: a fresh `#` provenance header, `====`, the English heading,
   then the blocks, with one blank line between blocks.

Other behaviour:

- Retries with backoff: 5/15/45 s, or 60/120/240 s on rate limits.
- A batch keeps going past failures and reports them at the end.
- Existing outputs are skipped unless `--force`.

**In the skill** the per-unit call is a subagent (`phases/13_translate.md`).
`tools/translate.py prep` writes its bundle: the work's rules and the blocks under numbered
`@@ n @@` markers. The agent writes the English under the same markers and runs
`translate.py assemble`, which checks the output and writes the English file. Exact problems are
errors the agent fixes (a missing or repeated marker names its block; text before the first
marker is a leaked preamble; a whole unit under half the source length). Heuristics are warnings
(a block shorter than its ratio, a scaffold phrase, a mark count that changed): the agent checks
each against the source, fixes a real slip, and otherwise records it as settled, never padding
the English to pass a length check. A unit that dies partway resumes from its output file.

**The prompt is where the quality comes from.** Beyond the generic rules (output only the
translation; keep the block count; keep `» «` and `* *`), each work's rules block covers:

- **Scripture first.** Translate quotations as they stand. Name the numbering system (LXX
  Psalms, "Kingdoms", LXX Leviticus up to a chapter off the MT). Never use a verse-lookup tool.
- **Names.** Standard English forms for the edition's spellings. When the author etymologizes
  a name, keep his form and gloss it.
- **Fixed vocabulary.** The recurring technical terms and their English, e.g. sacrificial terms
  for Leviticus; χαρίσματα → "spiritual gifts" and ψυχικός/πνευματικός kept distinct for
  1 Corinthians.
- **Every mark the base still carries** and what to do with it (§5.4), listing the actual
  instances ("only four square-bracket interventions exist: …").
- **Deliberate irregularities not to "fix".** For example, the non-uniform doxologies, listed
  homily by homily.
- **Special items.** A Greek word Origen etymologizes (keep it in Greek script), and a term the
  argument leans on (*apopompaeus*, the scapegoat).
- **Register.** Keep the argumentative connectives. Long periods may be broken up but no clause
  dropped. Fragments may begin or end abruptly.

All of this comes from the base-text reports. Writing it is mostly a matter of reading
`uncertain_readings.md` and the pass reports.

**Optional `--images`** attaches the unit's page scans. The model is told to open one only when a
reading looks impossible, and to read only the main text (not the apparatus, margins or running
heads).

**Workflow (the skill):**
```
python3 tools/translate.py --config CFG --check        # parse round-trip + mark balance, free
# trial: prep --units <shortest>, one translate agent, the configure agent reviews it
python3 tools/translate.py --config CFG prep           # bundles; then one agent per batch of units
python3 tools/validate.py  --config CFG --structure-only   # the translate gate
```

---

## 7. Phase 3: validate against our own source

**Script:** `validate_<author>_<work>_translation.py`, or `tools/validate.py --config <config>`.
The source is the **sole arbiter**. The source files are never modified.

**Layer 1: structure** (deterministic, free: `--structure-only`). Source slots vs English
paragraphs. It flags:

- block-count mismatch (a dropped, split or merged block);
- any block whose English is shorter than a set ratio of its source (0.70 for Latin, 0.55 for
  Greek, ignoring blocks under 200 chars);
- a block that stops mid-sentence where the source block completes;
- a missing closing doxology.

Run this first. It answers "did anything get truncated?" for nothing.

**Layer 2: fidelity** (one model judgment per unit: a scan subagent in the skill,
`phases/14a_validate_scan.md`; a headless call in the original scripts). The model sees the whole source file and the English.
It returns strict JSON:

```json
{ "score": 0-100, "grade": "A+..F", "fidelity": "high|moderate|low",
  "findings": [ { "locus", "severity", "category", "source", "ours", "issue",
                  "fix": { "old": "<verbatim unique English substring>", "new": "<corrected>" } } ],
  "summary": "…" }
```

Finding categories: omission, addition, mistranslation or sense-shift, Scripture, name or
referent, inconsistency, untranslated or garbled.

The prompt spends as much space on **what not to flag** as on what to flag:

- style and wording;
- our marks;
- name normalization;
- kept Greek terms;
- house renderings;
- deliberate irregularities;
- and above all **every crux already settled in the base-text passes**, stated precisely
  (e.g. "Homily XI reads *Iacobus* (James), not *Paulus*; render James").

Without that list the validator re-flags settled decisions forever.

**Auto-fix (the default).** A proposed fix is applied only if all of these hold:

- `old` occurs **exactly once**;
- after the edit the marks are still balanced;
- the block count is unchanged.

Anything else is reported and left for a person. (In the skill, `validate.py check-findings` runs
the same test while the scan agent writes, so it repairs a bad fix before `apply` would skip it;
`validate.py apply` keeps a journal, so a re-run never applies a fix twice.) The original scripts:
`--report-only` writes nothing, and transcripts go to `validation_logs_<work>/`.

**Then review `git diff english/`** and revert anything you disagree with. Re-run individual units
that had significant findings with no concrete fix, after fixing them by hand.

---

## 8. Phase 4: grade against the oracle (read-only)

**Script:** `grade_<author>_<work>_<oracle>.py`, or `tools/grade.py --config <config>`. It
**never writes** to the English or the source; it writes only its findings (the original
scripts: transcripts in `grading_logs_<work>/`).

- **The yardstick is the published translation's sense**, not its wording. The source is pasted
  alongside as context, so the grader can tell a real divergence from:
  - a wording difference;
  - the oracle translator's own freedom or footnotes;
  - a place where the oracle follows a **different reading** than our base.
- **Oracle text per unit.** Use the per-homily extracts made during R3 when they exist;
  otherwise `pdftotext -f/-l` a page range and cache it. For an anthology oracle (Kovacs's
  *1 Corinthians*, arranged by verse group, many Fathers interleaved, only ~33 of 90 fragments
  covered), use a coverage map pinned at R3 from the book's own source appendix. Slice the
  verse-group section from a whole-book text dump. Report uncovered units as UNGRADED.
- **The grading caveats** are the list of known oracle divergences R3 produced. Where the oracle
  is wrong or follows a variant, ours is not penalized. Leviticus had about two dozen such places:
  Barkley's "Elijah" for *Elisha*, "Paul" for *Iacobus*, a dropped negation, and so on. For an
  abridging anthology, the rule is: **content in ours but absent from the oracle is the oracle's
  cut, not our addition**, unless it contradicts the source.
- **Act on it by adjudicating against the source.** A significant divergence where the *source*
  supports the oracle is a real defect, so fix the English by hand. Where the source supports us,
  add it to the caveats so it stops being flagged.

---

## 9. Doing a new work: checklist

1. **Survey and plan.** Copy `templates/source_README_template.md` to
   `<Work>/_source/README.md`. Pick a public-domain base, a secondary witness, and an oracle.
   Write down the conventions.
2. **Pass 0.** Stage page images, OCR and the page map. Verify boundaries on the images. Drop in
   the oracle PDF.
3. **Passes A → B → R2 → R4 → R1 → R3 → R5 → R6 → R7.** Run each as a session from a written
   prompt (`templates/pass_prompt_template.md`). Keep the checker clean after each:
   ```
   python3 tools/base_check.py LATIN/ --pair »« --forbid '[Jj]' --anchor '\[GCS p\.(\d+)\]' \
       --section '(?m)^(?:\[GCS p\.\d+\] ?)?(\d+)\.\s' \
       --mirror _source/passB_final --mirror-start '^(\[GCS p\.\d+\] ?)?\d+\.\s'
   python3 tools/strip_anchors.py --pattern '\[GCS p\.\d+\]' LATIN/ _source/passB_final/ \
       --backup _source/scratchpad/prestrip            # R7 only
   ```
   Commit after each pass. Stop when a full pass changes nothing substantive.
4. **Configure.** Copy `tools/work_config_template.py`. Fill in the paths, parsing, and the three
   prompt blocks (translation rules, validation house rules, grading caveats) from the pass
   reports. Set the oracle location.
5. **Translate.** Run `--check`, then one unit (read it), then all.
6. **Validate.** Run `--structure-only`, then the full run. Review `git diff`, hand-fix the rest,
   and re-run the flagged units.
7. **Grade.** Adjudicate significant divergences against the source. Fix real ones; add oracle
   errors to the caveats.
8. **Done.** The deliverable is `english/<unit>_english.txt`, one file per unit, validated and
   graded, with its diffs reviewed.

The per-work scripts in `examples/original-scripts/` show the full, unabridged form of each
step. The generic `tools/` reproduce the translate, validate and grade behaviour. Checked on the
real data:

- the same blocks and headings for all 16 Leviticus homilies and all 90 1 Corinthians fragments;
- the same oracle text for every graded unit;
- `strip_anchors.py` output byte-identical to the real R7 results.

---

## 10. Pitfalls worth knowing in advance

- **Offsets drift and scans duplicate.** Glob by printed page. Record every archive-item quirk
  where the next person will find it.
- **Running heads lie at boundaries.** Headings, incipits and doxologies don't.
- **Validators only see what they scan.** Lemma lines, headers and doxology punctuation may sit
  outside the checked region, so check them by eye against the image.
- **Oracle ≠ truth.** Published translations follow other editions, footnote variants, smooth,
  abridge, and occasionally slip. Every oracle "difference" needs adjudicating on the image (base
  text) or the source (English).
- **The model will "helpfully" normalize.** Scripture gets pulled toward familiar versions,
  doxologies toward uniformity, names toward modern forms. The only defence is explicit,
  instance-level rules in the prompt, plus a validator that knows the settled calls.
- **Length checks miss thin translations.** A block can be the right length and still drop a
  clause. That is why the fidelity layer exists.
- **Auto-fix is conservative on purpose.** Unique match, balanced marks, same block count. Review
  the diff anyway.
- **Content filters can block generating benign patristic text.** Move text disk→disk with
  scripts and fix it with tiny edits.
- **Copyright hygiene.** Oracle PDFs and extracts stay in git-ignored `_source/`. Prompts and logs
  quote only a few words. Nothing from an oracle is copied into our text.

---

## 11. Reference: the five works

| | Exodus | Leviticus | Psalms 36–38 | Ephesians | 1 Corinthians |
|---|---|---|---|---|---|
| Issue | #145 | #146 | #149 | #155 | #154 |
| Base | GCS 29 pp. 145–279 | GCS 29 pp. 280–507 | Migne PG 12 cols. 1319–1410 | Gregg, *JTS* 3 (1902), 3 parts | Jenkins, *JTS* 9–10 (1908–09), 4 parts |
| OCR usable? | Latin: yes (draft) | Latin: yes (draft) | no (image-first, no Pass A) | structure only | structure only |
| R1 witness | Migne PG 12 | Migne PG 12 | Lommatzsch t. XII | Cramer *Catenae* vol. VI | Cramer *Catenae* vol. V |
| R6 aid | Baehrens apparatus | Baehrens apparatus | corroboration test | Gregg apparatus | Jenkins apparatus + Turner, *JTS* 10 |
| Oracle | Heine, FOTC 71 | Barkley, FOTC 83 | Heintz, FOTC 146 (+ Trigg, FOTC 141) | Heine, OECS 2002 | Kovacs, *Church's Bible* 2005 (selective) |
| Units | 13 homilies | 16 homilies | 9 homilies + preface | 37 fragments | 90 fragments |
| English output | `homilyNN_english.txt` | `homilyNN_english.txt` | `homilyNN_english.txt` | `fragNN_english.txt` | `fragNN_english.txt` |
| Scripts | `*_origen_exodus_*` | `*_origen_leviticus_*` | `*_origen_psalms36-38_*` | `*_origen_ephesians_*` | `*_origen_1corinthians_*` |

Typical calendar (Leviticus):

- Pass 0: Aug 28.
- Passes A through R7: Aug 29.
- Translation: morning of Aug 30.
- Validation: 10:37–11:20.
- Grading: 15:09–15:14.

1 Corinthians, with 90 Greek fragments, took Sep 15–20.

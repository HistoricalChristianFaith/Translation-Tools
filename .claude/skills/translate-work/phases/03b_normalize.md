# Phase 03b: Normalize the seed (subagent, role `normalize`)

Runs after structure, before Pass B, only when the base has a text layer or OCR that B would seed
from (`stage_base.json` → `ocr` = `usable-draft`). Its job is the **mechanical** work that B used
to do by hand: on a clean publisher text layer ~95% of B's fixes were invisible code-point
variants, mark conversions, marker clean-up and whitespace, while the text layer faithfully
reproduced the printed letters (misprints included). A script does these deterministically,
once, so B starts from normalized text and B's own changes stay auditable.

Inputs: `stage_base.json` (`ocr_slice`, `ocr_marked` if any, `text_layer`), `pass0_report.md`,
`README.md`, `manifest.json` (units, pages, incipit/explicit, `anchor.format`),
`boundary_audit.md`, resolved decisions, `[normalize]` items in `carry_forward.md`.
Work in `${RUN_DIR}/normalize/`.
`MODE: apply-decision <id>`: change the script per that resolved decision, re-run it on the seed
and the unit files (`--write`; they are still untouched by B), update the summary; nothing else.

## 1. Survey the seed

With Python (never by reading it into your context), write `${RUN_DIR}/normalize/survey.md`:
- a **character inventory**: every code point with count and Unicode name, grouped (base letters,
  combining marks, precomposed Greek, punctuation, Latin inside Greek or the reverse);
- **code-point variant pairs** for one printed glyph, with counts per form (Greek oxia U+1F71…
  vs tonos U+03AC…; `·` U+0387 vs U+00B7; `;` U+003B vs U+037E; `’` U+2019 vs U+1FBD vs U+02BC;
  `ʹ` U+0374 vs U+02B9; …);
- **mark patterns**: doubled, stray or detached combining marks (a mark after a space or
  punctuation, two identical marks on one letter, a mark on a letter that can't carry it);
  Latin look-alike letters inside Greek words (or Cyrillic, etc.);
- **known text-layer artifacts**: italics (`<i>`), inline markers (folio numbers, footnote
  signs), words or spans split by markers or anchors, hyphenation, false paragraph breaks,
  running heads or apparatus lines left in.
Look at 3–5 pages against their images to learn what each pattern looks like in print.

## 2. Write the custom script

`${RUN_DIR}/normalize/normalize.py` (pure Python, stdlib only), written for **this** text:
- `normalize.py <file|dir>...` = dry run: prints `changes: N` and counts per category;
  `--write` applies them; `--flags <file>` writes the spots to check on the image (jsonl:
  `{"page","unit","cat","context"}`). It must be **deterministic and idempotent** (a second run
  reports `changes: 0`) and work on the seed **and** on unit files (R5 re-runs it on the corpus).
- **Apply only invisible or mechanical changes**, each as a named category:
  - code points → the **corpus-majority form** of each printed glyph (never a blanket NFC/NFD:
    NFC turns Greek oxia into tonos);
  - combining-mark repair (compose a detached mark onto its letter, drop a doubled or stray one)
    where exactly one printed form is possible; otherwise flag it;
  - Latin look-alikes → the letter of the word's script;
  - whitespace, words split by markers or line ends, false paragraph breaks;
  - mark conversions **that the README or a resolved decision already settles** (e.g. `<i>` →
    `» «`, `‹ ›` → `⟨ ⟩`, drop folio markers), re-joining spans split by markers or anchors.
    An italic that may be a book title rather than Scripture is converted per the README and
    **flagged**.
- **Never change a visible letter, accent or breathing.** Where the text layer disagrees with
  itself or with Greek/Latin morphology (e.g. a breathing that looks wrong), log a **doubt**
  (`doubts.py add --phase normalize --packet normalize`, `status_contract.md` §2a) and leave it.
- An editorial-policy question (which code-point set, whether to keep a marker class, how to
  treat a typeface the README doesn't cover) becomes a **decision** (`decisions.py add`);
  script it under your recommended option so the re-run after resolution is one command.

## 3. Seed the unit files

`${RUN_DIR}/normalize/seed.py` cuts the normalized seed into units (manifest pages; split shared
pages at the incipit/explicit) and replaces each unit's `[[TO BE TRANSCRIBED IN PASS B]]` line
with its body: one paragraph per line, the page anchor (`anchor.format`) at every page turn,
section numbers as printed, per `conventions.md`. The header, heading and lemma lines stay as
structure wrote them. A unit whose boundary the script can't locate keeps its placeholder
(list it in the notes; B transcribes it the classic way). Before writing, save
`${RUN_DIR}/normalize/before/` (the seed as staged); after, run
`python3 "${TOOLS_DIR}/normalize_check.py" --work-dir "${WORK_DIR}"` → must print
`GATE normalize_check: PASS` (it runs `normalize.py ${LANG_DIR}`, which must print `changes: 0`,
and `manifest_check.py`). Keep the `changes: N` line exactly in that form: the gate reads it.

## 4. Check on the images

For **each category where the script touched letters or marks** (combining marks, look-alikes,
mark conversions, re-joined spans), crop and check at least 5 instances (all, if fewer) on the
page images. A category that proves wrong is fixed in the script and re-run, never hand-patched.

## 5. B mode

Recommend how thorough Pass B must be:
- `light`: born-digital text layer, letters matched the image on every sampled page; B checks
  each page for structure, marks and exclusions, and checks letters only at the flagged spots
  and wherever the image visibly differs;
- `full`: OCR or a noisy text layer; B collates every word (the classic method).

## Output

- `${RUN_DIR}/normalize/summary.md`: changes by category (count + 2 examples each), what was
  image-checked, units left unseeded, the recommendation for B mode, decisions and doubts raised.
- `${RUN_DIR}/normalize/flags.jsonl` (from `--flags`): the spots B must check on the image.
- `${RUN_DIR}/normalize/normalize.json` (compact; the orchestrator reads it):
  `{"changes": 6120, "by_category": {"codepoint": 57, "marks": 50, …}, "flags": 214,
  "seeded_units": 29, "unseeded": [], "b_mode": "light", "b_mode_reason": "…"}`
- Notes `${RUN_DIR}/notes/normalize/normalize.md` and status
  `${RUN_DIR}/status/normalize/normalize.json` (`fixes` = total changes), per
  `status_contract.md`.

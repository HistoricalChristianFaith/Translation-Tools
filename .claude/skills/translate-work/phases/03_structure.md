# Phase 03: Structure (Pass A; subagent, role `scout-<from>-<to>`, `assemble`, or `MODE: adopt`)

Establish the **spine** of the work: its units, their exact boundaries and pages, the text
conventions, and the work packets every later pass uses. Structural mistakes found later are
very expensive, so verify every boundary on the image.

Inputs:
- `${RUN_DIR}/stage_base.json`, `${SRC_DIR}/pass0_report.md`, `${SRC_DIR}/README.md`;
- `${SRC_DIR}/pages/base/index.json`;
- the OCR slice, if any.

## How the orchestrator uses the roles

- The OCR is `usable-draft` or `structure-only`, **or** the span is ≤ 60 pages → one
  `assemble` agent does everything.
- Otherwise (no usable OCR and a long span) → first `scout` agents over page ranges of about 40
  pages (in waves), then one `assemble` agent.

## Role `scout-<label-from>-<label-to>`

Read every page in your range (use the image reading rules). For each page, record every
structural feature, but **don't transcribe the text**:
- centered headings (e.g. `HOMILIA V.`, `§ XI`), titles, and lemma lines (first words);
- the first 5–8 words after each heading (the incipit);
- the last 5–8 words before a heading or closing formula (the explicit, e.g. a doxology ending
  "Amen");
- printed section numerals, and where they are;
- interleaved material that isn't the work (catena scholia, other works), with its extent;
- the running head.

Write `${RUN_DIR}/scout/<from>-<to>.json` as a list of objects like
`{"label": "332", "headings": [...], "incipits": [...], "explicits": [...], "sections": [...], "foreign": "...", "running_head": "..."}`.
Write notes and status (`status/structure/scout-<from>-<to>.json`).

## Role `assemble`

1. **Find every unit.** Use the scout files, or the OCR headings, or the images. For each unit,
   pin down on the images: the heading page and line, the lemma or title line, the incipit, the
   explicit, and the list of page labels it spans (in index order, contiguous). A page shared by
   two consecutive units belongs to both.
2. **Choose the file naming** and write `${RUN_DIR}/manifest.json` (schema in
   `${TOOLS_DIR}/manifest_check.py`):
   - `language`, `lang_dir` (`LATIN`, `GREEK`, …), `unit_noun`, and
     `file_suffix` (`_latin.txt`, `_greek.txt`);
   - unit files named `<noun><NN>_<lang>.txt`, zero-padded (`homily01_latin.txt`,
     `frag07_greek.txt`). **`n` must equal the number in the file name.** Units are numbered
     contiguously from 1, or from 0 when a preface precedes unit 1 (`homily00_…`, `n: 0`);
   - `anchor.format` and `anchor.regex`, from the edition's page labels: `[GCS p.{label}]` →
     `\[GCS p\.(\d+)\]`; Migne columns `[PG {col}]` → `\[PG (\d+)\]` (one anchor **per column**);
     multi-volume `[JTS 9 p.{page}]` → `\[JTS \d+ p\.(\d+)\]`. Choose a short siglum for the
     edition. The regex must match only anchors and have one numeric capture group;
   - `checks`:
     - `pairs`: `["»«"]`, plus `["⟨","⟩"]`, `["[[","]]"]` if the edition uses them;
     - `even`: `["*"]` only if lemma words are marked in-body; add `"†"` for obelized cruxes;
     - `even_exempt`: a regex for any heading siglum using `*`;
     - `forbid`: e.g. `["[Jj]"]` only if a normalization decision exists;
     - `section_regex`: `(?m)^(?:<anchor regex without its group> ?)?(\d+)\.\s` if units have
       printed section numbers, else `null`;
     - `section_start_for` for units whose numbering starts after 1;
     - `ending`: only if **every** unit ends the same way;
   - each unit: `n`, `file`, `label`, `heading` (the heading line exactly as it will appear in the
     file, e.g. `HOMILIA V.` or `§ XI`), `passage` (the biblical passage or topic, if known),
     `pages`, `incipit`, `explicit` (≤ 8 words each). `incipit` and `explicit` are the first and
     last words of the body **as you write it into the unit file** (copy them from the print now;
     later phases keep them in step with the text). Don't add a `lemma` key: the lemma lives in
     the unit file's lemma line.
   Also set `state.json` → `lang_dir` (`python3 ${TOOLS_DIR}/state.py set --work-dir ${WORK_DIR} lang_dir=LATIN`).
   This is the one state key you may set. **If `state.json` → `base_license` is `copyright`**, the
   verified base text is the edition's text and must stay private: use `_source/<LANG>` (e.g.
   `lang_dir=_source/GREEK`) in both `manifest.json` and `state.json`.
3. **Packets** → `${RUN_DIR}/packets.json`. Each packet is **whole units only** (never split a
   unit), contiguous, and about 8–15 printed pages. A single unit larger than that is its own
   packet. Ids are `p01`, `p02`, … Include each packet's `units` and `pages` (the union of its
   units' pages). Then run `python3 ${TOOLS_DIR}/packets.py split --work-dir ${WORK_DIR}`: it
   gives every packet over 12 pages page-range **sub-packets** (`p07a`, `p07b`, …), each run by
   its own agent in the page-reading phases.
4. **Scaffold every unit file** in `${WORK_DIR}/<lang_dir>/` in the format of
   `shared/conventions.md`:
   - the 4 `#` header lines (author and work, unit label and passage; how it survives; source
     edition and pages; Scripture note);
   - the `====` line (60 `=`);
   - the heading line;
   - the lemma or title line, if the unit has one, transcribed **from the image** (it is short;
     crop it);
   - the placeholder line `[[TO BE TRANSCRIBED IN PASS B]]` (the normalize phase, if it runs,
     replaces it with the normalized seed).
5. **Run** `python3 ${TOOLS_DIR}/manifest_check.py --work-dir ${WORK_DIR}` and fix until it
   prints `MANIFEST OK`. (Without `--files`, because bodies are empty until Pass B.)
6. **Report** → `${SRC_DIR}/boundary_audit.md`: a table of unit | heading | pages | incipit |
   explicit | how verified; shared pages; anything interleaved and excluded; numbering oddities;
   the packet table.
7. Notes (`## Carry-forward` items for B/R4, e.g. "unit 5's conclusion continues at the top of
   p.X above the catena") and status (`status/structure/assemble.json`).

## `MODE: adopt` (the work already has a finished base text)

Build `manifest.json`, `packets.json` and, if page images exist, `pages/base/index.json` from
the **existing** files in `<lang_dir>/`. Take headings from the files and pages from their
headers or reports. Don't modify the text files. Set `"adopted": true` in the manifest. If no
images exist, write `{"pages": []}` as the index and give units `"pages": []`. Run
`manifest_check.py --files`; it must print `MANIFEST OK`. Set
`checks` so that `check_base.py` passes on the existing text. Status: `status/structure/assemble.json`.

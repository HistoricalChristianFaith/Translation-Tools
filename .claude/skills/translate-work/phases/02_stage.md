# Phase 02: Stage the sources (Pass 0; subagent, role `base` or `witness`)

Download and render the sources, and verify the work's boundaries **on the images**. Nothing
downstream can be better than the staging. Read `${RUN_DIR}/survey.json` and `state.json`
(`base_id`, `base_source`, `witness`, `oracle`) first.

## Role `base`

### 1. Get the base edition

**From archive.org** (`base_source = archive`, the chosen candidate in `survey.json`):
- `python3 ${TOOLS_DIR}/archive_item.py test <item>`: confirm it still downloads.
- `archive_item.py pagemap <item> --out ${SRC_DIR}/page_map.json`: printed page per leaf.
- `archive_item.py ocr <item> --out ${SRC_DIR}/ocr/base_full_djvu.txt`, if the item has OCR.
- **Find the work's span.** Search the OCR for the work's title and section heading, and the
  running heads of its first and last units (e.g. `ORIGENIS / IN / LEVITICUM`,
  `in Leviticum Homilia XVI`). Get the leaf range from `page_map.json`. **Don't assume a
  constant page→leaf offset.** It drifts. Check the first and last pages on the images.
- Render the span plus 1 page either side:
  `archive_item.py render <item> --leaves <a-b> --out ${SRC_DIR}/pages/base --prefix base --pagemap ${SRC_DIR}/page_map.json`
  This writes `pages/base/index.json`. It takes a few seconds per leaf; re-running resumes.
- Write an OCR slice of just the work to `${SRC_DIR}/ocr/base_slice.txt` (by OCR line range).
  Record the line range.

**From a PDF** (downloaded with `archive_item.py pdf`, or dropped into `_source/incoming/base/`):
- `python3 ${TOOLS_DIR}/pdf_pages.py info <pdf>`
- Find the printed page ↔ PDF page offset by rendering two sample pages at low dpi and reading
  their page numbers. **Check it at both ends of the span.** If it changes (duplicated or
  missing pages), render the range in pieces with different `--offset`s.
- `pdf_pages.py render <pdf> --pages <a-b> --offset <k> --out ${SRC_DIR}/pages/base --prefix base --dpi 300`
- If the PDF has a text layer, `pdf_pages.py text <pdf> --pages <a-b> --out ${SRC_DIR}/ocr/base_slice.txt`.
  Say whether it is `born-digital` (a publisher's typeset text) or `ocr`. If the edition marks
  Scripture or titles by typeface (italic, bold), also extract a slice that keeps it
  (`<i>…</i>`, from the PDF's font names) → `ocr/base_slice_marked.txt`, main text only.

**From page images the user dropped in:** copy them to `pages/base/` as
`base_p<LABEL>_<orig>.jpg` (convert to RGB JPEG) and write `pages/base/index.json` yourself,
in printed order: `{"pages": [{"label": "…", "file": "pages/base/…"}]}`.

**Labels:**
- Printed page numbers as strings.
- For two-column editions numbered by **column** (Migne), use the image's first column number
  as its label and note "two columns per image: <odd>-<even>" in the report.
- For multi-volume or multi-issue bases, prefix the volume (`9:231`, `10:29`) so labels stay
  unique.
- Images outside the numbering (plates, blanks) get `L<leaf>`.
- A duplicated printed page gets `b`.

### 2. Judge the OCR

Look at 3 sample pages of the slice against the images. Set `ocr` to one of:
- `usable-draft`: mostly right words, systematic letter noise; fine as a seed for Pass B;
- `structure-only`: finds headings and section numbers, but the text is unreliable (Migne Latin,
  any polytonic Greek);
- `none`.

### 3. Verify boundaries on the images

Open the **first** and **last** page of the span. Find the work's title or heading, the first
unit's opening words (incipit), and the last unit's closing words (explicit). Check any
**seams**: volume, issue or part boundaries inside the span. Spot-check 3 unit boundaries in
the middle against the OCR's headings. Note anything odd: duplicated leaves, missing pages,
plates, interleaved material from other works, running heads that lag.

### 4. Oracle (if `state.json` → `oracle` is set)

- Move the file from `_source/incoming/oracle/` to `${SRC_DIR}/oracle/oracle.pdf` (or keep its
  extension if it isn't a PDF).
- `pdf_pages.py info` it. If it has a text layer, extract the whole book:
  `pdf_pages.py text ${SRC_DIR}/oracle/oracle.pdf --out ${SRC_DIR}/oracle/oracle_full.txt`
- Note in the report where the translation of the first and last units starts (PDF pages;
  `pdf_pages.py find`). Don't quote it beyond a few words (`copyright.md`).

### 5. The workspace README

Fill `${TEMPLATES_DIR}/source_README_template.md` into **`${SRC_DIR}/README.md`**: the survey
facts, witnesses in priority order, the pass list (mark skipped passes), the editorial
conventions (copy the defaults from `shared/conventions.md`, adapted to this edition's
typography: what marks Scripture, the lemma, supplements), the provenance links, and the
Status. This README is binding on every later agent, so be precise and short.

### 6. Outputs

- `${SRC_DIR}/pass0_report.md`: item(s) and files, span (pages and leaves), how the offset
  behaves, OCR quality with examples, the boundary checks (page + what you saw), anomalies,
  and oracle staging.
- `${RUN_DIR}/stage_base.json` (compact; the orchestrator reads it):
  ```json
  {"images_dir": "pages/base", "pages": 241, "first": "280", "last": "507",
   "ocr": "usable-draft", "ocr_slice": "ocr/base_slice.txt", "ocr_marked": null,
   "text_layer": "born-digital | ocr | none", "two_column": false,
   "oracle": {"file": "oracle/oracle.pdf", "text": "oracle/oracle_full.txt"} ,
   "anomalies": ["p.393 double-scanned (leaves 457/458)"]}
  ```
- Notes and status (`status/stage/base.json`), per `status_contract.md`.

## Role `witness`

Same method for the secondary witness named in `state.json` → `witness` (item from
`survey.json` → `witness_candidates`, or a file in `_source/incoming/witness/`):
- Render only the span that corresponds to the work into `${SRC_DIR}/pages/witness/`
  (`--prefix witness`), with its own `index.json`.
- Get its OCR if any, into `${SRC_DIR}/ocr/witness_slice.txt`.
- Verify both ends on the images.

Write `${RUN_DIR}/stage_witness.json`:
`{"images_dir": "pages/witness", "pages": N, "first": "…", "last": "…", "ocr": "…", "unit_map_hint": "…"}`
`unit_map_hint` says, if you can tell, where each unit starts in the witness (page or column).
Also append a `## Witness` section to a separate file, `${SRC_DIR}/pass0_witness.md` (never to
`pass0_report.md`, which the base agent owns). Write notes and status
(`status/stage/witness.json`).

Both roles run in parallel. **Write only your own folders and files.**

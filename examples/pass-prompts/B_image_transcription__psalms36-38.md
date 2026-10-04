# Pass B prompt — Origen, *Homilies on Psalms 36–38* (image transcription, the primary build)

You are building the **Latin base text** of Origen's *Homilies on Psalms 36–38* (Rufinus's Latin, 9
homilies) — GitHub issue #149. **This is Pass B: transcribe every homily directly from the Migne
PG 12 page images.** There is **no OCR scaffold and no Pass A** — the PG 12 images are the base, so
Pass B *is* the origin of the text. Your output is a diplomatic PG 12 transcript, column by column,
with no OCR noise ever entering.

**Scope: Pass B only.** Produce the 9 transcribed homilies (+ Rufinus's *Praefatio*), self-verify
each against the image, write `passB_report.md`, seed `uncertain_readings.md`. **Do NOT start R2,
R4, R1, R3, R5, R6, or R7.** Stop and report when all 9 are image-true and validate clean.

## Read first (in full)
1. `_source/README.md` — the project spec, esp. the "⚠️ base is Migne, image-first from PG 12" box
   and the **Editorial conventions** section. **These conventions override any default.**
2. `_source/pass0_staging.md` — the staging report: verified endpoints, per-homily column
   boundaries, the two inter-psalm seams, and the **quirks list (read every one)**.
3. `_source/pg12_columns.json` — the machine-readable homily → column-span → leaf map, with the
   verified heading columns, incipits, doxologies, and the `interleaved_selecta_catena` block.
4. For method/format templates, study the completed **Leviticus** Pass B (same author, same
   translator, same Migne workflow): `../Homilies on Leviticus/_source/passB_report.md`, a
   `../Homilies on Leviticus/LATIN/homilyNN_latin.txt` (header + body format), and the matching
   `../Homilies on Leviticus/_source/passB_final/homilyNN.txt` (byte-identical running text).

## The images
`_source/pg12_pages/pg12_col{ODD}-{EVEN}_leaf{L}.jpg` — 50 leaves (662–711 = cols 1315–1414), native
grayscale, two PG columns per leaf: **left half = odd (first) column, right half = even (second)
column.** The corner numbers in the running head are the PG 12 column numbers (used for `[PG n]`
anchors). The homily set proper = **cols 1319–1410 (leaves 664–709)**; 662–663 and 710–711 are
margin.

## The 9 homilies (+ Praefatio) — image-verified spans from `pg12_columns.json`

```
homily00 = Praefatio Rufini (Prologus)  col 1319         leaf 664
homily01 = Ps 36 Hom I    cols 1319–1328  leaves 664–669
homily02 = Ps 36 Hom II   cols 1329–1335  leaves 669–672
homily03 = Ps 36 Hom III  cols 1336–1348  leaves 672–679   (heading in RIGHT col 1336)
homily04 = Ps 36 Hom IV   cols 1349–1358  leaves 679–684
homily05 = Ps 36 Hom V    cols 1359–1367  leaves 684–688
homily06 = Ps 37 Hom I    cols 1369–1379  leaves 689–694
homily07 = Ps 37 Hom II   cols 1380–1388  leaves 694–698   (heading in RIGHT col 1380)
homily08 = Ps 38 Hom I    cols 1391–1400  leaves 700–704
homily09 = Ps 38 Hom II   cols 1400–1410  leaves 704–709   (heading in RIGHT col 1400)
```

Filename ↔ homily map is fixed (see README): homily01–05 = Ps 36 Hom I–V; homily06–07 = Ps 37
Hom I–II; homily08–09 = Ps 38 Hom I–II. **Confirm each start/end on the image before transcribing**
(the boundary heading and the "…Amen." doxology are your anchors, per `pass0_staging.md`) — the
column numbers above are exact but re-check the shared boundary columns, where one homily's doxology
and the next one's heading sit on the same leaf.

## ⚠️ Do NOT transcribe (from `pass0_staging.md` quirk #1) — this is the biggest trap
Migne interleaves **Greek+Latin *Selecta* catena** verse-scholia between the homily sets and after
the last homily. **These are catena fragments (Codex Coislinianus / Catena Corderii), NOT Rufinus's
homilies — skip them entirely:**
- **cols 1367–1368** (leaf 688) — Ps 37 Selecta, after Ps 36 Hom V.
- **cols 1387–1390** (leaves 698–699) — Ps 38 Selecta; **leaf 699 is entirely catena.**
- **cols 1409–1410 lower half** (leaf 709) — Ps 39 Selecta; begins *after* the Ps 38 Hom II doxology
  (which is the true end of the set).
Also skip: small **Greek Catena Corderii footnotes** at some column feet inside homily pages (e.g.
"(39) Καπνὸς δὲ πυρός … Catena Corderii" on leaf 664) — apparatus, not homily text. And **keep all
Greek out of the Latin body** (any Greek fragment goes to a separate note for later R5, never
interleaved into the Latin — README convention).

## Boundary discipline (from `pass0_staging.md` quirk #2)
The **recto running head lags the text** at the tail (leaf 705/707 read "HOMIL. I IN PSAL. XXXVIII"
during Ps 38 Hom II; leaf 709 reads "PSAL. XXXIX" during the Ps 38 close). **Trust the centered
`HOMILIA` headings and the "…Amen." doxologies for boundaries, never the running head.** Verso leaves
all read the generic "EX ORIGENE". The running head confirms the correct work on every leaf — but do
not use it to place a boundary.

## Editorial conventions (from README — apply exactly)
- `» … «` — Scripture Origen quotes in exposition (the printed guillemets); balanced, zero nesting,
  no stray ›‹ or ASCII `< >`.
- `* … *` — the **Psalm lemma** under comment. Each homily's heading carries a
  "*De eodem psalmo, ab illa parte: « … »*" sub-lemma (captured in `pg12_columns.json`) — mark it.
- `⟨ … ⟩` supplements; `[ … ]` seclusions; `…` / `* * * *` a printed lacuna (do **not** fill).
- `[PG n]` = Migne PG 12 column anchor. **Place one inline at the top of every column you cross**
  (e.g. `[PG 1320]` where col 1319 gives way to col 1320), so the base is column-traceable through
  R6. These are stripped only at R7 — keep them now.
- **Keep the edition's spellings** (Iesus, coelum, foenum, *tricesimum* at the Ps 37 seam vs.
  *trigesimum* elsewhere, printed *J* as printed) — do not modernize. (But if you mechanically
  normalize J→I as Leviticus did, do it uniformly and record it — your call, note it in the report.)
- **Latin reading text only.** Greek fragments kept separate.

## Output format (mirror Leviticus `LATIN/homilyNN_latin.txt`)
For each homily write **two byte-identical-running-text files**:
- `LATIN/homily0N_latin.txt` — leading `#` comment header lines (title/psalm/one-line description;
  source = "Migne PG 12, cols NNNN–NNNN"; note Rufinus's Latin, LXX/Old-Latin lemma wording), then a
  `====` rule, then the `HOMILIA …` heading line, then the numbered body with `[PG n]` anchors,
  guillemets, and the lemma.
- `_source/passB_final/homily0N.txt` — the final body (byte-identical to the LATIN running text).

Number the sections as Migne prints them (the bold "1., 2., 3. …" section numerals — restore any the
image shows but that are easy to miss mid-paragraph, exactly as the Leviticus pass had to). End each
homily at its verbatim doxology (the tails are non-uniform — transcribe what the image shows, e.g.
h07 "…per quem tibi gloria et potestas in saecula saeculorum. Amen."; h09 "…cui est honor et gloria
in saecula saeculorum. Amen.").

**Praefatio:** put Rufinus's *Praefatio* (Prologus, col 1319, incipit "*Quoniam trigesimi sexti…*")
in its own `LATIN/homily00_praefatio_latin.txt` (recommended — it prefaces the whole set and is
distinct from Hom I), OR at the head of homily01. Decide and record the choice in `passB_report.md`
(README leaves it to Pass B).

## Method (mirror Leviticus, adapted for image-first)
- **Fan out disjoint homilies to per-homily subagents** (one homily per agent → disjoint output
  files → run in parallel, no write conflicts). Each agent transcribes its homily **column by
  column** directly off its leaf images, then **re-reads its own output word-for-word against the
  image** (adversarial self-verify) before returning.
- **Content-filter caution (learned in Leviticus):** an account-level content-filter false-positive
  can reject emitting more than ~1–2 words of this patristic Latin per generation (penitential /
  sin / affliction themes — benign scholarship). If an agent hits it, fall back to the **tiny-edit
  method**: seed the file with a rough disk-write (a *noisy* `tesseract -l lat` pass on the PG image
  is fine purely as a scaffold — every word will be corrected against the image anyway), then correct
  it with many **1–2-word edits** against the image. The filter limits generation *size*, not which
  agent runs — subagants + tiny edits clear it.
- **Verify each homily:** guillemets balanced/no nesting; `[PG n]` anchors present and monotonic
  across the span with shared boundary columns handled; section numbers from 1; the exact doxology;
  and `LATIN/…` running text byte-identical to `passB_final/…`. A small `validate.py` (adapt the
  Leviticus one in its `_source/scratchpad/`) is worth writing.

## Deliverables & logging
- `LATIN/homily00_praefatio_latin.txt` (or folded into homily01) + `LATIN/homily01…09_latin.txt`.
- `_source/passB_final/homily00…09.txt` (byte-identical running text).
- `_source/passB_report.md` — per-homily coverage table (cols, `[PG]` anchor count, section range,
  guillemet balance, verbatim doxology tail), the Praefatio-placement decision, the J→I decision,
  and any filter-block encounters + how cleared. Mirror the Leviticus `passB_report.md`.
- `_source/uncertain_readings.md` — every doubtful reading, damaged word, restored numeral, and each
  Greek fragment stripped from the Latin body (flagged for R5 reinsertion). Adjudicate every doubtful
  reading **on the PG 12 image** — never on an English or the Greek.

## Definition of done
All 9 homilies (+ Praefatio) transcribed image-true from PG 12, each self-verified against the image,
guillemets/anchors/sections/doxologies clean, `LATIN/` ↔ `passB_final/` byte-identical,
`passB_report.md` and `uncertain_readings.md` written, the interleaved Selecta catena excluded, Greek
kept out of the Latin body. **Then stop and report** — summarize per-homily coverage and hand off to
R2 (independent lensless image re-collation). Do not begin R2 or any later pass.

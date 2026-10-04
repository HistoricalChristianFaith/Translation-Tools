# Pass B transcriber brief — Origen, Homilies on Psalms 36–38 (Migne PG 12, Rufinus's Latin)

You transcribe **one homily** directly from the Migne PG 12 page images into a diplomatic
Latin transcript. This is the base text's origin (no prior OCR-cleaned scaffold is trusted).
Your specific homily, column span, heading, incipit and doxology are given in the task prompt.

## Where the pixels are (all paths relative to the project root
`Origen of Alexandria/Homilies on Psalms 36-38/`)
- **Legible reading unit — USE THESE:** `_source/scratchpad/slices/col{N}_s0.png … col{N}_s3.png`
  = column N split top→bottom into 4 overlapping horizontal bands. `s0`=top, `s3`=bottom.
  Read them in order; they are large and sharp. **This is your primary evidence.**
- Full column (less legible, for orientation): `_source/scratchpad/cols/col{N}.png`.
- **Noisy OCR seed (SCAFFOLD ONLY):** `_source/scratchpad/ocr/col{N}.txt`, and the whole homily
  pre-concatenated at `_source/scratchpad/seed/homily{NN}.txt`. Tesseract on a 160-year-old font —
  it is WRONG often (c↔e, u↔n, i↔l, ii↔u, j spam, broken words, stray marks). **Never trust a word
  from it; use it only to not miss a word, and correct EVERY word against the slice image.**
- Layout: on each leaf the **left half = the odd column, right half = the even column**. Because
  the crops overlap the gutter, a thin vertical strip of the *neighbouring* column's first/last
  letters may appear at a crop's edge (in the OCR it looks like a column of stray single letters) —
  ignore it; transcribe only your column.

## What to SKIP (never goes in the Latin body)
- **Greek** of any kind: the interleaved Greek+Latin *Selecta* catena blocks, the Greek half of a
  bilingual block, and small Greek "Catena Corderii" footnotes at a column foot
  (e.g. `(39) Καπνὸς δὲ πυρός … Catena Corderii`). If you meet Greek, stop transcribing that block.
  Record any Greek you had to step over in your returned report (for a later pass), but keep it OUT
  of the Latin.
- **Migne's footnotes at the column foot:** the little italic Scripture-reference notes keyed by
  `*`, `**`, superscript numbers (e.g. `** Hebr. 1, 4.  ** Psal. xxxvi, 1.  ** Deut. xxxii, 24.`)
  and rule-separated apparatus. These are Migne's citations, NOT Rufinus. Skip them.
- **Running heads** (top of every column): `EX ORIGENE`, `SELECTA IN PSALMOS. — HOMIL. n IN PSAL. …`,
  the psalm name, and the **PG column number in the corner** (e.g. `1319`, `1320`). Do not transcribe
  the running head; DO use the corner number to confirm which column you are in.
- **Old Delarue column markers**: stray **3–4-digit** numbers dropped inline mid-column
  (e.g. `655`, `671`) — these are the reprinted older-edition column numbers, NOT section numbers and
  NOT text. Delete them. (Contrast: a genuine **section number** is a low integer in sequence —
  `1.` `2.` `3.` … — printed bold at the start of a paragraph. Keep those.)

## Transcription conventions (these OVERRIDE any default; mirror the finished Leviticus base)
1. **Scripture quotation marks.** Migne prints the passages Origen quotes as French guillemets
   `« … »` (opening `«`). Output them **reversed, German-style, no interior spaces**: `»word«`
   (`»` opens, `«` closes). So `« Noli aemulari »` → `»Noli aemulari«`. Balance every one; no nesting.
2. **The psalm lemma line.** Directly under the `HOMILIA …` heading Migne prints the verse under
   comment (`De eodem psalmo, ab illa parte: « … »` — or, for the first homily of each psalm, the
   `Super psalmum … qui dicitur: « … »` line). Put that whole line on its own line wrapped in
   `* … *`, with its scripture in `»…«`. Example: `*De eodem psalmo, ab illa parte: »Subditus esto
   Domino, et ora eum«.*`
3. **Column anchors.** Put `[PG N]` inline **exactly at the point where column N's text begins** —
   at the first word of that column, even if it falls mid-sentence or mid-word (write `re[PG 1294]demptio`
   only if the break truly splits the word; normally it's between words: `… verbum [PG 1320]Dei …`).
   Your homily's FIRST column anchor goes at the very start of the body, before `1.`. One anchor per
   column you cross; anchors must be monotonically increasing across your span.
4. **Section numbers.** Restore Migne's bold `1.` `2.` `3.` … at paragraph starts, numbering from 1.
   Some are easy to miss mid-paragraph or glued to an anchor — hunt for them on the image.
5. **Spelling — keep the edition's, with ONE mechanical normalization:**
   - **J → I / j → i uniformly** (this edition prints consonantal J; we normalize as the sibling
     Leviticus/Exodus bases do): `Jesu→Iesu`, `Jacob→Iacob`, `justus→iustus`, `judex→iudex`,
     `ejus→eius`, `cujus→cuius`, `hujus→huius`, `jam→iam`, `adjuvat→adiuvat`, `conjug-→coniug-`,
     `major→maior`, `projic-→proiic-`, etc. Apply to EVERY consonantal J/j, upper and lower.
   - Keep **u/v exactly as printed**. Keep `ae`/`oe` (expand any `æ`/`œ` ligature to `ae`/`oe`).
   - Keep every other edition spelling as printed: `coelum`, `foenum`, `coepit`, `Istrahel`,
     `Moyses`, `tricesimum` (the Ps 37 seam prints `tricesimum`, not `trigesimum` — keep it),
     `sylva`, `charissime`, `epistola`, doubled/!single consonants as printed, etc. Do NOT modernize.
6. **Editor marks** (rare here): `⟨ … ⟩` supplement, `[ … ]` seclusion, `…` a printed lacuna
   (never fill one). If none appear, use none.
7. **Latin reading text only.** No Greek anywhere in the body.

## Boundaries (use text anchors, NOT column arithmetic — the running head lags the text)
- **Start** at your homily's heading/incipit (given in the task). Everything above it on that column
  (previous homily's tail, a catena block, a seam heading you don't own) is not yours.
- **End** at your homily's verbatim `… Amen.` doxology (given in the task). Stop there. Anything below
  (the next `HOMILIA` heading, or a Selecta catena) is not yours. A doxology can sit at the TOP of the
  column after your last full column (e.g. Hom I's doxology is at the top of col 1329) — follow the
  text, transcribe through to `Amen.`, then stop.

## Output — write TWO files (the body text must be byte-for-byte identical between them)
**A. `_source/passB_final/homily{NN}.txt`** — the body ONLY: begins with `[PG {first}] 1. ` (for the
Praefatio, which has no section numbers, begins `[PG 1319] ` then the prose), each section its own
paragraph (blank line between sections), ends at the doxology `… Amen.`. No header, no HOMILIA line,
no lemma line.

**B. `LATIN/homily{NN}_latin.txt`** — exactly this, in order:
```
# Origen, Homilies on Psalms 36–38 — <psalm>, Homily <n> (<one-line topic>). Lemma as printed by Migne.
# Origen's Greek homily, surviving only in Rufinus of Aquileia's Latin translation (c. 401).
# Source text: Migne, Patrologia Graeca 12, cols <first>–<last> (Rufinus's Latin, In Psalmos).
# Scripture is quoted in Old-Latin / LXX wording (Rufinus renders Origen's lemmata, not the Vulgate).
============================================================
HOMILIA <numeral>.
*<the lemma line, per convention 2>*
<the body — the SAME characters as passB_final/homily{NN}.txt>
```
(The `====` rule is exactly 60 `=` characters. For the Praefatio see its task prompt — heading is
`PROLOGUS RUFINI PRESBYTERI.` and there is no `*lemma*` line.)

## Method (filter-safe)
Work column by column. For each column: open its 4 slice images, read the Latin, and write/repair
your output to match the image. A patristic-Latin content filter can reject emitting a large block of
this text in one shot; if a big Write is blocked, **seed the file from `_source/scratchpad/seed/…`
(a disk copy, no generation) and correct it with many small 1–2-word edits against the slices** — the
filter limits generation SIZE, not the work. Either way, EVERY word ends up image-verified.

## Self-verify before returning (adversarial re-read)
Re-open each column's slices and compare word-for-word to your output. Check: guillemets balanced,
zero nesting, no stray `« »` left unflipped, no ASCII `<>`; `[PG N]` present once per column and
increasing; section numbers sequential from 1; no consonantal J/j left; the doxology matches the image
exactly; no catena/Greek/footnote/running-head/Delarue-number leaked in; and
`LATIN/…` body == `passB_final/…` byte-for-byte.

## Return (as your final message — this is data, not prose)
- columns covered (first–last) and `[PG]` anchor count
- section range (e.g. 1..6), guillemet counts (»=X «=X)
- the exact doxology tail you transcribed
- every doubtful/illegible word (with column) and every Greek block you skipped (with column)
- whether a content-filter block was hit and how you cleared it

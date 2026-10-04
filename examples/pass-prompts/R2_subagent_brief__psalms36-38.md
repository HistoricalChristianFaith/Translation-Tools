# PASS R2 re-collator brief — Origen, Homilies on Psalms 36–38 (PG 12), issue #149

You are ONE R2 re-collator. You independently re-read the ENTIRE base of **your assigned homily**
word-for-word against the Migne PG 12 page images, with the **IMAGE as the ONLY reference**. Do NOT
open any English (Heintz), the Trigg Greek, or Lommatzsch — those are other passes. At R2 the base is
a pure diplomatic PG transcript, so **every base↔image divergence is a real slip**: fix it in place.

## Your evidence (paths relative to project root `Origen of Alexandria/Homilies on Psalms 36-38/`)
- **Primary reading unit:** `_source/scratchpad/slices/col{N}_s0.png … _s3.png` (top→bottom, overlapping,
  large & sharp). Read all 4 per column, in order.
- Full column (orientation): `_source/scratchpad/cols/col{N}.png`.
- Noisy tesseract seed (SCAFFOLD ONLY, never trust a word): `_source/scratchpad/ocr/col{N}.txt`.
- For a hard/faded/margin-cut word, make a **fresh zoom crop** with PIL from `_source/pg12_pages/`
  (leaf L → cols 2L−9 (odd, left half), 2L−8 (even, right half); split logic in
  `_source/scratchpad/split_cols.py`). Write crops to `_source/scratchpad/r2crops/`.
- Layout: on each leaf, left half = odd column, right half = even column. A thin strip of the
  neighbouring column may bleed at a crop edge — ignore it, transcribe only your column.

## Method
For EACH column of your homily, in order:
1. Open the 4 slices, read the Latin from the image, and form the expected text **independently**
   (don't just skim the current base for plausibility — reconstruct it fresh, then diff).
2. Diff your independent reading against the current base line in `_source/passB_final/homily{NN}.txt`.
3. Treat every mismatch as a candidate slip and adjudicate ON THE IMAGE. Hunt especially for the
   errors a first pass misses: **dropped/added words, dropped clauses, wrong word-forms
   (case/tense/number/person), missing or mis-sequenced section numbers, dropped/added guillemets,
   italic/roman quote-boundary errors, anchor placement at column tops.**
4. Apply each fix (see "How to edit" below). Then re-read the changed span against the slices once more.

## Conventions to preserve exactly (these are the base's rules — do not "modernize")
- **Scripture = italic in this edition's body** → wrapped `»…«` (reversed guillemets, `»` opens,
  `«` closes, no interior spaces). Printed `«»` appear ONLY in lemma headings. Interrupting roman
  `inquit`/`ait`/`ergo`/`ait ille` sits OUTSIDE the guillemets, splitting a quote into adjacent pairs
  (e.g. `»A Domino«, inquit, »gressus hominis diriguntur«`). **Verify every italic/roman boundary on
  the image — this is the single most error-prone convention.** Roman loose allusions/paraphrases stay
  UNWRAPPED.
- `[PG N]` anchor inline at the exact point column N's text begins (first word of that column, even
  mid-sentence). One per column, monotonically increasing.
- Section numbers: bold `1.` `2.` … at paragraph starts, from 1, in sequence.
- **J→I / j→i uniform** (no consonantal J/j may survive). Keep u/v as printed. `æ/œ→ae/oe`. Keep ALL
  other edition spellings: `coelum foenum foenerat tricesimum(Ps37 seam) trigesimum(Ps38 seam)
  charitas caeteri Istrahel Moyses naupagii coepit`, doubled/simplified consonants as printed.
- **NO Greek** in the body. Catena/Selecta blocks, bilingual Greek+Latin scholia, column-foot Corderii
  Greek footnotes, Migne's italic Scripture-reference footnotes, running heads, and stray Delarue
  3–4-digit inline column numbers are ALL excluded — if the current base accidentally leaked any, remove
  it. Catena columns **1368, 1389, 1390** are correctly absent (never transcribe them).
- Editor marks `⟨⟩ [ ] …` only if the image prints them; **never fill a lacuna**.

## Facts already image-verified — CONFIRM, do NOT "fix" away
1. **homily05 truncates with NO doxology.** Migne ends mid-clause at `…in saeculum aeternum esse`
   (col 1367), no terminal punctuation, then the Ps 37 catena. Do NOT add `Amen.` or lacuna dots.
   Confirm the truncation on the image; if you judge a lacuna mark is warranted, that is an R6 call —
   note it, do not fill.
2. Ps 37 seam prints *tricesimum*; Ps 38 seam prints *trigesimum* (both correct as printed).

## How to edit (filter-safe, byte-identity-safe, parallel-safe)
Your two output files share an identical body. For each fix, apply the SAME small Edit to BOTH:
- `_source/passB_final/homily{NN}.txt`
- `LATIN/homily{NN}_latin.txt`
Use a unique `old_string` (a few words of context) → `new_string`; the body text is identical in both
files, so the same edit lands in both and keeps them byte-identical. **Keep every Edit SMALL** (a
sentence, or 3–5 words if a larger one is blocked) — a large Latin block can trip an HTTP-400
content-filter false-positive on OUTPUT SIZE (not policy); if blocked, split into smaller edits.
Do NOT touch `build_latin.py`, `validate.py`, `recollation_pass.md`, or `uncertain_readings.md` — the
orchestrator owns those. Do NOT edit any homily but your own.

## Self-verify before returning
Re-read every changed span against the slices. Confirm: guillemets balanced & zero-nested, no stray
`« » < >`, no consonantal J/j, `[PG N]` present once per column & increasing, sections from 1, doxology
matches image (or h05 truncation preserved), no catena/Greek/footnote/running-head/Delarue-number leak,
and the two bodies still identical (same edits applied to both).

## Return (as your final message — DATA, not prose; the orchestrator assembles the shared logs)
- **homily NN**, columns re-read (first–last), anchor count.
- **CHANGES**: one line each as `col N: "before" → "after" (why, from image)`. If none: "no changes".
- **CONFIRMED**: notable items you checked and found already correct (esp. flagged uncertain_readings
  items, cut-margin columns, doxology/truncation, italic/roman boundaries).
- **RESIDUAL OPEN**: any word still doubtful after fresh crops (col + your best reading + the doubt).
- **UNCERTAIN_READINGS updates**: resolved items to mark, or new items to add.
- Whether a content-filter block was hit and how you cleared it.

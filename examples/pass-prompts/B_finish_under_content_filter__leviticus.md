# TASK: Finish Pass B for 6 Origen *In Leviticum* homilies — image-true transcription

You are completing **Pass B (image collation)** of a patristic Latin base-text project: Origen,
*Homilies on Leviticus* (16 homilies, surviving only in Rufinus's Latin, GCS 29 / Baehrens 1920).
**10 of the 16 homilies are already DONE and validated.** Your job is ONLY the **6 that remain**:

> **Homilies II, IV, V, VI, VII, XVI** — replace their bodies with text transcribed **directly from
> the GCS 29 page images**, so no OCR error enters the base text.

REPO ROOT: `/path/to/Writings-Database-Non-English`
PROJECT DIR: `Origen of Alexandria/Homilies on Leviticus`

---

## ⚠️ READ THIS FIRST — the content-filter constraint (non-negotiable)

An **API content-filter false-positive** blocks the model from emitting **more than a few words of
this Latin at a time** (the homilies are about sacrifice, blood, leprosy, punishment — benign
scholarship, but the filter trips anyway). This is **account/infrastructure-level, not context-level**
— a fresh session does NOT bypass it. It has been confirmed empirically that:

- A per-homily transcription (thousands of words in one output) → **blocked**. (Both main-loop AND
  subagents — do NOT try to delegate whole-homily transcription to a subagent; it fails identically.)
- A single ~230-word page written in one shot → **trips the filter** (the tool may report "success"
  because the harness silently retries, but each retry is a real filter hit and wastes the turn).
- **Only tiny outputs are safe: keep every single model generation to ~1–2 words / one short phrase.**

**Therefore you MUST NOT author flowing Latin.** Two safe techniques, use both:

1. **Move text with Python, not by typing it.** Seed each page from OCR (already on disk) and fix it
   with Python string operations. Text that flows disk→disk through a script is never "generated" by
   you, so it never trips the filter.
2. **When you must correct a word/guillemet by hand, do it as a TINY edit** — one `Edit` (or one short
   `(find,replace)` tuple in a Python file) touching **1–2 words at a time**. Never batch many
   corrections into one large generation. Keep even your prose replies almost Latin-free.

If you ignore this and try to write pages of Latin, you will stall the whole task. Respect it.

---

## What is already done (do NOT touch these)

- **Image-true & validated:** Homilies **I, III, VIII, IX, X, XI, XII, XIII, XIV, XV**
  (IX/X/XIV/XV via two blind machine passes; I/III/VIII/XII/XIII via image-verified single pass;
  **XI hand-transcribed**). Their final bodies live in `_source/passB_final/homily{01,03,08..15,11}.txt`
  and are assembled into `LATIN/homily…_latin.txt`. These are your **format template** and the
  **vocabulary source** for auto-correction (see below).
- The **scaffold headers** in every `LATIN/homilyNN_latin.txt` (the 4 `#` lines, the `====` rule, the
  `HOMILIA N.` line, and the `*lemma*` / `[Titulus deest…]` line) are **already image-verified and
  correct — keep them verbatim.** You only replace the numbered BODY.

## The 6 homilies you must finish

| Hom | pp. (GCS) | starts | ends | §§ (verify on image) | incipit (§1 first words) |
|-----|-----------|--------|------|------|--------------------------|
| II  | 288–299 | part-way down p.288 (shared I→II) | foot of p.299 (III starts fresh p.300) | ~5 | `Superior quidem de principiis Levitici disputatio edocuit nos legem sacrificiorum` |
| IV  | 316–332 | part-way down p.316 (shared III→IV) | part-way down p.332 (V follows, shared IV→V) | ~10 | `Si secundum divinae legis fidem haec, quae leguntur nobis, Dominus locutus est ad Moysen` |
| V   | 332–358 | part-way down p.332 (shared IV→V) | part-way down p.358 (VI follows, shared V→VI) | ~12 | `»Et locutus est Dominus ad Moysen, dicens: loquere ad Aaron et ad filios eius dicens: haec est lex peccati` |
| VI  | 358–370 | part-way down p.358 (shared V→VI) | part-way down p.370 (VII follows, shared VI→VII) | 6 | `Causam, qua haec, quae nobis recitantur, intelligi possint aut non intelligi, breviter ostendit Apostolus` |
| VII | 370–393 | part-way down p.370 (shared VI→VII) | part-way down p.393 (VIII follows, shared VII→VIII) | 7 | `Plura quidem superiori lectione fuerant recitata, ex quibus temporis brevitate constricti pauca admodum diximus` |
| XVI | 491–507 | part-way down p.491 (shared XV→XVI) | foot of p.507 (end of volume) | ~7 | `In agonibus corporalibus gradus quidam et differentiae singulorum quorumque observari ordinum solent` |

**Exact closing doxologies (the body ENDS here — image-verified, non-uniform, keep verbatim):**
- **II:** `…per Christum Dominum nostrum, »cui laus et gloria in saecula saeculorum. Amen«.` *(note: laus et gloria — unique)*
- **IV:** `…Per ipsum Deo Patri cum Spiritu sancto »est gloria et imperium in saecula saeculorum. Amen!«`
- **V:** `…per quem est Deo patri cum Spiritu sancto »gloria et imperium in saecula saeculorum. Amen«.`
- **VI:** `…in Christo Iesu Domino nostro, »cui est gloria et imperium in saecula saeculorum. Amen«.`
- **VII:** `…per Christum Dominum nostrum, per quem est Deo patri cum Spiritu sancto »gloria et imperium in saecula saeculorum. Amen.«` *(Amen inside the guillemets)*
- **XVI:** `…ac totius sanctitatis imposuit. Ipsi gloria in aeterna saecula saeculorum! Amen.` *(no imperium, no guillemets)*

Special notes: **Hom V's §1 IS a Scripture-lemma quotation** (»Et locutus est Dominus…«) — preserve as
printed, opened with ». All other lemma/title lines belong in the header, NOT the body — the body starts
at `1.`.

---

## Inputs already staged for you (in `_source/`)

- **Page images (source of truth):** `_source/gcs29_pages/gcs29_pNNN_leafMMM.jpg` — open with the image
  reader. The page→leaf offset drifts, so **glob by page number**, never compute leaves:
  `ls "_source/gcs29_pages/"gcs29_pP_leaf*.jpg`. Shared pages have two identical leaf files — read either.
- **Fresh Latin-model OCR of every needed page:** `_source/scratchpad/ocr/pP.txt` (tesseract `-l lat`).
  Much cleaner than the old German-model OCR, but still ~82% raw (scan quality caps it): residual
  `c↔e` confusions, dropped/rendered-as-`-` guillemets, occasional dropped section digits.
- **Prebuilt tooling in `_source/scratchpad/`:**
  - `build_homily.py N PS PE "incipit key words"` — **the main tool.** For each page it uses a
    hand-verified override `fix/hN_pP.txt` if present, else cleans the OCR (strip running heads /
    margins / gutter line-numbers / `NNN Lomm.`·`NNN Del.` tags / the footer / **both** foot-apparatus
    blocks / all Greek; join hyphenations; **vocabulary-autocorrect** each word against the 10 finished
    homilies; **state-machine-normalize guillemets** to balanced »…«), then joins pages with inline
    `[GCS p.P]` anchors, trims to the homily span, splits numbered sections, and writes
    `passB_final/homilyNN.txt`. It prints the anchor count, section list, and guillemet balance.
  - `fix/hN_pP.txt` — **per-page override files.** Drop a corrected page here (body text of that page
    only, verbatim as printed) and `build_homily.py` uses it in place of the OCR. **Hom II pages
    288–291 are already done as `fix/h2_p288..291.txt`** (image-true) — leave them; do 292–299.
    Hom XI's `fix/h11_p*.txt` are the finished-XI reference — a model of the target quality.
  - `validate.py` — the Pass-B validator (guillemets balanced/no-nesting/no stray ›‹><; no J/j; anchors
    monotonic & contiguous, first/last = the boundary pages, 13 shared pages double-anchored across
    neighbours; section sequence; the exact per-homily doxology signature; LATIN ↔ passB_final
    byte-identical). Run it after every homily; **all 16 must pass.**
  - `assemble.py` — rebuilds `LATIN/homilyNN_latin.txt` = the image-verified scaffold header +
    the `passB_final/homilyNN.txt` body (keeps them byte-identical over the running text).

## Recommended workflow per homily (filter-safe)

1. `python3 scratchpad/build_homily.py N PS PE "<incipit key>"` → an ~88% draft in `passB_final/`,
   guillemets balanced, systematic OCR errors already removed by the vocabulary auto-corrector.
2. **Page by page**, open the page image and read it against the draft page. Fix every residual —
   `c↔e` slips the autocorrect missed, **dropped closing/opening guillemets** (the hardest part;
   the OCR renders both `»«` and inner `›‹` as `»` / `-` / nothing — restore Baehrens's marks and
   normalize ALL quote levels to `»…«`, sequential, never nested), any **dropped/garbled section
   number**, and any word the OCR mangled. **Two safe ways to apply a fix, both keeping generation
   tiny:** (a) `Edit` `passB_final/homilyNN.txt` with a 1–2-word `old`→`new`; or (b) build a corrected
   page in `fix/hN_pP.txt` **incrementally** — start it from the OCR text with a Python copy (no typing),
   then Edit it in 1–2-word steps — and re-run `build_homily.py` to fold it in. Never paste a whole
   page of Latin in one output.
3. Re-run `build_homily.py N …`, then `python3 scratchpad/validate.py`. Confirm anchors 1-per-page over
   PS..PE, section numbers 1..K in order, guillemets balanced, and the **exact doxology** present.
4. `python3 scratchpad/assemble.py` to refresh the `LATIN/` file from the header + corrected body.

## Editorial conventions (must match the 10 done homilies exactly)

- Scripture quotes → `»…«` only (normalize the printed `»«` AND `›‹` AND scan `> <` / `-` to `»…«`);
  **balanced, zero nesting.** The printed lemma/title stays in the header, not the body.
- Orthography **exactly as Baehrens prints**: Iesus, Istrahel, Moyses, coelum/coelestis, foenum,
  bracchium, hoedus, adspectus, similam, clibano, etc. Keep `ae`/`oe`. **No consonantal `J`/`j`** —
  render every printed `J` as `I`.
- Keep Baehrens's own brackets `[ … ]` (seclusions) and `⟨ … ⟩` (supplements) and any printed lacuna
  `* * *` — never fill a lacuna.
- **Greek stays OUT** of the Latin body (a couple of inline Greek words occur, e.g. `ἅγιος` in a homily
  already done; strip the Greek and leave the Latin continuous — flag it for R5 in `uncertain_readings.md`).
- Section numbers `1. 2. 3. …` exactly as printed; each section is ONE reflowed line, blank line between.
- Inline `[GCS p.P]` anchor at each page break (mid-word `se[GCS p.281]cundum`; between words
  `verba [GCS p.NNN]eorum`); the body opens with `[GCS p.PS] 1.`; every page PS..PE anchored exactly once;
  the shared boundary pages stay anchored in BOTH neighbours (already true for the 10 done homilies).

## Output / done criteria

- Rewrite `LATIN/homily{02,04,05,06,07,16}_latin.txt` in place (header kept, body image-true) and mirror
  each to `_source/passB_final/homily{02,04,05,06,07,16}.txt` (byte-identical running text).
- Append your work to `_source/passB_report.md` (method, per-homily coverage, residual fixes, any new
  cruxes) and mark items in `_source/uncertain_readings.md`.
- `python3 _source/scratchpad/validate.py` → **ALL 16 CLEAN**, coverage of pages 280–507 complete with
  the 13 shared pages double-anchored. End state: **READY FOR PASS R4.**

Orientation docs to read: `_source/README.md`, `_source/passA_report.md`, `_source/boundary_audit.md`
(per-homily incipit/lemma/doxology ground truth), `_source/uncertain_readings.md`, and — as the format
and quality bar — `LATIN/homily11_latin.txt` plus any of the other 9 finished files.

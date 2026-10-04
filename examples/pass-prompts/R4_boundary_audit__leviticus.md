# TASK: Execute Pass R4 — Boundary & completeness audit of all 16 Origen *In Leviticum* homilies

You are running **Pass R4** of a patristic Latin base-text project: Origen, *Homilies on Leviticus*
(16 homilies, surviving only in Rufinus's Latin, GCS 29 / Baehrens 1920). **Pass B is complete: all 16
homilies are image-true and `validate.py` reports ALL 16 CLEAN.** Your job now is the **boundary &
completeness audit**: re-verify, **against the GCS 29 page images**, that every homily starts and ends
at the exact printed point and that nothing inside its span is missing, duplicated, or misplaced.

REPO ROOT: `/path/to/Writings-Database-Non-English`
PROJECT DIR: `Origen of Alexandria/Homilies on Leviticus` (cd here; all paths below are relative to it)

## What R4 is (and is NOT)
- **IS:** verify each homily's **start** (HOMILIA heading + lemma/title line + §1 incipit), its **end**
  (the exact printed doxology), the **13 shared-page splits** between neighbouring homilies, and
  **internal completeness** (no printed line/paragraph/section/page dropped, none duplicated, anchors at
  the true page breaks). The **GCS 29 page image is the sole arbiter.**
- **IS NOT:** the systematic sentence-by-sentence English-oracle back-check (that is **R3**), the Migne
  cross-check (**R1**), or the whole-corpus orthography/consistency sweep (**R5**). Do not do those here.
  You MAY consult the Barkley English oracle (`_source/oracle/oracle.pdf`, a PDF you can read)
  **only as a completeness tripwire** — e.g. if a paragraph exists in English with no Latin counterpart,
  that flags a possible dropped passage — but **adjudicate every call on the GCS image, and never
  rewrite the Latin to match the English.**

## ⚠️ CONTENT-FILTER CONSTRAINT — carry it forward (non-negotiable)
An **API content-filter false-positive** blocks emitting more than **~1–2 words of this Latin per model
generation** (subject: sacrifice/blood/leprosy — benign scholarship). It is **account/infrastructure-
level**: it blocks whole-page/whole-homily transcription in the **main loop and in subagents alike** (a
tool may falsely report "success" while the harness silently retries — each retry is a real filter hit).
- **Auditing itself is filter-safe** — reading page images and comparing them to the existing text
  generates no Latin.
- **Any FIX must be a TINY edit:** one `Edit` (or one short `(find,replace)` tuple), **1–2 words** at a
  time. If a genuinely dropped chunk must be restored, **seed it from the on-disk OCR**
  (`_source/scratchpad/ocr/pP.txt`) with a Python copy (disk→disk, never typed), then correct it in
  1–2-word steps against the image. **Never author flowing Latin.** Keep even prose replies near-Latin-free.

## Inputs & tooling (all staged)
- **Ground truth = page images:** `_source/gcs29_pages/gcs29_pNNN_leafMMM.jpg`. The page→leaf offset
  drifts (+59→+72) and **13 pages are double-scanned**, so **glob by PAGE number, never compute leaves**:
  `ls "_source/gcs29_pages/"gcs29_p<P>_leaf*.jpg` and open the first match with the Read tool (it renders
  images). Shared pages have two identical leaf files — read either.
- **The text under audit:** `LATIN/homily{01..16}_latin.txt` (scaffold header + body) and the mirror
  `_source/passB_final/homily{01..16}.txt` (running body; **git-ignored**). They are byte-identical over
  the running text and must stay so — edit `passB_final/homilyNN.txt`, then re-mirror centrally with
  `assemble.py` (below). Do **not** edit the header lines unless the image proves one wrong (log it).
- **On-disk OCR** (fallback seed for any restore): `_source/scratchpad/ocr/pP.txt` (tesseract `-l lat`).
- **Scripts** (`_source/scratchpad/`):
  - `validate.py` — the Pass-B/R validator: guillemets balanced/no-nesting/no stray ›‹><; no J/j; anchors
    monotonic & contiguous, first/last = the boundary pages, the 13 shared pages double-anchored across
    neighbours; section sequence from 1; exact per-homily doxology signature; LATIN ↔ passB_final
    byte-identical. **Currently ALL 16 CLEAN — it must stay ALL 16 CLEAN after R4.** (Its `SPAN` dict and
    `DOX` dict are the authoritative per-homily page-spans and doxology signatures — read them.)
  - `assemble.py` — rebuilds every `LATIN/homilyNN_latin.txt` = image-verified scaffold header + the
    `passB_final/homilyNN.txt` body. **Idempotent.** Run it **once, centrally** after all edits (never
    concurrently from parallel workers — it writes all 16 files).
  - `build_homily.py` — the Pass-B page-seeded builder. **Do NOT run it in R4** — it would overwrite the
    finished hand-collated bodies. It is listed only so you recognise and avoid it.
- **Ground-truth reference docs — READ THESE FIRST:**
  - `_source/boundary_audit.md` — the Pass-A boundary audit: every homily's heading, **incipit**, and
    **explicit** (closing words), the 13 shared/double-scanned pages, garbled-numeral resolutions. This
    is your primary checklist of what each boundary should read.
  - `_source/passB_report.md` — what Pass B did per homily (spans, section counts, restored numerals,
    stripped-Greek locations, the one open crux).
  - `_source/uncertain_readings.md` — the running log; several items are explicitly flagged **"for R…"**.
  - `_source/README.md` — conventions and the pass pipeline.

## The per-homily audit checklist (arbiter = the image)
For **each** homily 1..16, open the images across its span and confirm:
1. **Start.** The centered `HOMILIA N.` heading and the `*lemma*` / `[Titulus deest …]` line in the
   scaffold header match the print; the body's `§1` incipit begins at the exact printed first words
   (cross-check `boundary_audit.md`). **No tail of the previous homily leaked into the body**, and **no
   opening words of this homily were dropped.**
2. **End.** The body stops at the exact printed doxology (match `validate.py`'s `DOX[N]` signature
   verbatim). **Nothing of the next homily leaked in after it**, and **nothing before it was dropped.**
3. **Shared-page split (the 13 pages: 288, 316, 332, 358, 370, 393, 417, 440, 454, 467, 478, 487, 491).**
   On each, the split point on the physical page is exactly the printed `HOMILIA` heading: text **above**
   the heading belongs to the homily that closes there; text from the incipit **down** belongs to the
   homily that opens there. Confirm the page is anchored **once in each** neighbour and no line is
   double-counted or dropped at the seam.
4. **Internal completeness.** Every printed page in `SPAN[N]` is present and `[GCS p.P]`-anchored **exactly
   once**, in order; read each page top-to-bottom and confirm **every printed line of Rufinus's Latin**
   appears in the body between the correct anchors. Look hardest where risk is highest: **page breaks**
   (an anchor sitting a few words early/late; re-pin mid-word joins like `pres[GCS p.NNN]byteri`),
   **stripped apparatus/Greek blocks** (confirm **no Latin body line went out with the Greek** — see the
   flagged spots below), and **around restored section numbers**.
5. **Section numerals.** Every printed section number is present, correct, and in sequence; none invented,
   none dropped.

## Targeted spots already flagged (verify these explicitly, on the image)
- **Hom II p.299 — doxology punctuation crux.** Image may print `Amen!«`; the mandated/validated
  signature is `Amen«.`. Re-examine on the leaf and either resolve or re-confirm the flag (if you change
  the doxology, keep `validate.py`'s `DOX[2]` in sync — coordinate, don't silently break the validator).
- **Restored section numerals — confirm each sits at the correct printed spot:** IV §8 (p.327; printed
  `8.` OCR-read as `S.`), IV §3 (p.318), V §5 (p.343)/§7 (p.345)/§8 (p.347), XVI §3 (p.497)/§6 (p.502).
- **Stripped Greek — confirm no Latin was lost with it:** V Philocalia foot-blocks pp.333–334 + inline
  gloss p.355; VI recapitulatio gloss p.360; VII Theodoret catena p.386; VIII Procopius catena pp.405–409.
- **Hom VIII p.405 — OPEN crux** (a Greek-word-fused Latin line `Ἰοῦς … apparuit`): re-read leaf 481/482
  and confirm the Latin body line is complete/correct at that seam.
- **Hom I p.280** has no printed lemma (`[Titulus deest …]` — do not invent one); **Hom V §1** is a
  Scripture-lemma quotation opening with `»` (preserve as printed). Confirm both on the image.

## Recommended execution (this is how Pass B's blocked homilies got finished)
The audit is large (16 homilies, ~228 pages). **Fan out with subagents**, because the filter caps the
*size of each generation*, not *which agent* emits it, and subagents also solve the context limit:
- Spawn **one auditor subagent per homily** (or per small group), each given: this checklist, its homily's
  `SPAN`/incipit/doxology, and the strict **tiny-edit** discipline for any fix. Each edits **only its own**
  `passB_final/homilyNN.txt` → disjoint files → safe to run in parallel. Tell each to **NOT** run
  `assemble.py` or `build_homily.py`, and to report **Latin-free** (page numbers + PASS/FAIL + any fix
  locations, never pasted Latin).
- **De-risk first:** launch one or two, confirm they audit and (if needed) edit without a filter stall,
  then launch the rest.
- **You (main loop) are the orchestrator:** after all auditors finish, run `assemble.py` **once**, then
  `python3 _source/scratchpad/validate.py` and confirm **ALL 16 CLEAN**. Independently spot-verify each
  homily (guillemets balanced, anchors 1/page over its span, section sequence, doxology present) with a
  small read-only Python check.

## Output / done criteria
- **Fix in place** any boundary or completeness defect the image reveals (tiny edits; OCR-seeded restores
  for genuine drops). If the audit finds **no** defect for a homily, that is a valid result — record it
  as verified.
- **Write `_source/r4_boundary_audit.md`** (mirror the style of `boundary_audit.md`): per-homily
  start/end/shared-split/completeness verdict, every correction made (by page, Latin-free), and any
  residual crux. **Update `_source/uncertain_readings.md`** (mark resolved items RESOLVED; add new ones).
  Append a short R4 section to `_source/passB_report.md` **or** note in the new report that R4 supersedes
  the Pass-B boundary state.
- **Keep `LATIN/` ↔ `passB_final/` byte-identical** (via `assemble.py`) and **`validate.py` → ALL 16
  CLEAN**, coverage of pages 280–507 complete with the 13 shared pages double-anchored.
- **End state: READY FOR PASS R1** (Migne cross-check) — the next pass in the pipeline (see README:
  order is B → R4 → R1 → R3 → R5 → R6 → R7).

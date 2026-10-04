# R3 Collator Brief — Origen, *Homilies on Leviticus* (oracle back-check)

You are ONE collator in Pass R3. You collate **one homily's** finished Latin base text against the
copyright English oracle (**Barkley, FOTC 83**), using the English purely as a **detector** for
meaning-level defects, and you **adjudicate every candidate on the GCS 29 page image — the sole
arbiter.** Barkley is a detector, never an authority: you correct the base to match **its own witness
(GCS)**, never toward the English.

PROJECT DIR (cd here): `/path/to/Writings-Database-Non-English/Origen of Alexandria/Homilies on Leviticus`
All paths below are relative to it.

## ⚠️ CONTENT-FILTER CONSTRAINT (non-negotiable)
An API content-filter false-positive blocks emitting more than ~1–2 words of this Latin per model
generation (subject: sacrifice/blood/leprosy — benign patristic scholarship). It blocks in subagents
too. Therefore:
- **Collation is filter-safe** — reading GCS images, the Barkley slice, and the on-disk Latin and
  comparing them generates no Latin. Do that.
- In your reasoning AND your final report, **do NOT quote Latin.** Refer to base readings by **GCS
  page number + English description**. Name a Latin token in ≤1–2 words only if unavoidable.
- The oracle is **English** → quoting Barkley is filter-safe, but it is **copyright: consult, never
  copy.** Keep any Barkley quotation to the few words needed to name a discrepancy (fair use).
- **Any FIX is a TINY edit:** ONE `Edit` of 1–2 words to your `_source/passB_final/homilyNN.txt`,
  verified on the GCS image. For a genuine dropped chunk, seed from the on-disk OCR
  (`_source/scratchpad/ocr/pP.txt`) via a Python disk→disk copy, then correct 1–2 words at a time
  against the GCS image — never author flowing Latin yourself.
- **Do NOT** edit `LATIN/` files, the scaffold header, or any doxology text (doxologies are coupled to
  `validate.py`; if a doxology looks wrong, FLAG it in your report, do not edit). Do NOT run
  `assemble.py`/`validate.py`/`build_homily.py` — the orchestrator runs those centrally at the end.
  Edit **only** your own `passB_final/homilyNN.txt`.

## ⚠️ Rufinus's freer Leviticus rendering
Rufinus intervened more freely here than in the other Pentateuch homilies, and Barkley smooths
further, so expect **looser Latin↔English tracking than a normal oracle pass.** Most discrepancies
will be **benign translation latitude, not Latin defects** — expect to log almost everything as KEEP
and fix very little. Adjudicate every candidate on the GCS image; never on Barkley.

## What counts as a candidate (meaning-level only)
Flag where the English implies a real meaning difference: a dropped or added clause, a wrong word
sense, mis-parsed syntax, a wrong referent/antecedent, a mis-scoped Scripture quotation, a wrong
proper name / numeral / negation, a doxology anomaly. **Ignore pure translation freedom:** word
order, idiom, expansion/compression, participle↔finite, active↔passive, English-vs-Old-Latin verse
wording, orthography/spelling. Do NOT re-litigate Migne (R1) editorial variants or orthography (R5).

## Inputs
- **Base under check:** `_source/passB_final/homilyNN.txt` (running body with `[GCS p.N]` anchors and
  `N.` section numbers; edit THIS file only).
- **Oracle slice (English):** `_source/scratchpad/oracle/oracle_homNN.txt` (your homily only,
  pre-extracted; Barkley's `(2) (3) …` section numbers track the Latin `N.` §-numbers).
- **GCS image (the arbiter):** glob by PAGE number, never compute leaves —
  `ls _source/gcs29_pages/gcs29_p<P>_leaf*.jpg` and open the first match with the Read tool (it
  renders the image). Shared boundary pages return two leaves; the first is fine.
- **OCR restore seed (only if a genuine drop must be restored):** `_source/scratchpad/ocr/pP.txt`.

## Awareness (do not duplicate; already logged in R1/R4 — confirm, don't re-flag as new)
- Doxologies are intentionally **non-uniform** across homilies (see `boundary_audit.md` §Doxology).
  Do not "correct" a doxology toward another homily's wording.
- Hom XI p.453 §3 — Heb 12:9 attributed to **James** in GCS/base (Migne/Delarue emend to **Paul**);
  Baehrens keeps James as the witnesses transmit. Base is correctly image-true — KEEP if you meet it.
- Hom IX — the ark called "testimony" (§5) vs "covenant" (§9): a genuine GCS-internal inconsistency,
  image-true. KEEP if you meet it.
- Inline Greek was stripped from the Latin body (R5 owns reinsertion); Hom XI p.448 retains `ἅγιος`
  by design. Not R3's concern unless the English shows a **Latin clause** was actually lost.

## Procedure
1. `cd` to the project dir. Read your `oracle_homNN.txt` and your `passB_final/homilyNN.txt` fully.
2. Walk the homily in order, section by section, aligning on the shared §-numbers and `[GCS p.N]`
   anchors. At each meaning-level discrepancy, note the GCS page it falls on.
3. Open that GCS page image (glob by page number) and adjudicate:
   - **GCS shows the base departs from GCS → FIX** (tiny 1–2-word Edit to passB_final, image-verified).
   - **GCS supports the base, Barkley merely differs → KEEP** (log it, move on).
4. Watch hardest at: Scripture-quotation scope/wording, proper names, numerals, negations,
   clause presence/absence, referents, and the doxology.

## Output — return a Latin-free report (your final message) with:
- Homily number and GCS span.
- A bullet per meaning-level candidate: **GCS page + English description of the discrepancy +
  verdict (KEEP / FIX) + one-line GCS-image adjudication.** Minimal Barkley quotation only.
- Any FIX: state the GCS page, what the base had vs what GCS prints (English description; ≤1–2 Latin
  words if unavoidable), and confirm the Edit was applied to `passB_final/homilyNN.txt`.
- If you found nothing to fix, say so explicitly (that is the expected common outcome).
- Do NOT run validate.py/assemble.py. Do NOT quote flowing Latin anywhere.

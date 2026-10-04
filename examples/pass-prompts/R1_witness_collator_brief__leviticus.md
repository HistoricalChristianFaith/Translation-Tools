# R1 Migne cross-check — collator brief (shared)

You are one collator in **Pass R1** of a patristic Latin base-text project: Origen, *Homilies on
Leviticus* (Rufinus's Latin). The base text is **image-true against GCS 29** (Baehrens 1920) and already
passes a validator. Your job: collate ONE homily's base text against the **secondary Latin witness, Migne
PG 12**, and treat every divergence as a signal — **adjudicated on the GCS 29 page image, which is the sole
arbiter.** Migne is a *witness*, not an authority.

REPO PROJECT DIR (cd here): `Origen of Alexandria/Homilies on Leviticus`
All paths below are relative to it.

## ⚠️ CONTENT-FILTER CONSTRAINT — non-negotiable
An **API content-filter false-positive** blocks emitting more than **~1–2 words of this Latin per
generation** (subject: sacrifice/blood/leprosy — benign scholarship). It blocks in subagents too.
- **Collation is filter-safe** — reading images and the on-disk text and comparing them emits no Latin.
- In your reasoning AND your final report, **do NOT quote Latin.** Refer to everything by GCS page number /
  Migne column number + an English description. Name a token in **≤1–2 words only if unavoidable.**
- If you ever feel the urge to transcribe a Latin phrase, DON'T — describe it in English instead.
- **Any FIX is a TINY edit:** a single `Edit` of **1–2 Latin words** to `_source/passB_final/homilyNN.txt`.
  Never author flowing Latin. If a genuine multi-word chunk is dropped (R4 found none), STOP and report it
  to the orchestrator rather than typing Latin.

## What R1 IS
An independent editorial line. Walk the base text in order against the Migne PG 12 Latin. Flag every
**substantive** divergence: a different word, word order, a clause present in one and absent in the other, a
Scripture-quotation wording/boundary (guillemet extent), a proper name, a numeral, a doxology formula. For
each, **open the GCS leaf and decide:**
- **GCS supports the base text** (base == GCS image) → the divergence is Migne's; **log it, make no edit.**
  (Expect this for the large majority — Migne is a different recension and diverges freely.)
- **The base text mis-transcribes GCS** (base != GCS image) → make a **tiny 1–2-word edit** to
  `passB_final/homilyNN.txt` so the base matches **GCS** (never "correct" GCS toward Migne).

Do NOT do the orthography sweep, the English-oracle check, or the apparatus pass here. If you notice a
genuine orthographic/word-level slip that GCS itself prints (a print typo), **log it for R5/R6, don't fix.**

## Inputs
- **Base text (EDIT THIS ONE ONLY):** `_source/passB_final/homily{NN}.txt` (NN zero-padded). It is
  body-only: paragraphs `[GCS p.N] K. <text>` (K = section number; `[GCS p.N]` anchors are inline, one per
  printed page, and may sit mid-paragraph). Do NOT touch the `LATIN/` files or any header/lemma line.
- **GCS 29 images (THE ARBITER):** open by PAGE number, never compute leaves:
  `ls _source/gcs29_pages/gcs29_p<P>_leaf*.jpg` and open the FIRST match with the Read tool (it renders
  images). Shared boundary pages return two leaves (double-scanned, identical page) — first match is fine.
- **Migne PG 12 images:** `_source/migne_pages/pg12_col<odd>-<even>_leaf<L>.jpg`. Formula: leaf L carries
  cols (2L−9, 2L−8); a column C is on leaf round((C+9)/2). Staged leaves: **207–293 (cols 405–578)**. Each
  leaf's running head `IN LEVITICUM HOMILIA <ROMAN>` (or `ORIGENIS` on a verso) tells you which homily it
  is. Read `_source/migne_columns.json` for your homily's `leaf_window`, `gcs_pages`, and predicted columns.
- **Reference (already authoritative, read as needed):** `_source/boundary_audit.md` (per-homily incipit,
  explicit, exact doxology wording as GCS prints it), `_source/r4_boundary_audit.md`. Use these to know
  what GCS prints without re-deriving it.

## Procedure
1. **Pin your Migne span.** Open leaves across your `leaf_window`; use the running heads to find your
   centered **`HOMILIA <ROMAN>`** heading (= your start column) and the NEXT homily's heading (= your end).
   If the heading is outside the window, widen (any leaf 207–293 is openable). Record the heading column.
2. **Read your base file** `_source/passB_final/homily{NN}.txt` end to end.
3. **Walk it in order.** For each stretch, view the GCS page(s) it anchors and the Migne column(s) covering
   the same text. Compare. The Delarue marginal numbers in Migne (e.g. 185, 203, 213…) equal the GCS
   `Lomm./Del.` margin tags — a fine alignment aid.
4. **At each substantive divergence,** open the GCS leaf and adjudicate as above. Watch hardest at:
   Scripture-quotation wording and guillemet extents, proper names/numerals, clause presence/absence, and
   the doxology. Migne routinely prints `J` (Jesus, Judaei, jugum) and `æ/œ` ligatures and its own spellings
   — those are Migne house style, **not** substantive divergences; don't log them.
5. **Fixes:** only where the GCS image shows the base mis-transcribed GCS. One 1–2-word `Edit` each; keep
   `[GCS p.N]` anchors, section numbers, and guillemet balance intact. **Do NOT alter any doxology wording**
   without flagging to the orchestrator first (doxologies are coupled to the validator).
6. Do **NOT** run `assemble.py`, `validate.py`, or `build_homily.py` — the orchestrator runs those centrally.

## Report back (Latin-free)
- Confirmed **Migne column range** for your homily + the **HOMILIA heading column**.
- A per-divergence list: `GCS p.<P> / PG col <C> — <English description> — verdict: [GCS confirms base; log
  Migne variant] OR [base fixed to match GCS: <1–2-word note>]`.
- Any base-text **edits** you made (file, what 1–2 words, GCS page that justifies it).
- Anything handed off to R3/R5/R6, and any doxology issue flagged (not edited).
- If you hit a filter stall or anything blocks you, say so plainly — do not paste Latin to work around it.

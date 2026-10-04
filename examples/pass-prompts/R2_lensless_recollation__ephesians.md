You are running **Pass R2 — independent, lensless image re-collation** on the Greek base text of
Origen's *Commentary on Ephesians* catena fragments (Gregg, *JTS* 3, 1902). GitHub issue #155.

## The state you inherit
Pass A (structure) and Pass B (image collation) are done. The base text is now a **pure diplomatic
transcription of Gregg's page images** — 37 fragment bodies, §§ I–XXXVII, one file each. Because no
editorial pass has run yet, **there is no intentional-departure list**: every place where the text
diverges from the image is a *real transcription slip*. That is exactly what R2 catches. This is the
strongest direct check on the transcription, so it runs before any witness-based pass.

## Your job
Re-read **every fragment body word-for-word against the Gregg page images**, with **NO external
witness as a lens** (do not open Cramer, Heine, or any other edition — this pass is lensless, image
only). Fix every genuine slip **in place** in the tracked files. Prioritise the error classes Pass B
is weakest on:
- **accents** (acute/grave/circumflex), **breathings** (smooth/rough), **iota subscript** (ᾳ ῃ ῳ),
  **final vs medial sigma** (ς/σ), diaeresis, apostrophe/elision;
- the **clarendon-vs-uncial-vs-regular type boundary** — i.e. whether a run is `* … *` (bold lemma
  word), `» … «` (uncial biblical quotation), or unmarked regular type, and the exact extent of each;
- dropped/duplicated words, wrong word-splits at line ends, and mis-transcribed nomina sacra.

## Where everything is
- **Edit these (git-tracked, authoritative):**
  `Origen of Alexandria/Commentary on Ephesians/GREEK/frag01_greek.txt … frag37_greek.txt`
  Each file = a 4-line header (`§ N | Eph ref`, `[JTS p.N] [Cramer n]`, `LEMMA: …`, `====`) then the
  § body. **Never alter the header or the `====` separator.** Only correct the body.
- **Ground truth images (read-only):**
  `Origen of Alexandria/Commentary on Ephesians/_source/gregg_pages/gregg_pt{I,II,III}_p{PAGE}_leaf{NNNN}.jpg`
  (~2240×3290, 400 dpi, highly legible). The page span for each § is in its header `[JTS p.N]`
  anchors and in the manifest.
- **Reference (read for context, do not treat as a witness):**
  `_source/passA/fragments_manifest.md` (the § → Eph-ref → JTS pp. → Cramer table),
  `_source/passB_report.md` (Pass B record + the carry-forward items below).
- **The OCR (`_source/gregg_jts1902_*_djvu.txt`) is unusable for Greek — never take Greek from it.**

## Conventions (must match exactly — do not change the policy, only correct the Greek)
- `» … «` uncial/small-caps = a biblical quotation/allusion Origen cites.
- `* … *` clarendon/bold = the Ephesians lemma word(s) recurring in Origen's running prose.
- `⟨ … ⟩` Gregg's supplement · `[ … ]` Gregg's seclusion/rubric brackets · `[[ … ]]` Gregg's double
  brackets · `…` printed lacuna (never fill).
- `[JTS p.N]` page anchors at each in-body page turn — verify each anchor sits at the correct
  page-turn word; do not add or remove pages.

## Technique — crop when in doubt (required for every uncertain glyph or type call)
Read the whole page image first, then enlarge any doubtful line ~3× from the original JPEG before
deciding. PIL is installed. Inline snippet (use a unique output name each time):
```
python3 - <<'PY'
from PIL import Image
im = Image.open("Origen of Alexandria/Commentary on Ephesians/_source/gregg_pages/gregg_ptII_p410_leaf0089.jpg").convert("RGB")
W,H = im.size
# (x0,y0,x1,y1) as fractions of width/height — tune to the line you need
c = im.crop((int(0.12*W), int(0.30*H), int(0.88*W), int(0.40*H)))
c = c.resize((c.width*3, c.height*3), Image.LANCZOS)
c.save("/tmp/r2_crop_UNIQUE.png")
PY
```
then Read `/tmp/r2_crop_UNIQUE.png`. Bold (clarendon) reads visibly heavier; uncial reads as small
capitals; regular is the light italic-style face.

## Scale & approach
37 fragments across ~58 pages (Part I pp.234–244, Part II pp.398–420, Part III pp.554–576). This is
heavy. You may fan out to parallel sub-agents batched by **contiguous page range** (so each page is
read once) — that worked well in Pass B — but every sub-agent must apply the identical conventions
above and edit the same `GREEK/fragNN` files. Whatever you do, cover all 37.

## Carry-forward items from Pass B (verify on the image; do NOT restructure)
1. **§ XXIX** body runs onto p.567 (three regular-type lines "εἶναι πρὸς τὴν γυναῖκα … ἡ γυνή."
   before § XXX). Confirm those lines and the `[JTS p.567]` anchor against p.567.
2. **§ XXXV** appears wholly on p.574 (manifest said 574–575). Confirm no p.575 turn exists in its body.
3. **§ IX** carries a second inline rubric `[Ὠριγένους]` mid-fragment. Leave it in place; **flag it
   for R4** (is it a re-attribution within § IX or a missed boundary?) — do not split the fragment.
4. **§ XV** embedded marginal note on iii 15 πατριά is printed by Gregg himself in `[[ … ]]` with his
   own English "[Marginal note]" label and Latin "scilicet" — that is faithful diplomatic text; leave
   it verbatim and in place (its final placement is an R5 question, not yours).
5. **§ XXVII** double-bracketed `[[ … ]]` v.17 passage (probably Severian) — keep both brackets.
6. **§ XII** printed lacuna `…` is in the lemma (header) only — none in the body.
7. **Sub-lemma `* *` convention split** (some fragments wrap `[v N]` verse headings in `* *`, others
   leave them plain): this is an intentional **R5** decision, **NOT an R2 fix**. Do not normalise it.
   In R2, only correct the *Greek letters/accents* inside those headings, never the marker policy.

## Discipline
- Do not renumber or re-scope fragments. If an image genuinely contradicts the manifest, **log it —
  do not silently change** structure.
- Do not start any other pass (R4, R1, R3, R5, R6, R7). Do not download anything or modify files
  outside `GREEK/` and the two log/report files below.

## Output
1. Apply all corrections in place in `GREEK/frag01…37_greek.txt` (headers/`====` untouched).
2. Append every correction and every residual doubt to
   `_source/passA/uncertain_readings.md` under a new `## Pass R2` section (§ number, JTS page, the
   word, what changed or the remaining doubt).
3. Write `_source/recollation_pass.md`: what you re-collated, count of corrections by class
   (accents/breathings/sigma/iota/type-boundary/word-level), per-fragment change tally, anything
   handed to R4/R5, and what still looks uncertain for the witness passes.
4. **Commit the text iteration** so the pass is a visible diff (this is why the base is git-tracked):
   ```
   git add "Origen of Alexandria/Commentary on Ephesians/GREEK/"
   git commit -m "origen commentary on ephesians: greek base text, R2 (lensless image re-collation)"
   ```
   (Commit only the `GREEK/` changes; the `_source/` logs are git-ignored by design. Direct to
   master, matching this repo's per-text commit history.)
5. Finish with a short summary: fragments touched, correction counts by class, and the top items
   left for R4/R5.

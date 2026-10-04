# Origen, *Homilies on Leviticus* — Latin base-text project (issue #146)

Origen's homilies on Leviticus survive **only in Rufinus of Aquileia's Latin translation**
(made c. 403–405, part of Rufinus's programme of Latinizing Origen's homilies on the Hexateuch —
the same enterprise that produced the Genesis, Exodus, Numbers, Joshua, and Judges homilies).
**The collection is complete: all sixteen homilies (In Leviticum homiliae I–XVI) are extant** —
no lost original series to reconstruct. They expound selected passages of Leviticus (the
sacrifices, the priesthood, clean and unclean, the feasts, the Day of Atonement, the jubilee),
read allegorically: the ritual law as the outer *carnis velamen* over an inner spiritual sense,
the sacrifices fulfilled in Christ and re-enacted in the soul.

> **Rufinus's own caveat (bears on the oracle back-check).** Rufinus admitted he intervened more
> freely in the Leviticus homilies than in the other Pentateuch homilies — expanding and joining
> where Origen's Greek was terse. The Latin is therefore *our* text (that is what we edit and
> translate), but expect the English oracle (Barkley) to track it a little more loosely than Heine
> tracked Exodus; adjudicate every discrepancy on the GCS image, never on the oracle.

This folder is the **source-language workspace**. The English translation (one file per
homily) is a later project. Method/layout mirror the completed
**Homilies on Exodus** project (`../Homilies on Exodus/_source/`) — same author, same translator,
and **the very same source volume**: Leviticus is the section of GCS 29 (Werke VI) immediately
following Exodus, running to the end of the volume. Genesis and Exodus, already finished, are the
step-for-step template.

---

## ⇒ Project 1 (the current concern): a stable, clean Latin base text

**Goal:** through repeated correction passes against multiple witnesses, produce a *stable,
clean, verified Latin reading text* of Rufinus's translation — all **16 homilies** — good
enough to translate from. "Stable" = a further full pass yields no substantive change.
**Translation is a later project.**

**Status:** 🟢 **Pass 0 complete — source staged, ready for Pass A.** Full-volume OCR + slice +
all 241 Leviticus page images (pp. 280–507) staged and boundary-verified on the images. **Not yet
run:** Pass A (extract/structure), Pass B (per-homily image transcription), and the refinement
passes. The only outstanding staging item is the copyright Barkley oracle PDF (manual drop-in).
The Genesis and Exodus projects (same volume) are the template for every step.

### Pass 0 — GCS 29 staging (✅ done)
Mirrors the Exodus staging, against the **tail** of the same volume:
- **archive.org item:** `origenes-werke.-bd-6-1920` (Baehrens, *Origenes Werke* Bd. 6 =
  **GCS 29**, 1920; *Homilien zum Hexateuch in Rufins Übersetzung, Teil 1: Genesis, Exodus,
  Leviticus*) — **the same item** the Genesis and Exodus Latin were reconstructed from. (The
  archive item's internal files carry the spaced name `Origenes Werke. Bd 6, 1920_*`, not the
  item identifier; the `_jp2.zip` is 282 MB, 580 leaves `_0000…_0579`.)
- **Full-volume OCR:** ✅ `gcs29_werke6_1920_djvu.txt` (36 324 lines; German+Greek tesseract
  model — Latin-only stretches clean, systematic c→e / ligature noise + garbled apparatus). Copied
  from the Exodus `_source` (each project's `_source/` is git-ignored and self-contained).
- **Leviticus slice:** ✅ `gcs29_leviticus_slice_djvu.txt` (15 262 lines = full-volume OCR lines
  **21063–36324**). The In Leviticum section runs from the section title `ORIGENIS / IN /
  LEVITICUM / HOMILIA I.` (OCR line 21063, printed **p. 280**, opening *"Sicut »in novissimis
  diebus« verbum Dei ex Maria carne vestitum processit in hunc mundum…"*) to the **end of the
  volume** (OCR line 36324) — the closing doxology of Hom XVI (running head `in Leviticum Homilia
  XVI, 7`, printed **p. 507**): *"…et suum nobis suave iugum fidei et caritatis et spei ac totius
  sanctitatis imposuit. Ipsi gloria in aeterna saecula saeculorum! Amen."* Exodus (pp. 145–279)
  precedes Leviticus in this volume; the range was found by grepping the running heads and the
  `ORIGENIS` section title, not assumed.
- **Page images:** ✅ `gcs29_pages/gcs29_pNNN_leafMMM.jpg` — all **241 leaves** of the Leviticus
  homilies (printed **pp. 280–507**, archive leaves **339–579**), 1830×2567 px, 3-channel JPEG
  (168 MB total). *Rendering:* the deprecated `BookReaderImages.php` endpoint 404s and the IIIF
  `full/full` derivations 504 under load, so leaves were rendered locally — download the `_jp2.zip`,
  decode each leaf's `.jp2` with `opj_decompress` (OpenJPEG) → PNG → PIL `convert('RGB')` → JPEG at
  full native resolution (the Werke VI scan is only 1830×2567 native/grayscale; a `scale=2` halving
  would drop to an unreadable ~915 px). Matches the Exodus renders' readability.
- **Leaf ↔ jp2 mapping (✅ verified — no offset):** the jp2 entry for a given page-map leafNum `L`
  is **`Origenes Werke. Bd 6, 1920_{L:04d}.jp2`** — i.e. `leaf L → _{L:04d}.jp2`, *no* −1 (verified:
  `_0339` = p. 280 Homilia I opening; an initial −1 guess gave `_0338` = p. 279, the last Exodus
  page). Confirmed at both ends and mid-section on the images.
- **Printed-page → archive-leaf offset (✅ verified — it *drifts*):** unlike a constant offset, the
  volume's page→leaf gap keeps growing (Exodus saw **+49 → +59** across pp. 145–279 from interleaved
  unnumbered/duplicate leaves; Leviticus continues **+59 → +72**: **p. 280 = leaf 339**, **p. 507 =
  leaf 579**). There is **no single constant offset** — the authoritative per-page mapping is the
  full-volume `page_numbers.json`, used leaf-by-leaf for the render. Boundaries verified on the
  images: leaf 339 = p. 280 (`ORIGENIS / IN / LEVITICUM / HOMILIA I`, apparatus "4 der Titel fehlt
  in den HSS-Klassen" — Hom I's title is absent in the HSS-classes), leaf 579 = p. 507 (Hom XVI,7
  doxology), mid-section leaf 459 = p. 394 (running head "Origenes"; Hom VIII on Lev 12).
  *Quirk:* `page_numbers.json` labels **two** leaves p. 393 (leaves 457 & 458 — a scan
  duplicate/plate); the leaf number is unique and the printed running head is authoritative, so this
  does not affect Pass B (which transcribes from the running heads, not the filenames).
- `page_numbers.json` — ✅ reused from the Exodus `_source` (archive.org printed-page → leaf map for
  the whole volume; authoritative for the drifting offset).

### Witnesses, in priority order
1. **GCS 29 (Baehrens 1920)** — *Origenes Werke* VI; public-domain critical edition. Rufinus's
   Latin version of the Leviticus homilies at printed **pp. 280–507**. **Primary text.**
   ✅ OCR staged (`gcs29_werke6_1920_djvu.txt` + Leviticus slice `gcs29_leviticus_slice_djvu.txt`,
   OCR lines 21063–36324).
2. **GCS 29 page images** — ground truth for correcting the OCR. ✅ rendered to `gcs29_pages/`
   (leaves 339–579 = pp. 280–507, 241 JPGs). Offset **drifts +59→+72**; use `page_numbers.json`
   per-leaf (see Pass 0).
3. **Migne page images** — secondary Latin witness for readings GCS leaves doubtful:
   **PG 12 cols. 405–574** (Lommatzsch/Migne; exact column range to confirm at R1). PG OCR is
   typically unusable for Latin — use as **images** (add during pass R1).
4. **English oracle** — Rufinus translated *this same Latin*, so a modern English decides
   ambiguous or damaged readings. **Consult, never copy.** One standard version exists,
   copyright:
   - **Gary Wayne Barkley**, *Origen: Homilies on Leviticus 1–16* (FOTC 83, 1990) — the standard
     complete English. **Primary oracle.** ⬜ **Not staged** — copyright; drop the PDF in manually
     as `oracle/oracle.pdf` (git-ignored), mirroring the Exodus/Judges/Isaiah setup.
     (See Rufinus's caveat above: track the Latin, not Barkley's smoothing.)

### Passes to execute (same pipeline as Exodus)
- **A — Extract & structure:** isolate Rufinus's Latin from the GCS 29 OCR; split into the 16
  homilies.
- **B — Image collation:** transcribe every homily directly from the GCS 29 **page images**
  (not the OCR), so systematic OCR errors never enter. Per-homily transcribe + adversarial-
  verify agents.
- **R2 — Independent image re-collation (lensless):** a fresh agent re-reads the **entire** base
  word-for-word against the GCS 29 page images, with **no external witness as a lens** (unlike R1's
  Migne or R3's oracle, which flag spots via a second text; here the image itself is the only
  reference). This is the strongest, most direct transcription check — it catches residual slips B
  missed (dropped/added/wrong-form words, dropped clauses, missing/misplaced section numbers,
  guillemet drops), and it especially re-verifies any homily B had to finish under the content-filter
  constraint. **Run it here — right after B, before the editorial passes (R5/R6) — deliberately:**
  while the base is still a pure diplomatic transcript of GCS, every base↔image divergence is a real
  slip, so there is no intentional-departure list to filter against. (If run *after* R5/R6, a naive
  diff would "re-discover" R5's emendations and R6's kept cruxes and wrongly try to revert them — the
  whole reason it belongs early.) Fan out disjoint per-homily image reads; adjudicate every
  divergence on the image; fix in place as tiny image-verified edits. Log to `recollation_pass.md`.
  Expect near-zero on a well-transcribed corpus — a clean R2 is the goal, not a change count.
- **R4 — Boundary & completeness audit:** verify each homily's start/end against the images.
- **R1 — Migne cross-check** (PG 12 images): independent editorial line; every divergence a
  signal, adjudicated on the GCS image.
- **R3 — Systematic oracle back-check:** sentence-by-sentence vs Barkley; candidate slips
  adjudicated on the GCS image (the arbiter). Expect looser Latin↔English tracking than Exodus
  (Rufinus's freer Leviticus rendering).
- **R5 — Whole-corpus consistency & conventions:** single-editor uniformity pass (orthography
  as printed, balanced guillemets, uniform `[GCS p.N]` anchors, one lemma per homily, embedded
  Greek in Greek script). Build the verified **homily → Leviticus-passage** table.
- **R6 — Apparatus-informed variant pass:** narrow, apparatus-driven pass over residual cruxes.
- **R7 — Page-anchor strip (final base-text step → clean reading text):** remove every inline
  page-anchor tag — all `[GCS p.N]` — from `LATIN/` and `_source/passB_final/`, yielding a clean,
  tag-free reading text. **Preserve** any genuine editorial marks that also use square brackets
  (e.g. a `[Titulus deest — …]` note; Hom I's title is absent in the HSS-classes per Baehrens's
  apparatus). Match only `\[GCS p\.\d+\]`, never all `[...]`. Mechanics: anchors that sit
  **mid-word** (`pres[GCS p.NNN]byteri` → `presbyteri`) rejoin correctly under plain token-deletion;
  collapse any double space a word-boundary anchor leaves behind, and touch no other character.
  This is the **last** base-text step; once stripped, the page↔text map lives only in
  `variants_migne.md` / the reports. **Validator:** the `[GCS p.N]` monotonic/contiguous check is
  auto-skipped when a file has no anchors; all other checks (guillemets, no J/j, doxology,
  §-sequence) still apply. Keep `LATIN/` ↔ `passB_final/` byte-identical after the strip. Log to
  `_source/anchor_strip.md`.

Each pass **fixes in place** and **logs to a named `_source/*.md` report** (mirror the Exodus
reports: `boundary_audit.md`, `recollation_pass.md`, `variants_migne.md`, `oracle_discrepancies.md`,
`consistency_pass.md`, `apparatus_pass.md`, `uncertain_readings.md`). Convergence: keep a
running `uncertain_readings.md`; drive it to zero-or-documented. The base is "final" when a
complete pass produces no substantive diff — then it graduates to the translation
phase.

> **Scale note.** Leviticus is **16 homilies over ~228 printed pages** (pp. 280–507), vs Exodus's
> 13 over 135 — roughly **70 % more text**. Pass B (per-homily transcription) and R3 (oracle
> back-check) scale directly with that; budget accordingly.

### Editorial conventions (mirror Exodus / Judges / Genesis / the Matthew base text)
- `» … «` — Scripture that Origen quotes in his exposition (Baehrens's printed guillemets).
- `* … *` — the **Leviticus lemma** under comment (the verse each homily expounds).
- `⟨ … ⟩` — editor's **supplements**; `[ … ]` — editor's **seclusions** (Baehrens's own
  brackets, e.g. `qui[a]`); `…` / `* * * *` — a **printed lacuna** (do **not** fill).
- `[GCS p.N]` = GCS 29 printed page; `[PG n]` = Migne column — used for traceability through R6,
  then **stripped in R7** (the deliverable is anchor-free; the page↔text map lives in
  `variants_migne.md` / the pass reports).
- **Latin reading text only.** Any Greek fragments kept separate, not interleaved into the Latin.
- Keep Baehrens's spellings (Iesus, Istrahel, Moyses, coelum, foenum …); printed *J* left as
  the edition prints. (See the Genesis/Exodus LATIN READMEs — same volume, same conventions.)

### Project-1 deliverable
`LATIN/homily01_latin.txt … homily16_latin.txt` — the stable, verified Latin, plus a final
`uncertain_readings.md` recording residual editorial calls. (Genesis/Exodus use zero-padded
`homily01…`; match that here — `homily01…homily16`.)

---

## Source survey (why these witnesses)

**No public-domain English exists** — the Leviticus homilies were left out of the Ante-Nicene
Fathers. The only standard complete English version is Barkley (FOTC 83, 1990), copyright
(our oracle). So the work must be translated fresh from the Latin.

**Critical editions & PD status**

| Edition | Year | PD? | Role |
|---------|------|-----|------|
| **GCS 29 / Origenes Werke VI** (Baehrens), In Leviticum pp. 280–507 | 1920 | ✅ | **Our base.** archive.org/details/origenes-werke.-bd-6-1920 |
| Migne **PG 12**, cols. 405–574 | 1862 | ✅ | Secondary Latin witness (page images; Latin OCR unusable) |
| **Barkley**, *Homilies on Leviticus 1–16*, FOTC 83 — En | 1990 | ❌ | **Oracle** (consult, never copy) |
| Borret et al., *Homélies sur le Lévitique*, SC 286–287 — Lat+Fr | 1981 | ❌ | Later critical ed. (reference only, not staged) |

Baehrens (d. 1929) and the Migne volume are public domain, so the base + the Migne witness are
freely usable; only the modern English oracle (and the SC edition) are copyright.

## Provenance links
- GCS 29 (base): https://archive.org/details/origenes-werke.-bd-6-1920
- Issue: https://github.com/HistoricalChristianFaith/Writings-Database/issues/146

## `_source/` contents (this folder is git-ignored)
| File | What | Present? |
|------|------|-----------|
| `gcs29_werke6_1920_djvu.txt` | GCS 29 full-volume OCR (Latin+apparatus). 36 324 lines. | ✅ staged |
| `gcs29_leviticus_slice_djvu.txt` | GCS 29 OCR slice = In Leviticum section only (lines 21063–36324). 15 262 lines. | ✅ staged |
| `gcs29_pages/` | GCS 29 Leviticus page renders, leaves 339–579 (pp. 280–507). | ✅ 241 JPGs |
| `page_numbers.json` | archive.org printed-page → leaf map (whole volume; authoritative; offset drifts +59→+72). | ✅ staged |
| `migne_pages/` | PG 12 page renders (add during pass R1). | ⬜ later |
| `oracle/oracle.pdf` | Barkley FOTC 83 English oracle (Leviticus 1–16). | ⬜ **add manually (copyright)** |

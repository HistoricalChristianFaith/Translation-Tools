# Origen, *Commentary on 1 Corinthians* — Greek base-text project (issue #154)

Origen's *Commentary on 1 Corinthians* survives **only as Greek catena fragments** — excerpts
preserved in the medieval Greek exegetical chains (*catenae*) on the Pauline epistles, not as a
continuous running commentary. The standard public-domain edition of these fragments is
**Claude Jenkins, "Origen on I Corinthians," *Journal of Theological Studies* (old series) 9 (1908)
and 10 (1909)**, published across **four instalments (Parts I–IV) spanning two volumes**. Jenkins
assembled and *numbered* the fragments in a single continuous sequence of **`§` sections I → XC
(90 sections)**, each keyed to the 1 Corinthians verse (*lemma*) it comments on, running from
1 Cor i 1 to the epistle's close (last fragment on 1 Cor xvi 13–14). The fragments expound Paul's
letter verse-by-verse in Origen's characteristic manner — the wisdom of the world vs. the wisdom of
God (1 Cor i–iii), marriage and celibacy (1 Cor vii), the runner in the stadium and the "prize"
(1 Cor ix 24), the one bread / one body (1 Cor x), spiritual gifts and the discernment of spirits
(1 Cor xii), the whole armour of God (1 Cor xvi 13, cf. Eph vi).

> **Method note (bears on the whole project).** Jenkins states in his own preface (p. 231) that
> **"the form given to the text follows in the main that adopted in Mr J. A. F. Gregg's new edition
> of Origen's commentary on Ephesians already printed in the third volume of this JOURNAL."** So this
> project is a **near-exact parallel of the completed Ephesians project** (`../Commentary on
> Ephesians/_source/`): same author, same catena genre, same editor's conventions, same pass
> pipeline. The three big structural differences are: **(1) four instalments, not three; (2) they
> cross a *volume* boundary (JTS 9 → JTS 10); (3) ~90 sections vs. 37** (≈2.5× the transcription
> volume, weighted heavily into Part IV).

> **Genre caveat.** This is a **discontinuous fragment collection** reassembled by a modern editor
> across **four separate journal issues in two volumes**. The structural spine is **Jenkins's `§`
> numbering (I–XC) + the 1 Corinthians lemma of each fragment**, not chapter/section divisions of a
> running work. The single greatest completeness risk is a fragment silently dropped **at a seam
> between Parts** — above all the **Part III/IV seam, which crosses the JTS 9 → JTS 10 volume
> boundary**. (Pass 0 has already image-verified that seam as contiguous: § XLIV ends Part III on
> JTS 9 p. 514; § XLV opens Part IV on JTS 10 p. 29 — see `pass0_report.md`. R4 re-confirms.)

> **Language caveat (bears on every pass).** The base is **polytonic Greek**. Archive.org's OCR of a
> 1908–09 Greek journal is **not usable as text** (dropped final sigma, mangled breathings/accents,
> lost iota subscript). The OCR is good **only for locating the article boundaries and Jenkins's
> section numbers**; the Greek itself is transcribed almost entirely from the **page images**
> (Pass B). Same departure from the Latin-homily flow as Ephesians.

This folder is the **source-language workspace**. The deliverable is a stable, verified Greek
reading text of the fragments (later, a fresh English translation). Method mirrors the completed Ephesians project
and the Latin homily projects — same author, same multi-pass discipline. The nearest
**deliverable-layout** precedents are `Commentary on Ephesians/GREEK/…` and
`Commentary on Romans/GREEK/` (catena fragments stored as a `GREEK/` folder).

---

## ⇒ Project 1 (the current concern): a stable, clean Greek base text

**Goal:** through repeated correction passes against Jenkins's page images (plus the Cramer witness
and a modern oracle), produce a *stable, clean, verified polytonic-Greek reading text* of **all** the
1 Corinthians fragments, each keyed to its 1 Cor lemma, in Jenkins's numbering (§§ I–XC). "Stable" =
a further full pass yields no substantive change. **Translation is a later project.**

**Status:** 🟢 **Pass 0 complete — source staged and every article boundary image-verified; ready
for Pass A.** All four instalments rendered (75 article + 8 margin JPEGs), OCR + per-part page→leaf
maps staged, the fragment structure (§§ I–XC across the four parts) confirmed on the images,
including the critical JTS 9→10 seam. **Not yet done:** Pass A (structure) and all following passes.
Outstanding staging items are the R1/R3 witnesses (Cramer vol. V images, Kovacs PDF), added at their
passes. See `pass0_report.md` for the full staging record.

### Fragment structure (confirmed at Pass 0)
The fragment spine is **Jenkins's `§` sections, numbered continuously I → XC across the four parts
(90 sections)** — a new `§` each time the catena names Origen (Jenkins, p. 231: "a new
chapter-division has been marked … whenever the catenist mentions the name of Origen"). Split Pass A
on the `§`, not on pages/parts:

| Part | JTS (1908–09) pages | archive.org item | § sections | 1 Corinthians |
|------|---------------------|------------------|------------|---------------|
| **I**   | vol 9, pp. 231–247 | `sim_journal-of-theological-studies_1908-01_9` | **§ I–XVI**      | i 1 – iii 20 |
| **II**  | vol 9, pp. 353–372 | `sim_journal-of-theological-studies_1908-04_9` | **§ XVII–XXXII** | iii 21 – vi (Eph vi 24 cited) |
| **III** | vol 9, pp. 500–514 | `sim_journal-of-theological-studies_1908-07_9` | **§ XXXIII–XLIV** | vii 1 – ix 24 |
| **IV**  | vol 10, pp. 29–51  | `sim_journal-of-theological-studies_1908-10_10` | **§ XLV–XC**     | x 5 – xvi 13,14 |

**Section count:** 16 + 16 + 12 + 46 = **90 (§§ I–XC).** (Note: the earlier `ORIGEN_REMAINING.md`
analysis estimated "94 fragments"; the authoritative spine from the images is **90 numbered `§`
sections**. Confirm no lettered sub-sections / gaps at Pass A.) **Part IV is by far the densest** —
46 short sections over 23 pages, covering 1 Cor x–xvi, and it is where Jenkins folds in the ~30
previously-unpublished fragments from the **Athos catena (MS Pantocrator 28)** for the later portions
of the Epistle "where the Vatican MS for a time ceases to quote Origen."

### Base manuscript & witnesses (from Jenkins's preface, p. 231)
- **Base MS = Vatican MS gr. (saec. xi)** — "the hitherto unpublished Vatican MS gr. **762**" per the
  preface; **but the printed apparatus repeatedly cites the base as "Vat. gr. 692"** (e.g. JTS 9
  p. 514; JTS 10 p. 29). ⚠ **Unresolved siglum discrepancy 762 vs 692 — resolve by PIL crop at Pass
  A** (probably a print/OCR-of-the-eye slip; both digits are ambiguous in this face). The 16th-c.
  Paris MS gr. 227 (Cramer's source, via the "scriba Parisiensis") is apparently a copy of it.
- **Athos MS Pantocrator 28** — ~30 previously-unpublished fragments for the later Epistle,
  transcribed for Jenkins by Kirsopp Lake; folded into Part IV.
- **Cramer's printed text** (from Paris gr. 227) — the independent published witness ⇒ **Cramer's
  page numbers are printed in Jenkins's margin** "where the passage forms part of his printed text of
  the catena." Those marginal numbers are the built-in key for the **R1 Cramer collation**.

### Typography → our markers (Jenkins, p. 231, identical to Gregg)
- **Clarendon** (bold) = the 1 Cor words Origen is commenting on ⇒ lemma / `* *` handling.
- **Uncial** (small-caps Greek) = other Biblical citations or allusions ⇒ `» «`.
- Preserve Jenkins's supplements `⟨ ⟩` and seclusions `[ ]`; `…` / `* * *` = printed lacuna
  (do **not** fill). References to Origen's other works are given to the Berlin (GCS) edition.

### Witnesses, in priority order
1. **Jenkins, *JTS* 9–10 (1908–09)** — page images. Public-domain critical edition of the 1 Cor
   catena fragments, with apparatus. **Primary text / ground truth.** ✅ staged (`jenkins_pages/`,
   83 JPEGs).
2. **Jenkins OCR** (`_djvu.txt`) — for locating article boundaries + section numbers only. Greek OCR
   not trusted. ✅ staged (`jenkins_jts{I,II,III,IV}_djvu.txt`).
3. **Cramer, *Catenae Graecorum Patrum in Novum Testamentum*, vol. V** (*In Epp. ad Corinthios*,
   Oxford 1844) — the independent published catena witness; public domain. Secondary Greek witness
   for doubtful readings — use as **images** (add at pass R1). Item: archive.org multi-volume
   `CatenaeGraecorumPatrumchainOfGreekFathersOnNewTestament` (vol. V). ⬜ later. **⚠ Note: 1 Cor is
   Cramer vol. V, NOT vol. VI** (vol. VI = Gal–Thess, which was the Ephesians witness).
   Cross-reference aid: **Jenkins, "The Origen-Citations in Cramer's Catena on I Corinthians," *JTS*
   6 (1905) pp. 113–116** — Jenkins's own map of which Cramer passages are genuinely Origen (he flags
   15 that Cramer misattributed).
4. **English + Greek oracle** — **Judith L. Kovacs**, *1 Corinthians: Interpreted by Early Christian
   Commentators* (The Church's Bible; Eerdmans, 2005) — a modern English rendering of these
   fragments. **Oracle only — consult, never copy** (copyright). Decides ambiguous/damaged readings;
   adjudicate on the Jenkins image, never on Kovacs. ✅ staged (git-ignored) as `oracle/oracle.pdf`
   (384 pp; clean OCR text layer, extracts with `pdftotext` — arranged verse-by-verse by patristic
   author, incl. Origen). Also staged: `oracle/oracle_2.pdf` (Steve Harris's free English of
   frags ~1–5, 11 — itself incorporates Kovacs; partial, use only as a spot cross-check).
   *Secondary oracle (optional, not held):* F. Pieri, *Origene, Esegesi paolina* (Opere di Origene
   14/4; Città Nuova, 2009) — Italian, with the Greek.
5. **Turner's textual notes** — **C. H. Turner, "Notes on the Text of Origen's Commentary on I
   Corinthians," *JTS* 10 (1909) pp. 270–276** — a *second* scholar's apparatus (also folded inline
   into Jenkins's own footnotes as "Turner"). Public domain. Fold into **R6** (apparatus-informed
   variants) — a genuine independent editorial check Ephesians did not have.

### Passes to execute (same pipeline as Ephesians)
- **A — Extract & structure:** locate the Origen article in each of the 4 JTS issues; reassemble
  Jenkins's numbered `§` sequence (I–XC), each keyed to its 1 Cor lemma. OCR assists **structure
  only** — Greek not trusted from OCR. Resolve the Vat. gr. 762/692 siglum by crop; confirm no
  lettered sub-sections or numbering gaps I–XC.
- **B — Image collation:** transcribe every fragment directly from the Jenkins **page images**
  (not the OCR), in polytonic Greek. **This is the heavy pass** (~90 sections; batch by contiguous
  page range, one read per page; per-batch transcribe + adversarial-verify agents). Watch the classic
  Greek-OCR/typography traps: final sigma (ς/σ), breathings & accents, iota subscript, nomina sacra,
  clarendon-vs-uncial, and Jenkins's editorial brackets.
- **R2 — Independent image re-collation (lensless):** a fresh agent re-reads the **entire** base
  word-for-word against the Jenkins images, with **no external witness as a lens**. Run right after B.
  Log to `recollation_pass.md`.
- **R4 — Boundary & completeness audit:** verify every Jenkins `§` is present, correctly numbered,
  with the correct lemma, and — critically — that **no fragment was dropped at the Part seams,
  especially the JTS 9→10 (§ XLIV/§ XLV) volume seam**. Reconcile the count against I–XC = 90.
  Log to `boundary_audit.md`.
- **R1 — Cramer cross-check** (Catenae **vol. V** images): the independent-witness editorial line.
  Use the marginal Cramer page numbers + Jenkins's JTS 6 (1905) citation-map. Every divergence a
  signal, adjudicated on the Jenkins image. Log to `variants_cramer.md`.
- **R3 — Systematic oracle back-check:** fragment-by-fragment vs Kovacs 2005 (and Pieri 2009 if
  held); candidate slips adjudicated on the Jenkins image (the arbiter). Log to
  `oracle_discrepancies.md`.
- **R5 — Whole-corpus consistency & conventions:** single-editor uniformity pass (polytonic
  orthography/accentuation *as Jenkins prints*, balanced quotation marks, uniform `[JTS p.N]`
  anchors — tagged with volume, e.g. `[JTS 9 p.372]` / `[JTS 10 p.29]`, contiguous § numbering, one
  lemma per §, sub-lemma verse-heading convention). Build the verified **§ → 1 Cor-verse table**.
  Log to `consistency_pass.md`.
- **R6 — Apparatus-informed variant pass:** narrow, apparatus-driven pass over residual cruxes, using
  **Jenkins's apparatus + Turner's JTS 10 (1909) notes**. Log to `apparatus_pass.md`.
- **R7 — Page-anchor strip (final base-text step → clean reading text):** remove every inline page
  anchor from `GREEK/`, yielding a clean, tag-free reading text. **Preserve** genuine editorial marks
  that also use square brackets (Jenkins's seclusions). Consolidate into the single-file deliverable.
  Log to `anchor_strip.md`.

Each pass **fixes in place** and **logs to a named `_source/*.md` report**. Convergence: keep a
running `uncertain_readings.md`; drive it to zero-or-documented. The base is "final" when a complete
pass produces no substantive diff — then it graduates to the translation phase.

### Editorial conventions (mirror Ephesians)
- **Polytonic Greek reading text**, orthography/accentuation **as Jenkins prints** (do not silently
  modernise). Embedded Latin/English (apparatus sigla, Turner notes) kept out of the Greek body.
- `» … «` — Scripture Origen quotes in his exposition (uncial in Jenkins).
- `* … *` — the **1 Cor lemma word(s)** the fragment expounds where they recur in Origen's prose
  (clarendon in Jenkins).
- `⟨ … ⟩` — editor's **supplements**; `[ … ]` — editor's **seclusions / rubric brackets**;
  `…` / `* * * *` — a **printed lacuna** (do **not** fill).
- `[JTS 9 p.N]` / `[JTS 10 p.N]` = Jenkins's printed page (volume-tagged, since the work spans two
  volumes) — used for traceability through R6, then **stripped in R7**.
- **Greek reading text only.**

### Project-1 deliverable
`GREEK/…` — the stable, verified polytonic Greek of the fragments, keyed to 1 Cor lemmata, plus a
final `uncertain_readings.md`. Follow the DB's catena convention: store as a single continuous file
unless section count argues for splitting. Final naming to confirm at R5.

---

## Source survey (why these witnesses)

**No public-domain English exists** — the 1 Corinthians fragments were left out of the Ante-Nicene
Fathers (which prints only the surviving *books* of other works, not these catena fragments). The
only reasonably complete modern English is Kovacs (Church's Bible, 2005), copyright (our oracle);
the one free English online (Steve Harris) covers only a handful of fragments and itself
incorporates Kovacs. So the work must be translated fresh from the Greek.

**Editions & PD status**

| Edition | Year | PD? | Role |
|---------|------|-----|------|
| **Jenkins**, *JTS* 9 (1908) Pts I–III + 10 (1909) Pt IV | 1908–09 | ✅ | **Our base.** archive.org JTS issues |
| **Cramer**, *Catenae Graecorum Patrum in NT*, **vol. V** (ad Corinthios) | 1844 | ✅ | Secondary published catena witness (images) |
| **Jenkins**, "Origen-Citations in Cramer's Catena on I Cor," *JTS* 6 | 1905 | ✅ | Cramer↔Origen attribution map (R1 aid) |
| **Turner**, "Notes on the Text …," *JTS* 10 pp. 270–276 | 1909 | ✅ | Independent apparatus (R6) |
| **Kovacs**, *1 Corinthians* (The Church's Bible), Eerdmans | 2005 | ❌ | **Oracle** (consult, never copy) |
| **Pieri**, *Origene, Esegesi paolina* (OO 14/4), Città Nuova | 2009 | ❌ | Optional secondary oracle (Italian + Greek) |

## Provenance links
- Jenkins Part I:   https://archive.org/details/sim_journal-of-theological-studies_1908-01_9
- Jenkins Part II:  https://archive.org/details/sim_journal-of-theological-studies_1908-04_9
- Jenkins Part III: https://archive.org/details/sim_journal-of-theological-studies_1908-07_9
- Jenkins Part IV:  https://archive.org/details/sim_journal-of-theological-studies_1908-10_10
- Cramer (8 vols; vol. V = 1 Cor): https://archive.org/details/CatenaeGraecorumPatrumchainOfGreekFathersOnNewTestament
- JTS old-series article index: https://biblicalstudies.org.uk/articles_jts-os_01.php
- Issue: https://github.com/HistoricalChristianFaith/Writings-Database/issues/154

## `_source/` contents (this folder is git-ignored)
| File | What | Present? |
|------|------|-----------|
| `jenkins_pages/` | Jenkins JTS page renders — 75 article + 8 margin JPEGs, all 4 parts. | ✅ Pass 0 |
| `jenkins_jts{I,II,III,IV}_djvu.txt` | Full-issue OCR (structural aid only — Greek not trusted). | ✅ Pass 0 |
| `scandata_{I,II,III,IV}.xml` | archive.org page-data (leaf → printed page). | ✅ Pass 0 |
| `page_numbers.json` | Per-part printed-page → leaf map + target leaves (authoritative). | ✅ Pass 0 |
| `pass0_report.md` | Staging record + verified boundaries + structural facts for Pass A. | ✅ Pass 0 |
| `cramer_pages/` | Cramer *Catenae* **vol. V** page renders (add during pass R1). | ⬜ later |
| `oracle/oracle.pdf` | Kovacs Church's Bible 2005 oracle (384 pp, R3). | ✅ staged (copyright) |
| `oracle/oracle_2.pdf` | Steve Harris partial English of frags ~1–11 (spot cross-check). | ✅ staged (copyright) |

# Pass R6B — Full base ↔ GCS-image re-collation (independent final transcription sweep)

**Base / sole arbiter:** GCS 29 = Baehrens, *Origenes Werke* VI (1920), In Leviticum pp. 280–507.
Every decision below was adjudicated **on the GCS 29 page image** (`_source/gcs29_pages/`). Scope: a fresh,
direct, word-for-word re-read of the ENTIRE base against the GCS page images, **with no external lens** —
R1 used Migne as the lens, R3 used the Barkley English; both then checked flagged spots on the image. R6B
removes the lens entirely and re-collates the base against the printed main text itself, page by page. It is
the strongest and most direct transcription check, and the **last base-text verification before the R7
anchor strip.**

**What R6B is / is not.** IS: read each GCS page image and the on-disk base (`_source/passB_final/homilyNN.txt`)
side by side and confirm the base reproduces GCS's printed **main text** exactly — word forms, word order,
presence/absence of every word and clause, section numbers, guillemet `» «` placement. IS NOT: a
re-litigation of settled decisions — R5's intentional emendations, R6's KEEP rulings, the stripped-Greek
policy, and the `[GCS p.N]` anchors (stripped in R7) were all left untouched. R6B only closes the gap
between the base and GCS's own printed main text.

**End state:** **3 tiny image-verified transcription slips fixed** (all in the pre-collation base, none
touching an editorial decision); `validate.py` → **ALL 16 CLEAN**; `LATIN/homilyNN_latin.txt` ↔
`_source/passB_final/homilyNN.txt` byte-identical over the body (validator-enforced); coverage pp. 280–507
unchanged, 13 shared pages double-anchored; git working tree shows only the two edited `LATIN/` files.

---

## 1. Method

- **Baseline de-risk.** `validate.py` re-run up front → ALL 16 CLEAN. The orchestrator then re-collated the
  calibration homily (Hom V — largest, and one of the six content-filter-stalled) on a sample of high-risk
  pages (332, 333, 358): no content-filter stall in auditing; the base reproduced GCS main text; the R5/R6
  intentional departures (the p.332 `aqua.` de-doubled period, the p.333 `»qui in manifesto«, sed …`
  guillemet placement, the stripped Philocalia Greek, DOX[5]) were all confirmed correctly present. This
  fixed what a real slip vs an intentional departure looks like.
- **Fan-out.** Disjoint per-homily image reads to subagents (disjoint `passB_final/` files; Latin-free
  reports; **report-only**, no subagent edits). The six content-filter-stalled homilies (**II, IV, V, VI,
  VII, XVI**) each got a dedicated agent; the other ten were grouped (I+III, VIII+IX, X+XI+XII,
  XIII+XIV+XV). Each agent re-read **every page** of its homily against the image, excluded the R5/R6
  intentional list first, and reported discrepancies in Latin-free / ≤2-word form (page + line + English
  description + category).
- **Central adjudication.** Every reported discrepancy was re-opened by the orchestrator **on the GCS image**
  before any edit. Confirmed slips were applied as single-occurrence 1-word edits to `passB_final/`
  (uniqueness `grep`-checked, count==1). `assemble.py` + `validate.py` were run centrally, once up front and
  once at the end.
- **Content-filter constraint honoured throughout:** auditing (image vs on-disk compare) emits no flowing
  Latin; this report names Latin tokens only where the item IS a specific word form (≤2 words).

## 2. Per-homily verdict

| Hom | GCS pp. | Verdict | Slip(s) found (old → new) |
|-----|---------|---------|---------------------------|
| I    | 280–288 | CLEAN | — |
| II   | 288–299 | CLEAN | — |
| III  | 300–316 | CLEAN | — |
| **IV** | 316–332 | **1 slip → fixed** | p.317 §2 (Lev 6:5 lemma): `et reddet` → **`ei reddet`** |
| V    | 332–358 | CLEAN | — |
| VI   | 358–370 | CLEAN | — |
| VII  | 370–393 | CLEAN | — |
| VIII | 393–417 | CLEAN | — |
| IX   | 417–440 | CLEAN | — |
| X    | 440–445 | CLEAN | — |
| XI   | 446–454 | CLEAN | — |
| XII  | 454–467 | CLEAN | — |
| XIII | 467–478 | CLEAN | — |
| XIV  | 478–487 | CLEAN | — |
| XV   | 487–491 | CLEAN | — |
| **XVI** | 491–507 | **2 slips → fixed** | p.496 §2: `eum` → **`cum`** (before *frumenta teruntur*); p.505 §6: restored dropped sentence-period (`…mundus Deo« Vis` → `…mundus Deo«. Vis`) |

**13 homilies CLEAN outright; 3 slips total in 2 homilies, all fixed.** Given B/R4/R1/R3/R5/R6 convergence
this near-zero result is the expected, healthy outcome; the three that surfaced are exactly the sort of
single-character residue B leaves behind, two of them in a content-filter-stalled homily (XVI).

## 3. The three fixes, image-adjudicated

### 3.1 Hom IV p.317 §2 — Lev 6:5 (LXX 5:24) lemma: `ei reddet` (dative pronoun) — **EMEND**
**Image (leaf 378), line 9:** the main text prints the dative pronoun before the verb — `…et cuius est,
ei reddet, qua die convictus fuerit«` ("and to whom it belongs, **to him** he shall restore it, on the day
he is convicted"). **Base (pre-fix):** the conjunction `et` in that slot (`…et cuius est, et reddet…`), a
one-letter `ei`→`et` slip. Sense and the LXX (`τίνος ἐστίν, αὐτῷ ἀποδώσει`) both require the dative. The
apparatus at that line carries no variant on the pronoun. **Not** an intentional departure: this is a
different spot from the R1 fix in the *same* lemma (`est et` → `est ei`, at *commendatum est ei*, which the
base already carries correctly), and the §5 re-quotation on p.321 (`et ei, cuius est, reddet`) is likewise
correct in the base — so this was an isolated slip in the §2 occurrence only. **Fixed** (single-occurrence,
count==1).

### 3.2 Hom XVI p.496 §2 — `cum frumenta teruntur` — **EMEND**
**Image (leaf 568), lines 5–6:** `…id est cum messis colligitur, cum frumenta teruntur in areis…` ("that is,
when the harvest is gathered, **when** the grain is threshed on the floors"). **Base (pre-fix):** `eum
frumenta teruntur` — a `c`→`e` single-letter slip yielding a non-word in context (`eum` cannot govern the
clause). The parallel first clause `cum messis colligitur` fixes the intended conjunction. **Fixed**
(single-occurrence, count==1).

### 3.3 Hom XVI p.505 §6 — restored dropped sentence-period — **NORMALIZE (punctuation)**
**Image (leaf 577), line 8:** the main text closes a sentence with a period after the quotation —
`…ut subditus fiat omnis mundus Deo‹. Vis adhuc et de alia epistola Pauli…` (single-angle `‹` normalized to
`«` per corpus convention). **Base (pre-fix):** the two sentences were fused (`…mundus Deo« Vis adhuc…`), the
sentence-final period dropped. This is a punctuation-level transcription drop, not one of the six word/§/
guillemet categories, but it is a real, unambiguous departure from the printed main text (a dropped
character fusing two sentences); restored for reading-text fidelity, in the same spirit as R5's p.332
doubled-period normalization. **Fixed** (single-occurrence, count==1). Reported transparently as
punctuation-level, distinct from the two word-level slips above.

## 4. Intentional departures re-confirmed present (the trap — NOT reverted)

Each agent excluded the R5/R6 intentional list before reporting, and the orchestrator spot-re-confirmed the
highest-risk ones on the image. All left exactly as they stood:

- **R5 emendations** — Hom IV p.327 `sanctificati`; Hom VI p.369 `aliquid`; Hom VIII p.396 `scriptum`,
  p.398 `hoc est`, p.400 `corporis`, p.412 `iubeatur`; Hom IX p.420 `sanctificata`; Hom XIII p.468 `in loco`;
  Hom V p.332 `aqua.` and p.333 guillemet placement. Confirmed present; **not** re-flagged as slips.
- **R5 kept systematic Baehrens spellings** — Iesus, Istrahel, Moyses, Aaron, coelum, foenum,
  adspectus/adscend-, spiritalis, haereditas, sollemnitas, and the diaeresis forms `Soënen` (IX p.422),
  `Noë` (XVI p.493); the per-spot name variation Hierusalem/Ierusalem (XI p.453 `Hierusalem` vs XII p.461
  `Ierusalem`) and Hieremi-/Ieremi-. Left as printed.
- **R6 KEEP cruxes** — Hom XI p.453 §3 `Iacobus` (James); Hom IX ark `testimonii` (pp.418/427) vs
  `testamenti` (p.435); Hom IX p.422 `Soënen`. Left as printed.
- **The single intentional Greek word** — Hom XI §2 p.448 `ἅγιος`. Retained; no other Greek reinserted (the
  stripped Greek catena/gloss blocks on III p.311, V pp.333–334 & p.355, VI p.360, VII p.386, VIII
  pp.405–409, XIII p.472 were confirmed to leave the surrounding **Latin continuous** — no lost Latin word or
  clause — and were correctly **not** flagged).
- **`[GCS p.N]` anchors** — left in place for R7; not flagged.
- **Doxologies** — all 16 non-uniform `DOX` signatures verified image-true (II `laus`; VII `Amen.` inside the
  marks; IX/XII `cui gloria` no *est*; XIII `Ipsi`; XIV `qui est`; XVI `Ipsi gloria in aeterna …` no
  *imperium*, no guillemets; the `Amen`/`Amen!` closings). None edited — the `DOX` dict is untouched.

## 5. Final validation

```
Hom  1..16: anchors pStart-pEnd contiguous, guillemets balanced / no-nesting / no-stray,
            no J/j, correct per-homily doxology signature, §-sequence from 1        -> ALL 16 CLEAN
cross-file: total anchors=241, distinct pages=228, surplus=13 (the 13 shared pages
            double-anchored) -> as expected; coverage pp. 280–507 unchanged
```

`LATIN/` ↔ `passB_final/` running body byte-identical (all 16, validator-enforced). Central `assemble.py`
re-run; git working tree shows exactly the two touched files (`LATIN/homily04_latin.txt`,
`LATIN/homily16_latin.txt`); the three superseded strings survive nowhere in `LATIN/` or `passB_final/`
(grep-verified, 0 hits). No editorial policy from B/R4/R1/R3/R5/R6 was re-opened. **R6B complete —**
the base now reproduces Baehrens's printed main text to the letter across all 16 homilies.

**End state: READY FOR PASS R7** (page-anchor strip → clean, tag-free reading text) — the final base-text
step before the translation phase.

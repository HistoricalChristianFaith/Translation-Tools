# Pass R7 — Page-Anchor Strip (final base-text pass)

**Work:** Origen, *Homilies on Leviticus* (16 homilies; Rufinus's Latin; GCS 29 = Baehrens,
*Origenes Werke* VI, 1920, *In Leviticum* pp. 280–507).
**Pipeline position:** B → R4 → R1 → R3 → R5 → R6 → **R7 (this pass — last base-text step).**
**Scope:** deterministic removal of every inline `[GCS p.N]` page-anchor from the reading text,
leaving the running Latin otherwise byte-for-byte unchanged. No editorial, transcription, collation,
orthography, guillemet, or doxology change was made — R7 removes tags and nothing else.

## Method

The strip was performed by a deterministic script (`_source/scratchpad/r7_strip.py`) operating on the
single source of truth, `_source/passB_final/homilyNN.txt`; the deliverable `LATIN/` was then
regenerated from that source by `_source/scratchpad/assemble.py`. No Latin was hand-retyped at any
point — the script transforms the files and the human role was read/verify only.

Before touching anything, pristine copies of all 16 source files were saved to
`_source/scratchpad/passB_prestrip/` (and the pre-strip `LATIN/` to
`_source/scratchpad/LATIN_prestrip/`) to enable the diff-integrity gate below.

### Anchor taxonomy (measured on the pre-strip source)

Every one of the 241 anchors was classified by the character immediately before and after the tag:

| Context | Count | Shape | Rejoin behaviour |
|---|---:|---|---|
| space-before, word-after | 178 | `word [GCS p.N]word` | plain deletion leaves the single separating space → `word word` |
| word-before, word-after (mid-word) | 40 | `se[GCS p.N]cundum` | plain deletion rejoins the split word with no space → `secundum` |
| line-start, space-after (section opener) | 22 | `[GCS p.N] K. …` at line start | anchor **and its one trailing space** removed, so the line begins cleanly at the section number |
| line-start, word-after | 1 | `[GCS p.465]6. …` at line start | plain deletion → `6.` at line start (no space to remove) |

### The transform (two ordered regex substitutions)

1. `(?m)^\[GCS p\.\d+\] ` → *(nothing)* — matches only the 22 line-start section openers and removes
   the anchor **plus its single following space**, preventing an orphaned leading space at the line
   start.
2. `\[GCS p\.\d+\]` → *(nothing)* — removes all remaining anchors (the 178 space-before, the 40
   mid-word, and the 1 line-start-no-space case). Because the regex matches only the bracket token, a
   space that preceded an anchor is preserved (space-before case → one space) and two word-halves
   flanking an anchor become directly adjacent (mid-word case → no space).

No other rejoin situations exist: an independent scan confirmed **zero** anchors preceded by a
newline-plus-space, so no hidden leading-space hazard, and there were no standalone-line or line-end
anchors.

## Anchor count removed

**241 anchors removed across the corpus** (matching the expected total), by homily:

```
h01 9   h02 12  h03 17  h04 17  h05 27  h06 13  h07 24  h08 25
h09 24  h10 6   h11 9   h12 14  h13 12  h14 10  h15 5   h16 17   = 241
```

Of these, 22 were removed by rule 1 (line-start openers) and 219 by rule 2. Post-strip, both
`_source/passB_final/` and `LATIN/` contain **zero** `[GCS p.` substrings (grep-verified, all 32
files).

## Rejoin edge-case handling — verified outcomes

- **Mid-word (40 sites):** every split word reconstitutes into a valid, complete Latin word with no
  intruded space — e.g. `secundum` (p281), `holocaustum` (p284), `membratim` (p286), `tabernaculum`
  (p371), `dispensatione` (p312), `poenitentiam` (p487), `Quomodo` (p498). All 40 enumerated and
  checked programmatically.
- **Space-before (178 sites):** each leaves exactly one separating space — no double spaces
  introduced anywhere (double-space count stayed at its baseline of 0 in every file).
- **Line-start openers (22 sites):** each line now begins directly at its section number with no
  leading space (leading-line-space count stayed at baseline 0).
- **Line-start-no-space (1 site, p465):** section 6 of Homily 12 now opens cleanly with no leading
  space.

## Surviving-bracket audit

After the strip, every remaining `[`, `⟨`/`⟩`, and `*` was enumerated and confirmed to be an intended
editorial mark:

- **Header note (Homily 1):** `[Titulus deest — …]` — the title is absent in the HSS-classes per
  Baehrens (documented `consistency_pass.md` lines 111/171; image-confirmed on GCS p.280, whose
  apparatus reads "4 der Titel fehlt in den HSS-Klassen"). Lives in the LATIN scaffold header, not
  the body; untouched.
- **Body seclusions/supplements (4 sites):** the two secluded first-fruits phrases in Homily 2
  (GCS pp. 288–299 span; cf. `variants_migne.md` lines 120–121), and the single-word supplements
  `[qui]` (Homily 6) and `[et]` (Homily 7). All four are genuine Baehrens editorial marks (the class
  described in `consistency_pass.md` line 92) and were confirmed **byte-identical** to the pre-strip
  backup.
- **Angle-bracket supplements `⟨ ⟩`:** none present in this corpus (count 0, unchanged).
- **Lemma markers `*…*`:** none present in this corpus body (count 0, unchanged).
- **Zero** `[GCS p.` substrings remain.

## Diff-integrity result (the decisive correctness gate)

Each stripped source file was checked against its pristine pre-strip backup by three independent
O(n) tests (difflib's char-level opcodes were prohibitively slow on the larger files, so equivalently
rigorous linear checks were used):

1. **Independent reconstruction** — re-deriving the stripped text from the pristine backup with the
   anchor-only regexes (which cannot match a letter) reproduced the actual stripped file **exactly**
   in all 16 files. This proves no letter was altered.
2. **Deletion-only** — the stripped text is a strict subsequence of the backup in all 16 files
   (no insertion, no reordering, no substitution).
3. **Exact character accounting** — characters removed = (sum of anchor-token lengths) + (count of
   line-start openers, i.e. their one trailing space each), matching to the character in all 16 files
   (e.g. Homily 5: 298 chars removed = 27 tags + 1 opener space; Homily 1: 100 = 9 tags + 1).

**Result: all 16 files pass all three tests.** Every change is solely an anchor-token removal, plus
(for the 22 openers) the single adjacent space; nothing else changed.

## Shared-page spot-checks

The 13 shared boundary pages (288, 316, 332, 358, 370, 393, 417, 440, 454, 467, 478, 487, 491) were
each spot-checked at both occurrences — the mid-page rejoin closing the earlier homily's span and the
`1.`/`6.` section-opener beginning the next homily. All read continuously with correct word
boundaries. Two of the shared boundaries are mid-word rejoins (p370 → `populus`; p487 →
`poenitentiam`) and reconstitute correctly.

**Image spot-check on the GCS scans** (`_source/gcs29_pages/`): GCS p.280 ends its last line with a
hyphenated word-break and GCS p.281 opens with its continuation; the two halves form the single word
that the R7 rejoin produced, and the running text is continuous across the page turn. (Because the
diff-integrity gate proves no character other than the tags changed, every rejoin is character-
identical to the already image-verified pre-R7 base with its tag removed — continuity is preserved by
construction.)

## Final validation

- `grep -c "\[GCS p\."` = **0** in all 16 `LATIN/` files and all 16 `passB_final/` files.
- `LATIN/` ↔ `passB_final/` running text **byte-identical** over the body in all 16 (validator's
  `body_of`).
- `python3 _source/scratchpad/validate.py` → **ALL 16 CLEAN.** Guillemets balanced / no nesting / no
  stray marks; no consonantal J/j; per-homily doxology signature present; section numbers in sequence
  from 1; LATIN ↔ passB_final byte-identical. The `[GCS p.N]` monotonic/contiguous/coverage check
  **auto-skips** now that the files carry no anchors (the validator was made R7-aware: a file with no
  anchors skips its per-file anchor block, and the cross-file coverage/shared-page block skips when
  no anchors exist anywhere) — this is the expected and correct R7 outcome; every other check passes.

## End state

The deliverable `LATIN/homily01_latin.txt … homily16_latin.txt` is now a clean, tag-free, verified
Latin reading text. The page↔text map lives only in `variants_migne.md` and the pass reports. R7 is
the final base-text step; the base graduates to the translation phase.

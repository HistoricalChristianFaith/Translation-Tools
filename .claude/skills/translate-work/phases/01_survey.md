# Phase 01: Source survey (subagent, role `survey`)

You are researching one work, `state.json` → `work`, before a translation project starts. The
orchestrator and the user will choose sources based on your findings, so **be accurate and
concrete**. Verify identifiers, and actually test downloads. A wrong or broken source costs days.

`MODE: re-search` means: a previous survey exists
(`${RUN_DIR}/survey.json`), and the user gave a hint (in your assignment file,
`${RUN_DIR}/assignments/survey/survey.md`). Search again around the hint, then update
both files. `MODE: user-files` means the user already put files into `_source/incoming/`
(base/, oracle/, witness/): identify each one first (`pdf_pages.py info`), and recommend a
user-supplied base if it is fit for the job.

## What to find out

1. **How the work survives.** Original language, or only in an ancient translation (e.g.
   Rufinus's Latin of Origen's lost Greek), or as fragments (catenae, papyri, citations).
   Complete or partial? How many units (homilies, books, chapters, fragments), and how are they
   numbered? CPG / CPL / BHL number if easy to find.
2. **Existing English translations.** Every one you can find, and **whether any is in the public
   domain** (e.g. in the Ante-Nicene Fathers, or on CCEL / New Advent). A PD English translation
   is a reason the user may not need this project; flag it prominently.
3. **Base edition candidates** (the text to transcribe). Prefer, in order:
   - a public-domain **critical edition** (GCS, CSEL, CCSL volumes old enough to be PD; *Journal
     of Theological Studies* editions; Lommatzsch; Delarue);
   - **Migne** PG/PL (always PD; OCR usually unusable, so image-first).

   For each PD candidate, give exact volume, pages or columns, year, and a **scan source**.
4. **Copyright base candidates**: every modern critical edition of the work (Sources
   Chrétiennes, CCSL/CCSG, CSEL, GCS Neue Folge, Vetus Latina AGLB, Teubner, Oxford Classical
   Texts, …), each **with the exact names** a user needs to obtain it: editor(s), full title as
   printed, series and volume number (and which units each volume holds, for multi-volume
   editions), place, publisher, year, page range of the work. We can't download these, but we can
   translate from one if the user obtains it, and a modern critical text is often the better base.
   It is usually the text the oracle translates (say so: then R3 and grading flag real errors,
   not edition differences). For each, also give 2–4 **search strings** (exact title in quotes, series
   + volume, editor + short title) and the places it can turn up (publisher, library catalogue
   (WorldCat), Brepols *Library of Latin Texts* / TLG for a digital text, Google Books for
   previews). Verify each citation against a catalogue record or the publisher; a guessed
   volume number costs the user a wrong purchase. Don't download copyright scans yourself.
5. **Secondary witness**: another PD printing of the same text for collation (Migne against a
   GCS base; Lommatzsch against Migne; Cramer's *Catenae* against a JTS catena edition). Give its
   scan source too.
6. **Oracle candidates**: modern English translations of this exact text (Fathers of the Church,
   Ancient Christian Writers, Oxford Early Christian Studies, Church's Bible anthologies, …).
   For each, note how closely it tracks the base. Does it translate the same edition, a later
   critical edition, or selected excerpts only?
7. **Other sources for resolving doubts** (used late, by R8): digitized manuscripts (shelfmark,
   library viewer or IIIF manifest URL, folio range if known; the edition's sigla and folio
   markers point to them), other printed editions and digital texts not chosen as witness.
   (Copyright critical editions go in `copyright_bases`, not here; R8 consults both.)
8. **Foreseeable editorial decisions**: choices the edition's typography or the oracle already
   show will come up (how the English renders cruxes, lacunae, rubrics; Psalm or book
   numbering; name forms; inline folio or manuscript markers; typefaces that mark
   catena or Scripture passages; a code-point set for Greek). Each with options and a
   recommendation; the user answers them at plan approval. (Supplements and seclusions of a
   critical edition are house policy, not a decision: `12_configure.md`.)
9. **Hazards** that affect the method, for example:
   - the base is Migne (image-first);
   - polytonic Greek (OCR useless for text);
   - fragments spread over several journal issues (seams);
   - interleaved material from other works;
   - a translator who abridged;
   - an archive item that won't download.

## How to search

- Use WebSearch / WebFetch for bibliography (e.g. Wikipedia or the Clavis for the survival
  facts; publisher pages for the oracles).
- archive.org:
  - `python3 ${TOOLS_DIR}/archive_item.py search '<query>'`
    (e.g. `'title:(origenes werke) AND year:[1899 TO 1941]'`, `'patrologiae cursus completus
    graeca 12'`, `'journal of theological studies 1908'`);
  - `python3 ${TOOLS_DIR}/archive_item.py files <item>` lists an item's files.
- **Download test (mandatory for every candidate you recommend):**
  `python3 ${TOOLS_DIR}/archive_item.py test <item>`. It checks that the jp2 zip / PDF / OCR
  actually download (200 or 206). Some multi-volume items 404 on every file. Then look for a
  standalone upload of the same edition, and say which one works.
- **Find the pages.** Use the item's OCR (`archive_item.py ocr <item> --out ${RUN_DIR}/logs/<item>_ocr.txt`)
  or its page map (`archive_item.py pagemap <item> --out …`) to locate the work's printed page
  range. Report pages *as printed* and, if you can, the leaf range. Don't render images; that is
  the staging phase's job.
- Google Books and HathiTrust are fine for *identifying* editions. Prefer archive.org for
  *downloading*.

### Where sources have turned up before

These come from past projects (the Origen works). Check them first:

- **GCS (*Origenes Werke*, *Die griechischen christlichen Schriftsteller*)**: archive.org scans,
  e.g. `origenes-werke.-bd-3-1901` (GCS 6), `origenes-werke.-bd-6-1920` (GCS 29),
  `origenes-werke.-bd-7-1921` (GCS 30), `origenes-werke.-bd.-9-1930` (GCS 35), `GCS33`. Item names
  are inconsistent, so search by title and year as well.
- **Migne PG/PL**: archive.org, e.g. `patrologiae_cursus_completus_gr_vol_012`. Use it as the base
  when no PD critical edition exists (e.g. *Hom. in Ps. 36–38*), otherwise as the witness.
- **JTS catena editions** (Gregg on Ephesians, Jenkins on 1 Corinthians): archive.org
  `sim_journal-of-theological-studies_<YYYY-MM>_<vol>`, one item per issue. Also on
  biblicalstudies.org.uk. **Cramer's *Catenae*** is the usual witness for these.
- **Lommatzsch** and older printings: archive.org / Google Books (`bub_gb_…` items).
- **Digital Greek text:** First1KGreek (`github.com/OpenGreekAndLatin/First1KGreek`,
  `data/tlgNNNN/…`) and Scaife/Perseus (`urn:cts:greekLit:tlgNNNN.tlgNNN`). These are TEI
  transcriptions of the PD editions. They are useful as a scaffold, but they carry OCR and markup
  errors, so collate them against the page images.
- **Digital Latin text:** Corpus Corporum (`mlat.uzh.ch`). It has TEI transcriptions, often of
  Migne. Use them as a scaffold, then collate.
- **CLLG Freed Corpus** (`https://gitlab.inria.fr/almanach/cllg/freed-corpus`): TEI XML of about
  1,800 Greek authors from the TLG E CD-ROM. Files are at
  `data/tlgAAAA/tlgWWW/tlgAAAA.tlgWWW.cllg-grc1.xml`, using the same TLG author/work numbers as
  First1KGreek (e.g. Origen = `tlg2042`). It covers far more Greek than First1KGreek. It is a
  digital scaffold, not a page image, so collate it the same way.
- **Copyright-only works** (e.g. *Treatise on the Passover*): there is no PD base. The user drops
  a modern edition into `_source/incoming/base/` and it stays git-ignored. Its exact names go in
  `copyright_bases` like any other copyright edition.
- `existing_english[].coverage` must be one of `complete` | `most` | `excerpts`.
- If the user must source something, write **specific hints** (the user will drop files into
  `_source/incoming/base/`, `…/oracle/` or `…/witness/`; say which): exact title, editor, year,
  series and volume, page or column range, and 2–4 search strings and sites to try.

## Output (fixed paths)

### `${RUN_DIR}/survey.json`

Keep it **compact** (the orchestrator reads it). Short strings, no prose paragraphs:

```json
{
  "work": "Origen, Homilies on Leviticus",
  "author_folder": "Origen of Alexandria", "work_folder": "Homilies on Leviticus",
  "clavis": "CPG 1416",
  "survival": {"summary": "Greek lost; complete in Rufinus's Latin (c. 403-405)",
               "language": "Latin", "form": "ancient-translation", "units": {"noun": "homily", "count": 16},
               "numbering": "I-XVI"},
  "existing_english": [{"citation": "Barkley, FOTC 83 (1990)", "public_domain": false, "coverage": "complete"},
                       {"citation": "Tollinton, Selections (1929)", "public_domain": true, "coverage": "excerpts"}],
  "base_candidates": [
    {"id": "B1", "citation": "Baehrens, GCS 29 (Origenes Werke VI, 1920), pp. 280-507",
     "public_domain": true, "source": "archive.org", "item": "origenes-werke.-bd-6-1920",
     "download_test": "ok", "formats": ["jp2", "djvu_txt", "pdf", "page_numbers"],
     "ocr": "usable-latin-draft", "text_layer": "ocr", "pages": "280-507", "leaves": "339-579", "recommended": true,
     "notes": "page->leaf offset drifts; p.393 double-scanned"}
  ],
  "witness_candidates": [
    {"id": "W1", "citation": "Migne PG 12, cols. 405-574", "public_domain": true,
     "source": "archive.org", "item": "patrologiae_cursus_completus_gr_vol_012",
     "download_test": "ok", "pages": "cols 405-574", "recommended": true, "notes": "Latin OCR unusable"}
  ],
  "oracle_candidates": [
    {"id": "O1", "citation": "Barkley, Origen: Homilies on Leviticus 1-16, FOTC 83 (CUA Press, 1990)",
     "coverage": "all 16 homilies", "tracks": "same GCS edition", "recommended": true}
  ],
  "other_sources": [{"id": "M1", "kind": "manuscript", "citation": "Monac. gr. 314 (s. XI)",
                     "access": "<IIIF manifest URL>", "coverage": "all units", "notes": "GCS folio markers"}],
  "anticipated_decisions": [{"question": "Psalm numbers in the English: LXX only, or LXX with Hebrew?",
                             "options": ["LXX + Hebrew::Ps 36 (37)", "LXX::as the text numbers them"],
                             "recommended": "LXX + Hebrew", "why": "readers use English Bibles"}],
  "copyright_bases": [
    {"id": "C1", "citation": "Borret, Origène: Homélies sur le Lévitique, SC 286-287 (Paris: Cerf, 1981)",
     "volumes": ["SC 286: Hom. 1-7", "SC 287: Hom. 8-16"], "pages": "SC 286 pp. <from>-<to>; SC 287 pp. <from>-<to>",
     "text": "Baehrens's GCS text revised, with French translation", "oracle_tracks": false,
     "advantage": "newer collation; facing French", "verified": "WorldCat + Cerf catalogue",
     "search": ["\"Homélies sur le Lévitique\" Borret", "Sources Chrétiennes 286", "SC 287 Origène Lévitique"],
     "where": "Éditions du Cerf; library (WorldCat); Google Books preview"}
  ],
  "hazards": ["Rufinus expanded freely: oracle tracks loosely"],
  "user_sourcing_hints": [],
  "no_pd_base_possible": false
}
```

If no base candidate downloads, keep the candidates (with `"download_test": "failed: 404"`),
set no `recommended`, and fill `user_sourcing_hints`. Set `no_pd_base_possible: true` only when
the work demonstrably has no public-domain edition (e.g. first edited in 1979).

`copyright_bases` lists every modern critical edition you found, even when a good PD base exists:
the user may prefer to obtain one (the interview offers it next to the PD bases). Fields:
`citation` (editor, title as printed, series + volume, place: publisher, year), `volumes` (which
units each volume holds; one entry if a single volume), `pages`, `text` (what the edition is),
`oracle_tracks` (true if the recommended oracle translates this edition), `advantage` (one line:
why it beats the PD base, or `none`), `verified` (where you checked the citation, or
`unverified`), `search` (2–4 strings), `where`. Empty list only if none exists.

### `${RUN_DIR}/survey.md`

The human-readable version: the same facts with sources (URLs) for every claim, the full
edition table (edition | year | PD? | role), the download-test results, and a section
**Copyright editions you could obtain** (each `copyright_bases` entry in full, with its search
strings and where to look).

### Status

Status `${RUN_DIR}/status/survey/survey.json` (see `status_contract.md`; `fixes` = 0), and
notes `${RUN_DIR}/notes/survey/survey.md` (Summary + Doubts). Return under 20 words.

# Shared: text conventions (every source-text phase)

The project README (`_source/README.md`) may refine these. **Where it does, the README wins.**
Resolved editorial decisions (`decisions.py list --resolved`) win over both.

## File format (non-negotiable; every tool depends on it)

One file per unit, in `<LANG_DIR>/` (e.g. `LATIN/homily05_latin.txt`, `GREEK/frag11_greek.txt`):

```
# <Author>, <Work> — <Unit label> (<passage>). <one-line description>
# <how the text survives, e.g. "Rufinus's Latin translation (c. 403-405)">
# Source text: <edition, volume, pages/columns>
# Scripture is quoted in the author's own wording (<e.g. Old-Latin / LXX>).
============================================================
<HEADING LINE exactly as in manifest.json, e.g. "HOMILIA V." or "§ XI">
<*lemma line*, if the unit has one>
[GCS p.332] 1. First paragraph, ALL ON ONE PHYSICAL LINE ...
2. Second paragraph ... [GCS p.333] ... continues on the same line ...
```

- **Every paragraph is exactly one physical line.** Never hard-wrap. Blank lines between
  paragraphs are optional.
- The `#` lines and the `====` line are the header. Everything after `====` is the body.
- The heading line must match the unit's `heading` in `run/manifest.json`.
- Section numbers (`1.`, `2.`, …) start their line, after any page anchor, exactly as printed.

## Marks

| Mark | Use |
|---|---|
| `» … «` | Scripture the author quotes (whatever the edition prints: guillemets, italics, spaced or uncial type). Balanced, never nested. |
| `* … *` | the lemma under comment: the heading lemma line, and lemma words recurring in the exposition, if the edition marks them (bold/clarendon, spaced) |
| `⟨ … ⟩` | the editor's supplement, as printed |
| `[ … ]` | the editor's seclusion, **or** a printed rubric (e.g. `[Ὠριγένους]`) or verse label (e.g. `[iv 16]`), as printed |
| `[[ … ]]` | the editor's double brackets, as printed |
| `† … †` | an obelized crux, as printed |
| `…` `. . .` `* * * *` | a printed lacuna, exactly as printed. **Never fill a lacuna.** |
| page anchor | the manifest's `anchor.format`, e.g. `[GCS p.332]`, `[PG 1320]`, `[JTS 9 p.231]`. Placed exactly where the page or column turns, **even mid-word** (`pres[GCS p.259]byteri`). One per page, in order. The anchor of the page where a unit starts opens its first body line. Stripped only at R7. |

## What goes in, what stays out

- **In:** the main text of the edition, i.e. the author's words as the editor printed them
  (the *adopted* text).
- **Out:** the critical apparatus, footnotes, marginal numbers, running heads, printed page
  numbers, editor's introductions, and material interleaved from *other* works (e.g. catena
  scholia printed between homilies in Migne).
- **Other-language material** inside the body is controlled by the README / decisions. The default
  is to keep a word in its own script **only** when the author himself cites or glosses it
  (e.g. Origen explaining the Greek ἅγιος inside the Latin). Log anything else you leave out in
  your notes (`## Doubts`), with its page.
- **Orthography exactly as printed** (e.g. *Istrahel*, *coelum*, *Moyses*). Don't modernize. A
  uniform normalization (e.g. J→I) happens only if a resolved decision says so, and then
  everywhere.
- **Polytonic Greek:** accents, breathings, iota subscript and final sigma exactly as printed.
  The OCR of such pages is never trusted for Greek letters.

## Editing discipline

- Fix only what the page image proves. Anything else is a doubt: log it in your notes, don't
  change it.
- Never renumber units, move unit boundaries, or change the manifest **by hand**. The manifest's
  `incipit` and `explicit` mirror the unit file, not the print: they are locators (the first and
  last few words of the body as it stands), and they follow the text. Sync one with
  `python3 "${TOOLS_DIR}/manifest_edit.py" --work-dir "${WORK_DIR}" --unit <n> --field incipit|explicit --value "<the words as in the file>" --by <PHASE>/<id> --reason "<what you checked>"`
  when either:
  - you changed words inside it, for any reason (a fix, an emendation, a normalization): in the
    same step; or
  - it disagrees with the unit file, and in this pass you checked the text at that spot on the
    image and found it right (or carrying a recorded emendation).

  Never sync a field to text you haven't checked or changed, and **never edit text toward a
  field**: the image decides, the field only tells you where to look. The tool refuses a value
  that isn't where the field must be in the file (exit 1); exit 3 means another agent holds the
  lock: retry. Anything else in the manifest (`label`, `passage`, `pages`, boundaries,
  numbering): if the image contradicts it, report it (notes `## Carry-forward` tagged `[R4]` or
  `[orchestrator]`) and leave the structure as it is.
- Edit **only the unit files of your packet**. A **sub-packet** agent edits only the text of its
  own pages, with small in-place edits (`status_contract.md` → Sub-packets). Never edit another packet's units, the manifest,
  `state.json`, or shared reports. Your written output goes only to your notes and status files.

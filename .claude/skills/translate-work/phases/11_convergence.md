# Phase 11: Convergence re-read (subagent, one packet)

Prove the text is **stable**: a fresh reader re-reading it against the images finds nothing
substantive left to change.

Follow `05_recollate.md` exactly (lensless, word by word, band by band, crop before every
change), with these differences:

- The text is **no longer purely diplomatic**. Before changing anything, read the R6 emendations
  (`apparatus_pass.md` → the docket and `## Settled cruxes`), the R8 dispositions
  (`doubt_resolution.md`) and the resolved decisions (e.g. a
  uniform normalization). Those are **intentional** departures from the print. **Never revert
  them.**
- The manifest's `incipit` and `explicit` are locators, not evidence. Judge the boundary on the image; if the text is right and the field differs, sync the field with `manifest_edit.py` (`conventions.md` → *Editing discipline*). Never edit text toward a field. An emended reading stays emended: text ≠ print at an emended spot is not a slip.
- Classify every change you make:
  - **substantive:** a word added, dropped or changed; wrong word form; a mis-scoped `» «` or
    `* *`; wrong section or anchor placement; a lost or duplicated line;
  - **minor:** accent, breathing or punctuation without sense change; spacing.
- Notes `${RUN_DIR}/notes/convergence/<packet>.md`: list every change with its class. Status
  `${RUN_DIR}/status/convergence/<packet>.json` with an **extra field `"substantive": <count>`**
  (and `fixes` = all changes).

`substantive: 0` across all packets means the text has converged, which is the expected result.
Don't manufacture changes, and don't suppress real ones.

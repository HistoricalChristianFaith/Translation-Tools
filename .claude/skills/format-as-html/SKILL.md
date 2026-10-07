---
name: format-as-html
description: >
  Publish a translated work's English (the english/*_english.txt units a /translate-work run
  produces) as a Writings-Database HTML fragment: <article class="writing">, <h2> sections, <br><br>
  paragraphs, Scripture in <i>. Interviews the user for the output location, drafts a per-work
  html_config.py, renders with a tested tool, and proves the HTML holds exactly the English text
  before writing. Never commits.
argument-hint: "<work folder path | 'Author, Work'>"
---

# /format-as-html

You turn one work's finished English translation into its HTML page in the Writings-Database repo.
All parsing, rendering and checking is done by the tools below. **You never hand-write or hand-edit
the HTML**, and you never change the English. Your job: settle the choices the tools can't (location,
mark meanings, the source note, drops that carry information), with the user, inside the config.

`T` = `<this skill's folder>/tools` (the folder of this SKILL.md; if unsure, Glob
`**/format-as-html/SKILL.md`). Run tools as `python3 "T/<tool>.py" …`
with every path double-quoted (zsh). A gate passes only if its line reads `GATE <name>: PASS`; never pipe a
gate command.

House format authority: `<Writings-Database>/CLAUDE.md` (a bare fragment, no `<script>`). If that repo's
`AGENTS.md` still asks for the highlight.js `<script>`, tell the user once that it is out of date; don't follow it.

## 1. Locate the work

- The argument is a work folder (`…/Writings-Database-Non-English/<Author>/<Work>`), or "Author, Work":
  then look under the `Writings-Database-Non-English` root (current directory, its parents, `~/Desktop`).
- Require `english/*_english.txt`. If `_source/run/state.json` exists and `report` isn't `done`
  (`python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["phases"]["report"]["status"])' "<W>/_source/run/state.json"`),
  warn that the translation isn't finished and ask [Continue anyway / Stop].
- If `<W>/html_config.py` already exists, this is a **re-run**: skip to step 5.

## 2. Location interview

Run `python3 "T/locate.py" --work-dir "<W>"`. It lists the valid Writings-Database roots and numbered
options, the recommended one first: replace an existing file for the work, a new file
`<Author>/<Work>.html`, a new folder of per-unit files, or close name matches.

Ask with one `AskUserQuestion` (header "Location"): "Where should the HTML for <Work> go?" Offer up
to 4 of locate's options as quick selects, the first labelled "(Recommended)", each description
giving the full path. The user can type another path through "Other". With more than one valid
root, the root is part of each option's description. If locate found no root, ask for the
Writings-Database folder in plain text and end your turn.

The file name of an existing page must not change (other repos cite it by URL), so a "replace"
option keeps it exactly.

## 3. Census and draft

```
python3 "T/mark_census.py" --work-dir "<W>"
python3 "T/draft_config.py" --work-dir "<W>" --root "<root>" --relpath "<Author>/<Work>.html"
        (folder mode: --reldir "<Author>/<Work>")
```
The census shows each unit's first block (the printed heading the HTML replaces), verse-number
openers, in-body labels, and the mark characters with counts. The drafter writes `<W>/html_config.py`
with guesses marked `# GUESS`, every `MARKS` value `None`, and a `SOURCE_NOTE` with TODOs. The build
refuses to run until those are settled.

## 4. Settle the config (you), then ask the user once

Edit `<W>/html_config.py`:
- **MARKS:** read the run's `_source/run/work_config.py` → `TRANSLATION_RULES` (and its comments) for
  what each mark means. **Rule: a mark that encloses Scripture or lemmata → `"italic"`; other quotation
  → `"quote"`**; typographic quotes → `"straight"`. Cite the rule in the line's comment.
- **SOURCE_NOTE:** one paragraph, modelled on the sibling pages by the same author in the repo (read
  the first `<i>…</i>` line of one or two). Cover: the work and its date, the edition with `{pages}`,
  verification, the lemma/Scripture conventions, Greek/Hebrew handling, what was left untranslated
  (from `decisions.jsonl` and `FINAL_REPORT.md`). Inline `<i>` is allowed for series titles.
- **RELEASE / RIGHTS_CONFIRMED:** `RELEASE = "public-domain"` adds the release sentence. If
  `state.json` `base_license` is `copyright`, the `rights` gate needs `RIGHTS_CONFIRMED = True`, which
  only the user can give.
- **Headings:** check the drafted `UNIT_HEADINGS` against the existing page's heading *form* (e.g.
  `1:2-4`); keep the run's divisions. Works with headings inside units (Isaiah-style labels) need
  `BLOCK_LABELS`; see the template's comment and `htmlkit.build_items`.
- Resolve every `# GUESS` (fix it or delete the marker).

Then **one** `AskUserQuestion` (up to 4 questions), only those that apply:
1. (header "Title") if an existing page's `<h1>` differs from `H1`: keep the old title or use the new one;
2. (header "Headings") if the divisions differ from the existing page's: show both lists;
3. (header "Dropped") if a dropped item carries information (an incipit rubric, a verse number in the
   middle of a unit; the build's "dropped/stripped" list): drop it (Recommended) / keep it (`KEEP_PREFIX`);
4. (header "Rights") with a copyright base: add the public-domain release sentence? [No (Recommended) / Yes].
Show the full source note in your message and ask the user to approve it (or reply with changes).

## 5. Build, check, diff

```
python3 "T/build_html.py" --work-dir "<W>" --diff
```
Every gate must pass: `census` (every mark declared), `structure` (units, labels vs passages, coverage,
text under every heading), `marks`, `house`, `fidelity` (the HTML holds exactly the English text,
in order, minus the listed drops), `notes`, `rights`. Fix the config, never the English, and re-run.
A failure that the config can't fix (a real problem in the English: an unpaired mark, a missing unit)
goes to the user. It belongs to the translation, not to this skill.

Read the `--diff` section aloud to the user in two or three lines:
- `identical`: nothing to write;
- `re-render` (written by the last build): the changes are the English edits since then;
- `CHANGED BY HAND` / `not written by this skill`: show the listed differences. Fold any the user
  wants to keep into the config (a note sentence, a title), re-run until only the intended changes
  remain, then they decide;
- a replacement (similarity below 0.6): show the heading lists and word counts, not a text diff.

## 6. Write

Only after the user approves (or at once, if their request already said to write):
```
python3 "T/build_html.py" --work-dir "<W>" --write            (add --replace only after the user approved the diff)
python3 "T/check_html.py" "<target file>" --work-dir "<W>"
```
`--write` records `LAST_BUILD` (the output's hash) in the config, so the next run can tell a clean
re-render from hand edits.

## 7. Report (a few lines)

The target path; units, paragraphs, words; all gates PASS; what was dropped; open advisories; the
rights status. Say whether `english/` and `html_config.py` are untracked in git
(`git -C "<W>" status --short -- english html_config.py`): if so, they're the only record that can
rebuild this page. **Don't commit and don't offer to commit**, in either repo.

## Re-runs

After a translation fix: steps 5–7 with the saved config. `check_html.py <file>` alone audits any page
in the repo against the house format (read-only).

## Tests

`python3 -m unittest discover -s "<this skill's folder>/tests"` runs the synthetic suite, including a
byte-for-byte comparison with the frozen legacy Obadiah script.

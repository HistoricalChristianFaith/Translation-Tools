# /translate-work

A Claude Code skill that produces a fresh, verified English translation of a patristic or
medieval work from the page images of a public-domain edition. It automates the process described
in [`TRANSLATION_PROCESS.md`](../../../TRANSLATION_PROCESS.md). Its orchestration pattern:
a lean orchestrator, phase files that subagents read
themselves, fixed output files, waves of at most 6 agents, and checklist gates.

## What you interact with

1. `/translate-work Origen, Homilies on Numbers`, or just `/translate-work` and answer "which
   work?".
2. **Workspace.** Confirm where the work folder lives. If a run already exists there, you're
   offered a resume.
3. **Survey.** First you're asked whether you already have files (base, oracle, witness) to drop
   in. Then a subagent researches how the work survives, existing English translations,
   public-domain base editions (with a live download test), a secondary witness, the candidate
   oracles, other sources (e.g. a digitized manuscript), and the decisions it can foresee.
4. **Base text.** Accept the recommended edition, or drop your own copy into
   `_source/incoming/base/` (you get specific search hints).
5. **Oracle.** Optionally drop a copy of a modern translation into `_source/incoming/oracle/`.
   It's copyright, used only as a detector and yardstick, and never copied.
6. **Plan.** Approve it, and choose the autonomy level (checkpoints / guided / autonomous),
   whether translation may consult page images, and whether to auto-commit. The foreseeable
   editorial decisions are asked here too, so the run stops less later.
7. The run proceeds on its own through the phases. It stops only for batched editorial
   decisions (by autonomy level) or when blocked. It prints one progress line per phase.
8. **Result:** `<work>/english/<unit>_english.txt`, plus `_source/run/FINAL_REPORT.md`.

A run takes hours to days. Re-run `/translate-work <work folder>` in a new session to resume.

## Layout

```
translate-work/
├── SKILL.md            orchestrator: model check, interview, dispatch rules, gates, resume
├── phases/             one file per phase; subagents read these themselves
│   ├── shared/         boot (subagent entry point), conventions, image reading, content filter, copyright, status contract
│   ├── 00_interview.md (orchestrator) … 16_report.md, gate_repair.md
│   │   (03b_normalize.md: scripted seed clean-up before B; 10b_doubts.md: R8 doubt resolution;
│   │    13_translate.md, 14a_validate_scan.md, 15a_grade_scan.md: per unit, in batches)
├── tools/              deterministic helpers (Python 3 + Pillow; poppler, OpenJPEG)
│   ├── state.py  status_check.py  decisions.py  merge_notes.py        run bookkeeping
│   ├── packets.py  checklist.py  doubts.py            sub-packets, completeness checklists, doubt ledger
│   ├── archive_item.py  pdf_pages.py  crop.py                         staging + image reading
│   ├── manifest_check.py  check_base.py  base_check.py  strip_anchors.py   source-text gates
│   ├── normalize_check.py  manifest_edit.py   normalize gate; locked incipit/explicit sync
│   ├── translate.py  validate.py  grade.py   bundles for the per-unit agents + checks of their output
│   ├── common.py  skill_config_base.py  work_config_template.py
│   └── scratch_copy.py                        a test copy of a run that can't touch the original
└── templates/          source README template
```

## Workspace a run creates

```
<Work>/
├── LATIN/ | GREEK/ …          the verified source text, one file per unit
├── english/                   the translation, one file per unit
└── _source/                   git-ignored
    ├── README.md              the project spec (binding on every agent)
    ├── incoming/{base,oracle,witness}/   your drop-ins
    ├── pages/{base,witness}/  rendered page images + index.json
    ├── ocr/  oracle/          OCR slices; the oracle and its per-unit extracts (local only)
    ├── *.md                   one report per pass + uncertain_readings.md
    └── run/                   state.json, survey.json, manifest.json, packets.json,
                               status/, notes/, checklists/, decisions.jsonl, doubts.jsonl, carry_forward.md,
                               orchestrator_acks.jsonl ([orchestrator] items settled),
                               manifest_edits.jsonl (incipit/explicit syncs; manifest.lock),
                               normalize/ (this run's normalize.py, seed.py, summary),
                               bundles/<PHASE>/ (one per unit: what each translate / scan agent sees),
                               translate/ (agents' marked output; replaced/ = English moved aside),
                               findings/<round>/ (scan findings + apply journals),
                               structure_settled/ (structure warnings checked and settled),
                               snapshots/, logs/, crops/, work_config.py, FINAL_REPORT.md
```

## Installing elsewhere

In this repository the skill is picked up automatically as a project skill. To make it
available everywhere:

```
cp -R .claude/skills/translate-work ~/.claude/skills/
```

(The skill's `tools/` is its real home; the repository's top-level `tools` is a symlink to it.)

Requirements:
- Claude Code, with the model pin in the project's `.claude/settings.json` (the orchestrator on
  `claude-opus-5-5[1m]`, every subagent on `claude-opus-5-5`; SKILL.md Step 0 checks it). Installed
  under `~/.claude/skills/`, put the pin in `~/.claude/settings.json`;
- Python 3 with Pillow;
- `brew install poppler openjpeg tesseract tesseract-lang` (tesseract is optional).

Built for Claude Opus 5.5. The skill never runs `claude` headlessly: every model call is a
subagent of the session you run `/translate-work` in, and nothing bypasses permissions. To cut approval prompts, allowlist `python3` calls to the skill's
`tools/*.py` and Read/Edit/Write under your works folder (absolute paths in Read/Edit rules take
the `//` prefix); draft the exact rules from a real run with the `fewer-permission-prompts` skill.

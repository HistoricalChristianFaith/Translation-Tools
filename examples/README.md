# Examples

Real artifacts from the Origen translation projects, copied here so the process can be followed
without access to the original machine. The originals live in the (partly untracked)
HistoricalChristianFaith `Scripts` repo and in the git-ignored `_source/` workspaces of
`Writings-Database-Non-English`.

- `configs/`: configs for the generic `tools/`. They reproduce the Leviticus (Latin homilies) and
  1 Corinthians (Greek catena fragments) runs. They were checked against the originals: same
  parsed blocks, headings and oracle text for every unit.
- `original-scripts/`: **verbatim snapshots** of the per-work scripts as used (September 2026):
  translate, validate and grade, for Leviticus and 1 Corinthians. They contain
  hard-coded absolute paths and per-unit metadata. Read them as worked examples; don't run them
  as-is. Oracle file paths were made generic (`_source/oracle/oracle.pdf`) in these copies and
  throughout `examples/`. `base-text-helpers/` holds per-project scripts from `_source/scratchpad/` (validator,
  assembler, anchor strip, disk-to-disk file builder).
- `pass-prompts/`: prompts and subagent briefs for base-text passes B, R1, R2, R3 and R4, named
  `<pass>_<what>__<work>.md`.
- `source-workspace/`: two `_source/README.md` planning documents and two pass reports (R2
  re-collation, R7 anchor strip). Reports that quote oracle translations are deliberately not
  included (copyright). A few sentences about steps outside this workflow were trimmed from these
  copies.

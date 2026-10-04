# Translation-Tool

An LLM-assisted workflow for producing fresh, public-domain English translations of patristic
texts. It starts from the printed page images of a public-domain edition and ends with a
validated plain-text English translation, one file per unit.

**To run it:** in Claude Code, type `/translate-work <author, work>`. The skill interviews you,
then orchestrates the whole process with subagents. See
[`.claude/skills/translate-work/README.md`](.claude/skills/translate-work/README.md).

**To understand it:** read [`TRANSLATION_PROCESS.md`](TRANSLATION_PROCESS.md). It covers
establishing the source text in logged passes, then translating, validating and grading.

- `.claude/skills/translate-work/`: the skill (orchestrator `SKILL.md`, `phases/`, `tools/`,
  `templates/`).
- `tools/`: a symlink to the skill's tools. That's the config-driven `translate.py`,
  `validate.py` and `grade.py` (bundles for the skill's per-unit subagents, and checks of what
  they write; they never call a model), the source-text helpers (`base_check.py`,
  `strip_anchors.py`, …), and the run bookkeeping. Needs Python 3; staging and grading also need
  poppler and OpenJPEG.
- `.claude/settings.json`: pins the model (the orchestrator on `claude-opus-5-5[1m]`, every
  subagent on `claude-opus-5-5`).
- `examples/`: configs, the original per-work scripts, and real pass prompts and reports.
- `templates/`: skeletons for a new work's workspace README and pass prompts (for running passes
  by hand).

## License

Public domain. To the extent possible under law, the authors have waived all copyright and
related rights to this work under [CC0 1.0](LICENSE).

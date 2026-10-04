#!/usr/bin/env python3
"""Grade the English against a published (usually copyright) ORACLE translation: the tool half of a
grade round. A scan subagent per unit does the model work (phases/15a_grade_scan.md); this tool
prepares its bundle and checks its findings file. Grading never writes to the English or source.

The oracle is the yardstick for SENSE; the source-language base goes in the bundle as context, so
the grader can tell a genuine divergence from a wording difference, from the oracle translator's
own freedom, or from a place where the oracle follows a different reading than our base.

The config supplies `oracle_text(n) -> str | None` (see common.oracle_from_file /
oracle_from_pdf_pages), GRADING_CAVEATS (known ways the oracle is NOT a tight yardstick), and
optional per-unit ORACLE_NOTES. Units without oracle text are `ungraded`.

    grade.py --config C bundle --phase K [--units 3,8]
        For every unit: delete its earlier files of round K (findings, scan status and notes),
        then write run/bundles/K/u<NN>.md: the shared part (work context, caveats;
        common.shared_bundle), then the unit part (the output path, the unit note, the source as
        context, the English body, the oracle extract). Prints `bundled:` and `ungraded:`.
    grade.py --config C check-findings --phase K --unit 7     # schema + enums; exit 0 = valid
    grade.py --config C summary --phase K [--units 3,8]       # the score table, for logs/<K>.log

Bundles hold oracle text: they live under the git-ignored `_source/`.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

SCHEMA = {"enums": {"sense_alignment": {"high", "moderate", "low"},
                    "coverage": {"full", "partial", "minimal"}},
          "list": "divergences",
          "item_required": ["locus", "severity", "category", "oracle", "ours", "note"],
          "item_nonempty": ["locus"],
          "item_enums": {"severity": {"minor", "moderate", "significant"},
                         "category": {"omission", "addition", "shifted-sense", "scripture", "name",
                                      "truncation"}}}


def normalize(obj):
    divs = []
    for d in obj.get("divergences") or []:
        if isinstance(d, dict):
            divs.append({"locus": str(d.get("locus", "?")),
                         "severity": str(d.get("severity", "moderate")).lower(),
                         "category": str(d.get("category", "shifted-sense")).lower(),
                         "oracle": str(d.get("oracle", "")), "ours": str(d.get("ours", "")),
                         "note": str(d.get("note", ""))})
    score = C.clamp_score(obj.get("score"))
    return {"score": score, "grade": str(obj.get("grade") or C.letter_for(score)),
            "sense_alignment": str(obj.get("sense_alignment", "")).lower(),
            "coverage": str(obj.get("coverage", "")).lower(), "divergences": divs,
            "summary": str(obj.get("summary", "")).strip()}


def oracle_for(cfg, n):
    covered = C.setting(cfg, "ORACLE_COVERED")
    if covered is not None and n not in covered:
        return None
    fn = getattr(cfg, "oracle_text", None)
    return fn(n) if fn else None


def cmd_bundle(cfg, a):
    lang = C.setting(cfg, "SOURCE_LANGUAGE")
    short, label = C.setting(cfg, "ORACLE_SHORT"), C.setting(cfg, "ORACLE_LABEL")
    bundled, ungraded = [], []
    for n in C.parse_units(cfg, a.units):
        src_file, eng_file = C.unit_files(cfg)[n]
        C.clean_scan_slate(cfg, a.phase, n, eng_file)
        bp = C.bundle_path(cfg, a.phase, n)
        oracle = oracle_for(cfg, n)
        if not (oracle and os.path.exists(eng_file) and os.path.exists(src_file)):
            C.remove(bp)
            ungraded.append(n)
            continue
        note = C.setting(cfg, "ORACLE_NOTES").get(n)
        shared = ["## Work context", C.setting(cfg, "WORK_CONTEXT").strip() or "(none)",
                  "", "## Grading caveats (ways the oracle is not a tight yardstick)",
                  C.setting(cfg, "GRADING_CAVEATS").strip() or "(none)"]
        text = C.shared_bundle("Grade", shared, f"{C.unit_label(cfg, n)} (unit {n}), round {a.phase}", [
            f"work: {C.setting(cfg, 'AUTHOR')}, {C.setting(cfg, 'WORK')}",
            f"source_language: {lang}",
            f"oracle: {short} ({label})",
            f"english_file: {eng_file}",
            f"output: {C.findings_path(cfg, a.phase, eng_file)}",
            "", "## Unit note (from the oracle-collation pass; read before grading)", note or "(none)",
            "", f"## {lang} source (context)", C.read(src_file).strip(),
            "", "## Our English translation (being graded)", C.english_body(C.read(eng_file)),
            "", f"## Reference: {short}", oracle.strip(), ""])
        C.write(bp, text)
        bundled.append(n)
    p = os.path.join(C.run_dir(cfg), "bundles", a.phase, "units.json")
    data = C.read_json(p, {"bundled": [], "ungraded": []})
    touched = set(bundled) | set(ungraded)
    data["bundled"] = sorted((set(data.get("bundled", [])) - touched) | set(bundled))
    data["ungraded"] = sorted((set(data.get("ungraded", [])) - touched) | set(ungraded))
    C.write_json(p, data)
    print("bundled: " + ",".join(C.uid(cfg, n) for n in bundled))
    print("ungraded: " + ",".join(C.uid(cfg, n) for n in ungraded))


def cmd_check_findings(cfg, a):
    n = C.resolve_unit(cfg, a.unit)
    _, eng_file = C.unit_files(cfg)[n]
    fp = C.findings_path(cfg, a.phase, eng_file)
    if not os.path.exists(fp):
        print(f"ERROR: no findings file {fp}")
        sys.exit(1)
    try:
        obj = C.read_json(fp)
        probs = C.check_schema(obj, SCHEMA)
    except json.JSONDecodeError as e:
        obj, probs = None, [f"not valid JSON: {e}"]
    for p in probs:
        print(f"ERROR {p}")
    if probs:
        sys.exit(1)
    print(f"OK: {len(obj['divergences'])} divergence(s)")


def cmd_summary(cfg, a):
    rec = C.read_json(os.path.join(C.run_dir(cfg), "bundles", a.phase, "units.json"), {})
    units = C.parse_units(cfg, a.units) if a.units else sorted(set(rec.get("bundled", [])) |
                                                               set(rec.get("ungraded", [])))
    rows = []
    for n in units:
        _, eng_file = C.unit_files(cfg)[n]
        name = os.path.basename(eng_file)
        fp = C.findings_path(cfg, a.phase, eng_file)
        if n in rec.get("ungraded", []):
            rows.append((name, "ungraded", None, ""))
            continue
        try:
            obj = C.read_json(fp)
        except json.JSONDecodeError:
            obj = "bad"
        if not isinstance(obj, dict):
            rows.append((name, "no findings" if obj is None else "unparseable", None, ""))
            continue
        g = normalize(obj)
        sig = sum(1 for d in g["divergences"] if d["severity"] == "significant")
        rows.append((name, None, g, f"({len(g['divergences'])} div, {sig} sig)"))
    print(f"Grading round {a.phase} against {C.setting(cfg, 'ORACLE_LABEL')}: {len(units)} unit(s)")
    C.print_score_table("GRADING SUMMARY", rows, "Mean sense fidelity")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("cmd", choices=["bundle", "check-findings", "summary"])
    ap.add_argument("--phase", required=True, help="round key, e.g. grade-r2")
    ap.add_argument("--units", help="comma list of unit numbers, u<NN> ids or batch ids")
    ap.add_argument("--unit")
    a = ap.parse_args()
    cfg = C.load_config(a.config)
    if a.cmd == "check-findings" and not a.unit:
        sys.exit("check-findings needs --unit <n>.")
    {"bundle": cmd_bundle, "check-findings": cmd_check_findings, "summary": cmd_summary}[a.cmd](cfg, a)


if __name__ == "__main__":
    main()

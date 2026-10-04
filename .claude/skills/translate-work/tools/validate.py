#!/usr/bin/env python3
"""Validate the English against OUR OWN source-language base (the sole arbiter): the tool half of a
validate round. A scan subagent per unit does the model work (phases/14a_validate_scan.md); this
tool prepares its bundle, checks its findings file, and applies the safe fixes.

  1. STRUCTURE (deterministic, free): source slots vs English paragraphs. ERROR = exact checks
     (English or source missing, block count). WARN = heuristics: a block shorter than
     SHORT_BLOCK_RATIO x its source (`short-ratio`), a block that stops mid-sentence where the
     source completes (`mid-sentence`), an ENDING_CHECKS pattern missing (`ending:<label>`).
     Blocks are numbered like the translate markers `@@ n @@` (held lines not counted). A WARN
     checked against the source and found not to be a slip is recorded with `settle` and prints
     as SETTLED while that block's English is unchanged.
  2. FIDELITY (the scan agent): findings JSON, checked by `check-findings`. Each finding may carry
     a fix {"old", "new"}; `apply` applies it only if `old` occurs exactly once and the result
     keeps the marks balanced and the block count unchanged (one predicate, shared with
     `check-findings`). Reviewers review the result against run/snapshots/pre-<round>/.

    validate.py --config C --structure-only [unit] [--units 3,8] [--summary]
        ERROR / WARN / SETTLED lines; exit 1 only if an ERROR was printed. Ends with
        `GATE validate: PASS` or `GATE validate: FAIL (<n> problem(s))` (n = ERROR lines).
        --summary: only the units with an ERROR (their ERROR lines) and the totals, including
        the `errors in:` / `open warnings in:` lines.
    validate.py --config C settle <unit> --check short-ratio [--block 7] --by translate/u07 --reason "..."
        Record a WARN as settled (run/structure_settled/u<NN>.json). Refuses a check that isn't
        currently raised. Unit-level checks (ending:<label>) take no --block.
    validate.py --config C bundle --phase K [--units 3,8]
        For every unit: delete its earlier files of round K (findings, apply journal, scan status
        and notes), then write run/bundles/K/u<NN>.md: the shared part (work context, house
        rules; common.shared_bundle), then the unit part (unit label, output path,
        english_sha256, open structure ERROR/WARN lines, the source file, the English body). A unit whose English or source is missing is `unvalidated`: no bundle.
        Prints `bundled: u01,...` and `unvalidated: ...`.
    validate.py --config C check-findings --phase K --unit 7
        Schema + enums of run/findings/K/<stem>.json, and every fix tried in order against the
        current English, exactly as `apply` would. Exit 0 = valid.
    validate.py --config C apply --phase K [--units 3,8]
        The fixes of each findings file, with a journal (run/findings/K/<stem>.apply.json) so a
        re-run never applies twice. Exit 0 only if every unit ends "done". Default units: the
        ones `bundle` bundled.
    validate.py --config C summary --phase K [--units 3,8]
        The score table, for logs/<K>.log.
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import gate  # noqa: E402

TRAILING_MARKS = r"[\s»«⟨⟩*'\"“”‘’)\]\[†]+$"
CATEGORIES = {"omission", "addition", "mistranslation", "sense-shift", "scripture", "name",
              "inconsistency", "untranslated"}
SEVERITIES = {"minor", "moderate", "significant"}
SCHEMA = {"enums": {"fidelity": {"high", "moderate", "low"}}, "list": "findings",
          "item_required": ["locus", "severity", "category", "source", "ours", "issue"],
          "item_nonempty": ["locus", "issue"],
          "item_enums": {"severity": SEVERITIES, "category": CATEGORIES}}


# --- Structure layer ------------------------------------------------------------------


def settled_path(cfg, n):
    return os.path.join(C.run_dir(cfg), "structure_settled", f"{C.uid(cfg, n)}.json")


def settled_records(cfg, n):
    if not getattr(cfg, "PROJECT", None):
        return []
    return C.read_json(settled_path(cfg, n), {}).get("records", [])


def issue(level, check, msg, block=None, sha=None):
    return {"level": level, "check": check, "block": block, "msg": msg, "sha": sha}


def structure_report(cfg, n, src_file=None, eng_file=None):
    if src_file is None:
        src_file, eng_file = C.unit_files(cfg)[n]
    if not (os.path.exists(eng_file) and os.path.getsize(eng_file) > 0):
        return {"n": n, "eng": eng_file, "status": "missing-english",
                "issues": [issue("ERROR", "missing-english", "English missing or empty")]}
    if not os.path.exists(src_file):
        return {"n": n, "eng": eng_file, "status": "missing-source",
                "issues": [issue("ERROR", "missing-source", f"source not found: {src_file}")]}

    _, slots = C.parse_source(cfg, C.read(src_file))
    eng_raw = C.read(eng_file)
    all_blocks, content = C.english_content_blocks(cfg, n, eng_raw)
    expected = len(slots) + (1 if C.english_heading(cfg, n) else 0)
    issues = []
    if len(all_blocks) != expected:
        issues.append(issue("ERROR", "block-count",
                            f"BLOCK COUNT {len(all_blocks)} vs expected {expected} -- a block may be "
                            f"dropped, split, or merged"))

    ratio_floor = C.setting(cfg, "SHORT_BLOCK_RATIO")
    min_src = C.setting(cfg, "SHORT_MIN_SOURCE")
    ratios, t = [], 0
    for s, e in zip(slots, content):
        if s["kind"] == "held":
            continue
        t += 1  # the block's translate-marker number
        src = s["text"]
        e_cmp = e[len(s["prefix"]):].strip() if s["prefix"] and e.startswith(s["prefix"].strip()) else e
        r = len(e_cmp) / len(src) if src else 9.0
        ratios.append(r)
        sha = C.sha256(e)
        if len(src) >= min_src and r < ratio_floor:
            issues.append(issue("WARN", "short-ratio", f"English {len(e_cmp)}c is {r:.2f}x its source "
                                f"{len(src)}c -- possible truncation", t, sha))
        e_core, s_core = re.sub(TRAILING_MARKS, "", e), re.sub(TRAILING_MARKS, "", src)
        if (len(src) >= min_src and e_core and e_core[-1] not in ".!?…·;:"
                and s_core and s_core[-1] in ".!?·;"):
            issues.append(issue("WARN", "mid-sentence",
                                f"ends mid-sentence (source completes) -> …{e[-45:]!r}", t, sha))

    src_all = "\n".join(s["text"] for s in slots)
    eng_all = "\n".join(content)
    body_sha = C.sha256(C.english_body(eng_raw))
    for src_re, en_re, label in C.setting(cfg, "ENDING_CHECKS"):
        if re.search(src_re, src_all) and not re.search(en_re, eng_all):
            issues.append(issue("WARN", f"ending:{label}", "present in the source, missing in the English",
                                None, body_sha))

    recs = settled_records(cfg, n)
    for i in issues:
        if i["level"] != "WARN":
            continue
        hit = next((r for r in recs if r["check"] == i["check"] and r.get("block") == i["block"]
                    and r["english_sha256"] == i["sha"]), None)
        if hit:
            i["level"], i["settled"] = "SETTLED", hit
    return {"n": n, "eng": eng_file, "status": "ok", "source_slots": len(slots),
            "english_blocks": len(all_blocks), "expected": expected,
            "min_ratio": min(ratios) if ratios else None, "issues": issues}


def issue_line(i):
    where = f"block {i['block']}" if i["block"] is not None else "unit"
    if i["level"] == "SETTLED":
        r = i["settled"]
        return f"SETTLED {where}: {i['check']} ({r['by']}: {r['reason']})"
    if i["check"] in ("block-count", "missing-english", "missing-source"):
        return f"{i['level']} {where}: {i['msg']}"
    return f"{i['level']} {where}: {i['check']}: {i['msg']}"


def counts(rep):
    lv = [i["level"] for i in rep["issues"]]
    return lv.count("ERROR"), lv.count("WARN"), lv.count("SETTLED")


def print_structure(cfg, rep):
    head = f"  {C.unit_label(cfg, rep['n'])}"
    e, w, s = counts(rep)
    if rep["status"] != "ok":
        print(f"{head}: {rep['status'].upper()}")
    else:
        mr = f"{rep['min_ratio']:.2f}" if rep["min_ratio"] is not None else "--"
        flag = ", ".join(f"{k} {v}" for k, v in (("ERROR", e), ("WARN", w), ("SETTLED", s)) if v) or "OK"
        print(f"{head}: source {rep['source_slots']} slots / english {rep['english_blocks']} blocks "
              f"(exp {rep['expected']}), min ratio {mr} -> {flag}")
    for i in rep["issues"]:
        print(f"        {issue_line(i)}")


def cmd_structure(cfg, a):
    units = [C.resolve_unit(cfg, a.unit)] if a.unit else C.parse_units(cfg, a.units)
    files = C.unit_files(cfg)
    missing = [n for n in units if n not in files]
    if missing:
        sys.exit(f"No source file for unit(s) {missing}.")
    tot_e = tot_w = tot_s = clean = 0
    with_err, with_warn = [], []
    for n in units:
        rep = structure_report(cfg, n)
        e, w, s = counts(rep)
        if not a.summary:
            print_structure(cfg, rep)
        elif e:  # --summary: a unit's ERROR lines only
            print(f"  {C.unit_label(cfg, rep['n'])}:")
            for i in rep["issues"]:
                if i["level"] == "ERROR":
                    print(f"        {issue_line(i)}")
        tot_e, tot_w, tot_s = tot_e + e, tot_w + w, tot_s + s
        clean += not e
        if e:
            with_err.append(C.uid(cfg, n))
        if w:
            with_warn.append(C.uid(cfg, n))
    print(f"\n  {clean}/{len(units)} file(s) without errors; {tot_w} open warning(s), {tot_s} settled")
    if with_err:
        print("  errors in: " + ",".join(with_err))
    if with_warn:
        print("  open warnings in: " + ",".join(with_warn))
    gate.finish(tot_e)


def cmd_settle(cfg, a):
    n = C.resolve_unit(cfg, a.unit)
    if not a.check or not a.by or not a.reason:
        sys.exit("settle needs --check, --by and --reason.")
    rep = structure_report(cfg, n)
    block = a.block
    match = [i for i in rep["issues"] if i["check"] == a.check and i["block"] == block]
    if any(i["level"] == "SETTLED" for i in match) and not any(i["level"] == "WARN" for i in match):
        print(f"already settled: {C.uid(cfg, n)} {a.check}" + (f" block {block}" if block else ""))
        return
    hit = next((i for i in match if i["level"] == "WARN"), None)
    if not hit:
        raised = ", ".join(f"{i['check']}" + (f" block {i['block']}" if i["block"] is not None else "")
                           for i in rep["issues"] if i["level"] == "WARN") or "none"
        print(f"REFUSED: {a.check}" + (f" block {block}" if block else "") +
              f" is not currently raised on {C.uid(cfg, n)} (open warnings: {raised}).")
        sys.exit(1)
    p = settled_path(cfg, n)
    data = C.read_json(p, {"records": []})
    data["records"].append({"unit": n, "block": block, "check": a.check, "english_sha256": hit["sha"],
                            "by": a.by, "reason": a.reason, "at": C.now()})
    C.write_json(p, data)
    print(f"settled: {C.uid(cfg, n)} {a.check}" + (f" block {block}" if block else ""))


# --- Fixes ----------------------------------------------------------------------------


def fix_problem(cfg, text, n_blocks, old, new):
    """The guard every fix must pass (shared by check-findings and apply).
    -> (None, new text) or (reason, None)."""
    if old == new:
        return "old == new", None
    count = text.count(old)
    if count != 1:
        return ("`old` not found" if count == 0 else f"`old` not unique ({count})"), None
    cand = text.replace(old, new, 1)
    body = C.english_body(cand)
    if not C.marks_ok(cfg, body):
        return "would unbalance marks", None
    if len(C.paragraphs(body)) != n_blocks:
        return "would change the block count", None
    return None, cand


def apply_fixes(cfg, raw, findings):
    """Apply the findings' fixes in order to `raw` (in memory). -> (text, applied, skipped)."""
    n_blocks = len(C.paragraphs(C.english_body(raw)))
    text, applied, skipped = raw, [], []
    for f in findings:
        fix = f["fix"]
        if not fix:
            skipped.append((f, "no concrete edit -- manual review"))
            continue
        why, cand = fix_problem(cfg, text, n_blocks, fix["old"], fix["new"])
        if why:
            skipped.append((f, why))
        else:
            text = cand
            applied.append((f, f"{fix['old']!r} -> {fix['new']!r}"))
    return text, applied, skipped


def normalize(obj):
    findings = []
    for d in obj.get("findings") or []:
        if not isinstance(d, dict):
            continue
        fix = d.get("fix")
        fix = ({"old": str(fix["old"]), "new": str(fix["new"])}
               if isinstance(fix, dict) and fix.get("old") and fix.get("new") is not None else None)
        findings.append({"locus": str(d.get("locus", "?")),
                         "severity": str(d.get("severity", "moderate")).lower(),
                         "category": str(d.get("category", "mistranslation")).lower(),
                         "source": str(d.get("source", d.get("latin", d.get("greek", "")))),
                         "ours": str(d.get("ours", "")), "issue": str(d.get("issue", "")),
                         "fix": fix})
    score = C.clamp_score(obj.get("score"))
    return {"score": score, "grade": str(obj.get("grade") or C.letter_for(score)),
            "fidelity": str(obj.get("fidelity", "")).lower(), "findings": findings,
            "summary": str(obj.get("summary", "")).strip()}


# --- Round subcommands ------------------------------------------------------------------


def bundle_sha(cfg, phase, n):
    p = C.bundle_path(cfg, phase, n)
    if not os.path.exists(p):
        return None
    m = re.search(r"^english_sha256: ([0-9a-f]{64})$", C.read(p), re.M)
    return m.group(1) if m else None


def record_bundled(cfg, phase, bundled, unbundled, key):
    """run/bundles/<phase>/units.json: which units this round bundled (merged across calls, so a
    `bundle --units <n>` on resume adds to the round instead of replacing it)."""
    p = os.path.join(C.run_dir(cfg), "bundles", phase, "units.json")
    data = C.read_json(p, {"bundled": [], key: []})
    touched = set(bundled) | set(unbundled)
    data["bundled"] = sorted((set(data.get("bundled", [])) - touched) | set(bundled))
    data[key] = sorted((set(data.get(key, [])) - touched) | set(unbundled))
    C.write_json(p, data)


def cmd_bundle(cfg, a):
    rules = C.setting(cfg, "VALIDATION_HOUSE_RULES").strip()
    lang = C.setting(cfg, "SOURCE_LANGUAGE")
    bundled, unvalidated = [], []
    for n in C.parse_units(cfg, a.units):
        src_file, eng_file = C.unit_files(cfg)[n]
        C.clean_scan_slate(cfg, a.phase, n, eng_file)
        bp = C.bundle_path(cfg, a.phase, n)
        rep = structure_report(cfg, n, src_file, eng_file)
        if rep["status"] != "ok":
            C.remove(bp)
            unvalidated.append(n)
            continue
        eng_raw = C.read(eng_file)
        notes = [issue_line(i) for i in rep["issues"] if i["level"] in ("ERROR", "WARN")]
        shared = ["## Work context", C.setting(cfg, "WORK_CONTEXT").strip() or "(none)",
                  "", "## House rules (never flag these)", rules or "(none)"]
        text = C.shared_bundle("Validate", shared, f"{C.unit_label(cfg, n)} (unit {n}), round {a.phase}", [
            f"work: {C.setting(cfg, 'AUTHOR')}, {C.setting(cfg, 'WORK')}",
            f"source_language: {lang}",
            f"english_file: {eng_file}",
            f"output: {C.findings_path(cfg, a.phase, eng_file)}",
            f"english_sha256: {C.sha256(eng_raw)}",
            "", "## Structure notes", "\n".join(f"- {x}" for x in notes) or "(none)",
            "", f"## {lang} source (the arbiter)", C.read(src_file).strip(),
            "", "## Our English translation (being validated)", C.english_body(eng_raw), ""])
        C.write(bp, text)
        bundled.append(n)
    record_bundled(cfg, a.phase, bundled, unvalidated, "unvalidated")
    print("bundled: " + ",".join(C.uid(cfg, n) for n in bundled))
    print("unvalidated: " + ",".join(C.uid(cfg, n) for n in unvalidated))


def load_findings(path):
    try:
        return C.read_json(path), None
    except json.JSONDecodeError as e:
        return None, f"not valid JSON: {e}"


def cmd_check_findings(cfg, a):
    n = C.resolve_unit(cfg, a.unit)
    _, eng_file = C.unit_files(cfg)[n]
    fp = C.findings_path(cfg, a.phase, eng_file)
    if not os.path.exists(fp):
        print(f"ERROR: no findings file {fp}")
        sys.exit(1)
    obj, err = load_findings(fp)
    probs = [err] if err else C.check_schema(obj, SCHEMA)
    raw = C.read(eng_file)
    want = bundle_sha(cfg, a.phase, n)
    if want and C.sha256(raw) != want:
        probs.append("the English file changed since the bundle was made: scanners never edit the "
                     "English (restore it with `git checkout`, or ask for a new bundle)")
    nfix = 0
    if not err and isinstance(obj, dict) and isinstance(obj.get("findings"), list):
        text = raw
        n_blocks = len(C.paragraphs(C.english_body(raw)))
        for i, d in enumerate(obj["findings"], 1):
            if not isinstance(d, dict) or "fix" not in d or d["fix"] is None:
                continue
            fix = d["fix"]
            if not (isinstance(fix, dict) and isinstance(fix.get("old"), str) and fix["old"]
                    and isinstance(fix.get("new"), str)):
                probs.append(f"findings[{i}].fix: needs a non-empty `old` and a string `new` "
                             f"(or drop the fix and keep the finding)")
                continue
            nfix += 1
            why, cand = fix_problem(cfg, text, n_blocks, fix["old"], fix["new"])
            if why:
                probs.append(f"findings[{i}].fix ({d.get('locus', '?')[:40]!r}): {why} -- repair the "
                             f"fix or drop it; keep the finding")
            else:
                text = cand
    for p in probs:
        print(f"ERROR {p}")
    if probs:
        sys.exit(1)
    print(f"OK: {len(obj['findings'])} finding(s), {nfix} fix(es), every fix applies cleanly")


def round_units(cfg, a, key="bundled"):
    if a.units:
        return C.parse_units(cfg, a.units)
    got = C.bundled_units(cfg, a.phase)
    if got is None:
        sys.exit(f"No units given and no bundle record for round {a.phase}.")
    return got


def apply_unit(cfg, phase, n):
    """-> (state, message). Journal states: pending (English not yet confirmed written), done."""
    _, eng_file = C.unit_files(cfg)[n]
    fp = C.findings_path(cfg, phase, eng_file)
    jp = fp[: -len(".json")] + ".apply.json"
    if not os.path.exists(fp):
        return "error", "no findings file (its scan didn't finish)"
    obj, err = load_findings(fp)
    if err:
        return "error", f"findings {err}"
    f_sha = C.sha256(C.read(fp))
    raw = C.read(eng_file)
    j = C.read_json(jp)
    if j is not None:
        if j.get("findings_sha256") != f_sha:
            return "error", "findings rewritten after apply: bundle this unit again and re-scan it"
        if j.get("state") == "done":
            return "done", "already applied"
        if C.sha256(raw) == j["english_after"]:
            j["state"] = "done"
            C.write_json(jp, j)
            return "done", "already applied (journal completed)"
        if C.sha256(raw) != j["english_before"]:
            return "error", "English matches neither side of a pending journal: check it by hand"
    else:
        want = bundle_sha(cfg, phase, n)
        if want is None or C.sha256(raw) != want:
            return "error", "REFUSED: the English changed after the scanner saw it: bundle again"
    r = normalize(obj)
    text, applied, skipped = apply_fixes(cfg, raw, r["findings"])
    if j is None:
        j = {"state": "pending", "findings_sha256": f_sha, "english_before": C.sha256(raw),
             "english_after": C.sha256(text),
             "applied": [{"locus": f["locus"], "category": f["category"], "old": f["fix"]["old"],
                          "new": f["fix"]["new"]} for f, _ in applied],
             "skipped": [{"locus": f["locus"], "severity": f["severity"], "category": f["category"],
                          "reason": why} for f, why in skipped],
             "at": C.now()}
        C.write_json(jp, j)
    if text != raw:
        C.write(eng_file, text)
    j["state"] = "done"
    C.write_json(jp, j)
    return "done", f"applied {len(j['applied'])}, skipped {len(j['skipped'])}"


def cmd_apply(cfg, a):
    bad = 0
    for n in round_units(cfg, a):
        state, msg = apply_unit(cfg, a.phase, n)
        bad += state != "done"
        print(f"  {C.uid(cfg, n)}: {msg}")
    print(f"apply {a.phase}: {'all units done' if not bad else f'{bad} unit(s) NOT done'}")
    sys.exit(1 if bad else 0)


def cmd_summary(cfg, a):
    rec = C.read_json(os.path.join(C.run_dir(cfg), "bundles", a.phase, "units.json"), {})
    units = C.parse_units(cfg, a.units) if a.units else sorted(set(rec.get("bundled", [])) |
                                                               set(rec.get("unvalidated", [])))
    rows = []
    for n in units:
        _, eng_file = C.unit_files(cfg)[n]
        name = os.path.basename(eng_file)
        fp = C.findings_path(cfg, a.phase, eng_file)
        if n in rec.get("unvalidated", []):
            rows.append((name, "unvalidated", None, ""))
            continue
        obj, err = load_findings(fp) if os.path.exists(fp) else (None, "missing")
        if obj is None:
            rows.append((name, "no findings" if err == "missing" else "unparseable", None, ""))
            continue
        g = normalize(obj)
        sig = sum(1 for d in g["findings"] if d["severity"] == "significant")
        e, w, _ = counts(structure_report(cfg, n))
        struct = f"  [struct: {e + w}]" if e + w else ""
        j = C.read_json(fp[: -len(".json")] + ".apply.json")
        fixed = f"  [fixed {len(j['applied'])}]" if j else ""
        rows.append((name, None, g, f"({len(g['findings'])} find, {sig} sig){struct}{fixed}"))
    print(f"Validation round {a.phase}: {len(units)} unit(s)")
    C.print_score_table("VALIDATION SUMMARY", rows, "Mean fidelity")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("cmd", nargs="?", help="bundle | check-findings | apply | summary | settle")
    ap.add_argument("unit", nargs="?")
    ap.add_argument("--structure-only", action="store_true")
    ap.add_argument("--summary", action="store_true", help="with --structure-only: ERROR lines and totals only")
    ap.add_argument("--units", help="comma list of unit numbers, u<NN> ids or batch ids")
    ap.add_argument("--unit", dest="unit_opt")
    ap.add_argument("--phase", help="round key, e.g. validate-r2")
    ap.add_argument("--check")
    ap.add_argument("--block", type=int)
    ap.add_argument("--by")
    ap.add_argument("--reason")
    a = ap.parse_args()
    if a.structure_only:
        gate.arm("validate")
    cfg = C.load_config(a.config)
    if a.structure_only:
        a.unit = a.unit or a.cmd  # `--structure-only <unit>`
        cmd_structure(cfg, a)
    if a.cmd == "settle":
        if not a.unit:
            sys.exit("usage: settle <unit> --check ... [--block n] --by ... --reason ...")
        cmd_settle(cfg, a)
        return
    if a.cmd not in ("bundle", "check-findings", "apply", "summary"):
        ap.error("give --structure-only or a subcommand: bundle, check-findings, apply, summary, settle")
    if not a.phase:
        sys.exit(f"{a.cmd} needs --phase <round key>.")
    if a.cmd == "check-findings":
        a.unit = a.unit_opt or a.unit
        if not a.unit:
            sys.exit("check-findings needs --unit <n>.")
    {"bundle": cmd_bundle, "check-findings": cmd_check_findings, "apply": cmd_apply,
     "summary": cmd_summary}[a.cmd](cfg, a)


if __name__ == "__main__":
    gate.guard(main)

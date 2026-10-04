#!/usr/bin/env python3
"""The per-pass gate: manifest + unit files + base_check.py, with flags taken from manifest.json.

Run by the orchestrator after every base-text phase (never by parallel subagents). Exit 0 = ALL
CLEAN. With --quiet only problems and the final verdict are printed, which keeps the
orchestrator's context small. The last line is `GATE check_base: PASS` or
`GATE check_base: FAIL (<n> problem(s))` (gate.py); `BASE CHECK: …` stays just above it.

    check_base.py --work-dir D [--quiet]
"""

import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gate  # noqa: E402

NESTED = dict(os.environ, TRANSLATE_WORK_NESTED_GATE="1")  # manifest_check prints no GATE line here


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    gate.arm("check_base")
    work = os.path.abspath(a.work_dir)

    m = subprocess.run([sys.executable, os.path.join(HERE, "manifest_check.py"), "--work-dir", work, "--files"],
                       capture_output=True, text=True, env=NESTED)
    out = m.stdout.strip().split("\n")
    print("\n".join(l for l in out if not a.quiet or l.startswith("  -") or "MANIFEST" in l))
    if m.returncode and m.stderr.strip():
        print(m.stderr.strip()[-500:])
    try:
        man = json.load(open(os.path.join(work, "_source", "run", "manifest.json"), encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        print("BASE CHECK: FAILED (manifest unreadable)")
        gate.finish(1)
    c = man.get("checks", {})
    args = [sys.executable, os.path.join(HERE, "base_check.py"), os.path.join(work, man["lang_dir"]),
            "--glob", f"*{man['file_suffix']}"]
    for p in c.get("pairs", ["»«"]):
        args += ["--pair"] + (list(p) if isinstance(p, list) else [p])
    for e in c.get("even", []):
        args += ["--even", e]
    if c.get("even_exempt"):
        args += ["--even-exempt", c["even_exempt"]]
    for f in c.get("forbid", []):
        args += ["--forbid", f]
    args += ["--anchor", man["anchor"]["regex"]]
    args += ["--section", c.get("section_regex") or "none"]
    for unit, start in (c.get("section_start_for") or {}).items():
        args += ["--section-start-for", f"{unit}={start}"]
    if c.get("body_start"):
        args += ["--body-start", c["body_start"]]
    if c.get("ending"):
        args += ["--ending", c["ending"]]
    b = subprocess.run(args, capture_output=True, text=True)
    lines = b.stdout.strip().split("\n")
    if a.quiet:
        keep = []
        for i, l in enumerate(lines):
            if "ERRORS" in l or l.startswith("      -") or i == len(lines) - 1:
                keep.append(l)
        lines = keep
    print("\n".join(lines))
    if b.stderr.strip():
        print(b.stderr.strip()[-500:])
    ok = b.returncode == 0 and m.returncode == 0
    print("BASE CHECK: ALL CLEAN" if ok else "BASE CHECK: FAILED")
    gate.finish(0 if ok else problem_count(m, b))


def problem_count(m, b):
    """Manifest errors + unit files with errors, as the two checks report them (at least 1)."""
    n = 0
    if m.returncode:
        hit = re.search(r"MANIFEST ERRORS: (\d+)", m.stdout)
        n += int(hit.group(1)) if hit else 1
    if b.returncode:
        hit = re.search(r"(\d+) file\(s\) with errors", b.stdout)
        n += int(hit.group(1)) if hit else 1
    return max(n, 1)


if __name__ == "__main__":
    gate.guard(main)

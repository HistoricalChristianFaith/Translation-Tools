#!/usr/bin/env python3
"""The normalize gate: the run's own normalize script finds nothing left to change, and the manifest
is sound.

The normalize agent writes `run/normalize/normalize.py` for this text (`03b_normalize.md`); its dry
run prints `changes: N`. This tool runs that dry run on the language folder, requires
`changes: 0`, then runs `manifest_check.py` (without --files: B hasn't completed the text yet), so
the gate needs no pipe and ends with one line: `GATE normalize_check: PASS` or
`GATE normalize_check: FAIL (<n> problem(s))` (gate.py).

    normalize_check.py --work-dir D
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

NESTED = dict(os.environ, TRANSLATE_WORK_NESTED_GATE="1")
MAX_LINES = 30


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work-dir", required=True)
    a = ap.parse_args()
    gate.arm("normalize_check")
    work = os.path.abspath(a.work_dir)
    run = os.path.join(work, "_source", "run")
    script = os.path.join(run, "normalize", "normalize.py")
    if not os.path.exists(script):
        sys.exit(f"no normalize script at {os.path.relpath(script, work)}")
    try:
        with open(os.path.join(run, "manifest.json"), encoding="utf-8") as f:
            lang = json.load(f)["lang_dir"]
    except (OSError, json.JSONDecodeError, KeyError) as e:
        sys.exit(f"manifest.json unreadable: {e}")

    problems = 0
    n = subprocess.run([sys.executable, script, os.path.join(work, lang)], capture_output=True, text=True)
    out = n.stdout.strip().split("\n") if n.stdout.strip() else []
    print("\n".join(out[:MAX_LINES] + ([f"… ({len(out) - MAX_LINES} more line(s))"] if len(out) > MAX_LINES else [])))
    hits = re.findall(r"(?m)^changes:\s*(\d+)\s*$", n.stdout)
    if n.returncode:
        print(f"normalize.py exited {n.returncode}: {n.stderr.strip()[-500:]}")
        problems += 1
    elif not hits:
        print("normalize.py printed no `changes: N` line")
        problems += 1
    elif int(hits[-1]):
        print(f"NORMALIZE: {hits[-1]} change(s) left (run it with --write, or fix the script)")
        problems += 1

    m = subprocess.run([sys.executable, os.path.join(HERE, "manifest_check.py"), "--work-dir", work],
                       capture_output=True, text=True, env=NESTED)
    print("\n".join(l for l in m.stdout.strip().split("\n") if l.startswith("  -") or "MANIFEST" in l))
    if m.returncode:
        if m.stderr.strip():
            print(m.stderr.strip()[-500:])
        hit = re.search(r"MANIFEST ERRORS: (\d+)", m.stdout)
        problems += int(hit.group(1)) if hit else 1
    gate.finish(problems)


if __name__ == "__main__":
    gate.guard(main)

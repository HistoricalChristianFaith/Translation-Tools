#!/usr/bin/env python3
"""Sync a unit's `incipit` or `explicit` in manifest.json with its unit file: the only way an agent
may change the manifest.

The two fields mirror the unit file, not the print (manifest_check.py): they follow the text, fixes
and emendations included. This tool can only bring the manifest in line with the text, never the
reverse: it refuses a value that the `manifest_check.py --files` check for that field would reject.

    manifest_edit.py --work-dir D --unit 93 --field explicit --value "allegoriæ sequitur præviantem." \\
                     --by convergence/p09 --reason "col 422 reads præviantem; unit file agrees"

Exit 0: written, or `unchanged` (the value is already the field's). Exit 1: refused (the value isn't
where the field must be in the unit file). Exit 2: a field other than incipit / explicit (use a
`[orchestrator]` Carry-forward item), or a bad argument. Exit 3: `manifest busy: retry`.

Every call holds an exclusive lock on run/manifest.lock (manifest_lock()) from re-reading the
manifest to replacing it, so parallel agents never lose each other's edits. Each edit is logged to
run/manifest_edits.jsonl: {"unit", "field", "old", "new", "by", "reason", "time"}. Any other writer
of manifest.json must take the same lock; readers don't need it (os.replace swaps the file whole).
"""

import argparse
import contextlib
import datetime
import fcntl
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import manifest_check as MC  # noqa: E402

LOCK_WAIT = 30  # seconds


class Busy(Exception):
    pass


@contextlib.contextmanager
def manifest_lock(run, wait=None):
    """Exclusive lock on run/manifest.lock for a read-modify-write of manifest.json (raises Busy
    after `wait` seconds, default LOCK_WAIT)."""
    fd = os.open(os.path.join(run, "manifest.lock"), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        deadline = time.monotonic() + (LOCK_WAIT if wait is None else wait)
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise Busy() from None
                time.sleep(0.05)
        try:
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def indent_of(path):
    """The indent manifest.json was written with (keeps diffs small), default 1."""
    with open(path, encoding="utf-8") as f:
        f.readline()
        m = re.match(r"^( +)\S", f.readline())
    return len(m.group(1)) if m else 1


def write_json(path, data):
    tmp = f"{path}.tmp{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent_of(path))
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--unit", required=True, type=int)
    ap.add_argument("--field", required=True)
    ap.add_argument("--value", required=True)
    ap.add_argument("--by", required=True, help="who: <PHASE>/<id>, e.g. R6/docket, or orchestrator")
    ap.add_argument("--reason", required=True, help="one line: what you checked")
    a = ap.parse_args()
    if a.field not in MC.TEXT_FIELDS:
        print(f"refused: only {' / '.join(MC.TEXT_FIELDS)} can be edited here; "
              f"for {a.field!r} use [orchestrator] carry-forward")
        sys.exit(2)
    value = a.value.strip()
    if not value:
        print("refused: empty value")
        sys.exit(2)
    work = os.path.abspath(a.work_dir)
    run = os.path.join(work, "_source", "run")
    mpath = os.path.join(run, "manifest.json")

    try:
        with manifest_lock(run):
            man = MC.load(mpath)
            unit = next((u for u in man.get("units", []) if u.get("n") == a.unit), None)
            if unit is None:
                print(f"refused: no unit {a.unit} in the manifest")
                sys.exit(2)
            old = unit.get(a.field)
            if old == value:
                print(f"unit {a.unit} {a.field}: unchanged")
                sys.exit(0)
            fp = os.path.join(work, man["lang_dir"], unit["file"])
            body = MC.read_body(fp) if os.path.exists(fp) else None
            if not body or len(body) < 2:
                print(f"refused: unit {a.unit} has no readable body ({man['lang_dir']}/{unit['file']})")
                sys.exit(1)
            prob = MC.field_problem(MC.normalize_fn(man), a.unit, a.field, value, body)
            if prob:
                print(f"refused: {prob}")
                sys.exit(1)
            unit[a.field] = value
            write_json(mpath, man)
            with open(os.path.join(run, "manifest_edits.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps({"unit": a.unit, "field": a.field, "old": old, "new": value, "by": a.by,
                                    "reason": a.reason,
                                    "time": datetime.datetime.now().isoformat(timespec="seconds")},
                                   ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
    except Busy:
        print("manifest busy: retry")
        sys.exit(3)
    print(f"unit {a.unit} {a.field}: {old!r} -> {value!r}")


if __name__ == "__main__":
    main()

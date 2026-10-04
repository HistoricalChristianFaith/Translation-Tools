#!/usr/bin/env python3
"""Make a test copy of a /translate-work run that can never read or write the original.

Testing in place is destructive: TARGET_DIR is always <WORK_DIR>/english, `prep --force`
replaces the English, and bundles, statuses and findings land in the run's own `run/`. A plain
`cp -R` isn't enough either: run/work_config.py and state.json hold the absolute WORK_DIR, so a
copied config would still read and write the original folder.

    scratch_copy.py --work-dir SRC --to DST [--english-from <snapshot label>]

Refuses if DST exists, or if either path is inside the other. Copies SRC to DST (on APFS with
`cp -cR`: clonefile, instant, no extra space for the page images; else shutil.copytree),
rewrites the absolute SRC path to DST in run/work_config.py and run/state.json, and sets
auto_commit=false in the copy. --english-from pre-validate replaces DST/english with
run/snapshots/pre-validate/ (the English exactly as validate round 1 saw it).

Then VERIFIES: loads the copy's config and checks that every absolute path it holds (SOURCE_DIR,
TARGET_DIR, IMAGE_DIR, PROJECT, ..., every image_paths(n)) lies under DST (the skill's own
tools directory excepted), and greps the copy's run/*.py and run/*.json for SRC. Any hit: exit 1.
Put DST outside any git repository (e.g. the session scratchpad).
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))


def inside(a, b):
    return os.path.commonpath([a, b]) == b


def src_re(src):
    # SRC as a whole path: followed by a separator, a quote, or the end -- never `<SRC>2/...`
    return re.compile(re.escape(src) + r"(?=[/\"']|$)", re.M)


def rewrite(path, src, dst):
    if not os.path.exists(path):
        return 0
    text = open(path, encoding="utf-8").read()
    new, k = src_re(src).subn(dst, text)
    if k:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new)
    return k


def copy_tree(src, dst):
    if sys.platform == "darwin":
        r = subprocess.run(["cp", "-cR", src, dst], capture_output=True, text=True)
        if r.returncode == 0:
            return "cp -cR (clonefile)"
        if os.path.exists(dst):
            shutil.rmtree(dst)
    shutil.copytree(src, dst, symlinks=True)
    return "copytree"


PROBE = r"""
import json, os, sys
sys.path.insert(0, sys.argv[1])
import common as C
cfg = C.load_config(sys.argv[2])
out = {}
for k in dir(cfg):
    v = getattr(cfg, k)
    if isinstance(v, str) and v.startswith("/"):
        out[k] = v
fn = getattr(cfg, "image_paths", None)
if fn:
    for n in sorted(C.unit_files(cfg)):
        for i, p in enumerate(fn(n)):
            out[f"image_paths({n})[{i}]"] = p
print(json.dumps(out))
"""


def verify(src, dst):
    run = os.path.join(dst, "_source", "run")
    problems = []
    cfgp = os.path.join(run, "work_config.py")
    if os.path.exists(cfgp):
        r = subprocess.run([sys.executable, "-c", PROBE, TOOLS_DIR, cfgp], capture_output=True, text=True)
        if r.returncode:
            problems.append(f"config does not load: {r.stderr.strip()[-300:]}")
        else:
            for k, v in json.loads(r.stdout.strip().splitlines()[-1]).items():
                v = os.path.abspath(v)
                if not inside(v, dst) and not inside(v, TOOLS_DIR):
                    problems.append(f"config {k} = {v} lies outside the copy")
    rx = src_re(src)
    for name in sorted(os.listdir(run)):
        if name.endswith((".py", ".json")):
            p = os.path.join(run, name)
            if rx.search(open(p, encoding="utf-8", errors="replace").read()):
                problems.append(f"run/{name} still names {src}")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--to", required=True)
    ap.add_argument("--english-from")
    a = ap.parse_args()
    src, dst = os.path.realpath(a.work_dir), os.path.realpath(a.to)
    if not os.path.isdir(os.path.join(src, "_source", "run")):
        sys.exit(f"not a /translate-work run: {src}")
    if os.path.exists(dst):
        sys.exit(f"refused: {dst} exists")
    if inside(dst, src) or inside(src, dst):
        sys.exit("refused: one path is inside the other")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    how = copy_tree(src, dst)
    run = os.path.join(dst, "_source", "run")
    shutil.rmtree(os.path.join(run, "__pycache__"), ignore_errors=True)
    k = rewrite(os.path.join(run, "work_config.py"), src, dst) + rewrite(os.path.join(run, "state.json"), src, dst)
    sp = os.path.join(run, "state.json")
    st = json.load(open(sp, encoding="utf-8"))
    st["auto_commit"] = False
    with open(sp, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=2, ensure_ascii=False)
    if a.english_from:
        snap = os.path.join(run, "snapshots", a.english_from)
        if not os.path.isdir(snap):
            sys.exit(f"no snapshot {a.english_from!r} in the copy (left at {dst})")
        shutil.rmtree(os.path.join(dst, "english"), ignore_errors=True)
        shutil.copytree(snap, os.path.join(dst, "english"))
    print(f"copied {src} -> {dst} ({how}); {k} path reference(s) rewritten; auto_commit=false"
          + (f"; english from snapshots/{a.english_from}" if a.english_from else ""))
    problems = verify(src, dst)
    for p in problems:
        print(f"  LEAK: {p}")
    if problems:
        sys.exit(1)
    print("verified: the copy's config and run files point only inside the copy")


if __name__ == "__main__":
    main()

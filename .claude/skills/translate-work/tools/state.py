#!/usr/bin/env python3
"""Run state for a /translate-work project: `<work>/_source/run/state.json`.

The orchestrator keeps its own context lean by reading ONLY this file (and tool exit codes /
status summaries) to know where a multi-day run stands. Every phase is idempotent; `next`
tells a resumed session where to pick up.

    state.py init     --work-dir D --work "Origen, Homilies on Leviticus" [--set key=value ...]
                      # new runs get checklists_from=B (older runs lack it: checklists optional)
    state.py show     --work-dir D                   # compact summary
    state.py next     --work-dir D                   # first phase not done/skipped
                      # a phase added to the skill after a run was initialized counts as skipped
                      # ("added to the skill after this run passed it") if the run has already
                      # reached a later phase, else pending (saved on the next write)
    state.py phase    --work-dir D R2 in_progress|done|skipped|failed [--note "..."]
    state.py get      --work-dir D key.sub           # print a value (JSON)
    state.py set      --work-dir D key.sub=value     # value parsed as JSON when possible
    state.py agents   --work-dir D --add N           # count dispatched agents
    state.py snapshot --work-dir D LABEL [--dir english] [--keep]
                      # copy a text tree to run/snapshots/LABEL (replacing it; with --keep an
                      # existing snapshot is kept: review rounds, so a re-run never moves the
                      # baseline past fixes the reviewers haven't seen)
    state.py changed  --work-dir D --since LABEL [--dir english]
                      # packet ids (from packets.json) whose unit files differ from snapshot LABEL
"""

import argparse
import datetime
import json
import os
import re
import shutil
import sys

PHASES = ["survey", "stage", "structure", "normalize", "B", "R2", "R4", "R1", "R3", "R5", "R6",
          "R8", "convergence", "R7", "configure", "translate", "validate", "grade", "report"]
# The model every subagent and the orchestrator run on (SPEC §8.4). Compared without a context
# suffix: `claude-opus-5-5[1m]` (the orchestrator, 1M context) matches.
PINNED_MODEL = "claude-opus-5-5"
REACHED = ("in_progress", "done", "failed")  # a phase with one of these was actually run
RUN_SUBDIRS = ["status", "notes", "snapshots", "logs", "crops"]


def model_matches(model, pinned=PINNED_MODEL):
    base = lambda m: re.sub(r"\[[^\]]*\]$", "", str(m or "").strip())
    return base(model) == base(pinned)


def run_dir(work):
    return os.path.join(work, "_source", "run")


def path(work):
    return os.path.join(run_dir(work), "state.json")


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def load(work):
    p = path(work)
    if not os.path.exists(p):
        sys.exit(f"No state at {p} (run `state.py init` first).")
    with open(p, encoding="utf-8") as f:
        return reconcile(json.load(f))


def reconcile(st):
    """Older runs lack phases added to the skill since (e.g. normalize, R8). A missing phase that
    the run has already passed (a later phase was reached) is skipped; otherwise it is pending."""
    ph = st.setdefault("phases", {})
    for i, p in enumerate(PHASES):
        if p in ph:
            continue
        if any(ph.get(q, {}).get("status") in REACHED for q in PHASES[i + 1:]):
            ph[p] = {"status": "skipped", "note": "added to the skill after this run passed it"}
        else:
            ph[p] = {"status": "pending"}
    return st


def save(work, st):
    st["last_update"] = now()
    tmp = path(work) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path(work))


def parse_value(v):
    try:
        return json.loads(v)
    except (json.JSONDecodeError, ValueError):
        return v


def dig(st, key, create=False):
    parts = key.split(".")
    cur = st
    for p in parts[:-1]:
        if p not in cur:
            if not create:
                return None, None
            cur[p] = {}
        cur = cur[p]
    return cur, parts[-1]


def next_phase(st):
    for p in PHASES:
        if st["phases"].get(p, {}).get("status") not in ("done", "skipped"):
            return p
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["init", "show", "next", "phase", "get", "set", "agents", "snapshot", "changed"])
    ap.add_argument("--since")
    ap.add_argument("args", nargs="*")
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--work")
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--note")
    ap.add_argument("--add", type=int)
    ap.add_argument("--dir")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    work = os.path.abspath(a.work_dir)

    if a.cmd == "init":
        if os.path.exists(path(work)) and not a.force:
            sys.exit(f"State already exists at {path(work)} -- resume instead (or --force).")
        for d in RUN_SUBDIRS:
            os.makedirs(os.path.join(run_dir(work), d), exist_ok=True)
        st = {"work": a.work or os.path.basename(work), "work_dir": work, "created": now(),
              "autonomy": "checkpoints", "agents_dispatched": 0,
              "checklists_from": "B",  # status_check requires checklists from this phase on
              "phases": {p: {"status": "pending"} for p in PHASES}}
        for kv in a.set:
            k, v = kv.split("=", 1)
            holder, leaf = dig(st, k, create=True)
            holder[leaf] = parse_value(v)
        save(work, st)
        print(f"Initialized {path(work)}")
        return

    st = load(work)
    if a.cmd == "show":
        done = [p for p in PHASES if st["phases"][p]["status"] in ("done", "skipped")]
        cur = next_phase(st)
        print(f"work: {st['work']}  |  dir: {st['work_dir']}")
        print(f"language: {st.get('language', '?')}  base: {st.get('base', '?')}  oracle: "
              f"{st.get('oracle') or 'none'}  autonomy: {st.get('autonomy')}")
        print("phases: " + " ".join(f"{p}[{st['phases'][p]['status'][0].upper()}]" for p in PHASES))
        print(f"done {len(done)}/{len(PHASES)}; next: {cur or '— (complete)'}; agents dispatched: "
              f"{st.get('agents_dispatched', 0)}")
    elif a.cmd == "next":
        print(next_phase(st) or "")
    elif a.cmd == "phase":
        if len(a.args) != 2 or a.args[0] not in PHASES:
            sys.exit(f"usage: phase NAME STATUS  (NAME in {PHASES})")
        name, status = a.args
        entry = st["phases"][name]
        entry["status"] = status
        entry[f"{status}_at"] = now()
        if a.note:
            entry["note"] = a.note
        save(work, st)
        print(f"{name} -> {status}")
    elif a.cmd == "get":
        holder, leaf = dig(st, a.args[0])
        print(json.dumps(holder.get(leaf) if holder else None, ensure_ascii=False))
    elif a.cmd == "set":
        for kv in a.args:
            k, v = kv.split("=", 1)
            holder, leaf = dig(st, k, create=True)
            holder[leaf] = parse_value(v)
        save(work, st)
        print("ok")
    elif a.cmd == "agents":
        st["agents_dispatched"] = st.get("agents_dispatched", 0) + (a.add or 0)
        save(work, st)
        print(f"agents dispatched: {st['agents_dispatched']}")
    elif a.cmd == "snapshot":
        label = a.args[0]
        src_name = a.dir or st.get("lang_dir")
        if not src_name:
            sys.exit("snapshot: --dir not given and state has no lang_dir")
        src = os.path.join(work, src_name)
        dst = os.path.join(run_dir(work), "snapshots", label)
        if a.keep and os.path.exists(dst):
            print(f"snapshot run/snapshots/{label} kept (taken earlier)")
            return
        tmp = dst + ".tmp"
        if os.path.exists(tmp):
            shutil.rmtree(tmp)
        shutil.copytree(src, tmp)  # copy first, swap after: a crash never leaves half a snapshot
        if os.path.exists(dst):
            shutil.rmtree(dst)
        os.replace(tmp, dst)
        print(f"snapshot {src_name} -> run/snapshots/{label}")
    elif a.cmd == "changed":
        src_name = a.dir or st.get("lang_dir")
        snap = os.path.join(run_dir(work), "snapshots", a.since or "")
        if not a.since or not os.path.isdir(snap):
            sys.exit(f"changed: snapshot {a.since!r} not found")
        with open(os.path.join(run_dir(work), "packets.json"), encoding="utf-8") as f:
            packets = json.load(f)["packets"]
        with open(os.path.join(run_dir(work), "manifest.json"), encoding="utf-8") as f:
            man = json.load(f)
        files = {u["n"]: u["file"] for u in man["units"]}
        if src_name == "english":
            files = {n: re.sub(r"_[a-z]+\.txt$", "_english.txt", fn) for n, fn in files.items()}

        def differs(fn):
            p1, p2 = os.path.join(work, src_name, fn), os.path.join(snap, fn)
            if not (os.path.exists(p1) and os.path.exists(p2)):
                return os.path.exists(p1) != os.path.exists(p2)
            with open(p1, "rb") as x, open(p2, "rb") as y:
                return x.read() != y.read()

        hit = [p["id"] for p in packets if any(differs(files[n]) for n in p["units"] if n in files)]
        print(",".join(hit) if hit else "(none)")


if __name__ == "__main__":
    main()

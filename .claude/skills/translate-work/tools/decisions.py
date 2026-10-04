#!/usr/bin/env python3
"""Editorial decision queue: `<work>/_source/run/decisions.jsonl` (append-only).

Subagents cannot ask the user questions. When one meets a genuine editorial choice it ADDS a
decision (with a recommended option), proceeds on the recommendation, and records it in its
notes. At phase boundaries the orchestrator LISTs open decisions (≤4 at a time), asks the user
with AskUserQuestion, and RESOLVEs them -- or, in autonomous mode, resolves them all to the
recommendation. Later agents read the resolved list.

    decisions.py add --work-dir D --phase R5 --packet corpus \
        --question "Normalize consonantal J to I?" \
        --option "Normalize::Uniform I throughout (Leviticus precedent)" \
        --option "Keep as printed::Keep the edition's J/j" \
        --recommended "Normalize" --evidence "GCS prints both; 14 occurrences" [--affects "all units"]
    decisions.py list --work-dir D --open [--limit 4] [--json]
    decisions.py list --work-dir D --resolved
    decisions.py resolve --work-dir D --id R5-corpus-1 --choice "Normalize" [--note "..."]
    decisions.py resolve-recommended --work-dir D        # autonomous mode: accept all recommendations
    decisions.py count --work-dir D                     # "open=N resolved=M"
"""

import argparse
import datetime
import json
import os
import sys


def dfile(work):
    return os.path.join(os.path.abspath(work), "_source", "run", "decisions.jsonl")


def load(work):
    items, order = {}, []
    p = dfile(work)
    if not os.path.exists(p):
        return items, order
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("type") == "resolution":
                if rec["id"] in items:
                    items[rec["id"]].update(status="resolved", choice=rec["choice"],
                                            resolved_by=rec.get("by"), note=rec.get("note"))
            else:
                items[rec["id"]] = dict(rec, status="open")
                order.append(rec["id"])
    return items, order


def append(work, rec):
    os.makedirs(os.path.dirname(dfile(work)), exist_ok=True)
    with open(dfile(work), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["add", "list", "resolve", "resolve-recommended", "count"])
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--phase")
    ap.add_argument("--packet")
    ap.add_argument("--question")
    ap.add_argument("--option", action="append", default=[])
    ap.add_argument("--recommended")
    ap.add_argument("--evidence", default="")
    ap.add_argument("--affects", default="")
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--resolved", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--id")
    ap.add_argument("--choice")
    ap.add_argument("--note")
    a = ap.parse_args()
    items, order = load(a.work_dir)

    if a.cmd == "add":
        if not (a.phase and a.packet and a.question and a.recommended) or not 2 <= len(a.option) <= 4:
            sys.exit("add needs --phase --packet --question --recommended and 2-4 --option 'label::description'")
        opts = []
        for o in a.option:
            label, _, desc = o.partition("::")
            opts.append({"label": label.strip(), "description": desc.strip()})
        if a.recommended not in [o["label"] for o in opts]:
            sys.exit("--recommended must equal one option label")
        k = 1 + sum(1 for i in order if i.startswith(f"{a.phase}-{a.packet}-"))
        rid = f"{a.phase}-{a.packet}-{k}"
        append(a.work_dir, {"id": rid, "phase": a.phase, "packet": a.packet, "question": a.question,
                            "options": opts, "recommended": a.recommended, "evidence": a.evidence,
                            "affects": a.affects,
                            "created": datetime.datetime.now().isoformat(timespec="seconds")})
        print(rid)
    elif a.cmd == "list":
        sel = [items[i] for i in order if (not a.open or items[i]["status"] == "open")
               and (not a.resolved or items[i]["status"] == "resolved")]
        if a.limit:
            sel = sel[: a.limit]
        if a.json:
            print(json.dumps(sel, ensure_ascii=False, indent=1))
            return
        for d in sel:
            if d["status"] == "open":
                opts = " | ".join(o["label"] + (" (rec.)" if o["label"] == d["recommended"] else "")
                                  for o in d["options"])
                print(f"[{d['id']}] {d['question']}  ->  {opts}")
            else:
                print(f"[{d['id']}] {d['question']}  =>  {d['choice']}"
                      + (f"  ({d['note']})" if d.get("note") else ""))
        if not sel:
            print("(none)")
    elif a.cmd == "resolve":
        if a.id not in items:
            sys.exit(f"unknown decision id {a.id}")
        append(a.work_dir, {"type": "resolution", "id": a.id, "choice": a.choice, "by": "user", "note": a.note})
        print(f"{a.id} => {a.choice}")
    elif a.cmd == "resolve-recommended":
        n = 0
        for i in order:
            if items[i]["status"] == "open":
                append(a.work_dir, {"type": "resolution", "id": i, "choice": items[i]["recommended"],
                                    "by": "auto-recommended"})
                n += 1
        print(f"resolved {n} open decision(s) to their recommendation")
    elif a.cmd == "count":
        op = sum(1 for i in order if items[i]["status"] == "open")
        print(f"open={op} resolved={len(order) - op}")


if __name__ == "__main__":
    main()

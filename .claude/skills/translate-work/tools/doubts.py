#!/usr/bin/env python3
"""Doubt ledger: `<work>/_source/run/doubts.jsonl` (append-only; a missing file = empty ledger).

Every doubtful reading an agent leaves unchanged is ADDed here (not only written in notes), so
its fate is trackable. Later phases get the open doubts on their pages in their checklist and
UPDATE each one. Lifecycle:
    open -> confirmed-as-printed | changed | escalated (to a decision; give --decision) | deferred
(any status may be updated again by a later phase; the history is kept).

    doubts.py add    --work-dir D --phase R2 --packet p07a --unit 7 --page 175 \
                     --reading "few words as printed" --question "what is doubtful"   # prints id
    doubts.py update --work-dir D --id R2-p07a-1 --status confirmed-as-printed \
                     --phase R3 --by p07 --reason "image clear: accent as printed" [--decision R5-corpus-2]
    doubts.py list   --work-dir D [--status open] [--unit 7] [--pages 173-186|173,174] [--phase R2]
                     [--packet p07a] [--json] [--limit N]
    doubts.py count  --work-dir D [--group status|unit|phase] [--phase R2 --packet p07a]
                     # default: "open=N confirmed-as-printed=N changed=N escalated=N deferred=N total=N"
                     # with --phase (and --packet): "added=N" by that phase (packet) first
"""

import argparse
import datetime
import json
import os
import sys

STATUSES = ["open", "confirmed-as-printed", "changed", "escalated", "deferred"]


def dfile(work):
    return os.path.join(os.path.abspath(work), "_source", "run", "doubts.jsonl")


def load(work):
    """-> (items by id, ids in order). Each item: the add record + status + history."""
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
            if rec.get("type") == "update":
                if rec.get("id") in items:
                    it = items[rec["id"]]
                    it["status"] = rec["status"]
                    it["history"].append(rec)
            elif rec.get("id"):
                items[rec["id"]] = dict(rec, status="open", history=[])
                order.append(rec["id"])
    return items, order


def append(work, rec):
    os.makedirs(os.path.dirname(dfile(work)), exist_ok=True)
    with open(dfile(work), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def expand_pages(spec):
    """'173-186' or '173,174' -> set of labels (numeric ranges only)."""
    out = set()
    for part in (spec or "").split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            if lo.isdigit() and hi.isdigit():
                out |= {str(i) for i in range(int(lo), int(hi) + 1)}
                continue
        if part:
            out.add(part)
    return out


def select(items, order, status=None, unit=None, pages=None, phase=None, packet=None):
    sel = []
    for i in order:
        d = items[i]
        if status and d["status"] != status:
            continue
        if unit is not None and str(d.get("unit")) != str(unit):
            continue
        if pages is not None and str(d.get("page", "")) not in pages:
            continue
        if phase and d.get("phase") != phase:
            continue
        if packet and d.get("packet") != packet:
            continue
        sel.append(d)
    return sel


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["add", "update", "list", "count"])
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--phase")
    ap.add_argument("--packet")
    ap.add_argument("--unit")
    ap.add_argument("--page")
    ap.add_argument("--pages")
    ap.add_argument("--reading", default="")
    ap.add_argument("--question")
    ap.add_argument("--id")
    ap.add_argument("--status", choices=STATUSES)
    ap.add_argument("--by", default="", help="update: the packet/role making the update")
    ap.add_argument("--reason")
    ap.add_argument("--decision")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--group", dest="by_field", choices=["status", "unit", "phase"])
    a = ap.parse_args()
    items, order = load(a.work_dir)

    if a.cmd == "add":
        if not (a.phase and a.packet and a.unit is not None and a.question):
            sys.exit("add needs --phase --packet --unit --question (and --page, --reading if known)")
        k = 1 + sum(1 for i in order if i.startswith(f"{a.phase}-{a.packet}-"))
        rid = f"{a.phase}-{a.packet}-{k}"
        unit = int(a.unit) if str(a.unit).isdigit() else a.unit
        append(a.work_dir, {"id": rid, "phase": a.phase, "packet": a.packet, "unit": unit,
                            "page": a.page or "", "reading": a.reading[:80], "question": a.question[:300],
                            "created": now()})
        print(rid)
    elif a.cmd == "update":
        if not (a.id and a.status and a.phase and a.reason):
            sys.exit("update needs --id --status --phase --reason (and --by <packet/role>)")
        if a.id not in items:
            sys.exit(f"unknown doubt id {a.id}")
        if a.status == "escalated" and not a.decision:
            sys.exit("status escalated needs --decision <decision id from decisions.py add>")
        append(a.work_dir, {"type": "update", "id": a.id, "status": a.status, "phase": a.phase,
                            "by": a.by, "reason": a.reason[:200], "decision": a.decision, "at": now()})
        print(f"{a.id} -> {a.status}")
    elif a.cmd == "list":
        sel = select(items, order, a.status, a.unit, expand_pages(a.pages) if a.pages else None,
                     a.phase, a.packet)
        if a.limit:
            sel = sel[: a.limit]
        if a.json:
            print(json.dumps(sel, ensure_ascii=False, indent=1))
            return
        for d in sel:
            last = d["history"][-1] if d["history"] else None
            tail = f"  => {d['status']} ({last['phase']}: {last['reason']})" if last else "  [open]"
            print(f"[{d['id']}] u{d.get('unit')} p.{d.get('page') or '?'} `{d.get('reading', '')}`: "
                  f"{d['question']}{tail}")
        if not sel:
            print("(none)")
    elif a.cmd == "count":
        pre = ""
        if a.phase:
            pre = f"added={len(select(items, order, phase=a.phase, packet=a.packet))} "
        if a.by_field:
            c = {}
            for i in order:
                key = items[i].get(a.by_field) if a.by_field != "status" else items[i]["status"]
                c.setdefault(f"{a.by_field}={key}", {}).setdefault(items[i]["status"], 0)
                c[f"{a.by_field}={key}"][items[i]["status"]] += 1
            print(pre + "; ".join(f"{k}: " + " ".join(f"{s}={n}" for s, n in v.items()) for k, v in c.items())
                  if c else pre + "(empty ledger)")
            return
        c = {s: 0 for s in STATUSES}
        for i in order:
            c[items[i]["status"]] = c.get(items[i]["status"], 0) + 1
        print(pre + " ".join(f"{s}={n}" for s, n in c.items()) + f" total={len(order)}")


if __name__ == "__main__":
    main()

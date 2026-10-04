#!/usr/bin/env python3
"""Completeness checklists: `<work>/_source/run/checklists/<PHASE>/<id>.json`.

Enumerate every item up front, mark each one off as it is
done, and refuse completion while any item is unmarked. The orchestrator INITs the checklists
before dispatching a phase; the agent MARKs each item (one command per item) with a short
result; status_check.py fails (REDISPATCH) a `done` packet whose checklist is missing,
incomplete, or covers different pages than the packet/sub-packet now has.

Items:  pages "173" (default), units "u7" (--by unit), doubts "d:<doubt id>" (--doubts: the
ledger's open doubts on those pages/units; --all-open-doubts for a role over the whole work;
--include-deferred adds deferred doubts too, for R8).
A doubt item also counts as checked when doubts.py records an update to it by this phase.

    checklist.py init   --work-dir D --phase R2 [--ids p07a,p09] [--whole] [--by page|unit] [--doubts]
    checklist.py init   --work-dir D --phase R6 --role docket --all-open-doubts
    checklist.py init   --work-dir D --phase R5 --role corpus --by unit
    checklist.py init   --work-dir D --phase R8 --whole --by none --doubts --include-deferred
                        # prints "nonempty: <ids>": dispatch only those
    checklist.py show   --work-dir D --phase R2 --id p07a [--all]     # unchecked (or all) items
    checklist.py mark   --work-dir D --phase R2 --id p07a --item 175 --result "ok, 1 fix"
    checklist.py verify --work-dir D --phase R2 --id p07a             # exit 0 = COMPLETE
init overwrites (a re-dispatched agent starts a fresh checklist).
"""

import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doubts as D  # noqa: E402
import packets as P  # noqa: E402


def cpath(run, phase, cid):
    return os.path.join(run, "checklists", phase, f"{cid}.json")


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def save(fp, data):
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    tmp = fp + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    os.replace(tmp, fp)


def load(fp):
    with open(fp, encoding="utf-8") as f:
        return json.load(f)


def build(work, phase, e, by, with_doubts, all_doubts=False, first_sub_units=(), statuses=("open",)):
    items = []
    if by == "page":
        items += [{"item": pg, "kind": "page"} for pg in e["pages"]]
    elif by == "unit":
        items += [{"item": f"u{n}", "kind": "unit"} for n in e["units"]]
    if with_doubts or all_doubts:
        ditems, order = D.load(work)
        pages, units = set(e["pages"]), {str(n) for n in e["units"]}
        for i in order:
            d = ditems[i]
            if d["status"] not in statuses:
                continue
            pg, un = str(d.get("page") or ""), str(d.get("unit"))
            if all_doubts or (pg and pg in pages) or (not pg and un in units and un in first_sub_units):
                items.append({"item": f"d:{i}", "kind": "doubt", "unit": d.get("unit"), "page": pg})
    return {"phase": phase, "id": e["id"], "parent": e.get("parent"), "by": by,
            "units": e["units"], "pages": e["pages"], "created": now(), "items": items}


def doubt_touched(work, phase):
    """Doubt ids updated by this phase in the ledger."""
    items, order = D.load(work)
    return {i for i in order if any(h.get("phase") == phase for h in items[i]["history"])}


def verify(work, run, phase, cid, expect_pages=None):
    """-> (ok, message). Missing checklist = not ok (unknown coverage)."""
    fp = cpath(run, phase, cid)
    if not os.path.exists(fp):
        return False, "MISSING checklist (unknown coverage)"
    try:
        cl = load(fp)
    except (OSError, json.JSONDecodeError) as e:
        return False, f"MALFORMED checklist ({e.__class__.__name__})"
    if expect_pages is not None and cl.get("by") == "page" and list(cl.get("pages", [])) != list(expect_pages):
        return False, (f"checklist covers pages {P.page_range(cl.get('pages', []))}, "
                       f"packet now has {P.page_range(expect_pages)} (stale: re-init and re-dispatch)")
    touched = doubt_touched(work, phase) if any(i["kind"] == "doubt" for i in cl["items"]) else set()
    left = [i["item"] for i in cl["items"]
            if not i.get("done") and not (i["kind"] == "doubt" and i["item"][2:] in touched)]
    if left:
        shown = ",".join(left[:8]) + (f",… (+{len(left) - 8})" if len(left) > 8 else "")
        return False, f"{len(left)}/{len(cl['items'])} checklist items unchecked: {shown}"
    return True, f"COMPLETE ({len(cl['items'])} items)"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["init", "show", "mark", "verify"])
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--phase", required=True)
    ap.add_argument("--ids", help="init: comma list of packet/sub ids (a split packet expands to its subs)")
    ap.add_argument("--whole", action="store_true", help="init: ignore sub-packets")
    ap.add_argument("--by", choices=["page", "unit", "none"], default="page")
    ap.add_argument("--doubts", action="store_true", help="init: add the open ledger doubts on the pages")
    ap.add_argument("--role", help="init: a single-agent role (items span the whole work)")
    ap.add_argument("--all-open-doubts", action="store_true")
    ap.add_argument("--include-deferred", action="store_true", help="init: deferred doubts count as open")
    ap.add_argument("--id")
    ap.add_argument("--item")
    ap.add_argument("--result")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    work = os.path.abspath(a.work_dir)
    run = P.run_dir(work)
    sts = ("open", "deferred") if a.include_deferred else ("open",)

    if a.cmd == "init":
        if a.role:
            up = P.unit_pages(run)
            allpages = []
            for n in sorted(up):
                allpages += [pg for pg in up[n] if pg not in allpages]
            e = {"id": a.role, "parent": None, "units": sorted(up), "pages": allpages}
            cl = build(work, a.phase, e, a.by, a.doubts, a.all_open_doubts, statuses=sts)
            save(cpath(run, a.phase, a.role), cl)
            print(f"{a.phase}/{a.role}: {len(cl['items'])} items")
            return
        es = P.expand(run, a.ids.split(","), a.whole) if a.ids else P.entries(run, a.whole)
        owner = {}  # a doubt with a unit but no page goes to the first dispatch entry holding that unit
        for x in P.entries(run, a.whole):
            for n in x["units"]:
                owner.setdefault(str(n), (x["id"], x["parent"]))
        total, nonempty = 0, []
        for e in es:
            first = {str(n) for n in e["units"] if e["id"] in owner.get(str(n), ())}
            cl = build(work, a.phase, e, a.by, a.doubts, first_sub_units=first, statuses=sts)
            save(cpath(run, a.phase, e["id"]), cl)
            total += len(cl["items"])
            if cl["items"]:
                nonempty.append(e["id"])
        print(f"{a.phase}: {len(es)} checklist(s), {total} items")
        print("nonempty: " + (",".join(nonempty) or "(none)"))
        return

    if not a.id:
        sys.exit("--id is required")
    fp = cpath(run, a.phase, a.id)
    if a.cmd == "verify":
        ok, msg = verify(work, run, a.phase, a.id)
        print(f"{a.phase}/{a.id}: {msg}")
        sys.exit(0 if ok else 1)
    if not os.path.exists(fp):
        sys.exit(f"no checklist {os.path.relpath(fp, run)} -- the orchestrator must run `checklist.py init`")
    cl = load(fp)
    if a.cmd == "show":
        touched = doubt_touched(work, a.phase)
        n_left = 0
        for i in cl["items"]:
            done = i.get("done") or (i["kind"] == "doubt" and i["item"][2:] in touched)
            n_left += not done
            if a.all or not done:
                extra = f" (u{i.get('unit')} p.{i.get('page') or '?'})" if i["kind"] == "doubt" else ""
                print(f"[{'x' if done else ' '}] {i['item']}{extra}" + (f"  {i.get('result', '')}" if done else ""))
        print(f"{n_left} of {len(cl['items'])} unchecked")
    elif a.cmd == "mark":
        if not (a.item and a.result and a.result.strip()):
            sys.exit("mark needs --item and a non-empty --result")
        hit = [i for i in cl["items"] if i["item"] == a.item]
        if not hit:
            sys.exit(f"item {a.item!r} is not on checklist {a.phase}/{a.id} "
                     f"(pages {P.page_range(cl.get('pages', []))})")
        hit[0].update(done=True, result=a.result.strip()[:120], at=now())
        save(fp, cl)
        left = sum(1 for i in cl["items"] if not i.get("done"))
        print(f"{a.item} checked; {left} left")


if __name__ == "__main__":
    main()

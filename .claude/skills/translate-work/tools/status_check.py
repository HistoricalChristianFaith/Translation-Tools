#!/usr/bin/env python3
"""Check that every subagent of a phase left a valid status file ("a failed agent is
unknown coverage", made mechanical).

Per-packet phases:  run/status/<PHASE>/<packet-id>.json for every packet in run/packets.json
Single-agent phases: run/status/<PHASE>/<name>.json for each --expect name
Both (R4: packets, then the `seams` role): --with-packets --expect seams checks every packet (as
  with no --expect) and each --expect name. Without --with-packets, --expect checks only the roles.
Per-unit phases (--by-unit: translate, <K>-scan): run/status/<PHASE>/u<NN>.json for every
  manifest unit (or --units). A `done` status also needs its artifact, newer than the unit's
  bundle: the English file (translate) or run/findings/<K>/<stem>.json (<K>-scan). A `skipped`
  translate status needs the English file. --by-unit never requires or verifies a checklist.

Status JSON (see phases/shared/status_contract.md):
  {"phase": "R2", "packet": "p03", "units": [5], "status": "done", "fixes": 4,
   "doubts": 1, "decisions": 0, "notes": "run/notes/R2/p03.md"}
status ∈ done | skipped | failed | filter_blocked

    status_check.py --work-dir D --phase R2                 # all packets
    status_check.py --work-dir D --phase R2 --packets p01,p04
    status_check.py --work-dir D --phase R5 --expect corpus
    status_check.py --work-dir D --phase R4 --with-packets --expect seams
    status_check.py --work-dir D --phase convergence --packets p02,p07 --sum substantive --nonzero substantive
    status_check.py --work-dir D --phase translate --by-unit [--units 3,8]
    status_check.py --work-dir D --phase validate-r2-scan --by-unit --units u03,u08
Prints one summary line (+ one line per problem) and `REDISPATCH: id,id` if any are missing or
failed, then `GATE status_check: PASS` or `GATE status_check: FAIL (<n> problem(s))` (gate.py).
Exit 0 only if every expected status is done/skipped. --units also takes batch ids (u12-u17,
packets.py batches); REDISPATCH always lists single unit ids.

Sub-packets (packets.py): a packet with `subs` is complete only when every sub-packet status is
done/skipped; their counts are summed; REDISPATCH lists the sub ids. --packets accepts packet or
sub ids. A whole-packet status newer than its subs' (or with no sub status) still counts, so
runs dispatched before a split keep passing. `--whole` ignores subs (validate, grade).
Convergence with no --packets checks state.json `convergence_packets`, if set.

Checklists (checklist.py): a `done` status also needs run/checklists/<PHASE>/<id>.json with
every item checked and the same pages as the (sub-)packet. Required for per-packet phases at or
after state.json `checklists_from` (set by `state.py init`; absent in older runs), or with
--require-checklist; otherwise verified only if present. A missing checklist = unknown coverage.
Doubt ledger (doubts.py): if this phase has ledger entries, a status whose `doubts` differs from
the entries it added gets a WARN line (not a failure).
Model (state.PINNED_MODEL): a status whose `model` isn't the pinned model, or a per-unit `done`
status with no `model`, gets a `MODEL WARN` line. The orchestrator stops on it and tells the user
(a re-dispatch would run on the same wrong model).
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import checklist as CL  # noqa: E402
import doubts as D  # noqa: E402
import gate  # noqa: E402
import packets as P  # noqa: E402
from state import PHASES, PINNED_MODEL, model_matches  # noqa: E402

OK = {"done", "skipped"}
KNOWN = OK | {"failed", "filter_blocked"}


def checklists_required(run, phase):
    try:
        with open(os.path.join(run, "state.json"), encoding="utf-8") as f:
            frm = json.load(f).get("checklists_from")
    except (OSError, json.JSONDecodeError):
        return False
    # review rounds map to their base phase: validate-r2, validate-g1, validate-g2-r3,
    # validate-r5-confirm, grade-r3 (scan keys `<K>-scan` never match: they use --by-unit)
    phase = re.sub(r"^(validate|grade)(?:-[rg]\d+)*(?:-confirm)?$", r"\1", phase)
    return bool(frm) and frm in PHASES and phase in PHASES and PHASES.index(phase) >= PHASES.index(frm)


def unit_groups(work, run, units_arg):
    """--by-unit groups: one entry per manifest unit (or --units), id u<NN>."""
    with open(os.path.join(run, "manifest.json"), encoding="utf-8") as f:
        man = json.load(f)
    units = {u["n"]: u for u in man["units"]}
    if units_arg:
        wanted = P.parse_unit_list(units_arg)
        unknown = [n for n in wanted if n not in units]
        if unknown:
            sys.exit(f"unknown units: {unknown}")
    else:
        wanted = sorted(units)
    w = P.uid_width(run)
    suffix = man.get("file_suffix", "")
    out = []
    for n in wanted:
        fn = units[n]["file"]
        stem = (fn[: -len(suffix)] if suffix and fn.endswith(suffix) else os.path.splitext(fn)[0]) + "_english"
        out.append({"id": P.uid(run, n, w), "parent": None, "units": [n], "pages": None,
                    "english": os.path.join(work, "english", f"{stem}.txt"), "stem": stem})
    return out


def unit_artifact(run, phase, e):
    """(artifact path, bundle path) of a per-unit status."""
    if phase == "translate":
        return e["english"], os.path.join(run, "bundles", "translate", f"{e['id']}.md")
    k = phase[: -len("-scan")] if phase.endswith("-scan") else phase
    return (os.path.join(run, "findings", k, f"{e['stem']}.json"),
            os.path.join(run, "bundles", k, f"{e['id']}.md"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--phase", required=True)
    ap.add_argument("--packets", help="comma-separated subset of packet or sub-packet ids")
    ap.add_argument("--expect", action="append", default=[], help="status name(s) for single-agent phases")
    ap.add_argument("--with-packets", action="store_true",
                    help="with --expect: also check every packet (R4: packets + seams)")
    ap.add_argument("--sum", action="append", default=[], help="extra numeric status field(s) to total, e.g. substantive")
    ap.add_argument("--nonzero", help="also print the ids whose status has this field > 0 (e.g. substantive)")
    ap.add_argument("--whole", action="store_true", help="ignore sub-packets")
    ap.add_argument("--require-checklist", action="store_true")
    ap.add_argument("--by-unit", action="store_true", help="per-unit phase: translate, <K>-scan")
    ap.add_argument("--units", help="with --by-unit: comma list of unit numbers, u<NN> ids or batch ids")
    a = ap.parse_args()
    gate.arm("status_check")
    work = os.path.abspath(a.work_dir)
    run = os.path.join(work, "_source", "run")
    if a.by_unit and (a.require_checklist or a.expect or a.packets):
        sys.exit("--by-unit can't be combined with --require-checklist, --expect or --packets.")
    if a.units and not a.by_unit:
        sys.exit("--units goes with --by-unit.")
    if a.with_packets and not a.expect:
        sys.exit("--with-packets goes with --expect (without --expect every packet is checked anyway).")

    # groups: [(label, [entries])]; an entry is {id, parent, units, pages}
    if a.by_unit:
        groups = [(e["id"], [e]) for e in unit_groups(work, run, a.units)]
    elif a.expect and not a.with_packets:
        groups = []
    else:
        packets = P.load(run)["packets"]
        wanted = a.packets.split(",") if a.packets else None
        if wanted is None and a.phase == "convergence":
            try:
                cp = json.load(open(os.path.join(run, "state.json"), encoding="utf-8")).get("convergence_packets")
                wanted = cp.split(",") if isinstance(cp, str) and cp else None
            except (OSError, json.JSONDecodeError):
                pass
        if wanted:
            found = P.lookup(run, set(wanted))
            unknown = [w for w in wanted if w not in found]
            if unknown:
                sys.exit(f"unknown packet ids: {unknown}")
            groups = [(w, [found[w][1]] if found[w][1] else P.governing(run, a.phase, found[w][0], a.whole))
                      for w in wanted]
        else:
            groups = [(p["id"], P.governing(run, a.phase, p, a.whole)) for p in packets]
    # roles (--expect) need a checklist only with --require-checklist; packets as the phase says
    roles = [(n, [{"id": n, "parent": None, "units": [], "pages": None, "role": True}]) for n in a.expect]
    groups += roles
    need_cl_packets = not a.by_unit and (a.require_checklist or checklists_required(run, a.phase))
    ledger, lorder = D.load(work)
    in_ledger = any(ledger[i].get("phase") == a.phase for i in lorder)

    problems, warns, redo, totals, nonzero = [], [], [], {"fixes": 0, "doubts": 0, "decisions": 0}, []
    totals.update({k: 0 for k in a.sum})
    good = 0
    for label, ents in groups:
        group_ok = True
        for e in ents:
            pid = e["id"]
            fp = os.path.join(run, "status", a.phase, f"{pid}.json")
            if not os.path.exists(fp):
                problems.append(f"{pid}: MISSING status file")
                redo.append(pid)
                group_ok = False
                continue
            try:
                with open(fp, encoding="utf-8") as f:
                    st = json.load(f)
            except (json.JSONDecodeError, OSError) as ex:
                problems.append(f"{pid}: MALFORMED status ({ex.__class__.__name__})")
                redo.append(pid)
                group_ok = False
                continue
            s = st.get("status")
            bad = False
            if s not in KNOWN:
                problems.append(f"{pid}: unknown status {s!r}")
                bad = True
            elif s not in OK:
                problems.append(f"{pid}: {s}" + (f" -- {st.get('reason', '')[:80]}" if st.get("reason") else ""))
                bad = True
            notes = st.get("notes")  # relative to <work>/_source/, e.g. "run/notes/R2/p03.md"
            if s in OK and notes and not os.path.exists(os.path.join(os.path.dirname(run), notes)):
                problems.append(f"{pid}: notes file {notes} not found")
                bad = True
            if a.by_unit and s in OK:
                art, bun = unit_artifact(run, a.phase, e)
                if s == "done" or a.phase == "translate":
                    if not os.path.exists(art):
                        problems.append(f"{pid}: {s} but {os.path.relpath(art, work)} is missing")
                        bad = True
                    elif s == "done" and os.path.exists(bun) and os.path.getmtime(art) < os.path.getmtime(bun):
                        problems.append(f"{pid}: stale: {os.path.basename(art)} is older than its bundle")
                        bad = True
            if "model" in st or (a.by_unit and s == "done"):
                if not model_matches(st.get("model")):
                    warns.append(f"MODEL {pid}: status model {st.get('model')!r}, pinned {PINNED_MODEL}")
            need_cl = a.require_checklist if e.get("role") else need_cl_packets
            if not a.by_unit and s == "done" and (need_cl or os.path.exists(CL.cpath(run, a.phase, pid))):
                ok, msg = CL.verify(work, run, a.phase, pid, e["pages"])
                if not ok:
                    problems.append(f"{pid}: {msg}")
                    bad = True
            if bad:
                redo.append(pid)
                group_ok = False
            if in_ledger and s == "done":
                added = sum(1 for i in lorder if ledger[i].get("phase") == a.phase and ledger[i].get("packet") == pid)
                try:
                    if int(st.get("doubts", 0) or 0) != added:
                        warns.append(f"{pid}: status doubts={st.get('doubts', 0)} but ledger has {added} added")
                except (TypeError, ValueError):
                    pass
            for k in totals:
                try:
                    totals[k] += int(st.get(k, 0) or 0)
                except (TypeError, ValueError):
                    pass
            if a.nonzero:
                try:
                    if int(st.get(a.nonzero, 0) or 0) > 0:
                        nonzero.append(pid)
                except (TypeError, ValueError):
                    pass
        good += group_ok

    print(f"{a.phase}: {good}/{len(groups)} complete; " + " ".join(f"{k}={v}" for k, v in totals.items()))
    for p in problems:
        print(f"  - {p}")
    for w in warns:
        print(f"  {w.replace('MODEL ', 'MODEL WARN ', 1) if w.startswith('MODEL ') else 'WARN ' + w}")
    if a.nonzero:
        print(f"NONZERO {a.nonzero}: " + (",".join(nonzero) or "(none)"))
    if redo:
        print("REDISPATCH: " + ",".join(redo))
    gate.finish(len(redo))


if __name__ == "__main__":
    gate.guard(main)

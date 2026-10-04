#!/usr/bin/env python3
"""Sub-packets for long packets: `<work>/_source/run/packets.json`.

A packet is whole units (a unit is never split across packets), so a long unit makes a long
packet, and one agent reading 20+ pages dies on rate limits or the stall watchdog. A packet may
therefore carry SUB-PACKETS: contiguous page ranges of the same units, each run by its own agent,
each writing its own status/notes/checklist under its own id (p07a, p07b, ...). A packet is
complete only when all its sub-packets are; status_check.py and merge_notes.py handle this.

    {"id": "p07", "units": [7], "pages": ["173", ... "199"],
     "subs": [{"id": "p07a", "pages": ["173", ... "186"]}, {"id": "p07b", "pages": ["187", ... "199"]}]}

    packets.py split  --work-dir D [--max-pages 12]          # add subs to every packet > 12 pages
    packets.py split  --work-dir D --packet p07 --parts 3    # (re-)split one packet (retry rule)
    packets.py split  --work-dir D --packet p07 --parts 1    # remove p07's subs
    packets.py list   --work-dir D [--ids p07,p09b] [--whole] # one assignment line per dispatch id
    packets.py ids    --work-dir D [--ids p07,p09] [--whole]  # comma list of dispatch ids
    packets.py units  --work-dir D [--ids p03,p08]            # comma list of their unit numbers
    packets.py uids   --work-dir D [--units 3,8] [--ids p03,p08]   # comma list of unit ids (u03,u08)
    packets.py list   --work-dir D --ids u07                  # one per-unit assignment line
    packets.py list   --work-dir D --ids u12-u17              # a batch line + one line per unit
    packets.py batches --work-dir D --units <list> [--max-units N] [--max-chars C] [--isolate-first]
                                                              # comma list of batch ids (below)
    packets.py placeholders --work-dir D   # Pass B: one placeholder line per sub in split units
    packets.py join   --work-dir D         # Pass B: remove `[[JOIN]]` seams left by sub agents
                                           # (a gate: ends with `GATE join: PASS|FAIL`)

Dispatch ids = sub ids for packets that have subs, else the packet id (`--ids p07` expands to
p07's subs). `--whole` ignores subs (review phases that work per unit: validate, grade).
Per-unit phases (translate, the validate/grade scans) dispatch UNIT ids: `u` + the unit number
zero-padded to 2 digits, or to the width of the highest unit number (u07, or u007 in a work that
has a unit 100).

BATCHES (per-unit phases only). One agent may work a short run of consecutive units, one unit at
a time, each with its own bundle, output, notes and status. A batch id is `u<first>-u<last>`, both
ends inclusive and padded like unit ids (`u012-u017`); it covers every number in the range. A
batch of one is the plain unit id. `batches` groups the given units greedily, in order, starting a
new batch at a gap in the numbers, when the batch has N units, or when the next unit would push
the batch's source size (bytes of the unit files in the language folder) past C; a unit larger
than C alone is a batch of one. N and C default to state.json `batch_units` / `batch_chars`,
else 6 and 30000; N=1 gives today's one-agent-per-unit dispatch. `--isolate-first` (re-dispatch
after a failure) also makes the first unit of every run of consecutive units a batch of its own:
when a batch agent dies, that unit is the likeliest cause. Every `--units` option of the skill's
tools takes batch ids too (`parse_unit_list`).

Which status files count for a packet with subs ("governing"): the subs, if any sub status
exists that is newer than the whole-packet status; otherwise the whole-packet status, if it
exists (runs dispatched before the split); otherwise the subs (none dispatched yet).
"""

import argparse
import json
import math
import os
import re
import string
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate  # noqa: E402

PLACEHOLDER = "[[TO BE TRANSCRIBED IN PASS B]]"


def run_dir(work):
    return os.path.join(os.path.abspath(work), "_source", "run")


def load(run):
    with open(os.path.join(run, "packets.json"), encoding="utf-8") as f:
        return json.load(f)


def save(run, data):
    tmp = os.path.join(run, "packets.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    os.replace(tmp, os.path.join(run, "packets.json"))


def unit_pages(run):
    try:
        with open(os.path.join(run, "manifest.json"), encoding="utf-8") as f:
            return {u["n"]: u.get("pages") or [] for u in json.load(f)["units"]}
    except (OSError, json.JSONDecodeError, KeyError):
        return {}


def entry(p, sub=None, upages=None):
    """A dispatch entry: {id, parent, units, pages}."""
    if sub is None:
        return {"id": p["id"], "parent": None, "units": p.get("units", []), "pages": p.get("pages", [])}
    pg = set(sub["pages"])
    units = [n for n in p.get("units", []) if not upages or pg & set(upages.get(n, []))] or p.get("units", [])
    return {"id": sub["id"], "parent": p["id"], "units": units, "pages": sub["pages"]}


def entries(run, whole=False):
    """Every dispatch entry, in packet order (subs replace their parent unless whole)."""
    up = unit_pages(run)
    out = []
    for p in load(run)["packets"]:
        subs = [] if whole else (p.get("subs") or [])
        out += [entry(p, s, up) for s in subs] if subs else [entry(p)]
    return out


def lookup(run, ids):
    """Map ids (packet or sub ids) to (packet, entry-or-None)."""
    up = unit_pages(run)
    found = {}
    for p in load(run)["packets"]:
        if p["id"] in ids:
            found[p["id"]] = (p, None)
        for s in p.get("subs") or []:
            if s["id"] in ids:
                found[s["id"]] = (p, entry(p, s, up))
    return found


def expand(run, ids, whole=False):
    """Dispatch entries for a list of packet/sub ids; a packet with subs expands to its subs."""
    up = unit_pages(run)
    found = lookup(run, set(ids))
    unknown = [i for i in ids if i not in found]
    if unknown:
        sys.exit(f"unknown ids: {unknown}")
    out = []
    for i in ids:
        p, e = found[i]
        subs = [] if whole else (p.get("subs") or [])
        out += [e] if e else ([entry(p, s, up) for s in subs] if subs else [entry(p)])
    return out


def governing(run, phase, p, whole=False):
    """The entries whose status files decide whether packet p is complete (see module doc)."""
    subs = [] if whole else (p.get("subs") or [])
    if not subs:
        return [entry(p)]
    st = lambda i: os.path.join(run, "status", phase, f"{i}.json")
    sub_m = [os.path.getmtime(st(s["id"])) for s in subs if os.path.exists(st(s["id"]))]
    wfp = st(p["id"])
    if os.path.exists(wfp) and (not sub_m or os.path.getmtime(wfp) > max(sub_m)):
        return [entry(p)]
    up = unit_pages(run)
    return [entry(p, s, up) for s in subs]


def page_range(pages):
    return f"{pages[0]}-{pages[-1]}" if len(pages) > 1 else (pages[0] if pages else "")


def split_pages(pages, parts):
    q, r = divmod(len(pages), parts)
    out, i = [], 0
    for k in range(parts):
        j = i + q + (1 if k < r else 0)
        out.append(pages[i:j])
        i = j
    return out


def cmd_split(a, run):
    data = load(run)
    changed = []
    for p in data["packets"]:
        if a.packet and p["id"] != a.packet:
            continue
        pages = p.get("pages") or []
        parts = a.parts if a.packet and a.parts else math.ceil(len(pages) / a.max_pages)
        if not a.packet and (len(pages) <= a.max_pages or p.get("subs")):
            continue  # all-mode never re-splits a packet that already has subs
        if parts <= 1:
            if p.pop("subs", None) is not None:
                changed.append(f"{p['id']}: subs removed")
            continue
        parts = min(parts, len(pages), 26)
        chunks = split_pages(pages, parts)
        p["subs"] = [{"id": p["id"] + string.ascii_lowercase[i], "pages": c} for i, c in enumerate(chunks)]
        changed.append(f"{p['id']} ({len(pages)} pp.) -> " +
                       ", ".join(f"{s['id']} {page_range(s['pages'])}" for s in p["subs"]))
    if a.packet and not changed and not any(p["id"] == a.packet for p in data["packets"]):
        sys.exit(f"unknown packet {a.packet}")
    save(run, data)
    print("\n".join(changed) if changed else "no packet needs splitting")


def unit_labels(run):
    try:
        with open(os.path.join(run, "manifest.json"), encoding="utf-8") as f:
            return {u["n"]: u.get("label", str(u["n"])) for u in json.load(f)["units"]}
    except (OSError, json.JSONDecodeError, KeyError):
        return {}


def cmd_list(a, run):
    if a.ids and all(is_uid(i) or is_batch(i) for i in a.ids.split(",")):
        return list_units(run, a.ids.split(","))
    labels = unit_labels(run)
    es = expand(run, a.ids.split(","), a.whole) if a.ids else entries(run, a.whole)
    for e in es:
        u = ", ".join(labels.get(n, str(n)) for n in e["units"])
        line = f"{e['id']} = units {e['units']} ({u}), pages {page_range(e['pages'])}"
        if e["parent"]:
            line = (f"sub-packet {line} ONLY (of packet {e['parent']}; other pages belong to "
                    f"sibling sub-packets)")
        else:
            line = "packet " + line
        print(line)


def uid_width(run):
    return max(2, len(str(max(unit_pages(run), default=0))))


def uid(run, n, width=None):
    return f"u{n:0{width or uid_width(run)}d}"


def is_uid(s):
    return bool(re.fullmatch(r"u\d+", s))


def is_batch(s):
    return bool(re.fullmatch(r"u\d+-u\d+", s))


def parse_unit_list(spec):
    """`3,8`, `u03,u08`, batch ids `u012-u017` (or `12-17`), mixed -> sorted unit numbers."""
    out = set()
    for x in (t.strip() for t in spec.split(",")):
        if not x:
            continue
        m = re.fullmatch(r"u?(\d+)(?:-u?(\d+))?", x)
        if not m:
            sys.exit(f"not a unit, unit id or batch id: {x!r}")
        lo = int(m.group(1))
        hi = int(m.group(2)) if m.group(2) else lo
        if hi < lo:
            sys.exit(f"batch {x!r} runs backwards")
        out.update(range(lo, hi + 1))
    return sorted(out)


def batch_id(run, ns, width=None):
    w = width or uid_width(run)
    return uid(run, ns[0], w) if len(ns) == 1 else f"{uid(run, ns[0], w)}-{uid(run, ns[-1], w)}"


def batch_defaults(run):
    try:
        with open(os.path.join(run, "state.json"), encoding="utf-8") as f:
            st = json.load(f)
    except (OSError, json.JSONDecodeError):
        st = {}
    return int(st.get("batch_units") or 6), int(st.get("batch_chars") or 30000)


def make_batches(ns, size, max_units, max_chars, isolate_first=False):
    """Greedy grouping of sorted unit numbers into lists of consecutive units (see module doc)."""
    out, cur, cur_size, prev = [], [], 0, None
    for n in ns:
        run_start = prev is None or n != prev + 1
        prev = n
        if cur and (run_start or len(cur) >= max_units or cur_size + size.get(n, 0) > max_chars):
            out.append(cur)
            cur, cur_size = [], 0
        cur.append(n)
        cur_size += size.get(n, 0)
        if isolate_first and run_start:
            out.append(cur)
            cur, cur_size = [], 0
    if cur:
        out.append(cur)
    return out


def cmd_batches(a, run):
    _, files = unit_files(run)
    ns = parse_unit_list(a.units) if a.units else sorted(files)
    unknown = [n for n in ns if n not in files]
    if unknown:
        sys.exit(f"unknown units: {unknown}")
    max_units, max_chars = batch_defaults(run)
    max_units, max_chars = a.max_units or max_units, a.max_chars or max_chars
    size = {n: os.path.getsize(files[n]) if os.path.exists(files[n]) else 0 for n in ns}
    w = uid_width(run)
    print(",".join(batch_id(run, b, w) for b in make_batches(ns, size, max(1, max_units), max_chars,
                                                             a.isolate_first)))


def unit_packet(run):
    return {n: p["id"] for p in load(run)["packets"] for n in p.get("units", [])}


def cmd_uids(a, run):
    if a.units:
        ns = parse_unit_list(a.units)
    elif a.ids:
        found = lookup(run, set(a.ids.split(",")))
        unknown = [i for i in a.ids.split(",") if i not in found]
        if unknown:
            sys.exit(f"unknown ids: {unknown}")
        ns = sorted({n for p, _ in found.values() for n in p.get("units", [])})
    else:
        ns = sorted(unit_pages(run))
    w = uid_width(run)
    print(",".join(uid(run, n, w) for n in ns))


def list_units(run, ids):
    """One line per unit id; a batch id prints a batch line, then one line per unit."""
    labels, up, pk = unit_labels(run), unit_pages(run), unit_packet(run)
    w = uid_width(run)
    for i in ids:
        ns = parse_unit_list(i)
        unknown = [n for n in ns if n not in up]
        if unknown:
            sys.exit(f"unknown unit(s) in {i}: {unknown}")
        indent = ""
        if is_batch(i):
            pks = ",".join(dict.fromkeys(pk.get(n, "?") for n in ns))
            print(f"batch {i} = {len(ns)} units {ns[0]}-{ns[-1]} ({labels.get(ns[0], ns[0])} … "
                  f"{labels.get(ns[-1], ns[-1])}), packets {pks}; work them one at a time, in this order:")
            indent = "  "
        for n in ns:
            print(f"{indent}unit {uid(run, n, w)} = unit {n} ({labels.get(n, n)}), pages {page_range(up[n])}, "
                  f"packet {pk.get(n, '?')}")


def unit_files(run):
    with open(os.path.join(run, "manifest.json"), encoding="utf-8") as f:
        man = json.load(f)
    work = os.path.dirname(os.path.dirname(run))
    return man, {u["n"]: os.path.join(work, man["lang_dir"], u["file"]) for u in man["units"]}


def cmd_placeholders(a, run):
    man, files = unit_files(run)
    up = unit_pages(run)
    n_done = 0
    for p in load(run)["packets"]:
        for n in p.get("units", []):
            subs = [s for s in p.get("subs") or [] if set(s["pages"]) & set(up.get(n, []))]
            fp = files.get(n)
            if len(subs) < 2 or not fp or not os.path.exists(fp):
                continue
            text = open(fp, encoding="utf-8").read()
            lines = text.split("\n")
            if sum(1 for l in lines if l.strip() == PLACEHOLDER) != 1:
                continue  # already split, or already transcribed
            new = "\n".join(f"[[TO BE TRANSCRIBED IN PASS B: {s['id']} pp.{page_range(s['pages'])}]]"
                            for s in subs)
            lines = [new if l.strip() == PLACEHOLDER else l for l in lines]
            with open(fp, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            n_done += 1
    print(f"placeholders: split {n_done} unit file(s)")


def cmd_join(a, run):
    man, files = unit_files(run)
    joined, left = 0, []
    for n, fp in files.items():
        if not os.path.exists(fp):
            continue
        text = open(fp, encoding="utf-8").read()
        new, k = re.subn(r"[ \t]*\n+\[\[JOIN\]\]", "", text)
        if k:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(new)
            joined += k
        if "[[JOIN]]" in new or "TO BE TRANSCRIBED" in new:
            left.append(os.path.basename(fp))
    print(f"join: {joined} seam(s) joined" + (f"; LEFTOVER markers/placeholders in: {', '.join(left)}"
                                               if left else ""))
    gate.finish(len(left))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["split", "list", "ids", "units", "uids", "batches", "placeholders", "join"])
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--max-pages", type=int, default=12)
    ap.add_argument("--packet")
    ap.add_argument("--parts", type=int)
    ap.add_argument("--ids", help="comma list of packet/sub ids (list)")
    ap.add_argument("--whole", action="store_true", help="ignore sub-packets")
    ap.add_argument("--units", help="comma list of unit numbers, unit ids or batch ids (uids, batches)")
    ap.add_argument("--max-units", type=int, help="batches: units per batch (default state batch_units, else 6)")
    ap.add_argument("--max-chars", type=int, help="batches: source bytes per batch (default state batch_chars, else 30000)")
    ap.add_argument("--isolate-first", action="store_true",
                    help="batches: the first unit of every run of consecutive units goes alone (re-dispatch)")
    a = ap.parse_args()
    run = run_dir(a.work_dir)
    if a.cmd == "join":
        gate.arm("join")
    if a.cmd == "split":
        cmd_split(a, run)
    elif a.cmd == "list":
        cmd_list(a, run)
    elif a.cmd == "ids":
        print(",".join(e["id"] for e in (expand(run, a.ids.split(","), a.whole) if a.ids
                                         else entries(run, a.whole))))
    elif a.cmd == "units":
        ps = [p for p in load(run)["packets"] if not a.ids or p["id"] in a.ids.split(",")]
        print(",".join(str(n) for n in sorted({n for p in ps for n in p["units"]})))
    elif a.cmd == "uids":
        cmd_uids(a, run)
    elif a.cmd == "batches":
        cmd_batches(a, run)
    elif a.cmd == "placeholders":
        cmd_placeholders(a, run)
    elif a.cmd == "join":
        cmd_join(a, run)


if __name__ == "__main__":
    gate.guard(main)

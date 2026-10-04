#!/usr/bin/env python3
"""Merge per-packet agent notes into the pass report, the running uncertain-readings log, and the
carry-forward list.

Parallel agents never write to shared files. Each writes `_source/run/notes/<PHASE>/<packet>.md`:

    # <PHASE> — <packet>
    ## Summary
    ## Fixes
    ## Doubts
    ## Carry-forward
    - [R4] ...          (target pass in brackets)

After the wave, the orchestrator runs this script once. It:
  * writes `_source/<report>` = a header + every packet's notes, in packet order;
  * replaces this phase's block in `_source/uncertain_readings.md` with all "## Doubts" sections;
  * replaces this phase's block in `_source/run/carry_forward.md` with all "## Carry-forward"
    sections.
Blocks are delimited by HTML comments, so re-running a phase replaces rather than duplicates.
Then it prints this phase's un-acked `[orchestrator]` items (below), if any.
Sub-packet notes (p07a.md, p07b.md; see packets.py) are merged in page order under their packet;
for each packet only the notes of the governing status set (subs or whole) are merged, so stale
notes from an earlier whole-packet or sub-packet dispatch are left out.

    merge_notes.py --work-dir D --phase R2 --report recollation_pass.md --title "R2 — lensless re-collation"
    merge_notes.py --work-dir D --pending                  # every phase's un-acked items; merges nothing
    merge_notes.py --work-dir D --ack R4/seams#3f2a9c1d[,<id>...] --how routed|decision|user|none --ref "<one line>"

`[orchestrator]` items: the one kind of note the orchestrator reads. An item is a bullet of a
Carry-forward section whose leading bracket tag list contains `orchestrator`, in any case
(`[orchestrator]`, `[R4, orchestrator]`), with its continuation lines (until a blank line, a
heading or the next bullet at the same or a lower indent). Its id is `<phase>/<note id>#<h>`,
`<h>` = the first 8 hex digits of the SHA-1 of its text, whitespace collapsed. A merge prints

    ORCHESTRATOR: 2 item(s)
      R4/seams#3f2a9c1d: manifest u54 explicit ... (the first line, cut to 200 characters)

`--ack` records how one was settled in run/orchestrator_acks.jsonl ({"item", "how", "ref", "time"};
an unknown id exits 2). An item counts as acked when an ack for its id is newer than its note file,
so re-merging or resuming never re-lists it, but a fresh agent that rewrites the note under the
same phase key and reports the same item again re-opens it.
"""

import argparse
import datetime
import glob
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import packets as P  # noqa: E402


def section(text, name):
    m = re.search(rf"(?ms)^## {re.escape(name)}\s*\n(.*?)(?=^## |\Z)", text)
    body = m.group(1).strip() if m else ""
    return "" if body.lower() in ("", "none", "- none", "(none)", "n/a") else body


def replace_block(path, phase, content, title):
    start, end = f"<!-- {phase}:start -->", f"<!-- {phase}:end -->"
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else f"# {title}\n"
    block = f"{start}\n## {phase}\n\n{content.strip() or '(none)'}\n{end}"
    if start in old and end in old:
        new = re.sub(rf"(?s){re.escape(start)}.*?{re.escape(end)}", lambda _: block, old)
    else:
        new = old.rstrip() + "\n\n" + block + "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)


ITEM_RX = re.compile(r"^(\s*)[-*+]\s+(?:\*\*)?\[([^\]]*)\]\s*(?:\*\*)?\s*")
BULLET_RX = re.compile(r"^(\s*)[-*+]\s")
HOW = ("routed", "decision", "user", "none")


def orchestrator_items(text):
    """[(full text, first line without bullet and tags)] for the [orchestrator] bullets in text."""
    lines, out, i = text.split("\n"), [], 0
    while i < len(lines):
        m = ITEM_RX.match(lines[i])
        if not m or "orchestrator" not in [t.lower() for t in re.split(r"[\s,;/]+", m.group(2)) if t]:
            i += 1
            continue
        indent, item = len(m.group(1)), [lines[i]]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].lstrip().startswith("#"):
            b = BULLET_RX.match(lines[i])
            if b and len(b.group(1)) <= indent:
                break
            item.append(lines[i])
            i += 1
        out.append((" ".join(item), item[0][m.end():].strip()))
    return out


def item_id(phase, note, text):
    h = hashlib.sha1(re.sub(r"\s+", " ", text).strip().encode("utf-8")).hexdigest()[:8]
    return f"{phase}/{note}#{h}"


def all_items(run):
    """[(id, phase, note, first line)] for every [orchestrator] item in carry_forward.md."""
    path = os.path.join(run, "carry_forward.md")
    if not os.path.exists(path):
        return []
    text = open(path, encoding="utf-8").read()
    out = []
    for blk in re.finditer(r"(?s)<!-- (\S+?):start -->(.*?)<!-- \1:end -->", text):
        phase = blk.group(1)
        for sec in re.finditer(r"(?ms)^### from (.+?) / (\S+)[ \t]*\n(.*?)(?=^### |\Z)", blk.group(2)):
            note = sec.group(2)
            for full, first in orchestrator_items(sec.group(3)):
                out.append((item_id(phase, note, full), phase, note, first))
    return out


def acked(run, items):
    """The ids among items with an ack newer than their note file."""
    path = os.path.join(run, "orchestrator_acks.jsonl")
    last = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            try:
                r = json.loads(line)
                t = datetime.datetime.fromisoformat(r["time"]).timestamp()
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue
            last[r.get("item")] = max(t, last.get(r.get("item"), 0))
    done = set()
    for iid, phase, note, _ in items:
        nf = os.path.join(run, "notes", phase, f"{note}.md")
        if iid in last and last[iid] > (os.path.getmtime(nf) if os.path.exists(nf) else 0):
            done.add(iid)
    return done


def print_items(items, done, empty_too=False):
    todo = [it for it in items if it[0] not in done]
    if todo or empty_too:
        print(f"ORCHESTRATOR: {len(todo)} item(s)")
    for iid, _, _, first in todo:
        line = f"{iid}: {first}"
        print("  " + (line if len(line) <= 200 else line[:199] + "…"))


def ack(run, ids, how, ref):
    known = {it[0] for it in all_items(run)}
    unknown = [i for i in ids if i not in known]
    if unknown:
        print(f"unknown item id(s): {', '.join(unknown)} (merge_notes.py --pending lists the current ones)")
        sys.exit(2)
    with open(os.path.join(run, "orchestrator_acks.jsonl"), "a", encoding="utf-8") as f:
        for i in ids:
            f.write(json.dumps({"item": i, "how": how, "ref": ref,
                                "time": datetime.datetime.now().isoformat()}, ensure_ascii=False) + "\n")
    print(f"acked {len(ids)} item(s) ({how})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--phase")
    ap.add_argument("--report")
    ap.add_argument("--title", default="")
    ap.add_argument("--pending", action="store_true", help="list every phase's un-acked [orchestrator] items")
    ap.add_argument("--ack", help="comma list of item ids to record as settled")
    ap.add_argument("--how", choices=HOW)
    ap.add_argument("--ref", help="one line: where it went, or why no action")
    a = ap.parse_args()
    src = os.path.join(os.path.abspath(a.work_dir), "_source")
    run = os.path.join(src, "run")
    if a.ack:
        if not (a.how and a.ref):
            ap.error("--ack needs --how and --ref")
        ack(run, [i.strip() for i in a.ack.split(",") if i.strip()], a.how, a.ref)
        return
    if a.pending:
        items = all_items(run)
        print_items(items, acked(run, items), empty_too=True)
        return
    if not (a.phase and a.report):
        ap.error("a merge needs --phase and --report (or use --pending / --ack)")

    order, stale = [], set()
    pk = os.path.join(run, "packets.json")
    if os.path.exists(pk):
        for p in json.load(open(pk, encoding="utf-8"))["packets"]:
            ids = [p["id"]] + [s["id"] for s in p.get("subs") or []]
            order += ids
            stale |= set(ids) - {e["id"] for e in P.governing(run, a.phase, p)}
    files = [f for f in glob.glob(os.path.join(run, "notes", a.phase, "*.md"))
             if os.path.splitext(os.path.basename(f))[0] not in stale]
    key = lambda f: (order.index(os.path.splitext(os.path.basename(f))[0])
                     if os.path.splitext(os.path.basename(f))[0] in order else 10**6, f)
    files.sort(key=key)

    parts, doubts, carry = [], [], []
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0]
        text = open(f, encoding="utf-8").read().strip()
        parts.append(text)
        d, c = section(text, "Doubts"), section(text, "Carry-forward")
        if d:
            doubts.append(f"### {name}\n{d}")
        if c:
            carry.append(f"### from {a.phase} / {name}\n{c}")

    report = os.path.join(src, a.report)
    with open(report, "w", encoding="utf-8") as fh:
        fh.write(f"# {a.title or a.phase}\n\nMerged from {len(files)} agent note file(s) in "
                 f"`run/notes/{a.phase}/`.\n\n" + "\n\n---\n\n".join(parts) + "\n")
    replace_block(os.path.join(src, "uncertain_readings.md"), a.phase, "\n\n".join(doubts),
                  "Uncertain readings (running log)")
    replace_block(os.path.join(run, "carry_forward.md"), a.phase, "\n\n".join(carry),
                  "Carry-forward items (read the ones tagged for your pass)")
    print(f"{a.phase}: merged {len(files)} note file(s) -> {a.report}; "
          f"{len(doubts)} with doubts, {len(carry)} with carry-forward items")
    items = [it for it in all_items(run) if it[1] == a.phase]
    print_items(items, acked(run, items))


if __name__ == "__main__":
    main()

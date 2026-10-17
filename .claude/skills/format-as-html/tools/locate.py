#!/usr/bin/env python3
"""List plausible output locations for a work's HTML, for the location interview.

    locate.py --work-dir W [--json]

Finds candidate Writings-Database roots (a folder whose CLAUDE.md or AGENTS.md describes the
`<article class="writing">` fragment format), then, in each, an existing file or folder for the work
(exact and close name matches). Prints numbered options, the recommended one first; the model shows
them to the user as quick selects and records the answer in html_config.py OUTPUT.

Root candidates, in order: $FORMAT_AS_HTML_ROOT; the sibling of a `<X>-Non-English` ancestor named
`<X>`; any `Writings-Database*` folder next to an ancestor of W or on the Desktop.
"""
import argparse
import difflib
import json
import os
import re


def work_names(work_dir):
    cfg = os.path.join(work_dir, "_source", "run", "work_config.py")
    author = work = None
    if os.path.exists(cfg):
        with open(cfg, encoding="utf-8") as fh:
            text = fh.read()
        a = re.search(r'^AUTHOR\s*=\s*"([^"]+)"', text, re.M)
        w = re.search(r'^WORK\s*=\s*"([^"]+)"', text, re.M)
        author, work = (a.group(1) if a else None), (w.group(1) if w else None)
    parts = os.path.normpath(work_dir).split(os.sep)
    return author or parts[-2], work or parts[-1]


def is_root(path):
    for name in ("CLAUDE.md", "AGENTS.md"):
        f = os.path.join(path, name)
        if os.path.isfile(f):
            with open(f, encoding="utf-8", errors="ignore") as fh:
                if 'class="writing"' in fh.read():
                    return True
    return False


def candidate_roots(work_dir):
    seen, out = set(), []

    def add(path, why):
        path = os.path.realpath(os.path.expanduser(path))
        if path in seen or not os.path.isdir(path):
            return
        seen.add(path)
        out.append({"root": path, "why": why, "valid": is_root(path)})

    if os.environ.get("FORMAT_AS_HTML_ROOT"):
        add(os.environ["FORMAT_AS_HTML_ROOT"], "$FORMAT_AS_HTML_ROOT")
    d = os.path.realpath(work_dir)
    while d != os.path.dirname(d):
        base = os.path.basename(d)
        if base.endswith("-Non-English"):
            add(os.path.join(os.path.dirname(d), base[: -len("-Non-English")]),
                f"sibling of the non-English root {base}")
        parent = os.path.dirname(d)
        try:
            for name in sorted(os.listdir(parent)):
                if name.startswith("Writings-Database") and not name.endswith("-Non-English"):
                    add(os.path.join(parent, name), f"next to {base}")
        except OSError:
            pass
        d = parent
    desktop = os.path.expanduser("~/Desktop")
    if os.path.isdir(desktop):
        for name in sorted(os.listdir(desktop)):
            if name.startswith("Writings-Database") and not name.endswith("-Non-English"):
                add(os.path.join(desktop, name), "on the Desktop")
    return out


def matches(root, author, work):
    """Existing files/folders for the work under root/author (exact first, then close names)."""
    adir = os.path.join(root, author)
    res = []
    if not os.path.isdir(adir):
        close = difflib.get_close_matches(author, os.listdir(root), n=2, cutoff=0.75)
        return res, close
    names = os.listdir(adir)
    if f"{work}.html" in names:
        res.append({"kind": "file", "relpath": f"{author}/{work}.html", "exact": True})
    if work in names and os.path.isdir(os.path.join(adir, work)):
        htmls = sorted(f for f in os.listdir(os.path.join(adir, work)) if f.endswith(".html"))
        res.append({"kind": "folder", "relpath": f"{author}/{work}", "exact": True, "files": len(htmls)})
    if res:                                   # an exact match exists: similar names are noise
        return res, []
    stems = {n[:-5] if n.endswith(".html") else n: n for n in names}
    for c in difflib.get_close_matches(work, list(stems), n=3, cutoff=0.85):
        n = stems[c]
        if n in (f"{work}.html", work):
            continue
        res.append({"kind": "file" if n.endswith(".html") else "folder", "relpath": f"{author}/{n}",
                    "exact": False})
    return res, []


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    work_dir = os.path.abspath(os.path.expanduser(a.work_dir))
    author, work = work_names(work_dir)
    roots = candidate_roots(work_dir)
    options = []
    for r in roots:
        if not r["valid"]:
            continue
        found, close_authors = matches(r["root"], author, work)
        for m in found:
            options.append({**m, "root": r["root"], "label": (
                f"Replace existing {m['relpath']}" + ("" if m["exact"] else " (similar name)"))})
        if not any(m["exact"] for m in found):
            options.append({"kind": "file", "relpath": f"{author}/{work}.html", "root": r["root"],
                            "exact": False, "new": True, "label": f"New file {author}/{work}.html"})
        if not any(m["kind"] == "folder" for m in found):
            options.append({"kind": "folder", "relpath": f"{author}/{work}", "root": r["root"], "new": True,
                            "label": f"New folder {author}/{work}/ (one file per unit)"})
        if close_authors:
            options.append({"kind": "note", "root": r["root"],
                            "label": f"author folder '{author}' not found; similar: {close_authors}"})
    result = {"author": author, "work": work, "roots": roots, "options": options}
    if a.json:
        print(json.dumps(result, indent=1, ensure_ascii=False))
        return
    print(f"work: {author}, {work}")
    print("roots:")
    for r in roots:
        print(f"  {'OK ' if r['valid'] else '-- '} {r['root']}   ({r['why']}"
              f"{'' if r['valid'] else '; no fragment-format CLAUDE.md/AGENTS.md'})")
    print("options (recommended first):")
    for k, o in enumerate(options, 1):
        print(f"  {k}. {o['label']}   [{o['root']}]")
    if not options:
        print("  none found: ask the user for the Writings-Database folder")


if __name__ == "__main__":
    main()

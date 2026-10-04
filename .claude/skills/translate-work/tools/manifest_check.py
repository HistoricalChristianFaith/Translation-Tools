#!/usr/bin/env python3
"""Validate the unit manifest, the work packets, and the base page-image index.

Files (all under <work>/_source/):
  run/manifest.json      units of the work + text conventions + deterministic check settings
  run/packets.json       work packets: which units (and pages) one subagent handles per pass
  pages/base/index.json  staged page images of the base edition, in printed order

manifest.json:
  {"work": "...", "language": "Latin", "lang_dir": "LATIN", "unit_noun": "homily",
   "file_suffix": "_latin.txt", "base_images": "pages/base",
   "anchor": {"format": "[GCS p.{label}]", "regex": "\\\\[GCS p\\\\.(\\\\d+)\\\\]"},
   "checks": {"pairs": ["»«"], "even": ["*"], "even_exempt": null, "forbid": [],
              "section_regex": "(?m)^(?:\\\\[GCS p\\\\.\\\\d+\\\\] ?)?(\\\\d+)\\\\.\\\\s",
              "section_start_for": {"12": 2}, "body_start": null, "ending": null},
   "units": [{"n": 1, "file": "homily01_latin.txt",   (n = the number in the file name; from 0 or 1) "label": "Homily I", "heading": "HOMILIA I.",
              "passage": "Lev 1", "pages": ["280", "281", ...], "incipit": "...", "explicit": "..."}]}
packets.json:  {"packets": [{"id": "p01", "units": [1], "pages": ["280", ...],
                              "subs": [{"id": "p01a", "pages": [...]}, ...]}]}   (subs optional: packets.py)
index.json:    {"pages": [{"label": "280", "file": "pages/base/base_p280_leaf0339.jpg", "leaf": 339}]}

    manifest_check.py --work-dir D            # structure only
    manifest_check.py --work-dir D --files    # also check every unit file exists and is well-formed
The last line is `GATE manifest_check: PASS` or `GATE manifest_check: FAIL (<n> problem(s))` (gate.py).

`incipit` and `explicit` mirror the unit file, not the print: they are locators, and they follow
the text (fixes and emendations included). With --files, each must occur in the unit body (after
the heading line), compared after normalize_fn(): anchors stripped, the `checks.pairs` /
`checks.even` marks removed, whitespace collapsed; letters and punctuation stay exact. `incipit`
within the first INCIPIT_WINDOW characters, `explicit` within the last EXPLICIT_WINDOW. Sync a
field with manifest_edit.py. An adopted manifest (`"adopted": true`) gets these as info lines.
Unit keys outside SCHEMA get one info line (not checked, never an error).
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate  # noqa: E402


SCHEMA = ("n", "file", "label", "heading", "passage", "pages", "incipit", "explicit")
TEXT_FIELDS = ("incipit", "explicit")
INCIPIT_WINDOW = 1500  # normalized characters after the heading line (a lemma line falls inside)
EXPLICIT_WINDOW = 600  # normalized characters at the end of the body
PLACEHOLDER = "TO BE TRANSCRIBED"


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def normalize_fn(man):
    """The normalization shared by a unit body and its incipit / explicit (see module doc)."""
    try:
        anchor = re.compile(man["anchor"]["regex"])
    except (re.error, KeyError, TypeError):
        anchor = None
    checks = man.get("checks") or {}
    marks = set()
    for p in checks.get("pairs", ["»«"]) or []:
        marks.update(p if isinstance(p, list) else list(p))
    marks.update(checks.get("even", []) or [])
    marks = sorted((m for m in marks if m), key=len, reverse=True)

    def norm(s):
        if anchor:
            s = anchor.sub("", s)
        for m in marks:
            s = s.replace(m, "")
        return re.sub(r"\s+", " ", s).strip()
    return norm


def read_body(path):
    """The unit file's body lines after the ==== separator (blank lines dropped), or None."""
    lines = open(path, encoding="utf-8").read().split("\n")
    sep = next((i for i, l in enumerate(lines) if re.match(r"^={5,}\s*$", l)), None)
    return None if sep is None else [l for l in lines[sep + 1:] if l.strip()]


def field_found(norm, field, value, body):
    """True if `value` occurs where `field` must be: body = the body lines, heading first."""
    text = norm(" ".join(body[1:]))
    want = norm(value)
    if not want:
        return False
    return want in (text[:INCIPIT_WINDOW] if field == "incipit" else text[-EXPLICIT_WINDOW:])


def field_problem(norm, n, field, value, body):
    """The error line for a field the text doesn't bear out, or None."""
    if field_found(norm, field, value, body):
        return None
    where = "at the start" if field == "incipit" else "at the end"
    shown = value if len(value) <= 60 else (value[:59] + "…" if field == "incipit" else "…" + value[-59:])
    return f"unit {n}: {field} not found {where} of the body: {shown!r}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--files", action="store_true")
    a = ap.parse_args()
    gate.arm("manifest_check")
    work = os.path.abspath(a.work_dir)
    src = os.path.join(work, "_source")
    errs, info = [], []

    try:
        man = load(os.path.join(src, "run", "manifest.json"))
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"manifest.json unreadable: {e}")
    for k in ("language", "lang_dir", "unit_noun", "file_suffix", "base_images", "anchor", "units"):
        if k not in man:
            errs.append(f"manifest missing key '{k}'")
    if errs:
        print("\n".join(errs))
        gate.finish(len(errs))

    try:
        idx = load(os.path.join(src, man["base_images"], "index.json"))["pages"]
    except (OSError, json.JSONDecodeError, KeyError) as e:
        sys.exit(f"base image index unreadable: {e}")
    order = {p["label"]: i for i, p in enumerate(idx)}
    if len(order) != len(idx):
        errs.append("duplicate labels in the base image index")
    for p in idx:
        if not os.path.exists(os.path.join(src, p["file"])):
            errs.append(f"image missing for page {p['label']}: {p['file']}")

    try:
        rx = re.compile(man["anchor"]["regex"])
        if rx.groups != 1:
            errs.append("anchor.regex must have exactly one capture group (the page/column number)")
    except (re.error, KeyError, TypeError) as e:
        errs.append(f"anchor.regex invalid: {e}")
    sec = man.get("checks", {}).get("section_regex")
    if sec:
        try:
            re.compile(sec)
        except re.error as e:
            errs.append(f"checks.section_regex invalid: {e}")

    units = man["units"]
    adopted = bool(man.get("adopted"))
    ns = [u.get("n") for u in units]
    first = ns[0] if ns and ns[0] in (0, 1) else 1
    if ns != list(range(first, first + len(units))):
        errs.append(f"unit numbers must be contiguous from 0 or 1, in order (got {ns[:8]}...)")
    by_n = {u.get("n"): u for u in units}
    for u in units:
        m_num = re.search(r"(\d+)", u.get("file", ""))
        if not m_num or int(m_num.group(1)) != u.get("n"):
            errs.append(f"unit {u.get('n')}: the first number in its file name must equal n ({u.get('file')!r})")
    files = [u.get("file", "") for u in units]
    if len(set(files)) != len(files):
        errs.append("duplicate unit file names")
    for u in units:
        if not u.get("file", "").endswith(man["file_suffix"]):
            errs.append(f"unit {u.get('n')}: file {u.get('file')!r} does not end with {man['file_suffix']}")
        pages = u.get("pages") or []
        if not pages:
            if not adopted:
                errs.append(f"unit {u.get('n')}: no pages")
            continue
        missing = [p for p in pages if p not in order]
        if missing:
            errs.append(f"unit {u['n']}: pages not in image index: {missing[:5]}")
            continue
        pos = [order[p] for p in pages]
        if pos != list(range(pos[0], pos[0] + len(pos))):
            errs.append(f"unit {u['n']}: pages not contiguous in index order")

    users = {}
    for u in units:
        for p in u.get("pages") or []:
            users.setdefault(p, []).append(u["n"])
    shared = 0
    for p, us in users.items():
        # A page may hold several short units (e.g. verse sections in a two-column Migne image),
        # but only consecutive ones: [10, 11, 12] is fine, [10, 12] is an error.
        if us != list(range(us[0], us[0] + len(us))):
            errs.append(f"page {p} shared by non-consecutive units: {us}")
        elif len(us) >= 2:
            shared += 1
    if adopted:
        info.append("adopted base: page coverage not required")
    unused = [p["label"] for p in idx if p["label"] not in users]
    info.append(f"{len(units)} units, {len(users)} pages in units ({shared} shared at boundaries), "
                f"{len(unused)} staged page(s) outside any unit")

    try:
        packets = load(os.path.join(src, "run", "packets.json"))["packets"]
        ids = [p["id"] for p in packets]
        if len(set(ids)) != len(ids):
            errs.append("duplicate packet ids")
        seen = {}
        for p in packets:
            for n in p.get("units", []):
                seen.setdefault(n, []).append(p["id"])
            want = sorted({pg for n in p.get("units", []) for pg in (by_n[n].get("pages") or [] if n in by_n else [])},
                          key=lambda x: order.get(x, 10**9))
            if p.get("pages") and sorted(p["pages"], key=lambda x: order.get(x, 10**9)) != want:
                errs.append(f"packet {p['id']}: pages differ from the union of its units' pages")
            subs = p.get("subs") or []
            if subs and [pg for sp in subs for pg in sp.get("pages", [])] != list(p.get("pages", [])):
                errs.append(f"packet {p['id']}: sub-packet pages are not a contiguous split of its pages")
            ids += [sp.get("id") for sp in subs]
        if len(set(ids)) != len(ids):
            errs.append("duplicate packet/sub-packet ids")
        for n in ns:
            if len(seen.get(n, [])) != 1:
                errs.append(f"unit {n} is in {len(seen.get(n, []))} packets (must be exactly 1)")
        info.append(f"{len(packets)} packets")
    except (OSError, json.JSONDecodeError, KeyError) as e:
        errs.append(f"packets.json unreadable: {e}")

    extra = {}
    for u in units:
        for k in u:
            if k not in SCHEMA:
                extra[k] = extra.get(k, 0) + 1
    if extra:
        info.append("info: unit keys outside the schema (not checked): "
                    + ", ".join(f"{k} ({c} units)" for k, c in sorted(extra.items())))

    if a.files:
        ldir = os.path.join(work, man["lang_dir"])
        norm = normalize_fn(man)
        for u in units:
            fp = os.path.join(ldir, u["file"])
            if not os.path.exists(fp):
                errs.append(f"unit {u['n']}: file missing {man['lang_dir']}/{u['file']}")
                continue
            body = read_body(fp)
            if body is None:
                errs.append(f"unit {u['n']}: no ==== separator line")
                continue
            if len(body) < 2:
                errs.append(f"unit {u['n']}: body has fewer than 2 lines")
            elif u.get("heading") and not body[0].strip().startswith(u["heading"]):
                errs.append(f"unit {u['n']}: first body line is not the heading {u['heading']!r}")
            placeholder = any(PLACEHOLDER in l for l in body)
            if placeholder:
                errs.append(f"unit {u['n']}: still contains the Pass-B placeholder (not transcribed)")
            if any("[[JOIN]]" in l for l in body):
                errs.append(f"unit {u['n']}: unjoined [[JOIN]] seam (run packets.py join)")
            if placeholder or len(body) < 2:
                continue  # an unfinished body: its incipit / explicit can't be judged yet
            for f in TEXT_FIELDS:
                prob = u.get(f) and field_problem(norm, u["n"], f, u[f], body)
                if prob:
                    (info if adopted else errs).append(("info: " if adopted else "") + prob)

    for i in info:
        print(i)
    for e in errs:
        print(f"  - {e}")
    print("MANIFEST OK" if not errs else f"MANIFEST ERRORS: {len(errs)}")
    gate.finish(len(errs))


if __name__ == "__main__":
    gate.guard(main)

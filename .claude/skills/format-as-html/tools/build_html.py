#!/usr/bin/env python3
"""Build a work's Writings-Database HTML fragment from its English units and `html_config.py`.

    build_html.py --work-dir W                    build + run every gate; write nothing
    build_html.py --work-dir W --diff             ... and compare with the file already at the target
    build_html.py --work-dir W --out PREVIEW      ... and write a preview copy (no drift check)
    build_html.py --work-dir W --write            write to the target (refuses on drift)
    build_html.py --work-dir W --write --replace  write over a file this skill did not last write

Options: --config PATH (default W/html_config.py), --quiet (gates only).
The last line is `GATE build_html: PASS` or `GATE build_html: FAIL (n problem(s))`; exit 0/1.
"""
import argparse
import datetime
import difflib
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import htmlkit as K  # noqa: E402


def target_paths(cfg, units):
    o = cfg.OUTPUT
    root = os.path.expanduser(o["root"])
    if o.get("mode", "single") == "single":
        return {None: os.path.join(root, o["relpath"])}
    name = o["filename"]
    return {u.n: os.path.join(root, o["reldir"], name(u)) for u in units}


def build(cfg, work_dir):
    """-> (docs {key: html}, report dict). Raises nothing for content problems: they go to gates."""
    gates, adv, log = {}, [], []
    units = K.load_units(work_dir, cfg.SRC_GLOB)
    nums = [u.n for u in units]
    struct_errs = []
    if nums != list(range(nums[0], nums[0] + len(nums))):
        struct_errs.append(f"unit numbers are not contiguous: {nums}")

    # census: every mark character must be declared (footnote text included)
    counts, apos = {}, 0
    for u in units:
        for b in u.blocks:
            text, notes = K.footnote_split(b, cfg.FOOTNOTES)
            for t in [text] + notes:
                c, a = K.census(t)
                apos += a
                for k, v in c.items():
                    counts[k] = counts.get(k, 0) + v
    gates["census"] = [f"mark {k!r} ({v}x) is not declared in MARKS" for k, v in counts.items()
                       if k not in cfg.MARKS]

    unit_items, errs = K.build_items(cfg, units, log)
    gates["structure"] = struct_errs + errs

    state = K.load_json(os.path.join(work_dir, "_source", "run", "state.json")) or {}
    gates["rights"] = []
    if cfg.RELEASE and state.get("base_license") == "copyright" and cfg.RIGHTS_CONFIRMED is not True:
        gates["rights"].append("RELEASE is set but the base edition is in copyright "
                               "(state.json base_license); set RIGHTS_CONFIRMED = True once the user confirms")

    docs, gates["marks"], nnotes = {}, [], 0
    mode = cfg.OUTPUT.get("mode", "single")
    groups = [(None, unit_items)] if mode == "single" else [(u.n, [(u, it)]) for u, it in unit_items]
    for key, group in groups:
        h1 = cfg.H1 if mode == "single" else cfg.H1(group[0][0])
        gunits = [u for u, _ in group]
        try:
            doc, n = K.render_document(cfg, group, h1, gunits)
        except K.BuildError as e:
            gates["marks"].append(str(e))
            continue
        nnotes += n
        docs[key] = doc
        left = sorted({ch for ch in K.MARK_CHARS if ch in re.sub(r"<[^>]+>", "", doc)
                       and cfg.MARKS.get(K.mark_key(ch)) not in ("pass",)} - {"’"})
        if left:
            gates["marks"].append(f"unconverted mark(s) survived: {left}")
        src_spans = 0
        for _, items in group:
            for it in items:
                if it[0] == "p":
                    text, notes = K.footnote_split(it[1], cfg.FOOTNOTES)
                    src_spans += sum(K.italic_spans(t, cfg.MARKS) for t in [text] + notes)
        body = doc.split("\n", 3)[3]                        # after the source note
        if body.count("<i>") != src_spans:
            gates["marks"].append(f"{body.count('<i>')} italic spans in the output, {src_spans} in the source")

    gates["house"], gates["notes"], gates["fidelity"] = [], [], []
    author = getattr(cfg, "AUTHOR", None) or state.get("work", "").split(",")[0] or None
    for key, doc in docs.items():
        e, a = K.gate_house(doc, author)
        gates["house"] += e
        adv += a
        gates["notes"] += K.gate_notes(doc)
        group = unit_items if key is None else [x for x in unit_items if x[0].n == key]
        gates["fidelity"] += K.gate_fidelity(K.expected_stream(cfg, group), K.output_stream(doc))
    report = {"units": units, "items": unit_items, "log": log, "gates": gates, "advisories": adv,
              "notes": nnotes, "apostrophes": apos, "counts": counts}
    return docs, report


def heading_list(doc):
    return [html.unescape(t) for t in re.findall(r"<h[23]>(.*?)</h[23]>", doc)]


def show_diff(old, new, last_build):
    """Print the comparison with the file already at the target."""
    sha_old = K.sha256(old)
    if old == new:
        print("  existing file: identical to this build")
        return "identical"
    if last_build and last_build.get("sha256") == sha_old:
        state = "clean"
        print("  existing file: written by the last build (no hand edits since); this is a re-render")
    elif last_build:
        state = "drift"
        print("  existing file: CHANGED BY HAND since the last build (hash differs from LAST_BUILD)")
    else:
        state = "unknown"
        print("  existing file: not written by this skill (no LAST_BUILD): a first build or a replacement")
    ow, nw = K.output_stream(old), K.output_stream(new)
    ratio = difflib.SequenceMatcher(None, ow, nw, autojunk=False).ratio() if len(ow) < 200000 else 0
    print(f"  words: {len(ow)} -> {len(nw)}   similarity {ratio:.2f}")
    oh, nh = heading_list(old), heading_list(new)
    if oh != nh:
        print(f"  headings old: {', '.join(oh)}")
        print(f"  headings new: {', '.join(nh)}")
    else:
        print(f"  headings: unchanged ({len(nh)})")
    if ratio < 0.6:
        print("  -> a different text (replacement), so no line diff; compare the headings and counts above")
        return state
    shown = 0
    sm = difflib.SequenceMatcher(None, old.splitlines(), new.splitlines(), autojunk=False)
    for tag, a1, a2, b1, b2 in sm.get_opcodes():
        if tag == "equal":
            continue
        olds, news = old.splitlines()[a1:a2], new.splitlines()[b1:b2]
        for k in range(max(len(olds), len(news))):
            ol = olds[k] if k < len(olds) else ""
            nl = news[k] if k < len(news) else ""
            ow_, nw_ = ol.split(), nl.split()
            for t, x1, x2, y1, y2 in difflib.SequenceMatcher(None, ow_, nw_, autojunk=False).get_opcodes():
                if t == "equal":
                    continue
                ctx = " ".join(ow_[max(0, x1 - 5):x1])
                print(f"  line {a1 + k + 1}: …{ctx} [{' '.join(ow_[x1:x2])[:120] or '∅'}] -> "
                      f"[{' '.join(nw_[y1:y2])[:120] or '∅'}]")
                shown += 1
                if shown >= 20:
                    print("  … (diff truncated)")
                    return state
    return state


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--config")
    ap.add_argument("--out", help="write a preview copy here (single-file mode)")
    ap.add_argument("--diff", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--replace", action="store_true", help="with --write: overwrite drift / foreign file")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    work = os.path.abspath(os.path.expanduser(a.work_dir))
    cfg_path = a.config or os.path.join(work, "html_config.py")
    try:
        cfg = K.load_config(cfg_path)
        docs, rep = build(cfg, work)
    except K.BuildError as e:
        print(f"ERROR: {e}")
        print("GATE build_html: FAIL (1 problem(s))")
        sys.exit(1)

    if not a.quiet:
        for u, items in rep["items"]:
            heads = [it[2] for it in items if it[0] == "h"]
            paras = sum(1 for it in items if it[0] == "p")
            print(f"{u.where}  {' / '.join(heads):<28} {paras:>3} paras")
        print(f"\nmarks: {rep['counts']}  apostrophes: {rep['apostrophes']}  footnotes: {rep['notes']}")
        print(f"dropped/stripped ({len(rep['log'])}):")
        for where, what, text in rep["log"]:
            print(f"  {where}: {what}: {text[:60]!r}")
        if rep["advisories"]:
            print(f"advisories ({len(rep['advisories'])}):")
            for x in rep["advisories"]:
                print(f"  {x}")
        print()

    total = 0
    for name in ("census", "structure", "marks", "house", "fidelity", "notes", "rights"):
        errs = rep["gates"].get(name, [])
        total += len(errs)
        for e in errs[:12]:
            print(f"  {name}: {e}")
        print(f"GATE {name}: {'PASS' if not errs else f'FAIL ({len(errs)})'}")

    targets = target_paths(cfg, rep["units"])
    if total == 0 and (a.diff or a.write):
        for key, doc in docs.items():
            path = targets[key]
            print(f"\ntarget: {path}")
            if not os.path.exists(path):
                print("  no file there yet (new)")
                state = "new"
            else:
                state = show_diff(K.read_text(path), doc, cfg.LAST_BUILD)
            if a.write:
                if state in ("drift", "unknown") and not a.replace:
                    print("  REFUSED: the existing file was not written by the last build of this config. "
                          "Show the user the differences, fold wanted hand edits into html_config.py, "
                          "then re-run with --write --replace.")
                    total += 1
                    continue
                if state != "identical":
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "w", encoding="utf-8") as fh:
                        fh.write(doc)
                    print(f"  written ({len(doc):,} chars)")
        if a.write and total == 0 and len(docs) == 1:
            K.set_last_build(cfg_path, K.sha256(next(iter(docs.values()))), datetime.date.today().isoformat())
            print(f"  LAST_BUILD recorded in {cfg_path}")
    if a.out and docs and total == 0:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(next(iter(docs.values())))
        print(f"\npreview written to {a.out}")
    print(f"GATE build_html: {'PASS' if total == 0 else f'FAIL ({total} problem(s))'}")
    sys.exit(0 if total == 0 else 1)


if __name__ == "__main__":
    main()

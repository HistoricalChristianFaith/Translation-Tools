#!/usr/bin/env python3
"""Translate a verified source-language base text into English: the tool half of phase 13.

A translate subagent does the model work, one unit per agent. This tool stands on both sides of it:

  prep      For each unit: parse the source deterministically (common.parse_source: header held
            aside, heading re-emitted from the unit number, held-aside lines replaced by fixed
            English, every other paragraph = one translatable block) and write the bundle
            run/bundles/translate/u<NN>.md: work context, the work's rules (the shared part, first;
            common.shared_bundle), then the unit part with the blocks under numbered `@@ n @@`
            markers. The model never sees headers or held lines.
  assemble  Parse the agent's run/translate/u<NN>.out.txt (the same markers, one English paragraph
            each), check it, and render the English file: a fresh `#` provenance header, `====`,
            the English heading, then the blocks with the held lines back in place.
  --check   Parse-only self test plus an in-memory round trip. Writes nothing.

    python3 translate.py --config CONFIG.py prep [--units 3,8] [--images] [--force [--after-review]]
    python3 translate.py --config CONFIG.py assemble <unit>          # 7, u07 or a file name
    python3 translate.py --config CONFIG.py --check [<source file>] [--summary]
                                                  # ends `GATE translate: PASS|FAIL (<n> problem(s))`

prep skips units whose English exists (unless --force); such a unit gets a `skipped` status
("already translated") only if it has no status and was never bundled, so a `done` status keeps
its counts. For every unit it bundles it first deletes that unit's status, notes and settled
structure warnings, so nothing from an earlier attempt can pass for this one. Without --force it
keeps an existing run/translate/u<NN>.out.txt (the next agent continues it, MODE=retry); with
--force it deletes it and MOVES the English to run/translate/replaced/<stem>.<timestamp>.txt
(never deletes it). Once state.json says `translate` is done, --force refuses (exit 2) unless
--after-review is also given: the English now holds review-round fixes.

assemble exit codes: 0 = English written (WARN lines may be printed); 1 = ERROR lines, nothing
written; 2 = refused (the English was edited after this unit was assembled: re-run prep --force).
"""

import argparse
import datetime
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import gate  # noqa: E402

# Openings a leaked preamble would have. A WARN only: a real sentence can open this way too.
SCAFFOLD_KEYWORDS = (
    "i'll translate", "i will translate", "let me translate", "let me render", "let me produce",
    "i'm going to translate", "i am going to translate", "here is the translat",
    "here's the translat", "here is my translat", "here is the english", "the translated text",
    "translated text:", "preserving all", "preserve all", "paragraph structure", "output only",
    "i must output", "i need to translate", "let me check", "let me look", "looking at the image",
    "consulting the", "the page image",
)
SCAFFOLD_SPAN = 100          # a block "opens with" a phrase found in its first 100 characters
TRUNCATED_RATIO = 0.5        # whole unit: English shorter than this x source = ERROR
MARKER_RE = re.compile(r"^@@ (\d+) @@\s*$")


# --- Paths ------------------------------------------------------------------------------


def paths(cfg, n):
    run, u = C.run_dir(cfg), C.uid(cfg, n)
    src, eng = C.unit_files(cfg)[n]
    return {"src": src, "eng": eng, "uid": u,
            "bundle": os.path.join(run, "bundles", "translate", f"{u}.md"),
            "out": os.path.join(run, "translate", f"{u}.out.txt"),
            "assembled": os.path.join(run, "translate", f"{u}.assembled.json"),
            "replaced": os.path.join(run, "translate", "replaced"),
            "status": os.path.join(run, "status", "translate", f"{u}.json"),
            "notes": os.path.join(run, "notes", "translate", f"{u}.md"),
            "settled": os.path.join(run, "structure_settled", f"{u}.json")}


def image_paths(cfg, n):
    fn = getattr(cfg, "image_paths", None)
    return [p for p in (fn(n) if fn else []) if os.path.exists(p)]


def translatable(slots):
    return [s["text"] for s in slots if s["kind"] == "translate"]


# --- Bundle -----------------------------------------------------------------------------


def bundle_text(cfg, n, blocks, out_path, eng_path, images):
    shared = ["## Work context", C.setting(cfg, "WORK_CONTEXT").strip() or "(none)",
              "", "## Rules for this work", C.setting(cfg, "TRANSLATION_RULES").strip() or "(none)"]
    if images and C.setting(cfg, "IMAGE_RULE").strip():
        shared += ["", "## Page images for this work", C.setting(cfg, "IMAGE_RULE").strip()]
    unit = [f"source_language: {C.setting(cfg, 'SOURCE_LANGUAGE')}",
            f"work: {C.setting(cfg, 'AUTHOR')}, {C.setting(cfg, 'WORK')}",
            f"blocks: {len(blocks)}",
            f"output: {out_path}",
            f"english: {eng_path}",
            "images: " + ("none" if not images else "\n" + "\n".join(f"  {p}" for p in images)),
            "", "## Text", ""]
    for i, b in enumerate(blocks, 1):
        unit += [f"@@ {i} @@", b, ""]
    return C.shared_bundle("Translate", shared, f"{C.unit_label(cfg, n)} (unit {n})", unit)


def write_skipped(p, n):
    C.write_json(p["status"], {"phase": "translate", "packet": p["uid"], "units": [n],
                               "status": "skipped", "reason": "already translated"})


def cmd_prep(cfg, a):
    if a.after_review and not a.force:
        sys.exit("--after-review only goes with --force.")
    if a.force and C.phase_done(cfg, "translate") and not a.after_review:
        print("REFUSED: translate is done, so the English holds review-round fixes. Re-translating "
              "replaces them: add --after-review if that is really intended.")
        sys.exit(2)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bundled, existing, replaced, unfinished, no_images = [], [], [], [], []
    for n in C.parse_units(cfg, a.units):
        p = paths(cfg, n)
        has_en = os.path.exists(p["eng"]) and os.path.getsize(p["eng"]) > 0
        if has_en and not a.force:
            existing.append(p["uid"])
            if not os.path.exists(p["status"]):
                if os.path.exists(p["bundle"]):
                    unfinished.append(p["uid"])  # assembled, but its agent never wrote a status
                else:
                    write_skipped(p, n)
            continue
        C.remove(p["status"], p["notes"], p["settled"], p["assembled"])
        if a.force:
            C.remove(p["out"])
            if os.path.exists(p["eng"]):
                os.makedirs(p["replaced"], exist_ok=True)
                shutil.move(p["eng"], os.path.join(p["replaced"], f"{C.stem(p['eng'])}.{stamp}.txt"))
                replaced.append(p["uid"])
        _, slots = C.parse_source(cfg, C.read(p["src"]))
        images = image_paths(cfg, n) if a.images else []
        if a.images and not images:
            no_images.append(p["uid"])
        C.write(p["bundle"], bundle_text(cfg, n, translatable(slots), p["out"], p["eng"], images))
        bundled.append(p["uid"])
    print("bundled: " + ",".join(bundled))
    print("existing: " + ",".join(existing))
    print("replaced: " + ",".join(replaced))
    if unfinished:
        print("unfinished: " + ",".join(unfinished) + "  (English assembled, no status: dispatch MODE=retry)")
    if no_images:
        print("no page images found for: " + ",".join(no_images))


# --- Assemble ---------------------------------------------------------------------------


def parse_output(text, n_blocks):
    """The agent's output -> (blocks by number, errors, warns). Format: a marker line `@@ n @@`,
    then the block's English (one paragraph; blank lines between blocks are fine)."""
    errors, warns, found, order = [], [], {}, []
    cur, buf = None, []

    def close():
        if cur is None:
            return
        paras = C.paragraphs("\n".join(buf))
        if len(paras) > 1:
            warns.append((cur, f"internal blank lines: {len(paras)} paragraphs collapsed into one"))
        found[cur] = " ".join(" ".join(p.split("\n")) for p in paras).strip()

    for ln in text.split("\n"):
        m = MARKER_RE.match(ln.strip())
        if m:
            close()
            cur, buf = int(m.group(1)), []
            if cur in found or cur in order:
                errors.append((cur, "marker appears more than once"))
            order.append(cur)
            continue
        if cur is None:
            if ln.strip():
                errors.append((None, f"text before the first marker: {ln.strip()[:60]!r}"))
            continue
        buf.append(ln)
    close()

    for k in sorted(set(order)):
        if not 1 <= k <= n_blocks:
            errors.append((k, f"no such block (the source has {n_blocks})"))
    missing = [k for k in range(1, n_blocks + 1) if k not in found]
    for k in missing:
        errors.append((k, "missing"))
    seen = [k for k in order if 1 <= k <= n_blocks]
    if seen != sorted(seen):
        errors.append((None, "markers are out of order"))
    for k, t in found.items():
        if 1 <= k <= n_blocks and not t:
            errors.append((k, "empty block"))
    return found, errors, warns


def check_blocks(cfg, src_blocks, out_blocks):
    """Heuristic per-block checks (WARN) and the whole-unit truncation check (ERROR)."""
    errors, warns = [], []
    src_all, out_all = "\n\n".join(src_blocks), "\n\n".join(out_blocks)
    if len(out_all) < TRUNCATED_RATIO * len(src_all):
        errors.append((None, f"whole unit: English {len(out_all)}c is "
                             f"{len(out_all) / max(len(src_all), 1):.2f}x the source {len(src_all)}c "
                             f"(below {TRUNCATED_RATIO}): looks truncated"))
    floor, min_src = C.setting(cfg, "SHORT_BLOCK_RATIO"), C.setting(cfg, "SHORT_MIN_SOURCE")
    for i, (s, e) in enumerate(zip(src_blocks, out_blocks), 1):
        r = len(e) / len(s) if s else 9.0
        if len(s) >= min_src and r < floor:
            warns.append((i, f"short-ratio {r:.2f}: English {len(e)}c vs source {len(s)}c "
                             f"(floor {floor}): check for a dropped clause"))
        low = e[:SCAFFOLD_SPAN].lower()
        hit = next((k for k in SCAFFOLD_KEYWORDS if k in low), None)
        if hit:
            warns.append((i, f"scaffold: opens with {hit!r}: make sure no preamble leaked"))
        for o, c in C.setting(cfg, "PAIRED_MARKS"):
            if s.count(o) != e.count(o) or s.count(c) != e.count(c):
                warns.append((i, f"marks: {o}{c} {s.count(o)}/{s.count(c)} in the source, "
                                 f"{e.count(o)}/{e.count(c)} in the English"))
    return errors, warns


def default_header(cfg, n):
    return (f"# {C.setting(cfg, 'AUTHOR')}, {C.setting(cfg, 'WORK')} — English translation — "
            f"{C.unit_label(cfg, n)}\n"
            f"# Fresh English rendering from the verified {C.setting(cfg, 'SOURCE_LANGUAGE')} base text.")


def render(cfg, n, slots, translations):
    header_fn = getattr(cfg, "english_header", None)
    header = header_fn(n) if header_fn else default_header(cfg, n)
    parts = []
    heading = C.english_heading(cfg, n)
    if heading:
        parts.append(heading)
    it = iter(translations)
    for s in slots:
        if s["kind"] == "held":
            parts.append(s["en"])
        else:
            parts.append(s["prefix"] + next(it))
    return f"{header}\n{C.setting(cfg, 'SEP_OUT')}\n\n" + "\n\n".join(parts) + "\n"


def assemble_text(cfg, n, slots, out_text):
    """-> (rendered English or None, errors, warns); errors/warns are (block or None, message)."""
    src_blocks = translatable(slots)
    found, errors, warns = parse_output(out_text, len(src_blocks))
    if errors:
        return None, errors, warns
    out_blocks = [found[k] for k in range(1, len(src_blocks) + 1)]
    e2, w2 = check_blocks(cfg, src_blocks, out_blocks)
    errors, warns = errors + e2, warns + w2
    return (None if errors else render(cfg, n, slots, out_blocks)), errors, warns


def print_issues(level, issues):
    for b, msg in sorted(issues, key=lambda x: (x[0] is not None, x[0] or 0)):
        print(f"{level} {'block ' + str(b) if b is not None else 'unit'}: {msg}")


def cmd_assemble(cfg, a):
    n = C.resolve_unit(cfg, a.unit)
    if n not in C.unit_files(cfg):
        sys.exit(f"No source file for unit {n}.")
    p = paths(cfg, n)
    if not os.path.exists(p["out"]):
        print(f"ERROR unit: no output file {p['out']}")
        sys.exit(1)
    if os.path.exists(p["eng"]):
        rec = C.read_json(p["assembled"], {})
        if rec.get("english_sha256") != C.sha256(C.read(p["eng"])):
            print(f"REFUSED: {p['eng']} exists and was not written by this unit's last assemble "
                  f"(edited since, or translated earlier). Re-translating needs `prep --force`.")
            sys.exit(2)
    _, slots = C.parse_source(cfg, C.read(p["src"]))
    english, errors, warns = assemble_text(cfg, n, slots, C.read(p["out"]))
    print_issues("ERROR", errors)
    print_issues("WARN", warns)
    if errors:
        print(f"{p['uid']}: {len(errors)} error(s), nothing written. Fix the blocks named above.")
        sys.exit(1)
    C.write(p["eng"], english)
    C.write_json(p["assembled"], {"english_sha256": C.sha256(english), "at": C.now()})
    print(f"{p['uid']}: English written -> {p['eng']} ({len(translatable(slots))} blocks, "
          f"{len(warns)} warning(s))")


# --- Check ------------------------------------------------------------------------------


def check_files(cfg, files, summary=False):
    """Parse-only self test, plus an in-memory round trip through the bundle, the assemble parser
    and the renderer (the source blocks stand in for the agent's output). Writes nothing.
    -> the number of files with a problem. `summary`: print only those files and the totals."""
    ok, total, bad = True, 0, 0
    for f in files:
        n = C.unit_number(cfg, f)
        _, slots = C.parse_source(cfg, C.read(f))
        blocks = translatable(slots)
        held = len(slots) - len(blocks)
        joined = "\n\n".join(blocks)
        balanced = C.marks_ok(cfg, joined)
        trip = "no blocks"
        if blocks and n is not None:
            text = bundle_text(cfg, n, blocks, "<out>", "<english>", [])
            fake = text[text.index("## Text\n") + len("## Text\n"):]
            english, errors, _ = assemble_text(cfg, n, slots, fake)
            trip = "; ".join(m for _, m in errors) or None
            if english is not None:
                all_b, content = C.english_content_blocks(cfg, n, english)
                exp = len(slots) + (1 if C.english_heading(cfg, n) else 0)
                held_ok = all(content[i] == s["en"] for i, s in enumerate(slots)
                              if s["kind"] == "held" and i < len(content))
                if len(all_b) != exp:
                    trip = f"round trip: {len(all_b)} English blocks vs {exp} expected"
                elif not held_ok:
                    trip = "round trip: held lines moved"
        status = "OK" if (balanced and n is not None and blocks and trip is None) else "PROBLEM"
        ok = ok and status == "OK"
        bad += status != "OK"
        total += len(blocks)
        if status != "OK" or not summary:
            print(f"  {os.path.basename(f)}: {len(blocks)} block(s), {held} held | "
                  f"{C.marks_summary(cfg, joined)}  [{status}]" + (f"  {trip}" if trip else ""))
    print(f"\n  TOTAL: {len(files)} file(s), {total} translatable blocks. "
          f"{'Round-trip OK.' if ok else 'PROBLEMS -- see above.'}")
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("cmd", nargs="?", help="prep | assemble (or, with --check, a source file)")
    ap.add_argument("unit", nargs="?")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--summary", action="store_true", help="with --check: only problem files and the totals")
    ap.add_argument("--units", help="comma list of unit numbers, u<NN> ids or batch ids")
    ap.add_argument("--images", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--after-review", action="store_true")
    a = ap.parse_args()
    if a.check:
        gate.arm("translate")
    cfg = C.load_config(a.config)
    if a.check:
        files = C.collect(cfg, a.cmd, cfg.SOURCE_DIR, C.setting(cfg, "SOURCE_SUFFIX"))
        if not files:
            sys.exit("No source files found.")
        gate.finish(check_files(cfg, files, a.summary))
    if a.cmd == "prep":
        cmd_prep(cfg, a)
    elif a.cmd == "assemble":
        if not a.unit:
            sys.exit("usage: translate.py --config C assemble <unit>")
        cmd_assemble(cfg, a)
    else:
        ap.error("give a subcommand (prep, assemble) or --check")


if __name__ == "__main__":
    gate.guard(main)

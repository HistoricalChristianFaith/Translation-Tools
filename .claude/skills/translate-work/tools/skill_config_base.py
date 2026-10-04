"""Mechanical config settings for a /translate-work project, derived from its manifest.

The configure agent writes `<work>/_source/run/work_config.py` as:

    import os, sys
    sys.path.insert(0, "<TOOLS_DIR>")
    import skill_config_base as B
    globals().update(B.defaults("<WORK_DIR>"))
    # ... then only the judgement parts: WORK_CONTEXT, TRANSLATION_RULES,
    #     VALIDATION_HOUSE_RULES, GRADING_CAVEATS, ORACLE_LABEL/SHORT, ORACLE_NOTES,
    #     ENDING_CHECKS, HELD_LINES, and optionally heading_en / english_header overrides.

`defaults()` returns: paths, file suffixes, SLUG, SOURCE_LANGUAGE, UNIT_NOUN, AUTHOR, WORK,
BODY_HEADING_RE (built from the manifest's unit headings), ANCHOR_RE, PAIRED_MARKS, EVEN_MARKS,
EVEN_MARK_EXEMPT_RE, UNIT_META (run/unit_meta.json, else manifest `passage`), SHORT_BLOCK_RATIO,
heading_en(n) (the unit's `label_en`, else its `label`, upper-cased with a final period),
english_header(n), image_paths(n) (from the base image index), oracle_text(n) (from
_source/oracle/extracts/unitNN.txt), and ORACLE_COVERED (the units that have an extract).
"""

import json
import os
import re


def _load(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def defaults(work_dir):
    work = os.path.abspath(work_dir)
    src = os.path.join(work, "_source")
    run = os.path.join(src, "run")
    man = _load(os.path.join(run, "manifest.json"))
    state = _load(os.path.join(run, "state.json"), {})
    if man is None:
        raise SystemExit(f"no manifest at {run}/manifest.json")
    units = {u["n"]: u for u in man["units"]}
    meta = {int(k): v for k, v in (_load(os.path.join(run, "unit_meta.json"), {}) or {}).items()}
    for n, u in units.items():
        meta.setdefault(n, u.get("passage") or "")
    author, _, work_title = state.get("work", man.get("work", "")).partition(",")
    checks = man.get("checks", {})
    pairs = []
    for p in checks.get("pairs", ["»«"]):
        pairs.append(tuple(p) if isinstance(p, list) else (p[0], p[1]))
    headings = sorted({u["heading"] for u in units.values() if u.get("heading")}, key=len, reverse=True)
    idx = _load(os.path.join(src, man.get("base_images", "pages/base"), "index.json"), {"pages": []})
    files = {p["label"]: os.path.join(src, p["file"]) for p in idx.get("pages", [])}
    extracts = os.path.join(src, "oracle", "extracts")
    covered = set()
    if os.path.isdir(extracts):
        for f in os.listdir(extracts):
            m = re.match(r"unit(\d+)\.txt$", f)
            if m and os.path.getsize(os.path.join(extracts, f)) > 0:
                covered.add(int(m.group(1)))

    def heading_en(n):
        u = units.get(n, {})
        if u.get("label_en"):
            return u["label_en"]
        label = u.get("label") or f"{man.get('unit_noun', 'unit')} {n}"
        return label.upper().rstrip(".") + "."

    def english_header(n):
        m = meta.get(n)
        return (f"# {author.strip()}, *{work_title.strip()}* — English translation — {units.get(n, {}).get('label', n)}"
                + (f" ({m})" if m else "") + "\n"
                f"# Source text: {state.get('base', 'the verified base text')} — the verified reading text "
                f"(built from the page images through passes B, R2, R4, R1, R3, R5, R6, R7).\n"
                f"# Scripture is rendered in the author's own wording and numbering.")

    def image_paths(n):
        out = []
        for label in units.get(n, {}).get("pages", []):
            p = files.get(label)
            if p and os.path.exists(p):
                out.append(p)
        return out

    def oracle_text(n):
        p = os.path.join(extracts, f"unit{n:02d}.txt")
        if os.path.exists(p) and os.path.getsize(p) > 0:
            return open(p, encoding="utf-8").read()
        return None

    lang = man.get("language", "Latin")
    return {
        "SLUG": re.sub(r"[^a-z0-9]+", "-", state.get("work", os.path.basename(work)).lower()).strip("-"),
        "AUTHOR": author.strip() or "the author",
        "WORK": work_title.strip() or os.path.basename(work),
        "SOURCE_LANGUAGE": lang,
        "UNIT_NOUN": man.get("unit_noun", "unit").capitalize(),
        "PROJECT": work,
        "SOURCE_DIR": os.path.join(work, man["lang_dir"]),
        "TARGET_DIR": os.path.join(work, "english"),
        "SOURCE_SUFFIX": man["file_suffix"],
        "TARGET_SUFFIX": "_english.txt",
        "UNIT_NUMBER_RE": r"(\d+)",
        "BODY_HEADING_RE": ("^(?:" + "|".join(re.escape(h) for h in headings) + r")\s*$") if headings else None,
        "ANCHOR_RE": man.get("anchor", {}).get("regex"),
        "PAIRED_MARKS": pairs,
        "EVEN_MARKS": checks.get("even", ["*"]) or [],
        "EVEN_MARK_EXEMPT_RE": checks.get("even_exempt"),
        "UNIT_META": meta,
        "SHORT_BLOCK_RATIO": 0.55 if lang.lower().startswith("greek") else 0.70,
        "SHORT_MIN_SOURCE": 200,
        "IMAGE_DIR": os.path.join(src, man.get("base_images", "pages/base")),
        "ORACLE_COVERED": covered or None,
        "heading_en": heading_en,
        "english_header": english_header,
        "image_paths": image_paths,
        "oracle_text": oracle_text,
    }

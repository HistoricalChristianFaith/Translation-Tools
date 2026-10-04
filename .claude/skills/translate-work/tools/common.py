"""Shared helpers for the config-driven translate / validate / grade tools.

Everything work-specific (paths, parsing quirks, markup, prompt rules, oracle location) lives in a
per-work config file -- see `work_config_template.py`. The three tools load that file with
`--config path/to/config.py` and read its settings through `setting()` (falling back to DEFAULTS).

The tools never call a model. In a /translate-work run subagents do the model work, and the tools
stand on both sides of each one: they prepare a self-contained bundle, and they check the file
the agent wrote (the agent loops until the check passes). What the tools guarantee:

  * deterministic parsing of the source file into ordered "slots" (translatable blocks and
    held-aside lines), so the model never sees headers and can never corrupt a unit number;
  * a structural fingerprint (numbered block markers) checked on every translation;
  * mark-balance invariants (» «, * *, …) used both as soft checks and as auto-fix guards.
"""

import datetime
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))

# Settings of the retired headless path. A config that still sets them keeps loading (ignored).
RETIRED = ("CLAUDE_CMD", "CLAUDE_TIMEOUT", "MODEL")

DEFAULTS = {
    # identity / prompt context
    "AUTHOR": "the author",
    "WORK": "the work",
    "SOURCE_LANGUAGE": "Latin",
    "WORK_CONTEXT": "",
    "UNIT_NOUN": "unit",
    # files
    "SOURCE_SUFFIX": "_latin.txt",
    "TARGET_SUFFIX": "_english.txt",
    "UNIT_NUMBER_RE": r"(\d+)",
    # parsing
    "FRONT_SEPARATOR_RE": r"^={5,}\s*$",
    "HEADER_LEMMA_RE": None,
    "HEADER_LEMMA_OUT_PREFIX": "LEMMA: ",
    "BODY_HEADING_RE": None,
    "HELD_LINES": [],
    "ANCHOR_RE": None,
    # output
    "SEP_OUT": "=" * 66,
    # marks
    "PAIRED_MARKS": [("»", "«")],
    "EVEN_MARKS": ["*"],
    "EVEN_MARK_EXEMPT_RE": None,
    # work-specific rules (the generic ones live in the phase files)
    "TRANSLATION_RULES": "",
    "VALIDATION_HOUSE_RULES": "",
    "GRADING_CAVEATS": "",
    "IMAGE_RULE": "",  # optional work-specific page-image guidance (the generic rule is in 13_translate.md)
    # structure check
    "SHORT_BLOCK_RATIO": 0.70,
    "SHORT_MIN_SOURCE": 200,
    "ENDING_CHECKS": [],
    # oracle
    "ORACLE_LABEL": "the reference translation",
    "ORACLE_SHORT": "Oracle",
    "ORACLE_NOTES": {},
    "ORACLE_COVERED": None,
    # display
    "UNIT_META": {},
}


# --- Config -------------------------------------------------------------------


def load_config(path):
    """Import a per-work config file as a module."""
    path = os.path.abspath(path)
    if not os.path.exists(path):
        sys.exit(f"Config not found: {path}")
    spec = importlib.util.spec_from_file_location("work_config", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for required in ("SOURCE_DIR", "TARGET_DIR", "SLUG"):
        if not hasattr(mod, required):
            sys.exit(f"Config {path} must define {required}.")
    retired = [k for k in RETIRED if hasattr(mod, k)]
    if retired:
        print(f"note: {os.path.basename(path)} sets {', '.join(retired)}: no longer used (ignored).",
              file=sys.stderr)
    return mod


def setting(cfg, name):
    return getattr(cfg, name, DEFAULTS.get(name))


def run_dir(cfg):
    """`<PROJECT>/_source/run` of a /translate-work run (configs built on skill_config_base)."""
    project = getattr(cfg, "PROJECT", None)
    if not project:
        sys.exit("This command needs a /translate-work run config (PROJECT is not set).")
    return os.path.join(project, "_source", "run")


def phase_done(cfg, phase):
    st = read_json(os.path.join(run_dir(cfg), "state.json"), {})
    return st.get("phases", {}).get(phase, {}).get("status") == "done"


# --- Files --------------------------------------------------------------------


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write(path, text):
    """Atomic: a crash leaves the old file or the new one, never half of one."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = f"{path}.tmp{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def write_json(path, obj):
    write(path, json.dumps(obj, indent=1, ensure_ascii=False) + "\n")


def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def remove(*paths):
    for p in paths:
        if os.path.exists(p):
            os.remove(p)


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def stem(path):
    return os.path.splitext(os.path.basename(path))[0]


def unit_number(cfg, path):
    m = re.search(setting(cfg, "UNIT_NUMBER_RE"), os.path.basename(path))
    return int(m.group(1)) if m else None


def collect(cfg, arg, default_dir, suffix):
    """Resolve a CLI argument (bare filename, path, directory, or None) to a sorted file list."""
    if arg is None:
        path = default_dir
    elif os.path.isabs(arg) or os.sep in arg:
        path = arg
    else:
        path = os.path.join(default_dir, arg)
    if not os.path.exists(path):
        sys.exit(f"Input not found: {path}")
    if os.path.isdir(path):
        files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(suffix)]
        return sorted(files, key=lambda p: (unit_number(cfg, p) is None, unit_number(cfg, p) or 0, p))
    return [path]


def target_path_for(cfg, source_file):
    name = os.path.basename(source_file)
    name = name[: -len(setting(cfg, "SOURCE_SUFFIX"))] + setting(cfg, "TARGET_SUFFIX")
    return os.path.join(cfg.TARGET_DIR, name)


def source_path_for(cfg, target_file):
    name = os.path.basename(target_file)
    name = name[: -len(setting(cfg, "TARGET_SUFFIX"))] + setting(cfg, "SOURCE_SUFFIX")
    return os.path.join(cfg.SOURCE_DIR, name)


# --- Units ----------------------------------------------------------------------


def unit_files(cfg):
    """{unit number: (source file, English file)} for every source file in SOURCE_DIR."""
    srcs = collect(cfg, None, cfg.SOURCE_DIR, setting(cfg, "SOURCE_SUFFIX"))
    return {unit_number(cfg, s): (s, target_path_for(cfg, s)) for s in srcs if unit_number(cfg, s) is not None}


def resolve_unit(cfg, arg):
    """A unit given as `7`, `u07`, a file name (source or English, `.txt` optional) or a path."""
    m = re.fullmatch(r"u?(\d+)", arg.strip())
    if m:
        return int(m.group(1))
    n = unit_number(cfg, os.path.basename(arg))
    if n is None:
        sys.exit(f"Not a unit: {arg}")
    return n


def parse_units(cfg, spec):
    """`--units 3,8` (or u03,u08, or batch ids u012-u017) -> sorted unit numbers; None, "" or
    "all" -> every unit."""
    files = unit_files(cfg)
    if not spec or spec == "all":
        return sorted(files)
    wanted = set()
    for x in (t.strip() for t in spec.split(",")):
        m = re.fullmatch(r"u?(\d+)-u?(\d+)", x)
        if m:
            wanted.update(range(int(m.group(1)), int(m.group(2)) + 1))
        elif x:
            wanted.add(resolve_unit(cfg, x))
    wanted = sorted(wanted)
    unknown = [n for n in wanted if n not in files]
    if unknown:
        sys.exit(f"No source file for unit(s) {unknown}.")
    return wanted


def uid(cfg, n):
    """Per-unit dispatch id: `u` + the number zero-padded to 2 digits, or to the width of the
    highest unit number (same rule as packets.uid)."""
    width = max(2, len(str(max(unit_files(cfg), default=0))))
    return f"u{n:0{width}d}"


def unit_label(cfg, n):
    meta = setting(cfg, "UNIT_META").get(n)
    noun = setting(cfg, "UNIT_NOUN")
    return f"{noun} {n}" + (f" ({meta})" if meta else "")


# --- Roman numerals -------------------------------------------------------------

_ROMAN = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
          (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def roman(n):
    out = []
    for val, sym in _ROMAN:
        while n >= val:
            out.append(sym)
            n -= val
    return "".join(out)


# --- Source parsing -------------------------------------------------------------


def strip_anchors(cfg, text):
    """Defensively remove any residual page anchors (normally already gone after pass R7)."""
    pattern = setting(cfg, "ANCHOR_RE")
    if not pattern:
        return text
    text = re.sub(pattern, "", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return "\n".join(line.rstrip() for line in text.split("\n"))


def parse_source(cfg, raw):
    """Split a source file into ordered slots.

    Layout assumed (true of every base text this workflow produced): a header block ending in a
    `====` separator line, then a body in which every paragraph is ONE physical line (blank-line
    usage between them is irrelevant). Returns (header_lines, slots) where each slot is
      {"kind": "translate", "text": ..., "prefix": ""}      -- sent to the model
      {"kind": "held", "text": ..., "en": ...}               -- replaced by fixed English
    A header LEMMA (HEADER_LEMMA_RE) becomes the first translatable slot with an output prefix.
    Leading body lines matching BODY_HEADING_RE are dropped (the English heading is re-emitted
    from the filename number by the config's heading_en()).
    """
    raw = strip_anchors(cfg, raw)
    lines = raw.split("\n")
    sep_re = re.compile(setting(cfg, "FRONT_SEPARATOR_RE"))
    sep_idx = next((i for i, l in enumerate(lines) if sep_re.match(l)), None)
    header = lines[:sep_idx] if sep_idx is not None else []
    body = lines[sep_idx + 1:] if sep_idx is not None else lines

    slots = []
    lemma_re = setting(cfg, "HEADER_LEMMA_RE")
    if lemma_re:
        for l in header:
            m = re.match(lemma_re, l)
            if m and m.group(1).strip():
                slots.append({"kind": "translate", "text": m.group(1).strip(),
                              "prefix": setting(cfg, "HEADER_LEMMA_OUT_PREFIX")})
                break

    heading_re = setting(cfg, "BODY_HEADING_RE")
    held = [(re.compile(p), en) for p, en in setting(cfg, "HELD_LINES")]
    seen_content = False
    for l in body:
        s = l.strip()
        if not s:
            continue
        if not seen_content and heading_re and re.match(heading_re, s):
            continue
        seen_content = True
        hit = next((en for rx, en in held if rx.match(s)), None)
        if hit is not None:
            slots.append({"kind": "held", "text": s, "en": hit})
        else:
            slots.append({"kind": "translate", "text": s, "prefix": ""})
    return header, slots


def paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def english_body(raw):
    """English reading body: drop the leading `#` provenance header and `=` separator."""
    out, started = [], False
    for ln in raw.split("\n"):
        s = ln.strip()
        if not started and (s.startswith("#") or re.match(r"^=+$", s) or s == ""):
            continue
        started = True
        out.append(ln)
    return "\n".join(out).strip()


def english_heading(cfg, n):
    fn = getattr(cfg, "heading_en", None)
    return fn(n) if fn else None


def english_content_blocks(cfg, n, eng_raw):
    """English paragraphs aligned 1:1 with the source slots (the heading paragraph removed)."""
    blocks = paragraphs(english_body(eng_raw))
    lead = 1 if (english_heading(cfg, n) and blocks) else 0
    return blocks, blocks[lead:]


# --- Marks ----------------------------------------------------------------------


def mark_counts(cfg, text):
    exempt = setting(cfg, "EVEN_MARK_EXEMPT_RE")
    stripped = re.sub(exempt, "", text) if exempt else text
    counts = {}
    for o, c in setting(cfg, "PAIRED_MARKS"):
        counts[f"{o}{c}"] = (text.count(o), text.count(c))
    for m in setting(cfg, "EVEN_MARKS"):
        counts[m] = (stripped.count(m),)
    return counts


def marks_ok(cfg, text):
    """Paired marks balanced and even marks even (after removing exempt occurrences)."""
    for key, val in mark_counts(cfg, text).items():
        if len(val) == 2 and val[0] != val[1]:
            return False
        if len(val) == 1 and val[0] % 2:
            return False
    return True


def marks_summary(cfg, text):
    return " ".join(f"{k}={'/'.join(str(x) for x in v)}" for k, v in mark_counts(cfg, text).items())


# --- Scores ---------------------------------------------------------------------


def letter_for(score):
    if score is None:
        return "?"
    for cut, letter in ((97, "A+"), (93, "A"), (90, "A-"), (87, "B+"), (83, "B"), (80, "B-"),
                        (77, "C+"), (73, "C"), (70, "C-"), (67, "D+"), (63, "D"), (60, "D-")):
        if score >= cut:
            return letter
    return "F"


def clamp_score(value):
    try:
        return max(0, min(100, int(round(float(value)))))
    except (TypeError, ValueError):
        return None


SEV_ORDER = {"significant": 0, "moderate": 1, "minor": 2}
SEV_TAG = {"significant": "!!", "moderate": "! ", "minor": ". "}


# --- Findings files (validate / grade scans) -------------------------------------


def findings_path(cfg, phase, eng_file):
    return os.path.join(run_dir(cfg), "findings", phase, f"{stem(eng_file)}.json")


def bundle_path(cfg, phase, n):
    return os.path.join(run_dir(cfg), "bundles", phase, f"{uid(cfg, n)}.md")


def shared_bundle(kind, shared_lines, unit_title, unit_lines):
    """A bundle whose sections shared by every unit of the phase (work context, rules, …) come
    first, so an agent working a batch of units reads them once: line 1 names their hash and the
    line where this unit's own part starts; that part repeats the hash on its second line. Two
    bundles with the same hash have the same shared text, so their unit parts start on the same
    line."""
    shared = "\n".join(shared_lines).strip("\n")
    h = sha256(shared)[:12]
    start = shared.count("\n") + 4  # line 1 + the shared lines + one blank line
    head = (f"# {kind} bundle, shared part (sha {h}): lines 1-{start - 1}, identical in every bundle "
            f"with this sha. This unit's part starts at line {start}.")
    return "\n".join([head, shared, "", f"# Unit part: {unit_title}", f"shared: {h}"] + unit_lines)


def bundled_units(cfg, phase):
    """Units the last `bundle --phase <phase>` bundled (run/bundles/<phase>/units.json)."""
    return read_json(os.path.join(run_dir(cfg), "bundles", phase, "units.json"), {}).get("bundled")


def clean_scan_slate(cfg, phase, n, eng_file):
    """Delete every earlier file of this unit for round `phase`, so a re-run can never read an
    earlier attempt's findings, journal, status or notes as its own."""
    run, u = run_dir(cfg), uid(cfg, n)
    f = findings_path(cfg, phase, eng_file)
    remove(f, f[: -len(".json")] + ".apply.json",
           os.path.join(run, "status", f"{phase}-scan", f"{u}.json"),
           os.path.join(run, "notes", f"{phase}-scan", f"{u}.md"))


def check_schema(obj, spec):
    """Validate a findings object against spec = {"enums": {field: set}, "list": name,
    "item_required": [...], "item_enums": {field: set}}. Returns a list of problems."""
    probs = []
    if not isinstance(obj, dict):
        return ["the file is not one JSON object"]
    score = obj.get("score")
    if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 100:
        probs.append(f"score: a number 0-100 is required (got {score!r})")
    if not isinstance(obj.get("grade"), str) or not obj.get("grade"):
        probs.append("grade: a letter grade string is required")
    for k, allowed in spec["enums"].items():
        if obj.get(k) not in allowed:
            probs.append(f"{k}: one of {sorted(allowed)} (got {obj.get(k)!r})")
    if not isinstance(obj.get("summary"), str):
        probs.append("summary: a string is required")
    items = obj.get(spec["list"])
    if not isinstance(items, list):
        return probs + [f"{spec['list']}: a list is required"]
    for i, d in enumerate(items, 1):
        where = f"{spec['list']}[{i}]"
        if not isinstance(d, dict):
            probs.append(f"{where}: an object is required")
            continue
        for k in spec["item_required"]:
            if not isinstance(d.get(k), str) or (k in spec.get("item_nonempty", ()) and not d[k].strip()):
                probs.append(f"{where}.{k}: a {'non-empty ' if k in spec.get('item_nonempty', ()) else ''}string is required")
        for k, allowed in spec["item_enums"].items():
            if d.get(k) not in allowed:
                probs.append(f"{where}.{k}: one of {sorted(allowed)} (got {d.get(k)!r})")
    return probs


def print_score_table(title, rows, mean_label):
    """rows: (name, status-or-None, grade dict, extra text). Today's end-of-run summary format."""
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")
    scores = []
    for name, status, g, extra in rows:
        if status:
            print(f"  {name:32} {status.upper()}")
            continue
        if g["score"] is not None:
            scores.append(g["score"])
        print(f"  {name:32} {g['grade']:>2} {g['score'] if g['score'] is not None else '--':>3}/100 {extra}")
    if scores:
        avg = sum(scores) / len(scores)
        print(f"\n  {mean_label}: {avg:.1f}/100 ({letter_for(round(avg))}) over {len(scores)} unit(s).")


# --- Oracle helpers (used from config files) -------------------------------------------


def oracle_from_file(path):
    """Oracle text from a pre-extracted per-unit text file, or None if absent/empty."""
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return read(path)
    return None


def oracle_from_pdf_pages(pdf, first_page, last_page, cache):
    """Oracle text for a 1-based inclusive PDF page range via `pdftotext`, cached to `cache`."""
    cached = oracle_from_file(cache)
    if cached:
        return cached
    if not os.path.exists(pdf):
        print(f"    Oracle PDF not found: {pdf}")
        return None
    try:
        os.makedirs(os.path.dirname(cache) or ".", exist_ok=True)
        subprocess.run(["pdftotext", "-layout", "-f", str(first_page), "-l", str(last_page), pdf, cache],
                       check=True, capture_output=True, text=True)
    except FileNotFoundError:
        print("    `pdftotext` not on PATH (install poppler).")
        return None
    except subprocess.CalledProcessError as e:
        print(f"    pdftotext failed: {e.stderr.strip()[:160]}")
        return None
    return oracle_from_file(cache)

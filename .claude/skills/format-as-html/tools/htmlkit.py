"""Shared library for /format-as-html: read a work's English units, render them to a
Writings-Database HTML fragment from a per-work config (`html_config.py`), and run the gates.

The renderer and the checks are deliberately separate code paths: `render_inline` builds HTML,
`plain_expected` independently computes the text the HTML must contain, and the `fidelity` gate
compares the two as one word stream (headings, the source note and footnote markers excluded).

Config helpers that a `html_config.py` may import: `verse_heading`, `book_heading`,
`label_heading`, `verse_coverage`.
"""
import difflib
import hashlib
import html
import importlib.util
import json
import os
import re
import sys
from html.parser import HTMLParser

SEP_RE = re.compile(r"^={5,}\s*$", re.M)
PAIRS = {"»": "«", "“": "”", "‘": "’", "‹": "›", "⟨": "⟩", "[": "]"}
CLOSERS = {v: k for k, v in PAIRS.items()}
EVEN = ("*", "†", "‖")
MARK_KEYS = ["*", "†", "‖"] + [o + c for o, c in PAIRS.items()]
MARK_CHARS = set("".join(MARK_KEYS))
MODES = ("italic", "quote", "straight", "strip", "pass")
RELEASE_SENTENCES = {"public-domain": "This English translation is released into the public domain."}
ALLOWED_TAGS = {"article", "h1", "h2", "h3", "i", "b", "br", "sup", "a", "section", "hr", "span"}
FORBIDDEN_TAGS = {"p", "html", "head", "body", "title", "script", "style", "div"}
FN_OPEN, FN_CLOSE = "\ue000", "\ue001"
ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
WORDS = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
         "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen",
         "Nineteen", "Twenty"]


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class BuildError(Exception):
    """A problem that stops the build; the message names the file and quotes a snippet."""


# ----------------------------------------------------------------------------------- units

class Unit:
    def __init__(self, n, path, header, blocks, passage=None, pages=None):
        self.n, self.path, self.header, self.blocks = n, path, header, blocks
        self.passage, self.pages = passage, pages or []
        self.where = os.path.basename(path).split("_")[0]

    @property
    def first_block(self):
        return self.blocks[0] if self.blocks else ""

    def __repr__(self):
        return f"Unit({self.n}, {self.where}, passage={self.passage!r})"


def unit_number(path):
    m = re.search(r"(\d+)(?=_[^/]*$)", os.path.basename(path)) or re.search(r"(\d+)", os.path.basename(path))
    if not m:
        raise BuildError(f"{os.path.basename(path)}: no unit number in the file name")
    return int(m.group(1))


def read_unit(path):
    """`#` header lines, a `====` rule, then blank-line-separated blocks (whitespace kept as is)."""
    text = read_text(path)
    parts = SEP_RE.split(text, maxsplit=1)
    if len(parts) != 2:
        raise BuildError(f"{os.path.basename(path)}: no ==== rule between header and body")
    header = [l[1:].strip() for l in parts[0].strip().splitlines() if l.startswith("#")]
    blocks = [b.strip() for b in re.split(r"\n\s*\n", parts[1]) if b.strip()]
    if not blocks:
        raise BuildError(f"{os.path.basename(path)}: empty body")
    return header, blocks


HEADER_PASSAGE_RE = re.compile(r":\s*([A-Z][A-Za-z]*\.?\s+\d[\d:\-–ab, ]*?)\s*(?:\(|$)")
HEADER_PAGES_RE = re.compile(r"\b(pp?|cols?)\.\s*(\d+)(?:\s*[–\-]\s*(\d+))?")


def load_units(work_dir, src_glob):
    import glob
    files = sorted(glob.glob(os.path.join(work_dir, src_glob)), key=unit_number)
    if not files:
        raise BuildError(f"no English files match {src_glob!r} under {work_dir}")
    man = load_json(os.path.join(work_dir, "_source", "run", "manifest.json")) or {}
    by_n = {u["n"]: u for u in man.get("units", [])}
    units = []
    for p in files:
        n = unit_number(p)
        header, blocks = read_unit(p)
        mu = by_n.get(n)
        if mu:
            passage, pages = mu.get("passage"), [str(x) for x in mu.get("pages", [])]
        else:
            m = HEADER_PASSAGE_RE.search(header[0]) if header else None
            passage = m.group(1).strip() if m else None
            if not passage and header and re.search(r"—\s*Prologue\b", header[0]):
                passage = "Prologue"
            pm = next((HEADER_PAGES_RE.search(h) for h in header if HEADER_PAGES_RE.search(h)), None)
            pages = [pm.group(2), pm.group(3) or pm.group(2)] if pm else []
        units.append(Unit(n, p, header, blocks, passage, pages))
    if man.get("units") and len(units) != len(by_n):
        raise BuildError(f"{len(units)} English files but {len(by_n)} manifest units")
    return units


def load_json(path):
    try:
        return json.loads(read_text(path))
    except (OSError, ValueError):
        return None


# ------------------------------------------------------------------------------ config

DEFAULTS = {
    "SRC_GLOB": "english/*_english.txt",
    "OUTPUT": None,
    "H1": None,
    "SOURCE_NOTE": None,
    "RELEASE": None,
    "RIGHTS_CONFIRMED": False,
    "DROP_FIRST_BLOCK": None,
    "CHECK_LABEL": None,
    "UNIT_HEADINGS": None,
    "BLOCK_LABELS": None,
    "STRIP_PREFIX": [],
    "KEEP_PREFIX": [],
    "MARKS": {},
    "APOSTROPHE": "'",
    "FOOTNOTES": None,
    "COVERAGE": None,
    "EXCEPTIONS": {},
    "LAST_BUILD": None,
}


class Config:
    def __init__(self, path, module):
        self.path = path
        for k, v in DEFAULTS.items():
            setattr(self, k, getattr(module, k, v))


def load_config(path):
    tools = os.path.dirname(os.path.abspath(__file__))
    if tools not in sys.path:
        sys.path.insert(0, tools)
    spec = importlib.util.spec_from_file_location("html_config", path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except FileNotFoundError:
        raise BuildError(f"no config at {path} (run draft_config.py first)")
    cfg = Config(path, mod)
    problems = []
    if not cfg.OUTPUT or "root" not in cfg.OUTPUT:
        problems.append("OUTPUT must give 'root' and 'relpath' (single) or 'reldir' (folder)")
    if not cfg.H1:
        problems.append("H1 is not set")
    if not cfg.SOURCE_NOTE or "TODO" in str(cfg.SOURCE_NOTE):
        problems.append("SOURCE_NOTE is missing or still has a TODO")
    if not callable(cfg.UNIT_HEADINGS):
        problems.append("UNIT_HEADINGS must be a function unit -> [(level, text)]")
    for key, mode in cfg.MARKS.items():
        if key not in MARK_KEYS:
            problems.append(f"MARKS key {key!r} is not a known mark ({' '.join(MARK_KEYS)})")
        elif mode not in MODES:
            problems.append(f"MARKS[{key!r}] = {mode!r}: set it to one of {', '.join(MODES)}")
    if cfg.RELEASE and cfg.RELEASE not in RELEASE_SENTENCES:
        problems.append(f"RELEASE must be None or one of {list(RELEASE_SENTENCES)}")
    if problems:
        raise BuildError(f"{path}:\n  " + "\n  ".join(problems))
    return cfg


def set_last_build(cfg_path, sha, date):
    """Rewrite (or append) the single `LAST_BUILD = {...}` line of a config."""
    line = f'LAST_BUILD = {{"sha256": "{sha}", "date": "{date}"}}   # written by build_html.py --write'
    text = read_text(cfg_path)
    if re.search(r"^LAST_BUILD\s*=.*$", text, re.M):
        text = re.sub(r"^LAST_BUILD\s*=.*$", line, text, count=1, flags=re.M)
    else:
        text = text.rstrip("\n") + "\n\n" + line + "\n"
    with open(cfg_path, "w", encoding="utf-8") as fh:
        fh.write(text)


# ----------------------------------------------------------------------- heading helpers

SPAN_RE = re.compile(r"(\d+)([ab]?)(?:\s*[-–]\s*(\d+)([ab]?))?\s*$")


def parse_span(text):
    """`Obad 12-13a` / `12–13a` / `7` -> ((12, ''), (13, 'a')), or None."""
    m = SPAN_RE.search(text or "")
    if not m:
        return None
    first = (int(m.group(1)), m.group(2))
    last = (int(m.group(3)), m.group(4)) if m.group(3) else first
    return (first, last) if last >= first else None


def verse_heading(chapter=1, special=None, level=2):
    """Unit heading from the manifest passage: `Obad 12-13a` -> [(2, '1:12-13a')].
    `special` maps a passage (e.g. 'Prologue') to a fixed heading text."""
    special = {"Prologue": "Prologue", **(special or {})}

    def fn(unit):
        if unit.passage in special:
            return [(level, special[unit.passage])]
        span = parse_span(unit.passage)
        if not span:
            raise BuildError(f"{unit.where}: cannot read a verse span from passage {unit.passage!r}")
        (a, ap), (b, bp) = span
        body = f"{a}{ap}" if span[0] == span[1] else f"{a}{ap}-{b}{bp}"
        return [(level, f"{chapter}:{body}")]
    return fn


def roman_to_int(s):
    total = 0
    for i, ch in enumerate(s):
        v = ROMAN[ch]
        total += -v if i + 1 < len(s) and ROMAN[s[i + 1]] > v else v
    return total


def book_heading(noun="Book", level=2, special=None):
    """Unit heading from the first block `BOOK IV.` -> [(2, 'Book Four')]."""
    special = {"PROLOGUE.": "Prologue", **(special or {})}

    def fn(unit):
        fb = unit.first_block
        if fb in special:
            return [(level, special[fb])]
        m = re.match(rf"^{noun.upper()} ([IVXLC]+)\.$", fb)
        if not m:
            raise BuildError(f"{unit.where}: first block {fb[:40]!r} is not '{noun.upper()} N.'")
        k = roman_to_int(m.group(1))
        return [(level, f"{noun} {WORDS[k] if k < len(WORDS) else k}")]
    return fn


def label_heading(level=2):
    """Unit heading = the run's English label from the header (`… — Homily 3 (…)` -> 'Homily 3')."""
    def fn(unit):
        line = unit.header[0] if unit.header else ""
        m = re.search(r"—\s*([^—(]+?)\s*(?:\(|$)", line.split("English translation")[-1])
        if not m:
            raise BuildError(f"{unit.where}: no label in header line {line[:60]!r}")
        return [(level, m.group(1).rstrip(":").strip())]
    return fn


def verse_coverage(first, last):
    """COVERAGE helper: the units with a verse passage run on from `first` to `last`, with no gap
    and no overlap (`12-13a` then `13b-14`)."""
    def follows(prev, nxt):
        if prev[1] == "a":
            return nxt == (prev[0], "b")
        return nxt in ((prev[0] + 1, ""), (prev[0] + 1, "a"))

    def fn(units):
        errs, prev = [], (first - 1, "")
        for u in units:
            span = parse_span(u.passage)
            if not span:
                continue
            if not follows(prev, span[0]):
                errs.append(f"{u.where}: passage {u.passage!r} does not follow on from verse {prev[0]}{prev[1]}")
            prev = span[1]
        if prev != (last, ""):
            errs.append(f"the last verse section ends at {prev[0]}{prev[1]}, not {last}")
        return errs
    return fn


LABEL_SPAN_RE = re.compile(r"^\(Verses? ([\d–\-ab ,]+?)\.?\)$")


# --------------------------------------------------------------------------- structure

def build_items(cfg, units, log):
    """units -> list of (unit, items); items are ('h', level, text) / ('p', source_text).
    Every dropped or stripped piece of source text goes into `log`."""
    errs, out = [], []
    drop_re = re.compile(cfg.DROP_FIRST_BLOCK) if cfg.DROP_FIRST_BLOCK else None
    prefixes = [re.compile(p) for p in cfg.STRIP_PREFIX]
    keep = {tuple(k) for k in cfg.KEEP_PREFIX}
    bl = cfg.BLOCK_LABELS or {}
    bl_re = re.compile(bl["regex"]) if bl.get("regex") else None
    runon_re = re.compile(bl["split_runon"]) if bl.get("split_runon") else None
    for u in units:
        items = []
        try:
            items += [("h", lvl, txt) for lvl, txt in cfg.UNIT_HEADINGS(u)]
        except BuildError as e:
            errs.append(str(e))
            continue
        blocks = list(enumerate(u.blocks))
        if drop_re:
            idx, fb = blocks[0]
            if not drop_re.match(fb):
                errs.append(f"{u.where}: first block does not match DROP_FIRST_BLOCK: {fb[:50]!r}")
            log.append((u.where, "dropped first block", fb))
            blocks = blocks[1:]
            if cfg.CHECK_LABEL == "passage":
                lm = LABEL_SPAN_RE.match(fb)
                if lm and parse_span(lm.group(1)) != parse_span(u.passage):
                    errs.append(f"{u.where}: label {fb!r} disagrees with passage {u.passage!r}")
        ctx = {}
        for idx, b in blocks:
            pieces = [b]
            if runon_re:
                cuts = [m.start() for m in runon_re.finditer(b) if m.start() > 0]
                pieces, start = [], 0
                for c in cuts:
                    pieces.append(b[start:c].strip())
                    log.append((u.where, "split a run-on label out of block", b[c:c + 40]))
                    start = c
                pieces.append(b[start:].strip())
            for piece in pieces:
                if bl_re and bl_re.match(piece):
                    m = bl_re.match(piece)
                    try:
                        lvl, txt = bl["heading"](m, ctx)
                    except BuildError as e:
                        errs.append(f"{u.where}: {e}")
                        continue
                    items.append(("h", lvl, txt))
                    log.append((u.where, "label -> heading", m.group(0).strip()))
                    piece = piece[m.end():].strip()
                    if not piece:
                        continue
                if (u.n, idx) not in keep:
                    for pre in prefixes:
                        pm = pre.match(piece)
                        if pm:
                            if re.search(r"[A-Za-z]{2,}", pm.group(0)):
                                errs.append(f"{u.where}: STRIP_PREFIX would remove words: {pm.group(0)!r}")
                            log.append((u.where, f"stripped prefix (block {idx})", pm.group(0).strip()))
                            piece = piece[pm.end():]
                            break
                items.append(("p", piece))
        # a run of headings must end in reading text
        for k, it in enumerate(items):
            if it[0] == "h" and (k + 1 == len(items)):
                errs.append(f"{u.where}: heading {it[2]!r} has no reading text")
        if not any(it[0] == "p" for it in items):
            errs.append(f"{u.where}: no reading text")
        out.append((u, items))
    if callable(cfg.COVERAGE):
        errs += cfg.COVERAGE(units)
    return out, errs


# ------------------------------------------------------------------------------ marks

def is_apostrophe(text, i):
    """`’` inside a word (Esau’s, don’t) is an apostrophe; after a plural s (the prophets’ words)
    it is one too, unless a `‘` is still open before it (then it closes that quote)."""
    if text[i] != "’":
        return False
    before = text[i - 1] if i > 0 else " "
    after = text[i + 1] if i + 1 < len(text) else " "
    if before.isalpha() and after.isalpha():
        return True
    if before in "sS" and not after.isalpha():
        head = text[:i]
        inword = len(re.findall(r"(?<=[^\W\d_])’(?=[^\W\d_])", head))
        return head.count("‘") <= head.count("’") - inword
    return False


def mark_key(ch):
    if ch in EVEN:
        return ch
    if ch in PAIRS:
        return ch + PAIRS[ch]
    if ch in CLOSERS:
        return CLOSERS[ch] + ch
    return None


def census(text):
    """Count mark characters by MARKS key; `’` apostrophes are counted apart."""
    counts, apostrophes = {}, 0
    for i, ch in enumerate(text):
        if ch not in MARK_CHARS:
            continue
        if is_apostrophe(text, i):
            apostrophes += 1
            continue
        k = mark_key(ch)
        counts[k] = counts.get(k, 0) + 1
    return counts, apostrophes


def italic_spans(text, marks):
    """How many <i> spans the marks of `text` should give."""
    n = 0
    for key, mode in marks.items():
        if mode != "italic":
            continue
        if len(key) == 1:
            n += text.count(key) // 2
        else:
            n += text.count(key[0])
    return n


def footnote_split(text, fcfg):
    """Replace footnote matches by placeholders; return (text, [note texts])."""
    if not fcfg:
        return text, []
    notes = []
    pat = re.compile(r"\s*(?:" + fcfg["regex"] + ")")

    def sub(m):
        body = m.group(1) if m.lastindex else m.group(0).strip()
        notes.append(body)
        return f"{FN_OPEN}{len(notes)}{FN_CLOSE}"
    return pat.sub(sub, text), notes


def render_inline(text, marks, apostrophe="'", where=""):
    """Collapse whitespace, escape, convert marks. Raises BuildError on bad pairing."""
    text = html.escape(" ".join(text.split()), quote=False)
    out, stack = [], []          # stack of (key, mode)
    qdepth = 0
    for i, ch in enumerate(text):
        if ch not in MARK_CHARS:
            out.append(ch)
            continue
        if is_apostrophe(text, i):
            out.append(apostrophe)
            continue
        key = mark_key(ch)
        mode = marks.get(key)
        if mode is None:
            raise BuildError(f"{where}: undeclared mark {ch!r} in: {text[max(0, i - 30):i + 30]!r}")
        if mode == "pass":
            out.append(ch)
            continue
        if mode == "straight":
            out.append('"' if ch in "“”" else "'" if ch in "‘’" else ch)
            continue
        opening = (ch in PAIRS) or (ch in EVEN and not (stack and stack[-1][0] == key))
        if opening:
            if any(k == key for k, _ in stack) or (mode == "italic" and any(m == "italic" for _, m in stack)):
                raise BuildError(f"{where}: nested {ch!r} in: {text[max(0, i - 30):i + 30]!r}")
            stack.append((key, mode))
            if mode == "italic":
                out.append("<i>")
            elif mode == "quote":
                out.append('"' if qdepth % 2 == 0 else "'")
                qdepth += 1
        else:
            if not stack or stack[-1][0] != key:
                raise BuildError(f"{where}: {ch!r} closes nothing (or crosses another mark) in: "
                                 f"{text[max(0, i - 30):i + 30]!r}")
            stack.pop()
            if mode == "italic":
                out.append("</i>")
            elif mode == "quote":
                qdepth -= 1
                out.append('"' if qdepth % 2 == 0 else "'")
    if stack:
        raise BuildError(f"{where}: unclosed {stack[-1][0]!r} in: {text[:80]!r}")
    return "".join(out)


def plain_expected(text, marks, apostrophe="'"):
    """Independent of render_inline: the plain text the rendered HTML must show (quotes normalized
    to `"`, so nesting depth is not compared)."""
    out = []
    for i, ch in enumerate(text):
        if ch in MARK_CHARS and not is_apostrophe(text, i):
            mode = marks.get(mark_key(ch))
            if mode in ("italic", "strip"):
                continue
            if mode in ("quote", "straight"):
                out.append('"')
                continue
            out.append(ch)
        elif ch == "’":
            out.append(apostrophe)
        else:
            out.append(ch)
    return " ".join("".join(out).replace("'", '"').split())


# ------------------------------------------------------------------------------- render

def note_html(cfg, unit_pages_from, unit_pages_to):
    note = cfg.SOURCE_NOTE
    pages = (f"p. {unit_pages_from}" if unit_pages_from == unit_pages_to
             else f"pp. {unit_pages_from}–{unit_pages_to}")
    cols = (f"col. {unit_pages_from}" if unit_pages_from == unit_pages_to
            else f"cols. {unit_pages_from}–{unit_pages_to}")
    note = note.replace("{pages}", pages).replace("{cols}", cols)
    if cfg.RELEASE:
        note = note.rstrip() + " " + RELEASE_SENTENCES[cfg.RELEASE]
    return f"<i>{note}</i><br><br>"


def page_range(units):
    nums = [p for u in units for p in u.pages if str(p).isdigit()]
    if not nums:
        return "", ""
    nums = sorted(int(p) for p in nums)
    return nums[0], nums[-1]


def render_document(cfg, unit_items, h1, units_for_pages):
    """One HTML fragment from [(unit, items)]. Returns (doc, notes_count)."""
    out = ['<article class="writing">', f"<h1>{html.escape(h1, quote=False)}</h1>",
           note_html(cfg, *page_range(units_for_pages))]
    all_notes = []
    for u, items in unit_items:
        for it in items:
            if it[0] == "h":
                out.append(f"<h{it[1]}>{html.escape(it[2], quote=False)}</h{it[1]}>")
                continue
            text, notes = footnote_split(it[1], cfg.FOOTNOTES)
            base = len(all_notes)
            rendered = render_inline(text, cfg.MARKS, cfg.APOSTROPHE, u.where)
            for k, _ in enumerate(notes, 1):
                n = base + k
                rendered = rendered.replace(f"{FN_OPEN}{k}{FN_CLOSE}",
                                            f'<sup><a href="#fn{n}" id="r{n}">{n}</a></sup>', 1)
            all_notes += [(u.where, t) for t in notes]
            out.append(f"{rendered}<br><br>")
    if all_notes:
        out += ['<section class="notes">', "<hr>"]
        style = (cfg.FOOTNOTES or {}).get("style") or (lambda s: s)
        for n, (where, t) in enumerate(all_notes, 1):
            body = style(render_inline(t, cfg.MARKS, cfg.APOSTROPHE, where))
            out.append(f'<span id="fn{n}"><a href="#r{n}">{n}</a>&nbsp;{body}</span><br>')
        out.append("</section>")
    out += ["</article>", ""]
    return "\n".join(out), len(all_notes)


def expected_stream(cfg, unit_items):
    """Words the body must contain, in order: paragraphs, then footnote texts."""
    words, notes = [], []
    for u, items in unit_items:
        for it in items:
            if it[0] == "p":
                text, ns = footnote_split(it[1], cfg.FOOTNOTES)
                text = re.sub(f"{FN_OPEN}\\d+{FN_CLOSE}", "", text)
                words += plain_expected(text, cfg.MARKS, cfg.APOSTROPHE).split()
                notes += ns
    for t in notes:
        words += plain_expected(t, cfg.MARKS, cfg.APOSTROPHE).split()
    return words


def output_stream(doc):
    """Body words of a fragment: no headings, no source note, no footnote markers or numbers."""
    words = []
    for k, line in enumerate(doc.splitlines()):
        s = line.strip()
        if not s or s.startswith(("<article", "</article", "<h1", "<h2", "<h3", "<section", "</section", "<hr")):
            continue
        if k == 2 and s.startswith("<i>"):          # the source note
            continue
        s = re.sub(r"<sup>.*?</sup>", "", s)
        s = re.sub(r'^<span id="fn\d+"><a href="#r\d+">\d+</a>&nbsp;', "", s)
        s = html.unescape(re.sub(r"<[^>]+>", "", s))
        words += " ".join(s.replace("'", '"').split()).split()
    return words


# -------------------------------------------------------------------------------- gates

class TagCheck(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errors, self.h1 = [], [], 0

    def handle_starttag(self, tag, attrs):
        if tag in FORBIDDEN_TAGS:
            self.errors.append(f"forbidden <{tag}> at line {self.getpos()[0]}")
        elif tag not in ALLOWED_TAGS:
            self.errors.append(f"tag <{tag}> not in the house whitelist (line {self.getpos()[0]})")
        if tag == "h1":
            self.h1 += 1
        if tag not in ("br", "hr"):
            self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        self.errors.append(f"self-closing <{tag}/> at line {self.getpos()[0]} (use <{tag}>)")

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1][0] != tag:
            self.errors.append(f"</{tag}> at line {self.getpos()[0]} does not close "
                               f"{self.stack[-1] if self.stack else 'anything'}")
        else:
            self.stack.pop()


def gate_house(doc, author=None):
    """House format (Writings-Database/CLAUDE.md). Returns (errors, advisories)."""
    p = TagCheck()
    p.feed(doc)
    errs = list(p.errors)
    errs += [f"unclosed <{t}> from line {ln}" for t, ln in p.stack]
    if p.h1 != 1:
        errs.append(f"{p.h1} <h1> elements (need exactly 1)")
    lines = doc.rstrip("\n").splitlines()
    if not lines or lines[0] != '<article class="writing">' or lines[-1] != "</article>":
        errs.append('the fragment must start with <article class="writing"> and end with </article>')
    in_notes = False
    for k, line in enumerate(lines[1:-1], 2):
        s = line.strip()
        if s == '<section class="notes">':
            in_notes = True
            continue
        if s == "</section>":
            in_notes = False
            continue
        if re.fullmatch(r"<h[123]>.*</h[123]>", s) or s == "<hr>":
            continue
        if in_notes:
            if not re.fullmatch(r'<span id="fn\d+"><a href="#r\d+">\d+</a>&nbsp;.*</span><br>', s):
                errs.append(f"line {k}: malformed footnote line: {s[:60]!r}")
            continue
        if not s.endswith("<br><br>"):
            errs.append(f"line {k}: paragraph does not end with <br><br>: {s[-40:]!r}")
    adv = []
    h1 = re.search(r"<h1>(.*?)</h1>", doc)
    if author and h1 and author.split()[0].lower() in h1.group(1).lower():
        adv.append(f"<h1> contains the author's name ({h1.group(1)!r}); the house rule omits it")
    return errs, adv


def gate_notes(doc):
    refs = re.findall(r'<sup><a href="#fn(\d+)" id="r(\d+)">(\d+)</a></sup>', doc)
    defs = re.findall(r'<span id="fn(\d+)"><a href="#r(\d+)">(\d+)</a>', doc)
    errs = []
    if [int(r[0]) for r in refs] != list(range(1, len(refs) + 1)):
        errs.append("footnote references are not numbered 1..k in document order")
    if any(len(set(r)) != 1 for r in refs + defs):
        errs.append("a footnote link is not two-way (number, href and id disagree)")
    if [int(d[0]) for d in defs] != [int(r[0]) for r in refs]:
        errs.append(f"{len(refs)} references but definitions {[d[0] for d in defs]}")
    return errs


def gate_fidelity(expected, got):
    if expected == got:
        return []
    sm = difflib.SequenceMatcher(None, expected, got, autojunk=False)
    errs = []
    for tag, a1, a2, b1, b2 in sm.get_opcodes():
        if tag == "equal":
            continue
        ctx = " ".join(expected[max(0, a1 - 6):a1])
        errs.append(f"{tag}: after …{ctx!r}: source {' '.join(expected[a1:a2])[:80]!r} -> "
                    f"output {' '.join(got[b1:b2])[:80]!r}")
        if len(errs) >= 5:
            errs.append("…")
            break
    return errs


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

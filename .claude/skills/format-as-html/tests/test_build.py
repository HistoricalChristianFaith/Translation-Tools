#!/usr/bin/env python3
"""Tests for /format-as-html. Synthetic fixtures only (no real translation text in this repo).

    python3 -m unittest discover -s .claude/skills/format-as-html/tests -v

1. Differential: a synthetic 13-unit work in the Obadiah layout is rendered by the frozen legacy
   script (tests/legacy_scripts/) and by build_html.py with an equivalent config: byte-identical.
2. Negative fixtures: each defect fails the right gate.
3. Library units: apostrophes, quote nesting, footnotes, block labels, the house checker.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, "..", "tools")
LEGACY = os.path.join(HERE, "legacy_scripts", "build_jerome_obadiah_html.py")
sys.path.insert(0, TOOLS)
import htmlkit as K  # noqa: E402

# the 13 units of the Obadiah layout: (label in header, passage, first block)
SPANS = [("Verse 1", "1", None), ("Verses 2–4", "2-4", "(Verses 2–4.)"),
         ("Verses 5–6", "5-6", "(Verses 5–6.)"), ("Verse 7", "7", "(Verse 7.)"),
         ("Verses 8–9", "8-9", "(Verses 8–9.)"), ("Verses 10–11", "10-11", "(Verses 10–11.)"),
         ("Verses 12–13a", "12-13a", "(Verses 12–13a.)"), ("Verses 13b–14", "13b-14", "(Verses 13b–14.)"),
         ("Verses 15–16", "15-16", "(Verses 15–16.)"), ("Verses 17–18", "17-18", "(Verses 17–18.)"),
         ("Verse 19", "19", "(Verse 19.)"), ("Verses 20–21", "20-21", "(Verses 20–21.)")]
HEAD2 = "# Source text: Synthetic edition, CCSL 76 (Turnhout: Brepols, 1969), pp. {a}–{b} — test fixture."


def write_unit(d, n, line1, page_a, page_b, blocks):
    with open(os.path.join(d, f"section{n:02d}_english.txt"), "w", encoding="utf-8") as fh:
        fh.write(f"# Test, *Work* — English translation — {line1}\n{HEAD2.format(a=page_a, b=page_b)}\n"
                 f"# Third header line.\n{'=' * 66}\n\n" + "\n\n".join(blocks) + "\n")


def make_work(root, mutate=None):
    """A synthetic work folder with english/ (no _source/run: passages come from the headers)."""
    work = os.path.join(root, "Test Author", "Test Work")
    eng = os.path.join(work, "english")
    os.makedirs(eng)
    units = {0: ("Prologue (a preface)", 349, 351,
                 ["PROLOGUE.", "»When I was a child« I spoke — and *not* as a child; Tom & Jerry < 3 "
                  "said φερωνύμως (true to his name)."])}
    page = 352
    for k, (label, passage, first) in enumerate(SPANS, 1):
        lead = passage.replace("-", ".") + "."
        body = [f"{lead} *The lemma of {label}.* LXX: *The other lemma.* Text with »Scripture "
                f"quoted« and the word *lemma* again, then more prose about {label}."]
        if k == 7:
            body.append("13. *A second lemma inside the unit.* Further exposition.")
        blocks = (["HERE BEGINS THE BOOK."] if first is None else [first]) + body
        units[k] = (f"{label}: Obad. {passage} (summary)", page, page + 1, blocks)
        page += 2
    if mutate:
        mutate(units)
    for n, (line1, a, b, blocks) in units.items():
        write_unit(eng, n, line1, a, b, blocks)
    return work


def legacy_note():
    import importlib.util
    spec = importlib.util.spec_from_file_location("legacy_obadiah", LEGACY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    tmpl = mod.SOURCE_TMPL
    tail = " This English translation is released into the public domain.</i><br><br>"
    assert tmpl.startswith("<i>") and tmpl.endswith(tail)
    return tmpl[3:-len(tail)]


def write_config(work, root, **over):
    fields = {
        "OUTPUT": {"mode": "single", "root": root, "relpath": "Test Author/Test Work.html"},
        "H1": "Commentary on Obadiah",
        "SOURCE_NOTE": legacy_note(),
        "RELEASE": "public-domain",
        "RIGHTS_CONFIRMED": True,
        "DROP_FIRST_BLOCK": r"^(?:[A-Z][A-Z .,]+\.|\((?:Verses?|Chapter|Book|Homily)\b[^)]*\))$",
        "CHECK_LABEL": "passage",
        "STRIP_PREFIX": [r"^\d+(?:[./]\d+)*\.\s+(?=\S)"],
        "MARKS": {"*": "italic", "»«": "italic"},
    }
    fields.update(over)
    lines = ["from htmlkit import verse_heading, verse_coverage",
             "UNIT_HEADINGS = verse_heading(chapter=1)", "COVERAGE = verse_coverage(1, 21)"]
    lines += [f"{k} = {v!r}" for k, v in fields.items()]
    path = os.path.join(work, "html_config.py")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


def run(*args):
    p = subprocess.run([sys.executable, *args], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def build(self, work, *extra):
        return run(os.path.join(TOOLS, "build_html.py"), "--work-dir", work, "--quiet", *extra)


class Differential(Base):
    def test_legacy_obadiah_byte_identical(self):
        work = make_work(self.tmp)
        old = os.path.join(self.tmp, "old.html")
        code, out = run(LEGACY, "--src", os.path.join(work, "english"), "--out", old)
        self.assertEqual(code, 0, out)
        write_config(work, self.tmp)
        new = os.path.join(self.tmp, "new.html")
        code, out = self.build(work, "--out", new)
        self.assertEqual(code, 0, out)
        self.assertEqual(K.read_text(old), K.read_text(new))

    def test_write_then_drift_refusal(self):
        work = make_work(self.tmp)
        cfg = write_config(work, self.tmp)
        code, out = self.build(work, "--write")
        self.assertEqual(code, 0, out)
        self.assertIn("LAST_BUILD", K.read_text(cfg))
        target = os.path.join(self.tmp, "Test Author", "Test Work.html")
        with open(target, "a", encoding="utf-8") as fh:     # a hand edit
            fh.write("<!-- edited -->\n")
        code, out = self.build(work, "--write")
        self.assertEqual(code, 1, out)
        self.assertIn("CHANGED BY HAND", out)
        self.assertIn("REFUSED", out)
        code, out = self.build(work, "--write", "--replace")
        self.assertEqual(code, 0, out)


class Negative(Base):
    def gate_fails(self, out, gate):
        self.assertRegex(out, rf"GATE {gate}: FAIL", out)

    def test_undeclared_mark(self):
        work = make_work(self.tmp, lambda u: u[3][3].__setitem__(1, u[3][3][1] + " ‹odd›"))
        write_config(work, self.tmp)
        code, out = self.build(work)
        self.assertEqual(code, 1)
        self.gate_fails(out, "census")

    def test_unpaired_guillemet(self):
        work = make_work(self.tmp, lambda u: u[4][3].__setitem__(1, u[4][3][1] + " »open"))
        write_config(work, self.tmp)
        code, out = self.build(work)
        self.assertEqual(code, 1)
        self.gate_fails(out, "marks")

    def test_label_disagrees_with_passage(self):
        work = make_work(self.tmp, lambda u: u[5][3].__setitem__(0, "(Verses 8–10.)"))
        write_config(work, self.tmp)
        code, out = self.build(work)
        self.assertEqual(code, 1)
        self.gate_fails(out, "structure")

    def test_missing_unit(self):
        work = make_work(self.tmp, lambda u: u.pop(6))
        write_config(work, self.tmp)
        code, out = self.build(work)
        self.assertEqual(code, 1)
        self.gate_fails(out, "structure")

    def test_rights_with_copyright_base(self):
        work = make_work(self.tmp)
        os.makedirs(os.path.join(work, "_source", "run"))
        with open(os.path.join(work, "_source", "run", "state.json"), "w") as fh:
            json.dump({"base_license": "copyright"}, fh)
        write_config(work, self.tmp, RIGHTS_CONFIRMED=False)
        code, out = self.build(work)
        self.assertEqual(code, 1)
        self.gate_fails(out, "rights")

    def test_unset_mark_and_todo_note_refused(self):
        work = make_work(self.tmp)
        write_config(work, self.tmp, MARKS={"*": None, "»«": "italic"}, SOURCE_NOTE="TODO")
        code, out = self.build(work)
        self.assertEqual(code, 1)
        self.assertIn("MARKS['*'] = None", out)
        self.assertIn("TODO", out)

    def test_fidelity_catches_a_dropped_word(self):
        work = make_work(self.tmp)
        cfg = K.load_config(write_config(work, self.tmp))
        units = K.load_units(work, cfg.SRC_GLOB)
        items, errs = K.build_items(cfg, units, [])
        self.assertEqual(errs, [])
        doc, _ = K.render_document(cfg, items, cfg.H1, units)
        exp = K.expected_stream(cfg, items)
        self.assertEqual(K.gate_fidelity(exp, K.output_stream(doc)), [])
        broken = doc.replace("Further exposition.", "Further.", 1)
        self.assertTrue(K.gate_fidelity(exp, K.output_stream(broken)))

    def test_prefix_that_would_eat_words(self):
        work = make_work(self.tmp)
        write_config(work, self.tmp, STRIP_PREFIX=[r"^\S+ \S+ \S+\s"])
        code, out = self.build(work)
        self.assertEqual(code, 1)
        self.gate_fails(out, "structure")


class Library(unittest.TestCase):
    def test_apostrophes(self):
        t = "Esau’s house; the prophets’ words; ‘a quote’ here"
        self.assertEqual([i for i, c in enumerate(t) if c == "’" and K.is_apostrophe(t, i)], [4, 26])
        self.assertEqual(K.render_inline(t, {"‘’": "quote"}), "Esau's house; the prophets' words; \"a quote\" here")

    def test_quote_nesting(self):
        out = K.render_inline("»He said: “go” now«", {"»«": "quote", "“”": "quote"})
        self.assertEqual(out, "\"He said: 'go' now\"")

    def test_italic_inside_italic_rejected(self):
        with self.assertRaises(K.BuildError):
            K.render_inline("*a »b« c*", {"*": "italic", "»«": "italic"})

    def test_footnotes(self):
        class C:
            FOOTNOTES = {"regex": r"\[note: ([^\]]+)\]"}
            MARKS = {"*": "italic"}
            APOSTROPHE = "'"
            SOURCE_NOTE = "Note."
            RELEASE = None
        u = K.Unit(0, "/x/section00_english.txt", [], ["A [note: first] b *c* [note: *second*]."])
        doc, n = K.render_document(C, [(u, [("p", u.blocks[0])])], "T", [u])
        self.assertEqual(n, 2)
        self.assertIn('A<sup><a href="#fn1" id="r1">1</a></sup> b', doc)
        self.assertIn('<span id="fn2"><a href="#r2">2</a>&nbsp;<i>second</i></span><br>', doc)
        self.assertEqual(K.gate_notes(doc), [])
        self.assertEqual(K.gate_house(doc)[0], [])
        self.assertEqual(K.gate_fidelity(K.expected_stream(C, [(u, [("p", u.blocks[0])])]),
                                         K.output_stream(doc)), [])

    def test_block_labels_with_runon(self):
        def head(m, ctx):
            if m.group(1):
                ctx["ch"] = int(m.group(1))
            return 2, f"{ctx['ch']}:{m.group(2)}"

        class C:
            DROP_FIRST_BLOCK, CHECK_LABEL, STRIP_PREFIX, KEEP_PREFIX, COVERAGE = r"^BOOK I\.$", None, [], [], None
            BLOCK_LABELS = {"regex": r"^\((?:Chapter (\d+) — )?Verse (\d+)\)\s*",
                            "heading": head, "split_runon": r"\(Chapter \d+ — Verse \d+\)"}
            UNIT_HEADINGS = staticmethod(lambda u: [(2, "Book One")])
        u = K.Unit(1, "/x/book01_english.txt", [], ["BOOK I.", "Preface.", "(Chapter 1 — Verse 1) Text one.",
                                                    "(Verse 2) Text two. (Chapter 2 — Verse 1) Text three."])
        log = []
        items, errs = K.build_items(C, [u], log)
        self.assertEqual(errs, [])
        heads = [it[2] for it in items[0][1] if it[0] == "h"]
        self.assertEqual(heads, ["Book One", "1:1", "1:2", "2:1"])
        self.assertTrue(any("run-on" in x[1] for x in log))

    def test_house_checker_on_old_style_page(self):
        old = ('<script src="https://x/highlight.js"></script>\n<h1>Origen, Homily 1</h1>\n'
               "<p>Text</p>\n")
        errs, adv = K.gate_house(old, "Origen of Alexandria")
        self.assertTrue(any("script" in e for e in errs))
        self.assertTrue(any("<p>" in e for e in errs))
        self.assertTrue(any("article" in e for e in errs))
        self.assertTrue(adv)


if __name__ == "__main__":
    unittest.main()

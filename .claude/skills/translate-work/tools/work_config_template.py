"""Per-work configuration for tools/translate.py, tools/validate.py and tools/grade.py.

In a /translate-work run the configure phase writes `_source/run/work_config.py` on top of
`skill_config_base.defaults()`; this template documents every setting. The tools never call a
model: translate, validate and grade subagents do the model work (phases 13, 14a, 15a), and the
tools prepare their bundles and check their output:

    python3 tools/translate.py --config CONFIG.py --check                # parse + round-trip test, free
    python3 tools/translate.py --config CONFIG.py prep                   # translate bundles
    python3 tools/validate.py  --config CONFIG.py --structure-only       # free structure check
    python3 tools/validate.py  --config CONFIG.py bundle --phase validate   # a validate round's bundles
    python3 tools/grade.py     --config CONFIG.py bundle --phase grade      # a grade round's bundles

The round subcommands (bundle, check-findings, apply, summary) need a run config (PROJECT).

Everything below marked ADAPT is work-specific. Settings you omit fall back to
tools/common.py DEFAULTS. Worked examples: examples/configs/leviticus.py (continuous Latin
homilies) and examples/configs/1corinthians.py (Greek catena fragments).

The rule text you put here (it goes into every bundle) is the single most important lever on
quality. Write it from what the base-text passes taught you: the markup the base still carries,
the names and vocabulary to keep consistent, the scripture-numbering system, the deliberate
irregularities that must NOT be "fixed", and every crux already settled in the reports (so the
validator does not re-flag it).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import common as C  # noqa: E402  (roman(), oracle_from_file(), oracle_from_pdf_pages())

# --- Identity --------------------------------------------------------------------------
SLUG = "author-work"                       # ADAPT: a short id for the work
AUTHOR = "Origen of Alexandria"            # ADAPT
WORK = "Homilies on X"                     # ADAPT
SOURCE_LANGUAGE = "Latin"                  # ADAPT: "Latin" | "Greek" | ...
UNIT_NOUN = "Homily"                       # ADAPT: "Homily" | "Fragment" | "Chapter" ...
WORK_CONTEXT = (                           # ADAPT: 2-5 sentences that go into every bundle
    "The base is the constituted reading text of <edition>, transcribed from the page images and "
    "verified through the refinement passes. <What the work is, how it survives, what it expounds.>"
)

# --- Paths -----------------------------------------------------------------------------
PROJECT = "/path/to/Writings-Database-Non-English/<Author>/<Work>"   # ADAPT
SOURCE_DIR = os.path.join(PROJECT, "LATIN")        # the final (post-R7) base text, one file per unit
TARGET_DIR = os.path.join(PROJECT, "english")      # English output, one file per unit
SOURCE_SUFFIX = "_latin.txt"                       # homily01_latin.txt -> homily01_english.txt
TARGET_SUFFIX = "_english.txt"
UNIT_NUMBER_RE = r"(\d+)"                          # first number in the filename = unit number

# --- Source parsing --------------------------------------------------------------------
# Every base file is: header lines, a `====` separator line, then a body where each paragraph is
# ONE physical line. Everything up to the separator is never sent to the model.
HEADER_LEMMA_RE = None               # e.g. r"^LEMMA:\s*(.*)$" if the lemma sits in the header;
HEADER_LEMMA_OUT_PREFIX = "LEMMA: "  #      it is then translated and re-emitted with this prefix
BODY_HEADING_RE = r"^\[?HOMILIA\s+[IVXLCDM]+\.\]?$"   # leading body line(s) dropped; see heading_en
HELD_LINES = [                       # body lines never sent to the model, replaced by fixed English
    # (r"^\[Titulus deest\b", "[No title is transmitted ...]"),
]
ANCHOR_RE = r"\[GCS p\.\d+\]"        # residual page anchors removed defensively (normally none)

# --- Marks (used for --check, soft checks, and auto-fix safety) ----------------------------
PAIRED_MARKS = [("»", "«")]          # add ("⟨", "⟩"), ("[[", "]]") for Greek catena texts
EVEN_MARKS = ["*"]                   # add "†" if obelized cruxes survive into the English
EVEN_MARK_EXEMPT_RE = None           # e.g. r"(?m)^§\s+[IVXLCDM]+\*" (a siglum, not a lemma mark)

# --- Output ----------------------------------------------------------------------------
UNIT_META = {                        # ADAPT: n -> short description shown in logs and headers
    # 1: "Lev. 1 (the whole burnt offering)",
}


def heading_en(n):
    """The English heading paragraph, rebuilt from the filename number (never model output)."""
    return f"HOMILY {C.roman(n)}."   # ADAPT (return None for no heading)


def english_header(n):
    """`#` provenance lines written above the `====` in each English file."""
    meta = UNIT_META.get(n)
    return (f"# {AUTHOR}, *{WORK}* — English translation — {UNIT_NOUN} {n}"
            + (f" ({meta})" if meta else "") + "\n"
            f"# Source text: <edition, pages> — the verified reading text.\n"   # ADAPT
            f"# Scripture is rendered in the author's own wording and numbering.")


# --- Prompt rules ----------------------------------------------------------------------
# Appended to the generic rules (output only the translation; keep the block count; keep » « and
# * *; translate Scripture as it stands). Write each rule as "- TOPIC. instruction\n".
TRANSLATION_RULES = (                # ADAPT
    "- SCRIPTURE (most important). Translate every quotation AS IT STANDS in the source; never "
    "substitute a modern Bible or normalize to the Vulgate. Psalms follow LXX numbering; the "
    "historical books are the LXX 'Kingdoms'.\n"
    "- NAMES. Use standard English biblical forms (Moyses -> Moses, Istrahel -> Israel, ...). "
    "Where the author etymologizes a name, keep his form and gloss it on first mention.\n"
    "- VOCABULARY. <recurring technical terms and their fixed English renderings>\n"
    "- EDITORIAL MARKS. Supplements and seclusions (house policy: trust the critical editor): read "
    "every supplement into the sense and omit every secluded word, printing no brackets for either. "
    "<lacunae / cruxes / rubrics / verse labels: what to do with each>\n"
    "- DELIBERATE IRREGULARITIES. <non-uniform doxologies, odd spellings, etc.: render as printed>\n"
    "- REGISTER. Clear, faithful, dignified English; keep the argumentative connectives; long "
    "periods may be broken up but no clause may be dropped.\n"
)

# Optional, with --images: what this edition's pages look like (where the main text is, what to
# ignore). Goes into each translate bundle under the generic page-image rule of 13_translate.md.
IMAGE_RULE = ""

# What the validator must NOT flag: the settled calls of THIS project, each stated precisely.
VALIDATION_HOUSE_RULES = (           # ADAPT
    "  - <each settled crux / kept Greek word / house rendering / deliberate irregularity>\n"
)

# --- Structure check -------------------------------------------------------------------
SHORT_BLOCK_RATIO = 0.70             # Latin ~0.70, Greek ~0.55 (Greek is more compact)
SHORT_MIN_SOURCE = 200               # ignore short blocks (lemmata, rubrics) for the ratio test
ENDING_CHECKS = [                    # (regex in source, regex that must then be in English, label)
    # (r"Amen", r"Amen", "closing doxology"),
]

# --- Page images (optional; translate.py --images) ----------------------------------------
IMAGE_DIR = os.path.join(PROJECT, "_source", "pages")


def image_paths(n):
    """Page scans for unit n (globbed by printed page; leaf offsets may drift)."""
    return []                        # ADAPT


# --- Oracle (grade.py) -----------------------------------------------------------------
ORACLE_LABEL = "Translator, Title (Series N, Publisher Year)"   # ADAPT
ORACLE_SHORT = "Translator"                                     # ADAPT
ORACLE_COVERED = None                # None = every unit has an oracle; else a set of unit numbers
ORACLE_NOTES = {}                    # n -> note about how the oracle handles this unit
GRADING_CAVEATS = (                  # ADAPT: every known way the oracle is not a tight yardstick
    "  - <e.g. the oracle follows apparatus readings at these places; ours follows the main text>\n"
)


def oracle_text(n):
    """Return the oracle's text for unit n (or None). Prefer per-unit extracts made at pass R3."""
    extract = os.path.join(PROJECT, "_source", "oracle_txt", f"unit{n:02d}_en.txt")
    return C.oracle_from_file(extract)
    # or: return C.oracle_from_pdf_pages(PDF, first, last, cache_path) with a per-unit page map

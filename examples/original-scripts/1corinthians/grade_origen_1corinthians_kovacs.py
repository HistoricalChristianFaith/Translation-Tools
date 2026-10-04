#!/usr/bin/env python3
"""GRADE our English translation of Origen's *Commentary on 1 Corinthians* (the Greek catena
fragments, §§ I-XC, Claude Jenkins JTS 9-10, 1908-09) against our ORACLE English -- Judith L.
Kovacs's published translation (*1 Corinthians Interpreted by Early Christian Commentators*, The
Church's Bible, Eerdmans 2005) -- WITHOUT touching our files. This is the read-only, scoring
sibling of the 1 Corinthians validator (which grades us against our own Greek): here KOVACS is the
reference, and the grade measures HOW CLOSE OUR SENSE IS TO KOVACS'S, fragment by fragment, with an
itemised list of the places we materially diverge. It is the 1 Corinthians counterpart of
`grade_origen_ephesians_heine.py`.

WHAT THIS DOES (and does NOT do)
--------------------------------
  * It NEVER writes to our English, the Greek, or any report file. Its only writes are the
    (git-ignored) oracle text cache and the transcript logs; it commits nothing. (Contrast the
    validator, whose default auto-fixes our English; a GRADER only scores.)
  * KOVACS IS THE YARDSTICK. The grade answers one question: how faithfully does OUR English
    convey the same SENSE as Kovacs's published translation of the same Origen catena excerpt? She
    is the reference for meaning. The Greek is supplied as context/adjudicator (see below).
  * "Divergence" means a difference in MEANING, not style. Our wording is our own and is expected
    to differ from hers; that is not penalised. Only a shift in what the sentence SAYS -- an
    omission, an addition, a flipped/altered sense, a mis-set Scripture reference, a name handled
    so as to change the referent -- counts.

THE CRUCIAL 1-CORINTHIANS CAVEAT -- KOVACS IS A LOOSE, SELECTIVE ANTHOLOGY, NOT A TIGHT YARDSTICK.
This differs sharply from the Ephesians/Heine case. Heine translated the VERY SAME Gregg Greek we
render, verse for verse, so he was a tight yardstick. Kovacs draws her Origen excerpts from the
SAME Jenkins catena we do (Appendix 2 cites each excerpt's exact JTS page), so where she DOES
render a clause, the shared Greek adjudicates and a real sense-gap in ours is a genuine defect. BUT
her book is a general-reader ANTHOLOGY of the whole patristic chain on 1 Corinthians, and three of
its features are NOT our text and must never be scored against us:
  1. THE OTHER FATHERS (the "column" analogue). Each 1 Corinthians passage is expounded by MANY
     commentators in turn -- Cassiodorus, John Chrysostom, Ambrosiaster, Cyril of Alexandria,
     Theodoret, Severian of Gabala, Augustine, Jerome, John of Damascus, Gregory of Nazianzus, and
     others -- each under a `(N) Author` heading. We grade ONLY against the `(N) Origen` catena
     excerpt(s) for the fragment's verse. Content that appears only in another Father's excerpt is
     NOT something we omitted, and no other Father's wording is ever the reference for ours.
  2. NON-CATENA ORIGEN. A handful of Kovacs's `Origen` excerpts are drawn from OTHER works of
     Origen -- *On First Principles*, *Against Celsus*, or homilies on other books (Leviticus,
     Exodus, Luke, Jeremiah) -- NOT the JTS 1 Corinthians catena. Those are not our text at all.
     (E.g. Kovacs's Origen on 1 Cor 10:1-13, 15:28, 15:35-41, 15:42-49 is from *Homilies on
     Exodus* / *On First Principles* / *Against Celsus*; her §LXXXVII verse (xv 35-38) is
     genuinely uncovered.) The coverage map below lists ONLY the catena (JTS) excerpts, so a
     graded fragment is never pointed at non-catena Origen -- but if a window's Origen material
     turns out to be from another work, ignore it.
  3. KOVACS'S SELECTION, ABRIDGMENT, AND PARAPHRASE. She is an editor: she trims Origen's fragment
     to what suits her verse-group, drops stretches, and paraphrases loosely for a general
     audience, and she quotes Scripture in a modern English version (RSV), not in Origen's Greek.
     The ASYMMETRY THIS CREATES IS THE HEART OF GRADING HERE: content that is in OURS but ABSENT
     from Kovacs is almost always HER abridgment, NOT our addition -- do NOT flag it unless our
     extra content actually contradicts the Greek. The real signal runs the other way: where BOTH
     render the same clause and OUR sense differs from hers (with the Greek deciding), that is a
     divergence worth flagging. Because coverage is partial by design, the SCORE measures fidelity
     ACROSS THE OVERLAP, not how much of our fragment she happens to include.

Settled points from the R3 Kovacs oracle pass and the R6 apparatus pass where ours is right (do NOT
penalise): §XV (frag15) the `†αἱ μὲν ῥίζαι†` crux -- Kovacs renders the transmitted words at face
value ("the roots are thoughts") with no emendation, so the daggers are correct; §XVI (frag16)
βεβληκότας -- Kovacs's loose passive ("laid down by the Word") is translator smoothing, not a
sense difference; §XC (frag90) σοῖς -- Kovacs's "your eyelids" corroborates the base; §XXXV
(frag35) is OMITTED by Kovacs entirely (no oracle). The FOUR R6 emendations (base no longer
diplomatic at these loci) may post-date Kovacs's Jenkins reading -- never flag them as ours vs
hers: §VI χριστοῦ + λέγω (frag06), §XII γραφαῖς (frag12), §LXXXIX τοῦ τόπου (frag89). SETTLED HOUSE
RENDERINGS (not additions): χαρίσματα -> "spiritual gifts", γλῶσσαι -> "tongues", προφητεία ->
"prophecy", οἰκοδομή -> "edification".

LOCATING A FRAGMENT IN KOVACS. Kovacs does NOT reprint the Greek and is arranged by 1 Corinthians
PASSAGE (verse-group headers like "1 Corinthians 3:12-15"), each interleaving several Fathers -- so
there is no "§ N" label in her book. Coverage was fixed in the R3 oracle pass FROM KOVACS'S OWN
APPENDIX 2 ("Sources of Texts Translated"), which cites the exact JTS page behind every Origen
excerpt; that pins an exact Kovacs-excerpt -> JTS-page -> fragment-§ map (see FRAG_KOVACS below).
This grader extracts the fragment's verse-group section(s) from a whole-book `pdftotext -layout`
cache and asks the model to grade OUR English against the `(N) Origen` catena material in that
window, ignoring the other Fathers, Kovacs's footnotes, and any non-catena Origen. A fragment's
lemma-verse and its Kovacs verse-group need not coincide: a long § whose exposition runs past its
lemma (e.g. §XXVII, lemma vi 1-3, exposition to vi 9-11) is matched to the Kovacs group that its
TAIL overlaps -- so trust the coverage map, not the lemma, for WHERE to look.

COVERAGE. Kovacs is SELECTIVE: she draws catena Origen for ~33 of our 90 fragments. Only those are
graded; every other fragment is reported UNGRADED (no oracle available) rather than crashing. A
missing English, Greek, or oracle section is likewise reported UNGRADED; a missing PDF or a missing
`pdftotext` degrades the affected fragment to ungraded (never a crash).

COPYRIGHT. Kovacs (*1 Corinthians Interpreted by Early Christian Commentators*, The Church's Bible,
Eerdmans 2005) is IN COPYRIGHT and LOCAL-ONLY (the PDF and its text cache live under the
git-ignored `_source/`). This script reads it as a private reference for comparison and prints only
brief snippets needed to name a divergence. It writes no report into our files and copies nothing
back into our translation.

    python3 grade_origen_1corinthians_kovacs.py frag15_english.txt   # bare name
    python3 grade_origen_1corinthians_kovacs.py /abs/path.txt        # full path
    python3 grade_origen_1corinthians_kovacs.py <directory>          # batch a dir
    python3 grade_origen_1corinthians_kovacs.py                      # batch the english/ dir
    python3 grade_origen_1corinthians_kovacs.py --covered            # batch only Kovacs-covered §§

    --covered        restrict a directory batch to the fragments Kovacs actually covers
    --quiet          print each fragment's grade line but not its divergence list
    --log-dir DIR    where to write per-call transcripts (default: ./grading_logs_1corinthians)
    --no-log         do not write transcripts
"""

import json
import os
import re
import subprocess
import sys
import time

BASE = (
    "/path/to/Writings-Database-Non-English/"
    "Origen of Alexandria/Commentary on 1 Corinthians"
)
SOURCE_DIR = os.path.join(BASE, "GREEK")            # our Greek base (context + adjudicator)
TARGET_DIR = os.path.join(BASE, "english")          # our English (the thing being graded)

# In-copyright, LOCAL ONLY (Kovacs, Church's Bible 2005). The yardstick; under the git-ignored
# _source/, never written back, never committed, wording never copied into our translation.
ORACLE_PDF = os.path.join(BASE, "_source", "oracle", "oracle.pdf")
# Whole-book pdftotext cache (built once, then sliced per fragment by verse-group header).
ORACLE_CACHE = os.path.join(BASE, "_source", "oracle", "oracle_full.txt")

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "grading_logs_1corinthians")

AUTHOR = "Origen of Alexandria"
WORK = "Commentary on 1 Corinthians (Greek catena fragments)"
SOURCE_NOTE = ("the Greek catena fragments constituted by Claude Jenkins, JTS 9 (1908) + 10 (1909)"
               " Parts I-IV; base MS Vatican gr. 762, with 29 fragments (marked *) from MS Athos "
               "Pantocrator 28")
REF_AUTHOR = "Judith L. Kovacs"
REF_LABEL = ("Kovacs, 1 Corinthians Interpreted by Early Christian Commentators, "
             "The Church's Bible (Eerdmans, 2005)")
REF_SHORT = "Kovacs"

# Per-fragment 1 Corinthians reference and Athos-siglum flag (mirrors the validator/translator
# FRAG_META), used to label the grade line. `*` marks the 29 Athos Pantocrator 28 fragments.
FRAG_META = {
     1: ("i 2", False),          2: ("i 4-10", False),       3: ("i 9", False),
     4: ("i 10", False),         5: ("i 14, 17", False),     6: ("i 18", False),
     7: ("i 19-21", False),      8: ("i 23-31", False),      9: ("ii 4-7", False),
    10: ("ii 9-11", False),     11: ("ii 12-15", False),    12: ("iii 1-3 a", False),
    13: ("iii 3-5", False),     14: ("iii 6-8", False),     15: ("iii 9-15", False),
    16: ("iii 16-20", False),   17: ("iii 21-23", False),   18: ("iv 1-5", False),
    19: ("iv 6-8", False),      20: ("iv 9-10", False),     21: ("iv 15", False),
    22: ("iv 19-20", False),    23: ("iv 21-v 2", False),   24: ("v 3-5", False),
    25: ("v 7-8", False),       26: ("v 9-11", False),      27: ("vi 1-3", False),
    28: ("vi 12", False),       29: ("vi 13-14", False),    30: ("vi 15", False),
    31: ("vi 18", False),       32: ("vi 19-20", False),    33: ("vii 1-4", False),
    34: ("vii 5", False),       35: ("vii 8-12", False),    36: ("vii 14", False),
    37: ("vii 18-20", False),   38: ("vii 21-24", False),   39: ("vii 25", False),
    40: ("ix 7-9", False),      41: ("ix 9-11", False),     42: ("ix 16", False),
    43: ("ix 19-23", False),    44: ("ix 24", False),       45: ("x 5", False),
    46: ("x 6", False),         47: ("xii 3", False),       48: ("xii 8-10 (+ xii 27-28)", False),
    49: ("xiii 1-2", False),    50: ("xiii 3", False),      51: ("xiii 4-5", False),
    52: ("xiii 8", False),      53: ("xiii 9-12", False),   54: ("xiv 5", True),
    55: ("xiv 6", True),        56: ("xiv 7-9 a", True),    57: ("xiv 9 b", True),
    58: ("xiv 10", True),       59: ("xiv 11", True),       60: ("xiv 12", True),
    61: ("xiv 13-14", True),    62: ("xiv 15-17", True),    63: ("xiv 18-19", True),
    64: ("xiv 20", True),       65: ("xiv 21", True),       66: ("xiv 24-25", True),
    67: ("xiv 26-27", True),    68: ("xiv 29", True),       69: ("xiv 30-31", True),
    70: ("xiv 32", True),       71: ("xiv 34-35", True),    72: ("xiv 37-38", True),
    73: ("xiv 31", False),      74: ("xiv 34-35", False),   75: ("xiv 37-38", False),
    76: ("xv 1-2", False),      77: ("xv 5", True),         78: ("xv 9", True),
    79: ("xv 10", True),        80: ("xv 11", True),        81: ("xv 12-13", True),
    82: ("xv 14", True),        83: ("xv 15-16", True),     84: ("xv 20-23", False),
    85: ("xv 31", True),        86: ("xv 32", True),        87: ("xv 35-38", False),
    88: ("xv 51", True),        89: ("xvi 10-12", False),   90: ("xvi 13-14", False),
}

# COVERAGE MAP -- fragment -> list of Kovacs verse-group header(s) (the string after
# "1 Corinthians ") whose `(N) Origen` catena excerpt renders this fragment's material. Pinned in
# the R3 oracle pass from Kovacs's Appendix 2 (exact JTS-page citations). A fragment absent from
# this map has NO catena Origen oracle in Kovacs and is reported UNGRADED. Several fragments share
# one Kovacs excerpt (16+17 share 3:18-23; 33+34 share 7:1-7; 55+56 share 14:6-12) and a few need
# two verse-groups (15, 16, 18, 26); the model finds the part that matches the fragment's verse.
FRAG_KOVACS = {
     1: ["1:1-3"],
     2: ["1:4-9"],
     6: ["1:18-25"],
     8: ["1:26-31"],
     9: ["2:6-8"],
    11: ["2:13-16"],
    12: ["3:1-3"],
    14: ["3:4-8"],
    15: ["3:9-11", "3:12-15"],
    16: ["3:16-17", "3:18-23"],
    17: ["3:18-23"],
    18: ["4:1-2", "4:3-5"],
    20: ["4:9-13"],
    24: ["5:1-5"],
    25: ["5:6-8"],
    26: ["5:9-11", "5:12-13"],
    27: ["6:9-11"],
    33: ["7:1-7"],
    34: ["7:1-7"],
    40: ["9:3-7"],
    41: ["9:8-12a"],
    42: ["9:12b-18"],
    43: ["9:19-23"],
    44: ["9:24-27"],
    47: ["12:1-3"],
    51: ["13:4-7"],
    55: ["14:6-12"],
    56: ["14:6-12"],
    73: ["14:26-33a"],
    74: ["14:33b-36"],
    84: ["15:20-22"],
    89: ["16:10-12"],
    90: ["16:13-14"],
}

# Per-fragment coverage notes (documented in the R3/R6 passes) passed to the grader so it does not
# misread Kovacs's editorial selection/abridgment/paraphrase, a shared excerpt, or a settled crux
# as a divergence in ours. Optional; a fragment without a note is graded on the general rules.
FRAG_KOVACS_NOTE = {
     8: "Kovacs's 1:26-31 Origen covers only vv.26-27 and stops before 1 Cor 2:14; the material "
        "later in our fragment is outside her selection (abridgment), not our addition.",
     9: "Kovacs's 2:6-8 Origen overlaps only part of our §IX (she abridges); grade the overlap.",
    11: "Kovacs's 2:13-16 Origen overlaps only part of our §XI (she abridges); grade the overlap.",
    14: "Kovacs's 3:4-8 Origen excerpt is explicitly 'Origen on verse 6' = our §XIV; §XIII is not "
        "translated by her at all.",
    15: "Two Kovacs excerpts (3:9-11 and 3:12-15). At the crux `†αἱ μὲν ῥίζαι†` Kovacs renders "
        "the transmitted words at face value ('the roots are thoughts') with no emendation -- the "
        "daggers are correct; do NOT flag them or the words they mark.",
    16: "Kovacs 3:16-17 plus the opening of 3:18-23. Her loose passive for βεβληκότας ('laid down "
        "by the Word') is translator smoothing, not a sense difference; do NOT flag.",
    17: "§XVII begins WITHIN the shared 3:18-23 Origen excerpt at 'Let no one boast of men' (iii "
        "21); the earlier part of that Kovacs excerpt belongs to §XVI, not to us.",
    18: "Kovacs 4:1-2 + 4:3-5; she skips 4:3-4 -- an abridgment on her side, not our addition.",
    20: "Kovacs covers only the opening of §XX (not the θέατρον / 'fools for Christ' material) -- "
        "abridgment on her side, not our addition.",
    26: "Kovacs 5:9-11 + 5:12-13; she skips the πλεονέκται ('the greedy') middle -- abridgment.",
    27: "Long fragment: lemma vi 1-3, but the exposition runs (via [vi 4]..[vi 9] sub-lemmas) to "
        "vi 9-11. Kovacs's 6:9-11 Origen excerpt overlaps only the vi 9-11 TAIL of our fragment "
        "('the unrighteous will not inherit... if the kingdom of God is in Christ'). Grade that "
        "overlap; the vi 1-8 body simply has no Kovacs oracle (not an addition).",
    33: "§XXXIII and §XXXIV are ONE continuous Kovacs Origen excerpt (7:1-7); grade §XXXIII "
        "against its portion of it.",
    34: "Shares the 7:1-7 Origen excerpt with §XXXIII; §XXXIV's second [Ὠριγένους] block is left "
        "untranslated by Kovacs -- abridgment, not our addition.",
    41: "Kovacs 9:8-12a; §XLI and §XLII are adjacent excerpts (9:8-12a and 9:12b-18).",
    42: "Kovacs 9:12b-18; adjacent to §XLI (9:8-12a).",
    43: "Kovacs merges §XLIII's two [Ὠριγένους] blocks into one excerpt. The body legitimately "
        "re-cites 1 Cor ix 22 as 'that I might save all or some' (a genuine Origenic variant "
        "citation) -- not a divergence.",
    47: "Kovacs renders the repeated 12:3a clause loosely as 12:3b ('no one can say Jesus is Lord "
        "except in the Holy Spirit'); Origen's 12:3a repetition is deliberate -- not our error.",
    55: "§LV* and §LVI* are covered TOGETHER by one 14:6-12 Origen excerpt; grade §LV* against its "
        "first-paragraph portion.",
    56: "Shares the single 14:6-12 Origen excerpt with §LV* -- grade §LVI* against its "
        "second-paragraph portion.",
    84: "Kovacs's 15:20-22 Origen leaves the line-10 ἀπαρχή ('firstfruits') exegesis untranslated "
        "-- abridgment on her side, not our addition.",
    89: "Kovacs's 16:10-12 Origen omits the Apollos section -- abridgment, not our addition.",
    90: "Kovacs's 'your eyelids' (Prov/Ps quotation) corroborates the base σοῖς reading.",
}

FILE_RE = re.compile(r"^frag\d+_english\.txt$")
SEP_RE = re.compile(r"^=+$")
CRAMER_LINE_RE = re.compile(r"^\s*\[Cramer\b")        # Greek header scaffolding, dropped from context
# A Kovacs verse-group header line, e.g. "1 Corinthians 3:12-15" or "1 Corinthians 9:12b-18".
VG_HEADER_RE = re.compile(r"^\s*1\s+Corinthians\s+\d+:\d+[a-z]?(?:-\d+[a-z]?)?\s*\+?\s*$")

RETRY_DELAYS = [5, 15, 45]
RATE_LIMIT_DELAYS = [60, 120, 240]


# --- IO / body extraction -----------------------------------------------------


def parse_text(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def english_body(raw):
    """Return our English reading body: drop the leading `#`-comment provenance header and the
    `=`-run separator line, then everything that follows (the `§ … — 1 Corinthians …` heading, the
    `LEMMA:` line, and the exposition)."""
    lines = raw.split("\n")
    out, started = [], False
    for ln in lines:
        s = ln.strip()
        if not started and (s.startswith("#") or SEP_RE.match(s) or s == ""):
            continue
        started = True
        out.append(ln)
    return "\n".join(out).strip()


def greek_context(raw):
    """Return the Greek reading text for context/adjudication: keep the `§ … | 1 Cor …` heading,
    the `LEMMA:` line, and the body; drop only the `[Cramer n]` traceability line and the `====`
    rule (working scaffolding). This is the text BOTH we and Kovacs's Origen excerpt render."""
    keep = []
    for ln in raw.split("\n"):
        if CRAMER_LINE_RE.match(ln) or SEP_RE.match(ln.strip()):
            continue
        keep.append(ln)
    return "\n".join(keep).strip()


def paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def frag_num_of(path):
    m = re.search(r"frag(\d+)", os.path.basename(path))
    return int(m.group(1)) if m else None


def frag_label(n):
    """Roman-numeral § label with the Athos siglum where applicable (e.g. 'LVI*')."""
    ref, athos = FRAG_META.get(n, ("", False))
    romans = {1: "I", 4: "IV", 5: "V", 9: "IX", 10: "X", 40: "XL", 50: "L", 90: "XC"}
    val, out = n, ""
    for a, r in ((100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"),
                 (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while val >= a:
            out += r
            val -= a
    return out + ("*" if athos else "")


def source_path_for(english_file):
    n = frag_num_of(english_file)
    return os.path.join(SOURCE_DIR, f"frag{n:02d}_greek.txt")  # zero-padded


# --- Oracle (Kovacs 2005 -> whole-book cache -> per-fragment verse-group slice) ------


def kovacs_full_text():
    """Return the whole Kovacs book as `pdftotext -layout` text, cached to the git-ignored
    `_source/oracle/oracle_full.txt`. Returns None (with a printed note) if the PDF or `pdftotext`
    is unavailable and no cache exists."""
    if os.path.exists(ORACLE_CACHE) and os.path.getsize(ORACLE_CACHE) > 0:
        return parse_text(ORACLE_CACHE)
    if not os.path.exists(ORACLE_PDF):
        print(f"    Oracle PDF not found: {ORACLE_PDF} -- cannot grade.")
        return None
    try:  # layout mode preserves the single-column reading order and paragraphing
        subprocess.run(["pdftotext", "-layout", ORACLE_PDF, ORACLE_CACHE],
                       check=True, capture_output=True, text=True)
    except FileNotFoundError:
        print("    `pdftotext` not on PATH (install poppler) -- cannot extract oracle.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"    pdftotext failed: {e.stderr.strip()[:160]} -- cannot extract oracle.")
        return None
    if not (os.path.exists(ORACLE_CACHE) and os.path.getsize(ORACLE_CACHE) > 0):
        return None
    return parse_text(ORACLE_CACHE)


def slice_verse_group(full_lines, verse_group, cap=600):
    """Return the Kovacs body section for one verse-group header (e.g. '3:12-15'): the text from
    its FIRST body occurrence up to the next verse-group header line (or `cap` lines, whichever is
    first). Returns "" if the header is not found. The header also recurs in Appendix 2, but the
    first (body) occurrence is the exposition; slicing to the next verse-group header bounds it."""
    target = f"1 Corinthians {verse_group}"
    start = None
    for i, ln in enumerate(full_lines):
        if ln.strip() == target:
            start = i
            break
    if start is None:
        return ""
    end = min(start + 1 + cap, len(full_lines))
    for j in range(start + 1, end):
        if VG_HEADER_RE.match(full_lines[j]):
            end = j
            break
    chunk = "\n".join(full_lines[start:end]).replace("\x0c", "\n")
    return re.sub(r"\n{3,}", "\n\n", chunk).strip()


def oracle_text_for(n, full_text):
    """Reference text for fragment n: the concatenation of its mapped Kovacs verse-group section(s).
    Returns None if the fragment is uncovered (no catena Origen in Kovacs) or every section slice
    comes back empty."""
    vgs = FRAG_KOVACS.get(n)
    if not vgs:
        return None
    lines = full_text.split("\n")
    sections = []
    for vg in vgs:
        sec = slice_verse_group(lines, vg)
        if sec:
            sections.append(f"----- Kovacs, 1 Corinthians {vg} -----\n{sec}")
    return "\n\n".join(sections) if sections else None


# --- Prompt -------------------------------------------------------------------


def build_prompt(frag_num, cor_ref, greek_text, english_text, oracle_text, frag_note="",
                 reminder=""):
    label = frag_label(frag_num)
    ref_hint = f" (on 1 Cor. {cor_ref})" if cor_ref else ""
    verse = f"1 Cor. {cor_ref}" if cor_ref else "this fragment's verse"
    note_block = (f"\nCOVERAGE NOTE for this fragment (from the oracle-collation pass -- read "
                  f"before grading): {frag_note}\n" if frag_note else "")
    return (
        f"You are GRADING an existing English translation against a published reference "
        f"translation, for SENSE fidelity. The work is {AUTHOR}'s {WORK} -- {SOURCE_NOTE}. "
        f"Origen's commentary survives only as excerpts in the medieval Greek exegetical chains "
        f"(catenae). You are grading FRAGMENT {frag_num} (§ {label}){ref_hint}.\n\n"

        f"THE YARDSTICK IS {REF_AUTHOR.upper()}. Her published English ({REF_LABEL}) is the "
        f"reference for meaning; the relevant section is pasted below under 'REFERENCE'. Kovacs "
        f"draws her Origen excerpts from the SAME Jenkins catena we translate (her Appendix 2 "
        f"cites each excerpt's exact JTS page), so where she renders a clause, the GREEK below is "
        f"the text BOTH we and she render and it ADJUDICATES -- decide by the Greek whether ours "
        f"has actually shifted the sense or is merely worded differently.\n\n"

        f"BUT KOVACS IS A LOOSE, SELECTIVE ANTHOLOGY, NOT A TIGHT YARDSTICK. Her book expounds "
        f"each passage of 1 Corinthians through MANY Fathers in turn, and she edits Origen freely. "
        f"Three parts of the REFERENCE are NOT our text and MUST be ignored for grading:\n"
        f"  (1) THE OTHER FATHERS. Each verse-group interleaves several commentators, each under a "
        f"`(N) Author` heading (Cassiodorus, John Chrysostom, Ambrosiaster, Cyril of Alexandria, "
        f"Theodoret, Severian, Augustine, Jerome, and others). Grade ONLY against the `(N) Origen` "
        f"catena excerpt(s) on {verse}. Content that appears only in another Father's excerpt is "
        f"NOT something we omitted, and no other Father's wording is ever the reference for ours.\n"
        f"  (2) NON-CATENA ORIGEN and KOVACS'S FOOTNOTES. Ignore any Origen material drawn from "
        f"another work (On First Principles, Against Celsus, homilies on other books -- Kovacs "
        f"names the source), and ignore her numbered footnotes (her editorial notes, not the "
        f"text).\n"
        f"  (3) KOVACS'S SELECTION / ABRIDGMENT / PARAPHRASE. She trims Origen to fit her "
        f"verse-group, drops stretches, paraphrases loosely for a general reader, and quotes "
        f"Scripture in a modern English version (RSV), not Origen's Greek.\n\n"

        f"THE DECISIVE ASYMMETRY. Because Kovacs abridges, content that is in OURS but ABSENT from "
        f"her excerpt is almost always HER selection, NOT our addition -- do NOT flag such "
        f"material unless what we add actually CONTRADICTS the Greek. The real signal runs the "
        f"other way: where BOTH render the same clause and OUR sense differs from hers (with the "
        f"Greek deciding), that is a divergence. Grade fidelity ACROSS THE OVERLAP; partial "
        f"coverage on her side is expected and is not counted against us. If the extract's Origen "
        f"passage seems clipped, judge our opening/close against the GREEK, not the clip.\n"
        f"{note_block}\n"

        "WHAT COUNTS AS A DIVERGENCE. Only a difference in MEANING in OUR English, within the "
        "overlap, judged against what the GREEK says and Kovacs's Origen confirms:\n"
        "  - OMISSION: a clause whose sense is in the Greek AND in Kovacs's Origen excerpt but "
        "absent from ours.\n"
        "  - ADDITION: content in ours whose sense is neither in the Greek NOR anywhere Origen "
        "could support -- NOT merely absent from Kovacs's abridged excerpt.\n"
        "  - SHIFTED SENSE: our sentence asserts something materially different (altered "
        "subject/object, flipped negation, different referent, a different allegorical "
        "identification, wrong sense of an ambiguous word).\n"
        "  - SCRIPTURE: a quoted verse whose reference or wording points to a different "
        "passage/sense than the Greek's -- Origen's own Greek (LXX/NT) is the arbiter, NOT "
        "Kovacs's modern-version Bible wording.\n"
        "  - NAME/REFERENT: a name rendered so the person or place referred to differs.\n"
        "  - TRUNCATION: our fragment stops materially earlier than the GREEK runs (judge by the "
        "Greek, since Kovacs's excerpt may itself be abridged).\n\n"

        "WHAT DOES NOT COUNT (never flag these):\n"
        "  - Different word choice, synonyms, sentence length, clause order, register, or "
        "punctuation when the MEANING is the same. Our wording is independently our own and is "
        "EXPECTED to differ from hers.\n"
        "  - KOVACS'S ABRIDGMENT: any Origen material she selected out. Content present in ours "
        "and the Greek but missing from her excerpt is HER cut, not our addition.\n"
        "  - THE OTHER FATHERS, NON-CATENA ORIGEN, and KOVACS'S FOOTNOTES (above).\n"
        "  - KOVACS'S OWN FREEDOM. Where she paraphrases or construes loosely and OUR English "
        "stays closer to what the Greek actually says, that is NOT our divergence (e.g. §XLVII she "
        "renders the repeated 12:3a clause as 12:3b; §XVI βεβληκότας as a loose passive). Grade "
        "ours by the Greek, not by her liberty.\n"
        "  - Our editorial marks: we wrap the Scripture Origen quotes in guillemets `» «` and the "
        "lemma word(s) in asterisks `* *`; supplements `⟨ ⟩` and seclusions `[ … ]` in the Greek "
        "are DROPPED in our English; `[[ … ]]` double-bracket glosses, `† … †` obelized cruxes, "
        "the attribution rubric `[Of Origen]`, and the sub-lemma verse labels (`[vi 4]`, `[iv "
        "16]`, …) are part of our reading text. Marks are not meaning; never flag them.\n"
        "  - SCRIPTURE IN ORIGEN'S OWN GREEK (LXX / NT), Psalms in LXX numbering, historical books "
        "as the LXX 'Kingdoms'. Where our English renders Jenkins's printed Greek and it differs "
        "from a modern Bible or from Kovacs's own Scripture wording, ours is CORRECT (the Greek is "
        "the arbiter), not a divergence.\n"
        "  - STANDARD-ENGLISH NAME NORMALIZATION of the Greek forms (Ἰησοῦς->Jesus, Παῦλος->Paul, "
        "Ἀπολλώς->Apollos, Κηφᾶς->Cephas, Τιμόθεος->Timothy, Μωϋσῆς->Moses, Δαβίδ->David, "
        "Κορίνθιοι->the Corinthians, etc.). Same referent = not a divergence.\n"
        "  - SETTLED HOUSE RENDERINGS (correct, never flag as additions or shifts): "
        "χαρίσματα -> 'spiritual gifts'; γλῶσσαι -> 'tongues'; προφητεία -> 'prophecy'; "
        "οἰκοδομή -> 'edification'.\n"
        "  - SETTLED CRUXES / EMENDATIONS (adjudicated in the oracle + apparatus passes -- do NOT "
        "flag): frag15 (§XV) `†αἱ μὲν ῥίζαι†` -- Kovacs renders the transmitted words at face "
        "value ('the roots are thoughts'), daggers correct; frag16 (§XVI) βεβληκότας -- Kovacs's "
        "passive is smoothing; frag90 (§XC) σοῖς -- Kovacs's 'your eyelids' corroborates it; and "
        "the four R6 base emendations frag06 (§VI χριστοῦ + λέγω), frag12 (§XII γραφαῖς), frag89 "
        "(§LXXXIX τοῦ τόπου) may post-date Kovacs's Jenkins reading -- never scored against us.\n"
        "  - CATENA / FRAGMENT SEAMS: a fragment may begin or end abruptly (it is an excerpt); "
        "there is NO closing doxology. Rendering the seam as it stands is correct.\n\n"

        "OUTPUT -- STRICT JSON ONLY. Emit a single JSON object and NOTHING else (no prose, "
        "no code fence, no commentary before or after). Schema:\n"
        "{\n"
        '  "score": <integer 0-100, how fully our English matches her sense ACROSS THE OVERLAP; '
        "100 = every shared point of meaning conveyed, 0 = unrelated>,\n"
        '  "grade": "<letter A+ .. F matching the score>",\n'
        '  "sense_alignment": "<high|moderate|low>",\n'
        '  "coverage": "<full|partial|tail-only|minimal -- how much of our fragment Kovacs\'s '
        "excerpt actually overlaps>\",\n"
        '  "divergences": [\n'
        "    {\n"
        '      "locus": "<where, e.g. a short anchor phrase from OUR text>",\n'
        '      "severity": "<minor|moderate|significant>",\n'
        '      "category": "<omission|addition|shifted-sense|scripture|name|truncation>",\n'
        '      "oracle": "<brief: the sense Kovacs\'s Origen conveys>",\n'
        '      "ours": "<brief: how our English differs in sense>",\n'
        '      "note": "<one line: why it matters / how far the meaning drifts (cite the Greek '
        'if it decides it)>"\n'
        "    }\n"
        "  ],\n"
        '  "summary": "<1-3 sentences: overall how close we are to the reference across the '
        "overlap, and the most important divergences, if any>\"\n"
        "}\n"
        "List divergences MOST SEVERE FIRST. If our English conveys her sense throughout the "
        "overlap, return an empty \"divergences\" array and a high score -- do NOT invent "
        "differences, and do NOT flag her abridgment, the other Fathers, non-catena Origen, her "
        "paraphrase, or the settled cruxes/house renderings above. Keep every quoted snippet brief "
        "(a few words), enough only to identify the spot.\n"
        f"{reminder}"
        "\n"
        "=== GREEK SOURCE (context + adjudicator; the text BOTH we and Kovacs's Origen render -- "
        "Jenkins JTS 1908-09) ===\n"
        f"{greek_text}\n"
        "\n"
        "=== OUR ENGLISH TRANSLATION (the one being graded) ===\n"
        f"{english_text}\n"
        "\n"
        f"=== REFERENCE: {REF_SHORT} (Church's Bible 2005) -- PDF extract of the verse-group "
        f"section(s); use ONLY her `(N) Origen` catena material on {verse}, NOT the other Fathers, "
        f"her footnotes, or any non-catena Origen ===\n"
        f"{oracle_text}\n"
    )


# --- CLI call -----------------------------------------------------------------


def is_rate_limit_error(stderr):
    lower = stderr.lower()
    return any(term in lower for term in
               ["rate limit", "rate_limit", "overloaded", "too many requests", "529"])


def call_claude(prompt):
    """One CLI call with rate-limit-aware retry/backoff. Returns stdout text. No tools are
    needed (all three texts are pasted), so this is a plain text-in/JSON-out call."""
    delays = RETRY_DELAYS
    for attempt in range(len(delays) + 1):
        result = subprocess.run(
            ["claude", "-p", "--dangerously-skip-permissions"],
            input=prompt, capture_output=True, text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        if is_rate_limit_error(result.stderr):
            delays = RATE_LIMIT_DELAYS
        if attempt < len(delays):
            wait = delays[attempt]
            print(f"    Retry {attempt + 1}/{len(delays)} after {wait}s... "
                  f"(rc={result.returncode} stderr={result.stderr.strip()[:80]})")
            time.sleep(wait)
        else:
            raise RuntimeError(
                f"Grading call failed after retries: rc={result.returncode} "
                f"stderr={result.stderr.strip()[:200]} stdout={result.stdout.strip()[:200]}")
    raise RuntimeError("Unreachable")


# --- Grade parsing ------------------------------------------------------------


def extract_json(text):
    """Pull the JSON object out of a model reply, tolerating a code fence or a stray line
    of prose around it. Returns the parsed dict, or None on failure."""
    if not text:
        return None
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        start = text.find("{")
        end = text.rfind("}")
        candidate = text[start:end + 1] if (start != -1 and end > start) else None
    if candidate is None:
        return None
    try:
        obj = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def letter_for(score):
    if score is None:
        return "?"
    for cut, letter in ((97, "A+"), (93, "A"), (90, "A-"), (87, "B+"), (83, "B"),
                        (80, "B-"), (77, "C+"), (73, "C"), (70, "C-"), (67, "D+"),
                        (63, "D"), (60, "D-")):
        if score >= cut:
            return letter
    return "F"


def normalize_grade(obj):
    """Coerce a parsed grade dict into a predictable shape (fills sane defaults)."""
    score = obj.get("score")
    try:
        score = max(0, min(100, int(round(float(score)))))
    except (TypeError, ValueError):
        score = None
    divs = obj.get("divergences")
    divs = divs if isinstance(divs, list) else []
    clean_divs = []
    for d in divs:
        if not isinstance(d, dict):
            continue
        clean_divs.append({
            "locus": str(d.get("locus", "?")),
            "severity": str(d.get("severity", "moderate")).lower(),
            "category": str(d.get("category", "shifted-sense")).lower(),
            "oracle": str(d.get("oracle", d.get("kovacs", d.get("reference", "")))),
            "ours": str(d.get("ours", "")),
            "note": str(d.get("note", "")),
        })
    return {
        "score": score,
        "grade": str(obj.get("grade", "")).strip() or letter_for(score),
        "sense_alignment": str(obj.get("sense_alignment", "")).strip().lower(),
        "coverage": str(obj.get("coverage", "")).strip().lower(),
        "divergences": clean_divs,
        "summary": str(obj.get("summary", "")).strip(),
    }


SEV_ORDER = {"significant": 0, "moderate": 1, "minor": 2}


def grade_whole(frag_num, cor_ref, greek_body, english_body, oracle_text, frag_note="",
                log_base=None):
    """One grading call; parse its JSON, retrying once if the reply is not valid JSON.
    Returns a normalized grade dict, or None if grading could not be parsed."""

    def call(prompt, attempt):
        raw = call_claude(prompt)
        if log_base:
            with open(f"{log_base}.{attempt}.txt", "w", encoding="utf-8") as f:
                f.write(f"# fragment={frag_num} attempt={attempt} "
                        f"prompt_chars={len(prompt)}\n\n{raw}\n")
        return raw

    raw = call(build_prompt(frag_num, cor_ref, greek_body, english_body, oracle_text,
                            frag_note=frag_note), 1)
    obj = extract_json(raw)
    if obj is None:
        print("    Reply was not valid JSON -- retrying once for a clean object...")
        reminder = ("IMPORTANT: your previous reply could not be parsed. Output ONE JSON "
                    "object and nothing else -- no prose, no code fence.\n")
        raw = call(build_prompt(frag_num, cor_ref, greek_body, english_body,
                                oracle_text, frag_note=frag_note, reminder=reminder), 2)
        obj = extract_json(raw)
    if obj is None:
        return None
    return normalize_grade(obj)


# --- Reporting ----------------------------------------------------------------

SEV_TAG = {"significant": "!!", "moderate": "! ", "minor": ". "}


def print_grade(grade, quiet=False):
    score = grade["score"]
    score_str = f"{score}" if score is not None else "--"
    ndiv = len(grade["divergences"])
    sig = sum(1 for d in grade["divergences"] if d["severity"] == "significant")
    cov = f", cov {grade['coverage']}" if grade["coverage"] else ""
    print(f"  GRADE: {grade['grade']:>2}  ({score_str}/100, "
          f"sense {grade['sense_alignment'] or '?'}{cov})  ·  "
          f"{ndiv} divergence(s), {sig} significant")
    if grade["summary"]:
        print(f"  {grade['summary']}")
    if quiet or not grade["divergences"]:
        return
    ordered = sorted(grade["divergences"], key=lambda d: SEV_ORDER.get(d["severity"], 9))
    for d in ordered:
        tag = SEV_TAG.get(d["severity"], "  ")
        print(f"    {tag} [{d['severity']}/{d['category']}] {d['locus']}")
        if d["oracle"]:
            print(f"         {REF_SHORT}: {d['oracle'][:150]}")
        if d["ours"]:
            print(f"         Ours:  {d['ours'][:150]}")
        if d["note"]:
            print(f"         -> {d['note'][:150]}")


# --- Driver -------------------------------------------------------------------


def resolve_input(arg):
    if os.path.isabs(arg) or os.sep in arg:
        return arg
    return os.path.join(TARGET_DIR, arg)


def grade_file(english_file, full_oracle, quiet=False, log_dir=LOG_DIR):
    """Grade one fragment against Kovacs. Returns a result dict for the batch summary.
    Never writes to the English/Greek files."""
    n = frag_num_of(english_file)
    cor_ref = FRAG_META.get(n, ("", False))[0]
    source_file = source_path_for(english_file)
    vgs = FRAG_KOVACS.get(n)

    print(f"\n{'=' * 60}")
    print(f"Grade: {os.path.basename(english_file)}  (§ {frag_label(n)}"
          + (f", 1 Cor. {cor_ref})" if cor_ref else ")"))
    print(f"  ours:   {english_file}")
    print(f"  greek:  {source_file}")
    where = ("Kovacs " + " + ".join(vgs)) if vgs else "no catena Origen in Kovacs"
    print(f"  oracle: {REF_SHORT} 2005, {where}")
    print(f"{'=' * 60}")

    if not vgs:
        print(f"  Fragment {n} is not covered by Kovacs's catena Origen -- ungraded.")
        return {"file": english_file, "status": "uncovered", "grade": None}
    if not os.path.exists(english_file) or os.path.getsize(english_file) == 0:
        print("  Our English missing or empty -- ungraded.")
        return {"file": english_file, "status": "ungraded", "grade": None}
    if not os.path.exists(source_file):
        print(f"  Greek source not found: {source_file} -- ungraded.")
        return {"file": english_file, "status": "ungraded", "grade": None}
    if full_oracle is None:
        print("  Oracle unavailable -- ungraded.")
        return {"file": english_file, "status": "ungraded", "grade": None}

    oracle_text = oracle_text_for(n, full_oracle)
    if not oracle_text:
        print(f"  Could not locate Kovacs section(s) {vgs} for fragment {n} -- ungraded.")
        return {"file": english_file, "status": "ungraded", "grade": None}

    eng_body = english_body(parse_text(english_file))
    grk_body = greek_context(parse_text(source_file))
    frag_note = FRAG_KOVACS_NOTE.get(n, "")

    eng_q = eng_body.count("»")
    print(f"  Structure -- ours: {len(paragraphs(eng_body))} block(s), "
          f"{eng_q} Scripture-quote span(s) | {REF_SHORT} extract: "
          f"{len(oracle_text.split())} words (verse-group section, incl. other Fathers).")
    if frag_note:
        print(f"  Coverage note: {frag_note[:150]}")

    log_base = None
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        log_base = os.path.join(
            log_dir, os.path.splitext(os.path.basename(english_file))[0])
        print(f"  Transcript log: {log_base}.<attempt>.txt")

    grade = grade_whole(n, cor_ref, grk_body, eng_body, oracle_text,
                        frag_note=frag_note, log_base=log_base)
    if grade is None:
        print("  Could not obtain a parseable grade -- skipped.")
        return {"file": english_file, "status": "unparseable", "grade": None}

    print_grade(grade, quiet=quiet)
    return {"file": english_file, "status": "graded", "grade": grade}


def order_key(name):
    n = frag_num_of(name)
    return n if n is not None else 999


def collect_files(path, covered_only=False):
    if os.path.isdir(path):
        files = [os.path.join(path, f)
                 for f in sorted(os.listdir(path), key=order_key)
                 if FILE_RE.match(f)]
        if covered_only:
            files = [f for f in files if frag_num_of(f) in FRAG_KOVACS]
        return files
    return [path]


def print_summary(results):
    print(f"\n{'=' * 60}\nGRADING SUMMARY (yardstick: {REF_LABEL})\n{'=' * 60}")
    graded = [r for r in results if r["status"] == "graded"]
    scores = [r["grade"]["score"] for r in graded if r["grade"]["score"] is not None]
    for r in results:
        name = os.path.basename(r["file"])
        if r["status"] != "graded":
            print(f"  {name:28}  {r['status'].upper()}")
            continue
        g = r["grade"]
        score = g["score"]
        score_str = f"{score:3d}" if score is not None else " --"
        ndiv = len(g["divergences"])
        sig = sum(1 for d in g["divergences"] if d["severity"] == "significant")
        print(f"  {name:28}  {g['grade']:>2}  {score_str}/100  ({ndiv} div, {sig} sig)")
    if scores:
        avg = sum(scores) / len(scores)
        print(f"\n  Mean sense-fidelity score: {avg:.1f}/100 "
              f"({letter_for(int(round(avg)))}) across {len(scores)} graded fragment(s).")
    total_sig = sum(sum(1 for d in r["grade"]["divergences"]
                        if d["severity"] == "significant")
                    for r in graded)
    print(f"  Total significant divergences flagged: {total_sig}.")
    uncovered = [r for r in results if r["status"] == "uncovered"]
    if uncovered:
        print(f"  {len(uncovered)} fragment(s) UNCOVERED by Kovacs (no catena Origen excerpt) "
              f"-- expected; Kovacs is selective.")
    print(f"  Reminder: Kovacs draws from the SAME Jenkins catena, so the Greek adjudicates the "
          f"overlap -- but she abridges/paraphrases and interleaves other Fathers, so her "
          f"omissions are not our additions and her wording is not our yardstick.")


def main():
    argv = sys.argv[1:]
    quiet = False
    covered_only = False
    log_dir = LOG_DIR
    positional = []
    it = iter(argv)
    for a in it:
        if a == "--quiet":
            quiet = True
        elif a == "--covered":
            covered_only = True
        elif a == "--no-log":
            log_dir = None
        elif a == "--log-dir" or a.startswith("--log-dir="):
            log_dir = a.split("=", 1)[1] if "=" in a else next(it, None)
            if not log_dir:
                print("--log-dir requires a directory path.")
                sys.exit(1)
        elif a.startswith("--"):
            print(f"Unknown option: {a}")
            sys.exit(1)
        else:
            positional.append(a)

    raw_input = resolve_input(positional[0]) if positional else TARGET_DIR
    if not os.path.exists(raw_input):
        print(f"Input not found: {raw_input}")
        sys.exit(1)

    files = collect_files(raw_input, covered_only=covered_only)
    if not files:
        print("No English files found (expected frag<NN>_english.txt).")
        sys.exit(1)

    print(f"Grading {len(files)} file(s) against {REF_LABEL}"
          + (f". Logs -> {log_dir}" if log_dir else " (logging off)"))
    full_oracle = kovacs_full_text()
    if full_oracle is None:
        print("  WARNING: oracle text unavailable -- every fragment will be ungraded.")

    results, failures = [], []
    for f in files:
        try:
            results.append(grade_file(f, full_oracle, quiet=quiet, log_dir=log_dir))
        except Exception as e:  # keep the batch going; report at the end
            print(f"  ERROR on {os.path.basename(f)}: {e}")
            failures.append((f, str(e)))

    if results:
        print_summary(results)
    if failures:
        print(f"\n{len(failures)} failure(s):")
        for f, e in failures:
            print(f"  FAILED: {os.path.basename(f)} -- {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

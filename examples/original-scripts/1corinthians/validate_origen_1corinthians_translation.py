#!/usr/bin/env python3
"""VALIDATE our English translation of Origen's *Commentary on 1 Corinthians* (Greek catena
fragments) against OUR OWN GREEK base -- the verified Jenkins JTS 1908-09 reading text --
fragment by fragment. This is the twin of `validate_origen_ephesians_translation.py` (same
author, same catena genre, same Greek-is-the-arbiter method) and the Greek-is-the-arbiter
sibling of the Leviticus validator: it asks the one question the project's hard rule cares
about -- **does our English faithfully and completely render what the Greek actually says, in
the sense Origen's own argument requires?** -- and reports (and optionally FIXES in place) the
spots where it does not.

TWO LAYERS OF CHECK
-------------------
  1. STRUCTURE (deterministic, NO API call, always run first). Compares the Greek and English
     block-by-block and flags the mechanical failure modes of the translation step -- a DROPPED
     block (block-count mismatch), a TRUNCATED block (an English block far shorter than its
     Greek), or a substantial block that ends MID-SENTENCE. Run `--structure-only` to see it for
     the whole corpus without spending a token. (These are catena excerpts with NO uniform
     closing doxology and some legitimately begin or end abruptly, so there is no doxology check
     and the mid-sentence flag is informational.)
  2. FIDELITY (one LLM call per fragment). The Greek base is the sole arbiter, so ANY English
     departure from it is visible -- omissions, additions, sense-shifts, mis-rendered Scripture
     quotations, name/referent errors, and INTERNAL INCONSISTENCIES (e.g. a lemma word rendered
     one way and Origen's own later gloss of that same word rendered the opposite way). This is
     the layer that catches "thin" renderings that are the right LENGTH but drop clauses or
     flatten the argument.

WHAT THE FIDELITY LAYER CHECKS (a finding = a real fidelity defect in OUR English vs Greek)
  - OMISSION: a Greek clause/word whose sense is absent from our English.
  - ADDITION: content in our English whose sense is not in the Greek.
  - MISTRANSLATION / SENSE-SHIFT: wrong sense of a word, flipped negation, altered subject/object
    or referent, a different allegorical identification than the Greek supports.
  - SCRIPTURE: a quoted verse whose English wording misrenders the Greek quotation as printed.
  - NAME/REFERENT: a name rendered so the person/place referred to differs from the Greek's.
  - INCONSISTENCY: the same Greek word/phrase rendered incompatibly in two places, or the English
    contradicting itself where the Greek is coherent.
  - UNTRANSLATED / GARBLED: Greek left untranslated, or an incoherent English stretch.

WHAT IT DOES NOT FLAG (house rules -- the Greek base's own conventions and our settled calls)
  - Independent WORDING/STYLE: synonyms, clause order, sentence length, register, broken-up long
    periods -- when the MEANING matches. Our English is our own; only meaning counts.
  - Our EDITORIAL MARKS: Scripture in »…«, the 1 Corinthians lemma word(s) in *…*. Marks are not
    meaning. Also NOT meaning: whether the header LEMMA line keeps or drops Jenkins's diplomatic
    `[ … ]` wrap around the verse -- that is a presentation mark, never a fidelity defect.
  - KEPT BRACKETS that are part of the reading text: the catenist ATTRIBUTION RUBRIC
    (`[Of Origen]`, the one rubric form in this corpus), the SUB-LEMMA verse labels
    (`[iv 16]`, `[vi 9-10]`, `[vii 28 a]`, …), and the DOUBLE BRACKETS `[[ … ]]` (frag48's first
    lemma, 1 Cor xii 8-10; frag81's gloss naming the Manichaeans). Keeping these is correct.
  - THE OBELIZED CRUXES † … † (frag15, frag35): the daggers fence text Jenkins marks as corrupt.
    They are MARKS, not meaning -- never flag their presence; the daggered words are rendered as
    best they stand.
  - EDITOR'S SUPPLEMENTS ⟨ … ⟩ and SECLUSIONS [ … ] (mid-text -- only `[Χριστοῦ]` frag02 and
    `[μὴ]` frag19) read in sense WITHOUT printing the brackets -- correct, not omission/addition.
  - PRINTED LACUNAE `. . .` (frag05/07/08/14) and `…` (frag48): kept as they stand, NOT filled --
    keeping the gap is correct, never an omission.
  - STANDARD-ENGLISH NAME NORMALIZATION of the Greek forms (Ἰησοῦς->Jesus, Παῦλος->Paul,
    Ἀπολλώς->Apollos, Κηφᾶς->Cephas, Τιμόθεος->Timothy, Κορίνθιοι->the Corinthians, Μωσῆς->Moses,
    Ἡσαΐας->Isaiah, Ἀκύλας/Σύμμαχος/Θεοδοτίων->Aquila/Symmachus/Theodotion, Μανιχαῖοι->the
    Manichaeans, etc.). Same referent = not a defect.
  - KEPT-AND-GLOSSED GREEK TERMS where Origen etymologizes or draws a load-bearing contrast:
    above all §XI (frag11) ψυχικός ('the natural/unspiritual man') vs πνευματικός ('the spiritual
    man') -- keeping BOTH distinct is CORRECT; flag it ONLY if the English actually collapses or
    swaps the two senses.
  - SETTLED HOUSE RENDERINGS of recurring 1-Corinthians vocabulary (a consistent gloss, NOT an
    addition): χαρίσματα -> 'spiritual gifts' (the standard English for the Pauline charismata,
    used throughout this corpus, even though the word alone is 'gifts/graces'); γλῶσσαι ->
    'tongues'; προφητεία -> 'prophecy'; οἰκοδομή -> 'edification'. Do NOT flag the settled gloss
    as an addition.
  - SCRIPTURE IN ORIGEN'S OWN GREEK (LXX / NT) is the arbiter -- Psalms in LXX numbering, the
    historical books as the LXX 'Kingdoms'. Where our English renders Jenkins's printed Greek and
    it differs from a modern Bible or a manuscript variant, that is CORRECT, never a defect.
  - CATENA / FRAGMENT SEAMS: a fragment may begin or end abruptly (it is an excerpt); there is NO
    uniform doxology. Rendering the seam as it stands is correct, not a truncation.
  - SETTLED CRUXES (already adjudicated against the Greek at R6 -- do NOT re-flag): the four R6
    emendations, which ARE the base reading now -- § VI (frag06) `χριστοῦ` and `λέγω`, § XII
    (frag12) `γραφαῖς`, § LXXXIX (frag89) `τοῦ τόπου`; the daggered cruxes § XV (frag15)
    `†αἱ μὲν ῥίζαι†` and § XXXV (frag35, two †…† + a "something seems missing" gap) stay daggered
    and are rendered as they stand (NOT garbled/untranslated); § XLIII (frag43) the body citation
    `ἵνα πάντας ἢ τινὰς σώσω` vs the lemma `ἵνα πάντως τινὰς σώσω` are BOTH faithful (a genuine
    Origenic variant -- do NOT harmonize); § L (frag50) `καυχήσωμαι` is correct (Origen's own
    gloss vindicates it).

MODES
  * DEFAULT (report AND auto-fix in place): structure table, then per-fragment fidelity score,
    grade, and an itemised, severity-ranked finding list, plus a batch summary -- AND it applies,
    in place, every finding that carries a precise, safe edit (ANY category). A fix is applied
    only when it is safe: its `old` string is copied verbatim from our English and occurs EXACTLY
    once, and after the replacement the guillemets stay balanced, the `* *` marks stay even, the
    `[[ ]]` stay balanced, the `† †` stay even, and the paragraph/block count is unchanged.
    Findings with no concrete edit are reported but left for you. The English files are
    git-tracked -- REVIEW THE DIFF (`git diff`) and revert any edit you disagree with.
  * --report-only (a.k.a. --dry-run): report exactly as above but WRITE NOTHING.
  * --structure-only: run ONLY the deterministic structure/truncation check (no API calls).

    python3 validate_origen_1corinthians_translation.py                      # report + auto-fix all
    python3 validate_origen_1corinthians_translation.py frag11_english.txt   # report + auto-fix one
    python3 validate_origen_1corinthians_translation.py --report-only        # report only, no edits
    python3 validate_origen_1corinthians_translation.py --structure-only     # cheap truncation triage
    python3 validate_origen_1corinthians_translation.py --quiet              # grade lines only

    --report-only    report but DO NOT edit any file (alias: --dry-run)
    --structure-only run only the deterministic structure/truncation check (no API calls)
    --quiet          print each fragment's score line but not its finding list
    --log-dir DIR    where to write per-call transcripts (default: ./validation_logs_1corinthians)
    --no-log         do not write transcripts

The Greek base is NEVER modified. Only `english/fragNN_english.txt` is read, and (unless
--report-only) edited in place with every safe, concrete fix.
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
SOURCE_DIR = os.path.join(BASE, "GREEK")             # our Greek base -- the ARBITER
TARGET_DIR = os.path.join(BASE, "english")           # our English (the thing being validated)

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "validation_logs_1corinthians")

AUTHOR = "Origen of Alexandria"
WORK = "Commentary on the First Epistle to the Corinthians (Greek catena fragments)"
SOURCE_NOTE = (
    "the Greek catena fragments constituted by Claude Jenkins, JTS 9-10 (1908-09)"
)

# Per-fragment 1 Corinthians reference, for the score line. (§ XLVIII is a compound double
# lemma, xii 8-10 + xii 27-28. The 29 Athos-Pantocrator §§ carry a * on the heading; the ref
# string here is display-only, so it is left unstarred -- the file's own heading shows the *.)
FRAG_META = {
     1: "1 Cor. i 2",           2: "1 Cor. i 4-10",        3: "1 Cor. i 9",
     4: "1 Cor. i 10",          5: "1 Cor. i 14, 17",      6: "1 Cor. i 18",
     7: "1 Cor. i 19-21",       8: "1 Cor. i 23-31",       9: "1 Cor. ii 4-7",
    10: "1 Cor. ii 9-11",      11: "1 Cor. ii 12-15",     12: "1 Cor. iii 1-3 a",
    13: "1 Cor. iii 3-5",      14: "1 Cor. iii 6-8",      15: "1 Cor. iii 9-15",
    16: "1 Cor. iii 16-20",    17: "1 Cor. iii 21-23",    18: "1 Cor. iv 1-5",
    19: "1 Cor. iv 6-8",       20: "1 Cor. iv 9-10",      21: "1 Cor. iv 15",
    22: "1 Cor. iv 19-20",     23: "1 Cor. iv 21-v 2",    24: "1 Cor. v 3-5",
    25: "1 Cor. v 7-8",        26: "1 Cor. v 9-11",       27: "1 Cor. vi 1-3",
    28: "1 Cor. vi 12",        29: "1 Cor. vi 13-14",     30: "1 Cor. vi 15",
    31: "1 Cor. vi 18",        32: "1 Cor. vi 19-20",     33: "1 Cor. vii 1-4",
    34: "1 Cor. vii 5",        35: "1 Cor. vii 8-12",     36: "1 Cor. vii 14",
    37: "1 Cor. vii 18-20",    38: "1 Cor. vii 21-24",    39: "1 Cor. vii 25",
    40: "1 Cor. ix 7-9",       41: "1 Cor. ix 9-11",      42: "1 Cor. ix 16",
    43: "1 Cor. ix 19-23",     44: "1 Cor. ix 24",        45: "1 Cor. x 5",
    46: "1 Cor. x 6",          47: "1 Cor. xii 3",        48: "1 Cor. xii 8-10 (+ xii 27-28)",
    49: "1 Cor. xiii 1-2",     50: "1 Cor. xiii 3",       51: "1 Cor. xiii 4-5",
    52: "1 Cor. xiii 8",       53: "1 Cor. xiii 9-12",    54: "1 Cor. xiv 5 *",
    55: "1 Cor. xiv 6 *",      56: "1 Cor. xiv 7-9 a *",  57: "1 Cor. xiv 9 b *",
    58: "1 Cor. xiv 10 *",     59: "1 Cor. xiv 11 *",     60: "1 Cor. xiv 12 *",
    61: "1 Cor. xiv 13-14 *",  62: "1 Cor. xiv 15-17 *",  63: "1 Cor. xiv 18-19 *",
    64: "1 Cor. xiv 20 *",     65: "1 Cor. xiv 21 *",     66: "1 Cor. xiv 24-25 *",
    67: "1 Cor. xiv 26-27 *",  68: "1 Cor. xiv 29 *",     69: "1 Cor. xiv 30-31 *",
    70: "1 Cor. xiv 32 *",     71: "1 Cor. xiv 34-35 *",  72: "1 Cor. xiv 37-38 *",
    73: "1 Cor. xiv 31",       74: "1 Cor. xiv 34-35",    75: "1 Cor. xiv 37-38",
    76: "1 Cor. xv 1-2",       77: "1 Cor. xv 5 *",       78: "1 Cor. xv 9 *",
    79: "1 Cor. xv 10 *",      80: "1 Cor. xv 11 *",      81: "1 Cor. xv 12-13 *",
    82: "1 Cor. xv 14 *",      83: "1 Cor. xv 15-16 *",   84: "1 Cor. xv 20-23",
    85: "1 Cor. xv 31 *",      86: "1 Cor. xv 32 *",      87: "1 Cor. xv 35-38",
    88: "1 Cor. xv 51 *",      89: "1 Cor. xvi 10-12",    90: "1 Cor. xvi 13-14",
}

FILE_RE = re.compile(r"^frag\d+_english\.txt$")
SEP_RE = re.compile(r"^=+$")

# Source (Greek) header parsing, mirroring the translator's parse_fragment. The § heading may
# carry a trailing Athos siglum `*`.
JTS_ANCHOR_RE = re.compile(r"\[JTS[^\]]*\]")
GREEK_HEADING_RE = re.compile(r"^§\s*([IVXLCDM]+)\*?\s*\|")
LEMMA_LINE_RE = re.compile(r"^LEMMA:\s*(.*)$")
GREEK_SEP_RE = re.compile(r"^=+\s*$")
# English body heading block: "§ <ROMAN>[*] — 1 Corinthians <ref>".
ENG_HEADING_RE = re.compile(r"^§\s+[IVXLCDM]+\*?\b")

RETRY_DELAYS = [5, 15, 45]
RATE_LIMIT_DELAYS = [60, 120, 240]

# Structure-check thresholds.
SHORT_BLOCK_RATIO = 0.55   # an English block below this * its Greek length is a truncation suspect
                           # (Greek is far more compact than English, so the floor is lower than
                           # the Latin validator's 0.70)
SHORT_MIN_GREEK = 200      # ...but only worry about blocks whose Greek is at least this long
                           # (short lemma / sub-lemma / rubric lines swing wildly, not truncation)


# --- IO / body extraction -----------------------------------------------------


def parse_text(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def english_body(raw):
    """Return the English reading body: drop the leading `#`-comment provenance header and the
    `=`-run separator line, then the content that follows."""
    lines = raw.split("\n")
    out, started = [], False
    for ln in lines:
        s = ln.strip()
        if not started and (s.startswith("#") or SEP_RE.match(s) or s == ""):
            continue
        started = True
        out.append(ln)
    return "\n".join(out).strip()


def paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def frag_num_of(path):
    m = re.search(r"frag(\d+)", os.path.basename(path))
    return int(m.group(1)) if m else None


def source_path_for(english_file):
    n = frag_num_of(english_file)
    return os.path.join(SOURCE_DIR, f"frag{n:02d}_greek.txt")  # zero-padded


# --- Greek-body parsing (for the deterministic structure check) ---------------


def greek_blocks(greek_raw):
    """The Greek translatable blocks, mirroring the translation script's parse_fragment: strip
    the four-line header (§ / [Cramer] / LEMMA: / ====), take the LEMMA content as block 0, then
    each non-empty body line as a further block. Returns (lemma_or_None, [blocks])."""
    raw = JTS_ANCHOR_RE.sub("", greek_raw)
    lines = raw.split("\n")
    lemma = None
    sep_idx = None
    for i, line in enumerate(lines):
        m = LEMMA_LINE_RE.match(line)
        if m and lemma is None:
            lemma = m.group(1).strip()
            continue
        if GREEK_SEP_RE.match(line):
            sep_idx = i
            break
    body_lines = lines[sep_idx + 1:] if sep_idx is not None else []
    body_blocks = [l.strip() for l in body_lines if l.strip()]
    blocks = ([lemma] if lemma is not None else []) + body_blocks
    return lemma, [b for b in blocks if b]


def english_content_blocks(english_raw):
    """The English blocks that align 1:1 with the Greek blocks: paragraphs of the body with the
    leading `§ <ROMAN>[*] — 1 Corinthians <ref>` heading block dropped. Returns
    (all_blocks, content), where content[0] is the `LEMMA: …` line aligning with the Greek
    lemma."""
    blocks = paragraphs(english_body(english_raw))
    lead = 1 if (blocks and ENG_HEADING_RE.match(blocks[0])) else 0
    return blocks, blocks[lead:]


# --- Deterministic structure / truncation check -------------------------------


def structure_report(english_file):
    """Compare Greek vs English block-by-block with no API call. Returns a dict with the block
    counts, per-block ratios, and a list of mechanical issues (dropped/truncated/mid-sentence)."""
    n = frag_num_of(english_file)
    source_file = source_path_for(english_file)
    if not (os.path.exists(english_file) and os.path.getsize(english_file) > 0):
        return {"n": n, "status": "missing-english", "issues": ["English file missing or empty"]}
    if not os.path.exists(source_file):
        return {"n": n, "status": "missing-greek", "issues": ["Greek source not found"]}

    graw, eraw = parse_text(source_file), parse_text(english_file)
    _lemma, gblocks = greek_blocks(graw)
    eall, econtent = english_content_blocks(eraw)

    expected_e = 1 + len(gblocks)   # 1 heading block + (lemma + body-line blocks)
    issues = []
    if eall and not ENG_HEADING_RE.match(eall[0]):
        issues.append("first English block is not the '§ … — 1 Corinthians …' heading "
                      "-- heading may be merged into the lemma")
    if len(eall) != expected_e:
        issues.append(f"BLOCK COUNT {len(eall)} vs expected {expected_e} "
                      f"(greek blocks={len(gblocks)}) -- a block may be dropped, split, or merged")

    ratios = []
    pairs = min(len(gblocks), len(econtent))
    for i in range(pairs):
        gb, eb = gblocks[i], econtent[i]
        # strip the "LEMMA: " label from block 0 so it doesn't inflate the ratio
        eb_cmp = eb[len("LEMMA:"):].strip() if i == 0 and eb.startswith("LEMMA:") else eb
        r = len(eb_cmp) / len(gb) if gb else 9.0
        ratios.append(r)
        if len(gb) >= SHORT_MIN_GREEK and r < SHORT_BLOCK_RATIO:
            issues.append(f"block #{i}: English {len(eb_cmp)}c is {r:.2f}x its Greek {len(gb)}c "
                          f"-- possible truncation")
        # mid-sentence cutoff, but ONLY a real truncation: catena excerpts CAN end abruptly, so we
        # flag an English block that stops mid-sentence ONLY when its aligned Greek block actually
        # COMPLETED its sentence. Trailing marks/space (« * ' ) ] ⟩ † and the ]] close) are ignored
        # on both sides before the last meaningful character is tested.
        eng_core = re.sub(r"[\s»«⟨⟩*'\"“”‘’)\]\[†]+$", "", eb)
        grk_core = re.sub(r"[\s»«⟨⟩*'\"“”‘’)\]\[†]+$", "", gb)
        eng_open = eng_core and eng_core[-1] not in ".!?…·;:"
        grk_closed = grk_core and grk_core[-1] in ".!?·;"
        if len(gb) >= SHORT_MIN_GREEK and eng_open and grk_closed:
            issues.append(f"block #{i}: ends mid-sentence (Greek block completes) -> "
                          f"…{eb[-45:]!r}")

    return {
        "n": n, "status": "ok",
        "greek_blocks": len(gblocks), "english_blocks": len(eall),
        "expected_english": expected_e, "ratios": ratios,
        "min_ratio": min(ratios) if ratios else None,
        "issues": issues,
    }


def print_structure(rep):
    n = rep["n"]
    ref = FRAG_META.get(n, "")
    head = f"  frag{n:02d} ({ref})" if ref else f"  frag{n:02d}"
    if rep["status"] != "ok":
        print(f"{head}: {rep['status'].upper()} -- {'; '.join(rep['issues'])}")
        return bool(rep["issues"])
    mr = rep["min_ratio"]
    mr_s = f"{mr:.2f}" if mr is not None else "--"
    flag = "OK" if not rep["issues"] else f"{len(rep['issues'])} ISSUE(S)"
    print(f"{head}: greek {rep['greek_blocks']} blk / english {rep['english_blocks']} blk "
          f"(exp {rep['expected_english']}), min block ratio {mr_s}  ->  {flag}")
    for iss in rep["issues"]:
        print(f"        - {iss}")
    return bool(rep["issues"])


# --- Prompt -------------------------------------------------------------------


def build_prompt(frag_num, cor_ref, greek_text, english_text, reminder=""):
    ref_hint = f" (on {cor_ref})" if cor_ref else ""
    return (
        f"You are VALIDATING an English translation against its GREEK SOURCE for fidelity. The "
        f"work is {AUTHOR}'s {WORK} -- {SOURCE_NOTE}, base MS Vatican gr. 762 (with 29 fragments "
        f"from MS Athos Pantocrator 28); Origen's commentary survives only as excerpts in the "
        f"medieval Greek exegetical chains (catenae). You are checking FRAGMENT "
        f"{frag_num}{ref_hint}.\n\n"

        "THE GREEK IS THE SOLE ARBITER. The single question is: does the ENGLISH faithfully and "
        "COMPLETELY render what the GREEK says, in the sense Origen's own argument requires? Read "
        "the whole fragment so you can catch internal inconsistencies (e.g. the same Greek word "
        "rendered incompatibly in a lemma and in Origen's later gloss of it). Do NOT use any "
        "outside Bible or translation; judge ONLY English-against-Greek.\n\n"

        "WHAT COUNTS AS A FINDING (a real fidelity defect in the ENGLISH):\n"
        "  - OMISSION: a Greek clause/word whose sense is absent from the English.\n"
        "  - ADDITION: content in the English whose sense is not in the Greek.\n"
        "  - MISTRANSLATION / SENSE-SHIFT: wrong sense of a word, flipped negation, altered "
        "subject/object or referent, an allegorical identification the Greek does not support.\n"
        "  - SCRIPTURE: a quoted verse whose English wording misrenders the Greek quotation as "
        "printed (Origen's Greek is the arbiter -- NOT any modern Bible).\n"
        "  - NAME/REFERENT: a name rendered so the person/place referred to differs from the "
        "Greek's.\n"
        "  - INCONSISTENCY: the same Greek word/phrase rendered incompatibly in two places, or "
        "the English contradicting itself where the Greek is coherent.\n"
        "  - UNTRANSLATED / GARBLED: Greek left untranslated, or an incoherent English stretch.\n\n"

        "WHAT DOES NOT COUNT (never flag these -- they are correct by the base's own rules):\n"
        "  - Independent WORDING/STYLE: synonyms, clause order, sentence length, register, "
        "broken-up long periods -- when the MEANING matches. The English wording is its own; only "
        "meaning counts. Do not rewrite for taste.\n"
        "  - Our EDITORIAL MARKS: Scripture in »…«, the 1 Corinthians lemma word(s) in *…*. Marks "
        "are not meaning; never flag their presence. Whether the header LEMMA line keeps or drops "
        "Jenkins's `[ … ]` wrap around the verse is a presentation mark, NOT a fidelity defect.\n"
        "  - KEPT BRACKETS that belong to the reading text: the catenist ATTRIBUTION RUBRIC "
        "`[Of Origen]` (the one rubric form here), the SUB-LEMMA verse labels (`[iv 16]`, "
        "`[vi 9-10]`, `[vii 28 a]`, …), and the DOUBLE BRACKETS `[[ … ]]` (frag48's first lemma, "
        "1 Cor xii 8-10; frag81's gloss naming the Manichaeans). Keeping these is CORRECT.\n"
        "  - THE OBELIZED CRUXES `† … †` (frag15, frag35): daggers fence text Jenkins marks as "
        "corrupt. They are marks, not meaning -- never flag their presence, and do NOT flag the "
        "daggered words as garbled/untranslated; they are rendered as best they stand.\n"
        "  - EDITOR'S SUPPLEMENTS ⟨ … ⟩ and SECLUSIONS [ … ] (mid-text -- only `[Χριστοῦ]` and "
        "`[μὴ]`) read in sense WITHOUT printing the brackets -- correct, not omission/addition.\n"
        "  - PRINTED LACUNAE `. . .` or `…`: kept as they stand and NOT filled -- keeping the gap "
        "is correct, never an omission.\n"
        "  - STANDARD-ENGLISH NAME NORMALIZATION of the Greek forms (Ἰησοῦς->Jesus, Παῦλος->Paul, "
        "Ἀπολλώς->Apollos, Κηφᾶς->Cephas, Τιμόθεος->Timothy, Κορίνθιοι->the Corinthians, "
        "Μωσῆς->Moses, Ἡσαΐας->Isaiah, Ἀκύλας/Σύμμαχος/Θεοδοτίων->Aquila/Symmachus/Theodotion, "
        "Μανιχαῖοι->the Manichaeans, etc.). Same referent = not a defect.\n"
        "  - KEPT-AND-GLOSSED GREEK TERMS where Origen etymologizes or draws a load-bearing "
        "contrast, above all §XI (frag11) ψυχικός ('the natural/unspiritual man') vs πνευματικός "
        "('the spiritual man'). Keeping BOTH distinct with a gloss is CORRECT; flag it ONLY if "
        "the English actually collapses or swaps the two senses.\n"
        "  - SETTLED HOUSE RENDERINGS of recurring vocabulary (a consistent gloss used throughout "
        "this corpus, NOT an addition): χαρίσματα -> 'spiritual gifts' (the standard English for "
        "the Pauline charismata, even though the bare word is 'gifts/graces'); γλῶσσαι -> "
        "'tongues'; προφητεία -> 'prophecy'; οἰκοδομή -> 'edification'. Do NOT flag the settled "
        "gloss as an addition.\n"
        "  - SCRIPTURE IN ORIGEN'S OWN GREEK (LXX / NT), Psalms in LXX numbering, historical books "
        "as the LXX 'Kingdoms'. Where the English renders Jenkins's printed Greek and it differs "
        "from a modern Bible or a manuscript variant, that is CORRECT (the Greek is the arbiter), "
        "never a defect.\n"
        "  - CATENA / FRAGMENT SEAMS: a fragment may begin or end abruptly (it is an excerpt); "
        "there is NO uniform doxology. Rendering the seam as it stands is correct.\n"
        "  - SETTLED CRUXES (already adjudicated at R6 -- do NOT re-flag): the R6 emendations that "
        "ARE the base reading now -- frag06 `χριστοῦ` and `λέγω`, frag12 `γραφαῖς`, frag89 "
        "`τοῦ τόπου`; the daggered cruxes frag15 `†αἱ μὲν ῥίζαι†` and frag35 (two †…†) stay "
        "daggered; frag43 the body citation `ἵνα πάντας ἢ τινὰς σώσω` vs the lemma `ἵνα πάντως "
        "τινὰς σώσω` are BOTH faithful (a genuine Origenic variant -- do NOT harmonize); frag50 "
        "`καυχήσωμαι` is correct.\n\n"

        "For each genuine finding, when (and ONLY when) a precise, minimal, SAFE correction "
        "exists, include a `fix` object with:\n"
        "  - `old`: a VERBATIM substring copied EXACTLY from OUR ENGLISH (include enough "
        "surrounding words that it occurs EXACTLY ONCE in the English; keep any »…« / *…* / "
        "[[…]] / †…† / bracket marks intact inside it),\n"
        "  - `new`: the corrected English (same marks preserved; change only what the fidelity "
        "defect requires; keep the surrounding words identical).\n"
        "Make `new` internally consistent with the rest of the fragment. If no safe minimal edit "
        "is possible (the fix would need rephrasing across a whole sentence, or it is a judgement "
        "call), OMIT the `fix` object and just describe the finding.\n\n"

        "OUTPUT -- STRICT JSON ONLY. Emit a single JSON object and NOTHING else (no prose, no "
        "code fence). Schema:\n"
        "{\n"
        '  "score": <integer 0-100: how faithfully & completely our English renders the Greek; '
        "100 = every point of the Greek's meaning conveyed with none added, 0 = unrelated>,\n"
        '  "grade": "<letter A+ .. F matching the score>",\n'
        '  "fidelity": "<high|moderate|low>",\n'
        '  "findings": [\n'
        "    {\n"
        '      "locus": "<short anchor phrase from OUR English>",\n'
        '      "severity": "<minor|moderate|significant>",\n'
        '      "category": "<omission|addition|mistranslation|sense-shift|scripture|name|'
        'inconsistency|untranslated>",\n'
        '      "greek": "<the Greek phrase at issue>",\n'
        '      "ours": "<how our English renders it>",\n'
        '      "issue": "<one line: what is wrong / how the meaning drifts from the Greek>",\n'
        '      "fix": { "old": "<verbatim unique English substring>", "new": "<corrected>" }\n'
        "    }\n"
        "  ],\n"
        '  "summary": "<1-3 sentences: overall fidelity to the Greek, and the most important '
        "findings if any>\"\n"
        "}\n"
        "List findings MOST SEVERE FIRST. If our English faithfully renders the Greek throughout, "
        "return an empty \"findings\" array and a high score -- do NOT invent defects, and do NOT "
        "flag any of the house-rule items above. The `fix` field is OPTIONAL per finding; include "
        "it only for a safe minimal edit. Keep quoted snippets brief.\n"
        f"{reminder}"
        "\n"
        "=== GREEK SOURCE (the arbiter; Jenkins JTS 1908-09 reading text, MS Vatican gr. 762) ===\n"
        f"{greek_text}\n"
        "\n"
        "=== OUR ENGLISH TRANSLATION (the one being validated) ===\n"
        f"{english_text}\n"
    )


# --- CLI call -----------------------------------------------------------------


def is_rate_limit_error(stderr):
    lower = stderr.lower()
    return any(term in lower for term in
               ["rate limit", "rate_limit", "overloaded", "too many requests", "529"])


def call_claude(prompt):
    """One CLI call with rate-limit-aware retry/backoff. Returns stdout text. No tools are
    needed (both texts are pasted), so this is a plain text-in/JSON-out call."""
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
                f"Validation call failed after retries: rc={result.returncode} "
                f"stderr={result.stderr.strip()[:200]} stdout={result.stdout.strip()[:200]}")
    raise RuntimeError("Unreachable")


# --- Finding parsing ----------------------------------------------------------


def extract_json(text):
    """Pull the JSON object out of a model reply, tolerating a code fence or stray prose."""
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


def normalize(obj):
    """Coerce a parsed result dict into a predictable shape (fills sane defaults)."""
    score = obj.get("score")
    try:
        score = max(0, min(100, int(round(float(score)))))
    except (TypeError, ValueError):
        score = None
    raw = obj.get("findings")
    raw = raw if isinstance(raw, list) else []
    findings = []
    for d in raw:
        if not isinstance(d, dict):
            continue
        fix = d.get("fix")
        clean_fix = None
        if isinstance(fix, dict) and fix.get("old") and fix.get("new") is not None:
            clean_fix = {"old": str(fix["old"]), "new": str(fix["new"])}
        findings.append({
            "locus": str(d.get("locus", "?")),
            "severity": str(d.get("severity", "moderate")).lower(),
            "category": str(d.get("category", "mistranslation")).lower(),
            "greek": str(d.get("greek", d.get("latin", ""))),
            "ours": str(d.get("ours", "")),
            "issue": str(d.get("issue", d.get("note", ""))),
            "fix": clean_fix,
        })
    return {
        "score": score,
        "grade": str(obj.get("grade", "")).strip() or letter_for(score),
        "fidelity": str(obj.get("fidelity", "")).strip().lower(),
        "findings": findings,
        "summary": str(obj.get("summary", "")).strip(),
    }


SEV_ORDER = {"significant": 0, "moderate": 1, "minor": 2}


def validate_whole(frag_num, cor_ref, greek_body, english_text, log_base=None):
    """One validation call; parse its JSON, retrying once if the reply is not valid JSON.
    Returns a normalized result dict, or None if it could not be parsed."""

    def call(prompt, attempt):
        raw = call_claude(prompt)
        if log_base:
            with open(f"{log_base}.{attempt}.txt", "w", encoding="utf-8") as f:
                f.write(f"# fragment={frag_num} attempt={attempt} "
                        f"prompt_chars={len(prompt)}\n\n{raw}\n")
        return raw

    raw = call(build_prompt(frag_num, cor_ref, greek_body, english_text), 1)
    obj = extract_json(raw)
    if obj is None:
        print("    Reply was not valid JSON -- retrying once for a clean object...")
        reminder = ("IMPORTANT: your previous reply could not be parsed. Output ONE JSON object "
                    "and nothing else -- no prose, no code fence.\n")
        raw = call(build_prompt(frag_num, cor_ref, greek_body, english_text,
                                reminder=reminder), 2)
        obj = extract_json(raw)
    if obj is None:
        return None
    return normalize(obj)


# --- Fix application ----------------------------------------------------------


def marks_ok(text):
    """Post-fix invariants: guillemets balanced, lemma asterisks even, double-brackets balanced,
    dagger cruxes even. The Athos siglum `*` on a `§ <ROMAN>*` heading line is NOT a lemma-word
    mark, so it is stripped before the asterisk-parity test -- otherwise every one of the 29 Athos
    fragments reads odd and the auto-fixer would reject every fix on them."""
    stars = re.sub(r"(?m)^§\s+[IVXLCDM]+\*", "", text)
    return (text.count("»") == text.count("«")
            and stars.count("*") % 2 == 0
            and text.count("[[") == text.count("]]")
            and text.count("†") % 2 == 0)


def apply_fixes(english_file, findings):
    """Apply EVERY safe, validated fix to the English file in place, of any category. A fix is
    applied only if: it carries `old`/`new`; `old` occurs EXACTLY once in the file; and after
    replacement the guillemets stay balanced, the `* *` stay even, the `[[ ]]` stay balanced, the
    `† †` stay even, and the paragraph/block count is unchanged. Findings with no concrete edit
    are reported as skipped. Returns (applied, skipped) as lists of (finding, reason)."""
    raw = parse_text(english_file)
    body0 = english_body(raw)
    n_blocks0 = len(paragraphs(body0))

    applied, skipped = [], []
    text = raw
    for f in findings:
        fix = f.get("fix")
        if not fix:
            skipped.append((f, "no concrete/safe edit proposed -- left for manual review"))
            continue
        old, new = fix["old"], fix["new"]
        if old == new:
            skipped.append((f, "old == new"))
            continue
        count = text.count(old)
        if count == 0:
            skipped.append((f, "`old` not found (already fixed or misquoted)"))
            continue
        if count > 1:
            skipped.append((f, f"`old` not unique ({count} matches)"))
            continue
        candidate = text.replace(old, new, 1)
        cbody = english_body(candidate)
        if not marks_ok(cbody):
            skipped.append((f, "would unbalance » «, * *, [[ ]], or † † marks"))
            continue
        if len(paragraphs(cbody)) != n_blocks0:
            skipped.append((f, "would change the paragraph/block count"))
            continue
        text = candidate
        applied.append((f, f"{old!r} -> {new!r}"))

    if applied and text != raw:
        with open(english_file, "w", encoding="utf-8") as fh:
            fh.write(text)
    return applied, skipped


# --- Reporting ----------------------------------------------------------------

SEV_TAG = {"significant": "!!", "moderate": "! ", "minor": ". "}


def print_result(result, quiet=False):
    score = result["score"]
    score_str = f"{score}" if score is not None else "--"
    nf = len(result["findings"])
    sig = sum(1 for d in result["findings"] if d["severity"] == "significant")
    print(f"  FIDELITY: {result['grade']:>2}  ({score_str}/100, "
          f"{result['fidelity'] or '?'})  ·  {nf} finding(s), {sig} significant")
    if result["summary"]:
        print(f"  {result['summary']}")
    if quiet or not result["findings"]:
        return
    ordered = sorted(result["findings"], key=lambda d: SEV_ORDER.get(d["severity"], 9))
    for d in ordered:
        tag = SEV_TAG.get(d["severity"], "  ")
        fixmark = " [fix]" if d.get("fix") else ""
        print(f"    {tag} [{d['severity']}/{d['category']}]{fixmark} {d['locus']}")
        if d["greek"]:
            print(f"         Greek: {d['greek'][:150]}")
        if d["ours"]:
            print(f"         Ours:  {d['ours'][:150]}")
        if d["issue"]:
            print(f"         -> {d['issue'][:150]}")


# --- Driver -------------------------------------------------------------------


def resolve_input(arg):
    if os.path.isabs(arg) or os.sep in arg:
        return arg
    return os.path.join(TARGET_DIR, arg)


def validate_file(english_file, quiet=False, log_dir=LOG_DIR, do_fix=True):
    """Validate one fragment's English against its Greek. Returns a result dict for the batch
    summary. Reads the Greek (never modifies it); edits the English in place with every safe fix
    unless do_fix is False (--report-only)."""
    n = frag_num_of(english_file)
    cor_ref = FRAG_META.get(n)
    source_file = source_path_for(english_file)

    print(f"\n{'=' * 60}")
    print(f"Validate: {os.path.basename(english_file)}" + (f"  ({cor_ref})" if cor_ref else ""))
    print(f"  ours:  {english_file}")
    print(f"  greek: {source_file}  (the arbiter)")
    print(f"{'=' * 60}")

    if not os.path.exists(english_file) or os.path.getsize(english_file) == 0:
        print("  Our English missing or empty -- unvalidated.")
        return {"file": english_file, "status": "unvalidated", "result": None}
    if not os.path.exists(source_file):
        print(f"  Greek source not found: {source_file} -- unvalidated.")
        return {"file": english_file, "status": "unvalidated", "result": None}

    # Deterministic structure/truncation check first (free).
    rep = structure_report(english_file)
    print_structure(rep)

    eng_body = english_body(parse_text(english_file))
    grk_body = parse_text(source_file).strip()  # send the whole Greek file (header + body)

    log_base = None
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        log_base = os.path.join(
            log_dir, os.path.splitext(os.path.basename(english_file))[0])
        print(f"  Transcript log: {log_base}.<attempt>.txt")

    result = validate_whole(n, cor_ref, grk_body, eng_body, log_base=log_base)
    if result is None:
        print("  Could not obtain a parseable result -- skipped.")
        return {"file": english_file, "status": "unparseable", "result": None, "structure": rep}

    print_result(result, quiet=quiet)

    if do_fix and result["findings"]:
        applied, skipped = apply_fixes(english_file, result["findings"])
        print(f"\n  auto-fix: applied {len(applied)}, skipped {len(skipped)}.")
        for f, how in applied:
            print(f"     ✓ [{f['category']}] {how[:180]}")
        for f, why in skipped:
            print(f"     - [{f['category']}] {f['locus'][:60]}  ({why})")
        result["_applied"] = len(applied)
        result["_skipped"] = len(skipped)
        if applied:
            nb = english_body(parse_text(english_file))
            print(f"  Post-fix: marks {'OK' if marks_ok(nb) else 'BROKEN!'}, "
                  f"{len(paragraphs(nb))} block(s). Review with `git diff`.")

    return {"file": english_file, "status": "validated", "result": result, "structure": rep}


def order_key(name):
    n = frag_num_of(name)
    return n if n is not None else 999


def collect_files(path):
    if os.path.isdir(path):
        return [os.path.join(path, f)
                for f in sorted(os.listdir(path), key=order_key)
                if FILE_RE.match(f)]
    return [path]


def run_structure_only(files):
    """Deterministic structure/truncation triage across the given files -- no API calls."""
    print(f"STRUCTURE / TRUNCATION CHECK (deterministic, no API) -- {len(files)} file(s)")
    print("Arbiter: our Jenkins JTS 1908-09 Greek base. Flags dropped/truncated/mid-sentence "
          "blocks.\n")
    any_issue = False
    clean = 0
    for f in files:
        rep = structure_report(f)
        had = print_structure(rep)
        any_issue = any_issue or had
        if rep["status"] == "ok" and not had:
            clean += 1
    print(f"\n  {clean}/{len(files)} file(s) structurally clean.")
    if any_issue:
        print("  Some files have structural issues (see above) -- inspect those first "
              "(note: catena fragments may legitimately end abruptly).")
    else:
        print("  No dropped or truncated blocks detected: every fragment has its full block "
              "count and full-length blocks.")
    return 0 if not any_issue else 1


def print_summary(results, did_fix):
    print(f"\n{'=' * 60}\nVALIDATION SUMMARY (arbiter: our Jenkins JTS 1908-09 Greek base)"
          f"\n{'=' * 60}")
    validated = [r for r in results if r["status"] == "validated"]
    scores = [r["result"]["score"] for r in validated if r["result"]["score"] is not None]
    for r in results:
        name = os.path.basename(r["file"])
        if r["status"] != "validated":
            print(f"  {name:28}  {r['status'].upper()}")
            continue
        g = r["result"]
        score = g["score"]
        score_str = f"{score:3d}" if score is not None else " --"
        nf = len(g["findings"])
        sig = sum(1 for d in g["findings"] if d["severity"] == "significant")
        struct = r.get("structure") or {}
        st = "" if not struct.get("issues") else f"  [struct: {len(struct['issues'])}]"
        extra = ""
        if did_fix:
            extra = f"  [fixed {g.get('_applied', 0)}, skipped {g.get('_skipped', 0)}]"
        print(f"  {name:28}  {g['grade']:>2}  {score_str}/100  "
              f"({nf} find, {sig} sig){st}{extra}")
    if scores:
        avg = sum(scores) / len(scores)
        print(f"\n  Mean Greek-fidelity score: {avg:.1f}/100 "
              f"({letter_for(int(round(avg)))}) across {len(scores)} fragment(s).")
    total_sig = sum(sum(1 for d in r["result"]["findings"]
                        if d["severity"] == "significant") for r in validated)
    print(f"  Total significant findings: {total_sig}.")
    struct_flagged = [os.path.basename(r["file"]) for r in validated
                      if (r.get("structure") or {}).get("issues")]
    if struct_flagged:
        print(f"  Structure-flagged files: {', '.join(struct_flagged)}.")
    if did_fix:
        total_applied = sum(r["result"].get("_applied", 0) for r in validated)
        print(f"  Total fixes applied: {total_applied}. Review with `git diff` and revert any "
              f"you disagree with.")


def main():
    argv = sys.argv[1:]
    quiet = structure_only = False
    do_fix = True  # DEFAULT: report AND auto-apply every safe fix (see --report-only)
    log_dir = LOG_DIR
    positional = []
    it = iter(argv)
    for a in it:
        if a == "--quiet":
            quiet = True
        elif a == "--structure-only":
            structure_only = True
        elif a in ("--report-only", "--dry-run"):
            do_fix = False
        elif a in ("--fix", "--fix-all"):
            do_fix = True  # accepted for compatibility; auto-fix-all is already the default
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

    files = collect_files(raw_input)
    if not files:
        print("No English files found (expected frag<NN>_english.txt).")
        sys.exit(1)

    if structure_only:
        sys.exit(run_structure_only(files))

    mode = "REPORT + AUTO-FIX every safe edit in place" if do_fix else "report only (no edits)"
    print(f"Validating {len(files)} file(s) against our Jenkins JTS 1908-09 Greek base [{mode}]"
          + (f". Logs -> {log_dir}" if log_dir else " (logging off)"))
    if do_fix:
        print("  NOTE: auto-fix edits git-tracked English files in place. Review with `git diff` "
              "and revert any edit you disagree with (or use --report-only to preview).")
    results, failures = [], []
    for f in files:
        try:
            results.append(validate_file(f, quiet=quiet, log_dir=log_dir, do_fix=do_fix))
        except Exception as e:  # keep the batch going; report at the end
            print(f"  ERROR on {os.path.basename(f)}: {e}")
            failures.append((f, str(e)))

    if results:
        print_summary(results, did_fix=do_fix)
    if failures:
        print(f"\n{len(failures)} failure(s):")
        for f, e in failures:
            print(f"  FAILED: {os.path.basename(f)} -- {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

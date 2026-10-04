#!/usr/bin/env python3
"""Translate Origen's *Commentary on the First Epistle to the Corinthians* -- surviving only
as GREEK catena fragments (C. Jenkins, *JTS* 9-10, 1908-09) -- into English, one whole
fragment (§) at a time.

This is the near-exact twin of `translate_origen_ephesians_fragments.py` (same author, same
catena genre, same editor's conventions, same R7 per-fragment deliverable layout) and the
Greek-fragment sibling of the Rufinus-Latin homily translators: the same single-CLI-call-
per-unit flow, the same scaffolding cleanup, the same structural verify + one reminder retry
then a block-by-block fallback, the same rate-limit backoff, and the same optional page-scan
consultation. What differs from the Ephesians script is the SOURCE (Jenkins, not Gregg), the
90-fragment SPINE, the Athos `*` siglum on some § numbers, the single rubric form, the two
kinds of printed lacuna, the NAMES/VOCABULARY (1 Corinthians, not Ephesians), and the image
pipeline (Jenkins JTS page scans).

  1. SOURCE IS GREEK CATENA FRAGMENTS. Origen's commentary on 1 Corinthians does NOT survive
     as a running work; it survives only as excerpts preserved in the medieval Greek
     exegetical chains (*catenae*) on the Pauline epistles. The public-domain critical
     edition is Claude Jenkins, "Origen on I Corinthians," *Journal of Theological Studies*
     9 (1908) Parts I-III + 10 (1909) Part IV, base MS Vatican gr. 762. Jenkins numbers the
     fragments continuously in `§` sections; our base is a verified diplomatic polytonic-Greek
     transcription of Jenkins's PRINTED (adopted) text, 90 fragments, §§ I-XC, one file each
     `GREEK/fragNN_greek.txt`, driven through the full refinement pipeline (B image collation,
     R2 lensless re-collation, R4 boundaries, R1 the Cramer vol. V witness, R3 the Kovacs 2005
     oracle, R5 consistency/headers, R6 the apparatus pass -- four eclectic emendations, the
     text otherwise diplomatic -- and R7 the page-anchor strip). We render what the Greek says,
     as it says it; we do NOT harmonize the biblical quotations to a modern Bible.

  2. UNIT OF WORK IS A WHOLE FRAGMENT (§). Each `fragNN_greek.txt` (NN = 01..90, zero-padded)
     is one complete § section, translated in a single call. Most are short; the block-by-
     block fallback keeps the few long ones (frag02, frag08, frag15, frag16, frag18, frag19,
     frag35) safe.

  3. PLAIN-TEXT SHAPE. Each file is a FOUR-line header then the body:

         § XI  |  1 Cor. ii 12-15
         [Cramer 46-48]
         LEMMA: [Ἡμεῖς δὲ οὐ τὸ πνεῦμα τοῦ κόσμου ἐλάβομεν ...]
         ====================================================================
         [Ὠριγένους]
         [JTS-anchors were stripped in R7; the body is paragraphs / sub-lemma lines / rubrics]

     Parsing (all deterministic):
     * HEADER line 1 `§ <ROMAN>[*]  |  1 Cor. <ref>` -- held aside (never sent to the model);
       a canonical English heading `§ <ROMAN>[*] — 1 Corinthians <ref>` is re-emitted, the
       numeral taken from the FILENAME (so the § number can never be corrupted) and the ref
       from L1. The trailing `*` is the ATHOS SIGLUM (see rule 8): it marks the 29 fragments
       whose text comes from MS Athos Pantocrator 28, and it is re-emitted from a per-fragment
       flag so it survives on exactly those §§.
     * HEADER line 2 `[Cramer <n>]` -- traceability scaffolding: DISCARDED, never sent, not
       shown (mirrors the R7 reading-text deliverable, which keeps only what Ephesians keeps --
       and Ephesians's finished files keep the `[Cramer]` line, so we DO carry it in the Greek
       base, but the ENGLISH output, like the Ephesians English, drops it).
     * HEADER line 3 `LEMMA: …` -- the 1 Corinthians verse the fragment expounds. Its content
       is SENT to the model as translatable block 0 and re-emitted as `LEMMA: <translation>`.
       (Almost every lemma is wrapped in Jenkins's diplomatic `[ … ]`; the model drops those
       editor's brackets per the seclusion rule. Some lemmata carry a printed lacuna -- `. . .`
       or `…` -- which is kept, and small seclusions like `[Χριστοῦ]` / `[μὴ]`.)
     * HEADER line 4 `====…` -- separator: DISCARDED.
     * BODY: everything after `====`. The reliable unit here is the NON-EMPTY LINE (blank-line
       usage is INCONSISTENT across files, and no paragraph is soft-wrapped, so every paragraph
       / sub-lemma line / rubric is its own single physical line). Each non-empty body line is
       one translatable block; the output is normalized to one blank line between blocks.

  4. MARKUP carried in the base (all load-bearing, all handled in the prompt):
       »…«        Scripture Origen QUOTES (Greek)      -> keep the guillemets, translate wording
       *…*        the 1 Cor lemma word(s) in-body       -> keep the * marks, translate the words
       ⟨…⟩        editor's SUPPLEMENT                   -> read in the sense the grammar needs;
                                                           do NOT print the ⟨ ⟩ brackets
       […]        editor's SECLUSION (mid-text)         -> read in sense; do NOT print [ ]
                                                           (only [Χριστοῦ] frag02, [μὴ] frag19)
       [Ὠριγένους]   CATENIST ATTRIBUTION RUBRIC        -> KEEP the [ ] and translate
                     (the ONLY rubric form here, 96×)      ("[Of Origen]")
       [<ref>] <Greek>   SUB-LEMMA DISPLAY LINE         -> keep the [<ref>] label (e.g. [iv 16],
                          (e.g. [vii 28 a] …)              [vi 9-10], [vii 28 b]); translate the
                                                           Greek verse that follows as scripture
       [[ … ]]    a bracketed CATENA-SCHOLION / crux    -> keep the [[ ]] and translate: frag48's
                                                           first lemma (1 Cor xii 8-10) and
                                                           frag81's gloss naming the Manichaeans
       †…†        an OBELIZED CRUX (corrupt text)       -> keep the † daggers around it and
                                                           translate the daggered words as best
                                                           they stand (frag15, frag35)
       ‘…’ / '…'  a single-QUOTED word/term Origen cites -> keep a single quote, translate the
                                                           term (NB most ASCII ' are Greek
                                                           ELISION -- δι', ἀλλ', ἐπ' -- not quotes)
       . . .  / …  a printed LACUNA                      -> keep it as it stands, do NOT fill it
                   (both forms occur: spaced dots in frag05/07/08/14, the ellipsis char in frag48)
     PAGE ANCHORS `[JTS 9 p.N]` / `[JTS 10 p.N]` were stripped in R7; `strip_anchors` defensively
     removes any that remain. The anchor pattern matches ONLY `[JTS …]`, so the rubric / sub-
     lemma / seclusion / [[ ]] brackets are never touched.

  5. SCRIPTURE IS THE FIRST RULE. Origen quotes the LXX / NT in Greek and his argument turns on
     his exact wording. Translate every quotation AS IT STANDS in the Greek -- never substitute
     a modern Bible, never call a verse-lookup tool, never normalize to a standard version.
     PSALMS follow LXX numbering; the historical books are the LXX "Kingdoms". The 1 Corinthians
     lemmata themselves are Origen's Greek text of the epistle -- render them as they stand.

  6. NAMES & THEOLOGICAL VOCABULARY. Greek biblical names -> standard English (Ἰησοῦς Χριστός ->
     Jesus Christ, Παῦλος -> Paul, Ἀπολλώς -> Apollos, Κηφᾶς -> Cephas, Τιμόθεος -> Timothy,
     Κορίνθιοι -> the Corinthians, Μωσῆς -> Moses, Ἀκύλας/Σύμμαχος/Θεοδοτίων -> Aquila/Symmachus/
     Theodotion, Μανιχαῖοι -> the Manichaeans). Keep the recurring 1-Corinthians / Origenian
     vocabulary consistent (ψυχικός / πνευματικός -> the natural (unspiritual) man / the
     spiritual man -- the load-bearing contrast of §XI; χαρίσματα -> spiritual gifts; γλῶσσαι /
     γένη γλωσσῶν -> tongues / kinds of tongues; προφητεία -> prophecy; ἑρμηνεία -> interpretation;
     ἀνάστασις (νεκρῶν) -> the resurrection (of the dead); ἀγάπη -> love; σοφία τοῦ κόσμου / σοφία
     θεοῦ -> the wisdom of the world / the wisdom of God; μωρία -> foolishness; σχίσματα ->
     divisions; οἰκοδομή -> edification; ἐκκλησία -> the Church; ἑτερόδοξοι -> the heterodox).
     Where Origen ETYMOLOGIZES or puns on a Greek word, KEEP the Greek and gloss it.

  7. --images: CONSULT THE JENKINS PAGE SCANS (optional, OFF by default). Rendered under
     `_source/jenkins_pages/` as `jenkins_pt{I,II,III,IV}_p<PAGE>_leaf<NNNN>[_MARGIN].jpg`. The
     part (I/II/III = JTS 9 1908; IV = JTS 10 1909) and page span come from FRAG_META. `--images`
     hands a fragment its page scans and tells the model to open one when a reading looks
     impossible or mis-transcribed and follow Jenkins's printed Greek. Read the MAIN Greek text
     column; IGNORE the critical apparatus at the foot, the marginal Cramer numbers, running
     heads, and page numbers (skip the `_MARGIN` crops). Degrades gracefully to text-only if
     scans are absent.

  8. THE ATHOS SIGLUM `*`. Twenty-nine fragments (§§ LIV*-LXXII*, LXXVII*-LXXXIII*, LXXXV*,
     LXXXVI*, LXXXVIII*) carry a `*` on the § number: their text is drawn from MS Athos
     Pantocrator 28 (Jenkins's siglum A) rather than the Vatican base, and they carry no Cramer
     number. The `*` lives ONLY on the held-aside heading line (so it never reaches the model
     and never collides with the body clarendon `* *`); it is re-emitted on the English heading
     for exactly those §§, from the per-fragment `athos` flag in FRAG_META.

STRUCTURAL FINGERPRINT. The § heading is held aside (numeral from the filename, `*` from the
flag) and the anchors are gone, so per fragment we verify ONE thing: the number of translatable
blocks (the LEMMA + the non-empty body lines) returned equals the number sent. On mismatch (or
a suspiciously short output) we retry once with a block-count reminder; if it still fails we
fall back to translating each block on its own, which preserves the count by construction.

    python3 translate_origen_1corinthians_fragments.py frag11_greek.txt   # bare name
    python3 translate_origen_1corinthians_fragments.py /abs/path/file.txt # full path
    python3 translate_origen_1corinthians_fragments.py <directory>        # batch a dir
    python3 translate_origen_1corinthians_fragments.py                    # batch default dir

    --images  consult the Jenkins JTS page scans for doubtful readings (see rule 7)
    --force   re-translate even if the output already exists
    --check   parse only: validate header/lemma/block round-trip + marks, print structure

Pass a second positional path to override the output for a single-file run.
"""

import glob
import os
import re
import subprocess
import sys
import time

BASE = (
    "/path/to/Writings-Database-Non-English/"
    "Origen of Alexandria/Commentary on 1 Corinthians"
)
SOURCE_DIR = os.path.join(BASE, "GREEK")
TARGET_DIR = os.path.join(BASE, "english")
IMAGE_DIR = os.path.join(BASE, "_source", "jenkins_pages")

AUTHOR = "Origen of Alexandria"
WORK = "Commentary on the First Epistle to the Corinthians (Greek catena fragments)"
SOURCE_NOTE = (
    "the Greek catena fragments constituted by Claude Jenkins, JTS 9-10 (1908-09), "
    "base MS Vatican gr. 762 (with 29 fragments from MS Athos Pantocrator 28)"
)

FILE_RE = re.compile(r"^frag\d+_greek\.txt$")

RETRY_DELAYS = [5, 15, 45]
RATE_LIMIT_DELAYS = [60, 120, 240]

# Per-fragment metadata: (1 Cor reference, Athos-siglum flag, Jenkins JTS part, printed-page
# span). The part (I/II/III = JTS 9 1908; IV = JTS 10 1909) and page span drive the output
# header and the --images scan lookup; the Athos flag re-emits the `*` on the § heading. §§
# I-XC run without gap. (§ XLVIII is a compound double lemma, 1 Cor xii 8-10 + xii 27-28.)
FRAG_META = {
     1: ("i 2", False, "I", (232, 232)),
     2: ("i 4-10", False, "I", (232, 234)),
     3: ("i 9", False, "I", (234, 234)),
     4: ("i 10", False, "I", (234, 234)),
     5: ("i 14, 17", False, "I", (234, 235)),
     6: ("i 18", False, "I", (235, 235)),
     7: ("i 19-21", False, "I", (236, 236)),
     8: ("i 23-31", False, "I", (236, 238)),
     9: ("ii 4-7", False, "I", (238, 239)),
    10: ("ii 9-11", False, "I", (239, 239)),
    11: ("ii 12-15", False, "I", (239, 241)),
    12: ("iii 1-3 a", False, "I", (241, 242)),
    13: ("iii 3-5", False, "I", (242, 243)),
    14: ("iii 6-8", False, "I", (243, 243)),
    15: ("iii 9-15", False, "I", (243, 245)),
    16: ("iii 16-20", False, "I", (245, 247)),
    17: ("iii 21-23", False, "II", (353, 353)),
    18: ("iv 1-5", False, "II", (353, 357)),
    19: ("iv 6-8", False, "II", (357, 359)),
    20: ("iv 9-10", False, "II", (360, 361)),
    21: ("iv 15", False, "II", (361, 362)),
    22: ("iv 19-20", False, "II", (362, 362)),
    23: ("iv 21-v 2", False, "II", (362, 363)),
    24: ("v 3-5", False, "II", (363, 365)),
    25: ("v 7-8", False, "II", (365, 365)),
    26: ("v 9-11", False, "II", (365, 367)),
    27: ("vi 1-3", False, "II", (367, 369)),
    28: ("vi 12", False, "II", (369, 370)),
    29: ("vi 13-14", False, "II", (370, 371)),
    30: ("vi 15", False, "II", (371, 371)),
    31: ("vi 18", False, "II", (371, 371)),
    32: ("vi 19-20", False, "II", (371, 372)),
    33: ("vii 1-4", False, "III", (500, 501)),
    34: ("vii 5", False, "III", (501, 503)),
    35: ("vii 8-12", False, "III", (503, 505)),
    36: ("vii 14", False, "III", (505, 506)),
    37: ("vii 18-20", False, "III", (506, 507)),
    38: ("vii 21-24", False, "III", (507, 508)),
    39: ("vii 25", False, "III", (508, 510)),
    40: ("ix 7-9", False, "III", (510, 511)),
    41: ("ix 9-11", False, "III", (511, 512)),
    42: ("ix 16", False, "III", (512, 512)),
    43: ("ix 19-23", False, "III", (512, 514)),
    44: ("ix 24", False, "III", (514, 514)),
    45: ("x 5", False, "IV", (29, 29)),
    46: ("x 6", False, "IV", (29, 29)),
    47: ("xii 3", False, "IV", (29, 30)),
    48: ("xii 8-10 (+ xii 27-28)", False, "IV", (31, 32)),
    49: ("xiii 1-2", False, "IV", (32, 34)),
    50: ("xiii 3", False, "IV", (34, 34)),
    51: ("xiii 4-5", False, "IV", (34, 35)),
    52: ("xiii 8", False, "IV", (35, 35)),
    53: ("xiii 9-12", False, "IV", (35, 35)),
    54: ("xiv 5", True, "IV", (35, 36)),
    55: ("xiv 6", True, "IV", (36, 36)),
    56: ("xiv 7-9 a", True, "IV", (36, 36)),
    57: ("xiv 9 b", True, "IV", (37, 37)),
    58: ("xiv 10", True, "IV", (37, 37)),
    59: ("xiv 11", True, "IV", (37, 37)),
    60: ("xiv 12", True, "IV", (37, 37)),
    61: ("xiv 13-14", True, "IV", (37, 38)),
    62: ("xiv 15-17", True, "IV", (38, 38)),
    63: ("xiv 18-19", True, "IV", (38, 38)),
    64: ("xiv 20", True, "IV", (38, 38)),
    65: ("xiv 21", True, "IV", (38, 38)),
    66: ("xiv 24-25", True, "IV", (39, 39)),
    67: ("xiv 26-27", True, "IV", (39, 39)),
    68: ("xiv 29", True, "IV", (39, 39)),
    69: ("xiv 30-31", True, "IV", (39, 40)),
    70: ("xiv 32", True, "IV", (40, 40)),
    71: ("xiv 34-35", True, "IV", (40, 40)),
    72: ("xiv 37-38", True, "IV", (40, 40)),
    73: ("xiv 31", False, "IV", (40, 41)),
    74: ("xiv 34-35", False, "IV", (41, 42)),
    75: ("xiv 37-38", False, "IV", (43, 43)),
    76: ("xv 1-2", False, "IV", (43, 43)),
    77: ("xv 5", True, "IV", (44, 44)),
    78: ("xv 9", True, "IV", (44, 44)),
    79: ("xv 10", True, "IV", (44, 44)),
    80: ("xv 11", True, "IV", (44, 44)),
    81: ("xv 12-13", True, "IV", (44, 45)),
    82: ("xv 14", True, "IV", (45, 45)),
    83: ("xv 15-16", True, "IV", (45, 45)),
    84: ("xv 20-23", False, "IV", (45, 48)),
    85: ("xv 31", True, "IV", (48, 48)),
    86: ("xv 32", True, "IV", (48, 48)),
    87: ("xv 35-38", False, "IV", (48, 49)),
    88: ("xv 51", True, "IV", (49, 49)),
    89: ("xvi 10-12", False, "IV", (49, 51)),
    90: ("xvi 13-14", False, "IV", (51, 51)),
}

# Header lines. L1 = the § heading (roman + optional Athos `*`); L3 = the LEMMA line; L4 = the
# ==== rule.
HEADING_LINE_RE = re.compile(r"^§\s*([IVXLCDM]+)(\*?)\s*\|\s*(.*?)\s*$")
LEMMA_LINE_RE = re.compile(r"^LEMMA:\s*(.*)$")
SEP_LINE_RE = re.compile(r"^=+\s*$")

# The `[JTS 9 p.N]` / `[JTS 10 p.N]` page anchor -- already stripped in R7, so normally absent;
# removed defensively. The pattern matches ONLY `[JTS …]`, never the rubric / sub-lemma /
# seclusion / [[ ]] brackets, so those are left in place.
JTS_ANCHOR_RE = re.compile(r"\[JTS[^\]]*\]")

SEP_OUT = "=" * 66  # separator between the English provenance header and the body


# --- Roman numerals (§ labels) ------------------------------------------------

_ROMAN = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
    (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]


def int_to_roman(n):
    out = []
    for val, sym in _ROMAN:
        while n >= val:
            out.append(sym)
            n -= val
    return "".join(out)


def frag_label(n):
    """The canonical § label from the filename index: the roman numeral plus the Athos `*`
    siglum when this fragment carries it (so the numeral can never be corrupted and the
    provenance mark lands on exactly the right §§)."""
    star = "*" if FRAG_META.get(n, (None, False))[1] else ""
    return f"§ {int_to_roman(n)}{star}"


# --- Parsing ------------------------------------------------------------------


def parse_text(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def frag_number(basename):
    m = re.search(r"frag(\d+)", basename)
    return int(m.group(1)) if m else -1


def strip_anchors(text):
    """Remove any residual `[JTS …]` anchor, collapsing the gap it leaves (never touching
    newlines). Normally a no-op: the base was cleaned of anchors in the R7 pass."""
    text = JTS_ANCHOR_RE.sub("", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return "\n".join(line.rstrip() for line in text.split("\n"))


def parse_fragment(raw):
    """Return (roman_or_None, athos_bool, ref_or_None, lemma_or_None, [body blocks]).

    Splits the four-line header (`§ …` / `[Cramer …]` / `LEMMA: …` / `====`) from the body.
    The § roman + Athos `*` and the 1 Cor ref come from L1 (held aside); the `[Cramer …]` line
    and the `====` rule are discarded; the LEMMA content is block 0 (translatable); each
    non-empty body line is a further block."""
    raw = strip_anchors(raw)
    lines = raw.split("\n")

    roman = ref = lemma = None
    athos = False
    sep_idx = None
    for i, line in enumerate(lines):
        m = HEADING_LINE_RE.match(line)
        if m and roman is None:
            roman = m.group(1)
            athos = bool(m.group(2))
            ref = re.sub(r"^1\s*Cor\.\s*", "", m.group(3)).strip()
            continue
        m = LEMMA_LINE_RE.match(line)
        if m and lemma is None:
            lemma = m.group(1).strip()
            continue
        if SEP_LINE_RE.match(line):
            sep_idx = i
            break

    body_lines = lines[sep_idx + 1:] if sep_idx is not None else []
    body_blocks = [l.strip() for l in body_lines if l.strip()]

    blocks = ([lemma] if lemma is not None else []) + body_blocks
    return roman, athos, ref, lemma, [b for b in blocks if b]


def paragraphs(text):
    """Blank-line-delimited non-empty blocks -- used to count the model's returned blocks."""
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


# --- Scaffolding cleanup ------------------------------------------------------

SCAFFOLD_KEYWORDS = (
    "i'll translate", "i will translate", "let me translate", "let me render",
    "let me produce", "i'm going to translate", "i am going to translate",
    "here is the translat", "here's the translat", "here is my translat",
    "here is the english", "the translated text", "translated text:",
    "preserving all", "preserve all", "section marker", "sub-lemma",
    "paragraph structure", "output only", "i must output", "i need to translate",
    "the greek text", "here is the greek", "let me check", "let me look",
    "looking at the image", "consulting the", "the page image",
)


def clean_body(translated):
    """Strip leaked scaffolding from the model output while PRESERVING the blank-line
    paragraph structure -- only from the leading region, before the first real content.
    Returns (cleaned, removed)."""
    lines = translated.split("\n")
    removed, out = [], []
    in_preamble = True
    for line in lines:
        low = line.strip().lower()
        if in_preamble and low and any(k in low for k in SCAFFOLD_KEYWORDS):
            removed.append(line.strip())
            continue
        if line.strip():
            in_preamble = False
        out.append(line)
    text = "\n".join(out).strip("\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text, removed


# --- Page images (optional --images consultation) -----------------------------

_image_map = None  # cache: {frag_number: [existing scan paths]}


def load_image_map():
    """Build {frag_number: [scan paths that exist]} by globbing
    jenkins_pt<PART>_p<PAGE>_leaf*.jpg for each page in the fragment's range (excluding the
    _MARGIN crops). Empty per fragment if the scans are missing (so --images degrades to
    text-only)."""
    global _image_map
    if _image_map is not None:
        return _image_map
    _image_map = {}
    for n, (_ref, _athos, part, (lo, hi)) in FRAG_META.items():
        paths = []
        for page in range(lo, hi + 1):
            hits = sorted(
                p for p in glob.glob(
                    os.path.join(IMAGE_DIR, f"jenkins_pt{part}_p{page}_*.jpg"))
                if "_MARGIN" not in os.path.basename(p)
            )
            if hits:
                paths.append(hits[0])
        _image_map[n] = paths
    return _image_map


def image_paths_for(basename):
    return load_image_map().get(frag_number(basename), [])


_IMAGE_RULE = (
    "\nPAGE IMAGES (use them to check doubtful readings). Scans of the printed Jenkins JTS "
    "1908-09 pages this fragment spans are listed below, in order. The Greek above is "
    "transcribed and already page-verified through several passes, but a rare valid-but-wrong-"
    "word slip can still hide. Whenever a word or phrase is grammatically impossible, breaks "
    "the sense, or looks like a plausible mis-transcription, OPEN the matching page image with "
    "your file-reading tool and translate the reading the printed page actually shows. Read the "
    "MAIN Greek text column and IGNORE the critical apparatus at the foot of the page, the "
    "marginal Cramer page-numbers, running headers, and page numbers. Do not otherwise emend, "
    "and do not add notes about what you checked -- output only the translation.\n"
)


def image_block(paths):
    return (_IMAGE_RULE + "\n".join(paths) + "\n") if paths else ""


# --- Prompt -------------------------------------------------------------------

_COMMON_RULES = (
    "- SCRIPTURE (most important). Origen quotes the Bible constantly, in his Greek (LXX / New "
    "Testament) text, and his exposition frequently turns on his exact wording. Translate every "
    "quotation AS IT STANDS in the Greek -- its wording, order, and sense -- into natural "
    "English. Do NOT substitute a standard modern translation, do NOT normalize to a familiar "
    "version, do NOT call any Bible/verse-lookup tool. PSALMS follow LXX numbering; the "
    "historical books are the LXX 'Kingdoms' (1-4 Kingdoms = 1-2 Samuel + 1-2 Kings); give the "
    "number as the Greek implies it (you may add the modern equivalent in brackets). The "
    "1 Corinthians lemmata are Origen's own Greek text of the epistle -- render them as they "
    "stand. Translate scripture book names to English.\n"
    "- THE 1 CORINTHIANS LEMMA & SUB-LEMMATA. The header LEMMA line (block 1) is the "
    "1 Corinthians passage the fragment expounds; translate it as scripture. Within the body, a "
    "line that begins with a bracketed verse reference -- e.g. `[iv 16] …`, `[vi 9-10] …`, "
    "`[vii 28 a] …` -- is a SUB-LEMMA: keep the `[<ref>]` label exactly (it is a verse citation, "
    "not a seclusion) and translate the Greek verse that follows it as scripture. Words wrapped "
    "in `* *` inside the exposition are the lemma word(s) under comment: keep the `* *` marks and "
    "translate the words.\n"
    "- CATENIST ATTRIBUTION RUBRIC. The line `[Ὠριγένους]` (the one rubric form in this corpus, "
    "opening almost every fragment, and twice in a few) is the catenist's attribution, not "
    "Origen's own words. KEEP the square brackets and translate it: `[Of Origen]`. This "
    "bracketed rubric is the ONE class of square brackets you keep; see the seclusion rule for "
    "the rest.\n"
    "- EDITOR'S SUPPLEMENTS ⟨ ⟩ AND SECLUSIONS [ ]. Angle brackets `⟨ … ⟩` mark words the editor "
    "SUPPLIED and square brackets `[ … ]` (mid-text, not a rubric or a verse label) mark words the "
    "editor SECLUDED (in this corpus only `[Χριστοῦ]` and `[μὴ]`); in BOTH cases read the word(s) "
    "in the sense the grammar and context require and translate them naturally as part of the "
    "sentence -- do NOT reproduce the ⟨ ⟩ or [ ] brackets in the English. (This also applies to a "
    "LEMMA or sub-lemma whose Greek is wrapped in `[ … ]`: translate the verse, drop the wrapping "
    "brackets.)\n"
    "- DOUBLE BRACKETS [[ … ]]. Two passages stand inside `[[ … ]]`: frag48's first lemma "
    "(1 Cor xii 8-10, the list of spiritual gifts) and frag81's gloss identifying the "
    "Manichaeans. KEEP the `[[ ]]` around the whole passage in your English and translate the "
    "content faithfully; do not drop or duplicate the marks.\n"
    "- OBELIZED CRUXES † … †. A few corrupt places are fenced with daggers `† … †` (frag15, "
    "frag35). KEEP the `† †` around them and translate the daggered words as they stand, as best "
    "they can be construed; do not silently emend or drop them.\n"
    "- SINGLE-QUOTED TERMS ‘ ’ / ' '. Origen sometimes cites a single word or phrase in single "
    "quotes. Keep a single quotation mark around the cited term and translate it. NOTE: most "
    "ASCII apostrophes are Greek ELISION (δι', ἀλλ', ἐπ', οὐδ') and simply disappear in English "
    "-- do not treat those as quotes. A printed LACUNA appears either as spaced dots `. . .` "
    "(frag05, 07, 08, 14) or as the ellipsis character `…` (frag48): keep it exactly as it "
    "stands and do NOT fill it.\n"
    "- NAMES & VOCABULARY. Greek biblical names -> standard English forms: Ἰησοῦς (Χριστός) -> "
    "Jesus (Christ), Παῦλος / ὁ ἀπόστολος -> Paul / the Apostle, Θεός -> God, Κύριος -> the Lord, "
    "Πνεῦμα ἅγιον -> the Holy Spirit, Λόγος -> the Word, Πατήρ / υἱός -> the Father / the Son, "
    "Κορίνθιοι -> the Corinthians, Ἀπολλώς -> Apollos, Κηφᾶς -> Cephas, Τιμόθεος -> Timothy, "
    "Ἰσραήλ -> Israel, Ἰουδαῖοι / Ἕλληνες -> the Jews / the Greeks, ἐκκλησία -> the Church, "
    "Μωσῆς -> Moses, Δαβίδ -> David, Ἀβραάμ / Ἰσαάκ -> Abraham / Isaac, Ἡσαΐας -> Isaiah, "
    "Ἀκύλας / Σύμμαχος / Θεοδοτίων -> Aquila / Symmachus / Theodotion, Μανιχαῖοι -> the "
    "Manichaeans. Keep the 1-Corinthians / Origenian vocabulary consistent: ψυχικός / "
    "πνευματικός -> the natural (unspiritual) man / the spiritual man (the load-bearing contrast "
    "of §XI -- keep the two distinct); χαρίσματα -> spiritual gifts; γλῶσσαι / γένη γλωσσῶν -> "
    "tongues / kinds of tongues; προφητεία -> prophecy; ἑρμηνεία (γλωσσῶν) -> interpretation (of "
    "tongues); ἀνάστασις (νεκρῶν) -> the resurrection (of the dead); ἀγάπη -> love; σοφία τοῦ "
    "κόσμου / σοφία θεοῦ -> the wisdom of the world / the wisdom of God; μωρία -> foolishness; "
    "σκάνδαλον -> a stumbling-block; σχίσματα -> divisions; οἰκοδομή / οἰκοδομεῖν -> edification "
    "/ to build up; τὰ πνευματικά -> spiritual things; ἐκκλησία -> the Church; ἑτερόδοξοι -> the "
    "heterodox. Where Origen ETYMOLOGIZES or puns on a Greek word, KEEP the Greek word and gloss "
    "it on first mention.\n"
    "- REGISTER & FIDELITY. Aim for clear, faithful, dignified English suited to a patristic "
    "exegetical fragment. Keep Origen's direct address and his argumentative connectives (γάρ, "
    "οὖν, δέ, ὥσπερ … οὕτως, μήποτε) -- the reasoning is step-by-step and the logic must survive. "
    "Represent the Greek witness faithfully and COMPLETELY: do not paraphrase, summarize, abridge, "
    "or 'correct' the exegesis (the wisdom of God against the wisdom of the world, the spiritual "
    "vs the natural man, spiritual gifts, tongues and prophecy, love, marriage and continence, "
    "the resurrection of the dead). Long periodic sentences may be broken for readability, but do "
    "not drop clauses.\n"
    "- The Greek is a verified base; if an obvious residual typo remains, translate the evidently "
    "intended word without flagging it. These are fragments of a lost work -- some begin or end "
    "abruptly; render what stands without smoothing over the seam.\n"
)


def build_prompt(text, reminder="", images=None):
    return (
        f"Translate the following Greek text into English. It is from {AUTHOR}'s "
        f"{WORK} -- {SOURCE_NOTE}. Origen's commentary on 1 Corinthians survives only as "
        f"excerpts in the medieval Greek exegetical chains (catenae); this is one numbered "
        f"fragment, expounding its 1 Corinthians lemma phrase by phrase in Origen's manner "
        f"(the wisdom of God against the wisdom of the world, the spiritual and the natural "
        f"man, spiritual gifts, tongues and prophecy, love, marriage and continence, the "
        f"resurrection of the dead).\n\n"
        "Rules:\n"
        "1. Output ONLY the translated text -- no preamble, notes, meta-commentary, or "
        "quotation of the Greek. Do not write 'Here is the translation' or 'Let me translate'.\n"
        "2. Preserve the block structure EXACTLY: the blocks are separated by one blank line; "
        "return the SAME number of blocks, one translated block per source block, in order; do "
        "not merge, split, add, or drop any.\n"
        "3. Text between guillemets `» «` is Scripture Origen QUOTES. Keep the guillemets "
        "`» «` around the quoted words in your English and translate them in his wording (see "
        "the Scripture rule below). Do not add or remove guillemets.\n"
        "4. Text between asterisks `* *` is the 1 Corinthians wording under comment. Keep the "
        "`* *` marks around it and translate the words as the Greek gives them.\n"
        f"{_COMMON_RULES}"
        f"{reminder}"
        f"{image_block(images)}"
        "\n"
        f"{text}"
    )


# --- CLI call -----------------------------------------------------------------


def is_rate_limit_error(stderr):
    lower = stderr.lower()
    return any(t in lower for t in
               ["rate limit", "rate_limit", "overloaded", "too many requests", "529"])


def call_claude(prompt):
    """One CLI call with rate-limit-aware retry/backoff. Returns stdout text."""
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
                f"Translation failed after retries: rc={result.returncode} "
                f"stderr={result.stderr.strip()[:200]} stdout={result.stdout.strip()[:200]}")
    raise RuntimeError("Unreachable")


def looks_truncated(source, translated):
    """A translation far shorter than the Greek is almost certainly cut off."""
    return len(translated) < 0.5 * len(source)


# --- Fragment translation -----------------------------------------------------


def translate_blocks(blocks, images=None):
    """Translate a fragment's blocks in a single call and structurally verify the block count
    (so nothing is merged, split, or dropped). Returns (list_of_blocks, ok); on failure the
    caller falls back to block-by-block. The § heading is handled by the caller."""
    if not blocks:
        return [], True

    src = "\n\n".join(blocks)

    translated, removed = clean_body(call_claude(build_prompt(src, images=images)))
    if removed:
        print(f"    Stripped {len(removed)} leaked scaffolding line(s): "
              f"{removed[0][:70]!r}...")
    out = paragraphs(translated)
    if len(out) == len(blocks) and not looks_truncated(src, translated):
        return out, True

    print(f"    Block-count check failed ({len(out)} vs {len(blocks)}"
          f"{'; looks truncated' if looks_truncated(src, translated) else ''})"
          f" -- retrying once with a reminder...")
    reminder = (
        f"5. The source has EXACTLY {len(blocks)} block(s) separated by blank lines. Return "
        f"EXACTLY that many translated blocks, one per source block, in order; do not merge, "
        f"split, add, or drop any. Keep every `» «`, `* *`, `[[ ]]`, `† †`, single-quote, and "
        f"bracketed rubric / verse label. Translate through to the final sentence.\n"
    )
    translated, _ = clean_body(
        call_claude(build_prompt(src, reminder=reminder, images=images)))
    out = paragraphs(translated)
    if len(out) == len(blocks) and not looks_truncated(src, translated):
        return out, True

    print(f"    Still off ({len(out)} vs {len(blocks)}) -- translating block-by-block...")
    out = []
    for i, block in enumerate(blocks):
        print(f"      [block {i + 1}/{len(blocks)}] ({len(block)} chars)...")
        t, _ = clean_body(call_claude(build_prompt(block, images=images)))
        t = re.sub(r"\n\s*\n+", "\n", t).strip()  # keep each block a single paragraph
        out.append(t)
    return out, False


# --- Output front matter ------------------------------------------------------


def english_header(basename):
    """A fresh, deterministic English provenance block for the output file."""
    n = frag_number(basename)
    ref = FRAG_META.get(n, (None,))[0]
    unit = frag_label(n) + (f" — 1 Corinthians {ref}" if ref else "")
    return (
        f"# Origen, *Commentary on 1 Corinthians* — English translation — {unit}\n"
        f"# Origen's commentary on 1 Corinthians survives only as Greek catena fragments; this "
        f"is a fresh English rendering of one of the 90 fragments (§§ I–XC).\n"
        f"# Source text: Claude Jenkins, “Origen on I Corinthians,” *Journal of Theological "
        f"Studies* 9 (1908) Parts I–III + 10 (1909) Part IV — the verified reading text "
        f"(refinement passes B, R2, R4, R1, R3, R5, R6, R7); base MS Vatican gr. 762, with "
        f"29 fragments (marked *) from MS Athos Pantocrator 28.\n"
        f"# Scripture is rendered in Origen's own Greek (LXX/NT) wording and numbering; "
        f"biblical names follow standard English forms.\n"
        f"{SEP_OUT}"
    )


def render_output(basename, roman, ref, blocks):
    """Assemble the English file body: the canonical `§ <ROMAN>[*] — 1 Corinthians <ref>`
    heading (numeral from the filename, `*` from the Athos flag), then the translated LEMMA
    line, then the exposition blocks."""
    n = frag_number(basename)
    parts = []
    label = frag_label(n)
    if ref:
        label += f" — 1 Corinthians {ref}"
    parts.append(label)
    if blocks:
        parts.append(f"LEMMA: {blocks[0]}")
        parts.extend(blocks[1:])
    return "\n\n".join(parts)


# --- Driver -------------------------------------------------------------------


def resolve_input(arg):
    if os.path.isabs(arg) or os.sep in arg:
        return arg
    return os.path.join(SOURCE_DIR, arg)


def output_path_for(input_file):
    name = os.path.basename(input_file)
    name = re.sub(r"_greek(\.txt)$", r"_english\1", name)
    return os.path.join(TARGET_DIR, name)


def translate_file(input_file, output_file, force=False, use_images=False):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")
    print(f"{'=' * 60}")

    if not force and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
        print("  Already exists. Skipping (use --force to overwrite).")
        return True

    raw = parse_text(input_file)
    basename = os.path.basename(input_file)
    roman, athos, ref, lemma, blocks = parse_fragment(raw)

    images = None
    if use_images:
        images = image_paths_for(basename)
        if images:
            print(f"  Attaching {len(images)} page scan(s) for doubtful readings.")
        else:
            print("  --images requested but no scans available for this fragment "
                  "-- translating text-only.")

    lemma_state = "lemma" if lemma is not None else "NO LEMMA"
    print(f"  Translating {basename} (§ {roman}{'*' if athos else ''}, {lemma_state}, "
          f"{len(blocks)} block(s), {len(raw)} chars)...")

    translations, ok = translate_blocks(blocks, images=images)
    if not ok:
        print("  (used block-by-block fallback)")
    if len(translations) != len(blocks):
        print(f"  WARNING: block count off after fallback "
              f"({len(translations)} vs {len(blocks)}) -- inspect manually.")

    # Soft fidelity signals (not retry triggers): guillemet-span, double-bracket, dagger counts.
    src = "\n\n".join(blocks)
    out_joined = "\n\n".join(translations)
    for mark, lbl in (("»", "Scripture-quote (»…«)"), ("[[", "double-bracket ([[…]])"),
                      ("†", "dagger crux (†…†)")):
        s, o = src.count(mark), out_joined.count(mark)
        if s != o:
            print(f"  NOTE: {lbl} count {s} -> {o} -- a span was merged/split; spot-check marks.")

    out = english_header(basename) + "\n\n" + render_output(
        basename, roman, ref, translations) + "\n"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(out)

    print(f"  Done -> {output_file}")
    return True


def order_key(name):
    return frag_number(name) if frag_number(name) >= 0 else 999


def collect_files(path):
    if os.path.isdir(path):
        return [os.path.join(path, f)
                for f in sorted(os.listdir(path), key=order_key)
                if FILE_RE.match(f)]
    return [path]


def check_files(files):
    """Parse-only self-test: prove the header/lemma/block round-trip without any CLI calls.
    Reports per file the detected § roman (and whether it matches the filename), the Athos
    flag (and whether it agrees with FRAG_META), whether a lemma was found, the block count,
    and whether the `» «`, `⟨ ⟩`, `[[ ]]`, `* *`, and `† †` marks are balanced in the blocks
    that will be sent."""
    ok = True
    grand_blocks = 0
    for fp in files:
        raw = parse_text(fp)
        basename = os.path.basename(fp)
        roman, athos, ref, lemma, blocks = parse_fragment(raw)
        n = frag_number(basename)
        joined = "\n\n".join(blocks)
        guil = joined.count("»") == joined.count("«")
        ang = joined.count("⟨") == joined.count("⟩")
        dbrk = joined.count("[[") == joined.count("]]")
        star = joined.count("*") % 2 == 0
        dag = joined.count("†") % 2 == 0
        status = "OK"
        expect = int_to_roman(n)
        meta_athos = FRAG_META.get(n, (None, False))[1]
        if roman is None:
            status, ok = "NO § HEADING FOUND", False
        elif roman != expect:
            status, ok = f"§ ROMAN {roman} != filename {expect}", False
        elif athos != meta_athos:
            status, ok = f"Athos flag {athos} != FRAG_META {meta_athos}", False
        if lemma is None:
            status, ok = "NO LEMMA FOUND", False
        if not (guil and ang and dbrk and star and dag):
            status, ok = (f"UNBALANCED marks (»«={guil}, ⟨⟩={ang}, [[]]={dbrk}, "
                          f"**={star}, ††={dag})", False)
        print(f"  {basename}: {frag_label(n)} (ref {ref!r}) | "
              f"{'lemma' if lemma is not None else 'NO LEMMA'} | {len(blocks)} block(s) | "
              f"»«={joined.count('»')}/{joined.count('«')} ⟨⟩={joined.count('⟨')}/"
              f"{joined.count('⟩')} [[]]={joined.count('[[')}/{joined.count(']]')} "
              f"*={joined.count('*')} †={joined.count('†')}  [{status}]")
        grand_blocks += len(blocks)
    print(f"\n  TOTAL: {len(files)} file(s), {grand_blocks} blocks.")
    print("  Round-trip:", "OK — header + marks consistent." if ok else "FAILED — see above.")
    return ok


def main():
    argv = sys.argv[1:]
    force = use_images = check = False
    positional = []
    for a in argv:
        if a == "--force":
            force = True
        elif a == "--images":
            use_images = True
        elif a == "--check":
            check = True
        elif a.startswith("--"):
            print(f"Unknown option: {a}")
            sys.exit(1)
        else:
            positional.append(a)

    raw_input = resolve_input(positional[0]) if positional else SOURCE_DIR
    if not os.path.exists(raw_input):
        print(f"Input not found: {raw_input}")
        sys.exit(1)

    files = collect_files(raw_input)
    if not files:
        print("No source files found (expected frag<NN>_greek.txt).")
        sys.exit(1)

    if check:
        print(f"Parse-only check of {len(files)} file(s):")
        sys.exit(0 if check_files(files) else 1)

    explicit_output = positional[1] if len(positional) >= 2 else None
    if explicit_output and len(files) > 1:
        print("Second positional output path is only valid for a single input file.")
        sys.exit(1)

    print(f"Found {len(files)} fragment file(s) to translate"
          f"{' (with page-scan consultation)' if use_images else ''}.")
    failures = []
    for f in files:
        out = explicit_output if explicit_output else output_path_for(f)
        try:
            translate_file(f, out, force=force, use_images=use_images)
        except Exception as e:  # keep the batch going; report at the end
            print(f"  ERROR on {os.path.basename(f)}: {e}")
            failures.append((f, str(e)))

    print(f"\nProcessed {len(files)} file(s); {len(failures)} failure(s).")
    if failures:
        for f, e in failures:
            print(f"  FAILED: {os.path.basename(f)} -- {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

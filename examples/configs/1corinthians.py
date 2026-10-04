"""Worked example config: Origen, *Commentary on 1 Corinthians* (Greek catena fragments, Jenkins
JTS 9-10, 1908-09, §§ I-XC).

Reproduces the setup of examples/original-scripts/{translate_origen_1corinthians_fragments,
validate_origen_1corinthians_translation,grade_origen_1corinthians_kovacs}.py with the generic
tools. Shows the features a fragment collection needs that a homily collection does not: a lemma
held in the file HEADER, a siglum (`*`) on some headings, extra bracket marks, and an anthology
oracle that covers only some units (sliced by verse-group from a whole-book text dump).
"""

import glob
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import common as C  # noqa: E402

SLUG = "origen-1corinthians"
AUTHOR = "Origen of Alexandria"
WORK = "Commentary on the First Epistle to the Corinthians (Greek catena fragments)"
SOURCE_LANGUAGE = "Greek"
UNIT_NOUN = "Fragment"
WORK_CONTEXT = (
    "The commentary survives only as excerpts in the medieval Greek exegetical chains (catenae), "
    "constituted by Claude Jenkins, JTS 9-10 (1908-09), base MS Vatican gr. 762, with 29 fragments "
    "(marked * on the § number) from MS Athos Pantocrator 28. This is one numbered fragment, "
    "expounding its 1 Corinthians lemma phrase by phrase."
)

PROJECT = ("/path/to/Writings-Database-Non-English/"
           "Origen of Alexandria/Commentary on 1 Corinthians")
SOURCE_DIR = os.path.join(PROJECT, "GREEK")
TARGET_DIR = os.path.join(PROJECT, "english")
SOURCE_SUFFIX = "_greek.txt"
TARGET_SUFFIX = "_english.txt"

# Header = `§ XI | 1 Cor. ii 12-15` / `[Cramer 46-48]` / `LEMMA: [...]` / `====`. The LEMMA is sent
# as block 0 and re-emitted as `LEMMA: <English>`; every non-empty body line is one block.
HEADER_LEMMA_RE = r"^LEMMA:\s*(.*)$"
HEADER_LEMMA_OUT_PREFIX = "LEMMA: "
BODY_HEADING_RE = None
ANCHOR_RE = r"\[JTS[^\]]*\]"

PAIRED_MARKS = [("»", "«"), ("[[", "]]")]
EVEN_MARKS = ["*", "†"]
EVEN_MARK_EXEMPT_RE = r"(?m)^§\s+[IVXLCDM]+\*"   # the Athos siglum on a heading is not a lemma mark

# n -> (1 Cor ref, Athos?, Jenkins part, printed-page span)
_ATHOS = set(range(54, 73)) | set(range(77, 84)) | {85, 86, 88}
_REFS = [
    "i 2", "i 4-10", "i 9", "i 10", "i 14, 17", "i 18", "i 19-21", "i 23-31", "ii 4-7", "ii 9-11",
    "ii 12-15", "iii 1-3 a", "iii 3-5", "iii 6-8", "iii 9-15", "iii 16-20", "iii 21-23", "iv 1-5",
    "iv 6-8", "iv 9-10", "iv 15", "iv 19-20", "iv 21-v 2", "v 3-5", "v 7-8", "v 9-11", "vi 1-3",
    "vi 12", "vi 13-14", "vi 15", "vi 18", "vi 19-20", "vii 1-4", "vii 5", "vii 8-12", "vii 14",
    "vii 18-20", "vii 21-24", "vii 25", "ix 7-9", "ix 9-11", "ix 16", "ix 19-23", "ix 24", "x 5",
    "x 6", "xii 3", "xii 8-10 (+ xii 27-28)", "xiii 1-2", "xiii 3", "xiii 4-5", "xiii 8",
    "xiii 9-12", "xiv 5", "xiv 6", "xiv 7-9 a", "xiv 9 b", "xiv 10", "xiv 11", "xiv 12",
    "xiv 13-14", "xiv 15-17", "xiv 18-19", "xiv 20", "xiv 21", "xiv 24-25", "xiv 26-27", "xiv 29",
    "xiv 30-31", "xiv 32", "xiv 34-35", "xiv 37-38", "xiv 31", "xiv 34-35", "xiv 37-38", "xv 1-2",
    "xv 5", "xv 9", "xv 10", "xv 11", "xv 12-13", "xv 14", "xv 15-16", "xv 20-23", "xv 31",
    "xv 32", "xv 35-38", "xv 51", "xvi 10-12", "xvi 13-14",
]
_PAGES = [  # (part, first printed page, last printed page) per fragment, from the Pass A manifest
    ("I", 232, 232), ("I", 232, 234), ("I", 234, 234), ("I", 234, 234), ("I", 234, 235),
    ("I", 235, 235), ("I", 236, 236), ("I", 236, 238), ("I", 238, 239), ("I", 239, 239),
    ("I", 239, 241), ("I", 241, 242), ("I", 242, 243), ("I", 243, 243), ("I", 243, 245),
    ("I", 245, 247), ("II", 353, 353), ("II", 353, 357), ("II", 357, 359), ("II", 360, 361),
    ("II", 361, 362), ("II", 362, 362), ("II", 362, 363), ("II", 363, 365), ("II", 365, 365),
    ("II", 365, 367), ("II", 367, 369), ("II", 369, 370), ("II", 370, 371), ("II", 371, 371),
    ("II", 371, 371), ("II", 371, 372), ("III", 500, 501), ("III", 501, 503), ("III", 503, 505),
    ("III", 505, 506), ("III", 506, 507), ("III", 507, 508), ("III", 508, 510), ("III", 510, 511),
    ("III", 511, 512), ("III", 512, 512), ("III", 512, 514), ("III", 514, 514), ("IV", 29, 29),
    ("IV", 29, 29), ("IV", 29, 30), ("IV", 31, 32), ("IV", 32, 34), ("IV", 34, 34),
    ("IV", 34, 35), ("IV", 35, 35), ("IV", 35, 35), ("IV", 35, 36), ("IV", 36, 36),
    ("IV", 36, 36), ("IV", 37, 37), ("IV", 37, 37), ("IV", 37, 37), ("IV", 37, 37),
    ("IV", 37, 38), ("IV", 38, 38), ("IV", 38, 38), ("IV", 38, 38), ("IV", 38, 38),
    ("IV", 39, 39), ("IV", 39, 39), ("IV", 39, 39), ("IV", 39, 40), ("IV", 40, 40),
    ("IV", 40, 40), ("IV", 40, 40), ("IV", 40, 41), ("IV", 41, 42), ("IV", 43, 43),
    ("IV", 43, 43), ("IV", 44, 44), ("IV", 44, 44), ("IV", 44, 44), ("IV", 44, 44),
    ("IV", 44, 45), ("IV", 45, 45), ("IV", 45, 45), ("IV", 45, 48), ("IV", 48, 48),
    ("IV", 48, 48), ("IV", 48, 49), ("IV", 49, 49), ("IV", 49, 51), ("IV", 51, 51),
]
FRAGS = {n: (_REFS[n - 1], n in _ATHOS) + _PAGES[n - 1] for n in range(1, 91)}
UNIT_META = {n: f"§ {C.roman(n)}{'*' if a else ''}, 1 Cor. {ref}" for n, (ref, a, *_) in FRAGS.items()}


def heading_en(n):
    """Numeral from the unit number, Athos `*` from the flag, verse ref as printed on line 1 of the
    Greek file (`§ XI  |  1 Cor. ii 12–15`), falling back to the table."""
    ref, athos = FRAGS[n][:2]
    src = os.path.join(SOURCE_DIR, f"frag{n:02d}_greek.txt")
    if os.path.exists(src):
        m = re.match(r"^§\s*[IVXLCDM]+\*?\s*\|\s*(?:1\s*Cor\.\s*)?(.*?)\s*$", C.read(src).split("\n")[0])
        if m and m.group(1):
            ref = m.group(1)
    return f"§ {C.roman(n)}{'*' if athos else ''} — 1 Corinthians {ref}"


def english_header(n):
    return (
        f"# Origen, *Commentary on 1 Corinthians* — English translation — {heading_en(n)}\n"
        "# Origen's commentary on 1 Corinthians survives only as Greek catena fragments; this is a "
        "fresh English rendering of one of the 90 fragments (§§ I–XC).\n"
        "# Source text: Claude Jenkins, “Origen on I Corinthians,” *Journal of Theological Studies* "
        "9 (1908) Parts I–III + 10 (1909) Part IV — the verified reading text (refinement passes B, "
        "R2, R4, R1, R3, R5, R6, R7); base MS Vatican gr. 762, with 29 fragments (marked *) from MS "
        "Athos Pantocrator 28.\n"
        "# Scripture is rendered in Origen's own Greek (LXX/NT) wording and numbering; biblical names "
        "follow standard English forms."
    )


TRANSLATION_RULES = (
    "- SCRIPTURE (most important). Origen quotes the LXX / NT in Greek and his exposition turns on "
    "his exact wording: translate every quotation AS IT STANDS. PSALMS follow LXX numbering; the "
    "historical books are the LXX 'Kingdoms'. The 1 Corinthians lemmata are Origen's own Greek text "
    "of the epistle -- render them as they stand.\n"
    "- LEMMA & SUB-LEMMATA. Block 1 is the header LEMMA: translate it as scripture. A body line that "
    "begins with a bracketed verse reference (`[iv 16] …`, `[vii 28 a] …`) is a SUB-LEMMA: keep the "
    "`[<ref>]` label exactly and translate the verse after it.\n"
    "- CATENIST RUBRIC. `[Ὠριγένους]` is the catenist's attribution: KEEP the square brackets and "
    "translate it `[Of Origen]`. It is the ONE class of square brackets you keep.\n"
    "- SUPPLEMENTS ⟨ ⟩ AND SECLUSIONS [ ]. Read the words in the sense the grammar requires and "
    "translate them naturally -- do NOT reproduce the brackets (this includes a LEMMA wrapped in "
    "`[ … ]`).\n"
    "- DOUBLE BRACKETS [[ … ]] (frag48's first lemma; frag81's gloss on the Manichaeans): KEEP the "
    "`[[ ]]` and translate the content.\n"
    "- OBELIZED CRUXES † … † (frag15, frag35): KEEP the daggers and translate the words as they "
    "stand; do not emend or drop them.\n"
    "- SINGLE QUOTES & LACUNAE. Keep single quotes around a cited term (most ASCII apostrophes are "
    "Greek ELISION -- δι', ἀλλ' -- not quotes). A printed LACUNA (`. . .` or `…`) is kept exactly, "
    "never filled.\n"
    "- NAMES & VOCABULARY. Ἰησοῦς Χριστός -> Jesus Christ, Παῦλος / ὁ ἀπόστολος -> Paul / the "
    "Apostle, Ἀπολλώς -> Apollos, Κηφᾶς -> Cephas, Μωσῆς -> Moses, Ἀκύλας / Σύμμαχος / Θεοδοτίων -> "
    "Aquila / Symmachus / Theodotion, Μανιχαῖοι -> the Manichaeans. ψυχικός / πνευματικός -> the "
    "natural (unspiritual) man / the spiritual man (keep distinct); χαρίσματα -> spiritual gifts; "
    "γλῶσσαι -> tongues; προφητεία -> prophecy; οἰκοδομή -> edification; σοφία τοῦ κόσμου / σοφία "
    "θεοῦ -> the wisdom of the world / the wisdom of God. Where Origen ETYMOLOGIZES or puns, KEEP "
    "the Greek word and gloss it on first mention.\n"
    "- REGISTER & FIDELITY. Clear, faithful, dignified English; keep the connectives (γάρ, οὖν, δέ, "
    "ὥσπερ … οὕτως); never paraphrase, abridge, or 'correct'. These are fragments of a lost work -- "
    "some begin or end abruptly; render what stands without smoothing the seam.\n"
)

VALIDATION_HOUSE_RULES = (
    "  - Whether the header LEMMA line keeps or drops Jenkins's `[ … ]` wrap -- presentation only.\n"
    "  - KEPT BRACKETS: `[Of Origen]`, sub-lemma labels (`[iv 16]`, `[vii 28 a]`), and `[[ … ]]` "
    "(frag48, frag81). Correct.\n"
    "  - OBELIZED CRUXES † … † (frag15, frag35) -- marks, not meaning; the daggered words are "
    "rendered as best they stand, NOT garbled.\n"
    "  - SUPPLEMENTS ⟨ ⟩ and SECLUSIONS [ ] (`[Χριστοῦ]` frag02, `[μὴ]` frag19) read in sense "
    "without brackets; PRINTED LACUNAE kept, not filled.\n"
    "  - HOUSE RENDERINGS: χαρίσματα -> 'spiritual gifts'; γλῶσσαι -> 'tongues'; προφητεία -> "
    "'prophecy'; οἰκοδομή -> 'edification'. §XI ψυχικός vs πνευματικός kept distinct.\n"
    "  - SETTLED CRUXES (adjudicated at R6): frag06 `χριστοῦ` and `λέγω`, frag12 `γραφαῖς`, frag89 "
    "`τοῦ τόπου` ARE the base reading; frag43's body citation `ἵνα πάντας ἢ τινὰς σώσω` vs the lemma "
    "`ἵνα πάντως τινὰς σώσω` are BOTH faithful (do not harmonize); frag50 `καυχήσωμαι` is correct.\n"
    "  - CATENA SEAMS: a fragment may begin or end abruptly; there is no uniform doxology.\n"
)

SHORT_BLOCK_RATIO = 0.55   # Greek is far more compact than English
SHORT_MIN_SOURCE = 200
ENDING_CHECKS = []

IMAGE_DIR = os.path.join(PROJECT, "_source", "jenkins_pages")


def image_paths(n):
    _, _, part, lo, hi = FRAGS[n]
    out = []
    for page in range(lo, hi + 1):
        hits = sorted(p for p in glob.glob(os.path.join(IMAGE_DIR, f"jenkins_pt{part}_p{page}_*.jpg"))
                      if "_MARGIN" not in p)
        if hits:
            out.append(hits[0])
    return out


# --- Oracle: Kovacs is a verse-arranged ANTHOLOGY covering ~33 of the 90 fragments -------------
ORACLE_LABEL = ("Kovacs, 1 Corinthians Interpreted by Early Christian Commentators, "
                "The Church's Bible (Eerdmans, 2005)")
ORACLE_SHORT = "Kovacs"
ORACLE_PDF = os.path.join(PROJECT, "_source", "oracle", "oracle.pdf")
ORACLE_CACHE = os.path.join(PROJECT, "_source", "oracle", "oracle_full.txt")
# fragment -> Kovacs verse-group header(s), pinned at pass R3 from her Appendix 2 (JTS-page citations)
FRAG_KOVACS = {
    1: ["1:1-3"], 2: ["1:4-9"], 6: ["1:18-25"], 8: ["1:26-31"], 9: ["2:6-8"], 11: ["2:13-16"],
    12: ["3:1-3"], 14: ["3:4-8"], 15: ["3:9-11", "3:12-15"], 16: ["3:16-17", "3:18-23"],
    17: ["3:18-23"], 18: ["4:1-2", "4:3-5"], 20: ["4:9-13"], 24: ["5:1-5"], 25: ["5:6-8"],
    26: ["5:9-11", "5:12-13"], 27: ["6:9-11"], 33: ["7:1-7"], 34: ["7:1-7"], 40: ["9:3-7"],
    41: ["9:8-12a"], 42: ["9:12b-18"], 43: ["9:19-23"], 44: ["9:24-27"], 47: ["12:1-3"],
    51: ["13:4-7"], 55: ["14:6-12"], 56: ["14:6-12"], 73: ["14:26-33a"], 74: ["14:33b-36"],
    84: ["15:20-22"], 89: ["16:10-12"], 90: ["16:13-14"],
}
ORACLE_COVERED = set(FRAG_KOVACS)
ORACLE_NOTES = {  # a selection of the per-fragment notes from the original grader
    15: "At the crux †αἱ μὲν ῥίζαι† Kovacs renders the transmitted words at face value -- the "
        "daggers are correct; do NOT flag them.",
    17: "§XVII begins WITHIN the shared 3:18-23 excerpt at 'Let no one boast of men' (iii 21); the "
        "earlier part of that excerpt belongs to §XVI.",
    27: "Lemma vi 1-3 but the exposition runs to vi 9-11; Kovacs's 6:9-11 excerpt overlaps only that "
        "TAIL. Grade the overlap; the vi 1-8 body has no oracle (not an addition).",
    43: "The body re-cites 1 Cor ix 22 as 'that I might save all or some' -- a genuine Origenic "
        "variant, not a divergence.",
}
GRADING_CAVEATS = (
    "  KOVACS IS A LOOSE, SELECTIVE ANTHOLOGY. She draws her Origen excerpts from the SAME Jenkins "
    "catena (so where she renders a clause, the Greek adjudicates), but: (1) each verse-group "
    "interleaves MANY Fathers under `(N) Author` headings -- grade ONLY against the `(N) Origen` "
    "catena excerpt(s); (2) ignore Origen material from other works and her footnotes; (3) she "
    "trims, abridges and paraphrases and quotes Scripture in the RSV. Content in OURS but absent "
    "from hers is almost always HER abridgment, NOT our addition -- flag it only if it contradicts "
    "the Greek. Grade fidelity ACROSS THE OVERLAP.\n"
    "  - Settled: the four R6 emendations (frag06 χριστοῦ + λέγω, frag12 γραφαῖς, frag89 τοῦ τόπου) "
    "may post-date her reading -- never scored against us. House renderings: χαρίσματα -> 'spiritual "
    "gifts', γλῶσσαι -> 'tongues', προφητεία -> 'prophecy', οἰκοδομή -> 'edification'.\n"
)

_VG_RE = re.compile(r"^\s*1\s+Corinthians\s+\d+:\d+[a-z]?(?:-\d+[a-z]?)?\s*\+?\s*$")


def _kovacs_lines():
    if not C.oracle_from_file(ORACLE_CACHE):
        if not os.path.exists(ORACLE_PDF):
            return None
        subprocess.run(["pdftotext", "-layout", ORACLE_PDF, ORACLE_CACHE], check=True)
    return C.read(ORACLE_CACHE).split("\n")


def oracle_text(n):
    """Concatenate the Kovacs verse-group section(s) mapped to fragment n (first body occurrence
    of the header up to the next verse-group header)."""
    groups = FRAG_KOVACS.get(n)
    lines = _kovacs_lines() if groups else None
    if not lines:
        return None
    parts = []
    for vg in groups:
        start = next((i for i, l in enumerate(lines) if l.strip() == f"1 Corinthians {vg}"), None)
        if start is None:
            continue
        end = next((j for j in range(start + 1, min(start + 601, len(lines))) if _VG_RE.match(lines[j])),
                   min(start + 601, len(lines)))
        chunk = "\n".join(lines[start:end]).replace("\x0c", "\n")   # form feeds = page breaks
        chunk = re.sub(r"\n{3,}", "\n\n", chunk).strip()
        parts.append(f"----- Kovacs, 1 Corinthians {vg} -----\n{chunk}")
    return "\n\n".join(parts) or None

#!/usr/bin/env python3
"""Translate Origen's *Homilies on Leviticus* (*Homiliae in Leviticum*), in Rufinus of
Aquileia's Latin, into English -- one whole homily at a time.

This is the sibling of `translate_origen_exodus_homilies.py` (and, at one remove,
`translate_origen_judges_homilies.py` / `translate_origen_numbers.py`): the same
single-CLI-call-per-unit flow, the same scaffolding cleanup, the same structural
verify + one reminder retry, then a block-by-block fallback, the same rate-limit
backoff, and the same optional page-scan consultation. What differs is the SOURCE,
its plain-text SHAPE, the MARKUP still carried in the base, the NAMES, and the
image pipeline.

  1. SOURCE IS RUFINUS'S LATIN OF A LOST GREEK. Origen's homilies on Leviticus survive
     ONLY in Rufinus of Aquileia's Latin translation (made c. 403-405, part of Rufinus's
     programme of Latinizing Origen's Hexateuch homilies -- the same enterprise that
     produced the Genesis, Exodus, Numbers, Joshua, and Judges homilies). The collection
     is COMPLETE: all SIXTEEN homilies (In Leviticum I-XVI) are extant, with no gap,
     expounding selected passages of Leviticus (the burnt offering and the sacrificial
     laws, the sin and guilt offerings, the priestly consecration and vestments, clean
     and unclean animals, childbirth and leprosy, the Day of Atonement and the two goats,
     the holiness code, the great high priest, the feasts and the shewbread, the
     blasphemer, the Jubilee, and the blessings) read allegorically -- the sacrifices and
     the priesthood fulfilled in Christ and enacted in the soul. The base is the
     constituted READING TEXT of the critical edition -- W. A. Baehrens, *Origenes Werke*
     VI (GCS 29, Leipzig 1920), pp. 280-507 (In Leviticum, the section of that volume
     following Exodus) -- freshly transcribed from the page scans and driven through the
     full refinement pipeline (B image collation, R4 boundaries, R1 Migne PG 12, R3 the
     Barkley FOTC 83 oracle, R5 whole-corpus consistency, R6 the apparatus/variant pass,
     R7 the page-anchor strip). Rufinus translates freely but faithfully; this is still a
     translation of a translation: we render what the Latin says, as it says it, without
     harmonizing to the Vulgate, to the LXX, or to a modern Bible.

  2. UNIT OF WORK IS A WHOLE HOMILY. Each source file `homilyNN_latin.txt` (NN = 01..16,
     zero-padded) is one complete unit, translated in a single call. Most are short
     (2-12 numbered sections each), so a whole homily is a clean single-shot; the
     block-by-block fallback keeps the longer ones (V, VII, VIII, IX, XVI) safe if a
     single-shot truncates or drifts.

  3. PLAIN-TEXT SHAPE. Each file opens with a FOUR-line `#`-comment provenance header, a
     `====...` separator line, and then the body. As in Exodus, the body IS
     blank-line-delimited: `HOMILIA <ROMAN>.` and the lemma sit on two consecutive lines
     with NO blank between, the first section is glued straight onto the lemma (again no
     blank), and thereafter every numbered section is its own blank-line-separated
     paragraph:

         # Origen, Homilies on Leviticus -- Homily 2 (Lev. 4 ...).
         # ... (3 more # lines) ...
         ============================================================
         HOMILIA II.
         *De sacrificiorum ritu, hoc est de muneribus ...*
         1. Superior quidem de principiis Levitici disputatio ...
         <blank>
         2. Et primo velim videre, quae sit ista differentia ...

     Parsing (all deterministic):
     * The FOUR `#` lines and the `====` separator are FRONT MATTER: discarded, never
       sent to the model; a fresh English provenance header is emitted instead.
     * The HEADING is the first body line, `HOMILIA <ROMAN>.` (all sixteen are plain --
       none bracketed). Held aside (never sent to the model) and re-emitted
       deterministically as `HOMILY <ROMAN>.`, the numeral taken from the FILENAME -- so
       the homily number can never be corrupted.
     * The LEMMA is the next line, `*…*` (the Leviticus passage under comment, a
       descriptive rubric that itself often quotes Scripture in `»…«` and ends "et
       cetera"). Fifteen homilies have one. HOMILY I HAS NONE: in its place Baehrens
       prints no title, and the base carries an editorial note line `[Titulus deest — …]`.
       That note is NOT a lemma and is NOT sent to the model; it is held aside and a fixed
       English editorial note is emitted in its place.
     * Everything after is exposition: one numbered section per blank-line-separated
       paragraph. Every homily's exposition starts at section 1 (no unnumbered opener).

  4. MARKUP still carried in the base (all load-bearing, all handled in the prompt):
       »…«     Scripture Origen quotes             -> keep the guillemets, translate his wording
       *…*     the Leviticus lemma under comment    -> keep the * marks, translate the words
       […]     an editor's word seclusion/supplement-> read in the sense the grammar needs,
                                                        do NOT print the [ ] brackets
       ἅγιος   one Greek word (Homily XI §2)        -> KEEP it in Greek, gloss it (see rule 6)
     PAGE ANCHORS `[GCS p.N]` (and any `[PG …]` Migne columns) were STRIPPED from this base
     in the R7 cleanup pass, so normally there are none left; `strip_anchors` defensively
     removes any that remain (rejoining a word split across a page break). There are only
     FOUR editor's square-bracket interventions in the whole corpus -- the two secluded
     first-fruits phrases in Homily II (`[de primis frugibus,]`, `[igni quoque … sunt]`)
     and the single supplied words `[qui]` (Homily VI) and `[et]` (Homily VII). There are
     NO `⟨…⟩` angle-bracket supplements, NO `'…'` non-scriptural single-quote speeches,
     NO `›…‹` nested catch-words, and NO `…`/`****` lacunae. Aside from `ἅγιος` there is no
     Greek script in the body.

  5. SCRIPTURE IS THE FIRST RULE. Origen quotes a pre-Vulgate Old-Latin / Septuagint text
     and his argument often turns on his exact wording; Rufinus renders those citations
     into Latin. Translate the quotation AS IT STANDS in the Latin -- never substitute a
     modern Bible, never call a verse-lookup tool, never normalize to the Vulgate.
     LEVITICUS CHAPTER/VERSE NUMBERING FOLLOWS THE LXX (as Origen/Rufinus cite it), which
     diverges from the Vulgate/MT by up to a chapter across Lev 5-6 (the trespass/sin-
     offering laws); give the number as the Latin implies it. Psalms follow LXX numbering,
     and the historical books are the LXX "Kingdoms" (1-4 Kingdoms = 1-2 Samuel + 1-2
     Kings). Biblical NAMES are Baehrens's printed Old-Latin forms (Istrahel, Moyses,
     Aaron, Nadab, Abiud, Melchisedech, Aegyptius, Hierusalem): render them by their
     standard English equivalents.

  6. GREEK WORD + SCAPEGOAT TERM. (a) In Homily XI §2 Origen (through Rufinus) explains
     the Greek word `ἅγιος` ("holy") by an etymology -- "quod dicitur ἅγιος, quasi extra
     terram esse significat" (as though it meant 'outside the earth'). KEEP `ἅγιος` in
     Greek script and translate the surrounding clause so the etymology stays visible
     (e.g. "the word said in Greek, ἅγιος ('holy'), signifies as it were 'outside the
     earth'"). (b) In the Day-of-Atonement homilies (IX-X, Lev 16) the second of the
     "two goats" is the `hircus apopompaeus` -- the goat "sent away" into the wilderness
     (Greek ἀποπομπαῖος, the scapegoat; the »sors apopompaei« is the lot "of the sending-
     away"). Render it as "the scapegoat" while keeping the term Origen leans on (e.g.
     "the goat that is the apopompaeus (the one sent away)") on first mention.

  7. --images: CONSULT THE PAGE SCANS (optional, OFF by default). The GCS 29 pages each
     homily spans are pre-rendered under `_source/gcs29_pages/` as
     `gcs29_p<PAGE>_leaf<LEAF>.jpg`. The printed-page -> archive-leaf offset DRIFTS
     (+59 at p.280 growing to +72 at p.507, because unnumbered/duplicate leaves are
     interleaved), so the leaf number is NOT computable from the page -- the scans are
     found by GLOBBING `gcs29_p<PAGE>_*.jpg` (the 13 shared pages have two leaves; either
     is legible, the first is used). `--images` hands a call that homily's page scans and
     tells the model to open one whenever a reading looks impossible or smells like a
     mis-transcription and to follow the printed MAIN Latin text. These are SINGLE-column
     pages (Rufinus's Latin only -- no facing Greek): read the main text block and ignore
     the critical apparatus at the foot, the margins, running headers, and page numbers.
     Degrades gracefully to text-only if the scans are unavailable.

STRUCTURAL FINGERPRINT. The heading is held aside, the titulus note (Homily I) is handled
deterministically, and the anchors are gone, so per homily we verify ONE thing: the number
of translatable blocks (the `*…*` lemma, when present, + the numbered sections) returned
equals the number sent. On mismatch (or a suspiciously short output) we retry once with an
explicit block-count reminder; if it still fails we fall back to translating each block on
its own, which preserves the count by construction.

FRONT MATTER is never sent to the model: the source `#` header and `====` separator are
discarded and a fresh English provenance header is emitted deterministically.

    python3 translate_origen_leviticus_homilies.py homily06_latin.txt   # bare name
    python3 translate_origen_leviticus_homilies.py /abs/path/file.txt   # full path
    python3 translate_origen_leviticus_homilies.py <directory>          # batch a dir
    python3 translate_origen_leviticus_homilies.py                      # batch default dir

    --images  consult the GCS 29 page scans for doubtful readings (see rule 7)
    --force   re-translate even if the output already exists
    --check   parse only: validate heading/lemma/block round-trip, print structure, no calls

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
    "Origen of Alexandria/Homilies on Leviticus"
)
SOURCE_DIR = os.path.join(BASE, "LATIN")
TARGET_DIR = os.path.join(BASE, "english")

# Optional --images consultation. The GCS 29 pages are rendered under _source/gcs29_pages/
# as gcs29_p<PAGE>_leaf<LEAF>.jpg. The printed-page -> leaf offset DRIFTS (+59 -> +72), so
# the leaf is not computable: scans are found by globbing gcs29_p<PAGE>_*.jpg.
IMAGE_DIR = os.path.join(BASE, "_source", "gcs29_pages")

AUTHOR = "Origen of Alexandria"
WORK = "Homilies on Leviticus (Homiliae in Leviticum)"
TRANSLATOR_NOTE = "in the Latin translation of Rufinus of Aquileia"

FILE_RE = re.compile(r"^homily\d+_latin\.txt$")

RETRY_DELAYS = [5, 15, 45]
RATE_LIMIT_DELAYS = [60, 120, 240]

# Per-homily Leviticus coverage (verified R5/consistency passage table) + GCS 29 printed-
# page range, for the output header and the --images scan lookup. The sixteen homilies run
# I-XVI without gap; the 13 "shared" pages (288, 316, 332, 358, 370, 393, 417, 440, 454,
# 467, 478, 487, 491) close one homily and open the next, so they appear in two adjacent
# ranges (harmless for globbing).
HOMILY_META = {
    1:  ("prologue — the spiritual sense beneath the letter of the Law; Lev. 1 (the whole burnt offering)", (280, 288)),
    2:  ("Lev. 4 — the sin offerings (for priest, congregation, people); the peace offerings (Lev. 3)", (288, 299)),
    3:  ("Lev. 5 — oaths; touching the unclean; the guilt offering", (300, 316)),
    4:  ("Lev. 6 LXX (MT 5:20–26) — the trespass offering and restitution", (316, 332)),
    5:  ("Lev. 6:24 ff. — the law of the sin offering and the offering-portions", (332, 358)),
    6:  ("Lev. 8 — the consecration; the vestments of the high priest and priests", (358, 370)),
    7:  ("Lev. 10–11 — wine forbidden to the priests; clean and unclean animals", (370, 393)),
    8:  ("Lev. 12–14 — childbirth; leprosy and the purifications of the leper", (393, 417)),
    9:  ("Lev. 16 — the Day of Atonement; the two goats; entry into the holy of holies", (417, 440)),
    10: ("Lev. 16 (continued) — the fast of the Day of Atonement; the scapegoat", (440, 445)),
    11: ("Lev. 19–20 — “be holy, for I am holy”; the holiness code", (446, 454)),
    12: ("Lev. 21 — the great high priest; priestly holiness", (454, 467)),
    13: ("Lev. 23–24 — the feasts; the lamp and lampstand; the shewbread (Lev. 24:1–9)", (467, 478)),
    14: ("Lev. 24:10–23 — the blasphemer (the son of the Israelite woman and the Egyptian father)", (478, 487)),
    15: ("Lev. 25 — the Jubilee; the sale and redemption of houses", (487, 491)),
    16: ("Lev. 26 — the blessings (and curses) of Leviticus", (491, 507)),
}

# The Latin heading LINE at the very start of the body: `HOMILIA <ROMAN>.`. All sixteen are
# plain (none bracketed). Peeled off the first line, held aside, re-emitted in English from
# the filename numeral. The optional bracket groups are kept only for robustness.
HEADING_LINE_RE = re.compile(r"^(\[?)HOMILIA\s+([IVXLCDM]+)\.(\]?)[ \t]*(?:\n|$)")

# Homily I carries, in the lemma position, Baehrens's editorial note that no title is
# transmitted -- NOT a lemma. Detected and held aside; a fixed English note is emitted.
TITULUS_RE = re.compile(r"^\[Titulus deest\b")
TITULUS_NOTE_EN = (
    "[No title is transmitted: the title is absent in the manuscript classes (Baehrens); "
    "Homily I stands without a title.]"
)

# The `[GCS p.N]` page anchor and `[PG …]` Migne column -- already stripped from this base
# in the R7 cleanup pass, so normally absent; removed defensively here. An anchor can sit at
# a page's first prose word OR split a word across a page break (`pres[GCS p.259]byteri`), so
# removal is a bare delete followed by a space-collapse (which rejoins split words). The
# word seclusions/supplements (`[de primis frugibus,]`, `[igni quoque …]`, `[qui]`, `[et]`)
# and the `[Titulus deest …]` note are NOT anchors (the pattern only matches `[GCS p.N]` /
# `[PG …]`) and are left in place.
GCS_ANCHOR_RE = re.compile(r"\[GCS p\.\d+\]|\[PG[^\]]*\]")

SEP_OUT = "=" * 66  # separator between the English provenance header and the body


# --- Roman numerals (homily labels) -------------------------------------------

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


# --- Parsing ------------------------------------------------------------------


def parse_text(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def split_frontmatter(raw):
    """Drop the leading `#`-comment header (4 lines: title + Source + notes), the `====`
    separator line, and any blank lines after them; return the body. The source header is
    never carried over or sent to the model -- a fresh English provenance header is
    emitted instead."""
    lines = raw.split("\n")
    i = 0
    while i < len(lines) and lines[i].lstrip().startswith("#"):
        i += 1
    # skip a separator line of '='s and any surrounding blank lines
    while i < len(lines) and (not lines[i].strip() or set(lines[i].strip()) == {"="}):
        i += 1
    return "\n".join(lines[i:]).lstrip("\n")


def strip_anchors(text):
    """Remove any residual `[GCS p.N]` / `[PG …]` anchor, rejoining a word split across a
    page break and collapsing the gap where the anchor sat between words (never touching
    newlines). Normally a no-op: the base was cleaned of anchors in the R7 pass."""
    text = GCS_ANCHOR_RE.sub("", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return "\n".join(line.rstrip() for line in text.split("\n"))


def paragraphs(text):
    """Blank-line-delimited non-empty blocks. In this base each exposition SECTION is one
    such block, so this both segments the source sections and counts the model's returned
    blocks."""
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def homily_number(basename):
    m = re.search(r"homily(\d+)", basename)
    return int(m.group(1)) if m else -1


def parse_homily(body):
    """Return (heading_or_None, titulus_note_or_None, [translatable blocks]).

    The `HOMILIA <ROMAN>.` heading line is peeled off the front and held aside as
    {'bracketed': bool}. The next line is either the LEMMA (`*…*`, block 0) or -- for
    Homily I -- the `[Titulus deest …]` note, which is held aside (titulus_note) and NOT
    sent to the model. Everything after is the exposition, one block per blank-line-
    separated section (every homily's sections start at 1). So the block count is
    (lemma?) + sections."""
    body = strip_anchors(body).strip("\n")
    m = HEADING_LINE_RE.match(body)
    heading = None
    if m:
        heading = {"bracketed": bool(m.group(1) and m.group(3))}
        body = body[m.end():].lstrip("\n")
    if not body:
        return heading, None, []
    # The line right after the heading is the lemma OR Homily I's titulus note; the
    # exposition (blank-line-separated sections) follows, glued to it by a single newline.
    first_line, _, rest = body.partition("\n")
    first_line = first_line.strip()
    titulus = None
    lemma = None
    if TITULUS_RE.match(first_line):
        titulus = first_line          # Homily I: no lemma
    else:
        lemma = first_line            # *…* lemma
    sections = paragraphs(rest)
    blocks = ([lemma] if lemma else []) + sections
    return heading, titulus, [b for b in blocks if b]


# --- Scaffolding cleanup ------------------------------------------------------

SCAFFOLD_KEYWORDS = (
    "i'll translate", "i will translate", "let me translate", "let me render",
    "let me produce", "i'm going to translate", "i am going to translate",
    "here is the translat", "here's the translat", "here is my translat",
    "here is the english", "the translated text", "translated text:",
    "preserving all", "preserve all", "section marker", "section number",
    "paragraph structure", "output only", "i must output", "i need to translate",
    "the latin text", "here is the latin", "let me check", "let me look",
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

_image_map = None  # cache: {homily_number: [existing scan paths]}


def load_image_map():
    """Build {homily_number: [scan paths that exist]} by globbing gcs29_p<PAGE>_*.jpg for
    each page in the homily's range (the leaf offset drifts, so the leaf can't be computed).
    Shared pages have two leaves -- the first (sorted) is used. Empty per homily if the
    scans are missing (so --images degrades to text-only)."""
    global _image_map
    if _image_map is not None:
        return _image_map
    _image_map = {}
    for n, (_ref, (lo, hi)) in HOMILY_META.items():
        paths = []
        for page in range(lo, hi + 1):
            hits = sorted(glob.glob(os.path.join(IMAGE_DIR, f"gcs29_p{page}_*.jpg")))
            if hits:
                paths.append(hits[0])
        _image_map[n] = paths
    return _image_map


def image_paths_for(basename):
    return load_image_map().get(homily_number(basename), [])


_IMAGE_RULE = (
    "\nPAGE IMAGES (use them to check doubtful readings). Scans of the printed GCS 29 "
    "pages this homily spans are listed below, in order. The Latin above is transcribed "
    "and already page-verified through several passes, but a rare valid-but-wrong-word "
    "slip can still hide. Whenever a word or phrase is grammatically impossible, breaks "
    "the sense, or looks like a plausible mis-transcription, OPEN the matching page image "
    "with your file-reading tool and translate the reading the printed page actually "
    "shows. These are SINGLE-column pages (Rufinus's Latin only -- there is no facing "
    "Greek): read the main text block and IGNORE the critical apparatus at the foot of "
    "the page, the margins, running headers, and page numbers. Do not otherwise emend, and "
    "do not add notes about what you checked -- output only the translation.\n"
)


def image_block(paths):
    return (_IMAGE_RULE + "\n".join(paths) + "\n") if paths else ""


# --- Prompt -------------------------------------------------------------------

_COMMON_RULES = (
    "- SCRIPTURE (most important). Origen quotes the Bible constantly, in a pre-Vulgate "
    "Old-Latin / Septuagint (LXX) form that often differs from the Vulgate or a modern "
    "English Bible; his exposition frequently turns on his exact wording, and Rufinus "
    "renders those citations into Latin. Translate every quotation AS IT STANDS in the "
    "Latin -- its wording, order, and sense -- into natural English. Do NOT substitute a "
    "standard modern translation, do NOT normalize to the Vulgate, do NOT call any "
    "Bible/verse-lookup tool, and do NOT shift to Hebrew versification. LEVITICUS itself "
    "is cited in LXX chapter/verse numbering, which can run up to a chapter ahead of the "
    "Vulgate/MT across Lev 5-6 (the sin/trespass-offering laws); Psalms follow LXX "
    "numbering; the historical books are the LXX 'Kingdoms' (1-4 Kingdoms = 1-2 Samuel + "
    "1-2 Kings). Give the number as the Latin implies it (you may add the modern "
    "equivalent in brackets). Translate scripture book names to English (liber Levitici -> "
    "the book of Leviticus). A lemma or quotation ending 'et cetera' -> 'and so forth'.\n"
    "- SACRIFICIAL / PRIESTLY VOCABULARY (keep it consistent throughout). holocaustum -> "
    "the whole burnt offering (or 'holocaust'); sacrificium -> sacrifice; munus -> "
    "offering/gift; hostia -> victim/offering; oblatio / oblatum -> offering; sacrificium "
    "pro peccato -> the sin offering; sacrificia salutaria -> the peace (salutary) "
    "offerings; pontifex -> the high priest; sacerdos -> priest; sacerdotium -> the "
    "priesthood; Levita/Levitae -> Levite/Levites; altare -> the altar; tabernaculum "
    "testimonii -> the tabernacle of testimony (of witness); sancta sanctorum -> the holy "
    "of holies; dies propitiationis -> the Day of Atonement; ieiunium -> the fast; hircus "
    "-> the goat; vitulus -> the (bull-)calf; adeps/adipes -> the fat; lepra -> leprosy, "
    "leprosus -> the leper; mundus/immundus -> clean/unclean; panes propositionis -> the "
    "shewbread (the bread of the presentation); candelabrum -> the lampstand; lucerna -> "
    "the lamp.\n"
    "- NAMES. Use standard English biblical forms; the Latin keeps Baehrens's printed "
    "Old-Latin spellings, which you normalize only in the English. Core: Iesus -> Jesus, "
    "Christus -> Christ, Dominus -> the Lord, Salvator -> the Savior, Spiritus sanctus -> "
    "the Holy Spirit, Verbum (Dei) -> the Word (of God), filius/unigenitus -> the Son / "
    "the only-begotten, Pater -> the Father, Trinitas -> the Trinity. Leviticus cast & "
    "places: Moyses -> Moses, Aaron -> Aaron, Nadab -> Nadab, Abiud -> Abihu (Nadab and "
    "Abihu, Lev 10), Levi -> Levi, Istrahel/Istrahelitae -> Israel/Israelites, "
    "Istrahelita / filius mulieris Istrahelitidis -> the Israelite / the son of the "
    "Israelite woman (Homily XIV), Hebraei -> the Hebrews, Aegyptius/Aegyptii -> "
    "Egyptian/Egyptians, Aegyptus -> Egypt, Melchisedech -> Melchizedek, Sina -> Sinai. "
    "Other biblical figures: Abraham/Isaac -> Abraham/Isaac, Iacob -> Jacob, Ioseph -> "
    "Joseph, Iuda(s) -> Judah, Ruben -> Reuben, Beniamin -> Benjamin, Sem -> Shem, Iaphet "
    "-> Japheth, Cain -> Cain, Adam -> Adam, David -> David, Solomon -> Solomon, Esaias -> "
    "Isaiah, Hieremias -> Jeremiah, Ezechiel -> Ezekiel, Iob -> Job, Achab -> Ahab, "
    "Susanna -> Susanna, Lazarus -> Lazarus, Cherubim/Seraphim -> cherubim/seraphim. NT "
    "figures: Petrus -> Peter, Paulus / Apostolus -> Paul / the Apostle, Iohannes -> "
    "John, Cornelius -> Cornelius, Barabbas -> Barabbas, Pilatus -> Pilate, Pharisaei -> "
    "the Pharisees. Groups & places: Iudaei -> the Jews, Ecclesia -> the Church, synagoga "
    "-> the synagogue, Hierusalem/Ierusalem -> Jerusalem, Sion -> Zion, Babylon -> "
    "Babylon. GENERAL RULE for a name Origen ETYMOLOGIZES or puns on: KEEP the "
    "transliterated form he actually uses (so the wordplay stays visible), giving the "
    "standard English equivalent in parentheses on first mention (e.g. Melchisedech = "
    "'king of righteousness'). Keep a brief parenthetical Latin term only where it carries "
    "the argument.\n"
    "- THE GREEK WORD ἅγιος (Homily XI §2 only). Origen explains the Greek word for "
    "'holy', ἅγιος, by an etymology (as though it meant 'outside the earth'). KEEP ἅγιος "
    "in Greek script in your English and render the clause so the etymology survives (e.g. "
    "\"the word spoken in Greek, ἅγιος ('holy'), signifies as it were 'outside the "
    "earth'\"). Do not drop it, transliterate it away, or replace it with 'holy' alone.\n"
    "- THE TWO GOATS / SCAPEGOAT (Homilies IX-X, Lev 16). Of the two goats, one falls to "
    "the Lord and one is the `hircus apopompaeus` -- the goat 'sent away' into the "
    "wilderness (Greek ἀποπομπαῖος; the »sors apopompaei« is the lot 'of the sending-"
    "away', i.e. the scapegoat). Render it 'the scapegoat', but on first mention keep the "
    "term Origen builds on, e.g. 'the goat that is the apopompaeus (the one sent away)'.\n"
    "- EDITORIAL MARKS. The base carries only FOUR of the critical editor's square-bracket "
    "interventions, all word-level. In Homily II two secluded phrases in the first-fruits "
    "passage, `[de primis frugibus,]` ('of the first fruits') and `[igni quoque eam "
    "torreri vult, medio fractam esse … quia primitiae sunt]`; in Homily VI a supplied "
    "`[qui]`; in Homily VII a supplied `[et]`. In every case read the word(s) in the sense "
    "the grammar and context require and translate them naturally as part of the sentence "
    "-- do NOT reproduce the square brackets in the English.\n"
    "- THIS IS RUFINUS'S LATIN OF ORIGEN'S LOST GREEK. Translate what the Latin actually "
    "says, as it says it -- do NOT 'improve' it, harmonize it with the Vulgate or the "
    "Septuagint, or reconstruct what Origen 'really meant'. Represent the Latin witness "
    "faithfully and COMPLETELY; do not paraphrase, summarize, abridge, or 'correct' the "
    "exegesis, which reads the sacrifices, the priesthood, the purity laws, and the feasts "
    "as fulfilled in Christ and enacted spiritually in the soul. The closing DOXOLOGY is "
    "deliberately NOT uniform across the collection -- render each exactly as it stands, "
    "it is not a slip. Most homilies end '…cui est gloria et imperium in saecula "
    "saeculorum. Amen' (to whom be glory and dominion unto the ages of ages. Amen) and "
    "most wrap the doxology inside guillemets »…«; but note the variants: Homily II reads "
    "'cui LAUS et gloria …' (to whom be praise and glory); Homilies IX and XII drop 'est' "
    "('cui gloria et imperium …'); Homily XIII reads 'IPSI gloria et imperium …' (to Him "
    "be glory); Homily XIV reads 'QUI est gloria …'; Homily XVI reads 'Ipsi gloria in "
    "AETERNA saecula saeculorum! Amen' (to Him be glory unto the eternal ages of ages) "
    "with NO 'imperium' and NO guillemets; and the closings vary between 'Amen', 'Amen.', "
    "and 'Amen!'. Keep whatever guillemets and punctuation the Latin doxology carries.\n"
    "- REGISTER. Aim for clear, faithful, dignified English suited to a patristic homily. "
    "Keep Origen's direct address to the congregation ('let us see…', 'consider…') and "
    "his argumentative connectives (enim, ergo, autem, quoniam, sicut… ita) -- the "
    "reasoning is step-by-step and the logic must survive. Keep theological terms "
    "consistent throughout. Long periodic sentences may be broken for readability, but do "
    "not drop clauses.\n"
    "- The Latin is a verified base; if an obvious residual typo remains, translate the "
    "evidently intended word without flagging it.\n"
)


def build_prompt(text, reminder="", images=None):
    return (
        f"Translate the following Latin text into English. It is from {AUTHOR}'s "
        f"{WORK}, {TRANSLATOR_NOTE} -- Origen's Greek homilies on Leviticus survive only "
        f"in Rufinus's Latin (c. 403-405), in the constituted reading text of the critical "
        f"edition (W. A. Baehrens, GCS 29, 1920). All sixteen homilies are extant; Origen "
        f"expounds selected passages of Leviticus (the burnt offering and the sacrificial "
        f"laws, the sin and guilt offerings, the priestly consecration and vestments, "
        f"clean and unclean animals, childbirth and leprosy, the Day of Atonement and the "
        f"two goats, the holiness code, the great high priest, the feasts and the "
        f"shewbread, the blasphemer, the Jubilee, and the blessings), phrase by phrase, "
        f"morally and allegorically -- the sacrifices and the priesthood fulfilled in "
        f"Christ and enacted in the soul.\n\n"
        "Rules:\n"
        "1. Output ONLY the translated text -- no preamble, notes, meta-commentary, or "
        "quotation of the Latin. Do not write 'Here is the translation' or 'Let me "
        "translate'.\n"
        "2. Preserve the paragraph structure EXACTLY: one blank line between blocks, the "
        "same number of blocks, one translated paragraph per source paragraph; do not "
        "merge or split paragraphs. Keep each section number (1., 2., 3., …) at the head "
        "of its paragraph.\n"
        "3. Text between guillemets `» «` is Scripture Origen QUOTES. Keep the guillemets "
        "`» «` around the quoted words in your English and translate them in his wording "
        "(see the Scripture rule below). Do not add or remove guillemets.\n"
        "4. Text between asterisks `* *` is the Leviticus passage under comment (the "
        "lemma). Keep the `* *` around it and translate the words as the Latin gives them. "
        "(The lemma is a descriptive rubric, e.g. '*On the vestments of the high priest "
        "and the priests.*', and often quotes Scripture; translate it fully and keep both "
        "the `* *` and any `» «` inside it.)\n"
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
    """A translation far shorter than the Latin is almost certainly cut off."""
    return len(translated) < 0.5 * len(source)


# --- Homily translation -------------------------------------------------------


def translate_blocks(blocks, images=None):
    """Translate a homily's blocks in a single call and structurally verify the block
    count (so nothing is merged, split, or dropped). Returns (list_of_blocks, ok); on
    failure the caller falls back to block-by-block. The heading and the Homily I titulus
    note are handled by the caller, not the model."""
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
        f"5. The source has EXACTLY {len(blocks)} paragraph(s) separated by blank "
        f"lines. Return EXACTLY that many translated paragraphs, one per source "
        f"paragraph, in order; do not merge, split, add, or drop any. Keep every `» «` "
        f"and `* *` mark and every section number. Translate through to the final "
        f"sentence.\n"
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
    """A fresh, deterministic English provenance block for the output file (the Latin
    source header is never carried over or sent to the model)."""
    n = homily_number(basename)
    ref = HOMILY_META.get(n, (None, None))[0]
    unit = f"Homily {n}" + (f" ({ref})" if ref else "")
    return (
        f"# Origen, *Homilies on Leviticus* — English translation — {unit}\n"
        f"# Origen's Greek homilies on Leviticus, surviving only in Rufinus of Aquileia's "
        f"Latin translation (c. 403–405): all sixteen extant. Fresh English rendering.\n"
        f"# Source text: W. A. Baehrens (ed.), *Origenes Werke* VI (GCS 29, Leipzig "
        f"1920), pp. 280–507 — the constituted reading text (verified through refinement "
        f"passes B, R1, R3, R5, R6, R7).\n"
        f"# Scripture is rendered in Origen's Old-Latin/Septuagint wording (LXX chapter, "
        f"Psalm, and Kingdoms numbering); biblical names follow standard English forms.\n"
        f"{SEP_OUT}"
    )


def render_output(basename, heading, titulus, blocks):
    """Assemble the English file body: the canonical `HOMILY <ROMAN>.` heading (from the
    filename), then -- for Homily I -- the fixed English titulus note in the lemma's place,
    then the translated blocks."""
    parts = []
    n = homily_number(basename)
    if heading is not None and n > 0:
        label = f"HOMILY {int_to_roman(n)}."
        if heading.get("bracketed"):
            label = f"[{label}]"
        parts.append(label)
    if titulus is not None:
        parts.append(TITULUS_NOTE_EN)
    parts.extend(blocks)
    return "\n\n".join(parts)


# --- Driver -------------------------------------------------------------------


def resolve_input(arg):
    if os.path.isabs(arg) or os.sep in arg:
        return arg
    return os.path.join(SOURCE_DIR, arg)


def output_path_for(input_file):
    name = os.path.basename(input_file)
    name = re.sub(r"_latin(\.txt)$", r"_english\1", name)
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

    body = split_frontmatter(parse_text(input_file))
    basename = os.path.basename(input_file)
    heading, titulus, blocks = parse_homily(body)

    images = None
    if use_images:
        images = image_paths_for(basename)
        if images:
            print(f"  Attaching {len(images)} page scan(s) for doubtful readings.")
        else:
            print("  --images requested but no scans available for this homily "
                  "-- translating text-only.")

    if heading is None:
        label = "NO HEADING"
    else:
        label = "bracketed heading" if heading.get("bracketed") else "heading"
    lemma_state = "titulus-deest note (no lemma)" if titulus else "lemma"
    print(f"  Translating {basename} ({label}, {lemma_state}, {len(blocks)} block(s), "
          f"{len(body)} chars)...")

    translations, ok = translate_blocks(blocks, images=images)
    if not ok:
        print("  (used block-by-block fallback)")
    if len(translations) != len(blocks):
        print(f"  WARNING: block count off after fallback "
              f"({len(translations)} vs {len(blocks)}) -- inspect manually.")

    # Soft fidelity signal (not a retry trigger): two ADJACENT `»…«` Scripture spans can
    # legitimately merge when English word order forces it, but occasionally a quotation
    # loses its marks. Surface a count mismatch so it can be spot-checked; the guillemets
    # stay balanced either way.
    src_q = "\n\n".join(blocks).count("»")
    out_q = sum(t.count("»") for t in translations)
    if out_q != src_q:
        print(f"  NOTE: Scripture-quote (»…«) count {src_q} -> {out_q} "
              f"-- a quotation span was merged/split; spot-check the marks.")

    out = english_header(basename) + "\n\n" + render_output(
        basename, heading, titulus, translations) + "\n"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(out)

    print(f"  Done -> {output_file}")
    return True


def order_key(name):
    return homily_number(name) if homily_number(name) >= 0 else 999


def collect_files(path):
    if os.path.isdir(path):
        return [os.path.join(path, f)
                for f in sorted(os.listdir(path), key=order_key)
                if FILE_RE.match(f)]
    return [path]


def check_files(files):
    """Parse-only self-test: prove the heading/lemma/block round-trip without any CLI
    calls. Reports per file the detected heading, whether it carries a lemma or the
    Homily I titulus note, and the block count, and verifies that the `» «` and `* *`
    marks are balanced in the source."""
    ok = True
    grand_blocks = 0
    for fp in files:
        body = split_frontmatter(parse_text(fp))
        basename = os.path.basename(fp)
        heading, titulus, blocks = parse_homily(body)
        n = homily_number(basename)
        joined = "\n\n".join(blocks)
        guil = joined.count("»") == joined.count("«")
        star = joined.count("*") % 2 == 0
        if heading is None:
            head = "(NO HEADING)"
        else:
            lbl = f"HOMILY {int_to_roman(n)}."
            head = f"[{lbl}]" if heading.get("bracketed") else lbl
        lemma_state = "titulus-deest" if titulus else "lemma"
        status = "OK"
        if heading is None and n > 0:
            status, ok = "NO HEADING FOUND", False
        # Homily I is the only one legitimately without a lemma.
        if titulus and n != 1:
            status, ok = "unexpected titulus note (only Homily I should lack a lemma)", False
        if not titulus and n == 1:
            status, ok = "Homily I should carry the titulus-deest note", False
        if not guil or not star:
            status, ok = (f"UNBALANCED marks (»«={guil}, **={star})", False)
        print(f"  {basename}: {head} | {lemma_state} | {len(blocks)} block(s) | "
              f"»«={joined.count('»')}/{joined.count('«')} "
              f"*={joined.count('*')}  [{status}]")
        grand_blocks += len(blocks)
    print(f"\n  TOTAL: {len(files)} file(s), {grand_blocks} blocks.")
    print("  Round-trip:", "OK — heading + marks consistent." if ok else "FAILED — see above.")
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
        print("No source files found (expected homily<NN>_latin.txt).")
        sys.exit(1)

    if check:
        print(f"Parse-only check of {len(files)} file(s):")
        sys.exit(0 if check_files(files) else 1)

    explicit_output = positional[1] if len(positional) >= 2 else None
    if explicit_output and len(files) > 1:
        print("Second positional output path is only valid for a single input file.")
        sys.exit(1)

    print(f"Found {len(files)} homily file(s) to translate"
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

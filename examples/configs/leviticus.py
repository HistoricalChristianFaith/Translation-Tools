"""Worked example config: Origen, *Homilies on Leviticus* (Rufinus's Latin, GCS 29, 16 homilies).

Reproduces the setup of the per-work scripts
examples/original-scripts/{translate_origen_leviticus_homilies,validate_origen_leviticus_translation,
grade_origen_leviticus_barkley}.py with the generic tools. Prompt text is ported from those
scripts (lightly condensed where noted).
"""

import glob
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import common as C  # noqa: E402

SLUG = "origen-leviticus"
AUTHOR = "Origen of Alexandria"
WORK = "Homilies on Leviticus (Homiliae in Leviticum)"
SOURCE_LANGUAGE = "Latin"
UNIT_NOUN = "Homily"
WORK_CONTEXT = (
    "Origen's Greek homilies on Leviticus survive only in Rufinus of Aquileia's Latin translation "
    "(c. 403-405), here in the constituted reading text of the critical edition (W. A. Baehrens, "
    "GCS 29, 1920). All sixteen homilies are extant; Origen expounds selected passages of Leviticus "
    "(the sacrificial laws, the priesthood, clean and unclean, the Day of Atonement, the feasts, the "
    "Jubilee), phrase by phrase, morally and allegorically -- the sacrifices and the priesthood "
    "fulfilled in Christ and enacted in the soul."
)

PROJECT = ("/path/to/Writings-Database-Non-English/"
           "Origen of Alexandria/Homilies on Leviticus")
SOURCE_DIR = os.path.join(PROJECT, "LATIN")
TARGET_DIR = os.path.join(PROJECT, "english")
SOURCE_SUFFIX = "_latin.txt"
TARGET_SUFFIX = "_english.txt"

# Body = `HOMILIA <ROMAN>.` line, then the `*lemma*` line (or Homily I's titulus note), then one
# numbered section per line.
BODY_HEADING_RE = r"^\[?HOMILIA\s+[IVXLCDM]+\.\]?$"
HELD_LINES = [(r"^\[Titulus deest\b",
               "[No title is transmitted: the title is absent in the manuscript classes (Baehrens); "
               "Homily I stands without a title.]")]
ANCHOR_RE = r"\[GCS p\.\d+\]|\[PG[^\]]*\]"

PAIRED_MARKS = [("»", "«")]
EVEN_MARKS = ["*"]

# (Leviticus passage, GCS 29 printed-page span, FOTC 83 0-based PDF-index span)
HOMILIES = {
    1: ("Lev. 1 (prologue; the whole burnt offering)", (280, 288), (43, 52)),
    2: ("Lev. 4 (the sin offerings; peace offerings)", (288, 299), (53, 65)),
    3: ("Lev. 5 (oaths; the unclean; the guilt offering)", (300, 316), (66, 83)),
    4: ("Lev. 6 LXX / MT 5:20–26 (trespass offering; restitution)", (316, 332), (84, 101)),
    5: ("Lev. 6:24 ff. (the law of the sin offering)", (332, 358), (102, 129)),
    6: ("Lev. 8 (consecration; priestly vestments)", (358, 370), (130, 142)),
    7: ("Lev. 10–11 (wine forbidden; clean & unclean animals)", (370, 393), (143, 166)),
    8: ("Lev. 12–14 (childbirth; leprosy & purifications)", (393, 417), (167, 189)),
    9: ("Lev. 16 (Day of Atonement; the two goats)", (417, 440), (190, 215)),
    10: ("Lev. 16 cont. (the fast; the scapegoat)", (440, 445), (216, 221)),
    11: ("Lev. 19–20 (»be holy, for I am holy«)", (446, 454), (222, 231)),
    12: ("Lev. 21 (the great high priest)", (454, 467), (232, 245)),
    13: ("Lev. 23–24 (the feasts; the lamp; the shewbread)", (467, 478), (246, 258)),
    14: ("Lev. 24:10–23 (the blasphemer)", (478, 487), (259, 269)),
    15: ("Lev. 25 (the Jubilee; sale & redemption of houses)", (487, 491), (270, 274)),
    16: ("Lev. 26 (the blessings — and curses)", (491, 507), (275, 291)),
}
UNIT_META = {n: v[0] for n, v in HOMILIES.items()}


def heading_en(n):
    return f"HOMILY {C.roman(n)}."


def english_header(n):
    return (
        f"# Origen, *Homilies on Leviticus* — English translation — Homily {n} ({UNIT_META[n]})\n"
        "# Origen's Greek homilies on Leviticus, surviving only in Rufinus of Aquileia's Latin "
        "translation (c. 403–405): all sixteen extant. Fresh English rendering.\n"
        "# Source text: W. A. Baehrens (ed.), *Origenes Werke* VI (GCS 29, Leipzig 1920), "
        "pp. 280–507 — the constituted reading text (verified through refinement passes B, R1, R3, "
        "R5, R6, R7).\n"
        "# Scripture is rendered in Origen's Old-Latin/Septuagint wording (LXX chapter, Psalm, and "
        "Kingdoms numbering); biblical names follow standard English forms."
    )


TRANSLATION_RULES = (
    "- THE LEMMA. The first block is the Leviticus passage under comment wrapped in `* *` (a "
    "descriptive rubric that often quotes Scripture); translate it fully, keeping both the `* *` "
    "and any `» «` inside it. A lemma or quotation ending 'et cetera' -> 'and so forth'.\n"
    "- SCRIPTURE (most important). Origen quotes a pre-Vulgate Old-Latin / Septuagint form, "
    "rendered by Rufinus into Latin. Translate every quotation AS IT STANDS -- never substitute a "
    "modern translation, normalize to the Vulgate, call a verse-lookup tool, or shift to Hebrew "
    "versification. LEVITICUS is cited in LXX numbering, up to a chapter ahead of the Vulgate/MT "
    "across Lev 5-6; Psalms follow LXX numbering; the historical books are the LXX 'Kingdoms'. "
    "Give the number as the Latin implies it (you may add the modern equivalent in brackets).\n"
    "- SACRIFICIAL / PRIESTLY VOCABULARY (keep consistent). holocaustum -> the whole burnt "
    "offering; sacrificium -> sacrifice; munus -> offering/gift; hostia -> victim/offering; "
    "sacrificium pro peccato -> the sin offering; sacrificia salutaria -> the peace (salutary) "
    "offerings; pontifex -> the high priest; sacerdos -> priest; tabernaculum testimonii -> the "
    "tabernacle of testimony; sancta sanctorum -> the holy of holies; dies propitiationis -> the "
    "Day of Atonement; lepra -> leprosy; mundus/immundus -> clean/unclean; panes propositionis -> "
    "the shewbread; candelabrum -> the lampstand.\n"
    "- NAMES. Standard English biblical forms (Iesus -> Jesus, Moyses -> Moses, Abiud -> Abihu, "
    "Istrahel -> Israel, Melchisedech -> Melchizedek, Hierusalem -> Jerusalem, Esaias -> Isaiah, "
    "Paulus / Apostolus -> Paul / the Apostle). Where Origen ETYMOLOGIZES a name, keep the form he "
    "uses and give the standard English in parentheses on first mention.\n"
    "- THE GREEK WORD ἅγιος (Homily XI §2 only). Keep ἅγιος in Greek script and render the clause "
    "so Origen's etymology ('as it were outside the earth') survives.\n"
    "- THE SCAPEGOAT (Homilies IX-X). The `hircus apopompaeus` is the goat 'sent away' "
    "(ἀποπομπαῖος): render 'the scapegoat', keeping the term on first mention, e.g. 'the goat that "
    "is the apopompaeus (the one sent away)'.\n"
    "- EDITORIAL MARKS. Only four editor's square-bracket interventions exist: Homily II "
    "`[de primis frugibus,]` and `[igni quoque … sunt]`, Homily VI `[qui]`, Homily VII `[et]`. Read "
    "them in sense and translate naturally; do NOT reproduce the brackets.\n"
    "- RUFINUS'S LATIN OF A LOST GREEK. Translate what the Latin says, as it says it -- do not "
    "harmonize with the Vulgate or LXX, reconstruct Origen, paraphrase, summarize, or abridge. The "
    "closing DOXOLOGY is deliberately NOT uniform (Hom II 'cui LAUS et gloria'; IX and XII drop "
    "'est'; XIII 'IPSI gloria'; XIV 'QUI est gloria'; XVI 'Ipsi gloria in AETERNA saecula "
    "saeculorum! Amen' with no 'imperium' and no guillemets; Amen / Amen. / Amen!): render each "
    "exactly as it stands, keeping its guillemets and punctuation.\n"
    "- REGISTER. Clear, faithful, dignified English suited to a patristic homily. Keep Origen's "
    "direct address and his connectives (enim, ergo, autem, sicut … ita); long periods may be "
    "broken but no clause dropped. If an obvious residual typo remains, translate the evidently "
    "intended word without flagging it.\n"
)

VALIDATION_HOUSE_RULES = (
    "  - Standard-English names for the Old-Latin/LXX forms (Istrahel->Israel, Moyses->Moses, "
    "Abiud->Abihu, Melchisedech->Melchizedek, Hierusalem->Jerusalem).\n"
    "  - THE GREEK WORD ἅγιος (Homily XI §2) KEPT in Greek with a gloss and the 'outside the earth' "
    "etymology -- correct, not untranslated.\n"
    "  - THE SCAPEGOAT TERM (Homilies IX-X): keeping 'apopompaeus' with a gloss -- not an addition.\n"
    "  - THE FOUR SECLUSIONS/SUPPLEMENTS (Hom II `[de primis frugibus,]`, `[igni quoque … sunt]`; "
    "Hom VI `[qui]`; Hom VII `[et]`) read in sense without brackets -- correct.\n"
    "  - NON-UNIFORM DOXOLOGIES rendered as printed (Hom II 'laus'; IX, XII no 'est'; XIII 'Ipsi'; "
    "XIV 'qui'; XVI 'in aeterna saecula', no 'imperium', no guillemets). Homily I has NO lemma and "
    "a bracketed '[No title is transmitted…]' note -- correct.\n"
    "  - SETTLED KEEP DECISIONS: Leviticus cited in LXX numbering (up to a chapter ahead of the "
    "Vulgate/MT across Lev 5-6); Homily XI reads »Iacobus« (James), not 'Paulus' -- render James; "
    "Homily IX keeps 'Soënen' and the 'tabernacle/ark of testimony'.\n"
    "  - Where the English renders Baehrens's MAIN text and it differs from a modern Bible, the "
    "Vulgate, or a manuscript variant, that is CORRECT.\n"
)

SHORT_BLOCK_RATIO = 0.70
SHORT_MIN_SOURCE = 200
ENDING_CHECKS = [(r"Amen", r"Amen", "closing doxology")]

IMAGE_DIR = os.path.join(PROJECT, "_source", "gcs29_pages")


def image_paths(n):
    """GCS 29 scans across the homily's printed pages. The page->leaf offset drifts (+59 -> +72),
    so scans are found by globbing the printed page, never by computing the leaf."""
    lo, hi = HOMILIES[n][1]
    out = []
    for page in range(lo, hi + 1):
        hits = sorted(glob.glob(os.path.join(IMAGE_DIR, f"gcs29_p{page}_*.jpg")))
        if hits:
            out.append(hits[0])
    return out


ORACLE_LABEL = ("Barkley, Origen: Homilies on Leviticus 1–16, Fathers of the Church 83 "
                "(Catholic University of America Press, 1990)")
ORACLE_SHORT = "Barkley"
ORACLE_PDF = os.path.join(PROJECT, "_source", "oracle", "oracle.pdf")
GRADING_CAVEATS = (
    "  - Barkley translated the SAME Baehrens GCS 29 edition, but at a number of spots he renders an "
    "apparatus variant / Delarue emendation, harmonises to the Vulgate/LXX, or makes an English-side "
    "slip. Where the Latin supports OUR reading, that is his choice/error, NOT our divergence. Known "
    "instances (ours correct): Hom III 'Elisha' (B. 'Elijah'), 'sevenfold grace' (B. 'seven "
    "spirits'); Hom V 'of vow' (B. 'of prayer'); Hom VIII 'health' (B. 'holiness'), 'oxen' (B. "
    "'calves'), livor 'bruise' (B. 'envy'); Hom IX 'Soënen' (B. 'Saba'); Hom XI Heb 12:9 attributed "
    "to JAMES (B. 'Paul'), firstborn 'consecrated' (B. 'sacrificed'); Hom XV 'could NOT free it' "
    "(B. drops 'not').\n"
    "  - The reference is a pdftotext extract: page numbers, running heads, inline footnote numbers "
    "and footnote text are noise. Barkley's expansions/footnotes are not our omissions.\n"
    "  - Our English keeps the Greek ἅγιος (Hom XI) and the 'apopompaeus' term with glosses; the "
    "doxologies are deliberately non-uniform. Not divergences.\n"
)


def oracle_text(n):
    """Prefer the per-homily extract made during pass R3; else carve the PDF page range."""
    r3 = os.path.join(PROJECT, "_source", "scratchpad", "oracle", f"oracle_hom{n:02d}.txt")
    text = C.oracle_from_file(r3)
    if text:
        return text
    lo, hi = HOMILIES[n][2]
    cache = os.path.join(PROJECT, "_source", "oracle", f"oracle_hom{n:02d}.txt")
    return C.oracle_from_pdf_pages(ORACLE_PDF, lo + 1, hi + 1, cache)

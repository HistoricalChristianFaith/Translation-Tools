#!/usr/bin/env python3
"""GRADE our English translation of Origen's *Homilies on Leviticus* (Rufinus's Latin)
against our ORACLE English -- Gary Wayne Barkley's published translation (Fathers of the
Church 83, 1990) -- WITHOUT touching our files. This is the read-only, scoring sibling of
the Exodus/Heine grader: it measures HOW CLOSE OUR SENSE IS TO BARKLEY'S, homily by homily,
and prints a grade plus an itemised list of the places we significantly diverge.

WHAT THIS DOES (and does NOT do)
--------------------------------
  * It NEVER writes to our English, the Latin, or any report file. Its only writes are the
    (git-ignored) oracle text cache and the transcript logs; it commits nothing.
  * BARKLEY IS THE YARDSTICK. The grade answers one question: how faithfully does OUR English
    convey the same SENSE as Barkley's published translation? He is the reference for meaning.
    (The Latin is supplied only as context, so the grader can tell a genuine sense-divergence
    apart from a mere wording difference, from Barkley's own interpretive freedom, OR from a
    place where Barkley follows a different Latin reading than our base does -- see below. The
    Latin is NOT the referee here.)
  * "Divergence" means a difference in MEANING, not style. Our wording is our own and is
    expected to differ from his; that is not penalised. Only a shift in what the sentence
    SAYS -- an omission, an addition, a flipped/altered sense, a mis-set Scripture
    reference, a name handled so as to change the referent -- counts.

THE CRUCIAL LEVITICUS CAVEAT -- BARKLEY SOMETIMES DIFFERS FROM OUR BASE. Barkley translated
the SAME critical edition as ours (Baehrens, GCS 29 = *Origenes Werke* VI, In Leviticum
pp. 280-507). BUT our English deliberately renders Baehrens's constituted MAIN text, while
Barkley at a number of spots renders instead a reading from Baehrens's critical APPARATUS
(a manuscript variant / Delarue emendation), harmonises to the Vulgate/LXX, or -- repeatedly
in this corpus -- simply makes an English-side slip. Our R3 oracle back-check (Barkley FOTC
83) found ~24 such places and KEPT our main-text reading at EVERY one: in each case our Latin
faithfully reproduces the GCS main text and Barkley diverges. Notable instances (ALL: ours is
correct, do NOT penalise):
  - Hom III "Elisha" (bones that raise the dead) [Barkley "Elijah" -- English slip];
  - Hom III "sevenfold grace" [Barkley "seven spirits", paraphrase toward Rev 1:4];
  - Hom V "of vow" [Barkley "of prayer"]; the vessel order oven→gridiron→frying-pan;
  - Hom VIII Jer 30:17 "health" [Barkley "holiness" -- slip]; 1 Cor 9:9 "oxen"
    [Barkley "calves"]; Isa 1:6 "bruise"/livor [Barkley "envy"];
  - Hom IX place "Soënen"/Syene [Barkley "Saba", an apparatus variant]; the ark as
    "testimony"/"covenant" (a GCS-internal *testimonii*/*testamenti* variation, both exact);
  - Hom XI Heb 12:9 attributed to JAMES [Barkley "Paul", the Delarue emendation]; firstborn
    "sanctified/consecrated" [Barkley "sacrificed"]; the Greek word ἅγιος kept by design;
  - Hom XIV the Reuben/Judah pairing (Barkley's English is self-contradictory; ours is right);
  - Hom XV the redemption clause keeps its negation "could NOT free it" (Barkley drops it).
Where OUR English faithfully renders the GCS main text shown in the Latin and Barkley differs
by following a variant, by translator's freedom, or by an English slip, that is NOT our
divergence. The grader is told this explicitly and uses the Latin to adjudicate.

THE ORACLE IS A COPYRIGHT PDF -- but, unlike Heine's FOTC 71 (Genesis + Exodus in one book),
Barkley's FOTC 83 is a SINGLE-work volume: it contains ONLY the sixteen Leviticus homilies,
in order, so there is no like-numbered cross-work collision. Homily 1's body begins at PDF
idx 43 (pg 44) and the sixteen run to PDF idx 291; back matter (INDICES) begins at idx 292.
This grader prefers the per-homily extracts our R3 pass already produced:
  1. a hand-split `_source/oracle_txt/homilyNN_en.txt`, if present (zero-padded NN); else
  2. the R3 working extract `_source/scratchpad/oracle/oracle_homNN.txt` (present from R3);
     else
  3. a fresh `pdftotext -f/-l` extraction of that homily's page range from
     `_source/oracle/oracle.pdf`, cached to
     `_source/oracle/oracle_homNN.txt`.
Each extract begins at the homily's `Homily <N>` heading (which matches our Latin lemma;
Leviticus Homily I has NO title in Barkley either -- he opens directly into the exposition --
confirming our absent lemma) and includes Barkley's footnotes.

Because the reference is derived from a PDF, it carries mild noise -- page numbers, running
heads, FOOTNOTE numbers appended inline to words (e.g. 'Days,"1') and footnote text, and
hyphenation across line breaks; the grader is told to read through it and judge by SENSE.

COPYRIGHT. Barkley (Origen, *Homilies on Leviticus 1-16*, Fathers of the Church 83, Catholic
University of America Press, 1990) is IN COPYRIGHT and LOCAL-ONLY (the PDF and its text caches
are git-ignored). This script reads it as a private reference for comparison and prints only
brief snippets needed to name a divergence. It writes no report into our files and copies
nothing back into our translation.

COVERAGE. All 16 homilies have an oracle section and are graded. A missing English, Latin, or
oracle section for any homily is reported UNGRADED rather than crashing; a missing PDF or a
missing `pdftotext` degrades the affected homily to ungraded (never a crash).

    python3 grade_origen_leviticus_barkley.py homily06_english.txt   # bare name
    python3 grade_origen_leviticus_barkley.py /abs/path.txt          # full path
    python3 grade_origen_leviticus_barkley.py <directory>            # batch a dir
    python3 grade_origen_leviticus_barkley.py                        # batch the english/ dir

    --quiet          print each homily's grade line but not its divergence list
    --log-dir DIR    where to write per-call transcripts (default: ./grading_logs_leviticus)
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
    "Origen of Alexandria/Homilies on Leviticus"
)
SOURCE_DIR = os.path.join(BASE, "LATIN")            # our Latin base (context only)
TARGET_DIR = os.path.join(BASE, "english")          # our English (the thing being graded)

# In-copyright, LOCAL ONLY (Barkley, FOTC 83, 1990). The yardstick; git-ignored, never
# written back, never committed, wording never copied into our translation.
ORACLE_PDF = os.path.join(BASE, "_source", "oracle", "oracle.pdf")
# Optional hand-split per-homily extracts (zero-padded). If present, preferred over all else.
ORACLE_DIR = os.path.join(BASE, "_source", "oracle_txt")
# The R3 working extracts already on disk (present from the oracle back-check pass).
R3_EXTRACT_DIR = os.path.join(BASE, "_source", "scratchpad", "oracle")
# Per-homily pdftotext cache (built only if neither of the above extracts exists).
PDF_CACHE_DIR = os.path.join(BASE, "_source", "oracle")

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "grading_logs_leviticus")

AUTHOR = "Origen of Alexandria"
WORK = "Homilies on Leviticus (Homiliae in Leviticum)"
TRANSLATOR_NOTE = "in the Latin translation of Rufinus of Aquileia"
REF_AUTHOR = "Gary Wayne Barkley"
REF_LABEL = ("Barkley, Origen: Homilies on Leviticus 1–16, Fathers of the Church 83 "
             "(Catholic University of America Press, 1990)")
REF_SHORT = "Barkley"

# Per-homily Leviticus coverage (verified R5 passage table) + the homily's 0-based PDF-index
# range in the FOTC 83 volume (from oracle_pages_leviticus.md), used ONLY for the pdftotext
# fallback. FOTC 83 is a single-work volume, so no cross-work collision -- the range simply
# carves the homily out of the PDF. pdftotext pages are 1-based, so page = idx + 1.
HOMILY_META = {
    1:  ("Lev. 1 (prologue; the whole burnt offering)",            (43, 52)),
    2:  ("Lev. 4 (the sin offerings; peace offerings)",            (53, 65)),
    3:  ("Lev. 5 (oaths; the unclean; the guilt offering)",        (66, 83)),
    4:  ("Lev. 6 LXX / MT 5:20–26 (trespass offering; restitution)", (84, 101)),
    5:  ("Lev. 6:24 ff. (the law of the sin offering)",            (102, 129)),
    6:  ("Lev. 8 (consecration; priestly vestments)",             (130, 142)),
    7:  ("Lev. 10–11 (wine forbidden; clean & unclean animals)",  (143, 166)),
    8:  ("Lev. 12–14 (childbirth; leprosy & purifications)",       (167, 189)),
    9:  ("Lev. 16 (Day of Atonement; the two goats)",             (190, 215)),
    10: ("Lev. 16 cont. (the fast; the scapegoat)",               (216, 221)),
    11: ("Lev. 19–20 (»be holy, for I am holy«)",                 (222, 231)),
    12: ("Lev. 21 (the great high priest)",                        (232, 245)),
    13: ("Lev. 23–24 (the feasts; the lamp; the shewbread)",      (246, 258)),
    14: ("Lev. 24:10–23 (the blasphemer)",                         (259, 269)),
    15: ("Lev. 25 (the Jubilee; sale & redemption of houses)",    (270, 274)),
    16: ("Lev. 26 (the blessings — and curses)",                  (275, 291)),
}

FILE_RE = re.compile(r"^homily\d+_english\.txt$")
SEP_RE = re.compile(r"^=+$")
# A vestigial R3-style marker line ("===== PDF idx 43 ====="): stripped as noise if present.
PDF_IDX_MARKER_RE = re.compile(r"^\s*=+\s*PDF idx\s+\d+\s*=+\s*$", re.I)

RETRY_DELAYS = [5, 15, 45]
RATE_LIMIT_DELAYS = [60, 120, 240]


# --- IO / body extraction -----------------------------------------------------


def parse_text(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def body_of(raw):
    """Return the reading body: drop the leading `#`-comment provenance header and the
    `=`-run separator line (our English has both; our Latin has the 4-line `#` header and a
    `=` separator too), then the content that follows. Robust to either shape."""
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


def homily_num_of(path):
    m = re.search(r"homily(\d+)", os.path.basename(path))
    return int(m.group(1)) if m else None


def source_path_for(english_file):
    n = homily_num_of(english_file)
    return os.path.join(SOURCE_DIR, f"homily{n:02d}_latin.txt")  # zero-padded


# --- Oracle (Barkley FOTC 83 -> per-homily sections) --------------------------


def _strip_extract_noise(text):
    """Drop any '===== PDF idx N =====' marker line(s); leave everything else (running heads,
    footnotes, page numbers) for the grader to read through."""
    return "\n".join(ln for ln in text.split("\n")
                     if not PDF_IDX_MARKER_RE.match(ln)).strip()


def _pdftotext_range(n):
    """Fallback: extract homily n's page range from the PDF with `pdftotext -f/-l`, caching to
    _source/oracle/oracle_homNN.txt. Returns text or None (with a printed note) if
    the PDF or `pdftotext` is unavailable. FOTC 83 is a single-work volume, so the range simply
    carves the homily out of the Leviticus book."""
    meta = HOMILY_META.get(n)
    if not meta or meta[1] is None:
        return None
    lo, hi = meta[1]
    cache = os.path.join(PDF_CACHE_DIR, f"oracle_hom{n:02d}.txt")
    if os.path.exists(cache) and os.path.getsize(cache) > 0:
        return _strip_extract_noise(parse_text(cache))
    if not os.path.exists(ORACLE_PDF):
        print(f"    Oracle PDF not found: {ORACLE_PDF} -- cannot grade homily {n}.")
        return None
    try:  # pdftotext pages are 1-based; PDF idx is 0-based -> page = idx + 1
        subprocess.run(
            ["pdftotext", "-f", str(lo + 1), "-l", str(hi + 1), ORACLE_PDF, cache],
            check=True, capture_output=True, text=True)
    except FileNotFoundError:
        print("    `pdftotext` not on PATH (install poppler) -- cannot extract oracle.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"    pdftotext failed: {e.stderr.strip()[:160]} -- cannot extract oracle.")
        return None
    if not (os.path.exists(cache) and os.path.getsize(cache) > 0):
        return None
    return _strip_extract_noise(parse_text(cache))


def oracle_text_for(n):
    """Reference text for homily n, in preference order: a hand-split
    `oracle_txt/homilyNN_en.txt`; else the R3 working extract
    `scratchpad/oracle/oracle_homNN.txt`; else a fresh pdftotext extraction of the homily's
    page range. None if unavailable."""
    pre = os.path.join(ORACLE_DIR, f"homily{n:02d}_en.txt")
    if os.path.exists(pre) and os.path.getsize(pre) > 0:
        return _strip_extract_noise(parse_text(pre))
    r3 = os.path.join(R3_EXTRACT_DIR, f"oracle_hom{n:02d}.txt")
    if os.path.exists(r3) and os.path.getsize(r3) > 0:
        return _strip_extract_noise(parse_text(r3))
    return _pdftotext_range(n)


# --- Prompt -------------------------------------------------------------------


def build_prompt(homily_num, lev_ref, latin_text, english_text, oracle_text, reminder=""):
    ref_hint = f" (on {lev_ref})" if lev_ref else ""
    return (
        f"You are GRADING an existing English translation against a published reference "
        f"translation, for SENSE fidelity. The work is {AUTHOR}'s {WORK}, "
        f"{TRANSLATOR_NOTE} -- Origen's Greek homilies on Leviticus survive only in Rufinus's "
        f"Latin (c. 403-405), critical text of W. A. Baehrens, GCS 29 (1920). You are grading "
        f"HOMILY {homily_num}{ref_hint}.\n\n"

        f"THE YARDSTICK IS {REF_AUTHOR.upper()}. His published English ({REF_LABEL}) is the "
        f"reference for meaning; it is pasted below under 'REFERENCE'. He translated the "
        f"SAME Baehrens GCS 29 edition as ours. The REFERENCE is a `pdftotext` extract of "
        f"his book, so it carries mild noise -- page numbers, running heads, FOOTNOTE numbers "
        f"appended inline to words (e.g. 'Days,\"1' or 'else.2') and footnote text (his, not "
        f"the homily body), and words hyphenated across line breaks; read THROUGH such noise "
        f"and judge by sense. The Latin below is context so you can tell a real difference in "
        f"meaning from a mere difference in wording, from his own interpretive freedom, or "
        f"from a place where he follows a different Latin READING than our base does (see "
        f"below); do NOT grade our English directly against the Latin, and do NOT reward or "
        f"penalise closeness to the Latin as such.\n\n"

        "WHAT COUNTS AS A DIVERGENCE. Only a difference in MEANING in OUR English counts:\n"
        "  - OMISSION: a clause/sentence whose sense is in the reference (and in the Latin) "
        "but absent from ours.\n"
        "  - ADDITION: content in ours whose sense is neither in the reference nor the "
        "Latin.\n"
        "  - SHIFTED SENSE: our sentence asserts something materially different (altered "
        "subject/object, flipped negation, different referent, a different allegorical "
        "identification, wrong sense of an ambiguous word).\n"
        "  - SCRIPTURE: a quoted verse whose reference or wording points to a different "
        "passage/sense than the reference's -- UNLESS the difference is that Barkley followed "
        "a variant/Vulgate reading and ours follows the Latin base (not our error; see "
        "below).\n"
        "  - NAME/REFERENT: a name rendered so the person or place referred to differs.\n"
        "  - TRUNCATION: our homily stops materially earlier than the reference.\n\n"

        "WHAT DOES NOT COUNT (never flag these):\n"
        "  - Different word choice, synonyms, sentence length, clause order, register, or "
        "punctuation when the MEANING is the same. Our wording is independently our own and "
        "is EXPECTED to differ from his.\n"
        "  - Our editorial marks: we wrap Scripture Origen quotes in guillemets `» «` and the "
        "Leviticus lemma in asterisks `* *`; he does not. Marks are not meaning.\n"
        "  - Barkley's interpretive freedom or his FOOTNOTES: where he EXPANDS, paraphrases, "
        "or annotates beyond what the Latin says and our English stays closer to the Latin, "
        "that is NOT our omission. Footnote content is his, not the homily -- never treat it "
        "as something we dropped or added. Only flag where OUR English drops or alters the "
        "Latin's actual sense.\n"
        "  - BARKLEY FOLLOWS A DIFFERENT LATIN READING, OR SIMPLY ERRS (important, and "
        "specific to this work). Our English renders Baehrens's constituted MAIN text; "
        "Barkley at a number of spots renders instead a manuscript variant / Delarue "
        "emendation from Baehrens's apparatus, harmonises to the Vulgate/Septuagint, or makes "
        "an English-side slip. Where the Latin below supports OUR reading and Barkley's "
        "English reflects a different underlying word (or is simply mistaken), that is "
        "BARKLEY's choice/error, NOT our divergence -- do NOT flag it. Known instances (all: "
        "ours is correct, do not penalise): Hom III 'Elisha' (Barkley 'Elijah'); Hom III "
        "'sevenfold grace' (Barkley 'seven spirits'); Hom V 'of vow' (Barkley 'of prayer'); "
        "Hom VIII Jer 30:17 'health' (Barkley 'holiness'), 1 Cor 9:9 'oxen' (Barkley "
        "'calves'), Isa 1:6 'bruise'/livor (Barkley 'envy'); Hom IX place 'Soënen'/Syene "
        "(Barkley 'Saba'), and the ark called both 'testimony' and 'covenant' (a GCS-internal "
        "variation the base reproduces exactly); Hom XI Heb 12:9 attributed to JAMES (Barkley "
        "'Paul'), firstborn 'sanctified/consecrated' (Barkley 'sacrificed'); Hom XIV the "
        "Reuben/Judah pairing (Barkley's English is self-contradictory; ours is right); Hom "
        "XV the redemption clause keeps its negation 'could NOT free it' (Barkley drops the "
        "'not'). Similar unlisted cases get the same treatment.\n"
        "  - THE GREEK WORD ἅγιος (Homily XI §2). Our English keeps the Greek word ἅγιος (with "
        "a gloss) where Origen etymologises it; Barkley renders it 'holy'. Same referent -- "
        "not a divergence.\n"
        "  - NAME-FORMS & VERSIFICATION (ignore when the referent/passage is the same): both "
        "he and we use standard English names and give the Old-Latin/LXX numbering Origen "
        "uses (Leviticus itself by LXX chapter, up to a chapter ahead of the Vulgate/MT "
        "across Lev 5-6; Psalms by LXX number; the historical books as the LXX 'Kingdoms'). "
        "Same person/place/passage = not a divergence. This covers e.g. Moses, Aaron, Nadab "
        "and Abihu, the Levites, Melchizedek, Israel, the Israelite woman's son and the "
        "Egyptian father, and the 'scapegoat' / 'goat sent away' (Latin apopompaeus).\n"
        "  - The DOXOLOGY wording is deliberately NOT uniform across the collection and both "
        "he and we render each as printed: most homilies close '...to whom be glory and "
        "dominion unto the ages of ages. Amen' (most inside the quotation marks), but Homily "
        "II reads 'to whom be PRAISE and glory'; Homilies IX and XII drop 'is' ('to whom "
        "glory and dominion'); Homily XIII reads 'To HIM be glory'; Homily XIV reads 'WHO is "
        "glory'; Homily XVI reads 'To Him be glory unto the ETERNAL ages of ages' with no "
        "'dominion'; and the closings vary between 'Amen', 'Amen.', and 'Amen!'. Not our "
        "error.\n"
        "  - HOMILY I HAS NO TITLE. Neither Barkley nor the Latin prints a lemma for Homily I "
        "(the Latin carries an editorial '[Titulus deest]' note, which our English renders as "
        "a bracketed editorial line; Barkley opens directly into the exposition). Its "
        "absence/our note is not an omission or addition.\n"
        "  - CLIPPED OPENINGS/ENDINGS. If the reference seems to begin or end mid-phrase, or "
        "carries a stray running head or the next homily's heading, that is a PDF-extract "
        "artifact, not our doing; judge our opening/close against the Latin, not against a "
        "clipped reference.\n\n"

        "OUTPUT -- STRICT JSON ONLY. Emit a single JSON object and NOTHING else (no prose, "
        "no code fence, no commentary before or after). Schema:\n"
        "{\n"
        '  "score": <integer 0-100, how fully our English matches his sense across the '
        "whole homily; 100 = every point of meaning conveyed, 0 = unrelated>,\n"
        '  "grade": "<letter A+ .. F matching the score>",\n'
        '  "sense_alignment": "<high|moderate|low>",\n'
        '  "divergences": [\n'
        "    {\n"
        '      "locus": "<where, e.g. a short anchor phrase from OUR text>",\n'
        '      "severity": "<minor|moderate|significant>",\n'
        '      "category": "<omission|addition|shifted-sense|scripture|name|truncation>",\n'
        '      "oracle": "<brief: the sense the reference conveys>",\n'
        '      "ours": "<brief: how our English differs in sense>",\n'
        '      "note": "<one line: why it matters / how far the meaning drifts>"\n'
        "    }\n"
        "  ],\n"
        '  "summary": "<1-3 sentences: overall how close we are to the reference, and the '
        "most important divergences, if any>\"\n"
        "}\n"
        "List divergences MOST SEVERE FIRST. If our English conveys his sense throughout, "
        "return an empty \"divergences\" array and a high score -- do NOT invent "
        "differences, and do NOT flag the Barkley-follows-a-variant / Barkley-errs cases "
        "above. Keep every quoted snippet brief (a few words), enough only to identify the "
        "spot.\n"
        f"{reminder}"
        "\n"
        "=== LATIN SOURCE (context only; Rufinus's Latin, Baehrens GCS 29 main text) ===\n"
        f"{latin_text}\n"
        "\n"
        "=== OUR ENGLISH TRANSLATION (the one being graded) ===\n"
        f"{english_text}\n"
        "\n"
        f"=== REFERENCE: {REF_SHORT} (FOTC 83) -- PDF extract, the yardstick ===\n"
        f"{oracle_text}\n"
    )


# --- CLI call -----------------------------------------------------------------


def is_rate_limit_error(stderr):
    lower = stderr.lower()
    return any(term in lower for term in
               ["rate limit", "rate_limit", "overloaded", "too many requests", "529"])


def call_claude(prompt):
    """One CLI call with rate-limit-aware retry/backoff. Returns stdout text. No tools are
    needed (the reference is pasted), so this is a plain text-in/JSON-out call."""
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
            "oracle": str(d.get("oracle", d.get("barkley", d.get("reference", "")))),
            "ours": str(d.get("ours", "")),
            "note": str(d.get("note", "")),
        })
    return {
        "score": score,
        "grade": str(obj.get("grade", "")).strip() or letter_for(score),
        "sense_alignment": str(obj.get("sense_alignment", "")).strip().lower(),
        "divergences": clean_divs,
        "summary": str(obj.get("summary", "")).strip(),
    }


SEV_ORDER = {"significant": 0, "moderate": 1, "minor": 2}


def grade_whole(homily_num, lev_ref, latin_body, english_body, oracle_text, log_base=None):
    """One grading call; parse its JSON, retrying once if the reply is not valid JSON.
    Returns a normalized grade dict, or None if grading could not be parsed."""

    def call(prompt, attempt):
        raw = call_claude(prompt)
        if log_base:
            with open(f"{log_base}.{attempt}.txt", "w", encoding="utf-8") as f:
                f.write(f"# homily={homily_num} attempt={attempt} "
                        f"prompt_chars={len(prompt)}\n\n{raw}\n")
        return raw

    raw = call(build_prompt(homily_num, lev_ref, latin_body, english_body, oracle_text), 1)
    obj = extract_json(raw)
    if obj is None:
        print("    Reply was not valid JSON -- retrying once for a clean object...")
        reminder = ("IMPORTANT: your previous reply could not be parsed. Output ONE JSON "
                    "object and nothing else -- no prose, no code fence.\n")
        raw = call(build_prompt(homily_num, lev_ref, latin_body, english_body,
                                oracle_text, reminder=reminder), 2)
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
    print(f"  GRADE: {grade['grade']:>2}  ({score_str}/100, "
          f"sense {grade['sense_alignment'] or '?'})  ·  "
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


def grade_file(english_file, quiet=False, log_dir=LOG_DIR):
    """Grade one homily against Barkley. Returns a result dict for the batch summary.
    Never writes to the English/Latin files."""
    n = homily_num_of(english_file)
    lev_ref = HOMILY_META.get(n, (None, None))[0]
    source_file = source_path_for(english_file)

    print(f"\n{'=' * 60}")
    print(f"Grade: {os.path.basename(english_file)}"
          + (f"  ({lev_ref})" if lev_ref else ""))
    print(f"  ours:   {english_file}")
    print(f"  latin:  {source_file}")
    print(f"  oracle: {REF_SHORT} FOTC 83 (Leviticus homily {n} section)")
    print(f"{'=' * 60}")

    if not os.path.exists(english_file) or os.path.getsize(english_file) == 0:
        print("  Our English missing or empty -- ungraded.")
        return {"file": english_file, "status": "ungraded", "grade": None}
    if not os.path.exists(source_file):
        print(f"  Latin source not found: {source_file} -- ungraded.")
        return {"file": english_file, "status": "ungraded", "grade": None}

    oracle_text = oracle_text_for(n)
    if not oracle_text:
        print(f"  No oracle section for homily {n} -- ungraded.")
        return {"file": english_file, "status": "ungraded", "grade": None}

    english_body = body_of(parse_text(english_file))
    latin_body = body_of(parse_text(source_file))

    eng_q = english_body.count("»")
    print(f"  Structure -- ours: {len(paragraphs(english_body))} block(s), "
          f"{eng_q} Scripture-quote span(s) | {REF_SHORT} extract: "
          f"{len(oracle_text.split())} words.")

    log_base = None
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        log_base = os.path.join(
            log_dir, os.path.splitext(os.path.basename(english_file))[0])
        print(f"  Transcript log: {log_base}.<attempt>.txt")

    grade = grade_whole(n, lev_ref, latin_body, english_body, oracle_text,
                        log_base=log_base)
    if grade is None:
        print("  Could not obtain a parseable grade -- skipped.")
        return {"file": english_file, "status": "unparseable", "grade": None}

    print_grade(grade, quiet=quiet)
    return {"file": english_file, "status": "graded", "grade": grade}


def order_key(name):
    n = homily_num_of(name)
    return n if n is not None else 999


def collect_files(path):
    if os.path.isdir(path):
        return [os.path.join(path, f)
                for f in sorted(os.listdir(path), key=order_key)
                if FILE_RE.match(f)]
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
              f"({letter_for(int(round(avg)))}) across {len(scores)} graded homily(ies).")
    total_sig = sum(sum(1 for d in r["grade"]["divergences"]
                        if d["severity"] == "significant")
                    for r in graded)
    print(f"  Total significant divergences flagged: {total_sig}.")


def main():
    argv = sys.argv[1:]
    quiet = False
    log_dir = LOG_DIR
    positional = []
    it = iter(argv)
    for a in it:
        if a == "--quiet":
            quiet = True
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
        print("No English files found (expected homily<NN>_english.txt).")
        sys.exit(1)

    print(f"Grading {len(files)} file(s) against {REF_LABEL}"
          + (f". Logs -> {log_dir}" if log_dir else " (logging off)"))
    results, failures = [], []
    for f in files:
        try:
            results.append(grade_file(f, quiet=quiet, log_dir=log_dir))
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

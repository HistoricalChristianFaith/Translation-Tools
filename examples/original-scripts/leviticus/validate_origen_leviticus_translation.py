#!/usr/bin/env python3
"""VALIDATE our English translation of Origen's *Homilies on Leviticus* against OUR OWN
LATIN base -- the constituted GCS 29 reading text -- homily by homily. This is the
Latin-is-the-arbiter sibling of the Exodus validator: it asks the one question the
project's hard rule cares about -- **does our English faithfully and completely render what
the Latin actually says, in the sense Origen's own argument requires?** -- and reports (and
optionally FIXES in place) the spots where it does not.

TWO LAYERS OF CHECK
-------------------
  1. STRUCTURE (deterministic, NO API call, always run first). Compares the Latin and
     English block-by-block and flags the mechanical failure modes of the translation
     step -- a DROPPED section (block-count mismatch), a TRUNCATED section (an English
     block far shorter than its Latin), a block that ends MID-SENTENCE, or a missing
     closing doxology. This is the cheap answer to "did a lot get truncated?": run
     `--structure-only` to see it for the whole corpus without spending a token.
  2. FIDELITY (one LLM call per homily). The Latin base is the sole arbiter, so ANY English
     departure from it is visible -- omissions, additions, sense-shifts, mis-rendered
     Scripture quotations, name/referent errors, and INTERNAL INCONSISTENCIES (e.g. a lemma
     word rendered one way and Origen's own later gloss of that same word rendered the
     opposite way). This is the layer that catches "thin" renderings that are the right
     LENGTH but drop clauses or flatten the argument -- which a length check never sees.

WHAT THE FIDELITY LAYER CHECKS (a finding = a real fidelity defect in OUR English vs Latin)
  - OMISSION: a Latin clause/word whose sense is absent from our English.
  - ADDITION: content in our English whose sense is not in the Latin.
  - MISTRANSLATION / SENSE-SHIFT: wrong sense of a word, flipped negation, altered
    subject/object or referent, a different allegorical identification than the Latin supports.
  - SCRIPTURE: a quoted verse whose English wording misrenders the Latin quotation as printed.
  - NAME/REFERENT: a name rendered so the person/place referred to differs from the Latin's.
  - INCONSISTENCY: the same Latin word/phrase rendered incompatibly in two places, or the
    English contradicting itself where the Latin is coherent.
  - UNTRANSLATED / GARBLED: Latin left untranslated, or an incoherent English stretch.

WHAT IT DOES NOT FLAG (house rules -- the Latin base's own conventions and our settled calls)
  - Independent WORDING/STYLE: synonyms, clause order, sentence length, register, broken-up
    long periods -- when the MEANING matches. Our English is our own; only meaning counts.
  - Our EDITORIAL MARKS: Scripture wrapped in »…«, the lemma in *…*. Marks are not meaning.
  - STANDARD-ENGLISH NAME NORMALIZATION of the Latin's Old-Latin/LXX forms: Istrahel->Israel,
    Moyses->Moses, Aaron->Aaron, Nadab->Nadab, Abiud->Abihu, Melchisedech->Melchizedek,
    Aegyptius->Egyptian, Hierusalem->Jerusalem, etc. Same referent = not a defect.
  - THE GREEK WORD ἅγιος (Homily XI §2), KEPT in Greek with an English gloss and Origen's
    "outside the earth" etymology -- correct, NOT an untranslated defect.
  - THE SCAPEGOAT TERM (Homilies IX-X, Lev 16): the second goat is the »apopompaeus« (the
    one "sent away", Greek ἀποπομπαῖος); keeping the term with a gloss ("the scapegoat")
    is correct, not an addition.
  - THE FOUR EDITOR'S SECLUSIONS/SUPPLEMENTS read in sense without printing the brackets:
    Homily II `[de primis frugibus,]` and `[igni quoque … sunt]`; Homily VI `[qui]`;
    Homily VII `[et]`. Correct handling, not omissions/additions.
  - DELIBERATE FEATURES of the base: the NON-UNIFORM doxologies -- most homilies end »cui
    est gloria et imperium in saecula saeculorum. Amen« and most WRAP the doxology in »…«,
    but Homily II reads »cui LAUS et gloria …«, Homilies IX & XII drop "est" (»cui gloria
    …«), Homily XIII reads »IPSI gloria …«, Homily XIV reads »QUI est gloria …«, and Homily
    XVI reads "Ipsi gloria in AETERNA saecula saeculorum! Amen" with NO "imperium" and NO
    guillemets; the closings vary between "Amen", "Amen.", and "Amen!". All render-as-printed,
    not defects. Homily I has NO lemma and carries a bracketed "[No title is transmitted…]"
    editorial note -- correct, not an addition. Every homily's sections start at 1.
  - SETTLED KEEP DECISIONS (already adjudicated against the Latin -- do NOT re-flag): where
    the base cites Leviticus in LXX chapter/verse numbering (up to a chapter ahead of the
    Vulgate/MT across Lev 5-6), that is correct; Homily XI reads »Iacobus« (James), NOT the
    "Paulus" of some witnesses -- render as James; Homily IX keeps "Soënen" and the ark as
    the "tabernacle/ark of testimony" -- render as the Latin has them. Where OUR English
    renders Baehrens's MAIN text and it differs from a modern Bible/Vulgate or a manuscript
    variant: that is CORRECT here (the Latin is the arbiter), never a defect.

MODES
  * DEFAULT (report AND auto-fix in place): structure table, then per-homily fidelity score,
    grade, and an itemised, severity-ranked finding list, plus a batch summary -- AND it
    applies, in place, every finding that carries a precise, safe edit (ANY category:
    scripture, mistranslation, sense-shift, omission, name, addition, …). A fix is applied
    only when it is safe: its `old` string is copied verbatim from our English and occurs
    EXACTLY once, and after the replacement the guillemets stay balanced and the paragraph/
    block count is unchanged. Findings with no concrete edit (they need rephrasing or are a
    judgement call) are reported but left for you. The English files are git-tracked --
    REVIEW THE DIFF (`git diff`) and revert any edit you disagree with.
  * --report-only (a.k.a. --dry-run): report exactly as above but WRITE NOTHING -- no file
    is touched. Use when you only want to see the findings.
  * --structure-only: run ONLY the deterministic structure/truncation check (no API calls,
    no tokens). Fast triage for "what got dropped or truncated?".

    python3 validate_origen_leviticus_translation.py                        # report + auto-fix all
    python3 validate_origen_leviticus_translation.py homily09_english.txt   # report + auto-fix one
    python3 validate_origen_leviticus_translation.py --report-only          # report only, no edits
    python3 validate_origen_leviticus_translation.py --structure-only       # cheap truncation triage
    python3 validate_origen_leviticus_translation.py --quiet                # grade lines only

    --report-only    report but DO NOT edit any file (alias: --dry-run)
    --structure-only run only the deterministic structure/truncation check (no API calls)
    --quiet          print each homily's score line but not its finding list
    --log-dir DIR    where to write per-call transcripts (default: ./validation_logs_leviticus)
    --no-log         do not write transcripts

The Latin base is NEVER modified. Only `english/homilyNN_english.txt` is read, and (unless
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
    "Origen of Alexandria/Homilies on Leviticus"
)
SOURCE_DIR = os.path.join(BASE, "LATIN")            # our Latin base -- the ARBITER
TARGET_DIR = os.path.join(BASE, "english")          # our English (the thing being validated)

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "validation_logs_leviticus")

AUTHOR = "Origen of Alexandria"
WORK = "Homilies on Leviticus (Homiliae in Leviticum)"
TRANSLATOR_NOTE = "in the Latin translation of Rufinus of Aquileia"

# Per-homily Leviticus coverage (verified R5/consistency passage table), for the score line.
HOMILY_META = {
    1:  "Lev. 1 (prologue; the whole burnt offering)",
    2:  "Lev. 4 (the sin offerings; peace offerings)",
    3:  "Lev. 5 (oaths; the unclean; the guilt offering)",
    4:  "Lev. 6 LXX / MT 5:20–26 (trespass offering; restitution)",
    5:  "Lev. 6:24 ff. (the law of the sin offering)",
    6:  "Lev. 8 (consecration; priestly vestments)",
    7:  "Lev. 10–11 (wine forbidden; clean & unclean animals)",
    8:  "Lev. 12–14 (childbirth; leprosy & purifications)",
    9:  "Lev. 16 (Day of Atonement; the two goats)",
    10: "Lev. 16 cont. (the fast; the scapegoat)",
    11: "Lev. 19–20 (»be holy, for I am holy«)",
    12: "Lev. 21 (the great high priest)",
    13: "Lev. 23–24 (the feasts; the lamp; the shewbread)",
    14: "Lev. 24:10–23 (the blasphemer)",
    15: "Lev. 25 (the Jubilee; sale & redemption of houses)",
    16: "Lev. 26 (the blessings — and curses)",
}

# Homily I carries no lemma (a bracketed editorial note stands in its place); every other
# homily carries exactly one *…* lemma. Used by the structure check to compute the expected
# English block count (1 heading + [1 titulus note for Hom I] + lemma? + numbered sections).
NO_LEMMA_HOMILIES = {1}

FILE_RE = re.compile(r"^homily\d+_english\.txt$")
SEP_RE = re.compile(r"^=+$")

RETRY_DELAYS = [5, 15, 45]
RATE_LIMIT_DELAYS = [60, 120, 240]

# Structure-check thresholds.
SHORT_BLOCK_RATIO = 0.70   # an English block below this * its Latin length is a truncation suspect
SHORT_MIN_LATIN = 200      # ...but only worry about blocks whose Latin is at least this long
                           # (tiny lemma/heading lines swing wildly and are not truncation)


# --- IO / body extraction -----------------------------------------------------


def parse_text(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def body_of(raw):
    """Return the reading body: drop the leading `#`-comment provenance header and the
    `=`-run separator line (both our English and our Latin carry these), then the content
    that follows."""
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


# --- Latin-body parsing (for the deterministic structure check) ---------------

HEADING_LINE_RE = re.compile(r"^(\[?)HOMILIA\s+([IVXLCDM]+)\.(\]?)[ \t]*(?:\n|$)")
TITULUS_RE = re.compile(r"^\[Titulus deest\b")


def latin_blocks(latin_raw):
    """The Latin translatable blocks, mirroring the translation script's parser: strip the
    front matter and the `HOMILIA` heading, hold aside Homily I's titulus note, then
    (lemma? + numbered sections). Returns (has_lemma, [blocks])."""
    body = body_of(latin_raw)
    m = HEADING_LINE_RE.match(body)
    if m:
        body = body[m.end():].lstrip("\n")
    first_line, _, rest = body.partition("\n")
    first_line = first_line.strip()
    has_lemma = not TITULUS_RE.match(first_line)
    sections = paragraphs(rest)
    blocks = ([first_line] if has_lemma else []) + sections
    return has_lemma, [b for b in blocks if b]


def english_content_blocks(english_raw, n):
    """The English blocks that align 1:1 with the Latin blocks: drop the leading `HOMILY
    <ROMAN>.` heading block and (for Homily I) the bracketed titulus-note block."""
    blocks = paragraphs(body_of(english_raw))
    lead = 1 + (1 if n in NO_LEMMA_HOMILIES else 0)
    return blocks, blocks[lead:]


# --- Deterministic structure / truncation check -------------------------------


def structure_report(english_file):
    """Compare Latin vs English block-by-block with no API call. Returns a dict with the
    block counts, per-block ratios, and a list of mechanical issues (dropped/truncated/
    mid-sentence/doxology). This is the cheap 'what got truncated?' triage."""
    n = homily_num_of(english_file)
    source_file = source_path_for(english_file)
    if not (os.path.exists(english_file) and os.path.getsize(english_file) > 0):
        return {"n": n, "status": "missing-english", "issues": ["English file missing or empty"]}
    if not os.path.exists(source_file):
        return {"n": n, "status": "missing-latin", "issues": ["Latin source not found"]}

    lraw, eraw = parse_text(source_file), parse_text(english_file)
    has_lemma, lblocks = latin_blocks(lraw)
    eall, econtent = english_content_blocks(eraw, n)

    expected_e = 1 + (1 if n in NO_LEMMA_HOMILIES else 0) + len(lblocks)
    issues = []
    if len(eall) != expected_e:
        issues.append(f"BLOCK COUNT {len(eall)} vs expected {expected_e} "
                      f"(latin blocks={len(lblocks)}) -- a section may be dropped, split, or merged")

    # per-block length ratios (only meaningful where the two align 1:1)
    ratios = []
    pairs = min(len(lblocks), len(econtent))
    for i in range(pairs):
        lb, eb = lblocks[i], econtent[i]
        r = len(eb) / len(lb) if lb else 9.0
        ratios.append(r)
        if len(lb) >= SHORT_MIN_LATIN and r < SHORT_BLOCK_RATIO:
            issues.append(f"block #{i}: English {len(eb)}c is {r:.2f}x its Latin {len(lb)}c "
                          f"-- possible truncation")
        # mid-sentence cutoff: a real block should end with terminal punctuation, allowing
        # trailing closing marks -- the Scripture-close guillemet «, the lemma asterisk *,
        # quotes, or a paren/bracket.
        if len(lb) >= SHORT_MIN_LATIN and not re.search(r"[.!?…][»«*'\"”’)\]]*\s*$", eb):
            issues.append(f"block #{i}: ends mid-sentence -> …{eb[-45:]!r}")

    # closing doxology present?
    last = econtent[-1] if econtent else ""
    if "Amen" not in last[-60:]:
        issues.append("last block does not end in the doxology ('Amen') -- may be cut off")

    return {
        "n": n, "status": "ok",
        "latin_blocks": len(lblocks), "english_blocks": len(eall),
        "expected_english": expected_e, "ratios": ratios,
        "min_ratio": min(ratios) if ratios else None,
        "issues": issues,
    }


def print_structure(rep):
    n = rep["n"]
    ref = HOMILY_META.get(n, "")
    head = f"  H{n:02d} ({ref})" if ref else f"  H{n:02d}"
    if rep["status"] != "ok":
        print(f"{head}: {rep['status'].upper()} -- {'; '.join(rep['issues'])}")
        return bool(rep["issues"])
    mr = rep["min_ratio"]
    mr_s = f"{mr:.2f}" if mr is not None else "--"
    flag = "OK" if not rep["issues"] else f"{len(rep['issues'])} ISSUE(S)"
    print(f"{head}: latin {rep['latin_blocks']} blk / english {rep['english_blocks']} blk "
          f"(exp {rep['expected_english']}), min block ratio {mr_s}  ->  {flag}")
    for iss in rep["issues"]:
        print(f"        - {iss}")
    return bool(rep["issues"])


# --- Prompt -------------------------------------------------------------------


def build_prompt(homily_num, lev_ref, latin_text, english_text, reminder=""):
    ref_hint = f" (on {lev_ref})" if lev_ref else ""
    return (
        f"You are VALIDATING an English translation against its LATIN SOURCE for fidelity. "
        f"The work is {AUTHOR}'s {WORK}, {TRANSLATOR_NOTE} -- Origen's Greek homilies on "
        f"Leviticus survive only in Rufinus's Latin (c. 403-405), constituted reading text of "
        f"W. A. Baehrens, GCS 29 (1920). You are checking HOMILY {homily_num}{ref_hint}.\n\n"

        "THE LATIN IS THE SOLE ARBITER. The single question is: does the ENGLISH faithfully "
        "and COMPLETELY render what the LATIN says, in the sense Origen's own argument "
        "requires? Read the whole homily so you can catch internal inconsistencies (e.g. the "
        "same Latin word rendered incompatibly in a lemma and in Origen's later gloss of it). "
        "Do NOT use any outside Bible or translation; judge ONLY English-against-Latin.\n\n"

        "WHAT COUNTS AS A FINDING (a real fidelity defect in the ENGLISH):\n"
        "  - OMISSION: a Latin clause/word whose sense is absent from the English.\n"
        "  - ADDITION: content in the English whose sense is not in the Latin.\n"
        "  - MISTRANSLATION / SENSE-SHIFT: wrong sense of a word, flipped negation, altered "
        "subject/object or referent, an allegorical identification the Latin does not support.\n"
        "  - SCRIPTURE: a quoted verse whose English wording misrenders the Latin quotation as "
        "printed (the Latin quotation is the arbiter -- NOT any modern Bible).\n"
        "  - NAME/REFERENT: a name rendered so the person/place referred to differs from the "
        "Latin's.\n"
        "  - INCONSISTENCY: the same Latin word/phrase rendered incompatibly in two places, or "
        "the English contradicting itself where the Latin is coherent.\n"
        "  - UNTRANSLATED / GARBLED: Latin left untranslated, or an incoherent English "
        "stretch.\n\n"

        "WHAT DOES NOT COUNT (never flag these -- they are correct by the base's own rules):\n"
        "  - Independent WORDING/STYLE: synonyms, clause order, sentence length, register, "
        "broken-up long periods -- when the MEANING matches. The English wording is its own; "
        "only meaning counts. Do not rewrite for taste.\n"
        "  - Our EDITORIAL MARKS: Scripture in »…«, the lemma in *…*. Marks are not meaning; "
        "never flag their presence.\n"
        "  - STANDARD-ENGLISH NAME NORMALIZATION of the Latin's Old-Latin/LXX forms "
        "(Istrahel->Israel, Moyses->Moses, Aaron->Aaron, Nadab->Nadab, Abiud->Abihu, "
        "Melchisedech->Melchizedek, Aegyptius->Egyptian, Hierusalem->Jerusalem, etc.). Same "
        "referent = not a defect.\n"
        "  - THE GREEK WORD ἅγιος (Homily XI §2), KEPT in Greek with an English gloss and "
        "Origen's 'outside the earth' etymology -- CORRECT, not an untranslated defect.\n"
        "  - THE SCAPEGOAT TERM (Homilies IX-X, Lev 16): the second goat is the "
        "»apopompaeus« / »sors apopompaei« (the one 'sent away', Greek ἀποπομπαῖος); keeping "
        "the term with a gloss ('the scapegoat', 'the one sent away') is CORRECT, not an "
        "addition.\n"
        "  - THE FOUR EDITOR'S SECLUSIONS/SUPPLEMENTS read in sense WITHOUT printing the "
        "brackets: Homily II `[de primis frugibus,]` and `[igni quoque … sunt]`; Homily VI "
        "`[qui]`; Homily VII `[et]`. Rendering the words naturally is correct, not an "
        "omission/addition.\n"
        "  - DELIBERATE FEATURES of the base: the NON-UNIFORM doxologies -- most end »cui est "
        "gloria et imperium in saecula saeculorum. Amen« (most WRAPPED in »…«), but Homily II "
        "reads »cui LAUS et gloria …«; Homilies IX & XII drop 'est' (»cui gloria …«); Homily "
        "XIII reads »IPSI gloria …«; Homily XIV reads »QUI est gloria …«; Homily XVI reads "
        "'Ipsi gloria in AETERNA saecula saeculorum! Amen' with NO 'imperium' and NO "
        "guillemets; closings vary between 'Amen', 'Amen.', 'Amen!'. Render-as-printed, not "
        "defects. Homily I has NO lemma and carries a bracketed '[No title is transmitted…]' "
        "editorial note -- correct, not an addition. Every homily's sections start at 1.\n"
        "  - SETTLED KEEP DECISIONS (already adjudicated against the Latin -- do NOT re-flag): "
        "Leviticus is cited in LXX chapter/verse numbering (up to a chapter ahead of the "
        "Vulgate/MT across Lev 5-6) -- correct; Homily XI reads »Iacobus« (James), NOT the "
        "'Paulus' of some witnesses -- render as James; Homily IX keeps 'Soënen' and the "
        "'tabernacle/ark of testimony' -- render as the Latin has them.\n"
        "  - Where the English renders Baehrens's MAIN text and it happens to differ from a "
        "modern Bible/Vulgate or a manuscript variant: that is CORRECT (the Latin is the "
        "arbiter), never a defect.\n\n"

        "For each genuine finding, when (and ONLY when) a precise, minimal, SAFE correction "
        "exists, include a `fix` object with:\n"
        "  - `old`: a VERBATIM substring copied EXACTLY from OUR ENGLISH (include enough "
        "surrounding words that it occurs EXACTLY ONCE in the English; keep any »…« / *…* "
        "marks intact inside it),\n"
        "  - `new`: the corrected English (same marks preserved; change only what the fidelity "
        "defect requires; keep the surrounding words identical).\n"
        "Make `new` internally consistent with the rest of the homily. If no safe minimal edit "
        "is possible (the fix would need rephrasing across a whole sentence, or it is a "
        "judgement call), OMIT the `fix` object and just describe the finding.\n\n"

        "OUTPUT -- STRICT JSON ONLY. Emit a single JSON object and NOTHING else (no prose, no "
        "code fence). Schema:\n"
        "{\n"
        '  "score": <integer 0-100: how faithfully & completely our English renders the Latin; '
        "100 = every point of the Latin's meaning conveyed with none added, 0 = unrelated>,\n"
        '  "grade": "<letter A+ .. F matching the score>",\n'
        '  "fidelity": "<high|moderate|low>",\n'
        '  "findings": [\n'
        "    {\n"
        '      "locus": "<short anchor phrase from OUR English>",\n'
        '      "severity": "<minor|moderate|significant>",\n'
        '      "category": "<omission|addition|mistranslation|sense-shift|scripture|name|'
        'inconsistency|untranslated>",\n'
        '      "latin": "<the Latin phrase at issue>",\n'
        '      "ours": "<how our English renders it>",\n'
        '      "issue": "<one line: what is wrong / how the meaning drifts from the Latin>",\n'
        '      "fix": { "old": "<verbatim unique English substring>", "new": "<corrected>" }\n'
        "    }\n"
        "  ],\n"
        '  "summary": "<1-3 sentences: overall fidelity to the Latin, and the most important '
        "findings if any>\"\n"
        "}\n"
        "List findings MOST SEVERE FIRST. If our English faithfully renders the Latin "
        "throughout, return an empty \"findings\" array and a high score -- do NOT invent "
        "defects, and do NOT flag any of the house-rule items above. The `fix` field is "
        "OPTIONAL per finding; include it only for a safe minimal edit. Keep quoted snippets "
        "brief.\n"
        f"{reminder}"
        "\n"
        "=== LATIN SOURCE (the arbiter; Rufinus's Latin, Baehrens GCS 29 main text) ===\n"
        f"{latin_text}\n"
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
            "latin": str(d.get("latin", "")),
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


def validate_whole(homily_num, lev_ref, latin_body, english_body, log_base=None):
    """One validation call; parse its JSON, retrying once if the reply is not valid JSON.
    Returns a normalized result dict, or None if it could not be parsed."""

    def call(prompt, attempt):
        raw = call_claude(prompt)
        if log_base:
            with open(f"{log_base}.{attempt}.txt", "w", encoding="utf-8") as f:
                f.write(f"# homily={homily_num} attempt={attempt} "
                        f"prompt_chars={len(prompt)}\n\n{raw}\n")
        return raw

    raw = call(build_prompt(homily_num, lev_ref, latin_body, english_body), 1)
    obj = extract_json(raw)
    if obj is None:
        print("    Reply was not valid JSON -- retrying once for a clean object...")
        reminder = ("IMPORTANT: your previous reply could not be parsed. Output ONE JSON "
                    "object and nothing else -- no prose, no code fence.\n")
        raw = call(build_prompt(homily_num, lev_ref, latin_body, english_body,
                                reminder=reminder), 2)
        obj = extract_json(raw)
    if obj is None:
        return None
    return normalize(obj)


# --- Fix application (--fix) ---------------------------------------------------


def guillemets_balanced(text):
    return text.count("»") == text.count("«")


def apply_fixes(english_file, findings):
    """Apply EVERY safe, validated fix to the English file in place, of any category. A fix
    is applied only if: it carries `old`/`new`; `old` occurs EXACTLY once in the file; and
    after replacement the guillemets stay balanced and the paragraph/block count is
    unchanged. Findings with no concrete edit are reported as skipped so they stay visible.
    Returns (applied, skipped) as lists of (finding, reason)."""
    raw = parse_text(english_file)
    body0 = body_of(raw)
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
        cbody = body_of(candidate)
        if not guillemets_balanced(cbody):
            skipped.append((f, "would unbalance guillemets »«"))
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
        if d["latin"]:
            print(f"         Latin: {d['latin'][:150]}")
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
    """Validate one homily's English against its Latin. Returns a result dict for the batch
    summary. Reads the Latin (never modifies it); edits the English in place with every safe
    fix unless do_fix is False (--report-only)."""
    n = homily_num_of(english_file)
    lev_ref = HOMILY_META.get(n)
    source_file = source_path_for(english_file)

    print(f"\n{'=' * 60}")
    print(f"Validate: {os.path.basename(english_file)}"
          + (f"  ({lev_ref})" if lev_ref else ""))
    print(f"  ours:  {english_file}")
    print(f"  latin: {source_file}  (the arbiter)")
    print(f"{'=' * 60}")

    if not os.path.exists(english_file) or os.path.getsize(english_file) == 0:
        print("  Our English missing or empty -- unvalidated.")
        return {"file": english_file, "status": "unvalidated", "result": None}
    if not os.path.exists(source_file):
        print(f"  Latin source not found: {source_file} -- unvalidated.")
        return {"file": english_file, "status": "unvalidated", "result": None}

    # Deterministic structure/truncation check first (free).
    rep = structure_report(english_file)
    print_structure(rep)

    english_body = body_of(parse_text(english_file))
    latin_body = body_of(parse_text(source_file))

    log_base = None
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        log_base = os.path.join(
            log_dir, os.path.splitext(os.path.basename(english_file))[0])
        print(f"  Transcript log: {log_base}.<attempt>.txt")

    result = validate_whole(n, lev_ref, latin_body, english_body, log_base=log_base)
    if result is None:
        print("  Could not obtain a parseable result -- skipped.")
        return {"file": english_file, "status": "unparseable", "result": None,
                "structure": rep}

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
            # re-report structure so the user sees the file stayed well-formed
            nb = parse_text(english_file)
            print(f"  Post-fix: guillemets {'balanced' if guillemets_balanced(body_of(nb)) else 'UNBALANCED!'}"
                  f", {len(paragraphs(body_of(nb)))} block(s). Review with `git diff`.")

    return {"file": english_file, "status": "validated", "result": result, "structure": rep}


def order_key(name):
    n = homily_num_of(name)
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
    print("Arbiter: our GCS 29 Latin base. Flags dropped/truncated/mid-sentence blocks.\n")
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
        print("  Some files have structural issues (see above) -- inspect those first.")
    else:
        print("  No dropped or truncated blocks detected: every homily has its full block "
              "count, full-length blocks, and an intact closing doxology.")
    return 0 if not any_issue else 1


def print_summary(results, did_fix):
    print(f"\n{'=' * 60}\nVALIDATION SUMMARY (arbiter: our GCS 29 Latin base)\n{'=' * 60}")
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
        print(f"\n  Mean Latin-fidelity score: {avg:.1f}/100 "
              f"({letter_for(int(round(avg)))}) across {len(scores)} homily(ies).")
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
    quiet = structure_only = report_only = False
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
            report_only = True
            do_fix = False
        elif a in ("--fix", "--fix-names", "--fix-all"):
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
        print("No English files found (expected homily<NN>_english.txt).")
        sys.exit(1)

    if structure_only:
        sys.exit(run_structure_only(files))

    mode = "REPORT + AUTO-FIX every safe edit in place" if do_fix else "report only (no edits)"
    print(f"Validating {len(files)} file(s) against our GCS 29 Latin base [{mode}]"
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

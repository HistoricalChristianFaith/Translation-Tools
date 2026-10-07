"""html_config.py: how /format-as-html renders %%AUTHOR%%, *%%WORK%%* (drafted %%DATE%%).

Drafted by draft_config.py; every `# GUESS` line must be confirmed (or fixed) before the first
build, and every MARKS value set. Re-running the build after a translation fix needs no edits here.
Helpers (verse_heading, book_heading, label_heading, verse_coverage) come from the skill's htmlkit.py.
"""
from htmlkit import verse_heading, book_heading, label_heading, verse_coverage  # noqa: F401

# --- where (chosen in the location interview) ---
SRC_GLOB = "english/*_english.txt"
OUTPUT = %%OUTPUT%%

# --- title, note, rights ---
H1 = %%H1%%
# Shown in <i>…</i><br><br> at the top. Inline HTML allowed (e.g. <i>series title</i>).
# Placeholders: {pages} / {cols} = the manifest page range ("pp. 349–374").
%%NOTE_FACTS%%
SOURCE_NOTE = (
    %%SOURCE_NOTE%%
)
RELEASE = None              # "public-domain" appends: "This English translation is released into the public domain."
RIGHTS_CONFIRMED = False    # must be True to use RELEASE with a copyright base (base_license: %%LICENSE%%)

# --- structure ---
DROP_FIRST_BLOCK = %%DROP_FIRST_BLOCK%%
CHECK_LABEL = %%CHECK_LABEL%%
UNIT_HEADINGS = %%UNIT_HEADINGS%%
BLOCK_LABELS = None         # {"regex": r"^\(Chapter (\d+) — …\)", "heading": fn(match, ctx) -> (level, text), "split_runon": r"…"}
STRIP_PREFIX = %%STRIP_PREFIX%%
KEEP_PREFIX = []            # [(unit_n, block_index), …] where a stripped prefix is kept

# --- marks: every key the census found must have a mode ---
# modes: "italic" (Scripture, lemmata: house rule), "quote" (straight "…", nested '…'),
#        "straight" (typographic quotes -> straight), "strip" (drop the marks, keep the words), "pass"
MARKS = {
%%MARKS%%
}
APOSTROPHE = "'"

# --- notes, coverage, exceptions ---
FOOTNOTES = None            # {"regex": r"\[(?:another reading|so the edition)[^\]]*\]", "style": fn}
COVERAGE = %%COVERAGE%%
EXCEPTIONS = {}

LAST_BUILD = None   # written by build_html.py --write

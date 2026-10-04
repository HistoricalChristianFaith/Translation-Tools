#!/usr/bin/env python3
"""Measure the ORCHESTRATOR's context usage from its own Claude Code session transcript.

The session is pinned, never guessed: `--transcript`, else `--session-id`, else the
`CLAUDE_CODE_SESSION_ID` environment variable that Claude Code exports to every Bash command.
The transcript is ~/.claude/projects/<project>/<session-id>.jsonl, matched by file name. (Picking
"the newest transcript" is wrong: other sessions write there too, and subagent transcripts sit
next to it.)

The measure is exact: the token usage of the last main-chain assistant turn (input + cache read
+ cache creation = the whole context of that API call, system prompt and tools included). After
a compaction the next call is simply smaller. Transcripts with no usage fall back to a rough
chars / 3.5 estimate over the messages since the last compaction.

    context_check.py [--work-dir D] [--threshold K] [--transcript PATH | --session-id ID]
        # threshold in k tokens: --threshold, else state.json `context_threshold_k` when
        # --work-dir is given, else 400
    prints: context ~<N>k tokens / <T>k (<file>, <how>): OK|PAUSE
    exit 0 = OK, 2 = PAUSE, 1 = can't tell (no session id, transcript missing / stale /
             unparsable; the orchestrator continues)
"""

import argparse
import glob
import json
import os
import sys
import time

PROJECTS = os.path.expanduser("~/.claude/projects")
SESSION_ENV = "CLAUDE_CODE_SESSION_ID"
CHARS_PER_TOKEN = 3.5
DEFAULT_K = 400
STALE_SECONDS = 300  # the live session writes its transcript every turn


def fail(msg):
    print(f"context_check: {msg} (continue without the check)")
    sys.exit(1)


def find_transcript(args):
    if args.transcript:
        return args.transcript if os.path.isfile(args.transcript) else None
    sid = args.session_id or os.environ.get(SESSION_ENV)
    if not sid:
        fail(f"no session id (pass --session-id; ${SESSION_ENV} is not set)")
    hits = glob.glob(os.path.join(PROJECTS, "*", sid + ".jsonl"))
    if len(hits) > 1:
        fail(f"{len(hits)} transcripts named {sid}.jsonl")
    return hits[0] if hits else None


def threshold_k(args):
    if args.threshold is not None:
        return args.threshold
    if args.work_dir:
        try:
            with open(os.path.join(args.work_dir, "_source", "run", "state.json")) as f:
                v = json.load(f).get("context_threshold_k")
            if v:
                return float(v)
        except (OSError, ValueError, TypeError):
            pass
    return DEFAULT_K


def is_compact_boundary(e):
    return bool(e.get("isCompactSummary")) or (
        e.get("type") == "system" and "compact" in str(e.get("subtype", "")))


def estimate(path):
    """Return (tokens, how): exact from the last usage record, else the chars heuristic."""
    entries = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except ValueError:
                continue  # a partial last line while the session is writing
    if not entries:
        raise ValueError("no JSON entries")

    for e in reversed(entries):
        msg = e.get("message")
        if e.get("type") == "assistant" and not e.get("isSidechain") and isinstance(msg, dict):
            u = msg.get("usage")
            if isinstance(u, dict):
                tokens = sum(int(u.get(k) or 0) for k in
                             ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
                if tokens:
                    return tokens, "usage"

    start = 0
    for i, e in enumerate(entries):
        if is_compact_boundary(e):
            start = i  # a compact summary entry is itself part of the new context
    chars = 0
    for e in entries[start:]:
        if e.get("type") in ("user", "assistant") and not e.get("isSidechain"):
            msg = e.get("message")
            if isinstance(msg, dict):
                chars += len(json.dumps(msg.get("content", ""), ensure_ascii=False))
    return chars / CHARS_PER_TOKEN, "estimate"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work-dir")
    ap.add_argument("--threshold", type=float, help="k tokens (default 400)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--transcript")
    g.add_argument("--session-id")
    args = ap.parse_args()

    path = find_transcript(args)
    if not path:
        fail("this session's transcript was not found under ~/.claude/projects")
    age = time.time() - os.path.getmtime(path)
    if not args.transcript and age > STALE_SECONDS:
        fail(f"{os.path.basename(path)} not written for {age:.0f}s: stale session id?")
    try:
        tokens, how = estimate(path)
    except (OSError, ValueError) as ex:
        fail(f"can't parse {path}: {ex}")
    k = threshold_k(args)
    verdict = "PAUSE" if tokens >= k * 1000 else "OK"
    print(f"context ~{tokens / 1000:.0f}k tokens / {k:g}k ({os.path.basename(path)}, {how}): {verdict}")
    sys.exit(2 if verdict == "PAUSE" else 0)


if __name__ == "__main__":
    main()

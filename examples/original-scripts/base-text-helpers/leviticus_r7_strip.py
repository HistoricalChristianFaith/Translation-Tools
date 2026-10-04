#!/usr/bin/env python3
"""Pass R7 — deterministic page-anchor strip for passB_final/homilyNN.txt.
Removes every inline [GCS p.N] anchor and nothing else:
  A) line-start anchors followed by a single space (the 22 section openers
     '[GCS p.N] K. ...'): drop the anchor AND its one trailing space so the
     line begins cleanly at the section number (no orphaned leading space).
  B) all remaining anchors (mid-word WORD|WORD, mid-line SPACE|WORD, and the
     single line-start-no-space START|WORD '[GCS p.465]6.'): plain token
     deletion, which rejoins words / preserves the single separating space.
Self-checks after strip: no '[GCS p.' left; no double space, no leading or
trailing line-space introduced (baseline for all three was zero).
"""
import re, glob, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.normpath(os.path.join(HERE, '..', 'passB_final'))
ANCHOR = re.compile(r'\[GCS p\.\d+\]')
LINE_START_SP = re.compile(r'(?m)^\[GCS p\.\d+\] ')

rc = 0
grand = 0
for fp in sorted(glob.glob(os.path.join(FINAL, 'homily*.txt'))):
    orig = open(fp, encoding='utf-8').read()
    n_before = len(ANCHOR.findall(orig))
    # baseline anomaly counts (expect 0 across the board)
    base_dbl = orig.count('  ')
    base_lead = len(re.findall(r'\n[ \t]', orig)) + (1 if orig[:1] in (' ', '\t') else 0)
    base_trail = len(re.findall(r'[ \t]\n', orig)) + (1 if orig[-1:] in (' ', '\t') else 0)

    n_A = len(LINE_START_SP.findall(orig))
    txt = LINE_START_SP.sub('', orig)          # step A
    txt = ANCHOR.sub('', txt)                   # step B

    left = ANCHOR.findall(txt)
    dbl = txt.count('  ')
    lead = len(re.findall(r'\n[ \t]', txt)) + (1 if txt[:1] in (' ', '\t') else 0)
    trail = len(re.findall(r'[ \t]\n', txt)) + (1 if txt[-1:] in (' ', '\t') else 0)

    ok = (not left) and dbl == base_dbl and lead == base_lead and trail == base_trail
    base = os.path.basename(fp)
    print(f'{base}: anchors {n_before} (A={n_A} B={n_before-n_A}) removed; '
          f'left={len(left)} dbl={dbl}(base {base_dbl}) lead={lead}(base {base_lead}) '
          f'trail={trail}(base {base_trail}) -> {"OK" if ok else "ANOMALY"}')
    if not ok:
        rc = 1
        if left: print('   remaining anchors:', left[:5])
        continue
    grand += n_before
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(txt)

print(f'\nTOTAL anchors removed = {grand}')
sys.exit(rc)

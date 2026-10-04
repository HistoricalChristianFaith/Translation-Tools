#!/usr/bin/env python3
"""Assemble final LATIN/homilyNN_latin.txt = scaffold header (4 # lines + ==== rule +
HOMILIA N. + *lemma*/[Titulus] line) + the reconciled body from _source/passB_final/homilyNN.txt.
Guarantees LATIN running text == passB_final (byte-identical body), correct image-verified header.
Run only after the Pass B workflow has written all 16 passB_final files.
"""
import os, glob, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.normpath(os.path.join(HERE, '..', '..'))
LATIN = os.path.join(PROJ, 'LATIN')
FINAL = os.path.normpath(os.path.join(HERE, '..', 'passB_final'))

def header_of(scaffold_path):
    """Everything before the first [GCS p. anchor = the 4 # lines, rule, HOMILIA line, lemma line."""
    lines = open(scaffold_path, encoding='utf-8').read().splitlines()
    out = []
    for l in lines:
        if l.lstrip().startswith('[GCS p.'):
            break
        out.append(l)
    # trim trailing blank lines of the header
    while out and out[-1].strip() == '':
        out.pop()
    return '\n'.join(out)

def main():
    missing = []
    for n in range(1, 17):
        pad = f'{n:02d}'
        scaffold = os.path.join(LATIN, f'homily{pad}_latin.txt')
        finalf = os.path.join(FINAL, f'homily{pad}.txt')
        if not os.path.exists(finalf):
            missing.append(pad); continue
        header = header_of(scaffold)
        body = open(finalf, encoding='utf-8').read().strip('\n')
        text = header + '\n' + body + '\n'
        with open(scaffold, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'homily{pad}: header {len(header.splitlines())} lines + body {len(body.splitlines())} lines -> written')
    if missing:
        print('MISSING passB_final for:', missing); return 1
    print('all 16 assembled')
    return 0

if __name__ == '__main__':
    sys.exit(main())

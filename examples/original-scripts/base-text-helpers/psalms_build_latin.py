#!/usr/bin/env python3
"""Assemble LATIN/homilyNN_latin.txt = header + ==== rule + HOMILIA line + *lemma* + body,
pulling the body verbatim from _source/passB_final/homilyNN.txt (disk->disk; no re-typed Latin).
Config per homily below; run with the homily key as argv[1]."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
FINAL = os.path.join(ROOT, '_source', 'passB_final')
LATIN = os.path.join(ROOT, 'LATIN')
RULE = '=' * 60
COMMON2 = "# Origen's Greek homily, surviving only in Rufinus of Aquileia's Latin translation (c. 401)."
COMMON4 = "# Scripture is quoted in Old-Latin / LXX wording (Rufinus renders Origen's lemmata, not the Vulgate)."

CFG = {
 '09': dict(
   topic="# Origen, Homilies on Psalms 36–38 — Ps 38, Homily II (»Verumtamen in imagine pertransit homo«: man walks in an image; the earthly and heavenly image). Lemma as printed by Migne.",
   cols="cols 1400–1410",
   heading="HOMILIA II.",
   lemma="*De eodem psalmo, ab illa parte: »Verumtamen in imagine pertransit homo«.*",
   fname="homily09_latin.txt", body="homily09.txt"),
 '07': dict(
   topic="# Origen, Homilies on Psalms 36–38 — Ps 37, Homily II (»Amici mei et proximi mei«: confession, penitence, and the friends who stood aloof). Lemma as printed by Migne.",
   cols="cols 1380–1388",
   heading="HOMILIA II.",
   lemma="*De eodem psalmo, ab illa parte: »Amici mei et proximi mei«.*",
   fname="homily07_latin.txt", body="homily07.txt"),
}

def build(key):
    c = CFG[key]
    body = open(os.path.join(FINAL, c['body']), encoding='utf-8').read().rstrip('\n')
    src = f"# Source text: Migne, Patrologia Graeca 12, {c['cols']} (Rufinus's Latin, In Psalmos)."
    out = '\n'.join([c['topic'], COMMON2, src, COMMON4, RULE, c['heading'], c['lemma'], '', body]) + '\n'
    open(os.path.join(LATIN, c['fname']), 'w', encoding='utf-8').write(out)
    print('wrote', c['fname'], len(out), 'bytes')

if __name__ == '__main__':
    build(sys.argv[1])

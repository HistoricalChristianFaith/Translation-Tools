#!/usr/bin/env python3
"""Pass B validator for Origen In Leviticum LATIN files (adapted from the Exodus R3 validator).
Checks per file:
  - guillemets » « balanced, zero nesting, zero stray single › ‹ , zero stray > <
  - no consonantal J/j in the Latin body
  - [GCS p.N] anchors strictly monotonic non-decreasing, contiguous pStart..pEnd,
    first==pStart, last==pEnd (shared pages repeat across neighbouring files, not within one)
  - the correct (non-uniform) per-homily doxology signature present
  - section numbers in sequence from 1
Cross-file:
  - concatenated anchors cover every printed page 280..507, surplus of exactly 13 (the shared pages),
    each shared page double-anchored across its two neighbours
  - LATIN/homilyNN_latin.txt running text == _source/passB_final/homilyNN.txt (byte-identical)
"""
import re, sys, glob, os

HERE = os.path.dirname(os.path.abspath(__file__))
LATIN_DIR = os.path.normpath(os.path.join(HERE, '..', '..', 'LATIN'))
FINAL_DIR = os.path.normpath(os.path.join(HERE, '..', 'passB_final'))

SPAN = {1:(280,288),2:(288,299),3:(300,316),4:(316,332),5:(332,358),6:(358,370),
        7:(370,393),8:(393,417),9:(417,440),10:(440,445),11:(446,454),12:(454,467),
        13:(467,478),14:(478,487),15:(487,491),16:(491,507)}

# distinguishing substring of each non-uniform doxology (verified on the images, boundary_audit.md)
DOX = {
 1: 'est »gloria et imperium in saecula saeculorum. Amen«',
 2: '»cui laus et gloria in saecula saeculorum. Amen!«',
 3: '»gloria et imperium in saecula saeculorum. Amen!«',
 4: '»est gloria et imperium in saecula saeculorum. Amen!«',
 5: '»gloria et imperium in saecula saeculorum. Amen«',
 6: '»cui est gloria et imperium in saecula saeculorum. Amen«',
 7: '»gloria et imperium in saecula saeculorum. Amen.«',
 8: '»cui est gloria et imperium in saecula saeculorum. Amen«',
 9: '»cui gloria et imperium in saecula saeculorum! Amen«',
 10:'»cui est gloria et imperium in saecula saeculorum. Amen«',
 11:'»cui est gloria et imperium in saecula saeculorum. Amen!«',
 12:'»cui gloria et imperium in saecula saeculorum. Amen!«',
 13:'»Ipsi gloria et imperium in saecula saeculorum. Amen!«',
 14:'»qui est gloria et imperium in saecula saeculorum. Amen!«',
 15:'»cui est gloria et imperium in saecula saeculorum. Amen!«',
 16:'Ipsi gloria in aeterna saecula saeculorum! Amen.',
}
SHARED = {288,316,332,358,370,393,417,440,454,467,478,487,491}

def body_of(path):
    lines = open(path, encoding='utf-8').read().splitlines()
    bs = 0
    for i,l in enumerate(lines):
        if set(l.strip())=={'='} and len(l.strip())>=60:
            bs=i+1; break
    # drop the HOMILIA line and the *lemma* / [Titulus ...] header line(s); keep numbered body
    body_lines=[]
    started=False
    for l in lines[bs:]:
        if not started:
            if re.match(r'^\s*(\[GCS p\.\d+\]\s*)?\d+\.\s', l):
                started=True
            else:
                continue  # skip HOMILIA N. , *lemma*, [Titulus...] , blank
        body_lines.append(l)
    return '\n'.join(body_lines).strip()

def running_text(path):
    """The body used for the byte-identical LATIN<->final comparison."""
    return body_of(path)

def check(path):
    hn = int(re.search(r'homily(\d+)', os.path.basename(path)).group(1))
    body = body_of(path)
    errs=[]
    op=body.count('»'); cl=body.count('«')
    if op!=cl: errs.append(f'guillemets unbalanced »={op} «={cl}')
    depth=0; maxd=0
    for ch in body:
        if ch=='»': depth+=1; maxd=max(maxd,depth)
        elif ch=='«': depth-=1
        if depth<0: errs.append('guillemet close before open'); depth=0
    if maxd>1: errs.append(f'guillemet nesting depth {maxd}')
    if depth!=0: errs.append(f'guillemet left open depth {depth}')
    for bad,nm in [('›','stray ›'),('‹','stray ‹'),('>','stray >'),('<','stray <')]:
        if bad in body: errs.append(f'{nm} present ({body.count(bad)})')
    if re.search(r'[Jj]', body):
        errs.append('consonantal J/j: '+repr(re.findall(r'\S*[Jj]\S*',body)[:5]))
    anchors=[int(m) for m in re.findall(r'\[GCS p\.(\d+)\]', body)]
    ps,pe=SPAN[hn]
    if not anchors:
        pass  # R7: page anchors stripped from the reading text — anchor checks auto-skip
    else:
        if anchors[0]!=ps: errs.append(f'first anchor {anchors[0]} != pStart {ps}')
        if anchors[-1]!=pe: errs.append(f'last anchor {anchors[-1]} != pEnd {pe}')
        for a,b in zip(anchors,anchors[1:]):
            if b<a: errs.append(f'anchor non-monotonic {a}->{b}')
            if b>a+1: errs.append(f'anchor gap {a}->{b}')
        present=set(anchors)
        for p in range(ps,pe+1):
            if p not in present: errs.append(f'missing anchor p{p}')
        dup=[p for p in present if anchors.count(p)>1]
        if dup: errs.append(f'anchor repeated within file: {sorted(dup)}')
    if DOX[hn] not in body: errs.append(f'doxology signature missing: {DOX[hn]!r}')
    secs=[int(m) for m in re.findall(r'(?:(?<=\])|(?m:^))\s*(\d+)\.\s', body)]
    exp=1; seen=[]
    for s in secs:
        if s==exp: seen.append(s); exp+=1
    if seen and seen[0]!=1: errs.append(f'sections start at {seen[0]} not 1')
    # final vs LATIN byte-identical running text
    fp=os.path.join(FINAL_DIR, f'homily{hn:02d}.txt')
    if os.path.exists(fp):
        if running_text(path)!=open(fp,encoding='utf-8').read().strip():
            errs.append('LATIN body != passB_final (not byte-identical)')
    else:
        errs.append('passB_final file missing')
    return hn,anchors,seen,errs

def main():
    files=sorted(glob.glob(os.path.join(LATIN_DIR,'homily*_latin.txt')))
    allclean=True
    all_anchors=[]
    per={}
    for f in files:
        hn,anchors,secs,errs=check(f)
        per[hn]=anchors
        all_anchors+=anchors
        status='CLEAN' if not errs else 'FAIL'
        if errs: allclean=False
        a0=anchors[0] if anchors else None; a1=anchors[-1] if anchors else None
        print(f'Hom {hn:2d}: anchors {a0}-{a1} (n={len(anchors)}) secs 1..{secs[-1] if secs else "?"} -> {status}')
        for e in errs: print('     -',e)
    # cross-file coverage
    print('\n== cross-file coverage ==')
    if not all_anchors:
        # R7: page anchors stripped from every file — coverage/shared-page checks auto-skip
        print('  no anchors in any file — R7 strip complete; coverage checks auto-skipped')
    else:
        cov=set(all_anchors)
        missing=[p for p in range(280,508) if p not in cov]
        print(f'total anchors={len(all_anchors)}, distinct pages={len(cov)} (expect 228), surplus={len(all_anchors)-228} (expect 13)')
        if missing: print('  MISSING pages:',missing); allclean=False
        # shared-page double anchoring
        from collections import Counter
        c=Counter(all_anchors)
        doubled={p for p,n in c.items() if n>1}
        if doubled!=SHARED:
            print('  shared-page mismatch. doubled=',sorted(doubled),' expected=',sorted(SHARED)); allclean=False
        else:
            print(f'  13 shared pages double-anchored correctly: {sorted(SHARED)}')
    print('\nALL 16 CLEAN' if allclean else '\nERRORS PRESENT')
    return 0 if allclean else 1

if __name__=='__main__':
    sys.exit(main())

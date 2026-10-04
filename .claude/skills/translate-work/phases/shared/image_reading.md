# Shared: reading page images (every phase that looks at scans)

The printed page image is the **ground truth**. OCR, other editions and translations are only
detectors that point to places worth looking. Every decision is made by looking at the image.

## Finding the right image

- Page images are listed in `_source/<images dir>/index.json` (`label` → `file`, relative to
  `_source/`). The base edition's index is `_source/pages/base/index.json`; witnesses have
  their own folders (`_source/pages/<witness>/index.json`).
- **Look pages up by printed label through the index. Never compute a leaf or PDF number.**
  Page→leaf offsets drift, and scans duplicate or jumble pages. A label ending in `b`
  (`393b`) is a second scan of the same printed page. Either copy is fine; say which you used.
- Open an image with the Read tool.

## Reading reliably

1. **Read the whole page first** to get the layout: where the main text is, where the apparatus
   starts, how many columns there are, any headings.
2. **Very large scans** (longest side much over ~2500 px) can be read unreliably at full size.
   Make a reduced copy for orientation:
   `python3 ${TOOLS_DIR}/crop.py PAGE.jpg --downscale 1900 --out ${RUN_DIR}/crops/<unique>.jpg`
3. **Read the text band by band.** For transcription and collation, don't rely on a single look
   at the full page. Walk it in horizontal bands:
   `python3 ${TOOLS_DIR}/crop.py PAGE.jpg --band 3 --of 8 --scale 1.5 --out ${RUN_DIR}/crops/<unique>.png`
4. **Crop and enlarge every doubtful spot, about 3×:**
   `python3 ${TOOLS_DIR}/crop.py PAGE.jpg --box 0.10 0.42 0.90 0.47 --out ${RUN_DIR}/crops/<unique>.png`
   (box = x0 y0 x1 y1 as fractions). This is **mandatory** before you decide on:
   - accents, breathings, iota subscript, final vs medial sigma;
   - c/e, u/n, rn/m, li/h, ſ/f, and confusable ligatures;
   - italic vs roman, bold (clarendon) vs regular, small capitals / uncial: this is the
     boundary between `» «`, `* *` and plain text;
   - section numerals (`8.` misread as `S.`), punctuation at a doxology;
   - anything at a **cut, faded or curved margin**. Errors hide there most often.

   Always use a unique crop filename (include the phase, packet, page and a counter).
5. **Two-column pages** (Migne, Cramer): odd column = left half, even = right half. Read the
   whole left column top to bottom, then the right. Watch for a band that **spans both
   columns** at the top or bottom of a page. A unit's ending can sit in a full-width band above
   interleaved material.

## Layout traps (seen in real projects)

- **Running heads lag the text at boundaries.** Place unit boundaries using the centered
  headings, incipits and closing formulas (doxologies), never the running head.
- **Interleaved foreign material.** Migne interleaves *Selecta* catena scholia between homily
  sets. Catena editions interleave other Fathers. Transcribe only the work in hand.
- **Apparatus vs text.** The apparatus sits below a rule, in smaller type, keyed by line
  numbers. Never take apparatus words into the text.
- **Marginal numbers** (another edition's pages, e.g. Cramer's page numbers in Jenkins's
  margin) are not text. Note them in your notes if they matter for a witness pass.

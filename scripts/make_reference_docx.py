#!/usr/bin/env python3
"""
make_reference_docx.py -- Build the pandoc reference document used to style the
manuscript.

Pandoc's stock reference.docx defaults to a sans-serif theme font and carries no
explicit section properties. This script derives a styled template from it:

  * body font  -> Cambria 11 pt (serif, appropriate for a manuscript)
  * page size  -> US Letter (12240 x 15840 DXA), 1 inch margins

Run from the repository root:

    python scripts/make_reference_docx.py paper/build/reference.docx
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile


BODY_FONT = "Cambria"
BODY_SIZE_HALF_POINTS = "22"          # 11 pt

SECTPR = (
    '<w:sectPr>'
    '<w:pgSz w:w="12240" w:h="15840"/>'                       # US Letter
    '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
    'w:header="720" w:footer="720" w:gutter="0"/>'            # 1 inch margins
    '</w:sectPr>'
)


def main(out_path: str) -> int:
    out_path = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        stock = os.path.join(tmp, "stock.docx")
        with open(stock, "wb") as fh:
            subprocess.run(
                ["pandoc", "--print-default-data-file", "reference.docx"],
                stdout=fh, check=True,
            )

        work = os.path.join(tmp, "unpacked")
        with zipfile.ZipFile(stock) as z:
            z.extractall(work)

        # --- styles.xml: serif body font at 11 pt -------------------------
        styles_path = os.path.join(work, "word", "styles.xml")
        styles = open(styles_path, encoding="utf-8").read()
        old = ('<w:rFonts w:asciiTheme="minorHAnsi" w:eastAsiaTheme="minorHAnsi" '
               'w:hAnsiTheme="minorHAnsi" w:cstheme="minorBidi" />\n'
               '        <w:sz w:val="24" />\n        <w:szCs w:val="24" />')
        new = (f'<w:rFonts w:ascii="{BODY_FONT}" w:eastAsia="{BODY_FONT}" '
               f'w:hAnsi="{BODY_FONT}" w:cs="{BODY_FONT}" />\n'
               f'        <w:sz w:val="{BODY_SIZE_HALF_POINTS}" />\n'
               f'        <w:szCs w:val="{BODY_SIZE_HALF_POINTS}" />')
        if old not in styles:
            print("WARNING: pandoc's default docDefaults block changed; "
                  "body font not patched. Check your pandoc version.",
                  file=sys.stderr)
        else:
            styles = styles.replace(old, new, 1)
            open(styles_path, "w", encoding="utf-8").write(styles)

        # --- document.xml: US Letter page setup ---------------------------
        doc_path = os.path.join(work, "word", "document.xml")
        doc = open(doc_path, encoding="utf-8").read()
        if "<w:sectPr />" in doc:
            doc = doc.replace("<w:sectPr />", SECTPR, 1)
        elif not re.search(r"<w:pgSz", doc):
            doc = doc.replace("</w:body>", SECTPR + "</w:body>", 1)
        open(doc_path, "w", encoding="utf-8").write(doc)

        # --- repack -------------------------------------------------------
        if os.path.exists(out_path):
            os.remove(out_path)
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _dirs, files in os.walk(work):
                for name in files:
                    full = os.path.join(root, name)
                    z.write(full, os.path.relpath(full, work))

    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "paper/build/reference.docx"
    sys.exit(main(target))

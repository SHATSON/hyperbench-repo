#!/usr/bin/env python3
"""
apply_hanging_indent.py -- Apply APA 7th-edition hanging indents to the
reference list of a generated .docx.

Pandoc emits reference entries as ordinary body paragraphs, so the 0.5 inch
hanging indent APA requires must be applied afterwards. This script locates the
paragraphs between the "References" heading and the "Appendix A" heading and
inserts a <w:ind> element into each.

Schema note: CT_PPr enforces child element order (pStyle, ..., spacing, ind,
...). Inserting <w:ind> at the front of <w:pPr> produces a file that Word will
still open but that fails XSD validation, so the insertion point is chosen
relative to any existing pStyle or spacing element.

Usage:
    python scripts/apply_hanging_indent.py in.docx out.docx
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
import zipfile


HANG = '<w:ind w:left="720" w:hanging="720"/>'      # 0.5 inch = 720 DXA
START_HEADING = "References"
STOP_HEADING_PREFIX = "Appendix A"
SKIP_PREFIX = "Every entry below"                    # editorial note, not an entry


def indent_paragraph(block: str) -> str:
    if "<w:pPr>" in block:
        if "</w:pStyle>" in block:
            return block.replace("</w:pStyle>", "</w:pStyle>" + HANG, 1)
        if re.search(r"<w:pStyle[^>]*/>", block):
            return re.sub(r"(<w:pStyle[^>]*/>)", r"\1" + HANG, block, count=1)
        if re.search(r"<w:spacing[^>]*/>", block):
            return re.sub(r"(<w:spacing[^>]*/>)", r"\1" + HANG, block, count=1)
        return block.replace("<w:pPr>", "<w:pPr>" + HANG, 1)
    return re.sub(r"^(<w:p\b[^>]*>)", r"\1<w:pPr>" + HANG + "</w:pPr>",
                  block, count=1)


def main(src: str, dst: str) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        work = os.path.join(tmp, "unpacked")
        with zipfile.ZipFile(src) as z:
            z.extractall(work)

        doc_path = os.path.join(work, "word", "document.xml")
        doc = open(doc_path, encoding="utf-8").read()

        paras = list(re.finditer(r"<w:p\b.*?</w:p>|<w:p\b[^>]*/>", doc, re.S))
        texts = ["".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", m.group(0), re.S))
                 for m in paras]

        start = stop = None
        for i, (m, t) in enumerate(zip(paras, texts)):
            if start is None and t.strip() == START_HEADING and "Heading" in m.group(0):
                start = i
            elif start is not None and t.strip().startswith(STOP_HEADING_PREFIX):
                stop = i
                break
        if start is None or stop is None:
            print("ERROR: could not locate the reference list "
                  f"(start={start}, stop={stop})", file=sys.stderr)
            return 1

        edits = []
        for i in range(start + 1, stop):
            text = texts[i].strip()
            if not text or text.startswith(SKIP_PREFIX):
                continue
            m = paras[i]
            edits.append((m.start(), m.end(), indent_paragraph(m.group(0))))

        out, prev = [], 0
        for s, e, new in edits:
            out.append(doc[prev:s])
            out.append(new)
            prev = e
        out.append(doc[prev:])
        open(doc_path, "w", encoding="utf-8").write("".join(out))

        if os.path.exists(dst):
            os.remove(dst)
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _dirs, files in os.walk(work):
                for name in files:
                    full = os.path.join(root, name)
                    z.write(full, os.path.relpath(full, work))

    print(f"applied hanging indent to {len(edits)} reference entries -> {dst}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))

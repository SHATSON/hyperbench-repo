#!/usr/bin/env bash
# build_paper.sh -- Rebuild the manuscript .docx from Markdown source.
#
# Requires: pandoc >= 3.0, python3.
# Optional (for visual verification): libreoffice, poppler-utils.
#
# Usage:  bash scripts/build_paper.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

SRC="paper/traversable-hyperspace-paper.md"
FRONT="paper/frontmatter.md"
BUILD="paper/build"
REF="$BUILD/reference.docx"
OUT="paper/traversable-hyperspace-paper.docx"

command -v pandoc >/dev/null || { echo "pandoc not found"; exit 1; }
mkdir -p "$BUILD"

echo "[1/5] regenerating figures"
if python3 -c "import matplotlib" 2>/dev/null; then
  python3 figures/make_architecture_figure.py
else
  echo "  matplotlib not installed; reusing committed figures/architecture.png"
  echo "  (pip install -r requirements-paper.txt to regenerate)"
fi

echo "[2/5] building styled reference document"
python3 scripts/make_reference_docx.py "$REF"

echo "[3/5] concatenating front matter and body"
cat "$FRONT" "$SRC" > "$BUILD/full.md"

echo "[4/5] converting to docx (LaTeX math -> native Word equations)"
pandoc "$BUILD/full.md" \
  --from markdown+tex_math_dollars+pipe_tables+raw_attribute \
  --to docx \
  --reference-doc="$REF" \
  --standalone \
  -o "$BUILD/unindented.docx"

echo "[5/5] applying APA hanging indents to the reference list"
python3 scripts/apply_hanging_indent.py "$BUILD/unindented.docx" "$OUT"

echo
echo "Built: $OUT"
python3 - "$OUT" <<'PY'
import sys, zipfile, re
d = zipfile.ZipFile(sys.argv[1]).read('word/document.xml').decode()
print(f"  equations (native OMML): {d.count('<m:oMath')}")
print(f"  tables:                  {d.count('<w:tbl>')}")
print(f"  hanging indents:         {d.count('w:hanging=\"720\"')}")
print(f"  TOC field present:       {('TOC ' + chr(92) + 'o') in d}")
media = [n for n in zipfile.ZipFile(sys.argv[1]).namelist() if n.startswith('word/media')]
print(f"  embedded images:         {len(media)}")
m = re.search(r'<w:pgSz[^/]*/>', d)
print(f"  page size:               {m.group(0) if m else 'not set'}")
PY

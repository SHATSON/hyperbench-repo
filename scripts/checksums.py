#!/usr/bin/env python3
"""
checksums.py -- Record and verify SHA-256 digests of the committed result files.

The JSON files under results/ are the data of record backing every number in the
manuscript. This tool lets a reader confirm that the files they received are the
files that were published, and lets the author detect an unintended change
before committing.

    python scripts/checksums.py            # write results/CHECKSUMS.sha256
    python scripts/checksums.py --verify   # check current files against it

Note on floating-point reproducibility: digests are expected to match exactly on
the environment of record (see VERIFICATION.md). A different BLAS build, CPU, or
library version can alter the last bits of some values, which changes the digest
without indicating an error. If verification fails, run the test suite --
`python tests/test_paper_claims.py` -- which checks the values against
tolerances rather than byte-for-byte, and is the authoritative check.
"""

from __future__ import annotations

import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
MANIFEST = os.path.join(RESULTS, "CHECKSUMS.sha256")


def digest(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# run_metadata.json records wall-clock time and platform strings, which differ
# on every machine by design. Hashing it would guarantee a mismatch, so the
# manifest covers the deterministic data files only.
VOLATILE = {"run_metadata.json"}


def target_files() -> list[str]:
    return sorted(
        f for f in os.listdir(RESULTS)
        if f.endswith(".json") and f not in VOLATILE
    )


def write() -> int:
    lines = [f"{digest(os.path.join(RESULTS, f))}  {f}" for f in target_files()]
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"wrote {MANIFEST} ({len(lines)} files)")
    return 0


def verify() -> int:
    if not os.path.exists(MANIFEST):
        print(f"ERROR: {MANIFEST} not found; run without --verify first.",
              file=sys.stderr)
        return 1

    expected = {}
    for line in open(MANIFEST, encoding="utf-8"):
        line = line.strip()
        if line:
            h, name = line.split("  ", 1)
            expected[name] = h

    ok = True
    for name, want in sorted(expected.items()):
        path = os.path.join(RESULTS, name)
        if not os.path.exists(path):
            print(f"MISSING  {name}")
            ok = False
            continue
        got = digest(path)
        if got == want:
            print(f"OK       {name}")
        else:
            print(f"CHANGED  {name}\n           expected {want}\n           got      {got}")
            ok = False

    for name in target_files():
        if name not in expected:
            print(f"UNTRACKED {name}")

    if not ok:
        print("\nDigests differ. This may be benign (different CPU or library "
              "build). Run `python tests/test_paper_claims.py` -- the tolerance-"
              "based check is authoritative.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(verify() if "--verify" in sys.argv else write())

#!/usr/bin/env python3
"""Round-trip test (item 9 of the 2026-09 audit round) for the press-kit
ZIP writer: tests/test-zip-store-lite.mjs already checks reproducibility
and the presence of ZIP magic bytes, but never actually decompresses the
output with an independent parser. A byte-writer bug (wrong CRC, wrong
offset, wrong header field) can produce something that merely *looks* like
a ZIP without truly being one -- "it downloads" is not the same claim as
"it decompresses". This test generates a ZIP via Node (the real
zip-store-lite.js) and verifies it with Python's zipfile module, a
completely independent implementation, covering unicode content, a
unicode filename, an empty file, a nested path and a >1KB file.

Uso:
  python tests/test-zip-store-lite-roundtrip.py
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
GEN_SCRIPT = ROOT / "tests" / "fixtures" / "zip-store-lite-roundtrip-gen.mjs"

failures: list[str] = []


def check(condition: bool, label: str) -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}")
        failures.append(label)


with tempfile.TemporaryDirectory() as tmp_dir:
    zip_path = Path(tmp_dir) / "kit.zip"
    result = subprocess.run(
        ["node", str(GEN_SCRIPT), str(zip_path)],
        cwd=ROOT, capture_output=True, encoding="utf-8",
    )
    check(result.returncode == 0, f"node generator exits 0 (stderr: {result.stderr.strip()[:200]})")
    expected = json.loads(result.stdout.strip().splitlines()[-1])

    with zipfile.ZipFile(zip_path) as zf:
        check(zf.testzip() is None, "zipfile.testzip() reports no CRC errors")
        check(set(zf.namelist()) == set(expected.keys()), "namelist matches the expected file set exactly")

        for path, expected_text in expected.items():
            try:
                actual = zf.read(path).decode("utf-8")
            except KeyError:
                failures.append(f"{path}: missing from the archive")
                print(f"  FAIL {path}: missing from the archive")
                continue
            check(actual == expected_text, f"{path}: extracted content matches byte-for-byte")

print(f"tests/test-zip-store-lite-roundtrip: {'OK' if not failures else f'{len(failures)} FALLO(S)'}")
raise SystemExit(1 if failures else 0)

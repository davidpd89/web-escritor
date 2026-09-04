#!/usr/bin/env python3
"""Regression coverage for scripts/build-manecillas-sample.py's EPUB/TXT
output: structural EPUB validity (independent of the generator's own code,
same principle already used for the ICS/ZIP generators elsewhere in this
repo), content fidelity to the source transcription, and that the
committed files are not stale relative to data/manecillas-capitulo-1-1.txt.
"""
from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path
from xml.dom.minidom import parseString

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "manecillas-capitulo-1-1.txt"
EPUB_PATH = ROOT / "assets" / "downloads" / "manecillas" / "las-manecillas-del-recuerdo-muestra-capitulo-1-1.epub"
TXT_PATH = ROOT / "assets" / "downloads" / "manecillas" / "las-manecillas-del-recuerdo-muestra-capitulo-1-1.txt"

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


# 1. Committed files must be up to date with the source (the same
# --check convention as this repo's other build-*.py generators).
result = subprocess.run(
    [sys.executable, str(ROOT / "scripts" / "build-manecillas-sample.py"), "--check"],
    capture_output=True, text=True,
)
check(result.returncode == 0, f"sample files stale relative to source: {result.stdout}{result.stderr}")

check(EPUB_PATH.exists(), f"missing {EPUB_PATH.relative_to(ROOT)}")
check(TXT_PATH.exists(), f"missing {TXT_PATH.relative_to(ROOT)}")

if EPUB_PATH.exists():
    with zipfile.ZipFile(EPUB_PATH) as zf:
        names = zf.namelist()
        check(names[0] == "mimetype", "EPUB: mimetype must be the first zip entry")
        info = zf.getinfo("mimetype")
        check(info.compress_type == zipfile.ZIP_STORED, "EPUB: mimetype entry must be stored, not compressed")
        check(zf.read("mimetype") == b"application/epub+zip", "EPUB: mimetype content wrong")
        for required in ("META-INF/container.xml", "OEBPS/content.opf", "OEBPS/nav.xhtml"):
            check(required in names, f"EPUB: missing required entry {required}")
        # Every XML/XHTML document must independently parse as well-formed
        # XML -- this is a real, separate parser (xml.dom.minidom), not the
        # generator's own string templating trusting itself.
        for name in names:
            if name.endswith((".xhtml", ".xml", ".opf")):
                try:
                    parseString(zf.read(name))
                except Exception as exc:
                    errors.append(f"EPUB: {name} is not well-formed XML: {exc}")

        opf = zf.read("OEBPS/content.opf").decode("utf-8")
        check("979-8-90514-935-1" not in opf, "EPUB: must not reuse the paperback's ISBN as its own identifier")
        check("urn:uuid:" in opf, "EPUB: dc:identifier must be a stable UUID, not the paperback's ISBN")

        chapter = zf.read("OEBPS/chapter.xhtml").decode("utf-8")
        source_text = SOURCE.read_text(encoding="utf-8")
        source_paragraphs = [p.strip() for p in source_text.split("---\n", 1)[1].strip().split("\n\n") if p.strip()]
        check(len(source_paragraphs) == 51, f"source transcription paragraph count changed unexpectedly: {len(source_paragraphs)}")
        for needle in ("Tomás contó las siete veces", "las agujas invisibles del destino seguían girando"):
            check(needle in chapter, f"EPUB chapter: missing expected text {needle!r}")
        colophon = zf.read("OEBPS/colophon.xhtml").decode("utf-8")
        check("amzn.to/3SM4Oxu" in colophon, "EPUB colophon: missing the buy-the-full-book link")

if TXT_PATH.exists():
    txt = TXT_PATH.read_text(encoding="utf-8")
    check("Tomás contó las siete veces" in txt, "TXT: missing chapter opening")
    check("amzn.to/3SM4Oxu" in txt, "TXT: missing the buy-the-full-book link")
    check("Muestra gratuita" in txt, "TXT: must disclose this is a free sample, not the full book")

if errors:
    print("FAIL - manecillas-sample-build:")
    for err in errors:
        print(f"- {err}")
    raise SystemExit(1)

print("test-manecillas-sample-build: OK")

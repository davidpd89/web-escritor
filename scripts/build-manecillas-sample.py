#!/usr/bin/env python3
"""Build the downloadable free-sample files (EPUB, TXT) for Las manecillas
del recuerdo's chapter 1.1 ("El Ritual del Domingo") from a single source
of truth, so EPUB and TXT can never drift from each other or from the text
actually approved by the author.

Source: data/manecillas-capitulo-1-1.txt -- transcribed 2026-09-04 from a
PDF of the finished, published book David Porto Díaz provided directly
(verified word-for-word, 1104/1104 words, zero diff, against a pdftotext
extraction of that PDF). This is the complete chapter, not the ~150-word
teaser excerpt shown on the fragmentos page.

Deliberately NOT the print ISBN (979-8-90514-935-1): a free sample is not
the edition that ISBN identifies, so it gets its own stable identifier
(a UUID5 derived from a fixed namespace + name, so rebuilding always
produces the same one) instead of borrowing the book's.

PDF is intentionally not generated here: this repo's Python tooling is
stdlib-only (no requirements.txt/pyproject.toml, no pip installs in CI),
and no PDF-writing library is available without adding one. EPUB (this
script's primary format, matching Kindle's own Send-to-Kindle acceptance)
and TXT (trivial, stdlib-only) ship now; PDF is deferred until a dependency
addition is deliberately decided, not smuggled in via this script.

Usage:
  python scripts/build-manecillas-sample.py [--check]
    --check: verify the committed output files are up to date without
    writing (fails if stale -- same convention as the other build-*.py
    generators in this repo).
"""
from __future__ import annotations

import argparse
import io
import sys
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_PATH = ROOT / "data" / "manecillas-capitulo-1-1.txt"
OUT_DIR = ROOT / "assets" / "downloads" / "manecillas"
COVER_JPG = ROOT / "assets" / "portada-las-manecillas-del-recuerdo-1024.jpg"

BASENAME = "las-manecillas-del-recuerdo-muestra-capitulo-1-1"
EPUB_PATH = OUT_DIR / f"{BASENAME}.epub"
TXT_PATH = OUT_DIR / f"{BASENAME}.txt"

BUY_URL = "https://amzn.to/3SM4Oxu"
OFFICIAL_URL = "https://davidportodiaz.com/las-manecillas-del-recuerdo/"
KINDLE_PAGE_URL = "https://davidportodiaz.com/las-manecillas-del-recuerdo/kindle/"

# Fixed namespace so this UUID never changes across rebuilds (UUID5 is
# deterministic: same namespace + name always yields the same UUID).
SAMPLE_UUID = str(uuid.uuid5(uuid.NAMESPACE_URL, "https://davidportodiaz.com/las-manecillas-del-recuerdo/#muestra-capitulo-1-1"))


def parse_source(text: str) -> dict:
    header, body = text.split("---\n", 1)
    meta = {}
    for line in header.strip().splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    paragraphs = [p.strip() for p in body.strip().split("\n\n") if p.strip()]
    meta["paragraphs"] = paragraphs
    return meta


def xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_txt(meta: dict) -> str:
    lines = [
        meta["BOOK"],
        meta["AUTHOR"],
        "",
        f"{meta['CHAPTER_LABEL']} — {meta['TITLE']}",
        "(Muestra gratuita — no es el libro completo)",
        "",
        "=" * 40,
        "",
    ]
    lines.extend(meta["paragraphs"])
    lines.extend([
        "",
        "=" * 40,
        "",
        f"Muestra de «{meta['BOOK']}», de {meta['AUTHOR']}.",
        f"Web oficial: {OFFICIAL_URL}",
        f"Comprar el libro completo en Kindle: {BUY_URL}",
        f"Más formatos y la edición Kindle: {KINDLE_PAGE_URL}",
        "",
        f"© 2026 {meta['AUTHOR']}. Todos los derechos reservados. Esta muestra"
        " no puede reproducirse ni distribuirse sin autorización.",
    ])
    return "\n".join(lines) + "\n"


def build_epub_bytes(meta: dict) -> bytes:
    book = xml_escape(meta["BOOK"])
    author = xml_escape(meta["AUTHOR"])
    chapter_label = xml_escape(meta["CHAPTER_LABEL"])
    title = xml_escape(meta["TITLE"])
    paragraphs_xhtml = "\n".join(f"    <p>{xml_escape(p)}</p>" for p in meta["paragraphs"])

    container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

    style_css = """body { font-family: serif; line-height: 1.5; margin: 1em; }
h1, h2 { font-family: serif; text-align: center; }
p { margin: 0 0 1em 0; text-indent: 1.2em; }
p.no-indent { text-indent: 0; }
.centered { text-align: center; }
.muted { color: #555; font-size: 0.9em; }
"""

    title_xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="es" lang="es">
<head><title>{book}</title><link rel="stylesheet" type="text/css" href="style.css"/></head>
<body>
  <h1 class="centered">{book}</h1>
  <p class="centered">{author}</p>
  <p class="centered muted">Muestra gratuita — {chapter_label}: {title}</p>
  <p class="centered muted">Esta muestra no es el libro completo.</p>
</body>
</html>
"""

    chapter_xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="es" lang="es">
<head><title>{chapter_label} — {title}</title><link rel="stylesheet" type="text/css" href="style.css"/></head>
<body>
  <h2>{chapter_label}<br/>{title}</h2>
{paragraphs_xhtml}
</body>
</html>
"""

    colophon_xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="es" lang="es">
<head><title>Sobre esta muestra</title><link rel="stylesheet" type="text/css" href="style.css"/></head>
<body>
  <p class="no-indent">Has leído una muestra gratuita de <em>{book}</em>, de {author}.</p>
  <p class="no-indent">Web oficial: <a href="{OFFICIAL_URL}">{OFFICIAL_URL}</a></p>
  <p class="no-indent">Comprar el libro completo en Kindle: <a href="{BUY_URL}">{BUY_URL}</a></p>
  <p class="no-indent muted">© 2026 {author}. Todos los derechos reservados. Esta muestra no
  puede reproducirse ni distribuirse sin autorización.</p>
</body>
</html>
"""

    nav_xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="es" lang="es">
<head><title>Índice</title></head>
<body>
  <nav epub:type="toc" id="toc">
    <ol>
      <li><a href="title.xhtml">{book}</a></li>
      <li><a href="chapter.xhtml">{chapter_label} — {title}</a></li>
      <li><a href="colophon.xhtml">Sobre esta muestra</a></li>
    </ol>
  </nav>
</body>
</html>
"""

    has_cover = COVER_JPG.exists()
    cover_manifest_item = (
        '\n    <item id="cover-image" href="cover.jpg" media-type="image/jpeg" properties="cover-image"/>'
        if has_cover else ""
    )
    cover_meta = '\n    <meta name="cover" content="cover-image"/>' if has_cover else ""

    content_opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="pub-id" xml:lang="es">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="pub-id">urn:uuid:{SAMPLE_UUID}</dc:identifier>
    <dc:title>{book} — Muestra ({chapter_label})</dc:title>
    <dc:creator>{author}</dc:creator>
    <dc:language>es</dc:language>
    <dc:rights>© 2026 {author}. Todos los derechos reservados.</dc:rights>
    <dc:description>Muestra gratuita de {book}: {chapter_label}, "{title}".</dc:description>
    <meta property="dcterms:modified">2026-09-04T00:00:00Z</meta>{cover_meta}
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="style" href="style.css" media-type="text/css"/>
    <item id="title-page" href="title.xhtml" media-type="application/xhtml+xml"/>
    <item id="chapter" href="chapter.xhtml" media-type="application/xhtml+xml"/>
    <item id="colophon" href="colophon.xhtml" media-type="application/xhtml+xml"/>{cover_manifest_item}
  </manifest>
  <spine>
    <itemref idref="title-page"/>
    <itemref idref="chapter"/>
    <itemref idref="colophon"/>
  </spine>
</package>
"""

    # zipfile.writestr()/write() stamp each entry with the CURRENT time by
    # default, which would make every rebuild produce different bytes from
    # the exact same source -- breaking both the --check staleness gate and
    # any future reproducible-build expectation. A fixed date_time makes
    # the output a pure function of the source content.
    FIXED_DATE_TIME = (2026, 9, 4, 0, 0, 0)

    def _entry(name: str, compress_type: int) -> zipfile.ZipInfo:
        info = zipfile.ZipInfo(name, date_time=FIXED_DATE_TIME)
        info.compress_type = compress_type
        info.external_attr = 0o644 << 16
        # ZipInfo defaults create_system to 0 (DOS/Windows) or 3 (Unix)
        # based on the CURRENT platform running this script -- left at its
        # default, the exact same source produces different zip bytes when
        # built on Windows (this developer's machine) vs Linux (CI), which
        # is exactly what made --check see the committed EPUB as "stale"
        # in CI even though it was byte-identical to a local Windows
        # rebuild (confirmed live). Pinning it makes the build a pure
        # function of the source content, independent of the host OS.
        info.create_system = 3
        return info

    buf = io.BytesIO()
    # EPUB requires "mimetype" to be the FIRST entry in the zip, stored
    # (not deflated) -- readers use this exact byte layout to identify a
    # valid EPUB before parsing any XML.
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(_entry("mimetype", zipfile.ZIP_STORED), "application/epub+zip")
        zf.writestr(_entry("META-INF/container.xml", zipfile.ZIP_DEFLATED), container_xml)
        zf.writestr(_entry("OEBPS/style.css", zipfile.ZIP_DEFLATED), style_css)
        zf.writestr(_entry("OEBPS/nav.xhtml", zipfile.ZIP_DEFLATED), nav_xhtml)
        zf.writestr(_entry("OEBPS/title.xhtml", zipfile.ZIP_DEFLATED), title_xhtml)
        zf.writestr(_entry("OEBPS/chapter.xhtml", zipfile.ZIP_DEFLATED), chapter_xhtml)
        zf.writestr(_entry("OEBPS/colophon.xhtml", zipfile.ZIP_DEFLATED), colophon_xhtml)
        zf.writestr(_entry("OEBPS/content.opf", zipfile.ZIP_DEFLATED), content_opf)
        if has_cover:
            zf.writestr(_entry("OEBPS/cover.jpg", zipfile.ZIP_DEFLATED), COVER_JPG.read_bytes())
    return buf.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify output is up to date without writing")
    args = parser.parse_args()

    text = SOURCE_PATH.read_text(encoding="utf-8")
    meta = parse_source(text)

    txt_rendered = build_txt(meta)
    epub_rendered = build_epub_bytes(meta)

    if args.check:
        errors = []
        txt_on_disk = open(TXT_PATH, encoding="utf-8", newline="").read() if TXT_PATH.exists() else None
        if txt_on_disk != txt_rendered:
            errors.append(f"{TXT_PATH.relative_to(ROOT)} is stale or missing")
        if not EPUB_PATH.exists() or EPUB_PATH.read_bytes() != epub_rendered:
            errors.append(f"{EPUB_PATH.relative_to(ROOT)} is stale or missing")
        if errors:
            for e in errors:
                print(f"FAIL: {e}")
            print("Regenerate with: python scripts/build-manecillas-sample.py")
            return 1
        print("PASS: sample files match data/manecillas-capitulo-1-1.txt")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # newline="" disables the platform-native newline translation
    # write_text() applies by default (which would silently turn every \n
    # in txt_rendered into \r\n on Windows) -- without it, this file's
    # actual on-disk bytes depended on which OS last regenerated it.
    TXT_PATH.write_text(txt_rendered, encoding="utf-8", newline="")
    EPUB_PATH.write_bytes(epub_rendered)
    print(f"WROTE: {TXT_PATH.relative_to(ROOT)}")
    print(f"WROTE: {EPUB_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "data/content-registry.json").read_text(encoding="utf-8"))
DEFAULTS = REGISTRY.get("defaults", {})

MOJIBAKE = (
    "\ufffd",   # Unicode replacement character
    "Ã",        # UTF-8 decoded as Windows-1252/Latin-1
    "Â",
    "â€",
    "â€™",
    "â€œ",
    "â€\x9d",
    "ðŸ",
    "ï»¿",
)

def public_files() -> list[Path]:
    files: set[Path] = set()
    for raw in REGISTRY.get("entries", []):
        item = {**DEFAULTS, **raw}
        if item.get("status") != "public":
            continue
        source = item.get("sourceFile")
        if source:
            p = ROOT / source
            if p.is_file():
                files.add(p)
    for name in (
        "404.html", "robots.txt", "humans.txt", "llms.txt", "llms-full.txt",
        "manifest.json", "service-worker.js", "sitemap.xml", "editoriales-sitemap.xml",
        "convocatorias-escritores/opportunities.json",
        "convocatorias-escritores/deadlines.ics",
        "editoriales/editoriales-data.json",
    ):
        p = ROOT / name
        if p.is_file():
            files.add(p)
    return sorted(files)

errors: list[str] = []
checked = 0
for path in public_files():
    rel = path.relative_to(ROOT).as_posix()
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        errors.append(f"{rel}: invalid UTF-8 at byte {exc.start}")
        continue
    checked += 1

    for token in MOJIBAKE:
        if token in text:
            line = text[: text.index(token)].count("\n") + 1
            errors.append(f"{rel}:{line}: suspicious mojibake token {token!r}")

    if path.suffix.lower() in {".html", ".htm"}:
        head = text[:12000]
        if not re.search(r"<meta\s+charset\s*=\s*['\"]?utf-8", head, re.I):
            errors.append(f"{rel}: public HTML lacks UTF-8 meta charset")

    if path.suffix.lower() == ".json":
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            errors.append(f"{rel}:{exc.lineno}: invalid JSON: {exc.msg}")

if errors:
    print("PUBLIC TEXT ENCODING: FAIL")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print(f"PUBLIC TEXT ENCODING: PASS ({checked} public artifacts)")

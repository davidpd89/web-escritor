#!/usr/bin/env python3
"""Regression contract for local V1 font assets.

The generic asset-casing test only reports case mismatches. It does not fail
when a CSS url() points to a completely missing file. This test closes that
gap for the canonical V1 typography sheet and also verifies that referenced
.woff2 files are actual WOFF2 binaries rather than merely renamed files.
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CSS_PATH = ROOT / "assets" / "v1-fonts.css"
CSS = CSS_PATH.read_text(encoding="utf-8")
WOFF2_SIGNATURE = b"wOF2"

URL_RE = re.compile(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)", re.IGNORECASE)


def resolve_local(ref: str) -> Path:
    parsed = urlsplit(ref)
    rel = parsed.path
    if rel.startswith("/"):
        return (ROOT / rel.lstrip("/")).resolve()
    return (CSS_PATH.parent / rel).resolve()


def main() -> None:
    refs = [match.group(1).strip() for match in URL_RE.finditer(CSS)]
    assert refs, "v1-fonts.css: no font url() references found"

    failures: list[str] = []
    checked_binaries: set[Path] = set()

    for ref in refs:
        parsed = urlsplit(ref)
        if parsed.scheme or parsed.netloc:
            failures.append(f"remote font reference is not allowed: {ref}")
            continue

        target = resolve_local(ref)

        try:
            target.relative_to(ROOT)
        except ValueError:
            failures.append(f"font reference escapes repository root: {ref}")
            continue

        if target.suffix.lower() != ".woff2":
            failures.append(f"font asset must be WOFF2: {ref}")

        if not target.is_file():
            failures.append(f"missing font asset: {ref}")
            continue

        if target not in checked_binaries:
            checked_binaries.add(target)
            if target.read_bytes()[:4] != WOFF2_SIGNATURE:
                failures.append(f"invalid WOFF2 binary signature: {ref}")

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        raise SystemExit(1)

    print(
        "PASS V1 font assets contract: "
        f"{len(refs)} CSS reference(s), {len(checked_binaries)} unique WOFF2 binary file(s) verified"
    )


if __name__ == "__main__":
    main()

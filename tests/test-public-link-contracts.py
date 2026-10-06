#!/usr/bin/env python3
from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "content-registry.json"


OWN_HOSTS = {"davidportodiaz.com", "www.davidportodiaz.com"}


def _is_cross_origin(href: str) -> bool:
    """True only for an absolute URL pointing somewhere that is not this site.

    Root-relative hrefs, fragments and mailto:/tel: are not cross-origin
    navigations in the sense rel=noreferrer is about.
    """
    parsed = urlparse(href)
    if parsed.scheme in {"", "mailto", "tel"} and not parsed.netloc:
        return False
    if parsed.scheme not in {"http", "https"}:
        return False
    return (parsed.hostname or "").lower() not in OWN_HOSTS


class LinkParser(HTMLParser):
    def __init__(self, source: Path):
        super().__init__(convert_charrefs=True)
        self.source = source
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        line, _ = self.getpos()
        data = {k.lower(): (v or "") for k, v in attrs}
        href = data.get("href", "").strip()
        target = data.get("target", "").strip().lower()

        if href.lower().startswith("javascript:"):
            self.errors.append(f"{self.source}:{line}: javascript: URL is forbidden")

        if target == "_blank":
            rel = {token.lower() for token in data.get("rel", "").split()}
            # noopener is the security one and applies to every new tab: without
            # it the opened document gets a window.opener handle back into this
            # one. Required unconditionally.
            if "noopener" not in rel:
                self.errors.append(
                    f"{self.source}:{line}: target=_blank link lacks rel=noopener: {href!r}"
                )
            # noreferrer only buys something when the destination is a third
            # party, and it costs real data on our own links: it strips the
            # Referer for same-origin navigation too, so /prensa.html opening
            # /press-kit/*.json in a new tab would arrive with no referrer and
            # the site's own analytics could not tell where it came from. Asked
            # for cross-origin targets only.
            if _is_cross_origin(href) and "noreferrer" not in rel:
                self.errors.append(
                    f"{self.source}:{line}: cross-origin target=_blank link lacks rel=noreferrer: {href!r}"
                )

        if href.startswith("http://"):
            host = (urlparse(href).hostname or "").lower()
            if host in {"davidportodiaz.com", "www.davidportodiaz.com"}:
                self.errors.append(
                    f"{self.source}:{line}: own-site link must not use insecure http: {href!r}"
                )


def public_html_files() -> list[Path]:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    defaults = payload.get("defaults", {})
    seen: set[Path] = set()
    files: list[Path] = []
    for entry in payload.get("entries", []):
        merged = {**defaults, **entry}
        source = str(merged.get("sourceFile") or "")
        if merged.get("status") != "public" or not source.endswith(".html"):
            continue
        path = ROOT / source
        if path.exists() and path not in seen:
            files.append(path)
            seen.add(path)
    special = ROOT / "404.html"
    if special.exists() and special not in seen:
        files.append(special)
    return sorted(files)


def main() -> int:
    files = public_html_files()
    errors: list[str] = []
    for path in files:
        parser = LinkParser(path.relative_to(ROOT))
        parser.feed(path.read_text(encoding="utf-8"))
        parser.close()
        errors.extend(parser.errors)

    if errors:
        print(f"FAIL public link contracts: {len(errors)} issue(s) across {len(files)} files")
        for error in errors[:300]:
            print(error)
        if len(errors) > 300:
            print(f"... {len(errors)-300} more")
        return 1

    print(f"PASS public link contracts: {len(files)} public HTML files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

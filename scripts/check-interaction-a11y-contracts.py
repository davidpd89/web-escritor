#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORE_PREFIXES = ("lab/", "docs/", "tests/", "scripts/", "_")
VIEWPORT_BLOCK_RE = re.compile(
    r"(?:user-scalable\s*=\s*no|maximum-scale\s*=\s*1(?:\.0+)?)",
    re.I,
)

INTERACTIVE = {"a", "button", "input", "select", "textarea"}


def tracked_html() -> list[Path]:
    out = subprocess.check_output(
        ["git", "ls-files", "-z", "*.html"], cwd=ROOT
    ).decode("utf-8").split("\0")
    paths = []
    for rel in out:
        if not rel or rel.startswith(IGNORE_PREFIXES):
            continue
        path = ROOT / rel
        if path.is_file():
            paths.append(path)
    return sorted(paths)


class AuditParser(HTMLParser):
    def __init__(self, rel: str):
        super().__init__(convert_charrefs=True)
        self.rel = rel
        self.stack: list[tuple[str, dict[str, str | None], int]] = []
        self.errors: list[str] = []
        self.viewport_count = 0

    def fail(self, line: int, message: str) -> None:
        self.errors.append(f"{self.rel}:{line}: {message}")

    @staticmethod
    def attrs_dict(attrs):
        return {str(k).lower(): v for k, v in attrs}

    @staticmethod
    def is_focusable(tag: str, attrs: dict[str, str | None]) -> bool:
        if "hidden" in attrs or "disabled" in attrs:
            return False
        tabindex = (attrs.get("tabindex") or "").strip()
        if tabindex == "-1":
            return False
        if tag == "a":
            return bool((attrs.get("href") or "").strip())
        return tag in {"button", "input", "select", "textarea"}

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        a = self.attrs_dict(attrs)
        line, _ = self.getpos()

        tabindex = (a.get("tabindex") or "").strip()
        if re.fullmatch(r"\+?[1-9]\d*", tabindex):
            self.fail(line, f"positive tabindex={tabindex!r} disrupts natural keyboard order")

        if "autofocus" in a:
            self.fail(line, "autofocus can steal focus on page load")

        if tag == "meta" and (a.get("name") or "").lower() == "viewport":
            self.viewport_count += 1
            content = a.get("content") or ""
            if VIEWPORT_BLOCK_RE.search(content):
                self.fail(line, f"viewport blocks user zoom: {content!r}")

        aria_hidden = (a.get("aria-hidden") or "").lower() == "true"
        if aria_hidden and self.is_focusable(tag, a):
            self.fail(line, f"focusable <{tag}> is hidden from accessibility tree with aria-hidden=true")

        if tag in INTERACTIVE and self.is_focusable(tag, a):
            for ancestor_tag, ancestor_attrs, ancestor_line in reversed(self.stack):
                if ancestor_tag not in {"a", "button"}:
                    continue
                if self.is_focusable(ancestor_tag, ancestor_attrs):
                    self.fail(
                        line,
                        f"interactive <{tag}> nested inside focusable <{ancestor_tag}> opened at line {ancestor_line}",
                    )
                    break

        if tag == "input" and (a.get("type") or "text").lower() == "email":
            autocomplete = (a.get("autocomplete") or "").lower().split()
            if "email" not in autocomplete:
                self.fail(line, 'email input must expose autocomplete="email"')

        self.stack.append((tag, a, line))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self.stack:
            self.stack.pop()

    def handle_endtag(self, tag):
        tag = tag.lower()
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break


errors: list[str] = []
checked = 0
for path in tracked_html():
    rel = path.relative_to(ROOT).as_posix()
    parser = AuditParser(rel)
    try:
        parser.feed(path.read_text(encoding="utf-8"))
        parser.close()
    except Exception as exc:
        errors.append(f"{rel}: parser failure: {exc}")
        continue
    checked += 1
    if parser.viewport_count > 1:
        errors.append(f"{rel}: duplicate viewport meta tags ({parser.viewport_count})")
    errors.extend(parser.errors)

if errors:
    print("INTERACTION/A11Y CONTRACTS: FAIL")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print(f"INTERACTION/A11Y CONTRACTS: PASS ({checked} tracked public HTML files)")

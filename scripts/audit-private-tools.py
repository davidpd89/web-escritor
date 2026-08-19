#!/usr/bin/env python3
"""Static preflight for manuscript tools that promise browser-local processing.

This intentionally errs on the conservative side. It does not prove security;
it catches regressions that would invalidate the public privacy promise.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

NETWORK_PATTERNS = {
    "fetch": re.compile(r"\bfetch\s*\("),
    "fetchLater": re.compile(r"\bfetchLater\s*\("),
    "XMLHttpRequest": re.compile(r"\bXMLHttpRequest\b"),
    "sendBeacon": re.compile(r"\bsendBeacon\s*\("),
    "WebSocket": re.compile(r"\bWebSocket\s*\("),
    "EventSource": re.compile(r"\bEventSource\s*\("),
}

STORAGE_PATTERNS = {
    "localStorage": re.compile(r"\blocalStorage\b"),
    "sessionStorage": re.compile(r"\bsessionStorage\b"),
    "indexedDB": re.compile(r"\bindexedDB\b"),
    "document.cookie": re.compile(r"\bdocument\.cookie\b"),
    "OPFS": re.compile(r"\bnavigator\.storage\.getDirectory\s*\("),
}

REMOTE_EXECUTABLE = re.compile(
    r"<(?:script|iframe)\b[^>]*(?:src)=[\"'](?:https?:)?//",
    re.IGNORECASE,
)
REMOTE_STYLESHEET = re.compile(
    r"<link\b(?=[^>]*rel=[\"']stylesheet[\"'])[^>]*href=[\"'](?:https?:)?//",
    re.IGNORECASE,
)
CSP_META = re.compile(
    r'<meta\b[^>]*http-equiv=[\"\']Content-Security-Policy[\"\'][^>]*content=\"([^\"]*)\"',
    re.IGNORECASE,
)


def line_for(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def audit_js(path: Path, text: str) -> list[str]:
    failures: list[str] = []
    for label, pattern in {**NETWORK_PATTERNS, **STORAGE_PATTERNS}.items():
        for match in pattern.finditer(text):
            failures.append(f"{path}:L{line_for(text, match.start())}: forbidden {label}")
    if re.search(r"createElement\s*\(\s*[\"']script[\"']\s*\)", text):
        failures.append(f"{path}: dynamic <script> creation requires manual review")
    return failures


def audit_html(path: Path, text: str) -> list[str]:
    failures: list[str] = []
    csp = CSP_META.search(text)
    if not csp:
        failures.append(f"{path}: missing CSP meta")
    else:
        policy = csp.group(1)
        required = ["connect-src 'none'", "script-src 'self'", "form-action 'none'"]
        for directive in required:
            if directive not in policy:
                failures.append(f"{path}: CSP missing {directive}")

    if '/script.js' in text:
        failures.append(f"{path}: loads global /script.js; private tools must use private-tools-shell.js or no chrome script at all")
    # private-tools-shell.js is a convenience shim for pages that keep site
    # chrome (mobile nav, back-to-top). Pages with zero chrome and zero
    # extra scripts satisfy the actual privacy contract (no /script.js, no
    # third-party script) even more strictly than requiring the shell.
    if REMOTE_EXECUTABLE.search(text):
        failures.append(f"{path}: remote executable resource detected")
    if REMOTE_STYLESHEET.search(text):
        failures.append(f"{path}: remote stylesheet detected")
    if re.search(r"<form\b[^>]*\baction\s*=\s*[\"'][^\"']+", text, re.IGNORECASE):
        failures.append(f"{path}: form action detected; private tools must not submit manuscript data")
    return failures


def audit_path(path: Path) -> list[str]:
    if not path.exists():
        return [f"{path}: does not exist"]
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in {'.js', '.mjs'}:
        return audit_js(path, text)
    if suffix in {'.html', '.htm'}:
        return audit_html(path, text)
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs='+', type=Path)
    args = parser.parse_args()

    failures: list[str] = []
    checked = 0
    for path in args.paths:
        if path.is_dir():
            files = [p for p in path.rglob('*') if p.suffix.lower() in {'.js', '.mjs', '.html', '.htm'}]
        else:
            files = [path]
        for file in files:
            checked += 1
            failures.extend(audit_path(file))

    if failures:
        print(f"FAIL — {len(failures)} finding(s) across {checked} file(s)")
        for item in failures:
            print(f"- {item}")
        return 1

    print(f"PASS — {checked} file(s) satisfy the static private-tool preflight")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

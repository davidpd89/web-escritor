#!/usr/bin/env python3
"""Check HTML DOM integrity, accessible references, interactive nesting, and new-tab safety.

Enforces:
1. ID uniqueness: Every id attribute within a document must be unique (WCAG 4.1.1).
2. Label target validity: Every <label for="id"> must point to a declared element id.
3. ARIA reference validity: Every aria-labelledby, aria-describedby, and aria-controls
   reference must resolve to declared element id(s) on the same page.
4. Interactive nesting rules: Prohibits invalid nesting of interactive elements
   (<button> inside <a>, <a> inside <button>, <button> inside <button>, <a> inside <a>).
5. Document language: Every <html> tag must declare a non-empty lang attribute.
6. New-tab safety: Every target="_blank" link must explicitly include rel="noopener".

Usage:
    python scripts/check-dom-integrity.py
"""
from __future__ import annotations

import io
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {
    ".git", ".github", "node_modules", "tests", "scripts", "artifacts",
    ".preview-dist-sitewide-qa", ".preview-dist", ".claude", "tmp", "data",
}

class DomIntegrityParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.html_lang: str | None = None
        self.ids: list[str] = []
        self.labels: list[tuple[str, int]] = []
        self.aria_refs: list[tuple[str, str, int]] = []
        self.tag_stack: list[str] = []
        self.interactive_nesting_errors: list[str] = []
        self.blank_link_errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t = tag.lower()
        attr_dict = {k.lower(): (v or "") for k, v in attrs}
        line_num = self.getpos()[0]

        if t == "html":
            self.html_lang = attr_dict.get("lang")

        id_val = attr_dict.get("id")
        if id_val:
            self.ids.append(id_val.strip())

        if t == "label" and "for" in attr_dict:
            target = attr_dict["for"].strip()
            if target:
                self.labels.append((target, line_num))

        for aria_attr in ("aria-labelledby", "aria-describedby", "aria-controls", "aria-owns", "aria-activedescendant", "aria-details", "headers"):
            if aria_attr in attr_dict:
                for ref_id in attr_dict[aria_attr].split():
                    if ref_id.strip():
                        self.aria_refs.append((aria_attr, ref_id.strip(), line_num))

        # Check interactive nesting (HTML5 spec & WCAG)
        interactive_parents = [parent for parent in self.tag_stack if parent in ("a", "button")]
        if t in ("a", "button", "select", "textarea", "details") and interactive_parents:
            parent = interactive_parents[-1]
            self.interactive_nesting_errors.append(
                f"Line {line_num}: invalid interactive nesting <{t}> inside <{parent}>"
            )

        if t == "input" and attr_dict.get("type", "").lower() != "hidden" and interactive_parents:
            parent = interactive_parents[-1]
            self.interactive_nesting_errors.append(
                f"Line {line_num}: invalid interactive nesting <input> inside <{parent}>"
            )

        if t == "a" and attr_dict.get("target", "").lower() == "_blank":
            rel_tokens = {token.lower() for token in attr_dict.get("rel", "").split()}
            if "noopener" not in rel_tokens:
                href = attr_dict.get("href", "")
                self.blank_link_errors.append(
                    f"Line {line_num}: target='_blank' link is missing rel='noopener' (href={href!r})"
                )

        if not t in ("area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"):
            self.tag_stack.append(t)

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in self.tag_stack:
            while self.tag_stack:
                popped = self.tag_stack.pop()
                if popped == t:
                    break


def check_html_file(path: Path) -> list[str]:
    try:
        rel_path = path.relative_to(ROOT).as_posix()
    except ValueError:
        rel_path = str(path)
    content = path.read_text(encoding="utf-8", errors="ignore")
    parser = DomIntegrityParser()
    parser.feed(content)

    issues: list[str] = []

    if not parser.html_lang or not parser.html_lang.strip():
        issues.append(f"{rel_path}: <html> is missing required lang attribute")

    id_counts = Counter(parser.ids)
    for id_val, count in id_counts.items():
        if count > 1:
            issues.append(f"{rel_path}: duplicate id='{id_val}' (declared {count} times)")

    doc_ids = set(id_counts.keys())

    for target_id, line_num in parser.labels:
        if target_id not in doc_ids:
            issues.append(f"{rel_path} (line {line_num}): <label for='{target_id}'> points to non-existent id")

    for attr, ref_id, line_num in parser.aria_refs:
        if ref_id not in doc_ids:
            issues.append(f"{rel_path} (line {line_num}): {attr}='{ref_id}' points to non-existent id")

    for nesting_err in parser.interactive_nesting_errors:
        issues.append(f"{rel_path}: {nesting_err}")

    for link_err in parser.blank_link_errors:
        issues.append(f"{rel_path}: {link_err}")

    return issues


def check_dom_integrity_sitewide() -> list[str]:
    all_issues: list[str] = []
    for path in ROOT.rglob("*.html"):
        rel_parts = path.relative_to(ROOT).parts
        if any(part in SKIP_PARTS or part.startswith(".preview-dist-") for part in rel_parts):
            continue
        all_issues.extend(check_html_file(path))
    return all_issues


if __name__ == "__main__":
    issues = check_dom_integrity_sitewide()
    if issues:
        print(f"FAIL — {len(issues)} DOM integrity issue(s) detected:")
        for err in issues:
            print(f"- {err}")
        sys.exit(1)
    else:
        print("OK — DOM integrity verified sitewide (IDs, ARIA/labels, interactive nesting, language and new-tab safety).")

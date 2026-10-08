#!/usr/bin/env python3
"""Check HTML DOM integrity: unique IDs, valid ARIA/label references, and non-nested interactives.

Enforces:
1. ID uniqueness: Every id attribute within a document must be unique (WCAG 4.1.1).
2. Label target validity: Every <label for="id"> must point to a declared element id.
3. ARIA reference validity: Every aria-labelledby, aria-describedby, and aria-controls
   reference must resolve to declared element id(s) on the same page.
4. Interactive nesting rules: Prohibits invalid nesting of interactive elements
   (<button> inside <a>, <a> inside <button>, <button> inside <button>, <a> inside <a>).
5. Document language: Every <html> tag must declare a non-empty lang attribute.

Usage:
    python scripts/check-dom-integrity.py
"""
from __future__ import annotations

import io
import re
import sys
from collections import Counter
import subprocess
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

# WHATWG labelable elements; custom form-associated elements are conservatively
# permitted because static HTML cannot prove their JS formAssociated setting.
LABELABLE_TAGS = {"button", "input", "meter", "output", "progress", "select", "textarea"}
ASCII_SPACE_RE = re.compile(r"[ \t\n\r\f]+")


class DomIntegrityParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.html_lang: str | None = None
        self.ids: list[str] = []
        self.id_targets: dict[str, tuple[str, str]] = {}
        self.labels: list[tuple[str, int]] = []
        self.aria_refs: list[tuple[str, str, int]] = []
        self.tag_stack: list[str] = []
        self.interactive_nesting_errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t = tag.lower()
        attr_dict = {k.lower(): (v or "") for k, v in attrs}
        line_num = self.getpos()[0]

        if t == "html":
            self.html_lang = attr_dict.get("lang")

        id_val = attr_dict.get("id")
        if id_val:
            # Preserve exact DOM id value and first target in tree order.
            self.ids.append(id_val)
            self.id_targets.setdefault(id_val, (t, attr_dict.get("type", "").strip().lower()))

        if t == "label" and "for" in attr_dict:
            self.labels.append((attr_dict["for"], line_num))

        for aria_attr in ("aria-labelledby", "aria-describedby", "aria-controls", "aria-owns", "aria-activedescendant", "aria-details", "headers"):
            if aria_attr in attr_dict:
                # IDREF token lists use ASCII whitespace, not arbitrary Unicode spaces.
                for ref_id in ASCII_SPACE_RE.split(attr_dict[aria_attr]):
                    if ref_id:
                        self.aria_refs.append((aria_attr, ref_id, line_num))

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
        if target_id not in parser.id_targets:
            issues.append(f"{rel_path} (line {line_num}): <label for='{target_id}'> points to non-existent id")
            continue
        target_tag, target_type = parser.id_targets[target_id]
        if target_tag == "input" and target_type == "hidden":
            issues.append(
                f"{rel_path} (line {line_num}): <label for='{target_id}'> "
                "points to non-labelable <input type='hidden'>"
            )
        elif target_tag not in LABELABLE_TAGS and "-" not in target_tag:
            issues.append(
                f"{rel_path} (line {line_num}): <label for='{target_id}'> "
                f"points to non-labelable <{target_tag}>"
            )

    for attr, ref_id, line_num in parser.aria_refs:
        if ref_id not in doc_ids:
            issues.append(f"{rel_path} (line {line_num}): {attr}='{ref_id}' points to non-existent id")

    for nesting_err in parser.interactive_nesting_errors:
        issues.append(f"{rel_path}: {nesting_err}")

    return issues



def tracked_html(root: Path) -> list[Path]:
    """Every git-tracked HTML file under `root`.

    rglob() was fine until it wasn't: it also picks up whatever untracked HTML
    a working copy happens to have beside the site (scratch exports, a notes
    folder, a downloaded copy of a page), so the very same commit failed
    locally and passed in CI, where the checkout only ever contains tracked
    files. git ls-files is exactly the set CI sees. Falls back to rglob where
    git is unavailable, so the checker still works outside a clone.
    """
    try:
        listed = subprocess.run(
            ["git", "ls-files", "*.html"],
            cwd=root, capture_output=True, text=True, check=True,
        ).stdout.splitlines()
    except (OSError, subprocess.CalledProcessError):
        return list(root.rglob("*.html"))
    return [root / rel for rel in listed if rel and (root / rel).is_file()]


def check_dom_integrity_sitewide() -> list[str]:
    all_issues: list[str] = []
    for path in tracked_html(ROOT):
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
        print("OK — DOM integrity verified sitewide (IDs unique, ARIA/label references valid, no invalid interactive nesting).")

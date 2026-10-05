#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "content-registry.json"

INTERACTIVE_TAGS = {"a", "button", "input", "select", "textarea"}
ARIA_IDREF_ATTRS = {
    "aria-controls",
    "aria-describedby",
    "aria-details",
    "aria-errormessage",
    "aria-flowto",
    "aria-labelledby",
    "aria-owns",
}
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}


@dataclass
class Node:
    tag: str
    attrs: Dict[str, str]
    line: int
    parent: Optional["Node"] = None
    text: List[str] = field(default_factory=list)
    img_alts: List[str] = field(default_factory=list)

    def accessible_text(self) -> str:
        pieces = [*self.text, *self.img_alts]
        return " ".join(" ".join(pieces).split()).strip()


class AuditParser(HTMLParser):
    def __init__(self, source: Path):
        super().__init__(convert_charrefs=True)
        self.source = source
        self.ids: Dict[str, List[int]] = {}
        self.refs: List[Tuple[str, str, int, str]] = []
        self.labels_for: List[Tuple[str, int]] = []
        self.fragments: List[Tuple[str, int]] = []
        self.nodes: List[Node] = []
        self.stack: List[Node] = []
        self.errors: List[str] = []

    def _attrs(self, attrs) -> Dict[str, str]:
        return {k.lower(): (v or "") for k, v in attrs}

    def _active_interactive_ancestor(self) -> Optional[Node]:
        for node in reversed(self.stack):
            if node.tag in INTERACTIVE_TAGS:
                if node.tag == "a" and not node.attrs.get("href"):
                    continue
                if node.tag == "input" and node.attrs.get("type", "text").lower() == "hidden":
                    continue
                return node
        return None

    def handle_starttag(self, tag: str, attrs):
        tag = tag.lower()
        a = self._attrs(attrs)
        line, _ = self.getpos()
        parent = self.stack[-1] if self.stack else None
        node = Node(tag=tag, attrs=a, line=line, parent=parent)
        self.nodes.append(node)

        element_id = a.get("id", "").strip()
        if element_id:
            self.ids.setdefault(element_id, []).append(line)

        for attr in ARIA_IDREF_ATTRS:
            raw = a.get(attr, "").strip()
            if raw:
                for token in raw.split():
                    self.refs.append((attr, token, line, tag))
        active_desc = a.get("aria-activedescendant", "").strip()
        if active_desc:
            self.refs.append(("aria-activedescendant", active_desc, line, tag))

        if tag == "img":
            alt = a.get("alt", "").strip()
            if alt:
                for ancestor_node in self.stack:
                    ancestor_node.img_alts.append(alt)

        if tag == "label":
            target = a.get("for", "").strip()
            if target:
                self.labels_for.append((target, line))

        if tag == "a":
            href = a.get("href", "").strip()
            if href.startswith("#") and href not in {"#", "#!"}:
                self.fragments.append((unquote(href[1:]), line))

        if tag == "form":
            parent_form = next((n for n in reversed(self.stack) if n.tag == "form"), None)
            if parent_form:
                self.errors.append(
                    f"{self.source}:{line}: nested <form> inside <form> from line {parent_form.line}"
                )

        ancestor = self._active_interactive_ancestor()
        if ancestor and tag in INTERACTIVE_TAGS:
            if not (tag == "input" and a.get("type", "text").lower() == "hidden"):
                if not (tag == "a" and not a.get("href")):
                    self.errors.append(
                        f"{self.source}:{line}: interactive <{tag}> nested inside "
                        f"<{ancestor.tag}> from line {ancestor.line}"
                    )

        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs):
        self.handle_starttag(tag, attrs)
        if self.stack and self.stack[-1].tag == tag.lower():
            self.stack.pop()

    def handle_endtag(self, tag: str):
        tag = tag.lower()
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data: str):
        if not data.strip():
            return
        for node in self.stack:
            node.text.append(data)

    def audit(self) -> List[str]:
        errors = list(self.errors)

        for element_id, lines in sorted(self.ids.items()):
            if len(lines) > 1:
                errors.append(
                    f"{self.source}:{lines[1]}: duplicate id={element_id!r}; "
                    f"first occurrence line {lines[0]}"
                )

        id_set: Set[str] = set(self.ids)
        for attr, target, line, tag in self.refs:
            if target not in id_set:
                errors.append(
                    f"{self.source}:{line}: <{tag}> {attr} references missing id {target!r}"
                )

        for target, line in self.labels_for:
            if target not in id_set:
                errors.append(
                    f"{self.source}:{line}: <label for={target!r}> references missing id"
                )

        for target, line in self.fragments:
            if target and target not in id_set:
                errors.append(
                    f"{self.source}:{line}: same-page fragment #{target} has no matching id"
                )

        for node in self.nodes:
            attrs = node.attrs
            hidden = attrs.get("hidden") != "" or attrs.get("aria-hidden", "").lower() == "true"
            if hidden:
                continue

            if node.tag == "button":
                named = bool(
                    node.accessible_text()
                    or attrs.get("aria-label", "").strip()
                    or attrs.get("aria-labelledby", "").strip()
                    or attrs.get("title", "").strip()
                )
                if not named:
                    errors.append(f"{self.source}:{node.line}: unnamed <button>")

            if node.tag == "a" and attrs.get("href", "").strip():
                named = bool(
                    node.accessible_text()
                    or attrs.get("aria-label", "").strip()
                    or attrs.get("aria-labelledby", "").strip()
                    or attrs.get("title", "").strip()
                )
                if not named:
                    errors.append(
                        f"{self.source}:{node.line}: link with href={attrs.get('href')!r} has no accessible name"
                    )

            is_dialog = node.tag == "dialog" or attrs.get("role", "").lower() in {"dialog", "alertdialog"}
            if is_dialog:
                named = bool(
                    attrs.get("aria-label", "").strip()
                    or attrs.get("aria-labelledby", "").strip()
                    or attrs.get("title", "").strip()
                )
                if not named:
                    errors.append(f"{self.source}:{node.line}: unnamed dialog")

        return errors


def public_html_files() -> List[Path]:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    defaults = payload.get("defaults", {})
    files: List[Path] = []
    seen = set()
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
    if not files:
        raise SystemExit("No public HTML files discovered from content registry")

    errors: List[str] = []
    for path in files:
        parser = AuditParser(path.relative_to(ROOT))
        parser.feed(path.read_text(encoding="utf-8"))
        parser.close()
        errors.extend(parser.audit())

    if errors:
        print(f"FAIL semantic reference integrity: {len(errors)} issue(s) across {len(files)} public HTML files")
        for error in errors[:250]:
            print(error)
        if len(errors) > 250:
            print(f"... {len(errors) - 250} more")
        return 1

    print(f"PASS semantic reference integrity: {len(files)} public HTML files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {rel}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


semantic = load("semantic_guard", "tests/test-public-semantic-references.py")
links = load("link_guard", "tests/test-public-link-contracts.py")


class SemanticGuardTests(unittest.TestCase):
    def audit(self, html: str):
        parser = semantic.AuditParser(Path("fixture.html"))
        parser.feed(html)
        parser.close()
        return parser.audit()

    def test_valid_references_and_names_pass(self):
        self.assertEqual(
            self.audit(
                '<main><h1 id="t">X</h1>'
                '<button aria-labelledby="t">x</button>'
                '<a href="#t">go</a>'
                '<label for="x">X</label><input id="x">'
                '<dialog aria-label="Menu"></dialog></main>'
            ),
            [],
        )

    def test_duplicate_id_fails(self):
        self.assertTrue(any("duplicate id" in e for e in self.audit('<div id="x"></div><p id="x"></p>')))

    def test_broken_aria_reference_fails(self):
        self.assertTrue(any("missing id" in e for e in self.audit('<button aria-controls="missing">Menu</button>')))

    def test_broken_fragment_fails(self):
        self.assertTrue(any("same-page fragment" in e for e in self.audit('<a href="#missing">Ir</a>')))

    def test_nested_form_fails(self):
        self.assertTrue(any("nested <form>" in e for e in self.audit('<form><form></form></form>')))

    def test_unnamed_visible_button_fails(self):
        self.assertTrue(any("unnamed <button>" in e for e in self.audit('<button><svg aria-hidden="true"></svg></button>')))

    def test_hidden_unnamed_button_is_ignored(self):
        self.assertFalse(any("unnamed <button>" in e for e in self.audit('<button hidden></button>')))

    def test_unnamed_link_fails(self):
        self.assertTrue(any("has no accessible name" in e for e in self.audit('<a href="/x/"><svg aria-hidden="true"></svg></a>')))

    def test_img_alt_names_parent_link(self):
        self.assertEqual(self.audit('<a href="/x/"><img src="/x.webp" alt="Portada"></a>'), [])

    def test_unnamed_dialog_fails(self):
        self.assertTrue(any("unnamed dialog" in e for e in self.audit('<dialog><p>Contenido</p></dialog>')))


class LinkGuardTests(unittest.TestCase):
    def audit(self, html: str):
        parser = links.LinkParser(Path("fixture.html"))
        parser.feed(html)
        parser.close()
        return parser.errors

    def test_safe_blank_link_passes(self):
        self.assertEqual(self.audit('<a href="https://example.com" target="_blank" rel="noopener noreferrer">X</a>'), [])

    def test_blank_without_noopener_fails(self):
        self.assertTrue(any("noopener" in e for e in self.audit('<a href="https://example.com" target="_blank">X</a>')))

    def test_blank_without_noreferrer_fails(self):
        self.assertTrue(any("noreferrer" in e for e in self.audit('<a href="https://example.com" target="_blank" rel="noopener">X</a>')))

    def test_javascript_href_fails(self):
        self.assertTrue(any("javascript:" in e for e in self.audit('<a href="javascript:alert(1)">X</a>')))

    def test_insecure_own_origin_fails(self):
        self.assertTrue(any("insecure http" in e for e in self.audit('<a href="http://davidportodiaz.com/x">X</a>')))


if __name__ == "__main__":
    unittest.main()

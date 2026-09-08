#!/usr/bin/env python3
from __future__ import annotations

import html
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit-public-email-exposure.py"

spec = importlib.util.spec_from_file_location("email_audit", SCRIPT)
email_audit = importlib.util.module_from_spec(spec)
assert spec and spec.loader
# dataclasses (via `from __future__ import annotations`) resolves forward
# references by looking the module up in sys.modules; a module built with
# module_from_spec is never registered there on its own, so registering it
# first is required for `@dataclass` in the loaded script to work at all.
sys.modules[spec.name] = email_audit
spec.loader.exec_module(email_audit)


class EmailProtectionAuditTests(unittest.TestCase):
    def test_plaintext_email_is_detected(self):
        text = f'<a href="mailto:{email_audit.AUTHOR_EMAIL}">{email_audit.AUTHOR_EMAIL}</a>'
        kinds = email_audit.inspect_text(text)
        self.assertIn("plaintext_email", kinds)
        self.assertIn("plaintext_mailto", kinds)

    def test_numeric_entity_obfuscation_is_detected(self):
        address = "".join(f"&#{ord(char)};" for char in email_audit.AUTHOR_EMAIL)
        target = "".join(f"&#{ord(char)};" for char in f"mailto:{email_audit.AUTHOR_EMAIL}")
        text = f'<a href="{target}">{address}</a>'
        self.assertEqual(html.unescape(address), email_audit.AUTHOR_EMAIL)
        kinds = email_audit.inspect_text(text)
        self.assertIn("html_entity_email", kinds)
        self.assertIn("html_entity_mailto", kinds)

    def test_interaction_trigger_without_address_is_safe(self):
        text = (
            '<a href="/prensa.html#contacto" data-email-reveal '
            'data-email-subject="Entrevista">Mostrar correo</a>'
        )
        self.assertEqual(email_audit.inspect_text(text), set())

    def test_tree_scan_ignores_docs_but_scans_public_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "example.md").write_text(email_audit.AUTHOR_EMAIL, encoding="utf-8")
            (root / "index.html").write_text(
                f"Contacto: {email_audit.AUTHOR_EMAIL}", encoding="utf-8"
            )
            findings = email_audit.scan_tree(root)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].path, "index.html")
            self.assertEqual(findings[0].kind, "plaintext_email")


if __name__ == "__main__":
    unittest.main()

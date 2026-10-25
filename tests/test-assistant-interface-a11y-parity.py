#!/usr/bin/env python3
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class AssistantAccessibilityParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.standalone = (ROOT / 'asistente/index.html').read_text(encoding='utf-8')
        cls.embed = (ROOT / 'asistente/embed.html').read_text(encoding='utf-8')
        cls.upgrade = (ROOT / 'assets/assistant.js').read_text(encoding='utf-8')

    def test_document_languages(self):
        for document in (self.standalone, self.embed):
            self.assertRegex(document, r'<html\b[^>]*\blang=[\'\"]es[\'\"]')

    def test_embed_semantics(self):
        html = self.embed
        for marker in ('data-assistant-log', 'data-assistant-form', 'data-assistant-query', 'data-assistant-submit', 'data-assistant-stop', 'data-assistant-status'):
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertRegex(html, r'<h1\b')
        self.assertRegex(html, r'role=[\'\"]log[\'\"]')
        self.assertRegex(html, r'role=[\'\"]status[\'\"]')
        self.assertRegex(html, r'<label\b[^>]*for=[\'\"]assistant-query[\'\"]')

    def test_standalone_upgrade_contract(self):
        js = self.upgrade
        for marker in ('data.assistantLog', 'data.assistantForm', 'data.assistantQuery', 'data.assistantSubmit', 'data.assistantStop', 'data.assistantStatus'):
            with self.subTest(marker=marker):
                self.assertIn(marker, js)
        self.assertIn('aria-live', js)
        self.assertIn('aria-label', js)
        self.assertIn('role', js)

    def test_embed_no_duplicate_query_id(self):
        ids = re.findall(r'\bid=[\'\"]assistant-query[\'\"]', self.embed)
        self.assertEqual(len(ids), 1)

if __name__ == '__main__':
    unittest.main()
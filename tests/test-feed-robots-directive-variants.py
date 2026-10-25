#!/usr/bin/env python3
"""Variantes de robots relevantes para la selección de artículos."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_robots_qa', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class RobotsDirectiveVariants(unittest.TestCase):
    def test_noindex_variants(self):
        cases = [
            ('noindex', True),
            ('NOINDEX', True),
            ('index, noindex, follow', True),
            ('max-snippet:-1, noindex', True),
            ('index, follow', False),
            ('noarchive, nosnippet', False),
            ('noindexing', False),
        ]
        for value, expected in cases:
            with self.subTest(value=value):
                html = '<meta name="robots" content="' + value + '">'
                self.assertEqual(feed.is_noindex(html), expected)

    def test_multiple_robots_tags(self):
        html = '<meta name="robots" content="follow"><meta name="robots" content="noindex">'
        self.assertTrue(feed.is_noindex(html))

    def test_attribute_order(self):
        html = '<meta content="noindex,follow" name="robots">'
        self.assertTrue(feed.is_noindex(html))

if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python3
"""Matriz de directivas robots para el generador RSS."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_robots_qa', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class FeedRobotsMatrix(unittest.TestCase):
    def test_robots_directives(self):
        cases = [
            ('noindex', True),
            ('NOINDEX', True),
            ('index, noindex', True),
            ('nofollow, noindex, noarchive', True),
            ('noindex,follow', True),
            ('index, follow', False),
            ('nofollow', False),
            ('noarchive', False),
            ('max-snippet:0', False),
        ]
        for directives, expected in cases:
            with self.subTest(directives=directives):
                html = '<html><head><meta name="robots" content="' + directives + '"></head></html>'
                self.assertEqual(feed.is_noindex(html), expected)

    def test_unrelated_meta_does_not_exclude(self):
        html = '<meta name="description" content="noindex"><meta name="robots" content="index">'
        self.assertFalse(feed.is_noindex(html))

    def test_multiple_robots_tags_cannot_cancel_noindex(self):
        html = '<meta name="robots" content="noindex"><meta name="robots" content="index,follow">'
        self.assertTrue(feed.is_noindex(html))

if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python3
"""Clasificación de grafos JSON-LD para inclusión en RSS."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_graph_qa', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class FeedGraphTypeMatrix(unittest.TestCase):
    def test_graph_classification(self):
        cases = [
            ([{'@type': 'CollectionPage'}], True),
            ([{'@type': ['WebPage', 'CollectionPage']}], True),
            ([{'@type': 'CollectionPage'}, {'@type': 'BreadcrumbList'}], True),
            ([{'@type': 'Article'}], False),
            ([{'@type': 'BlogPosting'}], False),
            ([{'@type': ['WebPage', 'Article']}], False),
            ([{'@type': 'CollectionPage'}, {'@type': 'Article'}], False),
            ([{'@type': 'CollectionPage'}, {'@type': ['WebPage', 'NewsArticle']}], False),
        ]
        for graph, expected in cases:
            with self.subTest(graph=graph):
                self.assertEqual(feed.is_non_article_page({'@graph': graph}), expected)

    def test_malformed_graph_does_not_raise(self):
        for graph in (None, {}, 'invalid', [None, 'invalid', 42]):
            with self.subTest(graph=graph):
                self.assertFalse(feed.is_non_article_page({'@graph': graph}))

if __name__ == '__main__':
    unittest.main()

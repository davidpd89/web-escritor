#!/usr/bin/env python3
"""Compatibilidad de tipos múltiples en datos estructurados."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_multitype_qa', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class MultipleArticleTypes(unittest.TestCase):
    def test_multitype_article(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'index.html'
            for types in (['Article', 'BlogPosting'], ['WebPage', 'Article'], ['NewsArticle', 'Article']):
                with self.subTest(types=types):
                    data = {'@graph': [{'@type': types, 'headline': 'Título válido', 'url': 'https://davidportodiaz.com/cuaderno/prueba/', 'datePublished': '2026-10-20', 'description': 'Texto descriptivo'}]}
                    path.write_text('<script type="application/ld+json">' + json.dumps(data) + '</script>', encoding='utf-8')
                    result = feed.extract_metadata(str(path))
                    self.assertFalse(result['skip'])
                    self.assertEqual(result['title'], 'Título válido')
                    self.assertEqual(result['date'], '2026-10-20')
                    self.assertEqual(result['description'], 'Texto descriptivo')

if __name__ == '__main__':
    unittest.main()

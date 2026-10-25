#!/usr/bin/env python3
"""Regresión para páginas con varios scripts JSON-LD."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_multiple_scripts_qa', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class MultipleJsonLdScripts(unittest.TestCase):
    def test_article_after_organization(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'index.html'
            organization = {'@context': 'https://schema.org', '@type': 'Organization', 'name': 'Editorial'}
            article = {'@context': 'https://schema.org', '@graph': [{'@type': 'Article', 'headline': 'Título artículo', 'url': 'https://davidportodiaz.com/cuaderno/prueba/', 'datePublished': '2026-10-21', 'description': 'Descripción artículo'}]}
            html = '<html><head><title>Título fallback</title>'
            for block in (organization, article):
                html += '<script type="application/ld+json">' + json.dumps(block, ensure_ascii=False) + '</script>'
            html += '</head><body></body></html>'
            path.write_text(html, encoding='utf-8')
            actual = feed.extract_metadata(str(path))
            self.assertEqual(actual['title'], 'Título artículo')
            self.assertEqual(actual['date'], '2026-10-21')
            self.assertEqual(actual['url'], article['@graph'][0]['url'])

if __name__ == '__main__':
    unittest.main()

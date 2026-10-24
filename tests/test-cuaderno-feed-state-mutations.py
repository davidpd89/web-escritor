import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('cuaderno_build_feed', ROOT / 'scripts/build-feed.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class FeedMutations(unittest.TestCase):
    def metadata(self, kind='Article', robots='index, follow', published='2026-05-26', modified='2026-10-20'):
        node = {
            '@type': kind, 'headline': 'Artículo de prueba',
            'url': 'https://davidportodiaz.com/cuaderno/fixture/',
            'datePublished': published, 'dateModified': modified,
            'description': 'Contenido editorial de prueba'
        }
        html = ('<html><head><title>Prueba</title>'
                f'<meta name="robots" content="{robots}">'
                '<link rel="canonical" href="https://davidportodiaz.com/cuaderno/fixture/">'
                f'<script type="application/ld+json">{json.dumps({"@graph": [node]})}</script>'
                '</head><body><main><article>Texto</article></main></body></html>')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'index.html'
            path.write_text(html, encoding='utf-8')
            return MODULE.extract_metadata(str(path))

    def test_article_keeps_publication_date(self):
        old = self.metadata(modified='2026-06-01')
        new = self.metadata(modified='2026-10-20')
        self.assertFalse(old['skip'])
        self.assertEqual(old['date'], '2026-05-26')
        self.assertEqual(new['date'], old['date'])

    def test_noindex_excludes_article(self):
        result = self.metadata(robots='noindex, follow')
        self.assertTrue(result['skip'])

    def test_collection_is_not_an_article(self):
        result = self.metadata(kind='CollectionPage')
        self.assertTrue(result['skip'])

    def test_modified_date_fallback_when_unpublished(self):
        result = self.metadata(published='', modified='2026-10-20')
        self.assertEqual(result['date'], '2026-10-20')

if __name__ == '__main__':
    unittest.main()

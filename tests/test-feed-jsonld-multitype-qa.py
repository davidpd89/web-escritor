import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_multitype_qa', ROOT / 'scripts/build-feed.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class FeedMultitype(unittest.TestCase):
    def test_article_metadata_survives_multitype(self):
        article = {
            '@type': ['WebPage', 'Article'],
            'headline': 'Artículo de prueba',
            'url': 'https://davidportodiaz.com/cuaderno/prueba/',
            'datePublished': '2026-10-20T10:00:00+02:00'
        }
        html = '<html><head><script type="application/ld+json">' + json.dumps({'@graph': [article]}) + '</script></head></html>'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'index.html'
            path.write_text(html, encoding='utf-8')
            metadata = mod.extract_metadata(str(path))
        self.assertEqual(metadata['title'], article['headline'])
        self.assertEqual(metadata['url'], article['url'])
        self.assertEqual(metadata['date'], article['datePublished'])

if __name__ == '__main__':
    unittest.main()
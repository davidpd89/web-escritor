import importlib.util
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_language', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class LanguageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.language = None
    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'html' and self.language is None:
            self.language = dict(attrs).get('lang')

class FeedArticleLanguageTests(unittest.TestCase):
    def test_published_articles_declare_spanish(self):
        items, _ = feed.collect_items()
        self.assertTrue(items, 'cuaderno/feed.xml: no hay artículos para comprobar idioma')
        for item in items:
            with self.subTest(page=item['path']):
                parser = LanguageParser()
                parser.feed(Path(item['path']).read_text(encoding='utf-8'))
                parser.close()
                lang = (parser.language or '').lower()
                self.assertTrue(lang == 'es' or lang.startswith('es-'), f"{item['path']}: idioma HTML {parser.language!r}; esperado español")

if __name__ == '__main__':
    unittest.main()
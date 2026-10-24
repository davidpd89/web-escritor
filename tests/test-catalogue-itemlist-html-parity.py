from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

class Cards(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'li' and 'data-catalogue-book' in a:
            self.current = {'id': a.get('data-book-id'), 'href': None}
            self.cards.append(self.current)
        elif tag == 'a' and self.current:
            if 'catalogue-card__cover' in (a.get('class') or '').split():
                self.current['href'] = a.get('href')

class ItemListParity(unittest.TestCase):
    def test_structured_list_matches_visible_catalogue(self):
        html = (ROOT / 'recomendaciones/index.html').read_text(encoding='utf-8')
        scripts = re.findall(r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S)
        payloads = [json.loads(s) for s in scripts]
        lists = [p for p in payloads if p.get('@type') == 'ItemList']
        self.assertEqual(len(lists), 1)
        data = lists[0]
        items = data['itemListElement']
        parser = Cards()
        parser.feed(html)
        hrefs = [c['href'] for c in parser.cards]
        structured = [urlparse(i['item']['url']).path for i in items]
        self.assertGreater(len(hrefs), 50)
        self.assertEqual(data['numberOfItems'], len(items))
        self.assertEqual(len(items), len(parser.cards))
        self.assertEqual([i['position'] for i in items], list(range(1, len(items) + 1)))
        self.assertEqual(len(hrefs), len(set(hrefs)), 'Fichas HTML duplicadas')
        self.assertEqual(len(structured), len(set(structured)), 'URLs SEO duplicadas')
        self.assertEqual(hrefs, structured, 'La secuencia HTML no coincide con la secuencia estructurada')
        for item in items:
            self.assertEqual(item['item']['@type'], 'Book')
            self.assertTrue(item['item'].get('name'))

if __name__ == '__main__':
    unittest.main()
#!/usr/bin/env python3
"""Compara datos de preservación contra scaffolds sin acceso a red."""
from html.parser import HTMLParser
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1] / 'lab' / 'diseno-home-v1'

class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.text = []
        self.attrs = []
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        self.attrs.append(values)
        if values.get('id'):
            self.ids.add(values['id'])
    def handle_data(self, data):
        self.text.append(data)

def load(name):
    return json.loads((ROOT / 'data' / name).read_text(encoding='utf-8'))

def doc(name):
    parser = Document()
    parser.feed((ROOT / name).read_text(encoding='utf-8'))
    return parser

book = load('manecillas-preservation.json')['preserve']
book_page = doc('book-manecillas.html')
body_text = ' '.join(book_page.text)
for value in [book['book_facts']['name'], book['book_facts']['publisher'], book['book_facts']['isbn'], str(book['book_facts']['numberOfPages']), book['book_facts']['priceVisible']]:
    assert value in body_text, f'Manecillas: missing editorial fact {value}'
for fragment in book['deep_links']:
    assert fragment in book_page.ids, f'Manecillas: missing deep link #{fragment}'
for marker in book['functional_hooks_first_migration']:
    if marker.startswith('source:'):
        assert any(a.get('data-newsletter-source') == marker.split(':', 1)[1] for a in book_page.attrs)
    else:
        assert marker in book_page.ids, f'Manecillas: missing hook {marker}'
article = load('article-preservation.json')
article_page = doc('article-pilot.html')
assert article['seo']['h1'] in ' '.join(article_page.text)
for fragment in article['anchors']:
    assert fragment in article_page.ids, f'Article: missing #{fragment}'
for key in ['newsletter_form_id', 'newsletter_email_id', 'newsletter_consent_id', 'newsletter_status_id']:
    value = article['functional'][key]
    assert value in article_page.ids, f'Article: missing functional id {value}'
assert any(a.get('data-newsletter-source') == article['functional']['newsletter_source'] for a in article_page.attrs)
home = load('home-preservation.json')
home_page = doc('index.html')
assert home['manecillas_facts']['publisher'] in ' '.join(home_page.text)
assert home['manecillas_facts']['datePublished'] in (ROOT / 'index.html').read_text(encoding='utf-8')
print('PASS lab preservation drift')

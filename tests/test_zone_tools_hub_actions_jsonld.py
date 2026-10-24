import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = json.loads((ROOT / 'data/tools-hub.json').read_text(encoding='utf-8'))
page = (ROOT / 'herramientas/index.html').read_text(encoding='utf-8')

class LD(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.docs = []
        self.buf = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type') == 'application/ld+json':
            self.active = True
            self.buf = []

    def handle_data(self, value):
        if self.active:
            self.buf.append(value)

    def handle_endtag(self, tag):
        if tag == 'script' and self.active:
            self.docs.append(json.loads(''.join(self.buf)))
            self.active = False

parsed = LD()
parsed.feed(page)
entries = []

def walk(value):
    if isinstance(value, dict):
        if value.get('@type') == 'ItemList':
            entries.extend(value.get('itemListElement', []))
        for child in value.values():
            walk(child)
    elif isinstance(value, list):
        for child in value:
            walk(child)

for doc in parsed.docs:
    walk(doc)
urls = [item.get('url') for item in entries]
for row in source['tools']:
    href = row['href']
    title = html.escape(row['name'])
    assert re.search(r'<h3><a href="' + re.escape(href) + '">' + re.escape(title) + r'</a></h3>', page), row['slug']
    assert 'href="' + href + '">Abrir herramienta</a>' in page, row['slug']
    assert urls.count('https://davidportodiaz.com' + href) == 1, row['slug']
assert len(urls) == len(source['tools'])
print('tools hub actions ItemList: OK')

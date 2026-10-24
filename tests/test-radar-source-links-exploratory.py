from __future__ import annotations
import html
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = set()
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            href = dict(attrs).get('href')
            if href:
                self.hrefs.add(html.unescape(href))

raw = json.loads((ROOT / 'data/radar-opportunities.json').read_text(encoding='utf-8'))
page = ROOT / 'convocatorias-escritores/index.html'
parser = Links()
parser.feed(page.read_text(encoding='utf-8'))
items = [item for item in raw['items'] if item.get('published') is True]
assert items
missing = [(item['id'], item['source_url']) for item in items if item['source_url'] not in parser.hrefs]
assert not missing, f'Fuentes oficiales sin enlace HTML: {missing}'
print(f'radar source links: OK ({len(items)} convocatorias)')

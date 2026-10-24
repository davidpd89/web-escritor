from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
class Inspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])

pages = {}
for name in ('eventos.html', 'ferias.html'):
    parser = Inspector()
    parser.feed((ROOT / name).read_text(encoding='utf-8'))
    pages[name] = parser
checked = 0
for origin, parser in pages.items():
    for href in parser.links:
        url = urlsplit(href)
        if not url.fragment:
            continue
        target = url.path.lstrip('/') or origin
        if target not in pages:
            continue
        assert url.fragment in pages[target].ids, f'{origin}: fragmento roto {href}'
        checked += 1
assert checked > 0, 'No se encontraron enlaces entre páginas con fragmentos verificables'
print(f'eventos/ferias cross-links: OK ({checked} fragmentos)')

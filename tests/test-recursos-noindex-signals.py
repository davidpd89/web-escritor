from html.parser import HTMLParser
from pathlib import Path
import json
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ROUTE = '/recursos/herramientas-para-escritores/'
EXPECTED = 'https://davidportodiaz.com' + ROUTE

class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = []
        self.links = []
        self.schemas = []
        self.script = False
        self.buffer = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta':
            self.meta.append(a)
        if tag == 'link':
            self.links.append(a)
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.script = True
            self.buffer = []

    def handle_data(self, data):
        if self.script:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.script:
            self.schemas.append(json.loads(''.join(self.buffer)))
            self.script = False

p = Document()
p.feed((ROOT / ROUTE.lstrip('/') / 'index.html').read_text(encoding='utf-8'))
robots = [m['content'] for m in p.meta if m.get('name', '').lower() == 'robots']
assert len(robots) == 1, f'{ROUTE}: robots={robots}'
tokens = {x.strip().lower() for x in robots[0].split(',')}
assert 'noindex' in tokens and 'index' not in tokens, f'{ROUTE}: robots contradictorio {robots}'
canon = [x['href'] for x in p.links if 'canonical' in x.get('rel', '').lower().split()]
assert canon == [EXPECTED], f'{ROUTE}: canonical={canon}'
collections = [s for s in p.schemas if 'CollectionPage' in ([s.get('@type')] if isinstance(s.get('@type'), str) else s.get('@type', []))]
assert len(collections) == 1, f'{ROUTE}: CollectionPage={len(collections)}'
assert collections[0].get('url') == EXPECTED, f'{ROUTE}: CollectionPage.url={collections[0].get("url")}'
assert urlsplit(EXPECTED).scheme == 'https'
print('OK: señales noindex y canonical coherentes')
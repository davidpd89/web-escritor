import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['mapa-del-sitio/index.html', 'empieza-aqui/index.html']

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = []
        self.og = []
        self.scripts = []
        self.in_json = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonical.append(a.get('href'))
        if tag == 'meta' and a.get('property') == 'og:url':
            self.og.append(a.get('content'))
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.in_json = True
            self.scripts.append('')

    def handle_data(self, data):
        if self.in_json:
            self.scripts[-1] += data

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_json = False

for page in PAGES:
    parser = Metadata()
    parser.feed((ROOT / page).read_text(encoding='utf-8'))
    assert len(parser.canonical) == 1, f'{page}: canonical duplicada o ausente'
    assert len(parser.og) == 1, f'{page}: og:url duplicada o ausente'
    canonical = parser.canonical[0]
    assert canonical == parser.og[0], f'{page}: canonical != og:url'
    found = []
    for raw in parser.scripts:
        data = json.loads(raw)
        nodes = data.get('@graph', [data]) if isinstance(data, dict) else data
        for node in nodes:
            if not isinstance(node, dict):
                continue
            kinds = node.get('@type', [])
            if isinstance(kinds, str):
                kinds = [kinds]
            if any(kind in ('WebPage', 'CollectionPage') for kind in kinds) and 'url' in node:
                found.append(node['url'])
    assert found, f'{page}: no hay identidad de página en JSON-LD'
    assert all(url == canonical for url in found), f'{page}: identidad JSON-LD divergente: {found}'
print('navigation-social-canonical-parity: OK')

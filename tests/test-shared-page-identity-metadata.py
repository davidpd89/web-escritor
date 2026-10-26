import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['accesibilidad/index.html', 'mapa-del-sitio/index.html', 'recomendaciones/index.html']

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.canonical = None
        self.scripts = []
        self.collect = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta':
            key = a.get('property') or a.get('name')
            if key:
                self.meta[key] = a.get('content')
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonical = a.get('href')
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.collect = True
            self.scripts.append('')

    def handle_data(self, data):
        if self.collect:
            self.scripts[-1] += data

    def handle_endtag(self, tag):
        if tag == 'script':
            self.collect = False

def objects(value):
    if isinstance(value, list):
        for item in value:
            yield from objects(item)
    elif isinstance(value, dict):
        yield value
        if '@graph' in value:
            yield from objects(value['@graph'])

for path in PAGES:
    p = Page()
    p.feed((ROOT / path).read_text(encoding='utf-8'))
    assert p.canonical, f'{path}: falta canonical'
    assert p.meta.get('og:url') == p.canonical, f'{path}: og:url {p.meta.get("og:url")!r} != {p.canonical!r}'
    assert p.meta.get('og:locale') == 'es_ES', f'{path}: locale {p.meta.get("og:locale")!r}'
    assert p.meta.get('og:site_name') == 'David Porto Díaz', f'{path}: site_name {p.meta.get("og:site_name")!r}'
    for script in p.scripts:
        for obj in objects(json.loads(script)):
            types = obj.get('@type', [])
            if isinstance(types, str):
                types = [types]
            if any(t in types for t in ('WebPage', 'CollectionPage')):
                url = obj.get('url')
                if url:
                    assert url == p.canonical, f'{path}: JSON-LD url {url!r} != canonical {p.canonical!r}'
                identifier = obj.get('@id')
                if identifier and identifier.startswith('https://davidportodiaz.com/') and identifier.endswith('#page'):
                    assert identifier == p.canonical + '#page', f'{path}: @id {identifier!r} != canonical#page'
print('shared-page-identity-metadata: OK')

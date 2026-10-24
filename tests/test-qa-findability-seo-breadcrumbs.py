import json
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://davidportodiaz.com'
PAGES = ['mapa-del-sitio', 'empieza-aqui']

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonicals = []
        self.og_urls = []
        self.scripts = []
        self.in_json = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonicals.append(a.get('href'))
        if tag == 'meta' and a.get('property') == 'og:url':
            self.og_urls.append(a.get('content'))
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.in_json = True
            self.scripts.append('')
    def handle_data(self, data):
        if self.in_json:
            self.scripts[-1] += data
    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_json = False

def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk(value)

for slug in PAGES:
    p = Parser()
    p.feed((ROOT / slug / 'index.html').read_text(encoding='utf-8'))
    expected = f'{BASE}/{slug}/'
    assert p.canonicals == [expected], f'{slug}: canonical incorrecto'
    assert p.og_urls == [expected], f'{slug}: og:url incorrecto'
    nodes = [node for raw in p.scripts for node in walk(json.loads(raw))]
    crumbs = [node for node in nodes if node.get('@type') == 'BreadcrumbList']
    assert crumbs, f'{slug}: faltan breadcrumbs JSON-LD'
    assert any(c.get('itemListElement', [])[-1].get('item') == expected for c in crumbs if c.get('itemListElement')), f'{slug}: último breadcrumb incorrecto'
    pages = [node for node in nodes if node.get('@type') in ('WebPage', 'CollectionPage')]
    assert any(node.get('url') == expected for node in pages), f'{slug}: URL de página estructurada incorrecta'
print('findability-seo-breadcrumbs: OK')
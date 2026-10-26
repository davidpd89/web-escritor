import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['mapa-del-sitio/index.html', 'accesibilidad/index.html', 'recomendaciones/index.html']

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = None
        self.scripts = []
        self.collect = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
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

def nodes(value):
    if isinstance(value, list):
        for item in value:
            yield from nodes(item)
    elif isinstance(value, dict):
        yield value
        if '@graph' in value:
            yield from nodes(value['@graph'])

checked = 0
for page in PAGES:
    meta = Metadata()
    meta.feed((ROOT / page).read_text(encoding='utf-8'))
    assert meta.canonical, f'{page}: falta canonical'
    for script in meta.scripts:
        data = json.loads(script)
        for obj in nodes(data):
            if 'BreadcrumbList' not in ([obj.get('@type')] if isinstance(obj.get('@type'), str) else obj.get('@type', [])):
                continue
            items = obj.get('itemListElement', [])
            assert items, f'{page}: BreadcrumbList vacío'
            positions = [x.get('position') for x in items]
            assert positions == list(range(1, len(items) + 1)), f'{page}: posiciones {positions}'
            for item in items:
                assert item.get('name'), f'{page}: miga sin nombre: {item}'
                target = item.get('item') or item.get('url')
                if isinstance(target, dict):
                    target = target.get('@id') or target.get('url')
                assert isinstance(target, str) and urlparse(target).scheme == 'https', f'{page}: destino inválido {target!r}'
            last = items[-1].get('item') or items[-1].get('url')
            if isinstance(last, dict):
                last = last.get('@id') or last.get('url')
            assert last == meta.canonical, f'{page}: última miga {last!r} != canonical {meta.canonical!r}'
            checked += 1
assert checked > 0, 'No se encontraron BreadcrumbList en las páginas examinadas'
print(f'shared-breadcrumb-jsonld-contract: OK ({checked})')

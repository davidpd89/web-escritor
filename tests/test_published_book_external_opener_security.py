import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://davidportodiaz.com'

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs))

catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
checked_pages = 0
checked_external = 0
for book in catalogue['libros']:
    if book['estado'] != 'publicado':
        continue
    path = ROOT / 'recomendaciones/libros' / book['slug'] / 'index.html'
    assert path.is_file(), f'{path}: ficha publicada ausente'
    parser = Links()
    parser.feed(path.read_text(encoding='utf-8'))
    for link in parser.links:
        href = link.get('href', '')
        if not href:
            continue
        assert not href.strip().lower().startswith('javascript:'), f'{path}: enlace ejecutable {href!r}'
        resolved = urlsplit(urljoin(ORIGIN + '/', href))
        if resolved.scheme not in ('http', 'https') or resolved.hostname == 'davidportodiaz.com':
            continue
        checked_external += 1
        if link.get('target', '').lower() == '_blank':
            rel = set(link.get('rel', '').lower().split())
            assert rel.intersection({'noopener', 'noreferrer'}), f'{path}: enlace externo {href!r} con target=_blank sin aislamiento de opener'
    checked_pages += 1
assert checked_pages > 0, 'No se analizaron fichas publicadas'
assert checked_external > 0, 'No se analizaron enlaces externos reales'
print(f'PASS: {checked_external} enlaces externos en {checked_pages} fichas')

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'accesibilidad/index.html', 'mapa-del-sitio/index.html']

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.manifests = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link' and 'manifest' in a.get('rel', '').split():
            self.manifests.append(a.get('href'))

paths = set()
for page in PAGES:
    parser = Links()
    parser.feed((ROOT / page).read_text(encoding='utf-8'))
    assert len(parser.manifests) == 1, f'{page}: {len(parser.manifests)} manifiestos'
    href = parser.manifests[0]
    parsed = urlsplit(href)
    assert not parsed.netloc and parsed.path.startswith('/'), f'{page}: manifiesto no local {href!r}'
    target = ROOT / parsed.path.lstrip('/')
    assert target.is_file(), f'{page}: manifiesto inexistente {href!r}'
    data = json.loads(target.read_text(encoding='utf-8'))
    assert isinstance(data, dict), f'{page}: manifiesto no es objeto JSON'
    assert data.get('name') or data.get('short_name'), f'{page}: manifiesto sin nombre'
    assert data.get('start_url'), f'{page}: manifiesto sin start_url'
    paths.add(parsed.path)
assert len(paths) == 1, f'Manifiestos diferentes entre páginas: {sorted(paths)}'
print('shared-manifest-discovery-contract: OK')

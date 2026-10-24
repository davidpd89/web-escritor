#!/usr/bin/env python3
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://davidportodiaz.com'

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = set()
    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return
        href = dict(attrs).get('href', '')
        url = urlsplit(urljoin(ORIGIN + '/mapa-del-sitio/', href))
        if url.scheme == 'https' and url.netloc == 'davidportodiaz.com':
            self.urls.add(url.path)

parser = Links()
parser.feed((ROOT / 'mapa-del-sitio/index.html').read_text(encoding='utf-8'))
raw = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
errors = []
checked = 0
for item in raw['entries']:
    entry = {**raw.get('defaults', {}), **item}
    if entry['status'] != 'public' or entry.get('discoverability') not in {'primary', 'secondary'}:
        continue
    if not entry.get('sourceFile', '').endswith('.html'):
        continue
    checked += 1
    url = urlsplit(entry['url']).path
    if url not in parser.urls:
        errors.append(f'{entry["id"]}: falta enlace a {url}')
assert checked > 5, 'No se han encontrado rutas descubribles'
assert not errors, '\n'.join(errors[:100])
print(f'OK mapa visual: {checked} rutas examinadas')

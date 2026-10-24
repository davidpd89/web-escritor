#!/usr/bin/env python3
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://davidportodiaz.com'
EXT = {'.css', '.js', '.mjs', '.json', '.svg', '.woff2'}

class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag in {'script', 'img', 'source', 'iframe'} and d.get('src'):
            self.values.append(d['src'])
        if tag == 'link' and d.get('href'):
            self.values.append(d['href'])

registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
missing = []
examined = 0
for raw in registry['entries']:
    entry = {**registry.get('defaults', {}), **raw}
    file = entry.get('sourceFile', '')
    if entry['status'] != 'public' or not file.endswith('.html') or not (ROOT / file).is_file():
        continue
    parser = Resources()
    parser.feed((ROOT / file).read_text(encoding='utf-8'))
    for href in parser.values:
        url = urlsplit(urljoin(ORIGIN + entry['url'], href))
        if url.netloc != 'davidportodiaz.com':
            continue
        local = Path(unquote(url.path).lstrip('/'))
        if local.suffix.lower() not in EXT:
            continue
        examined += 1
        if '..' in local.parts or not (ROOT / local).is_file():
            missing.append(f'{file}: {href}')
assert examined > 50, 'No se han encontrado suficientes dependencias'
assert not missing, '\n'.join(missing[:150])
print(f'OK recursos locales: {examined} referencias')

#!/usr/bin/env python3
"""Audita referencias estáticas reales del mapa del sitio."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'mapa-del-sitio/index.html'
MAX_SOCIAL_IMAGE = 2 * 1024 * 1024

class ResourceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.resources = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in {'img', 'script'} and a.get('src'):
            self.resources.append((tag, a['src']))
        if tag == 'link' and 'preload' in a.get('rel', '').lower().split() and a.get('href'):
            self.resources.append(('preload', a['href']))
        if tag == 'meta' and a.get('property') in {'og:image', 'og:image:secure_url'}:
            self.resources.append(('social-image', a.get('content', '')))
        if tag == 'meta' and a.get('name') == 'twitter:image':
            self.resources.append(('social-image', a.get('content', '')))

parser = ResourceParser()
parser.feed(PAGE.read_text(encoding='utf-8'))
assert parser.resources, f'{PAGE}: no se encontraron recursos para auditar'

errors = []
checked = set()
for kind, url in parser.resources:
    parsed = urlsplit(url)
    if parsed.scheme and parsed.scheme not in {'http', 'https'}:
        continue
    if parsed.netloc and parsed.netloc.lower() not in {'davidportodiaz.com', 'www.davidportodiaz.com'}:
        continue
    resource = unquote(parsed.path)
    if not resource.startswith('/'):
        continue
    target = ROOT / resource.lstrip('/')
    key = (kind, resource)
    if key in checked:
        continue
    checked.add(key)
    if not target.is_file():
        errors.append(f'{PAGE}: {kind} {url}: archivo inexistente')
        continue
    size = target.stat().st_size
    if size == 0:
        errors.append(f'{PAGE}: {kind} {url}: archivo vacío')
    if kind == 'social-image' and size > MAX_SOCIAL_IMAGE:
        errors.append(
            f'{PAGE}: imagen social {url}: {size} bytes, '
            f'máximo {MAX_SOCIAL_IMAGE}'
        )

assert not errors, '\n'.join(errors)
print(f'PASS: {len(checked)} referencias de recursos verificadas')

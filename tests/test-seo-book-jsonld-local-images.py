#!/usr/bin/env python3
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'davidportodiaz.com'
SCRIPT = re.compile(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.I | re.S)
errors = []
checked = 0

def images(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from images(item)
    elif isinstance(value, dict):
        if isinstance(value.get('url'), str):
            yield value['url']
        if isinstance(value.get('contentUrl'), str):
            yield value['contentUrl']

for page in sorted((ROOT / 'recomendaciones/libros').glob('*/index.html')):
    html = page.read_text(encoding='utf-8')
    for block in SCRIPT.findall(html):
        document = json.loads(block)
        for node in document.get('@graph', [document]):
            if not isinstance(node, dict) or 'Book' not in [node.get('@type')] + (node.get('@type') if isinstance(node.get('@type'), list) else []):
                continue
            for url in images(node.get('image')):
                parsed = urlsplit(url)
                if parsed.hostname != ORIGIN:
                    continue
                checked += 1
                target = (ROOT / unquote(parsed.path).lstrip('/')).resolve()
                if not target.is_relative_to(ROOT.resolve()) or not target.is_file() or target.stat().st_size < 200:
                    errors.append(f'{page.relative_to(ROOT)}: imagen JSON-LD inexistente o vacía: {url}')

assert checked >= 8, f'Cobertura de imágenes estructuradas demasiado pequeña: {checked}'
assert not errors, '\n'.join(errors)
print(f'OK: {checked} imágenes locales de Book JSON-LD verificadas')

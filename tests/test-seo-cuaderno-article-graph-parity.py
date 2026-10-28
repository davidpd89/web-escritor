import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / 'cuaderno/index.html').read_text(encoding='utf-8')
blocks = re.findall(r'<script\b[^>]*type=[\"\']application/ld\+json[\"\'][^>]*>(.*?)</script>', html, re.I | re.S)
assert blocks, 'Cuaderno carece de JSON-LD'
nodes = []
for raw in blocks:
    data = json.loads(raw)
    nodes.extend(data.get('@graph', [data]))

collections = [n for n in nodes if n.get('@type') == 'CollectionPage']
assert len(collections) == 1, 'CollectionPage debe ser único'
refs = collections[0].get('hasPart', [])
assert isinstance(refs, list), 'El listado de artículos debe ser una colección'
structured = [urlsplit(x['@id']).path for x in refs]
assert len(structured) == len(set(structured)), 'Artículo duplicado en hasPart'

feature = re.search(r'<section\b[^>]*class="cuaderno-feature".*?</section>', html, re.S)
archive = re.search(r'<section\b[^>]*class="cuaderno-archive".*?</section>', html, re.S)
assert feature and archive, 'Falta el índice visible'
visible = set()
for section in (feature.group(), archive.group()):
    for href in re.findall(r'<a\b[^>]*href="(/cuaderno/[^"#?]+/)"', section):
        if not href.startswith('/cuaderno/temas/'):
            visible.add(href)

assert visible, 'No se encontraron artículos visibles'
assert set(structured) == visible, f'Schema-only: {set(structured)-visible}; visible-only: {visible-set(structured)}'
for route in visible:
    assert (ROOT / route.lstrip('/') / 'index.html').is_file(), route

print('PASS Cuaderno Article graph parity')

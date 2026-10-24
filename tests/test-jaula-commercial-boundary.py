#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'donde-empieza-la-jaula/index.html').read_text(encoding='utf-8')
preservation = json.loads((ROOT / 'lab/diseno-home-v1/data/jaula-preservation.json').read_text(encoding='utf-8'))
registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
entry = next(e for e in registry['entries'] if e.get('sourceFile') == 'donde-empieza-la-jaula/index.html')

assert preservation['productionAllowed'] is False
assert entry['status'] != 'public'
assert entry['searchIndex'] is False
assert entry['sitemap'] is False
assert 'class="book-cover-fallback"' in source
hero = re.search(r'<header class="book-hero".*?</header>', source, re.S)
assert hero, 'No se encontró el hero editorial'
assert '<img' not in hero.group(0), 'Una imagen se presenta como portada de la obra no publicada'
article = re.search(r'<article class="book-page".*?</article>', source, re.S)
assert article, 'No se encontró la ficha de la obra'
assert not re.search(r'<a[^>]+(?:comprar|amazon|checkout|purchase)', article.group(0), re.I), 'Aparece una CTA comercial dentro de la obra en desarrollo'
for raw in re.findall(r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>', source, re.S):
    payload = json.loads(raw)
    nodes = payload.get('@graph', [payload]) if isinstance(payload, dict) else payload
    for node in nodes:
        assert node.get('@type') not in ('Book', 'Product', 'Offer'), 'Tipo comercial prematuro'
        for key in ('isbn', 'datePublished', 'publisher', 'offers', 'price', 'aggregateRating'):
            assert key not in node, f'Afirmación sin verificar: {key}'
print('test-jaula-commercial-boundary: OK')

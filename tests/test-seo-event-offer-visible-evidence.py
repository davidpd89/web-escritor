import json
import re
from html import unescape
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / 'eventos.html').read_text(encoding='utf-8')
raw_blocks = re.findall(r'<script\b[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S | re.I)
assert raw_blocks
nodes = []
for raw in raw_blocks:
    data = json.loads(raw)
    nodes.extend(data.get('@graph', [data]))

checked = 0
for event in nodes:
    if event.get('@type') != 'Event':
        continue
    offer = event.get('offers')
    free_offer = isinstance(offer, dict) and str(offer.get('price')) in ('0', '0.00')
    if not free_offer and event.get('isAccessibleForFree') is not True:
        continue
    fragment = urlsplit(event['@id']).fragment
    assert fragment
    entry = re.search(r'<li\b[^>]*\bid="' + re.escape(fragment) + r'"[^>]*>(.*?)</li>', html, re.S | re.I)
    assert entry, f'{fragment}: sin ficha pública'
    visible = unescape(re.sub(r'<[^>]+>', ' ', entry.group(1)))
    visible = re.sub(r'\s+', ' ', visible).casefold()
    assert re.search(r'gratuit[oa]s?|acceso libre|entrada libre|sin coste|sin cargo', visible), (
        f'{fragment}: evento gratuito sin gratuidad explicada: {visible[:180]}'
    )
    checked += 1
assert checked >= 1, 'La prueba no examinó ningún evento gratuito'
print(f'PASS {checked} free Events with visible evidence')

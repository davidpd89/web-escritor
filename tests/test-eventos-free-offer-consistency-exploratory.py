from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def events(filename):
    html = (ROOT / filename).read_text(encoding='utf-8')
    blocks = re.findall(r'<script\s+type="application/ld\+json">\s*(.*?)\s*</script>', html, re.S)
    result = {}
    for block in blocks:
        document = json.loads(block)
        for node in document.get('@graph', [document]):
            if node.get('@type') == 'Event':
                fragment = node.get('@id', '').split('#')[-1]
                result[fragment] = node
    return result

agenda = events('eventos.html')
archive = events('ferias.html')
shared = set(agenda) & set(archive)
assert shared, 'No hay eventos comunes entre agenda y archivo'
for identifier in shared:
    left = agenda[identifier]
    right = archive[identifier]
    assert left.get('startDate') == right.get('startDate'), f'{identifier}: fecha distinta'
    assert left.get('eventStatus') == right.get('eventStatus'), f'{identifier}: estado distinto'
    for key in ('price', 'priceCurrency'):
        assert left.get('offers', {}).get(key) == right.get('offers', {}).get(key), f'{identifier}: oferta {key} distinta'
print(f'eventos free offer consistency: OK ({len(shared)} eventos)')

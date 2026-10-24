from pathlib import Path
from datetime import date
import json
import re

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'assets/v1-home-editorial-v3.js').read_text(encoding='utf-8')
agenda = (ROOT / 'eventos.html').read_text(encoding='utf-8')

rows = re.findall(
    r"\['(2026-\d{2}-\d{2})',\s*'[^']+',\s*'[^']+',\s*'[^']+',\s*'(/eventos\.html#[^']+)'\]",
    source
)
lead = re.search(r"leadTime\.dateTime\s*=\s*'(\d{4}-\d{2}-\d{2})'", source)
assert lead, 'Falta la fecha estructural del evento destacado'
rows.append((lead.group(1), '/eventos.html#feria-libro-madrid-2026'))
assert len(rows) == 4, f'Esperados cuatro eventos, encontrados {len(rows)}'

for stamp, href in rows:
    date.fromisoformat(stamp)
    fragment = href.split('#', 1)[1]
    pattern = (
        r'<li\b[^>]*\bid="' + re.escape(fragment) +
        r'"[^>]*>\s*<time\s+datetime="' + re.escape(stamp) + r'"'
    )
    assert re.search(pattern, agenda), f'{href}: fecha o ancla divergente'

blocks = re.findall(r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>', agenda, re.S)
structured = []
for block in blocks:
    payload = json.loads(block)
    structured += payload.get('@graph', [payload])

for event in structured:
    types = event.get('@type', [])
    if isinstance(types, str):
        types = [types]
    if 'Event' not in types:
        continue
    fragment = event.get('@id', '').split('#')[-1]
    matching = [d for d, href in rows if href.endswith('#' + fragment)]
    if matching:
        assert event['startDate'][:10] == matching[0], fragment

assert len(set(href for _, href in rows)) == len(rows)
assert [d for d, _ in rows[:-1]] == sorted((d for d, _ in rows[:-1]), reverse=True)
print('PASS home-events-temporal-parity')

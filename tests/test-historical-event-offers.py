"""The five archived Event nodes describe free attendance, not available tickets."""
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
count = 0
for rel in ('eventos.html', 'ferias.html', 'cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/index.html'):
    html = (ROOT / rel).read_text(encoding='utf-8')
    for raw in re.findall(r'<script\b[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S):
        doc = json.loads(raw)
        for node in doc.get('@graph', [doc]):
            if node.get('@type') != 'Event':
                continue
            if node.get('endDate', '')[:10] not in ('2026-05-23', '2026-06-10'):
                continue
            assert date.fromisoformat(node['endDate'][:10]) < date(2026, 11, 4)
            assert 'offers' not in node, f'{rel}: archived event must not advertise tickets'
            assert node['isAccessibleForFree'] is True
            assert node['eventStatus'] == 'https://schema.org/EventScheduled'
            count += 1
assert count == 5
print('PASS five historical Event nodes retain free attendance without ticket offers')

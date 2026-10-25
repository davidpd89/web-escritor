from __future__ import annotations
import json
import re
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def events(filename):
    html = (ROOT / filename).read_text(encoding='utf-8')
    blocks = re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I | re.S)
    result = {}
    for block in blocks:
        document = json.loads(block)
        nodes = document if isinstance(document, list) else document.get('@graph', [document])
        for node in nodes:
            if isinstance(node, dict) and node.get('@type') == 'Event':
                identifier = node['@id'].split('#')[-1]
                assert identifier not in result, f'Evento duplicado: {identifier}'
                result[identifier] = node
    return result

def parse(value):
    if len(value) == 10:
        return date.fromisoformat(value)
    return datetime.fromisoformat(value)

agenda = events('eventos.html')
archive = events('ferias.html')
shared = set(agenda) & set(archive)
assert shared, 'No hay eventos compartidos que comparar'
for identifier in shared:
    a, b = agenda[identifier], archive[identifier]
    for field in ('startDate', 'endDate'):
        assert a.get(field) == b.get(field), f'{identifier}: {field} diferente entre páginas'
    for event in (a, b):
        start, end = parse(event['startDate']), parse(event['endDate'])
        assert type(start) is type(end), f'{identifier}: precisión temporal incompatible'
        assert end >= start, f'{identifier}: intervalo temporal invertido'
print('Event temporal cross-page parity: OK')
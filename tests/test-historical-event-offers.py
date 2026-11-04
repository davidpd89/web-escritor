"""Ningún Event ya celebrado anuncia entradas (`offers`) en todo el HTML publicado.

Search Console marca como problema un Event pasado con Offer (2026-11-04: cinco nodos en eventos, ferias y
cuaderno). La regla es general para que el próximo evento que pase de fecha no repita el aviso: al terminar,
el nodo conserva `isAccessibleForFree` y pierde `offers`.
"""
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'.git', '.local', 'node_modules', 'pagefind', 'tests', 'qa', 'artifacts', '.ci', 'tools', '_dist'}
SCRIPT = re.compile(r'<script\b[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.S)


def events(doc):
    if isinstance(doc, list):
        for item in doc:
            yield from events(item)
    elif isinstance(doc, dict):
        kind = doc.get('@type')
        if kind == 'Event' or (isinstance(kind, list) and 'Event' in kind) or str(kind).endswith('Event'):
            yield doc
        for value in doc.values():
            if isinstance(value, (dict, list)):
                yield from events(value)


def violations(html, today):
    out = []
    for raw in SCRIPT.findall(html):
        try:
            doc = json.loads(raw)
        except ValueError:
            continue
        for node in events(doc):
            end = str(node.get('endDate') or node.get('startDate') or '')[:10]
            if len(end) == 10 and date.fromisoformat(end) < today and 'offers' in node:
                out.append(f"{node.get('@id') or node.get('name')} (terminó {end})")
    return out


def self_test():
    past = '<script type="application/ld+json">{"@type":"Event","name":"a","endDate":"2026-05-23","offers":{}}</script>'
    future = past.replace('2026-05-23', '2999-01-01')
    clean = past.replace(',"offers":{}', '')
    assert violations(past, date(2026, 11, 4))
    assert not violations(future, date(2026, 11, 4))
    assert not violations(clean, date(2026, 11, 4))


self_test()
bad, count = [], 0
for path in ROOT.rglob('*.html'):
    if SKIP & set(path.relative_to(ROOT).parts):
        continue
    html = path.read_text(encoding='utf-8', errors='ignore')
    if 'Event' not in html:
        continue
    count += 1
    bad += [f'{path.relative_to(ROOT).as_posix()}: {v}' for v in violations(html, date.today())]
assert not bad, 'Event pasado con offers (quita offers y deja isAccessibleForFree):\n' + '\n'.join(bad[:20])
print(f'PASS ningún Event pasado anuncia entradas ({count} páginas con eventos revisadas)')

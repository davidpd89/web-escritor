"""Typed image and Event vocabulary regressions reported by the 3/11 crawl."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def nodes(rel):
    html = (ROOT / rel).read_text(encoding='utf-8')
    for raw in re.findall(r'<script\b[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S):
        doc = json.loads(raw)
        yield from doc.get('@graph', [doc])

page = next(n for n in nodes('al-otro-lado/index.html') if n.get('@type') == 'WebPage')
assert page['primaryImageOfPage'] == {
    '@type': 'ImageObject',
    'contentUrl': 'https://davidportodiaz.com/assets/al-otro-lado-antologia-letras-como-espada-portada.webp',
}
for rel in ('eventos.html', 'ferias.html', 'cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/index.html'):
    events = [n for n in nodes(rel) if n.get('@type') == 'Event']
    assert events, rel
    for event in events:
        assert 'participant' not in event, rel
        assert event['performer']['@id'] == 'https://davidportodiaz.com/#author', rel
print('PASS Ahrefs schema regressions: typed primary image; performer preserved without participant')

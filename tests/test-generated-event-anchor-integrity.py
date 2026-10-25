from __future__ import annotations
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.canonical = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.append(attrs['id'])
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical.append(attrs.get('href'))

for filename in ('eventos.html', 'ferias.html'):
    html = (ROOT / filename).read_text(encoding='utf-8')
    parser = Parser()
    parser.feed(html)
    assert len(parser.canonical) == 1, f'{filename}: canonical ambiguo'
    counts = Counter(parser.ids)
    assert all(count == 1 for count in counts.values()), f'{filename}: IDs duplicados'
    blocks = re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I | re.S)
    found = 0
    for block in blocks:
        doc = json.loads(block)
        nodes = doc if isinstance(doc, list) else doc.get('@graph', [doc])
        for node in nodes:
            if not isinstance(node, dict) or node.get('@type') != 'Event':
                continue
            found += 1
            identifier = node.get('@id', '')
            assert identifier.startswith(parser.canonical[0] + '#'), (filename, identifier)
            assert node.get('url') == identifier, (filename, identifier)
            fragment = identifier.split('#', 1)[1]
            assert counts[fragment] == 1, f'{filename}: ancla rota {fragment}'
    assert found, f'{filename}: no hay Event'
print('Event anchor integrity: OK')
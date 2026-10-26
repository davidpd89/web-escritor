#!/usr/bin/env python3
"""Protege los identificadores de scripts publicados en la checklist."""
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'publicar-web/index.html'
EXPECTED = (
    'scripts/build-sitemap.py',
    'scripts/validate_jsonld.py',
    'scripts/check-internal-graph.py',
)

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.items = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == 'li':
            self.current = []
            self.depth = 1
        elif self.current is not None and tag not in {'br', 'img', 'input', 'hr'}:
            self.depth += 1

    def handle_endtag(self, tag):
        if self.current is None:
            return
        self.depth -= 1
        if self.depth == 0:
            self.items.append(''.join(self.current))
            self.current = None

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)

parser = Parser()
parser.feed(PAGE.read_text(encoding='utf-8'))
assert parser.items, '/publicar-web/: checklist sin elementos'

for path in EXPECTED:
    matches = [item for item in parser.items if path in item]
    assert len(matches) == 1, (
        f'/publicar-web/: {path} debe aparecer íntegro en una única instrucción; '
        f'coincidencias={len(matches)}'
    )
    assert matches[0].count(path) == 1, (
        f'/publicar-web/: identificador técnico duplicado: {path}'
    )

print('PASS publicar-web: identificadores técnicos íntegros')

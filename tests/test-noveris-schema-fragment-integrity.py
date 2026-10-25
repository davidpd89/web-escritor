#!/usr/bin/env python3
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'universo/noveris/index.html').read_text(encoding='utf-8')
CANONICAL = 'https://davidportodiaz.com/universo/noveris/'

class IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name == 'id' and value:
                self.ids.append(value)

parser = IdCollector()
parser.feed(HTML)
counts = Counter(parser.ids)
assert all(n == 1 for n in counts.values()), 'IDs HTML duplicados'

blocks = re.findall(r'<script\s+type="application/ld\+json">(.*?)</script>', HTML, re.S)
assert blocks, 'JSON-LD ausente'
documents = [json.loads(block) for block in blocks]
references = []

def walk(value):
    if isinstance(value, dict):
        identifier = value.get('@id')
        if isinstance(identifier, str):
            parsed = urlsplit(identifier)
            if parsed.fragment and identifier.startswith(CANONICAL):
                references.append((identifier, unquote(parsed.fragment)))
        for nested in value.values():
            walk(nested)
    elif isinstance(value, list):
        for nested in value:
            walk(nested)

for document in documents:
    walk(document)
assert references, 'No se ejercitan referencias fragmentadas'
for uri, fragment in references:
    assert counts[fragment] == 1, f'@id sin destino HTML único: {uri}'
print(f'no veris schema fragment integrity: PASS ({len(references)} referencias)')
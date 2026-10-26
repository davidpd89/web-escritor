#!/usr/bin/env python3
"""Homogeneidad de los avisos de procesamiento en tarjetas."""
import importlib.util
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('hub', ROOT / 'scripts/build-tools-hub.py')
hub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hub)

class CardParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.privacy = None
        self.labels = []
        self.capture = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'article':
            self.privacy = attrs.get('data-privacy')
        if tag == 'p' and 'tool-meta' in attrs.get('class', '').split():
            self.capture = True
            self.labels.append('')

    def handle_data(self, text):
        if self.capture:
            self.labels[-1] += text

    def handle_endtag(self, tag):
        if tag == 'p':
            self.capture = False

data = json.loads((ROOT / 'data/tools-hub.json').read_text(encoding='utf-8'))
tools, _ = hub.validate(data)
assert tools, 'data/tools-hub.json: catálogo vacío'
observed = {}
for tool in tools:
    parser = CardParser()
    parser.feed(hub.card(tool))
    assert parser.privacy == tool['privacy'], f"{tool['href']}: data-privacy={parser.privacy!r}, esperado {tool['privacy']!r}"
    assert len(parser.labels) == 1, f"{tool['href']}: se esperaban una etiqueta de privacidad, obtenidas {parser.labels!r}"
    label = parser.labels[0].strip()
    assert label == hub.PRIVACY[tool['privacy']], f"{tool['href']}: aviso {label!r} incompatible con {tool['privacy']!r}"
    previous = observed.setdefault(tool['privacy'], label)
    assert previous == label, f"{tool['href']}: aviso no homogéneo: {previous!r} frente a {label!r}"
print(f'OK: {len(tools)} tarjetas y {len(observed)} clases de privacidad')

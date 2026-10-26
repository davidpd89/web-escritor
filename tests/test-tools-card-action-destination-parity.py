#!/usr/bin/env python3
"""Paridad de destinos de las acciones de las tarjetas de herramientas."""
import importlib.util
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tools_hub', ROOT / 'scripts/build-tools-hub.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.current = {'href': dict(attrs).get('href'), 'text': ''}

    def handle_data(self, data):
        if self.current is not None:
            self.current['text'] += data

    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            self.links.append(self.current)
            self.current = None

data = json.loads((ROOT / 'data/tools-hub.json').read_text(encoding='utf-8'))
tools, _ = module.validate(data)
assert tools, 'data/tools-hub.json: no se encontraron herramientas'
for tool in tools:
    parser = Links()
    parser.feed(module.card(tool))
    title = [a for a in parser.links if a['text'].strip() == tool['name']]
    action = [a for a in parser.links if a['text'].strip() == 'Abrir herramienta']
    assert len(title) == 1, f"{tool['href']}: título navegable ausente o duplicado: {title!r}"
    assert len(action) == 1, f"{tool['href']}: acción de apertura ausente o duplicada: {action!r}"
    for link in title + action:
        assert link['href'] == tool['href'], f"{tool['href']}: destino incorrecto {link['href']!r}"
print(f'OK: {len(tools)} tarjetas con destinos homogéneos')

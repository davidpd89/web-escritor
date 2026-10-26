#!/usr/bin/env python3
"""Conexión de las herramientas publicadas con sus motores declarados."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SLUGS = ['contador-palabras', 'limpiador-manuscritos', 'dialogo', 'legibilidad']

class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            src = dict(attrs).get('src')
            if src:
                self.sources.append(src)

data = json.loads((ROOT / 'data/tools-hub.json').read_text(encoding='utf-8'))
tools = {tool['href']: tool for tool in data['tools']}
for slug in SLUGS:
    route = f'/herramientas/{slug}/'
    assert route in tools, f'data/tools-hub.json: herramienta ausente {route}'
    source = tools[route]['source_doc']
    assert (ROOT / source).is_file(), f'{route}: motor inexistente {source}'
    page = ROOT / 'herramientas' / slug / 'index.html'
    parser = Scripts()
    parser.feed(page.read_text(encoding='utf-8'))
    sources = {urlsplit(src).path.lstrip('/') for src in parser.sources}
    assert source in sources, f'{page}: motor {source!r} no cargado; scripts reales: {sorted(sources)!r}'
print(f'OK: {len(SLUGS)} herramientas conectadas a sus motores declarados')

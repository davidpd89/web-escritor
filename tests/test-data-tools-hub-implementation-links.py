from __future__ import annotations
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
records = json.loads((ROOT / 'data/tools-hub.json').read_text(encoding='utf-8'))['tools']

class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            href = dict(attrs).get('href')
            if href:
                self.hrefs.append(href)

parser = Anchors()
parser.feed((ROOT / 'herramientas/index.html').read_text(encoding='utf-8'))
seen = set()
for tool in records:
    href = tool['href']
    assert href.startswith('/') and not href.startswith('//'), tool['slug']
    assert not urlsplit(href).query and not urlsplit(href).fragment, tool['slug']
    assert href not in seen, f'Destino duplicado: {href}'
    seen.add(href)
    rel = href.strip('/')
    page = ROOT / rel / 'index.html' if href.endswith('/') else ROOT / rel
    assert page.is_file(), f'Destino inexistente: {page}'
    assert (ROOT / tool['source_doc']).is_file(), tool['slug']
    assert href in parser.hrefs, f'Herramienta sin enlace en el índice: {href}'

print(f'OK: {len(records)} herramientas trazables')

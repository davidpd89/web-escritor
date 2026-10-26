from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json
import re

ROOT = Path(__file__).resolve().parents[1]
PAGES = ('eventos.html', 'ferias.html', 'premios.html', 'autor.html')

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside = False
        self.rules = []
        self.buffer = []
    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type') == 'speculationrules':
            self.inside = True
            self.buffer = []
    def handle_data(self, data):
        if self.inside:
            self.buffer.append(data)
    def handle_endtag(self, tag):
        if tag == 'script' and self.inside:
            self.rules.append(json.loads(''.join(self.buffer)))
            self.inside = False

def destinations(value):
    if isinstance(value, dict):
        if isinstance(value.get('urls'), list):
            yield from value['urls']
        for key, child in value.items():
            if key != 'urls':
                yield from destinations(child)
    elif isinstance(value, list):
        for child in value:
            yield from destinations(child)

count = 0
for source in PAGES:
    parser = Parser()
    parser.feed((ROOT / source).read_text(encoding='utf-8'))
    for rule in parser.rules:
        for target in destinations(rule):
            if not isinstance(target, str) or not target.startswith('/') or target.startswith('//'):
                continue
            path = unquote(urlsplit(target).path)
            candidate = ROOT / path.lstrip('/')
            if candidate.is_dir():
                candidate /= 'index.html'
            assert candidate.is_file(), f'{source}: destino especulativo inexistente: {target}'
            content = candidate.read_text(encoding='utf-8')
            assert re.search(r'<html\b', content, re.I), f'{source}: destino no HTML: {target}'
            robots = re.findall(r'<meta\b[^>]*name=["\']robots["\'][^>]*>', content, re.I)
            assert not any(re.search(r'noindex', tag, re.I) for tag in robots), f'{source}: destino noindex: {target}'
            count += 1
assert count > 0, 'No se analizaron destinos especulativos de las páginas raíz'
print(f'PASS {count} destinos especulativos editoriales')
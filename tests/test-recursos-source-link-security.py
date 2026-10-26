from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit
import json

ROOT = Path(__file__).resolve().parents[1]
ROUTE = 'recursos/herramientas-para-escritores/index.html'

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.card_depth = 0
        self.depth = 0
        self.cards = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'article' and 'wt-card' in a.get('class', '').split():
            self.card_depth = self.depth + 1
            self.cards += 1
        if self.card_depth and tag == 'a':
            self.links.append(a)
        if tag not in ('meta', 'link', 'img', 'input', 'br', 'hr', 'source', 'area', 'wbr'):
            self.depth += 1

    def handle_endtag(self, tag):
        if tag not in ('meta', 'link', 'img', 'input', 'br', 'hr', 'source', 'area', 'wbr'):
            self.depth -= 1
        if self.card_depth and self.depth < self.card_depth:
            self.card_depth = 0

p = Parser()
p.feed((ROOT / ROUTE).read_text(encoding='utf-8'))
data = json.loads((ROOT / 'data/writer-tools.json').read_text(encoding='utf-8'))
active = [t for t in data['tools'] if t['status'] != 'deprecated']
assert p.cards == len(active), f'{ROUTE}: tarjetas={p.cards}, datos={len(active)}'
assert len(p.links) >= len(active), f'{ROUTE}: enlaces de tarjetas insuficientes'
for a in p.links:
    href = a.get('href', '')
    u = urlsplit(href)
    assert u.scheme == 'https' and u.hostname and not u.username and not u.password, f'{ROUTE}: destino inseguro {href}'
    assert not any(ord(c) < 32 for c in href), f'{ROUTE}: controles en URL {href!r}'
    rel = set(a.get('rel', '').lower().split())
    if a.get('target', '').lower() == '_blank':
        assert {'noopener', 'noreferrer'} <= rel, f'{ROUTE}: target=_blank sin aislamiento: {href}'
    if 'sponsored' in rel:
        assert a.get('target') == '_blank' or 'noopener' in rel, f'{ROUTE}: afiliado sin protección: {href}'
print('OK: enlaces documentales HTTPS y aislamiento de pestañas')
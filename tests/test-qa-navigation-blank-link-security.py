from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'mapa-del-sitio/index.html', 'empieza-aqui/index.html']

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs))

checked = 0
for path in PAGES:
    p = Parser()
    p.feed((ROOT / path).read_text(encoding='utf-8'))
    for link in p.links:
        if link.get('target', '').lower() != '_blank':
            continue
        checked += 1
        rel = set(link.get('rel', '').lower().split())
        href = link.get('href', '')
        assert 'noopener' in rel, f'{path}: target=_blank inseguro: {href}'
        if 'header-buy' in link.get('class', '').split():
            assert {'sponsored', 'nofollow'} <= rel, f'{path}: afiliado sin atributos: {href}'
assert checked > 0, 'No se analizaron enlaces de nueva pestaña'
print(f'navigation-blank-link-security: OK ({checked} enlaces)')
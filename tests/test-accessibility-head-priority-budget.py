from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGE = 'accesibilidad/index.html'
MAX_STYLE_PRELOADS = 9

class HeadLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_head = False
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'head':
            self.in_head = True
        if tag == 'link' and self.in_head:
            self.links.append(dict(attrs))

    def handle_endtag(self, tag):
        if tag == 'head':
            self.in_head = False

parser = HeadLinks()
parser.feed((ROOT / PAGE).read_text(encoding='utf-8'))
preloads = [link for link in parser.links if 'preload' in (link.get('rel') or '').lower().split()]
styles = [link for link in preloads if link.get('as') == 'style']
assert len(styles) <= MAX_STYLE_PRELOADS, f'{PAGE}: {len(styles)} precargas CSS, presupuesto {MAX_STYLE_PRELOADS}'
seen = set()
for link in preloads:
    href = link.get('href') or ''
    key = (link.get('as'), urlsplit(href).path, urlsplit(href).query)
    assert href, f'{PAGE}: preload sin href'
    assert key not in seen, f'{PAGE}: preload duplicado {href}'
    seen.add(key)
    assert link.get('as') not in {'image', 'script'}, f'{PAGE}: preload prioritario no presupuestado: {href}'
assert styles, f'{PAGE}: no se han inspeccionado precargas de estilos'
print(f'PASS: {PAGE}, {len(styles)} precargas CSS, {len(preloads)} precargas totales')
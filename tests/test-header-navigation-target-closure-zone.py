from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'mapa-del-sitio/index.html', 'empieza-aqui/index.html']

class HeaderLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'header':
            self.depth += 1
        if self.depth and tag == 'a':
            self.links.append(dict(attrs).get('href', ''))

    def handle_endtag(self, tag):
        if tag == 'header' and self.depth:
            self.depth -= 1

failures = []
checked = 0
for page in PAGES:
    parser = HeaderLinks()
    parser.feed((ROOT / page).read_text(encoding='utf-8'))
    assert parser.links, f'{page}: cabecera sin enlaces'
    for href in parser.links:
        url = urlsplit(href)
        if url.scheme or url.netloc or href.startswith(('mailto:', 'tel:')):
            continue
        if not href or not url.path and not url.fragment:
            failures.append(f'{page}: destino vacío: {href!r}')
            continue
        raw = unquote(url.path)
        if not raw:
            continue
        base = ROOT if raw.startswith('/') else ROOT / Path(page).parent
        target = (base / raw.lstrip('/')).resolve()
        if not target.is_relative_to(ROOT.resolve()):
            failures.append(f'{page}: escape de directorio: {href}')
            continue
        candidates = [target / 'index.html', target] if raw.endswith('/') else [target, target / 'index.html']
        if not any(p.is_file() for p in candidates):
            failures.append(f'{page}: destino inexistente: {href}')
        checked += 1
assert checked > 0
assert not failures, '\n'.join(failures)
print(f'header-navigation-target-closure: OK ({checked} destinos)')

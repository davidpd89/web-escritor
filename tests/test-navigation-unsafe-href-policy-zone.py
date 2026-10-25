from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'mapa-del-sitio/index.html', 'empieza-aqui/index.html']
ALLOWED = {'', 'https', 'mailto', 'tel'}

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.hrefs.append(dict(attrs).get('href', ''))

for page in PAGES:
    parser = Links()
    parser.feed((ROOT / page).read_text(encoding='utf-8'))
    errors = []
    for href in parser.hrefs:
        url = urlsplit(href)
        if not href.strip():
            errors.append('href vacío')
        if any(ord(char) < 32 or ord(char) == 127 for char in href):
            errors.append(f'carácter de control: {href!r}')
        if url.scheme.lower() not in ALLOWED:
            errors.append(f'protocolo prohibido: {href!r}')
        if url.username is not None or url.password is not None:
            errors.append(f'credenciales en URL: {href!r}')
        if url.scheme == 'http':
            errors.append(f'HTTP inseguro: {href!r}')
        if href.startswith('//'):
            errors.append(f'URL sin esquema: {href!r}')
    assert parser.hrefs, f'{page}: no se encontraron enlaces'
    assert not errors, f'{page}: ' + '; '.join(errors)
print('navigation-unsafe-href-policy: OK')

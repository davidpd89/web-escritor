import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGE = 'offline.html'
html = (ROOT / PAGE).read_text(encoding='utf-8')
ORIGIN = 'https://davidportodiaz.com'

class Resources(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.resources = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('script', 'img', 'iframe', 'source', 'audio', 'video') and attrs.get('src'):
            self.resources.append((tag, attrs['src']))
        if tag == 'link' and attrs.get('href'):
            self.resources.append((tag, attrs['href']))
        if tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])

parser = Resources()
parser.feed(html)
css_urls = re.findall(r'url\(\s*[\x22\x27]?([^\x22\x27)]+)', html, flags=re.I)
resources = parser.resources + [('CSS', value.strip()) for value in css_urls]
assert resources, f'{PAGE}: no se encontraron dependencias para verificar'

for kind, value in resources:
    if value.startswith('data:'):
        continue
    url = urlsplit(urljoin(ORIGIN + '/', value))
    assert url.scheme == 'https' and url.netloc == 'davidportodiaz.com', f'{PAGE} {kind}: recurso externo o inseguro: {value}'
    assert not url.username and not url.password, f'{PAGE} {kind}: URL con credenciales: {value}'
    target = ROOT / url.path.lstrip('/')
    if url.path.endswith('/'):
        target /= 'index.html'
    assert target.is_file(), f'{PAGE} {kind}: recurso local inexistente: {value}'

for href in parser.links:
    scheme = urlsplit(href).scheme.lower()
    assert scheme not in ('javascript', 'data', 'vbscript'), f'{PAGE}: enlace con esquema ejecutable: {href}'

print(f'PASS: {len(resources)} recursos y {len(parser.links)} enlaces seguros en {PAGE}')
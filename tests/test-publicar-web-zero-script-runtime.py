from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = '/publicar-web/'

class Runtime(HTMLParser):
    def __init__(self):
        super().__init__()
        self.executable = []
        self.headings = 0
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'script':
            self.executable.append('script')
        if tag == 'link' and 'modulepreload' in a.get('rel', '').lower().split():
            self.executable.append('modulepreload')
        for name, value in attrs:
            if name.lower().startswith('on'):
                self.executable.append(f'{tag}[{name}]')
            if name in ('href', 'src') and value and value.strip().lower().startswith('javascript:'):
                self.executable.append(f'{tag}[{name}=javascript:]')
        if tag == 'h1':
            self.headings += 1
        if tag == 'a':
            self.links.append(a.get('href', ''))

p = Runtime()
p.feed((ROOT / 'publicar-web/index.html').read_text(encoding='utf-8'))
assert p.headings == 1, f'{PAGE}: encabezados principales encontrados: {p.headings}'
for target in ('/sitemap.xml', '/herramientas/', '/lecturas/'):
    assert target in p.links, f'{PAGE}: falta navegación documental a {target}'
assert not p.executable, f'{PAGE}: ejecución JavaScript añadida: {p.executable}'
print('OK publicar-web: navegación documental sin JavaScript')

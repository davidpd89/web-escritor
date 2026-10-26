from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = '/publicar-web/'

class Audit(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.resources = []
        self.main = 0
        self.links = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'main':
            self.main += 1
        if tag == 'a' and a.get('href'):
            self.links += 1
        if tag in ('script', 'iframe', 'img', 'picture', 'video', 'audio', 'source', 'object', 'embed'):
            self.resources.append((tag, a.get('src', '')))
        if tag == 'link' and set(a.get('rel', '').lower().split()) & {'stylesheet', 'preload', 'modulepreload', 'prefetch'}:
            self.resources.append((tag, a.get('href', '')))

p = Audit()
p.feed((ROOT / 'publicar-web/index.html').read_text(encoding='utf-8'))
assert p.main == 1, f'{PAGE}: se esperaba un main; encontrados {p.main}'
assert p.links >= 3, f'{PAGE}: solo {p.links} enlaces de navegación'
assert not p.resources, f'{PAGE}: nuevas peticiones de renderizado: {p.resources}'
print('OK publicar-web: contenido y navegación sin peticiones críticas adicionales')

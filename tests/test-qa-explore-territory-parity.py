from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'mapa-del-sitio/index.html', 'empieza-aqui/index.html']
EXPECTED = [('/libros/', 'works-hub'), ('/autor.html', 'author'), ('/recomendaciones/', 'recommendations-hub'), ('/herramientas/', 'tools-hub'), ('/prensa.html', 'press')]

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return
        a = dict(attrs)
        if 'explore-row' in a.get('class', '').split():
            self.links.append((a.get('href'), a.get('data-preview')))

for path in PAGES:
    parser = Parser()
    parser.feed((ROOT / path).read_text(encoding='utf-8'))
    assert parser.links, f'{path}: menú Explorar ausente'
    assert parser.links == EXPECTED, f'{path}: destinos u orden divergentes: {parser.links}'
    assert len(set(parser.links)) == len(parser.links), f'{path}: duplicados'
print('explore-territory-parity: OK')
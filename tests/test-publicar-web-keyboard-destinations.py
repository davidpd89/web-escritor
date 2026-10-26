from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'publicar-web/index.html'

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a':
            self.current = {'href': a.get('href', ''), 'name': a.get('aria-label', ''), 'text': '', 'tabindex': a.get('tabindex')}

    def handle_data(self, data):
        if self.current is not None:
            self.current['text'] += data

    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            self.links.append(self.current)
            self.current = None

p = Parser()
p.feed(PAGE.read_text(encoding='utf-8'))
assert p.links, f'{PAGE}: no se encontraron enlaces'
for link in p.links:
    href = link['href']
    name = (link['name'] or link['text']).strip()
    assert name, f'{PAGE}: enlace {href!r} sin nombre accesible'
    assert link['tabindex'] is None or int(link['tabindex']) >= 0, f'{PAGE}: enlace {href} excluido de Tab'
    parsed = urlsplit(href)
    assert parsed.path.startswith('/') and not parsed.netloc, f'{PAGE}: destino inesperado {href}'
    destination = ROOT / unquote(parsed.path).lstrip('/')
    if parsed.path.endswith('/'):
        destination /= 'index.html'
    assert destination.is_file(), f'{PAGE}: enlace {name!r} apunta a recurso inexistente {destination}'
    if destination.suffix == '.html':
        html = destination.read_text(encoding='utf-8').lower()
        assert '<main' in html, f'{PAGE}: destino {parsed.path} sin landmark main'
print(f'OK {PAGE}: {len(p.links)} enlaces navegables con destino existente')
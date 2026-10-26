from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'accesibilidad/index.html', 'mapa-del-sitio/index.html']

class HeaderParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.controls = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.add(a['id'])
        if tag == 'header' and 'site-header' in a.get('class', '').split():
            self.depth = 1
            return
        if self.depth:
            self.depth += 1
            if tag in ('a', 'button'):
                self.controls.append((tag, a))

    def handle_endtag(self, tag):
        if self.depth:
            self.depth -= 1


def contract(page):
    parser = HeaderParser()
    parser.feed((ROOT / page).read_text(encoding='utf-8'))
    expected = {
        'Volver a inicio': '/',
        'Mapa del sitio': '/mapa-del-sitio/',
        'Contactar': '/prensa.html#contacto'
    }
    for label, href in expected.items():
        matches = [a for tag, a in parser.controls if tag == 'a' and a.get('aria-label') == label]
        assert len(matches) == 1, f'{page}: control {label}: {len(matches)} coincidencias'
        assert matches[0].get('href') == href, f'{page}: {label}: destino {matches[0].get("href")!r}'
    for attr in ('data-assistant-search-open', 'data-explore-open'):
        matches = [a for tag, a in parser.controls if tag == 'button' and attr in a]
        assert len(matches) == 1, f'{page}: botón {attr}: {len(matches)} coincidencias'
        assert matches[0].get('aria-label'), f'{page}: {attr} sin nombre accesible'
        if attr == 'data-explore-open':
            assert matches[0].get('aria-controls') in parser.ids, f'{page}: menú sin diálogo asociado'
    return True

for page in PAGES:
    assert contract(page)
print('shared-header-navigation-contract: OK')

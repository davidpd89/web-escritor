from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'mapa-del-sitio/index.html', 'empieza-aqui/index.html']

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = {}
        self.buttons = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.setdefault(a['id'], []).append((tag, a))
        if tag == 'button' and 'explore-row__toggle' in a.get('class', '').split():
            self.buttons.append(a)

for path in PAGES:
    p = Parser()
    p.feed((ROOT / path).read_text(encoding='utf-8'))
    assert len(p.buttons) >= 5, f'{path}: faltan controles'
    targets = []
    for button in p.buttons:
        target = button.get('aria-controls')
        assert target, f'{path}: botón sin aria-controls'
        assert button.get('aria-expanded') == 'false', f'{path}: expansión inicial incorrecta'
        assert button.get('aria-label', '').strip(), f'{path}: botón sin nombre'
        assert len(p.ids.get(target, [])) == 1, f'{path}: destino ausente o duplicado {target}'
        tag, panel = p.ids[target][0]
        assert tag == 'div' and 'explore-children' in panel.get('class', '').split(), f'{path}: panel incorrecto'
        assert 'hidden' in panel, f'{path}: panel visible inicialmente'
        targets.append(target)
    assert len(set(targets)) == len(targets), f'{path}: controles comparten panel'
print('explore-aria-controls: OK')
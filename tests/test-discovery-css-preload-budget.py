from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'recomendaciones/index.html'

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.preloads = []

    def handle_starttag(self, tag, attrs):
        if tag != 'link':
            return
        a = dict(attrs)
        if 'preload' in a.get('rel', '').split() and a.get('as') == 'style':
            self.preloads.append(a.get('href', ''))

p = Links()
p.feed(PAGE.read_text(encoding='utf-8'))
assert p.preloads, '/recomendaciones/: no se encontraron precargas CSS; revisar el contrato'
assert len(p.preloads) <= 6, (
    f'/recomendaciones/: {len(p.preloads)} precargas CSS, máximo 6: {p.preloads}'
)
print('PASS discovery CSS preload budget')

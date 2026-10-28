from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'mapa-del-sitio/index.html', 'empieza-aqui/index.html']

class Audit(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.regions = []
        self.controls = []
        self.current = None
        self.failures = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ('header', 'nav', 'footer'):
            self.regions.append(tag)
        if self.regions and tag in ('a', 'button'):
            self.controls.append({'tag': tag, 'attrs': a, 'text': '', 'alt': ''})
        if self.controls and tag == 'img':
            self.controls[-1]['alt'] += a.get('alt', '')

    def handle_data(self, data):
        for control in self.controls:
            control['text'] += data

    def handle_endtag(self, tag):
        if self.controls and self.controls[-1]['tag'] == tag:
            c = self.controls.pop()
            a = c['attrs']
            name = c['text'].strip() or c['alt'].strip() or a.get('aria-label', '').strip() or a.get('aria-labelledby', '').strip()
            if not name:
                self.failures.append(f'{tag} sin nombre: {a}')
        if tag in ('header', 'nav', 'footer') and self.regions:
            self.regions.pop()

for page in PAGES:
    parser = Audit()
    parser.feed((ROOT / page).read_text(encoding='utf-8'))
    assert not parser.failures, f'{page}: {parser.failures}'
print('navigation-accessible-names: OK')

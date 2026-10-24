from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'mapa-del-sitio/index.html', 'empieza-aqui/index.html']
TARGET = '/prensa.html#contacto'

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.contacts = []
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.add(a['id'])
        if tag == 'a' and 'header-contact' in a.get('class', '').split():
            self.contacts.append(a)

for path in PAGES:
    p = Parser()
    p.feed((ROOT / path).read_text(encoding='utf-8'))
    assert len(p.contacts) == 1, f'{path}: esperado un enlace de contacto'
    link = p.contacts[0]
    assert link.get('href') == TARGET, f'{path}: contacto obsoleto {link.get("href")}'
    assert link.get('aria-label', '').strip(), f'{path}: falta nombre accesible'

press = Parser()
press.feed((ROOT / 'prensa.html').read_text(encoding='utf-8'))
assert 'contacto' in press.ids, 'prensa.html: falta el destino #contacto'
print('header-contact-parity: OK')
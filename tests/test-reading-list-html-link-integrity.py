import importlib.util
import json
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_link_integrity', ROOT / 'scripts/build-reading-list.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class Reader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.headings = []
        self.current_heading = False
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs))
        if tag == 'h3':
            self.current_heading = True
    def handle_endtag(self, tag):
        if tag == 'h3':
            self.current_heading = False
    def handle_data(self, data):
        if self.current_heading:
            self.headings.append(data)

payload = json.loads((ROOT / 'data/reading-list.json').read_text(encoding='utf-8'))
item = dict(payload['items'][0])
item.update(publish=True, title='Las manecillas del recuerdo: memoria & tiempo', link_kind='official', url='https://editorial.example/book/las-manecillas?formato=papel&idioma=es', verified_on='2026-07-15')
items, disclosure = mod.validate({'items': [item], 'affiliate_disclosure': payload['affiliate_disclosure']}, date(2026, 10, 25))
page = mod.render(items, disclosure, '2026-08-19')
reader = Reader()
reader.feed(page)
assert reader.headings == [item['title']], f'lecturas/index.html: título editorial alterado: {reader.headings}'
assert len(reader.links) == 1, f'lecturas/index.html: número inesperado de enlaces de ficha: {reader.links}'
link = reader.links[0]
assert link.get('href') == item['url'], f'lecturas/index.html: destino oficial alterado: {link.get("href")!r}'
assert link.get('target') == '_blank', f'lecturas/index.html: apertura del enlace modificada: {link}'
assert {'noopener', 'noreferrer'} <= set(link.get('rel', '').split()), f'lecturas/index.html: faltan protecciones del enlace externo: {link}'
print('PASS reading HTML and outbound link integrity')
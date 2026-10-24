from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
class Inspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.skip_links = []
        self.main_count = 0
        self.breadcrumb_count = 0
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'main':
            self.main_count += 1
        if tag == 'a' and attrs.get('class', '').find('skip-link') >= 0:
            self.skip_links.append(attrs.get('href'))
        if tag == 'nav' and attrs.get('aria-label') == 'Ruta de navegación':
            self.breadcrumb_count += 1

pages = sorted((ROOT / 'editoriales').glob('*/index.html'))
assert pages, 'No hay fichas editoriales generadas'
for page in pages:
    inspector = Inspector()
    inspector.feed(page.read_text(encoding='utf-8'))
    assert inspector.main_count == 1, f'{page}: debe existir exactamente un main'
    assert inspector.breadcrumb_count >= 1, f'{page}: falta breadcrumb semántico'
    assert inspector.skip_links, f'{page}: falta salto al contenido'
    for href in inspector.skip_links:
        assert href and href.startswith('#') and href[1:] in inspector.ids, f'{page}: destino de salto inexistente: {href}'
    assert len(inspector.ids) == len(set(inspector.ids)), f'{page}: IDs duplicados'
print(f'editoriales semantic shell: OK ({len(pages)} páginas)')

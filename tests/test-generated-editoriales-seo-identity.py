from __future__ import annotations
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
records = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))['publishers']

class HeadParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = []
        self.meta = {}
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonical.append(a.get('href'))
        if tag == 'meta':
            key = a.get('property') or a.get('name')
            if key:
                self.meta.setdefault(key, []).append(a.get('content', ''))

published = [r for r in records if r.get('publish') is True]
assert published
for record in published:
    slug = record['slug']
    page = ROOT / 'editoriales' / slug / 'index.html'
    assert page.is_file(), f'Ficha inexistente: {slug}'
    parser = HeadParser()
    parser.feed(page.read_text(encoding='utf-8'))
    expected = f'https://davidportodiaz.com/editoriales/{slug}/'
    assert parser.canonical == [expected], f'{slug}: canonical incorrecto'
    assert parser.meta.get('og:url') == [expected], f'{slug}: og:url diferente'
    assert parser.meta.get('description', [''])[0].strip(), f'{slug}: sin descripción SEO'
    assert not any('noindex' in value.lower() for value in parser.meta.get('robots', [])), f'{slug}: ficha publicada noindex'
print('Editoriales SEO identity: OK')
from __future__ import annotations
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
records = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))['publishers']

class Semantics(HTMLParser):
    def __init__(self):
        super().__init__()
        self.counts = {}
        self.lang = None
    def handle_starttag(self, tag, attrs):
        self.counts[tag] = self.counts.get(tag, 0) + 1
        if tag == 'html':
            self.lang = dict(attrs).get('lang')

for record in records:
    if record.get('publish') is not True:
        continue
    slug = record['slug']
    path = ROOT / 'editoriales' / slug / 'index.html'
    parser = Semantics()
    parser.feed(path.read_text(encoding='utf-8'))
    assert parser.lang and parser.lang.startswith('es'), f'{slug}: idioma incorrecto'
    assert parser.counts.get('title', 0) == 1, f'{slug}: título ausente o duplicado'
    assert parser.counts.get('main', 0) == 1, f'{slug}: main ausente o duplicado'
    assert parser.counts.get('h1', 0) == 1, f'{slug}: H1 ausente o duplicado'
print('Editoriales HTML semantics: OK')
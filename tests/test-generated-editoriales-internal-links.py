from __future__ import annotations
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
records = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))['publishers']

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            href = dict(attrs).get('href')
            if href:
                self.hrefs.append(href)

for record in records:
    if record.get('publish') is not True:
        continue
    slug = record['slug']
    page = ROOT / 'editoriales' / slug / 'index.html'
    parser = Links()
    parser.feed(page.read_text(encoding='utf-8'))
    assert parser.hrefs, f'{slug}: página sin enlaces'
    for href in parser.hrefs:
        url = urlsplit(href)
        if url.scheme or url.netloc or not url.path.startswith('/'):
            continue
        target = ROOT / unquote(url.path).lstrip('/')
        if url.path.endswith('/'):
            target = target / 'index.html'
        assert target.is_file(), f'{slug}: enlace roto {href}'
print('Editoriales internal links: OK')
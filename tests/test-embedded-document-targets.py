#!/usr/bin/env python3
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://davidportodiaz.com'

class Frames(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.frames = []
    def handle_starttag(self, tag, attrs):
        if tag == 'iframe':
            self.frames.append(dict(attrs))

names = subprocess.check_output(['git', 'ls-files', '-z', '*.html'], cwd=ROOT).decode().split('\0')
errors = []
checked = 0
for name in names:
    if not name or name.startswith(('tests/', 'qa/', 'scripts/', 'data/', 'lab/')):
        continue
    parser = Frames()
    parser.feed((ROOT / name).read_text(encoding='utf-8'))
    page_url = ORIGIN + ('/' + name[:-10] if name.endswith('index.html') else '/' + name)
    for frame in parser.frames:
        checked += 1
        if not (frame.get('title') or '').strip() and not (frame.get('aria-label') or '').strip():
            errors.append(f'{name}: iframe sin nombre accesible')
        src = (frame.get('src') or '').strip()
        if not src or src == 'about:blank' or 'srcdoc' in frame:
            continue
        u = urlsplit(urljoin(page_url, src))
        if u.netloc not in ('davidportodiaz.com', 'www.davidportodiaz.com'):
            continue
        path = unquote(u.path)
        dest = ROOT / path.lstrip('/')
        if path.endswith('/'):
            dest /= 'index.html'
        if not dest.is_file():
            errors.append(f'{name}: iframe local sin destino: {src}')
assert not errors, '\n'.join(errors)
print(f'PASS iframe targets: {checked} iframes auditados')

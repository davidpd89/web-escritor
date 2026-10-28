#!/usr/bin/env python3
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
HOSTS = {'davidportodiaz.com', 'www.davidportodiaz.com'}

class Downloads(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.urls = []
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'a' and 'download' in d and d.get('href'):
            self.urls.append(d['href'])

names = subprocess.check_output(['git', 'ls-files', '-z', '*.html'], cwd=ROOT).decode().split('\0')
checked = 0
errors = []
for name in names:
    if not name or name.startswith(('tests/', 'qa/', 'scripts/', 'data/', 'lab/')):
        continue
    parser = Downloads()
    parser.feed((ROOT / name).read_text(encoding='utf-8'))
    for ref in parser.urls:
        u = urlsplit(ref)
        if u.scheme in ('blob', 'data', 'mailto'):
            continue
        if u.hostname and u.hostname not in HOSTS:
            continue
        if not u.path:
            continue
        checked += 1
        path = unquote(u.path)
        dest = ROOT / path.lstrip('/') if path.startswith('/') else (ROOT / name).parent / path
        if not dest.is_file():
            errors.append(f'{name}: descarga inexistente {ref}')
        elif dest.stat().st_size == 0:
            errors.append(f'{name}: descarga vacía {ref}')
assert checked > 0, 'No se encontraron descargas locales explícitas'
assert not errors, '\n'.join(errors)
print(f'PASS download targets: {checked} enlaces')

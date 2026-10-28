#!/usr/bin/env python3
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
ATTRS = {'data-href', 'data-url', 'data-link', 'data-target-url'}

class Targets(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.values = []
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ATTRS and value:
                self.values.append((key, value.strip()))

names = subprocess.check_output(['git', 'ls-files', '-z', '*.html'], cwd=ROOT).decode().split('\0')
errors = []
checked = 0
for name in names:
    if not name or name.startswith(('tests/', 'qa/', 'scripts/', 'data/', 'lab/')):
        continue
    parser = Targets()
    parser.feed((ROOT / name).read_text(encoding='utf-8'))
    for key, value in parser.values:
        if not value.startswith('/') or value.startswith('//'):
            continue
        u = urlsplit(value)
        path = unquote(u.path)
        if not path or path.startswith('/api/') or '${' in path:
            continue
        checked += 1
        target = ROOT / path.lstrip('/')
        if path.endswith('/'):
            target /= 'index.html'
        if not target.is_file():
            errors.append(f'{name} {key}={value}: destino inexistente')
assert not errors, '\n'.join(errors[:100])
print(f'PASS declarative URL targets: {checked} rutas locales')

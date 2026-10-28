#!/usr/bin/env python3
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://davidportodiaz.com'

class Redirects(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.targets = []
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'meta' and (d.get('http-equiv') or '').lower() == 'refresh':
            m = re.search(r'url\s*=\s*[\x22\x27]?([^;\x22\x27]+)', d.get('content', ''), re.I)
            if m:
                self.targets.append(m.group(1).strip())

names = subprocess.check_output(['git', 'ls-files', '-z', '*.html'], cwd=ROOT).decode().split('\0')
paths = {}
errors = []
for name in names:
    if not name or name.startswith(('tests/', 'qa/', 'scripts/', 'data/', 'lab/')):
        continue
    parser = Redirects()
    parser.feed((ROOT / name).read_text(encoding='utf-8'))
    if len(parser.targets) > 1:
        errors.append(f'{name}: redirecciones múltiples')
    if not parser.targets:
        continue
    source = '/' + name[:-10] if name.endswith('index.html') else '/' + name
    u = urlsplit(urljoin(ORIGIN + source, parser.targets[0]))
    if u.hostname not in ('davidportodiaz.com', 'www.davidportodiaz.com'):
        continue
    dest = unquote(u.path)
    file = ROOT / dest.lstrip('/')
    if dest.endswith('/'):
        file /= 'index.html'
    if not file.is_file():
        errors.append(f'{source}: redirección inexistente {dest}')
    paths[source] = dest
for source in paths:
    visited = set()
    current = source
    for hop in range(11):
        if current in visited:
            errors.append(f'Ciclo de redirección desde {source}: {current}')
            break
        visited.add(current)
        if current not in paths:
            break
        current = paths[current]
    else:
        errors.append(f'Cadena demasiado larga desde {source}')
assert not errors, '\n'.join(errors)
print(f'PASS redirect graph: {len(paths)} redirecciones locales')

#!/usr/bin/env python3
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://davidportodiaz.com'

class Forms(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.forms = []
    def handle_starttag(self, tag, attrs):
        if tag == 'form':
            self.forms.append(dict(attrs))

names = subprocess.check_output(['git', 'ls-files', '-z', '*.html'], cwd=ROOT).decode().split('\0')
errors = []
forms = 0
internal = 0
for name in names:
    if not name or name.startswith(('tests/', 'qa/', 'scripts/', 'data/', 'lab/')):
        continue
    parser = Forms()
    parser.feed((ROOT / name).read_text(encoding='utf-8'))
    page_url = ORIGIN + ('/' + name[:-10] if name.endswith('index.html') else '/' + name)
    for form in parser.forms:
        forms += 1
        action = (form.get('action') or '').strip()
        if not action or action.startswith(('#', 'javascript:')):
            continue
        url = urlsplit(urljoin(page_url, action))
        if url.netloc not in ('davidportodiaz.com', 'www.davidportodiaz.com'):
            continue
        internal += 1
        path = unquote(url.path)
        target = ROOT / path.lstrip('/')
        if path == '/' or path.endswith('/'):
            target /= 'index.html'
        if path.startswith('/api/'):
            continue
        if not target.is_file():
            errors.append(f'{name}: form action {action} no resuelve')
assert forms > 0, 'No se inspeccionaron formularios'
assert not errors, '\n'.join(errors)
print(f'PASS form actions: {forms} formularios, {internal} acciones locales explícitas')

#!/usr/bin/env python3
import json
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]

class Speculation(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.collect = False
        self.blocks = []
    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type', '').lower() == 'speculationrules':
            self.collect = True
            self.blocks.append('')
    def handle_data(self, data):
        if self.collect:
            self.blocks[-1] += data
    def handle_endtag(self, tag):
        if tag == 'script':
            self.collect = False

names = subprocess.check_output(['git', 'ls-files', '-z', '*.html'], cwd=ROOT).decode().split('\0')
errors = []
checked = 0
for name in names:
    if not name or name.startswith(('tests/', 'qa/', 'scripts/', 'lab/')):
        continue
    parser = Speculation()
    parser.feed((ROOT / name).read_text(encoding='utf-8'))
    for block in parser.blocks:
        try:
            rules = json.loads(block)
        except ValueError as exc:
            errors.append(f'{name}: JSON inválido: {exc}')
            continue
        for mode in ('prefetch', 'prerender'):
            for rule in rules.get(mode, []):
                for ref in rule.get('urls', []):
                    checked += 1
                    u = urlsplit(ref)
                    if u.scheme or u.netloc or not u.path.startswith('/'):
                        errors.append(f'{name}: destino no local {ref}')
                        continue
                    path = unquote(u.path)
                    dest = ROOT / path.lstrip('/')
                    if path.endswith('/'):
                        dest /= 'index.html'
                    if not dest.is_file():
                        errors.append(f'{name}: destino ausente {ref}')
assert checked > 0, 'Ninguna URL speculationrules examinada'
assert not errors, '\n'.join(errors[:100])
print(f'PASS speculation routes: {checked} destinos')

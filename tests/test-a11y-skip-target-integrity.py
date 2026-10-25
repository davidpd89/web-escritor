#!/usr/bin/env python3
"""Integridad de enlaces de salto en paginas publicas."""
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = ('tests/', 'qa/', 'scripts/', 'docs/', 'lab/')

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.skips = []
        self.refresh = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.append(a['id'])
        if tag == 'a' and 'skip-link' in a.get('class', '').split():
            self.skips.append(a.get('href', ''))
        if tag == 'meta' and a.get('http-equiv', '').lower() == 'refresh':
            self.refresh = True

paths = subprocess.check_output(['git', 'ls-files', '*.html'], cwd=ROOT, text=True).splitlines()
errors = []
checked = 0
for rel in paths:
    if rel.startswith(EXCLUDED) or rel == 'video-ios-test/index.html':
        continue
    p = Parser()
    p.feed((ROOT / rel).read_text(encoding='utf-8', errors='replace'))
    if p.refresh:
        continue
    checked += 1
    for href in p.skips:
        if not href.startswith('#') or len(href) < 2:
            errors.append(f'{rel}: destino de salto invalido: {href}')
        elif p.ids.count(href[1:]) != 1:
            errors.append(f'{rel}: {href} tiene {p.ids.count(href[1:])} destinos')
assert checked > 0
print(f'Skip links: {checked} paginas, {len(errors)} errores')
print('\n'.join(errors[:60]))
sys.exit(bool(errors))
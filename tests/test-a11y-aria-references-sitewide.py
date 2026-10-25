#!/usr/bin/env python3
"""Referencias ARIA rotas en HTML versionado."""
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = ('tests/', 'qa/', 'scripts/', 'docs/', 'lab/')
ATTRS = ('aria-controls', 'aria-labelledby', 'aria-describedby', 'aria-owns', 'aria-activedescendant')

class Audit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.refs = []
        self.redirect = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.append(a['id'])
        if tag == 'meta' and a.get('http-equiv', '').lower() == 'refresh':
            self.redirect = True
        for name in ATTRS:
            if a.get(name):
                for target in a[name].split():
                    self.refs.append((name, target))

paths = subprocess.check_output(['git', 'ls-files', '*.html'], cwd=ROOT, text=True).splitlines()
errors = []
checked = 0
for rel in paths:
    if rel.startswith(EXCLUDED) or rel == 'video-ios-test/index.html':
        continue
    doc = Audit()
    doc.feed((ROOT / rel).read_text(encoding='utf-8', errors='replace'))
    if doc.redirect:
        continue
    checked += 1
    for attr, target in doc.refs:
        count = doc.ids.count(target)
        if count != 1:
            errors.append(f'{rel}: {attr}={target}: {count} destinos')
assert checked > 0
print(f'ARIA references: {checked} paginas, {len(errors)} errores')
print('\n'.join(errors[:80]))
sys.exit(bool(errors))
#!/usr/bin/env python3
"""Precargas CSS locales y duplicados."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.preloads = []
        self.redirect = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('http-equiv', '').lower() == 'refresh':
            self.redirect = True
        if tag == 'link' and 'preload' in a.get('rel', '').split() and a.get('as') == 'style':
            self.preloads.append(a.get('href', ''))

paths = subprocess.check_output(['git', 'ls-files', '*.html'], cwd=ROOT, text=True).splitlines()
errors = []
checked = 0
for rel in paths:
    if rel.startswith(('tests/', 'qa/', 'docs/', 'scripts/', 'lab/')):
        continue
    doc = Links()
    doc.feed((ROOT / rel).read_text(encoding='utf-8', errors='replace'))
    if doc.redirect:
        continue
    checked += 1
    seen = set()
    for href in doc.preloads:
        parsed = urlsplit(href)
        if parsed.scheme or parsed.netloc:
            continue
        resource = unquote(parsed.path)
        if not resource.endswith('.css'):
            errors.append(f'{rel}: preload as=style no CSS: {href}')
            continue
        target = ROOT / resource.lstrip('/') if resource.startswith('/') else (ROOT / rel).parent / resource
        if not target.is_file():
            errors.append(f'{rel}: recurso inexistente: {href}')
        if resource in seen:
            errors.append(f'{rel}: precarga CSS duplicada: {resource}')
        seen.add(resource)
assert checked > 0
print(f'CSS preloads: {checked} paginas, {len(errors)} errores')
print('\n'.join(errors[:80]))
sys.exit(bool(errors))
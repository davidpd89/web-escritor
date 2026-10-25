#!/usr/bin/env python3
"""Politica de ampliacion movil WCAG 1.4.4."""
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

class Audit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.viewports = []
        self.redirect = False
    def handle_starttag(self, tag, attrs):
        if tag != 'meta':
            return
        a = dict(attrs)
        if a.get('http-equiv', '').lower() == 'refresh':
            self.redirect = True
        if a.get('name', '').lower() == 'viewport':
            self.viewports.append(a.get('content', ''))

paths = subprocess.check_output(['git', 'ls-files', '*.html'], cwd=ROOT, text=True).splitlines()
errors = []
checked = 0
for rel in paths:
    if rel.startswith(('tests/', 'qa/', 'scripts/', 'docs/', 'lab/')) or rel == 'video-ios-test/index.html':
        continue
    doc = Audit()
    doc.feed((ROOT / rel).read_text(encoding='utf-8', errors='replace'))
    if doc.redirect:
        continue
    checked += 1
    if len(doc.viewports) != 1:
        errors.append(f'{rel}: {len(doc.viewports)} viewports')
    for value in doc.viewports:
        parts = dict(x.strip().split('=', 1) for x in value.lower().split(',') if '=' in x)
        if parts.get('user-scalable') in ('no', '0'):
            errors.append(f'{rel}: zoom desactivado')
        if 'maximum-scale' in parts:
            try:
                if float(parts['maximum-scale']) < 5:
                    errors.append(f'{rel}: maximum-scale insuficiente')
            except ValueError:
                errors.append(f'{rel}: maximum-scale invalido')
assert checked > 0
print(f'Viewport zoom: {checked} paginas, {len(errors)} errores')
print('\n'.join(errors[:80]))
sys.exit(bool(errors))
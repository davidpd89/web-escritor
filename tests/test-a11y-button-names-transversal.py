#!/usr/bin/env python3
"""Botones sin nombre accesible en HTML estatico."""
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

class Audit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.buttons = []
        self.redirect = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('http-equiv', '').lower() == 'refresh':
            self.redirect = True
        if tag == 'button':
            item = {'attrs': a, 'text': ''}
            self.stack.append(item)
            self.buttons.append(item)
        if tag == 'img' and self.stack:
            self.stack[-1]['text'] += a.get('alt', '')
    def handle_data(self, data):
        for item in self.stack:
            item['text'] += data
    def handle_endtag(self, tag):
        if tag == 'button' and self.stack:
            self.stack.pop()

paths = subprocess.check_output(['git', 'ls-files', '*.html'], cwd=ROOT, text=True).splitlines()
errors = []
checked = 0
for rel in paths:
    if rel.startswith(('tests/', 'qa/', 'docs/', 'scripts/', 'lab/')) or rel == 'video-ios-test/index.html':
        continue
    audit = Audit()
    audit.feed((ROOT / rel).read_text(encoding='utf-8', errors='replace'))
    if audit.redirect:
        continue
    checked += 1
    for index, item in enumerate(audit.buttons, 1):
        a = item['attrs']
        if a.get('aria-hidden') == 'true':
            continue
        if not (item['text'].strip() or a.get('aria-label', '').strip() or a.get('aria-labelledby', '').strip() or a.get('title', '').strip()):
            errors.append(f'{rel}: button #{index} sin nombre')
assert checked > 0
print(f'Button names: {checked} paginas, {len(errors)} errores')
print('\n'.join(errors[:80]))
sys.exit(bool(errors))
#!/usr/bin/env python3
"""Identidad semantica de articulos y tarjetas."""
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]

class Audit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.articles = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'article':
            self.stack.append({'named': bool(a.get('aria-label') or a.get('aria-labelledby')), 'heading': False})
        elif re.fullmatch(r'h[1-6]', tag):
            for article in self.stack:
                article['heading'] = True

    def handle_endtag(self, tag):
        if tag == 'article' and self.stack:
            self.articles.append(self.stack.pop())

errors = []
checked = 0
for rel in subprocess.check_output(['git', 'ls-files', '*.html'], cwd=ROOT, text=True).splitlines():
    if rel.startswith(('tests/', 'qa/', 'scripts/', 'docs/', 'lab/')):
        continue
    html = (ROOT / rel).read_text(encoding='utf-8', errors='replace')
    if re.search(r'<meta\s+http-equiv=["\']refresh', html, re.I):
        continue
    page = Audit()
    page.feed(html)
    for index, article in enumerate(page.articles, 1):
        checked += 1
        if not article['named'] and not article['heading']:
            errors.append(f'{rel}: article #{index} sin nombre ni encabezado')

assert checked, 'No se encontraron articulos'
print(f'article-semantics: {checked} articulos, {len(errors)} fallos')
for error in errors[:100]:
    print('FAIL', error)
raise SystemExit(bool(errors))

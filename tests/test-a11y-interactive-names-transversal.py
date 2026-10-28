#!/usr/bin/env python3
"""Enlaces y botones sin nombre accesible."""
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import re

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = ('tests/', 'qa/', 'scripts/', 'docs/', 'lab/')

class Audit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = []
        self.controls = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ('a', 'button'):
            self.active.append([tag, a, ''])
        elif tag == 'img' and self.active:
            self.active[-1][2] += a.get('alt') or ''

    def handle_data(self, data):
        for item in self.active:
            item[2] += data

    def handle_endtag(self, tag):
        if self.active and self.active[-1][0] == tag:
            self.controls.append(self.active.pop())

errors = []
checked = 0
for rel in subprocess.check_output(['git', 'ls-files', '*.html'], cwd=ROOT, text=True).splitlines():
    if rel.startswith(EXCLUDED) or rel == 'video-ios-test/index.html':
        continue
    html = (ROOT / rel).read_text(encoding='utf-8', errors='replace')
    if re.search(r'<meta\s+http-equiv=["\']refresh', html, re.I):
        continue
    page = Audit()
    page.feed(html)
    for tag, a, content in page.controls:
        if tag == 'a' and (not a.get('href') or (a.get('aria-hidden', '').strip().lower() == 'true' and a.get('tabindex', '').strip() == '-1')):
            continue
        checked += 1
        named = any((a.get(k) or '').strip() for k in ('aria-label', 'aria-labelledby'))
        named |= bool(content.strip())
        if not named:
            errors.append(f'{rel}: {tag} sin nombre; href={a.get("href", "-")}')

assert checked, 'No se han revisado controles'
print(f'interactive-names: {checked} controles, {len(errors)} fallos')
for error in errors[:100]:
    print('FAIL', error)
raise SystemExit(bool(errors))

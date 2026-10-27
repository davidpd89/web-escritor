#!/usr/bin/env python3
"""Jerarquia de encabezados en HTML versionados."""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = ('tests/', 'qa/', 'scripts/', 'docs/', 'lab/')
NAMES = subprocess.check_output(
    ['git', '-c', 'core.quotepath=false', 'ls-files', '*.html'],
    cwd=ROOT, text=True
).splitlines()
errors = []
checked = 0

for rel in NAMES:
    if rel.startswith(EXCLUDED) or rel == 'video-ios-test/index.html':
        continue
    html = (ROOT / rel).read_text(encoding='utf-8', errors='replace')
    if re.search(r'<meta\s+http-equiv=["\']refresh', html, re.I):
        continue
    main = re.search(r'<main\b[^>]*>(.*?)</main\s*>', html, re.I | re.S)
    if not main:
        continue
    checked += 1
    levels = [int(n) for n in re.findall(r'<h([1-6])\b', main.group(1), re.I)]
    if levels.count(1) != 1:
        errors.append(f'{rel}: H1 en main = {levels.count(1)}')
    previous = 1
    for level in levels:
        if level > previous + 1:
            errors.append(f'{rel}: salto H{previous} -> H{level}')
        previous = level

assert checked > 0, 'No se han encontrado paginas comprobables'
for error in errors:
    print('FAIL', error)
print(f'heading-outline: {checked} paginas, {len(errors)} fallos')
raise SystemExit(bool(errors))

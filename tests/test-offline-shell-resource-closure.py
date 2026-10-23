#!/usr/bin/env python3
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sw = (ROOT / 'service-worker.js').read_text(encoding='utf-8')
html = (ROOT / 'offline.html').read_text(encoding='utf-8')
match = re.search(r'const\s+APP_SHELL\s*=\s*\[([\s\S]*?)\]', sw)
assert match, 'APP_SHELL no encontrado'
shell = set(re.findall(r'''['\"](/[^'\"]+)['\"]''', match.group(1)))
assert '/offline.html' in shell
assert len(shell) >= 5
errors = []
for url in shell:
    p = ROOT / urlsplit(url).path.lstrip('/')
    if not p.is_file():
        errors.append(f'APP_SHELL inexistente: {url}')
refs = re.findall(r'url\(\s*[\x22\x27]?(/[^)\x22\x27]+)', html)
assert refs, 'No se han encontrado las fuentes offline esperadas'
for url in refs:
    path = urlsplit(url).path
    if path not in shell:
        errors.append(f'Recurso offline fuera del precache: {url}')
    if not (ROOT / path.lstrip('/')).is_file():
        errors.append(f'Recurso offline inexistente: {url}')
assert not errors, '\n'.join(errors)
print(f'PASS offline closure: {len(shell)} recursos cacheados; {len(refs)} referencias')

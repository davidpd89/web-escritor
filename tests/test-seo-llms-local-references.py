#!/usr/bin/env python3
from __future__ import annotations
import re
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / 'llms.txt').read_text(encoding='utf-8')
urls = re.findall(r'https?://[^\s<>]+', text)
internal = []

for raw in urls:
    url = raw.rstrip('.,);]')
    parsed = urlsplit(url)
    if parsed.hostname != 'davidportodiaz.com':
        continue
    internal.append(url)

assert internal, 'No se han encontrado URL internas en llms.txt'
errors = []
for url in internal:
    parsed = urlsplit(url)
    path = unquote(parsed.path)
    if '..' in Path(path).parts:
        errors.append(f'Ruta con traversal: {url}')
        continue
    relative = path.lstrip('/')
    if not relative or path.endswith('/'):
        relative = relative + 'index.html'
    target = ROOT / relative
    if not target.is_file():
        errors.append(f'Recurso inexistente: {url} -> {target.relative_to(ROOT)}')

assert not errors, '\n'.join(errors)
print(f'PASS llms references: {len(internal)} URL internas verificadas')

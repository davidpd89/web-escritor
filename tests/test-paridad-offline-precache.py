#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
worker = (ROOT / 'service-worker.js').read_text(encoding='utf-8')
offline = (ROOT / 'offline.html').read_text(encoding='utf-8')
manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
match = re.search(r'const\s+APP_SHELL\s*=\s*(\[[\s\S]*?\]);', worker)
assert match, 'APP_SHELL no se puede localizar'
shell = json.loads(match.group(1))
assert len(shell) == len(set(shell)), 'Recursos APP_SHELL duplicados'
assert '/offline.html' in shell and '/manifest.json' in shell
resources = set(re.findall(r'url\([\x22\x27]?(/assets/fonts/[^\x22\x27)]+)', offline))
assert resources, 'La página offline no declara fuentes locales'
for resource in resources:
    assert resource in shell, f'Fuente offline fuera del precache: {resource}'
required = {'/offline.html', '/manifest.json'} | resources
required |= {item['src'] for item in manifest['icons']}
for url in required:
    assert url in shell, f'Recurso esencial sin precache: {url}'
for url in shell:
    assert url.startswith('/') and not url.startswith('//'), url
    assert (ROOT / url.lstrip('/')).is_file(), f'Recurso offline inexistente: {url}'
print(f'OK precache: {len(shell)} recursos, {len(resources)} fuentes')

#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
page = (ROOT / 'publicar-web/index.html').read_text(encoding='utf-8')
hub = (ROOT / 'herramientas/index.html').read_text(encoding='utf-8')
registry = json.loads((ROOT / 'data/tools-hub.json').read_text(encoding='utf-8'))

spec = importlib.util.spec_from_file_location('public_dist', ROOT / 'scripts/build-public-dist.py')
assert spec and spec.loader
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

assert 'href="/herramientas/"' in page
assert 'JSON-LD' in page
assert builder.is_publishable('herramientas/index.html', ROOT)

candidates = [tool for tool in registry['tools'] if 'json-ld' in tool['slug'].lower()]
assert candidates, 'No existe herramienta JSON-LD registrada'

for tool in candidates:
    href = tool['href']
    assert href in hub, f'El hub no presenta {href}'
    assert href.startswith('/') and href.endswith('/')
    target = href.strip('/') + '/index.html'
    assert (ROOT / target).is_file(), target
    assert builder.is_publishable(target, ROOT), target
    assert (ROOT / tool['source_doc']).is_file(), tool['source_doc']

print(f'PASS publicar-web: {len(candidates)} herramientas JSON-LD alcanzables desde el hub')

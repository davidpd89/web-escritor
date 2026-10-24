#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('public_dist', ROOT / 'scripts/build-public-dist.py')
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)

SOURCE = 'publicar-web/index.html'
HTML = (ROOT / SOURCE).read_text(encoding='utf-8')
assert 'name="robots"' in HTML and 'noindex' in HTML.lower()
assert not builder.is_publishable(SOURCE, ROOT)

states = (None, 'public', 'internal', 'noindex', 'gated', 'deprecated')
for status in states:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / 'data').mkdir()
        (root / 'publicar-web').mkdir()
        (root / SOURCE).write_text(HTML, encoding='utf-8')
        entry = {
            'id': 'checklist-publicacion',
            'url': '/publicar-web/',
            'sourceFile': SOURCE,
        }
        if status is not None:
            entry['status'] = status
        payload = {'defaults': {'status': 'public'}, 'entries': [entry]}
        (root / 'data/content-registry.json').write_text(json.dumps(payload), encoding='utf-8')
        assert not builder.is_publishable(SOURCE, root), f'Estado {status}: publicación inesperada'
        policy = builder.render_assetsignore(root)
        assert '!/publicar-web/' not in policy, f'Estado {status}: namespace abierto'

print(f'PASS publicar-web: {len(states)} estados editoriales mantienen el cierre')

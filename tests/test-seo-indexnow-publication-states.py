import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('indexnow_states', ROOT / 'scripts/indexnow.py')
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / 'registry.json'
    entries = []
    statuses = ['public', 'draft', 'preview', 'scheduled', 'internal', 'gated', 'noindex', 'deprecated']
    for status in statuses:
        entries.append({
            'id': status,
            'url': f'/{status}/',
            'sourceFile': f'{status}/index.html',
            'status': status,
            'searchIndex': True,
        })
    entries.append({
        'id': 'excluded',
        'url': '/excluded/',
        'sourceFile': 'excluded/index.html',
        'status': 'public',
        'searchIndex': False,
    })
    path.write_text(json.dumps({'defaults': {'status': 'public', 'searchIndex': True}, 'entries': entries}), encoding='utf-8')
    routes = mod.registry_routes(path)
    assert routes == {'/public/': 'public/index.html'}, routes

print('PASS IndexNow publication-state contract')

#!/usr/bin/env python3
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('indexnow_state_test', ROOT / 'scripts/indexnow.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

entries = [
    {'url': '/public/', 'sourceFile': 'public/index.html', 'status': 'public'},
    {'url': '/draft/', 'sourceFile': 'draft/index.html', 'status': 'draft'},
    {'url': '/review/', 'sourceFile': 'review/index.html', 'status': 'review'},
    {'url': '/archived/', 'sourceFile': 'archived/index.html', 'status': 'archived'},
    {'url': '/gated/', 'sourceFile': 'gated/index.html', 'status': 'gated'},
    {'url': '/deprecated/', 'sourceFile': 'deprecated/index.html', 'status': 'deprecated'},
    {'url': '/noindex/', 'sourceFile': 'noindex/index.html', 'status': 'noindex'},
    {'url': '/without-search/', 'sourceFile': 'without-search/index.html', 'searchIndex': False},
    {'url': '/without-sitemap/', 'sourceFile': 'without-sitemap/index.html', 'sitemap': False},
]
fixture = {
    'defaults': {'status': 'public', 'searchIndex': True, 'sitemap': True},
    'entries': entries,
}

with tempfile.TemporaryDirectory() as temporary:
    path = Path(temporary) / 'registry.json'
    path.write_text(json.dumps(fixture), encoding='utf-8')
    routes = mod.registry_routes(path)
    assert routes == {'/public/': 'public/index.html'}, f'IndexNow filtró mal los estados: {routes}'

print('OK: IndexNow solo anuncia rutas públicas autorizadas')

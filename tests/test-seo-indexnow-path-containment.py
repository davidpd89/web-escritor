import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('indexnow_paths', ROOT / 'scripts/indexnow.py')
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

entries = [
    {'url': '/normal/', 'sourceFile': 'normal/index.html'},
    {'url': '//evil.invalid/', 'sourceFile': 'evil/index.html'},
    {'url': '/traversal/', 'sourceFile': '../../secrets.html'},
    {'url': '/backslash/', 'sourceFile': '..\\private.html'},
    {'url': '/absolute/', 'sourceFile': '/etc/passwd'},
]
for entry in entries:
    entry.update(status='public', searchIndex=True)

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / 'registry.json'
    path.write_text(json.dumps({'defaults': {}, 'entries': entries}), encoding='utf-8')
    routes = mod.registry_routes(path)
    assert routes == {'/normal/': 'normal/index.html'}, routes

print('PASS IndexNow path containment')

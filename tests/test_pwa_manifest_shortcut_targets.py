from pathlib import Path
from urllib.parse import urlsplit
import json

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
shortcuts = manifest.get('shortcuts', [])
assert shortcuts, 'manifest.json: no hay accesos directos'
scope = manifest.get('scope', '/')
assert scope.startswith('/'), f'manifest.json: scope inválido {scope}'
seen = set()
for shortcut in shortcuts:
    name = shortcut.get('name', '')
    url = shortcut.get('url', '')
    parsed = urlsplit(url)
    assert name.strip(), f'manifest.json: acceso directo sin nombre: {url}'
    assert not parsed.scheme and not parsed.netloc, f'manifest.json: shortcut externo {url}'
    assert parsed.path.startswith(scope), f'manifest.json: {url} fuera del scope {scope}'
    assert parsed.path not in seen, f'manifest.json: shortcut duplicado {url}'
    seen.add(parsed.path)
    relative = parsed.path.lstrip('/')
    destination = ROOT / relative
    if parsed.path.endswith('/'):
        destination = destination / 'index.html'
    elif destination.suffix == '':
        destination = destination / 'index.html'
    assert destination.is_file(), f'manifest.json: {name} apunta a página inexistente {url}'
    content = destination.read_text(encoding='utf-8').lower()
    assert '<html' in content, f'manifest.json: {url} no contiene un documento HTML'
print(f'PASS: {len(shortcuts)} accesos directos válidos')

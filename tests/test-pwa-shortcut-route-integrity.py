#!/usr/bin/env python3
import json
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
raw = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
defaults = raw.get('defaults', {})
public = {e['url'] for item in raw['entries'] if (e := {**defaults, **item}).get('status') == 'public'}
errors = []
scope = manifest['scope']
assert scope.startswith('/') and not scope.startswith('//')

def verify(label, value):
    u = urlsplit(value)
    if u.scheme or u.netloc or not value.startswith('/') or value.startswith('//'):
        errors.append(f'{label}: URL no local: {value}')
        return
    path = unquote(u.path)
    if not path.startswith(scope):
        errors.append(f'{label}: fuera del scope: {value}')
    dest = ROOT / path.lstrip('/')
    if path == '/' or path.endswith('/'):
        dest /= 'index.html'
    if not dest.is_file():
        errors.append(f'{label}: fichero inexistente: {value}')
    if path not in public:
        errors.append(f'{label}: ruta ausente del registro público: {value}')

verify('start_url', manifest['start_url'])
shortcuts = manifest.get('shortcuts', [])
assert len(shortcuts) >= 3, 'Han desaparecido shortcuts de la PWA'
for item in shortcuts:
    assert item.get('name', '').strip()
    verify(item['name'], item['url'])
for icon in manifest.get('icons', []):
    p = urlsplit(icon['src']).path
    if not (ROOT / p.lstrip('/')).is_file():
        errors.append(f'Icono inexistente: {p}')
assert not errors, '\n'.join(errors)
print(f'PASS PWA navigation: {len(shortcuts)} shortcuts')

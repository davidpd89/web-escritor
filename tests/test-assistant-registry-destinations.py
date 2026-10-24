import json
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
registry = json.loads((ROOT / 'data/assistant-source-registry.json').read_text(encoding='utf-8'))
errors = []
checked = 0

for item in registry['sources']:
    if item.get('visibility') != 'public':
        continue
    url = item['url']
    parts = urlsplit(url)
    if parts.scheme or parts.netloc or parts.query or parts.fragment:
        errors.append(f'{item["id"]}: URL no canónica: {url}')
        continue
    decoded = unquote(parts.path)
    candidate = (ROOT / decoded.lstrip('/')).resolve()
    if decoded.endswith('/') or candidate.is_dir():
        candidate = candidate / 'index.html'
    if not candidate.is_relative_to(ROOT.resolve()):
        errors.append(f'{item["id"]}: destino fuera del repositorio')
        continue
    checked += 1
    if not candidate.is_file():
        errors.append(f'{item["id"]}: {url} no existe ({candidate.relative_to(ROOT)})')

assert checked > 10, 'Registro insuficiente o no cargado'
assert not errors, '\n'.join(errors)
print(f'assistant-registry-destinations: OK ({checked} destinos)')

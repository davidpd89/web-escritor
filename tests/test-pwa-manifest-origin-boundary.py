import json
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://davidportodiaz.com'
manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))

entries = [('id', manifest['id']), ('start_url', manifest['start_url']), ('scope', manifest['scope'])]
entries += [(f'icons[{i}].src', item['src']) for i, item in enumerate(manifest.get('icons', []))]
entries += [(f'shortcuts[{i}].url', item['url']) for i, item in enumerate(manifest.get('shortcuts', []))]
assert manifest.get('icons'), 'manifest.json: no declara iconos instalables'
assert manifest.get('shortcuts'), 'manifest.json: no declara accesos directos'

for name, value in entries:
    assert isinstance(value, str) and value.startswith('/') and not value.startswith('//'), f'manifest.json {name}: ruta no local: {value!r}'
    url = urlsplit(urljoin(ORIGIN + '/', value))
    assert url.scheme == 'https' and url.netloc == 'davidportodiaz.com', f'manifest.json {name}: origen inseguro: {value}'
    assert not url.username and not url.password and not url.fragment, f'manifest.json {name}: credenciales o fragmento inesperado: {value}'
    assert not url.query, f'manifest.json {name}: destino instalable con parámetros inesperados: {value}'
    target = ROOT / url.path.lstrip('/')
    if url.path == '/' or url.path.endswith('/'):
        target = target / 'index.html'
    assert target.is_file(), f'manifest.json {name}: recurso inexistente: {value}'

print(f'PASS: {len(entries)} destinos del manifiesto permanecen dentro del origen y existen')
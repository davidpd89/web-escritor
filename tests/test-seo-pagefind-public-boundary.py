#!/usr/bin/env python3
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pagefind_boundary_test', ROOT / 'scripts/build-pagefind-index.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    files = [
        'index.html',
        'lab/prototipo.html',
        '_tools/informe.html',
        '.preview-dist/pagina.html',
        'tests/fixtures/prueba.html',
        'data/fragmento.html',
    ]
    for relative in files:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('<html lang="es"><head><title>Fixture</title></head><body><main>Texto privado de prueba</main></body></html>', encoding='utf-8')

    registry = {'defaults': {'status': 'public', 'searchIndex': True}, 'entries': []}
    (root / 'data/content-registry.json').write_text(json.dumps(registry), encoding='utf-8')
    subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
    subprocess.run(['git', 'add', '-f', '--', *files, 'data/content-registry.json'], cwd=root, check=True)

    indexed = mod.eligible_pages(root)
    assert indexed == ['index.html'], f'Pagefind indexaría documentos internos: {indexed}'

print('OK: Pagefind y publicación comparten frontera de privacidad')

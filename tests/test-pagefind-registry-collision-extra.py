import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pagefind_builder_collision', ROOT / 'scripts/build-pagefind-index.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

for reverse in (False, True):
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root / 'data').mkdir()
        (root / 'target.html').write_text('<html><head></head><body>Contenido privado</body></html>', encoding='utf-8')
        entries = [
            {'sourceFile': 'target.html', 'status': 'private'},
            {'sourceFile': 'target.html', 'status': 'public'}
        ]
        if reverse:
            entries.reverse()
        registry = {'defaults': {'status': 'public', 'searchIndex': True}, 'entries': entries}
        (root / 'data/content-registry.json').write_text(json.dumps(registry), encoding='utf-8')
        subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
        subprocess.run(['git', 'add', '-A'], cwd=root, check=True)
        pages = b.eligible_pages(root)
        assert 'target.html' not in pages, f'Colisión insegura reverse={reverse}: {pages}'

print('PASS: política restrictiva resistente a colisiones')

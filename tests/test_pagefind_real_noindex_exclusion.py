import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pagefind_builder_real', ROOT / 'scripts/build-pagefind-index.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
manifest = json.loads((ROOT / 'pagefind/eligible-manifest.json').read_text(encoding='utf-8'))
indexed = set(manifest['pages'])
tracked = subprocess.check_output(['git', 'ls-files', '*.html'], cwd=ROOT, text=True).splitlines()
blocked = []

for relative in tracked:
    path = ROOT / relative
    if not path.is_file():
        continue
    html = path.read_text(encoding='utf-8', errors='ignore')
    if module.is_noindex(html):
        blocked.append(relative)

assert blocked, 'No se encontraron páginas HTML reales con noindex'
leaked = sorted(set(blocked) & indexed)
assert not leaked, f'Pagefind indexa páginas HTML con noindex: {leaked}'
print(f'PASS: {len(blocked)} documentos noindex excluidos del manifiesto Pagefind')

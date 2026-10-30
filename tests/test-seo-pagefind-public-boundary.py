#!/usr/bin/env python3
"""Todo lo que Pagefind indexa también debe poder publicarse.

El generador de Pagefind decide por su cuenta qué páginas son elegibles; el
publicador (scripts/build-public-dist.py) decide qué se sirve. Si divergen, el
buscador acabaría ofreciendo páginas internas que no existen en producción.
"""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_public_dist', ROOT / 'scripts' / 'build-public-dist.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)

manifest = json.loads((ROOT / 'pagefind' / 'eligible-manifest.json').read_text(encoding='utf-8'))
leaked = [page for page in manifest['pages'] if not publisher.is_publishable(page, ROOT)]
assert not leaked, f'Pagefind indexa páginas que el publicador no sirve: {leaked}'
print(f"OK: {len(manifest['pages'])} páginas indexadas, todas publicables")

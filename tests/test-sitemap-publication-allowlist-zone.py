from __future__ import annotations
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

sitemap = load('zone_sitemap_allowlist', 'scripts/build-sitemap.py')
publisher = load('zone_publisher_allowlist', 'scripts/build-public-dist.py')

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    pages = ['index.html', 'inventado/index.html', 'scripts/interno.html', 'lab/prototipo.html']
    for rel in pages:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('<html><head><title>Prueba</title></head><body>Contenido</body></html>', encoding='utf-8')
    urls = sitemap.collect_urls(root)
    for rel in pages:
        if not publisher.is_publishable(rel, root):
            loc = sitemap.normalize_canonical(None, root, root / rel)
            assert loc not in urls, f'El sitemap anuncia un documento no publicable: {rel}'
    assert 'https://davidportodiaz.com/' in urls
print('PASS sitemap publication allowlist')

from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('zone_sitemap_robots', ROOT / 'scripts/build-sitemap.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

blocked = [
    '<meta name="robots" content="noindex,follow">',
    '<meta content="noindex,follow" name="robots">',
    "<META CONTENT='NOINDEX' NAME='ROBOTS'>",
    '<meta name=robots content=noindex>',
    '<meta name="robots" content="index, noindex">',
    '<meta name="description" content="Texto"><meta name="robots" content="noindex">',
]
for markup in blocked:
    _, noindex, _ = module.extract_meta('<html><head>' + markup + '</head></html>')
    assert noindex, f'Noindex ignorado: {markup}'

allowed = [
    '<meta name="robots" content="index,follow">',
    '<meta name="description" content="noindex">',
    '<meta name="robots" content="nofollow">',
]
for markup in allowed:
    _, noindex, _ = module.extract_meta(markup)
    assert not noindex, f'Falso positivo noindex: {markup}'
print('PASS sitemap robots attribute permutations')

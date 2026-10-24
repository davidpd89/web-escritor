#!/usr/bin/env python3
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap_under_test', ROOT / 'scripts/build-sitemap.py')
sitemap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sitemap)

URL = 'https://davidportodiaz.com/cuaderno/prueba/'
variants = [
    ('<link rel="canonical" href="' + URL + '">', '<meta name="robots" content="noindex,follow">'),
    ('<link href="' + URL + '" rel="canonical">', '<meta content="noindex,follow" name="robots">'),
    ('<link HREF="' + URL + '" REL="canonical">', '<meta CONTENT="NOINDEX,FOLLOW" NAME="ROBOTS">'),
    ('<link data-qa="1" href="' + URL + '" rel="canonical">', '<meta data-qa="1" content="follow, noindex" name="robots">'),
]

for index, (link, meta) in enumerate(variants, 1):
    html = '<html><head>' + link + meta + '</head><body></body></html>'
    canonical, noindex, _ = sitemap.extract_meta(html)
    assert canonical == URL, f'Variante {index}: canonical perdido: {canonical!r}'
    assert noindex is True, f'Variante {index}: noindex no reconocido'

print('OK: canonical y noindex independientes del orden de atributos')

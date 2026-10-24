#!/usr/bin/env python3
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap_collision_test', ROOT / 'scripts/build-sitemap.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

BASE = 'https://davidportodiaz.com'

def document(canonical, date):
    return ('<html><head><link rel="canonical" href="' + canonical + '">' +
            '<script type="application/ld+json">' +
            '{"@type":"WebPage","dateModified":"' + date + '"}' +
            '</script></head><body><main>Contenido</main></body></html>')

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    files = {
        'index.html': document(BASE + '/', '2026-08-01'),
        'editoriales/index.html': document(BASE + '/editoriales/', '2026-10-03'),
        'editoriales/alias.html': document(BASE + '/editoriales/', '2026-10-09'),
        '404.html': document(BASE + '/404/', '2026-10-10'),
        'lab/prueba.html': document(BASE + '/lab/prueba/', '2026-10-10'),
        'assets/debug.html': document(BASE + '/assets/debug/', '2026-10-10'),
    }
    for relative, content in files.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')

    actual = mod.collect_urls(root)
    assert set(actual) == {BASE + '/', BASE + '/editoriales/'}, actual
    assert actual[BASE + '/editoriales/'] == '2026-10-09'
    assert actual[BASE + '/'] == '2026-08-01'
    assert list(actual) == sorted(actual), 'Orden no determinista'

print('OK: deduplicación, máximo lastmod y exclusión de contenido interno')

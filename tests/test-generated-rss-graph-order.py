from __future__ import annotations
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rss_graph', ROOT / 'scripts/build-feed.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

article = {
    '@type': 'Article',
    'headline': 'Artículo verificable',
    'url': 'https://davidportodiaz.com/cuaderno/fixture/',
    'datePublished': '2026-06-12',
    'description': 'Descripción verificable.'
}
other = {'@type': 'BreadcrumbList', 'name': 'Navegación'}
results = []
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / 'index.html'
    for nodes in ([article, other], [other, article]):
        document = {'@context': 'https://schema.org', '@graph': nodes}
        html = '<html><head><script type="application/ld+json">' + json.dumps(document, ensure_ascii=False) + '</script></head><body></body></html>'
        path.write_text(html, encoding='utf-8')
        result = mod.extract_metadata(str(path))
        results.append({key: result.get(key) for key in ('title', 'url', 'date', 'description')})
assert results[0] == results[1], f'El orden del grafo altera el RSS: {results}'
assert results[0]['date'] == '2026-06-12'
assert results[0]['url'] == article['url']
print('RSS graph order: OK')
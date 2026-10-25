from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rss_types', ROOT / 'scripts/build-feed.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

cases = [
    ({'@graph': [{'@type': 'CollectionPage'}]}, True),
    ({'@graph': [{'@type': 'CollectionPage'}, {'@type': 'BreadcrumbList'}]}, True),
    ({'@graph': [{'@type': 'Article'}]}, False),
    ({'@graph': [{'@type': 'BlogPosting'}]}, False),
    ({'@graph': [{'@type': ['CollectionPage', 'Article']}]}, False),
    ({'@graph': [{'@type': 'CollectionPage'}, {'@type': 'NewsArticle'}]}, False),
    ({'@graph': [{'@type': 'WebPage'}]}, False),
]
for document, expected in cases:
    actual = mod.is_non_article_page(document)
    assert actual is expected, f'Clasificación incorrecta: {document}: {actual}'
print('RSS collection types: OK')